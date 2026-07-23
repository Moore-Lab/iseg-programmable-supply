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
> This file quotes *"800 VDC, PD2, mat. group IIIa → ~4.0 mm creepage functional"* and an *"≥ 8 mm keep-out"* around the live module case. The MG IIIa reading at 800 V in the probe's transcription is **8.000 mm**, twice this file's 4.0 mm. The topology is REJECTED by G0-A1 regardless.
>
> **The single live source for every clearance/creepage number is
> `docs/NUMBERS_PROBE.md`, generated from `hardware/hvctl/numbers_probe.py`.**
> At the frozen part (AP010504, Vnom = 1000 V) the live values are
> **7.5 mm** HV-to-anything and **15.0 mm** HV_POS↔HV_NEG (and HV_OUT_A↔HV_OUT_B),
> every one of them tagged **`[unverified-primary]`** pending a human reading a primary copy
> of IPC-2221B Table 6-1. Do not quote this file's figure anywhere.

# Combiner topology study: series stack, driven midpoint

**Candidate owner:** Phase-1 topology probe, G0
**Date:** 2026-07-23
**Primary source:** iseg APS series technical documentation v2.5, 2024-08-20
(`references/iseg_manual_APS_en.pdf`), re-read this session with `fitz` under `PY_KICAD`.
**Verdict: 4 / 10 — CONDITIONAL ELIMINATE at G0.** Fails invariant (a) as written, and its
usable load current is ~5 µA. Survives only if the human amends invariant (a) *and* confirms the
load is capacitive / sub-10 µA.

---

## 0. What I re-verified myself, and what it changed

Everything in §0 is `[verified-artifact]` — extracted from the PDF this session, not recalled.

### 0.1 There is no HV return pin. The HV output is referenced to the module's own GND.

Table 4 (manual p.9) lists seven pins: `+VIN, VSET, GND(3/7), /ON, VMON, HV`. There is **no
separate HV return**. Note under the table: *"Case is connected to GND"*. Therefore the HV
output current returns through pins 3/7, and the metal box is at GND potential.

**Consequence, and it is the single most important fact in this study:** any topology that puts a
module's GND at a non-zero potential puts its *steel case* there too, and puts its entire
low-voltage domain there with it.

### 0.2 Figure 2 (Control principle, manual p.9) — internals not in the briefing packet

I rendered Figure 2 at 12× (it is vector art; `get_text()` returns nothing useful). Reading the
schematic inside the dashed "APS" boundary:

```
                    (to internal control loop)
                             |
   VMON o----[20k]---x       x---- +VIN o
                             |
                          [10k]      (REF)  2.5V / 5V
                             |         |
   VSET o---------------+----+         |
                        |              |
                     [100k]            |
                        |              |
                        +-----+--------+----- ... to internal control node
                              |        |
                       /ON o->|SW      |
                              |      [1uF]
                             GND      GND
```

Four facts fall out of this, none of which are in the brief's extracted ground truth:

1. **`VMON` is a 20 kΩ source.** The monitor output has a 20 kΩ series resistor to the pin. Any
   ADC or divider hung on `VMON` loads it directly. A 100 k:100 k divider on `VMON` would read
   low by 20 k/(20 k + 50 k) ≈ 29 %. **`VMON` must be buffered by a unity-gain op-amp with
   sub-nA bias current** (OPA2333 / MCP6V51 class), or sampled by an ADC that tolerates a 20 kΩ
   source. The ESP32's own SAR ADC does not, comfortably.
2. **The 10 kΩ pull-up to `Vref` is real and is on the `VSET` pin.** This confirms the Rset
   formula: `Vset = Vref·Rset/(Rset+10k)` → `Rset = 10k·Vout/(Vnom−Vout)`. It also confirms that
   **an open `VSET` node commands full scale**, and that a `VSET` driver must sink up to
   `Vref/10k` = 250 µA (0.5 W family) / 500 µA (1 W family).
3. **`Vref` is not brought out to a pin.** You cannot set `VSET` ratiometrically against the
   module's own reference, so the module's ±1 % `Vref` tolerance and your DAC reference tolerance
   *add*. **Workaround worth having:** tri-state the `VSET` driver and measure the `VSET` pin —
   with no DC path into the internal 100 kΩ, the open-circuit pin voltage *is* `Vref`. One-time
   per-module calibration, free.
4. **`/ON` asserts by shorting an internal 1 µF node to GND, and `VSET` reaches that node through
   100 kΩ.** So the module has an intrinsic set-node time constant of
   **τ_set = 100 kΩ × 1 µF = 100 ms**. This is the hard floor on how fast any APS-based supply can
   slew, in *any* topology. Full-scale settle to 1 % = 4.6 τ = **460 ms**; to 0.1 % = 6.9 τ = 690 ms.
   Conversely, asserting `/ON` HIGH dumps the internal set node ~instantly, so the module
   *commands* zero immediately — but nothing in Figure 2 pulls the **HV output** down. The HV node
   decays only through the module's internal bleeder (unspecified) and the external load. **This
   is exactly why invariant (b) exists.**

### 0.3 What the datasheet is silent about

No isolation voltage. No dielectric-strength figure. No common-mode rating for GND or case. No
maximum reverse voltage on the HV pin. No internal bleeder / output-divider resistance. No output
capacitance. No slew rate (τ_set above is inferred from Figure 2, not stated).

