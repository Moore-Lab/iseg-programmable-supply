# MONITOR_AND_BLEED — independent output monitoring and the discharge paths

**Session 2 · 2026-07-23 · detailed design against the frozen G0 answers (A1–A5).**
Scope: brief invariants **(b) defined discharge/bleed on changeover and on disable** and
**(c) output voltage monitored independently of the module readbacks**, now for **two output nodes**
(G0-A4), plus the **COLD permissive** string that `COMBINER_STUDY.md` correction **C-2** requires be
physically separate from both.

Out of scope, named so nobody thinks it was forgotten: the interlock algebra (`CONTROL_ARCHITECTURE.md`
§3), the mode switch part selection (`DECISIONS.md` MODE-13), the `VSET` clamp (`NUMBERS_PROBE.md` §5),
the relay selection (`topology/hv-relay-changeover.md`). This document consumes their outputs and
states what it needs from them.

---

> # ⛔ CORRECTION BANNER — added 2026-07-23 (session 2 verification). READ FIRST.
>
> The claim *"the independent output monitors load the modules acceptably, beat the module's own 10 V
> `VMON` accuracy, and are electrically independent of the `VMON` nets and of the COLD-permissive
> divider"* was put to **three independent skeptics tasked with refuting it. All three refuted it, at
> high confidence.** The three legs fail for three different reasons and each has a different fix.
>
> **M-0 — what SURVIVED, so it is not re-attacked:** §8 **did** sum the parallel strings
> (S1+S2+S3+S5 = **57.0 µA = 11.40 %**), so "nobody summed it" is false. The divider arithmetic
> reproduces independently: `1/G = 163.80 kΩ`, `α = 8.1899e-4`, `tap0 = 2.04747 V`, RSS terms
> `0.2566 / 0.7182 / 1.5086 V`. §5.2's COLD design and §7's discharge model are unchallenged here.
>
> **M-1 — LOADING: the published sum is INCOMPLETE against the golden netlist, and "acceptable"
> survives only numerically.** `board_spec.py` adds two mode-switch stub bleeds `BLDX` (`HV_X`) and
> `BLDM` (`HV_M`), **400 MΩ each**, which this document never mentions (grep for `HV_X|HV_M|stub|
> 400 M` returns **zero hits**). In **pseudo-bipolar** the live path is
> `HV_X–SW1A–HV_M–R_M1–SW1B–HV_OUT_A`, so **both stubs load the active module**:
> **62.0 µA = 12.40 %**, not 11.40 %. Unipolar negative module: **59.5 µA = 11.90 %**.
> Meanwhile `numbers_probe.py` still asserts on **55.0 µA / 11.00 %** (bleed + divider only) and
> `board_spec.py` asserts **no load budget at all**. Under 15 % on every reading — **but the
> published number is wrong and the assertion is passing on an incomplete sum**, which is the exact
> failure mode `COMBINER_STUDY.md` F-11 exists to warn about. **And with the `[ASSUMED]` ~20 MΩ
> internal module bleeder the total is 21.40 % (22.40 % with the stubs), which BREACHES the probe's
> own ≤15 % assertion** — §8 rules that *"acceptable — no change"* without noting the breach.
> **MEASURABLE-NOW: measure the internal bleeder before this is signed.**
> Separately, `board_spec.py` D-1 records that `COMBINER_DESIGN.md` §5.3's competing 17.24 MΩ
> closed-node figure is **optimistic by ~1.76×** under the arrangement actually built, and that the
> two documents' bleed values (20.0 MΩ here vs 40 MΩ there) **cannot both be true**. Unadjudicated —
> a G1 decision.
>
> **M-2 — ACCURACY: "beats 10 V" is CONDITIONAL, and the honest ratio is ~2×, not 31×.**
> §4.5's own table gives **20.0 V — a FAIL, worse than `VMON`** — on bare FR-4 with no guard. The
> **100× guard improvement factor is `[ASSUMED]` and has never been measured** (O-M6); this file
> already calls it *"the single least-supported number"*. §4.4 **excludes the 5.0 V long-term drift**
> that it concedes is larger than every instantaneous term; folding it back in gives
> **1.9–2.0× better than `VMON`**, not §4.4's 6.6× and certainly not the **31.0×** that
> `numbers_probe.py` still prints (the probe carries the α this file disowns in §11.1/§11.4 — the two
> instruments disagree and the probe has not been regenerated). The working-voltage ratings the string
> composition rests on (**800 V for the 1206, 1500 V for the 2512**) are `[ASSUMED]` and
> `[unverified-MPN]` — `board_spec_parts.py` says verbatim that the rating *"is [ASSUMED] — NEVER read
> from a datasheet"*, and **no MPN exists**, so they cannot be checked against a real part at all
> (O-M10). `k_VCR` is a **purchase specification**, not a measured value (O-M5).
> **New, and not in §10:** at the 2012 V fault this monitor is deliberately given headroom to read
> (§11.1), the co-located S1/S3 **2512 elements sit at 1006 V against a 750 V 50 %-derate limit.**
> Never analysed.
>
> **M-3 — INDEPENDENCE: not met, in three separate ways.**
> 1. **§5.4 deliberately makes `COLD = (S3 window) AND (a comparator on the S2 tap)`** — an outright
>    dependency on the monitor chain. This file admits it needs the **frozen** assertion SA-8
>    (*"shares no component"*) reworded and defers the decision to G1 (O-M7). `board_spec.py` **D-2
>    declines to build it.** Consequence: §10 rows 10 and 12, which claim STUCK-SAFE **solely** via
>    that AND, are **unmitigated in the netlist as built** — one open S3 element silently doubles the
>    COLD threshold (§5.2's built values give ±36.8 V → ~±74 V), **above the 60 V touch limit**, with
>    no annunciation.
> 2. **`RMO_x` (monitor offset) and `RCO_x` (COLD offset) both feed from `VREF_2V500` (one REF5025).**
>    `board_spec.py`'s own independence assertion passes **only because `VREF_2V500` is whitelisted**
>    in `ASSERTION_C_ALLOWED_SHARED_NETS`. Literal SA-8 is therefore not met.
> 3. **ONE `OPA2192` (`UGD`) drives BOTH driven guard rings** (pins 1,2 and 6,7) — a single-package
>    common-mode failure that degrades **both** "independent" monitors to ~20 V simultaneously. This
>    breaks §4.6's own different-package rule and **§10 has no row for it** (row 9 treats guard loss
>    per-chain and already calls it *"NOT RELIABLY DETECTED"*).
> 4. `MON_TAP_A/B` additionally feed the **hardware OVP** comparators (`U8`/`U9` → `nOVP` → `ARM`).
>    **One open S2 element halves the reading and pushes the 1050 V trip to ≈2100 V**, so the 1320 V
>    `VSET` fault would no longer trip OVP. **One resistor blinds the monitor and the OVP together.**
>    Not in §10.
>
> **M-4 — value slips to fix at G1:** §4.2's `MON_REF` divider `1.78k/8.25k` = **2.0563 V**, which
> does not match the **2.04747 V** tap it must match (E96 `8.06k` does); `board_spec.py` silently
> builds `1.82k/2.32k` instead. And `board_spec.py` **D-3** records that §5.2's COLD values are
> **unrealisable as published** and were moved (node centre 2.046 V → 1.950 V, `Ro` 1.24 M → 1.58 M).
>
> **RESTATE THE CLAIM AS:** *the monitors load the active module at **12.40 %** of Inom (pseudo-bipolar,
> stubs included) — inside the 15 % budget, but the budget must be re-summed and re-asserted, and it
> breaches on the assumed internal bleeder. They beat `VMON` by ~2× once long-term drift is included
> and ONLY IF the `[ASSUMED]` 100× guard factor is real; unguarded they are worse than `VMON`. They
> are independent of the module `VMON` nets, but they share a voltage reference with the COLD chain,
> share one op-amp package between the two guard drivers, and the proposed §5.4 AND would make them
> not independent at all.*

## 0. How to read this, and what instrument produced each number

| tag | meaning |
|---|---|
| `[verified-run]` | executed this session; the command and its output are in §13 |
| `[verified-artifact]` | a file on disk was read and inspected this session |
| `[recalled]` | from context, unverified — treat as an assumption |
| `[ASSUMED]` | an input constant nobody has measured |
| `[unverified-MPN]` | the part number has never been checked against a live distributor page |
| `[unverified-primary]` | a standards constant transcribed from a secondary source (`STATUS.md` §1.2) |
| **MEASURABLE-NOW** | depends on one of the four unmeasured module parameters; the modules are in hand (G0-A2) |

**`hardware/hvctl/numbers_probe.py` was re-run this session: 74 assertions, 74 pass, exit 0**
`[verified-run]`. Where this document quotes a number the probe prints, the probe is the source and
this document does not recompute it. Where this document introduces a number the probe does **not**
compute, the arithmetic was run separately and is reproducible from §13; those numbers are marked
**[new-this-session]** and are listed in §12 as assertions that must be folded back into the probe.

**Three places where I disagree with a document already in this repo. All three are in §11, stated
loudly, none of them silently applied.** The largest is that the monitor as specified in
`NUMBERS_PROBE.md` §4 **has zero overrange headroom and therefore cannot see the overvoltage
condition it partly exists to detect.**

---

## 1. Frozen inputs this design is built on

| | value | source |
|---|---|---|
| Module | iseg **AP010504P05** / **AP010504N05**, owned | G0-A2, `DECISIONS.md` PART-29 |
| `Vnom` | **1000 V** per module | G0-A2 |
| `Inom` | **0.5 mA**; `Iout` ≤ ≈1.5·Inom = **0.75 mA** | G0-A2, PART-13 |
| `VMON` accuracy | **1 %·Vnom = 10.0 V**, and `VMON` leaves through an internal **20 kΩ** | Table 1/4, Figure 2 `[verified-artifact]` |
| Module output capacitance | **unpublished** — assumed 100 pF | PART-24 `[ASSUMED]` **MEASURABLE-NOW** |
| Module internal bleeder | **unpublished** — assumed ~20 MΩ | PART-24 `[ASSUMED]` **MEASURABLE-NOW** |
| `C_load` | **≤ 10 nF per output**, an *imposed* interface limit, not a measured fact | NUM-13 |
| Touch-safe threshold | **60 V DC** | `[recalled]` `[unverified-primary]` |
| Hazardous stored energy | **350 mJ / 50 µC** | `[recalled]` `[unverified-primary]` |
| Modes | **pseudo-bipolar** (one output) / **unipolar dual-output** (two outputs, both live) | G0-A4/A5 |
| Mode element | a **physical panel switch**, no coil, no software mode bit | G0-A5, MODE-04/12 |
| Monitor loading budget | **≤ 1 % of Inom per output** = **5.0 µA at 1 kV** | ARCH-26/27, MODE-07 |
| Bleed loading budget | **≤ 10 % of Inom per output** = **50.0 µA at 1 kV** | `NUMBERS_PROBE.md` §3.3 |
| Disagreement trip | **2 %·Vnom = 20.0 V** between the independent monitor and `VMON` | ARCH-23 |

---

## 2. The three-strings rule, and a fourth string nobody has costed

`COMBINER_STUDY.md` **C-2** (retiring judge finding **F-3**) forbids deriving the COLD permissive from
the invariant-(c) monitor divider. `INTERFACES.md` **SA-8** encodes it: *"The COLD/permissive divider
shares no component with the invariant-(c) monitor divider."* The reason is a single-fault chain:

