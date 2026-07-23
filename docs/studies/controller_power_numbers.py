#!/usr/bin/env python3
"""controller_power_numbers.py -- reproduce and CHECK every computed number in
docs/design/CONTROLLER_AND_POWER.md.

Zero-argument. Deterministic. Standard library only (runs on any Python 3).

WHAT THIS IS, AS AN INSTRUMENT
------------------------------
Two halves, and the second is the point:

  1. It RECOMPUTES, from first principles, every number the design document
     quotes in sections 3 (power tree), 5 (set-point clamp) and 7.4 (heartbeat).
  2. It then GREPS THE DOCUMENT for the literal string each result should appear
     as, and fails if it is absent.

Half 2 is the acceptance check, and its source of truth is INDEPENDENT of half 1:
the prose was typed by a human, the arithmetic is done here.  If someone edits a
number in the markdown, or changes a component value here without updating the
prose, the two disagree and this exits 1.  A tool that only printed its own
output would agree with itself forever.

WHAT IT CANNOT SEE
------------------
It is arithmetic over datasheet values.  It verifies no circuit, simulates
nothing, and checks no part number against any distributor.  Exit 0 means the
algebra ran and the document repeats it correctly -- NOT that the design is safe.
Several inputs (regulator efficiencies, 74HCT thresholds, LM4040 minimum current,
OPA2320 output swing) are [recalled] and are flagged in the document as the
highest-value Phase-6 datasheet reads.

EXIT CODES  (per CLAUDE.md)
  0  every assertion passed
  1  a verification failed (recomputation disagrees with the document)
  2  structural failure (the document could not be found or read)
"""

import io
import math
import os
import sys

DOC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "design", "CONTROLLER_AND_POWER.md",
)

FAILURES = []
CHECKS = 0


