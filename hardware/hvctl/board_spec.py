#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOLDEN NETLIST AS CODE for `hvctl` -- the iseg bipolar/dual-unipolar HV controller.

    "One machine-readable source of truth for what connects to what, authored
     BEFORE any CAD file, consumed by the schematic generator, the netlist
     checker and the layout tools.  Acceptance everywhere is a diff against it."
                                       -- EE_PROJECT_BOOTSTRAP.md section V.1

Stdlib-only.  Zero-arg.  Deterministic (uuid5 over a fixed namespace, NEVER uuid4).
Runs on any Python 3; imports no KiCad API.  Exit 0 = every check passed.

    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/board_spec.py

Exit codes:  0 ok  /  1 verification failed  /  2 structural failure.

=============================================================================
0.  WHAT THIS FILE IS, AND WHAT IT STRUCTURALLY CANNOT SEE
=============================================================================
It is a connectivity graph plus a small behavioural model of the contacts and
the logic gates.  Exit 0 means the graph is internally consistent and the four
domain invariants hold ON THE GRAPH.  It does NOT mean the circuit works.

It cannot see:  component values being right;  whether any named part exists or
is procurable;  loop stability;  layout, clearance or creepage (those are DRC
and the generator invariants);  thermal behaviour;  whether a [recalled]
datasheet fact is true;  and -- most important -- whether a TIER-C borrowed
pinout (board_spec_parts.py) actually matches the fitted part.  A wrong TIER-C
pin map produces a netlist that passes every check here and a board that is
perfectly, self-consistently wrong.  That is what docs/PIN_MAPS.md is for.

=============================================================================
1.  NET NAMING CONVENTION  (extends docs/INTERFACES.md section 2.1)
=============================================================================
UPPER_SNAKE.  No spaces.  No '/' inside a name (KiCad reads '/' as a hierarchy
path).  `_P` / `_N` suffix means POSITIVE / NEGATIVE MODULE, never a differential
pair.  A leading lowercase 'n' means active-low (`nON_P`, `nARM`, `nOVP`).

  GND                       the one bare net name on the board: it comes from a
                            power symbol, so KiCad emits it WITHOUT a leading '/'.
  +12V +5V_MOD +5V_A        rails.  These are LOCAL LABELS, so KiCad emits them
  +3V3 +3V3_A +5V_COIL      as '/+5V_MOD' etc.  See the glob trap below.
  VCLAMP VREF_2V500         precision rails.
  VREF_2V048 VREF_2V048_SH

  HV_*        ANY node that can exceed 60 V carries an HV_ prefix.  The suffix
              after HV_ is the CLEARANCE DOMAIN and it is what the netclass
              globs key on:
                 HV_POS*      positive module branch   (module pin 6 -> K1)
                 HV_NEG*      negative module branch   (module pin 6 -> K2)
                 HV_OUT_A*    output A bus / terminal
                 HV_OUT_B*    output B bus / terminal
                 HV_X*        mode-switch node X  (K2 NO side)
                 HV_M*        mode-switch node M  (the split-stress node)
                 HV_SW_G*     mode-switch grounded-common pole, via R_G
  HVDIV_*     interior nodes of every HV divider / bleed string, and the two
              driven guard rings.  Named HVDIV_<STRING>_<sub>_N<k> so that the
              generator can recover each node's POSITION in the string and
              therefore its potential (see section 9.1 of MONITOR_AND_BLEED.md).
  MON_* COLD_* BRANCH_*      measurement and permissive signals.
  ARM SEL PERMIT_* INTLK     interlock domain.
  Everything else            Default.

  *** THE GLOB TRAP, STATED ONCE ***
  KiCad matches netclass patterns against the FULL net name.  A local label on
  the root sheet produces '/HV_POS', not 'HV_POS'.  A pattern written as
  'HV_POS*' therefore matches NOTHING and the net silently falls into Default at
  0.2 mm clearance -- on a 1 kV net.  Every non-power-symbol pattern in this file
  is written '*/HV_POS*'.  effective_net_name() below reproduces KiCad's naming
  and assert_netclass_coverage() checks the globs against THAT, not against the
  bare name.  This was verified against the Phase-0 netlist, which emits
  '/IN', '/MID' and bare 'GND'  [verified-artifact].

=============================================================================
2.  WHICH DOCUMENT GOVERNS WHICH PART OF THIS NETLIST
=============================================================================
Four design documents were written concurrently.  Where they overlap this file
records which one it followed and why.  Disagreements are NOT silently resolved.

  HV routing, relays, mode switch, interlock gate algebra
        -> docs/design/COMBINER_DESIGN.md            GOVERNS
  Set-point path, clamp, DAC, VSET pin network
        -> docs/design/SETPOINT_PATH.md              GOVERNS
  Monitor dividers, COLD chain, branch monitors, bleed VALUES
        -> docs/design/MONITOR_AND_BLEED.md          GOVERNS
  ESP32 variant, GPIO map, power tree, ARM chain terms, connectors
        -> docs/design/CONTROLLER_AND_POWER.md       GOVERNS
  Component dict shape, netclass field list, refdes prefixes, SA-* assertions
        -> docs/INTERFACES.md                        GOVERNS

=============================================================================
3.  DEVIATIONS AND UNRESOLVED CROSS-DOCUMENT CONFLICTS  -- read before G1
=============================================================================
D-1  BLEED TOPOLOGY AND VALUE.  COMBINER_DESIGN.md section 5.1 says the
     module-side bleeds sit "upstream of the relay" at 40 MOhm, and its
     sections 5.2/5.3 sum BOTH the module-side and the output-side bleed onto
     the same live node (5.00 % + 5.00 %; 17.24 MOhm closed).  But its OWN
     block diagram (section 2) draws "K1 NC -> R_bleed_POS -> GND", i.e. the
     module bleed on the NORMALLY-CLOSED CONTACT, and MONITOR_AND_BLEED.md
     section 6 REQUIRES that arrangement, because the weld self-test raises a
     PARKED module to 200-1000 V and needs it to actually get there (a 50 uA
     NC bleed lets it; a hard park would not).  The two readings cannot both be
     true.  THIS FILE BUILDS THE NC-CONTACT ARRANGEMENT (both block diagrams
     agree on it, and it is the one the self-test needs), WITH
     MONITOR_AND_BLEED.md's 20.0 MOhm value.  Consequence to propagate:
     COMBINER_DESIGN.md section 5.3's "relay closed = 17.24 MOhm" row is then
     OPTIMISTIC BY ~1.76x, because with the relay closed the module bleed is
     disconnected and only the output-node strings remain.  REPORTED, NOT
     PATCHED (CLAUDE.md rule 1 -- fix the generator, and here the generator is
     a document).  G1 must adjudicate.