> one open element in the monitor top leg ⇒ monitor reads 0 V ⇒ COLD is permanently TRUE ⇒ the
> changeover latch is permanently transparent ⇒ **every** changeover becomes a hot switch ⇒ the weld
> that the whole topology's safety case treats as a random wear-out becomes a systematic consequence
> of normal operation — while removing the monitor that would show it.

So, **per output node**, three physically distinct strings:

| # | string | job | R (top leg) | load at 1 kV | % of Inom |
|---|---|---|---:|---:|---:|
| **S1** | **BLEED** | invariant (b) — discharge, permanent, unswitched | 20.0 MΩ | 50.0 µA | **10.00 %** |
| **S2** | **MONITOR** | invariant (c) — independent, accurate, into an ADC | 200 MΩ | 5.0 µA | **1.00 %** |
| **S3** | **COLD** | hardware changeover permissive, into a window comparator | 1.00 GΩ | 1.0 µA | **0.20 %** |

and **per module branch** (on the module's own HV pin, *upstream* of the changeover relay):

| # | string | job | R | load at 1 kV | % of Inom |
|---|---|---|---:|---:|---:|
| **S4** | **NC BLEED** | bleeds the *parked* branch, via the Form-C NC contact | 20.0 MΩ | 50.0 µA | 10.00 % *(parked only)* |
| **S5** | **BRANCH MONITOR** | retires **F-2**: proves the parked branch really is energised during the weld self-test | 1.00 GΩ | 1.0 µA | **0.20 %** |

**S5 is the string nobody has costed.** `COMBINER_STUDY.md` C-2's second sentence — *"Add per-branch
monitor dividers"* — has never appeared in any load budget, including the probe's. F-2's point is that
without it, *"a module that produced no HV at all, an open `/ON`, an open series limiter or a dead
module all yield the same 'bus stayed at 0' PASS"*: the weld self-test cannot distinguish **stimulus
applied and blocked** from **no stimulus was ever applied**. S5 is a precondition of the self-test, not
an upgrade.

**Total: 10 HV strings on the board** (S1–S3 ×2 outputs, S4–S5 ×2 modules), each realised as **two
parallel sub-strings** per NUM-09/SA-9 → **20 physical strings**. §9 gives the area consequence and
§11.2 argues that SA-9 is right for S1/S3/S4/S5 and **wrong for S2**.

---

## 3. Architecture decision — two full chains, or one ADC multiplexed?

**Decision: two full independent analogue chains (divider + buffer + offset network), read by two
ADS1115 parts, with the safety-critical *permissive* removed from the ADC path entirely.**

### 3.1 The question is malformed until you say what the ADC is for

The task frames it as *"two full independent divider+ADC chains, or one ADC multiplexed across two
dividers — and a multiplexer that can stick is a safety element."* **The multiplexer is only a safety
element if a safety decision is taken from the ADC.** In this design it is not:

| decision | taken by | ADC involved? |
|---|---|---|
| "the output is discharged, the changeover armature may move" (**COLD**) | **hardware window comparator on S3**, gating the `74HC373` latch enable | **No** |
| "the output is over-voltage, kill HV" (**nOVP**) | **hardware comparator** on the buffered S2 tap, latched (`CONTROL_ARCHITECTURE.md` §3.4) | **No** |
| "the parked branch is energised" (self-test) | **hardware comparator on S5** | **No** |
| "monitor and `VMON` disagree by > 20 V, trip" (**ARCH-23**) | firmware, over I²C | **Yes** |
| `MEAS:VOLT?` reporting | firmware, over I²C | **Yes** |

**Every hardware permissive is a comparator on its own string.** The ADC carries reporting and the
firmware disagreement trip. That is a deliberate architectural choice and it is what makes the mux
question tractable: a stuck ADS1115 mux cannot defeat an interlock, because no interlock reads the ADC.

**Note the ADS1115 is *always* a multiplexer.** One PGA, one converter, four pins. "Two dividers on one
ADS1115" and "one divider on each of two ADS1115s" do not differ in whether multiplexing happens — they
differ in whether the *same* mux is in both measurement paths. So the honest comparison is about
common-mode failure, not about multiplexing per se.

### 3.2 What multiplexing costs in simultaneity — quantified

`[verified-run]`, §13:

| | |
|---|---|
| ADS1115 max data rate | 860 SPS ⇒ **1.163 ms** per conversion `[web-verified, ti.com]` `[unverified-MPN]` |
| I²C config write + result read at 400 kHz | ≈ **0.5 ms** |
| 16× oversample-and-average per channel | **26.6 ms** |
| Two differential channels sequenced | **skew up to 26.6 ms between output A and output B** |
| Plant pole (module internal set filter, 100 kΩ × 1 µF) | **100 ms** `[verified-artifact, Figure 2]` |
| Fastest bleed τ on an output node | **5.7 ms** (C_nom) / **198.6 ms** (C_worst) |

**Verdict on simultaneity: acceptable, and for a reason that must be stated rather than assumed.**
26.6 ms of skew is 3.8× *shorter* than the plant's own pole, so for the set-and-hold behaviour G0-A1
froze, the two outputs are effectively read at the same instant. It is **not** short compared with the
fastest bleed transient (5.7 ms at C_nom), so **the two monitors are not simultaneous during a
discharge** — which does not matter, because the discharge decision is COLD, in hardware, per output.
It *would* matter if anyone later required transient or ripple capture; that requirement does not
exist today and adding it re-opens this choice (ADS131M04, 4-channel simultaneous-sampling, is the
replacement — `CONTROL_ARCHITECTURE.md` §2.7).

### 3.3 Why two ADC parts, and which signals go on which

`CONTROL_ARCHITECTURE.md` §2.8 proposed the split *"put the two safety-critical HV monitors on the
SAME part and the diagnostics on the other, so a single ADC failure takes out both independent
monitors together and visibly"* — and explicitly asked for it to be argued rather than defaulted into.

**I adopt the split, and I reject the reason given for it.** "Fails together and visibly" assumes the
failure is visible; an ADS1115 with a drifted internal reference returns plausible numbers on every
channel and is not visible at all. **The real reason is stronger: every safety comparison must cross
the package boundary.**

The only independent check available on an HV monitor reading is the corresponding module's `VMON`
(ARCH-23). If a monitor and the `VMON` it is checked against sit on the same ADC, a common-mode ADC
fault — reference drift, PGA gain error, a stuck mux — moves **both** readings the same way and the
20 V disagreement trip goes blind. In mode 1 output A can be fed by *either* module, so **both**
`VMON`s must be off-part from `HV_MON_A`. That forces exactly one allocation:

| part | addr | channels |
|---|---|---|
| **ADC-A** ADS1115 | 0x48 (`ADDR`→GND) | AIN0 = `MON_TAP_A` · AIN1 = `MON_REF_A` · AIN2 = `MON_TAP_B` · AIN3 = `MON_REF_B` — **two differential pairs, the two independent HV monitors** |
| **ADC-B** ADS1115 | 0x49 (`ADDR`→VDD) | AIN0 = `VMON_P` (buffered) · AIN1 = `VMON_N` (buffered) · AIN2 = `VREF` sense · AIN3 = `+5V` ÷2 |

Every `HV_MON_x` ↔ `VMON_y` comparison crosses from ADC-A to ADC-B. ✔
`+3V3` rail health and the four comparator outputs (`COLD_A`, `COLD_B`, `BRANCH_LIVE_P`,
`BRANCH_LIVE_N`) go to ESP32 GPIO as **reporting copies only** — the hardware paths are direct.

### 3.4 A free mux-integrity check, and it needs one deliberate design asymmetry

The ADS1115 mux offers `AIN0-AIN1`, `AIN2-AIN3`, `AIN0-AIN3`, `AIN1-AIN3` `[recalled — confirm the
`MUX[2:0]` table at G1]`. With the allocation above, **`AIN1-AIN3` reads `MON_REF_A − MON_REF_B`**, a
DC constant that involves neither HV node. If the mux is stuck on any other setting, that read returns
the wrong value.

For the check to have teeth the two references must **deliberately differ**. Set `MON_REF_A` = 2.047 V
and `MON_REF_B` ≈ **1.953 V** (a −94 mV offset = **1502 LSB**, unmistakable). The cost is that chain B
reads a fixed +115 V of apparent HV at true zero, removed by the same two-point calibration that
removes everything else, and its overrange window becomes asymmetric (**+2386 V / −2616 V** instead of
±2501 V — both still beyond every modelled fault). **This is a recommendation, not a requirement; it
costs one resistor value and buys a stuck-mux detector.**

---

## 4. The independent output monitor — one chain per output

### 4.1 The binding constraint is loading, not accuracy and not power

At 1 kV with `Inom` = 0.5 mA, a **5.0 µA divider is exactly 1.00 % of Inom** `[verified-run,
numbers_probe §4.1]`. The top-leg resistance therefore falls straight out of the budget:

```
Rt = Vnom / (f · Inom) = 1000 / (0.01 × 0.0005) = 200.0 MΩ
```

Two things about that equality that are easy to get backwards:

1. **The budget gives `Rt ≥ 200 MΩ`, not `Rt = 200 MΩ`.** Higher resistance loads the module *less*.
   The reason to sit exactly at the limit is §4.5: the dominant error term is surface leakage, and its
   contribution scales as `Rt / R_leak`, so **every ohm added to the top leg makes the monitor worse.**
   200 MΩ is the leakage-optimal choice *subject to* the loading budget. State it that way or a future
   session will "improve" the loading and destroy the accuracy.
2. **Power is a non-issue by two orders of magnitude.** Total dissipation 4.99 mW `[verified-run,
   probe §4.1]`, 0.25 mW per element in the as-built two-string form. Every instinct that says
   *"HV divider, watch the self-heating"* is imported from a higher-current problem.

**In mode 2 there are two of these, each loading its own module by its own 1.00 %.** The budgets do not
share and do not average (MODE-07). Instrument-wide monitor load is 10.0 µA; the number that binds is
the per-module 5.0 µA.

### 4.2 Ratio and network — a passive offset divider read differentially

The output is bipolar and the ADC has no negative rail. Inject a fixed offset current from the
precision reference so that HV = 0 lands mid-window, and read the tap **differentially against a
matched copy of that offset**:

```
                                            guard ring at TAP potential
                                          ┌───────────────────────────────┐
   HV_OUT_A ──┬── S2 top leg, 200 MΩ ──┬──┼─── TAP_A ──[R_ser 1 MΩ]──┬────┼── + OPA2192/A ──┬─→ AIN0 (MON_TAP_A)
              │   (2 ∥ 10 × 40 MΩ)     │  └────────────┬─────────────┼────┘        └───┬────┘  │
              │                        │            C_aa 1 nF        │                 │       │
             S1 BLEED               Rb 909 kΩ           │             └──── guard ──────┘       │
             S3 COLD                   │              GND                                      │
                                    Ro 200 kΩ                                                  │
                                       │                                                       │
                                   VREF +2.500 V (REF5025)                                     │
                                       │                                                       │
                          ┌── 1.78 kΩ ─┴─ 8.25 kΩ ──┐                                          │
                          │      (0.1 % thin film)  │                                          │
                         GND ←──────────────────────┴── MON_REF_A ── OPA2192/B ──→ AIN1         │
                                                                                                │
                                                     ADS1115 ADC-A, differential AIN0–AIN1, FSR ±2.048 V
```

Values `[verified-run]` (E96, so a builder can order them):

| quantity | value |
|---|---|
| `Rt` top leg | **200.0 MΩ** = 2 parallel strings of 10 × **40.0 MΩ** |
| `Rb` to GND | **909 kΩ**, 0.1 %, 25 ppm/K thin film `[unverified-MPN]` |
| `Ro` to `VREF` | **200 kΩ**, 0.1 %, 25 ppm/K thin film `[unverified-MPN]` |
| attenuation α = ∂Vtap/∂Vhv | **8.1899 × 10⁻⁴** (**1221 : 1**) |
| tap at HV = 0 | **2.04747 V** |
| tap at ±1000 V | **2.86645 V / 1.22848 V** |
| tap source impedance 1/G | **163.8 kΩ** ⇒ **buffer mandatory** (ARCH-08, F-21) |
| ADC ±FS corresponds to | **±2500.7 V of HV** |
| 1 ADC LSB (62.5 µV) referred to HV | **0.0763 V** |
| overrange margin vs the 1320 V `VSET` single fault (PART-33) | **1.89×** |
| overrange margin vs the 2012 V clamp-reference fault (probe F-9) | **1.24×** |

**The last two rows are the reason α is 8.19 × 10⁻⁴ and not the probe's 1.024 × 10⁻³.** See §11.1 —
this is my loudest disagreement with `NUMBERS_PROBE.md`.

**`VREF` drift cancels in the differential reading.** `TAP = α·V + VREF·k₁` and `REF = VREF·k₂`; if
`k₁ = k₂` by construction, `TAP − REF = α·V` independent of `VREF`. Only the *mismatch* survives:
with 0.1 % resistors and a REF5025 at 3 ppm/K over 20 K, the residual is **~0.1 mV of HV** — i.e. the
probe's **0.200 V** "offset ref drift" term **disappears**. That is the second reason for the
differential topology, after bipolarity.

### 4.3 String composition — the per-resistor **working voltage** is the binding spec, not power

`DECISIONS.md` ARCH-12, read from the actual Yageo RC datasheet `[verified-artifact]`, kills the
obvious approach twice over:

- **Ordinary ±1 % chip resistors stop at 2.2 MΩ.** A 200 MΩ top leg out of them needs **91 elements in
  series** `[verified-run, probe §4.2]` — 91 chances to go open, 182 joints, 411 mm of board.
- **Upsizing the package buys power, not volts:** 0805 = 150 V, 1206 = 200 V, **2010 = 200 V,
  2512 = 200 V**. (Two pieces of folklore corrected: 0603 is 50 V not 75 V; 2512 is 200 V not 500 V.)

So the top leg is built from **purpose-made HV divider elements**, and the element count is set by
**working voltage at 50 % derating** *and* by a constraint that is not on any datasheet — **the
package's own pad-to-pad gap against the clearance that the per-element voltage demands**:

| string | part class | per string | element | V/element | P/element | pad gap | IPC-2221 B2 need | verdict |
|---|---|---|---|---:|---:|---:|---:|---|
| **S2 monitor** | 1206 HV, 800 V rated `[ASSUMED]` `[unverified-MPN]` | 10 series | **40.0 MΩ** | **100.0 V** | 0.250 mW | 1.925 mm | 0.600 mm `[unverified-primary]` | **OK, 3.2×** |
| **S1 bleed** | 2512 HV, 1500 V rated `[ASSUMED]` `[unverified-MPN]` | 2 series | **20.0 MΩ** | **500.0 V** | 12.50 mW | 4.925 mm | 2.500 mm `[unverified-primary]` | **OK, 1.97×** |
| **S3 COLD / S5 branch** | 2512 HV | 2 series | **1.00 GΩ** | **500.0 V** | 0.250 mW | 4.925 mm | 2.500 mm `[unverified-primary]` | **OK, 1.97×** |

Two elements are rejected outright by the probe's own screen and must not be substituted back in:

- **"1206 HV at 800 V rating, N = 3" is REJECTED** (probe finding F-5): a rating high enough to need
  only 3 elements puts **333 V across a package whose own pad gap is 1.925 mm**, below the 2.500 mm
  that voltage demands. *A part's voltage rating and its package clearance are independent constraints
  and only the first is on the datasheet.*
- **A 2 × 100 MΩ CRHV1206 top leg — the part `CONTROL_ARCHITECTURE.md` §2.3 recommends — fails the
  same screen** at 500 V per 1206 element. See §11.3.

**Element count is also the VCR lever, and it is the only one.** Voltage coefficient acts on the
voltage across *each* element, so the leg's fractional error is `k·V/N` and the error referred to the
output is `k·V²/N` — **quadratic in voltage, inverse in element count** `[verified-run, probe §4.3]`:

| | k = 1 ppm/V | k = 5 ppm/V | k = 25 ppm/V |
|---|---:|---:|---:|
| N = 2 | 0.500 V | 2.500 V | 12.500 V |
| N = 5 | 0.200 V | 1.000 V | 5.000 V |
| **N = 10** | **0.100 V** | **0.500 V** | **2.500 V** |
| N = 20 | 0.050 V | 0.250 V | 1.250 V |

**At k = 25 ppm/V and N = 2 the monitor is worse than the `VMON` it exists to check.** F-22 stands
un-retired: *nobody has costed the divider VCR*, and it is a nonlinearity, so a single-point gain
calibration cannot remove it. ⇒ **`k_VCR` is a purchase parameter with a specification, not an
assumption. Require `k_VCR ≤ 5 ppm/V` on the datasheet and put it in the BOM line.**

### 4.4 Error budget — and the assumption that swings it by 6×

All `[verified-run]`, §13. ΔT = ±20 K about a two-point calibration; initial gain, initial ratio and
the fixed offset are calibrated out, so only drift and nonlinearity remain.

| term | formula | k_VCR = 1 ppm/V, N = 10 |
|---|---|---:|
| VCR | `V·k·(V/N)` | 0.1000 V |
| **TCR mismatch top-vs-bottom** | `V·ΔTCR·ΔT` | **see below** |
| self-heating | `V·ΔTCR·(I²R·Rth)` | 0.0002 V |
| ADC INL, 1 LSB | `LSB/α` | 0.0763 V |
| ADC gain drift, 5 ppm/K `[recalled]` | `V·g·ΔT` | 0.1000 V |
| offset-reference drift | mismatch-limited (differential) | 0.0002 V |

| TCR tracking assumption | source | e_TCR | **RSS** | vs `VMON` 10 V |
|---|---|---:|---:|---:|
| **10 ppm/K** | `numbers_probe.py` `TCR_MATCH_PPM_K` — **`[ASSUMED]`, no part named** | 0.200 V | **0.2566 V** | **39.0×** |
| **35 ppm/K** | **the value this document specifies** (top ≤ 25 ppm/K, bottom ≤ 10 ppm/K) | 0.700 V | **0.7182 V** | **13.9×** |
| **75 ppm/K** | CRHV 100 ppm/K vs a 25 ppm/K bottom leg — the only part `CONTROL_ARCHITECTURE.md` §2.5 actually names, `[web-verified]` | 1.500 V | **1.5086 V** | **6.6×** |
| 75 ppm/K **and** k_VCR = 5 ppm/V | a plausible unspecified HV part | 1.500 V | **1.5861 V** | **6.3×** |

**Answer to "does it beat the module's own 10 V `VMON` accuracy": yes, in every case above — but the
"31× better" headline in `NUMBERS_PROBE.md` §4.3 is true only at an assumed TCR tracking that no
named part achieves.** At the CRHV the project has actually shortlisted, the honest number is **6.6×**.
Both meet the requirement; only one of them is evidence.

⇒ **Specification, not assumption:** top-leg TCR **≤ 25 ppm/K**, bottom-leg TCR **≤ 10 ppm/K**, and
they must be *specified on the datasheet*, not inferred. If the procurable part is 100 ppm/K, the
monitor still passes at 6.6× and nothing in the design changes — but §11.4 must be updated so nobody
quotes 31× at a review.

**Long-term drift is the dominant lifetime term and it is not in the RSS.** CRHV-class stability is
**< 0.5 % over life** `[web-verified]` = **5.0 V at 1 kV** — larger than every instantaneous term
combined. ⇒ **periodic two-point recalibration against a DMM belongs in the instrument's documented
maintenance**, not in a footnote.

### 4.5 Surface leakage — the term that decides whether any of the above is true

At 200 MΩ this is a >100 MΩ-class measurement and PCB surface resistance is a circuit element in
parallel with the top leg. `err = V · Rt / R_leak` `[verified-run, probe §4.4]`:

| board condition | R_leak | S2 error (200 MΩ) | S3 error (1 GΩ) |
|---|---:|---:|---:|
| clean, conformally coated | 1 TΩ | 0.200 V | 1.00 V |
| **bench-clean bare FR-4** | 10 GΩ | **20.0 V** | 100 V |
| contaminated / humid | 1 GΩ | 200 V | 1000 V |

**An unguarded 200 MΩ divider at 1 kV is not an independent monitor, it is a humidity sensor.** Total
RSS including leakage `[verified-run]`:

| condition | 10 ppm/K | 35 ppm/K | 75 ppm/K | |
|---|---:|---:|---:|---|
| coated 1 TΩ **+ driven guard** | 0.2566 V | 0.7182 V | 1.5086 V | beats `VMON` |
| bare FR-4 10 GΩ **+ driven guard** | 0.3253 V | 0.7455 V | 1.5218 V | beats `VMON` |
| **bare FR-4 10 GΩ, NO guard** | **20.00 V** | **20.01 V** | **20.06 V** | ***FAILS* — worse than the readback it exists to check** |

**The driven guard ring is a requirement of the monitor, not a refinement** (probe finding F-8).
Mandatory, all three:

1. **Guard ring at TAP potential, driven from the buffer output**, surrounding the tap node, the
   `R_ser`/`C_aa` network and the buffer's non-inverting input, and running alongside the whole S2
   string. Assumed improvement **100×** `[ASSUMED]` — this constant has never been measured and is the
   single least-supported number in the accuracy claim.
2. **Conformal coating over the divider region**, applied after cleaning to a written process.
3. **The divider gets its own netclass** (`HV_SENSE`) and its own dedicated `HVDIV_GUARD` net
   (`INTERFACES.md` §2.1 already reserves both).

**Two leakage paths, two different signs, and only one of them is dangerous:**

| path | in parallel with | reading | direction |
|---|---|---|---|
| HV node → TAP (across the top leg) | `Rt` | **reads HIGH** | fail-safe (over-reports) |
| TAP → GND | `Rb‖Ro` (163 kΩ — 61 000× lower) | negligible | — |
| interior string node → GND | the lower part of the string | **reads LOW** | **unsafe direction** |

The guard addresses all three: it terminates HV-side surface current before it reaches the tap, and it
holds the region around the tap at tap potential so a TAP → guard path sees ≈0 V.

### 4.6 Buffer

**OPA2192 (dual)** — Vos ±25 µV max, Ib ±20 pA max, RRIO, **minimum supply 4.5 V**
`[web-verified, ti.com]` `[unverified-MPN]`. **One dual per chain**: A = tap buffer, B = reference
buffer. Chain A and chain B are therefore in **different packages**; a package failure kills one chain
and is caught by that chain's cross-part `VMON` comparison.

- **It cannot run on 3.3 V. Power it from +5 V.** The tap swings 1.228…2.866 V for ±1000 V and
  0.000…4.096 V at the ±2500 V overrange limit — inside a 5 V RRIO range at both ends.
- Vos → **0.031 V of HV**; Ib × 163.8 kΩ → **0.004 V of HV** `[verified-run]`. Both negligible.
- If a 3.3 V-only analogue rail is ever mandated, **OPA333** (Vos 10 µV, Ib 200 pA `[recalled]`) gives
  0.012 V / 0.040 V — also fine. The 4.5 V minimum is the only reason OPA192 is not the default.

**Input protection — and why there are no clamp diodes on the tap.** A flashover from the HV node to
the tap would present kilovolts to the op-amp input. The protection is **`R_ser` = 1 MΩ in series**,
which limits a 1000 V fault to **1.00 mA** against the OPA192's ±10 mA input-current absolute maximum
`[recalled — confirm at G1]`. It costs `Ib × 1 MΩ` = **0.024 V of HV** and adds 0.407 µV of Johnson
noise over a 10 Hz bandwidth = **0.0005 V of HV** `[verified-run]` — both negligible.
**Deliberately no BAV99/BAV199 clamp on the tap:** a clamp's reverse leakage flows in the tap node's
163.8 kΩ and 1 nA there is **0.2 V of HV** — larger than the entire calibrated error budget. The
op-amp's own input cells, current-limited by `R_ser`, are the better protection.
`C_aa` = **1 nF** at the buffer input gives a 1 ms anti-alias pole against a 100 ms plant.

### 4.7 ADC selection — and the quantitative case against the ESP32's internal ADC

**Required tolerance**, derived rather than asserted: the monitor must (i) beat 10 V, (ii) resolve the
20 V disagreement trip with margin, and (iii) resolve the 45 V COLD threshold for the firmware's
independent confirmation. Target ≤ **1 V at 1 kV** ⇒ LSB ≤ 0.1 V of HV ⇒ **≥ 15 effective bits**.

| candidate | verdict |
|---|---|
| **ESP32 internal ADC** | **Reject, by a factor of 10–30, not by taste.** 12 bit over 3.3 V ⇒ LSB = 806 µV ⇒ **0.98 V of HV** *before* any error term — already at the whole budget. Then ±1–3 % INL/DNL with non-monotonic regions `[recalled]` ⇒ **10–30 V of HV**, i.e. **worse than the `VMON` it exists to check**, so invariant (c) would be unmet *by construction*. Non-monotonicity means two-point calibration cannot rescue it. And on classic ESP32, **ADC2 is unusable while WiFi is active** `[recalled]` — G0-A3 mandates WiFi. Not a close call. |
| **MCP3421** | 18 bit but **single channel** `[recalled]`. We need 8 channels across two parts. No advantage. |
| **ADS131M04** | 24 bit, 4-channel **simultaneous** sampling, SPI `[recalled]`. Genuinely better and the correct answer *if* ripple or transient capture ever becomes a requirement. Today it buys simultaneity we showed (§3.2) we do not need. |
| **ADS1115 ×2** ✅ | 16 bit ΔΣ, 4 SE / 2 differential, **4 selectable I²C addresses**, 2.0–5.5 V, internal low-drift reference, PGA ±0.256…±6.144 V, 860 SPS, on-chip comparator `[web-verified, ti.com]` `[unverified-MPN]` |

**Why the ADS1115 specifically fits this problem:**

- **True differential input** is what makes the bipolar offset divider work at all, and it is what
  cancels `VREF` drift (§4.2).
- **±2.048 V FSR** against a ±0.819 V signal gives **2.5× overrange headroom** (§11.1) — the headroom
  is not slack, it is what lets the monitor *see* the "output voltage is internally not limited"
  condition rather than railing and reporting a plausible full-scale number.
- **LSB = 0.0763 V of HV**, 3.4× finer than the best-case accuracy and 20× finer than the 20 V trip.
- **860 SPS is ample**: the plant's 100 ms pole means the output cannot move faster than ~1.6 Hz;
  16× averaging gives 37 Hz effective, still 23× faster than the plant, and buys 2 bits of noise
  averaging.
- **The on-chip comparator is useful but is NOT the hardware OVP** — it is I²C-configured and therefore
  trusts firmware. `nOVP` stays a discrete latched comparator (`CONTROL_ARCHITECTURE.md` §3.4).
- **Its 0.15 % gain error calibrates out entirely** in a two-point calibration against a DMM; what
  survives is the ~5 ppm/K drift term already budgeted.

⇒ **An external ADC is not a preference here, it is a requirement.** The internal ADC fails the stated
tolerance by more than an order of magnitude and fails it non-correctably.

### 4.8 What this monitor is, and is *not*, independent of

Invariant (c) says *"independent of the module readbacks."* It is worth writing down exactly what that
buys, because "independent" is doing a lot of work:

| shared with `VMON`? | element |
|---|---|
| **No** | the HV sense node · the divider · the attenuation ratio · the offset reference · the buffer · the ADC · the I²C address · the supply rail for the analogue chain |
| **Yes** | the HV output node itself · the board ground · the ESP32 and its firmware · the I²C bus |

So the pair detects: an open divider element, a stuck or welded relay, a module in current limit, an
ADC reference collapse, partial HV breakdown, and a wrong-polarity condition — **none of which either
monitor detects alone** `[probe §4.5]`. It does **not** detect a fault in anything in the right-hand
column. In particular **a hung I²C bus blinds both monitors at once**; the response to that is the
comms/heartbeat watchdog (C-3), not more analogue redundancy.

**Trip threshold** (ARCH-23, re-derived at this design's accuracy `[verified-run, probe §4.5]`):
legitimate quadrature disagreement `√(10.0² + 0.379²) = 10.007 V`; trip at **2 %·Vnom = 20.0 V** ⇒
**2.00× margin.** At the pessimistic 75 ppm/K monitor the legitimate disagreement is
`√(10.0² + 1.52²) = 10.11 V` and the margin is **1.98×** — the trip threshold survives the TCR
disagreement of §4.4 unchanged.

**Two extra firmware checks that cost nothing and cover the failures the trip cannot see:**

1. **Zero-point plausibility.** With both modules off, `MON_TAP_A − MON_REF_A` must sit inside a narrow
   calibrated window. An open top leg shifts the tap by **+1.678 mV = +2.05 V of apparent HV = 27 LSB**
   `[verified-run]` — a large, unambiguous signature. This is the *only* check that sees an open
   monitor string **at commanded zero**, which is exactly where the 20 V disagreement trip is blind
   (this is `COMBINER_STUDY.md` **F-13**'s lesson transferred: *the board is most energised exactly
   when its monitor is least trustworthy*).
2. **Sign check in mode 2.** With both outputs live, `OUT_A` must read positive and `OUT_B` negative.
   A sign disagreement means a routing element is not where it is believed to be, and the independent
   monitor is the only thing on the board that can see it `[probe §4.5]`.

---

## 5. The COLD-permissive chain — S3

### 5.1 What it must do and what it must never do

`COLD` is a **permissive to change state**, not a continuous requirement. The naive version — gate the
relay coil with "the bus is cold" — is a showstopper: raise the output and the gate opens and the relay
**drops out while HV is live**, which is the hot switch it was meant to prevent
(`topology/hv-relay-changeover.md` §2.3). The correct form is a **transparent latch**:
`74HC373`, `D` = `SEL` from the ESP32, `LE` = `COLD`. Bus hot ⇒ latch opaque ⇒ **the armature is frozen
no matter what firmware writes.**

### 5.2 The COLD divider is allowed to be inaccurate, and that is the whole design

`COLD` needs **20 : 1 discrimination** (is this node at 1000 V or below 45 V?), not 0.03 % accuracy. It
can therefore be **five times higher in resistance than the monitor**, which is exactly the currency
the load budget is short of.

```
   HV_OUT_A ──┬── S3 top leg 1.00 GΩ ──┬── COLD_NODE ──┬── TLV3201 (upper)  ─┐
              │   (2 ∥ 2 × 1.00 GΩ)    │               └── TLV3201 (lower)  ─┴─ AND ─→ COLD_A
             S1, S2                 Rb 5.62 MΩ                  ▲
                                       │                        │  window centre = REF3020, 2.048 V
                                    Ro 1.24 MΩ                  │  ±46 mV (a SEPARATE reference part)
                                       │
                                   VREF +2.500 V
```

`[verified-run]`:

| quantity | value |
|---|---|
| `Rt` | **1.00 GΩ** = 2 parallel strings of 2 × **1.00 GΩ**, 2512 HV, 500 V/element, 0.25 mW/element |
| `Rb` / `Ro` | **5.62 MΩ / 1.24 MΩ**, 0.1 % |
| α_cold | **1.0148 × 10⁻³** |
| node at HV = 0 | **2.04603 V** |
| node at ±1000 V | **3.0609 V / 1.0312 V** |
| node source impedance | 1.015 MΩ (fine for a 1 pA-bias comparator) |
| **COLD threshold** | **±45 V** ⇒ window **±45.67 mV** about the centre |
| loading | **1.0 µA = 0.20 % of Inom** |

**Threshold error budget** `[verified-run]`: TLV3201 Vos ±1 mV max → ±0.99 V of HV; 5 mV designed
hysteresis → 4.93 V; 0.25 % reference mismatch between the node's `VREF` offset and the REF3020 window
centre → ±5.00 V; static offset from the E96 rounding (node0 = 2.04603 V vs a 2.048 V centre) →
+1.94 V. **Total ≈ ±13 V ⇒ the true threshold lies in 32…58 V, entirely below the 60 V touch-safe
limit** `[unverified-primary]`. That is why the nominal is 45 V and not 50 V or 60 V.

### 5.3 Leakage cannot fool COLD, and the arithmetic says why

At 1 GΩ, bench-clean bare FR-4 (10 GΩ) injects a **100 V** error — ten times worse than the monitor's.
It does not matter, and the reason is worth writing down because it inverts the usual instinct:

- **HV → node leakage reads HIGH** ⇒ `COLD` false ⇒ **stuck-safe.**
- To make a genuinely live 1000 V node read below the 45 V threshold, a leakage path would have to
  attenuate the reading by **21.2×**, i.e. `R_leak ≈ Rt/21.2 =` **47.1 MΩ of surface leakage**
  `[verified-run]`. That is not a humid day, that is a visibly wet board.

⇒ **S3 needs no driven guard ring.** Generous spacing and conformal coating are sufficient, and one
buffer and one guard corridor are saved. *(S2 does need one — its requirement is 0.03 %, not 20 : 1.)*

### 5.4 The failure that redundancy alone cannot fix — and the fix

**An open S3 element makes `COLD` read TRUE. That is the unsafe direction, and NUM-09's parallel-string
rule does not repair it** — two parallel strings with one open read *half*, so the effective threshold
doubles from 45 V to 90 V. Better than a single string (which reads 0 V and declares COLD always), but
still unsafe and still silent.

**Fix: make COLD a 2-of-2 AND across two physically different measurements.**

```
  COLD_A = ( |S3_node_A − 2.048 V| < 46 mV )     ← dedicated COLD string, SA-8's requirement
       AND ( |MON_TAP_A − MON_REF_A| < 46 mV )   ← a second comparator on the ALREADY-BUFFERED S2 tap

  LE(74HC373) = COLD_A AND COLD_B               ← both outputs, in both modes
```

| fault | S3 comparator | S2 comparator | `COLD` | verdict |
|---|---|---|---|---|
| S3 string open | says COLD (wrong) | says HOT | **HOT** | **stuck-safe** ✔ |
| S2 string open | says HOT | says COLD (wrong) | **HOT** | **stuck-safe** ✔ |
| both genuinely discharged | COLD | COLD | **COLD** | changeover permitted ✔ |

**This exactly inverts F-3.** F-3's chain was *"one open HV resistor ⇒ COLD permanently TRUE ⇒ every
changeover hot-switches."* Under the AND, one open HV resistor ⇒ **COLD permanently FALSE ⇒ no
changeover ever happens**, which is an inconvenience, not a hazard, and it is loudly visible on the
first attempted polarity change.

> ⚠ **This requires a wording change to `INTERFACES.md` SA-8, and I am not making it silently.**
> SA-8 currently reads *"The COLD/permissive divider shares **no component** with the invariant-(c)
> monitor divider."* Read literally it forbids the AND above, because `COLD` would then *depend on*
> the monitor chain. **Proposed replacement, preserving F-3's intent and strengthening it:**
> *"The COLD permissive has its own divider string, and no single component failure anywhere may
> force COLD TRUE."* The dedicated S3 string still exists and SA-8's literal requirement is still
> met by it; the AND adds a veto. **This is a G1 decision — recorded, not taken here.**

**Comparator output polarity is load-bearing** (`topology/hv-relay-changeover.md` fault 21): use
**push-pull outputs with a pull-DOWN on the `COLD` net**, never open-drain with a pull-up. An
open-drain failure or a lost comparator supply pulls up to a **false `COLD` = 1**; push-pull plus
pull-down makes both of those `COLD` = 0 = latch opaque = **stuck-safe.**

### 5.5 The reference failure that would have defeated it, and the split that prevents it

If the S3 node's offset current and the comparator's window centre both came from `VREF`, then a
**`VREF` failure drives both to 0 V**, `|0 − 0| < 46 mV` is satisfied, and **`COLD` reads TRUE at any
output voltage.** A single-fault, silent, unsafe-direction failure of the changeover permissive.

⇒ **The two references must be different parts.** Node offset from **REF5025 (2.500 V)**, window centre
from **REF3020 (2.048 V)** `[unverified-MPN]`.

| fault | node | window centre | `COLD` | |
|---|---|---|---|---|
| REF5025 dies | → 0 V at HV = 0 | 2.048 V | `abs(0 − 2.048) > 46 mV` ⇒ **FALSE** | stuck-safe ✔ |
| REF3020 dies | 2.046 V | → 0 V | `abs(2.046 − 0) > 46 mV` ⇒ **FALSE** | stuck-safe ✔ |

The price is the 0.25 % inter-reference mismatch already carried in §5.2's ±13 V threshold budget.
**Both references are read by ADC-B (AIN2, and via the +5 V÷2 channel) so firmware can also see it —
but firmware is the second line, not the first.**

### 5.6 Two COLDs, one rule, both modes

`COLD_A` and `COLD_B` are built identically, one per output node, and the latch enable is
`COLD_A ∧ COLD_B` **in both modes**. In pseudo-bipolar mode `OUT_B` is dead, so `COLD_B` is trivially
true and the term costs nothing; in dual-unipolar mode there is no polarity changeover, so the latch is
not exercised — but `COLD_A ∧ COLD_B` is exactly the signal the **mode-change procedure** needs
(MODE-08 step 3: *verify both outputs below threshold on the independent monitors — verify, do not
merely wait*), and it is exactly the signal **MODE-18** needs when the mode switch sits between
detents. Making it mode-independent removes a state from the logic instead of adding one.

---

## 6. Branch monitors — S5

One per module, on the module's own HV pin, **upstream of the changeover relay**. Electrically
identical to S3 (1.00 GΩ, 2 ∥ 2 × 1.00 GΩ, 2512 HV, 0.20 % of Inom), with a **single-threshold**
comparator at 45 V rather than a window, giving `BRANCH_LIVE_P` / `BRANCH_LIVE_N`.

**Why it exists** (`COMBINER_STUDY.md` F-2, and correction C-2's second sentence): the weld self-test
raises one module while it is parked on its NC contact and requires the bus to stay at 0 V. Without a
monitor on the parked branch, **a dead module, an open `/ON`, an open series limiter and a correctly
blocked contact all produce the same "bus stayed at 0" PASS.** The test cannot distinguish *stimulus
applied and blocked* from *no stimulus was ever applied*. `BRANCH_LIVE_x` is what turns the self-test
from a detector with a silent false-pass into a real one.

**It must be a comparator and not an ADC channel**, for three reasons: the ADC channel budget is full
(§3.3); it must work with the ESP32 in any state; and the magnitude is already available from that
module's `VMON` on ADC-B — S5 supplies the *independent* fact, `VMON` supplies the number.

**Loading during the self-test:** a parked, energised module drives its NC bleed (50 µA) plus S5
(1 µA) = **51 µA against a 750 µA limit**, so the branch really does reach 1 kV and the stimulus is
real. Outside the self-test a parked module is off and the load is zero.

---

## 7. Bleed and discharge — S1 and S4

### 7.1 Discharge time is *not* the constraint at this class, and reading it the wrong way round leads to the wrong part

`R(t) = t / (C·ln(V₀/V_safe))`, V₀ = 1000 V, V_safe = 60 V, ln = 2.8134 `[verified-run, probe §3.2]`:

| target t | R at C_nom (0.320 nF) | R at C_worst (11.12 nF) |
|---:|---:|---:|
| 1 s | 1.11 GΩ | 31.96 MΩ |
| **5 s** | **5.55 GΩ** | **159.8 MΩ** |
| 30 s | 33.3 GΩ | 958.9 MΩ |

**A 5 s discharge from 1 kV at the nominal capacitance needs 5.6 GΩ** — a resistance so high that board
surface leakage would swamp it and no real part would hold its value. **The binding constraints are the
permanent-load budget and the element's working-voltage rating, not the time constant.** That inverts
the usual bleed-design intuition and is only visible with the numbers on the page.

### 7.2 The bleed we fit

```
R_bleed = Vnom / (f · Inom),  f = 0.10  =  1000 / (0.10 × 0.0005)  =  20.0 MΩ
```

**Realisation (NUM-09 / SA-9): two parallel strings of two series 2512 HV elements of 20.0 MΩ**
(2 ∥ 40 MΩ = 20 MΩ). Per element **500 V, 12.5 mW** `[verified-run]`, against a 1500 V `[ASSUMED]`
rating at 50 % derate = 750 V (**1.5×**) and a 0.3 W-class power rating (**24×**). Package pad gap
4.925 mm against the 2.500 mm `[unverified-primary]` that 500 V demands (**1.97×**).
**Two strings side by side, not end to end** — see §9.

**The bleed is PERMANENT, unswitched, and connected at the output connector, downstream of the mode
switch.** Three consequences, all structural:

- **A switched bleed can fail open, and a bleed that only runs on command is not a bleed.** `f` is a
  real budget, spent forever, and that is the price of the guarantee.
- Being at the connector, downstream of the mode element, it is present in **every** mode and in
  **every** switch position **including between detents** — which is precisely what **MODE-18** demands
  (*"both modules off, both output nodes bled"*) and it satisfies it **with no power, no firmware and
  no contact in the right place.**
- `OUT_B` is bled in pseudo-bipolar mode too, when it is otherwise disconnected from everything.

**S4, the module-side bleed**, is 20 MΩ in the same construction, connected through the Form-C **NC**
contact. It bleeds the *deselected* module and **never loads the active one** — invariant (b) satisfied
**structurally rather than by a timer**, which is the single best property of the adopted topology
(`COMBINER_STUDY.md` §5.1 reason 2). A bleed only downstream of the relay cannot discharge the node
behind an open contact, and in pseudo-bipolar mode that node is exactly the one holding full voltage
after disable.

### 7.3 What the output node actually discharges through — the probe undercounts, in the safe direction

The probe computes discharge from the bleed alone. **All three strings are on the node**
`[new-this-session, verified-run]`:

`20 MΩ ‖ 200 MΩ ‖ 1 GΩ = 17.857 MΩ`

| condition | R | τ (C_worst 11.12 nF) | 1 kV → 60 V | 1 kV → 45 V (COLD) | 1 kV → 1 V |
|---|---:|---:|---:|---:|---:|
| **all three strings, C_nom 0.320 nF** | 17.86 MΩ | 5.7 ms | **0.016 s** | 0.018 s | 0.040 s |
| **all three strings, C_worst** | 17.86 MΩ | 198.6 ms | **0.559 s** | 0.616 s | 1.372 s |
| *(probe §3.3, bleed alone, C_worst)* | 20.0 MΩ | 222.4 ms | *0.626 s* | — | 1.536 s |
| **one bleed sub-string open**, C_worst | 32.26 MΩ | 358.7 ms | **1.009 s** | 1.112 s | 2.478 s |
| **BOTH bleed strings open**, C_worst | 166.7 MΩ | 1.853 s | **5.214 s** | 5.747 s | 12.80 s |

**The probe's 0.626 s is conservative by 11 %** and this document does not disagree with it — it is the
right number to quote, because it is the number that survives if the monitor and COLD strings are ever
re-sized.

**Row 4 is NUM-09's payoff, quantified for the first time.** One open bleed element degrades the
discharge from 0.56 s to 1.01 s and nothing else — **still 5× inside the 5 s target, and silently.**
That is exactly the argument for two parallel strings rather than one series chain: *an open bleed is
silently undetectable*, so the design must tolerate it rather than detect it.

**Row 5 is the honest limit.** With both bleed strings open the node still discharges — through the
monitor and COLD strings — but takes 5.2 s, marginally past the 5 s target. It is **not a hazard**,
because `COLD` simply refuses the changeover until the node genuinely reads below 45 V. **That is the
structural answer to the whole question:** see §7.5.

### 7.4 Stored energy: this is a startle hazard, not an energy hazard

`[verified-run, probe §3.6]`, thresholds 350 mJ / 50 µC `[unverified-primary]`:

| scenario | C | E | Q |
|---|---:|---:|---:|
| bare board, no cable | 0.120 nF | 0.060 mJ | 0.120 µC |
| 2 m SHV lead, no load | 0.320 nF | 0.160 mJ | 0.320 µC |
| 2 m + 1 nF load | 1.320 nF | 0.660 mJ | 1.320 µC |
| **10 m lead + 10 nF load** | 11.12 nF | **5.560 mJ** | **11.12 µC** |
| mode-2 `OUT_A`↔`OUT_B` bridge at 2000 V | C/2 | **11.12 mJ** | 11.12 µC |

Worst credible stored energy is **63× below** the 350 mJ threshold. **The charge criterion binds first**
— 1000 V becomes a hazardous stored-energy source at **50 nF**, the energy criterion only at 700 nF.

> **DESIGN LIMIT, and it is a hard one: total output capacitance < 50 nF per output. Fit NO bulk HV
> filter capacitor.** The module already delivers < 30 mV pp ripple above 20 V; a filter cap would buy
> a little ripple and sell the stored-energy classification, which changes the enclosure and interlock
> requirements for the whole instrument.

**The shock hazard is the sustained source, not the stored charge:** 0.75 mA at up to 1000 V,
continuously, **from both outputs at once in mode 2**. 0.75 mA DC is above the let-go threshold for a
hand-to-hand path. The current limit reduces the *consequence* of contact; it does not make contact
acceptable and it is not an alternative to the enclosure.

### 7.5 Does the bleed alone satisfy the discharge invariant? — **No, and it is not supposed to.**

The task asks this directly, so here is the direct answer.

**The bleed alone does NOT satisfy invariant (b).** Three reasons, all still true after re-derivation:

1. **`C_out` is not ours to control.** NUM-13's ≤ 10 nF is a *declared constraint we impose*, not a
   measured fact about the user's load, and Q3 was not answered at G0. At 100 nF the discharge is
   **5.63 s** and the invariant fails; at 1 µF it is 56 s.
2. **A bleed is an open-loop timer.** "Wait 2 s" is a firmware convention, and `CLAUDE.md` says a
   firmware convention is not sufficient for an HV invariant.
3. **A bleed can fail open silently** (§7.3 row 5).

**What satisfies invariant (b) is the pair: a permanent bleed that performs the discharge, and the
hardware `COLD` permissive that *refuses to let anything move* until the discharge has actually
happened.** Neither is sufficient alone; together they turn every failure of the bleed into a
**refusal** rather than a hot switch:

| failure | with bleed only | with bleed + COLD |
|---|---|---|
| `C_load` 10× over spec | firmware's dwell expires, changeover proceeds at 400 V, **hot switch** | `COLD` false ⇒ latch opaque ⇒ **no changeover**, discharge timeout ⇒ **TRIP** (ARCH-24) |
| one bleed string open | 1.01 s instead of 0.56 s, undetected, harmless | same, and the permissive still verifies |
| both bleed strings open | dwell expires at ~500 V, **hot switch** | **no changeover**, TRIP |
| module internal capacitance 100× the assumption | **hot switch** | **no changeover**, TRIP |

**ARCH-24 is the rule that makes this work and it must not be softened:** on discharge timeout,
**TRIP — leave the switch where it is and tell a human.** Every other timeout in the state machine may
degrade toward "off" because off is safe; this one would hot-switch at unknown high voltage and weld a
contact.

### 7.6 Is a switched dump also needed? — **No. Recommendation: do not fit one.**

| for | against |
|---|---|
| Collapses the worst-case dwell from 0.63 s to ~1 ms | **Nothing requires it.** G0-A1 accepts *"a dead-band of order 1 second"*; the measured worst case is 0.87 s end-to-end (§7.7) |
| | **`INTERFACES.md` SA-12 forces `1.5·Inom·R < 60 V` ⇒ R < 80 kΩ.** A dump that low must be *switched*, and switched at 1 kV |
| | **The switch does not exist at this class.** G0-A2 consequence 2 eliminated the ≤600 V PhotoMOS parts. A 1 kV dump needs **a third HV relay**, ≈\$120, in the topology whose relay line is already 74 % of the combiner BOM and which two agents failed to price (R-7) |
| | **`COMBINER_STUDY.md` F-17: a fail-safe crowbar is hot-switched by design on every emergency operation** — exercising the exact welding mechanism the topology is built to avoid, on the one contact whose correct operation is the last line of defence and which is *never exercised in normal use* |
| | **F-12: a dump sized against the wrong impedance leaves a hazardous voltage.** Node analysis of a proposed 1 MΩ dump gave **−111.9 V** at commanded zero and **−223.8 V** with the other module at full scale. A dump is easy to get wrong and its failure is quiet |
| | It adds a **third** thing that must be bled, monitored and interlocked, on a board that already carries 20 HV strings |

**Reversal condition, stated so the decision is falsifiable:** fit a dump if a bench measurement shows
the module's own output capacitance, or an accepted `C_load`, pushes discharge to 45 V beyond ~2 s —
because at that point the dead-band exceeds what G0-A1 accepted and the argument changes from safety to
usability. **Then the correct dump is a third Form-C relay whose NC position carries the dump resistor,
so it is connected when de-energised** (never a normally-open crowbar that must actively close in an
emergency).

### 7.7 The changeover dead-band, end to end

Pseudo-bipolar polarity change, worst case `[new-this-session, verified-run]`:

| step | C_nom | C_worst |
|---|---:|---:|
| 1. command setpoint to 0 (module's own 100 ms pole; overlapped with step 3) | — | — |
| 2. disable — `/ON` high, then `+VIN` removed via `K_S` | ~20 ms | ~20 ms |
| 3. bleed until the node reads below the 45 V COLD threshold | **0.018 s** | **0.616 s** |
| 4. `COLD` asserts, latch opens, `SEL` propagates, relay transfers (Pickering 6 ms max) | 0.006 s | 0.006 s |
| 5. module restart from `+VIN` — **`[ASSUMED]` 150 ms, MEASURABLE-NOW** | 0.150 s | 0.150 s |
| 6. ramp to the new setpoint — **`[ASSUMED]` 100 ms, MEASURABLE-NOW** | 0.100 s | 0.100 s |
| **total** | **≈ 0.27 s** | **≈ 0.87 s** |

**Inside the "order 1 second" G0-A1 accepts, at the worst credible capacitance.** Note steps 5 and 6
are two of the four unmeasured module parameters and together they are **29 % of the C_nom dead-band**;
at C_worst the bleed dominates.

**The hardware monostable and `COLD` do different jobs and fail in different directions — keep both.**
`CONTROL_ARCHITECTURE.md` §3.5's `74HC123` forces `ARM = 0` for `T_dwell` on any `SEL` or `MODE_POS`
edge; it bounds the **minimum** dwell without any measurement. `COLD` bounds the **actual** dwell by
measuring. **Set `T_dwell` = 1.5 s** (not the 1.0 s §3.5 suggests): the single-open-bleed case needs
**1.112 s** to reach 45 V at C_worst `[verified-run]`, and a monostable shorter than that would release
before the node is cold and leave `COLD` as the only barrier. Firmware's own dwell must be longer
still — **2.0 s**, matching the probe's mode-change budget of 3 × the worst bleed time.

### 7.8 The mode change

`NUMBERS_PROBE.md` §3.7's sequence stands, restated under G0-A5 as a **powered-down, cables-off human
procedure** (MODE-17) rather than a firmware transition:

1. command both setpoints to zero;
2. disable both modules (`+VIN` removal primary, `/ON` secondary);
3. **dwell, then VERIFY both outputs below 60 V on the independent monitors** — verify, do not merely
   wait. Budget **3 × 0.626 s = 1.877 s, round to 2.0 s**;
4. move the mode element **cold**;
5. read the mode element's physical position back before re-enabling anything.

**What this design contributes to that procedure:** `COLD_A ∧ COLD_B` is a hardware fact available on
the panel and on GPIO, so step 3's *verify* has a hardware answer and not only a firmware one; and
because both bleeds are permanent and sit at the connectors, step 4 is safe even if steps 1–3 are
skipped entirely — the node discharges through 17.9 MΩ regardless of what anyone commands. **MODE-16**
(a mode change seen at runtime forces HV off immediately) and **MODE-15** (aux poles break before the
HV poles make) are the backstops, and neither is in this document's lane.

---

## 8. The load budget, summed — the thing nobody had summed since G0

`CONTROL_ARCHITECTURE.md` §2.10's post-G0 note says it plainly: *"nobody has summed the total standing
and transient load per module since G0. Do it before G1. `COMBINER_STUDY.md` F-11 is the precedent for
what happens when a load budget is never actually summed."* Here it is
`[new-this-session, verified-run]`.

**Per module, dual-unipolar mode, module at full output, its relay in the NO position:**

| load | R | I at 1 kV | % of Inom |
|---|---:|---:|---:|
| **S1** output bleed | 20.0 MΩ | 50.0 µA | **10.00 %** |
| **S2** independent monitor | 200 MΩ | 5.0 µA | **1.00 %** |
| **S3** COLD permissive divider | 1.00 GΩ | 1.0 µA | **0.20 %** |
| **S5** branch monitor | 1.00 GΩ | 1.0 µA | **0.20 %** |
| **S4** module NC bleed | — | **0** (NC contact open when selected) | 0 |
| **TOTAL, external, per module** | 17.5 MΩ eff. | **57.0 µA** | **11.40 %** |
| **remaining for the load** | | **443.0 µA** | **88.60 %** |

- **The probe's §3.4 sum is 11.00 %** (bleed + monitor only). **My delta is +0.40 %**, and it is C-2's
  two strings, which have never been in a budget. Under the probe's own 15 % assertion `[verified-run]`
  either way — **the assertion does not fail, but it was passing on an incomplete sum.**
- **The budgets do not share and do not average.** In mode 2 each module carries its own full copy.
  Instrument-wide standing HV load is 114 µA; the number that binds is the per-module 57 µA.
- **Pseudo-bipolar mode is identical for the active module.** `OUT_B`'s three strings sit on a dead
  node and draw nothing; the deselected module is off, so S4 and S5 draw nothing.

**And the load that is not on the list, because nobody has measured it: the module's own internal
bleeder.** PART-24 assumes ~20 MΩ, which would be another **50 µA = 10.00 %**, taking the total to
**21.40 %** and leaving **393 µA = 78.6 %**. **MEASURABLE-NOW.**

| measurement comes back at | consequence | designed response |
|---|---|---|
| **no internal bleeder / ≥ 1 GΩ** | budget as tabulated, 11.40 % | none |
| **≈ 20 MΩ (the assumption)** | 21.40 %, still leaves 393 µA | **acceptable — no change.** Also *halves* the module-node discharge time, in the good direction |
| **≤ 5 MΩ** | > 40 % of Inom consumed internally | **raise S1 from 20 MΩ to 40 MΩ**, reclaiming 5.00 %; discharge to 60 V at C_worst becomes 1.01 s, still 5× inside target `[verified-run]`. If that is not enough, the deliverable-current specification changes and the human must be told — do not quietly reduce the bleed below 40 MΩ |

---

## 9. Layout, DRC and generator requirements

### 9.1 A clearance trap this repo has not yet hit

`INTERFACES.md` §2.2 puts every `HVDIV_*` net in netclass `HV_SENSE` at `<C_hv>` = **7.5 mm**
`[unverified-primary]`. A KiCad netclass `clearance` is a **per-net minimum against all other copper**.
Applied literally, **the two parallel sub-strings of one divider would be forced 7.5 mm apart, and each
element-to-element node 7.5 mm from its neighbour** — even though adjacent interior nodes of the S2
string differ by **100 V**, needing 0.600 mm bare `[unverified-primary]` or 1.0 mm with the project's
1.5× margin.

This is not just wasteful. **It attacks the monitor's dominant error term**: a string stretched to 10×
its necessary length presents 10× the surface area for the leakage of §4.5.

⇒ **Required, and it must be a generator invariant because DRC cannot express it.** A `.kicad_dru`
rule keyed on the `HVDIV_*` pattern is *unsafe* — `HVDIV_A_S2a_N1` (900 V) and `HVDIV_A_S2b_N9` (100 V)
both match the pattern and are 800 V apart. DRC has no "adjacent in the string" predicate. So:

> **SA-14 (proposed):** the generator places each HV divider sub-string collinearly and in electrical
> order, at a fixed inter-element pitch, and `check_netlist.py` asserts that **no two `HVDIV_*` nodes
> closer than `<C_hv>` differ by more than 150 V**, computing each node's potential from the string's
> position and `Vnom`. Failing that assertion fails the build.

This is the same class of defect as probe finding **F-3** (a per-pad clearance override silently
replacing the netclass value on pad 6). **Never infer "the rule applied" from "DRC passed" — measure
the copper.**

### 9.2 Area — and why ~37 cm² of HV area is a floor, not an estimate

String geometry `[verified-run, probe §3.5/§4.2]`:

| string | elements per sub-string | package | sub-string length |
|---|---:|---|---:|
| S2 monitor | 10 | 1206 | **44.65 mm** (10 × 3.925 mm land + 9 × 0.600 mm) |
| S1 / S3 / S4 / S5 | 2 | 2512 | **16.35 mm** (2 × 6.925 mm land + 1 × 2.500 mm) |

Count: **4 × 44.65 mm** (S2 monitor, 2 sub-strings × 2 outputs) + **16 × 16.35 mm** (S1/S3 × 2 outputs
and S4/S5 × 2 modules, 2 sub-strings each). With each corridor bounded by the 7.5 mm single-ended rule
`[unverified-primary]` on both sides plus a 1.0 mm guard conductor, the upper bound is **≈ 70 cm² of
additional HV area** — *on top of* the combiner's ~37 cm². Radial arrangement from a common HV node
shares corridors and will beat that substantially, but **the honest statement is that the divider and
bleed networks are comparable in area to the combiner itself.** This supports LIB-19 / R-12:
**re-run the area before placement; HV clearance cannot be recovered by rerouting.**

### 9.3 Placement rules that carry safety meaning

1. **S1, S2 and S3 connect at the output connector, downstream of the mode switch** — so they are
   present in every mode and every switch position (§7.2, MODE-18).
2. **S4 and S5 connect at the module HV pin, upstream of the changeover relay** — a bleed only
   downstream cannot discharge the node behind an open contact (probe §3.4).
3. **Two parallel sub-strings side by side, never end to end.** End-to-end is a series chain wearing a
   parallel label.
4. **The driven guard ring surrounds the S2 tap, `R_ser`, `C_aa` and the buffer's + input, and runs
   alongside the whole S2 string.** Its own net, `HVDIV_GUARD`, one per chain — never shared between
   chain A and chain B.
5. **Conformal coating over the divider region, after cleaning**, to a written process. This is also
   the backstop for an open guard-drive wire (§10, fault 9).
6. **All HV copper single-layer** (NUM-04) — a `clearance` constraint is per-layer 2-D and cannot
   express `HV_POS` on top vs `HV_NEG` on bottom across 1.6 mm of dielectric.
7. **`HV_OUT_A` ↔ `HV_OUT_B` ≥ 15.0 mm** `[unverified-primary]` — in mode 2 they are simultaneously
   live at opposite polarity, which is a **normal steady state**, not a fault (probe finding F-4). The
   two output nodes' string groups must respect that gap between groups.

---

## 10. Single-fault analysis

Every row assumes exactly one fault, everything else healthy. **"ESP32 in reset or unpowered while HV
rails are up" is the standing background condition for rows 1–14**, because the analogue chain,
comparators and latch are powered from board rails, not from the ESP32.

| # | fault | immediate effect | detected by | verdict |
|---:|---|---|---|---|
| 1 | **ESP32 in reset / unpowered, HV rails up** | heartbeat stops ⇒ `EN_HB` = 0 ⇒ `ARM` = 0 ⇒ `+VIN` removed from both modules; comparators, latch and both bleeds keep working with no MCU | — | **SAFE.** Outputs discharge through 17.9 MΩ; `COLD` still asserts correctly; no monitoring *reporting*, but no monitoring is needed to be safe |
| 2 | **+3V3 logic rail lost** | open-drain `/ON` drivers release; 10 kΩ pull-ups to `+VIN` pull `/ON` HIGH | — | **SAFE** — loss of the logic rail is a turn-off event by construction |
| 3 | **+5 V analogue rail lost** | buffers and comparators lose supply; push-pull `COLD` output collapses, pull-down holds `COLD` = 0 | ADC-B AIN3 (if the MCU lives) | **SAFE** — latch opaque, no changeover. Monitors blind; also kills the modules' `+VIN`, so HV goes away too |
| 4 | **One S1 bleed sub-string open** | discharge 0.56 s → **1.01 s** at C_worst | **nothing — silent** | **TOLERATED BY DESIGN.** This is exactly what NUM-09 buys. Still 5× inside target |
| 5 | **Both S1 sub-strings open** | discharge → **5.21 s** through S2 ‖ S3 | `COLD` refuses; discharge timeout ⇒ **TRIP** (ARCH-24) | **SAFE, degraded.** Refusal, not hot switch |
| 6 | **One S2 monitor sub-string open** | monitor reads **half** the true voltage | 20 V disagreement trip at any \|V\| > 40 V | **DETECTED** whenever it matters |
| 7 | **Whole S2 top leg open** | tap → 2.04914 V; monitor reads ≈ 0 at all voltages | (a) 20 V disagreement trip at \|V\| > 20 V; (b) **zero-point check: +1.678 mV = 27 LSB** even at commanded zero | **DETECTED, including at zero** — the case F-13 says is normally blind |
| 8 | **`MON_TAP_A` trace open** | buffer input floats through `R_ser`/`C_aa`, drifts to a rail | disagreement trip; zero-point check | **DETECTED** |
| 9 | **Guard-drive open** | leakage returns to corrupting the tap: 0.2 V coated, **20 V on bare FR-4** | 20 V trip — **exactly at the threshold, not reliably** | ⚠ **NOT RELIABLY DETECTED.** Mitigation is the *conformal coating*, which keeps the unguarded error at 0.2 V. **This is why the coating is a requirement and not a finish option** |
| 10 | **S3 COLD sub-string open** | S3 comparator says COLD when hot | **the 2-of-2 AND with the S2 comparator (§5.4)** | **STUCK-SAFE** — no changeover ever; loudly visible on the first polarity change |
| 11 | **S3 comparator supply lost / output open** | push-pull output collapses, pull-down holds `COLD` = 0 | first attempted changeover | **STUCK-SAFE** |
| 12 | **S3 comparator stuck at 1** | latch always transparent ⇒ hot switching becomes possible on a firmware bug | the S2 comparator in the AND still vetoes | **STUCK-SAFE** — this was `topology/hv-relay-changeover.md` fault 20's *"degrades to a firmware convention"*; **the AND retires it** |
| 13 | **REF5025 (`VREF`) dies** | S2 tap and both `MON_REF` collapse; S3 node offset collapses | S3 node ≈ 0 vs a 2.048 V REF3020 window ⇒ **`COLD` FALSE**; ADC-B AIN2 sees it | **STUCK-SAFE** (§5.5) |
| 14 | **REF3020 (window centre) dies** | window centre → 0 V; S3 node sits at 2.046 V | `\|2.046 − 0\| > 46 mV` | **STUCK-SAFE** (§5.5) |
| 15 | **ADS1115 ADC-A dies / I²C hangs** | both independent monitors blind | firmware I²C timeout; `VMON`s on ADC-B still live | **SAFE, degraded.** No hardware permissive is lost. Firmware must treat "monitor unreadable" as a **hard fault**, not as "0 V" |
| 16 | **ADC-A mux stuck** | one monitor's reading substituted for the other | (a) `AIN1-AIN3` reference-difference check (§3.4); (b) cross-part `VMON` comparison; (c) mode-2 sign check | **DETECTED** |
| 17 | **ADC full-scale code returned** | reading pinned at ±2500.7 V | — | **Firmware must treat a full-scale code as OVER-RANGE and trip, never as 2500 V.** A required firmware rule, listed in §12 |
| 18 | **Broken wire: `COLD_A` to latch `LE`** | `LE` floats | pull-down ⇒ `LE` = 0 ⇒ latch opaque | **STUCK-SAFE** |
| 19 | **Broken wire: `BRANCH_LIVE_P`** | pull-down ⇒ reads "not live" | the weld self-test then reports **no stimulus** and must **fail**, not pass | **SAFE if and only if the self-test treats "branch not live" as a FAIL.** Listed in §12 |
| 20 | **Broken wire: S4 NC-bleed leg** | parked module retains charge behind an open contact | `BRANCH_LIVE_x` stays asserted after disable | **DETECTED** — and this is why S5 exists |
| 21 | **`C_load` 10× over the NUM-13 limit** | discharge to 45 V ≈ 6 s | `COLD` refuses ⇒ discharge timeout ⇒ **TRIP** | **SAFE.** The refusal is the enforcement of an interface limit that is otherwise only declared |
| 22 | **Flashover from the HV node to the S2 tap** | kilovolts at the buffer input, limited by `R_ser` to **1.00 mA** | disagreement trip | **SAFE for the op-amp** (±10 mA abs max `[recalled]`); the board damage is a separate matter |
| 23 | **Mode switch between detents** | HV poles open, aux poles decode "no valid mode" | MODE-18 hardware decode ⇒ both modules off | **SAFE, and both outputs remain bled because S1 is permanent and at the connector** |
| 24 | **Both monitor chains read plausible but wrong (common-mode)** | e.g. a shared `VREF` drift | cross-part `VMON` comparison — **the reason for §3.3's allocation** | **DETECTED** |

---

## 11. Where I disagree with documents already in this repo

Stated loudly, per the standing instruction. **None of these is applied silently and none of them is a
rounding error.**

### 11.1 ⛔ **`NUMBERS_PROBE.md` §4.2 leaves the monitor with ZERO overrange headroom, and that defeats one of its own jobs**

The probe sets `A = ADC_FS / (2·Vnom) = 1.024 × 10⁻³`, which puts **+Vnom exactly at +full scale**. At
+1001 V the ADC clips. Meanwhile:

- `NUMBERS_PROBE.md` §5, verbatim from iseg Table 1: *"Attention! Output voltage is internally not
  limited!"*
- `DECISIONS.md` **PART-33**: a single `VSET` fault reaches **132 % of Vnom = ≈1320 V**.
- Probe finding **F-9**: a clamp-reference fault reaches **201 % = 2012 V**.
- `CONTROL_ARCHITECTURE.md` §2.2, which the probe supersedes, explicitly specified **2.04× headroom**
  and said why: *"the 2× headroom is not slack — it is what lets the monitor **see** the overvoltage
  condition instead of railing and reporting a plausible full-scale number."*

**At the probe's ratio, a 1320 V fault reads as exactly 1000 V.** The instrument would report nominal
while producing 132 % of nominal, on the one measurement that exists to be independent.

**Resolution adopted here:** `Rt` is unchanged at 200 MΩ (loading is still the binding constraint) and
only the *bottom network* changes — `Ro` = 200 kΩ, `Rb` = 909 kΩ — giving **α = 8.190 × 10⁻⁴, ±FS =
±2500.7 V, 1.89× margin on the 1320 V fault and 1.24× on the 2012 V fault**, at a cost of 0.0611 →
0.0763 V per LSB, which is irrelevant against a 0.26–1.59 V accuracy. **This costs nothing and the
probe should be re-pinned to it.**

### 11.2 ⚠ **`NUMBERS_PROBE.md` §4 does not apply NUM-09/SA-9 to the monitor top leg, and `INTERFACES.md` SA-9 says it must**

Probe §4.2 specifies the monitor top leg as **one string of 10 × 20 MΩ**. Probe §3.5 applies the
parallel rule to the bleed explicitly (*"×2 for the parallel-string rule → two strings side by side"*).
**SA-9 applies it to "every bleed and every HV divider top leg."** The two documents disagree.

**I comply with SA-9** — the design above is 2 ∥ 10 × 40 MΩ — **and I argue the rule is wrong here:**

| string | an open element makes it read | direction | is parallel the right fix? |
|---|---|---|---|
| **S1 / S4 bleed** | nothing measurable | **silently undetectable** | **Yes** — tolerate, since you cannot detect |
| **S3 COLD / S5 branch** | 0 V (single) or half (parallel) | **unsafe** | **Partly** — parallel bounds the harm; the real fix is §5.4's AND |
| **S2 monitor** | 0 V (single) or half (parallel) | **detected either way** by the 20 V trip and the zero-point check | **No** — parallel buys nothing |

For S2 the parallel rule doubles the element count (20 instead of 10), doubles the joints, and — the
part that matters — **doubles the surface area exposed to the leakage that is already the dominant
error term (§4.5)**. **Proposed G1 amendment: SA-9 applies to bleed and permissive strings; the
invariant-(c) monitor top leg is exempted, on the recorded grounds that its open failure is loudly
detected.** NUM-09 is frozen, so **this document builds the compliant version** and flags the
amendment. **Not resolved here.**

### 11.3 ⚠ **`CONTROL_ARCHITECTURE.md` §2.3's recommended divider part fails the probe's own pad-gap screen**

§2.3 recommends *"Top leg: 2 × Vishay CRHV1206, 100 MΩ"* — 500 V per **1206** element. Probe §3.5
rejects "1206 HV series" at **333 V** per element because the 1206 pad gap is 1.925 mm against the
2.500 mm `[unverified-primary]` that voltage demands. **At 500 V the same screen rejects it harder.**
The recommendation predates the screen; the screen wins. Use **N = 10 at 100 V per 1206 element**
(this design), or 2512 packages if a low element count is ever wanted.

### 11.4 ⚠ **The "31× better than `VMON`" figure rests on an unsupported TCR assumption**

`numbers_probe.py` line 1453: `TCR_MATCH_PPM_K = 10.0  # [ASSUMED] top-leg to bottom-leg tracking`
`[verified-artifact]`. No part in this project is documented at 10 ppm/K tracking. The only HV divider
part actually named — CRHV at ±100 ppm/K against a 25 ppm/K bottom leg — gives **75 ppm/K** and an RSS
of **1.51 V**, i.e. **6.6×**, not 31×. Both meet the requirement. **Quote 6.6× until a part with a
specified tracking figure is on the BOM.** §4.4 gives the table so nobody has to re-derive it.

### 11.5 ⚠ **Minor arithmetic slip in `NUMBERS_PROBE.md` §3.5's bleed element**

The probe computes `N = 2, 500 V per element, **25.00 mW per element**` for a *single* 20 MΩ string,
then appends *"×2 for the parallel-string rule"* without carrying the ×2 into the element value. The
as-built form is **two parallel strings of 2 × 20 MΩ**, so the per-element dissipation is **12.5 mW**,
not 25.0 mW. **No safety consequence — the corrected figure is less stressed, not more** — but the
per-element *resistance* also changes from 10 MΩ to 20 MΩ, which is a BOM value, so it matters.

### 11.6 ⚠ **`CONTROL_ARCHITECTURE.md` §2.10's switched bleed is superseded, and the record should say so**

§2.10 concludes *"the dedicated bleed must be SWITCHED, never permanent"* at 2.2–3.3 MΩ, on a 100 nF
worst-case capacitance and a "1 kV → 10 V in ≤ 1 s" requirement. The probe re-derived it against
NUM-13's imposed ≤ 10 nF and a 60 V / 5 s target and landed on a **permanent 20 MΩ**. **The probe is
right and §2.10 should be marked superseded**, for a reason §2.10 itself half-anticipated: *a switched
bleed can fail open, and a bleed that only runs on command is not a bleed.* §2.10's elegant result —
*"the bleed and the break-before-make interlock are the same physical mechanism"* — **survives, but
only for S4, the module-side NC bleed.** It does not generalise to the output nodes (MODE-10), which
is why S1 is permanent.

### 11.7 ⚠ **`topology/hv-relay-changeover.md`'s 5 × 200 MΩ = 1 GΩ monitor string is worse than the probe's 200 MΩ, and the reason is counter-intuitive**

Higher top-leg resistance looks like better engineering (0.2 % of Inom instead of 1.00 %). It is not:
leakage error goes as `Rt / R_leak`, so a 1 GΩ monitor on bench-clean bare FR-4 carries **100 V** of
error instead of 20 V `[verified-run]`. **The probe's 200 MΩ is correct and the topology document's
1 GΩ must not be revived.** *(The same arithmetic is exactly why 1 GΩ **is** right for S3 — a 20 : 1
comparator does not care about a 10 % ratio error, and a 0.03 % monitor does. Same number, opposite
verdict, because the requirement is different.)*

---

## 12. What must be added to the executable checks, and what is still open

### 12.1 Assertions to fold into `hardware/hvctl/numbers_probe.py`

Per `CLAUDE.md`: every number in a design document should be re-derivable by a zero-arg, deterministic
tool with an acceptance check. **These are specified, not implemented — implementing them is the next
tool-lane task, and this document does not claim it is done.**

1. The monitor ratio gives **≥ 1.5× overrange margin against 132 %·Vnom** (§11.1). *This assertion
   would have failed on the current probe — it is the mutation test the probe is missing.*
2. **Summed** standing load per module over **all** strings (S1+S2+S3+S5) < 15 % of Inom, with the
   string list enumerated so adding a string without budgeting it fails the build (§8).
3. Discharge to 60 V through **the parallel combination of all strings on the node**, in all four
   capacitance scenarios, **and with one bleed sub-string open** (§7.3).
4. Every string's per-element voltage is inside its derated rating **and** its package pad gap clears
   the IPC-2221 B2 requirement at that voltage — already present for S2 and the bleed, **absent for S3
   and S5** (§4.3).
5. `COLD` threshold + its full error budget stays **below the 60 V touch-safe limit** (§5.2).
6. The monitor RSS beats `VMON` **at 75 ppm/K TCR tracking**, not only at the assumed 10 (§4.4).
7. **SA-14** (§9.1): no two `HVDIV_*` nodes closer than `<C_hv>` differ by more than 150 V.

### 12.2 Firmware rules this design imposes

| | rule | source |
|---|---|---|
| FW-1 | A **full-scale ADC code is OVER-RANGE and must trip** — never reported as ±2500 V | §10 row 17 |
| FW-2 | **"Monitor unreadable" is a hard fault**, never "0 V" | §10 row 15 |
| FW-3 | **Zero-point plausibility check** on both monitor chains before arming | §4.8 |
| FW-4 | **Mode-2 sign check**: `OUT_A` positive, `OUT_B` negative | §4.8, probe §4.5 |
| FW-5 | **Mux-integrity check** via `AIN1-AIN3` against its calibrated constant | §3.4 |
| FW-6 | Weld self-test **fails** if `BRANCH_LIVE_x` does not assert — "no stimulus" is a FAIL, not a PASS | §10 row 19, F-2 |
| FW-7 | **Per-output** two-point calibration (F-20 becomes per-output under G0-A4), and **scheduled recalibration** for CRHV 0.5 % life drift | §4.4 |
| FW-8 | Firmware dwell **2.0 s** > hardware monostable **1.5 s** > worst measured bleed **1.11 s** | §7.7 |

### 12.3 Open questions carried forward — **not closed here**

| id | question | why it is still open |
|---|---|---|
| **O-M1** | **Module output capacitance** | `[ASSUMED]` 100 pF. Sets every τ in §7. **MEASURABLE-NOW.** If > 50 nF, F-7's stored-energy classification changes and the enclosure requirements escalate |
| **O-M2** | **Module internal bleeder** | `[ASSUMED]` ~20 MΩ. Worth 0–10 % of the load budget (§8). **MEASURABLE-NOW** |
| **O-M3** | **`VSET` step response** | `[ASSUMED]` 100 ms pole. Sets §7.7 step 6 and the anti-alias pole choice. **MEASURABLE-NOW** |
| **O-M4** | **Turn-on time from `+VIN`** | `[ASSUMED]` 150 ms. Sets §7.7 step 5. If it comes back at seconds, the dead-band exceeds what G0-A1 accepted and **there is no design fix** — it is the module's own physics. Report it; do not paper over it. **MEASURABLE-NOW** |
| **O-M5** | **Divider `k_VCR`** | F-22 is un-retired. `[ASSUMED]` 1 ppm/V; at 25 ppm/V and N = 10 the VCR term alone is 2.5 V (§4.3). **Must become a specified purchase parameter** |
| **O-M6** | **Guard-ring improvement factor** | `[ASSUMED]` 100×, never measured, and the accuracy claim on bare FR-4 rests entirely on it |
| **O-M7** | **SA-8 wording vs the 2-of-2 AND** | §5.4. A G1 decision |
| **O-M8** | **SA-9 exemption for the monitor top leg** | §11.2. A G1 decision; NUM-09 is frozen |
| **O-M9** | **Every clearance number here is `[unverified-primary]`** | STATUS.md §1.2. A human must read a primary copy of IPC-2221B Table 6-1 before G1. This affects the pad-gap screen that rejected the 1206-at-333 V part and the 15.0 mm `HV_OUT_A`↔`HV_OUT_B` rule |
| **O-M10** | **Every MPN here is `[unverified-MPN]`** | Not one has been checked against a live distributor page. HV resistors at 40 MΩ / 1 GΩ in specified TCR and VCR grades are the risky lines (R-7's neighbourhood) |

---

## 13. Reproducing the numbers

```powershell
# the frozen numbers, re-run this session: 74 assertions, 74 pass, exit 0   [verified-run]
& "C:/Program Files/KiCad/10.0/bin/python.exe" `
  "C:/Users/darro/OneDrive - Yale University/Desktop/iseg-programmable-supply/hardware/hvctl/numbers_probe.py"
```

The arithmetic introduced by this document (the three-string parallel discharge, the summed load
budget, the differential network E96 values, the α = 8.19 × 10⁻⁴ overrange case, the TCR sensitivity
table, the buffer and ADC-loading terms, the multiplexing skew) was run this session as two throwaway
stdlib scripts and is **not yet in the probe** — see §12.1. **Every such number in this document is
marked `[new-this-session]` or appears in a table whose caption says `[verified-run]` against those
scripts. Treat them as computed-and-checked-once, not as probe-grade, until §12.1 is implemented.**

**What none of this can see** — stated because "exit code 0" is not "verified":

- **Nothing has been measured on hardware.** Every number is arithmetic over vendor documentation.
- **No physical module has been touched.** Four of the inputs are `[ASSUMED]` and all four are now
  measurable.
- **The real surface resistivity of the finished board** — the term that dominates §4.5 — is unknown,
  and the 100× guard improvement is assumed.
- **Resistor VCR and TCR are datasheet parameters this design *specifies*, not measures**, and no MPN
  has been confirmed to meet them.
- **ADC noise in the presence of the module's switching converter** has not been modelled at all.
- **The calibration this accuracy budget assumes has not been performed** and no calibration procedure
  has been written.
- **The clearance constants remain `[unverified-primary]`** and the pad-gap screen that rejects parts
  is built on them.
