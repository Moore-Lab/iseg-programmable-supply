#!/usr/bin/env python3
"""PART LIBRARY for the hvctl golden netlist.  Stdlib-only, zero-arg, deterministic.

This file exists so that `board_spec.py` never contains an undocumented symbol
reference or an undocumented voltage rating.  Every entry carries:

  sym       "<lib_nickname>:<symbol_name>"   -- the symbol whose pin numbering GOVERNS
  fp        "<lib_nickname>:<footprint>"     -- "" means a PANEL/OFF-BOARD part
  cite      the DATED source the pin map was taken from
  vmax      working-voltage rating in volts, used by the HV rating assertion
  status    MPN verification status (INTERFACES.md I-4)

=============================================================================
HOW THE PIN NUMBERING WAS ESTABLISHED -- read this before trusting any pin map
=============================================================================

Three tiers, and every part in the design declares which tier it is in.  The
tier is printed in `docs/PIN_MAPS.md` next to every pin map, because a human at
the G1 gate has to know which lines to check hardest.

  TIER A -- PROJECT SYMBOL, generated in this repo from a dated datasheet read.
            Only the two iseg modules.  Cite: docs/PART_iseg_APS.md, which
            transcribes iseg APS technical documentation v2.5, 2024-08-20,
            Table 4, page 9.  The numbering in board_spec.py was read this
            session out of hardware/hvctl/lib/iseg.kicad_sym [verified-artifact]
            and is cross-checked at run time by check_symbol_pins().

  TIER B -- KICAD 10.0.3 STOCK SYMBOL, pin map read this session directly out of
            C:/Program Files/KiCad/10.0/share/kicad/symbols/<lib>.kicad_sym
            [verified-artifact].  The KiCad symbol is a SECOND-HAND source: it
            is a transcription of a manufacturer datasheet made by the KiCad
            library team, not by us.  It is checkable (the file is on disk and
            the self-check re-reads it) but it is NOT a datasheet read.

  TIER C -- BORROWED SYMBOL.  The stock library has no symbol for the exact part,
            so a pin-compatible sibling is used and the `val` field carries the
            real part.  EVERY TIER-C ENTRY IS A CLAIM THAT TWO PARTS SHARE A
            PINOUT, AND THAT CLAIM HAS NOT BEEN VERIFIED AGAINST A DATASHEET
            THIS SESSION.  These are the highest-risk lines in the whole project
            and PIN_MAPS.md lists them first, in their own table.

=============================================================================
THE ONE PIN FACT THAT WOULD HAVE BEEN GOT WRONG BY ASSUMPTION
=============================================================================
`Switch:SW_SPDT` -- the COMMON is pin **2** (name "B"), not pin 1.  Pins 1 ("A")
and 3 ("C") are the two throws.  Read this session out of Switch.kicad_sym by
pin GEOMETRY (pin 2 sits alone at x = -5.08; pins 1 and 3 sit together at
x = +5.08) [verified-artifact].  Guessing "pin 1 is the common" is the obvious
error and it would have swapped a throw with the common on every HV pole of the
mode switch -- a self-consistent, perfectly wrong board.

=============================================================================
"""

# --------------------------------------------------------------------------
# Voltage-rating classes.  `vmax` is the WORKING voltage the part may see.
# The HV assertion in board_spec.py derates by RATING_DERATE.
# --------------------------------------------------------------------------
RATING_DERATE = 0.50          # a part may work at <= 50 % of its rating (NUM-20 practice)
TOUCH_SAFE_V = 60.0           # [recalled] [unverified-primary] NUM-15
LV_MAX = 60.0                 # anything not HV-rated may not exceed this

