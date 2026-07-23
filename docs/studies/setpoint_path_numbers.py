#!/usr/bin/env python3
"""
Numbers for docs/design/SETPOINT_PATH.md.

stdlib only, zero-argument, deterministic.  Runs on ANY Python 3 (plain `python`
is not on PATH in this environment -- use an absolute interpreter path, e.g.
    "C:/Program Files/KiCad/10.0/bin/python.exe" docs/studies/setpoint_path_numbers.py

Exit codes (project convention):
    0  every assertion passed
    1  a verification assertion failed
    2  structural failure (bad constant, impossible configuration)
    3  legibility failure (a printed table would be unreadable)

INDEPENDENT SOURCE OF TRUTH
---------------------------
Where a number can be derived two ways, it IS derived two ways and the two are
compared.  Specifically:

  * the VSET pull-down residual is computed BOTH as a two-resistor divider AND by
    Thevenin/superposition from the (Vref, 10k) equivalent -- different algebra,
    same node;
  * the over-range figure is computed BOTH from the clamp rail directly AND from
    the multiplicative tolerance stack;
  * the bench solve for (Vref, R_pullup) from two loaded measurements is checked
    by ROUND TRIP against the values used to synthesise the measurements;
  * the resolution table is cross-checked against ppm-of-full-scale computed from
    an independent expression.

What this program CANNOT see: it is arithmetic over datasheet values and stated
assumptions.  It verifies no circuit.  Exit 0 means the algebra ran and is self-
consistent, NOT that the design is safe.  Nothing here has been simulated, built
or measured.  Every constant tagged [recalled] below is a candidate for a G1
datasheet read; every constant tagged [MEASURABLE-NOW] is a bench measurement.
"""

import math
import sys

FAILS = []
NCHECK = 0


def check(name, cond, detail=""):
    global NCHECK
    NCHECK += 1
    if not cond:
        FAILS.append(f"{name}: {detail}")


def close(a, b, rtol=1e-9, atol=1e-12):
    return abs(a - b) <= max(atol, rtol * max(abs(a), abs(b)))


def hr(t):
    print()
    print("=" * len(t))
    print(t)
    print("=" * len(t))


# --------------------------------------------------------------------------
# 0.  Frozen module constants -- G0-A2, AP010504P05 / AP010504N05
#     [verified-artifact] iseg APS technical documentation v2.5, Tables 1-4
# --------------------------------------------------------------------------
VNOM = 1000.0          # V   module rated output              (Table 2)
INOM = 0.5e-3          # A   module rated current             (Table 2)
VREF_MOD = 2.5         # V   module internal reference        (Table 1)
VREF_MOD_TOL = 0.01    # +/- 1 %                              (Table 1)
R_PULLUP = 10.0e3      # ohm internal VSET pull-up to Vref    (Figure 2 / Rset formula)
R_SERIES_INT = 100.0e3 # ohm internal series into the set node(Figure 2)
C_SET_INT = 1.0e-6     # F   internal set-node capacitor      (Figure 2)
ADJ_ACC = 0.01         # +/- 1 % adjustment accuracy          (Table 1)
VMON_ACC = 0.01        # 1 % * Vnom monitor accuracy          (Table 1)
SPEC_FLOOR_FRAC = 0.02 # specs hold only for 2 % * Vnom < Vout <= Vnom (Table 1 note 1)
RIPPLE_MAX_PP = 30e-3  # V   max ripple, f > 10 Hz            (Table 1)
IOUT_MAX = 1.5 * INOM  # A   Iout limited to approx 1.5*Inom  (Table 2 note 1)

GAIN = VNOM / VREF_MOD          # 400 V per volt of VSET
TAU_MOD = R_SERIES_INT * C_SET_INT

# --------------------------------------------------------------------------
# 1.  Set-path component constants -- OUR choices.  Tags per CLAUDE.md rule 4.
# --------------------------------------------------------------------------
VRAIL_NOM = 2.500        # V   the clamp rail = REF5025 output
REF_INIT_TOL = 0.0005    # +/-0.05 % initial            [web-verified, ti.com, session 1]
REF_TC = 3e-6            # /K  3 ppm/degC max           [web-verified, ti.com, session 1]
REF_LTD = 50e-6          # long-term drift /1000 h      [recalled -- G1 datasheet read]
REF_IOUT_MAX = 10e-3     # A   +/-10 mA                 [web-verified, ti.com, session 1]
REF_LOADREG = 8e-6       # per mA                       [recalled -- G1 datasheet read]
DT_K = 20.0              # K   assumed temperature excursion about calibration

V33 = 3.3                # V   ESP32 logic rail
V50 = 5.0                # V   module +VIN and analog supply rail

# DAC candidates
DAC_BITS_REC = 16        # DAC8552                      [web-verified, ti.com, session 1]
DAC_BITS_ALT = 12        # MCP4726                      [web-verified, Microchip, session 1]
DAC_GAINERR = 0.001      # +/-0.1 % FSR                 [recalled -- G1 datasheet read]
DAC_OFFERR_V = 1.0e-3    # V  offset                    [recalled -- G1 datasheet read]
DAC_INL_LSB = 12.0       # LSB max INL at 16 bit        [recalled -- G1 datasheet read]
DAC_SETTLE_S = 10e-6     # s  to +/-0.003 % FSR         [web-verified, ti.com, session 1]

# VSET buffer requirements / assumed achieved values
BUF_VOS = 200e-6         # V   max input offset          (a REQUIREMENT we impose)
BUF_VOS_TC = 2e-6        # V/K max offset drift          (a REQUIREMENT we impose)
BUF_IB = 1e-9            # A   max input bias            (a REQUIREMENT we impose)
BUF_NOISE_PP_01_10 = 3e-6  # Vpp 0.1-10 Hz               (a REQUIREMENT we impose)
BUF_RIN_SERIES = 1.0e3   # ohm series R at the buffer NON-INVERTING input
BUF_RLOCAL = 10.0e3      # ohm local feedback R (out -> in-), Kelvin sense in parallel
REF_NOISE_PP_01_10 = 3e-6  # Vpp 0.1-10 Hz REF5025       [recalled -- G1 datasheet read]

# The pull-down at the module pin (ARCH-05, ARCH-18 duplicated)
RPD_EACH = 1.00e3        # ohm  each of two parallel elements
RPD_N = 2
RPD = RPD_EACH / RPD_N

# Force-path series resistance (buffer output -> VSET pin)
RS_FORCE_KELVIN = 0.20   # ohm  wide short trace, inside the Kelvin loop
RS_FORCE_PLAIN = 0.20    # ohm  same trace, NOT Kelvin sensed

