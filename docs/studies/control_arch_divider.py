#!/usr/bin/env python3
"""Corrected divider analysis after the Yageo RC + Caddock USVD + Vishay CRHV datasheet reads."""
import math

CFG = [  # name, Vnom, Inom, family
 ("AP002255x05", 200, 2.5e-3, "0.5 W"), ("AP004125x05", 400, 1.2e-3, "0.5 W"),
 ("AP006804x05", 600, 0.8e-3, "0.5 W"), ("AP008604x05", 800, 0.6e-3, "0.5 W"),
 ("AP010504x05",1000, 0.5e-3, "0.5 W"),
 ("AP002505x12", 200, 5.0e-3, "1 W"),   ("AP004255x12", 400, 2.5e-3, "1 W"),
 ("AP006165x12", 600, 1.6e-3, "1 W"),   ("AP008125x12", 800, 1.2e-3, "1 W"),
 ("AP010105x12",1000, 1.0e-3, "1 W"),
]
def hr(t): print(); print('='*len(t)); print(t); print('='*len(t))

hr("A. Divider loading, Caddock USVD (RT = 20 Mohm max) vs Vishay CRHV string (200 Mohm)")
print(f"{'module':>13} {'fam':>6} {'Vnom':>6} {'Inom':>8} | {'USVD 20M':>9} {'%Inom':>7} {'ok?':>4} | {'CRHV 200M':>10} {'%Inom':>7} {'ok?':>4}")
LIM = 1.0   # % of Inom we are willing to spend on the monitor
for nm,vn,inom,fam in CFG:
    i20 = vn/20e6; i200 = vn/200.2e6
    p20, p200 = i20/inom*100, i200/inom*100
    print(f"{nm:>13} {fam:>6} {vn:5d}V {inom*1e3:6.2f}mA | {i20*1e6:7.2f}uA {p20:6.2f}% {'OK' if p20<=LIM else 'NO':>4} |"
          f" {i200*1e6:8.3f}uA {p200:6.2f}% {'OK' if p200<=LIM else 'NO':>4}")
print(f"\n  criterion: monitor may draw <= {LIM}% of Inom")

hr("B. Recommended divider, +-1 kV worst case (Vishay CRHV top leg)")
R1 = 200e6; R2 = R3 = 402e3
G1,G2,G3 = 1/R1,1/R2,1/R3; SG=G1+G2+G3
ratio, vmid, zs = G1/SG, 2.5*G3/SG, 1/SG
print(f"  top leg  R1 = 2 x 100 Mohm Vishay CRHV1206 (3000 V, +-1%, 100 ppm/K)  = {R1/1e6:.0f} Mohm")
print(f"  bottom   R2 = R3 = {R2/1e3:.0f} kohm 0.1% thin film (25 ppm/K); R2->GND, R3->+2.500 V")
print(f"  ratio {ratio:.6e} (1:{1/ratio:.1f}) | tap {vmid:.4f} V at HV=0 | +-{1000*ratio:.4f} V for +-1 kV")
print(f"  Zsource at tap = {zs/1e3:.1f} kohm")
print(f"  volts per CRHV element at 1 kV = {1000/2:.0f} V  (rating 3000 V -> {3000/(1000/2):.0f}x margin)")
print(f"  dissipation per CRHV element   = {1000**2/R1/2*1e3:.3f} mW (rating 300 mW -> {300/(1000**2/R1/2*1e3):.0f}x margin)")
print("  => with an HV-rated part the string collapses from 14 chips to 2. Voltage rating, not power,")
print("     was always the binding constraint; buying the rating directly is cheaper than buying it in series.")

hr("C. Why NOT a string of standard Yageo RC chips (datasheet-verified)")
print("  RC series max working voltage: 0201 25V 0402 50V 0603 50V 0805 150V 1206 200V 1210 200V 2010 200V 2512 200V")
print("  -> 2010/2512 give NO voltage benefit over 1206. Going bigger buys power, not volts.")
for vn in (200,400,600,800,1000):
    print(f"    {vn:4d} V FS: 1206 @200V -> {math.ceil(vn/200):2d} min / {math.ceil(vn/100):2d} at 2x derate;"
          f"  0805 @150V -> {math.ceil(vn/150):2d} min / {math.ceil(vn/75):2d} at 2x derate")
