# SETPOINT_PATH — the `VSET` path, its hardware clamp, and the 3.3 V hazard

**Status: detailed design, post-G0. This document specifies a PRIMARY SAFETY ELEMENT
(`DECISIONS.md` PART-33, ARCH-06; `SCOPE.md` S-8). It is written to be drawable without
inventing anything.**

Every computed number in this file is the printed output of
`docs/studies/setpoint_path_numbers.py` — zero-argument, stdlib-only, deterministic.
**52 assertions, 52 pass, exit 0, byte-identical across two invocations, 14 of 14 injected
mutations caught** `[verified-run]`. Reproduce with:

```
"C:/Program Files/KiCad/10.0/bin/python.exe" "docs/studies/setpoint_path_numbers.py"
```

*What that instrument cannot see:* it is arithmetic over datasheet values and stated
assumptions. It verifies no circuit. **Exit 0 means the algebra is self-consistent, not
that the design is safe.** Nothing here has been simulated, built or measured. Import set
confirmed `{math, sys}` by AST walk `[verified-run]`.

**Evidence tags** per `CLAUDE.md` rule 4: `[verified-run]` · `[verified-artifact]` ·
`[web-verified]` (session 1, manufacturer page) · `[recalled]` · `[unverified-MPN]` ·
`[unverified-primary]` · `[MEASURABLE-NOW]` (the modules are in hand — G0-A2).

---

> # ⛔ CORRECTION BANNER — added 2026-07-23 (session 2 verification). READ FIRST.
>
> The claim *"the `VSET` clamp makes commanding over-range impossible in hardware, and its own
> failure modes are safe"* was put to **three independent skeptics tasked with refuting it. All three
> refuted it, at high confidence.** **This is a STOP-THE-LINE finding for a 1 kV instrument**: the
> clamp is `DECISIONS.md` PART-33 / ARCH-06 / `SCOPE.md` S-8, i.e. a **primary safety element**, and
> a primary safety element described in language stronger than it earns is worse than one described
> honestly. The text below is left in place; these corrections govern.
>
> **S-1 — "impossible" is refuted BY THIS REPO'S OWN PROBE.** `hardware/hvctl/numbers_probe.py` §5.3
> prints *"NO candidate makes over-voltage mathematically impossible"*, §5.4 asserts
> *"[PASS] no VSET clamp survives every single fault"*, and §5.6 concludes *"the VSET clamp is a
> necessary but NOT SUFFICIENT safety element … still passes 2 of 7 modelled single faults."*
> **The correct statement is: the clamp bounds COMMANDED over-range from 1320 V to ≈1000 V. It does
> not make over-range impossible, and it is not the safety case on its own.**
>
> **S-2 — the headline "+0.061 % (1000.6 V)" of §2.4 and §14 divides by a NOMINAL Vref.**
> The arithmetic `2.500 × (1 + 5e-4 + 6e-5 + 5e-5) = 2.501525 V` is correct, but §2.4 then divides by
> **Vref = 2.500 exactly**. The datasheet (extracted from `references/iseg_manual_APS_en.pdf` p.7 by
> three skeptics) says **"Reference voltage Vref (internal) 2.5 V ±1 %"**. At the low end
> **Vref = 2.475 V** the *same* hardware ceiling commands `1000 × 2.501525/2.475 =` **1010.7 V =
> +1.07 %, ~17× the quoted figure.** `numbers_probe.py` §5.3 independently rates the adopted clamp's
> no-fault ceiling at **100.30 % of Vnom**, not 100.061 %. §10 already uses 2.475 V — **the file is
> internally inconsistent**, and §2.4/§14 must be restated as **"+1.07 % worst-case Vref"**.
> Consequence: **hardware alone does not bound the output to ≤ Vnom.** ≤ Vnom comes only from the
> **98 % firmware code clamp of §10** — and G0-A3 put firmware and the network inside the untrusted
> boundary, which is the exact thing the hardware clamp existed to remove.
> Note also that 2.5015 V exceeds the datasheet's own *"Do not use Vset > 2.5 V!"*.
>
> **S-3 — a SINGLE fault does put 3.3 V on `VSET`.** This file's own §5.1 F7 (`VSET` shorted to
> +3V3, 0 Ω solder bridge ⇒ **1320 V**, *"not preventable by the set path"*) and `numbers_probe.py`
> §5.4 row F2 (**133 % for every candidate**, *"downstream of every clamp"*) both say so. It is
> mitigated by a **layout keep-out (SP-13)** and **detected** by `U7`, not prevented.
>
> **S-4 — one modelled failure mode of the clamp is WORSE than no clamp.** `numbers_probe.py` §5.4
> row F5, reference shorted to 5 V: **201 % of Vnom = 2012 V** for the adopted candidate — worse than
> the un-clamped 3.3 V case (1320 V). Its only cover is `U5`, whose stuck-HIGH failure this file
> calls **undetectable in service** (O-I). **"Its own failure modes are safe" is false as stated.**
>
> **S-5 — there is one un-mitigated open.** §5.1 F2: a break between the pull-down and pin 2 leaves
> the module's internal 10 kΩ unopposed ⇒ **1000 V**, *"the one un-mitigated open"*, prevented by
> nothing and mitigated only by layout (O-J).
>
> **S-6 — power-on / supply-ramp behaviour is NOT verified.** `numbers_probe.py` prints a
> `[BLIND SPOT]`: nothing in either instrument covers a transient overshoot of an RRIO output stage
> above its settled rail during supply ramp, nor reference start-up overshoot. The DAC8552
> power-on-reset-to-zero state is `[recalled]` (O-B), never read from a datasheet.
>
> **S-7 — the clamp part has no part number.** `U4` is `**UNSELECTED RRIO dual**` in `board_spec.py`
> (O-D: *"output current at a 2.5 V supply disqualifies most precision amps"*). The primary safety
> element is unselected, and three of its inputs — module `R_pullup` tolerance (O-A; the criterion
> **breaks at 7.83 kΩ**), the 60 V touch criterion (O-L, `[unverified-primary]`), the DAC POR state
> (O-B) — are unverified. **The 47.6 V fail-open figure inherits O-A and is MEASURABLE-NOW.**
>
> **WHAT SURVIVED, and keeps its standing:** the Vref-pin attack **fails** — Table 4 lists exactly
> seven pins and no Vref pin, and §2.3 already dropped candidate D rather than inventing one; the
> **duplicated 500 Ω pull-down** genuinely holds a clamp-open failure at **47.6 V**; and commanded
> (firmware/network) over-range **is** structurally bounded by `U4`'s own rail.
>
> **RESTATE THE CLAIM AS:** *the `VSET` clamp bounds commanded over-range to ≈+1 % of Vnom worst-case
> Vref, converts the 3.3 V hazard from 1320 V to ≈1000 V, and fails open to 47.6 V. It is a
> NECESSARY BUT NOT SUFFICIENT safety element: 2 of 7 modelled single faults pass it, one of them
> reaching 201 % of Vnom. The hardware OVP (layer 3) and the layout keep-out are load-bearing, not
> defence in depth.*
>
> **Also unresolved:** `CONTROLLER_AND_POWER.md` §5.3 and fault row F-21 still specify a **shunt
> LM4040-2.5 clamp rail** that `board_spec.py` does not build. One of the two must change at G1.

---

## 0. The problem in one page

Three module facts compose into a single hazard. All three are `frozen`.

| # | Fact | Source |
|---|---|---|
| 1 | `Vout = Vnom · Vset / Vref`, and **the output is internally NOT limited above Vref**, with *no stated ceiling* | Table 1, both revisions `[skeptic×3]`, PART-05 |
| 2 | `VSET` carries an internal **10 kΩ pull-up to Vref** ⇒ an **open `VSET` commands FULL SCALE** | Figure 2 + the `Rset` formula `[skeptic×3]`, PART-04 |
| 3 | `/ON` is **active-LOW and floats to ON** | Table 4 `[verified-run]`, PART-02 |

With `Vref = 2.5 V` (G0-A2) against a 3.3 V MCU:

```
source presented at VSET        V        Vout        % of Vnom
commanded zero              0.0000         0.0            0.0 %
module Vref (= full scale)  2.5000      1000.0          100.0 %
OPEN VSET  (the 10k wins)   2.5000      1000.0          100.0 %
ESP32 / 3.3 V rail          3.3000      1320.0          132.0 %
+5 V analog rail            5.0000      2000.0          200.0 %
```
`[verified-run]`

**The module's un-driven default state is ENERGISED AT OVER-RANGE.** G0-A3 puts the
set-point on a network-writable path, so firmware is no longer in the trust chain: the
hardware clamp carries the case.

### 0.1 The design rule that follows, and it decides everything below

> **The dominant hazard is the clamp failing OPEN, because the internal 10 kΩ then commands
> full scale. Therefore no element whose open-circuit failure removes the clamp may be the
> clamp.**

That single sentence kills the series-divider and the series-Schottky architectures and
selects a **rail-defined clamp plus a shunt pull-down**, both of which fail in the safe
direction. It is applied explicitly in §2 and §3.

---

## 1. Architecture — the recommendation, in one diagram