**Absence of a rating is not permission.** This matters enormously below.

---

## 1. The topology, drawn

"Series stack with a driven midpoint" admits two distinct circuits. They are not variations of
each other; one works and one does not. I analyse both because the brief's phrasing does not
choose, and because the one that does not work fails for a reason that must be on the record.

### 1.1 Variant A — true anti-series stack (one module floats)

```
   system GND (0 V)
        |
    [ MN  GND ]                     MN = negative module, e.g. AP008125N12
    [ MN  HV  ]---- node C = -Vn
                        |
                   [ MP  GND ]      <-- MP's ENTIRE LV domain and CASE sit at node C
                   [ MP  HV  ]---- OUT = Vp - Vn
                                        |
                                      load
                                        |
                                   system GND
```

`OUT = Vp − Vn`. Set `Vp = Vn` → 0 V. `Vp > Vn` → positive. `Vp < Vn` → negative. Continuous
through zero, no switching element anywhere. This is what the topology *promises*.

### 1.2 Variant B — series string through ballast resistors, output = midpoint

```
   [ MP GND ]--- system GND        MP = positive module
   [ MP HV  ]--- +Vp ----[ R1 ]----+---- OUT
                                   |
                                 [Cout]      [Rbleed]
                                   |            |
   [ MN GND ]--- system GND        |          system GND
   [ MN HV  ]--- -Vn ----[ R2 ]----+
```

Both module GNDs and both cases are at system ground. The two modules are still genuinely in
series — DC current circulates MP-HV → R1 → OUT → R2 → MN-HV → MN-GND → ground → MP-GND — and
the output *is* the driven midpoint of that series string. With `R1 = R2 = R`:

```
OUT   = (Vp − Vn) / 2
Z_out = R1 ∥ R2 = R/2
I_std = (Vp + Vn) / (R1 + R2)          standing current through the string
```

**Variant B is the real candidate.** Everything from §3 onward is variant B unless stated.

---

## 2. Variant A is dead. Here is the proof, in three lines.

In an anti-series string the **load current is common to both modules**, and the two EMFs
**oppose** (that is what produces `Vp − Vn`). Therefore, for any non-zero load current, the
current direction is forward for exactly one module and reverse for the other. Always. There is
no operating point where both are forward-biased.

Concretely, with `OUT > 0` and a resistive load, conventional current leaves `OUT`, meaning it
flows internally GND→HV inside MP (forward for a positive module ✔) *and* GND→HV inside MN
(reverse for a negative module ✘, whose normal current enters the HV pin).

An APS is a patented resonance converter with a rectifier/multiplier output. **It cannot sink
reverse current.** The only reverse path is the reverse-biased module's internal bleeder — an
impedance the datasheet does not publish. Estimating from ordinary HV-module practice (a monitor
divider drawing 1–5 % of `Inom`: 800 V / 20 µA = 40 MΩ), variant A's output impedance is
**10–100 MΩ, unspecified by the manufacturer.** 1 µA of load moves the output by 10–100 V.

Even into a *purely capacitive* load, where DC current is zero, slewing the output negative
requires transient reverse current through one module. So variant A is not rescued by choosing a
capacitive load; it is only rescued at exact DC equilibrium, which is not an operating mode.

**Corollary worth stating for the record:** a P-module and an N-module can be stacked
*series-aiding* (MP HV → MN HV, output at MN GND), which works perfectly and gives a **unipolar
0…2·Vnom** supply with both modules forward-biased. Series-*opposing* is the bipolar case and is
the broken one. There is no third arrangement.

### 2.1 What variant A would have cost, had it worked

Recorded because the brief asked, and because it is the number that kills variant A a second time.

| Item | Requirement | Reality | Cost |
|---|---|---|---|
| Isolated DC-DC for MP | 12 V / 3 W, **≥800 VDC continuous working** | The trap: catalogue parts quote a **1-second test** voltage (1.5/3/5 kVDC) and either omit continuous working voltage or state 250–354 VDC. Traco THM 3WI: 5 kVAC test, ~354 VDC continuous — **insufficient**. Needs a reinforced/HV family or a custom bobbin. | $25–60, lead-time risk |
| Digital isolator for `/ON` | VIOWM ≥ 800 Vpk | Basic-rated ISO7721/Si8621 are ~566 Vpk VIOWM — **insufficient**. Reinforced part required. | $3–5 |
| `VSET` / `VMON` across barrier | 12-bit analog, both directions | Cleanest is a floating MCU (RP2040/ATtiny + LDO) with local DAC+ADC, isolated SPI/UART | $8–12 |
| Creepage / clearance | 800 VDC, PD2, mat. group IIIa | ~4.0 mm creepage functional; but MP's **40 × 16 × 11 mm steel case is a touchable conductor at up to 800 V** → treat as hazardous-live: enclosure mandatory, ≥8 mm keep-out, no ground pour under or beside it, case unusable as shield or heat path | board area ×2 |
| **Total adder** | | | **$45–80 + an isolation-coordination review** |

### 2.2 The question for iseg (do not assume the answer)

