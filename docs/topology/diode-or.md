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
> This file's §"Board area" claims *"uncoated (Table B4) `0.25 mm + 0.01 mm/V above 500 V = 5.25 mm`; conformal-coated (B2) `0.25 + 0.005 × 500 = 2.75 mm`"*. Three errors in one sentence: **B4 is the *coated* column and B2 the *uncoated* one (labels swapped)**, the `0.25 mm` base belongs to **B1 (internal conductors)**, and **`0.01 mm/V` appears in no column of the transcription at all**. The live uncoated-external value at 1000 V is **5.000 mm bare B2, 7.5 mm recommended** — so this file is 1.4–2.7× permissive.
>
> **The single live source for every clearance/creepage number is
> `docs/NUMBERS_PROBE.md`, generated from `hardware/hvctl/numbers_probe.py`.**
> At the frozen part (AP010504, Vnom = 1000 V) the live values are
> **7.5 mm** HV-to-anything and **15.0 mm** HV_POS↔HV_NEG (and HV_OUT_A↔HV_OUT_B),
> every one of them tagged **`[unverified-primary]`** pending a human reading a primary copy
> of IPC-2221B Table 6-1. Do not quote this file's figure anywhere.

# Combiner topology study — opposite-polarity diode-OR

**Phase-1 candidate study, G0.** Author: combiner deep-dive agent. Date: 2026-07-23.
**Verdict: 1 / 10 — ELIMINATE at G0.** Not on cost, not on accuracy, not on parts availability.
It fails at the DC operating point, and no choice of diode fixes it.

Sources and evidence tags used throughout:
`[verified-artifact]` = read off a file on disk this session ·
`[verified-run]` = a command or fetch I executed this session and read the output of ·
`[recalled]` = from context, unverified.
Primary source: **iseg APS series technical documentation v2.5, 2024-08-20**, at
`C:/Users/darro/OneDrive - Yale University/Desktop/iseg-programmable-supply/references/iseg_manual_APS_en.pdf`.
I re-extracted every page of it this session with the KiCad-bundled `fitz`
(`C:/Program Files/KiCad/10.0/bin/python.exe`, git-bash) rather than relying on the briefing summary.

---

## 0. Anchor case

G0 has not frozen the module class, so the analysis is parameterised, anchored on two configurations
from Table 2 (manual page 8) `[verified-artifact]`:

| anchor | item code | Vnom | Inom | Iout ceiling (1.5·Inom) | Vin | Vref / Vset FS |
|---|---|---|---|---|---|---|
| **A (primary, worst case)** | `AP010504P05` / `AP010504N05` | 1 kV | 0.5 mA | 0.75 mA | 5 V | 2.5 V |
| **B (secondary)** | `AP004125P05` / `AP004125N05` | 400 V | 1.2 mA | 1.8 mA | 5 V | 2.5 V |

Anchor A is the hardest case for leakage and monitor-divider loading (largest V, smallest I).
All headline numbers are quoted for A with B in parentheses.

---

## 1. The circuit, precisely enough to draw

Four nodes: `HVP` (positive module pin 6), `HVN` (negative module pin 6), `OUT` (the single
output terminal), `GND` (system ground; APS pins 3 and 7, and the module case, are all GND —
manual Table 4 note, `[verified-artifact]`).

```
   Module P (AP010504P05)                              Module N (AP010504N05)
   pin6 HVP ──┬── D_P ──┬─────── OUT ───────┬── D_N ──┬── HVN pin6
              │  A→K    │                   │  A→K    │
              │         │                   │         │
              │      (bleed)             (monitor)    │
              │       R_b │                 │ R_top   │
              │           │                 │         │
             GND         GND               ...       GND
```

Orientations are **forced**, not chosen:

* `D_P`: **anode at HVP, cathode at OUT.** Module P sources conventional current out of pin 6,
  through the load, back to GND. The diode must conduct HVP → OUT.
* `D_N`: **anode at OUT, cathode at HVN.** A negative module *sinks* at pin 6: current runs
  GND → load → OUT → HVN. The diode must conduct OUT → HVN.

`R_b` = bleed from OUT to GND. `R_top`/`R_bot` = independent monitor divider from OUT to GND.
Both are bolt-ons required by the brief's invariants; neither is part of the diode-OR.

Per-module low-voltage support, common to every candidate topology:
`VSET` driven by a buffered DAC, `VMON` buffered to an ADC, `/ON` driven by an interlock-gated
open-drain stage, 22 µF bulk at `+VIN` (manual Table 1 note 2, `[verified-artifact]`).

---

## 2. The internal facts that decide this, re-read from the manual

Two things I re-verified rather than assumed, because the whole analysis turns on them.

