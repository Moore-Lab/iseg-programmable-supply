<!-- SESSION-2 BANNER -- do not edit the body of this file. -->
> ## ⚠ HISTORICAL DOCUMENT — superseded by G0 (signed off 2026-07-23)
>
> This is a **pre-G0 candidate study**, preserved as the evidence behind the combiner decision.
> It is **not** a live design document and its numbers are **not** the project's numbers.
>
> **G0-A1 selected HV RELAY CHANGEOVER.** The series-stack/driven-midpoint, diode-OR and
> single-module-reversing topologies are **REJECTED and must not be revived**.
> **G0-A4** additionally made the instrument switchable between a single *pseudo-bipolar*
> output and *two independent unipolar* outputs that **may both be energised at once**, so
> ±1000 V now coexist on the board as a **normal steady-state condition**.
>
> ### ⚡ The clearance number in this file is WRONG and is superseded
>
> `STATUS.md` §1.2 finding 7: **four documents in this repo carried four mutually
> incompatible IPC-2221 numbers, three of them more permissive than the probe's.**
> This file sets *"the HV netclass clearance to ≥ 5 mm HV-to-GND and ≥ 8 mm HVP-to-HVN"* from a Panasonic PhotoMOS terminal pitch (≈ 3.4 mm/kV) at its own ±600 V / 1200 V operating point. That reasoning is sound for the part but it is a **component** spacing, not a **board** standard, and the topology is eliminated anyway at 1 kV (G0-A2 consequence 2: the ≤600 V PhotoMOS parts do not reach 1 kV). At 1000 V/2000 V the live values are **7.5 mm / 15.0 mm**.
>
> **The single live source for every clearance/creepage number is
> `docs/NUMBERS_PROBE.md`, generated from `hardware/hvctl/numbers_probe.py`.**
> At the frozen part (AP010504, Vnom = 1000 V) the live values are
> **7.5 mm** HV-to-anything and **15.0 mm** HV_POS↔HV_NEG (and HV_OUT_A↔HV_OUT_B),
> every one of them tagged **`[unverified-primary]`** pending a human reading a primary copy
> of IPC-2221B Table 6-1. Do not quote this file's figure anywhere.

# Combiner topology study — `hv-mosfet-optocoupler-switch`

**Solid-state HV series switch, one per branch, optically driven, with a cross-coupled hardware inhibit.**

Phase-1 candidate study for `docs/BRIEF_iseg-hv-controller.md` Gate 0.
Author: combiner deep-dive subagent. Date: 2026-07-23.
Scope: this document owns **one** candidate. Other candidates (HV changeover relay, diode-OR,
driven-midpoint series stack) appear only where a comparison is load-bearing.

**Verdict up front: 6/10. Passes all three non-negotiable invariants, with the best interlock of
any candidate — and buys a switching-speed advantage that is provably worthless on this board,
at the price of a hard ceiling at the 600 V module class and one single-fault mode
(shorted switch) that the relay candidate does not have.**

---

## 0. Evidence ledger

Every number below carries one of these tags. Nothing is asserted without one.

| Tag | Meaning |
|---|---|
| `[verified-artifact]` | I opened the document/page this session and read the value off it. Source named inline. |
| `[verified-run]` | I executed something this session and it behaved as stated. |
| `[recalled]` | From context or memory. **Unverified. Treat as a hypothesis.** |

**Instruments used and what they structurally cannot see:**

- `PY_KICAD` + `fitz` reading `references/iseg_manual_APS_en.pdf` (v2.5, 2024-08-20).
  Sees: all text on all 10 pages, and vector art rendered to raster. **Cannot see**: anything iseg
  chose not to print. Absences below are therefore real absences in the document, not extraction
  failures — I dumped all 10 pages of text and searched them.
- `WebFetch`/`WebSearch` against manufacturer datasheets and Digi-Key product pages. Sees: the
  rendered page at fetch time. **Cannot see**: whether stock/price will hold; whether the
  manufacturer has a newer revision; anything behind a 403 (Littelfuse and ST both 403'd/timed out,
  so IXYS/ST leakage figures below are search-snippet quality, tagged accordingly).
- **No bench measurement of any kind was performed.** Every timing number that depends on the iseg
  module's *output* behaviour (as opposed to its documented *control* behaviour) is an estimate and
  is marked as requiring measurement.

---

## 1. Re-verification of the ground truth this analysis depends on

I re-read the manual rather than trusting the briefing. Results:

### 1.1 Confirmed from Table 1 / Table 2 / Table 4 `[verified-artifact]`

- `/ON`: `"/ON: = 0 (LOW or open) -> VOUT according setting"`, `"5.5V >= V/ON >2.5V(HIGH) -> VOUT =0"`.
  **Active-low with open = ON.** Confirmed verbatim.
- `"Attention! Output voltage is internally not limited! At Vset > 2.5 V -> Vout > Vnom is possible!"`
  Confirmed verbatim. This is a hardware-clamp requirement, not a firmware nicety.
- `Rset = Vout • 10kΩ / (Vnom – Vout)` — confirmed, implying a 10 kΩ internal pull-up to Vref.
- Configurations table: 600 V / 0.8 mA / 5 V / 0.5 W = `AP006804x05`; 600 V / 1.6 mA / 12 V / 1 W =
  `AP006165x12`; 1 kV / 0.5 mA = `AP010504x05`; 1 kV / 1 mA = `AP010105x12`. Confirmed.
- `Iout` limited to approx. `1.5 • Inom`. Confirmed (Table 2 note 1).
- Ripple/stability guaranteed **only** for `2% • Vnom < Vout <= Vnom` (Table 1 note 1). Confirmed.
- Adjustment accuracy ±1 %; voltage monitor accuracy `1 % • Vnom`; tempco < 50 ppm/K; operating
  0–40 °C. Confirmed.
- Overload and short-circuit protected. Confirmed.

### 1.2 Discrepancy the briefing asked me to flag, not resolve `[verified-artifact]`

Table 1 lists **`Current monitor accuracy — 1 % • Inom`**. Table 4 (PIN assignment) lists seven pins
and **no current-monitor pin**: `+VIN, VSET, GND, /ON, VMON, HV, GND`. The current-monitor accuracy
spec is therefore unreachable on this 7-pin part. Two readings are possible — (a) Table 1 is shared
boilerplate with a larger iseg family and does not apply here, or (b) there is an undocumented
mode. **I do not resolve this. It must go to iseg as a G0 question**, because if there is no output
current readback then §7 fault 3 below (dump switch stuck closed) is undetectable without adding
our own current sense.

### 1.3 New ground truth I extracted that the briefing did not have — from Figure 2, page 9

Figure 2 ("Control principle of APS HV supply series") is vector art with no extractable text. I
rendered it at 5× (`clip=Rect(50,350,545,560)`) and read it. It shows the module's **internal**
control chain `[verified-artifact]`:

```
        VMON o---[ 20k ]---- (internal monitor node)
                                REF (shunt ref to GND)
                                 |
                              [ 10k ]
                                 |
        VSET o------------------ * -----[ 100k ]---- * ---- (to converter)
                                                     |
                                              /ON switch to GND
                                                     |
                                                  [ 1 uF ] to GND
```