> *"Is the APS GND / case permitted to sit at a continuous DC potential of up to ±Vnom with respect
> to the mounting reference? If so, what is the maximum continuous common-mode voltage, what is the
> dielectric withstand of the internal HV section referred to GND, and what creepage is required
> from the case?"*

The v2.5 manual contains **no** isolation voltage, **no** common-mode rating, **no**
dielectric-strength figure, and no separate HV-return pin. My expectation is that the answer is
"the APS is designed for a grounded GND; we do not qualify common-mode operation" — but that is a
prediction, not a fact, and it must not be assumed either way. Variant A cannot be considered
without a written answer.

---

## 3. Variant B — the numbers

### 3.1 The range penalty is the headline

`OUT = (Vp − Vn)/2`. To reach `OUT = +400 V` you need `Vp − Vn = 800 V`. **The symmetric resistive
midpoint costs you a factor of two in voltage.** ±400 V out requires **800 V** modules
(`AP008125P12` / `AP008125N12`, 800 V, 1.2 mA, 12 V, 1 W), not 400 V modules.

### 3.2 Control law: constant-sum

Hold `Vp + Vn = 800 V` constant and move the midpoint:

```
Vp = 400 + V_cmd        Vn = 400 − V_cmd        OUT = V_cmd,  V_cmd ∈ [−400, +400]
```

Two properties fall out that are better than they look:

* **The standing current is constant** at `800 V / (R1+R2)` regardless of `V_cmd`. No
  load-dependent thermal drift in the ballast resistors.
* **The voltage across each ballast resistor is constant** at `(Vp+Vn)/2 = 400 V`, always.
  Simplifies derating.
* **Near zero, both modules sit at 400 V** — comfortably inside iseg's guaranteed envelope
  (specs hold only for `2 %·Vnom < Vout ≤ Vnom`, i.e. 16 V < Vout ≤ 800 V). The scheme degrades at
  the *extremes*, not at the zero crossing, which is exactly the right way round. Clamp the
  command to **±380 V** so each rail keeps a 20 V floor and neither module ever leaves spec.

### 3.3 Sizing the ballast

Budget the standing current at ≤ 25 % of `Inom` = 300 µA:

```
R1 + R2 ≥ 800 V / 300 µA = 2.67 MΩ    →    choose R1 = R2 = 1.5 MΩ
I_std   = 800 V / 3.0 MΩ = 267 µA     = 22 % of Inom (1.2 mA)     ✔
P_each  = 400 V × 267 µA = 107 mW     of a 1 W part                ✔
Z_out   = 750 kΩ
```

### 3.4 Load regulation — this is what disqualifies the topology for most loads

| Load current | Output droop | As % of 400 V |
|---|---|---|
| 1 µA | 0.75 V | 0.19 % |
| **5.3 µA** | **4.0 V** | **1.0 %** |
| 10 µA | 7.5 V | 1.9 % |
| 50 µA | 37.5 V | 9.4 % |
| 267 µA | 200 V | 50 % — **and MN's current has reached zero; beyond this the topology stops functioning entirely** |

**Usable spec: ±380 V at ≲5 µA for 1 % regulation; hard ceiling ~50 µA.**

Compare a rail-select (HV relay) combiner with 400 V / 2.5 mA modules: **±400 V at 2.5 mA**, `Z_out`
< 1 kΩ. Variant B delivers half the voltage per module-volt and **1/470th of the current.**

**This single number is the decision.** If the load is deflection plates, an electrostatic lens,
ion optics, a quadrupole DC bias, or a Kelvin probe — i.e. capacitive, sub-µA — variant B is
excellent. If the load is a PMT divider, a detector bias, or anything drawing >10 µA, it is
disqualified outright. **The load-current spec is an open G0 item in the brief and must be closed
before this topology can be scored.**

### 3.5 Through-zero: the arithmetic

| Quantity | Value | Source |
|---|---|---|
| Dead-band at the zero crossing | **0 ms** | topology — `OUT` is an affine function of two continuous rails |
| Voltage discontinuity at crossing | **0 V** | ditto; monotonic by construction |
| Intrinsic slew τ | **100 ms** | 100 kΩ × 1 µF, Figure 2 `[verified-artifact]` |
| Full-scale (−400→+400) settle to 1 % | **460 ms** | 4.6 τ |
| Output-node RC (750 kΩ × 10 nF) | 7.5 ms | negligible vs τ_set |
| **Open-loop zero-point offset** | **±8 V worst case, ±5.7 V RSS** | ±1 %·Vnom per module (±8 V at 800 V); `OUT` error = (ε_p − ε_n)/2 |
| Closed-loop trim bandwidth | ≤1.6 Hz | 10× phase margin around a 100 ms plant |
| **Realistic settle to a calibrated ±0.1 V zero** | **1–2 s** | |

So: **the through-zero is perfect in *shape* and mediocre in *speed*, and the zero point is not
free.** The output passes through zero with no glitch, no dead-band, and no discontinuity — but
open-loop it passes through *±8 V*, not zero. A clean zero requires closing the loop against the
independent output monitor (§4.3), which is a ~1 s settle. Anyone selling this topology on "true
through-zero" must be made to say that ±8 V out loud.

### 3.6 Ripple — a genuine, unique advantage