```
 +5V ────────────────────────────┬──────────────────────────────────────────────┐
                                 │                                              │
                    ┌────────────┴────────────┐                     ┌───────────┴──────────┐
   REF5025          │  U3  RAIL FORCE AMP     │                     │ U5  WINDOW COMPARATOR│
   2.500 V ±0.05 %  │  unity gain, V+ = +5 V  │                     │ dual comparator +    │
   3 ppm/°C  ───────┤ +                    OUT├──┬── VCLAMP 2.500 V  │ LM4040-2.048         │
        │           │ −◄───── Kelvin ─────────┼──┤   (STAR POINT)    │ (a DIFFERENT device  │
        │           └─────────────────────────┘  │                   │  from REF5025)       │
       GND                                       │                   │                      │
                                                 │  sense ───────────┤ 20.0k/20.0k, 0.1 %   │
                        ┌────────────────────────┤                   │ thresholds 2.430 V / │
                        │                        │                   │            2.551 V   │
   +3V3                 │                        │                   └───────┬──────────────┘
     │   ┌──────────┐   │                        │                           │ HIGH = in window
  ESP32──┤74AHCT125 ├──►│ DAC8552 (dual 16-bit)  │                           ▼
   SPI   │ 3V3→5V   │   │  VDD = +5 V            │                    ARM permissive chain
         └──────────┘   │  VREF ─────────────────┘                    (CONTROL_ARCH §3.3a)
                        │  OUTA ──1k──►  U4A +  ─────────────────────────────┐
                        │  OUTB ──1k──►  U4B +  ────────────────┐            │
                        └───────────────────────┘               │            │
                                                                │            │
      ╔═════════════════ V+ of U4A/U4B  IS  VCLAMP  (2.500 V) ═══╪════════════╪═══════════╗
      ║  THIS IS THE CLAMP.  A rail-to-rail output stage cannot  │            │           ║
      ║  exceed its own rail. Nothing in the set path downstream │            │           ║
      ║  of U4 touches +3V3 or +5V.                              │            │           ║
      ╚══════════════════════════════════════════════════════════╪════════════╪═══════════╝
                                                                 │            │
   U4A  ──force, ≤0.2 Ω, wide ──┬──────────────────────────────────────► VSET_P (module pin 2)
    │ −◄──── sense ─────────────┤                                             │
    └──── R_local 10 kΩ ────────┘                                             │
                                          ┌───────────┬──────────┬────────────┤
                                          │           │          │            │
                                     2 × 1.00 kΩ    BAT54      100 nF      2N7002
                                     (= 500 Ω)    (cathode      C0G       gate ◄─ /ON_P
                                     to GND        to VSET,               (at the MODULE end
                                     ARCH-18       anode GND)              of the /ON net)
                                          │           │          │            │
                                         GND         GND        GND          GND
      (U4B / VSET_N identical — one dual op-amp, one shared VCLAMP star)
```

**Five elements, five distinct jobs:**

| Element | Job | Fails how |
|---|---|---|
| `VCLAMP` = 2.500 V rail, and it is **U4's V+** | makes `Vset > Vref` **structurally impossible** | rail *rises* → caught by U5; rail *collapses* → pull-down wins |
| **U5 window comparator** | catches the one fault the rail clamp cannot: **the rail itself rising** | fails → falls back on the rail clamp + OVP |
| **2 × 1.00 kΩ pull-down at the pin** | turns *clamp fails open* from 1000 V into 47.6 V | one element open → 90.9 V (a second fault) |
| **2N7002 shunt** | *disabled module ⇒ `VSET` grounded*, in hardware | fails short → that channel dead (safe); fails open → pull-down still holds |
| **BAT54 to GND** | clamps negative excursions; **fails safe in both directions** | short → `VSET` = 0 (safe); open → protection lost only |

---

## 2. The clamp: four candidates evaluated, one recommended

`[verified-run]` — the clamp must sink the internal pull-up's **250 µA** at full scale.

| # | Candidate | Max `Vset` | `Vout` | Over-range | Verdict |
|---|---|---:|---:|---:|---|
| **A** | **RRO output stage whose V+ IS the 2.500 V reference** | 2.5015 | 1000.6 | **+0.061 %** | ✅ **ADOPTED** |
| B | precision divider, 3.3 V → 2.45 V | 2.5040 | 1001.6 | +0.160 % | ❌ rejected |
| B′ | *same, **bottom resistor open** (single fault)* | 3.3660 | 1346.4 | **+34.6 %** | — |
| C | Schottky from `VSET` to a 2.500 V rail | 2.7815 | 1112.6 | **+11.3 %** | ❌ rejected as primary |
| C′ | *same, **diode fails short** (single fault)* | 2.5015 | 1000.6 | +0.061 % | — uncommanded **full scale** |
| **D** | **DAC referenced to the module's own Vref pin** | 2.5000 | 1000.0 | **+0.000 %** | ⛔ **NOT IMPLEMENTABLE** |
| — | no clamp, 3.3 V-referenced source | 3.3000 | 1320.0 | +32.0 % | the hazard |

### 2.1 Why B (precision divider) is rejected — three independent reasons

1. **Its single-fault behaviour is worse than no clamp's ordinary behaviour.** A bottom-leg
   open puts the full 3.3 V rail on `VSET`: **1346 V**, +34.6 %. That is a *series* element
   whose open-circuit failure is unsafe — exactly what §0.1 forbids.
2. **Its full scale is the 3.3 V rail**, so the rail's ±2 % tolerance lands directly as a
   **±20 V gain error at the output** `[verified-run]`, and that rail moves with WiFi TX
   bursts (NUM-11: the TX burst is the largest current in the design).
3. **ARCH-04's series-resistance cap makes it un-buildable at the pin.** A divider whose
   Thévenin resistance is small enough not to divide against the internal 10 kΩ draws tens
   of milliamps continuously. Placing it *before* a buffer works — but then the buffer's
   rail is the clamp anyway, i.e. it collapses into candidate A with two extra tolerances.

### 2.2 Why C (Schottky to a precision reference) is rejected as the primary clamp

- It clamps at `V_rail + Vf`. At 250 µA the Schottky forward drop runs ≈0.21 V (40 °C) to
  ≈0.28 V (0 °C) `[recalled]`, i.e. the clamp point is **2.78 V worst case = 1112.6 V,
  +11.3 %**, and it **drifts 28 V over the operating range** `[verified-run]`. An 11 %
  clamp on insulation sized for 100 % is not a clamp worth having as the primary.
- **Its short-circuit failure commands full scale.** A shorted diode ties `VSET` to the
  2.500 V rail permanently: the module produces `Vnom` whenever it is enabled, with no
  command and no warning. Note this is *bounded* (it is exactly Vnom, not over-range) — the
  hazard is uncommanded output, not over-voltage. Stated precisely rather than dramatised.
- Against a solder-bridge short from `VSET` to +3V3 it does nothing: a 0 Ω bridge wins.

> **A Schottky IS adopted, but pointing the other way and for a different job.** See §3.4:
> `BAT54` **cathode to `VSET`, anode to GND**, clamping *negative* excursions. That
> orientation fails safe in **both** directions (short ⇒ `VSET` = 0; open ⇒ only the
> protection is lost), which is the exact inverse of the positive-going version.
> **Do not fit a positive-going Schottky to any rail.**

### 2.3 Candidate D — the elegant idea, and why it is dropped rather than invented

> **The APS Vref is NOT accessible. There is no Vref pin.**

Table 4 lists **seven** pins and no more: `1 +VIN · 2 VSET · 3 GND · 4 /ON · 5 VMON ·
6 HV · 7 GND` `[skeptic×3, verified-artifact]`. Figure 2 draws `REF` as an internal source
whose terminals are the internal 10 kΩ and internal GND; **it does not touch the module
boundary.** No customisation digit in Table 3 is documented to add one.

**Dropped. Not worked around with an assumed pin.**

What it would have bought is worth recording, because it is the largest single accuracy
term in the whole design: if `Vset = k · Vref`, then `Vout = Vnom · k` **exactly, independent
of Vref**, and the module's ±1 % Vref tolerance (**±10 V**) vanishes from the transfer.

**Partial recovery, and it is cheap.** Vref *is* observable — at the **open-circuit `VSET`
pin**, because the internal 10 kΩ pulls the pin there with no load. That is a bench
measurement, not a circuit:

- With a 10 MΩ DMM the loading error is `10k/(10k+10M)` = **0.100 %**, i.e. Vref is known to
  **2.50 mV** `[verified-run]`.
- Folded into a **per-module** gain constant this removes the ±1 % **initial** term. What
  remains is drift, bounded only by the datasheet's overall `< 50 ppm/K`: over a 20 K
  excursion **0.10 % = 1.0 V** `[verified-run]`.
- **A 10× accuracy improvement, obtained with a DMM and a text file.**

**Why it cannot be done in service.** Measuring the open-circuit pin requires the pull-down
and the shunt FET to be absent — i.e. a switch in a safety element, which is forbidden.
Measuring *through* the fitted 500 Ω pull-down instead multiplies the reading by 21×, so a
1 mV ADC error becomes 21 mV of Vref error = 0.85 %, worse than the ±1 % it was meant to
fix. **Rejected as an in-service feature; adopted as a one-time per-module bench
calibration** (§8.1).

⚠ **Maintenance consequence:** the calibration constant is keyed to a **module serial
number**. Replacing a module without recalibrating reintroduces up to ±1 % (±10 V).
This must appear on the panel/label and in the service note.

### 2.4 The recommendation

> **The 2.500 V rail that powers the `VSET` buffers' output stages IS the clamp.
> A rail-to-rail output stage cannot exceed its own positive rail; that is the entire
> mechanism, and it has no component in the signal path (so ARCH-04 is not violated).**
>
> Residual over-range: **+0.061 %** (`1000.6 V`), from
> `2.500 × (1 + 0.0005 initial + 0.000060 tempco over 20 K + 0.000050 long-term)`
> `[verified-run]`. Derived two independent ways (linear sum and multiplicative stack)
> and asserted to agree to better than 0.001 %.

This confirms and sharpens ARCH-06. **Two amendments to what ARCH-06 said, both stated
openly rather than slipped in:**

1. ARCH-06 quoted "+0.30 % with a 0.1 % reference". With the REF5025's actual ±0.05 % plus
   tempco and long-term drift the figure is **+0.061 %**. ARCH-06's conclusion is unchanged
   and its number was conservative.
