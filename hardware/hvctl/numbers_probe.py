#!/usr/bin/env python3
"""PHASE 1 NUMBERS PROBE for the iseg bipolar HV controller -- PINNED TO THE ACTUAL PART.

G0 is signed off (2026-07-23). The human owns iseg APS AP010504P05 and AP010504N05.
This probe therefore computes the AP010504 case IN FULL as the primary case, and keeps
other voltage classes / the 1 W family ONLY where the comparison changes a decision.

Frozen at G0:
  G0-A1  set-and-hold with polarity changeover; combiner is HV RELAY CHANGEOVER
  G0-A2  module = AP010504: Vnom 1000 V, Inom 0.5 mA, Pnom 0.5 W, Vin 5 V, Vref 2.5 V
  G0-A3  serial AND network, both with full write authority
  G0-A4  dual-mode: (1) single combined bipolar output, (2) TWO INDEPENDENT UNIPOLAR
         outputs, BOTH ENERGISED SIMULTANEOUSLY.  ==> +1 kV and -1 kV coexist on the
         board as a NORMAL STEADY-STATE CONDITION.  The 2 kV HV_POS<->HV_NEG differential
         is no longer a fault case and no longer topology-conditional.

Sections
  0  The frozen part
  1  Creepage / clearance, and the board area the 2 kV normal case implies
  2  Netclass + .kicad_dru rules
  3  Bleed / discharge / stored energy
  4  Monitor divider  (the 1.00 %-of-Inom loading constraint is the binding one)
  5  VSET clamp and single-fault survival  (PRIMARY SAFETY ELEMENT)
  6  Power budget on the 5 V rail
  7  Set-point resolution
  8  Comparison classes, kept only where informative

Acceptance: every assertion in R.checks holds.  Exit 0 only if all hold.
Exit codes: 0 all assertions hold | 1 one or more failed | 2 structural failure.

STDLIB ONLY. Zero-arg, headless, deterministic -- byte-identical output across runs.
"""

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
PHASE0_PRO = os.path.join(REPO, "hardware", "phase0_env_proof", "env_proof.kicad_pro")
ISEG_FP = os.path.join(HERE, "lib", "iseg.pretty", "iseg_APS_THT.kicad_mod")
KICAD_RES_PRETTY = "C:/Program Files/KiCad/10.0/share/kicad/footprints/Resistor_SMD.pretty"


# =====================================================================================
# SOURCES
# =====================================================================================

SOURCES = {
    "ISEG": (
        "iseg APS series technical documentation v2.5, last changed 2024-08-20 "
        "(references/iseg_manual_APS_en.pdf). Table 1 p.7 (specifications), "
        "Table 2 p.8 (configurations), Table 3 p.8 (item code), Table 4 p.9 (pins). "
        "[verified-artifact: text extracted with PyMuPDF in session 1, re-read by 3 skeptics]"
    ),
    "G0": (
        "Human answers to docs/G0_QUESTIONS.md, signed off 2026-07-23. "
        "Part identity, dual-mode requirement, comms authority. [frozen]"
    ),
    "IPC2221": (
        "IPC-2221 / IPC-2221B Table 6-1 'Electrical Conductor Spacing'. "
        "[unverified-primary] -- the primary standard is PAYWALLED and has NOT been read. "
        "The values here came off secondary web reproductions in session 1, and the two "
        "'independent' reproductions were later shown to be the same page. NO INTERNAL "
        "EVIDENCE SUPPORTS THIS TRANSCRIPTION. A human must read a primary copy before G1."
    ),
    "IEC": (
        "IEC 62368-1 / IEC 60664-1 creepage, pollution degree 2, basic insulation. "
        "[unverified-primary] -- same status as IPC2221, same single secondary source. "
        "The 'printed boards' column is additionally SUSPECTED MIS-TRANSCRIBED (section 1.5). "
        "Values above 1000 V are OUR OWN LINEAR EXTRAPOLATION, not a quotation."
    ),
    "TOUCH": (
        "Touch-safe DC threshold 60 V DC: the accessible-part limit used by IEC 61010-1 "
        "and the ES1 d.c. voltage limit of IEC 62368-1. "
        "[recalled -- confirm clause numbers against the standard before Phase 7]"
    ),
    "ENERGY": (
        "Hazardous stored-energy thresholds 350 mJ and 50 uC "
        "(IEC 62368-1 electrical energy source classification / IEC 61010-1). "
        "[recalled -- confirm before Phase 7]"
    ),
    "KICAD": (
        "KiCad 10.0 net_settings.classes field set, measured at runtime from a project file "
        "KiCad itself wrote: hardware/phase0_env_proof/env_proof.kicad_pro. [verified-artifact]"
    ),
    "FOOTPRINT": (
        "SMD chip-resistor pad geometry measured at runtime from the KiCad 10.0 stock library "
        "Resistor_SMD.pretty. gap = 2*(pad_cx - pad_w/2); extent = 2*(pad_cx + pad_w/2). "
        "[verified-artifact]"
    ),
    "ISEGFP": (
        "This project's own module footprint hardware/hvctl/lib/iseg.pretty/"
        "iseg_APS_THT.kicad_mod, parsed at runtime. Pin map and body offset survived 3 "
        "adversarial skeptics (STATUS.md 1.1). [verified-artifact]"
    ),
    "ARCH12": (
        "docs/DECISIONS.md ARCH-12, itself [verified-artifact] from the Yageo RC-series "
        "datasheet PDF extracted locally: max working voltage 0805/150 V, 1206/200 V, "
        "2010/200 V, 2512/200 V; the +/-1 % range stops at 2.2 Mohm."
    ),
    "ASSUMED": "Engineering assumption made by this probe. Listed in ASSUMPTIONS.",
}

ASSUMPTIONS = []
MEASURABLE_NOW = []


def assume(text):
    ASSUMPTIONS.append(text)
    return text


def measurable(text):
    MEASURABLE_NOW.append(text)
    return text


# =====================================================================================
# SECTION 0 GROUND TRUTH -- the frozen part, [ISEG] + [G0]
# =====================================================================================

PART = "AP010504"
ITEM_P = "AP010504P05"
ITEM_N = "AP010504N05"

VNOM = 1000.0          # V, module nominal output  [ISEG] Table 2
INOM = 0.5e-3          # A                          [ISEG] Table 2
PNOM = 0.5             # W                          [ISEG] Table 2
VIN_NOM = 5.0          # V                          [ISEG] Table 1
VIN_RANGE = (4.5, 5.5)
VREF = 2.5             # V, module internal reference
VREF_TOL = 0.01        # +/-1 %
VSET_FS = 2.5          # V, 0..2.5 -> 0..Vnom
VMON_FS = 2.5

IIN_VOUT0_MA = 5.0     # < 5 mA at Vout = 0
IIN_NOLOAD_MA = 25.0   # < 25 mA at Vnom, no load
IIN_LOADED_MA = 180.0  # < 180 mA at Vnom, loaded

IOUT_LIMIT_FACTOR = 1.5            # Iout limited to approx 1.5 * Inom
IOUT_LIMIT_A = IOUT_LIMIT_FACTOR * INOM   # 0.75 mA

ADJ_ACCURACY = 0.01                # +/-1 % of Vnom = 10 V
VMON_ACCURACY = 0.01               # 1 % * Vnom     = 10 V
TEMPCO_PPM_K = 50.0

RIPPLE_TYP_VPP = 10e-3
RIPPLE_MAX_VPP = 30e-3
RIPPLE_HF_VPP = 5e-3
RIPPLE_VALID_FRACTION = 0.02       # spec valid ONLY for 2%*Vnom < Vout <= Vnom
RIPPLE_VALID_FLOOR_V = RIPPLE_VALID_FRACTION * VNOM   # 20 V

VSET_PULLUP_OHM = 10e3             # internal pull-up to Vref, derived from the Rset formula
LOGIC_RAIL_V = 3.3                 # ESP32
LOGIC_RAIL_5V = 5.0
VIN_BLOCK_UF = 22


# =====================================================================================
# Reporting / assertion harness
# =====================================================================================