Per module: ≤10 mVpp typ / ≤30 mVpp max (f > 10 Hz) `[verified-artifact, Table 1]`. Uncorrelated
between two modules, halved by the divider:

```
OUT ripple = sqrt(10² + 10²)/2 = 7.1 mVpp typ      sqrt(30² + 30²)/2 = 21 mVpp max
```

But `Z_out = 750 kΩ` lets you add a 10 nF / 1 kV C0G-or-film output cap for a **21 Hz pole**:

| Frequency | Attenuation | Residual (typ) |
|---|---|---|
| 10 Hz | ×1.0 | 7.1 mVpp |
| 100 Hz | ×0.21 | 1.5 mVpp |
| 2 kHz | ×0.0105 | **0.075 mVpp** |

**No other combiner topology can do this**, because they all need a low output impedance and
therefore cannot afford the pole. Above ~100 Hz the resistive midpoint is quieter than either
module alone. Stored energy at 400 V: ½ · 10 nF · 400² = **0.80 mJ**, charge 4 µC — both far below
the IEC stored-energy (350 mJ) and charge (45 µC) hazard thresholds.

### 3.7 Touch current — the second genuine, unique advantage

The ballast resistors are in series with *any* path from the modules to the output terminal.
A person bridging `OUT` to ground sees a source impedance of ≥750 kΩ:

```
I_touch,max = 400 V / 750 kΩ = 533 µA
```

Above the ~0.5 mA perception threshold, **below the ~5 mA let-go threshold and far below the
~30 mA fibrillation threshold.** Compare the rail-select topology, where the terminal is hard-wired
to a module capable of 1.5 · Inom = 3.75 mA — squarely in the let-go range.

**This is the only combiner topology whose output is inherently current-limited below let-go by a
passive element that cannot fail short.** Thick-film HV resistors fail open, not short. If the
brief's safety envelope prioritises touch safety over load current, this changes the ranking.

### 3.8 Reverse-voltage exposure of the idle module

**In normal operation: none.** With the constant-sum law and a 20 V floor, MP's HV pin is actively
held at +20…+800 V and MN's at −20…−800 V. Neither is ever driven through zero.

**On a single fault (a module goes high-Z — dead, `/ON` stuck HIGH, or `+VIN` open):** the surviving
module drags the dead one's HV pin through the 1.5 MΩ ballast. With an assumed 20 MΩ internal
bleeder the dead module's HV pin reaches `−400 × 20/(20+1.5) = −372 V` — nearly full reverse
across its multiplier stack and smoothing capacitors, which are unipolar parts.

**Fix — one HV clamp diode per module, to its own GND** (cathode at MP's HV pin, anode to GND;
mirrored for MN). Note this is a **shunt clamp, not a series blocker**, so:

* no forward drop in the signal path → **no offset penalty** (a series HV blocker would add
  8–12 V of `Vf` at 267 µA, and a *varying* offset near the rail floors);
* in normal operation it sits reverse-biased at up to 800 V, so its leakage adds to the module's
  load. Arithmetic: a 5 nA-class HV diode contributes 0.002 % of `I_std`; **a 1N4007 stack
  contributes up to 5 µA = 1.9 % of `I_std` — do not use 1N4007s here**;
* on fault it carries 400 V / 1.5 MΩ = 267 µA. Trivial.

---

## 4. The three non-negotiable invariants

### 4.1 Invariant (a) — hardware interlock making both-enabled UNREACHABLE → **FAIL**

**Both modules are always enabled. That is the topology.** There is no state in which one is
disabled and the other is driving. The invariant as written is not merely violated; its negation
is the sole operating mode.

I will argue both sides, because the honest answer is not "the invariant is silly."

**The case that (a) is trivially satisfied in spirit:** the hazard an interlock guards against is a
*fight* — two stiff HV sources of opposite polarity contending for the same low-impedance node.
That fight is impossible here: 3.0 MΩ of passive ballast always separates them, and thick-film HV
resistors fail open. The elimination is *structural*, which is stronger than an interlock, because
an interlock is an active mechanism that can fail and a resistor cannot fail short.

**The case that (a) is fundamentally violated, which I find decisive:** invariant (a) is a proxy
for *"no single fault produces an uncommanded, wrong-polarity, full-magnitude output."* Variant B
fails that proxy **harder than any switched topology**:

> With the output commanded to 0 V (`Vp = Vn = 400 V`), if MP dies — a fault entirely within the
> *positive* channel — the output slews to `(0 − 400)/2 = **−200 V**`. Kill MP while commanding
> +380 V and the output goes to −10 V, through zero, uncommanded.
>
> In a rail-select topology, a dead module gives you **0 V**.

**In this topology, losing one module does not give you zero — it gives you half-scale of the
opposite polarity.** That is a strictly worse safety posture, arrived at by removing the very
mechanism invariant (a) demands.

**Declaration: this topology structurally cannot satisfy invariant (a). It requires the human to
amend the invariant, and it requires a compensating hardware mechanism (§4.1.1) that is *not* an
interlock.** Per the brief's own instruction that an unsatisfiable invariant is a G0 elimination,
this is a G0 elimination unless amended.

#### 4.1.1 The compensating mechanism, if (a) is amended