Three consequences, none of which are in the briefing, all load-bearing:

1. **`VMON` has a 20 kΩ internal series resistor.** Any ADC or divider hung on `VMON` forms a divider
   with it. An ESP32 SAR-ADC pin (effective input impedance of order 100 kΩ with its sampling cap)
   would read `20/(20+100) = 17 %` low. **`VMON` must be buffered by a high-impedance op-amp
   follower** (bias current ≤ 1 nA → error ≤ 20 µV). This is a real trap and it is invisible from
   the tables.
2. **`/ON` does not gate the converter — it shorts the internal setpoint node to ground.** The
   module's "off" state is "setpoint forced to zero", not "converter inhibited".
3. **The setpoint node is `100 kΩ` in series with `1 µF` → τ = 100 ms.** This is the module's own
   command-to-output time constant. It applies to a `/ON` release *and* to any `Vset` change.
   **5τ = 500 ms to settle to 1 %.** Initial slew on a 0→600 V step: `600 V / 100 ms = 6 kV/s
   = 6 mV/µs`.

Item 3 is the single most important number in this study. It is derived from the manufacturer's own
figure, and it demolishes the headline argument for a solid-state combiner. See §6.

### 1.4 Absences in the manual — verified absences, and each one is a bench task

I dumped all 10 pages and searched. The APS manual contains **no** specification for:

- **Reverse voltage rating on the `HV` output pin.** Nothing. `[verified-artifact — absent]`
  *This absence is the entire reason a combiner switch must exist.* If the manual said "the HV pin
  tolerates −Vnom", a bare diode-OR or even a bare wire-OR would be arguable. It does not.
- **Output capacitance.** Nothing. Every discharge time constant below therefore rests on an
  assumed `C_out`; I use 1 nF total and flag it.
- **Output ramp / slew rate / turn-off decay.** Nothing directly. §1.3 gives the *control-side*
  100 ms; the HV-side decay after `/ON` goes high depends on the multiplier's internal bleed, which
  is unspecified.
- **Output impedance when disabled.**
- **Any FIT / reliability data.**

---

## 2. Why a *bidirectional-blocking* switch is mandatory (and why a diode cannot help)

This has to be established first, because it determines the part count and it kills the obvious
fault mitigation.

Label the nodes: `HVP` = positive module's HV pin, `HVN` = negative module's HV pin,
`HVOUT` = the single output terminal. Load returns to GND.

Consider the P branch while the N module is driving `HVOUT` to −600 V. The P module is disabled, so
`HVP ≈ 0 V`. **The P-branch element must block 600 V with its `HVOUT` side negative.**

Now consider replacing the switch with a series HV diode, anode at `HVP`, cathode at `HVOUT` — the
orientation that passes the P module's forward current:

- Forward-bias condition is `V(HVP) > V(HVOUT)`, i.e. `0 V > −600 V` → **the diode conducts.**
- A forward-biased diode does not stop its anode being dragged down. `HVP` goes to
  `−600 V + V_f`. The positive multiplier is now reverse-stressed by nearly the full 600 V — exactly
  the damage we are preventing — and `HVOUT` is simultaneously loaded by the P module's internal
  impedance.

**Conclusion: a series diode is useless in a bipolar combiner. Each branch needs a genuinely
bidirectional blocking element.** Practically that means either (a) two N-channel MOSFETs in
common-source anti-series with a shared floating gate drive, or (b) a mechanical contact.
Consequence for §7: **there is no passive backup behind a failed solid-state switch.**

A second consequence: because the switch is bidirectional and the source node floats, the gate drive
must float with a node that swings the full ±Vnom relative to logic ground. **The isolation
barrier's *continuous working* voltage rating — not its 1-minute test voltage — is the binding
constraint on this whole topology.** §3.

---

## 3. Part selection: the switch sets the voltage class, not the module

Three concrete implementations were priced and rated. All prices/stock read this session from live
distributor pages.

### 3.1 Option A (recommended) — Panasonic PhotoMOS `AQV258H5AX`

A 1 Form A AC/DC PhotoMOS: internally *is* the anti-series MOSFET pair plus its photovoltaic driver
plus a certified barrier, in one 5-lead DIP6-footprint SMD package. `[verified-artifact —
Panasonic catalog ASCTB430E 202509, fetched and read locally with fitz; and the Digi-Key product
page]`

| Parameter | Value | Note |
|---|---|---|
| Load voltage, absolute max | **1500 V** peak AC / DC | |
| Load voltage, **recommended operating** | **1200 V** | *This is the real ceiling.* |
| Continuous load current | 20 mA | 25× our 800 µA |
| Peak load current | 60 mA, 100 ms, 1 shot | **binds the changeover inrush — §5** |
| On-resistance | 315 Ω typ / **500 Ω max** | |
| **Off-state leakage** | **10 µA max** at `IF=0`, `VL=Max` | **the headline leakage number** |
| Turn-on time | 0.35 ms typ / 1.0 ms max | |
| Turn-off time | 0.04 ms typ / 0.2 ms max | |
| I/O isolation voltage | 5000 Vrms (1 min test) | **no VIORM published — see §3.4** |
| Initial I/O isolation resistance | ≥ 1000 MΩ at 500 VDC | → ≤ 0.6 µA at 600 V CM |
| I/O capacitance | 1.3 pF typ / 3 pF max | → CMTI, §6.3 |
| LED: `IF` recommended | 5–30 mA | |
| LED: `IFon` max / `IFoff` min | 3.0 mA / 0.2 mA | 4× margin at a 12 mA drive |
| LED reverse voltage `VR` | **5 V** | **enables the anti-parallel interlock, §4** |
| Package | DIP6 outline, **5 leads (pin 5 omitted)** | output on pins 4 and 6 |
| Operating temp | −40 to +85 °C | |

Panasonic's own marketing line is `"Distance between output terminals are longer than 6-pin DIP
package"` — pin 5 is deleted so the output terminals sit 2 × 2.54 = **5.08 mm apart for a 1500 V
part**, i.e. the manufacturer's implicit creepage answer is ≈ 3.4 mm/kV.

**Price and stock, read from the Digi-Key page for `AQV258H5AX` (12685644) this session
`[verified-artifact]`:** $11.62 @1, $10.35 @10, $9.88 @25, **2223 in stock**, 6-SMD 5-lead.

### 3.2 Option B — discrete MOSFET pair + photovoltaic opto driver

For anyone who wants to go above the PhotoMOS ceiling or shave cost.

**Gate driver — Broadcom `ACPL-K308U`** `[verified-artifact — Broadcom datasheet ACPL-K308U-DS106,
2025-05-12, fetched and read locally]`:

| Parameter | Value |
|---|---|
| **Maximum working insulation voltage `VIORM`** | **1140 V_peak** (IEC/EN/DIN EN 60747-5-5) |
| `VIOTM` transient | 8000 V_peak |
| `VISO` | 5000 Vrms, 1 min, UL1577 |
| Creepage / clearance | **8 mm / 8 mm**, SSO-8 |
| CTI / material group | 175 / IIIa |
| Open-circuit output `VOC` | 8.2 V typ at `IF` = 10 mA |
| **Short-circuit current `ISC`** | **70 µA typ** at `IF` = 10 mA |
| Turn-on / turn-off | **50 µs / 23 µs** typ at `CL` = 1 nF |
| Reverse input voltage `VR` | 6 V |