class Report(object):
    def __init__(self):
        self.lines = []
        self.checks = []
        self.findings = []

    def h1(self, s):
        self.lines.append("")
        self.lines.append("=" * 92)
        self.lines.append(s)
        self.lines.append("=" * 92)

    def h2(self, s):
        self.lines.append("")
        self.lines.append("-- " + s + " " + "-" * max(0, 88 - len(s)))

    def p(self, s=""):
        self.lines.append(s)

    def check(self, ok, name, detail=""):
        self.checks.append((bool(ok), name, detail))
        self.lines.append("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                                           ("  --  " + detail) if detail else ""))
        return bool(ok)

    def finding(self, s):
        self.findings.append(s)
        self.lines.append("  [FINDING] " + s)

    def blind(self, s):
        self.lines.append("  [BLIND SPOT] this section cannot see: " + s)

    def dump(self):
        return "\n".join(self.lines)


R = Report()


# =====================================================================================
# Runtime artifact readers -- independent sources of truth
# =====================================================================================

def read_chip_pad_geometry():
    """Measure chip-resistor pad gap and pad extent from KiCad's own stock footprints.

    gap    = 2*(pad_centre_x - pad_width/2)     the copper-free span under the body
    extent = 2*(pad_centre_x + pad_width/2)     the land pattern's overall length

    Returns {} if the KiCad install is absent.  [FOOTPRINT]
    """
    files = {"0805": "R_0805_2012Metric.kicad_mod", "1206": "R_1206_3216Metric.kicad_mod",
             "2010": "R_2010_5025Metric.kicad_mod", "2512": "R_2512_6332Metric.kicad_mod"}
    out = {}
    for pkg, fn in sorted(files.items()):
        path = os.path.join(KICAD_RES_PRETTY, fn)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            txt = fh.read()
        cx = [abs(float(m)) for m in re.findall(r"\(at (-?[\d.]+) 0\)", txt)]
        w = [float(m) for m in re.findall(r"\(size ([\d.]+) [\d.]+\)", txt)]
        if not cx or not w:
            continue
        h = [float(m) for m in re.findall(r"\(size [\d.]+ ([\d.]+)\)", txt)]
        out[pkg] = (round(2 * (cx[0] - w[0] / 2.0), 4), round(2 * (cx[0] + w[0] / 2.0), 4),
                    round(h[0], 4))
    return out


def read_iseg_footprint():
    """Parse this project's own module footprint for pad centres, sizes and overrides."""
    if not os.path.isfile(ISEG_FP):
        return None
    with open(ISEG_FP, "r", encoding="utf-8") as fh:
        txt = fh.read()
    pads = {}
    for blk in re.findall(r'\(pad "(\d)" thru_hole \w+\s*\(at (-?[\d.]+) (-?[\d.]+)\)\s*'
                          r'\(size ([\d.]+) ([\d.]+)\)(.*?)\n\t\)', txt, re.S):
        num, x, y, sx, sy, rest = blk
        m = re.search(r"\(clearance ([\d.]+)\)", rest)
        pads[num] = {"x": float(x), "y": float(y), "sx": float(sx), "sy": float(sy),
                     "clearance": float(m.group(1)) if m else None}
    body = re.search(r"Body ([\d.]+) x ([\d.]+) x ([\d.]+); "
                     r"centre offset \+([\d.]+) / \+([\d.]+)", txt)
    if not pads or not body:
        return None
    return {"pads": pads,
            "body_l": float(body.group(1)), "body_w": float(body.group(2)),
            "body_h": float(body.group(3)),
            "off_x": float(body.group(4)), "off_y": float(body.group(5))}


CHIP_PADS_FALLBACK = {"0805": (0.8000, 2.8500, 1.4000), "1206": (1.8000, 4.0500, 1.7500),
                      "2010": (3.4000, 5.8500, 2.6500), "2512": (4.7000, 7.1500, 3.3500)}
CHIP_PADS = read_chip_pad_geometry() or dict(CHIP_PADS_FALLBACK)
PAD_GAP_MM = dict((k, v[0]) for k, v in CHIP_PADS.items())
PAD_EXTENT_MM = dict((k, v[1]) for k, v in CHIP_PADS.items())
PAD_WIDTH_MM = dict((k, v[2]) for k, v in CHIP_PADS.items())
CO_GRADE_SEP_MM = 1.0     # [ASSUMED] separation between two co-graded HV strings
ISEGFP = read_iseg_footprint()


# =====================================================================================
# SECTION 0 -- THE FROZEN PART
# =====================================================================================

def section0():
    R.h1("SECTION 0 -- THE FROZEN PART (G0 signed off 2026-07-23)")
    R.p("Decoded from [ISEG] Table 2 / Table 3 against the modules the human physically owns:")
    R.p("    %s  (positive)      %s  (negative)" % (ITEM_P, ITEM_N))
    R.p("    AP | 010 = %.0f V Vnom | 504 = %.2f mA Inom | polarity P/N | 05 = %.0f V input"
        % (VNOM, INOM * 1e3, VIN_NOM))
    R.p()
    R.p("    Vnom                %8.1f V" % VNOM)
    R.p("    Inom                %8.3f mA          Iout limit = 1.5*Inom = %.3f mA"
        % (INOM * 1e3, IOUT_LIMIT_A * 1e3))
    R.p("    Pnom                %8.2f W" % PNOM)
    R.p("    Vin                 %8.1f V   (%.1f .. %.1f V)  <-- 5 V, NOT 12 V"
        % (VIN_NOM, VIN_RANGE[0], VIN_RANGE[1]))
    R.p("    Vref                %8.2f V   +/-%.0f %%      <-- 2.5 V, and the MCU rail is 3.3 V"
        % (VREF, 100 * VREF_TOL))
    R.p("    Vset, Vmon          0 .. %.1f V full scale" % VSET_FS)
    R.p("    Iin  @Vout=0        < %6.1f mA" % IIN_VOUT0_MA)
    R.p("    Iin  @Vnom no load  < %6.1f mA" % IIN_NOLOAD_MA)
    R.p("    Iin  @Vnom loaded   < %6.1f mA   <-- the number the supply is sized on" % IIN_LOADED_MA)
    R.p("    Adjustment accuracy +/-%.0f %% = %.1f V at Vnom" % (100 * ADJ_ACCURACY,
                                                                ADJ_ACCURACY * VNOM))
    R.p("    VMON accuracy        %.0f %% * Vnom = %.1f V" % (100 * VMON_ACCURACY,
                                                             VMON_ACCURACY * VNOM))
    R.p("    Tempco              < %.0f ppm/K = %.3f V/K at Vnom" % (TEMPCO_PPM_K,
                                                                    TEMPCO_PPM_K * 1e-6 * VNOM))

    R.h2("0.1  The ripple spec has a FLOOR, and below it the output is UNSPECIFIED")
    R.p("     [ISEG] ripple/noise: typ < %.0f mVpp, max < %.0f mVpp (f > 10 Hz),"
        % (RIPPLE_TYP_VPP * 1e3, RIPPLE_MAX_VPP * 1e3))
    R.p("     < %.0f mVpp (f > 2 kHz) -- GUARANTEED ONLY FOR %.0f %% * Vnom < Vout <= Vnom."
        % (RIPPLE_HF_VPP * 1e3, 100 * RIPPLE_VALID_FRACTION))
    R.p("     At this part that floor is %.0f V. BELOW %.0f V THE OUTPUT IS UNSPECIFIED -- not"
        % (RIPPLE_VALID_FLOOR_V, RIPPLE_VALID_FLOOR_V))
    R.p("     merely worse. Every low-end number in this document must say so, and the host")
    R.p("     protocol must refuse to present 0 < |Vout| < %.0f V as a specified operating point."
        % RIPPLE_VALID_FLOOR_V)
    R.check(RIPPLE_VALID_FLOOR_V > 0.0 and RIPPLE_VALID_FLOOR_V < VNOM,
            "the unspecified low-output band is a real, non-empty band",
            "0 .. %.0f V of a %.0f V range = %.0f %% of full scale is UNSPECIFIED"
            % (RIPPLE_VALID_FLOOR_V, VNOM, 100 * RIPPLE_VALID_FRACTION))

    R.h2("0.2  The 3.3 V hazard is now real, load-bearing, and specific to THIS part")
    frac = LOGIC_RAIL_V / VREF
    R.p("     Vref = %.1f V. The MCU rail is %.1f V. Vout/Vnom = Vset/Vref, and [ISEG] states"
        % (VREF, LOGIC_RAIL_V))
    R.p("     verbatim: 'Attention! Output voltage is internally not limited!'")
    R.p("     A logic-level fault that puts %.1f V on VSET commands %.1f/%.1f = %.0f %% of Vnom"
        % (LOGIC_RAIL_V, LOGIC_RAIL_V, VREF, 100 * frac))
    R.p("     = %.0f V on a %.0f V module." % (frac * VNOM, VNOM))
    R.p("     Compounding it, the module's UN-DRIVEN DEFAULT STATE IS ENERGISED AT OVER-RANGE:")
    R.p("       * internal %.0f kohm pull-up to Vref  ==> an OPEN VSET commands FULL SCALE"
        % (VSET_PULLUP_OHM / 1e3))
    R.p("       * /ON is active LOW and 'LOW or n.c.' ==> a FLOATING /ON turns HV ON")
    R.p("     The 1 W family (Vref 5.0 V) would be immune to a 3.3 V rail. THAT FAMILY IS NOT")
    R.p("     AVAILABLE: the human owns the 0.5 W / 5 V part. The hazard is not designed away,")
    R.p("     it is clamped -- see section 5, which treats the clamp as a primary safety element.")
    R.check(frac > 1.30,
            "un-clamped 3.3 V drive on VSET is a >30 % over-voltage on the OWNED part",
            "%.0f %% of Vnom = %.0f V" % (100 * frac, frac * VNOM))
    R.check(VREF < LOGIC_RAIL_V,
            "module Vref sits BELOW the MCU logic rail (this is what creates the hazard)",
            "Vref %.1f V < rail %.1f V" % (VREF, LOGIC_RAIL_V))

    R.h2("0.3  What G0-A4 (dual-mode) changes in one sentence")
    R.p("     MODE 1 bipolar combined : one output terminal, one module at a time,")
    R.p("                               break-before-make, deselected module bled to ground.")
    R.p("     MODE 2 dual unipolar    : positive module -> OUT_A, negative module -> OUT_B,")
    R.p("                               BOTH ENERGISED SIMULTANEOUSLY. That is the point of it.")
    R.p()
    R.p("     ==> +%.0f V and -%.0f V coexist on this board as a NORMAL STEADY-STATE CONDITION."
        % (VNOM, VNOM))
    R.p("     ==> the HV_POS<->HV_NEG differential is %.0f V, permanently, not as a fault."
        % (2 * VNOM))
    R.p("     ==> the safety invariant is RESTATED, not discarded:")
    R.p("           'it must be impossible for both modules to be connected to the SAME")
    R.p("            output node simultaneously'")
    R.p("         which forbids the mode-1 both-enabled state exactly as before, and is")
    R.p("         satisfied STRUCTURALLY in mode 2 because the nodes are physically different.")
    R.p("     ==> the interlock permissive must be derived from the ACTUAL PHYSICAL POSITION of")
    R.p("         the mode routing element, never from a commanded mode bit. Numbers below")
    R.p("         assume mode 2 throughout, because mode 2 is the binding case for every one.")


# =====================================================================================
# SECTION 1 -- CREEPAGE AND CLEARANCE
# =====================================================================================

IPC_COLUMNS = ["B1", "B2", "B3", "B4", "A5", "A6", "A7"]
IPC_BANDS = [
    (15,   0.05, 0.10, 0.10, 0.05, 0.13, 0.13, 0.13),
    (30,   0.05, 0.10, 0.10, 0.05, 0.13, 0.25, 0.13),
    (50,   0.10, 0.60, 0.60, 0.13, 0.13, 0.40, 0.13),
    (100,  0.10, 0.60, 1.50, 0.13, 0.13, 0.50, 0.13),
    (150,  0.20, 0.60, 3.20, 0.40, 0.40, 0.80, 0.40),
    (170,  0.20, 1.25, 3.20, 0.40, 0.40, 0.80, 0.40),
    (250,  0.20, 1.25, 6.40, 0.40, 0.40, 0.80, 0.40),
    (300,  0.20, 1.25, 12.5, 0.40, 0.40, 0.80, 0.80),
    (500,  0.25, 2.50, 12.5, 0.80, 0.80, 1.50, 0.80),
]
IPC_PER_VOLT = {"B1": 0.0025, "B2": 0.005, "B3": 0.025,
                "B4": 0.00305, "A5": 0.00305, "A6": 0.00305, "A7": 0.00305}


def ipc2221_clearance_mm(volts, column):
    """IPC-2221 Table 6-1 minimum conductor spacing.  [IPC2221, unverified-primary]

        v <= 500 V : table lookup by band
        v >  500 V : spacing(301-500 band) + per_volt[col] * (v - 500)
    """
    if column not in IPC_COLUMNS:
        raise ValueError("unknown IPC-2221 column %r" % column)
    idx = IPC_COLUMNS.index(column) + 1
    v = abs(float(volts))
    if v <= 500.0:
        for band in IPC_BANDS:
            if v <= band[0]:
                return band[idx]
    return IPC_BANDS[-1][idx] + IPC_PER_VOLT[column] * (v - 500.0)


IEC_PD2_ANCHORS = {
    "printed_board": [(250, 1.0), (500, 2.5), (1000, 5.0)],
    "mg_I":          [(250, 1.25), (500, 2.5), (1000, 5.0)],
    "mg_II":         [(250, 1.8), (500, 3.6), (1000, 7.1)],
    "mg_IIIa":       [(250, 2.5), (500, 5.0), (1000, 10.0)],
}


def iec_creepage_pd2_mm(volts, kind):
    """Creepage, PD2, basic insulation. Returns (mm, extrapolated). [IEC, unverified-primary]"""
    pts = IEC_PD2_ANCHORS[kind]
    v = abs(float(volts))
    if v <= pts[0][0]:
        return pts[0][1] * v / pts[0][0], False
    for (v0, d0), (v1, d1) in zip(pts, pts[1:]):
        if v <= v1:
            return d0 + (d1 - d0) * (v - v0) / (v1 - v0), False
    (v0, d0), (v1, d1) = pts[-2], pts[-1]
    return d1 + (d1 - d0) / (v1 - v0) * (v - v1), True


DESIGN_MARGIN = 1.5


def recommended_clearance_mm(volts):
    """governing = max(IPC B2, IEC PD2 printed-board); rec = ceil_0.5(governing * 1.5)."""
    b2 = ipc2221_clearance_mm(volts, "B2")
    pcb, e1 = iec_creepage_pd2_mm(volts, "printed_board")
    iiia, e2 = iec_creepage_pd2_mm(volts, "mg_IIIa")
    gov = max(b2, pcb)
    return (math.ceil(gov * DESIGN_MARGIN * 2.0) / 2.0, gov, b2, pcb, iiia, e1 or e2)


GUARD_TRACE_MM = 1.0        # [ASSUMED] width of the grounded guard conductor
ISLAND_MARGIN_MM = 4.0      # [ASSUMED] LV/mechanical margin each side of a module body
BOARD_TIER_MM = 100.0       # the cheapest standard fab tier is 100 x 100 mm


def section1():
    R.h1("SECTION 1 -- CREEPAGE AND CLEARANCE (primary case: HV_POS <-> HV_NEG at 2000 V)")
    R.p("Source, IPC:  " + SOURCES["IPC2221"])
    R.p("Source, IEC:  " + SOURCES["IEC"])
    R.p()
    R.p("*** READ THIS BEFORE USING ANY NUMBER IN THIS SECTION ***")
    R.p("EVERY constant below is [unverified-primary]. Neither standard has been read in the")
    R.p("original by anyone on this project. Session 1's document claimed an 'independent")
    R.p("cross-check between two standards families' as evidence; section 1.5 below PROVES")
    R.p("that check had zero discriminating power, and it has been DELETED. No replacement")
    R.p("cross-check has been invented, because there is nothing honest to put there.")
    R.p("The numbers are kept CONSERVATIVE and stay unfrozen until a human reads a primary")
    R.p("copy of IPC-2221B Table 6-1 and IEC 60664-1 / 62368-1.")

    R.h2("1.1  IPC-2221 Table 6-1 as transcribed here (mm)")
    R.p("     B1 internal | B2 external uncoated <=3050 m | B3 external uncoated >3050 m |")
    R.p("     B4 external w/ permanent polymer coating | A5 external w/ conformal coating |")
    R.p("     A6 external component lead uncoated | A7 external component lead coated")
    R.p()
    R.p("     %-12s" % "band (V)" + "".join("%8s" % c for c in IPC_COLUMNS))
    lo = 0
    for band in IPC_BANDS:
        R.p("     %-12s" % ("%d-%d" % (lo, band[0]))
            + "".join("%8.3f" % band[i] for i in range(1, 8)))
        lo = band[0] + 1
    R.p("     %-12s" % ">500 (/V)" + "".join("%8.5f" % IPC_PER_VOLT[c] for c in IPC_COLUMNS))
    R.p()
    R.p("     >500 V rule:  spacing(V) = spacing(301-500 band) + per_volt[col] * (V - 500)")
    R.p("       B2 @ %4.0f V = 2.500 + 0.00500*(%4.0f-500) = %6.3f mm  <- single-ended, this part"
        % (VNOM, VNOM, ipc2221_clearance_mm(VNOM, "B2")))
    R.p("       B2 @ %4.0f V = 2.500 + 0.00500*(%4.0f-500) = %6.3f mm  <- HV_POS<->HV_NEG, mode 2"
        % (2 * VNOM, 2 * VNOM, ipc2221_clearance_mm(2 * VNOM, "B2")))
    R.p("       B4 @ %4.0f V = 0.800 + 0.00305*(%4.0f-500) = %6.3f mm  <- if conformally coated"
        % (2 * VNOM, 2 * VNOM, ipc2221_clearance_mm(2 * VNOM, "B4")))

    R.h2("1.2  D-2, still open: the task brief's IPC column labelling")
    R.p("     The original brief described 'the B4 external-uncoated >500 V rule")
    R.p("     (0.25 mm + 0.0025 mm per volt above 500 V)'. The transcription used here says")
    R.p("     B4 is the COATED external column at 0.80 + 0.00305/V, and that 0.25 + 0.0025/V")
    R.p("     is B1, the INTERNAL-conductor rule. Both readings cannot be right and NEITHER")
    R.p("     has been checked against a primary copy. Unresolved. Carried forward.")

    R.h2("1.3  The voltages that appear on this board -- SETTLED by G0-A4")
    R.p("     %-26s %12s   %s" % ("node pair", "V across", "when"))
    R.p("     %-26s %12.0f   %s" % ("HV_POS   <-> GND", VNOM, "always, either mode"))
    R.p("     %-26s %12.0f   %s" % ("HV_NEG   <-> GND", VNOM, "always, either mode"))
    R.p("     %-26s %12.0f   %s" % ("HV_OUT_A <-> GND", VNOM, "mode 1 and mode 2"))
    R.p("     %-26s %12.0f   %s" % ("HV_OUT_B <-> GND", VNOM, "mode 2 only"))
    R.p("     %-26s %12.0f   %s" % ("HV_POS   <-> HV_NEG", 2 * VNOM,
                                    "*** NORMAL STEADY STATE in mode 2 ***"))
    R.p("     %-26s %12s   %s" % ("MODULE_CASE <-> GND", "0 (bonded)",
                                  "see 1.7 -- UNRATABLE, component-internal"))
    R.p()
    R.p("     Session 1 called the %.0f V span a SINGLE-FAULT condition, conditional on the"
        % (2 * VNOM))
    R.p("     combiner topology, and sized for it only as insurance against interlock failure.")
    R.p("     G0-A4 removes the conditional. In dual-unipolar mode the two opposite-polarity")
    R.p("     outputs are live SIMULTANEOUSLY as the intended normal operating condition. The")
    R.p("     %.0f V differential is therefore the BINDING NORMAL CASE. It sizes the board, the"
        % (2 * VNOM))
    R.p("     netclass rules, and the spacing between the two output connectors.")

    R.h2("1.4  Required clearance for the frozen part")
    R.p("     governing   = max( IPC-2221 B2(V), IEC PD2 printed-board creepage(V) )")
    R.p("     recommended = ceil_to_0.5mm( governing * %.1f )" % DESIGN_MARGIN)
    R.p("     The %.1fx is a judgement call, itemised: (a) IPC's own >500 V numbers extrapolate"
        % DESIGN_MARGIN)
    R.p("     a table whose measured data stops at 500 V; (b) no conformal coating is assumed,")
    R.p("     so we sit in column B2; (c) etch + mask registration + route tolerance, order")
    R.p("     0.05 mm each; (d) [ISEG] permits 70 % RH non-condensing and a bench lab makes")
    R.p("     pollution degree 2 an assumption; (e) no board-level HV proof test is planned")
    R.p("     before first energization; and now (f) THE CONSTANTS THEMSELVES ARE UNVERIFIED,")
    R.p("     which is the largest single reason to keep the margin where it is.")
    R.p()
    R.p("     %-24s %9s %8s %8s %8s %9s %9s %8s" %
        ("node pair", "V across", "IPC_B2", "IPC_B1", "IPC_B4", "IEC_pcb", "IEC_IIIa", "REC"))
    R.p("     %-24s %9s %8s %8s %8s %9s %9s %8s" %
        ("", "(V)", "mm", "mm(int)", "mm(coat)", "mm", "mm", "DRC mm"))
    pairs = [("HV_* <-> GND (1x Vnom)", VNOM), ("HV_POS <-> HV_NEG (2x)", 2 * VNOM)]
    rec = {}
    for label, v in pairs:
        r, gov, b2, pcb, iiia, ext = recommended_clearance_mm(v)
        rec[label] = (r, gov, b2, pcb, iiia, ext)
        R.p("     %-24s %9.0f %8.3f %8.3f %8.3f %9.3f %9.3f %8.1f%s" %
            (label, v, b2, ipc2221_clearance_mm(v, "B1"), ipc2221_clearance_mm(v, "B4"),
             pcb, iiia, r, "   (IEC extrapolated)" if ext else ""))
    R.p("     %-24s %9s %8s %8s %8s %9s %9s %8s   <- 1.7" %
        ("MODULE_CASE <-> GND", "0", "n/a", "n/a", "n/a", "n/a", "n/a", "UNRATABLE"))
    R.p()
    rec_se = rec["HV_* <-> GND (1x Vnom)"][0]
    rec_span = rec["HV_POS <-> HV_NEG (2x)"][0]
    R.p("     FROZEN-PENDING-PRIMARY-STANDARD numbers for %s:" % PART)
    R.p("        HV net to anything else        >= %.1f mm" % rec_se)
    R.p("        HV_POS to HV_NEG specifically  >= %.1f mm   (pairwise -- NOT expressible as a"
        % rec_span)
    R.p("                                                    netclass; see section 2)")
    R.p("     IEC_IIIa is the conservative read: treat bare uncoated FR-4 as an ordinary")
    R.p("     material-group-IIIa insulator rather than 'printed board'. If an auditor takes")
    R.p("     that view every number DOUBLES (%.1f / %.1f mm) and the %.1fx margin is consumed"
        % (math.ceil(rec["HV_* <-> GND (1x Vnom)"][4] * DESIGN_MARGIN * 2) / 2,
           math.ceil(rec["HV_POS <-> HV_NEG (2x)"][4] * DESIGN_MARGIN * 2) / 2, DESIGN_MARGIN))
    R.p("     by that alone. Section 1.6 shows that is not academic -- it decides the board tier.")
    R.check(rec_span > rec_se,
            "the mode-2 pairwise span demands more spacing than any single-ended HV net",
            "%.1f mm vs %.1f mm" % (rec_span, rec_se))
    R.check(rec_se >= ipc2221_clearance_mm(VNOM, "B2"),
            "recommended single-ended DRC value is not below the bare IPC B2 requirement",
            "%.1f >= %.3f mm" % (rec_se, ipc2221_clearance_mm(VNOM, "B2")))
    R.check(rec_span >= ipc2221_clearance_mm(2 * VNOM, "B2"),
            "recommended pairwise DRC value is not below the bare IPC B2 requirement",
            "%.1f >= %.3f mm" % (rec_span, ipc2221_clearance_mm(2 * VNOM, "B2")))
    for col in IPC_COLUMNS:
        vals = [ipc2221_clearance_mm(v, col) for v in
                (10, 25, 40, 75, 120, 160, 200, 275, 400, 600, 1000, 2000)]
        R.check(all(b >= a - 1e-9 for a, b in zip(vals, vals[1:])),
                "IPC-2221 column %s is monotonic non-decreasing in voltage" % col)
    R.check(ipc2221_clearance_mm(2 * VNOM, "B4") < ipc2221_clearance_mm(2 * VNOM, "B2"),
            "coated external (B4) is less demanding than uncoated external (B2) at the span",
            "%.3f < %.3f mm, a %.2fx reduction if we commit to conformal coating"
            % (ipc2221_clearance_mm(2 * VNOM, "B4"), ipc2221_clearance_mm(2 * VNOM, "B2"),
               ipc2221_clearance_mm(2 * VNOM, "B2") / ipc2221_clearance_mm(2 * VNOM, "B4")))

    # ---------------------------------------------------------------------------------
    R.h2("1.5  DELETED: the 'independent cross-check between two standards families'")
    R.p("     Session 1's NUMBERS_PROBE.md section 1.5 asserted four checks of the form")
    R.p("         IPC-2221 B2(V)  ==  IEC PD2 printed-board creepage(V)")
    R.p("     and called their agreement 'the strongest evidence in this section' and 'the")
    R.p("     transcription's only internal evidence'. It is neither. Above 500 V:")
    R.p("         IPC B2(V)  = 2.50 + 0.005*(V-500)              = 0.005 * V   identically")
    R.p("         IEC pcb(V) = 2.50 + (5.0-2.5)/500 * (V-500)    = 0.005 * V   identically")
    R.p("     so the two expressions are the SAME FUNCTION and the check cannot fail for any")
    R.p("     input. It is an algebraic tautology, not evidence.")
    R.p()
    R.p("     Worse than merely uninformative: the check is INVARIANT UNDER ANY COMMON")
    R.p("     RESCALING of both columns. That is exactly the error mode we are exposed to,")
    R.p("     because both columns were transcribed from the SAME web page. Demonstrated:")
    R.p()
    R.p("       %-10s %14s %14s %10s" % ("scale k", "k*IPC_B2(1kV)", "k*IEC_pcb(1kV)",
                                         "old check"))
    tautology_still_passes = []
    for k in (0.25, 0.5, 1.0, 2.0, 10.0):
        a = k * ipc2221_clearance_mm(1000.0, "B2")
        b = k * iec_creepage_pd2_mm(1000.0, "printed_board")[0]
        passes = abs(a - b) < 0.01 * max(a, b)
        tautology_still_passes.append(passes)
        R.p("       %-10.2f %13.3f  %13.3f  %10s" % (k, a, b, "PASSES" if passes else "fails"))
    R.p()
    R.p("     A transcription error that scaled BOTH columns by 4x -- e.g. reading a column")
    R.p("     printed in a different unit, or reading the reinforced-insulation column instead")
    R.p("     of the basic-insulation one -- would sail through the old check untouched while")
    R.p("     putting every HV gap on this board at a quarter of its requirement.")
    R.check(all(tautology_still_passes),
            "PROOF the deleted cross-check had zero discriminating power "
            "(it passes under every common rescaling, including 0.25x and 10x)",
            "%d of %d rescalings still 'PASS'"
            % (sum(tautology_still_passes), len(tautology_still_passes)))
    R.finding("The 'independent cross-check between two standards families' in session 1's "
              "NUMBERS_PROBE.md section 1.5 is an ALGEBRAIC TAUTOLOGY and has been DELETED, "
              "not repaired. Above 500 V both expressions reduce to 0.005*V identically, so "
              "its four assertions could not fail for any input; and the check is invariant "
              "under any common rescaling of both columns, which is precisely the failure "
              "mode implied by both columns having come off one web page. NO REPLACEMENT "
              "CROSS-CHECK HAS BEEN INVENTED. The clearance constants are [unverified-primary] "
              "and stay that way until a human reads a primary copy of the standard.")

    # ---------------------------------------------------------------------------------
    R.h2("1.5b  The IEC 'printed boards' column is probably MIS-TRANSCRIBED -- flagged only")
    R.p("     %-16s %10s %10s %10s %10s" % ("working V", "pcb", "MG I", "MG II", "MG IIIa"))
    dupes = 0
    anchors = [a[0] for a in IEC_PD2_ANCHORS["printed_board"]]
    for v in anchors:
        row = dict((k, dict(IEC_PD2_ANCHORS[k])[v]) for k in
                   ("printed_board", "mg_I", "mg_II", "mg_IIIa"))
        same = abs(row["printed_board"] - row["mg_I"]) < 1e-9
        dupes += 1 if same else 0
        R.p("       %-14.0f %10.2f %10.2f %10.2f %10.2f   %s"
            % (v, row["printed_board"], row["mg_I"], row["mg_II"], row["mg_IIIa"],
               "<-- IDENTICAL to MG I" if same else ""))
    R.p()
    R.p("     The 'printed boards' column and the 'material group I' column are numerically")
    R.p("     IDENTICAL at %d of the %d transcribed anchors. In IEC 60664-1 those are different"
        % (dupes, len(anchors)))
    R.p("     columns of the same table, and printed-board creepage is normally SMALLER than")
    R.p("     the material-group columns. Identical values are the classic signature of the")
    R.p("     eye sliding one column across while copying. FLAGGED, NOT GUESSED AT: this probe")
    R.p("     does not invent a corrected column.")
    R.p("     Bounded consequence, stated so the flag is not read as alarm: the recommendation")
    R.p("     is max(IPC_B2, IEC_pcb), and at both voltages that matter here the two are equal")
    R.p("     (%.3f / %.3f mm), so IEC_pcb never binds and NO RECOMMENDED VALUE MOVES if the"
        % (ipc2221_clearance_mm(VNOM, "B2"), ipc2221_clearance_mm(2 * VNOM, "B2")))
    R.p("     column turns out to be wrong -- UNLESS the corrected column is LARGER than IPC B2,")
    R.p("     which is exactly what a human reading the primary copy has to check.")
    R.check(dupes >= 2,
            "TRIPWIRE: the IEC pcb/MG-I column duplication is still present in this table "
            "(this assertion FIRES when someone corrects the table, forcing a doc update)",
            "%d of %d anchors identical" % (dupes, len(anchors)))
    R.finding("The IEC PD2 'printed boards' creepage column transcribed in this probe is "
              "numerically identical to the 'material group I' column at %d of %d anchors, "
              "the signature of reading the wrong column. FLAGGED, NOT CORRECTED -- no "
              "guess has been substituted. Consequence is bounded today because IEC_pcb "
              "never exceeds IPC B2 at 1000 or 2000 V and therefore never governs; a human "
              "reading the primary copy must confirm that remains true."
              % (dupes, len(anchors)))
    return rec, rec_se, rec_span


def section1b(rec_se, rec_span, strings):
    """1.6 board area implied by the 2 kV normal case; 1.7 the unratable module case."""
    R.h2("1.6  What the %.0f V NORMAL case costs in board area" % (2 * VNOM))
    R.p("     Two ways to hold %.0f V apart, and they are not equal:" % (2 * VNOM))
    R.p("       (i)  one bare %.1f mm gap between the HV_POS and HV_NEG regions;" % rec_span)
    R.p("       (ii) a GROUNDED GUARD CONDUCTOR between them, which converts one %.0f V gap"
        % (2 * VNOM))
    R.p("            into two %.0f V gaps of %.1f mm each, plus the guard's own copper."
        % (VNOM, rec_se))
    corridor_bare = rec_span
    corridor_guard = 2 * rec_se + GUARD_TRACE_MM
    R.p()
    R.p("       corridor, bare gap        = %.1f mm" % corridor_bare)
    R.p("       corridor, guarded         = 2 x %.1f + %.1f (guard trace) = %.1f mm"
        % (rec_se, GUARD_TRACE_MM, corridor_guard))
    R.p("       cost of guarding          = %+.1f mm" % (corridor_guard - corridor_bare))
    R.p()
    R.p("     Session 1 claimed the guard-ring split is 'free in area'. At THIS class that is")
    R.p("     almost true but not exactly: it costs the guard conductor's own width, %.1f mm,"
        % GUARD_TRACE_MM)
    R.p("     because the recommended clearance is linear in voltage above 500 V and so the")
    R.p("     two halves sum to the whole. %.1f mm is the correct answer and 'free' is not."
        % GUARD_TRACE_MM)
    R.p("     RECOMMENDED ANYWAY, for the failure behaviour rather than the area: a flashover")
    R.p("     goes to the grounded guard instead of into the other module's output stage, and")
    R.p("     in mode 2 that other stage is ENERGISED, which was not true before G0-A4.")
    R.check(abs(corridor_guard - (2 * rec_se + GUARD_TRACE_MM)) < 1e-9
            and corridor_guard > corridor_bare,
            "guard-ring split costs exactly the guard conductor width, not double the gap",
            "%.1f mm guarded vs %.1f mm bare = %+.1f mm, i.e. %.1f mm and not 'free'"
            % (corridor_guard, corridor_bare, corridor_guard - corridor_bare, GUARD_TRACE_MM))

    R.p()
    R.p("     BOARD WIDTH MODEL. Two HV islands side by side, guarded corridor between them,")
    R.p("     HV-to-edge clearance on both outer sides:")
    R.p()
    body_w = ISEGFP["body_w"] if ISEGFP else 15.70
    body_l = ISEGFP["body_l"] if ISEGFP else 39.60
    island_w = body_w + 2 * ISLAND_MARGIN_MM
    R.p("       module body                          %6.2f x %6.2f mm   [%s]"
        % (body_l, body_w, "verified-artifact, read from the footprint" if ISEGFP else "recalled"))
    R.p("       island width = body + 2 x %.1f mm     %6.2f mm            [ASSUMED margin]"
        % (ISLAND_MARGIN_MM, island_w))
    R.p("       guarded corridor                     %6.2f mm" % corridor_guard)
    R.p("       HV-to-board-edge, each side          %6.2f mm" % rec_se)
    w_min = 2 * rec_se + 2 * island_w + corridor_guard
    R.p("       ------------------------------------------------")
    R.p("       w_min = 2*%.1f + 2*%.2f + %.2f     = %6.2f mm"
        % (rec_se, island_w, corridor_guard, w_min))
    R.p()
    R.p("     BOARD LENGTH MODEL. Along each island: the bleed string and the monitor divider")
    R.p("     string run SIDE BY SIDE, not end to end, then the changeover relay, then the")
    R.p("     output lead-out. Side by side is legitimate here and the reason is worth stating:")
    R.p("     both strings hang off the SAME HV node and grade to GND over the same distance,")
    R.p("     so if they are CO-GRADED -- laid out so that equal positions along the island sit")
    R.p("     at equal potential -- the voltage BETWEEN them is small everywhere and they need")
    R.p("     no HV gap from each other. That is a layout obligation, not a free lunch: it is")
    R.p("     a generator invariant, and a rotated or reversed string breaks it silently.")
    R.p("     String lengths are COMPUTED in sections 3 and 4 from measured land patterns:")
    for k in ("bleed", "divider"):
        R.p("       %-24s %6.2f mm  (%d x %s elements + %d x %.3f mm inter-element clearance)"
            % (k + " string", strings[k]["len"], strings[k]["n"], strings[k]["pkg"],
               strings[k]["n"] - 1, strings[k]["gap"]))
    relay_l, leadout_l = 20.0, 12.0
    strings_w = (PAD_WIDTH_MM[strings["bleed"]["pkg"]]
                 + PAD_WIDTH_MM[strings["divider"]["pkg"]] + 2 * CO_GRADE_SEP_MM)
    l_hv = max(strings["bleed"]["len"], strings["divider"]["len"]) + relay_l + leadout_l
    l_min = 2 * rec_se + max(body_l, l_hv)
    R.p("       two strings side by side, width      %6.2f mm  (%.2f + %.2f + 2 x %.2f)"
        % (strings_w, PAD_WIDTH_MM[strings["bleed"]["pkg"]],
           PAD_WIDTH_MM[strings["divider"]["pkg"]], CO_GRADE_SEP_MM))
    R.p("       changeover relay                     %6.2f mm            [ASSUMED]" % relay_l)
    R.p("       output lead-out to the bulkhead      %6.2f mm            [ASSUMED]" % leadout_l)
    R.p("       HV run per island                    %6.2f mm" % l_hv)
    R.p("       module body along the same axis      %6.2f mm" % body_l)
    R.p("       ------------------------------------------------")
    R.p("       l_min = 2*%.1f + max(%.2f, %.2f)     = %6.2f mm"
        % (rec_se, body_l, l_hv, l_min))
    R.check(strings_w < body_w,
            "the two co-graded HV strings fit side by side inside the module's own body width, "
            "so putting them in parallel costs no island width at all",
            "%.2f mm of strings vs a %.2f mm module body" % (strings_w, body_w))
    R.p()
    R.p("     PLAIN ANSWER: the %.0f V normal case forces a board of at least"
        % (2 * VNOM))
    R.p("     %.0f x %.0f mm, i.e. it consumes the %.0f x %.0f mm fab tier and rules out"
        % (math.ceil(w_min), math.ceil(l_min), BOARD_TIER_MM, BOARD_TIER_MM))
    R.p("     anything smaller. The corridor alone -- copper-free board that exists only to")
    R.p("     hold the two polarities apart -- is %.2f mm x %.2f mm = %.0f mm2 = %.1f %% of a"
        % (corridor_guard, l_hv, corridor_guard * l_hv,
           100 * corridor_guard * l_hv / (BOARD_TIER_MM ** 2)))
    R.p("     %.0f x %.0f mm board." % (BOARD_TIER_MM, BOARD_TIER_MM))
    R.check(w_min <= BOARD_TIER_MM and l_min <= BOARD_TIER_MM,
            "the design fits the %.0f x %.0f mm fab tier under the printed-board reading"
            % (BOARD_TIER_MM, BOARD_TIER_MM),
            "%.2f x %.2f mm required" % (w_min, l_min))

    R.p()
    R.p("     THE SAME MODEL UNDER THE CONSERVATIVE MG IIIa READING (every number doubles):")
    rec_se_iiia = math.ceil(iec_creepage_pd2_mm(VNOM, "mg_IIIa")[0] * DESIGN_MARGIN * 2) / 2
    rec_span_iiia = math.ceil(iec_creepage_pd2_mm(2 * VNOM, "mg_IIIa")[0] * DESIGN_MARGIN * 2) / 2
    corridor_iiia = 2 * rec_se_iiia + GUARD_TRACE_MM
    w_min_iiia = 2 * rec_se_iiia + 2 * island_w + corridor_iiia
    l_min_iiia = 2 * rec_se_iiia + max(body_l, l_hv)
    R.p("       HV-to-GND %.1f mm, span %.1f mm, corridor %.1f mm"
        % (rec_se_iiia, rec_span_iiia, corridor_iiia))
    R.p("       w_min = %.2f mm    l_min = %.2f mm" % (w_min_iiia, l_min_iiia))
    R.p("       ==> %s the %.0f mm tier."
        % ("STILL FITS" if max(w_min_iiia, l_min_iiia) <= BOARD_TIER_MM else "DOES NOT FIT",
           BOARD_TIER_MM))
    R.p()
    R.p("     THIS IS WHY THE UNVERIFIED STANDARD MATTERS. Under the printed-board reading the")
    R.p("     board fits the cheap tier; under the material-group-IIIa reading it does not.")
    R.p("     The open question in 1.5 is not academic bookkeeping -- it decides board size,")
    R.p("     fab tier and enclosure. Resolve it BEFORE layout, not at the fab-commit gate.")
    R.check(max(w_min_iiia, l_min_iiia) > BOARD_TIER_MM,
            "the two candidate readings of the standard give DIFFERENT board tiers, so the "
            "unresolved standards question is decision-relevant and not bookkeeping",
            "printed-board %.1f x %.1f mm fits; MG IIIa %.1f x %.1f mm does not fit %.0f mm"
            % (w_min, l_min, w_min_iiia, l_min_iiia, BOARD_TIER_MM))

    R.p()
    R.p("     THE TWO OUTPUT CONNECTORS -- and a result that saves a lot of panel.")
    R.p("     Mode 2 puts +%.0f V on OUT_A and -%.0f V on OUT_B at the same time, so the naive"
        % (VNOM, VNOM))
    R.p("     reading is that the two bulkheads must be %.1f mm apart. They must not:" % rec_span)
    R.p("       * an SHV bulkhead's SHELL is at chassis ground, and the chassis is bonded to")
    R.p("         GND ([ISEG] Table 4: 'Case is connected to GND'), so shell-to-shell is 0 V;")
    R.p("       * each centre conductor sees %.0f V to its OWN shell, not %.0f V to the other"
        % (VNOM, 2 * VNOM))
    R.p("         centre conductor, because the grounded shells sit between them;")
    R.p("       * i.e. the connectors' own grounded bodies ARE the guard ring of 1.6, for free.")
    R.p("     So the panel requirement is the SINGLE-ENDED one per connector (%.1f mm class,"
        % rec_se)
    R.p("     comfortably inside SHV's own 5 kV rating), and IPC-2221 does not rate panel air")
    R.p("     gaps at all -- it is a PCB standard. What DOES carry the %.0f V is the board-side"
        % (2 * VNOM))
    R.p("     wiring from each output net to its bulkhead, and that stays inside the %.1f mm"
        % rec_span)
    R.p("     corridor rule like any other HV copper. Two separate HV leads, routed apart,")
    R.p("     never in one bundle, never in one sleeve.")
    R.check(rec_span > rec_se,
            "grounded connector shells reduce the panel problem from the 2x span to the 1x span",
            "panel needs the %.1f mm class per connector, not the %.1f mm span"
            % (rec_se, rec_span))

    R.h2("1.7  MODULE_CASE <-> system GND -- an UNRATABLE, component-internal item")
    R.p("     [ISEG] Table 4 note: 'Case is connected to GND'. So the module case, board GND")
    R.p("     and (per the enclosure spec) the chassis are ONE node at 0 V. There is no")
    R.p("     board-level clearance to compute between them: the pair is at zero volts.")
    R.p()
    R.p("     THAT IS NOT THE INTERESTING NUMBER. The interesting number is how far the")
    R.p("     module's own HV pin sits from its own grounded case, because that distance is")
    R.p("     INSIDE the component, is set by iseg, and is NOT ratable by IPC-2221 or")
    R.p("     IEC 60664-1 -- those standards rate printed boards and insulation systems we")
    R.p("     control, not the internals of a purchased module.")
    if ISEGFP:
        p6 = ISEGFP["pads"]["6"]
        p7 = ISEGFP["pads"]["7"]
        half_l = ISEGFP["body_l"] / 2.0
        half_w = ISEGFP["body_w"] / 2.0
        edge_x = ISEGFP["off_x"] + half_l
        edge_y = ISEGFP["off_y"] + half_w
        d_case = min(edge_x - p6["x"], edge_y - p6["y"])
        d_pin = abs(p6["y"] - p7["y"])
        gap_pin = d_pin - p6["sy"] / 2.0 - p7["sy"] / 2.0
        R.p("     Measured from this project's own footprint [ISEGFP], body centre offset")
        R.p("     +%.2f / +%.2f mm from the pin centroid:" % (ISEGFP["off_x"], ISEGFP["off_y"]))
        R.p("       pad 6 (HV)  at (%+.2f, %+.2f) mm, pad %.2f mm dia"
            % (p6["x"], p6["y"], p6["sx"]))
        R.p("       pad 7 (GND) at (%+.2f, %+.2f) mm" % (p7["x"], p7["y"]))
        R.p("       body edges   x = %+.2f mm, y = %+.2f mm" % (edge_x, edge_y))
        R.p("       HV pin to nearest grounded case edge = %.2f mm" % d_case)
        R.p("       HV pad to GND pad, copper edge to copper edge = %.2f - %.2f = %.2f mm"
            % (d_pin, p6["sy"] / 2.0 + p7["sy"] / 2.0, gap_pin))
        R.p()
        R.p("     So at %.0f V the module holds its HV pin %.2f mm from its own grounded case,"
            % (VNOM, d_case))
        R.p("     while this design demands %.1f mm between HV copper and GND copper on the"
            % rec_se)
        R.p("     board -- %.1fx more. The module is not wrong and we are not wrong: iseg is"
            % (rec_se / d_case))
        R.p("     potting/encapsulating an internal insulation system whose withstand voltage")
        R.p("     they type-test and DO NOT PUBLISH, and we are spacing bare air over uncoated")
        R.p("     laminate. The two are not comparable and must not be compared.")
        R.p()
        R.p("     WHAT THIS MEANS IN PRACTICE, stated as rules rather than as a number:")
        R.p("       1. Do NOT apply the board clearance rule to the module's own pin field.")
        R.p("          A DRC that flags pad 6 against pad 7 at %.1f mm is flagging iseg's" % rec_se)
        R.p("          construction, not ours. Our footprint must nonetheless CLEAR it --")
        R.p("          see the assertion below, which passes here and would not at 2 kV.")
        R.p("       2. Do NOT run board copper into the %.2f mm shadow around pad 6. The"
            % d_case)
        R.p("          board-side requirement is still %.1f mm; the module's internals do not"
            % rec_se)
        R.p("          license us to be tighter.")
        R.p("       3. The module case is a TOUCHABLE grounded conductor. It is the reason the")
        R.p("          chassis bond is a safety requirement and not an EMC nicety.")
        R.p("       4. iseg publishes NO isolation/withstand rating for HV-pin-to-case. That")
        R.p("          question is on the open list to ask iseg (D-1 companion). Until it is")
        R.p("          answered this row stays UNRATABLE, and no session may substitute a")
        R.p("          board-standard number for it.")
        R.check(gap_pin >= rec_se,
                "the module's own HV-pad-to-GND-pad copper gap clears our board rule at %.0f V"
                % VNOM,
                "%.2f mm available vs %.1f mm required -- %.2f mm margin (this FAILS at any "
                "class above %.0f V)" % (gap_pin, rec_se, gap_pin - rec_se,
                                         gap_pin / DESIGN_MARGIN / 0.005))
        R.check(d_case < rec_se,
                "the module's INTERNAL HV-pin-to-case distance is tighter than our board rule, "
                "which is exactly why this row is unratable rather than merely lenient",
                "%.2f mm internal vs %.1f mm board rule = %.1fx"
                % (d_case, rec_se, rec_se / d_case))
        p6_clr = p6["clearance"]
        if p6_clr is not None:
            R.p()
            R.p("     *** DEFECT FOUND IN A COMMITTED ARTIFACT, reported not silently fixed ***")
            R.p("     The footprint carries a PER-PAD local clearance override on pad 6 of")
            R.p("     %.2f mm. In KiCad a pad-level (clearance ...) REPLACES the netclass value"
                % p6_clr)
            R.p("     for that pad. The netclass value this probe recommends is %.1f mm."
                % rec_se)
            R.p("     %.2f mm is the BARE IPC B2 value at %.0f V with the %.1fx design margin"
                % (p6_clr, VNOM, DESIGN_MARGIN))
            R.p("     omitted -- so the single most critical pad on the board would be DRC'd at")
            R.p("     %.2f mm while every other HV net is held to %.1f mm, silently."
                % (p6_clr, rec_se))
            R.p("     Fix in hardware/hvctl/gen_lib_footprints.py (CREEPAGE_MM must carry the")
            R.p("     design margin) and REGENERATE. Never hand-edit the .kicad_mod. Not fixed")
            R.p("     here: this is the numbers probe, and silently editing another generator")
            R.p("     inside this task is how a finding gets buried.")
            R.finding("hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod carries a per-pad "
                      "local clearance override of %.2f mm on pad 6 (HV). A KiCad pad-level "
                      "clearance REPLACES the netclass clearance, so with the netclass at "
                      "%.1f mm the most critical pad on the board is silently checked at "
                      "%.2f mm -- the bare IPC B2 value with the %.1fx design margin dropped. "
                      "FIX THE GENERATOR gen_lib_footprints.py (its CREEPAGE_MM constant) and "
                      "regenerate; do not hand-edit the artifact. Deliberately NOT fixed by "
                      "this probe."
                      % (p6_clr, rec_se, p6_clr, DESIGN_MARGIN))
    else:
        R.p("     [SKIP] module footprint not readable at %s" % ISEG_FP)

    R.blind("whether the fabricator can hold the spacing (no DFM query run); the real surface "
            "resistivity of the chosen laminate; altitude (column B3 is 5x B2 above 3050 m -- "
            "irrelevant at New Haven, 12 m); the module's internal withstand voltage, which "
            "iseg does not publish; and whether the transcribed standards values are the right "
            "values at all, which is the open item of 1.5.")


# =====================================================================================
# RESISTOR PART SCREEN -- shared by sections 1.6, 3 and 4
# =====================================================================================

RES_DERATE = 0.5   # [ASSUMED] operate at <= 50 % of rated working voltage

# name -> (package, max working voltage V, evidence tag)
RES_OPTIONS = [
    ("0805 thick film (Yageo RC)", "0805", 150.0, "ARCH12"),
    ("1206 thick film (Yageo RC)", "1206", 200.0, "ARCH12"),
    ("2010 thick film (Yageo RC)", "2010", 200.0, "ARCH12"),
    ("2512 thick film (Yageo RC)", "2512", 200.0, "ARCH12"),
    ("1206 HV series",             "1206", 800.0, "ASSUMED"),
    ("2512 HV series",             "2512", 1500.0, "ASSUMED"),
]
YAGEO_MAX_R_1PCT = 2.2e6   # [ARCH12] the +/-1 % range stops here

# The monitor divider's top-leg element count. Defined HERE, once, because BOTH the
# error budget (section 4.3, where the VCR term goes as 1/N) and the string geometry
# (section 1.6, where N sets the physical length and the per-element voltage) depend
# on it. Session 2 mutation test M8 found these had been two separate literals that
# could disagree silently: perturbing one moved the error budget while the pad-gap
# and working-voltage screens went on evaluating the other.
N_TOP_ELEMENTS = 10
# The part the divider string is built from, screened out of RES_OPTIONS by name so
# that its package AND its working-voltage rating come from one row, not two literals.
DIVIDER_PART = "1206 HV series"


def series_count(total_v, per_part_v, derate=RES_DERATE):
    return int(math.ceil(total_v / (per_part_v * derate)))


def string_geometry(n, pkg, v_total):
    """Physical length of an N-element series string, with the inter-element gap set by
    the voltage that actually appears BETWEEN adjacent elements (V_total / N).

        L = N * pad_extent(pkg) + (N-1) * IPC_B2(V_total/N)
    """
    v_el = v_total / float(n)
    gap = ipc2221_clearance_mm(v_el, "B2")
    return {"n": n, "pkg": pkg, "v_el": v_el, "gap": gap,
            "len": n * PAD_EXTENT_MM[pkg] + (n - 1) * gap}


def res_option(name):
    """One row of RES_OPTIONS by name -> (package, V_rated, evidence tag). Raises if absent,
    so a renamed part is a structural failure (exit 2) rather than a silent fallback."""
    for nm, pkg, v_rated, tag in RES_OPTIONS:
        if nm == name:
            return pkg, v_rated, tag
    raise KeyError("no RES_OPTIONS row named %r" % name)


BLEED_PART = "2512 HV series"


def compute_strings():
    """The two HV resistor strings, needed by section 1.6 before sections 3 and 4 print.

    Both strings take their package AND their working-voltage rating from the SAME
    RES_OPTIONS row, and the divider takes its element count from the SAME
    N_TOP_ELEMENTS the error budget uses. Nothing here is a second literal.
    """
    b_pkg, b_v, _ = res_option(BLEED_PART)
    d_pkg, d_v, _ = res_option(DIVIDER_PART)
    n_bleed = series_count(VNOM, b_v)
    s_bleed = string_geometry(n_bleed, b_pkg, VNOM)
    s_div = string_geometry(N_TOP_ELEMENTS, d_pkg, VNOM)
    s_bleed["v_rated"], s_bleed["part"] = b_v, BLEED_PART
    s_div["v_rated"], s_div["part"] = d_v, DIVIDER_PART
    return {"bleed": s_bleed, "divider": s_div}


# =====================================================================================
# SECTION 2 -- NETCLASS AND .kicad_dru RULES
# =====================================================================================

REQUIRED_NETCLASS_FIELDS = [
    "bus_width", "clearance", "diff_pair_gap", "diff_pair_via_gap", "diff_pair_width",
    "line_style", "microvia_diameter", "microvia_drill", "name", "pcb_color", "priority",
    "schematic_color", "track_width", "tuning_profile", "via_diameter", "via_drill",
    "wire_width",
]
SCHEMATIC_SIDE_FIELDS = ["wire_width", "bus_width", "line_style", "schematic_color"]


def hv_netclass(name, clearance_mm, color):
    """One net_settings.classes entry, complete with its SCHEMATIC fields.

    Bootstrap V.3: a class carrying only PCB fields breaks eeschema connectivity for every
    net in it, silently, only on project load, while ERC / netlist export / every check
    built on kicad-cli stay green -- because kicad-cli never reads .kicad_pro.
    """
    return {"name": name, "clearance": round(clearance_mm, 3), "track_width": 0.5,
            "via_diameter": 1.0, "via_drill": 0.5, "microvia_diameter": 0.3,
            "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
            "schematic_color": color, "pcb_color": color, "priority": 1,
            "tuning_profile": ""}


def ipc_ampacity_a(width_mm, thickness_oz=1.0, rise_c=10.0, external=True):
    """I = k * dT^0.44 * A^0.725, A in mil^2, k = 0.048 external / 0.024 internal."""
    area_mil2 = (width_mm / 0.0254) * (1.37 * thickness_oz)
    return (0.048 if external else 0.024) * (rise_c ** 0.44) * (area_mil2 ** 0.725)


def section2(rec_se, rec_span):
    R.h1("SECTION 2 -- HV NETCLASS RULES (.kicad_pro net_settings.classes + .kicad_dru)")
    R.p("Source for the required field set: " + SOURCES["KICAD"])

    R.h2("2.1  HV track width is not an ampacity question")
    amp = ipc_ampacity_a(0.5)
    R.p("     Worst-case HV current on this board = 1.5 x Inom = %.2f mA ([ISEG] Table 2 note)."
        % (IOUT_LIMIT_A * 1e3))
    R.p("     A 0.5 mm track in 1 oz external copper carries %.2f A at a 10 C rise" % amp)
    R.p("     (IPC-2221 fit I = 0.048 * dT^0.44 * A^0.725, A in mil^2). Headroom = %.0fx."
        % (amp / IOUT_LIMIT_A))
    R.p("     HV track width is therefore chosen for etch-defect robustness, edge-field")
    R.p("     uniformity and inspectability -- 0.5 mm minimum, rounded corners, no acute")
    R.p("     angles. DRC cannot check corner geometry, so that half is a generator invariant.")
    R.check(amp > 100 * IOUT_LIMIT_A,
            "0.5 mm HV track has >100x ampacity headroom",
            "%.2f A capacity vs %.2f mA demand" % (amp, IOUT_LIMIT_A * 1e3))

    R.h2("2.2  Class definitions for the frozen part")
    classes = [hv_netclass("HV_POS", rec_se, "rgba(200, 0, 0, 1.000)"),
               hv_netclass("HV_NEG", rec_se, "rgba(0, 0, 200, 1.000)"),
               hv_netclass("HV_OUT_A", rec_se, "rgba(160, 0, 160, 1.000)"),
               hv_netclass("HV_OUT_B", rec_se, "rgba(160, 80, 0, 1.000)")]
    R.p("     %-12s %12s %12s   %s" % ("class", "clearance", "track_width", "carries"))
    carries = {"HV_POS": "positive module HV pin -> changeover relay",
               "HV_NEG": "negative module HV pin -> changeover relay",
               "HV_OUT_A": "output A: combined bipolar (mode 1) or positive (mode 2)",
               "HV_OUT_B": "output B: dead (mode 1) or negative (mode 2)"}
    for c in classes:
        R.p("     %-12s %11.1fmm %11.1fmm   %s"
            % (c["name"], c["clearance"], c["track_width"], carries[c["name"]]))
    R.p()
    R.p("     All four take the SINGLE-ENDED %.1f mm value, not the %.1f mm span value,"
        % (rec_se, rec_span))
    R.p("     because a KiCad netclass clearance is a MINIMUM AGAINST EVERYTHING. Putting")
    R.p("     %.1f mm here would also push every HV net %.1f mm away from GND, which is twice"
        % (rec_span, rec_span))
    R.p("     what GND needs and would waste the board twice over.")
    R.p()
    R.p("     NOTE the mode-2 consequence: HV_OUT_B is a REAL, PERMANENTLY-CLASSED HV net now.")
    R.p("     Session 1 had one output net. Two outputs means two HV classes, two bleed paths,")
    R.p("     two monitor dividers and two connectors -- all of it doubled, none of it shared.")

    R.h2("2.3  The pairwise rule a netclass structurally cannot express")
    R.p("     KiCad's netclass 'clearance' is a per-class minimum against all other copper. It")
    R.p("     has no pairwise form. The %.1f mm HV_POS<->HV_NEG requirement therefore lives in"
        % rec_span)
    R.p("     hardware/hvctl/hvctl.kicad_dru:")
    R.p()
    R.p('        (version 1)')
    R.p('        (rule "HV_POS to HV_NEG bipolar span"')
    R.p('          (constraint clearance (min %.1fmm))' % rec_span)
    R.p('          (condition "A.NetClass == \'HV_POS\' && B.NetClass == \'HV_NEG\'"))')
    R.p('        (rule "HV_OUT_A to HV_OUT_B bipolar span"        ; mode 2, both live')
    R.p('          (constraint clearance (min %.1fmm))' % rec_span)
    R.p('          (condition "A.NetClass == \'HV_OUT_A\' && B.NetClass == \'HV_OUT_B\'"))')
    R.p('        (rule "HV nets to board edge"')
    R.p('          (constraint edge_clearance (min %.1fmm))' % rec_se)
    R.p('          (condition "A.NetClass == \'HV_POS\' || A.NetClass == \'HV_NEG\''
        ' || A.NetClass == \'HV_OUT_A\' || A.NetClass == \'HV_OUT_B\'"))')
    R.p()
    R.p("     TWO pairwise rules now, not one. G0-A4 added the second: in mode 2 the two")
    R.p("     OUTPUT nets are simultaneously live at opposite polarity, exactly like the two")
    R.p("     module nets. A design that rules only the module pair is under-spaced")
    R.p("     everywhere downstream of the relay.")
    R.finding("G0-A4 adds a SECOND pairwise DRC rule that did not exist in session 1: "
              "HV_OUT_A <-> HV_OUT_B must also hold %.1f mm, because in dual-unipolar mode "
              "the two OUTPUT nets are simultaneously live at opposite polarity. Ruling only "
              "the HV_POS<->HV_NEG module pair leaves every net downstream of the changeover "
              "relay silently spaced for %.1f mm instead of %.1f mm."
              % (rec_span, rec_se, rec_span))
    R.p()
    R.p("     And never infer 'the rule applied' from 'DRC passed'. kicad-cli pcb drc EXITS 0")
    R.p("     ON VIOLATIONS unless --exit-code-violations is passed (docs/ENVIRONMENT.md), so")
    R.p("     the check must read the report back and look for the rule BY NAME.")

    R.h2("2.4  Every class must carry its schematic fields")
    R.p("     Required field set, measured from a project file KiCad 10.0 wrote itself:")
    R.p("       " + ", ".join(REQUIRED_NETCLASS_FIELDS))
    R.p("     Of these the SCHEMATIC-side fields are: " + ", ".join(SCHEMATIC_SIDE_FIELDS))
    for cls in classes:
        missing = [f for f in REQUIRED_NETCLASS_FIELDS if f not in cls]
        R.check(not missing, "class %s carries the complete KiCad 10 field set" % cls["name"],
                "missing: %s" % missing if missing else "%d/%d fields"
                % (len(REQUIRED_NETCLASS_FIELDS), len(REQUIRED_NETCLASS_FIELDS)))
    if os.path.isfile(PHASE0_PRO):
        try:
            with open(PHASE0_PRO, "r", encoding="utf-8") as fh:
                pro = json.load(fh)
            real = sorted(pro["net_settings"]["classes"][0].keys())
            R.check(real == sorted(REQUIRED_NETCLASS_FIELDS),
                    "hardcoded field list matches the field set KiCad 10.0 actually wrote",
                    "read from %s" % os.path.basename(PHASE0_PRO))
        except Exception as exc:                                   # pragma: no cover
            R.p("  [SKIP] could not read %s (%s)" % (PHASE0_PRO, exc))
    else:
        R.p("  [SKIP] %s absent; field list not cross-checked this run." % PHASE0_PRO)

    R.h2("2.5  Assignment patterns")
    R.p("     netclass_patterns uses globs. Hierarchical net names need the sheet wildcard or")
    R.p("     the pattern silently matches nothing (bootstrap V.3):")
    for n in ("HV_POS", "HV_NEG", "HV_OUT_A", "HV_OUT_B"):
        R.p('         {"netclass": "%s", "pattern": "*/%s*"}' % (n, n))
    R.blind("whether KiCad actually applied the class (only reading back track widths and "
            "running DRC with the named custom rule proves that); whether any pattern matched "
            "any net; per-pad local clearance overrides, which SILENTLY REPLACE the netclass "
            "value and which section 1.7 caught on pad 6 of the module footprint.")
    return classes


# =====================================================================================
# SECTION 3 -- BLEED / DISCHARGE / STORED ENERGY
# =====================================================================================

TOUCH_SAFE_V = 60.0             # [TOUCH]
DISCHARGE_TARGET_S = 5.0        # [ASSUMED] stricter of the commonly cited 5 s / 10 s
BLEED_FRACTION_OF_INOM = 0.10   # [ASSUMED] permanent-load budget for the bleed
HAZ_ENERGY_J = 0.350            # [ENERGY]
HAZ_CHARGE_C = 50e-6            # [ENERGY]

C_BOARD = 20e-12                # [ASSUMED] HV copper + connector + divider top node
C_MODULE = 100e-12              # [ASSUMED] MEASURABLE NOW -- iseg does not specify it
C_LEAD_PER_M = 100e-12          # [ASSUMED] worst end of the 60-100 pF/m range
C_LOAD_LIMIT = 10e-9            # interface limit, DECISIONS NUM-13

C_SCENARIOS = [
    ("bare board, no cable",        C_BOARD + C_MODULE),
    ("2 m SHV lead, no load",       C_BOARD + C_MODULE + 2 * C_LEAD_PER_M),
    ("2 m SHV lead + 1 nF load",    C_BOARD + C_MODULE + 2 * C_LEAD_PER_M + 1e-9),
    ("10 m lead + 10 nF load",      C_BOARD + C_MODULE + 10 * C_LEAD_PER_M + C_LOAD_LIMIT),
]
C_NOMINAL = C_SCENARIOS[1][1]
C_WORST = C_SCENARIOS[3][1]


def discharge_time_s(r_ohm, c_farad, v0, v_target):
    """V(t) = V0*exp(-t/RC)  =>  t = R*C*ln(V0/V_target)."""
    if v_target <= 0 or v0 <= v_target:
        return 0.0
    return r_ohm * c_farad * math.log(v0 / v_target)


def r_for_discharge(t_s, c_farad, v0, v_target):
    """R = t / (C * ln(V0/V_target))."""
    return t_s / (c_farad * math.log(v0 / v_target))


def section3(strings):
    R.h1("SECTION 3 -- BLEED / DISCHARGE / STORED ENERGY at %.0f V" % VNOM)
    R.p("Touch-safe threshold: %.0f V DC.  %s" % (TOUCH_SAFE_V, SOURCES["TOUCH"]))
    R.p("Hazardous-energy thresholds: %.0f mJ and %.0f uC.  %s"
        % (HAZ_ENERGY_J * 1e3, HAZ_CHARGE_C * 1e6, SOURCES["ENERGY"]))

    R.h2("3.1  Output capacitance -- the assumption, and it is MEASURABLE NOW")
    R.p("     [ISEG] specifies NO output capacitance. Everything in this section inherits that")
    R.p("     gap. Session 1 could only assume; THE MODULES ARE NOW IN HAND, so every term")
    R.p("     below is a bench measurement away from being a fact.")
    R.p()
    R.p("       board stray (HV copper, connector, divider top node)  %6.0f pF   [ASSUMED]"
        % (C_BOARD * 1e12))
    R.p("       module internal output capacitance                    %6.0f pF   "
        "[ASSUMED -- *** MEASURABLE NOW ***]" % (C_MODULE * 1e12))
    R.p("       SHV coaxial lead                                  %6.0f pF/m   [ASSUMED]"
        % (C_LEAD_PER_M * 1e12))
    R.p("       detector / load                                   0 .. %4.0f nF   "
        "[interface limit NUM-13]" % (C_LOAD_LIMIT * 1e9))
    R.p()
    for i, (k, c) in enumerate(C_SCENARIOS, 1):
        R.p("       C%d  %-30s C_total = %9.3f nF%s"
            % (i, k, c * 1e9, "   <- NOMINAL" if abs(c - C_NOMINAL) < 1e-15 else
               ("   <- WORST" if abs(c - C_WORST) < 1e-15 else "")))
    measurable("Module internal output capacitance (assumed %.0f pF). Measure with an LCR "
               "meter on the HV pin of an UNPOWERED, BLED module, or by timing the decay "
               "against a known bleed resistor. The second method also yields the internal "
               "bleeder resistance, which iseg also does not publish."
               % (C_MODULE * 1e12))
    measurable("Module internal bleeder resistance (unpublished). Charge the output, disable, "
               "and time the open-circuit decay with an HV-rated 1000:1 probe of KNOWN input "
               "impedance; subtract the probe.")
    measurable("VSET step response / settling time (unpublished). Step VSET 10 % -> 90 % and "
               "watch VMON on a scope. This sets the changeover dead-band budget and the "
               "state machine's DISCHARGE timeout.")
    measurable("Turn-on time from +VIN (unpublished). Time from +VIN valid to VMON settled "
               "with /ON already asserted. This sets the power-on sequencing requirement.")
    assume("Board stray output capacitance %.0f pF." % (C_BOARD * 1e12))
    assume("SHV lead capacitance %.0f pF/m." % (C_LEAD_PER_M * 1e12))
    assume("Touch-safe target: discharge to %.0f V DC within %.0f s of disable."
           % (TOUCH_SAFE_V, DISCHARGE_TARGET_S))
    assume("Bleed permanent-load budget: <= %.0f %% of Inom." % (100 * BLEED_FRACTION_OF_INOM))

    R.h2("3.2  R required for a chosen discharge time -- the question as asked")
    R.p("     R(t) = t / ( C * ln(V0/V_safe) ),  V0 = %.0f V, V_safe = %.0f V,"
        % (VNOM, TOUCH_SAFE_V))
    R.p("     ln(%.0f/%.0f) = %.4f" % (VNOM, TOUCH_SAFE_V, math.log(VNOM / TOUCH_SAFE_V)))
    R.p()
    R.p("     %-6s %14s %12s %14s %12s" %
        ("t (s)", "R at C_nom", "I_bleed", "R at C_worst", "I_bleed"))
    R.p("     %-6s %14s %12s %14s %12s" %
        ("", "(%.3f nF)" % (C_NOMINAL * 1e9), "(% of Inom)",
         "(%.2f nF)" % (C_WORST * 1e9), "(% of Inom)"))
    for t in (1.0, 5.0, 30.0):
        rn = r_for_discharge(t, C_NOMINAL, VNOM, TOUCH_SAFE_V)
        rw = r_for_discharge(t, C_WORST, VNOM, TOUCH_SAFE_V)
        R.p("     %-6.0f %11.2f Gohm %11.4f %% %11.2f Mohm %11.4f %%"
            % (t, rn / 1e9, 100 * (VNOM / rn) / INOM, rw / 1e6, 100 * (VNOM / rw) / INOM))
    R.p()
    R.p("     READ THIS THE RIGHT WAY ROUND. A 5 s discharge from %.0f V needs %.1f Gohm at"
        % (VNOM, r_for_discharge(5.0, C_NOMINAL, VNOM, TOUCH_SAFE_V) / 1e9))
    R.p("     the nominal capacitance -- a resistance so high that board surface leakage would")
    R.p("     swamp it and a real part would not hold its value. DISCHARGE TIME IS NOT THE")
    R.p("     CONSTRAINT AT THIS CLASS. The constraints are the permanent-load budget and the")
    R.p("     resistor's working-voltage rating. That inverts the usual bleed-design intuition")
    R.p("     and is only visible with the numbers on the page.")

    R.h2("3.3  The bleed we actually fit, sized by the permanent-load budget")
    r_bleed = VNOM / (BLEED_FRACTION_OF_INOM * INOM)
    i_bleed = VNOM / r_bleed
    p_bleed = VNOM * VNOM / r_bleed
    R.p("     R_bleed = Vnom / (f * Inom),  f = %.2f" % BLEED_FRACTION_OF_INOM)
    R.p("             = %.0f / (%.2f * %.4g) = %.1f Mohm" % (VNOM, BLEED_FRACTION_OF_INOM,
                                                             INOM, r_bleed / 1e6))
    R.p("     I_bleed = %.1f uA = %.2f %% of Inom      P_bleed = %.1f mW"
        % (i_bleed * 1e6, 100 * i_bleed / INOM, p_bleed * 1e3))
    R.p("     tau     = R*C = %.1f ms at C_nom, %.1f ms at C_worst"
        % (r_bleed * C_NOMINAL * 1e3, r_bleed * C_WORST * 1e3))
    R.p()
    R.p("     The bleed is PERMANENT. A switched bleed can fail open, and a bleed that only")
    R.p("     runs on command is not a bleed. So f is a real budget, spent forever.")
    R.p()
    R.p("     %-32s %14s %12s" % ("capacitance scenario", "t to %.0f V" % TOUCH_SAFE_V,
                                  "verdict"))
    worst_t = 0.0
    for k, c in C_SCENARIOS:
        t = discharge_time_s(r_bleed, c, VNOM, TOUCH_SAFE_V)
        worst_t = max(worst_t, t)
        R.p("     %-32s %11.4f s  %12s" % (k, t, "ok" if t <= DISCHARGE_TARGET_S else "TOO SLOW"))
    R.check(worst_t <= DISCHARGE_TARGET_S,
            "the %.1f Mohm bleed reaches %.0f V within %.0f s in every capacitance scenario"
            % (r_bleed / 1e6, TOUCH_SAFE_V, DISCHARGE_TARGET_S),
            "worst %.4f s at %.2f nF" % (worst_t, C_WORST * 1e9))
    R.check(abs(100 * i_bleed / INOM - 100 * BLEED_FRACTION_OF_INOM) < 1e-9,
            "bleed current is exactly the budgeted fraction of Inom",
            "%.1f uA of a %.1f uA Inom = %.2f %%"
            % (i_bleed * 1e6, INOM * 1e6, 100 * i_bleed / INOM))

    R.h2("3.4  How many bleeds, and where -- G0-A4 doubles this")
    R.p("     One bleed PER MODULE, on that module's own HV pin, UPSTREAM of the changeover")
    R.p("     relay. A bleed only downstream cannot discharge the node behind an open contact,")
    R.p("     and in mode 1 that node is exactly the one holding full voltage after disable.")
    R.p("     PLUS one bleed per OUTPUT node, downstream, to cover the cable and the load.")
    R.p()
    R.p("     Mode 1 (one output):  2 module bleeds + 1 output bleed = 3")
    R.p("     Mode 2 (two outputs): 2 module bleeds + 2 output bleeds = 4")
    R.p("     Fit 4. The mode is switchable at runtime, so the board must carry the mode-2 set.")
    R.p()
    R.p("     PERMANENT LOAD PER MODULE, both loads present at once in mode 2:")
    div_frac = 0.01
    total_frac = BLEED_FRACTION_OF_INOM + div_frac
    R.p("       bleed            %.2f %% of Inom = %.1f uA"
        % (100 * BLEED_FRACTION_OF_INOM, BLEED_FRACTION_OF_INOM * INOM * 1e6))
    R.p("       monitor divider  %.2f %% of Inom = %.1f uA   (section 4 -- the binding one)"
        % (100 * div_frac, div_frac * INOM * 1e6))
    R.p("       ------------------------------------------")
    R.p("       total            %.2f %% of Inom = %.1f uA, leaving %.1f uA = %.2f %% for the load"
        % (100 * total_frac, total_frac * INOM * 1e6, (1 - total_frac) * INOM * 1e6,
           100 * (1 - total_frac)))
    R.p("     In mode 2 EACH module carries its own copy of this. The budgets do not share and")
    R.p("     do not average: two outputs means two full sets of permanent load.")
    R.check(total_frac < 0.15,
            "permanent load per module (bleed + divider) stays under 15 % of Inom",
            "%.2f %% = %.1f uA of %.1f uA"
            % (100 * total_frac, total_frac * INOM * 1e6, INOM * 1e6))
    R.p()
    R.p("     And per DECISIONS NUM-09 each bleed is TWO PARALLEL STRINGS, never one chain:")
    R.p("     an N-element series chain has N chances to go open and an open bleed is silently")
    R.p("     undetectable. Two %.1f Mohm strings in parallel give the %.1f Mohm target and"
        % (2 * r_bleed / 1e6, r_bleed / 1e6))
    R.p("     degrade tau by 2x on a single open instead of removing the path entirely.")

    R.h2("3.5  Working-voltage rating and the series-string count -- the binding constraint")
    R.p("     A resistor's WORKING VOLTAGE rating, not its power rating, is what limits it at")
    R.p("     %.0f V.  N = ceil( V / (V_rating * derate) ),  derate = %.2f." % (VNOM, RES_DERATE))
    R.p("     Ratings tagged [ARCH12] come from the Yageo RC datasheet PDF, read locally.")
    R.p()
    R.p("     %-30s %8s %5s %10s %10s %11s %8s" %
        ("part option", "V_rated", "N", "V/element", "P/element", "pad gap", "IPC B2"))
    rejects = []
    for name, pkg, vr, tag in RES_OPTIONS:
        n = series_count(VNOM, vr)
        v_el = VNOM / n
        gap = PAD_GAP_MM[pkg]
        need = ipc2221_clearance_mm(v_el, "B2")
        ok = gap >= need
        if not ok:
            rejects.append((name, n, v_el, gap, need))
        R.p("     %-30s %7.0fV %5d %9.1fV %8.2f mW %8.3f mm %7.3f mm  %s"
            % (name, vr, n, v_el, p_bleed / n * 1e3, gap, need,
               "OK" if ok else "*** REJECTED ***"))
    R.p()
    R.p("     %d of %d candidates are rejected ON THEIR OWN PAD GAP. A part's voltage RATING"
        % (len(rejects), len(RES_OPTIONS)))
    R.p("     and its PACKAGE CLEARANCE are independent constraints and only the first is on")
    R.p("     the datasheet: a rating high enough to need few elements puts a large voltage")
    R.p("     across a small package.")
    for name, n, v_el, gap, need in rejects:
        R.finding("Bleed/divider part '%s' is REJECTED at %.0f V: a working-voltage rating "
                  "high enough to need only N=%d elements puts %.0f V across a package whose "
                  "own pad-to-pad gap is %.3f mm, below the %.3f mm IPC-2221 B2 clearance "
                  "that voltage demands." % (name, VNOM, n, v_el, gap, need))
    R.check(len(rejects) > 0,
            "the pad-gap screen actually rejects something (proves it is not vacuous)",
            "%d rejected: %s" % (len(rejects), ", ".join(r[0] for r in rejects)))
    bs = strings["bleed"]
    R.p()
    R.p("     RECOMMENDED BLEED PART: 2512 HV series.")
    R.p("       N = %d, %.0f V per element, %.2f mW per element" % (bs["n"], bs["v_el"],
                                                                   p_bleed / bs["n"] * 1e3))
    R.p("       pad gap %.3f mm vs IPC B2 requirement %.3f mm at %.0f V"
        % (PAD_GAP_MM["2512"], bs["gap"], bs["v_el"]))
    R.p("       string length = %d x %.3f mm land + %d x %.3f mm inter-element = %.2f mm"
        % (bs["n"], PAD_EXTENT_MM["2512"], bs["n"] - 1, bs["gap"], bs["len"]))
    R.p("       x2 for the parallel-string rule -> two strings side by side, not end to end.")
    R.check(PAD_GAP_MM[bs["pkg"]] >= bs["gap"],
            "recommended bleed part clears its own pad gap at the per-element voltage",
            "N=%d, %.0f V/element, gap %.3f mm vs need %.3f mm"
            % (bs["n"], bs["v_el"], PAD_GAP_MM[bs["pkg"]], bs["gap"]))
    R.check(series_count(VNOM, 200.0) > series_count(VNOM, 1500.0),
            "the ARCH-12 correction has teeth: a 200 V-rated 2512 needs more elements than "
            "the 500 V figure session 1's probe used",
            "N=%d at the verified 200 V rating vs N=%d at the folklore 500 V rating"
            % (series_count(VNOM, 200.0), series_count(VNOM, 500.0)))
    R.finding("Session 1's probe rated a standard 2512 chip resistor at 500 V working voltage. "
              "DECISIONS ARCH-12, which is [verified-artifact] from the actual Yageo RC "
              "datasheet, says 200 V -- and that upsizing 1206->2010->2512 buys power, not "
              "volts. The corrected rating changes the standard-part series count at %.0f V "
              "from N=%d to N=%d. This probe uses the verified number; the two documents "
              "disagreed and the datasheet wins."
              % (VNOM, series_count(VNOM, 500.0), series_count(VNOM, 200.0)))

    R.h2("3.6  Stored energy: shock hazard, or startle hazard?")
    R.p("     E = 0.5*C*V^2 ,  Q = C*V .  Thresholds %.0f mJ / %.0f uC."
        % (HAZ_ENERGY_J * 1e3, HAZ_CHARGE_C * 1e6))
    R.p()
    R.p("     %-32s %8s %12s %12s %10s" % ("scenario", "V (V)", "E (mJ)", "Q (uC)", "verdict"))
    for k, c in C_SCENARIOS:
        e = 0.5 * c * VNOM * VNOM
        q = c * VNOM
        R.p("     %-32s %8.0f %12.5f %12.4f %10s"
            % (k, VNOM, e * 1e3, q * 1e6,
               "below" if (e < HAZ_ENERGY_J and q < HAZ_CHARGE_C) else "HAZARDOUS"))
        R.check(e < HAZ_ENERGY_J and q < HAZ_CHARGE_C,
                "stored energy and charge below the hazard thresholds (%s)" % k,
                "E=%.5f mJ (<%.0f), Q=%.4f uC (<%.0f)"
                % (e * 1e3, HAZ_ENERGY_J * 1e3, q * 1e6, HAZ_CHARGE_C * 1e6))
    R.p()
    R.p("     MODE-2 BRIDGING CASE, which did not exist before G0-A4: a person or a dropped")
    R.p("     tool bridging OUT_A to OUT_B sees %.0f V across the SERIES combination of the"
        % (2 * VNOM))
    R.p("     two output capacitances, C_A*C_B/(C_A+C_B) = C/2 for equal outputs:")
    for k, c in C_SCENARIOS:
        cs = c / 2.0
        e = 0.5 * cs * (2 * VNOM) ** 2
        q = cs * 2 * VNOM
        R.p("       %-30s C_series %8.3f nF   E = %9.5f mJ   Q = %8.4f uC"
            % (k, cs * 1e9, e * 1e3, q * 1e6))
        R.check(e < HAZ_ENERGY_J and q < HAZ_CHARGE_C,
                "mode-2 OUT_A-to-OUT_B bridging stays below the hazard thresholds (%s)" % k,
                "E=%.5f mJ, Q=%.4f uC at %.0f V" % (e * 1e3, q * 1e6, 2 * VNOM))
    R.p("     Energy doubles (half the C, four times the V^2) and charge is unchanged.")
    R.p()
    c_haz_q = HAZ_CHARGE_C / VNOM
    c_haz_e = 2 * HAZ_ENERGY_J / VNOM ** 2
    R.p("     Inverted -- the capacitance at which %.0f V BECOMES a hazardous stored-energy"
        % VNOM)
    R.p("     source:  charge criterion  C = Q/V    = %6.1f nF" % (c_haz_q * 1e9))
    R.p("              energy criterion  C = 2E/V^2 = %6.1f nF" % (c_haz_e * 1e9))
    R.p("     The CHARGE criterion binds first.")
    R.check(c_haz_q < c_haz_e,
            "the charge criterion binds before the energy criterion at %.0f V" % VNOM,
            "%.1f nF (charge) vs %.1f nF (energy)" % (c_haz_q * 1e9, c_haz_e * 1e9))
    R.p()
    R.p("     *** THE ANSWER TO 'SHOCK OR STARTLE' ***")
    R.p("     STORED energy is a STARTLE hazard here, not a shock hazard: %.5f mJ worst case"
        % (0.5 * C_WORST * VNOM * VNOM * 1e3))
    R.p("     against a %.0f mJ threshold, %.0fx below, and %.2f uC against %.0f uC."
        % (HAZ_ENERGY_J * 1e3, HAZ_ENERGY_J / (0.5 * C_WORST * VNOM * VNOM),
           C_WORST * VNOM * 1e6, HAZ_CHARGE_C * 1e6))
    R.p("     THE SUSTAINED SOURCE IS THE SHOCK HAZARD: [ISEG] limits Iout to ~1.5*Inom =")
    R.p("     %.2f mA, available continuously at up to %.0f V, and in mode 2 from BOTH outputs"
        % (IOUT_LIMIT_A * 1e3, VNOM))
    R.p("     at once. %.2f mA DC through a body is above the let-go threshold for a hand-to-"
        % (IOUT_LIMIT_A * 1e3))
    R.p("     hand path. The current limit reduces the CONSEQUENCE of contact; it does not")
    R.p("     make contact acceptable, and it is not an alternative to enclosure.")
    R.p()
    R.p("     DESIGN LIMIT that falls out of this: keep total output capacitance below %.0f nF"
        % (c_haz_q * 1e9))
    R.p("     per output. Concretely, fit NO bulk HV filter capacitor: [ISEG] already delivers")
    R.p("     <%.0f mVpp ripple above %.0f V, and a filter cap would buy a little ripple and"
        % (RIPPLE_MAX_VPP * 1e3, RIPPLE_VALID_FLOOR_V))
    R.p("     sell the stored-energy classification.")
    R.finding("At %.0f V this instrument is a SUSTAINED-SOURCE shock hazard and a STORED-ENERGY "
              "startle hazard. Worst credible stored energy is %.3f mJ against the %.0f mJ "
              "threshold (%.0fx below) and %.2f uC against %.0f uC; the sustained %.2f mA at "
              "up to %.0f V -- from BOTH outputs simultaneously in mode 2 -- is the thing that "
              "hurts. Design limit: total output capacitance < %.0f nF per output, i.e. no "
              "bulk HV filter capacitor."
              % (VNOM, 0.5 * C_WORST * VNOM * VNOM * 1e3, HAZ_ENERGY_J * 1e3,
                 HAZ_ENERGY_J / (0.5 * C_WORST * VNOM * VNOM), C_WORST * VNOM * 1e6,
                 HAZ_CHARGE_C * 1e6, IOUT_LIMIT_A * 1e3, VNOM, c_haz_q * 1e9))

    R.h2("3.7  A MODE CHANGE is a new transition and needs its own bleed dwell")
    R.p("     G0-A4 consequence 4. Moving the mode routing element while either output is live")
    R.p("     hot-switches a %.0f V contact and can weld it. The transition must be:" % VNOM)
    R.p("       1. command both set-points to zero")
    R.p("       2. disable both modules (+VIN removal primary, /ON secondary)")
    R.p("       3. DWELL for the bleed, then VERIFY both outputs below %.0f V on the"
        % TOUCH_SAFE_V)
    R.p("          INDEPENDENT monitors -- verify, do not merely wait")
    R.p("       4. move the mode element COLD")
    R.p("       5. read the mode element's PHYSICAL position back before re-enabling anything")
    R.p()
    dwell = 3 * discharge_time_s(r_bleed, C_WORST, VNOM, TOUCH_SAFE_V)
    R.p("     Dwell budget: 3 x the worst-case bleed time = 3 x %.4f s = %.3f s. Round up to"
        % (discharge_time_s(r_bleed, C_WORST, VNOM, TOUCH_SAFE_V), dwell))
    dwell_rounded = math.ceil(dwell * 2.0) / 2.0
    R.p("     %.1f s in the state machine and TRIP -- do not fall through -- on timeout."
        % dwell_rounded)
    R.p("     Per DECISIONS ARCH-24 the DISCHARGE->CHANGEOVER edge is the one transition that")
    R.p("     must never fall through on timeout, because 'off' is not where a timeout leaves")
    R.p("     you -- a stuck-live node plus a moving contact is. MODE CHANGE inherits that.")
    R.check(dwell < DISCHARGE_TARGET_S,
            "a 3x-bleed-time mode-change dwell is shorter than the touch-safe target, i.e. "
            "the dead-band is bounded by the relay, not by the bleed",
            "%.3f s dwell vs %.0f s target" % (dwell, DISCHARGE_TARGET_S))

    R.blind("the module's real output capacitance and internal bleeder (both unpublished, both "
            "MEASURABLE NOW); the load's actual capacitance; board surface leakage, which at "
            "%.0f V across a contaminated %.1f mm gap can rival the bleed itself; and any of "
            "this under fault, since the model assumes the bleed is intact."
            % (VNOM, 7.5))
    return r_bleed


# =====================================================================================
# SECTION 4 -- INDEPENDENT HV MONITOR DIVIDER
# =====================================================================================

ADC = {"name": "ADS1115-class (16-bit delta-sigma, I2C)", "fs_v": 2.048, "bits": 16,
       "inl_lsb": 1.0, "gain_drift_ppm_k": 5.0}
VREF_OFFSET_V = 2.500
VREF_OFFSET_DRIFT_PPM_K = 10.0
DELTA_T_K = 20.0                 # [ASSUMED] 0..40 C band about a 20 C calibration point
RTH_2512_K_W = 60.0              # [ASSUMED] element thermal resistance on 1 oz copper
DIVIDER_FRACTION_OF_INOM = 0.01  # *** THE BINDING CONSTRAINT: 1.00 % of Inom = 5.0 uA ***
# N_TOP_ELEMENTS and DIVIDER_PART live with RES_OPTIONS, above -- one definition each,
# shared by the error budget here and the string geometry in section 1.6.
VCR_PPM_PER_V = 1.0              # [ASSUMED] low-VCR HV divider element
TCR_MATCH_PPM_K = 10.0           # [ASSUMED] top-leg to bottom-leg tracking
R_LEAK_CASES = [("clean, conformally coated", 1e12),
                ("bench-clean bare FR-4", 1e10),
                ("contaminated / humid", 1e9)]
GUARD_IMPROVEMENT = 100.0        # [ASSUMED] a driven guard ring at tap potential


def design_divider(fs_v, inom_a, n_top, vcr_ppm_v, tcr_match_ppm_k):
    """Bipolar-capable passive divider with a reference-injected offset, and its errors.

        HV_OUT --[Rt]--+--[Rb]-- GND
                       +--[Ro]-- VREF_OFFSET
                       +--> unity buffer --> ADC

        G      = 1/Rt + 1/Rb + 1/Ro
        V_node = ( V_hv/Rt + VREF/Ro ) / G                 (superposition)

    Design targets: V_node(-FS)=0, V_node(0)=ADC_FS/2, V_node(+FS)=ADC_FS, so
        atten = ADC_FS/(2*FS)
    Loading budget fixes Rt:  I_div(+FS) = FS/Rt = DIVIDER_FRACTION_OF_INOM * Inom.
    """
    adc_fs = ADC["fs_v"]
    atten = adc_fs / (2.0 * fs_v)
    rt = fs_v / (DIVIDER_FRACTION_OF_INOM * inom_a)
    rp = rt * atten / (1.0 - atten)                 # Rb || Ro
    r_par_all = 1.0 / (1.0 / rt + 1.0 / rp)
    ro = VREF_OFFSET_V * r_par_all / (adc_fs / 2.0)
    inv_rb = 1.0 / rp - 1.0 / ro
    rb = 1.0 / inv_rb if inv_rb > 0 else float("inf")

    i_div = fs_v / rt
    r_element = rt / n_top
    p_element = i_div * i_div * r_element
    dt_self = p_element * RTH_2512_K_W
    v_element = fs_v / n_top

    e_vcr = fs_v * (vcr_ppm_v * 1e-6) * v_element          # note the 1/N through v_element
    e_tcr = fs_v * (tcr_match_ppm_k * 1e-6) * DELTA_T_K
    e_self = fs_v * (tcr_match_ppm_k * 1e-6) * dt_self
    lsb_v = 2.0 * adc_fs / (2 ** ADC["bits"])
    e_inl = ADC["inl_lsb"] * lsb_v / atten
    e_gain = fs_v * ADC["gain_drift_ppm_k"] * 1e-6 * DELTA_T_K
    eps = VREF_OFFSET_V * VREF_OFFSET_DRIFT_PPM_K * 1e-6 * DELTA_T_K
    e_vref = eps * (r_par_all / ro) / atten

    terms = [("VCR (k*V^2/N)", e_vcr), ("TCR mismatch", e_tcr), ("self-heating", e_self),
             ("ADC INL", e_inl), ("ADC gain drift", e_gain), ("offset ref drift", e_vref)]
    rss = math.sqrt(sum(v * v for _, v in terms))
    return {"atten": atten, "rt": rt, "rb": rb, "ro": ro, "rp": rp, "r_par_all": r_par_all,
            "i_div": i_div, "r_element": r_element, "p_element": p_element,
            "dt_self": dt_self, "v_element": v_element, "lsb_hv": lsb_v / atten,
            "lsb_v": lsb_v, "terms": terms, "rss": rss, "n_top": n_top}


def section4(strings):
    R.h1("SECTION 4 -- INDEPENDENT HV MONITOR DIVIDER (one PER OUTPUT -- G0-A4 doubles it)")
    R.p("Brief invariant (c): output voltage monitored INDEPENDENTLY of the module readback.")
    R.p("Target to beat: [ISEG] VMON accuracy = %.0f %% * Vnom = %.1f V."
        % (100 * VMON_ACCURACY, VMON_ACCURACY * VNOM))
    R.p("ADC assumed: %s, FS +/-%.3f V, %d bit." % (ADC["name"], ADC["fs_v"], ADC["bits"]))
    assume("Monitor ADC is an ADS1115-class 16-bit device at +/-%.3f V FS." % ADC["fs_v"])
    assume("Temperature excursion about the calibration point: +/-%.0f K." % DELTA_T_K)
    assume("Divider element VCR %.0f ppm/V and top/bottom TCR tracking %.0f ppm/K."
           % (VCR_PPM_PER_V, TCR_MATCH_PPM_K))

    R.h2("4.1  The binding constraint, stated first because everything follows from it")
    d = design_divider(VNOM, INOM, N_TOP_ELEMENTS, VCR_PPM_PER_V, TCR_MATCH_PPM_K)
    R.p("     Inom is %.1f uA. A divider drawing %.1f uA is EXACTLY %.2f %% of it."
        % (INOM * 1e6, d["i_div"] * 1e6, 100 * d["i_div"] / INOM))
    R.p("     At the 1 kV / 0.5 mA class the monitor's own load is a first-order claim on the")
    R.p("     output current budget, not a rounding error. That is what makes this class the")
    R.p("     deliberate worst case, and it is why the loading budget -- not accuracy, not")
    R.p("     resolution -- sets the divider's top-leg resistance.")
    R.p()
    R.p("         Rt = Vnom / (f * Inom),  f = %.2f" % DIVIDER_FRACTION_OF_INOM)
    R.p("            = %.0f / (%.2f * %.4g) = %.1f Mohm"
        % (VNOM, DIVIDER_FRACTION_OF_INOM, INOM, d["rt"] / 1e6))
    R.check(abs(d["i_div"] * 1e6 - 5.0) < 1e-9,
            "the divider draws exactly 5.0 uA, which is exactly 1.00 % of the 0.5 mA Inom",
            "%.4f uA = %.4f %% of Inom" % (d["i_div"] * 1e6, 100 * d["i_div"] / INOM))
    R.p()
    R.p("     AND IN MODE 2 THERE ARE TWO OF THESE, one per output, each loading ITS OWN")
    R.p("     module by the same %.2f %%. The budgets do not share. Total monitor load across"
        % (100 * d["i_div"] / INOM))
    R.p("     the instrument is %.1f uA, but the number that matters is the per-module %.1f uA."
        % (2 * d["i_div"] * 1e6, d["i_div"] * 1e6))

    R.h2("4.2  Ratio, string composition and per-resistor voltage")
    R.p("     Topology (passive, bipolar-capable, single-supply ADC, no negative rail):")
    R.p("         HV_OUT --[Rt]--+--[Rb]-- GND       V_node = (V_hv/Rt + VREF/Ro) / G")
    R.p("                        +--[Ro]-- VREF      G = 1/Rt + 1/Rb + 1/Ro")
    R.p("                        +--> unity buffer --> ADC")
    R.p("     The offset leg puts V_hv = 0 at mid-scale so -%.0f..+%.0f V maps to 0..%.3f V"
        % (VNOM, VNOM, ADC["fs_v"]))
    R.p("     with no negative rail and NO POLARITY FLAG -- the monitor reports the SIGN, which")
    R.p("     is exactly what a polarity-switching instrument has to verify.")
    R.p()
    R.p("       attenuation A = ADC_FS / (2*Vnom)        = %.6e  (%.1f : 1)"
        % (d["atten"], 1.0 / d["atten"]))
    R.p("       Rt  (top leg, HV)                        = %10.2f Mohm" % (d["rt"] / 1e6))
    R.p("       Rp  = Rb || Ro = Rt*A/(1-A)              = %10.2f kohm" % (d["rp"] / 1e3))
    R.p("       Ro  (offset leg to VREF %.3f V)          = %10.2f kohm"
        % (VREF_OFFSET_V, d["ro"] / 1e3))
    R.p("       Rb  (bottom leg to GND)                  = %10.2f kohm" % (d["rb"] / 1e3))
    R.p("       I_div at +Vnom                           = %10.3f uA" % (d["i_div"] * 1e6))
    R.p()
    ds = strings["divider"]
    R.p("     TOP-LEG STRING COMPOSITION: N = %d series elements" % d["n_top"])
    R.p("       per element  R = %.2f Mohm    V = %.1f V    P = %.3f mW    dT_self = %.4f K"
        % (d["r_element"] / 1e6, d["v_element"], d["p_element"] * 1e3, d["dt_self"]))
    R.p("       part %s, package %s, working-voltage rating %.0f V [%s]"
        % (ds["part"], ds["pkg"], ds["v_rated"], res_option(ds["part"])[2]))
    R.p("       package %s: pad gap %.3f mm vs IPC B2 need %.3f mm at %.1f V per element -> %s"
        % (ds["pkg"], PAD_GAP_MM[ds["pkg"]], ds["gap"], ds["v_el"],
           "OK" if PAD_GAP_MM[ds["pkg"]] >= ds["gap"] else "REJECTED"))
    R.p("       string length = %d x %.3f mm land + %d x %.3f mm inter-element = %.2f mm"
        % (ds["n"], PAD_EXTENT_MM[ds["pkg"]], ds["n"] - 1, ds["gap"], ds["len"]))
    R.check(PAD_GAP_MM[ds["pkg"]] >= ds["gap"],
            "divider element package clears its own pad gap at the per-element voltage",
            "gap %.3f mm vs need %.3f mm at %.1f V"
            % (PAD_GAP_MM[ds["pkg"]], ds["gap"], ds["v_el"]))
    # THE ELEMENT'S OWN WORKING-VOLTAGE RATING. Section 3.5 screens the BLEED string on
    # this and the divider string was not screened at all until session 2's mutation
    # test M8 drove N_TOP_ELEMENTS to 1 -- 1000 V across a single 1206 -- and nothing
    # fired. A rating is a different constraint from a clearance and needs its own check.
    v_allow = ds["v_rated"] * RES_DERATE
    R.p("       working voltage: %.1f V per element vs %.0f V rating x %.2f derate = %.1f V"
        % (ds["v_el"], ds["v_rated"], RES_DERATE, v_allow))
    R.check(ds["v_el"] <= v_allow,
            "divider element stays inside its own derated working-voltage rating",
            "%.1f V per element vs %.1f V allowed (%.0f V rating, %.0fx derate) at N=%d"
            % (ds["v_el"], v_allow, ds["v_rated"], 1.0 / RES_DERATE, ds["n"]))
    R.check(ds["n"] == d["n_top"],
            "the string geometry and the error budget use the SAME element count",
            "geometry N=%d, error budget N=%d" % (ds["n"], d["n_top"]))
    R.p()
    n_yageo = int(math.ceil(d["rt"] / YAGEO_MAX_R_1PCT))
    R.p("     WHY NOT ORDINARY 1 % CHIP RESISTORS: [ARCH12] says the Yageo RC +/-1 % range")
    R.p("     stops at %.1f Mohm. A %.0f Mohm top leg out of ordinary parts would need"
        % (YAGEO_MAX_R_1PCT / 1e6, d["rt"] / 1e6))
    R.p("       ceil(%.0f Mohm / %.1f Mohm) = %d elements in series."
        % (d["rt"] / 1e6, YAGEO_MAX_R_1PCT / 1e6, n_yageo))
    R.p("     That is not a divider, it is a liability: %d chances to go open, %d joints, and"
        % (n_yageo, 2 * n_yageo))
    R.p("     a physical length of %.0f mm. Purpose-made HV divider elements are not a luxury"
        % (n_yageo * PAD_EXTENT_MM["1206"] + (n_yageo - 1) * ds["gap"]))
    R.p("     at this class, they are the only way the part count is sane.")
    R.check(n_yageo >= 91,
            "independently reproduces DECISIONS ARCH-12's '>=91 parts' figure for a top leg "
            "built from ordinary 1 % chip resistors",
            "%.0f Mohm / %.1f Mohm = %d elements"
            % (d["rt"] / 1e6, YAGEO_MAX_R_1PCT / 1e6, n_yageo))

    R.h2("4.3  Error budget, referred to the HV output, at full scale")
    R.p("       VCR         : err = V_hv * k_vcr * (V_hv/N)  <- the 1/N is the whole design.")
    R.p("                     A resistor's voltage coefficient acts on the voltage across THAT")
    R.p("                     element. Splitting the top leg into N puts V_hv/N across each, so")
    R.p("                     the leg's fractional error is k*V_hv/N and the error referred to")
    R.p("                     the output is k*V_hv^2/N -- QUADRATIC in voltage, INVERSE in")
    R.p("                     element count. It is the single most effective lever and it is")
    R.p("                     invisible unless you write it down.")
    R.p("       TCR mismatch: err = V_hv * dTCR * dT")
    R.p("       self-heating: err = V_hv * dTCR * (I^2 * R_element * Rth)")
    R.p("       ADC INL     : err = INL_lsb * LSB / A")
    R.p("       ADC gain    : err = V_hv * gain_drift * dT   (initial gain calibrated out)")
    R.p("       offset ref  : err = dVREF * (Rpar/Ro) / A")
    R.p()
    R.p("     %-22s %14s %14s" % ("term", "error (V)", "% of Vnom"))
    for name, v in d["terms"]:
        R.p("     %-22s %14.4f %13.4f %%" % (name, v, 100 * v / VNOM))
    R.p("     %-22s %14s %14s" % ("", "-" * 12, "-" * 12))
    R.p("     %-22s %14.4f %13.4f %%" % ("RSS", d["rss"], 100 * d["rss"] / VNOM))
    R.p()
    R.p("     ACHIEVED ACCURACY: %.3f V at %.0f V output, calibrated, guarded, clean board."
        % (d["rss"], VNOM))
    R.p("     MODULE VMON:       %.1f V (1 %% * Vnom).   RATIO: %.1fx better."
        % (VMON_ACCURACY * VNOM, VMON_ACCURACY * VNOM / d["rss"]))
    R.check(d["rss"] < VMON_ACCURACY * VNOM,
            "the divider beats the module's own VMON accuracy (clean, guarded)",
            "%.4f V RSS vs %.1f V, %.1fx"
            % (d["rss"], VMON_ACCURACY * VNOM, VMON_ACCURACY * VNOM / d["rss"]))
    R.p()
    R.p("     Monitor resolution: 1 ADC LSB (%.1f uV) referred to HV = %.4f V."
        % (d["lsb_v"] * 1e6, d["lsb_hv"]))
    R.p("     Self-heating is %.4f K and contributes %.5f V. Every instinct that says 'HV"
        % (d["dt_self"], d["terms"][2][1]))
    R.p("     divider, watch the self-heating' is imported from a higher-current problem and")
    R.p("     is wrong here -- at %.1f uA the top leg dissipates %.3f mW per element."
        % (d["i_div"] * 1e6, d["p_element"] * 1e3))

    R.h2("4.4  SURFACE LEAKAGE -- the term that decides whether any of the above is true")
    R.p("     A leakage path R_leak from the HV node to the tap or to GND sits in PARALLEL")
    R.p("     with the %.0f Mohm top leg. Fractional ratio error = Rt / R_leak, so referred to"
        % (d["rt"] / 1e6))
    R.p("     the output:   err = V_hv * Rt / R_leak")
    R.p()
    R.p("     %-30s %14s %14s %16s" % ("board condition", "R_leak", "err (V)", "vs VMON %.0f V"
                                       % (VMON_ACCURACY * VNOM)))
    unguarded_worse = False
    for label, rl in R_LEAK_CASES:
        err = VNOM * d["rt"] / rl
        worse = err > VMON_ACCURACY * VNOM
        if abs(rl - 1e10) < 1e-6:
            unguarded_worse = worse
        R.p("     %-30s %11.3g ohm %13.3f %16s"
            % (label, rl, err, "WORSE" if worse else "ok"))
    R.p()
    R.p("     At bench-clean bare FR-4 the leakage term ALONE is %.1f V -- larger than every"
        % (VNOM * d["rt"] / 1e10))
    R.p("     other term put together and larger than the %.0f V VMON accuracy this divider"
        % (VMON_ACCURACY * VNOM))
    R.p("     exists to improve on. An unguarded %.0f Mohm divider at %.0f V is not an"
        % (d["rt"] / 1e6, VNOM))
    R.p("     independent monitor, it is a humidity sensor.")
    R.p()
    R.p("     MITIGATION, and it is mandatory, not optional:")
    R.p("       1. A GUARD RING at TAP POTENTIAL, driven from the buffer output, surrounding")
    R.p("          the tap node and running alongside the whole top-leg string. Leakage then")
    R.p("          flows HV -> guard (driven, harmless) instead of HV -> tap, and the residual")
    R.p("          guard-to-tap path sits across ~0 V. Assumed improvement %.0fx [ASSUMED]."
        % GUARD_IMPROVEMENT)
    R.p("       2. Conformal coating over the divider region specifically.")
    R.p("       3. The divider gets its OWN netclass clearance, not the generic HV one.")
    R.p()
    R.p("     %-34s %14s %14s" % ("condition", "leak err (V)", "TOTAL RSS (V)"))
    for label, rl in R_LEAK_CASES:
        for guarded in (False, True):
            rl_eff = rl * (GUARD_IMPROVEMENT if guarded else 1.0)
            err = VNOM * d["rt"] / rl_eff
            tot = math.sqrt(d["rss"] ** 2 + err ** 2)
            R.p("     %-34s %14.4f %14.4f%s"
                % (label + (" + guard ring" if guarded else ""), err, tot,
                   "   <-- FAILS to beat VMON" if tot >= VMON_ACCURACY * VNOM else ""))
    R.check(unguarded_worse,
            "an UNGUARDED divider on bench-clean bare FR-4 is WORSE than the module's own "
            "VMON, which is the proof that the guard ring is a requirement and not a polish",
            "leakage term %.1f V alone vs VMON %.1f V"
            % (VNOM * d["rt"] / 1e10, VMON_ACCURACY * VNOM))
    guarded_total = math.sqrt(d["rss"] ** 2 + (VNOM * d["rt"] / (1e10 * GUARD_IMPROVEMENT)) ** 2)
    R.check(guarded_total < VMON_ACCURACY * VNOM,
            "WITH the guard ring the divider beats VMON even on bench-clean bare FR-4",
            "%.4f V total vs %.1f V, %.1fx"
            % (guarded_total, VMON_ACCURACY * VNOM, VMON_ACCURACY * VNOM / guarded_total))
    R.finding("Surface leakage is the dominant, non-obvious error term of the independent "
              "monitor at this class. With Rt = %.0f Mohm forced by the 1.00 %%-of-Inom "
              "loading budget, a 10 Gohm board leakage path injects %.1f V of ratio error -- "
              "on its own larger than the %.1f V VMON accuracy the divider exists to improve "
              "on. A DRIVEN GUARD RING AT TAP POTENTIAL IS THEREFORE A REQUIREMENT OF THE "
              "MONITOR, not a refinement, and it must be in the netclass/DRC rules and in the "
              "generator's invariants."
              % (d["rt"] / 1e6, VNOM * d["rt"] / 1e10, VMON_ACCURACY * VNOM))

    R.h2("4.5  Independence, and the disagreement threshold")
    R.p("     This divider shares NOTHING with the module's VMON path: different node, "
        "different")
    R.p("     reference, different ADC channel, different rail. Firmware must compare the two")
    R.p("     and fault on disagreement -- that comparison IS the value of the independent")
    R.p("     monitor.")
    thr = math.sqrt((VMON_ACCURACY * VNOM) ** 2 + guarded_total ** 2)
    R.p("       legitimate disagreement, quadrature = sqrt(%.1f^2 + %.3f^2) = %.3f V"
        % (VMON_ACCURACY * VNOM, guarded_total, thr))
    R.p("       trip threshold, DECISIONS ARCH-23 = 2 %% * Vnom = %.1f V" % (0.02 * VNOM))
    R.p("       margin over legitimate disagreement = %.2fx" % (0.02 * VNOM / thr))
    R.p("     It catches an open divider element, a stuck relay, a module in current limit, an")
    R.p("     ADC reference collapse and partial HV breakdown -- none of which either monitor")
    R.p("     detects alone.")
    R.check(0.02 * VNOM > thr,
            "the 2 %-of-Vnom disagreement trip sits above legitimate quadrature disagreement",
            "%.1f V trip vs %.3f V legitimate, %.2fx margin"
            % (0.02 * VNOM, thr, 0.02 * VNOM / thr))
    R.p()
    R.p("     MODE 2 ADDS A SECOND COMPARISON AND A THIRD CHECK. With two outputs live there")
    R.p("     are two independent monitors and two VMONs, so firmware must also verify that")
    R.p("     OUT_A reads POSITIVE and OUT_B reads NEGATIVE. A sign disagreement means the")
    R.p("     mode element is not where the mode bit says it is -- which is precisely the")
    R.p("     failure G0-A4 warns about, and the independent monitor is the only thing on the")
    R.p("     board that can see it.")

    R.blind("resistor VCR is a datasheet parameter this probe assumes, not measures; the real "
            "surface resistivity of the finished board (the term that dominates 4.4); ADC "
            "noise in the presence of the module's switching converter; and the calibration "
            "it assumes, which has not been performed.")
    return d


# =====================================================================================
# SECTION 5 -- THE VSET CLAMP  (a PRIMARY SAFETY ELEMENT, treated as one)
# =====================================================================================

SCHOTTKY_VF = 0.30        # [ASSUMED] BAT54-class at ~1 uA, 25 C
SCHOTTKY_LEAK_A = 1e-6    # [ASSUMED] at 25 C
OPAMP_SAT_MV = 20.0       # [ASSUMED] RRIO output saturation at ~250 uA load
OPAMP_VOS_UV = 200.0      # [ASSUMED]
EXT_REF_TOL = 0.001       # 0.1 % precision reference
R_PD_OHM = 1000.0         # VSET fail-safe pull-down
ATTEN_C = 0.98            # candidate C fixed attenuator
ATTEN_C_TOL = 0.002
COMPARATOR_TRIP_FRAC = 1.05   # trip at 105 % of VMON full scale


def vset_series_r_error(rs_ohm, vdrive):
    """Set-point error from ANY series resistance in the VSET path.

        V_set = (Vdrive*10k + Vref*Rs) / (10k + Rs)
        error = V_set - Vdrive = (Vref - Vdrive) * Rs / (10k + Rs)      worst at Vdrive = 0
    """
    vset = (vdrive * VSET_PULLUP_OHM + VREF * rs_ohm) / (VSET_PULLUP_OHM + rs_ohm)
    return vset - vdrive, vset


def pct(vset_v):
    """Commanded output as a fraction of Vnom, worst case (module Vref at its LOW tolerance)."""
    return vset_v / (VREF * (1 - VREF_TOL))


def section5():
    R.h1("SECTION 5 -- THE VSET CLAMP  (PRIMARY SAFETY ELEMENT)")
    R.p("[ISEG] Table 1, verbatim: 'Attention! Output voltage is internally not limited!'")
    R.p("                          'At Vset > 2.5 V -> Vout > Vnom is possible!'")
    R.p("                          'Do not use Vset > 2.5 V !'")
    R.p("[ISEG] implies an internal %.0f kohm pull-up from VSET to Vref (the Rset formula has"
        % (VSET_PULLUP_OHM / 1e3))
    R.p("no other consistent reading -- STATUS.md 1.1, survived 3 skeptics) and requires any")
    R.p("driver to have Ri << %.0f kohm." % (VSET_PULLUP_OHM / 1e3))
    R.p()
    R.p("G0-A3 put HV set-point and enable commands on a NETWORK WITH WRITE AUTHORITY. The")
    R.p("human made that choice with the risk stated. The consequence is that the hardware")
    R.p("interlock, THIS CLAMP, and the soft limits carry the entire safety case. This section")
    R.p("is therefore written as a safety analysis, not as a component selection.")

    R.h2("5.1  The un-clamped hazard, quantified on the frozen part")
    # ARCH-18 fits TWO pull-downs in parallel. Session 2 found the probe quoting the
    # SINGLE-element figure (9.2 %) beside a recommendation to fit the pair, and computing
    # the buffer sink current from the pair -- two different R_pd in one section. Both
    # numbers are now derived from one place and both are printed, because they answer
    # different questions: what is fitted, and what one open element does to it.
    r_pd_both = R_PD_OHM / 2.0
    v_pd_both = VREF * r_pd_both / (VSET_PULLUP_OHM + r_pd_both)
    v_pd_one = VREF * R_PD_OHM / (VSET_PULLUP_OHM + R_PD_OHM)
    R.p("     %-34s %12s %12s" % ("condition", "Vset (V)", "Vout"))
    R.p("     %-34s %12.4f %9.0f V  (%.0f %% of Vnom)"
        % ("3.3 V logic rail on VSET", LOGIC_RAIL_V, pct(LOGIC_RAIL_V) * VNOM,
           100 * pct(LOGIC_RAIL_V)))
    R.p("     %-34s %12.4f %9.0f V  (%.0f %% of Vnom)"
        % ("5 V rail on VSET", LOGIC_RAIL_5V, pct(LOGIC_RAIL_5V) * VNOM,
           100 * pct(LOGIC_RAIL_5V)))
    R.p("     %-34s %12.4f %9.0f V  (%.0f %% of Vnom)"
        % ("VSET open -> internal pull-up", VREF, pct(VREF) * VNOM, 100 * pct(VREF)))
    R.p("     %-34s %12.4f %9.0f V  (%.1f %% of Vnom)"
        % ("VSET open, R_pd BOTH fitted (%.0f ohm)" % r_pd_both,
           v_pd_both, pct(v_pd_both) * VNOM, 100 * pct(v_pd_both)))
    R.p("     %-34s %12.4f %9.0f V  (%.1f %% of Vnom)"
        % ("VSET open, ONE R_pd open (%.0f ohm)" % R_PD_OHM,
           v_pd_one, pct(v_pd_one) * VNOM, 100 * pct(v_pd_one)))
    R.p()
    R.p("     Two inversions of ordinary intuition, both from [ISEG], both load-bearing:")
    R.p("       * an OPEN VSET commands FULL SCALE, because of the internal pull-up to Vref;")
    R.p("       * /ON is 'LOW or n.c. -> HV ON', so a FLOATING /ON turns HV ON.")
    R.p("     The module's un-driven default state is ENERGISED AT OVER-RANGE. 'Unpowered =")
    R.p("     safe' is false for this part.")
    R.check(pct(v_pd_both) < 0.10,
            "the fitted pull-down PAIR holds the driver-dead output below 10 % of Vnom",
            "%.1f %% = %.0f V instead of %.0f V, at R_pd(pair) = %.0f ohm"
            % (100 * pct(v_pd_both), pct(v_pd_both) * VNOM, VNOM, r_pd_both))
    R.p()
    R.p("     R_pd must be DUPLICATED (two %.0f ohm in parallel = %.0f ohm) per DECISIONS"
        % (R_PD_OHM, r_pd_both))
    R.p("     ARCH-18. State BOTH numbers, because they are different arguments:")
    R.p("       * the PAIR is what is fitted, so %.1f %% is the driver-dead output in service;"
        % (100 * pct(v_pd_both)))
    R.p("       * ONE element going open degrades that to %.1f %% -- still safe, and that is"
        % (100 * pct(v_pd_one)))
    R.p("         the POINT of the duplication. A SINGLE pull-down going open would restore")
    R.p("         the documented unsafe default (%.0f %% of Vnom) silently, and an open"
        % (100 * pct(VREF)))
    R.p("         pull-down is not observable from anywhere else on the board.")
    R.check(pct(v_pd_one) < 0.10,
            "a SINGLE-OPEN pull-down still holds the driver-dead output below 10 % of Vnom, "
            "which is what makes the duplication a fail-safe rather than a fail-over",
            "%.1f %% (one open) vs %.1f %% (both fitted) vs %.0f %% (none)"
            % (100 * pct(v_pd_one), 100 * pct(v_pd_both), 100 * pct(VREF)))

    R.h2("5.2  Residual set-point error injected by each candidate clamp")
    R.p("     Any series resistance in the VSET path divides against the internal %.0f kohm:"
        % (VSET_PULLUP_OHM / 1e3))
    R.p("         error = (Vref - Vdrive) * Rs / (%.0f k + Rs),   worst at Vdrive = 0"
        % (VSET_PULLUP_OHM / 1e3))
    R.p()
    R.p("     %-10s %16s %14s %16s" % ("Rs (ohm)", "err @Vset=0 (mV)", "err (% FS)",
                                       "-> Vout error"))
    for rs in (0.0, 10.0, 47.0, 100.0, 470.0, 1000.0):
        err, _ = vset_series_r_error(rs, 0.0)
        R.p("     %-10.0f %16.3f %13.4f %% %13.2f V"
            % (rs, err * 1e3, 100 * err / VSET_FS, VNOM * err / VSET_FS))
    err10, _ = vset_series_r_error(10.0, 0.0)
    err1k, _ = vset_series_r_error(1000.0, 0.0)
    R.p()
    R.p("     A 1 kohm series resistor -- an utterly ordinary value, and exactly what an RC")
    R.p("     filter on VSET would put there -- produces %.0f V of output when ZERO was"
        % (VNOM * err1k / VSET_FS))
    R.p("     commanded. That is [ISEG]'s 'Ri << 10 kohm' warning made quantitative. It is why")
    R.p("     DECISIONS ARCH-04 forbids ANY resistor between the buffer and the VSET pin: the")
    R.p("     budget is <= 10 ohm, which in practice means 'a track, not a component'.")
    R.check(VNOM * err1k / VSET_FS > 50.0,
            "a 1 kohm series element in the VSET path is disqualifying on its own",
            "%.0f V of uncommanded output at zero command" % (VNOM * err1k / VSET_FS))
    R.check(100 * err10 / VSET_FS < 0.11,
            "Rs <= 10 ohm keeps the zero-offset error under 0.11 % of full scale",
            "%.3f mV = %.4f %% FS = %.2f V at the output"
            % (err10 * 1e3, 100 * err10 / VSET_FS, VNOM * err10 / VSET_FS))
    R.p()
    R.p("     RESIDUAL ERROR PER CANDIDATE, referred to the output at %.0f V:" % VNOM)
    R.p("     %-46s %12s %12s %12s" % ("candidate", "err (V)", "% of Vnom", "vs +/-1 %"))
    e_track = VNOM * err10 / VSET_FS
    e_vos = VNOM * (OPAMP_VOS_UV * 1e-6) / VSET_FS
    e_ref = VNOM * EXT_REF_TOL
    e_att = VNOM * ATTEN_C_TOL
    cand_err = [
        ("N  no clamp (DAC straight off the 3.3 V rail)",
         VNOM * 0.02, "rail tolerance +/-2 % is the reference"),
        ("A  series R (10 ohm) + Schottky to precision ref",
         math.sqrt(e_track ** 2 + e_ref ** 2 + (VNOM * SCHOTTKY_LEAK_A * 10.0 / VSET_FS) ** 2),
         "track + ref + diode leakage"),
        ("B  RRIO buffer powered FROM the precision ref",
         math.sqrt(e_track ** 2 + e_vos ** 2 + e_ref ** 2), "track + Vos + ref"),
        ("C  fixed 0.98 attenuator before the buffer",
         math.sqrt(e_track ** 2 + e_vos ** 2 + e_ref ** 2 + e_att ** 2),
         "B + attenuator ratio drift, and 2 % of range lost"),
    ]
    for name, e, note in cand_err:
        R.p("     %-46s %12.3f %11.4f %% %11.2fx" % (name, e, 100 * e / VNOM,
                                                     ADJ_ACCURACY * VNOM / e))
    R.p()
    R.p("     Read the last column as 'how much of the module's own +/-1 %% (%.0f V) adjustment"
        % (ADJ_ACCURACY * VNOM))
    R.p("     accuracy the clamp costs'. Candidate B costs about a seventh of it. That is the")
    R.p("     price of making a %.0f V command structurally impossible, and it is cheap."
        % (pct(LOGIC_RAIL_V) * VNOM))
    b_err = cand_err[2][1]
    R.check(b_err < ADJ_ACCURACY * VNOM / 3.0,
            "candidate B's residual set-point error is well inside the module's own accuracy",
            "%.3f V vs %.1f V, %.1fx headroom"
            % (b_err, ADJ_ACCURACY * VNOM, ADJ_ACCURACY * VNOM / b_err))

    R.h2("5.3  How each candidate CLAMPS, in the no-fault case")
    v_ext_max = VREF * (1 + EXT_REF_TOL)
    v_ext_min = VREF * (1 - EXT_REF_TOL)
    vref_mod_min = VREF * (1 - VREF_TOL)
    vref_mod_max = VREF * (1 + VREF_TOL)
    ceil_A = v_ext_max + SCHOTTKY_VF
    ceil_B = v_ext_max - OPAMP_SAT_MV * 1e-3
    ceil_C = v_ext_max * ATTEN_C * (1 + ATTEN_C_TOL)
    R.p("     Module Vref is %.3f V +/-%.0f %%, i.e. %.4f .. %.4f V. The clamp ceiling must be"
        % (VREF, 100 * VREF_TOL, vref_mod_min, vref_mod_max))
    R.p("     compared against the LOW end, %.4f V, because that is where a given Vset"
        % vref_mod_min)
    R.p("     commands the largest fraction of Vnom.")
    R.p()
    R.p("     %-44s %12s %14s %12s" % ("candidate", "ceiling (V)", "max Vout", "range lost"))
    for name, ceil_v in (("A  Schottky to ref: Vref_ext + Vf", ceil_A),
                         ("B  buffer rail: Vref_ext - Vsat", ceil_B),
                         ("C  attenuator: Vref_ext * a", ceil_C)):
        lost = max(0.0, 1.0 - (v_ext_min * (ATTEN_C * (1 - ATTEN_C_TOL) if "C " in name else 1.0)
                               - (OPAMP_SAT_MV * 1e-3 if "B " in name or "C " in name else 0.0))
                   / vref_mod_max)
        R.p("     %-44s %12.4f %10.0f V (%.1f %%) %10.2f %%"
            % (name, ceil_v, pct(ceil_v) * VNOM, 100 * pct(ceil_v), 100 * lost))
    R.p()
    R.p("     A leaves %.1f %% of over-voltage on the table even when it works, because a"
        % (100 * (pct(ceil_A) - 1)))
    R.p("     Schottky clamps at Vref + Vf, not at Vref.")
    R.p("     B is structural: a rail-to-rail output physically cannot exceed its own positive")
    R.p("     rail, and that rail IS the precision reference that also feeds the DAC. One part,")
    R.p("     two jobs, and they cannot drift apart because they are the same node. It adds")
    R.p("     ZERO components to the signal path, so it does not violate the <=10 ohm rule.")
    R.p("     C gives a genuinely ONE-SIDED bound (%.2f %% -- guaranteed under Vnom) but pays"
        % (100 * (pct(ceil_C) - 1)))
    R.p("     %.0f %% of range for it, unconditionally, and adds a ratio-drift error term."
        % (100 * (1 - ATTEN_C)))
    R.check(pct(ceil_B) < 1.01,
            "candidate B's no-fault ceiling is inside the module's own +/-1 % accuracy",
            "%.2f %% of Vnom = %.0f V" % (100 * pct(ceil_B), pct(ceil_B) * VNOM))
    R.check(pct(ceil_A) > pct(ceil_B),
            "the Schottky candidate clamps LESS tightly than the buffer-rail candidate",
            "%.1f %% vs %.2f %% of Vnom" % (100 * pct(ceil_A), 100 * pct(ceil_B)))
    R.p("     NOTE, said plainly rather than claimed away: NO candidate makes over-voltage")
    R.p("     mathematically impossible. Two references with independent tolerances cannot be")
    R.p("     ordered with certainty. B converts a %.0f %% hazard into a %.2f %% irrelevance."
        % (100 * pct(LOGIC_RAIL_V), 100 * (pct(ceil_B) - 1)))

    R.h2("5.4  *** SINGLE-FAULT SURVIVAL -- the analysis this section exists for ***")
    R.p("     Each row is ONE fault, from an otherwise-correct board. The number is the")
    R.p("     resulting output as a percentage of Vnom. 'ok' means <= 110 % of Vnom.")
    R.p()
    # F3/F4 are "VSET floating with the board otherwise correct", i.e. BOTH pull-downs
    # fitted. F6 is the one row where a pull element is the fault, and it is shown at its
    # worst consequence. Same derivation as 5.1 -- one definition, two consumers.
    r_pd_both = R_PD_OHM / 2.0
    v_open_pd = VREF * r_pd_both / (VSET_PULLUP_OHM + r_pd_both)
    v_open_pd_one = VREF * R_PD_OHM / (VSET_PULLUP_OHM + R_PD_OHM)
    faults = [
        ("F1 firmware/network commands full DAC code",
         pct(LOGIC_RAIL_V), pct(ceil_A), pct(ceil_B), pct(ceil_C),
         "the G0-A3 network-write case"),
        ("F2 VSET net shorted to the 3.3 V rail",
         pct(LOGIC_RAIL_V), pct(LOGIC_RAIL_V), pct(LOGIC_RAIL_V), pct(LOGIC_RAIL_V),
         "a hard short to a rail is downstream of every clamp"),
        ("F3 VSET net open (broken track, lifted pad)",
         pct(VREF), pct(v_open_pd), pct(v_open_pd), pct(v_open_pd),
         "internal pull-up; R_pd saves it"),
        ("F4 buffer dead / output high-Z",
         pct(VREF), pct(v_open_pd), pct(v_open_pd), pct(v_open_pd),
         "same node state as F3"),
        ("F5 precision reference shorted to the 5 V rail",
         pct(LOGIC_RAIL_5V), pct(LOGIC_RAIL_5V + SCHOTTKY_VF),
         pct(LOGIC_RAIL_5V - OPAMP_SAT_MV * 1e-3), pct(LOGIC_RAIL_5V * ATTEN_C),
         "the clamp's own reference becomes the hazard"),
        # F6 CORRECTED in session 2. It previously showed 101 % -- the UN-DUPLICATED
        # number -- while 5.6 recommended fitting two. With the pair fitted, ONE element
        # opening is a single fault and leaves the other in circuit, so the output is
        # v_open_pd_one, not Vref. 101 % needs BOTH open, which is two faults.
        ("F6 ONE R_pd open (pair fitted, ARCH-18)",
         pct(v_open_pd_one), pct(v_open_pd_one), pct(v_open_pd_one), pct(v_open_pd_one),
         "LATENT, and covered: the surviving element still holds it down"),
        ("F7 R_pd NOT duplicated, then it opens",
         pct(VREF), pct(VREF), pct(VREF), pct(VREF),
         "NOT a fault -- a DESIGN CHOICE that turns F6 into a 101 % event"),
    ]
    R.p("     %-44s %9s %9s %9s %9s" % ("single fault", "none", "A", "B", "C"))
    surviving = {"none": [], "A": [], "B": [], "C": []}
    for label, fn, fa, fb, fc in [(f[0], f[1], f[2], f[3], f[4]) for f in faults]:
        R.p("     %-44s %8.0f%% %8.0f%% %8.0f%% %8.0f%%"
            % (label, 100 * fn, 100 * fa, 100 * fb, 100 * fc))
        for key, v in (("none", fn), ("A", fa), ("B", fb), ("C", fc)):
            if v > 1.10:
                surviving[key].append((label, v))
    R.p()
    for f in faults:
        R.p("       %-44s %s" % (f[0][:44], f[5]))
    R.p()
    R.p("     FAULTS THAT SURVIVE EACH CLAMP (output above 110 % of Vnom):")
    for key in ("none", "A", "B", "C"):
        R.p("       %-6s %d of %d :  %s" % (key, len(surviving[key]), len(faults),
                                            ", ".join(s[0][:2] for s in surviving[key])
                                            or "(none)"))
    R.p()
    R.p("     *** THE RESULT, STATED WITHOUT SOFTENING ***")
    R.p("     The best clamp still lets %d of %d single faults through, and one of them (F5)"
        % (len(surviving["B"]), len(faults)))
    R.p("     reaches %.0f %% of Vnom = %.0f V, WORSE than the un-clamped 3.3 V case, because"
        % (100 * pct(LOGIC_RAIL_5V - OPAMP_SAT_MV * 1e-3),
           pct(LOGIC_RAIL_5V - OPAMP_SAT_MV * 1e-3) * VNOM))
    R.p("     the fault is IN the clamp's own reference. A clamp that shares a node with the")
    R.p("     thing it protects against fails in the direction of the hazard.")
    R.check(len(surviving["B"]) > 0,
            "no VSET clamp survives every single fault -- proving the clamp alone is NOT the "
            "safety case and an independent backstop is mandatory",
            "candidate B (the best) still passes %d of %d faults: %s"
            % (len(surviving["B"]), len(faults),
               ", ".join(s[0][:2] for s in surviving["B"])))
    R.check(len(surviving["B"]) < len(surviving["none"]),
            "the clamp is nevertheless worth fitting: it strictly reduces the surviving set",
            "%d surviving with clamp B vs %d with no clamp"
            % (len(surviving["B"]), len(surviving["none"])))

    R.h2("5.5  The backstop that covers what the clamp cannot")
    trip_v = COMPARATOR_TRIP_FRAC * VMON_FS
    R.p("     An INDEPENDENT hardware comparator on VMON -- not on the DAC code, not in")
    R.p("     firmware -- that drives /ON HIGH (= HV OFF) when VMON exceeds its threshold.")
    R.p("       trip at %.0f %% of VMON full scale = %.3f V  =>  %.0f V at the output"
        % (100 * COMPARATOR_TRIP_FRAC, trip_v, COMPARATOR_TRIP_FRAC * VNOM))
    R.p("       margin over the module's own VMON accuracy (%.1f V) = %.1f V"
        % (VMON_ACCURACY * VNOM, COMPARATOR_TRIP_FRAC * VNOM - VNOM - VMON_ACCURACY * VNOM))
    R.p()
    R.p("     It catches every surviving fault above, because all of them are above %.0f %%:"
        % (100 * COMPARATOR_TRIP_FRAC))
    for label, v in surviving["B"]:
        R.p("       %-44s %6.0f %% -> tripped" % (label[:44], 100 * v))
    R.check(all(v > COMPARATOR_TRIP_FRAC for _, v in surviving["B"]),
            "the %.0f %% VMON comparator trips on every fault that survives clamp B"
            % (100 * COMPARATOR_TRIP_FRAC),
            "smallest surviving over-voltage %.0f %% vs %.0f %% trip"
            % (100 * min(v for _, v in surviving["B"]), 100 * COMPARATOR_TRIP_FRAC))
    R.p()
    R.p("     FOUR CONDITIONS ON THE COMPARATOR, or it is decoration:")
    R.p("       1. Its threshold reference must NOT be the same precision reference that")
    R.p("          feeds the DAC and the buffer rail. F5 takes that reference out; a")
    R.p("          comparator referenced to it fails in the same event it exists to catch.")
    R.p("       2. Its output must drive /ON HIGH in HARDWARE, with no firmware in the path.")
    R.p("       3. It must be powered from a rail that survives the faults it covers, and")
    R.p("          losing that rail must ALSO turn HV off (open-drain, pull-up to the module's")
    R.p("          own +VIN per DECISIONS ARCH-17).")
    R.p("       4. It must be TESTABLE without HV: inject %.3f V at the VMON sense node with"
        % trip_v)
    R.p("          the MCU held in reset and confirm /ON goes HIGH. That is Stage 2.5 of the")
    R.p("          bench procedure and it is the only cheap moment to prove it.")
    R.p()
    R.p("     AND THE PRIMARY DISABLE IS STILL +VIN REMOVAL, NOT /ON (DECISIONS ARCH-19). A")
    R.p("     module with no input power cannot make HV at all, so the 'LOW or n.c. -> HV ON'")
    R.p("     trap stops being the last line of defence.")

    R.h2("5.6  RECOMMENDATION")
    R.p("     Candidate B + duplicated fail-safe pull-down + independent VMON comparator:")
    R.p("       1. ONE precision reference (0.1 %%, low drift) at %.3f V. It is the DAC" % VREF)
    R.p("          reference AND the VSET buffer's positive rail. Same node, cannot drift apart.")
    R.p("       2. DAC -> RRIO buffer (unity gain) -> VSET, series resistance <= 10 ohm, i.e.")
    R.p("          a track and not a component. NO RC filter on VSET, ever.")
    R.p("       3. TWO %.0f ohm pull-downs in parallel (= %.0f ohm) at the VSET pin:"
        % (R_PD_OHM, R_PD_OHM / 2.0))
    R.p("          driver-dead output becomes %.1f %% of Vnom instead of %.0f %%, and ONE"
        % (100 * pct(v_open_pd), 100 * pct(VREF)))
    R.p("          going open degrades that only to %.1f %% -- it does NOT restore the"
        % (100 * pct(v_open_pd_one)))
    R.p("          unsafe default. Both numbers are stated in 5.1; do not quote one alone.")
    R.p("       4. Independent VMON comparator per 5.5, on its own reference.")
    R.p("       5. /ON open-drain with a pull-up to the module's OWN +VIN, within 5 mm of pin 4.")
    R.p("       6. +VIN switching as the primary disable.")
    R.p("     The buffer must SINK the pull-up current at Vset = 0:")
    sink = VREF / VSET_PULLUP_OHM + 2 * VREF / R_PD_OHM
    R.p("       sink = Vref/%.0fk + 2*Vref/%.0f = %.0f uA + %.0f uA = %.2f mA"
        % (VSET_PULLUP_OHM / 1e3, R_PD_OHM, VREF / VSET_PULLUP_OHM * 1e6,
           2 * VREF / R_PD_OHM * 1e6, sink * 1e3))
    R.p("     Trivial for any RRIO part, but it must be one that SINKS to its negative rail --")
    R.p("     check the datasheet's output-sink curve, not the 'rail-to-rail' marketing line.")
    R.finding("The VSET clamp is a necessary but NOT SUFFICIENT safety element. The best "
              "candidate (RRIO buffer powered from the precision reference) still passes %d of "
              "%d modelled single faults, including a reference-to-5 V short that reaches "
              "%.0f %% of Vnom = %.0f V -- worse than the un-clamped 3.3 V case, because the "
              "fault is in the clamp's own reference. The independent VMON comparator, on its "
              "OWN reference and driving /ON in hardware, is what closes the set, and +VIN "
              "removal is the primary disable. With a network carrying write authority "
              "(G0-A3) this chain IS the safety case."
              % (len(surviving["B"]), len(faults),
                 100 * pct(LOGIC_RAIL_5V - OPAMP_SAT_MV * 1e-3),
                 pct(LOGIC_RAIL_5V - OPAMP_SAT_MV * 1e-3) * VNOM))

    R.blind("op-amp behaviour during supply ramp (an RRIO part can transiently drive above its "
            "settled rail, or go high-Z as the reference starts -- the pull-down covers high-Z, "
            "nothing here covers a transient overshoot); reference start-up overshoot; "
            "multiple simultaneous faults; and any of this in silicon rather than on paper.")
    return surviving


# =====================================================================================
# SECTION 6 -- POWER BUDGET ON THE 5 V RAIL
# =====================================================================================

ESP32_PEAK_MA = 500.0      # [ASSUMED] WiFi TX peak
ESP32_TX_AVG_MA = 240.0    # [ASSUMED] 802.11b sustained TX average
ESP32_IDLE_MA = 80.0       # [ASSUMED]
ANALOG_MA = 60.0           # [ASSUMED] 2 DACs + ref + op-amps + 2 ADCs + comparators + LEDs
RELAY_COILS = 4            # 2 changeover + 1 mode (multi-pole) + 1 dump
RELAY_COIL_MA = 20.0       # [ASSUMED] per coil at 5 V
ESP32_RAIL_V = 3.3
BUCK_EFF = 0.85            # [ASSUMED]
SUPPLY_MARGIN = 2.0        # [ASSUMED]


def section6():
    R.h1("SECTION 6 -- POWER BUDGET ON THE 5 V RAIL")
    R.p("Module input currents are [ISEG] Table 1 MAXIMA, not typicals. Vin is 5 V, not 12 V:")
    R.p("the modules and the logic share one rail and there is no galvanic separation between")
    R.p("the HV converter's switching current and the ADC's ground reference.")
    assume("ESP32 peak %.0f mA / TX-average %.0f mA / idle %.0f mA."
           % (ESP32_PEAK_MA, ESP32_TX_AVG_MA, ESP32_IDLE_MA))
    assume("Analog rail %.0f mA; %d relay coils at %.0f mA; buck efficiency %.0f %%."
           % (ANALOG_MA, RELAY_COILS, RELAY_COIL_MA, 100 * BUCK_EFF))

    R.h2("6.1  Both modules loaded, or one plus margin? -- SETTLED, and the reason CHANGED")
    one = IIN_LOADED_MA + IIN_VOUT0_MA
    both = 2 * IIN_LOADED_MA
    R.p("     one loaded + one at Vout=0  = %.0f + %.0f = %6.1f mA = %.2f W"
        % (IIN_LOADED_MA, IIN_VOUT0_MA, one, one * 1e-3 * VIN_NOM))
    R.p("     both loaded                 = 2 x %.0f    = %6.1f mA = %.2f W"
        % (IIN_LOADED_MA, both, both * 1e-3 * VIN_NOM))
    R.p("     delta                                     = %6.1f mA = %.3f W"
        % (both - one, (both - one) * 1e-3 * VIN_NOM))
    R.p()
    R.p("     Session 1 argued for BOTH on three grounds that were all about faults and")
    R.p("     transients: overlap during changeover, wanting the MCU alive during an interlock")
    R.p("     failure, and the delta being cheap. Those arguments were correct but they were")
    R.p("     arguments about MARGIN.")
    R.p()
    R.p("     *** G0-A4 REPLACES THEM WITH A REQUIREMENT. ***")
    R.p("     In dual-unipolar mode BOTH MODULES ARE AT FULL OUTPUT SIMULTANEOUSLY AS NORMAL")
    R.p("     OPERATION. Sizing for one-plus-margin is not conservative-or-not, it is WRONG:")
    R.p("     it under-sizes the supply for the instrument's own advertised mode. The")
    R.p("     'only one is ever enabled, so size for one plus margin' argument is DEAD and")
    R.p("     must not be revived under the changeover topology either, because the changeover")
    R.p("     topology is only mode 1 of two.")
    R.check(both > one,
            "sizing for both modules loaded is the binding case, not a margin choice",
            "%.0f mA (mode 2 normal operation) vs %.0f mA (mode 1 one-plus-idle), %+.0f mA"
            % (both, one, both - one))

    R.h2("6.2  Rail-by-rail worst case")
    esp_on_5v = ESP32_PEAK_MA * ESP32_RAIL_V / (5.0 * BUCK_EFF)
    relay_ma = RELAY_COILS * RELAY_COIL_MA
    total_ma = both + esp_on_5v + ANALOG_MA + relay_ma
    total_w = total_ma * 1e-3 * 5.0
    R.p("     %-46s %10s %10s" % ("load", "mA @ 5 V", "W"))
    rows = [("2 x module, both loaded, [ISEG] maximum", both),
            ("ESP32 %.0f mA peak on 3.3 V via an %.0f %% buck" % (ESP32_PEAK_MA, 100 * BUCK_EFF),
             esp_on_5v),
            ("analog: refs, DACs x2, buffers, ADCs x2, comparators", ANALOG_MA),
            ("%d relay coils at %.0f mA" % (RELAY_COILS, RELAY_COIL_MA), relay_ma)]
    for label, ma in rows:
        R.p("     %-46s %10.1f %10.3f" % (label, ma, ma * 1e-3 * 5.0))
    R.p("     %-46s %10s %10s" % ("", "-" * 8, "-" * 8))
    R.p("     %-46s %10.1f %10.3f" % ("SINGLE 5 V RAIL TOTAL", total_ma, total_w))
    R.p()
    rec_a = math.ceil(total_ma * SUPPLY_MARGIN / 100.0) * 100.0 / 1000.0
    R.p("     RECOMMENDED SUPPLY: 5 V / %.1f A  (%.1fx margin over %.1f mA)"
        % (rec_a, SUPPLY_MARGIN, total_ma))
    R.p()
    R.p("     Arrangement: one 5 V / %.1f A external brick" % rec_a)
    R.p("       -> module rail taken DIRECTLY from the brick, each module behind its own series")
    R.p("          ferrite and %.0f uF blocking capacitor at +VIN ([ISEG] Table 1 note 2), and"
        % VIN_BLOCK_UF)
    R.p("          behind the +VIN disable switch (ARCH-19, primary disable)")
    R.p("       -> separate buck 5 -> 3.3 V for the ESP32")
    R.p("       -> separate LOW-NOISE LDO from 5 V for the analog / reference rail")
    R.p("     The modules and the ESP32 share one rail. The resonant converter's switching")
    R.p("     current and the WiFi TX burst are both on it. Per-module ferrite + bulk cap is")
    R.p("     not optional decoration at 5 V input.")
    R.check(rec_a * 1000.0 >= total_ma * SUPPLY_MARGIN - 1e-9,
            "the recommended supply covers %.1fx the computed worst case" % SUPPLY_MARGIN,
            "%.1f A rating vs %.1f mA x %.1f = %.0f mA"
            % (rec_a, total_ma, SUPPLY_MARGIN, total_ma * SUPPLY_MARGIN))

    R.h2("6.3  The ESP32 burst, and why a capacitor is not the answer")
    R.p("     C = I*dt/dV for a %.0f mV droop:" % 100.0)
    for dt_ms in (0.05, 2.0):
        c = ESP32_PEAK_MA * 1e-3 * dt_ms * 1e-3 / 0.1
        R.p("       %5.2f ms burst of %.0f mA  ->  C = %8.1f uF" % (dt_ms, ESP32_PEAK_MA, c * 1e6))
    R.p("     A 50 us RF envelope peak is capacitor territory. A full 2 ms 802.11b frame is")
    R.p("     not -- it needs %.0f uF, which nobody fits."
        % (ESP32_PEAK_MA * 1e-3 * 2e-3 / 0.1 * 1e6))
    R.p("     CONCLUSION: SIZE THE REGULATOR for >= %.0f mA continuous on 3.3 V and fit"
        % ESP32_PEAK_MA)
    R.p("     %.0f uF bulk + 100 nF local. Do not try to solve a 2 ms event with bulk C."
        % VIN_BLOCK_UF)
    R.check(esp_on_5v > both,
            "the ESP32 WiFi TX burst is a LARGER 5 V load than both HV modules combined",
            "%.1f mA reflected vs %.0f mA for two loaded modules" % (esp_on_5v, both))
    R.finding("The ESP32's WiFi TX burst reflects %.0f mA onto the 5 V rail -- more than both "
              "HV modules at full load combined (%.0f mA). G0-A3 chose a network interface "
              "with write authority, so this current is real and continuous-duty, not a "
              "curiosity. Sizing the supply from the HV modules alone under-sizes it by "
              "roughly a factor of two."
              % (esp_on_5v, both))
    R.blind("inrush at power-on (both module converters and the buck start together; this "
            "model is steady-state only); HV converter efficiency versus load, which iseg does "
            "not publish; regulator thermal rise; relay coil inrush and back-EMF; and whether "
            "the [ISEG] maxima hold across the whole temperature range.")
    return total_ma, rec_a


# =====================================================================================
# SECTION 7 -- SET-POINT RESOLUTION
# =====================================================================================

def section7(divider):
    R.h1("SECTION 7 -- SET-POINT RESOLUTION")
    R.p("[ISEG] control version 2: 0 <= Vset <= Vref maps to 0 <= |Vout| <= Vnom.")
    R.p("With a DAC whose reference IS the same %.1f V the module uses (section 5.6), the" % VREF)
    R.p("mapping is exact and independent of the reference value:")
    R.p("      LSB_out = Vnom / 2^bits")
    R.p("because the DAC's full scale and the module's full scale become the same node. That")
    R.p("is a design property worth stating: referencing the DAC to Vref removes the reference")
    R.p("from the resolution equation entirely.")
    R.p("Computed INDEPENDENTLY of docs/CONTROL_ARCHITECTURE.md. Disagreement is a finding.")

    R.h2("7.1  Volts at the output per LSB, into a 0..%.1f V Vset" % VSET_FS)
    R.p("     %-8s %14s %14s %16s %16s"
        % ("bits", "LSB at Vset", "LSB at output", "% of Vnom",
           "vs +/-1 pct (%.0f V)" % (ADJ_ACCURACY * VNOM)))
    for b in (8, 12, 16):
        lsb_set = VSET_FS / 2 ** b
        lsb_out = VNOM / 2 ** b
        R.p("     %-8d %11.6f V %11.5f V %15.5f %% %14.4fx"
            % (b, lsb_set, lsb_out, 100 * lsb_out / VNOM, lsb_out / (ADJ_ACCURACY * VNOM)))
    R.p()
    R.p("     %-8s %16s %16s %18s" % ("bits", "vs ripple max", "vs monitor LSB", "verdict"))
    R.p("     %-8s %16s %16s" % ("", "(%.0f mV)" % (RIPPLE_MAX_VPP * 1e3),
                                 "(%.4f V)" % divider["lsb_hv"]))
    verdicts = {
        8: "the ESP32's own DAC lives here -- steps visible on a sweep",
        12: "below the module's accuracy, above the monitor LSB: the sweet spot",
        16: "below the ripple floor AND below the monitor LSB: unobservable",
    }
    for b in (8, 12, 16):
        lsb_out = VNOM / 2 ** b
        R.p("     %-8d %15.4fx %15.4fx  %s"
            % (b, lsb_out / RIPPLE_MAX_VPP, lsb_out / divider["lsb_hv"], verdicts[b]))
    R.check(VNOM / 2 ** 12 < ADJ_ACCURACY * VNOM,
            "12-bit LSB is finer than the module's own +/-1 % adjustment accuracy",
            "%.4f V vs %.1f V, %.0fx finer"
            % (VNOM / 2 ** 12, ADJ_ACCURACY * VNOM, ADJ_ACCURACY * VNOM / (VNOM / 2 ** 12)))
    R.check(VNOM / 2 ** 12 > divider["lsb_hv"],
            "a 12-bit set-point step is RESOLVABLE in the independent monitor readback",
            "set LSB %.4f V vs monitor LSB %.4f V, %.1fx"
            % (VNOM / 2 ** 12, divider["lsb_hv"], (VNOM / 2 ** 12) / divider["lsb_hv"]))
    R.check(VNOM / 2 ** 16 < divider["lsb_hv"] and VNOM / 2 ** 16 < RIPPLE_MAX_VPP,
            "a 16-bit set-point step is NOT observable -- below both the monitor LSB and the "
            "module's own ripple floor",
            "set LSB %.5f V vs monitor LSB %.4f V and ripple %.3f V"
            % (VNOM / 2 ** 16, divider["lsb_hv"], RIPPLE_MAX_VPP))
    R.check(VNOM / 2 ** 8 > 0.001 * VNOM,
            "8-bit is coarser than 0.1 % of full scale, i.e. insufficient",
            "%.4f V steps vs a %.3f V target" % (VNOM / 2 ** 8, 0.001 * VNOM))

    R.h2("7.2  The bottom of the range is UNSPECIFIED, and the DAC must know it")
    codes_unspec = int(math.ceil(RIPPLE_VALID_FRACTION * 2 ** 12))
    R.p("     [ISEG] guarantees ripple/noise only for %.0f %% * Vnom < Vout <= Vnom, i.e. above"
        % (100 * RIPPLE_VALID_FRACTION))
    R.p("     %.0f V. On a 12-bit path that is codes 0 .. %d -- %d of 4096 codes, %.1f %% of"
        % (RIPPLE_VALID_FLOOR_V, codes_unspec - 1, codes_unspec,
           100.0 * codes_unspec / 4096))
    R.p("     the command space -- addressing an output region iseg DOES NOT SPECIFY.")
    R.p("     This is not 'slightly worse performance at low output'. It is 'no guarantee'.")
    R.p("     Consequences that belong in the protocol and the firmware, not in a footnote:")
    R.p("       * the host must be able to command 0 (fully off) and anything >= %.0f V,"
        % RIPPLE_VALID_FLOOR_V)
    R.p("         and a request in between must return an explicit WARNING, not a silent clamp")
    R.p("         and not a silent acceptance (DECISIONS REF-05: no silent clamping, ever);")
    R.p("       * the monitor-disagreement trip and the discharge self-test both operate in")
    R.p("         this band and must not treat unspecified behaviour as a fault;")
    R.p("       * every accuracy number in this document is quoted at full scale and NONE of")
    R.p("         them is claimed below %.0f V." % RIPPLE_VALID_FLOOR_V)
    R.check(codes_unspec > 0 and codes_unspec < 4096,
            "the unspecified band is a real, bounded region of the 12-bit command space",
            "%d of 4096 codes (0 .. %.0f V)" % (codes_unspec, RIPPLE_VALID_FLOOR_V))

    R.h2("7.3  RECOMMENDATION")
    R.p("     12-bit set path, 16-bit monitor path. TWO of each in mode 2 -- two DACs and two")
    R.p("     monitor channels, since both outputs are independently commanded and measured.")
    R.p("     The monitor must be FINER than the set path so a set-point step is resolvable in")
    R.p("     readback: %.4f V set LSB against %.4f V monitor LSB satisfies that by %.0fx."
        % (VNOM / 2 ** 12, divider["lsb_hv"], (VNOM / 2 ** 12) / divider["lsb_hv"]))
    R.p("     16-bit setting buys resolution below the module's own ripple; 8-bit -- including")
    R.p("     the ESP32's internal DAC -- gives %.2f V steps at %.0f V."
        % (VNOM / 256, VNOM))
    R.blind("DAC INL and DNL (LSB size is not accuracy); the module's own %.0f ppm/K tempco, "
            "which at %.0f V is %.3f V/K and swamps a 16-bit LSB after %.2f K; and VSET "
            "settling time, which iseg does not publish and which is MEASURABLE NOW."
            % (TEMPCO_PPM_K, VNOM, TEMPCO_PPM_K * 1e-6 * VNOM,
               (VNOM / 2 ** 16) / (TEMPCO_PPM_K * 1e-6 * VNOM)))


# =====================================================================================
# SECTION 8 -- OTHER CLASSES, KEPT ONLY WHERE THE COMPARISON CHANGES SOMETHING
# =====================================================================================

OTHER_CLASSES = [(200, 2.5e-3), (400, 1.2e-3), (600, 0.8e-3), (800, 0.6e-3), (1000, 0.5e-3)]


def section8():
    R.h1("SECTION 8 -- OTHER CLASSES, KEPT ONLY WHERE THE COMPARISON IS INFORMATIVE")
    R.p("The part is FROZEN at %s. Nothing here is a design option. These three comparisons"
        % PART)
    R.p("are kept because each explains WHY a number above is what it is; every other")
    R.p("parameterisation from session 1 has been deleted as noise.")

    R.h2("8.1  Clearance across the 0.5 W range -- what the 1 kV choice costs in board")
    R.p("     NOTE THE COLUMN LABEL. It is MODULE Vnom, not 'FS'. Session 1 never disambiguated")
    R.p("     module nominal voltage from OUTPUT full scale, and under the (now rejected)")
    R.p("     series-stack topology the two differed by 2x. On the frozen design they are equal")
    R.p("     -- one module drives the output at a time -- but the label must say which.")
    R.p()
    R.p("     %-12s %14s %14s %14s %12s" %
        ("module Vnom", "HV<->GND (mm)", "span V", "HV+<->HV- (mm)", "corridor"))
    for vnom, _ in OTHER_CLASSES:
        r_se = recommended_clearance_mm(vnom)[0]
        r_sp = recommended_clearance_mm(2 * vnom)[0]
        R.p("     %-12d %14.1f %14.0f %14.1f %11.1f mm%s"
            % (vnom, r_se, 2 * vnom, r_sp, 2 * r_se + GUARD_TRACE_MM,
               "   <- FROZEN" if vnom == VNOM else ""))
    R.p()
    R.p("     The 1 kV class costs %.1f mm of guarded corridor against %.1f mm at 200 V --"
        % (2 * recommended_clearance_mm(1000)[0] + GUARD_TRACE_MM,
           2 * recommended_clearance_mm(200)[0] + GUARD_TRACE_MM))
    R.p("     %.1fx. That is the price of the part the human owns, and it is paid in exactly"
        % ((2 * recommended_clearance_mm(1000)[0] + GUARD_TRACE_MM)
           / (2 * recommended_clearance_mm(200)[0] + GUARD_TRACE_MM)))
    R.p("     one region of the board.")

    R.h2("8.2  Monitor loading -- why 1 kV / 0.5 mA is the binding class")
    R.p("     Hold the divider at 1.00 % of Inom at every class and watch Rt:")
    R.p()
    R.p("     %-12s %10s %12s %12s %14s %12s" %
        ("module Vnom", "Inom (mA)", "1 % (uA)", "Rt (Mohm)", "leak err @10G", "vs VMON"))
    binding = []
    for vnom, inom in OTHER_CLASSES:
        i1 = 0.01 * inom
        rt = vnom / i1
        leak = vnom * rt / 1e10
        worse = leak > VMON_ACCURACY * vnom
        if worse:
            binding.append(vnom)
        R.p("     %-12d %10.2f %12.2f %12.1f %13.3f V %12s"
            % (vnom, inom * 1e3, i1 * 1e6, rt / 1e6, leak,
               "WORSE" if worse else "ok"))
    R.p()
    R.p("     Rt grows %.0fx from the 200 V class to the 1 kV class, because Vnom rises 5x"
        % ((1000 / (0.01 * 0.5e-3)) / (200 / (0.01 * 2.5e-3))))
    R.p("     while Inom falls 5x. The unguarded surface-leakage error therefore grows as the")
    R.p("     SQUARE of the class, and it crosses the module's own VMON accuracy at %s V."
        % ", ".join(str(v) for v in binding))
    R.p("     THIS is why section 4.4 makes the guard ring a requirement: at a lower class the")
    R.p("     same design would have been merely untidy.")
    R.check(len(binding) > 0 and VNOM in binding,
            "the frozen 1 kV class is one where unguarded divider leakage beats VMON, which "
            "is what makes the guard ring mandatory rather than optional",
            "classes where unguarded leakage exceeds VMON: %s V"
            % ", ".join(str(v) for v in binding))

    R.h2("8.3  The 1 W / 12 V family -- kept ONLY to show the hazard is family-specific")
    R.p("     The 1 W family runs Vref = 5.0 V. A 3.3 V rail on VSET would then command")
    R.p("     3.3/5.0 = %.0f %% of Vnom -- UNDER full scale, not over. The entire section-5"
        % (100 * 3.3 / 5.0))
    R.p("     over-voltage hazard is an artefact of a 2.5 V reference sitting below a 3.3 V")
    R.p("     logic rail.")
    R.p()
    R.p("     *** THAT FAMILY IS NOT AVAILABLE. *** The human owns %s and %s."
        % (ITEM_P, ITEM_N))
    R.p("     This is recorded so that nobody re-derives 'we should have bought the 1 W part'")
    R.p("     as though it were an open decision, and so that the clamp is understood as")
    R.p("     compensating for a fixed property of the hardware in hand rather than as a")
    R.p("     precaution someone could trade away.")
    R.check(3.3 / 5.0 < 1.0 < 3.3 / VREF,
            "the 3.3 V VSET hazard exists for the owned 2.5 V-Vref part and would not for a "
            "5 V-Vref part -- i.e. it is a property of THIS part, not of the architecture",
            "%.0f %% of Vnom on the owned part vs %.0f %% on the 1 W family"
            % (100 * 3.3 / VREF, 100 * 3.3 / 5.0))


# =====================================================================================
# MAIN
# =====================================================================================

def main():
    try:
        R.h1("iseg BIPOLAR HV CONTROLLER -- NUMBERS PROBE, PINNED TO %s" % PART)
        R.p("Every number the design freezes, with its formula and its source.")
        R.p("PRIMARY CASE: %s / %s -- the modules the human owns. Computed in full."
            % (ITEM_P, ITEM_N))
        R.p("Other voltage classes and the 1 W family appear ONLY in section 8, and only where")
        R.p("the comparison explains a number rather than offering an option.")
        R.p()
        R.p("G0 is signed off. The behaviour is set-and-hold with polarity changeover; the")
        R.p("combiner is an HV relay changeover; comms are serial AND network, both with write")
        R.p("authority; and the instrument is switchable between one combined bipolar output")
        R.p("and two independent unipolar outputs that may BOTH BE ENERGISED AT ONCE.")
        R.p()
        R.p("Runtime artifact reads used as independent sources of truth this run:")
        R.p("   chip-resistor land patterns : %s"
            % ("KiCad 10.0 stock library [verified-artifact]" if read_chip_pad_geometry()
               else "NOT AVAILABLE -- hardcoded fallback in use"))
        R.p("   module footprint            : %s"
            % ("hardware/hvctl/lib/iseg.pretty [verified-artifact]" if ISEGFP
               else "NOT AVAILABLE"))
        R.p("   KiCad netclass field set    : %s"
            % ("hardware/phase0_env_proof/env_proof.kicad_pro [verified-artifact]"
               if os.path.isfile(PHASE0_PRO) else "NOT AVAILABLE"))
        for pkg in sorted(CHIP_PADS):
            R.p("     %-6s pad gap %.4f mm   land extent %.4f mm"
                % (pkg, PAD_GAP_MM[pkg], PAD_EXTENT_MM[pkg]))

        section0()
        rec, rec_se, rec_span = section1()
        strings = compute_strings()
        section1b(rec_se, rec_span, strings)
        section2(rec_se, rec_span)
        section3(strings)
        divider = section4(strings)
        section5()
        section6()
        section7(divider)
        section8()

        # ---- discrepancy register ----
        R.h1("DISCREPANCY REGISTER -- flagged, deliberately NOT resolved")
        R.p("D-1  [ISEG] Table 1 specifies 'Current monitor accuracy 1 % * Inom', but Table 4")
        R.p("     lists only seven pins and NO current-monitor pin:")
        R.p("       1 +VIN | 2 VSET | 3 GND | 4 /ON | 5 VMON | 6 HV | 7 GND")
        R.p("     Either the spec is inherited boilerplate from a larger iseg family, or there")
        R.p("     is an undocumented output. DO NOT design a current readback against it.")
        R.p("     Action: ask iseg. NOW MEASURABLE: the modules are in hand, so the seven pins")
        R.p("     can be probed directly and the question answered on the bench.")
        R.p()
        R.p("D-2  IPC-2221 column labelling: the task brief's description of column B4 matches")
        R.p("     column B1's formula. See section 1.2. Unresolved; needs a primary copy.")
        R.p()
        R.p("D-3  [ISEG] gives no output capacitance, no output impedance, no internal bleeder,")
        R.p("     no VSET step response and no turn-on time. Sections 3 and 7 rest on")
        R.p("     assumptions for all five. ALL FIVE ARE NOW MEASURABLE -- see the")
        R.p("     MEASURABLE-NOW register below.")
        R.p()
        R.p("D-4  Dimensional: the datasheet spec table rounds the body to 40/16/11 mm while")
        R.p("     Figure 1 dimensions it 39.6/15.7/11 mm. Use Figure 1. The footprint study")
        R.p("     owns this and has resolved it; recorded here for completeness.")
        R.p()
        R.p("D-5  MODULE_CASE <-> internal HV: iseg publishes NO dielectric withstand or")
        R.p("     isolation rating between the HV pin and the grounded case, and section 1.7")
        R.p("     measures the internal spacing at a fraction of what this design demands on")
        R.p("     the board. The row is UNRATABLE by any board standard. Ask iseg. Until")
        R.p("     answered, no session may substitute a board-standard number for it.")
        R.p()
        R.p("D-6  The clearance/creepage constants are [unverified-primary] and session 1's")
        R.p("     internal evidence for them was proved circular (section 1.5). Section 1.6")
        R.p("     shows the two candidate readings give DIFFERENT board tiers, so this is a")
        R.p("     blocking item for layout, not for fab.")

        # ---- measurable-now register ----
        R.h1("MEASURABLE-NOW REGISTER -- the modules are in hand (G0-A2 consequence 4)")
        R.p("Everything session 1 listed as 'unmeasurable, assumed' is now a bench afternoon.")
        R.p("Each entry names the quantity, the assumed value in use, and how to measure it.")
        R.p()
        for i, m in enumerate(MEASURABLE_NOW, 1):
            R.p("  M-%-2d %s" % (i, m))
        R.p()
        R.p("  M-%-2d Pin positions and body dimensions: CALIPER-MEASURABLE. The footprint has"
            % (len(MEASURABLE_NOW) + 1))
        R.p("       survived three adversarial skeptics against the VENDOR ARTWORK, which is")
        R.p("       not the same as against a module. Measure one.")
        R.p("  M-%-2d The D-1 current-monitor question: probe all seven pins on a live module."
            % (len(MEASURABLE_NOW) + 2))
        R.p()
        R.p("  SAFETY NOTE ON ALL OF THE ABOVE: these measurements energise a %.0f V source."
            % VNOM)
        R.p("  They are Phase-7-class work, human-present, with an HV-rated probe and a")
        R.p("  grounding stick. Several (output capacitance, internal bleeder) can be done")
        R.p("  UNPOWERED and should be done that way first.")

        # ---- assumptions ----
        R.h1("ASSUMPTIONS LOGGED (each needs G1 confirmation)")
        for i, a in enumerate(ASSUMPTIONS, 1):
            R.p("  A-%-2d %s" % (i, a))

        # ---- sources ----
        R.h1("SOURCES")
        for k in sorted(SOURCES):
            R.p("  [%s]" % k)
            for line in SOURCES[k].split(". "):
                if line.strip():
                    R.p("      " + line.strip().rstrip(".") + ".")

        # ---- findings ----
        R.h1("FINDINGS")
        if R.findings:
            for i, f in enumerate(R.findings, 1):
                R.p("  F-%-2d %s" % (i, f))
        else:
            R.p("  (none)")

        # ---- verdict ----
        n = len(R.checks)
        bad = [c for c in R.checks if not c[0]]
        R.h1("VERDICT")
        R.p("  assertions evaluated : %d" % n)
        R.p("  passed               : %d" % (n - len(bad)))
        R.p("  FAILED               : %d" % len(bad))
        if bad:
            R.p()
            for ok, name, detail in bad:
                R.p("    FAIL  %s  --  %s" % (name, detail))
        R.p()
        R.p("  What this probe structurally CANNOT see, taken as a whole:")
        R.p("    * it is arithmetic on datasheet numbers. Nothing has been measured, nothing")
        R.p("      simulated, no component selected by MPN, no MPN checked against a live")
        R.p("      distributor page -- and the modules that ARE in hand have not been touched;")
        R.p("    * BOTH standards it leans on are [unverified-primary]. Session 1's internal")
        R.p("      evidence for them was an algebraic tautology (section 1.5) and has been")
        R.p("      deleted rather than replaced. There is currently NO evidence that the")
        R.p("      clearance constants are the right constants;")
        R.p("    * it assumes the module behaves as specified across its whole range, and")
        R.p("      [ISEG] explicitly does NOT specify behaviour below %.0f V of output;"
            % RIPPLE_VALID_FLOOR_V)
        R.p("    * it says nothing about whether the mode-position sense path is trustworthy,")
        R.p("      which is the central new safety question G0-A4 opened;")
        R.p("    * it cannot see per-pad clearance overrides applied elsewhere in the design,")
        R.p("      only the one it happened to read in section 1.7;")
        R.p("    * exit code 0 here means 'every arithmetic assertion holds', which is a much")
        R.p("      weaker claim than 'the design is safe'.")

        print(R.dump())
        return 1 if bad else 0

    except Exception:
        import traceback
        traceback.print_exc()
        print(R.dump())
        return 2


if __name__ == "__main__":
    sys.exit(main())