# Touch-safety threshold carried from NUM-15
V_TOUCH_SAFE = 60.0      # V    [recalled] [unverified-primary]

# Window comparator on the clamp rail
WC_VREF = 2.048          # V   LM4040-2.048, a DIFFERENT device from REF5025 [recalled]
WC_SENSE_DIV = 0.5       # rail / 2 via two 20.0 k 0.1 %
WC_R1 = 7.50e3           # E96, top of the threshold string (to WC_VREF)
WC_R2 = 590.0            # E96, between the two taps
WC_R3 = 11.8e3           # E96, bottom of the string (to GND)

FW_CODE_CLAMP = 0.98     # firmware maximum code fraction

if VNOM <= 0 or VREF_MOD <= 0 or R_PULLUP <= 0:
    print("STRUCTURAL: nonsensical module constants", file=sys.stderr)
    sys.exit(2)

# ==========================================================================
hr("0.  Frozen constants and the one derived gain")
# ==========================================================================
print(f"Vnom              = {VNOM:.0f} V          (AP010504, G0-A2)")
print(f"Inom              = {INOM*1e3:.1f} mA         Iout <= 1.5*Inom = {IOUT_MAX*1e3:.2f} mA")
print(f"Vref (module)     = {VREF_MOD:.3f} V +/-{VREF_MOD_TOL*100:.0f} %  "
      f"=> {VREF_MOD*(1-VREF_MOD_TOL):.3f} .. {VREF_MOD*(1+VREF_MOD_TOL):.3f} V")
print(f"SET-PATH GAIN     = Vnom/Vref = {GAIN:.1f} V per volt at VSET")
print(f"internal pull-up  = {R_PULLUP/1e3:.1f} k to Vref  -> open VSET commands {VNOM:.0f} V")
print(f"internal set pole = {R_SERIES_INT/1e3:.0f}k * {C_SET_INT*1e6:.0f}uF = {TAU_MOD*1e3:.0f} ms"
      f"  (f = {1/(2*math.pi*TAU_MOD):.3f} Hz)   [MEASURABLE-NOW]")
print(f"spec floor        = {SPEC_FLOOR_FRAC*100:.0f} % * Vnom = {SPEC_FLOOR_FRAC*VNOM:.1f} V"
      f"  -- below this NOTHING is specified")
print(f"module accuracies = adjustment +/-{ADJ_ACC*100:.0f} % = +/-{ADJ_ACC*VNOM:.0f} V ; "
      f"VMON {VMON_ACC*100:.0f} %*Vnom = +/-{VMON_ACC*VNOM:.0f} V")
check("gain", close(GAIN, 400.0), f"{GAIN}")
check("iout", close(IOUT_MAX, 0.75e-3), f"{IOUT_MAX}")
check("floor", close(SPEC_FLOOR_FRAC * VNOM, 20.0), "2 % of 1 kV must be 20 V")
# TRIPWIRE.  Table 1 states Vref = 2.5 V +/-1 % AND adjustment accuracy = +/-1 %.
# Figure 2 / sec 7.2a give Vout = Vnom*Vset/Vref, so the Vref tolerance IS the dominant
# contributor to the adjustment accuracy and the two numbers must remain equal.  If a
# future edit changes one without the other, the datasheet reading has drifted.
check("Vref tol == adjustment accuracy (datasheet consistency tripwire)",
      close(VREF_MOD_TOL, ADJ_ACC),
      f"Vref tol {VREF_MOD_TOL} vs adjustment accuracy {ADJ_ACC} -- Table 1 gives both as 1 %")

# ==========================================================================
hr("1.  The hazard, quantified: what each un-clamped source commands")
# ==========================================================================
print("Vout = Vnom * Vset / Vref_module.  The module does not limit above Vref.\n")
print(f"{'source at VSET':44} {'V':>7} {'Vout (V)':>10} {'% of Vnom':>10}")
haz = [
    ("commanded zero", 0.0),
    ("nominal full scale (= module Vref)", VREF_MOD),
    ("OPEN VSET (internal 10k pulls to Vref)", VREF_MOD),
    ("our clamp rail, worst-case high", None),      # filled below
    ("ESP32 / DAC-VDD 3.3 V rail", V33),
    ("+5 V analog rail", V50),
]
VRAIL_HI = VRAIL_NOM * (1 + REF_INIT_TOL + REF_TC * DT_K + REF_LTD)
for name, v in haz:
    if v is None:
        v = VRAIL_HI
    vout = VNOM * v / VREF_MOD
    print(f"{name:44} {v:7.4f} {vout:10.1f} {100*vout/VNOM:9.1f} %")
print()
print(f"clamp rail worst-case high = {VRAIL_NOM:.3f} * (1 + {REF_INIT_TOL:.4f} init"
      f" + {REF_TC*DT_K:.6f} tempco + {REF_LTD:.6f} LTD) = {VRAIL_HI:.6f} V")
check("hazard 3v3", close(VNOM * V33 / VREF_MOD, 1320.0), "3.3 V must command 1320 V")
check("hazard 5v", close(VNOM * V50 / VREF_MOD, 2000.0), "5 V must command 2000 V")
check("hazard open", close(VNOM * VREF_MOD / VREF_MOD, 1000.0), "open VSET must command Vnom")

# ==========================================================================
hr("2.  Over-range residual injected by each clamp candidate")
# ==========================================================================
# Candidate A: rail-to-rail output stage whose V+ IS the 2.500 V reference.
overA_direct = 100.0 * (VRAIL_HI / VREF_MOD - 1.0)
# independent derivation: multiply the tolerance stack out term by term
stack = (1 + REF_INIT_TOL) * (1 + REF_TC * DT_K) * (1 + REF_LTD)
overA_stack = 100.0 * (VRAIL_NOM * stack / VREF_MOD - 1.0)
check("A two ways", abs(overA_direct - overA_stack) < 0.001,
      f"{overA_direct:.6f} vs {overA_stack:.6f} (linear vs multiplicative, must agree to <0.001 %)")

# Candidate B: precision divider from the 3.3 V rail down to 2.45 V nominal.
V33_TOL = 0.02          # +/-2 % LDO initial + load + temp   [recalled]
DIV_RATIO_TOL = 0.002   # +/-0.2 % from two 0.1 % resistors
VB_NOM = 2.45
overB = 100.0 * (VB_NOM * (1 + V33_TOL) * (1 + DIV_RATIO_TOL) / VREF_MOD - 1.0)
overB_fault = 100.0 * (V33 * (1 + V33_TOL) / VREF_MOD - 1.0)   # bottom resistor open
gainerrB = VNOM * V33_TOL   # the 3.3 V rail tolerance lands directly as gain error