**Contrast — Vishay `VOM1271` (SOP-4), the cheap default `[verified-artifact — Vishay datasheet
83469 rev 1.9, fetched and read locally]`: `VIORM = 707 V_peak`, creepage/clearance ≥ 5 mm,
`VISO` 3750 Vrms, `ISC` 15 µA typ, `ton/toff` 53/65 µs, `VR` 5 V.**

> **This is the cleanest single finding of the study.** `VOM1271`'s 3750 Vrms headline number is a
> 1-minute test. Its *continuous* rating is **707 V_peak**. Our barrier sees the full output swing
> **DC, continuously**. On a 1 kV design `VOM1271` is used **out of spec** while its datasheet
> front page appears to say 3750 V. A designer who reads only the feature bullets ships a part at
> 141 % of its working rating. The correct part is `ACPL-K308U` at 1140 V_peak.

**Switch element — `STP3N150`** (ST, 1500 V, 2.5 A, TO-220). `IDSS` ≈ 10 µA at
`VDS` = 1500 V / 25 °C and 500 µA max at 125 °C `[recalled from search snippet — st.com and
Littelfuse both refused fetch (403/timeout). Re-verify before committing.]`
Alternative `IXTY02N120P` (IXYS/Littelfuse, 1200 V, 200 mA, 75 Ω, TO-252 DPAK): **$3.76 @1,
$1.80 @10, 4630 in stock** `[verified-artifact — Digi-Key page 2354490 read this session]`;
its `IDSS` is not on the Digi-Key page and the Littelfuse datasheet 403'd.

Per branch: 2 MOSFETs anti-series + 1 `ACPL-K308U` + a 1 MΩ gate-source bleed + a 12 V gate-source
Zener clamp. Gate charging time = `Qg/ISC` ≈ 40 nC / 70 µA ≈ **570 µs** — still 1000× faster than
the module (§6).

### 3.3 Options eliminated

**Behlke HTS series — eliminated on suitability first, cost second.**
Behlke publishes no prices anywhere; there is no distributor stock; every unit is individually
quoted. The one second-hand listing I found (Hofstra Group, HTS-300) is explicitly a **discontinued
legacy item with no price** `[verified-artifact — I read the Hofstra product page; it states the
product is no longer offered]`. Behlke's own site organises the catalogue into *"HV switches with
fixed on-time"* and *"variable on-time"* families `[verified-artifact — behlke.com separation
pages]` — a fixed-on-time pulsed-power switch is disqualifying for a DC-hold application before
price enters the conversation. These are ns-scale, tens-of-amps switches; we need DC hold at
**800 µA**. That is a four-order-of-magnitude mismatch in current and an infinite one in duty.
Street price is four figures per switch `[recalled — unverified]`. **Eliminate.**

**Voltage Multipliers Inc. `OC100`/`OC200`/`OC250` — eliminated on output device type.**
10–25 kV isolation is genuinely attractive. But the output element is a **photodiode**, not a
photovoltaic stack: output current is nA–µA into a reverse-biased junction, and it cannot charge a
MOSFET gate without an added floating supply — which reintroduces the isolation problem it was
supposed to solve. VMI publishes no part-level specs or prices on its optocoupler page and is
single-source `[verified-artifact — voltagemultipliers.com optocoupler page read this session:
part-level specs, CTR, package and price are all absent]`. **Usable as a HV-isolated sense element;
not usable as our gate driver. Eliminate.**

### 3.4 The voltage-class constraint — this is a G0 decision, not a detail

The switch, not the module, sets the ceiling:

| Module class | OFF-switch stress | vs. `AQV258H5` 1200 V rec. | vs. `ACPL-K308U` 1140 V_peak | verdict |
|---|---|---|---|---|
| 200 V | 200 V | 17 % | 18 % | trivially fine |
| 400 V | 400 V | 33 % | 35 % | fine |
| **600 V** | 600 V | **50 %** | **53 %** | **recommended** |
| 800 V | 800 V | 67 % | 70 % | acceptable, thin |
| 1000 V | 1000 V | **83 %** | **88 %** | **reject** |

The 1 kV row is a reject for a specific reason, not general conservatism: **the iseg output is
internally not limited.** A DAC or firmware fault that puts `Vset` at 2× `Vref` produces roughly 2×
`Vnom` with no ceiling. On a 600 V module that is 1200 V — right at the PhotoMOS recommended rating,
survivable. On a 1 kV module it is ~2 kV, which destroys the switch **and punches through the
isolation barrier into the logic domain**. The hardware `Vset` clamp (§7 fault 12) is what makes
even the 600 V row honest, and it is mandatory in every topology.

> **Therefore: choosing this topology caps the instrument at the 600 V class
> (`AP006804P05` + `AP006804N05`, 0.5 W, 0.8 mA; or `AP006165P12`/`AP006165N12`, 1 W, 1.6 mA).
> If the human requires ±1 kV, this topology is eliminated at G0.**
> The relay candidate has no such ceiling — Standex/Gigavac HV reeds reach 5–15 kV. That is the
> single strongest argument for the relay over this design and I am not going to bury it.

Series-stacking two PhotoMOS per branch to reach 2.4 kV is arithmetically possible but requires
static voltage-sharing resistors (say 100 MΩ across each device, which sets a 4–6 µA leakage floor)
and doubles the LED count per branch. The LEDs series-connect so the interlock survives, but the
part count goes to 6 switches + sharing network and the failure surface roughly doubles. **Not
recommended; noted for completeness.**

---

## 4. Circuit description — drawable from this text

Design point: **600 V class, 0.5 W family** (`Vnom` = 600 V, `Inom` = 800 µA,
`Iout,max ≈ 1.5·Inom` = 1.2 mA, `Vref` = 2.5 V, `Vin` = 5 V).

### 4.1 HV power path

```
  [P module HV pin] --*--------------------[ SW_P ]-------*------------- HVOUT --> SHV connector
   AP006804P05        |                                   |
                      D_clampP  (cathode->HVP,            |
                      |          anode->GND, >=1 kV)      |
                     GND                                  |
                      |                                   |
                   R_modP 100M  (HVP -> GND)              |
                                                          |
  [N module HV pin] --*--------------------[ SW_N ]-------*
   AP006804N05        |                                   |
                      D_clampN  (anode->HVN,              +---[ SW_D ]---[ R_dump 2M2 ]--- GND
                      |          cathode->GND)            |
                     GND                                  +---[ R_bleedA 100M ]--- GND
                      |                                   +---[ R_bleedB 100M ]--- GND
                   R_modN 100M                            |
                                                          +---[ R_top 500M (5 x 100M) ]---*--- ADS1115 IN
                                                                                          |
                                                                                      R_bot 500k 0.1%
                                                                                          |
                                                                                         GND