Replace "both-enabled unreachable" with **"output magnitude and polarity bounded in hardware."**
Concretely: a **window comparator on the independent monitor tap** (§4.3) that de-energises the
shunt dump relay when `|OUT|` exceeds a threshold *or* when `OUT` disagrees with the commanded
setpoint by more than a window. Two comparators (LM393 class) plus a resistor network, ~$3.

The window (not just over-voltage) is essential: an **open top resistor in the monitor divider
makes the tap read mid-rail, i.e. "0 V output," which a bare over-voltage trip cannot see** and
which would let firmware ramp `VSET` up chasing a phantom zero. The comparison must be against the
setpoint, both directions.

Latency to safe: comparator ~1 µs + relay release ~0.5 ms + RC dump 7.2 ms → **<10 ms.**

### 4.2 Invariant (b) — defined discharge on changeover and on disable → **PASS, and unusually cleanly**

**On changeover: there is no changeover.** No polarity transfer event exists. `dV/dt` is bounded by
the module's own 100 ms τ. This is the topology's strongest claim and it is real.

**On disable:** assert both `/ON` HIGH → both internal set nodes are shorted to GND (Figure 2), both
rails command 0. `OUT` then discharges through `R1 ∥ R2 ∥ R_bleed`.

**The mechanism of record is a permanent passive bleed with no active element in it:**

```
R_bleed = 20 MΩ  (4 × 5 MΩ HV chip resistors in series), OUT → system GND, always present
```

| Path | τ | to <50 V from 400 V | to <1 V |
|---|---|---|---|
| Rails alive, normal (`R1∥R2∥R_bleed` = 723 kΩ, C = 10 nF) | 7.2 ms | 15 ms | 43 ms |
| `R_bleed` alone (both ballasts open — implausible) | 200 ms | 420 ms | 1.2 s |

Cost: `R_bleed` divides against `Z_out = 750 kΩ` → gain 20/(20.75) = **0.9639, a −3.6 % gain error**,
calibrated out, plus 400 V/20 MΩ = 20 µA of extra standing load.

**Why this is better than every alternative:** the bleed is a passive resistor that is *always*
connected. It has no enable, no coil, no gate, no firmware, and no failure mode other than open —
and it is built from four series parts so a single open still leaves 15 MΩ of bleed. It satisfies
(b) unconditionally, with the ESP32 unpowered, with the 3.3 V rail dead, with everything on fire.

An optional relay shunt for a *fast* dump (§4.1.1) is additive, not load-bearing. Note that even
that relay is a **shunt**, not a series element: stuck-closed clamps the output to ~0 V through
1 MΩ, which is fail-safe. The topology's "no switch in the HV path" claim survives intact.

### 4.3 Invariant (c) — independent output monitoring → **PASS** (but non-discriminating)

Independent of `VMON` entirely: an HV divider on the actual output node.

```
R_top = 500 MΩ (5 × 100 MΩ HV chip, series)     I at 400 V = 0.80 µA  (0.3 % of I_std)
R_bot = 1.253 MΩ, returned to a buffered +1.65 V reference, not to GND
ratio = 400 : 1
tap   = 1.65 V + OUT/400  →  0.65 V @ −400 V  …  2.65 V @ +400 V
ADC   = ADS1115 (16-bit, I²C, differential, internal PGA)
        + 1 kΩ series and a BAV199 clamp to the ADC rails
```

The mid-reference return is required because the ADS1115 inputs must stay ≥ GND − 0.3 V and the
output is bipolar. Do **not** use the ESP32's own SAR ADC for the safety monitor.

Loading arithmetic: 500 MΩ against `Z_out = 750 kΩ` → 0.15 % gain error. Fine, and calibratable.

Caveat: this passes for *every* candidate topology, so it does not discriminate. The only
topology-specific note is that the divider must handle **both polarities**, which rules out
single-ended level shifting to ground.

---

## 5. Single-fault analysis

`/ON` is **active-LOW**: floating `/ON` = HV **ON** `[verified-artifact, Table 4]`. Every fail-safe
below is built around that.

### 5.0 Two prerequisites that are not optional

1. **`/ON` pulled HIGH by default.** 2 × 20 kΩ **in parallel** to +3.3 V (redundant — a single
   pull-up is itself a single point of failure in the unsafe direction, and the second resistor
   costs $0.02), driven LOW by an open-drain GPIO. 3.3 V − 10 % = 2.97 V > the 2.5 V threshold ✔,
   and < the 5.5 V maximum ✔. ESP32 in reset → GPIO Hi-Z → `/ON` HIGH → HV OFF.
2. **`+VIN` interlocked to the 3.3 V rail — this is the fail-safe of record, not `/ON`.**
   P-FET in the modules' 12 V feed, gate pulled to 12 V by 100 kΩ (OFF), pulled down by a 2N7002
   whose gate is driven by a GPIO through 10 kΩ to GND. No 3.3 V → 2N7002 off → P-FET off → modules
   unpowered. No GPIO drive → same. This covers the `/ON`-pull-up-fails case, the DAC-Hi-Z case,
   and the ESP32-unpowered-while-12 V-alive case in one mechanism.

**The trap this closes:** a tri-stated DAC output leaves `VSET` open, and the internal 10 kΩ pull-up
to `Vref` then commands **full scale**. Every "safe" Hi-Z default in the LV domain is a full-scale
HV command. Only removing `+VIN` is genuinely safe.