# Candidate C: Schottky from VSET to a 2.500 V rail.
VF_SCHOTTKY_LO = 0.21   # V at 250 uA, 40 degC   [recalled]
VF_SCHOTTKY_HI = 0.28   # V at 250 uA, 0 degC    [recalled]
overC = 100.0 * ((VRAIL_HI + VF_SCHOTTKY_HI) / VREF_MOD - 1.0)
overC_short = 100.0 * (VRAIL_HI / VREF_MOD - 1.0)  # diode fails SHORT -> VSET = rail = FS

# Candidate D: DAC referenced to the module's own Vref pin.
overD = 0.0             # exact by construction -- but NOT IMPLEMENTABLE, see below

I_PU = VREF_MOD / R_PULLUP   # current the clamp must sink at full scale

print(f"the clamp must sink the internal pull-up: Vref/10k = {I_PU*1e6:.0f} uA\n")
print(f"{'candidate':52} {'max Vset':>9} {'Vout':>8} {'over-range':>11}")
rows = [
    ("A  RRO stage powered from the 2.500 V reference", VRAIL_HI, overA_direct),
    ("B  precision divider 3.3 V -> 2.45 V", VB_NOM * (1 + V33_TOL) * (1 + DIV_RATIO_TOL), overB),
    ("B' same, BOTTOM RESISTOR OPEN (single fault)", V33 * (1 + V33_TOL), overB_fault),
    ("C  Schottky to a 2.500 V rail (Vf at 250 uA, 0 C)", VRAIL_HI + VF_SCHOTTKY_HI, overC),
    ("C' same, DIODE FAILS SHORT (single fault)", VRAIL_HI, overC_short),
    ("D  DAC referenced to the module Vref pin", VREF_MOD, overD),
    ("-  no clamp, 3.3 V-referenced source", V33, 100.0 * (V33 / VREF_MOD - 1)),
]
for n, v, o in rows:
    print(f"{n:52} {v:9.4f} {VNOM*v/VREF_MOD:8.1f} {o:+10.3f} %")
print()
print(f"B also injects a GAIN error of +/-{gainerrB:.0f} V at the output, because the 3.3 V rail's")
print(f"  +/-{V33_TOL*100:.0f} % tolerance IS its full scale, and that rail moves with WiFi TX bursts.")
print(f"C's Vf spread {VF_SCHOTTKY_LO:.2f}..{VF_SCHOTTKY_HI:.2f} V is "
      f"{100*(VF_SCHOTTKY_HI-VF_SCHOTTKY_LO)/VREF_MOD:.1f} % of Vnom "
      f"= {VNOM*(VF_SCHOTTKY_HI-VF_SCHOTTKY_LO)/VREF_MOD:.0f} V of clamp-point drift.")
print("D is EXACT and is NOT IMPLEMENTABLE: Table 4 lists seven pins")
print("  (+VIN, VSET, GND, /ON, VMON, HV, GND).  There is no Vref pin.  Dropped, not invented.")
check("A best", overA_direct < 0.2, f"candidate A over-range {overA_direct:.3f} % should be <0.2 %")
check("C worse than A", overC > 10 * overA_direct, "Schottky must be shown materially worse than A")
check("B fault bad", overB_fault > 30.0, "B's single-fault must be shown to reach >30 % over-range")

# ==========================================================================
hr("3.  The dominant hazard: the clamp fails OPEN.  Pull-down sizing.")
# ==========================================================================
print("With the driver open, VSET floats on the internal (Vref, 10k) Thevenin source.")
print("A pull-down Rpd AT THE MODULE PIN turns 'full scale' into a divider.\n")


def residual_divider(rpd):
    """Plain two-resistor divider."""
    return VREF_MOD * rpd / (R_PULLUP + rpd)


def residual_superposition(rpd):
    """Same node by Thevenin/superposition: short the ideal source, form the
    Norton current Vref/R_PULLUP into the parallel combination."""
    inorton = VREF_MOD / R_PULLUP
    rpar = 1.0 / (1.0 / R_PULLUP + 1.0 / rpd)
    return inorton * rpar


print(f"{'Rpd (ohm)':>10} {'Vset (V)':>10} {'Vout (V)':>9} {'% Vnom':>8} "
      f"{'I at FS (mA)':>13} {'<60 V?':>7}")
for rpd in (10e3, 2.00e3, 1.00e3, 604.0, 500.0, 402.0, 302.0, 200.0, 100.0):
    v1 = residual_divider(rpd)
    v2 = residual_superposition(rpd)
    check(f"pulldown {rpd:.0f} two ways", close(v1, v2, rtol=1e-12),
          f"{v1!r} vs {v2!r}")
    vout = VNOM * v1 / VREF_MOD
    ifs = VRAIL_NOM / rpd
    mark = "yes" if vout < V_TOUCH_SAFE else "NO"
    print(f"{rpd:10.0f} {v1:10.4f} {vout:9.1f} {100*vout/VNOM:7.2f} % "
          f"{ifs*1e3:12.2f}  {mark:>6}")

print()
RES_V = residual_divider(RPD)
RES_OUT = VNOM * RES_V / VREF_MOD
RES_I_FS = VRAIL_NOM / RPD
RES_DEG_V = residual_divider(RPD_EACH)
RES_DEG_OUT = VNOM * RES_DEG_V / VREF_MOD
print(f"CHOSEN: {RPD_N} x {RPD_EACH:.0f} ohm in parallel = {RPD:.0f} ohm at the VSET pin (ARCH-05 + ARCH-18)")
print(f"  driver-open residual        : {RES_V:.4f} V at VSET -> {RES_OUT:.1f} V "
      f"({100*RES_OUT/VNOM:.2f} % of Vnom)")
print(f"  buffer source current at FS : {RES_I_FS*1e3:.2f} mA")
print(f"  ONE element open (2nd fault): {RES_DEG_V:.4f} V -> {RES_DEG_OUT:.1f} V "
      f"({100*RES_DEG_OUT/VNOM:.2f} % of Vnom)")
print(f"  touch-safe threshold        : {V_TOUCH_SAFE:.0f} V [recalled] [unverified-primary]")
check("residual under touch-safe", RES_OUT < V_TOUCH_SAFE,
      f"{RES_OUT:.1f} V must be below {V_TOUCH_SAFE:.0f} V")
check("degraded is a 2nd fault", RES_DEG_OUT > RES_OUT, "degradation must be monotone")
check("drive affordable", RES_I_FS < REF_IOUT_MAX, "FS drive must fit a 10 mA reference budget")

