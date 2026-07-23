#!/usr/bin/env python3
"""Numbers for docs/CONTROL_ARCHITECTURE.md. stdlib only."""
import math

VNOM   = 1000.0      # V, worst-case module (AP010504P05 / AP010105P05 class)
VREF   = 2.5         # V, module internal reference, 5 V family
GAIN   = VNOM/VREF   # V-out per V-set  = 400
TAU_INT = 100e3*1e-6 # module internal 100k * 1uF  (Figure 2, manual p.9)
APB    = 80e6        # ESP32 LEDC source clock

def hr(t): print('-'*len(t)); print(t); print('-'*len(t))

hr("0. Constants")
print(f"Vnom={VNOM} V  Vref={VREF} V  set-path gain={GAIN:.1f} V/V")
print(f"module internal set-node tau = {TAU_INT*1e3:.1f} ms  -> fc = {1/(2*math.pi*TAU_INT):.3f} Hz")
print(f"module adjustment accuracy +-1%  -> +-{0.01*VNOM:.1f} V at output")
print(f"module VMON accuracy 1%*Vnom     -> +-{0.01*VNOM:.1f} V")
print(f"module ripple spec typ<10 mVpp, max<30 mVpp")

hr("1a. Set-point resolution: 1 LSB in volts at the HV output")
rows=[]
for name, bits, fs_at_vset in [
    ("ESP32 LEDC PWM, 8-bit",            8, 2.5),
    ("ESP32 LEDC PWM, 10-bit",          10, 2.5),
    ("ESP32 LEDC PWM, 12-bit",          12, 2.5),
    ("ESP32 LEDC PWM, 14-bit",          14, 2.5),
    ("classic-ESP32 internal DAC 8-bit",  8, 2.5),
    ("MCP4725 12-bit (VDD ref, attenuated to 2.5V)", 12, 2.5),
    ("MCP4725 12-bit (0..2.5 V of a 3.3 V span)",    12, 3.3),
    ("12-bit DAC, external 2.5 V ref",   12, 2.5),
    ("16-bit DAC, external 2.5 V ref",   16, 2.5),
    ("18-bit DAC, external 2.5 V ref",   18, 2.5),
]:
    codes = 2**bits - 1
    lsb_v = fs_at_vset/codes
    lsb_out = lsb_v*GAIN
    rows.append((name, bits, lsb_v*1e6, lsb_out, lsb_out/VNOM*1e6))
w=max(len(r[0]) for r in rows)
print(f"{'source':{w}}  bits  LSB@VSET(uV)   LSB@out(V)   ppm of FS")
for n,b,uv,ov,ppm in rows:
    print(f"{n:{w}}  {b:4d}  {uv:12.2f}  {ov:11.4f}  {ppm:10.1f}")

hr("1b. Resolution vs the module's own accuracy")
print(f"module adjustment accuracy band  = +-{0.01*VNOM:.0f} V  ({2*0.01*VNOM:.0f} V wide)")
for name,bits,fs in [("8-bit PWM",8,2.5),("12-bit PWM/DAC",12,2.5),("16-bit DAC",16,2.5)]:
    lsb = fs/(2**bits-1)*GAIN
    print(f"  {name:16}: LSB {lsb:8.4f} V -> {2*0.01*VNOM/lsb:10.1f} codes inside the +-1% accuracy band")

hr("1c. PWM ripple at the HV output (fundamental-only estimate)")
print("square wave 0..Vsw at VSET, D=0.5, fundamental pp = (4/pi)*Vsw")
print("attenuation per pole = 1/sqrt(1+(2*pi*f*tau)^2); module contributes tau=100 ms always\n")
def ripple(f, Vsw, taus):
    a = (4/math.pi)*Vsw
    for t in taus:
        a /= math.sqrt(1+(2*math.pi*f*t)**2)
    return a
cases=[]
for bits in (8,10,12,14):
    f = APB/2**bits
    for label, ext in [("none",[]), ("tau=1 ms",[1e-3]), ("tau=10 ms",[10e-3]), ("2x tau=1 ms",[1e-3,1e-3])]:
        r = ripple(f, 2.5, ext+[TAU_INT])
        cases.append((bits, f, label, r*1e6, r*GAIN*1e3))
print(f"{'bits':>4} {'f_pwm(Hz)':>11} {'ext filter':>12} {'ripple@VSET(uV)':>17} {'ripple@out(mVpp)':>18}  vs 30mV spec")
for b,f,l,uv,mv in cases:
    print(f"{b:4d} {f:11.0f} {l:>12} {uv:17.4f} {mv:18.4f}  {'PASS' if mv<30 else 'FAIL'}")

hr("1d. Settling penalty: time to settle to 1 LSB after a full-scale step")
print("t = tau_total * ln(2^N), tau_total = tau_ext + 100 ms (module)")
for bits in (8,12,16):
    for ext,lbl in [(0,"none"),(1e-3,"1 ms"),(10e-3,"10 ms")]:
        tt=ext+TAU_INT
        print(f"  {bits:2d}-bit, ext {lbl:>5}: tau_tot={tt*1e3:6.1f} ms -> t_settle={tt*math.log(2**bits):6.3f} s")