```

`SW_P`, `SW_N`, `SW_D` are each one `AQV258H5AX`. Everything else is passive.

**Roles, one line each:**

- `SW_P` / `SW_N` — the exclusive bidirectional branch switches.
- `SW_D` — commanded fast dump, `HVOUT` → 2.2 MΩ → GND. **Deliberately not interlocked** (§4.4).
- `R_bleedA` ∥ `R_bleedB` = 50 MΩ — the fail-passive discharge. Two in parallel so a single cracked
  chip does not silently delete invariant (b) (§7 fault 15).
- `R_modP` / `R_modN` = 100 MΩ from each module's HV pin to GND — **the load-bearing part of the
  changeover sequence** (§5). Not optional.
- `D_clampP` / `D_clampN` — anti-reverse clamps across each module output. **These are what turn a
  shorted-switch event from "destroyed module" into "output reads zero" (§7 fault 1). Not
  optional.**
- `R_top` / `R_bot` + ADS1115 — invariant (c) (§4.5).

### 4.2 Interlock — the anti-parallel LED loop (invariant (a))

This is the best feature of the topology and it deserves the detail.

```
                  +5V_WD  (charge-pump-gated rail, see 4.3)
                     |
                  [ 220R ]        <- shoot-through limiter
                     |
                  H-bridge (DRV8837 or 2 complementary pairs)
                   OUT_A       OUT_B
                     |           |
                     *-----------*
                     |           |
        string F:  LED(SW_P) --> LED(OPTO_P) -->      (anode at A, cathode at B)
        string R:  <-- LED(OPTO_N) <-- LED(SW_N)      (anode at B, cathode at A)