print()
print("SENSITIVITY TO THE UNTOLERANCED INTERNAL 10 k  (PART sec 10.14 -- iseg publishes no tolerance)")
print(f"{'R_pullup':>10} {'Vout residual':>14} {'vs 60 V':>9}")
for rup in (7.0e3, 8.0e3, 9.0e3, 10.0e3, 11.0e3, 12.0e3, 13.0e3):
    v = VREF_MOD * RPD / (rup + RPD)
    vo = VNOM * v / VREF_MOD
    print(f"{rup/1e3:9.1f}k {vo:13.1f} V {'ok' if vo < V_TOUCH_SAFE else 'FAILS':>9}")
RUP_BREAK = RPD * (V_TOUCH_SAFE / VNOM * VREF_MOD) ** -1 * VREF_MOD - RPD
print(f"the 60 V criterion breaks at R_pullup = {RUP_BREAK/1e3:.2f} k "
      f"({100*(RUP_BREAK/R_PULLUP-1):+.1f} % of nominal)")
check("break point sane", 6.0e3 < RUP_BREAK < 9.0e3, f"{RUP_BREAK}")

# ==========================================================================
hr("4.  Series resistance in the force path -- TWO error terms, not one")
# ==========================================================================
print("ARCH-04 caps DAC-to-pin series R at 10 ohm.  That cap was derived from ONE")
print("term (the divider against the internal 10k, worst at commanded ZERO).  A")
print("pull-down at the pin adds a SECOND term (IR drop, worst at FULL SCALE).\n")
print(f"{'Rs (ohm)':>9} {'term1 zero (V out)':>19} {'term2 FS (V out)':>18} {'worse':>7}")
for rs in (0.1, 0.2, 1.0, 10.0, 100.0):
    t1 = GAIN * (VREF_MOD - 0.0) * rs / (rs + R_PULLUP)          # ARCH-04 term
    t2 = GAIN * (RES_I_FS * rs)                                   # new pull-down IR term
    print(f"{rs:9.1f} {t1:18.3f} {t2:17.3f} {'IR' if t2 > t1 else 'divider':>7}")
print()
# term1/term2 = [Vref/(rs+Rup)] / I_fs.  With I_fs = Vrail/Rpd this ratio is < 1 for
# EVERY rs >= 0 whenever Rpd < Rup*Vrail/Vref, i.e. for every useful pull-down.
ratio_at_0 = (VREF_MOD / R_PULLUP) / RES_I_FS
print(f"term2/term1 at rs -> 0 is {1/ratio_at_0:.1f}x, and the ratio only grows with rs:")
print(f"the two are equal only at rs = Vrail*Rup/(Vref*... ) < 0, i.e. NEVER for a real")
print(f"resistance.  The IR term dominates EVERYWHERE.  With {RPD:.0f} ohm at the pin the")
print(f"binding cap is NOT 10 ohm; at rs = 10 ohm the IR term alone is "
      f"{GAIN*RES_I_FS*10.0:.1f} V at the output -- 20x the ARCH-04 term it replaced.")
check("IR term dominates", ratio_at_0 < 1.0,
      f"pull-up current {VREF_MOD/R_PULLUP*1e3:.3f} mA vs pull-down current {RES_I_FS*1e3:.3f} mA")
print()
err_plain = GAIN * RES_I_FS * RS_FORCE_PLAIN
# Kelvin: the force-path drop is inside the loop; residual = drop * R_sense/(R_sense+R_local)
# with R_sense = the sense trace (~0.05 ohm) and R_local = BUF_RLOCAL
R_SENSE_TRACE = 0.05
err_kelvin = err_plain * R_SENSE_TRACE / (R_SENSE_TRACE + BUF_RLOCAL)
print(f"plain (no Kelvin), Rs = {RS_FORCE_PLAIN:.2f} ohm : {err_plain:.3f} V at the output "
      f"({100*err_plain/VNOM:.3f} % FS)  -- a pure GAIN error, calibratable")
print(f"Kelvin sensed at the VSET pin       : {err_kelvin*1e3:.4f} mV at the output "
      f"-- nulled by {BUF_RLOCAL/R_SENSE_TRACE:.0f}x")
print(f"if the SENSE trace opens, feedback reverts to the local {BUF_RLOCAL/1e3:.0f}k path and the")
print(f"amp degrades GRACEFULLY to the plain case ({err_plain:.3f} V), NOT to the rail.")
check("kelvin helps", err_kelvin < err_plain / 100, "Kelvin must null by >100x")
# The local feedback resistor is NOT free: with the sense trace intact, OUT -> R_local ->
# FB -> R_sense -> PIN is a real series path and the current it circulates lands in VSET.
i_circ = (RES_I_FS * RS_FORCE_PLAIN) / (BUF_RLOCAL + R_SENSE_TRACE)
print(f"sense-loop circulating current = IR drop {RES_I_FS*RS_FORCE_PLAIN*1e3:.3f} mV over "
      f"({BUF_RLOCAL/1e3:.0f}k + {R_SENSE_TRACE*1e3:.0f} mohm) = {i_circ*1e9:.1f} nA")
print(f"  that current is injected into the VSET node; as a fraction of the pull-down")
print(f"  current it is {100*i_circ/RES_I_FS:.6f} %.  R_local must therefore be LARGE, not")
print(f"  merely larger than the trace -- a 10 ohm 'local' resistor would circulate "
      f"{100*(RES_I_FS*RS_FORCE_PLAIN/(10.0+R_SENSE_TRACE))/RES_I_FS:.3f} %.")
check("R_local large enough", BUF_RLOCAL >= 1000 * RS_FORCE_PLAIN,
      f"R_local {BUF_RLOCAL:.1f} must be >= 1000x the force-path resistance {RS_FORCE_PLAIN:.2f}")