### 5.1 Fault table

| Element | Failure | Output does what | Severity |
|---|---|---|---|
| **MP (positive module)** | stuck OFF / dead / high-Z | `OUT → −Vn/2`, i.e. **uncommanded −200 V from a commanded 0 V**; MP's HV pin reverse-driven to −372 V (clamp diode required) | **Critical** — polarity reversal from a single fault, unique to this topology |
| **MP** | stuck ON at full scale | `Vp = 800` → `OUT → +400 V` uncommanded, still inside the normal envelope (no over-range) | High |
| **MN** | stuck OFF | `OUT → +Vp/2` = **+200 V uncommanded** | Critical, mirror of above |
| **MN** | stuck ON | `OUT → −400 V` uncommanded | High |
| **`VSET` line open** (either) | — | internal 10 kΩ pulls to `Vref` → that module goes to `Vnom` → `OUT → ±400 V` | High |
| **`VSET` DAC railed high** | — | clamped by construction (§5.2): cannot exceed `Vref` → `Vout ≤ Vnom`, no over-range | Mitigated |
| **`/ON` line open** | — | `/ON` floats → **HV ON** at whatever `VSET` says | Mitigated by redundant pull-ups + `+VIN` interlock |
| **`/ON` pull-up opens** (both) | — | `/ON` floats → HV ON | Mitigated by `+VIN` interlock |
| **`+VIN` open** (either) | — | that module dies → half-scale opposite polarity (row 1) | Critical |
| **GND pin 3 *or* 7 open** | — | the other GND carries it — **pins 3 and 7 are genuinely redundant** ✔ | Low |
| **GND pins 3 *and* 7 both open** | — | that module's reference floats; its HV return is broken; **its metal case, a touchable conductor, floats to an undefined HV potential** | **Critical.** Layout mitigation only: generous pads on both GND pins, redundant via clusters, and treat the case as bonded-or-hazardous in the mechanical review |
| **`VMON` open** | — | reads 0 while HV is up → firmware could chase a phantom zero upward | Mitigated: **never close a loop on `VMON`**; the independent monitor is the control and safety feedback |
| **Monitor divider `R_top` open** | — | tap → 1.65 V = "0 V" → bare OV trip is blind | Mitigated: **window** comparator vs setpoint, not bare OV (§4.1.1) |
| **Monitor divider `R_bot` open** | — | tap → full HV into the ADC | Mitigated: 1 kΩ + BAV199 clamp; window trip fires |
| **Ballast R1 or R2 open** | — | `OUT` pulled to the surviving rail through 1.5 MΩ, but `R_bleed` (20 MΩ) holds it at 1.5/21.5 → ~7 % of that rail. Fails toward zero ✔ | Low |
| **Ballast R1 or R2 short** | — | thick-film HV chips fail open, not short; if forced, `OUT` = that rail directly, 800 V, and `Z_out` collapses | Low probability, high consequence |
| **`R_bleed` open** (one of 4) | — | 15 MΩ remains; discharge τ 200→150 ms | Low |
| **ADS1115 / I²C dead** | — | no independent readback; firmware blind | Mitigated: hardware window trip is analog and does not go through the ADC |
| **ESP32 in reset** | GPIOs Hi-Z | `/ON` pulled HIGH → OFF; `+VIN` P-FET off → modules unpowered; `OUT` bleeds to <1 V in 43 ms | **Safe** ✔ |
| **ESP32 unpowered, 12 V rail up** | — | `+VIN` interlock keyed to 3.3 V → P-FET off → modules unpowered | **Safe** ✔ |
| **3.3 V rail dies mid-run, 12 V alive** | — | 2N7002 gate falls → P-FET off → modules unpowered | **Safe** ✔ |
| **12 V rail dies, 3.3 V alive** | — | modules unpowered, `OUT` bleeds | Safe ✔ |

### 5.2 The `VSET` over-range clamp (a hardware requirement, per the datasheet)

The manual is unusually emphatic: *"Attention! Output voltage is internally not limited! At
Vset > 5 V → Vout > Vnom is possible! Do not use Vset > 5 V!"* `[verified-artifact, Table 1]`.

**Clamp by construction, not by diode:** buffer each DAC output with a rail-to-rail op-amp whose
**positive supply *is* a 5.000 V precision reference** (REF5050 class, sourcing the 500 µA the
internal 10 kΩ pull-up demands). The buffer physically cannot output more than 5.000 V. The
module's own `Vref` is 5 V ±1 % → ≥4.95 V, so a 5.000 V clamp guarantees `Vout ≤ Vnom · (5.000/4.95)`
= `Vnom · 1.010` worst case — i.e. at most 1 % over, which is inside the stated adjustment accuracy
anyway. One part does the job; a Schottky clamp is belt-and-braces, not the mechanism.

Note the pleasing asymmetry: **an open `VSET` gives exactly `Vref` → exactly `Vnom`, never more.**
The over-range hazard exists only for an *active* driver going above `Vref`, and the supply-rail
clamp removes it.

---

## 6. Parts and cost

**Evidence discipline on MPNs:** I opened live DigiKey product pages for two parts and read the
stock and price from them; those are marked `[distributor-verified 2026-07-23]`. Search-result
snippets that quoted DigiKey but which I did not open directly are marked `[snippet]`. Everything
else is `[unverified-MPN]` and must be checked before BOM release.