D-2  COLD 2-of-2 AND NOT IMPLEMENTED.  MONITOR_AND_BLEED.md section 5.4
     proposes COLD_x = (S3 window) AND (a second comparator on the S2 tap),
     which is strictly safer.  It also states that this REQUIRES rewording the
     FROZEN assertion SA-8 ("the COLD divider shares no component with the
     invariant-(c) monitor divider") and that the decision is G1's, not its own.
     Implementing it here would silently break a frozen assertion, so this file
     builds the SA-8-compliant dedicated-S3 window only.  The AND is carried
     forward as OPEN, not dropped.

D-3  COLD WINDOW CENTRE MOVED FROM 2.048 V TO 1.950 V.  MONITOR_AND_BLEED.md
     section 5.2 puts the COLD node at 2.04603 V at HV = 0 and the window
     centre at REF3020's 2.048 V.  Those two numbers cannot BOTH be realised
     while the window thresholds come from a 2.048 V-topped resistor string --
     a divider from 2.048 V can only produce voltages BELOW 2.048 V, so the
     upper threshold (centre + 46 mV = 2.094 V) is unreachable without
     importing the OTHER reference, which is exactly what section 5.5 forbids.
     Resolved by moving the node's offset resistor from 1.24 MOhm to 1.58 MOhm
     (node0 ~ 1.950 V) and taking both thresholds from a REF3020-topped string.
     The reference-separation property (section 5.5) is preserved exactly.
     VALUES ARE NOMINAL-E96 AND HAVE NOT BEEN THROUGH A NUMBERS PROBE.

D-4  ESP32 GPIO REMAP.  CONTROLLER_AND_POWER.md section 2.3 puts MODE_A_RB on
     GPIO33 and MODE_B_RB on GPIO34.  **The ESP32-S3-WROOM-1 module symbol in
     KiCad 10.0.3 brings out IO35, IO36, IO37 and IO38 but has NO module pin
     for IO33 or IO34** [verified-artifact, RF_Module.kicad_sym].  The map is
     therefore shifted: MODE_A_RB -> IO35, MODE_B_RB -> IO36, OVP_RB -> IO37,
     nOVP_CLR -> IO38, nALERT_ADC -> IO47, LED_NET -> IO48.  The claim that the
     module lacks IO33/34 pads rests on the KiCad symbol, NOT on a datasheet
     read; confirm at G1 before layout.  The SAFETY property that matters is
     preserved and asserted: nothing HV-relevant sits on a strapping pin.

D-5  W5500 AND CP2102N ARE OUT OF SCOPE FOR spec_version 1.  Their 48- and
     29-pin reference designs contain no HV safety content and could only be
     authored from recall this session, which is precisely the
     "highest-consequence, lowest-feedback" work this task warns about.  The
     board-boundary nets are real and are brought to two headers (J_ETH, J_PROG)
     exactly as CONTROLLER_AND_POWER.md section 9.4 already specifies for the
     programming header.  CONTROLLER_AND_POWER.md section 1.3 specifies an
     ON-BOARD W5500; building it is G1 work and is recorded as open.

D-6  INTERFACES.md section 2.2 states "5 V only -- there is no +12 V rail".
     CONTROLLER_AND_POWER.md delta-1 changed the input to a single 12 V feed.
     This file follows CONTROLLER_AND_POWER.md and adds a +12V netclass; the
     INTERFACES.md line is stale and needs a G1 edit.

-----------------------------------------------------------------------------
D-7 .. D-10 ADDED 2026-07-23 BY THE SESSION-2 VERIFICATION PASS.
     Three independent skeptics mutation-tested this file against the claim
     "its domain safety assertions genuinely CAN fail, and its pin numbering
     agrees with the generated symbol and footprint".  RESULT: 2 of 3 refuted.
     The assertions are NOT vacuous -- 13/13 in-scope mutations fired, naming
     the exact state and mode -- but FOUR ESCAPE ROUTES were found, and the
     footprint half of the claim is unsupported.  REPORTED, NOT PATCHED: fixing
     them changes the checker's behaviour and that is a G1 decision, not a
     silent edit.  Every item below is a G1 ACTION.
-----------------------------------------------------------------------------

D-7  assert_a_no_shared_output_node() IS VACUOUS IN PSEUDO-BIPOLAR -- the mode
     the invariant is actually at risk in.  It filters `if not (pp and pn):
     continue`, and PERMIT_P . PERMIT_N == ARM . MODE_UNI by construction, so
     PB states are ALL deleted before evaluation.  Verified by three skeptics
     against this file's OWN reachable_states()/_adjacency(): "modes surviving
     the assertion-(a) filter = ['UNI']", 4 states, zero PB states; and
     "PB, K1=1 K2=1: HV_POS->HV_OUT_A True AND HV_NEG->HV_OUT_A True".
     => The assertion CANNOT detect the F-15 welded-reed case it is nominally
     the proof against.  FIX: drop the pp/pn filter and assert on GALVANIC
     reachability, treating an unpowered-but-connected module as a violation
     (its HV pin is then reverse-driven to the opposite kV, and PART-27 reverse
     tolerance is unpublished -- COMBINER_DESIGN F-31).  Until then, state
     plainly that assertion (a) covers UNIPOLAR ONLY.

D-8  assert_a_mode_origin() HAS THREE BYPASSES, each of which hands firmware
     the mode permissive while check() stays CLEAN (exit 0, no orphan nets):
       (i)  it allow-lists PartClass R_LV / HDR* / TP / C_LV unconditionally
            and never follows the resistor's FAR end.  Re-terminating both
            MODE_A pull-downs (RMA1, RMA2 pin 2) on an ESP32 GPIO passes.  So
            does feeding MODE_A through header J6.
       (ii) it does `if cls.startswith("74"): continue`, commented "outputs are
            in `driver`".  THAT COMMENT IS FALSE: only 8 of the 20 74-series
            refs are in LOGIC (U30,31,32,33,34,36,38,43).  U6, U35, U37, U45,
            U46, U47, U48, U49, U51, U52 are invisible to `driver`, so their
            OUTPUTS are silently skipped.  ESP32 ARM_EN -> U47 (74LVC14) ->
            MODE_A passes.  U45 (74LVC165) -> MODE_A passes.
       (iii) `esp_out` is a HARD-CODED list of 6 net names; ~25 other U50 nets
            are excluded from the reachability walk entirely.
     FIX: derive esp_out from the ESP32 component's pins, follow two-terminal
     passives to their far end, and treat any non-LOGIC part as opaque rather
     than transparent.

D-9  TWO MORE ASSERTIONS ARE WEAKER THAN THEY READ.
     (a) hv_energisable_nets() is NOT derived -- it is parameterised by two
         hand-lists (ROUTING_RESISTORS, 4 refs, and HV_STRINGS).  Any HV net
         outside both is INVISIBLE, so an unbled HV net passes assertion (b).
         Two HV resistors bridging HV_OUT_A -> a new net HV_M2 were confirmed
         to pass full check() with no bleed path to GND.  Its docstring's claim
         that deriving the set "is what keeps assertion (b) honest" is wrong.
     (b) assert_c_monitor_independence() never compares monitor A against
         monitor B.  Merging them passes.  (It also passes only because
         VREF_2V500 is whitelisted in ASSERTION_C_ALLOWED_SHARED_NETS -- see
         MONITOR_AND_BLEED.md correction M-3.)

D-10 THE FOOTPRINT HALF OF THE PIN-NUMBERING CLAIM IS UNSUPPORTED, AND 11 PARTS
     NAME FOOTPRINTS THAT DO NOT EXIST.  `grep -c kicad_mod board_spec.py` = 0:
     this file NEVER opens a .kicad_mod.  Symbol<->spec agreement is real and
     checked both directions; symbol<->FOOTPRINT agreement is checked for
     iseg_APS_THT (pads 1..7) only by skeptics' own parsers, not by this file.
     Footprints named here that exist in NEITHER the KiCad 10.0.3 tree NOR this
     repo: Relay_THT:Relay_Pickering_Series67 (K1,K2,K3,K4),
     Relay_THT:Relay_DPDT_Panasonic_TQ (KS), Inductor_SMD:L_Bourns_SRP7028A
     (L1,L2), Package_SO:MSOP-12-1EP... (U12), Package_SO:VSSOP-10_3x3mm...
     (UADCA,UADCB), and the CK KMR2 switch (SWB).  PIN_MAPS.md flags "DOES NOT
     EXIST" for K1..K4 ONLY.  K1/K2 -- the two HV routing relays -- therefore
     have no footprint for their pin numbering to agree WITH.  G1 must generate
     these footprints and add a symbol<->footprint pad-set cross-check to this
     file.  The 9-item "not structurally expressible" list at the end of main()
     does not currently mention D-7..D-10.

=============================================================================
"""

import os
import re
import sys
import uuid
import itertools

from board_spec_parts import (PARTS, part, derate_of, RATING_DERATE,
                              LV_MAX, TOUCH_SAFE_V)

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIR = os.path.join(HERE, "lib")
KICAD_SYMBOLS = "C:/Program Files/KiCad/10.0/share/kicad/symbols"

PROJECT = "hvctl"
SPEC_VERSION = 1
REV = "A"

# Fixed namespace -> deterministic identity.  uuid5 over a semantic key, NEVER
# uuid4: "regenerate and git diff" is then a free regression test.
NS = uuid.UUID("b3d9a7c1-6e42-5f08-9a1d-2c7e4b8f0a35")


def sym_uuid(ref):
    """Deterministic schematic symbol UUID for `ref`.  The PCB generator must
    use THIS function for each footprint's (path ...) so the schematic<->board
    linkage is reproducible and diffable."""
    return str(uuid.uuid5(NS, "%s/symbol/%s" % (PROJECT, ref)))


def pin_uuid(ref, pad):
    return str(uuid.uuid5(NS, "%s/pin/%s.%s" % (PROJECT, ref, pad)))


def net_uuid(net):
    return str(uuid.uuid5(NS, "%s/net/%s" % (PROJECT, net)))


def root_uuid():
    return str(uuid.uuid5(NS, "%s/root" % PROJECT))


# ===========================================================================
# 4.  NET CLASSIFICATION
# ===========================================================================
# The one net whose KiCad name is BARE (it comes from a power symbol).
POWER_SYMBOL_NETS = {"GND"}


def effective_net_name(net):
    """Reproduce the name KiCad will emit.  Power-symbol nets are bare; every
    other named net on the root sheet gets a leading '/'.  Netclass globs MUST
    be matched against this, not against the bare name."""
    return net if net in POWER_SYMBOL_NETS else "/" + net


def _glob_to_re(pat):
    return re.compile("^" + "".join(".*" if c == "*" else re.escape(c) for c in pat) + "$")


# --- the HV domains, in match order.  Longest/most specific first. ----------
HV_DOMAINS = ("HV_OUT_A", "HV_OUT_B", "HV_POS", "HV_NEG", "HV_X", "HV_M", "HV_SW_G")


def is_hv_net(net):
    """True for any net that can exceed the touch-safe threshold."""
    return net.startswith("HV_") or net.startswith("HVDIV_")


def hv_domain_of(net):
    """Which clearance domain an HV net belongs to, or None.

    HVDIV_ nets carry their domain in the string id, e.g. HVDIV_MONA_a_N3 ->
    the string table says which node it hangs off."""
    if net.startswith("HVDIV_"):
        sid = net.split("_")[1]
        return HV_STRINGS[sid]["domain"] if sid in HV_STRINGS else None
    for d in HV_DOMAINS:
        if net == d or net.startswith(d + "_"):
            return d
    return None


def is_analog_net(net):
    return net in ANALOG_NETS or net.startswith("MON_") or net.startswith("VSET_") \
        or net.startswith("DAC_") or net in ("VCLAMP", "VREF_2V500", "VREF_2V048",
                                             "VREF_2V048_SH")


def is_digital_net(net):
    return not is_hv_net(net) and not is_analog_net(net) and net not in RAILS


RAILS = {"GND", "+12V", "+12V_IN", "+12V_F", "+5V_MOD", "+5V_A", "+3V3", "+3V3_A"}

ANALOG_NETS = {
    "VCLAMP", "VCLAMP_STAR", "VCLAMP_FB", "VCLAMP_SENSE", "VREF_2V500",
    "VREF_2V048", "VREF_2V048_SH", "REF_NR",
    "COLD_TH_HI", "COLD_TH_LO", "CLAMP_TH_HI", "CLAMP_TH_LO", "VSET_TH",
    "RAIL5V_DIV", "OVP_TH_AH", "OVP_TH_AL", "OVP_TH_BH", "OVP_TH_BL",
}

# ===========================================================================
# 5.  NETCLASSES -- ALL 17 KiCad-10 FIELDS, INCLUDING THE SCHEMATIC ONES
# ===========================================================================
# A PCB-only netclass silently breaks eeschema connectivity for every net in
# it, and `kicad-cli` NEVER reads .kicad_pro, so no headless check would ever
# notice.  (ENVIRONMENT.md section 3.3; bootstrap section V.3; NUM-05.)
C_HV = 7.5          # mm, single-ended.  [unverified-primary] NUM-01/NUM-02.
C_HV_PAIR = 15.0    # mm, pairwise -- NOT expressible as a netclass, see .kicad_dru


def _nc(name, clearance, track, patterns, wire_width=6, notes=""):
    return {
        "name": name,
        "patterns": list(patterns),
        # ---- PCB fields
        "clearance": clearance,
        "track_width": track,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "diff_pair_width": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        # ---- SCHEMATIC fields.  Omitting ANY of these breaks eeschema.
        "wire_width": wire_width,
        "bus_width": 12,
        "line_style": 0,
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        # ---- bookkeeping
        "priority": 0,
        "notes": notes,
    }


NETCLASS_FIELDS_REQUIRED = (
    "clearance", "track_width", "via_diameter", "via_drill",
    "microvia_diameter", "microvia_drill",
    "diff_pair_width", "diff_pair_gap", "diff_pair_via_gap",
    "wire_width", "bus_width", "line_style",
    "schematic_color", "pcb_color", "name", "priority", "patterns",
)


def netclasses():
    return {
        "HV_POS":   _nc("HV_POS", C_HV, 0.5, ["*/HV_POS*"],
                        notes="positive module HV pin -> R_S_P -> K1. 1000 V."),
        "HV_NEG":   _nc("HV_NEG", C_HV, 0.5, ["*/HV_NEG*"],
                        notes="negative module HV pin -> R_S_N -> K2. 1000 V."),
        "HV_OUT_A": _nc("HV_OUT_A", C_HV, 0.5, ["*/HV_OUT_A*"],
                        notes="output A: combined pseudo-bipolar OR positive unipolar."),
        "HV_OUT_B": _nc("HV_OUT_B", C_HV, 0.5, ["*/HV_OUT_B*"],
                        notes="output B: grounded in pseudo-bipolar, negative in unipolar."),
        "HV_X":     _nc("HV_X", C_HV, 0.5, ["*/HV_X*"],
                        notes="mode-switch node X (K2 NO). Carries -1000 V while "
                              "HV_OUT_A carries +1000 V in unipolar => a PERMANENT "
                              "2000 V pair. New pairwise .kicad_dru rule required."),
        "HV_M":     _nc("HV_M", C_HV, 0.5, ["*/HV_M*"],
                        notes="mode-switch intermediate node M. Exists ONLY to split "
                              "the 2000 V stress inside the switch into two 1000 V "
                              "gaps (COMBINER_DESIGN 3.2). Grounded by S3 in unipolar."),
        "HV_SW_G":  _nc("HV_SW_G", C_HV, 0.5, ["*/HV_SW_G*"],
                        notes="S3 common, GND through R_G. HV-classed because an S3 "
                              "weld or an R_G open puts it at full output."),
        "HV_SENSE": _nc("HV_SENSE", C_HV, 0.25, ["*/HVDIV_*"],
                        notes="divider taps, string interior nodes and the two DRIVEN "
                              "guard rings. TRAP (MONITOR_AND_BLEED 9.1): a netclass "
                              "clearance is a per-net minimum against ALL copper, so "
                              "7.5 mm here forces adjacent 100 V string nodes 7.5 mm "
                              "apart and stretches the string ~10x, multiplying the "
                              "leakage area that dominates the error budget. This MUST "
                              "be relaxed by a generator invariant that places each "
                              "sub-string collinearly in electrical order; DRC has no "
                              "'adjacent in string' predicate and a pattern rule is "
                              "UNSAFE (both ends of a string match the same pattern "
                              "and are 800 V apart)."),
        "PWR":      _nc("PWR", 0.25, 0.6,
                        ["*/+12V*", "*/+5V*", "*/+3V3*", "*/VREF*", "*/VCLAMP*",
                         "*/VIN_*", "*/COIL_*"], wire_width=8,
                        notes="rails. +12V added per CONTROLLER_AND_POWER delta-1; "
                              "INTERFACES.md 2.2's 'there is no +12 V rail' is stale."),
        "Default":  _nc("Default", 0.2, 0.25, ["*"], notes="everything else, incl. GND"),
    }


# ===========================================================================
# 6.  HV STRING TABLE
# ===========================================================================
# Every bleed and every divider top leg is TWO PARALLEL STRINGS of series
# elements (NUM-09 / SA-9): a single open element then costs a factor, not the
# path.  The table is data so that (a) the elements are generated rather than
# typed, (b) every interior node's POTENTIAL is derivable from its position,
# and (c) the per-element working voltage is checkable against the package
# rating instead of being asserted in prose.
#
#   sid       -> string id, appears in every interior net name
#   top       -> the HV net the string hangs off
#   bot       -> where the string lands (GND for a bleed, a tap for a divider)
#   n_series  -> elements per sub-string
#   n_par     -> parallel sub-strings (2 everywhere, per NUM-09)
#   r_elem    -> ohms per element
#   pkg       -> part class, carries the package voltage rating
#   vmax      -> |V| the TOP of this string can reach, volts
#   role      -> bleed | monitor | cold | branch | stub
#   domain    -> clearance domain for the interior nodes
HV_STRINGS = {
    # ---- permanent output-node bleeds (S1).  20.0 MOhm = 2 || (2 x 20.0 M).
    "BLDA": dict(top="HV_OUT_A", bot="GND", n_series=2, n_par=2, r_elem=20.0e6,
                 pkg="R_HV_2512", vmax=1000.0, role="bleed", domain="HV_OUT_A",
                 note="MONITOR_AND_BLEED 7.2: R = Vnom/(f.Inom), f = 0.10."),
    "BLDB": dict(top="HV_OUT_B", bot="GND", n_series=2, n_par=2, r_elem=20.0e6,
                 pkg="R_HV_2512", vmax=1000.0, role="bleed", domain="HV_OUT_B"),
    # ---- module-branch bleeds (S4), on the relay NC contact.  See D-1.
    "BLDP": dict(top="HV_POS_PARK", bot="GND", n_series=2, n_par=2, r_elem=20.0e6,
                 pkg="R_HV_2512", vmax=1000.0, role="bleed", domain="HV_POS",
                 note="on K1 NC. Engaged whenever K1 is de-energised, which is "
                      "the unpowered default state."),
    "BLDN": dict(top="HV_NEG_PARK", bot="GND", n_series=2, n_par=2, r_elem=20.0e6,
                 pkg="R_HV_2512", vmax=1000.0, role="bleed", domain="HV_NEG"),
    # ---- mode-switch stub bleeds.  Cover the SAFE detent, where X and M are
    #      isolated from everything else by the switch itself.
    "BLDX": dict(top="HV_X", bot="GND", n_series=2, n_par=2, r_elem=400.0e6,
                 pkg="R_HV_2512", vmax=1000.0, role="stub", domain="HV_X"),
    "BLDM": dict(top="HV_M", bot="GND", n_series=2, n_par=2, r_elem=400.0e6,
                 pkg="R_HV_2512", vmax=1000.0, role="stub", domain="HV_M"),
    # ---- invariant-(c) independent monitors (S2).  200 MOhm = 2 || (10 x 40 M).
    #      N = 10 is set by VCR (goes as 1/N) and by the 1206 pad-gap screen at
    #      100 V/element, NOT by the resistance.
    "MONA": dict(top="HV_OUT_A", bot="HVDIV_TAP_A", n_series=10, n_par=2, r_elem=40.0e6,
                 pkg="R_HV_1206", vmax=1000.0, role="monitor", domain="HV_OUT_A"),
    "MONB": dict(top="HV_OUT_B", bot="HVDIV_TAP_B", n_series=10, n_par=2, r_elem=40.0e6,
                 pkg="R_HV_1206", vmax=1000.0, role="monitor", domain="HV_OUT_B"),
    # ---- COLD permissive (S3).  1.00 GOhm = 2 || (2 x 1.00 G).  Deliberately
    #      5x lighter than the monitor: it needs 20:1 discrimination, not 0.03 %.
    "CLDA": dict(top="HV_OUT_A", bot="HVDIV_COLD_A", n_series=2, n_par=2, r_elem=1.0e9,
                 pkg="R_HV_2512", vmax=1000.0, role="cold", domain="HV_OUT_A"),
    "CLDB": dict(top="HV_OUT_B", bot="HVDIV_COLD_B", n_series=2, n_par=2, r_elem=1.0e9,
                 pkg="R_HV_2512", vmax=1000.0, role="cold", domain="HV_OUT_B"),
    # ---- per-branch monitors (S5), UPSTREAM of the relays.  These are what
    #      turn the weld self-test from a detector with a silent false-pass
    #      into a real one (COMBINER_STUDY F-2).
    "BRNP": dict(top="HV_POS", bot="HVDIV_BR_P", n_series=2, n_par=2, r_elem=1.0e9,
                 pkg="R_HV_2512", vmax=1000.0, role="branch", domain="HV_POS"),
    "BRNN": dict(top="HV_NEG", bot="HVDIV_BR_N", n_series=2, n_par=2, r_elem=1.0e9,
                 pkg="R_HV_2512", vmax=1000.0, role="branch", domain="HV_NEG"),
}

SUBSTRING_IDS = ("a", "b")


def string_node_net(sid, sub, k):
    """Interior node k of sub-string `sub` of string `sid` (1-based, k < n)."""
    return "HVDIV_%s_%s_N%d" % (sid, sub, k)


def string_node_potential(sid, k):
    """|V| at interior node k, counting from the TOP.  Node k sits below k
    elements, so it is at vmax * (n - k) / n."""
    s = HV_STRINGS[sid]
    return s["vmax"] * (s["n_series"] - k) / float(s["n_series"])


def element_working_voltage(sid):
    s = HV_STRINGS[sid]
    return s["vmax"] / float(s["n_series"])


# ===========================================================================
# 7.  CONTACT MODEL -- what is connected to what, in each mechanical state
# ===========================================================================
# This is what makes domain assertions (a) and (b) STRUCTURAL rather than
# prose.  Each entry maps a mechanical state to the pin pairs that are shorted.
#
#   K1, K2 : Pickering 1 Form C.  De-energised => COM-NC.  Energised => COM-NO.
#   SW1    : the three-position PANEL mode selector, PB . SAFE . UNI.
#            NON-SHORTING: in SAFE every HV pole is open (SW-R2).
CONTACT_MODEL = {
    "K1": {"NE": [("11", "12")], "E": [("11", "14")]},
    "K2": {"NE": [("11", "12")], "E": [("11", "14")]},
    "KS": {"NE": [("11", "12"), ("21", "22")], "E": [("11", "14"), ("21", "24")]},
    # SW_SPDT: pin 2 is the COMMON.  pin 1 = PB throw, pin 3 = UNI throw.
    "SW1A": {"PB": [("2", "1")], "SAFE": [], "UNI": [("2", "3")]},
    "SW1C": {"PB": [("2", "1")], "SAFE": [], "UNI": [("2", "3")]},
    # SW_SPST poles: closed only in the named position(s).
    "SW1B": {"PB": [("1", "2")], "SAFE": [], "UNI": []},
    "SW1D": {"PB": [("1", "2")], "SAFE": [], "UNI": []},
    "SW1E": {"PB": [], "SAFE": [], "UNI": [("1", "2")]},
    "SW1F": {"PB": [], "SAFE": [], "UNI": [("1", "2")]},
    "SW1G": {"PB": [], "SAFE": [], "UNI": [("1", "2")]},
}
RELAY_STATES = ("NE", "E")
MODE_STATES = ("PB", "SAFE", "UNI")

# Components that carry ROUTING current (as opposed to a bleed or a divider).
# Assertion (a) walks ONLY these: a 20 MOhm bleed is not a route to an output.
ROUTING_RESISTORS = {"R_S_P", "R_S_N", "R_M1", "R_G"}


# ===========================================================================
# 8.  LOGIC MODEL -- the interlock gate array, as evaluable boolean structure
# ===========================================================================
# ref -> (function, [input pads in order], output pad)
# Functions: AND, OR, NAND, NOR, XOR, NOT, BUF.
# The gate array is evaluated exhaustively over its primary inputs by
# assert_mode_aware_interlock().  Rewiring ONE gate input makes that assertion
# fail -- which is the point.
LOGIC = {
    # ARM chain: 8-input NAND, 8th input tied high.
    "U30": ("NAND", ["1", "2", "3", "4", "5", "6", "11", "12"], "8"),
    # 74HCT14 hex inverter
    "U31a": ("NOT", ["1"], "2"),
    "U31b": ("NOT", ["3"], "4"),
    "U31c": ("NOT", ["5"], "6"),
    "U31d": ("NOT", ["9"], "8"),
    "U31e": ("NOT", ["11"], "10"),
    "U31f": ("NOT", ["13"], "12"),
    # 74HCT86 quad XOR
    "U32a": ("XOR", ["1", "2"], "3"),
    "U32b": ("XOR", ["4", "5"], "6"),
    "U32c": ("XOR", ["9", "10"], "8"),
    "U32d": ("XOR", ["12", "13"], "11"),
    # 74HCT08 quad AND (interlock core)
    "U33a": ("AND", ["1", "2"], "3"),
    "U33b": ("AND", ["4", "5"], "6"),
    "U33c": ("AND", ["9", "10"], "8"),
    "U33d": ("AND", ["12", "13"], "11"),
    # 74HCT32 quad OR
    "U34a": ("OR", ["1", "2"], "3"),
    "U34b": ("OR", ["4", "5"], "6"),
    "U34c": ("OR", ["9", "10"], "8"),
    "U34d": ("OR", ["12", "13"], "11"),
    # 74HCT03 open-drain NAND -> /ON, and the KS latch-enable pair
    "U36a": ("NAND", ["1", "2"], "3"),
    "U36b": ("NAND", ["4", "5"], "6"),
    "U36c": ("NAND", ["9", "10"], "8"),
    "U36d": ("NAND", ["12", "13"], "11"),
    # 74HCT08 #2 : EN_HB and the COLD ANDs
    "U38a": ("AND", ["1", "2"], "3"),
    "U38b": ("AND", ["4", "5"], "6"),
    "U38c": ("AND", ["9", "10"], "8"),
    "U38d": ("AND", ["12", "13"], "11"),
    # 74HCT08 #3 : the coil-rail permissive (C-1)
    "U43a": ("AND", ["1", "2"], "3"),
    "U43b": ("AND", ["4", "5"], "6"),
}

# Nets the logic evaluator treats as constants.
LOGIC_CONSTANTS = {"+5V_MOD": 1, "GND": 0, "+3V3": 1}


# ===========================================================================
# 9.  THE NETLIST
# ===========================================================================
_COMPONENTS = []
_SEEN_REFS = set()
_NETS_CACHE = {}          # id(board) -> nets;  the board dict itself stays
_STATES_CACHE = {}        # id(board) -> states; EXACTLY the INTERFACES.md shape


def C(ref, pclass, val, pins, nc=(), dnp=False, notes="", extra=None):
    """Append one component in the INTERFACES.md section 1.1 shape."""
    if ref in _SEEN_REFS:
        raise ValueError("duplicate refdes %s" % ref)
    _SEEN_REFS.add(ref)
    p = part(pclass)
    fields = {
        "MPN": val,
        "MPN_STATUS": p["status"],
        "Mfr": p["mfr"],
        "Datasheet": p["cite"],
        "Assembly": "panel" if p["fp"] == "" else ("hand" if pclass.startswith("ISEG")
                                                   or pclass == "R_HV_AXIAL" else "smt"),
        "PartClass": pclass,
        "Tier": p["tier"],
        "V_RATING": "%.0f" % p["vmax"],
        "Notes": notes,
    }
    if extra:
        fields.update(extra)
    full = dict(pins)
    for pad in nc:
        full[pad] = None
    _COMPONENTS.append({
        "ref": ref, "sym": p["sym"], "val": val, "fp": p["fp"],
        "pins": full, "dnp": dnp, "nc": list(nc), "fields": fields,
    })
    return ref


def R(ref, value, a, b, pclass="R_LV", notes="", dnp=False):
    return C(ref, pclass, value, {"1": a, "2": b}, notes=notes, dnp=dnp)


def CAP(ref, value, a, b, pclass="C_LV", notes="", dnp=False):
    return C(ref, pclass, value, {"1": a, "2": b}, notes=notes, dnp=dnp)


def build_hv_string(sid):
    """Emit the 2 x n elements of one HV string.  Returns the refs."""
    s = HV_STRINGS[sid]
    refs = []
    for sub in SUBSTRING_IDS[:s["n_par"]]:
        prev = s["top"]
        for k in range(1, s["n_series"] + 1):
            nxt = s["bot"] if k == s["n_series"] else string_node_net(sid, sub, k)
            ref = "R%s%s%d" % (sid, sub.upper(), k)
            v = s["r_elem"]
            val = ("%.0fM" % (v / 1e6)) if v < 1e9 else ("%.2fG" % (v / 1e9))
            refs.append(R(ref, val, prev, nxt, pclass=s["pkg"],
                          notes="%s string %s element %d/%d; working %.0f V/element"
                                % (s["role"], sub, k, s["n_series"],
                                   element_working_voltage(sid))))
            prev = nxt
    return refs


def _build():
    del _COMPONENTS[:]
    _SEEN_REFS.clear()

    # -------------------------------------------------- power symbols / flags
    C("#PWR01", "PWR_GND", "GND", {"1": "GND"},
      notes="the one bare-named net on the board")
    C("#FLG01", "PWR_FLAG", "PWR_FLAG", {"1": "GND"},
      notes="without it ERC raises power_pin_not_driven on GND")
    C("#FLG02", "PWR_FLAG", "PWR_FLAG", {"1": "+12V"},
      notes="the input rail has no power-OUTPUT pin behind it")

    # ================================================== 9.1  INPUT + POWER TREE
    C("J1", "BARREL", "12V 2.0A", {"1": "+12V_IN", "2": "GND"},
      notes="2.1x5.5 mm LOCKING jack. Losing input power is SAFE.")
    R("F1", "PTC 2A", "+12V_IN", "+12V_F", pclass="PFUSE")
    C("Q1", "Q_PMOS", "reverse-block P-FET",
      {"1": "Q1_GATE", "2": "+12V_F", "3": "+12V"},
      notes="source to the jack, drain to the board: body diode blocks reverse")
    R("R1", "100k", "Q1_GATE", "GND")
    C("D2", "D_ZEN", "BZX84C12", {"1": "+12V_F", "2": "Q1_GATE"},
      notes="clamps Vgs of Q1")
    C("D1", "D_TVS", "SMBJ15A", {"1": "+12V", "2": "GND"},
      notes="unidirectional TVS: pin 1 is the cathode side")
    CAP("C1", "470u/25V", "+12V", "GND", pclass="C_BULK")
    CAP("C2", "10u/25V", "+12V", "GND")

    # ---- U10: 12 V -> 5.00 V, the module / interlock rail
    C("U10", "LMR33620", "LMR33620",
      {"1": "GND", "2": "+12V", "3": "+12V", "5": "FB_5V", "6": "VCC_5V",
       "7": "BOOT_5V", "8": "SW_5V", "9": "GND"}, nc=["4"],
      notes="EN tied to VIN; PG unused")
    R("L1", "10uH", "SW_5V", "+5V_MOD", pclass="L_PWR")
    CAP("C3", "100n", "SW_5V", "BOOT_5V")
    CAP("C4", "1u", "VCC_5V", "GND")
    R("R2", "100k 1%", "+5V_MOD", "FB_5V")
    R("R3", "23.7k 1%", "FB_5V", "GND")
    CAP("C5", "47u/16V", "+5V_MOD", "GND", pclass="C_BULK")
    CAP("C6", "47u/16V", "+5V_MOD", "GND", pclass="C_BULK")

    # ---- U11: 12 V -> 3.30 V, the digital rail
    C("U11", "LMR33620", "LMR33620",
      {"1": "GND", "2": "+12V", "3": "+12V", "5": "FB_3V3", "6": "VCC_3V3",
       "7": "BOOT_3V3", "8": "SW_3V3", "9": "GND"}, nc=["4"])
    R("L2", "10uH", "SW_3V3", "+3V3", pclass="L_PWR")
    CAP("C7", "100n", "SW_3V3", "BOOT_3V3")
    CAP("C8", "1u", "VCC_3V3", "GND")
    R("R4", "100k 1%", "+3V3", "FB_3V3")
    R("R5", "45.3k 1%", "FB_3V3", "GND")
    CAP("C9", "47u/16V", "+3V3", "GND", pclass="C_BULK")

    # ---- U12: 12 V -> 5.00 V LOW-NOISE analog rail.  Exists because OPA192's
    #      minimum supply is 4.5 V, so a quiet 5 V cannot be made from a 5 V
    #      input -- the whole reason the input became 12 V (delta-1).
    C("U12", "LT3045", "LT3045",
      {"1": "+12V", "2": "+12V", "3": "+12V", "4": "+12V", "6": "LT_ILIM",
       "8": "LT_SET", "9": "GND", "10": "+5V_A", "11": "+5V_A", "12": "+5V_A",
       "13": "GND"}, nc=["5", "7"],
      notes="PG/PGFB unused; SET resistor sets 5.00 V")
    R("R6", "50.0k 0.1%", "LT_SET", "GND", notes="LT3045 SET current x R = Vout")
    R("R7", "10k", "LT_ILIM", "GND")
    CAP("C10", "10u", "+5V_A", "GND")
    CAP("C11", "100n", "+5V_A", "GND")

    # ---- U13: 3.3 V analog for the ADCs
    C("U13", "LP5907", "LP5907-3.3",
      {"1": "+3V3", "2": "GND", "3": "+3V3", "5": "+3V3_A"}, nc=["4"])
    CAP("C12", "1u", "+3V3_A", "GND")

    # ---- rail supervisors: RAIL_OK is a wire-AND of three open-drain outputs
    C("U40", "TPS3701", "TPS3701", {"1": "RAIL_OK", "2": "GND", "3": "+5V_MOD",
                                    "4": "GND", "5": "+5V_MOD", "6": "RAIL_OK"},
      notes="4.62 / 5.38 V window on +5V_MOD; module Vin range is 4.5-5.5 V")
    C("U41", "TPS3701", "TPS3701", {"1": "RAIL_OK", "2": "GND", "3": "VCLAMP",
                                    "4": "GND", "5": "+5V_MOD", "6": "RAIL_OK"},
      notes="2.40 / 2.60 V window on the CLAMP rail; OV trips BEFORE the VSET "
            "comparator so a rail fault is diagnosed as a rail fault")
    C("U42", "TPS3701", "TPS3701", {"1": "RAIL_OK", "2": "GND", "3": "+5V_A",
                                    "4": "GND", "5": "+5V_MOD", "6": "RAIL_OK"},
      notes="4.60 / 5.40 V on +5V_A; below 4.5 V the monitor buffers are out of "
            "spec and the independent monitor cannot be trusted")
    R("R8", "10k", "RAIL_OK", "+5V_MOD", notes="ARCH-18 pair 1/2")
    R("R9", "10k", "RAIL_OK", "+5V_MOD", notes="ARCH-18 pair 2/2, >=5 mm away")

    # ================================================ 9.2  MODULE SUPPLY CHAIN
    # ARM -> Q_ARM -> K_S pole A -> per-module load switch -> ferrite -> module.
    # SA-6: each module's +VIN reaches it ONLY through the interlock element.
    C("U14", "TPS22918", "TPS22918", {"1": "+5V_MOD", "2": "GND", "3": "ARM",
                                      "6": "VIN_ARMED"}, nc=["4", "5"],
      notes="Q_ARM (C-1). Fail-safe-OPEN switch in the module supply rail.")
    C("U15", "TPS22918", "TPS22918", {"1": "+5V_MOD", "2": "GND", "3": "COIL_EN",
                                      "6": "+5V_COIL"}, nc=["4", "5"],
      notes="Q_COIL (C-1). Gated by EN_HB.INTLK.MODE_VALID, deliberately NOT by "
            "the full ARM -- a coil rail that dropped on every nOVP event would "
            "force a HOT BREAK on every trip (COMBINER_DESIGN 6.4).")
    C("KS", "RELAY_LV", "TQ2SA-5V",
      {"A1": "+5V_MOD", "A2": "KS_COIL_LO",
       "11": "VIN_ARMED", "14": "VIN_P_PRE", "12": "VIN_N_PRE",
       "21": "+5V_COIL", "24": "COIL_FEED_P", "22": "COIL_FEED_N"},
      notes="THE SINGLE ARMATURE. Pole A routes the only +VIN; pole B routes the "
            "only coil feed. In UNIPOLAR the panel switch's S6/S7 bridge AROUND "
            "it -- which is why a falsely-asserted MODE_UNI logic line cannot "
            "reach the forbidden state.")
    C("D3", "D_SCH", "1N4148W", {"1": "+5V_MOD", "2": "KS_COIL_LO"},
      notes="KS coil flyback")
    C("QKS", "Q_NMOS", "2N7002", {"1": "KS_SEL", "2": "GND", "3": "KS_COIL_LO"})
    R("R10", "100k", "KS_SEL", "GND", notes="ARCH-18 pair 1/2")
    R("R11", "100k", "KS_SEL", "GND", notes="ARCH-18 pair 2/2")

    C("U16", "TPS22918", "TPS22918", {"1": "VIN_P_PRE", "2": "GND", "3": "PERMIT_P",
                                      "6": "VIN_P_SW"}, nc=["4", "5"])
    C("U17", "TPS22918", "TPS22918", {"1": "VIN_N_PRE", "2": "GND", "3": "PERMIT_N",
                                      "6": "VIN_N_SW"}, nc=["4", "5"])
    R("FB1", "600R@100MHz", "VIN_P_SW", "VIN_P", pclass="FB")
    R("FB2", "600R@100MHz", "VIN_N_SW", "VIN_N", pclass="FB")
    CAP("C13", "22u/16V", "VIN_P", "GND", pclass="C_BULK",
        notes="PART-18: the datasheet MANDATES >=22 uF at each module +VIN")
    CAP("C14", "22u/16V", "VIN_N", "GND", pclass="C_BULK", notes="PART-18")
    CAP("C15", "1u", "VIN_P_PRE", "GND", notes="<=1 uF: keeps the K_S contact "
                                               "transfer out of a 22 uF inrush")
    CAP("C16", "1u", "VIN_N_PRE", "GND")

    # ==================================================== 9.3  THE HV MODULES
    C("U1", "ISEG_P", "AP010504P05",
      {"1": "VIN_P", "2": "VSET_P", "3": "GND", "4": "nON_P",
       "5": "VMON_P", "6": "HV_POS", "7": "GND"},
      notes="Vnom 1000 V, Inom 0.5 mA, Vin 5 V, Vref 2.5 V. /ON is ACTIVE LOW "
            "(low OR OPEN = HV ON). VSET has an internal 10k pull-up to Vref, "
            "so an OPEN VSET NODE COMMANDS FULL SCALE. Output is NOT internally "
            "limited. Pins 3 and 7 are BOTH GND and both must be present (SA-11).",
      extra={"Polarity": "POSITIVE (factory-fixed by the item-code letter P)"})
    C("U2", "ISEG_N", "AP010504N05",
      {"1": "VIN_N", "2": "VSET_N", "3": "GND", "4": "nON_N",
       "5": "VMON_N", "6": "HV_NEG", "7": "GND"},
      notes="as U1, negative polarity. Factory-fixed, not switchable.",
      extra={"Polarity": "NEGATIVE (factory-fixed by the item-code letter N)"})

    # ================================================= 9.4  HV ROUTING MATRIX
    R("R_S_P", "10k", "HV_POS", "HV_POS_COM", pclass="R_HV_AXIAL",
      notes="limits the capacitive MAKE discharge Pickering Note 1 warns about: "
            "100 mA at 1 kV against a 3 A rating = 30x margin")
    R("R_S_N", "10k", "HV_NEG", "HV_NEG_COM", pclass="R_HV_AXIAL")
    C("K1", "RELAY_HV", "67-1-C-5/5D",
      {"A1": "COIL_FEED_P", "A2": "K1_COIL_LO",
       "11": "HV_POS_COM", "12": "HV_POS_PARK", "14": "HV_OUT_A"},
      notes="1 Form C reed, 5 kV stand-off. INTERNAL COIL DIODE ('/5D') => COIL "
            "POLARITY IS MANDATORY. Mount K1 and K2 with their long axes "
            "ORTHOGONAL: reed sensitivity is strongly axial and this mitigation "
            "costs nothing at layout and cannot be added later.")
    C("K2", "RELAY_HV", "67-1-C-5/5D",
      {"A1": "COIL_FEED_N", "A2": "K2_COIL_LO",
       "11": "HV_NEG_COM", "12": "HV_NEG_PARK", "14": "HV_X"},
      notes="as K1. Long axis ORTHOGONAL to K1.")
    C("QK1", "Q_NMOS_COIL", ">=300mA NFET", {"1": "REL_EN_P", "2": "GND", "3": "K1_COIL_LO"},
      notes="COMBINER_DESIGN 6.3 specifies 2N7002 (~115 mA) for a 125 mA coil. "
            "UNDER-RATED. A >=300 mA part is required; reported, not patched.")
    C("QK2", "Q_NMOS_COIL", ">=300mA NFET", {"1": "REL_EN_N", "2": "GND", "3": "K2_COIL_LO"})
    R("R12", "100k", "REL_EN_P", "GND")
    R("R13", "100k", "REL_EN_P", "GND")
    R("R14", "100k", "REL_EN_N", "GND")
    R("R15", "100k", "REL_EN_N", "GND")

    # ---- the mode element.  PANEL part, seven poles, three positions.
    #      S3 (SW1C) MUST be PHYSICALLY INTERPOSED between S1 (SW1A) and
    #      S2 (SW1B) -- BUILD RULE SW-1.  Otherwise the pole-to-pole stress is
    #      2 kV regardless of the contact algebra, and the mistake will not
    #      look wrong.
    C("SW1A", "SW_SPDT", "SW1 pole S1", {"2": "HV_X", "1": "HV_M", "3": "HV_OUT_B"},
      notes="pin 2 = COMMON. PB throw (pin 1) -> M; UNI throw (pin 3) -> OUT_B.")
    C("SW1B", "SW_SPST", "SW1 pole S2", {"1": "HV_M1", "2": "HV_OUT_A"},
      notes="closed in PSEUDO-BIPOLAR only. M -> R_M1 -> BUS_A.")
    C("SW1C", "SW_SPDT", "SW1 pole S3", {"2": "HV_SW_G", "1": "HV_OUT_B", "3": "HV_M"},
      notes="pin 2 = COMMON = GND through R_G. GROUNDS OUT_B in pseudo-bipolar "
            "and GROUNDS M in unipolar. This pole is what splits the 2000 V "
            "stress into two 1000 V gaps; every weld of it fails toward "
            "'output grounded'.")
    R("R_M1", "10k", "HV_M", "HV_M1", pclass="R_HV_AXIAL",
      notes="bounds the UNI->PB-on-a-live-instrument transient to 200 mA at 2000 V")
    R("R_G", "10k", "HV_SW_G", "GND", pclass="R_HV_AXIAL",
      notes="makes OUT_B's pseudo-bipolar ground bond DEFINED and current-limited: "
            "a module at the 0.75 mA limit lifts OUT_B by 7.5 V, still touch-safe")
    # LV poles of the same armature
    C("SW1D", "SW_SPST_LV", "SW1 pole S4 (aux PB)", {"1": "+3V3", "2": "MODE_A"},
      notes="POSITIVE decode of pseudo-bipolar. Wired to +3V3, not to GND, so a "
            "BROKEN WIRE -- the likelier panel-harness fault -- reads 0.")
    C("SW1E", "SW_SPST_LV", "SW1 pole S5 (aux UNI)", {"1": "+3V3", "2": "MODE_B"},
      notes="POSITIVE decode of unipolar. (1,1) is mechanically impossible and "
            "therefore means a shorted aux => MODE_VALID = 0 => ARM = 0.")
    C("SW1F", "SW_SPST_LV", "SW1 pole S6 (+VIN bridge)",
      {"1": "VIN_P_PRE", "2": "VIN_N_PRE"},
      notes="THE POWER PERMISSIVE. Bridges around K_S pole A in UNIPOLAR only. "
            "A stuck GPIO or a shorted MODE_B line cannot close this contact, "
            "so it cannot release exclusivity.")
    C("SW1G", "SW_SPST_LV", "SW1 pole S7 (coil bridge)",
      {"1": "COIL_FEED_P", "2": "COIL_FEED_N"},
      notes="as S6, for the relay coil feed.")
    C("J6", "HDR8", "mode-switch LV harness",
      {"1": "+3V3", "2": "MODE_A", "3": "MODE_B", "4": "GND",
       "5": "VIN_P_PRE", "6": "VIN_N_PRE", "7": "COIL_FEED_P", "8": "COIL_FEED_N"},
      notes="board boundary for the panel switch's four LV poles. The three HV "
            "poles are wired to individual HV standoffs, NOT to a header.")

    # ---- output terminals
    C("J2", "SHV", "SHV bulkhead A", {"1": "HV_OUT_A", "2": "GND"},
      notes="pseudo-bipolar: the ONE output. unipolar: the POSITIVE output.")
    C("J3", "SHV", "SHV bulkhead B", {"1": "HV_OUT_B", "2": "GND"},
      notes="pseudo-bipolar: GROUNDED through R_G, never floating. "
            "unipolar: the NEGATIVE output. Spaced from J2 for the full 2000 V.")

    # ---- every HV string
    for sid in sorted(HV_STRINGS):
        build_hv_string(sid)

    # ============================================ 9.5  INDEPENDENT MONITORS
    for X, refn, r_ref_top in (("A", "MON_REF_A", "1.82k"), ("B", "MON_REF_B", "2.32k")):
        tap = "HVDIV_TAP_%s" % X
        R("RMB_%s" % X, "909k 0.1%%", tap, "GND",
          notes="bottom leg; alpha = 8.1899e-4, +-FS = +-2500.7 V")
        R("RMO_%s" % X, "200k 0.1%%", tap, "VREF_2V500",
          notes="offset injection; VREF drift CANCELS in the differential read")
        R("RMS_%s" % X, "1.00M", tap, "MON_TAPF_%s" % X, notes="anti-alias series")
        CAP("CMA_%s" % X, "1n C0G", "MON_TAPF_%s" % X, "GND")
        R("RMR1_%s" % X, r_ref_top, "VREF_2V500", "MON_REFD_%s" % X,
          notes="A and B are DELIBERATELY DIFFERENT (2.046 V vs 1.951 V) so that "
                "the ADS1115's AIN1-AIN3 read is a free stuck-mux detector")
        R("RMR2_%s" % X, "8.25k 0.1%", "MON_REFD_%s" % X, "GND")
        C("UMB_%s" % X, "OPA2192", "OPA2192",
          {"1": "MON_TAP_%s" % X, "2": "MON_TAP_%s" % X, "3": "MON_TAPF_%s" % X,
           "4": "GND", "5": "MON_REFD_%s" % X, "6": refn, "7": refn, "8": "+5V_A"},
          notes="A = tap buffer (source Z is 163.8 kOhm, so the buffer is "
                "MANDATORY, not optional); B = matched offset buffer")
        CAP("CMB_%s" % X, "100n", "+5V_A", "GND")
    C("UGD", "OPA2192", "OPA2192",
      {"1": "HVDIV_GUARD_A", "2": "HVDIV_GUARD_A", "3": "MON_TAP_A",
       "4": "GND", "5": "MON_TAP_B", "6": "HVDIV_GUARD_B", "7": "HVDIV_GUARD_B",
       "8": "+5V_A"},
      notes="DRIVEN guard rings at tap potential. At Rt = 200 MOhm a 10 GOhm "
            "board leakage path injects 20.0 V of error -- LARGER than the "
            "10.0 V VMON accuracy the divider exists to beat. The guard ring is "
            "a REQUIREMENT of the monitor, not a refinement.")
    C("TP1", "TP", "HVDIV_GUARD_A", {"1": "HVDIV_GUARD_A"})
    C("TP2", "TP", "HVDIV_GUARD_B", {"1": "HVDIV_GUARD_B"})

    # VMON buffers -> ADC-B.  Every HV-monitor-vs-VMON comparison must CROSS
    # the package boundary, or a common-mode ADC fault moves both readings the
    # same way and the 20 V disagreement trip goes blind.
    C("UVM", "OPA2192", "OPA2192",
      {"1": "VMON_P_BUF", "2": "VMON_P_BUF", "3": "VMON_P", "4": "GND",
       "5": "VMON_N", "6": "VMON_N_BUF", "7": "VMON_N_BUF", "8": "+5V_A"})
    C("UADCA", "ADS1115", "ADS1115",
      {"1": "GND", "2": "nALERT_ADC", "3": "GND", "4": "MON_TAP_A",
       "5": "MON_REF_A", "6": "MON_TAP_B", "7": "MON_REF_B",
       "8": "+3V3_A", "9": "I2C_SDA", "10": "I2C_SCL"},
      notes="ADDR->GND = 0x48. BOTH independent HV monitors, as two "
            "differential pairs. NOTHING IN THE INTERLOCK READS THIS PART: "
            "every hardware permissive is a discrete comparator on its own "
            "string, so a stuck mux is not a safety element.")
    C("UADCB", "ADS1115", "ADS1115",
      {"1": "+3V3_A", "2": "nALERT_ADC", "3": "GND", "4": "VMON_P_BUF",
       "5": "VMON_N_BUF", "6": "VREF_2V500", "7": "RAIL5V_DIV",
       "8": "+3V3_A", "9": "I2C_SDA", "10": "I2C_SCL"},
      notes="ADDR->VDD = 0x49. Both module VMONs plus reference and rail health.")
    R("R16", "100k 0.1%", "+5V_MOD", "RAIL5V_DIV")
    R("R17", "100k 0.1%", "RAIL5V_DIV", "GND")
    CAP("C17", "100n", "+3V3_A", "GND")
    R("R18", "4.7k", "I2C_SDA", "+3V3_A")
    R("R19", "4.7k", "I2C_SCL", "+3V3_A")

    # ================================================ 9.6  COLD + BRANCH CHAINS
    for X in ("A", "B"):
        node = "HVDIV_COLD_%s" % X
        R("RCB_%s" % X, "5.62M 0.1%", node, "GND")
        R("RCO_%s" % X, "1.58M 0.1%", node, "VREF_2V500",
          notes="D-3: 1.58M (not 1.24M) puts the node at ~1.950 V so that BOTH "
                "window thresholds are reachable from a 2.048 V-topped string")
        C("UCC_%s" % X, "TLV3202", "TLV3202",
          {"1": "COLD_%s_HI" % X, "2": "COLD_TH_HI", "3": node, "4": "GND",
           "5": node, "6": "COLD_TH_LO", "7": "COLD_%s_LO" % X, "8": "+5V_A"},
          notes="WINDOW comparator, sign-blind by design. A: HIGH while node < "
                "TH_HI. B: HIGH while node > TH_LO. MUST BE PUSH-PULL: an "
                "open-drain failure pulls up to a FALSE COLD = 1.")
        R("RCP1_%s" % X, "100k", "COLD_%s" % X, "GND", notes="pull-DOWN, ARCH-18 1/2")
        R("RCP2_%s" % X, "100k", "COLD_%s" % X, "GND", notes="pull-DOWN, ARCH-18 2/2")
        R("RCH_%s" % X, "100k", "COLD_%s_HI" % X, "GND")
        R("RCL_%s" % X, "100k", "COLD_%s_LO" % X, "GND")
    # window thresholds, from REF3020 -- a DIFFERENT PART from the REF5025 that
    # supplies the node's offset.  If both came from one reference, a reference
    # failure would drive node and centre to 0 V together, |0-0| < window would
    # be satisfied, and COLD would read TRUE at any output voltage.
    R("R20", "5.23k 0.1%", "VREF_2V048", "COLD_TH_HI")
    R("R21", "9.09k 0.1%", "COLD_TH_HI", "COLD_TH_LO")
    R("R22", "191k 0.1%", "COLD_TH_LO", "GND")

    for P, node in (("P", "HVDIV_BR_P"), ("N", "HVDIV_BR_N")):
        R("RBB_%s" % P, "5.62M 0.1%", node, "GND")
        R("RBO_%s" % P, "1.58M 0.1%", node, "VREF_2V500")
    C("UBR", "TLV3202", "TLV3202",
      {"1": "BRANCH_LIVE_P", "2": "COLD_TH_HI", "3": "HVDIV_BR_P", "4": "GND",
       "5": "COLD_TH_LO", "6": "HVDIV_BR_N", "7": "BRANCH_LIVE_N", "8": "+5V_A"},
      notes="single-threshold, one per module, UPSTREAM of the relays. Without "
            "these the weld self-test cannot distinguish 'stimulus applied and "
            "blocked' from 'no stimulus was ever applied'. Diagnostics only -- "
            "they feed the shift register, not the interlock -- which is why "
            "sharing the COLD threshold taps is acceptable here.")
    R("R23", "100k", "BRANCH_LIVE_P", "GND")
    R("R24", "100k", "BRANCH_LIVE_N", "GND")

    # ================================================ 9.7  REFERENCES + CLAMP
    C("U20", "REF5025", "REF5025", {"2": "+5V_A", "4": "GND", "5": "REF_NR",
                                    "6": "VREF_2V500"}, nc=["1", "3", "7", "8"],
      notes="2.500 V, +-0.05 %, 3 ppm/K. Sets DAC gain AND both offset legs.")
    CAP("C18", "1u C0G", "REF_NR", "GND")
    CAP("C19", "10u", "VREF_2V500", "GND")
    C("U21", "REF3020", "REF3020", {"1": "+5V_A", "2": "VREF_2V048", "3": "GND"},
      notes="2.048 V. The COLD window centre. A DIFFERENT DEVICE from U20 -- "
            "that separation is the whole of MONITOR_AND_BLEED 5.5.")
    CAP("C20", "1u", "VREF_2V048", "GND")
    C("U22", "LM4040_2V048", "LM4040-2.048",
      {"1": "VREF_2V048_SH", "2": "GND"}, nc=["3"],
      notes="SHUNT 2.048 V, a different FAMILY again, for the VSET/clamp window. "
            "A SERIES reference here would fail to its own input on a pass-"
            "element short: 5 V on the clamp rail is 2000 V at the output.")
    R("R25", "1.50k", "+5V_A", "VREF_2V048_SH")

    # ---- the rail force amplifier.  MANDATORY, and the probe is what found it:
    #      with both modules at full scale simultaneously (NORMAL since G0-A4)
    #      the clamp-rail load is 12.062 mA against REF5025's +-10 mA rating.
    C("U3", "OPA2192", "OPA2192",
      {"1": "VCLAMP", "2": "VCLAMP_FB", "3": "VREF_2V500", "4": "GND",
       "5": "GND", "6": "U3_PARK", "7": "U3_PARK", "8": "+5V_A"},
      notes="A = unity-gain rail force amp, >=18.1 mA. B is PARKED as a unity "
            "buffer of GND rather than left floating.")
    R("R26", "0R", "VCLAMP", "VCLAMP_STAR", notes="FORCE leg of the Kelvin pair")
    R("R27", "0R", "VCLAMP_STAR", "VCLAMP_FB", notes="SENSE leg, taken AT THE STAR")
    R("R28", "10k", "VCLAMP", "VCLAMP_FB",
      notes="SP-8: local feedback >= 1000x the force resistance. Without it an "
            "open sense trace leaves the loop open and rails the amplifier -- "
            "i.e. commands FULL SCALE. With it, an open sense degrades to a "
            "plain buffer.")
    CAP("C21", "10u", "VCLAMP_STAR", "GND")

    # ---- window comparator on the clamp rail: the ONE fault the rail clamp
    #      cannot cover is the rail itself RISING.
    R("R29", "20.0k 0.1%", "VCLAMP_STAR", "VCLAMP_SENSE")
    R("R30", "20.0k 0.1%", "VCLAMP_SENSE", "GND")
    R("R31", "4.99k 0.1%", "VREF_2V048_SH", "CLAMP_TH_HI")
    R("R32", "2.00k 0.1%", "CLAMP_TH_HI", "CLAMP_TH_LO")
    R("R33", "97.6k 0.1%", "CLAMP_TH_LO", "GND")
    C("U5", "TLV3202", "TLV3202",
      {"1": "CLAMP_OV", "2": "CLAMP_TH_HI", "3": "VCLAMP_SENSE", "4": "GND",
       "5": "CLAMP_TH_LO", "6": "VCLAMP_SENSE", "7": "CLAMP_UV", "8": "+5V_A"},
      notes="thresholds 2.430 / 2.5515 V referred to the rail. Caps a reference "
            "fault at 1021 V instead of 1320 V (3.3 V) or 2000 V (5 V).")
    R("R34", "100k", "CLAMP_OV", "GND")
    R("R35", "100k", "CLAMP_UV", "GND")

    # ================================================ 9.8  DAC + VSET PATH
    C("U18", "DAC8552", "DAC8552",
      {"1": "+5V_A", "2": "VCLAMP_STAR", "3": "DAC_OUTB", "4": "DAC_OUTA",
       "5": "nSYNC_DAC_5V", "6": "SPI_A_SCK_5V", "7": "SPI_A_MOSI_5V", "8": "GND"},
      notes="VREF = THE CLAMP RAIL, so Vout <= Vref is a ratiometric property of "
            "the part, not a promise. VDD = 5 V is chosen for the LAYOUT reason: "
            "it keeps the entire +3V3 domain out of the analog set-path region, "
            "which is the only real defence against a VSET-to-3V3 solder bridge. "
            "POWER-ON RESET TO ZERO SCALE IS A DISQUALIFYING GATE AND IS STILL "
            "[recalled] -- G1 datasheet read (O-B).")
    CAP("C22", "100n", "+5V_A", "GND")
    C("U6", "74AHCT125", "74AHCT125",
      {"1": "GND", "2": "nSYNC_DAC", "3": "nSYNC_DAC_5V",
       "4": "GND", "5": "SPI_A_SCK", "6": "SPI_A_SCK_5V",
       "7": "GND", "8": "SPI_A_MOSI_5V", "9": "SPI_A_MOSI", "10": "GND",
       "11": "AHCT_SPARE", "12": "GND", "13": "+5V_A", "14": "+5V_A"},
      notes="AHCT has TTL thresholds, so it accepts 3.3 V directly. It exists "
            "because TI DAC85xx digital VIH is [recalled] 0.7xVDD = 3.5 V at "
            "VDD = 5 V, which 3.3 V logic DOES NOT MEET.")
    C("TP3", "TP", "AHCT_SPARE", {"1": "AHCT_SPARE"})

    # ---- U4: THE CLAMP.  Its V+ IS the 2.500 V rail.  A rail-to-rail output
    #      stage cannot exceed its own rail, and nothing downstream of U4
    #      touches +3V3 or +5V.
    C("U4", "OPA_CLAMP", "**UNSELECTED RRIO dual**",
      {"1": "VSET_P_FORCE", "2": "VSET_P_SENSE", "3": "DAC_A_F", "4": "GND",
       "5": "DAC_B_F", "6": "VSET_N_SENSE", "7": "VSET_N_FORCE", "8": "VCLAMP_STAR"},
      notes="*** PRIMARY SAFETY ELEMENT WITH AN UNSELECTED PART (O-D). *** "
            "Pin 8 on VCLAMP_STAR is the clamp. Over-range residual +0.061 % "
            "(1000.6 V) against 1320 V unclamped at 3.3 V and 2000 V at 5 V.")
    R("R36", "1.00k", "DAC_OUTA", "DAC_A_F",
      notes="input current limiter, at the AMPLIFIER INPUT -- ARCH-04 does not "
            "apply to it and it costs <= 1 uV")
    R("R37", "1.00k", "DAC_OUTB", "DAC_B_F")
    R("R38", "10k", "VSET_P_FORCE", "VSET_P_SENSE", notes="SP-8 local feedback")
    R("R39", "10k", "VSET_N_FORCE", "VSET_N_SENSE")
    R("R40", "10R", "VSET_P_FORCE", "VSET_P",
      notes="capacitive-load isolation INSIDE the Kelvin loop, so it is nulled "
            "at DC. Outside the loop this would be the ARCH-04 violation it "
            "exists to avoid.")
    R("R41", "10R", "VSET_N_FORCE", "VSET_N")
    R("R42", "0R", "VSET_P", "VSET_P_SENSE", notes="Kelvin sense AT THE MODULE PIN")
    R("R43", "0R", "VSET_N", "VSET_N_SENSE")
    # at the module pin, in this physical order
    for M, on in (("P", "nON_P"), ("N", "nON_N")):
        R("RPD1_%s" % M, "1.00k 0.1%", "VSET_%s" % M, "GND",
          notes="ARCH-18 pair 1/2. Turns 'clamp fails open' from 1000 V into "
                "47.6 V. One element open is a SECOND fault at 90.9 V.")
        R("RPD2_%s" % M, "1.00k 0.1%", "VSET_%s" % M, "GND", notes="ARCH-18 pair 2/2")
        C("DVS_%s" % M, "D_SCH", "BAT54", {"1": "VSET_%s" % M, "2": "GND"},
          notes="cathode to VSET, anode to GND: clamps NEGATIVE excursions and "
                "fails safe BOTH ways (short => VSET = 0; open => only the "
                "protection is lost). The opposite orientation was REJECTED "
                "because its short commands full scale.")
        CAP("CVS_%s" % M, "100n C0G", "VSET_%s" % M, "GND")
        C("QVS_%s" % M, "Q_NMOS", "2N7002",
          {"1": on, "2": "GND", "3": "VSET_%s" % M},
          notes="disabled module => VSET grounded, in hardware. Gate tapped at "
                "the MODULE end of the /ON net.")
    # VSET over-range comparators
    R("R44", "100k 0.1%", "+5V_A", "VSET_TH")
    R("R45", "20.5k 0.1%", "VSET_TH", "VREF_2V048_SH",
      notes="threshold = 2.048 + (5 - 2.048)*R45/(R44+R45) = 2.551 V. Sitting on "
            "a 2.048 V shunt reference makes the threshold's rail sensitivity "
            "0.2 %/% instead of the 1 %/% a plain rail divider would have.")
    C("U7", "TLV3202", "TLV3202",
      {"1": "VSET_OVR_P", "2": "VSET_TH", "3": "VSET_P", "4": "GND",
       "5": "VSET_N", "6": "VSET_TH", "7": "VSET_OVR_N", "8": "+5V_A"})
    R("R46", "100k", "VSET_OVR_P", "GND")
    R("R47", "100k", "VSET_OVR_N", "GND")

    # ---- HV over-voltage comparators (105 % = 1050 V) on the BUFFERED taps.
    #      This is what closes session 1's fault 15 (broken VSET wire => full
    #      scale, marked UNSAFE and unfixable).
    R("R48", "10.0k 0.1%", "VREF_2V048_SH", "OVP_TH_AH")
    R("R49", "3.32k 0.1%", "OVP_TH_AH", "OVP_TH_AL")
    R("R50", "10.0k 0.1%", "OVP_TH_AL", "GND")
    C("U8", "TLV3202", "TLV3202",
      {"1": "OVP_A_HI", "2": "OVP_TH_AH", "3": "MON_TAP_A", "4": "GND",
       "5": "OVP_TH_AL", "6": "MON_TAP_A", "7": "OVP_A_LO", "8": "+5V_A"},
      notes="+-105 % of Vnom on output A, read off the independent monitor -- "
            "the only layer that is indifferent to the fault's MECHANISM.")
    C("U9", "TLV3202", "TLV3202",
      {"1": "OVP_B_HI", "2": "OVP_TH_AH", "3": "MON_TAP_B", "4": "GND",
       "5": "OVP_TH_AL", "6": "MON_TAP_B", "7": "OVP_B_LO", "8": "+5V_A"})
    for n in ("OVP_A_HI", "OVP_A_LO", "OVP_B_HI", "OVP_B_LO"):
        R("R%s" % (51 + ("OVP_A_HI", "OVP_A_LO", "OVP_B_HI", "OVP_B_LO").index(n)),
          "100k", n, "GND")

    # ============================================ 9.9  THE INTERLOCK GATE ARRAY
    # Everything on +5V_MOD, everything 74HCT.  HCT NOT HC on every input
    # reachable from the ESP32: 74HC at VCC = 5 V wants VIH = 3.5 V and a 3.3 V
    # output does not meet it -- an HC part appears to work at room temperature
    # and fails at a corner.  The symbol cannot express this and ERC will not
    # catch it; it is a BOM-value property, which is why every logic `val`
    # below says HCT.
    #
    #   ARM = EN_HB . ARM_EN . INTLK . nOVP . SETTLE . RAIL_OK . MODE_VALID
    C("U30", "74HCT30", "74HCT30",
      {"1": "EN_HB", "2": "ARM_EN", "3": "INTLK", "4": "nOVP", "5": "SETTLE",
       "6": "RAIL_OK", "11": "MODE_VALID", "12": "+5V_MOD", "8": "nARM",
       "7": "GND", "14": "+5V_MOD"},
      notes="8-input NAND. The 8th input is tied HIGH. Seven ARM terms, of "
            "which THREE ARE PHYSICAL (INTLK loop, MODE_VALID from the panel "
            "switch's own contacts, and -- through EN_HB -- firmware liveness).")
    C("U31", "74HCT14", "74HCT14",
      {"1": "nARM", "2": "ARM",
       "3": "MODE_A", "4": "nMODE_A",
       "5": "SEL", "6": "nSEL",
       "9": "HB_PUMP", "8": "EN_HB_PUMP",
       "11": "GND", "10": "HCT14_SPARE",
       "13": "OVP_CLR_AC", "12": "nOVP_CLR_SQ",
       "7": "GND", "14": "+5V_MOD"})
    C("TP4", "TP", "HCT14_SPARE", {"1": "HCT14_SPARE"})
    C("U32", "74HCT86", "74HCT86",
      {"1": "MODE_A", "2": "MODE_B", "3": "MODE_VALID",
       "4": "SEL", "5": "SEL_DLY", "6": "SEL_EDGE",
       "9": "MODE_A", "10": "MODE_A_DLY", "8": "MODEA_EDGE",
       "12": "MODE_B", "13": "MODE_B_DLY", "11": "MODEB_EDGE",
       "7": "GND", "14": "+5V_MOD"},
      notes="MODE_VALID = MODE_A XOR MODE_B. POSITIVE DECODE OF BOTH MODES: "
            "(1,0) pseudo-bipolar, (0,1) unipolar, (0,0) SAFE detent / in "
            "transit / broken aux wire, (1,1) mechanically impossible => "
            "shorted aux. One extra contact and one XOR cover the intermediate "
            "position, a shorted aux and a broken aux SIMULTANEOUSLY. "
            "The other three gates are edge detectors into SETTLE.")
    for a, b in (("SEL", "SEL_DLY"), ("MODE_A", "MODE_A_DLY"), ("MODE_B", "MODE_B_DLY")):
        R("RD_%s" % b, "100k", a, b)
        CAP("CD_%s" % b, "100n", b, "GND")
    C("U33", "74HCT08", "74HCT08",
      {"1": "MODE_B", "2": "nMODE_A", "3": "MODE_UNI",
       "4": "ARM", "5": "OUT_EN", "6": "ARM_OUTEN",
       "9": "ARM", "10": "MU_OR_nSEL", "8": "PERMIT_P",
       "12": "ARM", "13": "MU_OR_SEL", "11": "PERMIT_N",
       "7": "GND", "14": "+5V_MOD"},
      notes="*** THE MODE-AWARE PERMISSIVE. ***  "
            "PERMIT_P . PERMIT_N = ARM.(MODE_UNI + nSEL).(MODE_UNI + SEL) "
            "= ARM . MODE_UNI.  Both modules can be permitted ONLY when the "
            "switch's own aux pole says the armature is already in the position "
            "that has put them on different nodes. When MODE_UNI = 0 this "
            "collapses BIT FOR BIT to the SEL/nSEL gate. MODE_CMD does not "
            "exist and appears nowhere.")
    C("U34", "74HCT32", "74HCT32",
      {"1": "MODE_UNI", "2": "nSEL", "3": "MU_OR_nSEL",
       "4": "MODE_UNI", "5": "SEL", "6": "MU_OR_SEL",
       "9": "SEL_EDGE", "10": "MODEA_EDGE", "8": "EDGE_1",
       "12": "EDGE_1", "13": "MODEB_EDGE", "11": "EDGE_ANY",
       "7": "GND", "14": "+5V_MOD"})
    C("U35", "74HCT123", "74HCT123",
      {"1": "GND", "2": "EDGE_ANY", "3": "+5V_MOD", "4": "SETTLE",
       "5": "SETTLE_PULSE", "6": "GND", "7": "RCEXT_1",
       "9": "GND", "10": "GND", "11": "GND", "12": "MONO_SPARE_NQ",
       "13": "MONO_SPARE_Q", "14": "GND", "15": "RCEXT_2",
       "8": "GND", "16": "+5V_MOD"},
      notes="SETTLE is ~Q (pin 4): HIGH at rest, LOW for T_dwell after any SEL "
            "or mode edge, and LOW when unpowered -- all three fail-safe. "
            "t_w ~= 0.45.R.C = 0.99 s [recalled formula, G1 datasheet read].")
    R("R_SET", "1.0M", "+5V_MOD", "RCEXT_1")
    CAP("C_SET", "2.2u film", "RCEXT_1", "GND")
    R("R_SET2", "1.0M", "+5V_MOD", "RCEXT_2", notes="parks the unused half")
    C("TP5", "TP", "SETTLE_PULSE", {"1": "SETTLE_PULSE"})
    C("TP6", "TP", "MONO_SPARE_NQ", {"1": "MONO_SPARE_NQ"})
    C("TP7", "TP", "MONO_SPARE_Q", {"1": "MONO_SPARE_Q"})
    C("U36", "74HCT03", "74HCT03",
      {"1": "ARM_OUTEN", "2": "MU_OR_nSEL", "3": "nON_P",
       "4": "ARM_OUTEN", "5": "MU_OR_SEL", "6": "nON_N",
       "9": "COLD_AB", "10": "nARM", "8": "KS_LE_N",
       "12": "KS_LE_N", "13": "KS_LE_N", "11": "KS_LE",
       "7": "GND", "14": "+5V_MOD"},
      notes="OPEN-DRAIN NAND. Gates a/b are /ON_P and /ON_N, pulled up to each "
            "module's OWN +VIN within 5 mm of pin 4 (ARCH-17) so the pull-up "
            "cannot outlive the module's supply. Gates c/d build "
            "KS_LE = COLD_AB . nARM out of two open-drain NANDs.")
    R("R55", "10k", "nON_P", "VIN_P", notes="ARCH-17/ARCH-18 pair 1/2, <5 mm from pin 4")
    R("R56", "10k", "nON_P", "VIN_P", notes="pair 2/2")
    R("R57", "10k", "nON_N", "VIN_N", notes="pair 1/2")
    R("R58", "10k", "nON_N", "VIN_N", notes="pair 2/2")
    R("R59", "10k", "KS_LE_N", "+5V_MOD")
    R("R60", "10k", "KS_LE", "+5V_MOD")
    C("U38", "74HCT08", "74HCT08",
      {"1": "EN_HB_PUMP", "2": "WDT_OK", "3": "EN_HB",
       "4": "COLD_A_HI", "5": "COLD_A_LO", "6": "COLD_A",
       "9": "COLD_B_HI", "10": "COLD_B_LO", "8": "COLD_B",
       "12": "COLD_A", "13": "COLD_B", "11": "COLD_AB",
       "7": "GND", "14": "+5V_MOD"})
    C("U43", "74HCT08", "74HCT08",
      {"1": "EN_HB", "2": "INTLK", "3": "COIL_EN1",
       "4": "COIL_EN1", "5": "MODE_VALID", "6": "COIL_EN",
       "9": "GND", "10": "GND", "8": "AND_SPARE1",
       "12": "GND", "13": "GND", "11": "AND_SPARE2",
       "7": "GND", "14": "+5V_MOD"},
      notes="C-1: the coil rail passes through its OWN fail-safe switch, so "
            "both-coils-off is reachable and the weld self-test can execute.")
    C("TP8", "TP", "AND_SPARE1", {"1": "AND_SPARE1"})
    C("TP9", "TP", "AND_SPARE2", {"1": "AND_SPARE2"})

    # ---- cold-switch latches.  SEPARATING the module enable from the relay
    #      enable and latching ONLY the latter is what gives cold make AND cold
    #      break with no circularity: the thing that makes the node cold
    #      (removing +VIN, raising /ON) is NOT the thing that is latched.
    C("U39", "74HCT75", "74HCT75",
      {"2": "PERMIT_P", "16": "REL_EN_P", "1": "LATCH_NQ0", "13": "COLD_A",
       "3": "GND", "15": "LATCH_Q1", "14": "LATCH_NQ1",
       "6": "PERMIT_N", "10": "REL_EN_N", "11": "LATCH_NQ2", "4": "COLD_AB",
       "7": "GND", "9": "LATCH_Q3", "8": "LATCH_NQ3",
       "5": "+5V_MOD", "12": "GND"},
      notes="REL_EN_P = LATCH(D = PERMIT_P, LE = COLD_A). "
            "REL_EN_N = LATCH(D = PERMIT_N, LE = COLD_A . COLD_B). "
            "Turning ON: the node is already cold, the latch is transparent, "
            "the relay closes 6 ms before any HV exists. Turning OFF: PERMIT "
            "drops (module dead at once), the node is hot so the latch is "
            "OPAQUE and the relay STAYS CLOSED -- which puts the module-side "
            "and output-side bleeds in parallel and discharges FASTER -- and "
            "when COLD asserts it releases cold.")
    for n in ("LATCH_NQ0", "LATCH_Q1", "LATCH_NQ1", "LATCH_NQ2",
              "LATCH_Q3", "LATCH_NQ3"):
        C("TP_%s" % n, "TP", n, {"1": n})
    C("U44", "74HCT75", "74HCT75",
      {"2": "SEL", "16": "KS_SEL", "1": "L2_NQ0", "13": "KS_LE",
       "3": "GND", "15": "L2_Q1", "14": "L2_NQ1",
       "6": "GND", "10": "L2_Q2", "11": "L2_NQ2", "4": "GND",
       "7": "GND", "9": "L2_Q3", "8": "L2_NQ3",
       "5": "+5V_MOD", "12": "GND"},
      notes="KS_SEL = LATCH(D = SEL, LE = COLD_A . COLD_B . nARM). Because the "
            "enable includes nARM and Q_ARM is gated by ARM, whenever the "
            "armature is allowed to move VIN_ARMED is 0 V and the contact "
            "transfers WITH NO SOURCE BEHIND IT. F-5 retired for free.")
    for n in ("L2_NQ0", "L2_Q1", "L2_NQ1", "L2_Q2", "L2_NQ2", "L2_Q3", "L2_NQ3"):
        C("TP_%s" % n, "TP", n, {"1": n})

    # ---- OVP SR latch.  Powers up SET (tripped); the CLEAR path is AC-coupled
    #      so a stuck GPIO cannot hold the protection defeated.
    C("U37", "74HCT00", "74HCT00",
      {"1": "nOVP_SET", "2": "nOVP", "3": "OVP_Q",
       "4": "nOVP_CLR_SQ", "5": "OVP_Q", "6": "nOVP",
       "9": "GND", "10": "GND", "8": "NAND_SPARE1",
       "12": "GND", "13": "GND", "11": "NAND_SPARE2",
       "7": "GND", "14": "+5V_MOD"})
    C("TP10", "TP", "NAND_SPARE1", {"1": "NAND_SPARE1"})
    C("TP11", "TP", "NAND_SPARE2", {"1": "NAND_SPARE2"})
    R("R61", "10k", "nOVP_SET", "+5V_MOD")
    R("R62", "10k", "nOVP_SET", "+5V_MOD")
    CAP("C23", "1u", "nOVP_SET", "GND",
        notes="POWER-ON SET: holds nOVP_SET low while it charges, so EVERY "
              "power-up begins latched-off and requires an explicit clear. "
              "A brownout that glitches the logic rail lands in the same place.")
    C("QSET", "Q_NMOS", "2N7002", {"1": "OVP_SET", "2": "GND", "3": "nOVP_SET"},
      notes="pulls the latch SET input low when ANY protection comparator trips")
    R("R63", "100k", "OVP_SET", "GND")
    R("R64", "100k", "OVP_SET", "GND")
    for i, src in enumerate(("OVP_A_HI", "OVP_A_LO", "OVP_B_HI", "OVP_B_LO",
                             "VSET_OVR_P", "VSET_OVR_N", "CLAMP_OV", "CLAMP_UV")):
        C("DOR%d" % (i + 1), "D_SCH", "BAT54", {"1": "OVP_SET", "2": src},
          notes="wire-OR into the latch SET: anode on the comparator, cathode "
                "on OVP_SET")
    CAP("C24", "100n", "nOVP_CLR", "OVP_CLR_AC",
        notes="ONLY AN EDGE CLEARS THE LATCH. Without this the OVP is one stuck "
              "GPIO away from being decorative.")
    R("R65", "10k", "OVP_CLR_AC", "GND")
    R("R66", "10k", "OVP_CLR_AC", "GND")

    # ---- heartbeat pump (C-3).  TWO coupling capacitors IN SERIES: a single
    #      shorted capacitor still leaves one, so a static GPIO level cannot
    #      hold EN_HB.  Toggled ONLY from the main loop -- never from LEDC,
    #      RMT, a hardware timer or an ISR, because a peripheral free-runs
    #      through the exact application hang the pump exists to detect.
    CAP("C25", "22n", "HB_OUT", "HB_MID")
    CAP("C26", "22n", "HB_MID", "HB_RECT")
    C("D4", "D_SCH", "BAT54", {"1": "HB_PUMP", "2": "HB_RECT"})
    C("D5", "D_SCH", "BAT54", {"1": "HB_RECT", "2": "GND"})
    CAP("C27", "100n", "HB_PUMP", "GND")
    R("R67", "2.0M", "HB_PUMP", "GND", notes="ARCH-18 pair 1/2")
    R("R68", "2.0M", "HB_PUMP", "GND", notes="ARCH-18 pair 2/2")
    R("R69", "100k", "HB_OUT", "GND", notes="ARCH-18 pair 1/2 at the ESP32 pin")
    R("R70", "100k", "HB_OUT", "GND", notes="ARCH-18 pair 2/2")
    C("J7", "HDR3", "windowed watchdog (MAX6746 class)",
      {"1": "+5V_MOD", "2": "WDT_OK", "3": "GND"},
      notes="OPEN ITEM: the WINDOWED supervisor is specified but not yet a "
            "part. A windowed device faults on kicks that are TOO FAST as well "
            "as too slow, which is what catches a free-running peripheral "
            "pretending to be a main loop.")
    R("R71", "100k", "WDT_OK", "GND")
    R("R72", "100k", "WDT_OK", "GND")

    # ---- interlock loop: key, lid and mode guard IN SERIES, closed = 1.
    C("SWK", "SW_SPST_LV", "panel key switch", {"1": "+5V_MOD", "2": "ILK_N1"})
    C("SWL", "SW_SPST_LV", "lid switch", {"1": "ILK_N1", "2": "ILK_N2"})
    C("SWG", "SW_SPST_LV", "mode-guard microswitch", {"1": "ILK_N2", "2": "ILK_N3"},
      notes="the guard that must be opened to REACH the mode selector. This is "
            "what actually meets the lead-break requirement: opening the guard "
            "drops ARM hundreds of milliseconds of hand travel BEFORE any HV "
            "pole can move. Geometry, not contact sequencing.")
    C("J4", "HDR3", "external interlock", {"1": "ILK_N3", "2": "INTLK", "3": "GND"},
      notes="ship a fitted shorting plug and say so on the panel")
    R("R73", "10k", "INTLK", "GND", notes="ARCH-18 pair 1/2")
    R("R74", "10k", "INTLK", "GND", notes="ARCH-18 pair 2/2")

    # ---- safe-state pull-downs on every ESP32-sourced interlock line
    for i, n in enumerate(("ARM_EN", "OUT_EN", "SEL")):
        R("RSS%da" % (i + 1), "10k", n, "GND", notes="ARCH-18/C-4 pair 1/2")
        R("RSS%db" % (i + 1), "10k", n, "GND", notes="ARCH-18/C-4 pair 2/2")
    R("RMA1", "100k", "MODE_A", "GND", notes="ARCH-18 pair 1/2 -- broken aux reads 0")
    R("RMA2", "100k", "MODE_A", "GND", notes="ARCH-18 pair 2/2")
    R("RMB1", "100k", "MODE_B", "GND", notes="ARCH-18 pair 1/2")
    R("RMB2", "100k", "MODE_B", "GND", notes="ARCH-18 pair 2/2")

    # ============================================ 9.10  CONTROLLER + READBACK
    C("U50", "ESP32S3", "ESP32-S3-WROOM-1U-N8R2",
      {"1": "GND", "2": "+3V3", "3": "ESP_EN",
       "4": "HB_OUT", "5": "ARM_EN", "6": "OUT_EN", "7": "SEL",
       "8": "SPI_B_MISO", "9": "nCS_W5500", "10": "nRST_W5500",
       "11": "nINT_W5500", "12": "nSYNC_DAC",
       "17": "SPI_A_SCK", "18": "SPI_A_MOSI", "19": "SPI_A_MISO",
       "20": "nLOAD_165", "21": "SPI_B_SCK", "22": "SPI_B_MOSI",
       "23": "I2C_SDA", "24": "nALERT_ADC", "25": "LED_NET",
       "26": "STRAP45", "27": "BOOT0", "16": "STRAP46",
       "28": "MODE_A_RB", "29": "MODE_B_RB", "30": "OVP_RB", "31": "nOVP_CLR",
       "36": "U0RXD", "37": "U0TXD", "38": "I2C_SCL",
       "40": "GND", "41": "GND"},
      nc=["13", "14", "15", "32", "33", "34", "35", "39"],
      notes="-1U (external antenna) and N8R2 (QUAD PSRAM) are HARD "
            "requirements: a PCB-antenna module inside an earthed steel box "
            "does not communicate, and OCTAL PSRAM occupies GPIO33-37. "
            "nc pins 13/14 = USB D-/D+ (internal only), 32-35 = JTAG "
            "(GPIO39-42, deliberately free), 15 = GPIO3 (strapping), "
            "39 = GPIO1 spare. See D-4 for the GPIO33/34 remap.")
    CAP("C28", "10u", "+3V3", "GND")
    CAP("C29", "100n", "+3V3", "GND")
    R("R75", "10k", "ESP_EN", "+3V3")
    CAP("C30", "1u", "ESP_EN", "GND")
    R("R76", "10k", "STRAP45", "GND",
      notes="GPIO45 = VDD_SPI select, must be LOW. Pull-down fitted as insurance.")
    R("R77", "10k", "STRAP46", "GND", notes="GPIO46 = ROM message / boot mode")
    C("SWB", "SW_PUSH", "BOOT", {"1": "BOOT0", "2": "GND"})
    R("R78", "10k", "BOOT0", "+3V3")
    C("J5", "HDR6", "programming / recovery (INTERNAL ONLY)",
      {"1": "+3V3", "2": "GND", "3": "U0TXD", "4": "U0RXD",
       "5": "ESP_EN", "6": "BOOT0"},
      notes="NEVER on the panel: it is an un-isolated ground tie. D-5: the "
            "CP2102N + USB-C subsystem is out of scope for spec_version 1.")
    C("J8", "HDR8", "W5500 sub-board (D-5)",
      {"1": "+3V3", "2": "GND", "3": "SPI_B_SCK", "4": "SPI_B_MOSI",
       "5": "SPI_B_MISO", "6": "nCS_W5500", "7": "nRST_W5500", "8": "nINT_W5500"},
      notes="D-5: CONTROLLER_AND_POWER.md 1.3 specifies an ON-BOARD W5500 with "
            "magnetics and an RJ45. Building it is G1 work; this header is the "
            "honest board boundary until then, NOT a design decision.")
    R("R79", "10k", "nCS_W5500", "+3V3")
    R("R80", "10k", "nRST_W5500", "+3V3")
    R("R81", "10k", "nINT_W5500", "+3V3")
    R("R82", "10k", "nSYNC_DAC", "+3V3")
    R("R83", "10k", "nLOAD_165", "+3V3")
    R("R84", "10k", "SPI_A_MISO", "GND")
    R("R85", "10k", "nALERT_ADC", "+3V3_A")

    # ---- status readback.  Two cascaded shift registers, and TWO pattern bits
    #      so that a DEAD REGISTER IS DETECTABLE.  Bits 10/11 read the ACTUAL
    #      level at each module's pin 4, not the commanded state -- which
    #      catches a stuck open-drain output, a lifted pull-up and a shorted
    #      /ON net, none of which any command-side check can see.
    #      NOTHING IN THE INTERLOCK READS THESE. If the register dies, only
    #      firmware's KNOWLEDGE degrades, and the response to degraded
    #      knowledge is to stop the heartbeat.
    C("U45", "74LVC165", "74LVC165A",
      {"1": "nLOAD_165", "2": "SPI_A_SCK", "15": "GND", "10": "SR_CHAIN",
       "11": "MODE_A_BUF", "12": "MODE_B_BUF", "13": "K1_DRV_RB", "14": "K2_DRV_RB",
       "3": "INTLK_BUF", "4": "RAIL_OK_BUF", "5": "COLD_A_BUF", "6": "COLD_B_BUF",
       "9": "SPI_A_MISO", "7": "SR1_NQ7", "8": "GND", "16": "+3V3"})
    C("U46", "74LVC165", "74LVC165A",
      {"1": "nLOAD_165", "2": "SPI_A_SCK", "15": "GND", "10": "GND",
       "11": "OVP_RB_BUF", "12": "nON_P_RB", "13": "nON_N_RB", "14": "VSET_OVR_P_B",
       "3": "VSET_OVR_N_B", "4": "BRANCH_LIVE_P_B", "5": "+3V3", "6": "GND",
       "9": "SR_CHAIN", "7": "SR2_NQ7", "8": "GND", "16": "+3V3"},
      notes="bits 14/15 are tied HIGH/LOW as a pattern: any other value means "
            "the readback path is untrustworthy => hard fault => stop the "
            "heartbeat.")
    C("TP12", "TP", "SR1_NQ7", {"1": "SR1_NQ7"})
    C("TP13", "TP", "SR2_NQ7", {"1": "SR2_NQ7"})
    # *** FINDING. CONTROLLER_AND_POWER.md 2.4 puts "K1_AUX / K2_AUX -- relay
    # armature position" in status bits 2 and 3. A Pickering 67-1-C is a
    # ONE-FORM-C part: there is NO spare contact to read the armature with.
    # What is fitted instead reads the COIL DRIVE, which is strictly weaker --
    # it shows what was COMMANDED, not where the armature went, and therefore
    # cannot see a stuck armature at all. Reported, not silently relabelled.
    R("R93", "10k", "K1_COIL_LO", "K1_DRV_RB",
      notes="COIL-DRIVE readback, NOT armature position -- see the note above")
    R("R94", "10k", "K2_COIL_LO", "K2_DRV_RB", notes="as R93")
    C("TP14", "TP", "K1_DRV_RB", {"1": "K1_DRV_RB"})
    C("TP15", "TP", "K2_DRV_RB", {"1": "K2_DRV_RB"})
    C("U47", "74LVC14", "74LVC14A",
      {"1": "MODE_A", "2": "MODE_A_N",
       "3": "MODE_A_N", "4": "MODE_A_BUF",
       "5": "MODE_B", "6": "MODE_B_N",
       "9": "MODE_B_N", "8": "MODE_B_BUF",
       "11": "OVP_Q", "10": "OVP_Q_N",
       "13": "OVP_Q_N", "12": "OVP_RB_BUF",
       "7": "GND", "14": "+3V3"},
      notes="LVC at VCC = 3.3 V is 5 V-tolerant on its inputs [recalled], which "
            "is what lets a 3.3 V part read the 5 V interlock domain with no "
            "translator. Double inversion so the ESP32 reads TRUE POLARITY.")
    C("U48", "74LVC14", "74LVC14A",
      {"1": "INTLK", "2": "INTLK_N",
       "3": "INTLK_N", "4": "INTLK_BUF",
       "5": "RAIL_OK", "6": "RAIL_OK_N",
       "9": "RAIL_OK_N", "8": "RAIL_OK_BUF",
       "11": "COLD_A", "10": "COLD_A_N",
       "13": "COLD_A_N", "12": "COLD_A_BUF",
       "7": "GND", "14": "+3V3"})
    C("U49", "74LVC14", "74LVC14A",
      {"1": "COLD_B", "2": "COLD_B_N",
       "3": "COLD_B_N", "4": "COLD_B_BUF",
       "5": "VSET_OVR_P", "6": "VSET_OVR_P_N",
       "9": "VSET_OVR_P_N", "8": "VSET_OVR_P_B",
       "11": "VSET_OVR_N", "10": "VSET_OVR_N_N",
       "13": "VSET_OVR_N_N", "12": "VSET_OVR_N_B",
       "7": "GND", "14": "+3V3"})
    C("U51", "74LVC14", "74LVC14A",
      {"1": "BRANCH_LIVE_P", "2": "BLP_N",
       "3": "BLP_N", "4": "BRANCH_LIVE_P_B",
       "5": "BRANCH_LIVE_N", "6": "BLN_N",
       "9": "BLN_N", "8": "BRANCH_LIVE_N_B",
       "11": "nON_P_TAP", "10": "nON_P_N",
       "13": "nON_P_N", "12": "nON_P_RB",
       "7": "GND", "14": "+3V3"},
      notes="pin 11 taps the REAL level at U1 pin 4, level-limited by the "
              "series resistor R86 -- not the commanded state.")
    R("R86", "100k", "nON_P", "nON_P_TAP", notes="limits the 5 V-domain tap current")
    C("U52", "74LVC14", "74LVC14A",
      {"1": "nON_N", "2": "nON_N_N",
       "3": "nON_N_N", "4": "nON_N_RB",
       "5": "BRANCH_LIVE_N_B", "6": "LVC_SP1",
       "9": "GND", "8": "LVC_SP2",
       "11": "GND", "10": "LVC_SP3",
       "13": "GND", "12": "LVC_SP4",
       "7": "GND", "14": "+3V3"})
    for n in ("LVC_SP1", "LVC_SP2", "LVC_SP3", "LVC_SP4", "nON_P_TAP",
              "MODE_A_RB", "MODE_B_RB", "OVP_RB"):
        C("TP_%s" % n, "TP", n, {"1": n})
    R("R87", "10k", "MODE_A_RB", "GND")
    R("R88", "10k", "MODE_B_RB", "GND")
    R("R89", "10k", "OVP_RB", "GND")
    R("R90", "0R", "MODE_A_BUF", "MODE_A_RB",
      notes="the direct GPIO copy of a bit that is ALSO in the shift register: "
            "a disagreement means one of the two paths is dead")
    R("R91", "0R", "MODE_B_BUF", "MODE_B_RB")
    R("R92", "0R", "OVP_RB_BUF", "OVP_RB")

    # ============================================ 9.11  PANEL INDICATION
    # The HV PRESENT and FAULT lamps are driven from HARDWARE interlock
    # signals, never from a GPIO: a firmware-driven HV lamp lies in exactly
    # the fault where you need it.
    for i, (name, src, rail) in enumerate((
            ("HV_PRESENT", "ARM_OUTEN", "+5V_MOD"),
            ("FAULT", "OVP_Q", "+5V_MOD"),
            ("MODE_PB", "MODE_A_BUF", "+3V3"),
            ("MODE_UNI", "MODE_B_BUF", "+3V3"))):
        R("RLED%d" % (i + 1), "1k", rail, "LEDA_%s" % name)
        C("DLED%d" % (i + 1), "LED", name, {"2": "LEDA_%s" % name,
                                            "1": "LEDK_%s" % name})
        C("QLED%d" % (i + 1), "Q_NMOS", "2N7002",
          {"1": src, "2": "GND", "3": "LEDK_%s" % name})
    R("RLED5", "1k", "+3V3", "LEDA_NET")
    C("DLED5", "LED", "NET", {"2": "LEDA_NET", "1": "LEDK_NET"})
    C("QLED5", "Q_NMOS", "2N7002", {"1": "LED_NET", "2": "GND", "3": "LEDK_NET"})

    # ==================================== 9.12  DNP AND MECHANICAL-ONLY PARTS
    # Three kinds of part that exist on the board without being fitted, or
    # without being electrically present at all. Each one is here because a
    # design document names a specific condition under which it is needed --
    # a DNP footprint that was never laid out cannot be fitted later.

    # ---- (i) the auto-reset jumper, SHIPPED REMOVED.
    # The standard CP2102N auto-reset circuit drives EN and GPIO0 from
    # DTR/RTS, so ANY host program that opens the serial port resets the
    # ESP32 -- and HV then drops in 62-165 ms as the heartbeat pump decays.
    # That is CORRECT behaviour and it will look like a fault the first time
    # it happens. Fit the pads, ship the jumper off.
    C("JP1", "HDR2", "AUTO-RESET (ship REMOVED)",
      {"1": "ESP_EN", "2": "AUTORST_EN"}, dnp=True,
      notes="DNP BY DESIGN, not by omission. Fitting it makes 'opening a "
            "terminal drops HV' the normal behaviour of the instrument.")
    R("R95", "10k", "AUTORST_EN", "+3V3", dnp=True,
      notes="only meaningful with JP1 fitted")

    # ---- (ii) the switched dump, NOT FITTED, with a falsifiable condition.
    # MONITOR_AND_BLEED.md 7.6 recommends against a crowbar and says exactly
    # when to change its mind: fit one if a bench measurement pushes
    # discharge-to-45 V beyond ~2 s. It must then be a THIRD Form-C relay
    # whose NC position carries the dump (connected when DE-ENERGISED), never
    # a normally-open crowbar -- because a fail-safe crowbar is hot-switched
    # by design on every emergency operation, on the one contact that is never
    # exercised in normal use.
    for X, node in (("A", "HV_OUT_A"), ("B", "HV_OUT_B")):
        C("K%s" % ("3" if X == "A" else "4"), "RELAY_HV", "67-1-C-5/5D",
          {"A1": "+5V_COIL", "A2": "DUMP_COIL_%s" % X,
           "11": node, "12": "HV_OUT_%s_DUMP" % X}, nc=["14"],
          dnp=True,
          notes="DNP. NC position carries the dump, so the de-energised state "
                "is 'dumped'. Fit ONLY on the bench result named in "
                "MONITOR_AND_BLEED.md 7.6; fitting both takes the 5 V rail to "
                "~8.4 W, outside the enclosure's ventilation band.",
          extra={"FitCondition": "discharge to 45 V measured > 2 s"})
        R("R_DUMP_%s" % X, "10k", "HV_OUT_%s_DUMP" % X, "GND",
          pclass="R_HV_AXIAL", dnp=True,
          notes="SA-12: 1.5*Inom*R = 7.5 V, well under the 60 V touch-safe "
                "threshold. A 1 MOhm 'dump' would leave a 750 V clamp.")
        C("QD%s" % X, "Q_NMOS_COIL", ">=300mA NFET",
          {"1": "DUMP_EN_%s" % X, "2": "GND", "3": "DUMP_COIL_%s" % X}, dnp=True)
        R("RD%s1" % X, "100k", "DUMP_EN_%s" % X, "GND", dnp=True)
        R("RD%s2" % X, "100k", "DUMP_EN_%s" % X, "REL_EN_%s" % ("P" if X == "A" else "N"),
          dnp=True, notes="dump follows the relay enable: dumped whenever the "
                          "node is deselected")
    # mark the dump resistors so SA-12 is a LIVE assertion, not a vacuous one
    for c in _COMPONENTS:
        if c["ref"].startswith("R_DUMP_"):
            c["fields"]["Role"] = "dump"

    # ---- (iii) the VSET pull-down contingency.
    # SETPOINT_PATH.md 8.1: the module's internal 10 kOhm VSET pull-up has NO
    # PUBLISHED TOLERANCE, and the 60 V open-clamp residual depends on it
    # inversely -- the criterion breaks at 7.83 kOhm, i.e. -21.7 %. If the
    # bench measurement comes back pessimistic, the fix is to drop the
    # pull-down from 500 to 302 ohms. Lay the pads now.
    for M in ("P", "N"):
        R("RPD3_%s" % M, "604R 0.1%", "VSET_%s" % M, "GND", dnp=True,
          notes="DNP. Fit (with RPD4) only if the measured internal pull-up is "
                "below ~7.8 kOhm. MEASURABLE-NOW on the modules in hand.",
          )
        R("RPD4_%s" % M, "604R 0.1%", "VSET_%s" % M, "GND", dnp=True,
          notes="DNP, ARCH-18 partner of RPD3_%s" % M)

    # ---- (iv) mounting holes -- mechanically real, electrically NOT absent
    #      in the LV region (they are the chassis earth bond, and this board's
    #      GND is the HV return) and electrically ABSENT in the HV region
    #      (where a plated, earthed fixing would be a clearance violation).
    for i in (1, 2, 3, 4):
        C("MH%d" % i, "MTG_PAD", "M3 earth bond", {"1": "GND"},
          notes="plated and bonded: this is the safety earth path, not a fixing")
    for i in (5, 6):
        C("MH%d" % i, "MTG_NOPAD", "M3 HV-region fixing", {},
          notes="NON-PLATED. Zero pins by construction -- a bonded fixing in "
                "the HV region would violate the clearance rule it sits inside.")

    return _COMPONENTS


# ===========================================================================
# 10.  PUBLIC API
# ===========================================================================
NET_NOTES = {
    "HV_M": "Exists ONLY to split the mode switch's 2000 V stress into two "
            "1000 V gaps. Deleting it as 'redundant wiring' doubles the "
            "insulation requirement of a panel part and will not look wrong.",
    "HV_SW_G": "S3's common. HV-classed on purpose: an S3 weld or an open R_G "
               "puts a nominally-grounded node at full output.",
    "VCLAMP_STAR": "THE CLAMP. U4's V+ pin. A rail-to-rail output stage cannot "
                   "exceed its own rail; nothing downstream of U4 touches +3V3 "
                   "or +5V. Exactly one driver (U3) is permitted.",
    "nON_P": "ACTIVE LOW, and an OPEN /ON MEANS HV ON. Its pull-up must go to "
             "the module's OWN +VIN so it cannot outlive the module's supply.",
    "nON_N": "as nON_P.",
    "VSET_P": "An OPEN VSET NODE COMMANDS FULL SCALE (internal 10k pull-up to "
              "Vref). A node pulled to 3.3 V on a 2.5 V-Vref module commands "
              "~1320 V on an input the datasheet says is not internally limited.",
    "VSET_N": "as VSET_P.",
    "MODE_A": "Originates at the PANEL SWITCH's aux pole S4 and nowhere else. "
              "No ESP32 output may reach it. Read-only to firmware.",
    "MODE_B": "Originates at the PANEL SWITCH's aux pole S5 and nowhere else.",
    "MODE_VALID": "MODE_A XOR MODE_B. (0,0) and (1,1) both mean 'no valid mode' "
                  "and both drop ARM.",
    "COIL_EN": "C-1. The coil rail has its OWN fail-safe switch, so both-coils-"
               "off is reachable and the weld self-test can execute.",
    "OVP_SET": "Wire-OR of eight protection comparators. The latch it sets "
               "powers up TRIPPED and can only be cleared by an EDGE.",
}


def build_board():
    """The ONE source of truth for what connects to what.
    No CAD file, no coordinate, no layer. Pure connectivity + identity."""
    return {
        "meta": {"board": PROJECT, "rev": REV, "spec_version": SPEC_VERSION},
        "components": _build(),
        "netclasses": netclasses(),
        "net_notes": dict(NET_NOTES),
    }


def nets(board=None):
    """{net: sorted [(ref, pad), ...]}."""
    b = board or build_board()
    if id(b) in _NETS_CACHE:
        return _NETS_CACHE[id(b)]
    out = {}
    for c in b["components"]:
        for pad, net in c["pins"].items():
            if net is None:
                continue
            out.setdefault(net, []).append((c["ref"], pad))
    _NETS_CACHE[id(b)] = {n: sorted(v) for n, v in out.items()}
    return _NETS_CACHE[id(b)]


def netclass_of(net, board=None):
    """Which netclass a net lands in. Default is the FALLBACK, not a pattern."""
    b = board or build_board()
    eff = effective_net_name(net)
    hits = []
    for name, ncdef in b["netclasses"].items():
        if name == "Default":
            continue
        for pat in ncdef["patterns"]:
            if _glob_to_re(pat).match(eff):
                hits.append(name)
                break
    if len(hits) == 1:
        return hits[0]
    if not hits:
        return "Default"
    return hits            # a list means AMBIGUOUS -- the checker fails on it


# --- signed potential ranges for the HV nets, by structural derivation -----
V_NOM = 1000.0


def _routing_edges(k1, k2, mode):
    """Undirected edges that carry ROUTING current in one mechanical state."""
    e = []
    for ref, st in (("K1", "E" if k1 else "NE"), ("K2", "E" if k2 else "NE")):
        e.append((ref, CONTACT_MODEL[ref][st]))
    for ref in ("SW1A", "SW1B", "SW1C"):
        e.append((ref, CONTACT_MODEL[ref][mode]))
    return e


BLEED_ROLES = ("bleed", "stub")


def bleed_element_refs():
    """Refs of the elements that are actually BLEEDS. A 200 MOhm monitor string
    is a resistive path to ground and it is NOT a discharge path -- treating it
    as one is how assertion (b) passes on a board whose bleed has been deleted."""
    out = set()
    for sid, st in HV_STRINGS.items():
        if st["role"] not in BLEED_ROLES:
            continue
        for sub in SUBSTRING_IDS[:st["n_par"]]:
            for k in range(1, st["n_series"] + 1):
                out.add("R%s%s%d" % (sid, sub.upper(), k))
    return out


def _adjacency(board, k1, k2, mode, include_resistive):
    """net -> set(net) reachable in one hop, in this mechanical state."""
    comps = {c["ref"]: c for c in board["components"]}
    adj = {}

    def link(a, b):
        if a is None or b is None:
            return
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    for ref, pairs in _routing_edges(k1, k2, mode):
        for p, q in pairs:
            link(comps[ref]["pins"].get(p), comps[ref]["pins"].get(q))
    if include_resistive == "all":
        allowed = {c["ref"] for c in board["components"]
                   if c["fields"]["PartClass"].startswith("R_")}
        for c in board["components"]:
            if c["ref"] in allowed and len(c["pins"]) == 2:
                a, b = list(c["pins"].values())
                link(a, b)
    elif include_resistive:
        allowed = bleed_element_refs() | ROUTING_RESISTORS
        for c in board["components"]:
            if c["ref"] in allowed and len(c["pins"]) == 2:
                a, b = list(c["pins"].values())
                link(a, b)
    else:
        for ref in ROUTING_RESISTORS:
            a, b = list(comps[ref]["pins"].values())
            link(a, b)
    return adj


def _reach(adj, start):
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(adj.get(n, ()))
    return seen


def net_potential_ranges(board, permit_p, permit_n, k1, k2, mode):
    """Signed (vmin, vmax) per net in one reachable state, derived from the
    routing graph rather than asserted. A node reachable from an ENERGISED
    module carries that module's polarity; anything else is bled to ~0."""
    adj = _adjacency(board, k1, k2, mode, include_resistive=False)
    pos = _reach(adj, "HV_POS") if permit_p else set()
    neg = _reach(adj, "HV_NEG") if permit_n else set()
    rng = {}
    for net in nets(board):
        lo = hi = 0.0
        if net in pos:
            hi = V_NOM
        if net in neg:
            lo = -V_NOM
        rng[net] = (lo, hi)
    return rng


# ===========================================================================
# 11.  SYMBOL CROSS-CHECK -- against the .kicad_sym ON DISK
# ===========================================================================
_SYM_CACHE = {}
_LIB_CACHE = {}           # path -> parsed top-level symbol blocks


def _lib_path(nickname):
    if nickname in ("iseg",):
        return os.path.join(LIBDIR, "iseg.kicad_sym")
    return os.path.join(KICAD_SYMBOLS, nickname + ".kicad_sym")


def _top_level_symbol_blocks(text):
    out, i, n = {}, 0, len(text)
    while True:
        m = re.search(r'^\t\(symbol "([^"]+)"', text[i:], re.M)
        if not m:
            break
        start, name = i + m.start(), m.group(1)
        depth, j, instr = 0, start, False
        while j < n:
            ch = text[j]
            if instr:
                if ch == "\\":
                    j += 2
                    continue
                if ch == '"':
                    instr = False
            elif ch == '"':
                instr = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        out[name] = text[start:j]
        i = j
    return out


def symbol_pin_numbers(symref):
    """Set of pin numbers the SYMBOL ON DISK actually has. Follows `extends`.
    This is the INDEPENDENT source of truth: board_spec.py's pin maps are
    hand-authored intent, this is what KiCad will really instantiate."""
    if symref in _SYM_CACHE:
        return _SYM_CACHE[symref]
    nickname, name = symref.split(":", 1)
    path = _lib_path(nickname)
    if not os.path.exists(path):
        raise IOError("symbol library not found: %s" % path)
    if path not in _LIB_CACHE:
        with open(path, "r", encoding="utf-8") as f:
            _LIB_CACHE[path] = _top_level_symbol_blocks(f.read())
    blocks = _LIB_CACHE[path]
    seen = set()
    while name in blocks and name not in seen:
        seen.add(name)
        body = blocks[name]
        nums = set(re.findall(r'\(number "([^"]*)"', body))
        if nums:
            _SYM_CACHE[symref] = nums
            return nums
        ext = re.search(r'\(extends "([^"]+)"\)', body)
        if not ext:
            break
        name = ext.group(1)
    if name in blocks or symref.split(":", 1)[1] in blocks:
        return set()          # legal: e.g. a non-plated mounting hole
    raise KeyError("symbol %s was not found in %s" % (symref, path))


# ===========================================================================
# 12.  CHECKS
# ===========================================================================
def check_structure(board):
    p = []
    refs = [c["ref"] for c in board["components"]]
    if len(refs) != len(set(refs)):
        p.append("duplicate refdes")
    prefixes = ("U", "K", "R", "C", "L", "D", "J", "TP", "SW", "F", "MH", "Q", "Y",
                "FB", "#PWR", "#FLG", "DLED", "QLED", "RLED")
    for c in board["components"]:
        if not any(c["ref"].startswith(x) for x in prefixes):
            p.append("%s: refdes prefix not in the INTERFACES.md 1.2 list" % c["ref"])
        for k in ("ref", "sym", "val", "fp", "pins", "dnp", "nc", "fields"):
            if k not in c:
                p.append("%s: missing key %r" % (c["ref"], k))
        if "MPN_STATUS" not in c["fields"]:
            p.append("%s: no MPN_STATUS (I-4)" % c["ref"])
        for pad in c["nc"]:
            if pad not in c["pins"] or c["pins"][pad] is not None:
                p.append("%s: nc pad %s must appear in pins with net None (I-3)"
                         % (c["ref"], pad))
    return p


def check_min_two_connections(board):
    """A net with one pin is a typo, not a net."""
    return ["net %s has %d connection(s); every net needs >= 2  [%s]"
            % (n, len(v), ", ".join("%s.%s" % t for t in v))
            for n, v in sorted(nets(board).items()) if len(v) < 2]


def check_symbol_pins(board):
    """Cross-check EVERY pin map against the .kicad_sym on disk -- not against
    our own assumptions. Both directions: no invented pin, no forgotten pin."""
    p = []
    for c in board["components"]:
        try:
            have = symbol_pin_numbers(c["sym"])
        except Exception as e:                                   # noqa: BLE001
            p.append("%s: cannot read symbol %s (%s)" % (c["ref"], c["sym"], e))
            continue
        mine = set(c["pins"].keys())
        for extra in sorted(mine - have):
            p.append("%s (%s): pin %r is NOT on the symbol" % (c["ref"], c["sym"], extra))
        for missing in sorted(have - mine):
            p.append("%s (%s): symbol pin %r is not in the pin map (list it in "
                     "`nc` if it is deliberately unconnected -- omission is "
                     "indistinguishable from a mistake, I-3)"
                     % (c["ref"], c["sym"], missing))
    return p


# --- pin SEMANTICS, using the symbol's own pin NAMES as an independent axis --
# The pin-NUMBER check cannot catch a pin map that swaps two pads the symbol
# both has -- e.g. putting the module's HV output on pad 5 (VMON) and VMON on
# pad 6 (HV). That mutation produces a netlist that passes every other check in
# this repo and a board that is perfectly, self-consistently wrong. It is the
# exact defect class docs/PIN_MAPS.md exists for, and this is the only
# machine-checkable part of it: the symbol on disk carries pin NAMES as well as
# numbers, so the NAME can be cross-checked against the KIND of net attached.
#
# pin-name regex -> predicate the attached net must satisfy
PIN_SEMANTICS = {
    "iseg:APS_HV_MODULE_P": [
        (r"^HV$", lambda net: net is not None and hv_domain_of(net) in HV_DOMAINS,
         "the module's 1 kV output must be on an HV routing net"),
        (r"^VMON$", lambda net: net is not None and not is_hv_net(net),
         "VMON is a LOW-VOLTAGE monitor output and must NOT be on an HV net"),
        (r"^VSET$", lambda net: net is not None and net.startswith("VSET_"),
         "VSET must be on a VSET_* net"),
        (r"^GND$", lambda net: net == "GND", "module GND pins must be on GND"),
        (r"^\+VIN$", lambda net: net is not None and net.startswith("VIN_"),
         "+VIN must come from that module's own load switch"),
        (r"^~\{ON\}$", lambda net: net is not None and net.startswith("nON_"),
         "/ON must be on an active-low nON_* net"),
    ],
    "Relay:Relay_SPDT": [
        (r"^$", lambda net: True, ""),   # generic symbol: names are empty
    ],
}
PIN_SEMANTICS["iseg:APS_HV_MODULE_N"] = PIN_SEMANTICS["iseg:APS_HV_MODULE_P"]


def _symbol_pin_names(symref):
    nickname, name = symref.split(":", 1)
    path = _lib_path(nickname)
    if path not in _LIB_CACHE:
        with open(path, "r", encoding="utf-8") as f:
            _LIB_CACHE[path] = _top_level_symbol_blocks(f.read())
    blocks = _LIB_CACHE[path]
    seen = set()
    while name in blocks and name not in seen:
        seen.add(name)
        body = blocks[name]
        pairs = re.findall(
            r'\(name "([^"]*)"\s*\n\s*\(effects[\s\S]{0,240}?\)\s*\n\s*\)\s*\n'
            r'\s*\(number "([^"]*)"', body)
        if pairs:
            return {num: nm for nm, num in pairs}
        ext = re.search(r'\(extends "([^"]+)"\)', body)
        if not ext:
            break
        name = ext.group(1)
    return {}


def check_pin_semantics(board):
    p = []
    for c in board["components"]:
        rules = PIN_SEMANTICS.get(c["sym"])
        if not rules:
            continue
        names = _symbol_pin_names(c["sym"])
        for pad, net in c["pins"].items():
            nm = names.get(pad, "")
            for pat, ok, why in rules:
                if re.match(pat, nm) and not ok(net):
                    p.append("%s pad %s (symbol pin name %r) is on net %r -- %s"
                             % (c["ref"], pad, nm, net, why))
    return p


def check_netclass_coverage(board):
    """Every net lands in exactly one class, matched against the name KiCad
    will really emit. Catches the glob trap: a pattern without the sheet
    wildcard matches NOTHING and drops a 1 kV net into Default."""
    p = []
    for name, ncdef in board["netclasses"].items():
        for f in NETCLASS_FIELDS_REQUIRED:
            if f not in ncdef:
                p.append("netclass %s: missing field %r -- a PCB-only netclass "
                         "silently breaks eeschema connectivity for every net "
                         "in it, and kicad-cli never reads .kicad_pro" % (name, f))
    for net in sorted(nets(board)):
        cls = netclass_of(net, board)
        if isinstance(cls, list):
            p.append("net %s matches %d netclass patterns %s; must be exactly one (I-5)"
                     % (net, len(cls), cls))
            continue
        if is_hv_net(net) and cls == "Default":
            p.append("HV net %s fell through to Default (0.2 mm clearance). "
                     "Check the pattern has the '*/' sheet wildcard -- KiCad "
                     "emits '%s', not '%s'." % (net, effective_net_name(net), net))
        if not is_hv_net(net) and cls.startswith("HV_"):
            p.append("non-HV net %s landed in HV class %s (SA-10)" % (net, cls))
    return p


def check_hv_ratings(board):
    """No HV net may touch a part not rated for it, per the declared per-part
    voltage-rating table in board_spec_parts.py."""
    p = []
    # 12a. per-element working voltage inside every HV string
    for sid, s in sorted(HV_STRINGS.items()):
        wv = element_working_voltage(sid)
        lim = part(s["pkg"])["vmax"] * derate_of(s["pkg"])
        if wv > lim + 1e-9:
            p.append("HV string %s: %.1f V per element against a derated limit "
                     "of %.1f V (%s)" % (sid, wv, lim, s["pkg"]))
        if s["n_par"] < 2:
            p.append("HV string %s is a single series chain; NUM-09/SA-9 require "
                     "two parallel strings" % sid)
    # 12b. every other component, over every REACHABLE mechanical state
    string_refs = set()
    for sid, s in HV_STRINGS.items():
        for sub in SUBSTRING_IDS[:s["n_par"]]:
            for k in range(1, s["n_series"] + 1):
                string_refs.add("R%s%s%d" % (sid, sub.upper(), k))
    worst = {}
    for permit_p, permit_n, k1, k2, mode in reachable_states(board):
        rng = net_potential_ranges(board, permit_p, permit_n, k1, k2, mode)
        for c in board["components"]:
            if c["ref"] in string_refs:
                continue
            live = [n for n in c["pins"].values() if n is not None]
            if not any(is_hv_net(n) for n in live):
                continue
            hi = max(rng[n][1] for n in live)
            lo = min(rng[n][0] for n in live)
            d = hi - lo
            if d > worst.get(c["ref"], (-1, None))[0]:
                worst[c["ref"]] = (d, (permit_p, permit_n, k1, k2, mode))
    # 12c. a blunt, fault-tolerant screen the derived walk cannot replace
    for c in board["components"]:
        if c["ref"] in string_refs:
            continue
        pc = c["fields"]["PartClass"]
        on_hv_node = any(n is not None and not n.startswith("HVDIV_")
                         and hv_domain_of(n) in HV_DOMAINS
                         for n in c["pins"].values())
        if on_hv_node and part(pc)["vmax"] < V_NOM:
            p.append("%s (%s, rated %s V) sits on an HV routing node but is not "
                     "rated for Vnom = %.0f V. The derived normal-state walk "
                     "cannot see this: parts like R_G are rated for a WELDED "
                     "contact, not for normal operation."
                     % (c["ref"], pc, c["fields"]["V_RATING"], V_NOM))
    for ref, (d, st) in sorted(worst.items()):
        c = [x for x in board["components"] if x["ref"] == ref][0]
        pc = c["fields"]["PartClass"]
        lim = part(pc)["vmax"] * derate_of(pc)
        if d > lim + 1e-9:
            p.append("%s (%s, rated %s V, derated %.0f V) sees %.0f V across its "
                     "pins in state permit=(%d,%d) K=(%d,%d) mode=%s"
                     % (ref, c["fields"]["PartClass"], c["fields"]["V_RATING"],
                        lim, d, st[0], st[1], st[2], st[3], st[4]))
    return p


# ---------------------------------------------------------------- logic model
def _logic_index(board):
    comps = {c["ref"]: c for c in board["components"]}
    driver = {}          # net -> (gatekey, func, [input nets])
    for key, (func, ins, out) in LOGIC.items():
        ref = re.match(r"^(U\d+)", key).group(1)
        c = comps[ref]
        onet = c["pins"][out]
        innets = [c["pins"][i] for i in ins]
        if onet in driver:
            raise ValueError("net %s driven by two gates (%s and %s)"
                             % (onet, driver[onet][0], key))
        driver[onet] = (key, func, innets)
    return driver


_OPS = {
    "AND": lambda v: int(all(v)), "OR": lambda v: int(any(v)),
    "NAND": lambda v: int(not all(v)), "NOR": lambda v: int(not any(v)),
    "XOR": lambda v: int(sum(v) % 2 == 1),
    "NOT": lambda v: int(not v[0]), "BUF": lambda v: int(bool(v[0])),
}


def eval_net(net, driver, assign, depth=0):
    if depth > 40:
        raise ValueError("combinational loop at %s" % net)
    if net in LOGIC_CONSTANTS:
        return LOGIC_CONSTANTS[net]
    if net in assign:
        return assign[net]
    if net not in driver:
        raise KeyError("net %s is neither a primary input nor a gate output" % net)
    _, func, ins = driver[net]
    return _OPS[func]([eval_net(i, driver, assign, depth + 1) for i in ins])


def logic_primary_inputs(board, targets=None):
    """Primary inputs of the gate array. With `targets`, only the SUPPORT SET
    of those nets -- the inputs they transitively depend on.

    Enumerating the whole array is 2^19; enumerating a target's support set is
    2^10 for the permissives. Same exhaustiveness over the thing being proved,
    ~500x less work, and it makes the mutation test runnable."""
    driver = _logic_index(board)
    if targets is None:
        ins = {n for _, (_, _, innets) in driver.items() for n in innets
               if n not in driver and n not in LOGIC_CONSTANTS}
        return driver, sorted(ins)
    ins, stack, seen = set(), list(targets), set()
    while stack:
        n = stack.pop()
        if n in seen or n in LOGIC_CONSTANTS:
            continue
        seen.add(n)
        if n in driver:
            stack.extend(driver[n][2])
        else:
            ins.add(n)
    return driver, sorted(ins)


def reachable_states(board):
    """Every (PERMIT_P, PERMIT_N, K1, K2, mode) the HARDWARE can actually be in.

    The mode comes from the physical switch, the permits come from evaluating
    the real gate array, and the relay contacts are free because they are
    LATCHED (a relay can be held closed after its permit drops -- that is the
    designed cold-break behaviour). This is what makes the routing assertions
    below statements about the built circuit and not about a diagram."""
    key = id(board)
    if key in _STATES_CACHE:
        return _STATES_CACHE[key]
    driver, prim = logic_primary_inputs(board, ["PERMIT_P", "PERMIT_N"])
    seen = set()
    for bits in itertools.product((0, 1), repeat=len(prim)):
        assign = dict(zip(prim, bits))
        ma, mb = assign.get("MODE_A", 0), assign.get("MODE_B", 0)
        mode = "PB" if (ma, mb) == (1, 0) else ("UNI" if (ma, mb) == (0, 1) else "SAFE")
        pp = eval_net("PERMIT_P", driver, assign)
        pn = eval_net("PERMIT_N", driver, assign)
        for k1 in (0, 1):
            for k2 in (0, 1):
                seen.add((pp, pn, k1, k2, mode))
    _STATES_CACHE[key] = sorted(seen)
    return _STATES_CACHE[key]


# ============================ DOMAIN SAFETY ASSERTION (a) ===================
def assert_a_no_shared_output_node(board):
    """(a) NO SINGLE NET CAN CONNECT BOTH MODULES TO THE SAME OUTPUT NODE.

    G0-A4 restated form: it must be impossible for both modules to be connected
    to the SAME output node simultaneously. In pseudo-bipolar that forbids the
    both-enabled state exactly as before; in dual-unipolar it is satisfied
    STRUCTURALLY because the two modules are on physically different nodes.

    This is proved by combining the two models: the gate array decides which
    (PERMIT_P, PERMIT_N, mode) triples exist, and the contact model decides
    which output node each module reaches. A module with PERMIT = 0 has neither
    +VIN nor a low /ON and therefore makes no HV, so it cannot contribute."""
    p = []
    outputs = ("HV_OUT_A", "HV_OUT_B")
    for pp, pn, k1, k2, mode in reachable_states(board):
        if not (pp and pn):
            continue
        adj = _adjacency(board, k1, k2, mode, include_resistive=False)
        rp, rn = _reach(adj, "HV_POS"), _reach(adj, "HV_NEG")
        for o in outputs:
            if o in rp and o in rn:
                p.append("(a) VIOLATED: with PERMIT_P=PERMIT_N=1, K1=%d K2=%d, "
                         "mode=%s, BOTH energised modules reach %s"
                         % (k1, k2, mode, o))
    return p


def assert_a_gate_structure(board):
    """(a) part 2 -- the gate structure itself, read off the netlist.

    PERMIT_P . PERMIT_N must IMPLY the physical unipolar decode (MODE_A=0,
    MODE_B=1). Rewiring one gate input breaks this."""
    p = []
    tgts = ["PERMIT_P", "PERMIT_N", "nON_P", "nON_N"]
    driver, prim = logic_primary_inputs(board, tgts)
    for tgt in ("PERMIT_P", "PERMIT_N", "nON_P", "nON_N", "MODE_VALID", "MODE_UNI"):
        if tgt not in driver:
            p.append("(a) net %s is not produced by the declared gate array" % tgt)
    if p:
        return p
    for bits in itertools.product((0, 1), repeat=len(prim)):
        a = dict(zip(prim, bits))
        both_permitted = eval_net("PERMIT_P", driver, a) and eval_net("PERMIT_N", driver, a)
        both_on = (eval_net("nON_P", driver, a) == 0) and (eval_net("nON_N", driver, a) == 0)
        if both_permitted or both_on:
            if not (a.get("MODE_A", 0) == 0 and a.get("MODE_B", 0) == 1):
                p.append("(a) VIOLATED in the GATE ARRAY: both modules "
                         "%s with MODE_A=%d MODE_B=%d (inputs %s)"
                         % ("permitted" if both_permitted else "/ON-enabled",
                            a.get("MODE_A", 0), a.get("MODE_B", 0),
                            {k: v for k, v in a.items() if v}))
                break
    return p


def assert_a_mode_decode(board):
    """(a) part 4 -- MODE-18: BOTH illegal aux states must decode INVALID.

    (0,0) is the SAFE detent, a between-detents position or two broken wires;
    (1,1) is mechanically impossible and therefore means a SHORTED aux. Both
    must give MODE_VALID = 0. A decode of the form "B means unipolar, otherwise
    bipolar" satisfies assertion (a) and still lets a shorted aux masquerade as
    a valid mode, which is why this is a separate assertion."""
    p = []
    driver, prim = logic_primary_inputs(board, ["MODE_VALID"])
    if "MODE_VALID" not in driver:
        return ["(a) MODE_VALID is not produced by the declared gate array"]
    for ma in (0, 1):
        for mb in (0, 1):
            a = {n: 0 for n in prim}
            a["MODE_A"], a["MODE_B"] = ma, mb
            v = eval_net("MODE_VALID", driver, a)
            if (ma == mb) and v:
                p.append("(a) MODE-18 VIOLATED: aux state (%d,%d) decodes "
                         "MODE_VALID = 1. (0,0) is the SAFE detent or a broken "
                         "wire; (1,1) is a SHORTED aux contact. Both must be "
                         "INVALID." % (ma, mb))
            if (ma != mb) and not v:
                p.append("(a) aux state (%d,%d) is a LEGAL mode but decodes "
                         "MODE_VALID = 0" % (ma, mb))
    return p


def assert_a_mode_origin(board):
    """(a) part 3 -- the mode permissive originates at the PHYSICAL SWITCH's
    auxiliary contacts, and NO ESP32-driven net can reach it.

    G0-A5: there is no mode relay and no MODE_CMD. If firmware could assert the
    mode, a stuck GPIO or a network command could claim 'mode 2, both modules
    permitted' while the HV routing was physically still in mode 1 -- which is
    exactly the forbidden state, reached through exactly the firmware-promise
    path the brief forbids."""
    p = []
    comps = {c["ref"]: c for c in board["components"]}
    driver = _logic_index(board)
    for mnet, pole in (("MODE_A", "SW1D"), ("MODE_B", "SW1E")):
        if mnet in driver:
            p.append("(a) %s is driven by gate %s -- it must come ONLY from the "
                     "panel switch" % (mnet, driver[mnet][0]))
        touching = {r for r, _ in nets(board).get(mnet, [])}
        if pole not in touching:
            p.append("(a) %s does not touch its aux pole %s" % (mnet, pole))
        # anything on the net that is not a passive pull, a header, a gate
        # INPUT, a buffer INPUT or the switch itself is a potential driver.
        for ref, pad in nets(board).get(mnet, []):
            cls = comps[ref]["fields"]["PartClass"]
            if ref == pole:
                continue
            if cls in ("R_LV", "HDR8", "HDR3", "HDR6", "TP", "C_LV"):
                continue
            if cls.startswith("74"):
                continue          # logic INPUTS only; outputs are in `driver`
            p.append("(a) unexpected component %s (%s) on the mode net %s"
                     % (ref, cls, mnet))
    # no ESP32 pin may sit on a mode net or drive anything that reaches one
    esp = comps["U50"]["pins"]
    for pad, net in esp.items():
        if net in ("MODE_A", "MODE_B"):
            p.append("(a) VIOLATED: ESP32 pin %s is on %s" % (pad, net))
    # forward-reachability through the gate array from every ESP32 output
    esp_out = {n for n in esp.values() if n in
               ("ARM_EN", "OUT_EN", "SEL", "HB_OUT", "nOVP_CLR", "nSYNC_DAC")}
    for mnet in ("MODE_A", "MODE_B", "MODE_VALID"):
        if mnet not in driver:
            continue
        stack, seen = [mnet], set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)                      # record BEFORE the driver test:
            if n in driver:                  # a primary input is exactly what
                stack.extend(driver[n][2])   # we are looking for here
        bad = esp_out & seen
        if bad:
            p.append("(a) VIOLATED: ESP32-driven net(s) %s reach %s through the "
                     "gate array" % (sorted(bad), mnet))
    return p