2. **ARCH-06 as written does not cover the fault where the reference rail itself rises.**
   `PART_iseg_APS.md` §8.2 warned about exactly this ("the clamp rail must not be the same
   node the DAC uses as its reference — a shared reference failure would raise the clamp and
   the command together") and ARCH-06 deliberately makes them the same node. **Both are
   right; the repo contains a genuine unresolved tension and this document resolves it**
   — see §4.

---

## 3. Circuit, component by component

### 3.1 Reference and clamp rail

| Ref | Part | Value / setting | Notes |
|---|---|---|---|
| `U2` | **REF5025** (SOIC-8) | 2.500 V, ±0.05 % initial, 3 ppm/°C max, ±10 mA | `[web-verified, ti.com, session 1]` `[unverified-MPN]` |
| `U3` | **rail force amplifier**, unity-gain follower of `U2` | V+ = **+5 V**, V− = GND | see §3.1.1 — **mandatory** |
| `C_REF` | reference output capacitor | per the REF5025 datasheet's stability requirement | ⚠ **G1 datasheet read.** Some series references oscillate into particular capacitance ranges. Do not pick this value by habit. |

#### 3.1.1 The rail force amplifier is MANDATORY, and the probe is what proved it

Load on the 2.500 V clamp rail, **with both modules at full scale simultaneously — which is
a NORMAL steady-state condition in dual-unipolar mode (G0-A4), not an overlap allowance**:

```
VSET buffer P output at FS (into 500 ohm)         5.000 mA
VSET buffer N output at FS (into 500 ohm)         5.000 mA
DAC reference input (code dependent)              1.000 mA   [recalled]
VSET buffer quiescent, two channels               1.000 mA   [recalled]
window-comparator sense divider                   0.062 mA
TOTAL                                            12.062 mA
```
`[verified-run]`

**REF5025 is rated ±10 mA. Direct drive FAILS at 0.83× — it is not marginal, it is short.**

`CONTROL_ARCHITECTURE.md` §1.7 assumed the reference could drive the set path directly.
That was true only while **(a)** the pull-down was weak and **(b)** only one module could be
enabled at a time. **G0-A4 broke premise (b) and this design breaks premise (a).** The probe
carries a standing assertion that direct drive is inadequate, so if a future edit ever makes
it adequate again the check fires and the rail buffer is re-examined rather than silently
retained.

With `U3` interposed, the REF5025 sees only `U3`'s input bias current (≤1 nA) and `U3`
supplies the 12.06 mA from +5 V. **Required: ≥18.1 mA continuous with ≤5 mV of drop**
(1.5× margin) `[verified-run]`.

`U3` also removes a term that would otherwise have been **cross-coupled between the two
outputs**: REF5025 load regulation at 8 ppm/mA `[recalled]` × 12.06 mA = 96.5 ppm, and it
depends on the *total* rail current, i.e. on the *other* channel's setting.

#### 3.1.2 Star routing and Kelvin feedback on the clamp rail — not optional either

The two `VSET` buffers share `VCLAMP`. 20 mΩ of shared copper between `U3` and the star
point carries 10.0 mA when both channels are at full scale ⇒ **0.080 V of error on each
output that depends on the other output's setting** `[verified-run]`. This coupling did not
exist before G0-A4.

> **Take `U3`'s feedback AT THE STAR POINT and route `VCLAMP` as a true star.** The shared
> drop is then inside `U3`'s loop and the cross term becomes **structurally zero**, not
> merely smaller. What remains is star→pin, carrying only that channel's own current:
> **0.0200 V**, a per-channel gain term, hence calibratable `[verified-run]`.

### 3.2 DAC and its digital interface

| Ref | Part | Notes |
|---|---|---|
| `U1` | **DAC8552** — dual 16-bit, SPI, external VREF, on-chip rail-to-rail output buffer, 10 µs settling to ±0.003 % FSR, lifecycle ACTIVE | `[web-verified, ti.com, session 1]` `[unverified-MPN]` |
| — | `VDD` = **+5 V**, `VREF` = **VCLAMP (2.500 V)** | |
| `U6` | **74AHCT125** quad buffer, VCC = +5 V, on `SYNC` / `SCLK` / `DIN` | AHCT has **TTL** input thresholds, so it accepts 3.3 V logic directly with no direction control |

**Selection gates any substitute must pass — all four are safety- or function-critical:**

1. **Ratiometric output**: `Vout = VREF × code/2^N`, and the part must specify that the
   output cannot exceed `VREF`. This, not the supply rail, is the DAC's contribution to the
   clamp.
2. **Power-on reset to ZERO scale.** ⚠ `[recalled]` for the DAC8552 — **this is a G1
   datasheet read and it is not a formality.** A DAC that powers up at mid- or full-scale
   commands HV before firmware exists. If the chosen part does not guarantee zero-scale POR,
   it is disqualified; a `/CLR` pin held asserted by an RC until firmware releases it is the
   only acceptable substitute.
3. **Digital `VIH` compatible with whatever drives it.** ⚠ **A concrete trap:** TI DAC85xx
   digital inputs are `[recalled]` specified at `VIH = 0.7·VDD`. At `VDD = 5 V` that is
   **3.5 V, which 3.3 V logic does not meet.** This is why `U6` exists. If the chosen part
   turns out to be TTL-compatible at 5 V, delete `U6`; if `VDD = 3.3 V` is chosen instead,
   delete `U6` and read §3.2.1.
4. **Write-only is acceptable** (DAC8552 has no readback). The loop closes on the
   independent monitor, which is a *better* detector of a corrupted DAC state than a
   readback register would be, because it sees the actual output rather than the intent.

**Fallback if 16-bit is refused:** `MCP4726` ×2 (12-bit, external VREF, I²C)
`[web-verified, Microchip, session 1]`. Fully adequate — see §6.

**Rejected DAC options, with reasons:** `MCP4725` (reference is its own VDD — ratiometric to
3.3 V, so its top codes command 1320 V); `MCP4822` (internal 2.048 V reference: at gain ×1
its full scale is **819 V**, so it *cannot reach* the required 1 kV; at gain ×2 it reaches
1638 V, i.e. over-range is a normal code); **any ESP32 internal DAC** (§7).

#### 3.2.1 Why the 3.3 V domain is kept off the set path *physically*, not just electrically

Either `VDD` choice is electrically safe, because `U4`'s rail clamps regardless:

| DAC `VDD` | Worst internal DAC fault (output shorted to VDD) | `VSET` after `U4` |
|---|---|---|
| 5 V | 5 V at `U4`'s input | **≤ 2.5015 V** (`U4` clamps) |
| 3.3 V | 3.3 V at `U4`'s input | **≤ 2.5015 V** (`U4` clamps) |

**`U4`'s input must survive it.** `U4` runs from a 2.500 V rail, so its input absolute
maximum is `V+ + 0.3 V ≈ 2.8 V` and 5 V would violate it. The **1 kΩ series resistor at
`U4`'s non-inverting input** limits the input clamp current to
`(5 − 2.5 − 0.6)/1 kΩ = 1.9 mA` — inside a typical CMOS input clamp rating `[recalled]`.
That resistor is at the *amplifier input*, not in the `VSET` path, so ARCH-04 does not
apply to it and it costs `Ib × 1 kΩ ≤ 1 µV`.

**Recommendation: `VDD = 5 V` plus `U6`**, chosen for the *layout* reason, not the
electrical one — it keeps the entire +3V3 domain out of the analog set-path region of the
board, which is the only real defence against a `VSET`-to-3V3 solder bridge (§5, fault F7).

> ⚠ **AMENDMENT TO `CONTROL_ARCHITECTURE.md` DESIGN RULE 8, stated explicitly.**
> Rule 8 reads: *"no net that touches `VSET_*` may also touch `+3V3`"*. As an executable
> netlist check that is correct and must be kept. But its **intent** — "the set path must
> not be able to reach 3.3 V" — needs the stronger phrasing, because with `VDD = 3.3 V` the
> DAC's supply pin is in the set path's *chain* while satisfying the letter of the rule.
> **Restate as:**
> - **8a.** No net downstream of `U4`'s output may touch `+3V3` or `+5V`. *(unchanged in
>   effect, this is the original rule)*
> - **8b.** `U4`'s V+ net must be `VCLAMP`, and `VCLAMP` must have exactly one driver, `U3`.
> - **8c.** Any rail present upstream of `U4` must be one whose full value `U4` can survive
>   at its input through the 1 kΩ limiter.
> All three are netlist-checkable. **This is a refinement, not a reversal.**

### 3.3 The `VSET` buffer — this is the clamp

| Ref | Part class | Notes |
|---|---|---|
| `U4A`, `U4B` | dual precision RRIO op-amp, **V+ = VCLAMP (2.500 V)**, V− = GND | one package, both channels |

**Requirements. These are selection gates, not preferences.**

| Parameter | Requirement | Why |
|---|---|---|
| Supply range | must be **specified** at V+ = 2.40–2.60 V single supply | the rail *is* the reference; an amp specified only ≥2.7 V is disqualified |
| Input CM range | **rail-to-rail input**, must include V+ | it buffers a 0…2.500 V DAC into a 2.500 V rail |
| Output swing | **≤ 5 mV below V+ at 5.0 mA source** | a larger drop costs range; it errs **low**, i.e. safe, but the loss is real |
| Output current | **≥ 10 mA source, ≥ 1 mA sink**, continuous | 5.0 mA into the pull-down + 250 µA from the module's pull-up + margin |
| `Vos` | ≤ 200 µV | 0.080 V at the output; calibratable |
| `Vos` drift | ≤ 2 µV/°C | 0.016 V over 20 K; **not** calibratable |
| `Ib` | ≤ 1 nA | with the 1 kΩ input resistor: ≤1 µV |
| **0.1–10 Hz noise** | **≤ 3 µVpp** | §9 — this is where the module specifies *nothing* |
| `Iq` | ≤ 0.5 mA per channel | it loads the clamp rail |
| Input abs-max | tolerate `VDD_DAC` at the input through 1 kΩ | §3.2.1 |
| Stability | unity-gain stable into the `VSET` node capacitance (module pin + 100 nF local) | see the note below |