| Function | Part | Status |
|---|---|---|
| Independent monitor ADC | **ADS1115IDGSR** (TI), 10-MSOP, 2–5.5 V, 16-bit I²C. DigiKey 296-38849-1-ND, **45,872 in stock, $5.28 @1 / $4.02 @10** | `[distributor-verified 2026-07-23]` — I opened digikey.com/en/products/detail/texas-instruments/ADS1115IDGSR/2231567 |
| HV monitor divider top (5×100 MΩ) | **Vishay CRHV2512AF50M0FKE5** family (2512, 1 W, ±1 %, ±100 ppm/°C, series rated to 3 kV). The 50 MΩ value: DigiKey **0 in stock**, $4.13 @1 / ~$3.07 @10 | `[distributor-verified 2026-07-23]` — I opened digikey.com/en/products/detail/vishay-dale/CRHV2512AF50M0FKE5/2499027. **Stock risk flagged: zero on hand.** The 100 MΩ value must be checked separately. |
| HV ballast R1/R2, 1.5 MΩ | **Vishay CRHV2512AF-series** (2512, 1 W, 3 kV max working per series datasheet). Exact 1.5 MΩ ordering P/N **not confirmed in stock** | `[unverified-MPN]` — searched; the 1.5 MΩ value did not surface on a distributor page |
| HV ballast alternate | **Ohmite HVF2512** series. Note: **HVF2512T5003FE (500 kΩ) is marked obsolete / no longer manufactured on DigiKey** — do not design the HVF series in without checking each value | `[distributor-verified 2026-07-23]` — obsolescence read off the DigiKey page |
| Bleed, 4×5 MΩ | CRHV2512 or Ohmite HVC/MOX | `[unverified-MPN]` |
| HV clamp diode (2×) | Need ≤10 nA reverse leakage at 800 V. **Voltage Multipliers / Dean Technology HV axial series.** VMI's "UX-F05B" as I recalled it **does not appear as a VMI part** — the DigiKey hit for "UX-F5B" is a **Sanken** 8 kV rectifier, a different manufacturer and part. **My recalled MPN was wrong; treat as unresolved.** Do NOT substitute 1N4007 (5 µA max IR = 1.9 % of `I_std`) | `[unverified-MPN — recalled P/N disconfirmed]` |
| Dual DAC | MCP4922 (12-bit) or DAC8552 (16-bit, if mV-class zero wanted) | `[unverified-MPN]` |
| 5.000 V reference (doubles as the `VSET` clamp rail) | REF5050 | `[unverified-MPN]` |
| `VSET` buffers / `VMON` buffers | OPA2333 or MCP6V51 (sub-nA bias, needed for the 20 kΩ `VMON` source) | `[unverified-MPN]` |
| Window-trip comparators | LM393 + refs | `[unverified-MPN]` |
| Optional fast dump relay | small NC/NO reed + 1 MΩ | `[unverified-MPN]` |
| `+VIN` load switch | P-FET (DMP3098L class) + 2N7002 | `[unverified-MPN]` |
| Module blocking cap | 22 µF near each `+VIN`, per datasheet note 2 | — |

### 6.1 Cost, and the comparison that matters

Combiner-specific BOM adder, singles:

| | series/resistive midpoint | rail-select (HV relay) |
|---|---|---|
| HV switching element | **$0** | **$70.73** (Standex-Meder HM12-1A69-150, 10 kV, 12 V coil; DigiKey 304 in stock, $49.36 @100) `[snippet]` |
| HV ballast + bleed (8 HV chips) | ~$28 | ~$8 (bleed only) |
| Monitor divider + ADS1115 + buffer | ~$30 | ~$30 |
| DAC + REF5050 + buffers | ~$12 | ~$12 |
| Window trip + `/ON` + `+VIN` interlock | ~$6 | ~$6 |
| Clamp diodes | ~$6 | ~$6 |
| **Combiner adder** | **≈ $82** | **≈ $133** |
| Modules | 2 × **800 V** APS (~$300–500 ea. direct from iseg; **not distributor-stocked**) | 2 × **400 V** APS |

**The resistive midpoint is ~$50/board cheaper in combiner parts and needs no $70 HV relay — but
it needs 800 V modules instead of 400 V ones to reach the same output, which almost certainly
costs more than $50 at the module level.** Net cost: a wash or slightly worse.

**The topology's cost is not in dollars. It is in load current: 5 µA versus 2.5 mA.**

---

## 7. Adversarial summary — what is actually wrong with my own candidate

1. **It cannot satisfy invariant (a), and the substitute is worse.** Both modules are always
   enabled. Worse, the topology *introduces* a failure mode the interlock exists to prevent:
   a single dead module produces uncommanded half-scale output of the **opposite polarity**. In
   every switched topology a dead module produces 0 V. I cannot argue my way out of this one.
2. **±Vnom/2, not ±Vnom.** The symmetric divider costs a factor of two. Every module-volt bought
   delivers half a volt of output.
3. **5 µA.** `Z_out = 750 kΩ`. This is not a power supply; it is a bipolar voltage *reference* for
   a capacitive load. If the brief's load is resistive at all, the topology is dead on arrival, and
   the brief has not yet specified the load.