def hv_energisable_nets(board):
    """The nets that can actually exceed the touch-safe threshold, DERIVED
    rather than hand-listed: every net a live module can reach in some
    reachable state, plus every HV-string interior node whose position in the
    string puts it above the threshold.

    Deriving this instead of listing it is what keeps assertion (b) honest --
    a hand-list would silently stop covering a node the moment someone added
    one, which is exactly the enumeration defect that lets a budget 'pass' on
    an incomplete list."""
    out = set()
    for pp, pn, k1, k2, mode in reachable_states(board):
        rng = net_potential_ranges(board, pp, pn, k1, k2, mode)
        for net, (lo, hi) in rng.items():
            if max(abs(lo), abs(hi)) > TOUCH_SAFE_V:
                out.add(net)
    for sid, s in HV_STRINGS.items():
        for sub in SUBSTRING_IDS[:s["n_par"]]:
            for k in range(1, s["n_series"]):
                if string_node_potential(sid, k) > TOUCH_SAFE_V:
                    out.add(string_node_net(sid, sub, k))
    return sorted(out)


# ============================ DOMAIN SAFETY ASSERTION (b) ===================
def assert_b_discharge_paths(board):
    """(b) EVERY HV NODE has a discharge path to GND -- both output nodes and
    both module outputs, INCLUDING the output that is idle in the selected
    mode -- in EVERY mechanical state, including the unpowered default.

    Checked as reachability to GND over resistive elements plus whatever
    contacts are closed in that state. The de-energised state (K1 = K2 = 0,
    which is what the board sits in whenever coil power is absent) is included,
    and it is the one that matters most."""
    p = []
    energisable = set(hv_energisable_nets(board))
    routing_nodes = sorted(n for n in energisable if not n.startswith("HVDIV_"))
    interior = sorted(n for n in energisable if n.startswith("HVDIV_"))
    for k1 in (0, 1):
        for k2 in (0, 1):
            for mode in MODE_STATES:
                # (b1) ROUTING nodes: the path must go through a real BLEED (or
                #      a routing resistor to ground). A 200 MOhm monitor string
                #      is a resistive path to ground and is NOT a discharge path.
                bled = _reach(_adjacency(board, k1, k2, mode, True), "GND")
                for n in routing_nodes:
                    if n not in bled:
                        p.append("(b) VIOLATED: HV routing node %s has no BLEED "
                                 "path to GND with K1=%d K2=%d mode=%s "
                                 "(a monitor or COLD divider does not count)"
                                 % (n, k1, k2, mode))
                # (b2) DIVIDER INTERIOR nodes: discharged by their own string.
                allr = _reach(_adjacency(board, k1, k2, mode, "all"), "GND")
                for n in interior:
                    if n not in allr:
                        p.append("(b) VIOLATED: divider interior node %s does "
                                 "not reach GND through its own string "
                                 "(K1=%d K2=%d mode=%s)" % (n, k1, k2, mode))
    return p