print(f"\nDAC path (no PWM filter, 10 ohm series): tau_ext ~ 0, t_settle = {TAU_INT*math.log(2**16):.3f} s")
print("=> the module's own 100 ms pole dominates in every case; the PWM filter penalty")
print("   at tau_ext=10 ms is only +10% on settling time. The PWM cost is NOT speed.")

hr("1e. VSET source-impedance error (internal 10k pull-up to Vref)")
print("Vpin = Vdrive + (Vref-Vdrive)*Rs/(Rs+10k); worst case at Vdrive=0")
for rs in (0.1,1,10,22,100,470,1000,10000):
    err = VREF*rs/(rs+10e3)
    print(f"  Rs={rs:8.1f} ohm -> offset {err*1e3:9.3f} mV = {err/VREF*100:7.3f} % FS = {err*GAIN:9.3f} V at output")
print("\nOPEN VSET (Rs = infinity): Vpin = Vref -> Vout = Vnom  (FULL SCALE). Failure mode.")

hr("2a. Independent HV monitor: divider design (bipolar, +-1 kV)")
R1 = 200e6
R2 = R3 = 402e3            # E96 0.1%
G1,G2,G3 = 1/R1,1/R2,1/R3
SG = G1+G2+G3
ratio = G1/SG
vmid  = VREF*G3/SG
print(f"R1 (HV string) = {R1/1e6:.0f} Mohm as 10 x 20 Mohm")
print(f"R2 = R3 = {R2/1e3:.0f} kohm 0.1%   (R2 to GND, R3 to a +2.500 V precision reference)")
print(f"divider ratio (HV -> tap) = {ratio:.6e}  = 1 : {1/ratio:.1f}")
print(f"tap common-mode (HV=0)    = {vmid:.4f} V   (mid of a 0..2.5 V ADC window)")
print(f"tap swing for +-1000 V    = +-{1000*ratio:.4f} V  -> use ADS1115 differential FSR +-2.048 V")
print(f"headroom to FSR           = {2.048/(1000*ratio):.2f}x  -> detects the 'not internally limited' overvoltage up to {2.048/ratio:.0f} V")
print(f"source impedance at tap   = {1/(G1+G2+G3)/1e3:.1f} kohm  -> BUFFER MANDATORY")

hr("2b. Divider loading vs module Inom")
print(f"{'module':>22} {'Vnom':>6} {'Inom':>8} {'I_div@Vnom':>11} {'% of Inom':>10}")
for nm,vn,inom in [("AP010504x05 (0.5 W)",1000,0.5e-3),("AP010105x12 (1 W)",1000,1.0e-3),
                   ("AP008604x05 (0.5 W)",800,0.6e-3),("AP006804x05 (0.5 W)",600,0.8e-3),
                   ("AP004125x05 (0.5 W)",400,1.2e-3),("AP002255x05 (0.5 W)",200,2.5e-3),
                   ("AP002505x12 (1 W)",200,5.0e-3)]:
    idiv = vn/(R1+R2*R3/(R2+R3))
    print(f"{nm:>22} {vn:5d}V {inom*1e3:6.2f}mA {idiv*1e6:9.3f}uA {idiv/inom*100:9.2f}%")

hr("2c. Divider power and per-element voltage stress")
Pt = 1000**2/(R1+R2*R3/(R2+R3))
print(f"total string dissipation at 1 kV = {Pt*1e3:.2f} mW")
for n in (5,7,10,14,20):
    print(f"  {n:2d} x {R1/n/1e6:6.2f} Mohm in series: {1000/n:6.1f} V each, {Pt/n*1e3:6.3f} mW each")

hr("2d. Series-element count from MAX WORKING VOLTAGE (not power)")
print("thick-film max working voltage (typical series values -- CONFIRM on the chosen part):")
print("  0603 = 75 V, 0805 = 150 V, 1206 = 200 V, 2010 = 400 V, 2512 = 500 V")
print(f"\n{'Vnom':>6} " + " ".join(f"{s:>12}" for s in ("0603/75V","0805/150V","1206/200V","2512/500V")))
for vn in (200,400,600,800,1000):
    cells=[]
    for mv in (75,150,200,500):
        n1 = math.ceil(vn/mv); n2 = math.ceil(vn/(mv/2.0))
        cells.append(f"{n1:3d} ({n2:3d})")
    print(f"{vn:5d}V " + " ".join(f"{c:>12}" for c in cells))
print("  n (n) = minimum at 100% rating (recommended at 2x derating)")

hr("2e. Monitor accuracy budget (1 kV FS, uncalibrated then calibrated)")
terms=[("R1 string, 10 x 0.1% uncorrelated (RSS)", 0.1/math.sqrt(10)),
       ("R2/R3 0.1%",                              0.1),
       ("tempco mismatch, 25 ppm/K thin film, dT=20 K", 25*20/1e4),
       ("VCR of the HV string, 5 ppm/V @ 100 V/element", 5*100/1e4),
       ("buffer op-amp Vos 25 uV + Ib*201k (1 pA)", (25e-6+1e-12*201e3)/1.0*100),
       ("ADS1115 gain error 0.15%",                0.15),
       ("ADS1115 INL 1 LSB of +-2.048 V FSR",      62.5e-6/1.0*100),
       ("+2.500 V reference 0.05% (offset term)",  0.05*vmid/1.0*0),
      ]
