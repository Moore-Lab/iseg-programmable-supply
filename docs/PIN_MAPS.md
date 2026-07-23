# PIN_MAPS &mdash; every part's pin map, for a human to check line by line

> **GENERATED FILE.** Produced by `hardware/hvctl/gen_pin_maps.py` from
> `hardware/hvctl/board_spec.py` and the symbol libraries on disk.
> **Never hand-edit it.** Fix the generator and regenerate.
>
> Regenerate with:
> ```
> "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/gen_pin_maps.py
> ```

## What this document is for

Pin maps are the **highest-consequence, lowest-feedback work in the project**.
Every other check in this repo &mdash; ERC, DRC, the netlist parity check, the
golden-netlist domain assertions &mdash; is *blind* to a wrong pin map, because
a wrong pin map produces a netlist that is perfectly self-consistent and a board
that is perfectly, self-consistently wrong.

**This document is the only gate that can catch that, and the only instrument
is a human with a datasheet.** It is laid out for exactly that job.

## How to review it, in order

1. **Section 1 first.** Those are the parts whose pinout is a *claim* that two
   different part numbers share a package pinout. Nobody has checked those
   claims against a datasheet. They are the most likely place a defect is
   hiding, and several of them are safety elements.
2. **Section 2 next.** One part, two symbols, and it is the 1 kV source. If
   `U1`/`U2` are wrong, everything downstream is wrong.
3. **Section 3 last**, and it can be sampled rather than read exhaustively:
   these pin maps were transcribed from a KiCad stock symbol that is itself a
   transcription of a datasheet. Second-hand, but *checkable* &mdash; the file
   is on disk and `board_spec.py` re-reads it on every run.

## The three tiers

| Tier | What it means | How much to trust it |
|---|---|---|
| **A** | Project symbol generated in this repo from a **dated datasheet read**. | Highest available. Still transcription. |
| **B** | KiCad 10.0.3 **stock symbol**, read off disk this session. | Second-hand: the KiCad library team transcribed the datasheet, not us. |
| **C** | **Borrowed** symbol &mdash; a pin-compatible sibling used for a part the stock library does not have. | **A CLAIM, NOT A READ.** Check every one. |

## The mechanical check that already runs

`board_spec.py` re-parses each `.kicad_sym` on disk on every run and asserts
**set equality both ways** between the pin numbers in the hand-authored map and
the pin numbers the symbol actually has: no invented pin, no forgotten pin, and
every deliberately-unconnected pad explicitly declared.

**That check cannot see whether the symbol matches the physical part.**
That is what you are here to do.

## The one pin fact that would have been got wrong by assumption

`Switch:SW_SPDT` &mdash; **the common is pin 2**, not pin 1. Pins 1 and 3 are
the throws. Established from pin *geometry* in `Switch.kicad_sym` (pin 2 sits
alone on the opposite side of the symbol). Assuming "pin 1 is the common" would
have swapped a throw with the common on every HV pole of the mode switch.

---


# 1. TIER C &mdash; BORROWED PINOUTS. **CHECK THESE FIRST.**

Each of these is the claim *'part X shares part Y's package pinout'*. **No datasheet was opened to verify any of them.** The `symbol` row names the symbol whose numbering was used; the `manufacturer` row names the part that will actually be soldered down.

#### `J2` &mdash; SHV bulkhead A

| | |
|---|---|
| symbol | `Connector:Conn_Coaxial` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SHV` &nbsp; **TIER C** |
| manufacturer | SHV bulkhead |
| MPN status | `unverified-MPN` |
| voltage rating | 5000 V working, derated to 5000 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: generic Connector:Conn_Coaxial (KiCad 10.0.3): pin 1 'In' = centre, pin 2 'Ext' = shell. fp = '' -- chassis bulkhead, wired to the board.

> **DESIGN NOTE.** pseudo-bipolar: the ONE output. unipolar: the POSITIVE output.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `In` | `HV_OUT_A` | **HV** |
| `2` | `Ext` | `GND` |  |

#### `J3` &mdash; SHV bulkhead B

| | |
|---|---|
| symbol | `Connector:Conn_Coaxial` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SHV` &nbsp; **TIER C** |
| manufacturer | SHV bulkhead |
| MPN status | `unverified-MPN` |
| voltage rating | 5000 V working, derated to 5000 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: generic Connector:Conn_Coaxial (KiCad 10.0.3): pin 1 'In' = centre, pin 2 'Ext' = shell. fp = '' -- chassis bulkhead, wired to the board.

> **DESIGN NOTE.** pseudo-bipolar: GROUNDED through R_G, never floating. unipolar: the NEGATIVE output. Spaced from J2 for the full 2000 V.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `In` | `HV_OUT_B` | **HV** |
| `2` | `Ext` | `GND` |  |

#### `K1` &mdash; 67-1-C-5/5D

| | |
|---|---|
| symbol | `Relay:Relay_SPDT` |
| footprint | `Relay_THT:Relay_Pickering_Series67` |
| part class | `RELAY_HV` &nbsp; **TIER C** |
| manufacturer | Pickering 67-1-C-5/5D |
| MPN status | `unverified-MPN` |
| voltage rating | 5000 V working, derated to 2500 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: generic symbol Relay:Relay_SPDT (KiCad 10.0.3 Relay.kicad_sym): A1, A2 coil; 11 COM, 12 NC, 14 NO. The Pickering datasheet (Issue 1.4, Apr 2022) was read in a prior session for RATINGS (5 kV stand-off, 2.5 kV switching, 3 A, 40 ohm 5 V coil) but its PIN NUMBERING WAS NOT TRANSCRIBED, and the '/5D' suffix means an INTERNAL COIL DIODE, so COIL POLARITY IS MANDATORY. **THE FOOTPRINT NAMED HERE DOES NOT EXIST IN ANY LIBRARY -- it is a placeholder. G1 must generate it.**

> **DESIGN NOTE.** 1 Form C reed, 5 kV stand-off. INTERNAL COIL DIODE ('/5D') => COIL POLARITY IS MANDATORY. Mount K1 and K2 with their long axes ORTHOGONAL: reed sensitivity is strongly axial and this mitigation costs nothing at layout and cannot be added later.

| pad | symbol pin name | net | |
|---|---|---|---|
| `11` | `` | `HV_POS_COM` | **HV** |
| `12` | `` | `HV_POS_PARK` | **HV** |
| `14` | `` | `HV_OUT_A` | **HV** |
| `A1` | `` | `COIL_FEED_P` |  |
| `A2` | `` | `K1_COIL_LO` |  |

#### `K2` &mdash; 67-1-C-5/5D

| | |
|---|---|
| symbol | `Relay:Relay_SPDT` |
| footprint | `Relay_THT:Relay_Pickering_Series67` |
| part class | `RELAY_HV` &nbsp; **TIER C** |
| manufacturer | Pickering 67-1-C-5/5D |
| MPN status | `unverified-MPN` |
| voltage rating | 5000 V working, derated to 2500 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: generic symbol Relay:Relay_SPDT (KiCad 10.0.3 Relay.kicad_sym): A1, A2 coil; 11 COM, 12 NC, 14 NO. The Pickering datasheet (Issue 1.4, Apr 2022) was read in a prior session for RATINGS (5 kV stand-off, 2.5 kV switching, 3 A, 40 ohm 5 V coil) but its PIN NUMBERING WAS NOT TRANSCRIBED, and the '/5D' suffix means an INTERNAL COIL DIODE, so COIL POLARITY IS MANDATORY. **THE FOOTPRINT NAMED HERE DOES NOT EXIST IN ANY LIBRARY -- it is a placeholder. G1 must generate it.**

> **DESIGN NOTE.** as K1. Long axis ORTHOGONAL to K1.

| pad | symbol pin name | net | |
|---|---|---|---|
| `11` | `` | `HV_NEG_COM` | **HV** |
| `12` | `` | `HV_NEG_PARK` | **HV** |
| `14` | `` | `HV_X` | **HV** |
| `A1` | `` | `COIL_FEED_N` |  |
| `A2` | `` | `K2_COIL_LO` |  |

#### `K3` &mdash; 67-1-C-5/5D

| | |
|---|---|
| symbol | `Relay:Relay_SPDT` |
| footprint | `Relay_THT:Relay_Pickering_Series67` |
| part class | `RELAY_HV` &nbsp; **TIER C** |
| manufacturer | Pickering 67-1-C-5/5D |
| MPN status | `unverified-MPN` |
| voltage rating | 5000 V working, derated to 2500 V by this design |
| DNP | **YES** |

> **CITATION.** TIER C BORROW: generic symbol Relay:Relay_SPDT (KiCad 10.0.3 Relay.kicad_sym): A1, A2 coil; 11 COM, 12 NC, 14 NO. The Pickering datasheet (Issue 1.4, Apr 2022) was read in a prior session for RATINGS (5 kV stand-off, 2.5 kV switching, 3 A, 40 ohm 5 V coil) but its PIN NUMBERING WAS NOT TRANSCRIBED, and the '/5D' suffix means an INTERNAL COIL DIODE, so COIL POLARITY IS MANDATORY. **THE FOOTPRINT NAMED HERE DOES NOT EXIST IN ANY LIBRARY -- it is a placeholder. G1 must generate it.**

> **DESIGN NOTE.** DNP. NC position carries the dump, so the de-energised state is 'dumped'. Fit ONLY on the bench result named in MONITOR_AND_BLEED.md 7.6; fitting both takes the 5 V rail to ~8.4 W, outside the enclosure's ventilation band.

| pad | symbol pin name | net | |
|---|---|---|---|
| `11` | `` | `HV_OUT_A` | **HV** |
| `12` | `` | `HV_OUT_A_DUMP` | **HV** |
| `14` | `` | *(nc)* | deliberately unconnected |
| `A1` | `` | `+5V_COIL` |  |
| `A2` | `` | `DUMP_COIL_A` |  |

#### `K4` &mdash; 67-1-C-5/5D

| | |
|---|---|
| symbol | `Relay:Relay_SPDT` |
| footprint | `Relay_THT:Relay_Pickering_Series67` |
| part class | `RELAY_HV` &nbsp; **TIER C** |
| manufacturer | Pickering 67-1-C-5/5D |
| MPN status | `unverified-MPN` |
| voltage rating | 5000 V working, derated to 2500 V by this design |
| DNP | **YES** |

> **CITATION.** TIER C BORROW: generic symbol Relay:Relay_SPDT (KiCad 10.0.3 Relay.kicad_sym): A1, A2 coil; 11 COM, 12 NC, 14 NO. The Pickering datasheet (Issue 1.4, Apr 2022) was read in a prior session for RATINGS (5 kV stand-off, 2.5 kV switching, 3 A, 40 ohm 5 V coil) but its PIN NUMBERING WAS NOT TRANSCRIBED, and the '/5D' suffix means an INTERNAL COIL DIODE, so COIL POLARITY IS MANDATORY. **THE FOOTPRINT NAMED HERE DOES NOT EXIST IN ANY LIBRARY -- it is a placeholder. G1 must generate it.**

> **DESIGN NOTE.** DNP. NC position carries the dump, so the de-energised state is 'dumped'. Fit ONLY on the bench result named in MONITOR_AND_BLEED.md 7.6; fitting both takes the 5 V rail to ~8.4 W, outside the enclosure's ventilation band.

| pad | symbol pin name | net | |
|---|---|---|---|
| `11` | `` | `HV_OUT_B` | **HV** |
| `12` | `` | `HV_OUT_B_DUMP` | **HV** |
| `14` | `` | *(nc)* | deliberately unconnected |
| `A1` | `` | `+5V_COIL` |  |
| `A2` | `` | `DUMP_COIL_B` |  |

#### `KS` &mdash; TQ2SA-5V

| | |
|---|---|
| symbol | `Relay:Relay_DPDT` |
| footprint | `Relay_THT:Relay_DPDT_Panasonic_TQ` |
| part class | `RELAY_LV` &nbsp; **TIER C** |
| manufacturer | Panasonic TQ2SA-5V |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: generic symbol Relay:Relay_DPDT (KiCad 10.0.3 Relay.kicad_sym): A1, A2 coil; 11/12/14 pole 1; 21/22/24 pole 2. TQ2SA-5V pin numbering NOT read.

> **DESIGN NOTE.** THE SINGLE ARMATURE. Pole A routes the only +VIN; pole B routes the only coil feed. In UNIPOLAR the panel switch's S6/S7 bridge AROUND it -- which is why a falsely-asserted MODE_UNI logic line cannot reach the forbidden state.

| pad | symbol pin name | net | |
|---|---|---|---|
| `11` | `` | `VIN_ARMED` |  |
| `12` | `` | `VIN_N_PRE` |  |
| `14` | `` | `VIN_P_PRE` |  |
| `21` | `` | `+5V_COIL` |  |
| `22` | `` | `COIL_FEED_N` |  |
| `24` | `` | `COIL_FEED_P` |  |
| `A1` | `` | `+5V_MOD` |  |
| `A2` | `` | `KS_COIL_LO` |  |

#### `U14` &mdash; TPS22918

| | |
|---|---|
| symbol | `Power_Management:TPS22917DBV` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS22918` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS22917DBV (KiCad 10.0.3 Power_Management.kicad_sym): 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT. CLAIM: TPS22918 shares the TPS22917 SOT-23-6 pinout. NOT VERIFIED. This part is the module +VIN interlock element (ARCH-19 / SA-6).

> **DESIGN NOTE.** Q_ARM (C-1). Fail-safe-OPEN switch in the module supply rail.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `VIN` | `+5V_MOD` |  |
| `2` | `GND` | `GND` |  |
| `3` | `ON` | `ARM` |  |
| `4` | `CT` | *(nc)* | deliberately unconnected |
| `5` | `QOD` | *(nc)* | deliberately unconnected |
| `6` | `VOUT` | `VIN_ARMED` |  |

#### `U15` &mdash; TPS22918

| | |
|---|---|
| symbol | `Power_Management:TPS22917DBV` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS22918` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS22917DBV (KiCad 10.0.3 Power_Management.kicad_sym): 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT. CLAIM: TPS22918 shares the TPS22917 SOT-23-6 pinout. NOT VERIFIED. This part is the module +VIN interlock element (ARCH-19 / SA-6).