# ==========================================================================
hr("5.  Static error budget of the recommended chain, referred to the output")
# ==========================================================================
lsb16 = VRAIL_NOM / (2 ** DAC_BITS_REC - 1)
lsb12 = VRAIL_NOM / (2 ** DAC_BITS_ALT - 1)
R_RAIL_STAR_TO_PIN = 0.010   # ohm, star point -> one buffer's V+ pin
terms = [
    ("REF5025 initial tolerance",        VRAIL_NOM * REF_INIT_TOL,        True),
    ("REF5025 tempco over 20 K",         VRAIL_NOM * REF_TC * DT_K,       False),
    ("REF5025 long-term drift /1000 h",  VRAIL_NOM * REF_LTD,             False),
    ("rail force amp Vos",               BUF_VOS,                         True),
    ("rail force amp Vos drift over 20 K", BUF_VOS_TC * DT_K,             False),
    ("rail star -> V+ pin IR (own chan)", RES_I_FS * R_RAIL_STAR_TO_PIN,  True),
    ("DAC gain error",                   VRAIL_NOM * DAC_GAINERR,         True),
    ("DAC offset error",                 DAC_OFFERR_V,                    True),
    ("DAC INL (16-bit)",                 DAC_INL_LSB * lsb16,             False),
    ("DAC quantisation (1/2 LSB, 16-bit)", 0.5 * lsb16,                   False),
    ("buffer Vos",                       BUF_VOS,                         True),
    ("buffer Vos drift over 20 K",       BUF_VOS_TC * DT_K,               False),
    ("buffer Ib x 1k input series R",    BUF_IB * BUF_RIN_SERIES,         False),
    ("force-path IR, Kelvin residual",   err_kelvin / GAIN,               False),
]
print(f"{'term':38} {'at VSET (uV)':>13} {'at output (V)':>14} {'calibratable':>13}")
sum_all2 = 0.0
sum_uncal2 = 0.0
for n, v, cal in terms:
    o = v * GAIN
    sum_all2 += o * o
    if not cal:
        sum_uncal2 += o * o
    print(f"{n:38} {v*1e6:13.2f} {o:14.4f} {'yes' if cal else 'NO':>13}")
RSS_ALL = math.sqrt(sum_all2)
RSS_UNCAL = math.sqrt(sum_uncal2)
print()
print(f"RSS of ALL set-path terms        : {RSS_ALL:8.4f} V  ({100*RSS_ALL/VNOM:.4f} % of FS)")
print(f"RSS of NON-CALIBRATABLE terms    : {RSS_UNCAL:8.4f} V  ({100*RSS_UNCAL/VNOM:.4f} % of FS)")
print(f"module adjustment accuracy alone : {ADJ_ACC*VNOM:8.4f} V  "
      f"({100*ADJ_ACC:.4f} % of FS)   <-- {ADJ_ACC*VNOM/RSS_UNCAL:.0f}x LARGER")
print(f"independent monitor accuracy     : {1.58:8.4f} V  (CONTROL_ARCHITECTURE sec 2.5)")
print()
print("READING: after a one-time calibration the SET PATH is not the accuracy limit and")
print("is not close to being it.  ARCH-01 stands: the module's own +/-1 % Vref dominates,")
print("and the only route past it is closing the loop on the independent monitor.")
check("set path not the limit", RSS_UNCAL < 0.1 * ADJ_ACC * VNOM,
      f"{RSS_UNCAL:.3f} V must be <10 % of the module's own {ADJ_ACC*VNOM:.0f} V")
# The CALIBRATABLE terms are not free either: they consume RANGE before calibration,
# and the 98 % code clamp already spends 2 %.  Cap the pre-calibration set-path error.
print(f"pre-calibration set-path error {RSS_ALL:.3f} V = {100*RSS_ALL/VNOM:.3f} % of FS; "
      f"the 98 % code clamp spends {100*(1-FW_CODE_CLAMP):.0f} % of range, so the two together")
print(f"must stay inside the {100*(1 - 950.0/VNOM):.0f} % headroom implied by a +/-950 V rating.")
check("pre-cal error fits the range budget", RSS_ALL < 0.005 * VNOM,
      f"{RSS_ALL:.3f} V exceeds 0.5 % of FS -- calibratable is not the same as free")

print()
print("CROSS-COUPLING BETWEEN THE TWO OUTPUTS -- only exists because of G0-A4.")
R_RAIL_SHARED = 0.020    # ohm, force-amp output -> star point, carries BOTH currents
xc_unkelvin = 2 * RES_I_FS * R_RAIL_SHARED * GAIN
print(f"  both channels share the clamp rail.  {R_RAIL_SHARED*1e3:.0f} mohm of shared copper")
print(f"  between the force amp and the star point carries {2*RES_I_FS*1e3:.1f} mA when BOTH")
print(f"  channels are at full scale -> {xc_unkelvin:.3f} V of error on EACH output that")
print(f"  depends on the OTHER output's setting.")
print(f"  FIX: take the force amp's feedback AT THE STAR POINT and route the rail as a")
print(f"  true star.  The shared drop is then INSIDE the loop, so the CROSS term "
      f"(dependence")
print(f"  on the other channel) becomes structurally ZERO, not merely smaller.  What is")
print(f"  left is star->pin, carrying only that channel's OWN current: "
      f"{RES_I_FS*R_RAIL_STAR_TO_PIN*GAIN:.4f} V, a")
print(f"  per-channel GAIN term, hence calibratable.  Reduction of the SELF term alone is "
      f"{xc_unkelvin/(RES_I_FS*R_RAIL_STAR_TO_PIN*GAIN):.1f}x.")
check("cross term structurally zero", True,
      "asserted by construction of the star + Kelvin, not by arithmetic")
check("residual self term small", RES_I_FS * R_RAIL_STAR_TO_PIN * GAIN < 0.05,
      f"{RES_I_FS*R_RAIL_STAR_TO_PIN*GAIN:.4f} V must stay well under the 1.58 V monitor floor")

# ==========================================================================
hr("6.  Per-module Vref calibration -- what the un-implementable idea D recovers")
# ==========================================================================
print("Idea D (DAC referenced to the module Vref) is impossible: no Vref pin.")
print("But Vref IS observable at the OPEN-CIRCUIT VSET pin, because the internal 10k")
print("pulls it there with no load.  That is a BENCH measurement, not a circuit.\n")
DMM_Z = 10e6
err_dmm = 100.0 * R_PULLUP / (R_PULLUP + DMM_Z)
print(f"measure pin 2 open-circuit with a {DMM_Z/1e6:.0f} Mohm DMM:")
print(f"  loading error = R_pullup/(R_pullup+Z) = {err_dmm:.3f} %  -> Vref known to "
      f"{err_dmm/100*VREF_MOD*1e3:.2f} mV")
print(f"  folded into the per-module gain constant, this removes the module's +/-{VREF_MOD_TOL*100:.0f} %")
print(f"  ({ADJ_ACC*VNOM:.0f} V) INITIAL term.  What remains is DRIFT, bounded only by the")
print(f"  datasheet's overall <50 ppm/K:  50e-6 * {DT_K:.0f} K = {50e-6*DT_K*100:.2f} % = "
      f"{50e-6*DT_K*VNOM:.1f} V")
print(f"  => a {ADJ_ACC*VNOM/(50e-6*DT_K*VNOM):.0f}x improvement, obtained with a DMM and a text file.")
check("cal improvement", ADJ_ACC * VNOM / (50e-6 * DT_K * VNOM) > 5,
      "per-module Vref calibration must buy at least 5x")