### 2.1 `/ON = HIGH` is *not* an output disconnect

Manual **Figure 2, "Control principle", page 9**. The figure is raster/vector art with no
extractable text; I rendered it at 6× with `page.get_pixmap(matrix=fitz.Matrix(6,6),
clip=fitz.Rect(50,330,520,525))` and read it `[verified-run]`. What it shows, inside the APS
dashed boundary:

* `VSET` pin ← **10 kΩ pull-up to an internal `REF`** (the 2.5 V / 5 V reference).
* `VSET` pin → **100 kΩ series** → internal setpoint node → **1 µF to GND**.
* `/ON` pin → drives a **switch that shorts that internal setpoint node to GND**.
* `VMON` pin ← **20 kΩ series** from the internal monitor node.

Therefore: **`/ON = HIGH` works by forcing the module's internal setpoint to zero. The module
then actively regulates its HV pin to 0 V.** There is no series output switch, no relay, no
high-impedance state. An APS module in every state — enabled, disabled, at any setpoint — is a
low-impedance-ish *voltage source* holding pin 6 somewhere in [0, +Vnom] (or [−Vnom, 0]).

This corroborates and sharpens the manual's own wording (Table 1, `[verified-artifact]`):
`5.5 V ≥ V/ON > 2.5 V (HIGH) ➜ VOUT = 0 !` — it says the output *is zero*, not that it is
disconnected.

Any combiner design that assumes "disabled module = high impedance at pin 6" is built on a
false premise. The diode-OR is exactly such a design.

### 2.2 Derived numbers from Figure 2, useful to every topology

* **Setpoint time constant = 100 kΩ × 1 µF = 100 ms.** 5τ = **500 ms** to settle a commanded
  change. Any output servo loop must cross over well below 1/(2π·0.1 s) = **1.6 Hz**.
* **`/ON` release ramp** is that same 100 ms charge; `/ON` assert is fast (the switch shorts the cap).
  So HV-OFF is prompt, HV-ON is a half-second ramp. Asymmetric, and useful.
* **Open `VSET` commands full scale.** The 10 kΩ pull-up to REF drives an undriven VSET to REF.
  This independently confirms the Table 1 `Rset = Vout·10kΩ/(Vnom − Vout)` formula, which is
  algebraically exactly a 10 kΩ from REF to VSET with Rset to GND. `[verified-artifact]`
* **Any VSET driver must sink** REF/10 kΩ = **250 µA** (0.5 W family) or **500 µA** (1 W family)
  to hold VSET at 0.
* **`VMON` has 20 kΩ of source impedance.** Its buffer needs ≤ 1 nA input bias to keep the
  induced error under 20 µV. CMOS-input op-amp, not a bipolar one.

---

## 3. The showstopper: the idle leg's diode is FORWARD biased

This is the finding. Everything else in this document is supporting material.

`D_P` is reverse-biased **iff** `V(HVP) < V(OUT)`.

Module P is a positive-only supply referenced to GND. From §2.1, `V(HVP) ∈ [0, +Vnom]`; its
**minimum is 0 V**, in every state including `/ON` asserted.

For `D_P` to block while the N leg drives the output to −1 kV, we would need `V(HVP) < −1000 V`.
Unreachable. `V(HVP) ≥ 0 > V(OUT)` always.

> **`D_P` is hard forward-biased, by the entire negative excursion, in exactly the condition it
> was placed in the circuit to block.** Mirror-image for `D_N` on the positive excursion.

The briefing's framing — *"the idle module's diode sees the full opposite-polarity reverse
voltage"* — is the thing that is **not true**, and it is the reason this topology looks
attractive on a whiteboard. No diode rating changes it, because the diodes never get the chance
to block.

**Why the intuition fails.** A diode-OR works between same-polarity sources because "idle" means
"lower voltage *in the conduction direction*". In a bipolar system, **zero is not an off state,
it is the midpoint** — and the idle module's 0 V sits on the *conducting* side of the opposite
polarity's swing. There is no unipolar-module state that is "beyond the far rail".

Stated generally: **a two-terminal unidirectional-blocking device cannot isolate a
ground-referenced 0 V node from an output of the opposite polarity, because the required
blocking direction is identical to the required conducting direction.** That is a structural
theorem about the topology, not a component-selection problem.

### 3.1 Case A — idle module powered (whether enabled at Vset = 0 or `/ON` asserted)

Electrically identical per §2.1: the module regulates HVP to 0 V.

`D_P` conducts. Module P sources current into OUT, clamping OUT at ≈ **−V_F(D_P) ≈ −1.5 V**
(see §5.2). Module N sinks. Both saturate against their output ceilings — manual Table 2 note 1,
`Iout is limited to approx. 1.5 · Inom` `[verified-artifact]` — **0.75 mA (1.8 mA)** each.