# ============================ DOMAIN SAFETY ASSERTION (c) ===================
# Declared, VISIBLE exception. Both offset legs are injected from the same
# 2.500 V reference (MONITOR_AND_BLEED.md draws it that way). The property
# that actually protects COLD is that its WINDOW CENTRE is a different part
# (REF3020), so a REF5025 failure moves the node but not the threshold and
# COLD lands stuck-safe. INTERFACES.md SA-8 says "shares no COMPONENT", which
# is met: no resistor, buffer, comparator or ADC is shared.
#
# The four other exceptions, each stated with WHY it is not a defect:
#   HV_OUT_A / HV_OUT_B  -- the monitor string and the COLD string necessarily
#       hang off the SAME output node; that is what they are both measuring.
#       Independence means no shared ELEMENT, not a different node.
#   I2C_SDA / I2C_SCL / nALERT_ADC -- ADC-A and ADC-B are different PACKAGES on
#       one bus. A bus fault takes both, but NO HARDWARE PERMISSIVE READS EITHER
#       ADC (every permissive is a discrete comparator on its own string), so a
#       bus fault cannot defeat an interlock. It degrades firmware's KNOWLEDGE,
#       and the designed response to degraded knowledge is to stop the heartbeat.
ASSERTION_C_ALLOWED_SHARED_NETS = {
    "GND", "+5V_A", "+3V3_A", "VREF_2V500",
    "HV_OUT_A", "HV_OUT_B",
    "I2C_SDA", "I2C_SCL", "nALERT_ADC",
}