rss=0.0; tot=0.0
for n,p in terms:
    print(f"  {n:52} {p:7.4f} %")
    rss+=p*p; tot+=p
print(f"  {'worst-case sum':52} {tot:7.4f} %  = {tot/100*1000:6.2f} V at 1 kV")
print(f"  {'RSS':52} {math.sqrt(rss):7.4f} %  = {math.sqrt(rss)/100*1000:6.2f} V at 1 kV")
cal = math.sqrt(sum(p*p for n,p in terms if 'gain error' not in n and '0.1%' not in n))
print(f"  {'RSS after 2-point calibration vs a DMM':52} {cal:7.4f} %  = {cal/100*1000:6.2f} V at 1 kV")
print(f"\n  compare: module VMON accuracy 1%*Vnom = 10.00 V")

hr("2f. Divider as a bleed path: tau = (R1 + R2||R3) * C_out")
Rb = R1 + R2*R3/(R2+R3)
print(f"R_bleed(passive) = {Rb/1e6:.1f} Mohm")
print(f"{'C_out':>10} {'tau':>10} {'1kV->50V (3tau)':>18} {'1kV->10V (4.6tau)':>19} {'1kV->1V (6.9tau)':>18}")
for C,lbl in [(100e-12,"100 pF"),(470e-12,"470 pF"),(1e-9,"1 nF"),(10e-9,"10 nF"),(100e-9,"100 nF")]:
    t=Rb*C
    print(f"{lbl:>10} {t:9.4f}s {3*t:17.3f}s {math.log(100)*t:18.3f}s {math.log(1000)*t:17.3f}s")

hr("2g. Dedicated switched bleed sizing")
print("requirement: 1 kV -> 10 V in <= 1.0 s with C_out up to 100 nF")
Cw=100e-9; t_req=1.0; tau_req=t_req/math.log(100)
Rreq=tau_req/Cw
print(f"  need tau <= {tau_req*1e3:.1f} ms -> R <= {Rreq/1e6:.2f} Mohm")
for R in (1e6,2.2e6,3.3e6,4.7e6,10e6):
    print(f"  R={R/1e6:5.2f} Mohm: tau(100nF)={R*Cw:6.3f}s, t(1kV->10V)={math.log(100)*R*Cw:6.3f}s, "
          f"I@1kV={1000/R*1e6:7.1f}uA = {1000/R/0.5e-3*100:6.1f}% of a 0.5 mA Inom, P_peak={1000**2/R:6.3f} W")
print(f"  energy dumped from 100 nF at 1 kV = {0.5*Cw*1000**2*1e3:.1f} mJ")
print("  => the dedicated bleed MUST be switched (default-connected when disabled), never permanent.")

hr("3. Interlock: both-low glitch magnitude during a SEL transition")
for tg in (10e-9, 100e-9, 1e-6, 1e-3):
    dv = VREF*(1-math.exp(-tg/TAU_INT))
    print(f"  both /ON low for {tg*1e9:9.0f} ns -> internal set node rises {dv*1e6:9.3f} uV -> {dv*GAIN*1e3:9.4f} mV at HV out")
print("  (the module's own 100 ms set-node pole makes a logic-race glitch physically harmless,")
print("   but the state is still eliminated by construction - see the changeover monostable.)")

hr("3b. Heartbeat charge-pump decay")
for R,C in [(1e6,100e-9),(1e6,220e-9),(470e3,220e-9)]:
    print(f"  R={R/1e3:6.0f}k C={C*1e9:5.0f}nF -> tau={R*C*1e3:6.1f} ms, decay to a 1.5 V HC threshold from 3.3 V "
          f"in {R*C*math.log(3.3/1.5)*1e3:6.1f} ms")

hr("4. Monitor-disagreement trip threshold")
print(f"  module VMON accuracy      = 1%*Vnom            = {0.01*VNOM:6.2f} V")
print(f"  independent monitor (cal) = {cal:.3f}%             = {cal/100*VNOM:6.2f} V")
print(f"  quadrature sum            = {math.sqrt((0.01*VNOM)**2+(cal/100*VNOM)**2):6.2f} V")
print(f"  -> trip threshold 2%*Vnom = {0.02*VNOM:6.2f} V  (>= 1.7x the legitimate disagreement)")

hr("5. Ramp / changeover timing")
print(f"  module set-node pole tau            = {TAU_INT*1e3:.0f} ms")
print(f"  useful max slew (1 LSB per 3 tau)   = ramp steps no faster than {3*TAU_INT*1e3:.0f} ms apart")
print(f"  full-scale ramp at 100 V/s          = {VNOM/100:.1f} s")
print(f"  ramp-to-zero timeout = |dV|/slew + 3 s")
print(f"  discharge dwell: 5 tau_bleed with C=10 nF = {5*Rb*10e-9:.2f} s ; timeout 30 s -> TRIP, do NOT switch")