Current-budget arithmetic. To reach −1 kV at a load, module N must supply

```
I_N  =  I_load  +  I_through_D_P
```

and `I_through_D_P` is limited only by module P's own source ceiling, 0.75 mA. Module N's
ceiling is the same 0.75 mA. So:

```
I_load  ≤  0.75 mA − 0.75 mA  =  0 mA        (anchor A)
I_load  ≤  1.8 mA  − 1.8 mA   =  0 mA        (anchor B)
```

**Available load current at either polarity is exactly zero.** The entire current budget is
consumed by the two modules fighting through the forward-biased blocking diodes.

Unloaded, the outcome is worse than useless — it is *indeterminate*. Two current-limited sources
in direct opposition; the node runs to whichever module's limit is lower, decided by
unit-to-unit tolerance on a spec written as "approx." **A high-voltage output whose polarity and
magnitude are decided by which of two current limits happens to be lower is not an engineering
outcome I will sign off on.**

Realistic operating range of the built circuit: about **±2 V**, instead of ±1000 V.

### 3.2 Case B — idle module unpowered (VIN cut by a FET or relay)

Now module P cannot source. `D_P` still forward-conducts, and OUT at −1 kV drags HVP down to
**−1 kV + V_F ≈ −998 V**. The current is whatever conducts inside module P at reverse polarity:
its internal monitor divider (hundreds of MΩ, so µA-class) and — the real concern — the output
rectifier stack of a resonant-converter multiplier, now forward-biased backwards into its own
polarised capacitors.

**iseg specifies no reverse-voltage withstand on pin 6.** I re-read all ten pages of v2.5
`[verified-artifact]`: nothing permits, characterises, or bounds a negative potential on the HV
pin of a positive module. Applying −998 V to it is out-of-spec operation with an undefined
outcome, on a €200-class module, on a board whose first energisation is human-present.

### 3.3 The mutual exclusion that closes the door

To *prevent* case B you would add a clamp diode from GND to HVP (anode GND, cathode HVP) so HVP
cannot go below −V_F. But that clamp is in series-forward with `D_P`, creating the path

```
GND ──►|── HVP ──►|── OUT
     D_clamp    D_P
```

a direct, un-current-limited forward conduction path from system ground to the output. The clamp
converts the module into a **hard ground clamp on OUT**, worse than case A because there is no
regulator in the loop to current-limit.

> **Protecting the idle module and letting the output swing to the opposite polarity are mutually
> exclusive with diodes alone.**

---

## 4. Can a series resistor rescue it? No — it is 10⁴ short

Insert `R_s` in each leg between the module HV pin and its diode. Two constraints:

**(i) Accuracy when the leg is driving.** The drop `I_load · R_s` is downstream of the module's
regulation node, so the module cannot correct it. To keep the combiner from dominating the
module's own ±1 % adjustment accuracy:

```
R_s  ≤  0.01 · Vnom / Inom
     =  0.01 · 1000 V / 0.5 mA   =  20 kΩ        (anchor A)
     =  0.01 · 400 V  / 1.2 mA   =  3.33 kΩ      (anchor B)
```

**(ii) Isolation when the leg is idle.** The fight current through the forward-biased idle leg:

```
I_fight  =  (0 − (−Vnom) − V_F) / R_s  ≈  Vnom / R_s
```

To hold that to 1 % of Inom (5 µA for anchor A):

```
R_s  ≥  1000 V / 5 µA    =  200 MΩ               (anchor A)
R_s  ≥  400 V  / 12 µA   =  33.3 MΩ              (anchor B)
```

**Ratio of the two requirements:**

```
200 MΩ / 20 kΩ    = 1.0 × 10⁴      (anchor A)
33.3 MΩ / 3.33 kΩ = 1.0 × 10⁴      (anchor B)
```

Identical, because the gap is structurally `1/(ε_drive · ε_idle) = 1/(0.01 × 0.01) = 10⁴`,
independent of module class. **80 dB.** No resistor value exists; this is not a tuning problem.

At the accuracy-limited `R_s = 20 kΩ`, the fight current would be `1000 V / 20 kΩ = 50 mA` —
**67× module P's 0.75 mA ceiling.** It saturates instantly and we are back in §3.1.

---

## 5. The counterfactual numbers, for completeness

These are the quantities the brief asked me to work out. I present them because a topology should
not be dismissed on a technicality, and because the answers are *good* — which is precisely why
this candidate survived to a Phase-1 study. They are all irrelevant, because the DC operating
point is broken before any of them apply.

### 5.1 Reverse rating — justifying the 2× number

The brief asks for 2× full scale, "justify the number". Here is the correct justification, and it
is **not** the one usually given.