**Candidates, all `[recalled]` and all `[unverified-MPN]` — every one needs a G1 datasheet
read against the table above:** `OPA2391` (1.7–5.5 V, RRIO, low `Ib`), `TLV9062`
(1.8–5.5 V, RRIO, high output current, more 1/f), `OPA2377`, `OPA2333` (chopper, excellent
1/f, **but its output current is likely insufficient — check it first, it is the parameter
that disqualifies most precision amps here**). **Do not commit a BOM line without the
read.** One distributor deep-link consulted in session 1 returned a completely unrelated
product; that is why no availability claim is made here.

> **Stability note.** The 100 nF C0G at the `VSET` pin is a capacitive load on `U4`. Most
> RRO amps are not unconditionally stable into 100 nF. **Do not solve this with a series
> isolation resistor outside the loop** — that is precisely the ARCH-04 violation. Solve it
> **inside** the Kelvin loop (§3.5): the isolation resistor sits between `U4`'s output and
> the pin while the feedback is taken *at the pin*, so it is nulled at DC. Verify the
> resulting loop stability in simulation before layout; this is the one place in the set
> path where a simulation is genuinely required.

#### 3.3.1 Why the buffer may not be dropped — a NEW argument, stronger than ARCH-32's

`DECISIONS.md` ARCH-32 resolved "keep the buffer" on the grounds that ARCH-06 needs a
rail-to-rail stage on a 2.500 V rail anyway. Two further reasons, neither previously stated:

1. **Drive.** The DAC8552's output is specified into a 2 kΩ / 1000 pF load. The 500 Ω
   pull-down demands **5.0 mA**, which no DAC in this class delivers at rated accuracy.
   With the pull-down at the pin, **the buffer is a functional necessity, not a safety
   refinement.**
2. **Fault containment.** Without `U4`, an internal DAC fault shorting its output to `VDD`
   puts **5 V on `VSET` = 2000 V**. With `U4`, the same fault is bounded at **≤2.5015 V =
   1000.6 V**. The buffer converts a class of DAC internal faults from *200 % of Vnom* into
   *100.1 % of Vnom*.

### 3.4 At the module pin — four parts, in this physical order

**The pull-down must be the LAST element before pin 2.** A break between the pull-down and
the pin restores the 1000 V default; a break anywhere upstream of it does not. This is a
layout rule with a factor-of-21 consequence.

| Ref | Part | Value | Job |
|---|---|---|---|
| `R_PD1`, `R_PD2` | thin film, ≥1 %, 0805 | **2 × 1.00 kΩ in parallel = 500 Ω** | ARCH-05 pull-down, duplicated per ARCH-18 |
| `D_NEG` | **BAT54** or equivalent small-signal Schottky | cathode → `VSET`, **anode → GND** | clamps negative excursions (§10.13: negative `Vset` is undocumented). **Fails safe both ways.** |
| `C_LOCAL` | 100 nF **C0G** | — | local HF bypass at the pin |
| `Q_SHUNT` | **2N7002** | gate driven from `/ON_x` **at the module end of that net** | *disabled ⇒ `VSET` grounded*, in hardware (ARCH / §3.6) |

**Pull-down sizing — the full trade, computed** `[verified-run]`:

```
 Rpd (ohm)   Vset (V)  Vout (V)   % Vnom  I at FS (mA)  <60 V?
     10000     1.2500     500.0   50.00 %         0.25      NO
      2000     0.4167     166.7   16.67 %         1.25      NO
      1000     0.2273      90.9    9.09 %         2.50      NO
       604     0.1424      57.0    5.70 %         4.14     yes
  ►    500     0.1190      47.6    4.76 %         5.00     yes   ◄ CHOSEN
       402     0.0966      38.6    3.86 %         6.22     yes
       302     0.0733      29.3    2.93 %         8.28     yes
       200     0.0490      19.6    1.96 %        12.50     yes
       100     0.0248       9.9    0.99 %        25.00     yes
```

Computed **two independent ways** — as a two-resistor divider, and by Thévenin/superposition
from the `(Vref, 10 kΩ)` Norton equivalent — and asserted equal to machine precision at every
row. This is the probe's independent source of truth for the most consequential number here.

**Why 500 Ω:**
- Driver-open residual **47.6 V**, which is **below the 60 V touch-safe threshold**
  (NUM-15, `[recalled]` `[unverified-primary]`) with 21 % margin.
- Full-scale drive **5.0 mA** — affordable for a real RRO amp on a 2.500 V rail.
- **`2 × 1.00 kΩ`, not one 500 Ω**, per ARCH-18. One element open is a *second* fault and
  degrades to **90.9 V**, which is above the touch-safe threshold and must be stated as such
  rather than absorbed: at that point the independent monitor and the firmware trip are what
  meet the criterion.

**⚠ Sensitivity to an untoleranced number — flag this, do not bury it.** The residual is
inversely dependent on the module's internal 10 kΩ, for which **iseg publishes no tolerance
at all** (`PART_iseg_APS.md` §10.14):

```
  R_pullup  Vout residual   vs 60 V
      7.0k          66.7 V     FAILS
      8.0k          58.8 V        ok
     10.0k          47.6 V        ok
     13.0k          37.0 V        ok
the 60 V criterion breaks at R_pullup = 7.83 k (-21.7 % of nominal)
```
`[verified-run]`

> **[MEASURABLE-NOW]** — the modules are in hand (G0-A2). **Measure the internal pull-up
> before the pull-down value is frozen.** Procedure in §8.1.
> **If the measurement comes back at the pessimistic end** (`R_pullup ≤ 7.8 kΩ`): move to
> **2 × 604 Ω ∥ = 302 Ω**, which gives 41 V at a 7 kΩ pull-up, at the cost of **8.28 mA**
> of buffer drive per channel (16.6 mA total) and a correspondingly larger `U3`. Nothing
> else in the design changes.
> **This is a fifth measurable module parameter, additional to the four in `G0_QUESTIONS.md`
> O-2**, and it is load-bearing for a primary safety element. It should be added to O-2.

### 3.5 Kelvin sensing — and the two errors it fixes, one of them new

**ARCH-04 caps DAC-to-pin series resistance at 10 Ω. That cap was derived from ONE error
term. The pull-down at the pin adds a second, and the second is 20× larger.**

| `Rs` (Ω) | term 1: divider vs the 10 kΩ, worst at **zero** | term 2: IR drop, worst at **full scale** | dominant |
|---:|---:|---:|:--|
| 0.1 | 0.010 V | 0.200 V | IR |
| 0.2 | 0.020 V | 0.400 V | IR |
| 1.0 | 0.100 V | 2.000 V | IR |
| 10.0 | 0.999 V | **20.000 V** | IR |
| 100.0 | 9.901 V | 200.000 V | IR |

`[verified-run]` — the ratio at `Rs → 0` is **20×** and it only grows with `Rs`. The two
terms are never equal for any physical resistance. **At ARCH-04's own 10 Ω limit the new
term alone is 20 V at the output.**

> **⚠ This is a correction to ARCH-04, and it is stated as one.** ARCH-04's *reasoning*
> is correct and its number is correct **for the circuit it was derived against** (a driver
> feeding a bare `VSET` pin). **With a pull-down at the pin, 10 Ω is no longer a safe cap.**
> ARCH-04 should be restated as: *"the total series resistance from the driver to the `VSET`
> pin, EXCLUDING any resistance enclosed by a Kelvin feedback loop whose sense point is the
> `VSET` pin itself, shall be ≤ 0.2 Ω when a pull-down of ≤1 kΩ is fitted at the pin."*

**The arrangement:**

```
      U4 OUT ──── force trace, ≤0.2 Ω, wide ────► VSET pin 2
         │                                            │
         └──── R_local = 10 kΩ ────┬──── sense trace ─┘   (carries only Ib)
                                   │
                              U4 IN− (feedback node)
```

- **Sense intact:** `V_FB ≈ V_PIN`, the force-path drop is inside the loop.
  Residual error **0.0020 mV at the output — nulled by 200 000×** `[verified-run]`.
- **Sense trace OPEN (single fault):** the feedback node reverts to the local 10 kΩ path,
  and `U4` degrades **gracefully to a plain buffer** — 0.400 V of gain error, **not to the
  rail**. This is the reason `R_local` exists and it is the reason a bare remote-sense wire
  is unacceptable: without `R_local`, an open sense trace opens the feedback loop and drives
  the output **to V+, i.e. full scale**.
- **`R_local` must be LARGE.** With the sense intact, `OUT → R_local → FB → sense → PIN` is
  a real series path, and the current it circulates is injected into `VSET`. At
  `R_local = 10 kΩ` it is **0.1 nA = 0.000002 %** of the pull-down current; at a
  "local" 10 Ω it would be **0.100 %** `[verified-run]`. **Rule: `R_local ≥ 1000 × R_force`.**

### 3.6 Shunt FET and its gate tap point