def _chain_components(board, seed_nets):
    """Components touching any net in `seed_nets`, transitively through the
    HV string that feeds it."""
    n = nets(board)
    out = set()
    for s in seed_nets:
        for ref, _ in n.get(s, []):
            out.add(ref)
    return out


def assert_c_monitor_independence(board):
    """(c) EACH OUTPUT'S MONITOR IS ELECTRICALLY INDEPENDENT of both module
    VMON nets and of the COLD-permissive divider."""
    p = []
    n = nets(board)
    def string_refs(sid):
        s = HV_STRINGS[sid]
        return {"R%s%s%d" % (sid, sub.upper(), k)
                for sub in SUBSTRING_IDS[:s["n_par"]]
                for k in range(1, s["n_series"] + 1)}

    for X, mon_sid, cold_sid in (("A", "MONA", "CLDA"), ("B", "MONB", "CLDB")):
        mon = string_refs(mon_sid) | _chain_components(
            board, ["HVDIV_TAP_%s" % X, "MON_TAPF_%s" % X, "MON_TAP_%s" % X,
                    "MON_REF_%s" % X, "MON_REFD_%s" % X])
        cold = string_refs(cold_sid) | _chain_components(
            board, ["HVDIV_COLD_%s" % X, "COLD_%s_HI" % X, "COLD_%s_LO" % X,
                    "COLD_%s" % X])
        vmon = _chain_components(board, ["VMON_P", "VMON_N",
                                         "VMON_P_BUF", "VMON_N_BUF"])
        for other, label in ((cold, "the COLD-permissive divider"),
                             (vmon, "a module VMON chain")):
            shared = (mon & other) - {"#PWR01"}
            if shared:
                p.append("(c) VIOLATED: monitor %s shares component(s) %s with %s"
                         % (X, sorted(shared), label))
        # shared NETS, reported against the declared exception list
        mon_nets = {net for net in n
                    for ref, _ in n[net] if ref in mon}
        cold_nets = {net for net in n for ref, _ in n[net] if ref in cold}
        vmon_nets = {net for net in n for ref, _ in n[net] if ref in vmon}
        for other_nets, label in ((cold_nets, "COLD"), (vmon_nets, "VMON")):
            bad = (mon_nets & other_nets) - ASSERTION_C_ALLOWED_SHARED_NETS
            if bad:
                p.append("(c) monitor %s shares net(s) %s with %s -- not in the "
                         "declared exception list" % (X, sorted(bad), label))
    # the cross-package rule: every HV-monitor-vs-VMON comparison must cross
    # an ADC package boundary, or a common-mode ADC fault moves both readings
    # the same way and the disagreement trip goes blind.
    adc_a = {net for net in n for ref, _ in n[net] if ref == "UADCA"}
    adc_b = {net for net in n for ref, _ in n[net] if ref == "UADCB"}
    if {"VMON_P_BUF", "VMON_N_BUF"} & adc_a:
        p.append("(c) VIOLATED: a module VMON is on the SAME ADC as the "
                 "independent monitors -- the cross-check no longer crosses a "
                 "package boundary")
    if not ({"MON_TAP_A", "MON_TAP_B"} <= adc_a):
        p.append("(c) both independent monitors must be on ADC-A")
    if not ({"VMON_P_BUF", "VMON_N_BUF"} <= adc_b):
        p.append("(c) both module VMONs must be on ADC-B")
    return p