* **Normal operation, switched topology:** idle leg's module side at 0 V, output side at −Vnom
  → the blocking element sees **1 × Vnom = 1 kV**.
* **Single-fault, idle module stuck-on at full scale while the other drives the opposite rail:**
  +Vnom on one side, −Vnom on the other → **2 × Vnom = 2 kV**.

So **2× is the correct rating basis because of the stuck-on single-fault case, not because of
normal operation.** Then apply the standard 2:1 HV-rectifier derate for partial discharge,
surface tracking and humidity (manual permits 70 % RH non-condensing, `[verified-artifact]`):

```
2 × 1000 V × 2  =  4000 V  →  a 4 kV part.
```

The chain closes cleanly on a stock part. Note that in the *diode-OR as drawn*, this reverse
condition never occurs at all — the diodes are forward-biased instead.

### 5.2 Forward drop — servoable, and not a reason to reject

**Vishay GP02-40**, datasheet document 88635 rev 09-Aug-2022, which I fetched and text-extracted
this session `[verified-run]`:

| parameter | value |
|---|---|
| V_RRM / V_DC | 4000 V |
| I_F(AV) | 0.25 A |
| **V_F max** | **3.0 V @ 1.0 A** |
| **I_R max @ rated V_DC, T_A = 25 °C** | **5.0 µA** |
| **I_R max @ rated V_DC, T_A = 100 °C** | **50 µA** |
| t_rr typ | 2.0 µs |
| C_J typ | 3.0 pF @ 4 V, 1 MHz |
| T_J max | 175 °C |
| R_θJA typ | 130 °C/W |

Fig. 3 (typical instantaneous forward characteristics) bottoms out at 10 mA / ≈1.5–2 V.
Extrapolating at `n·V_T·ln(10)` per decade with n ≈ 2 down to our 0.5 mA (1.2 mA):

```
V_F(0.5 mA)  ≈  1.3 – 1.7 V.   Take 1.5 V ± 0.3 V.
```

* As a fraction of full scale: **1.5 V / 1000 V = 0.15 %** — well inside the module's own ±1 %.
* At a low set-point, say OUT = 5 V: the module must produce 6.5 V, a **30 % error at that
  set-point**. But the module's own voltage-monitor accuracy is `1 % · Vnom` = **±10 V** at
  anchor A `[verified-artifact]`, so nothing is accurate at 5 V regardless of the combiner.
* **Tempco:** −2 mV/°C per junction; the GP02 behaves as ≈2 junctions → ≈ **−4 mV/°C**. Over the
  module's 0–40 °C operating window that is 160 mV = **0.016 % of 1 kV**.

**Can the independent output monitor servo it out? Yes, completely.** V_F is a slow, monotonic,
load- and temperature-dependent offset. A firmware integrator closing OUT_measured → VSET removes
it to within the monitor's own accuracy.

**But** the loop must live inside the module's 100 ms setpoint time constant (§2.2): crossover
≪ 1.6 Hz, so a **0.1–0.5 Hz integrator**. That is fine for set-and-hold and **hopeless for
tracking a load step**. The load-dependent part of the V_F error (and of any series-R drop)
remains uncorrected on transients. Worth carrying to whichever topology wins.

### 5.3 Reverse leakage — a genuine non-problem, honestly reported

At anchor A the idle diode's reverse voltage is 1 kV = **25 % of the GP02-40's rating**. Fig. 4
(typical reverse characteristics, log 0.01–10 µA over 0–100 % of rated V_R, curves for T_J = 25
and 100 °C) puts the 25 °C typical at roughly **0.1–0.5 µA**; scaling the 5 µA *max* by the same
curve shape gives a worst case near **1 µA at 25 °C**. The datasheet's own 25 °C → 100 °C ratio
is 10×; we operate at ≤ 40 °C ambient (manual, `[verified-artifact]`), so realistically **2–3 µA**
hot-case worst.

```
1 µA / 0.5 mA  =  0.2 % of Inom          3 µA / 0.5 mA  =  0.6 % of Inom   (anchor A)
1 µA / 1.2 mA  =  0.08 % of Inom                                            (anchor B)
```

**Where does that leakage flow, and does it hurt accuracy?** In the counterfactual working
version, leakage in the reverse-biased idle `D_N` flows OUT → D_N → HVN, i.e. it is simply an
extra load on the driving P module. The P module *regulates*, so it absorbs it. **Leakage costs
current budget, not accuracy.**

And the effect at low set-points — the thing the brief specifically flagged — is the opposite of
the worry: **leakage scales with the reverse voltage across the idle diode, which equals the
output voltage. At a small set-point the idle diode has a small reverse voltage and leaks
nanoamps.** At OUT = +10 V, `D_N` sees 10 V reverse and leaks sub-nA. Leakage is smallest exactly
where accuracy matters most.

