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
> This file declines to quote IPC-2221B (correctly) but offers a working figure of *"≥ 2 mm clearance and ≥ 8 mm creepage at 2 kV on uncoated external FR4"*. The live requirement at the 2000 V HV_POS↔HV_NEG span is **10.000 mm bare IPC B2 / 15.0 mm recommended**, i.e. this file's clearance figure is **7.5× permissive** and its creepage figure **1.9× permissive**. Note this is the SELECTED topology — the *decision* stands, the *number* does not.
>
> **The single live source for every clearance/creepage number is
> `docs/NUMBERS_PROBE.md`, generated from `hardware/hvctl/numbers_probe.py`.**
> At the frozen part (AP010504, Vnom = 1000 V) the live values are
> **7.5 mm** HV-to-anything and **15.0 mm** HV_POS↔HV_NEG (and HV_OUT_A↔HV_OUT_B),
> every one of them tagged **`[unverified-primary]`** pending a human reading a primary copy
> of IPC-2221B Table 6-1. Do not quote this file's figure anywhere.

# Combiner topology study — `hv-relay-changeover`

Phase-1 deep-dive for `docs/BRIEF_iseg-hv-controller.md`, open question "Combiner topology".
One candidate, analysed to the bottom. Author: G0 topology study, 2026-07-23.

**Verdict up front: 8/10 if set-and-hold with polarity changeover is acceptable; 2/10 if smooth
through-zero is required.** The topology passes all three non-negotiable invariants against every
*electrical* single fault, and fails invariant (a) against exactly one *mechanical* single fault
(a welded HV contact) — which is detectable but not preventable. Dead-band through zero is
**0.68 s**, of which the relay accounts for **6 %**; the rest is the iseg module's inability to sink
current and its unspecified restart time.

---

## 0. Evidence key and sources

| Tag | Meaning |
|---|---|
| `[verified-artifact]` | I opened the file/PDF this session and read the stated text |
| `[verified-live-page]` | I fetched the distributor page this session and read stock + price off it |
| `[verified-run]` | I executed the arithmetic this session (`scratchpad/relay_numbers.py`, stdlib-only) |
| `[recalled]` | from background knowledge, **unverified** — treat as a hypothesis |

Primary sources actually opened this session:

1. `references/iseg_manual_APS_en.pdf` — iseg APS series technical documentation v2.5, 2024-08-20.
   Read pages 6–8 in full via `fitz` under `PY_KICAD`. `[verified-artifact]`
2. Pickering Electronics **Series 67/68 High Voltage Dry Reed Relays**, Issue 1.4 Apr 2022, 7 pp.
   Fetched as PDF and text-extracted in full. `[verified-artifact]`
3. DigiKey product pages, read live: Standex-Meder `HE12-1A83-02`, `HE12-1A83-03`;
   Sensata/Cynergy3 `DAT70510F`; Panasonic `TQ2SA-5V`; Ohmite `HVC1206Z2504JET`. `[verified-live-page]`
4. Newark listing for Pickering `67-1-C-12/5`, SKU **40AK2389** — the listing title, MPN and SKU are
   confirmed from search results, but **newark.com timed out on three fetch attempts and I never read
   its price or stock**. Every price for this part below is an estimate and is labelled as such.

Instruments and their blind spots are stated at the end of each section.

---

## 1. Design point (assumed, logged)

The brief leaves module class open. This study assumes the **top of the range**, because it is the
worst case for every relay parameter and the analysis degrades gracefully downward:

| Item | Value | Source |
|---|---|---|
| Positive module | `AP010504P05` — 1 kV, 0.5 mA, +5 V in, 0.5 W | manual Table 2, p.8 `[verified-artifact]` |
| Negative module | `AP010504N05` — 1 kV, 0.5 mA, +5 V in, 0.5 W | same |
| Vset / Vmon span | 0–2.5 V, Vref 2.5 V ±1 % | manual Table 1, p.7 `[verified-artifact]` |
| Iout limit | ≈ 1.5 · Inom = **0.75 mA** | manual Table 2 note 1 `[verified-artifact]` |
| Iin at Vnom, loaded | < 180 mA | manual Table 1 `[verified-artifact]` |
| Worst-case volts across an open HV contact | **2000 V** (+1 kV branch vs −1 kV branch) | derived |

Facts the manual *does not* contain — I grepped all 10 pages for `discharg`, `bleed`, `capacit`,
`slew`, `ramp`, `rise time`, `turn-on`, `start` and got **zero hits** `[verified-run]`:

- **no output capacitance figure**
- **no internal bleeder / discharge time**
- **no slew rate, settling time, or turn-on delay**