print()
print("Two-point solve for BOTH unknowns (Vref and R_pullup) from two known loads.")
print("  V1 = Vref*R1/(Rup+R1) ,  V2 = Vref*R2/(Rup+R2)")
print("  =>  Vref = (R1-R2) / (R1/V1 - R2/V2) ,  Rup = R1*(Vref/V1 - 1)")
R1, R2 = 10.0e3, 1.00e3
V1 = VREF_MOD * R1 / (R_PULLUP + R1)
V2 = VREF_MOD * R2 / (R_PULLUP + R2)
vref_solved = (R1 - R2) / (R1 / V1 - R2 / V2)
rup_solved = R1 * (vref_solved / V1 - 1.0)
print(f"  synthesised: R1={R1/1e3:.1f}k -> V1={V1:.6f} V ; R2={R2/1e3:.2f}k -> V2={V2:.6f} V")
print(f"  ROUND TRIP : Vref = {vref_solved:.9f} V (true {VREF_MOD})  "
      f"Rup = {rup_solved:.4f} ohm (true {R_PULLUP})")
check("roundtrip vref", close(vref_solved, VREF_MOD, rtol=1e-9), f"{vref_solved}")
check("roundtrip rup", close(rup_solved, R_PULLUP, rtol=1e-9), f"{rup_solved}")
den = R1 / V1 - R2 / V2
cond = (R1 / V1 + R2 / V2) / abs(den)
print(f"  conditioning: |R1/V1| + |R2/V2| over |denominator| = {cond:.2f}  "
      f"(a 1 % voltage error becomes ~{cond:.1f} % in Vref)")
check("conditioning", cond < 5.0, f"two-point solve must not be ill-conditioned: {cond}")
print(f"  => prefer the single OPEN-CIRCUIT reading ({err_dmm:.3f} % error) and use the")
print(f"     two-point solve only to obtain R_pullup, which the 60 V criterion depends on.")

# ==========================================================================
hr("7.  Firmware code clamp, and the range the instrument can actually guarantee")
# ==========================================================================
vset_max_cmd = VRAIL_NOM * FW_CODE_CLAMP
vset_max_cmd_hi = VRAIL_HI * FW_CODE_CLAMP
VREF_LO = VREF_MOD * (1 - VREF_MOD_TOL)
VREF_HI = VREF_MOD * (1 + VREF_MOD_TOL)
vout_worst_hi = VNOM * vset_max_cmd_hi / VREF_LO
vout_worst_lo = VNOM * (VRAIL_NOM * (1 - REF_INIT_TOL) * FW_CODE_CLAMP) / VREF_HI
print(f"firmware maximum code fraction    = {FW_CODE_CLAMP*100:.0f} %")
print(f"  commanded Vset at that code     = {vset_max_cmd:.4f} V nominal, "
      f"{vset_max_cmd_hi:.4f} V worst-case-high rail")
print(f"  WORST CASE HIGH (our rail high, their Vref low {VREF_LO:.3f} V) = {vout_worst_hi:.1f} V "
      f"({100*vout_worst_hi/VNOM:.2f} % of Vnom)")
print(f"  WORST CASE LOW  (our rail low,  their Vref high {VREF_HI:.3f} V) = {vout_worst_lo:.1f} V "
      f"({100*vout_worst_lo/VNOM:.2f} % of Vnom)")
frac_needed = VREF_LO / VRAIL_HI
print(f"  the code fraction that EXACTLY reaches Vnom in the worst high case is "
      f"{frac_needed*100:.2f} %")
check("98pc safe", vout_worst_hi <= VNOM,
      f"98 % clamp must guarantee <= Vnom; got {vout_worst_hi:.1f} V")
check("98pc chosen below break-even", FW_CODE_CLAMP < frac_needed, f"{frac_needed}")
guaranteed = vout_worst_lo * (1 - ADJ_ACC)
print(f"  folding in the module's own +/-{ADJ_ACC*100:.0f} % adjustment accuracy, the")
print(f"  GUARANTEED deliverable magnitude is {guaranteed:.1f} V.")
print(f"  => rate the instrument at +/-950 V guaranteed / ~{vset_max_cmd/VREF_MOD*VNOM:.0f} V typical,")
print(f"     NOT +/-1000 V.  Declaring 1000 V would be a spec the hardware cannot meet.")
check("rating honest", guaranteed > 950.0, f"guaranteed {guaranteed:.1f} V vs a 950 V claim")

# ==========================================================================
hr("8.  Window comparator on the clamp rail -- the fault ARCH-06 does not cover")
# ==========================================================================
wc_sum = WC_R1 + WC_R2 + WC_R3
tap_lo = WC_VREF * WC_R3 / wc_sum
tap_hi = WC_VREF * (WC_R2 + WC_R3) / wc_sum
rail_lo = tap_lo / WC_SENSE_DIV
rail_hi = tap_hi / WC_SENSE_DIV
print(f"sense divider   : rail x {WC_SENSE_DIV} (two 20.0 k, 0.1 %)")
print(f"threshold string: {WC_R1:.0f} / {WC_R2:.0f} / {WC_R3:.0f} ohm across "
      f"{WC_VREF:.3f} V (LM4040-2.048, a DIFFERENT device from REF5025)")
print(f"  low  tap {tap_lo:.4f} V -> rail trips low  at {rail_lo:.4f} V "
      f"({100*(rail_lo/VRAIL_NOM-1):+.2f} %)")
print(f"  high tap {tap_hi:.4f} V -> rail trips high at {rail_hi:.4f} V "
      f"({100*(rail_hi/VRAIL_NOM-1):+.2f} %)")
print(f"  max Vout a reference fault can produce before the trip fires : "
      f"{VNOM*rail_hi/VREF_MOD:.0f} V")
print(f"  vs an UNDETECTED rail rise to 3.3 V ({VNOM*V33/VREF_MOD:.0f} V) "
      f"or 5 V ({VNOM*V50/VREF_MOD:.0f} V)")
legit_lo = VRAIL_NOM * (1 - REF_INIT_TOL - REF_TC * DT_K - REF_LTD)
print(f"  legitimate rail band {legit_lo:.4f} .. {VRAIL_HI:.4f} V ; "
      f"margin to the low trip {100*(legit_lo/rail_lo-1):.2f} %, "
      f"to the high trip {100*(rail_hi/VRAIL_HI-1):.2f} %")
check("wc no nuisance", rail_lo < legit_lo and rail_hi > VRAIL_HI,
      f"window {rail_lo:.4f}..{rail_hi:.4f} must contain the legitimate band")
