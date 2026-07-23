#!/usr/bin/env python3
"""Arithmetic behind docs/design/COMBINER_DESIGN.md.  stdlib only, zero-arg, deterministic."""
import math

Vnom   = 1000.0          # V   [ISEG] AP010504
Inom   = 500e-6          # A
Ilim   = 1.5 * Inom      # A   PART-13
Vsafe  = 10.0            # V   cold-switch / arm threshold  (ARCH / CONTROL_ARCH 5.2)
Vtouch = 60.0            # V   NUM-15 [unverified-primary]

MEG = 1e6
def pct(i): return 100.0 * i / Inom

print("== 1. standing load per module ==")
R_mod_bleed  = 40*MEG      # module-side bleed, 2 x 80M parallel
R_out_bleed  = 40*MEG      # output-node bleed, 2 x 80M parallel
R_mon        = 200*MEG     # invariant-(c) divider top leg  (NUMBERS_PROBE 4.1)
R_cold       = 500*MEG     # COLD permissive divider top leg (C-2, separate string)
R_branch     = 1000*MEG    # per-branch (module-side) monitor, F-2
R_X = R_M    = 400*MEG     # mode-switch stub bleeds

def load(items):
    tot = 0.0
    for name, R in items:
        i = Vnom / R
        tot += i
        print(f"    {name:34s} {R/MEG:7.0f} Mohm  {i*1e6:6.2f} uA  {pct(i):5.2f} %")
    print(f"    {'TOTAL':34s} {'':7s}       {tot*1e6:6.2f} uA  {pct(tot):5.2f} %"
          f"   -> load gets {(Inom-tot)*1e6:.0f} uA = {100-pct(tot):.1f} %")
    return tot

print("  POS module -> OUT_A  (either mode):")
lp = load([("module-side bleed", R_mod_bleed), ("branch monitor", R_branch),
           ("OUT_A output bleed", R_out_bleed), ("OUT_A monitor divider", R_mon),
           ("OUT_A COLD divider", R_cold)])
print("  NEG module -> OUT_A  (pseudo-bipolar; adds the two mode-switch stubs):")
ln = load([("module-side bleed", R_mod_bleed), ("branch monitor", R_branch),
           ("node X stub bleed", R_X), ("node M stub bleed", R_M),
           ("OUT_A output bleed", R_out_bleed), ("OUT_A monitor divider", R_mon),
           ("OUT_A COLD divider", R_cold)])
print("  NEG module -> OUT_B  (unipolar; node M is grounded, so only X loads):")
lu = load([("module-side bleed", R_mod_bleed), ("branch monitor", R_branch),
           ("node X stub bleed", R_X), ("OUT_B output bleed", R_out_bleed),
           ("OUT_B monitor divider", R_mon), ("OUT_B COLD divider", R_cold)])
worst = max(lp, ln, lu)
print(f"  worst standing load = {pct(worst):.2f} % of Inom   (budget 15 %)  "
      f"{'PASS' if pct(worst) < 15 else 'FAIL'}")

print()
print("== 2. discharge ==")
def par(*R): return 1.0/sum(1.0/r for r in R)
C_board, C_mod, C_cable2m, C_cable10m = 20e-12, 1e-9, 200e-12, 1000e-12
scen = {"bare board":            C_board,
        "2 m SHV, no load":      C_board + C_cable2m,
        "2 m SHV + 1 nF load":   C_board + C_cable2m + 1e-9,
        "10 m SHV + 10 nF load": C_board + C_cable10m + 10e-9}
R_relay_closed = par(R_mod_bleed, R_out_bleed, R_mon, R_cold, R_branch)
R_relay_open   = par(R_out_bleed, R_mon, R_cold)
R_one_string_open = par(80*MEG, R_mon, R_cold)
print(f"  R(node, relay CLOSED, module C included) = {R_relay_closed/MEG:.2f} Mohm")
print(f"  R(node, relay OPEN)                      = {R_relay_open/MEG:.2f} Mohm")
print(f"  R(node, relay OPEN, one bleed string open) = {R_one_string_open/MEG:.2f} Mohm")
for name, C in scen.items():
    for tag, R, Cx in (("closed", R_relay_closed, C + C_mod), ("open", R_relay_open, C),
                       ("open/1-string-open", R_one_string_open, C)):
        tau = R * Cx
        t60 = tau * math.log(Vnom / Vtouch)
        t10 = tau * math.log(Vnom / Vsafe)
        print(f"    {name:22s} {tag:19s} tau={tau*1e3:7.1f} ms  "
              f"->60V {t60:6.3f} s  ->10V {t10:6.3f} s")