> **DESIGN NOTE.** Q_COIL (C-1). Gated by EN_HB.INTLK.MODE_VALID, deliberately NOT by the full ARM -- a coil rail that dropped on every nOVP event would force a HOT BREAK on every trip (COMBINER_DESIGN 6.4).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `VIN` | `+5V_MOD` |  |
| `2` | `GND` | `GND` |  |
| `3` | `ON` | `COIL_EN` |  |
| `4` | `CT` | *(nc)* | deliberately unconnected |
| `5` | `QOD` | *(nc)* | deliberately unconnected |
| `6` | `VOUT` | `+5V_COIL` |  |

#### `U16` &mdash; TPS22918

| | |
|---|---|
| symbol | `Power_Management:TPS22917DBV` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS22918` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS22917DBV (KiCad 10.0.3 Power_Management.kicad_sym): 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT. CLAIM: TPS22918 shares the TPS22917 SOT-23-6 pinout. NOT VERIFIED. This part is the module +VIN interlock element (ARCH-19 / SA-6).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `VIN` | `VIN_P_PRE` |  |
| `2` | `GND` | `GND` |  |
| `3` | `ON` | `PERMIT_P` |  |
| `4` | `CT` | *(nc)* | deliberately unconnected |
| `5` | `QOD` | *(nc)* | deliberately unconnected |
| `6` | `VOUT` | `VIN_P_SW` |  |

#### `U17` &mdash; TPS22918

| | |
|---|---|
| symbol | `Power_Management:TPS22917DBV` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS22918` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS22917DBV (KiCad 10.0.3 Power_Management.kicad_sym): 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT. CLAIM: TPS22918 shares the TPS22917 SOT-23-6 pinout. NOT VERIFIED. This part is the module +VIN interlock element (ARCH-19 / SA-6).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `VIN` | `VIN_N_PRE` |  |
| `2` | `GND` | `GND` |  |
| `3` | `ON` | `PERMIT_N` |  |
| `4` | `CT` | *(nc)* | deliberately unconnected |
| `5` | `QOD` | *(nc)* | deliberately unconnected |
| `6` | `VOUT` | `VIN_N_SW` |  |

#### `U3` &mdash; OPA2192

| | |
|---|---|
| symbol | `Amplifier_Operational:OPA2196xD` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `OPA2192` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol OPA2196xD (KiCad 10.0.3 Amplifier_Operational.kicad_sym): 1 OUTA, 2 -A, 3 +A, 4 V-, 5 +B, 6 -B, 7 OUTB, 8 V+. CLAIM: OPA2192 and the VSET buffer part share this standard dual-op-amp SOIC-8 pinout. NOT VERIFIED against a datasheet this session. SETPOINT_PATH.md O-D: no op-amp is actually selected yet.

> **DESIGN NOTE.** A = unity-gain rail force amp, >=18.1 mA. B is PARKED as a unity buffer of GND rather than left floating.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `VCLAMP` |  |
| `2` | `-` | `VCLAMP_FB` |  |
| `3` | `+` | `VREF_2V500` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `GND` |  |
| `6` | `-` | `U3_PARK` |  |
| `7` | `` | `U3_PARK` |  |
| `8` | `V+` | `+5V_A` |  |

#### `U30` &mdash; 74HCT30

| | |
|---|---|
| symbol | `74xx:74LS30` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT30` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS30 used for a 74HCT30. KiCad 10.0.3 74xx.kicad_sym. 11 pins: 1-6 inputs A-F, 7 GND, 8 Y, 11 G, 12 H, 14 VCC. NOTE the '30 has NO pins 9, 10, 13 in the symbol (they are package NC) -- the pin map must NOT list them or the symbol cross-check fails.

> **DESIGN NOTE.** 8-input NAND. The 8th input is tied HIGH. Seven ARM terms, of which THREE ARE PHYSICAL (INTLK loop, MODE_VALID from the panel switch's own contacts, and -- through EN_HB -- firmware liveness).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `EN_HB` |  |
| `2` | `` | `ARM_EN` |  |
| `3` | `` | `INTLK` |  |
| `4` | `` | `nOVP` |  |
| `5` | `` | `SETTLE` |  |
| `6` | `` | `RAIL_OK` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `nARM` |  |
| `11` | `` | `MODE_VALID` |  |
| `12` | `` | `+5V_MOD` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U31` &mdash; 74HCT14

| | |
|---|---|
| symbol | `74xx:74HC14` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT14` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC14 used for a 74HCT14. Pairs (in,out): (1,2)(3,4)(5,6)(9,8)(11,10)(13,12); 7 GND, 14 VCC. HCT NOT HC IS MANDATORY on every input reachable from the 3.3 V ESP32 (CONTROLLER_AND_POWER 6.2) -- the symbol cannot express that and ERC will not catch it.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `nARM` |  |
| `2` | `` | `ARM` |  |
| `3` | `` | `MODE_A` |  |
| `4` | `` | `nMODE_A` |  |
| `5` | `` | `SEL` |  |
| `6` | `` | `nSEL` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `EN_HB_PUMP` |  |
| `9` | `` | `HB_PUMP` |  |
| `10` | `` | `HCT14_SPARE` |  |
| `11` | `` | `GND` |  |
| `12` | `` | `nOVP_CLR_SQ` |  |
| `13` | `` | `OVP_CLR_AC` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U32` &mdash; 74HCT86

| | |
|---|---|
| symbol | `74xx:74HC86` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT86` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC86 used for a 74HCT86. Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

> **DESIGN NOTE.** MODE_VALID = MODE_A XOR MODE_B. POSITIVE DECODE OF BOTH MODES: (1,0) pseudo-bipolar, (0,1) unipolar, (0,0) SAFE detent / in transit / broken aux wire, (1,1) mechanically impossible => shorted aux. One extra contact and one XOR cover the intermediate position, a shorted aux and a broken aux SIMULTANEOUSLY. The other three gates are edge detectors into SETTLE.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `MODE_A` |  |
| `2` | `` | `MODE_B` |  |
| `3` | `` | `MODE_VALID` |  |
| `4` | `` | `SEL` |  |
| `5` | `` | `SEL_DLY` |  |
| `6` | `` | `SEL_EDGE` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `MODEA_EDGE` |  |
| `9` | `` | `MODE_A` |  |
| `10` | `` | `MODE_A_DLY` |  |
| `11` | `` | `MODEB_EDGE` |  |
| `12` | `` | `MODE_B` |  |
| `13` | `` | `MODE_B_DLY` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U33` &mdash; 74HCT08

| | |
|---|---|
| symbol | `74xx:74LS08` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT08` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS08 used for a 74HCT08. Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

> **DESIGN NOTE.** *** THE MODE-AWARE PERMISSIVE. ***  PERMIT_P . PERMIT_N = ARM.(MODE_UNI + nSEL).(MODE_UNI + SEL) = ARM . MODE_UNI.  Both modules can be permitted ONLY when the switch's own aux pole says the armature is already in the position that has put them on different nodes. When MODE_UNI = 0 this collapses BIT FOR BIT to the SEL/nSEL gate. MODE_CMD does not exist and appears nowhere.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `MODE_B` |  |
| `2` | `` | `nMODE_A` |  |
| `3` | `` | `MODE_UNI` |  |
| `4` | `` | `ARM` |  |
| `5` | `` | `OUT_EN` |  |
| `6` | `` | `ARM_OUTEN` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `PERMIT_P` |  |
| `9` | `` | `ARM` |  |
| `10` | `` | `MU_OR_nSEL` |  |
| `11` | `` | `PERMIT_N` |  |
| `12` | `` | `ARM` |  |
| `13` | `` | `MU_OR_SEL` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U34` &mdash; 74HCT32

| | |
|---|---|
| symbol | `74xx:74LS32` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT32` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS32 used for a 74HCT32. Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `MODE_UNI` |  |
| `2` | `` | `nSEL` |  |
| `3` | `` | `MU_OR_nSEL` |  |
| `4` | `` | `MODE_UNI` |  |
| `5` | `` | `SEL` |  |
| `6` | `` | `MU_OR_SEL` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `EDGE_1` |  |
| `9` | `` | `SEL_EDGE` |  |
| `10` | `` | `MODEA_EDGE` |  |
| `11` | `` | `EDGE_ANY` |  |
| `12` | `` | `EDGE_1` |  |
| `13` | `` | `MODEB_EDGE` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U36` &mdash; 74HCT03

| | |
|---|---|
| symbol | `74xx:74LS03` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT03` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS03 used for a 74HCT03 (open-drain quad NAND). Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

> **DESIGN NOTE.** OPEN-DRAIN NAND. Gates a/b are /ON_P and /ON_N, pulled up to each module's OWN +VIN within 5 mm of pin 4 (ARCH-17) so the pull-up cannot outlive the module's supply. Gates c/d build KS_LE = COLD_AB . nARM out of two open-drain NANDs.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `ARM_OUTEN` |  |
| `2` | `` | `MU_OR_nSEL` |  |
| `3` | `` | `nON_P` |  |
| `4` | `` | `ARM_OUTEN` |  |
| `5` | `` | `MU_OR_SEL` |  |
| `6` | `` | `nON_N` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `KS_LE_N` |  |
| `9` | `` | `COLD_AB` |  |
| `10` | `` | `nARM` |  |
| `11` | `` | `KS_LE` |  |
| `12` | `` | `KS_LE_N` |  |
| `13` | `` | `KS_LE_N` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U38` &mdash; 74HCT08

| | |
|---|---|
| symbol | `74xx:74LS08` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT08` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS08 used for a 74HCT08. Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `EN_HB_PUMP` |  |
| `2` | `` | `WDT_OK` |  |
| `3` | `` | `EN_HB` |  |
| `4` | `` | `COLD_A_HI` |  |
| `5` | `` | `COLD_A_LO` |  |
| `6` | `` | `COLD_A` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `COLD_B` |  |
| `9` | `` | `COLD_B_HI` |  |
| `10` | `` | `COLD_B_LO` |  |
| `11` | `` | `COLD_AB` |  |
| `12` | `` | `COLD_A` |  |
| `13` | `` | `COLD_B` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U39` &mdash; 74HCT75

| | |
|---|---|
| symbol | `74xx:74LS75` |
| footprint | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` |
| part class | `74HCT75` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS75 used for a 74HCT75 quad transparent latch. 16 pins: 1 /Q0, 2 D0, 3 D1, 4 E23, 5 VCC, 6 D2, 7 D3, 8 /Q3, 9 Q3, 10 Q2, 11 /Q2, 12 GND, 13 E01, 14 /Q1, 15 Q1, 16 Q0. TWO enables (E01, E23) is exactly why this part is used and not a '373.

> **DESIGN NOTE.** REL_EN_P = LATCH(D = PERMIT_P, LE = COLD_A). REL_EN_N = LATCH(D = PERMIT_N, LE = COLD_A . COLD_B). Turning ON: the node is already cold, the latch is transparent, the relay closes 6 ms before any HV exists. Turning OFF: PERMIT drops (module dead at once), the node is hot so the latch is OPAQUE and the relay STAYS CLOSED -- which puts the module-side and output-side bleeds in parallel and discharges FASTER -- and when COLD asserts it releases cold.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `~{Q0}` | `LATCH_NQ0` |  |
| `2` | `D0` | `PERMIT_P` |  |
| `3` | `D1` | `GND` |  |
| `4` | `E23` | `COLD_AB` |  |
| `5` | `VCC` | `+5V_MOD` |  |
| `6` | `D2` | `PERMIT_N` |  |
| `7` | `D3` | `GND` |  |
| `8` | `~{Q3}` | `LATCH_NQ3` |  |
| `9` | `Q3` | `LATCH_Q3` |  |
| `10` | `Q2` | `REL_EN_N` |  |
| `11` | `~{Q2}` | `LATCH_NQ2` |  |
| `12` | `GND` | `GND` |  |
| `13` | `E01` | `COLD_A` |  |
| `14` | `~{Q1}` | `LATCH_NQ1` |  |
| `15` | `Q1` | `LATCH_Q1` |  |
| `16` | `Q0` | `REL_EN_P` |  |

#### `U4` &mdash; **UNSELECTED RRIO dual**

| | |
|---|---|
| symbol | `Amplifier_Operational:OPA2196xD` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `OPA_CLAMP` &nbsp; **TIER C** |
| manufacturer | **UNSELECTED** |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW, same symbol as OPA2192. This is the VSET buffer whose V+ IS THE CLAMP. Its selection gates (specified at V+ = 2.40-2.60 V, RRIO, >=10 mA source, <=3 uVpp 0.1-10 Hz) are SETPOINT_PATH.md 3.3 and NO PART MEETS THEM ON PAPER YET (O-D). This is a primary safety element with an unselected part.

> **DESIGN NOTE.** *** PRIMARY SAFETY ELEMENT WITH AN UNSELECTED PART (O-D). *** Pin 8 on VCLAMP_STAR is the clamp. Over-range residual +0.061 % (1000.6 V) against 1320 V unclamped at 3.3 V and 2000 V at 5 V.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `VSET_P_FORCE` |  |
| `2` | `-` | `VSET_P_SENSE` |  |
| `3` | `+` | `DAC_A_F` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `DAC_B_F` |  |
| `6` | `-` | `VSET_N_SENSE` |  |
| `7` | `` | `VSET_N_FORCE` |  |
| `8` | `V+` | `VCLAMP_STAR` |  |

#### `U40` &mdash; TPS3701

| | |
|---|---|
| symbol | `Power_Supervisor:TPS3702` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS3701` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS3702 (KiCad 10.0.3 Power_Supervisor.kicad_sym): 1 UV, 2 GND, 3 SENSE, 4 SET, 5 VDD, 6 OV. CLAIM: TPS3701 shares the TPS3702 SOT-23-6 pinout. NOT VERIFIED.

> **DESIGN NOTE.** 4.62 / 5.38 V window on +5V_MOD; module Vin range is 4.5-5.5 V

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `UV` | `RAIL_OK` |  |
| `2` | `GND` | `GND` |  |
| `3` | `SENSE` | `+5V_MOD` |  |
| `4` | `SET` | `GND` |  |
| `5` | `VDD` | `+5V_MOD` |  |
| `6` | `OV` | `RAIL_OK` |  |

#### `U41` &mdash; TPS3701