# --------------------------------------------------------------------------
PARTS = {

  # ---------------------------------------------------------------- TIER A
  "ISEG_P": dict(
      tier="A", sym="iseg:APS_HV_MODULE_P", fp="iseg:iseg_APS_THT",
      vmax=1000.0, status="unverified-MPN",
      mfr="iseg Spezialelektronik GmbH",
      cite="docs/PART_iseg_APS.md -> iseg APS technical documentation v2.5, "
           "2024-08-20, Table 4 p.9 (pin map) and Table 1-3 (ratings). "
           "Symbol read from hardware/hvctl/lib/iseg.kicad_sym this session."),
  "ISEG_N": dict(
      tier="A", sym="iseg:APS_HV_MODULE_N", fp="iseg:iseg_APS_THT",
      vmax=1000.0, status="unverified-MPN",
      mfr="iseg Spezialelektronik GmbH",
      cite="docs/PART_iseg_APS.md -> iseg APS technical documentation v2.5, "
           "2024-08-20, Table 4 p.9 (pin map) and Table 1-3 (ratings). "
           "Symbol read from hardware/hvctl/lib/iseg.kicad_sym this session."),

  # ---------------------------------------------------------------- passives
  "R_LV": dict(tier="B", sym="Device:R", fp="Resistor_SMD:R_0603_1608Metric",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol R (2 pins)"),
  "R_HV_2512": dict(tier="B", sym="Device:R", fp="Resistor_SMD:R_2512_6332Metric",
               vmax=1500.0, status="unverified-MPN", mfr="Vishay CRHV class",
               cite="KiCad 10.0.3 Device.kicad_sym symbol R. RATING 1500 V is "
                    "[ASSUMED] per NUM-20 -- NEVER read from a datasheet."),
  "R_HV_1206": dict(tier="B", sym="Device:R", fp="Resistor_SMD:R_1206_3216Metric",
               vmax=800.0, status="unverified-MPN", mfr="Vishay CRHV class",
               cite="KiCad 10.0.3 Device.kicad_sym symbol R. RATING 800 V is "
                    "[ASSUMED] per NUM-20 -- NEVER read from a datasheet."),
  "R_HV_AXIAL": dict(tier="B", sym="Device:R", fp="Resistor_THT:R_Axial_Power_L25.0mm_W9.0mm_P30.48mm",
               vmax=3500.0, status="unverified-MPN", mfr="Ohmite MOX-400 class",
               cite="KiCad 10.0.3 Device.kicad_sym symbol R. 3.5 kV working is "
                    "[unverified-MPN] from COMBINER_DESIGN.md 3.3."),
  "C_LV": dict(tier="B", sym="Device:C", fp="Capacitor_SMD:C_0603_1608Metric",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol C (2 pins)"),
  "C_BULK": dict(tier="B", sym="Device:C_Polarized",
               fp="Capacitor_SMD:CP_Elec_8x10.5", vmax=LV_MAX,
               status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol C_Polarized"),
  "L_PWR": dict(tier="B", sym="Device:L", fp="Inductor_SMD:L_Bourns_SRP7028A",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol L (pins 1,2)"),
  "FB": dict(tier="B", sym="Device:L_Ferrite", fp="Inductor_SMD:L_0805_2012Metric",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol L_Ferrite"),
  "D_SCH": dict(tier="B", sym="Device:D_Schottky", fp="Diode_SMD:D_SOD-323",
               vmax=LV_MAX, status="unverified-MPN", mfr="BAT54 class",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol D_Schottky "
                    "(pin 1 = K, pin 2 = A)"),
  "D_ZEN": dict(tier="B", sym="Device:D_Zener", fp="Diode_SMD:D_SOD-323",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol D_Zener "
                    "(pin 1 = K, pin 2 = A)"),
  "D_TVS": dict(tier="B", sym="Device:D_TVS", fp="Diode_SMD:D_SMB",
               vmax=LV_MAX, status="unverified-MPN", mfr="Littelfuse SMBJ15A",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol D_TVS "
                    "(pins A1, A2 -- unidirectional part fitted A1 = cathode side)"),
  "LED": dict(tier="B", sym="Device:LED", fp="LED_SMD:LED_0805_2012Metric",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol LED "
                    "(pin 1 = K, pin 2 = A)"),
  "PFUSE": dict(tier="B", sym="Device:Polyfuse", fp="Fuse:Fuse_1812_4532Metric",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Device.kicad_sym, symbol Polyfuse"),
  "TP": dict(tier="B", sym="Connector:TestPoint", fp="TestPoint:TestPoint_Pad_D1.5mm",
               vmax=LV_MAX, status="n/a", mfr="n/a",
               cite="KiCad 10.0.3 Connector.kicad_sym, symbol TestPoint (1 pin)"),

  # ---------------------------------------------------------------- FETs
  "Q_NMOS": dict(tier="B", sym="Transistor_FET:2N7002", fp="Package_TO_SOT_SMD:SOT-23",
               vmax=LV_MAX, status="unverified-MPN", mfr="onsemi 2N7002",
               cite="KiCad 10.0.3 Transistor_FET.kicad_sym, symbol 2N7002 "
                    "(1 = G, 2 = S, 3 = D)"),
  "Q_NMOS_COIL": dict(tier="B", sym="Transistor_FET:2N7002", fp="Package_TO_SOT_SMD:SOT-23",
               vmax=LV_MAX, status="unverified-MPN", mfr="**>=300 mA part required**",
               cite="Same symbol as Q_NMOS. VALUE DELIBERATELY DIFFERENT: "
                    "CONTROLLER_AND_POWER.md finding -- 2N7002 (~115 mA) is "
                    "UNDER-RATED for the Pickering 125 mA coil. A >=300 mA part "
                    "must be fitted; the SOT-23 pinout is assumed identical and "
                    "that assumption is [recalled]."),
  "Q_PMOS": dict(tier="B", sym="Transistor_FET:Q_PMOS_GSD", fp="Package_TO_SOT_SMD:SOT-223",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Transistor_FET.kicad_sym, symbol Q_PMOS_GSD "
                    "(1 = G, 2 = S, 3 = D)"),

  # ---------------------------------------------------------------- analog ICs
  "DAC8552": dict(tier="B", sym="Analog_DAC:DAC8552", fp="Package_SO:VSSOP-8_3x3mm_P0.65mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Analog_DAC.kicad_sym, symbol DAC8552. "
                    "8 pins: 1 VDD, 2 VREF, 3 VOUTB, 4 VOUTA, 5 /SYNC, 6 SCLK, "
                    "7 DIN, 8 GND. DATASHEET NOT READ THIS SESSION -- the "
                    "power-on-reset-to-zero-scale gate (SETPOINT_PATH O-B) is "
                    "STILL OPEN and is a disqualifying gate."),
  "ADS1115": dict(tier="B", sym="Analog_ADC:ADS1115IDGS", fp="Package_SO:VSSOP-10_3x3mm_P0.5mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Analog_ADC.kicad_sym, symbol ADS1115IDGS. "
                    "10 pins: 1 ADDR, 2 ALERT/RDY, 3 GND, 4-7 AIN0-3, 8 VDD, "
                    "9 SDA, 10 SCL."),
  "REF5025": dict(tier="B", sym="Reference_Voltage:REF5025IDGK",
               fp="Package_SO:VSSOP-8_3x3mm_P0.65mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Reference_Voltage.kicad_sym, REF5025IDGK. "
                    "8 pins: 1 DNC, 2 Vin, 3 Temp, 4 GND, 5 Trim/NR, 6 Vout, "
                    "7 NC, 8 DNC."),
  "REF3020": dict(tier="B", sym="Reference_Voltage:REF3020",
               fp="Package_TO_SOT_SMD:SOT-23",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Reference_Voltage.kicad_sym, REF3020. "
                    "3 pins: 1 IN, 2 OUT, 3 GND."),
  "LM4040_2V048": dict(tier="B", sym="Reference_Voltage:LM4040DBZ-2.0",
               fp="Package_TO_SOT_SMD:SOT-23",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Reference_Voltage.kicad_sym, LM4040DBZ-2.0. "
                    "3 pins: 1 K, 2 A, 3 NC. The '-2.0' grade is the 2.048 V "
                    "device (SETPOINT_PATH.md 4.2 calls it LM4040-2.048)."),

  # ---------------------------------------------------------------- TIER C analog
  "OPA2192": dict(tier="C", sym="Amplifier_Operational:OPA2196xD",
               fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="TIER C BORROW. Symbol OPA2196xD (KiCad 10.0.3 "
                    "Amplifier_Operational.kicad_sym): 1 OUTA, 2 -A, 3 +A, "
                    "4 V-, 5 +B, 6 -B, 7 OUTB, 8 V+. CLAIM: OPA2192 and the "
                    "VSET buffer part share this standard dual-op-amp SOIC-8 "
                    "pinout. NOT VERIFIED against a datasheet this session. "
                    "SETPOINT_PATH.md O-D: no op-amp is actually selected yet."),
  "OPA_CLAMP": dict(tier="C", sym="Amplifier_Operational:OPA2196xD",
               fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="**UNSELECTED**",
               cite="TIER C BORROW, same symbol as OPA2192. This is the VSET "
                    "buffer whose V+ IS THE CLAMP. Its selection gates "
                    "(specified at V+ = 2.40-2.60 V, RRIO, >=10 mA source, "
                    "<=3 uVpp 0.1-10 Hz) are SETPOINT_PATH.md 3.3 and NO PART "
                    "MEETS THEM ON PAPER YET (O-D). This is a primary safety "
                    "element with an unselected part."),
  "TLV3202": dict(tier="C", sym="Comparator:LM393",
               fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="TIER C BORROW. Symbol LM393 (KiCad 10.0.3 "
                    "Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, "
                    "6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard "
                    "dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the "
                    "LM393 symbol declares its outputs OPEN_COLLECTOR; the "
                    "fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- "
                    "an open-drain failure pulls up to a false COLD = 1). The "
                    "symbol's pin TYPE is therefore wrong for the fitted part "
                    "and ERC will not notice."),
  "TPS3701": dict(tier="C", sym="Power_Supervisor:TPS3702",
               fp="Package_TO_SOT_SMD:SOT-23-6",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="TIER C BORROW. Symbol TPS3702 (KiCad 10.0.3 "
                    "Power_Supervisor.kicad_sym): 1 UV, 2 GND, 3 SENSE, "
                    "4 SET, 5 VDD, 6 OV. CLAIM: TPS3701 shares the TPS3702 "
                    "SOT-23-6 pinout. NOT VERIFIED."),
  "TPS22918": dict(tier="C", sym="Power_Management:TPS22917DBV",
               fp="Package_TO_SOT_SMD:SOT-23-6",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="TIER C BORROW. Symbol TPS22917DBV (KiCad 10.0.3 "
                    "Power_Management.kicad_sym): 1 VIN, 2 GND, 3 ON, 4 CT, "
                    "5 QOD, 6 VOUT. CLAIM: TPS22918 shares the TPS22917 "
                    "SOT-23-6 pinout. NOT VERIFIED. This part is the module "
                    "+VIN interlock element (ARCH-19 / SA-6)."),

  # ---------------------------------------------------------------- regulators
  "LMR33620": dict(tier="B", sym="Regulator_Switching:LMR33620ADDA",
               fp="Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Regulator_Switching.kicad_sym, LMR33620ADDA. "
                    "9 pins: 1 GND, 2 VIN, 3 EN, 4 PG, 5 FB, 6 VCC, 7 BOOT, "
                    "8 SW, 9 GND(EP)."),
  "LT3045": dict(tier="B", sym="Regulator_Linear:LT3045xMSE",
               fp="Package_SO:MSOP-12-1EP_3x4mm_P0.65mm_EP1.65x2.85mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Analog Devices",
               cite="KiCad 10.0.3 Regulator_Linear.kicad_sym, LT3045xMSE. "
                    "13 pins: 1-3 IN, 4 EN/UV, 5 PG, 6 ILIM, 7 PGFB, 8 SET, "
                    "9 GND, 10 OUTS, 11-12 OUT, 13 GND(EP)."),
  "LP5907": dict(tier="B", sym="Regulator_Linear:LP5907MFX-3.3",
               fp="Package_TO_SOT_SMD:SOT-23-5",
               vmax=LV_MAX, status="unverified-MPN", mfr="Texas Instruments",
               cite="KiCad 10.0.3 Regulator_Linear.kicad_sym, LP5907MFX-3.3. "
                    "5 pins: 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT."),

  # ---------------------------------------------------------------- logic (TIER C)
  # KiCad's 74xx library has no HCT part for several of these functions. The
  # symbol borrowed is the SAME JEDEC function number in another family, whose
  # DIP/SOIC pinout is standard across LS/HC/HCT/AHCT. That is a real and
  # ordinary practice -- and it is still a CLAIM, so it is TIER C.
  "74HCT30": dict(tier="C", sym="74xx:74LS30", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74LS30 used for a 74HCT30. KiCad "
                    "10.0.3 74xx.kicad_sym. 11 pins: 1-6 inputs A-F, 7 GND, "
                    "8 Y, 11 G, 12 H, 14 VCC. NOTE the '30 has NO pins 9, 10, "
                    "13 in the symbol (they are package NC) -- the pin map "
                    "must NOT list them or the symbol cross-check fails."),
  "74HCT14": dict(tier="C", sym="74xx:74HC14", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74HC14 used for a 74HCT14. "
                    "Pairs (in,out): (1,2)(3,4)(5,6)(9,8)(11,10)(13,12); "
                    "7 GND, 14 VCC. HCT NOT HC IS MANDATORY on every input "
                    "reachable from the 3.3 V ESP32 (CONTROLLER_AND_POWER 6.2) "
                    "-- the symbol cannot express that and ERC will not catch it."),
  "74HCT86": dict(tier="C", sym="74xx:74HC86", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74HC86 used for a 74HCT86. "
                    "Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); "
                    "7 GND, 14 VCC."),
  "74HCT08": dict(tier="C", sym="74xx:74LS08", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74LS08 used for a 74HCT08. "
                    "Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); "
                    "7 GND, 14 VCC."),
  "74HCT32": dict(tier="C", sym="74xx:74LS32", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74LS32 used for a 74HCT32. "
                    "Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); "
                    "7 GND, 14 VCC."),
  "74HCT03": dict(tier="C", sym="74xx:74LS03", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74LS03 used for a 74HCT03 "
                    "(open-drain quad NAND). Gates (a,b,y): (1,2,3)(4,5,6)"
                    "(9,10,8)(12,13,11); 7 GND, 14 VCC."),
  "74HCT00": dict(tier="B", sym="74xx:74HCT00", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="KiCad 10.0.3 74xx.kicad_sym, symbol 74HCT00. "
                    "Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); "
                    "7 GND, 14 VCC."),
  "74HCT123": dict(tier="B", sym="74xx:74HCT123", fp="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="KiCad 10.0.3 74xx.kicad_sym, symbol 74HCT123. 16 pins: "
                    "1 A, 2 B, 3 Clr, 4 /Q, 5 Q, 6 Cext, 7 RCext, 8 GND, "
                    "9 A, 10 B, 11 Clr, 12 /Q, 13 Q, 14 Cext, 15 RCext, 16 VCC."),
  "74HCT75": dict(tier="C", sym="74xx:74LS75", fp="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="TIER C BORROW: symbol 74LS75 used for a 74HCT75 quad "
                    "transparent latch. 16 pins: 1 /Q0, 2 D0, 3 D1, 4 E23, "
                    "5 VCC, 6 D2, 7 D3, 8 /Q3, 9 Q3, 10 Q2, 11 /Q2, 12 GND, "
                    "13 E01, 14 /Q1, 15 Q1, 16 Q0. TWO enables (E01, E23) is "
                    "exactly why this part is used and not a '373."),
  "74AHCT125": dict(tier="B", sym="74xx:74AHCT125", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia/TI",
               cite="KiCad 10.0.3 74xx.kicad_sym, symbol 74AHCT125. "
                    "Buffers (/OE,A,Y): (1,2,3)(4,5,6)(10,9,8)(13,12,11); "
                    "7 GND, 14 VCC."),
  "74LVC165": dict(tier="C", sym="74xx:74HC165", fp="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia",
               cite="TIER C BORROW: symbol 74HC165 used for a 74LVC165A. "
                    "16 pins: 1 /PL, 2 CP, 3-6 D4-D7, 7 /Q7, 8 GND, 9 Q7, "
                    "10 DS, 11-14 D0-D3, 15 /CE, 16 VCC. LVC is specified "
                    "here for 5 V-tolerant inputs at VCC = 3.3 V [recalled]."),
  "74LVC14": dict(tier="C", sym="74xx:74HC14", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
               vmax=LV_MAX, status="unverified-MPN", mfr="Nexperia",
               cite="TIER C BORROW: symbol 74HC14 used for a 74LVC14A. "
                    "Same pairs as 74HCT14."),

  # ---------------------------------------------------------------- relays
  "RELAY_HV": dict(tier="C", sym="Relay:Relay_SPDT", fp="Relay_THT:Relay_Pickering_Series67",
               vmax=5000.0, status="unverified-MPN", mfr="Pickering 67-1-C-5/5D",
               cite="TIER C BORROW: generic symbol Relay:Relay_SPDT (KiCad "
                    "10.0.3 Relay.kicad_sym): A1, A2 coil; 11 COM, 12 NC, "
                    "14 NO. The Pickering datasheet (Issue 1.4, Apr 2022) "
                    "was read in a prior session for RATINGS (5 kV stand-off, "
                    "2.5 kV switching, 3 A, 40 ohm 5 V coil) but its PIN "
                    "NUMBERING WAS NOT TRANSCRIBED, and the '/5D' suffix means "
                    "an INTERNAL COIL DIODE, so COIL POLARITY IS MANDATORY. "
                    "**THE FOOTPRINT NAMED HERE DOES NOT EXIST IN ANY LIBRARY "
                    "-- it is a placeholder. G1 must generate it.**"),
  "RELAY_LV": dict(tier="C", sym="Relay:Relay_DPDT", fp="Relay_THT:Relay_DPDT_Panasonic_TQ",
               vmax=LV_MAX, status="unverified-MPN", mfr="Panasonic TQ2SA-5V",
               cite="TIER C BORROW: generic symbol Relay:Relay_DPDT (KiCad "
                    "10.0.3 Relay.kicad_sym): A1, A2 coil; 11/12/14 pole 1; "
                    "21/22/24 pole 2. TQ2SA-5V pin numbering NOT read."),

  # ---------------------------------------------------------------- switches
  "SW_SPDT": dict(tier="B", sym="Switch:SW_SPDT", fp="",
               vmax=2000.0, status="unverified-MPN", mfr="**UNSOURCED (O-10)**",
               cite="KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPDT. "
                    "**PIN 2 IS THE COMMON** (name 'B', geometry x=-5.08); "
                    "pins 1 ('A') and 3 ('C') are the throws. fp = '' because "
                    "SW1 is a PANEL part wired to the board."),
  "SW_SPST": dict(tier="B", sym="Switch:SW_SPST", fp="",
               vmax=2000.0, status="unverified-MPN", mfr="**UNSOURCED (O-10)**",
               cite="KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2). "
                    "fp = '' -- panel part."),
  "SW_SPST_LV": dict(tier="B", sym="Switch:SW_SPST", fp="",
               vmax=LV_MAX, status="unverified-MPN", mfr="panel",
               cite="KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2)."),
  "SW_PUSH": dict(tier="B", sym="Switch:SW_Push", fp="Button_Switch_SMD:SW_SPST_CK_KMR2",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Switch.kicad_sym, symbol SW_Push (pins 1, 2)."),

  # ---------------------------------------------------------------- connectors
  "SHV": dict(tier="C", sym="Connector:Conn_Coaxial", fp="",
               vmax=5000.0, status="unverified-MPN", mfr="SHV bulkhead",
               cite="TIER C BORROW: generic Connector:Conn_Coaxial (KiCad "
                    "10.0.3): pin 1 'In' = centre, pin 2 'Ext' = shell. "
                    "fp = '' -- chassis bulkhead, wired to the board."),
  "HDR6": dict(tier="B", sym="Connector:Conn_01x06_Pin",
               fp="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Connector.kicad_sym, Conn_01x06_Pin (pins 1-6)."),
  "HDR8": dict(tier="B", sym="Connector:Conn_01x08_Pin",
               fp="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Connector.kicad_sym, Conn_01x08_Pin (pins 1-8)."),
  "HDR3": dict(tier="B", sym="Connector:Conn_01x03_Pin",
               fp="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
               vmax=LV_MAX, status="unverified-MPN", mfr="Phoenix MC 1,5/3-G-3,5",
               cite="KiCad 10.0.3 Connector.kicad_sym, Conn_01x03_Pin (pins 1-3)."),
  "BARREL": dict(tier="B", sym="Connector:Barrel_Jack",
               fp="Connector_BarrelJack:BarrelJack_Horizontal",
               vmax=LV_MAX, status="unverified-MPN", mfr="Switchcraft S-761K",
               cite="KiCad 10.0.3 Connector.kicad_sym, Barrel_Jack (pins 1, 2)."),

  # ---------------------------------------------------------------- MCU
  "ESP32S3": dict(tier="B", sym="RF_Module:ESP32-S3-WROOM-1",
               fp="RF_Module:ESP32-S3-WROOM-1",
               vmax=LV_MAX, status="unverified-MPN", mfr="Espressif",
               cite="KiCad 10.0.3 RF_Module.kicad_sym, ESP32-S3-WROOM-1. "
                    "41 pins. **THE -1U VARIANT IS REQUIRED** (external "
                    "antenna; the chassis is an earthed metal box, "
                    "CONTROLLER_AND_POWER delta-8) and **N8R2 QUAD PSRAM** "
                    "(octal PSRAM occupies GPIO33-37 [web-verified]). The "
                    "KiCad symbol is for the -1; the -1U differs only in the "
                    "antenna and is assumed pin-identical [recalled]."),

  # ------------------------------------- mechanically real, electrically absent
  "MTG_PAD": dict(tier="B", sym="Mechanical:MountingHole_Pad",
               fp="MountingHole:MountingHole_3.2mm_M3_Pad", vmax=LV_MAX,
               status="n/a", mfr="n/a",
               cite="KiCad 10.0.3 Mechanical.kicad_sym, MountingHole_Pad "
                    "(1 pin). Bonds the board to the earthed chassis -- the "
                    "board's GND IS the HV return, so these are the safety "
                    "earth bond, not just mechanical fixings."),
  "MTG_NOPAD": dict(tier="B", sym="Mechanical:MountingHole",
               fp="MountingHole:MountingHole_3.2mm_M3", vmax=LV_MAX,
               status="n/a", mfr="n/a",
               cite="KiCad 10.0.3 Mechanical.kicad_sym, MountingHole (ZERO "
                    "pins -- mechanically real, electrically absent). Used in "
                    "the HV region, where a plated, earthed fixing would be a "
                    "clearance violation, not a bond."),
  "JUMPER2": dict(tier="B", sym="Jumper:SolderJumper_2_Open",
               fp="Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm", vmax=LV_MAX,
               status="unverified-MPN", mfr="n/a",
               cite="KiCad 10.0.3 Jumper.kicad_sym, SolderJumper_2_Open "
                    "(pins 1 = A, 2 = B)."),
  "HDR2": dict(tier="B", sym="Connector:Conn_01x02_Pin",
               fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
               vmax=LV_MAX, status="unverified-MPN", mfr="generic",
               cite="KiCad 10.0.3 Connector.kicad_sym, Conn_01x02_Pin."),

  # ---------------------------------------------------------------- power syms
  "PWR_GND": dict(tier="B", sym="power:GND", fp="", vmax=LV_MAX, status="n/a",
               mfr="n/a", cite="KiCad 10.0.3 power.kicad_sym, symbol GND (1 pin)."),
  "PWR_FLAG": dict(tier="B", sym="power:PWR_FLAG", fp="", vmax=LV_MAX, status="n/a",
               mfr="n/a", cite="KiCad 10.0.3 power.kicad_sym, PWR_FLAG (1 pin)."),
}


# Parts whose voltage figure is a SPECIFICATION rather than a stress margin:
# the module IS the 1 kV source and the SHV terminal IS the 1 kV terminal, so
# derating them against their own output is meaningless. Everything else keeps
# RATING_DERATE.
NO_DERATE = {"ISEG_P", "ISEG_N", "SHV"}


def derate_of(key):
    return 1.0 if key in NO_DERATE else RATING_DERATE


def part(key):
    p = PARTS.get(key)
    if p is None:
        raise KeyError("no such part class: %r" % key)
    return p


def tier_c_parts():
    """The list a G1 reviewer must check hardest: borrowed pinouts."""
    return sorted(k for k, v in PARTS.items() if v["tier"] == "C")


if __name__ == "__main__":
    print("%d part classes; %d TIER-C (borrowed pinout) classes:"
          % (len(PARTS), len(tier_c_parts())))
    for k in tier_c_parts():
        print("   %-14s %s" % (k, PARTS[k]["sym"]))