def _load_doc():
    try:
        with io.open(DOC, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:                                  # pragma: no cover
        sys.stderr.write("STRUCTURAL FAILURE: cannot read %s (%s)\n" % (DOC, exc))
        sys.exit(2)


TEXT = _load_doc()


def check(label, expected_doc_text):
    """Assert that a string BUILT FROM THE COMPUTED VALUES appears in the document.

    The expected text is always assembled from this script's own arithmetic, never
    typed as a literal.  That is what makes the check two-sided: change a component
    value here and the assembled string stops matching the prose; change a number in
    the prose and the prose stops matching the assembled string.  Either way, exit 1.

    An earlier version of this function took the computed value and a hand-typed
    document string and only grepped for the latter.  Mutation testing found that a
    changed script constant produced no failure at all, because the computed value
    was never used.  That version was worthless as an acceptance check and is
    recorded here so the mistake is not repeated.
    """
    global CHECKS
    CHECKS += 1
    present = expected_doc_text in TEXT
    print("  [%s] %-52s doc must contain: %s"
          % ("PASS" if present else "FAIL", label, expected_doc_text))
    if not present:
        FAILURES.append("%s -- document does not contain the computed string %r"
                        % (label, expected_doc_text))


def head(title):
    print("\n" + "=" * 92)
    print(title)
    print("=" * 92)


# ===========================================================================
head("SECTION 3 -- POWER TREE, 12 V INPUT")
# ===========================================================================
# All module currents are iseg Table 1 MAXIMA, not typicals (NUMBERS_PROBE §6).
# G0-A4/NUM-22: BOTH modules loaded simultaneously is NORMAL operation, not a
# margin choice.  The "only one is ever enabled" argument is dead.
I_MOD_EACH = 180.0          # mA, iseg max at Vnom with load
I_LOGIC_HCT = 5.0           # mA, 7 x 74HCT packages
I_SUPERVISORS = 1.0         # mA, 3 x TPS3701
# Coil rail: SUPERSEDES NUMBERS_PROBE §6.2's 80 mA.  COMBINER_DESIGN.md §4.2 selected
# Pickering 67-1-C-5/5D (40 ohm coil = 125 mA at 5 V) and Panasonic TQ2SA-5V (36 mA).
# BOTH Form-C coils are energised simultaneously in unipolar mode -- that is the mode,
# not an overlap allowance (G0-A4).
I_COIL_K1 = 125.0           # mA, Pickering 67-1-C-5/5D, 40 ohm coil
I_COIL_K2 = 125.0           # mA, same part
I_COIL_KS = 36.0            # mA, Panasonic TQ2SA-5V interlock armature
I_COIL_RAIL = I_COIL_K1 + I_COIL_K2 + I_COIL_KS

i_5v_mod = 2 * I_MOD_EACH + I_LOGIC_HCT + I_SUPERVISORS + I_COIL_RAIL
w_5v_mod = i_5v_mod * 5.0 / 1000.0
check("+5V_MOD total (mA | W)",
      "| **Total** | **%.0f** | **%.3f** |" % (i_5v_mod, w_5v_mod))

I_ESP32_PEAK = 500.0        # mA on 3V3, WiFi TX burst  [recalled, NUM-21]
I_W5500 = 132.0             # mA, 100 Mbps link         [recalled -> Phase 6]
I_CP2102N = 20.0
I_MISC_33 = 30.0
i_3v3 = I_ESP32_PEAK + I_W5500 + I_CP2102N + I_MISC_33
w_3v3 = i_3v3 * 3.3 / 1000.0
check("+3V3 total (mA | W)",
      "| **Total (worst-case simultaneous)** | **%.0f** | **%.3f** |" % (i_3v3, w_3v3))

I_5V_A = 60.0               # mA budget, retained unchanged from NUMBERS_PROBE §6.2
w_5v_a = I_5V_A * 5.0 / 1000.0

ETA_BUCK_5 = 0.90
ETA_BUCK_33 = 0.88
W_QUIESCENT = 0.240         # input protection, indicators, regulator quiescent

w_in_5 = w_5v_mod / ETA_BUCK_5
w_in_33 = w_3v3 / ETA_BUCK_33
w_in_a = I_5V_A * 12.0 / 1000.0                 # LDO: input current == output current
w_total = w_in_5 + w_in_33 + w_in_a + W_QUIESCENT
i_total_12v = w_total / 12.0 * 1000.0
w_delivered = w_5v_mod + w_3v3 + w_5v_a

check("12 V input, 5 V buck branch",
      "| `+5V_MOD` buck | %.3f | %.2f | %.3f | %.0f |"
      % (w_5v_mod, ETA_BUCK_5, w_in_5, w_in_5 / 12 * 1000))
check("12 V input, 3V3 buck branch",
      "| `+3V3` buck | %.3f | %.2f | %.3f | %.0f |"
      % (w_3v3, ETA_BUCK_33, w_in_33, w_in_33 / 12 * 1000))
check("12 V input, analog LDO branch",
      "| `+5V_A` LDO | %.3f | %.2f | %.3f | %.0f |"
      % (w_5v_a, w_5v_a / w_in_a, w_in_a, w_in_a / 12 * 1000))
check("12 V input TOTAL",
      "| **TOTAL** | **%.3f** | **%.2f** | **%.3f** | **%.0f** |"
      % (w_delivered, w_delivered / w_total, w_total, i_total_12v))

# The enclosure work (HV_SAFETY_ENVELOPE §2 item 5) specifies ventilation for
# 4.2-6.4 W.  Essentially all input power becomes heat inside the chassis.
# HV_SAFETY_ENVELOPE §2 item 5 specifies ventilation for 4.2-6.4 W.  After the
# coil correction of §0.4.2 the real figure is ABOVE that band.  The assertion is
# therefore NOT "the number is in the band" -- it is "if the number is outside the
# band, the document SAYS SO."  An exceedance that is reported is a finding; an
# exceedance that is silent is a defect.
ENCLOSURE_BAND = (4.2, 6.4)
CHECKS += 1
inside = ENCLOSURE_BAND[0] <= w_total <= ENCLOSURE_BAND[1]
if inside:
    print("  [PASS] worst-case dissipation inside the enclosure band  = %.3f W in 4.2-6.4 W" % w_total)
else:
    declared = "**%.2f W is ABOVE that band by %.2f W" % (w_total, w_total - ENCLOSURE_BAND[1])
    if declared in TEXT:
        print("  [PASS] dissipation EXCEEDS the enclosure band AND the document says so = %.3f W vs 6.4 W"
              % w_total)
    else:
        FAILURES.append("worst-case dissipation %.3f W falls outside the enclosure's stated "
                        "4.2-6.4 W band and the document does not report the exceedance "
                        "(expected the literal string %r)" % (w_total, declared))
        print("  [FAIL] dissipation outside the enclosure band and NOT reported = %.3f W" % w_total)

# Supply margin.  The probe's convention is 2.0x; this design carries 4.0x and
# names 1.5 A (3.0x) as the floor, because module inrush (M-7) is unmeasured.
supply_a = 2.0              # A, recommended 12 V brick
CHECKS += 1
margin = supply_a / (i_total_12v / 1000.0)
if margin < 3.0:
    FAILURES.append("supply margin %.2fx is below the stated 3.0x floor" % margin)
    print("  [FAIL] supply margin                                     = %.2fx" % margin)
else:
    print("  [PASS] supply margin at 12 V / 2.0 A                     = %.2fx (floor 3.0x)" % margin)


# ===========================================================================
head("SECTION 5 -- THE 2.500 V SHUNT CLAMP RAIL AND BUFFER HEADROOM")
# ===========================================================================
# Δ3: the clamp is a SHUNT reference, not a series one, because a series
# reference fails to ITS INPUT on a pass-element short -- 5 V on this rail is
# 2000 V at the output, from one fault.
R_SH = 180.0                # ohm, 1 %, 1206
V_CLAMP_NOM = 2.500
V_REF_NOM = 2.500
LM4040_TOL = 0.001          # grade A, +/-0.1 %
REF5025_TOL = 0.0005        # +/-0.05 %
I_OPAMP_IQ = 0.034            # mA, 2 x OPA2320 quiescent
R_THR_TOP, R_THR_BOT = 9.53e3, 10.5e3   # 0.1 % divider, VSET over-range threshold
R_VSET_PULLDOWN = 500.0     # 2 x 1 kohm in parallel, AT THE MODULE PIN (ARCH-05/18)
CODE_CLAMP = 0.98           # hardware headroom requirement, not just firmware (Δ4)

v_cmd_max = CODE_CLAMP * V_REF_NOM * (1 + REF5025_TOL)
i_buffer_each = v_cmd_max / R_VSET_PULLDOWN * 1000.0
i_buffer_both = 2 * i_buffer_each

for v_a in (5.00, 4.90, 4.75):
    i_avail = (v_a - V_CLAMP_NOM) / R_SH * 1000.0
    i_each_shunt = (i_avail - i_buffer_both) / 2.0
    print("     +5V_A = %.2f V: available %.2f mA, buffer load %.2f mA, each shunt %.2f mA"
          % (v_a, i_avail, i_buffer_both, i_each_shunt))
    CHECKS += 1
    if i_each_shunt < 0.060:        # LM4040 minimum operating current [recalled]
        FAILURES.append("at +5V_A=%.2f V each LM4040 carries only %.3f mA, below the "
                        "~60 uA minimum -- the shunt rail loses regulation" % (v_a, i_each_shunt))

check("clamp rail available current @ +5V_A = 5.00 V",
      "`(5.00 − 2.50) / %.0f = %.1f mA`" % (R_SH, (5.00 - V_CLAMP_NOM) / R_SH * 1000))
check("both buffers at the code clamp, into the pull-downs",
      "`2 × %.4f/%.0f = %.2f mA`" % (v_cmd_max, R_VSET_PULLDOWN, i_buffer_both))
check("each shunt device @ +5V_A = 5.00 V",
      "`(%.1f − %.2f)/2 = %.2f mA each`"
      % ((5.00 - V_CLAMP_NOM) / R_SH * 1000, i_buffer_both + I_OPAMP_IQ,
         ((5.00 - V_CLAMP_NOM) / R_SH * 1000 - i_buffer_both - I_OPAMP_IQ) / 2))
check("each shunt device @ +5V_A = 4.75 V (low corner)",
      "remaining `%.2f mA` each" % (((4.75 - V_CLAMP_NOM) / R_SH * 1000 - i_buffer_both) / 2))
check("R_sh dissipation, no load",
      "`2.5²/%.0f = %.1f mW`" % (R_SH, V_CLAMP_NOM ** 2 / R_SH * 1000))

v_rail_low = V_CLAMP_NOM * (1 - LM4040_TOL)
headroom_mv = (v_rail_low - v_cmd_max) * 1000.0
check("clamp rail worst-case low", "| **%.4f V** |" % v_rail_low)
check("commanded VSET at the code clamp", "| **%.4f V** |" % v_cmd_max)
check("buffer headroom", "| **%.1f mV** |" % headroom_mv)
check("buffer load at that point", "| **%.2f mA** |" % i_buffer_each)

OPA2320_SWING_AT_5MA = 30.0     # mV from rail  [recalled -> Phase 6, open question O-C]
CHECKS += 1
if headroom_mv <= OPA2320_SWING_AT_5MA:
    FAILURES.append("buffer headroom %.1f mV does not exceed the assumed %.0f mV output-swing "
                    "dropout -- drop the code clamp to 96 %% (+/-960 V) or raise the VSET "
                    "pull-downs (see O-C)" % (headroom_mv, OPA2320_SWING_AT_5MA))
    print("  [FAIL] headroom vs assumed swing dropout")
else:
    print("  [PASS] headroom / assumed swing dropout                  = %.2fx" % (headroom_mv / OPA2320_SWING_AT_5MA))

check("declared full-scale output",
      "**Declared full scale is ±%.0f V**" % (CODE_CLAMP * 1000))

# The VSET open-buffer default, i.e. what the duplicated pull-downs alone command
# against the module's internal 10 kohm pull-up to Vref.  These two numbers come
# from NUMBERS_PROBE §5.1 and are quoted, not re-derived, in the design document.
R_MODULE_PULLUP = 10000.0
for r, label in ((500.0, "both pull-downs fitted"), (1000.0, "one of the pair open")):
    pct = r / (r + R_MODULE_PULLUP) * 100.0
    print("     VSET open-buffer default, %-24s = %5.2f %% of Vnom (%.0f V)"
          % (label, pct, pct * 10))
check("VSET over-range comparator threshold divider",
      "`5.000 × 10.5/20.03 = %.3f V`" % (5.0 * R_THR_BOT / (R_THR_TOP + R_THR_BOT)))


# ===========================================================================
head("SECTION 7.4 -- HEARTBEAT CHARGE PUMP (Δ6)")
# ===========================================================================
# C-3 requires TWO SERIES coupling capacitors: a single shorted cap would turn
# the AC path into a DC path, letting a stuck-high GPIO hold the pump charged.
F_HB = 1000.0               # Hz, from a hardware-timer ISR gated on a
                            # main-loop-serviced counter -- NOT a free-running
                            # LEDC peripheral, which keeps toggling after a hang.
C_COUPLE_EACH = 47e-9
C_P = 1.0 / (1.0 / C_COUPLE_EACH + 1.0 / C_COUPLE_EACH)
R_HB = 1e6
C_HOLD = 100e-9
V_DRIVE = 3.3
V_F_SCHOTTKY = 0.3          # BAT54S at these currents  [recalled]

v_pump = F_HB * C_P * (V_DRIVE - 2 * V_F_SCHOTTKY) / (F_HB * C_P + 1.0 / R_HB)
tau_hb = R_HB * C_HOLD

check("two coupling caps in series", "`C_p = %.1f nF`" % (C_P * 1e9))
check("pump equilibrium voltage", "**`V = %.3f V`**" % v_pump)

VT_PLUS_MAX = 2.0           # 74HCT14 at VCC 4.5-5.5 V  [recalled -> Phase 6]
VT_MINUS_MAX = 1.4
VT_MINUS_MIN = 0.5

CHECKS += 1
if v_pump <= VT_PLUS_MAX:
    FAILURES.append("pump equilibrium %.3f V does not exceed the 74HCT14 V_T+ max of %.1f V "
                    "-- the enable would never assert" % (v_pump, VT_PLUS_MAX))
    print("  [FAIL] pump equilibrium vs V_T+ max")
else:
    print("  [PASS] margin over 74HCT14 V_T+ max (2.0 V)              = %.3f V" % (v_pump - VT_PLUS_MAX))

t_late = tau_hb * math.log(v_pump / VT_MINUS_MAX) * 1000.0
t_slow = tau_hb * math.log(v_pump / VT_MINUS_MIN) * 1000.0
check("decay to V_T- max (earliest turn-off bound)",
      "`100·ln(%.3f/%.1f) =` **%.1f ms**" % (v_pump, VT_MINUS_MAX, t_late))
check("decay to V_T- min (latest turn-off bound)",
      "`100·ln(%.3f/%.1f) =` **%.1f ms**" % (v_pump, VT_MINUS_MIN, t_slow))
check("quoted hardware turn-off window",
      "%.1f–%.1f ms" % (t_late, t_slow))

# The chop must stay faster than the module's own set-node time constant, which
# is 100 ms (manual Figure 2, [verified-artifact]).  Session 1's whole argument
# for the pump rests on this comparison.
MODULE_SET_TAU_MS = 100.0
CHECKS += 1
if t_late >= MODULE_SET_TAU_MS:
    FAILURES.append("earliest hardware turn-off (%.1f ms) is no longer faster than the module's "
                    "own 100 ms set-node pole -- the pump stops being a fast chop" % t_late)
    print("  [FAIL] hardware chop vs module 100 ms pole")
else:
    print("  [PASS] earliest chop is faster than the module's 100 ms pole = %.1f ms" % t_late)


# ===========================================================================
head("SECTION 6 -- CHANGEOVER MONOSTABLE AND LOGIC TIMING")
# ===========================================================================
R_EXT, C_EXT = 1e6, 2.2e-6
t_dwell = 0.45 * R_EXT * C_EXT      # 74HCT123 pulse width  [recalled -> Phase 6]
check("74HCT123 T_dwell", "`t_w ≈ 0.45·R·C = %.2f s`" % t_dwell)

TPD_HCT_MAX_NS = 25.0
GATE_DEPTH = 4
t_on_path_ns = TPD_HCT_MAX_NS * GATE_DEPTH
check("deepest /ON logic path", "**≤ %.0f ns**" % t_on_path_ns)
print("     margin over the module's 100 ms set-node pole            = %.2e x"
      % (MODULE_SET_TAU_MS * 1e6 / t_on_path_ns))

# Firmware's dwell must exceed the hardware backstop, so that the hardware is a
# backstop rather than the normal path (CONTROL_ARCHITECTURE §3.5).
T_DWELL_FIRMWARE = 2.0
CHECKS += 1
if T_DWELL_FIRMWARE <= t_dwell:
    FAILURES.append("firmware T_dwell (%.2f s) does not exceed the hardware monostable "
                    "(%.2f s) -- the hardware would become the normal path" % (T_DWELL_FIRMWARE, t_dwell))
    print("  [FAIL] firmware dwell vs hardware dwell")
else:
    print("  [PASS] firmware dwell (2.0 s) exceeds hardware dwell      = %.2f s of headroom"
          % (T_DWELL_FIRMWARE - t_dwell))


# ===========================================================================
head("SECTION 6.3 -- RAIL_OK WINDOW THRESHOLDS vs THE MODULE'S OWN Vin WINDOW")
# ===========================================================================
# G0-A2 freezes the module input range at 4.5-5.5 V.  The supervisor's window
# must sit strictly INSIDE it, including the supervisor's own tolerance.
MODULE_VIN_MIN, MODULE_VIN_MAX = 4.5, 5.5
UV_TRIP, OV_TRIP = 4.62, 5.38
SUPERVISOR_TOL = 0.01

uv_lo, uv_hi = UV_TRIP * (1 - SUPERVISOR_TOL), UV_TRIP * (1 + SUPERVISOR_TOL)
ov_lo, ov_hi = OV_TRIP * (1 - SUPERVISOR_TOL), OV_TRIP * (1 + SUPERVISOR_TOL)
print("     UV trip 4.62 V +/-1 %% -> %.3f .. %.3f V" % (uv_lo, uv_hi))
print("     OV trip 5.38 V +/-1 %% -> %.3f .. %.3f V" % (ov_lo, ov_hi))
CHECKS += 1
if uv_lo <= MODULE_VIN_MIN or ov_hi >= MODULE_VIN_MAX:
    FAILURES.append("RAIL_OK window (%.3f..%.3f V worst case) is not strictly inside the "
                    "module's 4.5-5.5 V input range" % (uv_lo, ov_hi))
    print("  [FAIL] RAIL_OK window inside the module Vin range")
else:
    print("  [PASS] RAIL_OK window strictly inside 4.5-5.5 V           "
          "= %.0f mV / %.0f mV of margin" % ((uv_lo - MODULE_VIN_MIN) * 1000,
                                             (MODULE_VIN_MAX - ov_hi) * 1000))

# The 2V5_CLAMP OV trip must fire BEFORE the VSET over-range comparator, so that
# a rail fault is diagnosed as a rail fault and not as a set-point fault.
V2V5_OV_TRIP = 2.60
VSET_COMP_THRESHOLD = 2.625
CHECKS += 1
if V2V5_OV_TRIP >= VSET_COMP_THRESHOLD:
    FAILURES.append("+2V5_CLAMP OV trip (%.3f V) does not precede the VSET over-range "
                    "comparator (%.3f V)" % (V2V5_OV_TRIP, VSET_COMP_THRESHOLD))
    print("  [FAIL] rail OV precedes VSET comparator")
else:
    print("  [PASS] +2V5_CLAMP OV trips before the VSET comparator     = %.0f mV earlier"
          % ((VSET_COMP_THRESHOLD - V2V5_OV_TRIP) * 1000))


# ===========================================================================
head("SECTION 2 -- STRAPPING PINS AND THE GPIO MAP")
# ===========================================================================
# [web-verified this session, Espressif ESP32-S3 Schematic Checklist]
S3_STRAPPING = {0, 3, 45, 46}
S3_USB = {19, 20}
S3_FLASH = set(range(26, 33))
S3_UART0 = {43, 44}
S3_JTAG_RESERVED = {39, 40, 41, 42}

HV_RELEVANT = {4: "HB_OUT", 5: "ARM_EN", 6: "OUT_EN", 7: "SEL", 36: "nOVP_CLR",
               33: "MODE_A_RB", 34: "MODE_B_RB", 35: "OVP_RB"}
ALL_ASSIGNED = dict(HV_RELEVANT)
ALL_ASSIGNED.update({8: "nSYNC_DAC", 9: "SPI_A_SCK", 10: "SPI_A_MOSI", 11: "SPI_A_MISO",
                     12: "nLOAD_165", 13: "SPI_B_SCK", 14: "SPI_B_MOSI", 15: "SPI_B_MISO",
                     16: "nCS_W5500", 17: "nRST_W5500", 18: "nINT_W5500", 21: "I2C_SDA",
                     2: "I2C_SCL", 37: "nALERT_ADC", 1: "LED_NET",
                     43: "U0TXD", 44: "U0RXD"})

CHECKS += 1
collide = sorted(set(HV_RELEVANT) & S3_STRAPPING)
if collide:
    FAILURES.append("HV-relevant signals on ESP32-S3 STRAPPING pins: %s" % collide)
    print("  [FAIL] HV-relevant signal on a strapping pin: %s" % collide)
else:
    print("  [PASS] no HV-relevant signal on GPIO0/3/45/46             = %d HV-relevant signals checked"
          % len(HV_RELEVANT))

for name, reserved in (("USB D-/D+", S3_USB), ("SPI flash", S3_FLASH),
                       ("JTAG (reserved)", S3_JTAG_RESERVED)):
    CHECKS += 1
    bad = sorted(set(ALL_ASSIGNED) & reserved)
    if bad:
        FAILURES.append("assigned signals collide with %s pins: %s" % (name, bad))
        print("  [FAIL] collision with %s: %s" % (name, bad))
    else:
        print("  [PASS] no collision with %-38s = clear" % name)

CHECKS += 1
uart_only = sorted(set(ALL_ASSIGNED) & S3_UART0)
if set(ALL_ASSIGNED[p] for p in uart_only) - {"U0TXD", "U0RXD"}:
    FAILURES.append("GPIO43/44 carry something other than UART0 -- the ROM boot log is on GPIO43")
    print("  [FAIL] GPIO43/44 carry non-UART signals")
else:
    print("  [PASS] GPIO43/44 carry UART0 only (ROM boot log is here)  = clear")

# Quad-PSRAM requirement: octal PSRAM occupies GPIO33-37
# [web-verified, ESP32-S3 Hardware Design Guidelines].
OCTAL_PSRAM_OCCUPIED = set(range(33, 38))
CHECKS += 1
used_in_band = sorted(set(ALL_ASSIGNED) & OCTAL_PSRAM_OCCUPIED)
if used_in_band:
    print("  [PASS] GPIO33-37 in use (%s) -> the module MUST be QUAD PSRAM (-N8R2), not octal"
          % used_in_band)
    if "**Quad PSRAM (`R2`), not octal (`R8`), is a requirement.**" not in TEXT:
        FAILURES.append("GPIO33-37 are used but the document does not state the quad-PSRAM requirement")
else:                                                       # pragma: no cover
    print("  [PASS] GPIO33-37 unused")

SPARE = {38, 47, 48}
check("assigned GPIO count",
      "**Count: %d signals assigned (including UART0), %d spare"
      % (len(ALL_ASSIGNED), len(SPARE)))

# Nothing may be both assigned and spare, and nothing may be assigned twice.
CHECKS += 1
overlap = sorted(set(ALL_ASSIGNED) & SPARE)
if overlap:
    FAILURES.append("GPIO listed as both assigned and spare: %s" % overlap)
    print("  [FAIL] assigned/spare overlap: %s" % overlap)
else:
    print("  [PASS] no GPIO is both assigned and spare                 = %d assigned, %d spare"
          % (len(ALL_ASSIGNED), len(SPARE)))


# ===========================================================================
head("RESULT")
# ===========================================================================
print("%d assertions checked." % CHECKS)
if FAILURES:
    print("\n%d FAILURE(S):" % len(FAILURES))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("All pass.")
print("\nNOTE: exit 0 means the algebra ran and docs/design/CONTROLLER_AND_POWER.md")
print("repeats it correctly. It does NOT mean the design is safe, buildable, or")
print("that any part number exists. See §12.4 of that document.")
sys.exit(0)