| | |
|---|---|
| symbol | `Power_Supervisor:TPS3702` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS3701` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS3702 (KiCad 10.0.3 Power_Supervisor.kicad_sym): 1 UV, 2 GND, 3 SENSE, 4 SET, 5 VDD, 6 OV. CLAIM: TPS3701 shares the TPS3702 SOT-23-6 pinout. NOT VERIFIED.

> **DESIGN NOTE.** 2.40 / 2.60 V window on the CLAMP rail; OV trips BEFORE the VSET comparator so a rail fault is diagnosed as a rail fault

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `UV` | `RAIL_OK` |  |
| `2` | `GND` | `GND` |  |
| `3` | `SENSE` | `VCLAMP` |  |
| `4` | `SET` | `GND` |  |
| `5` | `VDD` | `+5V_MOD` |  |
| `6` | `OV` | `RAIL_OK` |  |

#### `U42` &mdash; TPS3701

| | |
|---|---|
| symbol | `Power_Supervisor:TPS3702` |
| footprint | `Package_TO_SOT_SMD:SOT-23-6` |
| part class | `TPS3701` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol TPS3702 (KiCad 10.0.3 Power_Supervisor.kicad_sym): 1 UV, 2 GND, 3 SENSE, 4 SET, 5 VDD, 6 OV. CLAIM: TPS3701 shares the TPS3702 SOT-23-6 pinout. NOT VERIFIED.

> **DESIGN NOTE.** 4.60 / 5.40 V on +5V_A; below 4.5 V the monitor buffers are out of spec and the independent monitor cannot be trusted

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `UV` | `RAIL_OK` |  |
| `2` | `GND` | `GND` |  |
| `3` | `SENSE` | `+5V_A` |  |
| `4` | `SET` | `GND` |  |
| `5` | `VDD` | `+5V_MOD` |  |
| `6` | `OV` | `RAIL_OK` |  |

#### `U43` &mdash; 74HCT08

| | |
|---|---|
| symbol | `74xx:74LS08` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT08` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS08 used for a 74HCT08. Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

> **DESIGN NOTE.** C-1: the coil rail passes through its OWN fail-safe switch, so both-coils-off is reachable and the weld self-test can execute.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `EN_HB` |  |
| `2` | `` | `INTLK` |  |
| `3` | `` | `COIL_EN1` |  |
| `4` | `` | `COIL_EN1` |  |
| `5` | `` | `MODE_VALID` |  |
| `6` | `` | `COIL_EN` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `AND_SPARE1` |  |
| `9` | `` | `GND` |  |
| `10` | `` | `GND` |  |
| `11` | `` | `AND_SPARE2` |  |
| `12` | `` | `GND` |  |
| `13` | `` | `GND` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U44` &mdash; 74HCT75

| | |
|---|---|
| symbol | `74xx:74LS75` |
| footprint | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` |
| part class | `74HCT75` &nbsp; **TIER C** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74LS75 used for a 74HCT75 quad transparent latch. 16 pins: 1 /Q0, 2 D0, 3 D1, 4 E23, 5 VCC, 6 D2, 7 D3, 8 /Q3, 9 Q3, 10 Q2, 11 /Q2, 12 GND, 13 E01, 14 /Q1, 15 Q1, 16 Q0. TWO enables (E01, E23) is exactly why this part is used and not a '373.

> **DESIGN NOTE.** KS_SEL = LATCH(D = SEL, LE = COLD_A . COLD_B . nARM). Because the enable includes nARM and Q_ARM is gated by ARM, whenever the armature is allowed to move VIN_ARMED is 0 V and the contact transfers WITH NO SOURCE BEHIND IT. F-5 retired for free.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `~{Q0}` | `L2_NQ0` |  |
| `2` | `D0` | `SEL` |  |
| `3` | `D1` | `GND` |  |
| `4` | `E23` | `GND` |  |
| `5` | `VCC` | `+5V_MOD` |  |
| `6` | `D2` | `GND` |  |
| `7` | `D3` | `GND` |  |
| `8` | `~{Q3}` | `L2_NQ3` |  |
| `9` | `Q3` | `L2_Q3` |  |
| `10` | `Q2` | `L2_Q2` |  |
| `11` | `~{Q2}` | `L2_NQ2` |  |
| `12` | `GND` | `GND` |  |
| `13` | `E01` | `KS_LE` |  |
| `14` | `~{Q1}` | `L2_NQ1` |  |
| `15` | `Q1` | `L2_Q1` |  |
| `16` | `Q0` | `KS_SEL` |  |

#### `U45` &mdash; 74LVC165A

| | |
|---|---|
| symbol | `74xx:74HC165` |
| footprint | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` |
| part class | `74LVC165` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC165 used for a 74LVC165A. 16 pins: 1 /PL, 2 CP, 3-6 D4-D7, 7 /Q7, 8 GND, 9 Q7, 10 DS, 11-14 D0-D3, 15 /CE, 16 VCC. LVC is specified here for 5 V-tolerant inputs at VCC = 3.3 V [recalled].

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `~{PL}` | `nLOAD_165` |  |
| `2` | `CP` | `SPI_A_SCK` |  |
| `3` | `D4` | `INTLK_BUF` |  |
| `4` | `D5` | `RAIL_OK_BUF` |  |
| `5` | `D6` | `COLD_A_BUF` |  |
| `6` | `D7` | `COLD_B_BUF` |  |
| `7` | `~{Q7}` | `SR1_NQ7` |  |
| `8` | `GND` | `GND` |  |
| `9` | `Q7` | `SPI_A_MISO` |  |
| `10` | `DS` | `SR_CHAIN` |  |
| `11` | `D0` | `MODE_A_BUF` |  |
| `12` | `D1` | `MODE_B_BUF` |  |
| `13` | `D2` | `K1_DRV_RB` |  |
| `14` | `D3` | `K2_DRV_RB` |  |
| `15` | `~{CE}` | `GND` |  |
| `16` | `VCC` | `+3V3` |  |

#### `U46` &mdash; 74LVC165A

| | |
|---|---|
| symbol | `74xx:74HC165` |
| footprint | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` |
| part class | `74LVC165` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC165 used for a 74LVC165A. 16 pins: 1 /PL, 2 CP, 3-6 D4-D7, 7 /Q7, 8 GND, 9 Q7, 10 DS, 11-14 D0-D3, 15 /CE, 16 VCC. LVC is specified here for 5 V-tolerant inputs at VCC = 3.3 V [recalled].

> **DESIGN NOTE.** bits 14/15 are tied HIGH/LOW as a pattern: any other value means the readback path is untrustworthy => hard fault => stop the heartbeat.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `~{PL}` | `nLOAD_165` |  |
| `2` | `CP` | `SPI_A_SCK` |  |
| `3` | `D4` | `VSET_OVR_N_B` |  |
| `4` | `D5` | `BRANCH_LIVE_P_B` |  |
| `5` | `D6` | `+3V3` |  |
| `6` | `D7` | `GND` |  |
| `7` | `~{Q7}` | `SR2_NQ7` |  |
| `8` | `GND` | `GND` |  |
| `9` | `Q7` | `SR_CHAIN` |  |
| `10` | `DS` | `GND` |  |
| `11` | `D0` | `OVP_RB_BUF` |  |
| `12` | `D1` | `nON_P_RB` |  |
| `13` | `D2` | `nON_N_RB` |  |
| `14` | `D3` | `VSET_OVR_P_B` |  |
| `15` | `~{CE}` | `GND` |  |
| `16` | `VCC` | `+3V3` |  |

#### `U47` &mdash; 74LVC14A

| | |
|---|---|
| symbol | `74xx:74HC14` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74LVC14` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC14 used for a 74LVC14A. Same pairs as 74HCT14.

> **DESIGN NOTE.** LVC at VCC = 3.3 V is 5 V-tolerant on its inputs [recalled], which is what lets a 3.3 V part read the 5 V interlock domain with no translator. Double inversion so the ESP32 reads TRUE POLARITY.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `MODE_A` |  |
| `2` | `` | `MODE_A_N` |  |
| `3` | `` | `MODE_A_N` |  |
| `4` | `` | `MODE_A_BUF` |  |
| `5` | `` | `MODE_B` |  |
| `6` | `` | `MODE_B_N` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `MODE_B_BUF` |  |
| `9` | `` | `MODE_B_N` |  |
| `10` | `` | `OVP_Q_N` |  |
| `11` | `` | `OVP_Q` |  |
| `12` | `` | `OVP_RB_BUF` |  |
| `13` | `` | `OVP_Q_N` |  |
| `14` | `VCC` | `+3V3` |  |

#### `U48` &mdash; 74LVC14A

| | |
|---|---|
| symbol | `74xx:74HC14` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74LVC14` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC14 used for a 74LVC14A. Same pairs as 74HCT14.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `INTLK` |  |
| `2` | `` | `INTLK_N` |  |
| `3` | `` | `INTLK_N` |  |
| `4` | `` | `INTLK_BUF` |  |
| `5` | `` | `RAIL_OK` |  |
| `6` | `` | `RAIL_OK_N` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `RAIL_OK_BUF` |  |
| `9` | `` | `RAIL_OK_N` |  |
| `10` | `` | `COLD_A_N` |  |
| `11` | `` | `COLD_A` |  |
| `12` | `` | `COLD_A_BUF` |  |
| `13` | `` | `COLD_A_N` |  |
| `14` | `VCC` | `+3V3` |  |

#### `U49` &mdash; 74LVC14A

| | |
|---|---|
| symbol | `74xx:74HC14` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74LVC14` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC14 used for a 74LVC14A. Same pairs as 74HCT14.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `COLD_B` |  |
| `2` | `` | `COLD_B_N` |  |
| `3` | `` | `COLD_B_N` |  |
| `4` | `` | `COLD_B_BUF` |  |
| `5` | `` | `VSET_OVR_P` |  |
| `6` | `` | `VSET_OVR_P_N` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `VSET_OVR_P_B` |  |
| `9` | `` | `VSET_OVR_P_N` |  |
| `10` | `` | `VSET_OVR_N_N` |  |
| `11` | `` | `VSET_OVR_N` |  |
| `12` | `` | `VSET_OVR_N_B` |  |
| `13` | `` | `VSET_OVR_N_N` |  |
| `14` | `VCC` | `+3V3` |  |

#### `U5` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

> **DESIGN NOTE.** thresholds 2.430 / 2.5515 V referred to the rail. Caps a reference fault at 1021 V instead of 1320 V (3.3 V) or 2000 V (5 V).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `CLAMP_OV` |  |
| `2` | `-` | `CLAMP_TH_HI` |  |
| `3` | `+` | `VCLAMP_SENSE` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `CLAMP_TH_LO` |  |
| `6` | `-` | `VCLAMP_SENSE` |  |
| `7` | `` | `CLAMP_UV` |  |
| `8` | `V+` | `+5V_A` |  |

#### `U51` &mdash; 74LVC14A

| | |
|---|---|
| symbol | `74xx:74HC14` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74LVC14` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC14 used for a 74LVC14A. Same pairs as 74HCT14.

> **DESIGN NOTE.** pin 11 taps the REAL level at U1 pin 4, level-limited by the series resistor R86 -- not the commanded state.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `BRANCH_LIVE_P` |  |
| `2` | `` | `BLP_N` |  |
| `3` | `` | `BLP_N` |  |
| `4` | `` | `BRANCH_LIVE_P_B` |  |
| `5` | `` | `BRANCH_LIVE_N` |  |
| `6` | `` | `BLN_N` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `BRANCH_LIVE_N_B` |  |
| `9` | `` | `BLN_N` |  |
| `10` | `` | `nON_P_N` |  |
| `11` | `` | `nON_P_TAP` |  |
| `12` | `` | `nON_P_RB` |  |
| `13` | `` | `nON_P_N` |  |
| `14` | `VCC` | `+3V3` |  |

#### `U52` &mdash; 74LVC14A