# ------------------------- assertions that cannot be expressed structurally --
NOT_STRUCTURALLY_EXPRESSIBLE = [
    ("SA-9 placement", "NUM-09 requires the two parallel sub-strings to be "
     "PLACED at least 5 mm apart, and ARCH-18 requires each duplicated pull "
     "pair to be >= 5 mm apart. A netlist has no coordinates. This must be a "
     "PCB-generator invariant; check_netlist.py cannot see it."),
    ("graded string spacing", "MONITOR_AND_BLEED.md 9.1: no two HVDIV_* nodes "
     "closer than C_hv may differ by more than 150 V. That is a joint "
     "geometry+potential predicate; DRC has no 'adjacent in string' operator "
     "and a .kicad_dru pattern rule is UNSAFE because both ends of one string "
     "match the same pattern and are 800 V apart. Generator invariant only."),
    ("HCT vs HC", "Every 74-series part here MUST be HCT (or AHCT/LVC) because "
     "74HC at VCC = 5 V wants VIH = 3.5 V and a 3.3 V ESP32 output does not "
     "meet it. The KiCad symbol carries no family, so this lives in the `val` "
     "string and in the BOM -- it is NOT netlist-checkable."),
    ("push-pull comparators", "MONITOR_AND_BLEED.md 5.4: the COLD comparators "
     "must be PUSH-PULL, never open-drain-with-pull-up, because an open-drain "
     "failure pulls up to a false COLD = 1. The borrowed LM393 symbol declares "
     "its outputs open_collector. Pin TYPE is a symbol property we do not "
     "control and ERC will not flag the mismatch."),
    ("relay coil polarity", "The Pickering '/5D' suffix means an INTERNAL COIL "
     "DIODE, so A1/A2 polarity is mandatory. The generic Relay_SPDT symbol has "
     "no polarity marking, so a reversed coil is netlist-legal."),
    ("K1/K2 orthogonal mounting", "Reed sensitivity is strongly axial; K1 and "
     "K2 must be mounted with their long axes ORTHOGONAL so one stray magnet "
     "cannot close both. Geometry, not connectivity."),
    ("weld detection", "SCOPE.md Q6 was never answered. This design DETECTS "
     "welds (self-tests plus per-branch monitors) and cannot PREVENT them. "
     "Nothing in a netlist can assert otherwise."),
    ("discharge TIME", "Assertion (b) proves a discharge PATH exists in every "
     "state. It says nothing about how long the discharge takes, which depends "
     "on C_module and C_load -- both MEASURABLE-NOW and both unmeasured. That "
     "is a numbers-probe question, not a netlist question."),
    ("SA-12 dump sizing", "No dump/crowbar resistor is fitted (MONITOR_AND_BLEED "
     "7.6 recommends against one), so SA-12 is vacuously true here. If a "
     "switched dump is ever fitted the assertion must be implemented."),
]