`/ON_x` is HIGH exactly when module *x* is disabled (open-drain, 10 kΩ pull-up to that
module's own `+VIN` = 5 V, ARCH-17). Driving `Q_SHUNT`'s gate directly from it makes
*"disabled ⇒ `VSET` grounded"* a hardware invariant with zero added logic and zero firmware.
2N7002 `Vgs(max)` is ±20 V, so a 5 V gate is within rating `[recalled]`.

> **Layout rule: tap the gate at the MODULE end of the `/ON_x` net, at the pull-up.**
> Then a break *anywhere* in `/ON_x` simultaneously (i) releases `/ON` HIGH → module off,
> and (ii) turns the shunt ON → `VSET` grounded. Both safe. Tapping at the driver end makes
> a break turn the shunt *off*, which is merely benign rather than actively safe.

This mechanism survives G0-A4 unchanged: in **dual-unipolar** mode both modules are enabled,
so both FETs are off and both DACs drive — correct. In **pseudo-bipolar** mode the deselected
module's `VSET` is shunted — correct. It was keyed to *enablement*, not *selection*.

Firmware must **also** write code 0 to a disabled channel, so the FET normally carries no
current. Per ARCH / §3.6, put ~100 Ω between the DAC and the FET drain **on the DAC side of
the `VSET` tap**, never in series with the pin.

---

## 4. The window comparator — the fault the rail clamp cannot cover

### 4.1 The tension in the repo, named and resolved

| | claim |
|---|---|
| `PART_iseg_APS.md` §8.2 | *"The clamp rail must not be the same node the DAC uses as its reference — a shared reference failure would raise the clamp and the command together."* |
| `DECISIONS.md` ARCH-06 | Make the DAC's own rail-to-rail stage, powered from the DAC's reference, the clamp. |

**Both are correct and they are about different things.** ARCH-06 is right that a shared
rail is the *cleanest possible* clamp for every fault *except one*. §8.2 is right that
**the excepted fault — the reference rail rising — is real and is not covered**:

- REF5025 internal pass element shorting to its own +5 V supply ⇒ `VCLAMP` = 5 V ⇒ **2000 V**.
- `U3`'s output stage failing to its +5 V rail ⇒ same.
- A solder bridge from `VCLAMP` to +5 V or +3V3 ⇒ 2000 V or 1320 V.

**Resolution: keep the shared rail (ARCH-06's elegance is real), and add an independent
detector of the one thing it cannot see.** The detector must not be a shunt clamp — see
§4.3 for why that was evaluated and rejected with numbers.

### 4.2 Specification

| Ref | Part | Notes |
|---|---|---|
| `U5` | dual comparator, **push-pull outputs**, V+ = +5 V | `[unverified-MPN]` |
| `D_REF2` | **LM4040-2.048**, ±0.1 % grade | ⚠ **a DIFFERENT device from a DIFFERENT family than REF5025** — a common-mode reference failure must not move the detector and the thing it detects together |
| sense divider | 2 × 20.0 kΩ, 0.1 % | `VCLAMP`/2 → 1.2500 V at nominal |
| threshold string | **7.50 kΩ / 590 Ω / 11.8 kΩ** (E96) across 2.048 V | taps at 1.2150 V and 1.2758 V |
| hysteresis | ~1 MΩ output→(+) on each comparator | a few mV; prevents chatter at the threshold |

**Resulting thresholds** `[verified-run]`:

```
low  trip  2.4300 V  (-2.80 %)
high trip  2.5515 V  (+2.06 %)
max Vout a reference fault can produce before the trip fires : 1021 V
vs an UNDETECTED rail rise to 3.3 V (1320 V) or 5 V (2000 V)
legitimate rail band 2.4985 .. 2.5015 V
  margin to the low trip 2.82 % ; to the high trip 2.00 %
```

The margins are asserted in both directions: the window must **contain** the legitimate
REF5025 tolerance band (no nuisance trips) and must **cap** a reference fault below the
105 % OVP threshold (so the layers nest rather than overlap).

**Fail-safe polarity.** Comparator outputs are **HIGH = in window**, ANDed into the `ARM`
permissive chain, with a **duplicated pull-down (2 × 200 kΩ, ARCH-18)** at the AND-gate
input. A comparator that loses power, or whose output floats, reads **0 = not permitted**.
`U5` is powered from **+5 V**, which is present whenever the modules are powered — not from
+3V3, which is not.

**Sense point: at `U4`'s V+ pin (the load end of `VCLAMP`), not at `U3`'s output.** A break
between `U3` and `U4` must be visible to the detector.

**What `U5` cannot do:** if `U5`'s own output stage fails HIGH, the layer is silently lost.
Nothing detects that in service; it is a **bench test** (§8.3), and the latched hardware OVP
on the independent monitor remains behind it.

> **Firmware cross-check, and it is already provisioned.**
> `docs/design/MONITOR_AND_BLEED.md` allocates **ADC-B `AIN2` to a `VREF` sense** channel.
> That is exactly the right home for a continuous firmware read of `VCLAMP`, giving a check
> on the rail that is **independent of `U5`** and that would catch F19 (`U5` stuck HIGH) in
> service after all — provided firmware actually compares it against a band and trips.
> **It is a diagnostic, not a permissive:** it must not be wired into `ARM`, because
> MONITOR_AND_BLEED's own design rule is that no interlock reads the ADC. Recorded here so
> the channel is not repurposed and so the firmware requirement is not lost between the two
> documents.

### 4.3 A shunt clamp on the rail was evaluated and rejected

The obvious alternative — a shunt reference (LM4040/TLV431 class) across `VCLAMP` to hold it
down — fails on arithmetic. To clamp a rail that `U3` is actively forcing, a series element
between `U3` and the rail is required. Sizing it:

- With 10 Ω of series resistance, a `U3`-shorted-to-5 V fault drives
  `(5 − 2.7)/10 Ω = 230 mA` through the shunt — two orders beyond any LM4040's rating.
- Sizing the series resistor to bound that current instead costs rail stiffness: at
  12 mA of legitimate load, 100 Ω is a **1.2 V** drop. Unusable.

**Therefore: detection plus interlock, not shunt clamping.** Stated so the next reader does
not re-derive it.

### 4.4 Three nested layers, each indifferent to a different failure

| Layer | Mechanism | Covers | Blind to |
|---|---|---|---|
| **1. `VCLAMP` = `U4`'s V+** | an RRO stage cannot exceed its own rail | every digital fault, every DAC fault, every firmware and network command | the rail itself rising |
| **2. `U5` window comparator** | independent reference + `ARM` permissive | rail rise, rail collapse, `VCLAMP` open between `U3` and `U4` | a `VSET`-to-3V3 bridge downstream of `U4`; its own stuck-high failure |
| **3. latched hardware OVP at 105 % = 1050 V** | comparator on the **buffered independent monitor**, latched, cleared only by `OUTP:PROT:CLE` | **anything that produces over-voltage, by any mechanism** | nothing in this path — it measures the actual output |

> **Layer 3 is the only one indifferent to the fault's mechanism.** Layers 1 and 2 are
> preventive; layer 3 is the backstop. Say this plainly in review: a design that has only
> layer 1 (which is what ARCH-06 alone specifies) is one component failure from 2000 V.

---

## 5. Single-fault analysis

`ESP32-S3` assumed (§7). `+VIN` = 5 V. "Armed" means `ARM = 1` and that module enabled.

### 5.1 Faults in the set path

| # | Fault | `VSET` becomes | `Vout` | Verdict |
|---|---|---|---|---|
| F1 | **`VSET` track open between `U4` and the pin** | pull-down (at the pin) holds | **47.6 V** | ✅ safe-ish; monitor + trip. *This is why the pull-down is the last element before the pin* |
| F2 | **`VSET` track open between the pull-down and the pin** | internal 10 kΩ wins | **1000 V** | ❌ **the one un-mitigated open.** Mitigation is layout only: the pull-down pad shares the pin-2 land. Detected by the monitor and by layer 3, never prevented |

> **Reconciliation with `docs/design/COMBINER_DESIGN.md` F-10.** That document states
> *"`VSET` open ⇒ internal 10 kΩ to Vref ⇒ full scale"* and relies on the latched `nOVP` at
> 1050 V. **The two documents are compatible, but only if the break's location is named:**
> COMBINER_DESIGN's F-10 is precisely **F2 here** (a break *downstream* of the pull-down).
> For **F1** — a break anywhere *upstream* of the pull-down, which is the far larger share of
> the track length and of the solder joints — the pull-down holds the module at **47.6 V** and
> the module never approaches the OVP threshold. **Do not read F-10 as saying the pull-down is
> ineffective.** COMBINER_DESIGN also supplies the useful timing for the F2 case: the output
> reaches the 1050 V trip point ≈159 ms after the fault (bounded by the module's own 100 ms
> set-node pole) and the comparator responds in microseconds.
| F3 | `U4` dead / output high-Z, rail present | pull-down holds (0.119 V < the 0.6 V needed to forward-bias `U4`'s ESD diode, so the diode never conducts) | **47.6 V** | ✅ |
| F4 | `U4` unpowered (`VCLAMP` collapsed) | pull-down holds; DAC output also collapses | **47.6 V** | ✅ **and** `U5` low-trip fires → `ARM = 0` → `/ON` HIGH → 0 V. Two mechanisms |
| F5 | **`VCLAMP` rises to +5 V** (REF or `U3` pass short) | up to 5 V | **2000 V** | ⚠ `U5` high-trip fires at 2.5515 V → `ARM = 0`. **Bounded at 1021 V during the trip delay**, then 0 V |
| F6 | `VCLAMP` open between `U3` and `U4` | `U4` unpowered | as F4 | ✅ — provided `U5` senses at `U4`'s V+ pin |
| F7 | **`VSET` shorted to +3V3** (solder bridge, 0 Ω) | 3.3 V; `U4` cannot win | **1320 V** | ❌ *not preventable by the set path.* `U4`'s ESD diode conducts at ≈3.0 V and back-drives `VCLAMP` up → `U5` fires. Layer 3 fires regardless. **Prevented only by keeping the 3.3 V domain physically away — §3.2.1** |
| F8 | `VSET` shorted to GND | 0 V | 0 V | ✅ safe; channel dead |
| F9 | **one pull-down element open** | 1.00 kΩ | *no effect while `U4` drives*; 90.9 V only if F1/F3/F4 also | ✅ this is what ARCH-18 buys |
| F10 | both pull-downs open | — | *no effect while `U4` drives*; 1000 V with F1/F3/F4 | double fault |
| F11 | **Kelvin sense trace open** | — | 0.400 V gain error | ✅ **graceful**, because of `R_local` (§3.5). Without `R_local` this fault rails the amp to full scale |
| F12 | `R_local` open | Kelvin still works; sense-open fault F11 becomes fatal | — | ⚠ latent; both are 0402/0603 resistors, treat as a pair in the pre-fab checklist |
| F13 | `Q_SHUNT` fails SHORT | 0 V permanently | 0 V | ✅ safe; that channel produces nothing. Caught by the power-up self-test |
| F14 | `Q_SHUNT` fails OPEN | loses *disabled ⇒ grounded* | disabled module still has `/ON` HIGH ⇒ 0 V | ✅ second-order |
| F15 | **DAC internal short, output to `VDD`** | `U4` input at 5 V, limited by 1 kΩ | **≤1000.6 V** | ✅ **this is the buffer's fault-containment value** (§3.3.1) |
| F16 | DAC stuck at full code | 2.500 V | **1000.0 V** | ✅ *by design* — the clamp permits exactly Vnom. Soft limits (ARCH-37) are the layer that would have prevented it; hardware correctly does not |
| F17 | DAC `VREF` trace open | DAC output undefined | `U4` output bounded by `VCLAMP` | ⚠ add a **duplicated 2 × 200 kΩ pull-down at `U4`'s input** so an open DAC output or open `VREF` drives `U4` to 0 V rather than to an undefined level |
| F18 | `U6` (level shifter) unpowered or `/OE` floating | DAC inputs float, spurious codes | any code, but **≤ 2.500 V ⇒ ≤1000 V** | ✅ bounded. Pull `U6`'s *inputs* to defined levels (SYNC high, SCLK/DIN low) so the ESP32 in reset presents `SYNC` inactive |
| F19 | `U5` output stuck HIGH | layer 2 silently lost | — | ⚠ **undetectable in service.** Bench test only (§8.3); layer 3 remains |
| F20 | `D_REF2` (LM4040) fails | thresholds move | high ⇒ less protection (layer 3 remains); low ⇒ nuisance trip | ✅ asymmetric in the safe direction |
| F21 | Negative excursion injected on `VSET` (HV flashover coupling) | clamped to −0.3 V by `D_NEG` | — | ✅ and `D_NEG` fails safe both ways (§2.2) |

### 5.2 The ESP32 in reset or unpowered while the HV rails are up

**This is the case the whole interlock exists for, and the set path does not solve it alone.**

- **The DAC holds its last code. It does NOT fail safe.** State that plainly: an SPI bus
  that stops being written leaves `VSET` exactly where it was.
- What saves it, in order:
  1. The **heartbeat charge pump** decays below the HC threshold in **~79 ms**
     (1 MΩ / 100 nF, ARCH-20) `[verified-run, session 1]` ⇒ `EN_HB = 0` ⇒ `ARM = 0`.
  2. `/ON_P` and `/ON_N` are released by the open-drain drivers and pulled **HIGH by the
     10 kΩ to each module's own `+VIN`** ⇒ both modules commanded to zero.
  3. The same `/ON` transition turns **both shunt FETs ON** ⇒ both `VSET` nodes grounded.
- **All three are independent of the DAC's state and of the 3.3 V rail's existence.**
- Note the ordering luck: 79 ms is *shorter* than the module's own 100 ms set-node pole, so
  the hardware chop is faster than the module could have ramped.

**Loss of the +3V3 rail specifically** (F: LDO dies while +5 V lives): open-drain drivers
release → `/ON` HIGH via the +VIN pull-ups → off. The DAC (`VDD` = +5 V) and `U4`
(`V+` = `VCLAMP`) both stay alive, so `VSET` holds — but `/ON` HIGH commands zero anyway.
✅ **This is the reason `U6` and the DAC run from +5 V rather than +3V3.**

### 5.3 Broken wire on each control line

| Line | Break effect | Verdict |
|---|---|---|
| `SPI SCLK` / `DIN` / `SYNC` | DAC holds last code | ⚠ **no over-range possible**, but the commanded value is frozen. **The independent monitor is the detector** — it sees the output not tracking the ramp. There is no readback path and none is needed |
| heartbeat GPIO | pump decays → `ARM = 0` | ✅ |
| `/ON_P` or `/ON_N` | pull-up at the module holds HIGH → that module OFF **and** its shunt FET ON (gate tapped at the module end) | ✅ doubly safe |
| `VCLAMP` to `U4` | as F6 | ✅ via `U5` |
| `VCLAMP` sense to `U3` | `U3`'s loop opens → its output rails to +5 V → `VCLAMP` = 5 V | ⚠ **caught by `U5` high-trip.** `U3` must also have a local feedback resistor for the same reason `U4` does — **`R_local` on `U3` is not optional either** |
| `U4` sense trace | F11 — graceful | ✅ |
| `U4` force trace | F1 — pull-down holds | ✅ |
| pull-down leg | F9 | ✅ |
| `U5` sense divider (top leg) | sense node → 0 → low-trip fires | ✅ fail-safe |
| `U5` sense divider (bottom leg) | sense node → `VCLAMP` = 2.5 V > 1.2758 V → high-trip fires | ✅ fail-safe. **Both legs fail safe — check this explicitly at review, it is not automatic** |
| `MODE_POS` aux pole (G0-A5) | must fail to 0 = pseudo-bipolar, duplicated pull per ARCH-18 | outside this document; see `CONTROL_ARCHITECTURE.md` §3.3a |

---

## 6. DAC resolution and settling — what is actually required

`[verified-run]`

| DAC | LSB at `VSET` | **LSB at the output** | ppm FS | codes inside the module's ±1 % band |
|---:|---:|---:|---:|---:|
| 8 b | 9803.92 µV | 3.9216 V | 3921.6 | 5.1 |
| 12 b | 610.50 µV | **0.2442 V** | 244.2 | 81.9 |
| 14 b | 152.60 µV | 0.0610 V | 61.0 | 327.7 |
| **16 b** | **38.15 µV** | **0.0153 V** | 15.3 | 1310.7 |
| 18 b | 9.54 µV | 0.0038 V | 3.8 | 5242.9 |

*(ppm computed twice, from two independent expressions, asserted equal.)*

**Settling is a non-requirement.** The module's own set-node pole is
`100 kΩ × 1 µF = 100 ms` (Figure 2 `[verified-artifact ×4]`, PART-07, **[MEASURABLE-NOW]**).
Time to settle to 1 LSB after a full-scale step:

```
12-bit : 0.832 s    DAC's own settling 10 us  =>  the module is  83 178x slower
16-bit : 1.109 s    DAC's own settling 10 us  =>  the module is 110 904x slower
```

**Any DAC in this class beats the module by four orders of magnitude.** No settling
specification discriminates between candidates.

### 6.1 A correction to `CONTROL_ARCHITECTURE.md` §1.3, stated openly

§1.3 lists "ramp smoothness — a 3.92 V step into a capacitive HV load is a real `i = C dV/dt`
event" as a reason to prefer resolution. **Checked at the declared interface limit
`C_load ≤ 10 nF` (NUM-13), it is not a reason here** `[verified-run]`:

```
 8-bit step  3.9216 V smeared over the module's 100 ms pole ->  392.157 nA
12-bit step  0.2442 V                                       ->   24.420 nA
16-bit step  0.0153 V                                       ->    1.526 nA
compare Iout limit 750 uA:  the largest of these is 0.05229 % of it.
```

The module's own 100 ms pole integrates every LSB step, so the dI/dt argument is three
orders of magnitude away from mattering. **Do not use it.** It would only become real with a
much larger `C_load`, which NUM-13 forbids, or a much faster module pole, which
`[MEASURABLE-NOW]` could in principle reveal.

### 6.2 Recommendation

> **16-bit (`DAC8552`), because it removes the DAC from the error budget entirely at
> essentially the same cost. 12-bit (`MCP4726` ×2) is a fully adequate fallback.**

The honest reasoning, since §6.1 removed one of session 1's arguments:

- **Accuracy: neither matters.** `ARCH-01` stands — `Vout/Vnom = Vset/Vref` and *their* Vref
  is ±1 %, so no open-loop accuracy better than 1 % is obtainable at any resolution.
- **The closed loop is limited by the sensor, not the actuator.** The independent monitor is
  ~1.58 V (CONTROL_ARCH §2.5). 12-bit's 0.2442 V LSB is already **6.5× finer**; 16-bit is
  100× finer. Both are adequate; neither limits the loop.
- **What 16-bit actually buys** is settability and repeatability, and freedom from ever
  having to think about DAC quantisation again (0.0076 V RSS contribution vs the 1.58 V
  monitor floor).

> ⚠ **`DECISIONS.md` ARCH-03 says "12-bit set path, 16-bit monitor path".
> `CONTROL_ARCHITECTURE.md` §1.7 recommends the 16-bit DAC8552. Those are not the same
> statement.** Read ARCH-03's 12-bit as a **floor**, not a target, and update the row to say
> so. Flagged rather than silently resolved.

---

## 7. ESP32 variant

> **Assume ESP32-S3** (ARCH-25, `assumed-pending-G1`). **The DAC question does not influence
> the choice at all**, and the reason is worth stating precisely because it is different
> from session 1's.

| Variant | Internal DAC | |
|---|---|---|
| ESP32 (classic) | 2 × **8-bit**, GPIO25/26 | `[web-verified, espressif, session 1]` |
| **ESP32-S3** | **none** | `[web-verified, espressif, session 1]` |
| ESP32-C3 | **none** | `[recalled]` |

**Session 1 disqualified the internal DAC on resolution (8-bit = 3.92 V per LSB, 5.1 codes
across the module's entire accuracy band). G0-A2 disqualifies it on SAFETY, which is a
harder disqualification and would hold at any resolution:** the classic ESP32's DAC is
referenced to its own **3.3 V rail**, so **its top 24 % of codes command an over-range the
datasheet says is internally not limited.** The over-range is not at the end of a fault
chain — it is at the end of the *code range*.

**⇒ Do not use any 3.3 V-rail-referenced set-point source. That includes the PWM fallback:**
a PWM DAC's full scale *is* the rail, so at full duty it commands 1320 V. If PWM is ever
revived it **must** be followed by a buffer powered from `VCLAMP` — at which point it has
bought nothing and still costs the filter and the buffer.

**Why S3 anyway:** dual core (the safety supervisor must be pinned away from the network
stack — load-bearing since G0-A3), GPIO count, native USB. The missing DAC and ADC are
irrelevant because both are external.

**Pin rules carried in (`CONTROL_ARCHITECTURE.md` §3.2, design rules 2 and 10):**
no DAC `SYNC`/`SCLK`/`DIN`, no `SEL`, no `EN_HB`, no `MODE_POS` input on any strapping pin.
On S3 the strapping pins are GPIO0, 3, 45, 46 `[recalled — G1 datasheet read]`; use the
GPIO4–GPIO18 band. **This must be an executable netlist check, not a review item.**

**`SYNC` idle state:** pull `U6`'s `SYNC` **input** high to +3V3 and `SCLK`/`DIN` low, so
that while the ESP32 is in reset (all GPIO high-Z) `U6` drives `SYNC` inactive. Note these
are *function* pulls, not safe-state pulls — a spurious DAC code is bounded at `VCLAMP` —
so ARCH-18's duplication requirement does **not** apply to them. Stated so nobody duplicates
them reflexively or, worse, treats them as a safety element.

---

## 8. Calibration, and the bench measurements this design needs

### 8.1 Per-module characterisation — do this before the pull-down value is frozen

**On a jig, module out of circuit, `+VIN` = 5 V applied, `/ON` left open or tied high — pin 2
must be loaded by nothing but the meter.**

1. **`Vref`**: measure pin 2 (VSET) open-circuit with a **≥10 MΩ** DMM.
   `Vref = V_measured × (1 + 10 kΩ/Z_meter)`; at 10 MΩ the correction is **0.100 %**.
   → per-module gain constant. **Recovers 10 V of the module's ±1 % (§2.3).**
2. **`R_pullup`** — the number the 60 V criterion depends on and which iseg does not publish.
   Fit a known precision resistor `R1` from pin 2 to GND, measure `V1`; repeat with `R2`.
   ```
   Vref = (R1 − R2) / (R1/V1 − R2/V2)        R_pullup = R1·(Vref/V1 − 1)
   ```
   Round-tripped in the probe to 1e-9 relative `[verified-run]`. With `R1 = 10.0 kΩ` and
   `R2 = 1.00 kΩ` the conditioning number is **3.44**, i.e. a 1 % voltage error becomes
   ~3.4 % in `Vref` — **so use method 1 for `Vref` and this solve only for `R_pullup`.**
3. Record both against the **module serial number**. §2.3's maintenance note applies.

**Contingency if `R_pullup` measures ≤ 7.8 kΩ:** move the pull-down to 2 × 604 Ω ∥ = 302 Ω,
buffer drive 8.28 mA/channel, `U3` sized for ≥25 mA. See §3.4.

### 8.2 The other module parameters this design touches

| Parameter | Status | If it comes back pessimistic |
|---|---|---|
| **`VSET` step response / set-node τ** | `[MEASURABLE-NOW]`, O-2. Inferred as 100 ms from Figure 2 | **Only the firmware ramp rate moves. NO HARDWARE IN THE SET PATH IS SENSITIVE TO IT.** If τ ≫ 100 ms, drop the ramp rate and lengthen the changeover dwell. If τ ≪ 100 ms, broadband set-path noise is less filtered — add an RC **on the DAC output, before `U4`**, never on `VSET` |
| **internal 10 kΩ pull-up** | ⬛ **NEW — add to O-2.** Unpublished (§10.14) | §8.1 contingency above |
| output capacitance · internal bleeder · turn-on time | `[MEASURABLE-NOW]`, O-2 | none of the three enters the set path. They set the discharge and changeover budgets, documented elsewhere |

**Turn-on-time interaction, stated because it is easy to miss:** if the module produces
output very quickly after `+VIN` is applied, a module could energise before firmware has
written the DAC. **This is covered structurally, not by sequencing:** `/ON` is HIGH until
`ARM`, and `/ON` HIGH holds the shunt FET ON, so `VSET` is grounded regardless of DAC state.
The recommended sequence (DAC to zero → verify → `+VIN` → `/ON` low) is belt-and-braces.

### 8.3 Bench verification of the clamp itself — `SCOPE.md` S-8

**This is a primary safety element and it gets its own test. The test must attack the clamp,
not confirm it.**

| # | Test | Pass criterion |
|---|---|---|
| T1 | Command the maximum code the firmware will emit; measure `VSET` at the pin and `Vout` | `Vset ≤ 2.5015 V`; `Vout ≤ 1000 V` |
| T2 | **Bypass firmware**: write full code (0xFFFF) directly over SPI with soft limits disabled | `Vset ≤ 2.5015 V`. **This is the test that proves the clamp is hardware** |
| T3 | Lift `U4`'s output (or open the force trace) with the module enabled | `Vout` settles to **47.6 V ±20 %**, and the independent monitor trips |
| T4 | Substitute a bench supply for `VCLAMP`, ramp 2.30 → 2.70 V | `ARM` de-asserts below **2.430 V** and above **2.5515 V**; `Vout` → 0 at both. **This is the only test of `U5`, and F19 makes it the only one there will ever be** |
| T5 | Remove one pull-down element, repeat T3 | `Vout` settles to **90.9 V ±20 %** |
| T6 | Open the Kelvin sense trace with the channel at full scale | output shifts by ≈0.4 V and **does not rail** |
| T7 | Power the modules with the ESP32 held in reset | both `VSET` = 0, both `/ON` HIGH, `Vout` = 0 at both terminals |
| T8 | Measure `Vref` and `R_pullup` per §8.1 on **both** modules | recorded against serial numbers |

T2 and T4 are the two that matter. **T4 requires a bench supply on `VCLAMP`, so provide a
test point and a link on that rail — designed in, not bodged.**

---

## 9. Noise, and the band where the module specifies nothing

`[verified-run]`

```
0.1-10 Hz, reference 3.0 uVpp RSS buffer 3.0 uVpp = 4.24 uVpp at VSET
  x gain 400  =  1.70 mVpp at the HV output   (0.000170 % of FS)
set-path noise budget referred to VSET = 30 mVpp / 400 = 75.0 uVpp; we use 5.7 % of it.
```

The module's ripple spec (`typ <10 mVpp`, `max <30 mVpp`) is stated for **f > 10 Hz**.
**Below 10 Hz the datasheet specifies nothing at all** (PART-32) — and for a DC bias read on
a DMM, sub-10 Hz wander *is* the measurement.

> **Our set path contributes ~1.70 mVpp in that band. Therefore any sub-10 Hz wander observed
> on the bench above roughly 1.7 mVpp is the MODULE's, not ours.** That is a usable
> diagnostic, and it is why the buffer's 0.1–10 Hz noise (≤3 µVpp) is a hard selection
> parameter in §3.3 rather than an afterthought.

Above 1.59 Hz the module's own 100 ms pole rolls off everything we inject at 20 dB/decade,
so broadband noise is not a concern **while τ = 100 ms holds**. `[MEASURABLE-NOW]` — see
§8.2 for the contingency if it does not.

---

## 10. Range, the firmware code clamp, and what the instrument may claim

`[verified-run]`

```
firmware maximum code fraction    = 98 %
  commanded Vset                  = 2.4500 V nominal, 2.4515 V worst-case-high rail
  WORST CASE HIGH (our rail high, their Vref low  2.475 V) =  990.5 V  (99.05 % of Vnom)
  WORST CASE LOW  (our rail low,  their Vref high 2.525 V) =  969.8 V  (96.98 % of Vnom)
  the code fraction that EXACTLY reaches Vnom in the worst high case is 98.94 %
  folding in the module's own +/-1 % adjustment accuracy,
  the GUARANTEED deliverable magnitude is 960.1 V.
```

**The 98 % clamp (ARCH / §1.7) is confirmed**: it guarantees `≤ Vnom` in the worst-case
tolerance stack, with the break-even at 98.94 % — so 98 % carries margin rather than sitting
on the boundary. It is the **second** layer, and it is firmware, so `CLAUDE.md`'s "firmware
agreement is not sufficient" applies: the hardware rail is the first layer.

> ### ⬛ Product-spec consequence, and it is a real one
>
> **Rate the instrument at ±950 V guaranteed, ~980 V typical. Do NOT declare ±1000 V.**
>
> The guaranteed deliverable magnitude is **960.1 V** once the 98 % clamp, our reference
> tolerance and the module's own ±1 % are stacked in the unfavourable direction. Declaring
> 1000 V would be a specification the hardware cannot meet in the worst tolerance case, and
> the reference board's REF-05 (a readback that reported 200 V while producing 182.94 V) is
> exactly the anti-pattern.
>
> **This interacts with Q3, which the human did not answer** (`G0_QUESTIONS.md` O-3 — output
> spec and required range). If ±1000 V at the terminal is genuinely required, the module
> class is wrong, not the clamp. **Flagged, not resolved.**

---

## 11. The low end — documented behaviour below 2 % · Vnom

**Specs hold only for `20 V < |Vout| ≤ 1000 V`. Below 20 V the output is UNSPECIFIED, not
merely worse** (Table 1 note 1, PART-10/PART-32).

Three facts, all computed `[verified-run]`:

1. The sub-20 V band is **1310 codes at 16-bit / 81 codes at 12-bit** — 2.00 % of the code
   range. It is not a corner case; it is 2 % of everything the instrument can be asked to do.
2. **VMON is blind across the whole band.** VMON accuracy is ±10 V, so two true outputs
   separated by less than **20 V** can produce the same reading: **VMON cannot distinguish
   0 V from 20 V.** It is therefore useless as evidence that the output is at zero.
3. **The two-monitor cross-check is INOPERATIVE below 20 V.** Legitimate quadrature
   disagreement between VMON (±10 V) and the independent monitor (1.58 V) is **10.12 V**,
   against an ARCH-23 trip threshold of **20 V**. In the sub-20 V band a *real* disagreement
   is indistinguishable from the legitimate one. **It does not false-trip — it simply cannot
   detect.** Only the independent monitor means anything there.

### 11.1 The decision: three zones, and why not "refuse"

> **Refuse is wrong.** Every ramp from 0 to any set-point passes through the band. A blanket
> refusal makes monotonic ramping impossible and would have to be special-cased, which is
> how silent behaviours get born.
> **Proceed silently is wrong.** REF-05's anti-pattern: "I asked for X and got Y and nothing
> said so" must be unreachable (`INTERFACES.md` §3.1).
> **Therefore: accept, and say so, every time, in a machine-readable way.**

| Zone | Behaviour |
|---|---|
| `\|V\| = 0` exactly | **Always accepted, from any state.** This is the safe set-point and the target of every ramp-down, changeover and discharge. It must never be refused or warned about |
| `0 < \|V\| < 20.0 V` | **Accepted**, and: (i) a non-fatal advisory is pushed to the error queue — `+110,"Setpoint below specified range (2%*Vnom = 20.0 V): ripple, stability and monitor accuracy are UNSPECIFIED"`; (ii) `STATus?` asserts a **sticky `UNSPEC_RANGE` flag** that remains set while the *commanded* magnitude is in the band; (iii) firmware records in the log that the cross-check of §11 item 3 is inoperative for the duration |
| `\|V\| ≥ 20.0 V` | normal |

**Ramp transit is exempt.** The advisory fires on the **commanded** set-point, not on
intermediate ramp steps, so a ramp from 0 to 500 V produces no advisory and a command of
5.0 V produces exactly one.

**Additional firmware rules in the band, all of them consequences of §11 item 3:**
- **`MEASure:VOLTage?` is the only readback that means anything.** `MODule:VMON?` must still
  answer, but the sticky flag tells the host why not to believe it.
- **Do not trip on monitor disagreement below 20 V.** The threshold stays at 20 V absolute;
  no special case is needed, but the *reason* must be in the code comment or a future reader
  will "fix" it.
- **"Discharged" is never inferred from VMON or from the commanded set-point.** It is
  measured by the independent monitor, whose 1.58 V accuracy is what makes the 60 V / 5 s
  criterion (NUM-15, `[unverified-primary]`) checkable at all.

### 11.2 Protocol delta

Add to `INTERFACES.md` §3.2 / ARCH-33's device-specific code block:

```
+110  "Setpoint below specified range (2%*Vnom): output is UNSPECIFIED"   (advisory, non-fatal)
```

and to `STATus?`: the `UNSPEC_RANGE` flag. Per G0-A4 both are **per output**.

---

## 12. Design rules for the schematic generator

Each is executable at the netlist level. Rules 1–7 amend or extend
`CONTROL_ARCHITECTURE.md` §6.4; the amendments are named as such.

| # | Rule | Source |
|---|---|---|
| **SP-1** | **Total un-nulled series resistance from `U4` to the `VSET` pin ≤ 0.2 Ω**, excluding resistance enclosed by a Kelvin loop whose sense point is the pin. ⚠ **AMENDS ARCH-04's 10 Ω** — see §3.5 | §3.5 |
| **SP-2** | The `VSET` pull-down is **2 elements in parallel** and its pads are the **last elements before pin 2**, sharing the pin-2 land | §3.4, F2 |
| **SP-3** | No net downstream of `U4`'s output may touch `+3V3` or `+5V`. `U4`'s V+ net is `VCLAMP`; `VCLAMP` has **exactly one driver**, `U3`. ⚠ **restates design rule 8 in three parts** — §3.2.1 | §3.2.1 |
| **SP-4** | `U5`'s reference is a **different part number from a different family** than `U2`. Assert they are not the same MPN | §4.2 |
| **SP-5** | `U5` senses `VCLAMP` **at `U4`'s V+ pin**, not at `U3`'s output | §4.2, F6 |
| **SP-6** | Every safe-state pull element is **duplicated** (pull-down at the pin; `U4` input pull-down; `U5` permissive pull-down). **Function-only pulls (`U6` `SYNC`/`SCLK`/`DIN` idle) are explicitly exempt** and must be annotated as such so nobody "fixes" them | ARCH-18, §7 |
| **SP-7** | `Q_SHUNT`'s gate net taps `/ON_x` **at the module-end pull-up**, not at the driver | §3.6 |
| **SP-8** | Both `U3` and `U4` carry a **local feedback resistor** in addition to the remote sense, `R_local ≥ 1000 × R_force` | §3.5, F11, F12 |
| **SP-9** | `VCLAMP` is **star-routed** from `U3`'s Kelvin point; no daisy-chain between the two `VSET` buffers | §3.1.2 |
| **SP-10** | No DAC `SYNC`/`SCLK`/`DIN` on any ESP32 strapping pin | ARCH design rule 2, §7 |
| **SP-11** | A **test point and a link on `VCLAMP`**, so bench test T4 is performable without a bodge | §8.3 |
| **SP-12** | `R_local` and its sense trace are a **matched pair in the pre-fab checklist** (F12 is latent) | F12 |
| **SP-13** | The set-path analog region is a **3.3 V keep-out**: no `+3V3` copper within the HV-adjacent set-path zone | §3.2.1, F7 |

---

## 13. What is NOT settled, carried forward flagged

**Do not read this document as closing any of these.**

| # | Open item | Where it lives |
|---|---|---|
| O-A | **`R_pullup` (the internal 10 kΩ) has no published tolerance and the 60 V criterion depends on it inversely.** Breaks at 7.83 kΩ, −21.7 % | ⬛ **NEW — add to `G0_QUESTIONS.md` O-2** as a fifth measurable module parameter |
| O-B | **The DAC8552's power-on-reset state is `[recalled]`.** A part that powers up above zero-scale is disqualified | G1 datasheet read; §3.2 gate 2 |
| O-C | **DAC digital `VIH` at `VDD` = 5 V is `[recalled]` as 0.7·VDD.** `U6` exists because of it and may be deletable | G1 datasheet read; §3.2 gate 3 |
| O-D | **No op-amp has been selected.** §3.3's table is a requirement set; every candidate is `[recalled]` `[unverified-MPN]`. **Output current at a 2.5 V supply is the parameter that disqualifies most precision amps** | G1 |
| O-E | **REF5025 output-capacitor stability range** — some series references oscillate into particular capacitances | G1 datasheet read |
| O-F | **`U4`'s stability into 100 nF at the pin** is the one place a simulation is genuinely required | before layout |
| O-G | **`ARCH-04` (10 Ω) and `ARCH-03` (12-bit set path) both need amending**, per §3.5 and §6.2. Flagged, not edited — those rows are `frozen` and changing them is a gate | `DECISIONS.md` |
| O-H | **The ±950 V rating interacts with Q3, which was not answered.** If ±1000 V at the terminal is required, the module class is wrong | `G0_QUESTIONS.md` O-3 |
| O-I | **F19 (`U5` stuck HIGH) is undetectable in service.** Accepted, with layer 3 behind it. If that is not acceptable, `U5` needs a self-test path — and any such path is a firmware-reachable input to a safety element, which is why none is proposed | §5.1 |
| O-J | **F2 and F7 are un-preventable by the set path** and rest on layout plus layer 3 | §5.1 |
| O-K | Every MPN here is **`[unverified-MPN]`** until Phase 6. Session 1 recorded a distributor deep-link returning a confident spec report for an entirely different product | `SCOPE.md` S-6 |
| O-L | The **60 V / 5 s** touch-safe threshold used throughout §3.4 is `[recalled]` `[unverified-primary]` (NUM-15). **If a primary standard gives a different number, the pull-down value changes** | `G0_QUESTIONS.md` O-1 |

---

## 14. Summary — the five things a reviewer should check first

1. **The clamp is a rail, not a component in the signal path.** `VCLAMP` = 2.500 V is
   `U4`'s V+; an RRO stage cannot exceed its own rail. Over-range residual **+0.061 %**.
2. **The dominant hazard is the clamp failing open**, because the internal 10 kΩ then
   commands 1000 V. Answered by a **duplicated 500 Ω pull-down at the pin** → **47.6 V**,
   and the pull-down must be the last element before pin 2.
3. **The rail clamp cannot see the rail itself rising.** A **window comparator on an
   independent reference** covers it, capping a reference fault at **1021 V** instead of
   1320 or 2000 V. Behind both, the **latched 105 % OVP on the independent monitor** is the
   only layer indifferent to the fault mechanism.
4. **The rail force amplifier is mandatory** — 12.06 mA against the REF5025's 10 mA. The
   probe asserts this and will fire if the premise ever changes back.
5. **Below 20 V the instrument is unspecified and says so**: accepted, advisory `+110`,
   sticky `UNSPEC_RANGE`, and the two-monitor cross-check is documented as inoperative there
   rather than quietly relied upon.

*Ground truth: iseg APS technical documentation v2.5, 2024-08-20 (Tables 1–4, Figures 1–2),
via `docs/PART_iseg_APS.md`; the frozen G0 answers of 2026-07-23; and
`docs/studies/setpoint_path_numbers.py` for every computed value. **Nothing in this document
has been measured on a physical module, simulated, or built.***