| | |
|---|---|
| symbol | `74xx:74HC14` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74LVC14` &nbsp; **TIER C** |
| manufacturer | Nexperia |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW: symbol 74HC14 used for a 74LVC14A. Same pairs as 74HCT14.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `nON_N` |  |
| `2` | `` | `nON_N_N` |  |
| `3` | `` | `nON_N_N` |  |
| `4` | `` | `nON_N_RB` |  |
| `5` | `` | `BRANCH_LIVE_N_B` |  |
| `6` | `` | `LVC_SP1` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `LVC_SP2` |  |
| `9` | `` | `GND` |  |
| `10` | `` | `LVC_SP3` |  |
| `11` | `` | `GND` |  |
| `12` | `` | `LVC_SP4` |  |
| `13` | `` | `GND` |  |
| `14` | `VCC` | `+3V3` |  |

#### `U7` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `VSET_OVR_P` |  |
| `2` | `-` | `VSET_TH` |  |
| `3` | `+` | `VSET_P` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `VSET_N` |  |
| `6` | `-` | `VSET_TH` |  |
| `7` | `` | `VSET_OVR_N` |  |
| `8` | `V+` | `+5V_A` |  |

#### `U8` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

> **DESIGN NOTE.** +-105 % of Vnom on output A, read off the independent monitor -- the only layer that is indifferent to the fault's MECHANISM.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `OVP_A_HI` |  |
| `2` | `-` | `OVP_TH_AH` |  |
| `3` | `+` | `MON_TAP_A` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `OVP_TH_AL` |  |
| `6` | `-` | `MON_TAP_A` |  |
| `7` | `` | `OVP_A_LO` |  |
| `8` | `V+` | `+5V_A` |  |

#### `U9` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `OVP_B_HI` |  |
| `2` | `-` | `OVP_TH_AH` |  |
| `3` | `+` | `MON_TAP_B` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `OVP_TH_AL` |  |
| `6` | `-` | `MON_TAP_B` |  |
| `7` | `` | `OVP_B_LO` |  |
| `8` | `V+` | `+5V_A` |  |

#### `UBR` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

> **DESIGN NOTE.** single-threshold, one per module, UPSTREAM of the relays. Without these the weld self-test cannot distinguish 'stimulus applied and blocked' from 'no stimulus was ever applied'. Diagnostics only -- they feed the shift register, not the interlock -- which is why sharing the COLD threshold taps is acceptable here.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `BRANCH_LIVE_P` |  |
| `2` | `-` | `COLD_TH_HI` |  |
| `3` | `+` | `HVDIV_BR_P` | **HV** |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `COLD_TH_LO` |  |
| `6` | `-` | `HVDIV_BR_N` | **HV** |
| `7` | `` | `BRANCH_LIVE_N` |  |
| `8` | `V+` | `+5V_A` |  |

#### `UCC_A` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

> **DESIGN NOTE.** WINDOW comparator, sign-blind by design. A: HIGH while node < TH_HI. B: HIGH while node > TH_LO. MUST BE PUSH-PULL: an open-drain failure pulls up to a FALSE COLD = 1.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `COLD_A_HI` |  |
| `2` | `-` | `COLD_TH_HI` |  |
| `3` | `+` | `HVDIV_COLD_A` | **HV** |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `HVDIV_COLD_A` | **HV** |
| `6` | `-` | `COLD_TH_LO` |  |
| `7` | `` | `COLD_A_LO` |  |
| `8` | `V+` | `+5V_A` |  |

#### `UCC_B` &mdash; TLV3202

| | |
|---|---|
| symbol | `Comparator:LM393` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `TLV3202` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol LM393 (KiCad 10.0.3 Comparator.kicad_sym): 1 OUT1, 2 -1, 3 +1, 4 V-, 5 +2, 6 -2, 7 OUT2, 8 V+. CLAIM: TLV3202 shares the standard dual-comparator SOIC-8 pinout. NOT VERIFIED. NOTE the LM393 symbol declares its outputs OPEN_COLLECTOR; the fitted part MUST be PUSH-PULL (MONITOR_AND_BLEED 5.4 -- an open-drain failure pulls up to a false COLD = 1). The symbol's pin TYPE is therefore wrong for the fitted part and ERC will not notice.

> **DESIGN NOTE.** WINDOW comparator, sign-blind by design. A: HIGH while node < TH_HI. B: HIGH while node > TH_LO. MUST BE PUSH-PULL: an open-drain failure pulls up to a FALSE COLD = 1.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `COLD_B_HI` |  |
| `2` | `-` | `COLD_TH_HI` |  |
| `3` | `+` | `HVDIV_COLD_B` | **HV** |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `HVDIV_COLD_B` | **HV** |
| `6` | `-` | `COLD_TH_LO` |  |
| `7` | `` | `COLD_B_LO` |  |
| `8` | `V+` | `+5V_A` |  |

#### `UGD` &mdash; OPA2192

| | |
|---|---|
| symbol | `Amplifier_Operational:OPA2196xD` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `OPA2192` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol OPA2196xD (KiCad 10.0.3 Amplifier_Operational.kicad_sym): 1 OUTA, 2 -A, 3 +A, 4 V-, 5 +B, 6 -B, 7 OUTB, 8 V+. CLAIM: OPA2192 and the VSET buffer part share this standard dual-op-amp SOIC-8 pinout. NOT VERIFIED against a datasheet this session. SETPOINT_PATH.md O-D: no op-amp is actually selected yet.

> **DESIGN NOTE.** DRIVEN guard rings at tap potential. At Rt = 200 MOhm a 10 GOhm board leakage path injects 20.0 V of error -- LARGER than the 10.0 V VMON accuracy the divider exists to beat. The guard ring is a REQUIREMENT of the monitor, not a refinement.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `HVDIV_GUARD_A` | **HV** |
| `2` | `-` | `HVDIV_GUARD_A` | **HV** |
| `3` | `+` | `MON_TAP_A` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `MON_TAP_B` |  |
| `6` | `-` | `HVDIV_GUARD_B` | **HV** |
| `7` | `` | `HVDIV_GUARD_B` | **HV** |
| `8` | `V+` | `+5V_A` |  |

#### `UMB_A` &mdash; OPA2192

| | |
|---|---|
| symbol | `Amplifier_Operational:OPA2196xD` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `OPA2192` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol OPA2196xD (KiCad 10.0.3 Amplifier_Operational.kicad_sym): 1 OUTA, 2 -A, 3 +A, 4 V-, 5 +B, 6 -B, 7 OUTB, 8 V+. CLAIM: OPA2192 and the VSET buffer part share this standard dual-op-amp SOIC-8 pinout. NOT VERIFIED against a datasheet this session. SETPOINT_PATH.md O-D: no op-amp is actually selected yet.

> **DESIGN NOTE.** A = tap buffer (source Z is 163.8 kOhm, so the buffer is MANDATORY, not optional); B = matched offset buffer

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `MON_TAP_A` |  |
| `2` | `-` | `MON_TAP_A` |  |
| `3` | `+` | `MON_TAPF_A` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `MON_REFD_A` |  |
| `6` | `-` | `MON_REF_A` |  |
| `7` | `` | `MON_REF_A` |  |
| `8` | `V+` | `+5V_A` |  |

#### `UMB_B` &mdash; OPA2192

| | |
|---|---|
| symbol | `Amplifier_Operational:OPA2196xD` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `OPA2192` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol OPA2196xD (KiCad 10.0.3 Amplifier_Operational.kicad_sym): 1 OUTA, 2 -A, 3 +A, 4 V-, 5 +B, 6 -B, 7 OUTB, 8 V+. CLAIM: OPA2192 and the VSET buffer part share this standard dual-op-amp SOIC-8 pinout. NOT VERIFIED against a datasheet this session. SETPOINT_PATH.md O-D: no op-amp is actually selected yet.

> **DESIGN NOTE.** A = tap buffer (source Z is 163.8 kOhm, so the buffer is MANDATORY, not optional); B = matched offset buffer

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `MON_TAP_B` |  |
| `2` | `-` | `MON_TAP_B` |  |
| `3` | `+` | `MON_TAPF_B` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `MON_REFD_B` |  |
| `6` | `-` | `MON_REF_B` |  |
| `7` | `` | `MON_REF_B` |  |
| `8` | `V+` | `+5V_A` |  |

#### `UVM` &mdash; OPA2192

| | |
|---|---|
| symbol | `Amplifier_Operational:OPA2196xD` |
| footprint | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| part class | `OPA2192` &nbsp; **TIER C** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** TIER C BORROW. Symbol OPA2196xD (KiCad 10.0.3 Amplifier_Operational.kicad_sym): 1 OUTA, 2 -A, 3 +A, 4 V-, 5 +B, 6 -B, 7 OUTB, 8 V+. CLAIM: OPA2192 and the VSET buffer part share this standard dual-op-amp SOIC-8 pinout. NOT VERIFIED against a datasheet this session. SETPOINT_PATH.md O-D: no op-amp is actually selected yet.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `VMON_P_BUF` |  |
| `2` | `-` | `VMON_P_BUF` |  |
| `3` | `+` | `VMON_P` |  |
| `4` | `V-` | `GND` |  |
| `5` | `+` | `VMON_N` |  |
| `6` | `-` | `VMON_N_BUF` |  |
| `7` | `` | `VMON_N_BUF` |  |
| `8` | `V+` | `+5V_A` |  |



# 2. TIER A &mdash; the iseg HV modules

These two are the 1 kV source. The pin map below must be checked against **iseg APS technical documentation v2.5, 2024-08-20, Table 4, page 9** &mdash; the actual table, not `docs/PART_iseg_APS.md`, which is itself a transcription.

Three facts on this part make a pin-map error unusually dangerous, and all three are in `docs/PART_iseg_APS.md` carrying `[skeptic x3]`:

* pin 4 `/ON` is **active low, and an OPEN PIN MEANS HV ON**;
* pin 2 `VSET` has an **internal 10 k pull-up to Vref, so an open VSET node commands FULL SCALE**;
* pin 6 `HV` is **not internally limited** &mdash; Vset above Vref drives the output above Vnom.

A swapped pin 2 / pin 5, or a swapped pin 5 / pin 6, is therefore not a wiring inconvenience.

#### `U1` &mdash; AP010504P05

| | |
|---|---|
| symbol | `iseg:APS_HV_MODULE_P` |
| footprint | `iseg:iseg_APS_THT` |
| part class | `ISEG_P` &nbsp; **TIER A** |
| manufacturer | iseg Spezialelektronik GmbH |
| MPN status | `unverified-MPN` |
| voltage rating | 1000 V working, derated to 1000 V by this design |
| DNP | no |

> **CITATION.** docs/PART_iseg_APS.md -> iseg APS technical documentation v2.5, 2024-08-20, Table 4 p.9 (pin map) and Table 1-3 (ratings). Symbol read from hardware/hvctl/lib/iseg.kicad_sym this session.

> **DESIGN NOTE.** Vnom 1000 V, Inom 0.5 mA, Vin 5 V, Vref 2.5 V. /ON is ACTIVE LOW (low OR OPEN = HV ON). VSET has an internal 10k pull-up to Vref, so an OPEN VSET NODE COMMANDS FULL SCALE. Output is NOT internally limited. Pins 3 and 7 are BOTH GND and both must be present (SA-11).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `+VIN` | `VIN_P` |  |
| `2` | `VSET` | `VSET_P` |  |
| `3` | `GND` | `GND` |  |
| `4` | `~{ON}` | `nON_P` |  |
| `5` | `VMON` | `VMON_P` |  |
| `6` | `HV` | `HV_POS` | **HV** |
| `7` | `GND` | `GND` |  |

#### `U2` &mdash; AP010504N05

| | |
|---|---|
| symbol | `iseg:APS_HV_MODULE_N` |
| footprint | `iseg:iseg_APS_THT` |
| part class | `ISEG_N` &nbsp; **TIER A** |
| manufacturer | iseg Spezialelektronik GmbH |
| MPN status | `unverified-MPN` |
| voltage rating | 1000 V working, derated to 1000 V by this design |
| DNP | no |

> **CITATION.** docs/PART_iseg_APS.md -> iseg APS technical documentation v2.5, 2024-08-20, Table 4 p.9 (pin map) and Table 1-3 (ratings). Symbol read from hardware/hvctl/lib/iseg.kicad_sym this session.

> **DESIGN NOTE.** as U1, negative polarity. Factory-fixed, not switchable.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `+VIN` | `VIN_N` |  |
| `2` | `VSET` | `VSET_N` |  |
| `3` | `GND` | `GND` |  |
| `4` | `~{ON}` | `nON_N` |  |
| `5` | `VMON` | `VMON_N` |  |
| `6` | `HV` | `HV_NEG` | **HV** |
| `7` | `GND` | `GND` |  |


# 3. TIER B &mdash; KiCad stock symbols

Read off `C:/Program Files/KiCad/10.0/share/kicad/symbols/` this session. Repeated pin maps (every 0603 resistor, every test point) are printed once.

#### `#FLG01` &mdash; PWR_FLAG

| | |
|---|---|
| symbol | `power:PWR_FLAG` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `PWR_FLAG` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 power.kicad_sym, PWR_FLAG (1 pin).

> **DESIGN NOTE.** without it ERC raises power_pin_not_driven on GND

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `GND` |  |

#### `#FLG02` &mdash; PWR_FLAG

| | |
|---|---|
| symbol | `power:PWR_FLAG` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `PWR_FLAG` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 power.kicad_sym, PWR_FLAG (1 pin).

> **DESIGN NOTE.** the input rail has no power-OUTPUT pin behind it

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `+12V` |  |

#### `#PWR01` &mdash; GND

| | |
|---|---|
| symbol | `power:GND` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `PWR_GND` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 power.kicad_sym, symbol GND (1 pin).

> **DESIGN NOTE.** the one bare-named net on the board

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `GND` |  |

#### `C1` &mdash; 470u/25V

| | |
|---|---|
| symbol | `Device:C_Polarized` |
| footprint | `Capacitor_SMD:CP_Elec_8x10.5` |
| part class | `C_BULK` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol C_Polarized

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `+12V` |  |
| `2` | `` | `GND` |  |

#### `C10` &mdash; 10u

| | |
|---|---|
| symbol | `Device:C` |
| footprint | `Capacitor_SMD:C_0603_1608Metric` |
| part class | `C_LV` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol C (2 pins)

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `+5V_A` |  |
| `2` | `` | `GND` |  |

#### `D1` &mdash; SMBJ15A

| | |
|---|---|
| symbol | `Device:D_TVS` |
| footprint | `Diode_SMD:D_SMB` |
| part class | `D_TVS` &nbsp; **TIER B** |
| manufacturer | Littelfuse SMBJ15A |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol D_TVS (pins A1, A2 -- unidirectional part fitted A1 = cathode side)

> **DESIGN NOTE.** unidirectional TVS: pin 1 is the cathode side

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A1` | `+12V` |  |
| `2` | `A2` | `GND` |  |

#### `D2` &mdash; BZX84C12

| | |
|---|---|
| symbol | `Device:D_Zener` |
| footprint | `Diode_SMD:D_SOD-323` |
| part class | `D_ZEN` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol D_Zener (pin 1 = K, pin 2 = A)

> **DESIGN NOTE.** clamps Vgs of Q1

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `K` | `+12V_F` |  |
| `2` | `A` | `Q1_GATE` |  |

#### `D3` &mdash; 1N4148W

| | |
|---|---|
| symbol | `Device:D_Schottky` |
| footprint | `Diode_SMD:D_SOD-323` |
| part class | `D_SCH` &nbsp; **TIER B** |
| manufacturer | BAT54 class |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol D_Schottky (pin 1 = K, pin 2 = A)

> **DESIGN NOTE.** KS coil flyback

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `K` | `+5V_MOD` |  |
| `2` | `A` | `KS_COIL_LO` |  |

#### `DLED1` &mdash; HV_PRESENT

| | |
|---|---|
| symbol | `Device:LED` |
| footprint | `LED_SMD:LED_0805_2012Metric` |
| part class | `LED` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol LED (pin 1 = K, pin 2 = A)

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `K` | `LEDK_HV_PRESENT` |  |
| `2` | `A` | `LEDA_HV_PRESENT` |  |

#### `F1` &mdash; PTC 2A

| | |
|---|---|
| symbol | `Device:Polyfuse` |
| footprint | `Fuse:Fuse_1812_4532Metric` |
| part class | `PFUSE` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol Polyfuse

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `+12V_IN` |  |
| `2` | `` | `+12V_F` |  |

#### `FB1` &mdash; 600R@100MHz

| | |
|---|---|
| symbol | `Device:L_Ferrite` |
| footprint | `Inductor_SMD:L_0805_2012Metric` |
| part class | `FB` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol L_Ferrite

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `VIN_P_SW` |  |
| `2` | `2` | `VIN_P` |  |

#### `J1` &mdash; 12V 2.0A

| | |
|---|---|
| symbol | `Connector:Barrel_Jack` |
| footprint | `Connector_BarrelJack:BarrelJack_Horizontal` |
| part class | `BARREL` &nbsp; **TIER B** |
| manufacturer | Switchcraft S-761K |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Barrel_Jack (pins 1, 2).

> **DESIGN NOTE.** 2.1x5.5 mm LOCKING jack. Losing input power is SAFE.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `+12V_IN` |  |
| `2` | `` | `GND` |  |

#### `J4` &mdash; external interlock

| | |
|---|---|
| symbol | `Connector:Conn_01x03_Pin` |
| footprint | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` |
| part class | `HDR3` &nbsp; **TIER B** |
| manufacturer | Phoenix MC 1,5/3-G-3,5 |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Conn_01x03_Pin (pins 1-3).