Near OUT = 0 both diodes are at ~0 V reverse; the bleed resistor dominates entirely.

**Conclusion: reverse leakage is not a reason to reject diode-OR.** Reporting this plainly matters
— if the topology died of leakage it would be a component-selection problem, solvable with a
better diode. It dies of something structural instead.

### 5.4 Make-before-break, through-zero, dead-band

A diode-OR is **make-before-break by construction** — no leg is ever mechanically disconnected.
For same-polarity sources that is benign and is the whole reason diode-ORs are used.

For **opposite-polarity** sources sharing a node, make-before-break means a permanent
source-into-sink connection. **The property the brief hoped would deliver smooth through-zero is
the exact property that kills the topology.** That is worth stating plainly, because it means the
attraction and the defect are the same fact.

In the counterfactual working version:

* **Genuine through-zero glide: yes**, continuous, no dead time at all.
* **Un-servoed window:** the region where neither diode conducts, `|OUT| < V_F ≈ 1.5 V`, i.e.
  **±0.15 % of ±1 kV**. Inside it the output is held by the bleed resistor alone — not
  uncontrolled, just open-loop.
* **Crossing duration** is a voltage window, not a fixed time. On a 100 V/s sweep, 3 V of window
  takes **30 ms**.

In the real circuit that ±1.5 V window is not a dead-band — it is the **entire reachable operating
range** (§3.1). The headline advantage evaporates into the failure.

For comparison, the relay alternative's dead-band is the contact transfer time (order 1 ms for a
reed relay `[recalled]` — I did not verify HM12 timing). With `τ = R_b·C_out = 26 ms` (§6b), the
output decays `1 − e^(−1/26)` = **3.8 %**, i.e. from 1000 V to ~962 V, during a 1 ms transfer.
Entirely acceptable. **A relay's dead-band is a non-issue; the diode-OR's absence of one is the
issue.**

---

## 6. The three non-negotiable invariants

### (a) Hardware interlock making both-enabled UNREACHABLE — **FAIL, and unrescuable**

Diodes are two-terminal passives with no connection to `/ON`. They provide **zero** interlock.

Worse than "permits both-enabled": **a diode-OR's normal operating state IS both-enabled.** The
topology *requires* both modules to be powered — cut one and you get §3.2, reverse voltage on its
HV pin. Every instant of operation is the state the invariant forbids.

An interlock *can* be bolted on and should be, for whichever topology wins. The right mechanism
is mechanical exclusivity, not logic: **a single-armature SPDT/DPDT relay contact, where one
armature physically cannot touch both `/ON` release contacts.** Both `/ON` lines carry 10 kΩ
pull-ups to +5 V (default = HV OFF); the armature grounds exactly one of them; the mid-transfer
state grounds neither, which is the safe state. A cross-coupled 74HC00 SR latch is a cheaper
electrical equivalent but shares a die, a rail and a ground with the thing it is protecting
against — the relay is the honest hardware answer.

**But no interlock rescues the diode-OR**, because `/ON = HIGH` does not disconnect the module
(§2.1). An interlocked, correctly-"disabled" module still clamps the output (§3.1). Adding a
VIN-cut so the idle module is genuinely dead gives §3.2 instead. **The interlock is orthogonal
to, and insufficient for, this topology.** FAIL.

### (b) Defined discharge on changeover and on disable — **FAIL as drawn**

The diodes provide no discharge path, and they actively make it worse: after the P leg charges
OUT to +1 kV, `D_P` **blocks the return path**. The module cannot pull OUT back down through
`D_P` — wrong direction. With no bleed, OUT holds +1 kV on stray capacitance indefinitely after
module P is disabled. (The idle-leg clamp of §3.1 does accidentally discharge it, which is the
only thing the broken topology does right, and it does it by fighting.)

A proper bleed, which any topology needs:

```
budget 10 % of Inom at full scale:  R_b ≥ 1000 V / 50 µA  = 20 MΩ  → use 22 MΩ   (anchor A)
                                    R_b ≥ 400 V / 120 µA  = 3.33 MΩ              (anchor B)
P_diss = 1000² / 22 MΩ = 45 mW
C_out ≈ 1 nF (module internal, undocumented — assume) + ~100 pF/m RG-58 + wiring ≈ 1.2 nF
τ  = 22 MΩ × 1.2 nF = 26 ms
3τ = 79 ms   → 1 kV decays below the 50 V touch-safe threshold
5τ = 132 ms  → to 1 %
```