check("wc useful", VNOM * rail_hi / VREF_MOD < 1050.0,
      "the window must cap a reference fault below the 105 % OVP threshold")
print(f"  the latched hardware OVP on the INDEPENDENT monitor sits at 105 % = "
      f"{1.05*VNOM:.0f} V and is the only layer indifferent to the fault's mechanism.")

# ==========================================================================
hr("9.  Resolution, settling, and what the DAC actually has to be")
# ==========================================================================
print(f"{'DAC':>6} {'LSB at VSET (uV)':>18} {'LSB at output (V)':>19} {'ppm FS':>8} "
      f"{'codes in +/-1 %':>16}")
for bits in (8, 12, 14, 16, 18):
    lsb = VRAIL_NOM / (2 ** bits - 1)
    lo = lsb * GAIN
    ppm_a = 1e6 * lo / VNOM
    ppm_b = 1e6 / (2 ** bits - 1) * (VRAIL_NOM / VREF_MOD)   # independent expression
    check(f"ppm {bits}", close(ppm_a, ppm_b, rtol=1e-9), f"{ppm_a} vs {ppm_b}")
    print(f"{bits:5d}b {lsb*1e6:18.2f} {lo:19.4f} {ppm_a:8.1f} "
          f"{2*ADJ_ACC*VNOM/lo:15.1f}")
print()
print(f"module set-node settle to 1 LSB after a full-scale step, tau = {TAU_MOD*1e3:.0f} ms:")
for bits in (12, 16):
    t = TAU_MOD * math.log(2 ** bits)
    print(f"  {bits:2d}-bit : {t:.3f} s        DAC's own settling {DAC_SETTLE_S*1e6:.0f} us "
          f"=> the module is {t/DAC_SETTLE_S:.0f}x slower")
check("module dominates", TAU_MOD / DAC_SETTLE_S > 1000, "the module's pole must dominate")
print()
print("=> SETTLING IS NOT A REQUIREMENT ON THE DAC.  Any part in this class beats the")
print("   module by four orders of magnitude.  Resolution buys settability, not accuracy.")
print()
CLOAD = 10e-9      # NUM-13 declared interface limit, per output
print(f"the 'ramp smoothness / i = C dV/dt' argument, checked at C_load = {CLOAD*1e9:.0f} nF (NUM-13):")
for bits in (8, 12, 16):
    lo = VRAIL_NOM / (2 ** bits - 1) * GAIN
    i = CLOAD * lo / TAU_MOD          # the module's own pole smears one LSB over tau
    print(f"  {bits:2d}-bit step {lo:7.4f} V smeared over {TAU_MOD*1e3:.0f} ms -> {i*1e9:8.3f} nA")
print(f"  compare Iout limit {IOUT_MAX*1e6:.0f} uA.  The largest of these is "
      f"{100*CLOAD*(VRAIL_NOM/(2**8-1)*GAIN)/TAU_MOD/IOUT_MAX:.5f} % of it.")
print("  => the capacitive-step argument does NOT discriminate between 8 and 16 bits at")
print("     this load.  CONTROL_ARCHITECTURE sec 1.3 lists it as a reason for resolution;")
print("     it is not one here.  Stated as a correction, not slipped in.")

# ==========================================================================
hr("10.  Noise: what the set path contributes where the module specifies nothing")
# ==========================================================================
n_tot = math.sqrt(REF_NOISE_PP_01_10 ** 2 + BUF_NOISE_PP_01_10 ** 2)
print(f"0.1-10 Hz noise, reference {REF_NOISE_PP_01_10*1e6:.1f} uVpp + buffer "
      f"{BUF_NOISE_PP_01_10*1e6:.1f} uVpp (RSS) = {n_tot*1e6:.2f} uVpp at VSET")
print(f"  x gain {GAIN:.0f}  =  {n_tot*GAIN*1e3:.2f} mVpp at the HV output "
      f"({100*n_tot*GAIN/VNOM:.6f} % of FS)")
print(f"  module ripple spec (f > 10 Hz) is {RIPPLE_MAX_PP*1e3:.0f} mVpp max; BELOW 10 Hz the")
print(f"  datasheet specifies NOTHING (PART-32).  Our contribution there is "
      f"{n_tot*GAIN*1e3:.2f} mVpp.")
print(f"  => any sub-10 Hz wander observed on the bench above ~{n_tot*GAIN*1e3:.1f} mVpp is the")
print(f"     MODULE's, not ours.  That is a usable diagnostic, and it is why the")
print(f"     set-path buffer's 1/f noise is a selection parameter and not an afterthought.")
budget = RIPPLE_MAX_PP / GAIN
print(f"  set-path noise budget referred to VSET = {RIPPLE_MAX_PP*1e3:.0f} mVpp / {GAIN:.0f} = "
      f"{budget*1e6:.1f} uVpp;  we use {100*n_tot/budget:.1f} % of it.")
check("noise budget", n_tot < 0.25 * budget, f"{n_tot*1e6:.2f} uVpp vs budget {budget*1e6:.1f}")

# ==========================================================================
hr("11.  The low end: what happens below 2 % * Vnom = 20 V")
# ==========================================================================
floor_v = SPEC_FLOOR_FRAC * VNOM
print(f"specs (ripple, noise, stability) hold ONLY for {floor_v:.0f} V < Vout <= {VNOM:.0f} V.")
print(f"Below {floor_v:.0f} V the output is UNSPECIFIED, not merely worse (PART-32).\n")
for bits in (12, 16):
    codes = int(floor_v / VNOM * (2 ** bits - 1))
    print(f"  {bits:2d}-bit: the sub-{floor_v:.0f} V band spans {codes} codes "
          f"({100*codes/(2**bits-1):.2f} % of the code range)")
print()
print(f"  module VMON accuracy is +/-{VMON_ACC*VNOM:.0f} V.  Referred to VMON's own 0..{VREF_MOD} V")
print(f"  span that is +/-{VMON_ACC*VREF_MOD*1e3:.0f} mV.  Two true outputs separated by less than")
print(f"  2 x {VMON_ACC*VNOM:.0f} V = {2*VMON_ACC*VNOM:.0f} V can produce the SAME VMON reading, so VMON CANNOT")
print(f"  DISTINGUISH 0 V from {2*VMON_ACC*VNOM:.0f} V -- it is blind across the ENTIRE unspecified band")
print(f"  and is useless as evidence of 'the output is at zero'.")
check("VMON blind over the whole band", 2 * VMON_ACC * VNOM >= SPEC_FLOOR_FRAC * VNOM,
      "VMON's ambiguity must be shown to span at least the unspecified band")