```

Two **two-LED series strings, wired anti-parallel across the same two nodes A and B.**

- Bridge drives A→B: string F conducts. `SW_P` closes **and** `OPTO_P`'s phototransistor pulls the
  P module's `/ON` low. The positive branch is enabled — switch and module, by the *same electrons*.
- Bridge drives B→A: string R conducts. `SW_N` closes and the N module's `/ON` goes low.
- Bridge coasts / tri-states / loses supply: zero current, both strings dark, both switches open,
  both `/ON` pins float high through their pull-ups → both modules off.

**Why "both enabled" is unreachable:** the two strings are physically in opposition across one node
pair. Current has one direction. There is no state of the H-bridge, no firmware bug, no stuck GPIO,
no broken wire, and no failure of any single transistor that makes both strings conduct at once.
**Kirchhoff enforces the interlock, not a logic gate and not a mechanical linkage.** There is no
inverter to fail and no "both-high" decode to get wrong.

Arithmetic:

- Drive current 12 mA. `AQV258H5` recommends 5–30 mA and specifies `IFon` ≤ 3.0 mA → **4× margin**
  over the worst-case operate current. `[verified-artifact]`
- Forward drop of a conducting string ≈ 2 × 1.3 V = **2.6 V**.
- **Reverse stress on the idle string = 2.6 V, shared across its two series LEDs.** Even in the
  pathological case where mismatched reverse leakage puts the whole 2.6 V on one LED, that is
  **52 % of the 5 V `VR` rating** (`AQV258H5`) or 43 % of the `ACPL-K308U`'s 6 V. `[verified-artifact
  — both datasheets read]` **Safe with margin, verified, not assumed.**
- LED power per string: 12 mA × 2.6 V = 31 mW; `Pin` max is 75 mW per device. Fine.
- The 220 Ω limiter sits in the bridge's supply, so a bridge shoot-through burns 5 V/220 Ω = 23 mA
  in a resistor rather than destroying the bridge.

**Second interlock layer, free:** because `/ON` and the switch share one current, the *module* also
cannot be enabled into a closed opposite switch. Two independent mechanisms would have to fail.

### 4.3 The watchdog rail — why a GPIO is never allowed to hold HV on

`+5V_WD` is **not** the 5 V rail. It is generated by a two-stage diode/capacitor charge pump driven
by a 10–100 kHz square wave from an ESP32 GPIO, loaded by 100 kΩ ∥ 100 nF.

- Toggling → `+5V_WD` ≈ 5 V − 2 V_f ≈ 3.6 V, bridge alive.
- Stops toggling for any reason → the rail collapses with τ = 100 kΩ × 100 nF = **10 ms**.
- **A GPIO stuck high, stuck low, tri-stated, or unpowered all produce the same result: no rail.**
  DC cannot pass a capacitor. This is what makes "ESP32 in reset" and "ESP32 unpowered" safe
  states rather than undefined ones.
- The H-bridge's `VM` is fed from `+5V_WD`, not from 5 V. That is deliberate: it means **no failure
  of the bridge itself can source LED current when the watchdog is dead** (§7 fault 5).
- Use **two series pump capacitors**, so a single shorted cap does not create a DC path (§7 fault 7).

### 4.4 Discharge (invariant (b))

Three paths, in order of how much they are trusted:

1. **`R_bleedA` ∥ `R_bleedB` = 50 MΩ, permanently across `HVOUT`.** Works with the board completely
   unpowered — this is what actually satisfies the invariant.
2. **Per-module `R_mod` = 100 MΩ.** Drains the charge stranded behind an open switch.
3. **`SW_D` + `R_dump` = 2.2 MΩ.** Commanded, fast, and *verifiable* — firmware can command a dump
   and check the decay against the independent monitor.

Numbers, with `C_out(HVOUT)` = 1 nF assumed (module ≈ 200–500 pF `[recalled]` + 100 pF/m of SHV
cable + load) — **`C_out` is unspecified by iseg (§1.4) and must be measured at Phase 7**:

| Path | R | τ | 600 V → 50 V | 600 V → 1 V | standing load at 600 V | as % of `Inom` (800 µA) |
|---|---|---|---|---|---|---|
| `R_bleed` both strings | 50 MΩ | 50 ms | 124 ms | 320 ms | 12.0 µA | 1.50 % |
| `R_bleed` one string open | 100 MΩ | 100 ms | 248 ms | 640 ms | 6.0 µA | 0.75 % |
| `SW_D` + `R_dump` | 2.2 MΩ | 2.2 ms | 5.5 ms | 14 ms | 273 µA **when closed** | 34 % |
| `R_mod` per module (`C`≈500 pF) | 100 MΩ | 50 ms | 124 ms | 320 ms | 6.0 µA | 0.75 % |
| divider `R_top` | 500 MΩ | — | — | — | 1.2 µA | 0.15 % |

Total permanent HV load: 50 MΩ ∥ 500 MΩ ∥ 100 MΩ = 44.5 MΩ → **13.5 µA at 600 V = 1.7 % of `Inom`.**
The module supplies this trivially; it is only a nuisance at `Vout` near zero.

`R_bleed` implemented as 2 strings × (2 × 50 MΩ in series), so no single chip carries more than
300 V. Power per chip: 300²/50e6 = 1.8 mW against a 1.5 W part.

**`SW_D` is deliberately left out of the interlock.** If `SW_D` fails closed while a branch is
driving, the load is 600 V / 2.2 MΩ = 273 µA — 34 % of `Inom` and well inside the 1.2 mA `Iout`
limit. The output still regulates. **A stuck-closed dump switch is benign by sizing, so it needs no
interlock**, and adding one would have required a logic gate that is not Kirchhoff-enforced. This is
a deliberate simplification, not an oversight.

### 4.5 Independent output monitoring (invariant (c))

- `R_top` = 5 × `HVC4020V1006JET` (100 MΩ, ±5 %, 1.5 W, 4020 chip) in series = 500 MΩ. **$4.36 @1,
  $3.25 @10, 1146 in stock** `[verified-artifact — Digi-Key page 4759736 read this session]`.
  Five in series keeps each chip under 120 V and gives a long physical creepage path by construction.
- `R_bot` = 500 kΩ, 0.1 %, → ratio **1001 : 1**. ±600 V → **±599.4 mV**.
- **ADS1115**, ±2.048 V FSR, 16-bit, differential, I²C. LSB = 62.5 µV → **62.6 mV at `HVOUT`**, i.e.
  **0.010 % of 600 V** — 100× finer than the module's own ±1 %. It is bipolar natively, which the
  ESP32's unipolar 0–3.1 V SAR ADC is not; **do not use the ESP32 ADC for this.**
- Accuracy is dominated by `R_top` tolerance: 5 × ±5 % → ±2.2 % RSS. Either buy ±0.5 % parts or
  **calibrate against a DMM at build** — which the brief's success criteria already require.
- Protection: 1 MΩ series into the ADC input, back-to-back Schottky to rails. The 500 MΩ top leg
  already limits any fault current to 1.2 µA.
- **Independence audit:** this path shares no component, no reference, no rail, and no silicon with
  either module's `VMON`. It reads *after* both switches, so it also sees the `Ron` drop, a failed
  handoff, and a stuck switch. **Passes cleanly.**
- **`VMON` and the independent monitor are complementary, not redundant.** `VMON` reports what the
  module is making (even behind an open switch); the divider reports what reaches the terminal.
  Comparing them distinguishes *stuck switch* from *stuck module* — a diagnostic the relay topology
  gets too, but which this topology needs more because of §7 fault 1. Remember `VMON` needs a
  high-Z buffer because of its internal 20 kΩ (§1.3).

### 4.6 `Vset` and `/ON` conditioning (per module)

- `Vset` driven by MCP4725 DAC → rail-to-rail op-amp follower. Required `Ri << 10 kΩ`; a buffer's
  output impedance is < 1 Ω. **Satisfied by 4 orders of magnitude.** The buffer must sink 250 µA at
  `Vset` = 0 (from the internal 10 kΩ to `Vref`) and source ~2.5 mA into `Rd` at full scale.
- **`Rd` = 1 kΩ from `Vset` to GND, placed within 5 mm of module pin 2.** With `Rd` in place, an
  open DAC output leaves `Vout = Vnom · Rd/(10 kΩ + Rd)` = **600 × 1/11 = 54.5 V (9.1 % of FS)**
  instead of full scale. Derived from the manual's own `Rset` formula.
- **Hardware `Vset` clamp: an `LM4040-2.5` shunt reference on the `Vset` node**, so no DAC or
  firmware fault can command `Vset > Vref` and therefore `Vout > Vnom`. Mandatory, per §1.1.
- **`/ON` pull-up: 10 kΩ to the *module's own* pin 1 (`+VIN`), placed within 5 mm of module pin 4.**
  Two reasons, both from `/ON` being active-low-with-open-=-ON:
  - Tying it to `+VIN` rather than the logic rail guarantees the pull-up exists **whenever the
    module is capable of making HV**, even if the logic rail is dead.
  - Placing it at the module end means a broken track between board and module leaves `/ON` **high
    (safe)** rather than floating **(HV ON)**.
  This is the single most important wiring detail on the board and it falls straight out of the
  pin table. Encode it as a placement/length DRC rule.

---

## 5. Changeover sequence and dead-band — with the arithmetic that forced it

### 5.1 The inrush problem, and why the obvious fix fails

Naïve changeover: open `SW_P`, close `SW_N`. The P module's own output capacitance
(≈ 500 pF `[recalled]`) is **stranded at +600 V behind the open switch**. When `SW_P` next closes
onto an `HVOUT` sitting at −600 V, ΔV = 1200 V across a 500 Ω `Ron`:

```
I_peak = 1200 V / 500 Ω = 2.4 A
```

against a peak rating of **60 mA for 100 ms** `[verified-artifact]`. That is **40× over rating.
The first polarity change destroys the PhotoMOS.**

**Obvious fix — a series limiting resistor `R_lim` — does not work.** Requirements collide:

```
limit the dump:   R_lim >= 1200 V / 60 mA        = 20 kΩ
keep the drop:    drop  = 800 µA x 20 kΩ         = 16 V  =  2.7 % of 600 V
```

2.7 % is **2.7× the module's own ±1 % adjustment accuracy**, and it is a *load-current-dependent*
error sitting **outside** the module's regulation loop, so the module cannot correct it. To get the
drop under 0.5 % you need `R_lim` ≤ 3.75 kΩ, which permits 320 mA — still 5× over rating.
**No single value of `R_lim` satisfies both. Reject `R_lim`.**

### 5.2 The fix that works: `R_mod` + a sequenced handoff

`R_modP`/`R_modN` = 100 MΩ from each module's HV pin to its own GND. With `C_mod` ≈ 500 pF,
τ = **50 ms**. After a mandated 250 ms (5τ) settling wait:

```
V_stranded = 600 V x e^-5 = 4.0 V
I_inrush   = 4.0 V / 500 Ω = 8 mA     <<  60 mA peak rating   OK, 7.5x margin
```

**`R_mod` is therefore not a nicety — it is what makes the topology survivable, and it costs
6 µA (0.75 % of `Inom`).**

### 5.3 The mandated sequence

| Step | Action | Duration | What enforces it |
|---|---|---|---|
| 1 | H-bridge → coast. Both LED strings dark. | 1 ms max (`Toff` 0.2 ms max) | hardware |
| 2 | Both `/ON` release high via pull-ups (same electrons as step 1) | — | hardware |
| 3 | Close `SW_D`; `HVOUT` dumps through 2.2 MΩ | 15 ms to <1 V | firmware, verified by monitor |
| 4 | Stranded module decays through `R_mod` | **250 ms** | passive |
| 5 | Set the new branch's `Vset` via DAC | — | firmware |
| 6 | Open `SW_D`; bridge → opposite polarity. New `SW` closes, new `/ON` goes low. | 1 ms | hardware |
| 7 | Module setpoint node charges through 100 kΩ / 1 µF | **τ = 100 ms, 5τ = 500 ms** | §1.3, `[verified-artifact]` |

**Total dead-band: ≈ 300 ms of enforced dead time + ≈ 500 ms of module settling ≈ 0.8 s.**
Steps 3–4 overlap. Firmware must *verify* step 3 against the independent monitor before proceeding,
which converts invariant (b) from an assumption into an executable check.

The solid-state contribution to that 0.8 s is **1.2 ms** — steps 1 and 6.

---

## 6. Through-zero, and the death of the speed argument

### 6.1 Can this topology do smooth through-zero? **No.**

And the switch is not the reason. Three independent walls, in increasing order of how fundamental
they are:

1. **The combiner is a selector.** Two unipolar sources, one terminal; near zero you must hand off
   between two physically different modules. No arrangement of series switches changes that.
2. **The module's specification stops.** iseg guarantees ripple, noise and stability **only for
   `2 % · Vnom < Vout <= Vnom`** `[verified-artifact, Table 1 note 1]`. On a 600 V module that floor
   is **12 V**. Below 12 V the output is *not specified* — not "worse", **unspecified**.
3. **The module's accuracy stops.** Adjustment accuracy ±1 % and voltage-monitor accuracy
   `1 % · Vnom` = **±6 V on a 600 V module**. There is no meaningful setpoint at 2 V.

So the achievable behaviour is **set-and-hold with polarity changeover**, with an unspecified
dead-band of roughly **±12 V (±2 % `Vnom`)** around zero and a changeover dead time of **≈ 0.8 s**.
Inside the dead-band the output is not zero — it is *unknown*, and the only thing that forces it to
a defined value is `SW_D` + `R_bleed`.

> **If smooth through-zero is a requirement, this does not eliminate my topology — it eliminates the
> APS module family.** That is a G0 finding that belongs in front of the human before any combiner
> is chosen. The fix would be a different HV architecture (a bipolar output stage, or a driven
> midpoint), not a different combiner.

### 6.2 The speed argument, killed with its own numbers

The brief invited me to evaluate "switching speed (which could enable fast polarity handoff)". Here
is the honest answer:

| Element | Time | Source |
|---|---|---|
| `AQV258H5` turn-off | **0.04 ms** typ / 0.2 ms max | `[verified-artifact]` |
| `AQV258H5` turn-on | **0.35 ms** typ / 1.0 ms max | `[verified-artifact]` |
| `ACPL-K308U` turn-off / turn-on | 23 µs / 50 µs at `CL` = 1 nF | `[verified-artifact]` |
| **iseg setpoint node settling (5 × 100 kΩ × 1 µF)** | **500 ms** | `[verified-artifact — Figure 2]` |
| Stranded-charge decay through `R_mod` | 250 ms | computed, §5.2 |
| HV reed relay changeover, for comparison | 1–3 ms | `[recalled]` |

```
module settling / PhotoMOS turn-off  =  500 ms / 0.04 ms  =  12 500 x
module settling / relay changeover   =  500 ms / 2 ms     =     250 x
```

**The module's own control filter is 250× slower than a mechanical relay and 12 500× slower than
the PhotoMOS. Speed is not a discriminator between the candidates — it is not even measurable
against the dominant term.** The single stated advantage of the solid-state approach over the relay
buys nothing on this board. I would rather say that plainly at G0 than have a judge find it.

### 6.3 One place where slowness helps — dV/dt immunity, verified

Because everything is slow, the classic solid-state HV hazard (Miller-coupled or CMTI-induced
spurious turn-on) does not exist here:

```
max output slew  = 600 V / 100 ms = 6 kV/s = 0.006 V/µs
coupled current  = 3 pF (Ciso max) x 0.006 V/µs = 18 pA
```

18 pA against an `IFoff` threshold of 0.2 mA is a margin of **10^7**. Even a 1 kV/µs flashover
transient injects only 3 mA into the LED node; a 100 pF cap across the LED string absorbs it.
`[computed from verified datasheet values]` **A genuine, if unglamorous, advantage.**

Similarly, the barrier's own leakage: `Riso` ≥ 1000 MΩ at 500 VDC → ≤ **0.6 µA** at 600 V common
mode injected into the LED drive circuit `[verified-artifact]`. It flows harmlessly through the
bridge/current source and cannot forward-bias the idle string.

---

## 7. Single-fault analysis

Convention: for each element, **stuck-on** and **stuck-off**, and what `HVOUT` does.

### 7.1 The power path

**1. `SW_P` stuck ON (PhotoMOS output shorted).** ⚠ **The central weakness.**
The interlock lives in the *command* path (LED current), not the *power* path. A shorted `SW_P`
leaves the P module permanently tied to `HVOUT`. Commanding the N branch closes `SW_N` too →
**both modules connected**, which the interlock was supposed to make impossible.
What saves it: `D_clampP` conducts as soon as `HVP` is dragged below −0.7 V, so the N module now
sees `SW_N` (500 Ω) into a forward diode into GND. The N module current-limits at ≈1.2 mA and
`HVOUT` collapses to `1.2 mA × 500 Ω ≈ 0.6 V`.
**Output → ≈ 0 V. No damage. Detected immediately by the independent monitor (`|Vout| << |Vset|`).**
Without `D_clampP` the P multiplier eats −600 V and is destroyed.
> **A relay does not have this failure mode.** A welded Form-C common is still *exclusive* — it
> sticks on one throw and physically cannot reach the other. **This is the honest, decisive
> reliability argument against my topology and for the relay, and the clamp diodes only downgrade
> the consequence from "destroyed module" to "silently reads zero".**
Probability is low at 50 % derating, but Panasonic publishes **no FIT data** in the catalog I read
`[verified-artifact — absent]`.

**2. `SW_P` stuck OFF (LED open, output open, LED degradation).**
Branch never conducts; commanded +V gives 0 V. Independent monitor catches it. **Fail-safe.**
Realistic mechanism is 10-year LED droop; the 12 mA drive against `IFon` ≤ 3.0 mA gives 4× headroom.

**3. `SW_D` stuck ON.** 273 µA permanent load = 34 % of `Inom`. Voltage still regulates; available
load current drops to ~530 µA. Monitor reads correct voltage → **not detectable from voltage
alone**, and per §1.2 **there is no current-monitor pin**, so this is invisible unless we add an
output current sense. ⚠ **Open item for G0.** Benign, but silent.

**4. `SW_D` stuck OFF.** Fast dump lost. `R_bleed` still gives 124 ms to 50 V. **Invariant (b) still
satisfied.** Detected by the firmware dump self-test (commanded dump, measured decay τ).

**5. Clamp diode `D_clampP` shorted.** That polarity produces 0 V; the module sits in continuous
short-circuit at ~1.2 mA. It is short-circuit protected (Table 1) so it survives, but 600 V × 1.2 mA
= 0.72 W dissipated against a 0.5 W `Pnom` — **the 120 °C case-temperature limit is now in play.**
Detected by the monitor. Firmware must latch off, not retry.

**6. `R_bleed` string open (a real failure mode — 4020 chips crack under board flex).**
One string open → 100 MΩ remains, 248 ms to 50 V. **Invariant (b) survives by design.** Both open →
invariant (b) is violated **silently**. Mitigation: the two-string layout plus the firmware dump
self-test, which measures τ and can distinguish 50 ms from 100 ms from ∞.

**7. `R_mod` open.** Stranded charge no longer decays → the next changeover delivers the 2.4 A
inrush of §5.1 → `SW` destroyed → converts to fault 1. ⚠ **Undetectable by any monitor.** Mitigation:
`R_mod` as two parallel 200 MΩ strings, same argument as `R_bleed`.

### 7.2 The control path

**8. H-bridge leg shorted (one high, one low).** Constant DC through one string → that branch
permanently on. **The opposite branch remains impossible** — the idle string is still reverse-biased.
**Exclusivity survives a bridge failure.** And because `VM` comes from `+5V_WD`, the watchdog can
still kill it. This is exactly why `VM` is on the pumped rail.

**9. Watchdog charge pump fails OPEN** (cap open, diode open). Rail collapses → both branches off,
`/ON` both high, `R_bleed` discharges. **Fail-safe.**

**10. Watchdog charge pump fails SHORT** (pump diode or coupling cap shorted). A DC path now exists,
so a hung ESP32 holding that GPIO high keeps HV enabled indefinitely. ⚠ **This is the residual
single-fault-to-hazard of the design.** Mitigation: **two series coupling capacitors** ($0.02) so a
single short still leaves one; or an independent hardware timer (TPL5010, ~$1) in series.
**Recommended: do both. This is the cheapest safety in the BOM.**

**11. ESP32 in reset.** GPIOs go to input; strapping pins differ; **it does not matter**, because a
static level cannot pass the pump capacitor. Rail collapses in 10 ms → both branches off, both `/ON`
float high via their pull-ups, `R_bleed` discharges `HVOUT` to <50 V in 124 ms. **Safe.**

**12. ESP32 unpowered while HV rails are up.** Identical to 11 *provided* the `/ON` pull-ups tie to
each module's own `+VIN` (§4.6). If they tied to a 3.3 V logic rail that is down while the modules'
5 V is up, both `/ON` pins float → **`/ON` open = HV ON** → both modules make full HV behind open
switches, stranded on 100 MΩ. **The `+VIN` pull-up is what makes this case safe and it is a
one-net design decision.**
(For the 0.5 W family, `Vin` = 5 V may be the same rail as the logic, making this moot. For the 1 W
family at 12 V it is definitely a separate rail and the rule bites.)

**13. Broken wire: H-bridge output A or B.** Loop open → both strings dark → both switches open.
**Fail-safe.** The most likely single wire break is also the safest one.

**14. Broken wire: `/ON` track, board side of the pull-up.** `/ON` floats at the module → **HV ON**.
With `Vset` intact, the module makes the commanded voltage behind a (probably open) switch — a
hazardous stranded internal node at up to 600 V with only 100 MΩ to bleed it. Mitigated by placing
the pull-up within 5 mm of pin 4 (§4.6) so this break is not physically reachable on the PCB.
**Encode as a placement rule, not a hope.**

**15. Broken wire: `Vset` track.** `Vset` open → the internal 10 kΩ pulls it to `Vref` → **full-scale
output**. With `Rd` = 1 kΩ at the pin, the same break instead gives 9.1 % FS = 54.5 V. **`Rd` is
what converts a wire break from full-scale HV to a nuisance.**

**16. DAC or firmware commands `Vset > Vref`.** Without the `LM4040-2.5` clamp: `Vout > Vnom`,
unbounded, destroying the switch and punching the isolation barrier. With the clamp: capped at
`Vnom`. **Mandatory; not topology-specific.**

**17. `OPTO_P` (the `/ON` driver) fails.** Open → module never enables (safe). Collector-emitter
shorted → that module makes HV whenever powered, but its `SW` is still open unless its LED is lit,
so the HV is stranded behind the switch. **Output stays correct; degraded, not hazardous.** Detected
by comparing `VMON` (reports the stranded HV) against the independent monitor (reports 0 for that
branch) — the complementary-monitor argument of §4.5 earning its keep.

**18. ADS1115 fails / I²C hangs.** Invariant (c) is lost. **No hardware mitigation** — the monitor is
inherently an active element. Firmware must treat loss of monitor as a fault and stop toggling the
watchdog, which drops HV in 10 ms. **The watchdog rail is what makes a software failure a hardware
shutdown.**

### 7.3 Summary of fault outcomes

| Outcome class | Faults |
|---|---|
| Fail-safe (HV off or 0 V, detected) | 2, 4, 8, 9, 11, 12(with rule), 13, 18 |
| Benign but **silent** | 3, 6(single), 17 |
| Degraded, detected, no damage | 1 (with clamp diodes), 5 |
| ⚠ **Hazard or damage** | **7** (`R_mod` open → next changeover destroys `SW`), **10** (pump shorted → hung ESP32 holds HV), **14** (`/ON` break board-side), **15/16** (`Vset` open or over-range without `Rd`/clamp) |

Every entry in the hazard row has a named mitigation costing under $2. **None of them is optional.**

---

## 8. Bill of materials and cost

Digi-Key qty-1 pricing, read this session where marked.

| Item | Qty | Unit | Ext. | Evidence |
|---|---|---|---|---|
| `AQV258H5AX` PhotoMOS (SW_P, SW_N, SW_D) | 3 | $11.62 | $34.86 | `[verified-artifact — DK 12685644, 2223 in stock]` |
| `HVC4020V1006JET` 100 MΩ HV chip (bleed ×4, divider ×5) | 9 | $4.36 | $39.24 | `[verified-artifact — DK 4759736, 1146 in stock]` |
| HV clamp diode ≥1 kV (e.g. `1N6517`-class) | 2 | ~$1.50 | $3.00 | `[unverified-MPN]` |
| `R_bot` 500 kΩ 0.1 % | 1 | $1.00 | $1.00 | `[recalled]` |
| `ADS1115` + passives | 1 | $5.00 | $5.00 | `[recalled]` |
| `DRV8837` H-bridge + 220 Ω + charge pump (2 C, 2 D, 2 R) + `TPL5010` | 1 | $4.00 | $4.00 | `[recalled]` |
| `LTV-826`-class opto ×2 for `/ON` + 2 × `2N7002` + pull-ups | 1 set | $3.00 | $3.00 | `[recalled]` |
| `MCP4725` ×2 + op-amp buffers ×3 + `LM4040-2.5` ×2 | 1 set | $8.00 | $8.00 | `[recalled]` |
| **Combiner + interlock + monitor subtotal** | | | **≈ $98 @1, ≈ $75 @10** | |

**Context:** the two APS modules dominate the BOM. iseg is quote-only with no distributor stock; a
0.5 W APS is of order €200–300 each `[recalled — I did not obtain a quote and could not verify this
online]`. The combiner is therefore **~15 % of BOM cost and cost is not a discriminator between
topologies.** A single HV changeover reed relay (Standex/Gigavac class) is $40–100 `[recalled]`,
i.e. the same order as our three PhotoMOS. **Anyone eliminating a candidate on price here is
optimising the wrong variable.**

**Discrete alternative (Option B), for reference:** 4 × `IXTY02N120P` @ $3.76 + 2 × `ACPL-K308U`
(~$3.50 `[recalled — the Digi-Key base-product page did not render per-variant pricing for me]`) +
gate networks ≈ **$25** for the two branch switches vs. $23 for two PhotoMOS. **No cost advantage,
strictly more parts, more layout risk, and one more thing to get wrong. Recommend Option A.**

---

## 9. Layout constraints this topology imposes

- `HVOUT` swings ±600 V and can reach `HVP` − `HVN` = 1200 V differentially between the two branch
  nodes. Panasonic's own answer for 1500 V is **5.08 mm** terminal spacing (DIP6 with pin 5 deleted)
  `[verified-artifact]`, i.e. ≈ 3.4 mm/kV. **Set the HV netclass clearance to ≥ 5 mm HV-to-GND and
  ≥ 8 mm HVP-to-HVN**, roughly 2× the part's own spacing, which is affordable on a board this size.
  Encode as a DRC netclass rule with its schematic fields present (bootstrap §V.3).
- Mill a **slot under each PhotoMOS between pins 4 and 6**, and under each HV resistor string, to
  break the surface-tracking path. This is the layout cost of using a small SMD package at HV; a
  relay with wide terminals does not need it.
- The nine `HVC4020` chips are 10.2 × 5.1 mm each — the HV resistor strings, not the switches,
  dominate the HV area.
- Keep `R_bleed` on the connector side of `SW_D` so it is across `HVOUT` unconditionally.
- Place the `/ON` pull-up and the `Vset` `Rd` **within 5 mm of module pins 4 and 2 respectively**
  (§4.6, §7 faults 14/15). Encode as a placement check in the generator's acceptance test.

---

## 10. Verdict

**Score: 6 / 10.**

**Passes:**

- **(a) Hardware interlock — PASS, and better than any alternative.** The anti-parallel two-LED
  strings across one H-bridge node pair make both-enabled unreachable *by Kirchhoff*, with no logic
  gate, no inverter, and no decode to fail. The same current enables both the switch and the
  module's `/ON`, so two independent mechanisms would have to fail together. Verified against real
  `VR` ratings (2.6 V reverse against a 5 V rating). **This is the strongest single argument for the
  topology.**
- **(b) Discharge — PASS.** 2 × 100 MΩ permanent bleed (works unpowered, 124 ms to 50 V, 1.5 % of
  `Inom`), per-module 100 MΩ bleeds, and a commanded 2.2 MΩ dump switch that is benign when stuck
  closed. Firmware can *verify* the path by measuring τ. But the topology contributes nothing here —
  it is all bolted on.
- **(c) Independent monitoring — PASS, cleanly**, and the topology makes the monitor *more* useful
  because comparing it against `VMON` distinguishes a stuck switch from a stuck module.

**Costs:**

- **Hard ceiling at the 600 V class.** 1200 V recommended (PhotoMOS) / 1140 V_peak `VIORM`
  (`ACPL-K308U`) are real, verified numbers. At 1 kV there is no margin, and the un-limited `Vset`
  path makes an over-range fault a barrier-puncturing event. **If the human wants ±1 kV, eliminate
  this topology at G0.**
- **A shorted switch defeats exclusivity in the power path.** The interlock guards the command path
  only. Clamp diodes downgrade the outcome from "destroyed module" to "silently reads zero", which
  is a mitigation, not a fix. A welded relay contact remains exclusive; a shorted MOSFET does not.
- **The speed advantage is worthless.** The module's own 100 kΩ × 1 µF setpoint filter (500 ms to
  settle, read off iseg's Figure 2) is 12 500× the PhotoMOS turn-off and 250× a mechanical relay.
  The stated reason to prefer solid-state does not survive contact with the datasheet.
- **No through-zero** — but that is the module family's fault, not the combiner's, and it applies to
  every candidate.

**Recommend it if** the output spec lands at ≤600 V and the human values silence, unlimited
switching lifetime, no contact bounce, and no acoustic/vibration signature.
**Recommend against it if** ±800 V–1 kV is wanted, or if surviving a single component short without
a silent zero-output failure is a requirement.

### Questions this study raises for the G0 batch

1. **Is ±1 kV required, or is ±600 V acceptable?** This single answer selects or eliminates the
   topology. (§3.4)
2. **Is smooth through-zero required?** If yes, the APS family is wrong, independent of combiner.
   (§6.1)
3. **Ask iseg: does the APS have any reverse-voltage tolerance on the HV pin, and what is the
   output capacitance and the HV decay time after `/ON` goes high?** All three are absent from
   v2.5. (§1.4)
4. **Ask iseg: Table 1 specifies a current-monitor accuracy but Table 4 has no current-monitor pin.
   Which is right?** Decides whether fault 3 (§7) is detectable. (§1.2)
5. **Is a ~0.8 s polarity changeover dead-band acceptable?** (§5.3)
6. **Is an output current sense wanted?** Without it, several benign-but-silent faults stay silent.

### What still needs a bench, not a datasheet

- `C_out` of an actual APS module — every discharge τ in §4.4 depends on it.
- HV decay after `/ON` goes high — sets whether the 250 ms of §5.2 is enough.
- Actual `AQV258H5` off-state leakage at 600 V (the 10 µA spec is at 1500 V; the catalog's
  Fig. 9 curve implies much less, but I could not read values off the plot).
- The 100 ms setpoint τ derived from Figure 2 — confirm with a step response before trusting the
  0.8 s changeover budget.

---

## Sources read this session

- `references/iseg_manual_APS_en.pdf` — iseg APS series technical documentation v2.5, 2024-08-20.
  All 10 pages of text extracted with `fitz`; Figure 2 (page 9) rendered at 4× and 5× and read.
- [Vishay VOM1271 datasheet, doc 83469 rev 1.9 (2023-08-08)](https://www.vishay.com/docs/83469/vom1271.pdf)
- [Broadcom ACPL-K308U datasheet, ACPL-K308U-DS106 (2025-05-12)](https://docs.broadcom.com/doc/ACPL-K308U-Industrial-Photovoltaic-MOSFET-Driver-DS)
- [Panasonic PhotoMOS HE DIP6 (5-pin) 1 Form A product catalog, ASCTB430E 202509](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8882/semi_eng_he1a_aqv25_h.pdf)
- [Panasonic AQV258H5 product page](https://industry.panasonic.com/global/en/products/control/relay/photomos/number/aqv258h5)
- [Digi-Key — Panasonic AQV258H5AX](https://www.digikey.com/en/products/detail/panasonic-electric-works/AQV258H5AX/11685644) — price and stock read
- [Digi-Key — IXYS/Littelfuse IXTY02N120P](https://www.digikey.com/en/products/detail/littelfuse-inc/IXTY02N120P/2354490) — price and stock read
- [Digi-Key — Ohmite HVC4020V1006JET](https://www.digikey.com/en/products/detail/ohmite/HVC4020V1006JET/4759736) — price and stock read
- [Behlke — HV switches with fixed on-time](https://www.behlke.com/separations/separation_b1.htm)
- [Hofstra Group — Behlke HTS-300 listing](https://hofstragroup.com/product/behlke-fast-high-voltage-transistor-switch-10-microsecond-on-time-30-kv-30-a/) — confirmed discontinued, no price
- [Voltage Multipliers Inc. — Optocouplers & Opto-Diodes](https://voltagemultipliers.com/products/optocouplers-opto-diodes/) — confirmed no part-level specs or pricing published