> **DESIGN NOTE.** ship a fitted shorting plug and say so on the panel

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `Pin_1` | `ILK_N3` |  |
| `2` | `Pin_2` | `INTLK` |  |
| `3` | `Pin_3` | `GND` |  |

#### `J5` &mdash; programming / recovery (INTERNAL ONLY)

| | |
|---|---|
| symbol | `Connector:Conn_01x06_Pin` |
| footprint | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` |
| part class | `HDR6` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Conn_01x06_Pin (pins 1-6).

> **DESIGN NOTE.** NEVER on the panel: it is an un-isolated ground tie. D-5: the CP2102N + USB-C subsystem is out of scope for spec_version 1.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `Pin_1` | `+3V3` |  |
| `2` | `Pin_2` | `GND` |  |
| `3` | `Pin_3` | `U0TXD` |  |
| `4` | `Pin_4` | `U0RXD` |  |
| `5` | `Pin_5` | `ESP_EN` |  |
| `6` | `Pin_6` | `BOOT0` |  |

#### `J6` &mdash; mode-switch LV harness

| | |
|---|---|
| symbol | `Connector:Conn_01x08_Pin` |
| footprint | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` |
| part class | `HDR8` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Conn_01x08_Pin (pins 1-8).

> **DESIGN NOTE.** board boundary for the panel switch's four LV poles. The three HV poles are wired to individual HV standoffs, NOT to a header.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `Pin_1` | `+3V3` |  |
| `2` | `Pin_2` | `MODE_A` |  |
| `3` | `Pin_3` | `MODE_B` |  |
| `4` | `Pin_4` | `GND` |  |
| `5` | `Pin_5` | `VIN_P_PRE` |  |
| `6` | `Pin_6` | `VIN_N_PRE` |  |
| `7` | `Pin_7` | `COIL_FEED_P` |  |
| `8` | `Pin_8` | `COIL_FEED_N` |  |

#### `J7` &mdash; windowed watchdog (MAX6746 class)

| | |
|---|---|
| symbol | `Connector:Conn_01x03_Pin` |
| footprint | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` |
| part class | `HDR3` &nbsp; **TIER B** |
| manufacturer | Phoenix MC 1,5/3-G-3,5 |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Conn_01x03_Pin (pins 1-3).

> **DESIGN NOTE.** OPEN ITEM: the WINDOWED supervisor is specified but not yet a part. A windowed device faults on kicks that are TOO FAST as well as too slow, which is what catches a free-running peripheral pretending to be a main loop.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `Pin_1` | `+5V_MOD` |  |
| `2` | `Pin_2` | `WDT_OK` |  |
| `3` | `Pin_3` | `GND` |  |

#### `J8` &mdash; W5500 sub-board (D-5)

| | |
|---|---|
| symbol | `Connector:Conn_01x08_Pin` |
| footprint | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` |
| part class | `HDR8` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Conn_01x08_Pin (pins 1-8).

> **DESIGN NOTE.** D-5: CONTROLLER_AND_POWER.md 1.3 specifies an ON-BOARD W5500 with magnetics and an RJ45. Building it is G1 work; this header is the honest board boundary until then, NOT a design decision.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `Pin_1` | `+3V3` |  |
| `2` | `Pin_2` | `GND` |  |
| `3` | `Pin_3` | `SPI_B_SCK` |  |
| `4` | `Pin_4` | `SPI_B_MOSI` |  |
| `5` | `Pin_5` | `SPI_B_MISO` |  |
| `6` | `Pin_6` | `nCS_W5500` |  |
| `7` | `Pin_7` | `nRST_W5500` |  |
| `8` | `Pin_8` | `nINT_W5500` |  |

#### `JP1` &mdash; AUTO-RESET (ship REMOVED)

| | |
|---|---|
| symbol | `Connector:Conn_01x02_Pin` |
| footprint | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |
| part class | `HDR2` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | **YES** |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, Conn_01x02_Pin.

> **DESIGN NOTE.** DNP BY DESIGN, not by omission. Fitting it makes 'opening a terminal drops HV' the normal behaviour of the instrument.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `Pin_1` | `ESP_EN` |  |
| `2` | `Pin_2` | `AUTORST_EN` |  |

#### `L1` &mdash; 10uH

| | |
|---|---|
| symbol | `Device:L` |
| footprint | `Inductor_SMD:L_Bourns_SRP7028A` |
| part class | `L_PWR` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol L (pins 1,2)

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `SW_5V` |  |
| `2` | `2` | `+5V_MOD` |  |

#### `MH1` &mdash; M3 earth bond

| | |
|---|---|
| symbol | `Mechanical:MountingHole_Pad` |
| footprint | `MountingHole:MountingHole_3.2mm_M3_Pad` |
| part class | `MTG_PAD` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Mechanical.kicad_sym, MountingHole_Pad (1 pin). Bonds the board to the earthed chassis -- the board's GND IS the HV return, so these are the safety earth bond, not just mechanical fixings.

> **DESIGN NOTE.** plated and bonded: this is the safety earth path, not a fixing

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `GND` |  |

#### `MH2` &mdash; M3 earth bond

| | |
|---|---|
| symbol | `Mechanical:MountingHole_Pad` |
| footprint | `MountingHole:MountingHole_3.2mm_M3_Pad` |
| part class | `MTG_PAD` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Mechanical.kicad_sym, MountingHole_Pad (1 pin). Bonds the board to the earthed chassis -- the board's GND IS the HV return, so these are the safety earth bond, not just mechanical fixings.

> **DESIGN NOTE.** plated and bonded: this is the safety earth path, not a fixing

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `GND` |  |

#### `MH3` &mdash; M3 earth bond

| | |
|---|---|
| symbol | `Mechanical:MountingHole_Pad` |
| footprint | `MountingHole:MountingHole_3.2mm_M3_Pad` |
| part class | `MTG_PAD` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Mechanical.kicad_sym, MountingHole_Pad (1 pin). Bonds the board to the earthed chassis -- the board's GND IS the HV return, so these are the safety earth bond, not just mechanical fixings.

> **DESIGN NOTE.** plated and bonded: this is the safety earth path, not a fixing

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `GND` |  |

#### `MH4` &mdash; M3 earth bond

| | |
|---|---|
| symbol | `Mechanical:MountingHole_Pad` |
| footprint | `MountingHole:MountingHole_3.2mm_M3_Pad` |
| part class | `MTG_PAD` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Mechanical.kicad_sym, MountingHole_Pad (1 pin). Bonds the board to the earthed chassis -- the board's GND IS the HV return, so these are the safety earth bond, not just mechanical fixings.

> **DESIGN NOTE.** plated and bonded: this is the safety earth path, not a fixing

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `GND` |  |

#### `MH5` &mdash; M3 HV-region fixing

| | |
|---|---|
| symbol | `Mechanical:MountingHole` |
| footprint | `MountingHole:MountingHole_3.2mm_M3` |
| part class | `MTG_NOPAD` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Mechanical.kicad_sym, MountingHole (ZERO pins -- mechanically real, electrically absent). Used in the HV region, where a plated, earthed fixing would be a clearance violation, not a bond.

> **DESIGN NOTE.** NON-PLATED. Zero pins by construction -- a bonded fixing in the HV region would violate the clearance rule it sits inside.

| pad | symbol pin name | net | |
|---|---|---|---|

#### `MH6` &mdash; M3 HV-region fixing

| | |
|---|---|
| symbol | `Mechanical:MountingHole` |
| footprint | `MountingHole:MountingHole_3.2mm_M3` |
| part class | `MTG_NOPAD` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Mechanical.kicad_sym, MountingHole (ZERO pins -- mechanically real, electrically absent). Used in the HV region, where a plated, earthed fixing would be a clearance violation, not a bond.

> **DESIGN NOTE.** NON-PLATED. Zero pins by construction -- a bonded fixing in the HV region would violate the clearance rule it sits inside.

| pad | symbol pin name | net | |
|---|---|---|---|

#### `Q1` &mdash; reverse-block P-FET

| | |
|---|---|
| symbol | `Transistor_FET:Q_PMOS_GSD` |
| footprint | `Package_TO_SOT_SMD:SOT-223` |
| part class | `Q_PMOS` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Transistor_FET.kicad_sym, symbol Q_PMOS_GSD (1 = G, 2 = S, 3 = D)

> **DESIGN NOTE.** source to the jack, drain to the board: body diode blocks reverse

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `G` | `Q1_GATE` |  |
| `2` | `S` | `+12V_F` |  |
| `3` | `D` | `+12V` |  |

#### `QDA` &mdash; >=300mA NFET

| | |
|---|---|
| symbol | `Transistor_FET:2N7002` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `Q_NMOS_COIL` &nbsp; **TIER B** |
| manufacturer | **>=300 mA part required** |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | **YES** |

> **CITATION.** Same symbol as Q_NMOS. VALUE DELIBERATELY DIFFERENT: CONTROLLER_AND_POWER.md finding -- 2N7002 (~115 mA) is UNDER-RATED for the Pickering 125 mA coil. A >=300 mA part must be fitted; the SOT-23 pinout is assumed identical and that assumption is [recalled].

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `G` | `DUMP_EN_A` |  |
| `2` | `S` | `GND` |  |
| `3` | `D` | `DUMP_COIL_A` |  |

#### `QDB` &mdash; >=300mA NFET

| | |
|---|---|
| symbol | `Transistor_FET:2N7002` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `Q_NMOS_COIL` &nbsp; **TIER B** |
| manufacturer | **>=300 mA part required** |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | **YES** |

> **CITATION.** Same symbol as Q_NMOS. VALUE DELIBERATELY DIFFERENT: CONTROLLER_AND_POWER.md finding -- 2N7002 (~115 mA) is UNDER-RATED for the Pickering 125 mA coil. A >=300 mA part must be fitted; the SOT-23 pinout is assumed identical and that assumption is [recalled].

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `G` | `DUMP_EN_B` |  |
| `2` | `S` | `GND` |  |
| `3` | `D` | `DUMP_COIL_B` |  |

#### `QK1` &mdash; >=300mA NFET

| | |
|---|---|
| symbol | `Transistor_FET:2N7002` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `Q_NMOS_COIL` &nbsp; **TIER B** |
| manufacturer | **>=300 mA part required** |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** Same symbol as Q_NMOS. VALUE DELIBERATELY DIFFERENT: CONTROLLER_AND_POWER.md finding -- 2N7002 (~115 mA) is UNDER-RATED for the Pickering 125 mA coil. A >=300 mA part must be fitted; the SOT-23 pinout is assumed identical and that assumption is [recalled].

> **DESIGN NOTE.** COMBINER_DESIGN 6.3 specifies 2N7002 (~115 mA) for a 125 mA coil. UNDER-RATED. A >=300 mA part is required; reported, not patched.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `G` | `REL_EN_P` |  |
| `2` | `S` | `GND` |  |
| `3` | `D` | `K1_COIL_LO` |  |

#### `QK2` &mdash; >=300mA NFET

| | |
|---|---|
| symbol | `Transistor_FET:2N7002` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `Q_NMOS_COIL` &nbsp; **TIER B** |
| manufacturer | **>=300 mA part required** |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** Same symbol as Q_NMOS. VALUE DELIBERATELY DIFFERENT: CONTROLLER_AND_POWER.md finding -- 2N7002 (~115 mA) is UNDER-RATED for the Pickering 125 mA coil. A >=300 mA part must be fitted; the SOT-23 pinout is assumed identical and that assumption is [recalled].

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `G` | `REL_EN_N` |  |
| `2` | `S` | `GND` |  |
| `3` | `D` | `K2_COIL_LO` |  |

#### `QKS` &mdash; 2N7002

| | |
|---|---|
| symbol | `Transistor_FET:2N7002` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `Q_NMOS` &nbsp; **TIER B** |
| manufacturer | onsemi 2N7002 |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Transistor_FET.kicad_sym, symbol 2N7002 (1 = G, 2 = S, 3 = D)

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `G` | `KS_SEL` |  |
| `2` | `S` | `GND` |  |
| `3` | `D` | `KS_COIL_LO` |  |

#### `R1` &mdash; 100k

| | |
|---|---|
| symbol | `Device:R` |
| footprint | `Resistor_SMD:R_0603_1608Metric` |
| part class | `R_LV` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym, symbol R (2 pins)

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `Q1_GATE` |  |
| `2` | `` | `GND` |  |

#### `RBLDAA1` &mdash; 20M

| | |
|---|---|
| symbol | `Device:R` |
| footprint | `Resistor_SMD:R_2512_6332Metric` |
| part class | `R_HV_2512` &nbsp; **TIER B** |
| manufacturer | Vishay CRHV class |
| MPN status | `unverified-MPN` |
| voltage rating | 1500 V working, derated to 750 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym symbol R. RATING 1500 V is [ASSUMED] per NUM-20 -- NEVER read from a datasheet.

> **DESIGN NOTE.** bleed string a element 1/2; working 500 V/element

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `HV_OUT_A` | **HV** |
| `2` | `` | `HVDIV_BLDA_a_N1` | **HV** |

#### `RMONAA1` &mdash; 40M