Realisation at 1 kV needs voltage-rated parts: **2 × 11 MΩ in series**, 500 V each, in a
2010 HV thick-film (Vishay CHV2010 class, 3 kV working) `[unverified-MPN]`. A standard 1206
thick-film is 200 V working — five of them at 200 V each is zero margin and is wrong.

**Asymmetry worth recording for the winning topology:** the P leg can only *raise* OUT; all
downward slewing depends on the bleed plus the opposite module's sink capability. Rise and fall
are governed by different mechanisms with different time constants, and firmware must model that.

Verdict: the bleed is a bolt-on that every candidate needs. The diode-OR contributes nothing and
makes the un-bled case strictly worse.

### (c) Independent output monitoring — **PASS, but topology-independent**

```
R_top = 4 × 100 MΩ  (Ohmite MOX-400 class, 3.5 kV, 1 %)   [unverified-MPN]
R_bot = 402 kΩ 0.1 %
ratio = 400.4 MΩ / 402 kΩ ≈ 996 : 1   →   ±1000 V maps to ±1.004 V
divider current at FS = 1000 V / 400.4 MΩ = 2.50 µA = 0.50 % of Inom (anchor A)
```

0.5 % of the current budget is noticeable at anchor A. Going to 1 GΩ (5 × 200 MΩ) drops it to
1 µA = 0.2 %, at the cost of noise and a stray-capacitance pole: ~1 pF of top-node stray against
1 GΩ is a **1 ms pole**, so a fast readback needs a compensating ~1 pF across each top resistor.

**Do not use the ESP32's own SAR ADC**: unipolar 0–3.1 V, non-linear, ±2 % uncalibrated. The
signal here is bipolar. Use a differential ΔΣ that takes ±1.004 V directly with no level shift:
**MCP3421** (18-bit, single differential channel, ±2.048 V, I²C, ≈ $2.50) or **ADS1115** (16-bit,
4-ch, PGA, ≈ $5) `[unverified-MPN]`.

This taps OUT, not VMON, and uses a different converter than any module signal. Invariant
satisfied. **It is equally available to the relay and stacked topologies, so it is not a point
in the diode-OR's favour.**

---

## 7. Single-fault analysis

Active elements: modules P and N, `D_P`, `D_N`, ESP32, VSET DACs/buffers, `/ON` drivers,
interlock, bleed, monitor divider.

| element / fault | what OUT does | detectability |
|---|---|---|
| **`D_P` open** (cracked body, post-avalanche open) | positive polarity lost entirely; OUT can only go negative. HVP now floats up to +1 kV into an open circuit — **a live, unbled 1 kV node on the PCB**, because R_b sits on the OUT side of the diode | independent monitor ≈ 0 while VMON_P reads full scale. Good |
| **`D_P` short** (thermal runaway; the more common HV-rectifier failure under repeated reverse stress) | module P hard-connected to OUT. The clamp of §3.1 becomes unconditional and V_F-free. If module P is at a setpoint, OUT is at that setpoint **regardless of the interlock** | invisible to module readbacks. **Only the independent monitor sees it** |
| `D_N` open / short | mirror image | mirror image |
| **Module P stuck-ON** (converter runs at full duty, or the internal `/ON` switch fails open so the 1 µF setpoint cap charges to VSET) | OUT driven to +1 kV regardless of command. Module N *can* sink through `D_N`, so both current-limit; **output indeterminate anywhere in [0, +1 kV]**. No hardware limits it | monitor + VMON disagree with command |
| Module P stuck-OFF | positive polarity unavailable | monitor sees it. Safe |
| **ESP32 in reset** — GPIOs go high-Z | `/ON` floats → **HV ON** (Table 4: `LOW or n.c. ➜ HV ON`). VSET floats → internal 10 kΩ to REF → **FULL SCALE**. **Both modules commanded to ±Vnom simultaneously.** The diode-OR is the only candidate with no series element to break the path, so it is the only one where this fault reaches the output terminal | none, without hardware |
| **ESP32 unpowered, HV rails up** | identical to reset. DAC/op-amp ESD structures may accidentally hold VSET near a dead rail — an accident, not a design | none, without hardware |
| **Broken wire, `/ON_P`** | floats → **HV ON**. The interlock *drives* the line and does not *sense* it, so it silently loses authority over that module | **undetectable unless `/ON` is read back** — mandate a sense GPIO on each `/ON` node |
| **Broken wire, `VSET_P`** | internal 10 kΩ pulls to REF → **module commands full-scale Vnom**. VMON faithfully reports the full-scale output that is genuinely there, so the module-side readback *agrees* and looks healthy | **only** the independent monitor + a commanded-vs-measured check. Invariant (c) is load-bearing |
| Broken wire, `VMON_P` | reads 0 or floats. Cosmetic | independent monitor covers it |
| **Broken wire, GND (pin 3 *or* 7)** | survivable — pins 3 and 7 are both GND and the case is GND `[verified-artifact]`. **Genuine redundancy**, but only if layout routes both pins independently to the pour rather than daisy-chaining them | layout rule, not a runtime check |
| **Bleed resistor open** | discharge invariant silently lost | split the bleed into two parallel strings (one open halves the current, does not remove it) + a firmware self-test that disables and times the decay against expected τ, flagging > 2× nominal |
| **Monitor R_top open** | monitor reads 0. **If firmware is servoing, the integrator winds to full scale and drives OUT to maximum.** A monitor failure inside a closed loop is an over-voltage generator | cross-check independent monitor against VMON; halt on > 5 % of Vnom disagreement |
| Monitor R_bot open | tap floats toward the top-node potential — but the 400 MΩ top string limits the fault current to 2.5 µA, so the ADC clamp diodes handle it trivially. **The high top-resistance is itself the protection** | benign, by design |