4. **The through-zero is ±8 V wide, open-loop.** The one thing this topology is supposed to be best
   at, it does with an offset equal to 1 % of `Vnom` from each module. Getting a real zero requires
   closing a ~1.6 Hz loop against the independent monitor — at which point the "no switching
   element, instant through-zero" story becomes a 1–2 s settle.
5. **Ratio drift is direct zero drift.** `R1/R2` mismatch sets both gain and zero. 100 ppm/K TCR
   mismatch over 20 K = 0.2 % ratio shift = **0.8 V of zero-point drift**, on top of item 4.
   A matched HV divider network helps and costs more.
6. **The 100 ms internal τ is not mine to fix.** 460 ms full-scale settle is a property of the APS,
   not of the combiner — but this topology has to move *both* rails for every output change, so it
   pays that penalty on every setpoint, including ones a rail-select topology would service by
   moving one module only.
7. **Both modules run continuously at ~22 % of `Inom`, forever.** Two 1 W converters running warm
   24/7 instead of one. Case limit 120 °C, operating range 0–40 °C ambient; not a problem at 267 µA
   × 800 V = 214 mW of HV output, but it is 2× the thermal load and 2× the wear of a rail-select
   design, and both modules age.
8. **Extremes leave the guaranteed envelope.** iseg guarantees ripple/stability only for
   `Vout > 2 %·Vnom` = 16 V. The constant-sum law drives one rail below 16 V for `|OUT| > 384 V`.
   The ±380 V clamp fixes it by giving up range I already halved once.
9. **My own recalled part number was wrong.** I quoted "VMI UX-F05B" for the HV clamp diode from
   memory; searching found no such VMI part, and the near-hit is a Sanken 8 kV rectifier. If I got
   that wrong, treat every `[unverified-MPN]` in §6 as guilty until a distributor page says
   otherwise. And the one HV resistor value I *did* verify was **out of stock**, and the Ohmite
   alternative I reached for is **obsolete**. HV passive availability is a live schedule risk.
10. **Variant A — the interpretation that actually deserves the name "series stack" — is
    physically broken**, and I only proved it after working the current directions. Anyone who
    reads "series stack, driven midpoint" and pictures variant A is picturing a circuit that
    cannot deliver DC load current in either polarity.

## 8. Recommendation to the human at G0

**Eliminate, unless both of the following are true:**

* the human explicitly amends invariant (a) from "both-enabled unreachable" to "output magnitude
  and polarity bounded in hardware," accepting the §4.1 argument and mandating the §4.1.1 window
  trip; **and**
* the load is confirmed capacitive / **< 10 µA** (deflection plates, electrostatic optics,
  quadrupole DC bias, Kelvin probe).

**If both hold, this becomes a strong candidate** — zero dead-band, zero HV switch, infinite cycle
life, a free 21 Hz output filter, a passive unfailable bleed, and a touch current of 533 µA that no
other topology can match.

**The single question that decides it: what is the maximum DC load current at the output
terminal?** That is an open G0 item in the brief. Until it is answered, this topology cannot be
scored above a 4.

---

### Evidence log

* `[verified-run]` `PY_KICAD` and `kicad-cli` paths confirmed present (PowerShell 5.1, `Test-Path`).
* `[verified-artifact]` Full text of all 10 pages of `references/iseg_manual_APS_en.pdf` extracted
  with `fitz` under `PY_KICAD`; Tables 1–4 read directly. Figure 2 rendered at `Matrix(12,12)`,
  clip `Rect(140,360,315,530)` on page index 8, and read visually — the 20 kΩ `VMON` source
  resistance, the 10 kΩ `Vref` pull-up, the 100 kΩ + 1 µF set-node network, and the `/ON` shunt
  switch are all read off that render. **What this instrument cannot see:** Figure 2 is a
  *simplified* control-principle drawing with deliberately unterminated stubs into "internal
  circuitry." It does not show the HV section, the output impedance, the internal bleeder, or the
  output capacitance. τ_set = 100 ms is *inferred* from the drawn 100 kΩ × 1 µF; iseg does not
  state a slew rate anywhere. **This should be confirmed on the bench before any timing budget
  depends on it.**
* `[distributor-verified 2026-07-23]` DigiKey product pages opened and read: ADS1115IDGSR
  (45,872 in stock, $5.28/$4.02); CRHV2512AF50M0FKE5 (0 in stock, $4.13/$3.07);
  HVF2512T5003FE (obsolete, "no longer manufactured").
* `[snippet]` Standex-Meder HM12-1A69-150 price/stock quoted from a DigiKey search-result summary,
  not from the page itself — re-check before citing.
* `[recalled]` IEC 60664-1 creepage figures, human let-go/perception current thresholds, and the
  350 mJ / 45 µC stored-energy hazard criteria are from memory and are used only for
  order-of-magnitude argument. Confirm against the actual standard before any safety claim.
* `[recalled]` The 20 MΩ estimate for the APS internal bleeder is an *assumption* from general HV
  module practice. iseg publishes no such figure. Two conclusions lean on it (variant A's output
  impedance, and the −372 V reverse-drag number in §3.8); both would change if the real value
  differs by 10×.