| | |
|---|---|
| symbol | `Device:R` |
| footprint | `Resistor_SMD:R_1206_3216Metric` |
| part class | `R_HV_1206` &nbsp; **TIER B** |
| manufacturer | Vishay CRHV class |
| MPN status | `unverified-MPN` |
| voltage rating | 800 V working, derated to 400 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym symbol R. RATING 800 V is [ASSUMED] per NUM-20 -- NEVER read from a datasheet.

> **DESIGN NOTE.** monitor string a element 1/10; working 100 V/element

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `HV_OUT_A` | **HV** |
| `2` | `` | `HVDIV_MONA_a_N1` | **HV** |

#### `R_DUMP_A` &mdash; 10k

| | |
|---|---|
| symbol | `Device:R` |
| footprint | `Resistor_THT:R_Axial_Power_L25.0mm_W9.0mm_P30.48mm` |
| part class | `R_HV_AXIAL` &nbsp; **TIER B** |
| manufacturer | Ohmite MOX-400 class |
| MPN status | `unverified-MPN` |
| voltage rating | 3500 V working, derated to 1750 V by this design |
| DNP | **YES** |

> **CITATION.** KiCad 10.0.3 Device.kicad_sym symbol R. 3.5 kV working is [unverified-MPN] from COMBINER_DESIGN.md 3.3.

> **DESIGN NOTE.** SA-12: 1.5*Inom*R = 7.5 V, well under the 60 V touch-safe threshold. A 1 MOhm 'dump' would leave a 750 V clamp.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `HV_OUT_A_DUMP` | **HV** |
| `2` | `` | `GND` |  |

#### `SW1A` &mdash; SW1 pole S1

| | |
|---|---|
| symbol | `Switch:SW_SPDT` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPDT` &nbsp; **TIER B** |
| manufacturer | **UNSOURCED (O-10)** |
| MPN status | `unverified-MPN` |
| voltage rating | 2000 V working, derated to 1000 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPDT. **PIN 2 IS THE COMMON** (name 'B', geometry x=-5.08); pins 1 ('A') and 3 ('C') are the throws. fp = '' because SW1 is a PANEL part wired to the board.

> **DESIGN NOTE.** pin 2 = COMMON. PB throw (pin 1) -> M; UNI throw (pin 3) -> OUT_B.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `HV_M` | **HV** |
| `2` | `B` | `HV_X` | **HV** |
| `3` | `C` | `HV_OUT_B` | **HV** |

#### `SW1B` &mdash; SW1 pole S2

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST` &nbsp; **TIER B** |
| manufacturer | **UNSOURCED (O-10)** |
| MPN status | `unverified-MPN` |
| voltage rating | 2000 V working, derated to 1000 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2). fp = '' -- panel part.

> **DESIGN NOTE.** closed in PSEUDO-BIPOLAR only. M -> R_M1 -> BUS_A.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `HV_M1` | **HV** |
| `2` | `B` | `HV_OUT_A` | **HV** |

#### `SW1C` &mdash; SW1 pole S3

| | |
|---|---|
| symbol | `Switch:SW_SPDT` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPDT` &nbsp; **TIER B** |
| manufacturer | **UNSOURCED (O-10)** |
| MPN status | `unverified-MPN` |
| voltage rating | 2000 V working, derated to 1000 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPDT. **PIN 2 IS THE COMMON** (name 'B', geometry x=-5.08); pins 1 ('A') and 3 ('C') are the throws. fp = '' because SW1 is a PANEL part wired to the board.

> **DESIGN NOTE.** pin 2 = COMMON = GND through R_G. GROUNDS OUT_B in pseudo-bipolar and GROUNDS M in unipolar. This pole is what splits the 2000 V stress into two 1000 V gaps; every weld of it fails toward 'output grounded'.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `HV_OUT_B` | **HV** |
| `2` | `B` | `HV_SW_G` | **HV** |
| `3` | `C` | `HV_M` | **HV** |

#### `SW1D` &mdash; SW1 pole S4 (aux PB)

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

> **DESIGN NOTE.** POSITIVE decode of pseudo-bipolar. Wired to +3V3, not to GND, so a BROKEN WIRE -- the likelier panel-harness fault -- reads 0.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `+3V3` |  |
| `2` | `B` | `MODE_A` |  |

#### `SW1E` &mdash; SW1 pole S5 (aux UNI)

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

> **DESIGN NOTE.** POSITIVE decode of unipolar. (1,1) is mechanically impossible and therefore means a shorted aux => MODE_VALID = 0 => ARM = 0.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `+3V3` |  |
| `2` | `B` | `MODE_B` |  |

#### `SW1F` &mdash; SW1 pole S6 (+VIN bridge)

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

> **DESIGN NOTE.** THE POWER PERMISSIVE. Bridges around K_S pole A in UNIPOLAR only. A stuck GPIO or a shorted MODE_B line cannot close this contact, so it cannot release exclusivity.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `VIN_P_PRE` |  |
| `2` | `B` | `VIN_N_PRE` |  |

#### `SW1G` &mdash; SW1 pole S7 (coil bridge)

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

> **DESIGN NOTE.** as S6, for the relay coil feed.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `COIL_FEED_P` |  |
| `2` | `B` | `COIL_FEED_N` |  |

#### `SWB` &mdash; BOOT

| | |
|---|---|
| symbol | `Switch:SW_Push` |
| footprint | `Button_Switch_SMD:SW_SPST_CK_KMR2` |
| part class | `SW_PUSH` &nbsp; **TIER B** |
| manufacturer | generic |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_Push (pins 1, 2).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `BOOT0` |  |
| `2` | `2` | `GND` |  |

#### `SWG` &mdash; mode-guard microswitch

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

> **DESIGN NOTE.** the guard that must be opened to REACH the mode selector. This is what actually meets the lead-break requirement: opening the guard drops ARM hundreds of milliseconds of hand travel BEFORE any HV pole can move. Geometry, not contact sequencing.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `ILK_N2` |  |
| `2` | `B` | `ILK_N3` |  |

#### `SWK` &mdash; panel key switch

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `+5V_MOD` |  |
| `2` | `B` | `ILK_N1` |  |

#### `SWL` &mdash; lid switch

| | |
|---|---|
| symbol | `Switch:SW_SPST` |
| footprint | *(none &mdash; panel / off-board part)* |
| part class | `SW_SPST_LV` &nbsp; **TIER B** |
| manufacturer | panel |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Switch.kicad_sym, symbol SW_SPST (pins 1, 2).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `ILK_N1` |  |
| `2` | `B` | `ILK_N2` |  |

#### `TP1` &mdash; HVDIV_GUARD_A

| | |
|---|---|
| symbol | `Connector:TestPoint` |
| footprint | `TestPoint:TestPoint_Pad_D1.5mm` |
| part class | `TP` &nbsp; **TIER B** |
| manufacturer | n/a |
| MPN status | `n/a` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Connector.kicad_sym, symbol TestPoint (1 pin)

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `1` | `HVDIV_GUARD_A` | **HV** |

#### `U10` &mdash; LMR33620

| | |
|---|---|
| symbol | `Regulator_Switching:LMR33620ADDA` |
| footprint | `Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm` |
| part class | `LMR33620` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Regulator_Switching.kicad_sym, LMR33620ADDA. 9 pins: 1 GND, 2 VIN, 3 EN, 4 PG, 5 FB, 6 VCC, 7 BOOT, 8 SW, 9 GND(EP).

> **DESIGN NOTE.** EN tied to VIN; PG unused

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `GND` | `GND` |  |
| `2` | `VIN` | `+12V` |  |
| `3` | `EN` | `+12V` |  |
| `4` | `PG` | *(nc)* | deliberately unconnected |
| `5` | `FB` | `FB_5V` |  |
| `6` | `VCC` | `VCC_5V` |  |
| `7` | `BOOT` | `BOOT_5V` |  |
| `8` | `SW` | `SW_5V` |  |
| `9` | `GND` | `GND` |  |

#### `U11` &mdash; LMR33620

| | |
|---|---|
| symbol | `Regulator_Switching:LMR33620ADDA` |
| footprint | `Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm` |
| part class | `LMR33620` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Regulator_Switching.kicad_sym, LMR33620ADDA. 9 pins: 1 GND, 2 VIN, 3 EN, 4 PG, 5 FB, 6 VCC, 7 BOOT, 8 SW, 9 GND(EP).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `GND` | `GND` |  |
| `2` | `VIN` | `+12V` |  |
| `3` | `EN` | `+12V` |  |
| `4` | `PG` | *(nc)* | deliberately unconnected |
| `5` | `FB` | `FB_3V3` |  |
| `6` | `VCC` | `VCC_3V3` |  |
| `7` | `BOOT` | `BOOT_3V3` |  |
| `8` | `SW` | `SW_3V3` |  |
| `9` | `GND` | `GND` |  |

#### `U12` &mdash; LT3045

| | |
|---|---|
| symbol | `Regulator_Linear:LT3045xMSE` |
| footprint | `Package_SO:MSOP-12-1EP_3x4mm_P0.65mm_EP1.65x2.85mm` |
| part class | `LT3045` &nbsp; **TIER B** |
| manufacturer | Analog Devices |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Regulator_Linear.kicad_sym, LT3045xMSE. 13 pins: 1-3 IN, 4 EN/UV, 5 PG, 6 ILIM, 7 PGFB, 8 SET, 9 GND, 10 OUTS, 11-12 OUT, 13 GND(EP).

> **DESIGN NOTE.** PG/PGFB unused; SET resistor sets 5.00 V

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `IN` | `+12V` |  |
| `2` | `IN` | `+12V` |  |
| `3` | `IN` | `+12V` |  |
| `4` | `EN/UV` | `+12V` |  |
| `5` | `PG` | *(nc)* | deliberately unconnected |
| `6` | `ILIM` | `LT_ILIM` |  |
| `7` | `PGFB` | *(nc)* | deliberately unconnected |
| `8` | `SET` | `LT_SET` |  |
| `9` | `GND` | `GND` |  |
| `10` | `OUTS` | `+5V_A` |  |
| `11` | `OUT` | `+5V_A` |  |
| `12` | `OUT` | `+5V_A` |  |
| `13` | `GND` | `GND` |  |

#### `U13` &mdash; LP5907-3.3

| | |
|---|---|
| symbol | `Regulator_Linear:LP5907MFX-3.3` |
| footprint | `Package_TO_SOT_SMD:SOT-23-5` |
| part class | `LP5907` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Regulator_Linear.kicad_sym, LP5907MFX-3.3. 5 pins: 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `IN` | `+3V3` |  |
| `2` | `GND` | `GND` |  |
| `3` | `EN` | `+3V3` |  |
| `4` | `NC` | *(nc)* | deliberately unconnected |
| `5` | `OUT` | `+3V3_A` |  |

#### `U18` &mdash; DAC8552

| | |
|---|---|
| symbol | `Analog_DAC:DAC8552` |
| footprint | `Package_SO:VSSOP-8_3x3mm_P0.65mm` |
| part class | `DAC8552` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Analog_DAC.kicad_sym, symbol DAC8552. 8 pins: 1 VDD, 2 VREF, 3 VOUTB, 4 VOUTA, 5 /SYNC, 6 SCLK, 7 DIN, 8 GND. DATASHEET NOT READ THIS SESSION -- the power-on-reset-to-zero-scale gate (SETPOINT_PATH O-B) is STILL OPEN and is a disqualifying gate.

> **DESIGN NOTE.** VREF = THE CLAMP RAIL, so Vout <= Vref is a ratiometric property of the part, not a promise. VDD = 5 V is chosen for the LAYOUT reason: it keeps the entire +3V3 domain out of the analog set-path region, which is the only real defence against a VSET-to-3V3 solder bridge. POWER-ON RESET TO ZERO SCALE IS A DISQUALIFYING GATE AND IS STILL [recalled] -- G1 datasheet read (O-B).

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `V_{DD}` | `+5V_A` |  |
| `2` | `V_{REF}` | `VCLAMP_STAR` |  |
| `3` | `V_{OUT}B` | `DAC_OUTB` |  |
| `4` | `V_{OUT}A` | `DAC_OUTA` |  |
| `5` | `~{SYNC}` | `nSYNC_DAC_5V` |  |
| `6` | `SCLK` | `SPI_A_SCK_5V` |  |
| `7` | `D_{IN}` | `SPI_A_MOSI_5V` |  |
| `8` | `GND` | `GND` |  |

#### `U20` &mdash; REF5025

| | |
|---|---|
| symbol | `Reference_Voltage:REF5025IDGK` |
| footprint | `Package_SO:VSSOP-8_3x3mm_P0.65mm` |
| part class | `REF5025` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Reference_Voltage.kicad_sym, REF5025IDGK. 8 pins: 1 DNC, 2 Vin, 3 Temp, 4 GND, 5 Trim/NR, 6 Vout, 7 NC, 8 DNC.

> **DESIGN NOTE.** 2.500 V, +-0.05 %, 3 ppm/K. Sets DAC gain AND both offset legs.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `DNC` | *(nc)* | deliberately unconnected |
| `2` | `Vin` | `+5V_A` |  |
| `3` | `Temp` | *(nc)* | deliberately unconnected |
| `4` | `GND` | `GND` |  |
| `5` | `Trim/NR` | `REF_NR` |  |
| `6` | `Vout` | `VREF_2V500` |  |
| `7` | `NC` | *(nc)* | deliberately unconnected |
| `8` | `DNC` | *(nc)* | deliberately unconnected |

#### `U21` &mdash; REF3020

| | |
|---|---|
| symbol | `Reference_Voltage:REF3020` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `REF3020` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Reference_Voltage.kicad_sym, REF3020. 3 pins: 1 IN, 2 OUT, 3 GND.

> **DESIGN NOTE.** 2.048 V. The COLD window centre. A DIFFERENT DEVICE from U20 -- that separation is the whole of MONITOR_AND_BLEED 5.5.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `IN` | `+5V_A` |  |
| `2` | `OUT` | `VREF_2V048` |  |
| `3` | `GND` | `GND` |  |

#### `U22` &mdash; LM4040-2.048

| | |
|---|---|
| symbol | `Reference_Voltage:LM4040DBZ-2.0` |
| footprint | `Package_TO_SOT_SMD:SOT-23` |
| part class | `LM4040_2V048` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Reference_Voltage.kicad_sym, LM4040DBZ-2.0. 3 pins: 1 K, 2 A, 3 NC. The '-2.0' grade is the 2.048 V device (SETPOINT_PATH.md 4.2 calls it LM4040-2.048).

> **DESIGN NOTE.** SHUNT 2.048 V, a different FAMILY again, for the VSET/clamp window. A SERIES reference here would fail to its own input on a pass-element short: 5 V on the clamp rail is 2000 V at the output.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `K` | `VREF_2V048_SH` |  |
| `2` | `A` | `GND` |  |
| `3` | `NC` | *(nc)* | deliberately unconnected |

#### `U35` &mdash; 74HCT123

| | |
|---|---|
| symbol | `74xx:74HCT123` |
| footprint | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` |
| part class | `74HCT123` &nbsp; **TIER B** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 74xx.kicad_sym, symbol 74HCT123. 16 pins: 1 A, 2 B, 3 Clr, 4 /Q, 5 Q, 6 Cext, 7 RCext, 8 GND, 9 A, 10 B, 11 Clr, 12 /Q, 13 Q, 14 Cext, 15 RCext, 16 VCC.