print("  RC series E96 (+-1%) resistance range tops out at 2.2 Mohm.")
print(f"  -> a 200 Mohm top leg from +-1% RC parts needs >= {math.ceil(200e6/2.2e6)} resistors in series. Not a design.")
print("  RC series life drift: +-(1% + 0.05 ohm) after 1000 h at RCWV; moisture 1000 h +-0.5%.")
print("  -> a thick-film RC string drifts ~1%, i.e. as badly as the module's own 1%*Vnom monitor. Defeats the purpose.")

hr("D. Monitor accuracy budget, corrected parts")
terms = [
 ("CRHV top leg TCR 100 ppm/K vs bottom 25 ppm/K, dT=20 K", (100-25)*20/1e4),
 ("CRHV voltage coefficient, assume 1 ppm/V @ 500 V/element", 1*500/1e4),
 ("R2/R3 thin-film ratio 0.1%",                    0.10),
 ("OPA192 Vos 25 uV max / 1.004 V FS",             25e-6/1.004*100),
 ("OPA192 Ib 20 pA max x 201 kohm / 1.004 V",      20e-12*201e3/1.004*100),
 ("ADS1115 gain error 0.15% max",                  0.15),
 ("ADS1115 INL 1 LSB (62.5 uV) / 1.004 V",         62.5e-6/1.004*100),
 ("REF5025 initial 0.05% (affects the offset leg)",0.05),
]
tot=sum(p for _,p in terms); rss=math.sqrt(sum(p*p for _,p in terms))
for n,p in terms: print(f"  {n:56} {p:7.4f} %")
print(f"  {'--- worst-case sum':56} {tot:7.4f} % = {tot*10:6.2f} V at 1 kV")
print(f"  {'--- RSS':56} {rss:7.4f} % = {rss*10:6.2f} V at 1 kV")
drift = [t for t in terms if 'TCR' in t[0] or 'coefficient' in t[0] or 'Vos' in t[0] or 'Ib' in t[0] or 'INL' in t[0]]
d = math.sqrt(sum(p*p for _,p in drift))
print(f"  {'--- RSS after 2-point calibration (drift terms only)':56} {d:7.4f} % = {d*10:6.2f} V at 1 kV")
print(f"  {'--- plus CRHV long-term stability <0.5% (recalibrate!)':56} {0.5:7.4f} % = {5.0:6.2f} V at 1 kV")
print(f"\n  module VMON accuracy for comparison: 1%*Vnom = 10.00 V")
print(f"  -> calibrated monitor is {10/(d*10):.0f}x tighter than the module readback it must independently check.")
print(f"  -> even at end-of-life drift (0.5%) it is still 2x tighter. Requirement met.")

hr("E. Surface leakage: the error term nobody budgets for")
for Rl,lbl in [(1e12,"1 Tohm (clean, coated)"),(1e11,"100 Gohm"),(1e10,"10 Gohm (humid, uncoated)"),(1e9,"1 Gohm (contaminated)")]:
    R1e = R1*Rl/(R1+Rl)
    err = (R1/R1e-1)*100
    print(f"  leakage {lbl:26} in parallel with R1: R1_eff={R1e/1e6:7.2f} Mohm, ratio error {err:7.3f} % = {err*10:7.2f} V at 1 kV")
print("  => at 200 Mohm the divider is a >100 Mohm-class measurement. MANDATORY: a guard ring around the")
print("     tap node driven from the buffer output, conformal coating, and no soldermask-only HV creepage.")

hr("F. Set-path parts: does 16-bit actually buy anything?")
GAIN=400.0
for bits in (12,16):
    lsb = 2.5/(2**bits-1)*GAIN
    print(f"  {bits}-bit DAC LSB at output = {lsb*1e3:8.2f} mV")
    print(f"     vs module ripple spec 30 mVpp        : {'below the noise floor' if lsb*1e3<30 else f'{lsb*1e3/30:.1f}x the ripple floor'}")
    print(f"     vs calibrated monitor resolution {d*10*1e3:.0f} mV: closed-loop floor is max(DAC LSB, monitor) = {max(lsb*1e3, d*10*1e3):.0f} mV")
print("  => 12-bit is already ~3x below the monitor that closes the loop; 16-bit is not required,")
print("     it is merely cheap insurance and makes ramps smoother. Recommend 16-bit, justify as cost-not-need.")