Everything downstream that depends on those three numbers is an assumption and is marked. This is the
single largest source of uncertainty in the study and it applies to **all** candidate topologies, not
just this one.

Three quoted hazards from the manual that shape the whole design `[verified-artifact]`:

- p.7: *"Attention! Output voltage is internally not limited!"* — Vset > Vref gives Vout > Vnom.
- p.7: `/ON = 0 (LOW **or open**) → VOUT according setting`. **A floating /ON turns HV ON.**
- p.7, control version 1: `Rset = Vout · 10 kΩ / (Vnom − Vout)` ⇒ the Vset pin has an internal
  **10 kΩ pull-up to Vref**. **An open Vset wire commands full-scale output.**
- Discrepancy, unresolved, flagged not fixed: Table 1 specifies *"Current monitor accuracy 1 % · Inom"*
  but Table 4 (p.9) lists **no current-monitor pin** on this 7-pin part. Either the spec line is
  inherited boilerplate from a larger family, or there is an undocumented pin function. Do not design
  against a current monitor on this part until iseg confirms.

---

## 2. The circuit

### 2.1 Topology choice: two 1-Form-C, not one, and not four 1-Form-A

The task asks SPDT vs two SPST-NO with hardware break-before-make. Working through it:

| Arrangement | Verdict |
|---|---|
| **One HV SPDT**, COM→output, NC→NEG, NO→POS | Rejected. Two problems. (i) De-energised default connects the NEG module to the output — a power-up default of "negative module wired to the terminal" is the wrong safe state. (ii) The deselected module's output **floats charged**, with no bleed. Fails invariant (b). |
| **Two HV SPST-NO** in series with each module | Rejected as the sole mechanism. De-energised default is safe (output isolated), but "both closed" is a reachable coil state, so the interlock has to be bolted on externally, and the deselected branch still floats charged (needs 2 more relays or 2 permanent bleeds that load the active module). A classic mutual NC cross-interlock (K_P coil through K_N's break contact and vice versa) is available only if you buy *2-pole* HV relays, and it has the well-known simultaneous-command race: both coils pull in, both break contacts open, both drop out, chatter. |
| **Two HV 1-Form-C**, one per module, NC→bleed, NO→bus | **Selected.** Each module is *always* in a defined state: either driving the bus, or clamped to its own bleed resistor. There is no floating-charged state at all. Invariant (b) is satisfied *structurally* rather than by a timer. |

**Break-before-make** is intrinsic to a Form C reed: the moving blade physically leaves the NC contact
before it reaches NO. It is a property of one piece of ferromagnetic metal, not of the drive circuit.
Note however that Pickering does **not** specify the BBM interval for switch #5 — the datasheet gives
only "operate time inc. bounce 6 ms max / release 6 ms" `[verified-artifact]`. The BBM gap is
`[recalled]` to be tens to a few hundred µs for a changeover reed. **Measure it on the bench before
relying on any number.** It does not matter for this design (we switch cold), but it would matter if
anyone later proposes make-before-break tricks.

### 2.2 Full circuit, HV side

```
                 +---[ R_S 10k, 2 kV ]---+ COM   K_P  (Pickering 67-1-C-12/5)
  AP010504P05 ---+                       |        NO -----+
   HV out (pin6)                         |        NC --+  |
                                                       |  |
                                             R_bleedP  |  |
                                             2 x 10M   |  |     HVBUS
                                             (=20M) ---+  +------+-------------> SHV jack
                                                  |                |
                                                 GND               |
                 +---[ R_S 10k, 2 kV ]---+ COM   K_N               |
  AP010504N05 ---+                       |        NO -------------+|
   HV out (pin6)                         |        NC --+           |
                                                       |           |
                                             R_bleedN  |           |
                                             2 x 10M --+           |
                                                  |                |
                                                 GND               |
                                                                   |
                        R_bus  2 x 50M (=100M) --------------------+
                          |                                        |
                         GND                                       |
                                                                   |
      MONITOR (independent):                                       |
        R_top = 5 x 200M in series (=1.00G) --------------------- -+
                          |
                        MON node --- 100k --+--> ADS1115 ch0
                          |                 |
                     R_bot 1.00M         BAV99 clamp to 0/3.3 V
                          |                 + 3.6 V TVS
                    VMID = 1.25 V  (REF3012 or divided REF3025)
                          |
                       (to GND)
```

Notes on each HV element:

- **`R_S`, 10 kΩ 2 kV, in series between each module output and its relay COM.** Its only job is to
  survive the *fault* case where a contact makes hot. It limits the capacitive make-current to
  100 mA at 1 kV / 200 mA at 2 kV, against a 3 A contact rating — 15–30× margin `[verified-run]`.
  Static penalty: 7.5 V at the 0.75 mA current limit = 0.75 % of Vnom `[verified-run]`, and because
  the independent monitor sits *downstream* of `R_S` on the bus, that drop is measured, not guessed.
- **`R_bleedP/N`, 20 MΩ each (2 × 10 MΩ in series so no element sees > 500 V).** Connected only via
  the NC contact, so it loads the *deselected* module and **never** loads the active one. Parked-branch
  time constant 20 MΩ × 1 nF = 20 ms; to < 1 V in 138 ms.
  (`relay_numbers.py` was run with a single 10 MΩ, giving τ = 10 ms / 69 ms; either is fine, the
  2-element series string is the layout-correct version. Loading on the parked module at 1 kV is
  50–100 µA = 10–20 % of Inom `[verified-run]` — irrelevant, because a parked module is off.)
- **`R_bus`, 100 MΩ (2 × 50 MΩ).** In parallel with the 1.001 GΩ monitor string this gives
  **90.9 MΩ** on the bus `[verified-run]`. That is the number that sets both the discharge time and
  the permanent load on the active module: **11.0 µA at 1 kV = 2.2 % of Inom** `[verified-run]`.
- **Monitor string 5 × 200 MΩ.** Five elements so that each sees ≤ 400 V even at the 2 kV
  worst case `[verified-run]`; that keeps voltage-coefficient error small (see §4).

### 2.3 Low-voltage side: the interlock and the cold-switch permissive

```
  +5V ---[ TPS22918 load switch ]--- VIN_SW ---+ pole A COM   K_S  (Panasonic TQ2SA-5V,
                                               |    NO --> +VIN of POS module      2 Form C)
                                               |    NC --> +VIN of NEG module
  +12V --[ 200 mA polyfuse ]-------------------+ pole B COM
                                               |    NO --> K_P coil (+ flyback D)
                                               |    NC --> K_N coil (+ flyback D)

  K_S coil <-- 2N7002 <-- Q of 74HC373 latch, D = SEL(ESP32), LE = COLD
                                                       ^
  COLD <-- window comparator on MON: |MON - 1.25 V| < 50 mV   (i.e. |Vbus| < 50 V)

  /ON drive, per module:
     module pin4 --+-- 4k7 to +5V (default HIGH = HV OFF)
                   +-- 2N7002 drain (pulls LOW = HV ON)
     gate = AND( ARM_from_ESP32 , ALIVE )       with 100k pull-DOWN on the gate node
     ALIVE = diode-pump rectifier of a 1 kHz square wave from the ESP32, 10 nF / 1 MΩ, τ = 10 ms
```

**Why the interlock is `K_S` and not logic.** `K_S` has one armature. Its COM cannot touch NO and NC
at the same time — that is a statement about a single piece of metal, not about a truth table. Pole A
routes the *only* +5 V supply that reaches either module; pole B routes the *only* 12 V that reaches
either HV coil. Therefore, for **any** state of the ESP32, the drivers, the firmware, or a shorted
transistor:

- at most one module can be **powered at all**, and
- at most one HV relay coil can be **energised**, and
- those two facts are guaranteed *consistent* because they are the same armature.

This is why switching **+VIN** rather than **/ON** is the right primary disable on this part: a module
with no input power cannot make high voltage, and the manual's `/ON = open → HV ON` trap
`[verified-artifact]` stops being the last line of defence. Contact loading is comfortable: pole A
carries ≤ 180 mA and pole B 80 mA against a 500 mA rating — 36 % and 16 % `[verified-run]`.

**Why the cold-switch permissive is a transparent latch and not a gate.** The naive design — gate the
coil supply with "bus is cold" — is a **showstopper trap** that I fell into and then killed: as soon as
you raise the output, the bus is no longer cold, so the gate opens, so the relay *drops out while HV is
live*, which is precisely the hot switch you were trying to prevent. The fix is that COLD is a
**permissive to change state**, not a continuous requirement:

- `74HC373` transparent latch, `D` = SEL from the ESP32, `LE` = COLD.
- Bus hot ⇒ COLD = 0 ⇒ latch opaque ⇒ **the armature is frozen no matter what the firmware writes.**
- Bus cold ⇒ COLD = 1 ⇒ SEL propagates ⇒ `K_S` transfers ⇒ the HV relays transfer.

The COLD threshold is 50 mV at MON = 50 V at the bus, taken from the **independent** divider, not from
either module's VMON. Invariants (a), (b) and (c) therefore share one measurement chain, which is a
concentration of risk I return to in §5, fault 13.

**Why the /ON enable is AC-coupled.** `/ON` is active-LOW and floats to ON. Every *static* control
scheme fails unsafe on this pin: a reset ESP32 tri-states, an unpowered ESP32 tri-states, a cut wire
is an open. So the enable is made **dynamic**: the ESP32 must emit a continuous 1 kHz square wave which
a diode pump rectifies into `ALIVE`. Stop the square wave — by resetting, crashing, losing power, or
having the wire cut — and `ALIVE` decays through 10 nF / 1 MΩ (τ = 10 ms), the pull-down FET releases,
the 4k7 pulls `/ON` high, HV off within ≈ 20 ms. **Every static failure of the enable path is safe by
construction.** This is the single most important idea in the low-voltage section and it is
topology-independent — it belongs in `docs/DECISIONS.md` whichever combiner wins.

---

## 3. Invariants: pass / fail

### (a) Hardware interlock making both-enabled-into-the-output UNREACHABLE — **PASS against electrical faults, FAIL against one mechanical fault**

Three independent layers, listed strongest first:

1. **Single armature on `K_S` pole A** — only one module ever receives +5 V. Both modules cannot be
   *enabled* at all, in the strongest reading of the brief. Defeated only by a welded/bridged `K_S`
   contact.
2. **Single armature on `K_S` pole B** — only one HV coil is ever energised. Both HV relays cannot be
   *commanded* to NO.
3. **Two separate Form C armatures in the HV path** — both modules reach the bus only if both COMs are
   at NO simultaneously.

To defeat all three you need a *mechanical* failure: a contact welded closed. Layer 3 has a real,
quantifiable weld path (§5 fault 1). **I will not claim this invariant is absolutely satisfied.**
It is satisfied against every electrical, logic, firmware, driver and wiring fault I can construct,
and it is *detectable but not preventable* against a weld. The honest formulation for the gate review:

> `hv-relay-changeover` makes both-enabled electrically unreachable and mechanically improbable
> (weld probability bounded by ≥ 15× inrush margin and 10⁸-op cold-switch life = 2 700 years at
> 100 changeovers/day `[verified-run]`), with a startup self-test that detects a weld before HV is
> applied. It does not make it *impossible*.

**Weld self-test, executable at every power-up** (uses the independent monitor, so it is a real test):
with both coils de-energised, power and enable the POS module to +200 V. `K_P` is at NC, so the bus
must stay at 0 V ± noise. If the bus follows, `K_P` is welded at NO → latch fault, refuse to arm.
Repeat for NEG. Two 5-second checks; cost is firmware only.

### (b) Defined discharge / bleed on changeover and on disable — **PASS, structurally**

There is no state in which any HV node is floating and unbled:

| State | POS branch | NEG branch | Bus |
|---|---|---|---|
| Both coils off (power-up, power-loss, ARM low) | NC → 20 MΩ → GND | NC → 20 MΩ → GND | 90.9 MΩ → GND |
| POS selected | driving bus | NC → 20 MΩ → GND | 90.9 MΩ → GND |
| NEG selected | NC → 20 MΩ → GND | driving bus | 90.9 MΩ → GND |

Measured/derived times `[verified-run]`:

| Node | R | C | τ | →50 V from 1 kV | →1 V |
|---|---|---|---|---|---|
| parked branch | 10 MΩ | 1 nF (assumed) | 10 ms | 30 ms | 69 ms |
| bus, module still connected | 90.9 MΩ | 1.2 nF | 109 ms | **327 ms** | 754 ms |
| bus, both relays released | 90.9 MΩ | 200 pF | 18 ms | 55 ms | 126 ms |
| bus + 10 nF external load | 90.9 MΩ | 10 nF | 909 ms | 2.72 s | 6.28 s |

Touch-safety check against the common "< 60 V within 5 s after disconnection" rule
(`[recalled]` as IEC 61010-1 §6.3 — **I did not open the standard**, verify before it goes in a safety
case): PASS at 1 nF (0.26 s) and at 10 nF (2.56 s), FAIL at 100 nF (25.6 s). Maximum permissible
external load capacitance is **19.5 nF** `[verified-run]`. **Write "C_load ≤ 10 nF" into
`docs/INTERFACES.md` as a hard interface constraint** — it is a real design limit, and it is also what
bounds the fault energy in §5.

The 327 ms row is the reason this topology has a long dead-band, and it is *not the relay's fault*:
the iseg module is a source-only converter with no sink path, so commanding Vset → 0 does not pull the
output down — the bleed does. §6 shows how to buy that time back.

### (c) Independent output monitoring — **PASS, and quantitatively better than VMON**

The 1.001 GΩ : 1.00 MΩ divider taps **HVBUS**, i.e. the actual output terminal, downstream of every
relay contact and every series resistor. It shares no silicon, no pin, no wire and no ground reference
path with either module's VMON. Numbers `[verified-run]`:

- ratio 1001 : 1, so ±1000 V → **1.25 V ± 0.999 V = 0.251 … 2.249 V**, i.e. bipolar sensing on a
  single-supply ADC by returning R_bot to a 1.25 V reference. This matters: the monitor must be
  **sign-aware**, because a wrong-polarity fault (§5 fault 3) is only detectable by sign.
- divider current at 1 kV: 0.999 µA = **0.2 % of Inom**.
- error budget: voltage coefficient 0.02 % (1 ppm/V) to 0.50 % (25 ppm/V) depending on resistor grade;
  TCR mismatch 100 ppm/K over 20 K = 0.20 %; ADS1115 LSB = 125 µV = **0.125 V at the HV node**.
  Total ≈ 0.2–0.6 % of full scale, against the module's own **VMON accuracy of 1 % · Vnom = 10 V**
  `[verified-artifact]`. So the independent monitor is 2–5× better than the thing it is checking —
  it is a genuine measurement, not a redundant one.
- Use Ohmite HVC1206 (verified $2.15 @1, 166 in stock for the 2.5 MΩ value `[verified-live-page]`;
  the series covers 100 kΩ–100 GΩ at up to 3 kV) for a cheap build; move to a matched HV divider
  (Vishay VHD200 or Caddock 1776-C, both `[unverified-MPN]`) if the 0.5 % VCR term is unacceptable.
- **R_bot must never be the only thing between 1 kV and the ADC**: 100 kΩ series + BAV99 clamp to the
  rails + 3.6 V TVS. With R_bot open, the clamp sinks (1000 − 3.3)/1 GΩ ≈ 1 µA. Mandatory, ~$0.30.

---

## 4. The through-zero question — the finding that outranks the topology

**Smooth through-zero is impossible with this topology.** Dead-band budget `[verified-run]`:

| Step | ms |
|---|---:|
| T1 Vset→0, passive decay of the bus to < 50 V (90.9 MΩ, 1.2 nF) | 326.8 |
| T2 kill +VIN load switch, force /ON high, converter collapses | 10.0 |
| T3 COLD window-comparator guard band | 50.0 |
| T4 `K_S` transfer (TQ2SA-5V, 4 ms operate / 4 ms release) `[verified-live-page]` | 8.0 |
| T5 HV Form C: 6 ms release + 6 ms operate incl. bounce `[verified-artifact]` | 12.0 |
| T6 contact settle guard | 20.0 |
| T7 re-apply +VIN, module start-up — **UNSPECIFIED in the manual, assumed** | 150.0 |
| T8 ramp Vset to the new setpoint — **assumed** | 100.0 |
| **TOTAL** | **676.8 ms** |

**The relay contributes 40 ms — 5.9 % of the dead-band.** The other 94 % is the iseg module: it cannot
sink current (T1) and its restart time is undocumented (T7). Any topology built on these modules pays
T1 and T7. So:

> **The relay is not what makes through-zero impossible. The modules are.**

And there is a second, harder floor that has nothing to do with any combiner. The manual states
`[verified-artifact]`: *"Specifications for stability, ripple and noise are guaranteed in the range
2 % · Vnom < Vout ≤ Vnom."* At Vnom = 1 kV that is **20 V**. The achievable, *specified* output set is

```
  [-1000 V, -20 V]   ∪   {0}   ∪   [+20 V, +1000 V]
```

with a ±20 V band in which the module's behaviour is simply not characterised — before the relay is
even considered. **If the answer to the brief's open question "is smooth through-zero required?" is
yes, then the APS module family is the wrong part, and no combiner topology rescues it.** That
conclusion should be escalated to the human at G0 ahead of the topology decision itself, because it
invalidates the premise of the comparison.

---

## 5. Single-fault analysis

Format: element → stuck-on behaviour / stuck-off behaviour → what the **output terminal** does.

| # | Element | Fault | Output behaviour | Verdict |
|---|---|---|---|---|
| 1 | `K_P` HV contact | **welded at NO** | POS module permanently on the bus. Selecting NEG now puts *both* modules on the bus → invariant (a) violated by one mechanical fault. Current is bounded (each module limits at 0.75 mA), so it is not energetic, but the output voltage is indeterminate and both modules are back-fed to 2 kV differential. | **The topology's central weakness.** Bounded by 15–30× inrush margin and the startup weld self-test (§3a). Not preventable. |
| 2 | `K_P` | armature stuck at NC / coil open | POS branch never reaches the bus. Bus stays at 0. But the POS module, if powered, sits at up to 1 kV into its 20 MΩ bleed — **1 kV present on an internal node with no monitor on it**. | Fail-safe at the terminal. **Add a per-branch monitor divider** (2 × $11) so an energised parked branch is visible. |
| 3 | `K_S` | coil open, driver stuck off, or broken SEL wire | Armature stays at NC = NEG selected and NEG powered, while firmware believes POS. Commanding +500 V produces **−500 V at the terminal** — catastrophic for a polarised load (PMT, APD, electrometer). | Only caught because the independent monitor is **bipolar and sign-aware**. This is the concrete reason for the 1.25 V mid-reference. Prevent by upgrading `K_S` to 3 Form C and feeding the third pole back as armature-position sense (Panasonic TQ3SA-5V `[unverified-MPN]`, not stocked at DigiKey; TQ2SA verified). |
| 4 | `K_S` | welded | Polarity locked to one module. Detectable via position sense; not preventable. | Fail-detectable. |
| 5 | TPS22918 +VIN load switch | FET shorted (stuck ON) | Modules powered whenever the board is. HV then depends on `/ON` alone — which defaults HIGH via the 4k7. **Still off.** | Degrades to one layer, still safe. |
| 6 | same | stuck OFF | No HV ever. | Safe. |
| 7 | `/ON` pull-down 2N7002 | D–S short | `/ON` held LOW = HV ON whenever +VIN present. Defence is now the +VIN load switch alone. | Degrades to one layer, still safe (needs faults 5 **and** 7 together to make uncommanded HV). |
| 8 | same | open | `/ON` stays high, HV never on. | Safe. |
| 9 | `ALIVE` pump / comparator | stuck asserted | Gate follows ARM. **ARM must have a 100 kΩ pull-DOWN at the gate node**, so a floating ESP32 pin is still off. | Safe *only if the pull-down exists*. Make it a DRC/ERC-checkable rule: every ESP32 output that enables anything gets a pull-down to its safe state at the receiving end. |
| 10 | **ESP32 in reset** (GPIOs tri-state) | — | ARM floats → pull-down → coils off, +VIN off; square wave stops → ALIVE decays in ~20 ms → `/ON` high. Armatures release to NC. Terminal at < 1 V in ≈ 130 ms. | **Safe.** Design intent; must be bench-verified at Phase 7. |
| 11 | **ESP32 unpowered while HV rails up** | — | Identical to #10. | **Safe.** |
| 12 | Broken wire: ARM | — | Pull-down → coils off, +VIN off → both branches parked on their bleeds, bus bled. | Safe. |
| 13 | Broken wire: the 1 kHz ALIVE line | — | Pump decays → `/ON` high. | Safe. **This is the payoff of AC-coupling the enable.** |
| 14 | **Broken wire: `/ON` harness, module side** | — | Module-side `/ON` floats → **HV ON**, per the manual. | **UNSAFE and not fixable on that pin.** Mitigations: (i) `/ON` is the *secondary* disable — +VIN is primary, so a harness cut that takes both is safe; (ii) sequence the connector so **+VIN breaks first** on unmating (shortest pin / staggered contacts); (iii) route `/ON` and +VIN in the same bundle so a cut takes both. Accept residual risk of a single-conductor break in `/ON` only. |
| 15 | **Broken wire: Vset** | — | Internal 10 kΩ pull-up to Vref drives Vset to full scale → **module commanded to Vnom.** | **UNSAFE.** Mitigate with (i) a sense ADC channel at the *module end* of the Vset wire, and (ii) a hardware comparator on |Vset_sensed − Vset_commanded| whose output is ANDed into the `/ON` permit. Even so, the module ramps to Vnom for the comparator's response time. This is a property of the part, present in every topology. |
| 16 | Broken wire: VMON | — | Module readback reads 0 while the output may be at full scale. | **This is exactly why invariant (c) exists.** Independent divider catches it. Invariant pays off. |
| 17 | Broken wire: GND (pin 3 **or** 7) | — | The other GND carries return. Both broken: HV return finds a path through the case/chassis bond. | Use both GND pins on separate conductors + a chassis bond. |
| 18 | HV divider **top string open** | — | MON reads 1.25 V (= "0 V") while the bus is at full scale. **Defeats invariant (c) silently.** | **The most dangerous single fault on the board.** No cheap passive detector distinguishes it (an open string and a zero bus give the same MON). Fix: (i) two independent divider strings with different values, compared in firmware — disagreement = fault, ~$11; (ii) a mandatory self-test at every enable that commands a known nonzero output and requires the monitor to follow. Do both. |
| 19 | HV divider **bottom resistor open** | — | MON node rises toward the bus voltage → destroys the ADC and possibly the ESP32. | Prevented by the mandatory 100 kΩ + BAV99 + TVS clamp (§3c). Also use 2 × 2 MΩ in parallel for R_bot. |
| 20 | COLD comparator | stuck at 1 | Latch always transparent → hot switching becomes possible on a firmware bug. **The hardware cold-switch guarantee degrades to a firmware convention.** | Honest statement: this is a **firmware-verified hardware interlock**, not a pure hardware one. Self-test: raise HV, require COLD to fall; if it does not, latch a fault. |
| 21 | COLD comparator | stuck at 0 | No polarity change ever possible. | Stuck-safe. Choose comparator output polarity so that the *likely* failure sits here (push-pull outputs, not open-drain-with-pull-up — an open-drain failure pulls up to a false COLD=1). |
| 22 | HV relay coil | shorted turn | 12 V into a low resistance through `K_S` pole B → contact damage. | 200 mA polyfuse in the 12 V coil rail (nominal draw 80 mA). |
| 23 | HV relay coil | open | Armature parked at NC. | Safe; detected by the weld/position self-test. |
| 24 | **External magnet near the board** | — | Reed relays are magnetically operated. A stray magnet **can close an HV contact with no coil current at all.** In a physics lab with permanent magnets, magnetic mounts and cryostats, this is a real exposure, not a curiosity. | Pickering 67 has an internal mu-metal screen `[verified-artifact]`, which is the main mitigation. Add: ≥ 5 mm relay-to-relay spacing, a note in the enclosure spec, and the startup weld self-test also catches a magnetically-held contact. **This failure mode does not exist for any solid-state combiner and it is a genuine point against reeds in this environment.** |
| 25 | Contact bounce on make | — | Harmless: we switch cold. In a hot-switch fault, bounce means N repeats of the 0.6–2.4 mJ capacitive discharge, each limited to ≤ 200 mA by `R_S`. | Contained. |
| 26 | Load capacitance far above spec (e.g. 1 µF) | — | 0.5 J single-pulse into `R_S` on a hot make; bleed time 25 s at 100 nF, i.e. touch-safety failure. | Bounded only by the **C_load ≤ 10 nF** interface constraint. This constraint must be written down and, ideally, physically enforced by an in-line HV resistor in the cable. |

### Arc physics — the one place this topology gets a free pass

At these power levels the relay is effectively always dry-switching *current*, even in a hot-switch
fault, because the module's own limiter caps Iout at **0.75 mA** `[verified-artifact]`. The minimum
current to sustain a metallic arc between tungsten contacts is `[recalled]` ≈ 1 A — **three orders of
magnitude above what these modules can deliver.** A sustained arc across a reed gap is therefore not
physically available. The only real contact stress is the *capacitive* make-discharge, which `R_S`
handles (§2.2), and which is exactly what Pickering's Note 1 warns about: *"even stray capacitance can
generate very high current pulses, which can damage the contact plating causing welding"*
`[verified-artifact]`.

The converse — why you must buy **HV-rated** reeds and not cheap ones — is Paschen. A generic reed
switch has a contact gap of order 0.05–0.1 mm in ~1 atm fill gas; small-gap breakdown in air/N₂ at that
p·d sits in the **~0.5–1.5 kV** range `[recalled]`, i.e. right on top of our 1 kV operating point and
below our 2 kV worst case. Pickering's 5 kV standoff for switch #5 is achieved with a purpose-built
gap and fill. **Do not substitute a $3 SIL reed relay for the $90 part on the grounds that "1 kV is
not that high".**

---

## 6. Options considered and rejected, with numbers

- **Add a third HV relay as a switched crowbar bleed** (1 MΩ, energised only during disable). Cuts T1
  from 327 ms to ~2 ms and the total dead-band from 677 ms to ~350 ms. Cost: +$90 and +36 cm² is
  already tight (§7). *Rejected for the first build*; revisit if the bench measurement of the module's
  real output capacitance makes T1 worse than modelled. Note also that if the crowbar closes while a
  module is still on, the output does **not** go to zero — it settles at 0.75 mA × 1 MΩ = 750 V, a
  detectable but non-obvious failure.
- **Lower `R_bus` to 20 MΩ** for faster bleed. Rejected: 50 µA at 1 kV = **10 % of Inom** on the active
  module, and it buys only ~65 ms of the 677 ms budget.
- **Cheaper relays.** Verified live: Standex `HE12-1A83-02` 7.5 kV 1 Form A, **$60.24 @1, 34 in stock**;
  `HE12-1A83-03` **$49.93, not stocked, 10-week lead**; Cynergy3 `DAT70510F` 7 kV 1 Form A, **$68.50 @1,
  11 in stock, 18-week lead** `[verified-live-page]`. All are **Form A only** — building the same
  function from Form A parts needs 4 relays (2 select + 2 bleed) at $200–270 and *loses* the structural
  bleed guarantee. **The Form C part is cheaper and safer than four Form A parts.** DigiKey does not
  list Pickering at all (searched `67-1-C-12/5D` live: no results); Newark does, SKU **40AK2389**.
- **Vacuum relays (Gigavac G2/G3, Kilovac)** `[unverified-MPN]`. Rated 5–20 kV, but coil currents of
  hundreds of mA to >1 A, package volumes 10–50× the Pickering, and $100–400 each. Massively
  over-specified for a 0.75 mA source. Rejected on power, size and cost.

---

## 7. Cost, size, availability

BOM for the HV switching subsystem only (qty 1, USD) `[verified-run]`:

| Qty | Item | Unit | Ext | Evidence |
|---:|---|---:|---:|---|
| 2 | Pickering `67-1-C-12/5` HV 1 Form C, 5 kV standoff | $90.00 | $180.00 | **ESTIMATE.** Newark SKU 40AK2389 confirmed to exist; price never read. Bracketed by verified comparables $49.93–$68.50. |
| 1 | Panasonic `TQ2SA-5V` 2 Form C interlock | $2.65 | $2.65 | `[verified-live-page]` DigiKey, 14 805 in stock |
| 5 | Ohmite HVC1206 200 MΩ divider string | $2.15 | $10.75 | price from verified `HVC1206Z2504JET` |
| 4 | Ohmite HVC1206 10 MΩ NC bleeds | $2.15 | $8.60 | same series |
| 2 | Ohmite HVC1206 50 MΩ bus bleed | $2.15 | $4.30 | same series |
| 2 | Ohmite HVC1206 10 kΩ series limiter | $2.15 | $4.30 | same series |
| 1 | R_bot 1 MΩ 0.1 % + BAV99 + 100 kΩ + TVS | $1.50 | $1.50 | estimate |
| 1 | TLV3702 + REF3025 + 74HC373 | $8.00 | $8.00 | estimate |
| 1 | TPS22918 + 2N7002 × 2 + passives | $3.00 | $3.00 | estimate |
| 1 | SHV panel jack | $20.00 | $20.00 | estimate |
| | **TOTAL** | | **$243** | HV relays = **74 %** |

Size: the Pickering 67 body is **58.4 × 12.6 × 14.5 mm, 13.58 g** `[verified-artifact]`. Two of them
with an 8 mm creepage keepout ring occupy roughly **74 × 49 mm = 36.6 cm²** `[verified-run]` — a
substantial fraction of a Eurocard. The long SIL package is actually helpful: it puts the switch pins
at opposite ends of a 58 mm body, so the *package* supplies most of the creepage for free.

Creepage/clearance for the 2 kV branch-to-branch worst case must be encoded as a KiCad netclass DRC
rule per `CLAUDE.md`. I am **not** going to invent the IPC-2221B Table 6-1 number — the practical
working figure I would start from is ≥ 2 mm clearance and ≥ 8 mm creepage at 2 kV on uncoated external
FR4, with a milled slot where that cannot be met `[recalled, must be verified against IPC-2221B before
layout]`.

Availability risk: the Pickering Form C is build-to-order with a typical 2–4 week lead `[recalled]`;
the verified stocked comparables carry 10- and 18-week manufacturer leads `[verified-live-page]`.
**Order the relays at G1, not at fab.**

---

## 8. What would make me abandon this topology

1. The answer to "is smooth through-zero required?" comes back **yes**. Then this topology scores 2/10
   and, more importantly, the APS module family itself is disqualified (§4).
2. Polarity changeover is needed faster than ~0.4 s, or more often than ~1 Hz sustained.
3. The bench measurement of the modules' real output capacitance comes back ≫ 10 nF, which would blow
   both the discharge budget and the fault-energy budget.
4. The build must survive a welded-contact fault *by prevention* rather than by detection — no
   contact-based topology can do that.

## 9. Recommended next actions

1. **Escalate the 2 % · Vnom finding to the human before the topology vote** — it may change the
   module selection, which is upstream of the combiner decision.
2. Bench-measure on one module, before G1: output capacitance, decay time with a known bleed, restart
   time after +VIN is re-applied, and Vset→Vout settling. Four numbers, all currently assumptions.
3. Get a live quote for Pickering `67-1-C-12/5` (Newark 40AK2389) and confirm the Ohmite HVC per-size
   voltage rating.
4. Write `C_load ≤ 10 nF` into `docs/INTERFACES.md`.
5. Put "every enable output gets a pull-down to its safe state at the receiving end" and "the /ON
   enable is AC-coupled" into `docs/DECISIONS.md` — they are topology-independent.