print()
print("== 3. pseudo-bipolar changeover dead-band ==")
tau_nom  = R_relay_closed * (C_board + C_cable2m + C_mod)
tau_wrst = R_relay_closed * (C_board + C_cable10m + 10e-9 + C_mod)
T1n = tau_nom  * math.log(Vnom/Vsafe)
T1w = tau_wrst * math.log(Vnom/Vsafe)
T2  = 0.010          # +VIN load switch off, /ON high
Tdw = 0.500          # hardware monostable, covers K_S 8 ms + reed 12 ms + settle
T78n, T78w = 0.150+0.460, 0.150+0.690   # module restart + 4.6/6.9 tau of the 100 ms set node
print(f"  T1 decay to {Vsafe:.0f} V   nominal {T1n*1e3:7.1f} ms   worst {T1w*1e3:7.1f} ms")
print(f"  T2 disable            {T2*1e3:7.1f} ms")
print(f"  T_dwell (hw '123)     {Tdw*1e3:7.1f} ms")
print(f"  T7+T8 restart+settle  {T78n*1e3:7.1f} ms   worst {T78w*1e3:7.1f} ms")
print(f"  TOTAL                 {(T1n+T2+Tdw+T78n):7.3f} s   worst {(T1w+T2+Tdw+T78w):7.3f} s")

print()
print("== 4. make-current margins ==")
for name, V, R in (("K1/K2 hot make via R_S, 1 kV", 1000.0, 10e3),
                   ("K1/K2 hot make via R_S, 2 kV fault", 2000.0, 10e3),
                   ("mode-switch make via R_M1, 2 kV", 2000.0, 10e3),
                   ("S3 grounding make via R_G, 1 kV", 1000.0, 10e3)):
    I = V/R
    print(f"  {name:36s} I_pk = {I*1e3:6.1f} mA   vs 3.0 A switch rating -> {3.0/I:5.1f}x")
print(f"  static drop across R_S at Ilim   = {Ilim*10e3:.1f} V = {100*Ilim*10e3/Vnom:.2f} % of Vnom")
print(f"  static drop R_S + R_M1 (NEG, PB) = {Ilim*20e3:.1f} V = {100*Ilim*20e3/Vnom:.2f} % of Vnom")

print()
print("== 5. coil / rail budget  [verified-artifact Pickering 67 datasheet] ==")
coil = {"67-1-C-5/5D": (5.0, 40.0), "67-1-C-12/5D": (12.0, 150.0), "67-1-C-24/5D": (24.0, 600.0)}
for k, (V, R) in coil.items():
    print(f"  {k:14s} {V:4.0f} V {R:5.0f} ohm -> {V/R*1e3:6.1f} mA, {V*V/R:5.3f} W")
I5 = 2*5.0/40.0
print(f"  two Form-C coils on 5 V (unipolar mode, both closed) = {I5*1e3:.0f} mA")
rail = {"2 x module loaded": 0.360, "ESP32 500 mA via 85% buck": 0.3882,
        "analog (2 refs, 2 DACs, buffers, 2 ADCs, comparators)": 0.060,
        "K1+K2 Form-C coils (5 V, 40 ohm each)": I5, "K_S interlock relay coil": 0.036}
tot = sum(rail.values())
for k, v in rail.items(): print(f"    {k:56s} {v*1e3:7.1f} mA")
print(f"    {'TOTAL 5 V':56s} {tot*1e3:7.1f} mA   -> supply at 2.0x = {tot*2:.2f} A")

print()
print("== 6. COLD window comparator ==")
Rt_cold, Rb_cold = 500*MEG, 1.0*MEG
ratio = (Rt_cold + Rb_cold) / Rb_cold
print(f"  COLD divider ratio {ratio:.1f}:1 ; {Vsafe:.0f} V -> {Vsafe/ratio*1e3:.2f} mV ; "
      f"{Vnom:.0f} V -> {Vnom/ratio:.3f} V")
for Voff in (1e-3, 3.5e-3):
    print(f"    comparator offset {Voff*1e3:.1f} mV  -> threshold uncertainty "
          f"{Voff*ratio:.2f} V at the HV node")
print(f"  one of the two parallel top strings open -> ratio doubles -> COLD asserts up to "
      f"{2*Vsafe:.0f} V, still a cold switch")