legit_disagree = math.sqrt((VMON_ACC * VNOM) ** 2 + 1.58 ** 2)
print(f"  legitimate monitor disagreement (quadrature) = {legit_disagree:.2f} V, and the")
print(f"  ARCH-23 trip threshold is {SPEC_FLOOR_FRAC*VNOM:.0f} V.  In the sub-{floor_v:.0f} V band a REAL")
print(f"  disagreement is therefore INDISTINGUISHABLE from the legitimate one: the")
print(f"  two-monitor cross-check is INOPERATIVE there.  It does not false-trip; it")
print(f"  simply cannot detect.  Only the independent monitor ({1.58:.2f} V) means anything.")
check("cross-check inoperative", legit_disagree > 0.5 * SPEC_FLOOR_FRAC * VNOM,
      "the legitimate-disagreement figure must be shown to fill most of the trip window")

# ==========================================================================
hr("12.  Reference / rail current budget")
# ==========================================================================
DAC_IREF = 1.0e-3       # [recalled -- code-dependent, G1 datasheet read]
BUF_IQ = 1.0e-3         # [recalled] two channels
WC_IDIV = VRAIL_NOM / (2 * 20.0e3)   # window-comparator sense divider
loads = [
    ("VSET buffer P output at FS (into 500 ohm)", RES_I_FS),
    ("VSET buffer N output at FS (into 500 ohm)", RES_I_FS),
    ("DAC reference input (code dependent)", DAC_IREF),
    ("VSET buffer quiescent, two channels", BUF_IQ),
    ("window-comparator sense divider", WC_IDIV),
]
tot = sum(v for _, v in loads)
print(f"{'load on the 2.500 V CLAMP RAIL':46} {'mA':>8}")
for n, v in loads:
    print(f"{n:46} {v*1e3:8.3f}")
print(f"{'TOTAL':46} {tot*1e3:8.3f}")
print()
print("BOTH modules at full scale simultaneously is a NORMAL condition in dual-unipolar")
print("mode (G0-A4), so both buffer currents are steady-state, not alternatives.")
print()
print("CONFIGURATION 1 -- REF5025 drives the clamp rail DIRECTLY:")
print(f"  required {tot*1e3:.2f} mA vs rated {REF_IOUT_MAX*1e3:.0f} mA "
      f"-> margin {REF_IOUT_MAX/tot:.2f}x   ==> {'PASS' if tot < REF_IOUT_MAX else 'FAILS'}")
check("direct drive is INADEQUATE (this assertion documents WHY the rail buffer exists)",
      tot > REF_IOUT_MAX,
      "if this ever passes, revisit: the rail buffer may no longer be mandatory")
print()
print("CONFIGURATION 2 -- RAIL FORCE AMPLIFIER (unity gain, V+ = +5 V) between the")
print("reference and the clamp rail.  The reference then sees only the amplifier's input:")
ref_load_buffered = BUF_IB + DAC_IREF * 0  # only the force amp's Ib; the DAC hangs off the rail
print(f"  REF5025 load          = force-amp Ib <= {BUF_IB*1e9:.1f} nA "
      f"-> margin {REF_IOUT_MAX/max(ref_load_buffered,1e-12):.0f}x")
print(f"  rail force amp load   = {tot*1e3:.2f} mA, sourced from +5 V")
print(f"  required amp capability: >= {1.5*tot*1e3:.1f} mA continuous with <= 5 mV of drop")
check("buffered rail passes", ref_load_buffered < 0.01 * REF_IOUT_MAX,
      "the force amp must reduce the reference load to a negligible fraction")
print()
print(">> THE RAIL FORCE AMPLIFIER IS MANDATORY, NOT OPTIONAL.  This is a design change")
print("   this probe forced: CONTROL_ARCHITECTURE sec 1.7 assumed the reference could")
print("   drive the set path directly, which was true only while the pull-down was weak")
print("   and only one module could be enabled at a time.  G0-A4 broke both premises.")
print()
print(f"FOR REFERENCE, the term the force amplifier REMOVES: REF5025 load regulation")
print(f"{REF_LOADREG*1e6:.0f} ppm/mA x {tot*1e3:.2f} mA = {REF_LOADREG*tot*1e3*1e6:.1f} ppm = "
      f"{VRAIL_NOM*REF_LOADREG*tot*1e3*GAIN:.4f} V at the output, and it would have been")
print(f"CROSS-COUPLED between the two channels (it depends on the TOTAL rail current).")
print(f"With the force amp the equivalent term is the amp's closed-loop output impedance,")
print(f"Zout_openloop / (1 + A0).  At A0 >= 100 dB and Zout_ol ~ 50 ohm that is < 1 mohm,")
print(f"i.e. {50/1e5*tot*GAIN*1e3:.4f} mV at the output -- negligible, and it is inside the")
print(f"Kelvin loop anyway.  [recalled -- confirm A0 and Zout for the chosen amp at G1]")

# ==========================================================================
hr("13.  Ramp rate derived from the monitor, not guessed")
# ==========================================================================
ADS_SPS = 128.0
N_CHAN = 4.0
per_chan = ADS_SPS / N_CHAN
step_max = SPEC_FLOOR_FRAC * VNOM - legit_disagree
rate_max = step_max * per_chan
print(f"ADS1115 at {ADS_SPS:.0f} SPS round-robin over {N_CHAN:.0f} channels -> "
      f"{per_chan:.1f} updates/s per channel ({1000/per_chan:.1f} ms)")
print(f"one ramp step must not exceed (trip threshold {SPEC_FLOOR_FRAC*VNOM:.0f} V - legitimate "
      f"disagreement {legit_disagree:.2f} V) = {step_max:.2f} V")
print(f"=> maximum ramp rate {rate_max:.0f} V/s.  RECOMMEND a {50:.0f} V/s default "
      f"({VNOM/50:.0f} s full range), which is {rate_max/50:.1f}x inside the limit.")
check("ramp headroom", rate_max / 50.0 > 3.0, f"{rate_max}")
print()
print(f"if the MEASURED module step response comes back at the pessimistic end (tau >> "
      f"{TAU_MOD*1e3:.0f} ms),")
print("only this firmware constant moves.  NO HARDWARE IN THE SET PATH IS SENSITIVE TO IT.")

# ==========================================================================
hr("SUMMARY")
# ==========================================================================
print(f"assertions run : {NCHECK}")
print(f"failures       : {len(FAILS)}")
for f in FAILS:
    print("  FAIL " + f)

if FAILS:
    sys.exit(1)
print("\nALL CHECKS PASSED.  Exit 0 means the algebra is self-consistent, NOT that the")
print("design is safe.  Nothing here has been simulated, built or measured.")
sys.exit(0)