# ================ INTERFACES.md section 1.3, SA-1 .. SA-13 =================
# Promoted from review to build failure. Two are implemented in a CORRECTED
# form and both corrections are stated, not silently applied:
#
#   SA-5 as written ("no resistor of ANY value in series between a buffer/DAC
#        output and a VSET pin") is SUPERSEDED by SETPOINT_PATH.md's SP-1
#        (<= 0.2 ohm UN-NULLED, EXCLUDING resistance enclosed by a Kelvin loop
#        whose sense point is the VSET pin). The design deliberately fits a
#        10 ohm capacitive-load isolation resistor INSIDE the Kelvin loop,
#        because solving the stability problem outside the loop is exactly the
#        ARCH-04 violation SA-5 exists to prevent. SA-5 read literally would
#        force the unsafe answer. **This needs a G1 edit to INTERFACES.md.**
#
#   SA-12 is vacuous here: no dump/crowbar resistor is fitted. Implemented
#        anyway so that fitting one later cannot bypass it.
INOM_A = 0.5e-3


def _rails_le(v):
    return {"+5V_MOD", "+5V_A", "+3V3", "+3V3_A", "VIN_P", "VIN_N", "VCLAMP",
            "VCLAMP_STAR"}


def interfaces_assertions(board):
    p = []
    n = nets(board)
    comps = {c["ref"]: c for c in board["components"]}

    def two_terminal(net, other):
        """*** DNP PARTS DO NOT COUNT. ***  A Do-Not-Populate footprint is in
        the schematic and the BOM and NOT ON THE BOARD, so it can never satisfy
        a safety requirement. This is not pedantry: adding the DNP pull-down
        contingency parts made the ARCH-18 'exactly two pull elements' check
        pass on a board with ONE fitted pull element, and the mutation test is
        what caught it."""
        return [comps[r] for r, _ in n.get(net, [])
                if len(comps[r]["pins"]) == 2
                and not comps[r]["dnp"]
                and other in comps[r]["pins"].values()]

    # SA-1 / SA-2 : /ON pull-ups, duplicated, to that module's OWN +VIN
    for m, vin in (("nON_P", "VIN_P"), ("nON_N", "VIN_N")):
        ups = [c for c in two_terminal(m, vin) if c["fields"]["PartClass"] == "R_LV"]
        if len(ups) != 2:
            p.append("SA-1: %s has %d pull-up(s) to %s; ARCH-17/ARCH-18 need "
                     "exactly 2 in parallel" % (m, len(ups), vin))
        for r, _ in n.get(m, []):
            c = comps[r]
            if len(c["pins"]) == 2 and not c["dnp"]                     and c["fields"]["PartClass"] == "R_LV":
                other = [x for x in c["pins"].values() if x != m]
                if other and other[0] not in (vin, "GND") and other[0] in RAILS:
                    p.append("SA-2: %s is pulled to %s, a rail that can be "
                             "absent while %s is present" % (m, other[0], vin))
    # SA-3 : VSET pull-downs, duplicated
    for v in ("VSET_P", "VSET_N"):
        dns = [c for c in two_terminal(v, "GND")
               if c["fields"]["PartClass"] == "R_LV"]
        if len(dns) < 2:
            p.append("SA-3: %s has %d pull-down(s) to GND; needs >= 2 "
                     "(ARCH-05/ARCH-18)" % (v, len(dns)))
    # SA-4 : the VSET buffer's V+ is the precision reference, not a logic rail
    u4 = comps.get("U4")
    if u4 is None or u4["pins"].get("8") not in ("VCLAMP", "VCLAMP_STAR"):
        p.append("SA-4: the VSET buffer's V+ pin is not on the clamp rail "
                 "(it is on %r) -- ARCH-06 makes that rail the clamp"
                 % (u4 and u4["pins"].get("8")))
    # SA-5 (as SP-1) : series resistance in the VSET path must be Kelvin-nulled
    for v, sense in (("VSET_P", "VSET_P_SENSE"), ("VSET_N", "VSET_N_SENSE")):
        series = [c for r, _ in n.get(v, []) for c in [comps[r]]
                  if c["fields"]["PartClass"] in ("R_LV",)
                  and set(c["pins"].values()) & {"VSET_P_FORCE", "VSET_N_FORCE"}]
        for c in series:
            if not any(r == c["ref"] for r, _ in n.get(v, [])):
                continue
            kelvin = [x for x, _ in n.get(sense, [])
                      if v in comps[x]["pins"].values()]
            if not kelvin:
                p.append("SA-5/SP-1: %s carries series element %s but the "
                         "feedback is NOT taken at the pin -- an un-nulled "
                         "series resistor here is uncommanded output voltage"
                         % (v, c["ref"]))
    # SA-6 : +VIN reaches each module only through the interlock element
    for vin, sw, fb in (("VIN_P", "U16", "FB1"), ("VIN_N", "U17", "FB2")):
        srcs = {r for r, _ in n.get(vin, [])}
        if fb not in srcs:
            p.append("SA-6: %s is not fed through its ferrite %s" % (vin, fb))
        if comps[sw]["pins"].get("6") != vin.replace("VIN_", "VIN_") + "_SW":
            p.append("SA-6: load switch %s does not feed %s" % (sw, vin))
        if any(comps[r]["fields"]["PartClass"] in
               ("LMR33620", "LT3045", "LP5907") for r, _ in n.get(vin, [])):
            p.append("SA-6: %s is fed directly by a regulator, bypassing the "
                     "interlock load switch (ARCH-19)" % vin)
    # SA-7 : the relay COIL rail passes through its own fail-safe switch
    coil = comps.get("U15")
    if coil is None or coil["pins"].get("6") != "+5V_COIL" \
            or comps["KS"]["pins"].get("21") != "+5V_COIL":
        p.append("SA-7: the relay coil rail does not pass through a dedicated "
                 "fail-safe switch (COMBINER_STUDY F-1)")
    # SA-8 : covered by assert_c_monitor_independence (component disjointness)
    # SA-9 : every bleed and divider top leg is two parallel strings
    for sid, s in HV_STRINGS.items():
        if s["n_par"] < 2:
            p.append("SA-9: HV string %s is a single series chain" % sid)
    # SA-10 : no net in both an HV and a non-HV class -- structurally impossible
    #         here because netclass_of returns one class; checked there.
    # SA-11 : module GND pins 3 and 7 both present and both on GND
    for u in ("U1", "U2"):
        for pad in ("3", "7"):
            if comps[u]["pins"].get(pad) != "GND":
                p.append("SA-11: %s pad %s is %r, not GND -- both module GND "
                         "pins are physically present and both must be wired"
                         % (u, pad, comps[u]["pins"].get(pad)))
    # SA-12 : every dump/crowbar resistor satisfies 1.5 * Inom * R < 60 V
    for c in board["components"]:
        if c["fields"].get("Role") == "dump":
            try:
                ohms = float(re.sub(r"[^0-9.]", "", c["val"]))
            except ValueError:
                p.append("SA-12: dump %s has an unparseable value" % c["ref"])
                continue
            if 1.5 * INOM_A * ohms >= TOUCH_SAFE_V:
                p.append("SA-12: dump %s (%s) leaves %.1f V at 1.5*Inom"
                         % (c["ref"], c["val"], 1.5 * INOM_A * ohms))
    # SA-13 : each module has a >= 22 uF cap from its +VIN to GND
    for vin in ("VIN_P", "VIN_N"):
        caps = [c for c in two_terminal(vin, "GND")
                if c["fields"]["PartClass"] in ("C_BULK", "C_LV")
                and "22u" in c["val"]]
        if not caps:
            p.append("SA-13: %s has no >= 22 uF capacitor to GND (PART-18 "
                     "MANDATES one)" % vin)
    return p