> **DESIGN NOTE.** SETTLE is ~Q (pin 4): HIGH at rest, LOW for T_dwell after any SEL or mode edge, and LOW when unpowered -- all three fail-safe. t_w ~= 0.45.R.C = 0.99 s [recalled formula, G1 datasheet read].

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `A` | `GND` |  |
| `2` | `B` | `EDGE_ANY` |  |
| `3` | `Clr` | `+5V_MOD` |  |
| `4` | `~{Q}` | `SETTLE` |  |
| `5` | `Q` | `SETTLE_PULSE` |  |
| `6` | `Cext` | `GND` |  |
| `7` | `RCext` | `RCEXT_1` |  |
| `8` | `GND` | `GND` |  |
| `9` | `A` | `GND` |  |
| `10` | `B` | `GND` |  |
| `11` | `Clr` | `GND` |  |
| `12` | `~{Q}` | `MONO_SPARE_NQ` |  |
| `13` | `Q` | `MONO_SPARE_Q` |  |
| `14` | `Cext` | `GND` |  |
| `15` | `RCext` | `RCEXT_2` |  |
| `16` | `VCC` | `+5V_MOD` |  |

#### `U37` &mdash; 74HCT00

| | |
|---|---|
| symbol | `74xx:74HCT00` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74HCT00` &nbsp; **TIER B** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 74xx.kicad_sym, symbol 74HCT00. Gates (a,b,y): (1,2,3)(4,5,6)(9,10,8)(12,13,11); 7 GND, 14 VCC.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `nOVP_SET` |  |
| `2` | `` | `nOVP` |  |
| `3` | `` | `OVP_Q` |  |
| `4` | `` | `nOVP_CLR_SQ` |  |
| `5` | `` | `OVP_Q` |  |
| `6` | `` | `nOVP` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `NAND_SPARE1` |  |
| `9` | `` | `GND` |  |
| `10` | `` | `GND` |  |
| `11` | `` | `NAND_SPARE2` |  |
| `12` | `` | `GND` |  |
| `13` | `` | `GND` |  |
| `14` | `VCC` | `+5V_MOD` |  |

#### `U50` &mdash; ESP32-S3-WROOM-1U-N8R2

| | |
|---|---|
| symbol | `RF_Module:ESP32-S3-WROOM-1` |
| footprint | `RF_Module:ESP32-S3-WROOM-1` |
| part class | `ESP32S3` &nbsp; **TIER B** |
| manufacturer | Espressif |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 RF_Module.kicad_sym, ESP32-S3-WROOM-1. 41 pins. **THE -1U VARIANT IS REQUIRED** (external antenna; the chassis is an earthed metal box, CONTROLLER_AND_POWER delta-8) and **N8R2 QUAD PSRAM** (octal PSRAM occupies GPIO33-37 [web-verified]). The KiCad symbol is for the -1; the -1U differs only in the antenna and is assumed pin-identical [recalled].

> **DESIGN NOTE.** -1U (external antenna) and N8R2 (QUAD PSRAM) are HARD requirements: a PCB-antenna module inside an earthed steel box does not communicate, and OCTAL PSRAM occupies GPIO33-37. nc pins 13/14 = USB D-/D+ (internal only), 32-35 = JTAG (GPIO39-42, deliberately free), 15 = GPIO3 (strapping), 39 = GPIO1 spare. See D-4 for the GPIO33/34 remap.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `GND` | `GND` |  |
| `2` | `3V3` | `+3V3` |  |
| `3` | `EN` | `ESP_EN` |  |
| `4` | `IO4` | `HB_OUT` |  |
| `5` | `IO5` | `ARM_EN` |  |
| `6` | `IO6` | `OUT_EN` |  |
| `7` | `IO7` | `SEL` |  |
| `8` | `IO15` | `SPI_B_MISO` |  |
| `9` | `IO16` | `nCS_W5500` |  |
| `10` | `IO17` | `nRST_W5500` |  |
| `11` | `IO18` | `nINT_W5500` |  |
| `12` | `IO8` | `nSYNC_DAC` |  |
| `13` | `USB_D-` | *(nc)* | deliberately unconnected |
| `14` | `USB_D+` | *(nc)* | deliberately unconnected |
| `15` | `IO3` | *(nc)* | deliberately unconnected |
| `16` | `IO46` | `STRAP46` |  |
| `17` | `IO9` | `SPI_A_SCK` |  |
| `18` | `IO10` | `SPI_A_MOSI` |  |
| `19` | `IO11` | `SPI_A_MISO` |  |
| `20` | `IO12` | `nLOAD_165` |  |
| `21` | `IO13` | `SPI_B_SCK` |  |
| `22` | `IO14` | `SPI_B_MOSI` |  |
| `23` | `IO21` | `I2C_SDA` |  |
| `24` | `IO47` | `nALERT_ADC` |  |
| `25` | `IO48` | `LED_NET` |  |
| `26` | `IO45` | `STRAP45` |  |
| `27` | `IO0` | `BOOT0` |  |
| `28` | `IO35` | `MODE_A_RB` |  |
| `29` | `IO36` | `MODE_B_RB` |  |
| `30` | `IO37` | `OVP_RB` |  |
| `31` | `IO38` | `nOVP_CLR` |  |
| `32` | `IO39` | *(nc)* | deliberately unconnected |
| `33` | `IO40` | *(nc)* | deliberately unconnected |
| `34` | `IO41` | *(nc)* | deliberately unconnected |
| `35` | `IO42` | *(nc)* | deliberately unconnected |
| `36` | `RXD0` | `U0RXD` |  |
| `37` | `TXD0` | `U0TXD` |  |
| `38` | `IO2` | `I2C_SCL` |  |
| `39` | `IO1` | *(nc)* | deliberately unconnected |
| `40` | `GND` | `GND` |  |
| `41` | `GND` | `GND` |  |

#### `U6` &mdash; 74AHCT125

| | |
|---|---|
| symbol | `74xx:74AHCT125` |
| footprint | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| part class | `74AHCT125` &nbsp; **TIER B** |
| manufacturer | Nexperia/TI |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 74xx.kicad_sym, symbol 74AHCT125. Buffers (/OE,A,Y): (1,2,3)(4,5,6)(10,9,8)(13,12,11); 7 GND, 14 VCC.

> **DESIGN NOTE.** AHCT has TTL thresholds, so it accepts 3.3 V directly. It exists because TI DAC85xx digital VIH is [recalled] 0.7xVDD = 3.5 V at VDD = 5 V, which 3.3 V logic DOES NOT MEET.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `` | `GND` |  |
| `2` | `` | `nSYNC_DAC` |  |
| `3` | `` | `nSYNC_DAC_5V` |  |
| `4` | `` | `GND` |  |
| `5` | `` | `SPI_A_SCK` |  |
| `6` | `` | `SPI_A_SCK_5V` |  |
| `7` | `GND` | `GND` |  |
| `8` | `` | `SPI_A_MOSI_5V` |  |
| `9` | `` | `SPI_A_MOSI` |  |
| `10` | `` | `GND` |  |
| `11` | `` | `AHCT_SPARE` |  |
| `12` | `` | `GND` |  |
| `13` | `` | `+5V_A` |  |
| `14` | `VCC` | `+5V_A` |  |

#### `UADCA` &mdash; ADS1115

| | |
|---|---|
| symbol | `Analog_ADC:ADS1115IDGS` |
| footprint | `Package_SO:VSSOP-10_3x3mm_P0.5mm` |
| part class | `ADS1115` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Analog_ADC.kicad_sym, symbol ADS1115IDGS. 10 pins: 1 ADDR, 2 ALERT/RDY, 3 GND, 4-7 AIN0-3, 8 VDD, 9 SDA, 10 SCL.

> **DESIGN NOTE.** ADDR->GND = 0x48. BOTH independent HV monitors, as two differential pairs. NOTHING IN THE INTERLOCK READS THIS PART: every hardware permissive is a discrete comparator on its own string, so a stuck mux is not a safety element.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `ADDR` | `GND` |  |
| `2` | `ALERT/RDY` | `nALERT_ADC` |  |
| `3` | `GND` | `GND` |  |
| `4` | `AIN0` | `MON_TAP_A` |  |
| `5` | `AIN1` | `MON_REF_A` |  |
| `6` | `AIN2` | `MON_TAP_B` |  |
| `7` | `AIN3` | `MON_REF_B` |  |
| `8` | `VDD` | `+3V3_A` |  |
| `9` | `SDA` | `I2C_SDA` |  |
| `10` | `SCL` | `I2C_SCL` |  |

#### `UADCB` &mdash; ADS1115

| | |
|---|---|
| symbol | `Analog_ADC:ADS1115IDGS` |
| footprint | `Package_SO:VSSOP-10_3x3mm_P0.5mm` |
| part class | `ADS1115` &nbsp; **TIER B** |
| manufacturer | Texas Instruments |
| MPN status | `unverified-MPN` |
| voltage rating | 60 V working, derated to 30 V by this design |
| DNP | no |

> **CITATION.** KiCad 10.0.3 Analog_ADC.kicad_sym, symbol ADS1115IDGS. 10 pins: 1 ADDR, 2 ALERT/RDY, 3 GND, 4-7 AIN0-3, 8 VDD, 9 SDA, 10 SCL.

> **DESIGN NOTE.** ADDR->VDD = 0x49. Both module VMONs plus reference and rail health.

| pad | symbol pin name | net | |
|---|---|---|---|
| `1` | `ADDR` | `+3V3_A` |  |
| `2` | `ALERT/RDY` | `nALERT_ADC` |  |
| `3` | `GND` | `GND` |  |
| `4` | `AIN0` | `VMON_P_BUF` |  |
| `5` | `AIN1` | `VMON_N_BUF` |  |
| `6` | `AIN2` | `VREF_2V500` |  |
| `7` | `AIN3` | `RAIL5V_DIV` |  |
| `8` | `VDD` | `+3V3_A` |  |
| `9` | `SDA` | `I2C_SDA` |  |
| `10` | `SCL` | `I2C_SCL` |  |


**Identical pin maps suppressed** (same part class, same pad set as the entry above &mdash; the refdes list is given so nothing is silently missing from this document):

* `C_BULK` pads `1,2` &mdash; also `C13`, `C14`, `C5`, `C6`, `C9`
* `C_LV` pads `1,2` &mdash; also `C11`, `C12`, `C15`, `C16`, `C17`, `C18`, `C19`, `C2`, `C20`, `C21`, `C22`, `C23`, `C24`, `C25`, `C26`, `C27`, `C28`, `C29`, `C3`, `C30`, `C4`, `C7`, `C8`, `CD_MODE_A_DLY`, `CD_MODE_B_DLY`, `CD_SEL_DLY`, `CMA_A`, `CMA_B`, `CMB_A`, `CMB_B`, `CVS_N`, `CVS_P`, `C_SET`
* `D_SCH` pads `1,2` &mdash; also `D4`, `D5`, `DOR1`, `DOR2`, `DOR3`, `DOR4`, `DOR5`, `DOR6`, `DOR7`, `DOR8`, `DVS_N`, `DVS_P`
* `FB` pads `1,2` &mdash; also `FB2`
* `LED` pads `1,2` &mdash; also `DLED2`, `DLED3`, `DLED4`, `DLED5`
* `L_PWR` pads `1,2` &mdash; also `L2`
* `Q_NMOS` pads `1,2,3` &mdash; also `QLED1`, `QLED2`, `QLED3`, `QLED4`, `QLED5`, `QSET`, `QVS_N`, `QVS_P`
* `R_HV_1206` pads `1,2` &mdash; also `RMONAA10`, `RMONAA2`, `RMONAA3`, `RMONAA4`, `RMONAA5`, `RMONAA6`, `RMONAA7`, `RMONAA8`, `RMONAA9`, `RMONAB1`, `RMONAB10`, `RMONAB2`, `RMONAB3`, `RMONAB4`, `RMONAB5`, `RMONAB6`, `RMONAB7`, `RMONAB8`, `RMONAB9`, `RMONBA1`, `RMONBA10`, `RMONBA2`, `RMONBA3`, `RMONBA4`, `RMONBA5`, `RMONBA6`, `RMONBA7`, `RMONBA8`, `RMONBA9`, `RMONBB1`, `RMONBB10`, `RMONBB2`, `RMONBB3`, `RMONBB4`, `RMONBB5`, `RMONBB6`, `RMONBB7`, `RMONBB8`, `RMONBB9`
* `R_HV_2512` pads `1,2` &mdash; also `RBLDAA2`, `RBLDAB1`, `RBLDAB2`, `RBLDBA1`, `RBLDBA2`, `RBLDBB1`, `RBLDBB2`, `RBLDMA1`, `RBLDMA2`, `RBLDMB1`, `RBLDMB2`, `RBLDNA1`, `RBLDNA2`, `RBLDNB1`, `RBLDNB2`, `RBLDPA1`, `RBLDPA2`, `RBLDPB1`, `RBLDPB2`, `RBLDXA1`, `RBLDXA2`, `RBLDXB1`, `RBLDXB2`, `RBRNNA1`, `RBRNNA2`, `RBRNNB1`, `RBRNNB2`, `RBRNPA1`, `RBRNPA2`, `RBRNPB1`, `RBRNPB2`, `RCLDAA1`, `RCLDAA2`, `RCLDAB1`, `RCLDAB2`, `RCLDBA1`, `RCLDBA2`, `RCLDBB1`, `RCLDBB2`
* `R_HV_AXIAL` pads `1,2` &mdash; also `R_DUMP_B`, `R_G`, `R_M1`, `R_S_N`, `R_S_P`
* `R_LV` pads `1,2` &mdash; also `R10`, `R11`, `R12`, `R13`, `R14`, `R15`, `R16`, `R17`, `R18`, `R19`, `R2`, `R20`, `R21`, `R22`, `R23`, `R24`, `R25`, `R26`, `R27`, `R28`, `R29`, `R3`, `R30`, `R31`, `R32`, `R33`, `R34`, `R35`, `R36`, `R37`, `R38`, `R39`, `R4`, `R40`, `R41`, `R42`, `R43`, `R44`, `R45`, `R46`, `R47`, `R48`, `R49`, `R5`, `R50`, `R51`, `R52`, `R53`, `R54`, `R55`, `R56`, `R57`, `R58`, `R59`, `R6`, `R60`, `R61`, `R62`, `R63`, `R64`, `R65`, `R66`, `R67`, `R68`, `R69`, `R7`, `R70`, `R71`, `R72`, `R73`, `R74`, `R75`, `R76`, `R77`, `R78`, `R79`, `R8`, `R80`, `R81`, `R82`, `R83`, `R84`, `R85`, `R86`, `R87`, `R88`, `R89`, `R9`, `R90`, `R91`, `R92`, `R93`, `R94`, `R95`, `RBB_N`, `RBB_P`, `RBO_N`, `RBO_P`, `RCB_A`, `RCB_B`, `RCH_A`, `RCH_B`, `RCL_A`, `RCL_B`, `RCO_A`, `RCO_B`, `RCP1_A`, `RCP1_B`, `RCP2_A`, `RCP2_B`, `RDA1`, `RDA2`, `RDB1`, `RDB2`, `RD_MODE_A_DLY`, `RD_MODE_B_DLY`, `RD_SEL_DLY`, `RLED1`, `RLED2`, `RLED3`, `RLED4`, `RLED5`, `RMA1`, `RMA2`, `RMB1`, `RMB2`, `RMB_A`, `RMB_B`, `RMO_A`, `RMO_B`, `RMR1_A`, `RMR1_B`, `RMR2_A`, `RMR2_B`, `RMS_A`, `RMS_B`, `RPD1_N`, `RPD1_P`, `RPD2_N`, `RPD2_P`, `RPD3_N`, `RPD3_P`, `RPD4_N`, `RPD4_P`, `RSS1a`, `RSS1b`, `RSS2a`, `RSS2b`, `RSS3a`, `RSS3b`, `R_SET`, `R_SET2`
* `TP` pads `1` &mdash; also `TP10`, `TP11`, `TP12`, `TP13`, `TP14`, `TP15`, `TP2`, `TP3`, `TP4`, `TP5`, `TP6`, `TP7`, `TP8`, `TP9`, `TP_L2_NQ0`, `TP_L2_NQ1`, `TP_L2_NQ2`, `TP_L2_NQ3`, `TP_L2_Q1`, `TP_L2_Q2`, `TP_L2_Q3`, `TP_LATCH_NQ0`, `TP_LATCH_NQ1`, `TP_LATCH_NQ2`, `TP_LATCH_NQ3`, `TP_LATCH_Q1`, `TP_LATCH_Q3`, `TP_LVC_SP1`, `TP_LVC_SP2`, `TP_LVC_SP3`, `TP_LVC_SP4`, `TP_MODE_A_RB`, `TP_MODE_B_RB`, `TP_OVP_RB`, `TP_nON_P_TAP`


# 4. Review checklist

| # | Part class | Tier | Symbol | Instances | Checked? |
|---|---|---|---|---|---|
| 1 | `74HCT03` | **C** | `74xx:74LS03` | 1 (U36) | &#9744; |
| 2 | `74HCT08` | **C** | `74xx:74LS08` | 3 (U33&hellip;) | &#9744; |
| 3 | `74HCT14` | **C** | `74xx:74HC14` | 1 (U31) | &#9744; |
| 4 | `74HCT30` | **C** | `74xx:74LS30` | 1 (U30) | &#9744; |
| 5 | `74HCT32` | **C** | `74xx:74LS32` | 1 (U34) | &#9744; |
| 6 | `74HCT75` | **C** | `74xx:74LS75` | 2 (U39&hellip;) | &#9744; |
| 7 | `74HCT86` | **C** | `74xx:74HC86` | 1 (U32) | &#9744; |
| 8 | `74LVC14` | **C** | `74xx:74HC14` | 5 (U47&hellip;) | &#9744; |
| 9 | `74LVC165` | **C** | `74xx:74HC165` | 2 (U45&hellip;) | &#9744; |
| 10 | `OPA2192` | **C** | `Amplifier_Operational:OPA2196xD` | 5 (UMB_A&hellip;) | &#9744; |
| 11 | `OPA_CLAMP` | **C** | `Amplifier_Operational:OPA2196xD` | 1 (U4) | &#9744; |
| 12 | `RELAY_HV` | **C** | `Relay:Relay_SPDT` | 4 (K1&hellip;) | &#9744; |
| 13 | `RELAY_LV` | **C** | `Relay:Relay_DPDT` | 1 (KS) | &#9744; |
| 14 | `SHV` | **C** | `Connector:Conn_Coaxial` | 2 (J2&hellip;) | &#9744; |
| 15 | `TLV3202` | **C** | `Comparator:LM393` | 7 (UCC_A&hellip;) | &#9744; |
| 16 | `TPS22918` | **C** | `Power_Management:TPS22917DBV` | 4 (U14&hellip;) | &#9744; |
| 17 | `TPS3701` | **C** | `Power_Supervisor:TPS3702` | 3 (U40&hellip;) | &#9744; |
| 18 | `ISEG_N` | **A** | `iseg:APS_HV_MODULE_N` | 1 (U2) | &#9744; |
| 19 | `ISEG_P` | **A** | `iseg:APS_HV_MODULE_P` | 1 (U1) | &#9744; |
| 20 | `74AHCT125` | **B** | `74xx:74AHCT125` | 1 (U6) | &#9744; |
| 21 | `74HCT00` | **B** | `74xx:74HCT00` | 1 (U37) | &#9744; |
| 22 | `74HCT123` | **B** | `74xx:74HCT123` | 1 (U35) | &#9744; |
| 23 | `ADS1115` | **B** | `Analog_ADC:ADS1115IDGS` | 2 (UADCA&hellip;) | &#9744; |
| 24 | `BARREL` | **B** | `Connector:Barrel_Jack` | 1 (J1) | &#9744; |
| 25 | `C_BULK` | **B** | `Device:C_Polarized` | 6 (C1&hellip;) | &#9744; |
| 26 | `C_LV` | **B** | `Device:C` | 34 (C2&hellip;) | &#9744; |
| 27 | `DAC8552` | **B** | `Analog_DAC:DAC8552` | 1 (U18) | &#9744; |
| 28 | `D_SCH` | **B** | `Device:D_Schottky` | 13 (D3&hellip;) | &#9744; |
| 29 | `D_TVS` | **B** | `Device:D_TVS` | 1 (D1) | &#9744; |
| 30 | `D_ZEN` | **B** | `Device:D_Zener` | 1 (D2) | &#9744; |
| 31 | `ESP32S3` | **B** | `RF_Module:ESP32-S3-WROOM-1` | 1 (U50) | &#9744; |
| 32 | `FB` | **B** | `Device:L_Ferrite` | 2 (FB1&hellip;) | &#9744; |
| 33 | `HDR2` | **B** | `Connector:Conn_01x02_Pin` | 1 (JP1) | &#9744; |
| 34 | `HDR3` | **B** | `Connector:Conn_01x03_Pin` | 2 (J7&hellip;) | &#9744; |
| 35 | `HDR6` | **B** | `Connector:Conn_01x06_Pin` | 1 (J5) | &#9744; |
| 36 | `HDR8` | **B** | `Connector:Conn_01x08_Pin` | 2 (J6&hellip;) | &#9744; |
| 37 | `LED` | **B** | `Device:LED` | 5 (DLED1&hellip;) | &#9744; |
| 38 | `LM4040_2V048` | **B** | `Reference_Voltage:LM4040DBZ-2.0` | 1 (U22) | &#9744; |
| 39 | `LMR33620` | **B** | `Regulator_Switching:LMR33620ADDA` | 2 (U10&hellip;) | &#9744; |
| 40 | `LP5907` | **B** | `Regulator_Linear:LP5907MFX-3.3` | 1 (U13) | &#9744; |
| 41 | `LT3045` | **B** | `Regulator_Linear:LT3045xMSE` | 1 (U12) | &#9744; |
| 42 | `L_PWR` | **B** | `Device:L` | 2 (L1&hellip;) | &#9744; |
| 43 | `MTG_NOPAD` | **B** | `Mechanical:MountingHole` | 2 (MH5&hellip;) | &#9744; |
| 44 | `MTG_PAD` | **B** | `Mechanical:MountingHole_Pad` | 4 (MH1&hellip;) | &#9744; |
| 45 | `PFUSE` | **B** | `Device:Polyfuse` | 1 (F1) | &#9744; |
| 46 | `PWR_FLAG` | **B** | `power:PWR_FLAG` | 2 (#FLG01&hellip;) | &#9744; |
| 47 | `PWR_GND` | **B** | `power:GND` | 1 (#PWR01) | &#9744; |
| 48 | `Q_NMOS` | **B** | `Transistor_FET:2N7002` | 9 (QKS&hellip;) | &#9744; |
| 49 | `Q_NMOS_COIL` | **B** | `Transistor_FET:2N7002` | 4 (QK1&hellip;) | &#9744; |
| 50 | `Q_PMOS` | **B** | `Transistor_FET:Q_PMOS_GSD` | 1 (Q1) | &#9744; |
| 51 | `REF3020` | **B** | `Reference_Voltage:REF3020` | 1 (U21) | &#9744; |
| 52 | `REF5025` | **B** | `Reference_Voltage:REF5025IDGK` | 1 (U20) | &#9744; |
| 53 | `R_HV_1206` | **B** | `Device:R` | 40 (RMONAA1&hellip;) | &#9744; |
| 54 | `R_HV_2512` | **B** | `Device:R` | 40 (RBLDAA1&hellip;) | &#9744; |
| 55 | `R_HV_AXIAL` | **B** | `Device:R` | 6 (R_S_P&hellip;) | &#9744; |
| 56 | `R_LV` | **B** | `Device:R` | 153 (R1&hellip;) | &#9744; |
| 57 | `SW_PUSH` | **B** | `Switch:SW_Push` | 1 (SWB) | &#9744; |
| 58 | `SW_SPDT` | **B** | `Switch:SW_SPDT` | 2 (SW1A&hellip;) | &#9744; |
| 59 | `SW_SPST` | **B** | `Switch:SW_SPST` | 1 (SW1B) | &#9744; |
| 60 | `SW_SPST_LV` | **B** | `Switch:SW_SPST` | 7 (SW1D&hellip;) | &#9744; |
| 61 | `TP` | **B** | `Connector:TestPoint` | 36 (TP1&hellip;) | &#9744; |


# 5. What this document does NOT cover

Recorded rather than left to be discovered:

* **SA-9 placement** &mdash; NUM-09 requires the two parallel sub-strings to be PLACED at least 5 mm apart, and ARCH-18 requires each duplicated pull pair to be >= 5 mm apart. A netlist has no coordinates. This must be a PCB-generator invariant; check_netlist.py cannot see it.
* **graded string spacing** &mdash; MONITOR_AND_BLEED.md 9.1: no two HVDIV_* nodes closer than C_hv may differ by more than 150 V. That is a joint geometry+potential predicate; DRC has no 'adjacent in string' operator and a .kicad_dru pattern rule is UNSAFE because both ends of one string match the same pattern and are 800 V apart. Generator invariant only.
* **HCT vs HC** &mdash; Every 74-series part here MUST be HCT (or AHCT/LVC) because 74HC at VCC = 5 V wants VIH = 3.5 V and a 3.3 V ESP32 output does not meet it. The KiCad symbol carries no family, so this lives in the `val` string and in the BOM -- it is NOT netlist-checkable.
* **push-pull comparators** &mdash; MONITOR_AND_BLEED.md 5.4: the COLD comparators must be PUSH-PULL, never open-drain-with-pull-up, because an open-drain failure pulls up to a false COLD = 1. The borrowed LM393 symbol declares its outputs open_collector. Pin TYPE is a symbol property we do not control and ERC will not flag the mismatch.
* **relay coil polarity** &mdash; The Pickering '/5D' suffix means an INTERNAL COIL DIODE, so A1/A2 polarity is mandatory. The generic Relay_SPDT symbol has no polarity marking, so a reversed coil is netlist-legal.
* **K1/K2 orthogonal mounting** &mdash; Reed sensitivity is strongly axial; K1 and K2 must be mounted with their long axes ORTHOGONAL so one stray magnet cannot close both. Geometry, not connectivity.
* **weld detection** &mdash; SCOPE.md Q6 was never answered. This design DETECTS welds (self-tests plus per-branch monitors) and cannot PREVENT them. Nothing in a netlist can assert otherwise.
* **discharge TIME** &mdash; Assertion (b) proves a discharge PATH exists in every state. It says nothing about how long the discharge takes, which depends on C_module and C_load -- both MEASURABLE-NOW and both unmeasured. That is a numbers-probe question, not a netlist question.
* **SA-12 dump sizing** &mdash; No dump/crowbar resistor is fitted (MONITOR_AND_BLEED 7.6 recommends against one), so SA-12 is vacuously true here. If a switched dump is ever fitted the assertion must be implemented.


## Deviations and unresolved cross-document conflicts

Reproduced verbatim from `board_spec.py` section 3 so this document stands alone at the review gate:

```
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
```

Plus the deviations and unresolved cross-document conflicts recorded in `board_spec.py` section 3 (`D-1` &hellip; `D-6`). **`D-1` (bleed topology and value) and `D-4` (the ESP32 GPIO remap) both change the netlist and both need a G1 decision.**