### 7.1 Mandatory hardware mitigations these faults imply

All topology-independent; carry them to whichever combiner wins.

1. **`/ON` default must be HIGH.** 10 kΩ pull-up to +5 V on each `/ON`; the ESP32 must actively
   pull LOW to enable. Never rely on the GPIO's own reset state.
2. **Watchdog-gated `/ON`.** A retriggerable supervisor (TPS3823 / MAX6369 class, ≈ $1)
   `[unverified-MPN]` in series with the enable, so loss of firmware releases `/ON` HIGH → HV OFF.
3. **Modules' VIN downstream of the ESP32 rail and the watchdog**, so "ESP32 unpowered" ⇒
   "modules unpowered". Cheap and complete.
4. **A VSET pull-down resistor cannot work — use a switch.** The arithmetic, which is
   non-obvious and worth recording:
   ```
   undriven VSET = REF · R_pd / (10 kΩ + R_pd)
   want ≤ 1 % of 2.5 V = 25 mV  →  R_pd ≤ 101 Ω
   but then, at full scale, the DAC must source 2.5 V / 101 Ω = 24.8 mA into that pull-down
   ```
   A 1 kΩ pull-down — the value one would reach for — leaves VSET at
   `2.5 · 1k/11k = 0.227 V` = **9 % of full scale = 91 V on a 1 kV module**. The correct part is a
   **normally-closed analog switch / N-FET shorting VSET to GND**, opened only by the same
   watchdog-gated enable.
5. **Hardware VSET clamp, not firmware.** Manual Table 1 is explicit `[verified-artifact]`:
   *"Attention! Output voltage is internally not limited! At Vset > 2.5 V ➜ Vout > Vnom is
   possible!"* Power the VSET buffer op-amp **from a 2.5 V precision reference rail**
   (REF3325 / LM4040DIZ-2.5, ≈ $1) `[unverified-MPN]` and reference the DAC to the same node, so
   the DAC's own full scale *is* the clamp and a rail-to-rail output physically cannot exceed it.

---

## 8. Part count, board area, cost

**Combiner-attributable BOM** (everything else is shared with every candidate topology):

| item | qty | unit @1 | unit @100 | note |
|---|---|---|---|---|
| GP02-40-E3/73, 4 kV / 250 mA, DO-41 | 2 | **$1.72** | **$0.7257** | `[verified-run]` DigiKey PN 9600285, **3 307 in stock**, fetched 2026-07-23 |
| GND clamp diodes (same part) — required by §3.3, and self-defeating | 2 | $1.72 | $0.7257 | |
| pre-diode bleeds, one per module HV pin (§7, `D_P` open case) | 4 | ~$0.75 | | HV thick-film `[unverified-MPN]` |
| **combiner total** | **8** | **$9.88** | **~$5.90** | |

Board area: 4 × DO-41 axial on HV pitch. IPC-2221 external clearance at 1 kV:
uncoated (Table B4) `0.25 mm + 0.01 mm/V above 500 V = 5.25 mm`; conformal-coated (B2)
`0.25 + 0.005 × 500 = 2.75 mm`. Axial bodies at 5.25 mm spacing are comfortable; **creepage, not
clearance, is the binding constraint** and will want milled slots under the diode bodies.

**Comparison, for the record only.** The HV-relay alternative needs a contact rated for the full
bipolar span. **Standex-Meder HM12-1A69-150** (10 kV switching, 12 V / 80 mA coil, SPST-NO):
**304 in stock at DigiKey, $70.73 @ 1, $49.36 @ 100** — from a search-result summary, not a page I
opened directly, so treat as **single-source** `[unverified-MPN]`. Two of them ≈ **$141**, plus
80 mA of coil current at 12 V = **0.96 W** continuous for the energised leg.