def safety_assertions(board):
    """Return specific problems; [] means pass. Each entry names the failure."""
    out = []
    out += interfaces_assertions(board)
    out += assert_a_gate_structure(board)
    out += assert_a_mode_decode(board)
    out += assert_a_mode_origin(board)
    out += assert_a_no_shared_output_node(board)
    out += assert_b_discharge_paths(board)
    out += assert_c_monitor_independence(board)
    return out


def check(board=None):
    b = board or build_board()
    p = []
    p += check_structure(b)
    p += check_min_two_connections(b)
    p += check_symbol_pins(b)
    p += check_pin_semantics(b)
    p += check_netclass_coverage(b)
    p += check_hv_ratings(b)
    p += safety_assertions(b)
    return p


def main():
    try:
        b = build_board()
    except Exception as e:                                        # noqa: BLE001
        print("STRUCTURAL FAILURE while building: %s" % e)
        return 2
    problems = check(b)
    n = nets(b)
    hv = [x for x in n if is_hv_net(x)]
    print("hvctl golden netlist -- spec_version %d, rev %s" % (SPEC_VERSION, REV))
    print("  components : %d" % len(b["components"]))
    print("  nets       : %d  (%d HV, %d analog, %d digital/other)"
          % (len(n), len(hv),
             len([x for x in n if is_analog_net(x)]),
             len([x for x in n if not is_hv_net(x) and not is_analog_net(x)])))
    print("  netclasses : %s" % ", ".join(sorted(b["netclasses"])))
    print("  HV strings : %d, %d elements total"
          % (len(HV_STRINGS),
             sum(s["n_series"] * s["n_par"] for s in HV_STRINGS.values())))
    print("  reachable mechanical states evaluated : %d" % len(reachable_states(b)))
    print("  TIER-C (borrowed pinout) components   : %d"
          % len([c for c in b["components"] if c["fields"]["Tier"] == "C"]))
    print("")
    print("  ASSERTIONS THAT ARE *NOT* STRUCTURALLY EXPRESSIBLE (%d) -- these are"
          % len(NOT_STRUCTURALLY_EXPRESSIBLE))
    print("  recorded, NOT dropped. Each needs a generator invariant, a BOM")
    print("  property or a bench test:")
    for k, why in NOT_STRUCTURALLY_EXPRESSIBLE:
        print("    - %s" % k)
    print("")
    if problems:
        print("FAIL (%d):" % len(problems))
        for x in problems:
            print("   " + x)
        return 1
    print("PASS - structure, symbol pin-number AND pin-name cross-check,")
    print("       netclass coverage, HV ratings, INTERFACES SA-1..SA-13")
    print("       and domain safety assertions (a), (b), (c) all hold.")
    print("")
    print("  WHAT EXIT 0 DOES NOT MEAN: no value was verified, no part was")
    print("  confirmed to exist, no TIER-C borrowed pinout was checked against a")
    print("  datasheet, and nothing was simulated, built or measured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