> **The diode-OR is ~20× cheaper in combiner parts and it does not work.** It is the cheap option
> that fails the physics, not the expensive option that fails the budget. That is the honest
> summary, and it is why this study exists.

---

## 9. Adversarial pass — the strongest objections to my own conclusion

**"Your §3.1 assumes the idle module can source at 0 V. Prove it."** Figure 2 shows the `/ON`
switch shunting the setpoint node, and Table 1 says `VOUT = 0`, not `VOUT = open`. A resonant
converter regulating to 0 V with a live control loop is a source. I did **not** bench-measure the
output impedance of a disabled APS at 0 V — **this is the one claim in this document that a
20-minute bench test could overturn**, and it is the test I would run before anyone spends money
on the alternative. If a disabled APS turned out to present > 200 MΩ *and* a specified reverse
withstand on pin 6, §3 would need rewriting. I judge that very unlikely on both counts, and
iseg specify neither.

**"Add a series HV opto-MOSFET to fix the forward bias."** Then the diodes are a $3.44 redundancy
on a $30 switch, and the correct name for the circuit is *"solid-state HV changeover with
reverse-blocking diodes"*. Recommending diode-OR at G0 would be recommending a **component**, not
a topology. Which is, in fact, the recommendation I make below.

**"The GP02 is EOL."** Correct, and I found it myself: the datasheet is stamped **"Not for New
Designs"** by Vishay `[verified-run]`, and the /54 variant's DigiKey page carries the same flag.
The best-stocked, best-documented candidate part starts with a lifecycle problem. Immaterial here,
but it would matter to any topology that needs 4 kV rectifiers.

**What I could not verify.** Dean Technology's UX-F pages return HTTP 403 to WebFetch, and the VMI
catalogue PDF exceeds the fetch size limit `[verified-run]` — so I have **no first-party numbers**
for the UX-F or VMI parts the brief named. Everything I quote for them would be `[recalled]`, so
I quote nothing. The GP02-40 is the part I actually verified, and it is sufficient to make every
argument above.

---

## 10. Recommendation

**Eliminate opposite-polarity diode-OR as a combiner topology at G0.** It fails invariant (a)
structurally and unrescuably, fails (b) as drawn, and satisfies (c) only via a bolt-on available
to every candidate. Its one genuine attraction — inherent make-before-break through-zero — is the
same property that destroys it.

**Carry these forward to whichever topology wins:**

1. **Diodes are still worth buying — as a supporting component, not a combiner.** A series
   reverse-blocking diode in each leg of a relay or solid-state changeover protects each module
   from the other during contact transfer and from contact leakage/creepage. $3.44 for real
   protection against the §3.2 reverse-voltage abuse. **This is the surviving recommendation.**
2. **`/ON` does not disconnect** (§2.1). Every combiner must provide its own series interruption.
3. **100 ms module setpoint time constant** (§2.2) → output servo crossover ≪ 1.6 Hz.
4. **Open VSET commands full scale**; a pull-down resistor cannot fix it, a switch can (§7.1.4).
5. **Hardware VSET clamp via a 2.5 V reference rail** on the buffer op-amp (§7.1.5).
6. **Route APS pins 3 and 7 independently** to the ground pour — free single-fault redundancy.
7. **`/ON` must be sensed as well as driven** — a broken enable wire turns HV ON silently.

---

## Appendix — instruments used, and what they cannot see

| claim class | instrument | blind to |
|---|---|---|
| iseg electrical/mechanical specs | `fitz` text extraction of all 10 pages of v2.5, git-bash + PY_KICAD `[verified-run]` | anything iseg chose not to publish: internal bleed value, output capacitance, reverse withstand on pin 6, output impedance in the disabled state |
| APS internal control structure | 6× pixmap render of Figure 2, page 9, read visually `[verified-run]` | component tolerances, whether the drawn switch is a FET or a relay, anything simplified out of a marketing figure |
| GP02-40 ratings | Vishay doc 88635 rev 09-Aug-2022, fetched and text-extracted `[verified-run]` | V_F below 10 mA and I_R below 100 % of rated V_R exist only as *log-axis curves* — my 1.5 V and 1 µA figures are **extrapolations**, not datasheet guarantees |
| GP02-40 stock/price | DigiKey product page 9600285, WebFetch `[verified-run]`, 2026-07-23 | price volatility; whether the 3 307 units are committed |
| HM12-1A69-150 stock/price | **search-result summary only**, page not opened `[unverified-MPN]` | everything — treat as indicative |
| every circuit conclusion above | pencil and paper | **nothing has been breadboarded.** No APS module has been powered. §9 names the one bench test that could overturn the central claim |
