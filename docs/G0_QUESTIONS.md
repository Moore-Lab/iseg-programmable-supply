# ⬛⬛ GATE G0 — **ANSWERED AND SIGNED OFF, 2026-07-23** ⬛⬛

> **STATUS: CLOSED.** The human answered on **2026-07-23**. Everything in the four boxes below is a
> **FROZEN fact**. The questions and all of the analysis beneath them are **retained deliberately** —
> they are the record of *why* each answer matters and what each answer costs. Do not delete them, and
> do not re-litigate an answered question.
>
> **FIVE answers, not three.** The human gave three answers to the batched questions, then **added a
> fourth item that is a scope change, not an answer** (A4), then **answered the question A4 itself
> created** (A5 — how the mode is selected). Treat A4 as a first-class requirement and A5 as a
> **frozen design decision**, not a recommendation.
>
> **Three of the seven questions remain UNANSWERED** (Q3 output spec, Q5 safety envelope, Q6
> weld-prevention-vs-detection) plus Q7 (procurement). Those proceed on the §6 defaults and stay
> flagged. See §7 "What is still open after G0" at the foot of this document.
>
> ### ⬛ TERMINOLOGY — the human's words, adopted project-wide (G0-A5)
>
> | Use this | For | Never write |
> |---|---|---|
> | **pseudo-bipolar** | the single-output mode that changes polarity by switching across zero | "bipolar" unqualified |
> | **unipolar / dual-output** | the two-output mode in which both modules may be live at once | "dual unipolar" is acceptable; "two-channel" is not |
>
> **"Pseudo-bipolar" is the honest word and that is why it was chosen:** the instrument does **not** pass
> smoothly through zero (G0-A1), it changes polarity by switching. Mode 1 is referred to as
> "MODE 1 — BIPOLAR COMBINED" throughout the pre-A5 text below; read that as **pseudo-bipolar**.

---

## G0-A1 — BEHAVIOUR (answers Q1) — verbatim

> **Set-and-hold with polarity changeover.** Smooth through-zero is NOT required. A dead-band of order
> 1 second at each polarity crossing is acceptable, with the output actively clamped to ground while it
> happens.

**⇒ This is candidate answer A of §Q1.** The combiner is **HV RELAY CHANGEOVER**. The
`series-stack-driven-midpoint`, `diode-or`, and `single-module-polarity-reversing-relay` topologies are
**REJECTED and must not be revived**. `docs/COMBINER_STUDY.md`'s decision tree collapses to its
branch A. The APS family is **not** disqualified (the §Q1 disqualification argument applied only to
answer C/D).

## G0-A2 — MODULE (answers Q2) — verbatim

> **We have the aps10504 (both negative and positive polarity).**

**The human already owns the modules.** This is not a selection to be made; it is a fact to be designed
around. Decoding that string against manual Table 2 / Table 3 (v2.5, 2024-08-20) — the decode rule is
`DECISIONS.md` PART-12, `[verified-run]`:

| Item-code field | Value in `AP010504…` | Meaning |
|---|---|---|
| Series | `AP` | APS series |
| `Vnom` — three significant digits × 100 V | `010` | **1 000 V** |
| `Inom` — two significant digits + count of trailing zeros, in nA | `504` | 50 followed by 4 zeros = 500 000 nA = **0.5 mA** |
| Polarity letter | `P` and `N` | **one of each, both in hand** |
| Input-voltage suffix | `05` | **5 V input** ⇒ the **0.5 W / 5 V family** |

⇒ the two parts are **`AP010504P05`** (positive) and **`AP010504N05`** (negative). `Pnom` = 0.5 W.

### The frozen parameter set that follows, and is not negotiable

| Parameter | Frozen value | Note |
|---|---|---|
| `Vnom` | **1000 V per module** | bipolar output is −1 kV … +1 kV, **one polarity at a time** in mode 1 |
| `Inom` | **0.5 mA** | `Iout` limited to ≈1.5 × Inom = **0.75 mA** (PART-13) |
| `Vin` | **5 V** (range 4.5–5.5 V) | **NOT 12 V.** Every 12 V-family row in this repo is now *wrong*, not merely superseded |
| `Vref` | **2.5 V ±1 %** | **NOT 5 V** |
| `Vset`, `Vmon` full scale | **0 … 2.5 V** | |
| `Iin` | <5 mA at Vout=0 · <25 mA at Vnom no load · **<180 mA at Vnom loaded** | per module |
| Ripple / noise | typ <10 mVpp, max <30 mVpp (f>10 Hz), <5 mVpp (f>2 kHz) | **guaranteed only for 2 %·Vnom < Vout ≤ Vnom, i.e. only above 20 V.** Below 20 V the output is **UNSPECIFIED, not merely worse.** Say so wherever a low-end spec is quoted |
| Monitor accuracy | **1 %·Vnom = 10 V** on VMON | adjustment accuracy ±1 % = 10 V |

### Consequence 1 — **THE 3.3 V HAZARD IS NOW REAL AND LOAD-BEARING**

§Q2 listed "the set-path rail" as one bullet among five and recommended the 1 W / 12 V family
*specifically* because its Vref = 5 V is immune to a 5 V logic rail. **That recommendation is dead —
the human owns the 2.5 V-Vref family.** The hazard the recommendation existed to avoid is therefore the
condition we must now design against:

- Vref is **2.5 V**; the ESP32 is a **3.3 V** part.
- A logic-level fault, a mis-set DAC reference, or a floating node pulled to 3.3 V commands
  **3.3 / 2.5 = 132 %** of nominal ⇒ **≈1320 V**, on an input the datasheet explicitly says is
  *"internally not limited"* (PART-05 — and it states no ceiling, so a clamp must be designed to Vref,
  not to an assumed overshoot).
- Combined with the internal ~10 kΩ pull-up to Vref (**an OPEN `VSET` node commands FULL SCALE** —
  PART-04) and **active-low `/ON`** (**a floating `/ON` turns HV ON** — PART-02), the module's un-driven
  default state is **ENERGISED AT OVER-RANGE.**

⇒ **The hardware `VSET` clamp is a PRIMARY SAFETY ELEMENT of this design, not a refinement.** Design it
accordingly and give it its own verification. (ARCH-06: the clamp is the `VSET` buffer's own rail, powered
from the same precision reference that feeds the DAC.)

### Consequence 2 — the ≤600 V solid-state PhotoMOS combiner is **ELIMINATED**

`hv-mosfet-optocoupler-switch` (T2) was the fallback *conditional on the class landing at ≤600 V*
(TOPO-07). At 1 kV **its parts do not reach**. The §Q1/§6 branch "if ≤600 V, re-run the T1-vs-T2 vote"
is closed and cannot be reopened without changing modules.

### Consequence 3 — 1 kV / 0.5 mA **is** the deliberate worst case session 1 sized against

The §6 default *"size everything for the worst case 1 kV / 0.5 mA / 0.5 W"* turned out to be exactly
right. All existing clearance / bleed / monitor arithmetic applies **directly**, with no rescaling.
**Monitor-divider loading is MARGINAL at this class** — a 5 µA divider is **1.00 % of Inom**, exactly at
the adopted budget. This is now the binding constraint on the monitor, not a footnote.

### Consequence 4 — the modules are **IN HAND**

Everything §Q1/§Q2/§6 listed as *"unmeasurable, assumed"* is now **BENCH-MEASURABLE**, and the pin
positions are **CALIPER-MEASURABLE**. The four unpublished module numbers (VSET step response, HV output
capacitance, internal bleeder resistance, turn-on time from +VIN) move from "assumption we must live
with" to "afternoon of bench work". Session 2 writes the procedure.

## G0-A3 — COMMS (answers Q4) — verbatim

> **Both serial and network, with FULL WRITE AUTHORITY on both.**

**The human chose this deliberately, over §Q4's recommended read-only-network default, and made that
choice with the risk stated.** Do **not** re-litigate it and do **not** quietly downgrade the network to
read-only. §Q4's recommendation is overturned; the reasoning behind it is retained below as the record
of what is being accepted.

**What it changes is where the safety burden sits.** With HV set-point and enable commands reachable
over the network, the **hardware interlock, the hardware `VSET` clamp, and the soft limits carry the
ENTIRE safety case.** Design to that. Two things that §Q4 treated as options are now **required parts of
the design**:

1. an explicit **arm/disarm** step, and
2. a **comms-loss watchdog that fails to HV-OFF**.

## G0-A4 — ⚠ **NEW FEATURE — SCOPE CHANGE, added by the human after the first three answers** ⚠

> **"One added feature I would like is to be able to choose between a single 'bipolar' output or two
> unipolar outputs — that would actually be a nice feature that gives us maximum flexibility with the
> design."**

**This DIRECTLY AMENDS the original brief**, which said *"explicitly **not** two independent unipolar
outputs"*. The brief is **superseded on this point**. Dual-mode is a **first-class requirement**, not a
bolt-on.

| Mode | Behaviour |
|---|---|
| **MODE 1 — BIPOLAR COMBINED** | Both modules route to **ONE** output terminal, one at a time, break-before-make, with the deselected module bled to ground. This is the behaviour designed so far. |
| **MODE 2 — DUAL UNIPOLAR** | The positive module drives **output A**, the negative module drives **output B**, **INDEPENDENTLY**, and **BOTH MAY BE ENERGISED SIMULTANEOUSLY.** That is the whole point of the mode. |

### The safety invariant is RESTATED, not discarded

The brief's invariant (a) was *"impossible to enable both modules into the output simultaneously"*. Read
literally, **mode 2 violates it**. The correct generalisation — which preserves the entire safety intent
while permitting mode 2 — is:

> **It must be impossible for both modules to be connected to the SAME output node simultaneously.**

Enforce **that** in hardware. In mode 1 it forbids the both-enabled state exactly as before; in mode 2 it
is satisfied **structurally**, because the two modules are on physically different nodes.

### ⚠ The hard part, and the thing most likely to be got wrong

**The interlock is now MODE-AWARE, which makes the mode itself a SAFETY INPUT.** If the mode is a
software-commanded bit, then a firmware fault, a stuck GPIO, or a network command (and G0-A3 grants the
network write authority) can assert *"mode 2, both modules permitted"* while the HV routing element is
physically still in the mode-1 position — **which connects both modules to the same node.** That is
precisely the forbidden state, reached through exactly the kind of firmware-promise path `CLAUDE.md`
forbids.

**THEREFORE: the interlock permissive MUST be derived from the ACTUAL PHYSICAL POSITION of the routing
element** — **NEVER from the commanded mode bit.** Prove it in the truth table.

Two mechanisms, both to be evaluated, one to be recommended at G1:

| | Mechanism | Trade |
|---|---|---|
| **(a)** | Mode set by a **PHYSICAL human-set element** (link, keyed switch) that software cannot change | **Safest**, but costs the remote flexibility the human explicitly asked for |
| **(b)** | Mode set by a **relay whose real armature position feeds the interlock** | Keeps the flexibility; **the sense path and its own failure modes then become safety-critical** and must be analysed |

State the trade plainly and let it surface at G1 rather than burying it.

> ### ◀ ANSWERED 2026-07-23 by **G0-A5** — **mechanism (a). The trade did not survive contact with the
> > human's own use case.** Session 1 framed (a)'s cost as *"loses the remote flexibility the human asked
> for"*. **The human pointed out that cost is illusory**: changing between one-output and two-output
> operation **requires physically re-cabling the instrument anyway**, so remote mode selection was never
> usable. Mechanism (b) is therefore **rejected**, there is **no mode relay**, and the sense-path failure
> analysis (b) demanded is **not needed because the sense path does not exist**. See **G0-A5** below.

### Consequences that CHANGE already-computed numbers — all propagated

1. **CLEARANCE.** In mode 2, +1 kV and −1 kV coexist as a **STEADY-STATE NORMAL OPERATING CONDITION**,
   on the board and at two connectors simultaneously. The **2 kV differential between `HV_POS` and
   `HV_NEG` is no longer a fault case or a topology-conditional worst case — it is the normal condition,
   permanently.** This binds board clearance, the netclass rules, the spacing between the two output
   connectors, and board area. Session 1 left this "topology-conditional"; **it is now settled and
   binding** (`DECISIONS.md` NUM-02, NUM-03, MODE-06).
2. **POWER.** Both modules can be at full output at once ⇒ size the supply for **BOTH loaded
   simultaneously** (2 × <180 mA at 5 V for the modules alone), plus ESP32 WiFi TX bursts. The
   *"only one is ever enabled, so size for one plus margin"* argument is **DEAD — do not use it.**
3. **MONITORING.** Invariant (c) — independent output monitoring — now applies to **TWO** outputs. That
   is a **second independent HV divider string**, and each string loads its own module by a fraction of
   the same 0.5 mA Inom (a 5 µA divider is **1.00 %** of Inom). Budget the loading **per output**.
4. **DISCHARGE.** Invariant (b) now applies to **both** output nodes: each needs a defined bleed path on
   disable **and on mode change**. **A MODE CHANGE is a new transition that must be as safe as a polarity
   changeover** — both outputs to zero, both modules disabled, dwell for bleed, **then** move the routing
   element **cold**. Add it to the state machine as a first-class transition with its own timeouts.
5. **CONNECTORS.** **Two** HV output connectors, not one, spaced for the full **2 kV** differential.
6. **PANEL / UX.** The mode must be **unambiguously indicated to the operator**, because *which terminal
   is live* differs between modes, and a wrong assumption at 1 kV is a shock hazard.

## G0-A5 — ⬛ **MODE SELECTION IS A PHYSICAL SWITCH. DECIDED BY THE HUMAN. NOT AN OPEN QUESTION.** ⬛

> **"I think we can have a physical switch to move from unipolar mode (two outputs) to pseudo-bipolar
> mode (single output with switching across 0) — we would need to physically change cables, anyways, so
> we can flip a physical switch. This will also make it fault tolerant."**

**This ANSWERS the question G0-A4 created** (§O-7, `DECISIONS.md` MODE-04): mechanism **(a)**, a physical
human-set element. **There is NO mode relay. Do not design one. Do not re-evaluate relay-vs-switch — it
is settled.**

**The human's reasoning is correct and should be visible, not just the conclusion.** Session 1 costed
mechanism (a) as *"safest, but costs the remote flexibility the human explicitly asked for"*. That cost
was **never real**: switching between one-output and two-output operation means **moving HV cables**, a
hands-on, in-the-room operation. A remote mode command could never have completed the job, so it bought
nothing while carrying the worst hazard in the design.

### What this SIMPLIFIES — take all of it; it is a strictly better design

| # | Simplification |
|---|---|
| 1 | **One fewer HV switching element** in the output path ⇒ one fewer weld risk and one fewer part that must be rated to 1 kV. |
| 2 | **No hot-switching hazard on mode change**, and **no mode-change state-machine transition to get right** — mode change is by nature a **powered-down, cables-off, human-in-the-loop** operation. |
| 3 | ⬛ **The mode is no longer a safety INPUT that firmware can assert falsely. It is a PHYSICAL FACT.** A network command cannot reach it. This is what the human means by *"fault tolerant"*, and it **removes the single most dangerous path the G0-A4 design had to defend against** — the "software says mode 2, HV routing is still mode 1" state. |
| 4 | ⬛ **The interlock permissive and the HV routing are moved BY THE SAME ARMATURE**, so they **cannot disagree by construction.** That is **far stronger than a sensed relay position**, which can (a sense contact mis-wired to report the coil command instead of the armature is invisible in normal operation and fatal in the fault — `DECISIONS.md` MODE-04, now moot). |

### What it STILL DEMANDS — this is not free

1. **SWITCH SELECTION AND RATING.** The switch carries the HV routing. It must be rated for **1 kV
   working on the switched pole**, and — critically — for the **full 2 kV between poles carrying
   opposite polarities**, if any such pair exists in the chosen arrangement. Panel switches rated for
   kilovolts are a real and somewhat awkward part class. **Evaluate: HV rotary switches · ceramic wafer
   switches · and the alternative of an HV-rated jumper/link block or a re-plugged HV cable acting as the
   selector.** Give real candidates with real voltage ratings; flag every MPN `[unverified-MPN]`.
   **If the honest answer is that a suitable panel switch is expensive or unobtainable and a link block
   or connector re-plug is better engineering, SAY SO** — the human's requirement is *"a physical thing
   the operator moves"*, **not specifically a toggle switch**.
2. **AUXILIARY LV POLES.** The switch must carry **extra low-voltage poles** telling **both** the
   hardware interlock **and** the ESP32 which mode is physically selected. The interlock must be
   **COMBINATIONAL** on those contacts — **never latched, never cached in firmware.**
3. ⬛ **CONTACT TIMING — the one genuinely subtle requirement.** The dangerous transition is
   **unipolar → pseudo-bipolar performed while both modules are energised**, because that routes both
   modules onto the same node. **Specify that the LV interlock poles BREAK BEFORE the HV poles MAKE** —
   the auxiliary contacts must **lead** the HV contacts — so the interlock has already commanded both
   modules off before any HV re-routing occurs. State the timing margin required, and say what happens
   if a switch not meeting it is fitted.
   **Report the hazard honestly rather than overstating it:** the modules are short-circuit protected
   and current-limited to ≈0.75 mA (PART-13), so the worst case if this is got wrong is a
   **current-limited polarity fight, not an energetic fault.** Design for it anyway.
4. **OPERATING PROCEDURE AND GUARDING.** Mode change is specified as a **powered-down** operation. Say
   how that is enforced or encouraged: a **guard/cover over the switch**, a **panel legend**, and an
   **interlock that forces HV OFF whenever the aux contacts are in transit or in an illegal intermediate
   state.** **Firmware reads the mode at boot AND continuously; a mode change detected at runtime must
   force HV OFF IMMEDIATELY rather than attempting a graceful transition.**
5. **ILLEGAL / INTERMEDIATE POSITIONS.** A rotary or multi-pole switch **can sit between detents.**
   Define what the hardware does when the aux contacts read **neither valid mode**, and make that state
   **safe** (both modules off, both outputs bled).

### What G0-A5 does NOT change

The **restated invariant (a)** of G0-A4 is untouched: *it must be impossible for both modules to be
connected to the SAME output node simultaneously.* A5 changes **how the mode input is obtained**, not
what must be forbidden. The mode-aware interlock algebra of `CONTROL_ARCHITECTURE.md` §3.3a stands
**unchanged in form**; only the **origin of `MODE_POS`** changes — from a relay aux contact to a **switch
aux pole** — and `MODE_CMD` **ceases to exist as a writable bit at all**, which is a strict improvement.

Also unchanged: **every clearance, connector, monitor, bleed and power consequence of G0-A4** (the six
numbered consequences above). A5 removes an element; it removes no requirement.

---

# GATE G0 — questions for the human

**⚠ EVERYTHING BELOW THIS LINE IS THE PRE-ANSWER RECORD, retained verbatim.** It is kept because it is
the reasoning that made the answers meaningful — the candidate answers, the recommended defaults, and
the stated cost of each. Where an answer overturned a recommendation, an inline **`◀ ANSWERED`** note
says so at the point of the recommendation. No analysis has been deleted.

**Seven questions. One of them is much more important than the other six.**

This is the batched question set required by bootstrap Principle 7: *ask blocking unknowns once in a
batch, log assumptions and proceed.* Everything that could be assumed **has been assumed**, with a
stated default, and is recorded in `docs/DECISIONS.md` as an `assumed-pending-G0` row — about 45 of
them. Only questions whose **answer changes the design** appear here.

Each question gives: the question · why it matters · the candidate answers · **our recommended
default with reasoning** · what happens if we simply proceed on that default.

If you answer nothing, see §6 — we can proceed on defaults for six of the seven. **Not for Q1.**

---

# ⬛ Q1 — THE ONE THAT COMES FIRST

## **Is smooth THROUGH-ZERO operation required, or is set-and-hold with polarity changeover acceptable?**

> **◀ ANSWERED 2026-07-23 — candidate answer A. See G0-A1 at the top.** Set-and-hold with polarity
> changeover is acceptable; a ~1 s dead-band with the output clamped to ground is acceptable. The
> module family is **not** disqualified. `hv-relay-changeover` is adopted. The recommended default
> below was **confirmed**, not overturned.

The brief calls this *"the key behavioral question"* and says the answer selects the combiner
topology. It does more than that. **It may disqualify the module family.**

### Why it matters

We analysed five combiner topologies and had three independent judges rank them. Three of the five
analysts and all three judges independently reached the same conclusion:

> **If smooth through-zero is required, the iseg APS family is itself disqualified — and the entire
> topology comparison is moot.**

Three reasons, all properties of the module, none fixable by any combiner:

1. **The datasheet guarantees nothing near zero.** Table 1, note 1, verbatim `[verified-run, four
   independent extractions]`: *"Specifications for stability, ripple and noise are guaranteed in the
   range 2 %·Vnom < Vout ≤ Vnom."* On a 1 kV module that is a **±20 V band in which the output is
   not specified** — not "worse", *unspecified*.
2. **The module cannot sink current.** It is a resonant converter with a rectifier output. Rising
   edges are driven; falling edges are set by the load plus an unpublished internal bleed. Rise and
   fall obey different physics.
3. **The module's own command path has a ~100 ms pole** (100 kΩ into 1 µF, read off the control-principle
   figure by four agents independently) — about 460–690 ms to settle. The fastest solid-state switch
   we found turns off in 0.04 ms, **12 500× faster than the module settles.** Nothing we build near
   the output makes this quicker.

There is also a counter-intuitive result worth your attention, produced by the judge whose lens most
favoured through-zero: **the switched topologies have a better ZERO than the through-zero topology
does.** A switched design's zero is "both modules unpowered, terminal tied to ground through a bleed"
— exactly 0.000 V, zero temperature coefficient, zero ripple. The continuous topology reaches zero by
cancelling two live 400 V rails, so its zero drifts **14–28 mV/K** (141–283 mV over a 10 K lab swing,
up to 1.13 V over the specified operating range) and carries 7–21 mVpp of ripple. So the "no
through-zero" penalty is **entirely a penalty on TIME**, not on the accuracy of zero.

### Candidate answers

| | Answer | Consequence |
|---|---|---|
| **A** | **Set-and-hold with polarity changeover is acceptable.** A ~1 s dead-band at each polarity crossing, during which the output is actively clamped to ground. | Proceed with `hv-relay-changeover`. Everything in `PLAN.md` runs as written. |
| **B** | Through-zero required, but a **±2 %·Vnom unspecified band** (±20 V at 1 kV) and a slow traverse are tolerable. | This is really A with a slow sweep. Proceed as A, and we document the band on the panel. |
| **C** | Through-zero genuinely required, **and** the load is capacitive at **<10 µA**, **and** you will amend invariant (a) in writing to "output magnitude and polarity bounded in hardware". | The `series-stack-driven-midpoint` topology becomes the only candidate. It costs a factor of 2 in voltage (800 V modules for ±400 V out), delivers ~5 µA, and **both modules are always enabled — the forbidden state is the operating mode.** |
| **D** | Through-zero genuinely required and the load is not tiny. | **Stop.** The APS family is the wrong part. This is a module-selection decision, not a combiner decision, and it belongs to you. |

### Our recommended default: **A — set-and-hold with polarity changeover**

Reasoning. Bipolar HV bias for detectors, electrostatic optics, or a Kelvin probe is set-and-hold in
practice: you choose a bias, you hold it, you occasionally change it. A ~1 s crossing is invisible in
that use. Answer A also buys the strongest safety story on the panel — an air-gap OFF state, a bleed
that is structural rather than timed, and `+VIN` removal as the primary disable — none of which the
continuous topology can offer. And if we later discover through-zero is wanted, we lose a board; if we
build the continuous topology and later discover we needed 100 µA of load current, we lose a board
**and** the module pair.

### If we proceed on this default without hearing from you

We build a supply that traverses zero in about one second with the output clamped to ground while it
does. If you then need a continuous sweep, the combiner and probably the modules are scrap.
**This is the one default we are least comfortable assuming**, which is why it is Q1.

---

# (a) Module selection

## Q2 — Which module class: voltage, current, and 5 V/0.5 W vs 12 V/1 W?

> **◀ ANSWERED 2026-07-23 — and the question turned out to be moot in form: THE MODULES ARE ALREADY
> OWNED.** The answer arrived as *"we have the aps10504 (both negative and positive polarity)"* ⇒
> **`AP010504P05` + `AP010504N05`**, i.e. **1 kV / 0.5 mA / 0.5 W / 5 V in / Vref 2.5 V**, both
> polarities in hand. Full decode and the frozen parameter set are in **G0-A2** at the top.
>
> **The recommendation below is OVERTURNED.** Session 1 recommended *"the 1 W / 12 V family"* on an
> explicit **safety** argument — Vref = 5 V is immune to a 5 V logic rail. G0 answered **0.5 W / 5 V,
> Vref = 2.5 V.** Therefore the hazard that recommendation existed to avoid is now the condition we
> must design against: **3.3 V on a 2.5 V-Vref set input = 132 % of Vnom ≈ 1320 V, on an input that is
> "internally not limited".** The hardware `VSET` clamp is promoted to a primary safety element.
>
> Also overturned: the *"argues for the LOWEST Vnom that meets your maximum requirement"* bullet is
> moot — the class is not ours to choose. And the *"cheap ≤600 V combiner"* bullet is closed: at 1 kV
> the PhotoMOS parts do not reach, so **T2 is eliminated, not merely un-chosen.**
>
> Confirmed, not overturned: the **provisional working assumption of 1 kV / 0.5 mA / 0.5 W** was exactly
> right, so every number sized against it stands unchanged.

### Why it matters

More than any other answer. The iseg item code encodes **voltage class AND polarity**, and the part is
quote-only and build-to-order, so **both are irreversible at order time**. Downstream:

- **Clearance, hence board area.** Recommended HV-to-GND spacing scales linearly above 500 V. At 1 kV
  we need ~7.5 mm HV-to-GND and ~15 mm between the two HV branches; at 200 V those roughly quarter.
- **Whether the cheap combiner is legal.** The solid-state alternative caps the instrument at
  **600 V** — because of the *switch*, not the module. Choosing ≤600 V unlocks a combiner that is
  ~40 % of the cost, ~¼ the board area, has no coil power, and — unlike reed relays — cannot be
  closed by a stray magnet.
- **The set-path rail.** The 0.5 W family has Vref = 2.5 V, so a 3.3 V logic fault commands **132 %**
  of nominal. The 1 W family has Vref = 5 V, immune to a 5 V logic rail.
- **The monitor.** Monitor accuracy is 1 %·Vnom, and specs hold only above 2 %·Vnom, so the lowest
  usable output sits above 2 % of Vnom. **This argues for the LOWEST Vnom that meets your maximum
  requirement, not for headroom.**
- **The supply rail and connector.**

### Candidate answers

Vnom ∈ {200, 400, 600, 800, 1000} V × family ∈ {0.5 W @ 5 V in, 2.5 mA…0.5 mA; 1 W @ 12 V in,
5 mA…1 mA}. Both polarities of the same class are required.

### Our recommended default: **the 1 W / 12 V family, at the lowest Vnom that meets your maximum**

The family choice is a **safety** argument, not a convenience one: Vref = 5 V is immune to a 5 V logic
rail, it doubles the set-point full scale (halving the relative effect of every millivolt of error),
and it gives 2× the output current at every voltage class — for about 2 W more input power. The
voltage choice follows from your answer to Q3.

**Provisional working assumption if you say nothing: 1 kV / 0.5 mA / 0.5 W** — deliberately the
*worst* case, because it is the only configuration where monitor loading is marginal (exactly 1.00 %
of Inom) and discharge times are long. Every other configuration relaxes constraints, so sizing
against it is safe. But it is almost certainly not what you want to buy.

### If we proceed on this default without hearing from you

We size clearance, bleed, divider and supply for 1 kV and pick the relay combiner, which spans the
whole family. The board is over-spaced and somewhat larger than needed, but **correct**. The real cost
is that we cannot order modules — and they are the long-lead, dominant BOM line. **No agent obtained
an iseg quote this session; that is a task for whoever has the vendor relationship.**

---

# (b) Output specification

## Q3 — Full-scale ±V, maximum load current, load capacitance, required ripple

> **◀ NOT ANSWERED at G0. STILL OPEN — proceeding on the §6 default.** Partially *constrained* by
> G0-A2: full scale is now fixed at **±1000 V** (mode 1) / **+1000 V and −1000 V simultaneously**
> (mode 2, per G0-A4), and available load current is bounded by **Inom = 0.5 mA, Iout ≤ 0.75 mA**.
> What remains genuinely unknown is **`C_load`** and **the required ripple**, and one clarification is
> now mandatory in every quoted low-end spec: **ripple/noise is guaranteed only above 2 %·Vnom = 20 V;
> below 20 V the output is UNSPECIFIED, not merely worse.**

### Why it matters

- **Load current separates two topologies by a factor of ~470** (2.5 mA vs 5.3 µA). It is the single
  number that decides whether the continuous-through-zero option in Q1-C is even physically available.
- **Load capacitance sets everything about discharge.** It is *your* cable and *your* detector, not
  ours: 100 pF gives 92 ms to safe, 100 nF gives 92 s. It also sets the fault-energy classification.
- **Ripple** decides whether an output filter is needed — and we cannot fit a big one (see below).

### Candidate answers

Full scale: some ±V ≤ the module Vnom. Load: resistive or capacitive; a current in µA or mA; a
capacitance in pF or nF. Ripple: the module gives typ <10 mVpp / max <30 mVpp **above 10 Hz** — note
that **nothing below 10 Hz is specified anywhere**, and for a DC bias read on a DMM, sub-10 Hz wander
*is* the measurement.

### Our recommended default

- **Load capacitance ≤ 10 nF**, declared as a **hard interface constraint** printed on the panel and
  in the manual. This is simultaneously the discharge limit (10 nF → 2.56 s to 60 V, passes;
  100 nF → 25.6 s, fails touch-safety) and the fault-energy limit. Maximum permissible is ~19.5 nF.
- **No bulk HV filter capacitor on the board.** Total output capacitance stays **below 50 nF**, above
  which the instrument becomes a hazardous-stored-*energy* source rather than merely a
  hazardous-*voltage* one.
- **Load current: assume ≤ 50 % of Inom is available to you**, the rest going to the bleed (10 %),
  the monitor divider (2 %) and margin.
- **Ripple: whatever the module gives**, plus the small filtering our output impedance affords.

### If we proceed on this default without hearing from you

We build to ±(module Vnom), ≤10 nF, no bulk output capacitor. If your detector is a large-area device
with tens of nF of capacitance, **the discharge analysis and the touch-safety argument both fail** and
must be redone with a switched bleed. If your load is resistive at more than half of Inom, the
combiner choice is unaffected but the module class is.

---

# (c) Communications

## Q4 — Serial, network, or both — and may the network **write**?

> **◀ ANSWERED 2026-07-23 — BOTH, WITH FULL WRITE AUTHORITY ON BOTH. The recommendation below is
> OVERTURNED.** Session 1 recommended *serial with full write authority; network read-only telemetry,
> defaulting to OFF, with write authority behind a PHYSICAL switch*. **G0 answered: both transports,
> full write authority on both** — deliberately, with the risk stated. Do not re-litigate it and do not
> quietly downgrade the network to read-only.
>
> The reasoning below is retained because it is exactly the statement of **what is being accepted**.
> The "If we proceed on this default" paragraph's claim that this is a **low-risk default** no longer
> applies: with HV set-point and enable commands reachable over the network, the **hardware interlock,
> the hardware `VSET` clamp and the soft limits carry the ENTIRE safety case.** An explicit
> **arm/disarm** step and a **comms-loss watchdog that fails to HV-OFF** are now **required**, not
> optional. Risk R-10 in `SCOPE.md` is escalated accordingly, and the bounded-parser / fuzzing work in
> the §Q4 precedent paragraph becomes mandatory scoped work rather than a contingency.

### Why it matters

Not the transport. **The write authority.** A network path that can change the setpoint is a remote
code execution path to a device that can kill someone. If it is in scope, authentication, session
management, and OTA security become real, maintained work that must be scoped now — not assumed away.

There is a concrete precedent in this project's own reference material: the previous board's vendored
command parser contains an **unbounded buffer write reachable from the control port**, sitting as the
last member of its object so an over-long line writes into adjacent globals. We are not reusing it.

Secondary: whether this integrates with SIMPLE or runs standalone changes the protocol surface, and
ESP32-S3 has no Ethernet MAC, so wired Ethernet means a W5500 over SPI.

### Candidate answers

Serial only · serial + network read-only telemetry · serial + full network control · WiFi vs wired ·
standalone vs SIMPLE-integrated.

### Our recommended default: **serial with full write authority; network read-only telemetry, defaulting to OFF, with write authority behind a PHYSICAL switch**

You get remote monitoring for free and remote control only when someone has physically walked to the
instrument and enabled it. The physical switch is one part and it converts a security problem into a
mechanical one.

### If we proceed on this default without hearing from you

Firmware ships with a full command surface on USB/UART and a read-only subset on the network. If you
need unattended remote control later, it is a firmware change plus a security review — not a board
change. **Low-risk default.**

---

# (d) Safety envelope

## Q5 — Working standard, conformal coating, and does the enclosure exist?

> **◀ NOT ANSWERED at G0. STILL OPEN — proceeding on the §6 defaults (no coating; SHV; enclosure
> assumed bought).** Two things got *worse*, not better, and must be carried forward:
> - **Sub-question 1 (the standard) is unchanged and remains the project's highest risk.** Every
>   clearance number stays tagged **`[unverified-primary]`** and the DRC values stay conservative.
>   A human must read a **primary** copy before G1 closes.
> - **G0-A4 raises the stakes on the numbers themselves.** In dual-unipolar mode the **2 kV
>   `HV_POS`↔`HV_NEG` differential is the NORMAL steady-state condition**, not a fault case — so the
>   worst gap on the board is now permanent and is the gap most dependent on the unverified constant.
> - **Enclosure requirements gain a seventh item** (G0-A4 consequence 6): the **output mode must be
>   unambiguously indicated to the operator**, because which terminal is live differs by mode.
>   **◀ G0-A5 makes this cheaper and better**: the mode **is** a panel switch, so the switch's own
>   position **is** the indication, and it cannot lie. The enclosure requirement becomes **legending and
>   guarding the switch** rather than driving an indicator from a sense contact.
> - **Enclosure requirements gain an EIGHTH item (G0-A5): a GUARD or COVER over the mode switch**, plus a
>   panel legend stating that mode change is a **powered-down, cables-off** operation.
> - **Connector count doubles**: two HV output connectors, spaced for the full 2 kV.

### Why it matters

**Three sub-questions, and the coating one must be answered before layout, not after.**

1. **Which clearance standard governs?** This is our **highest project risk**. The constants we
   currently hold are `[recalled]` from memory and web reproductions; the primary standards are
   paywalled and not on this machine. Three independent reviewers showed that the "independent
   cross-check" we relied on was an **algebraic tautology** and that both of its supposedly
   independent sources were **the same web page**. Four documents in this repo currently carry four
   mutually incompatible numbers. **A wrong constant becomes a DRC rule and is undiscoverable after
   fabrication.**
2. **Conformal coating: yes or no?** It is the difference between the coated and uncoated columns —
   about **1.86×** on every HV gap, i.e. 10.0 mm vs 5.4 mm at the worst gap on the board. It is a
   *process* commitment (masking, cure, rework difficulty) that must be made **before layout**.
3. **Does the enclosure exist, or are we designing it too?** We have drafted six requirements
   (earthed metal chassis; tool-required access; a lid interlock that **CLOSES** to pull the enable
   pin high — note the polarity, a switch that *opens* on lid removal is exactly backwards for this
   part; ventilation for 4.2–6.4 W; HV-present indication; labelling). Whether satisfying them is our
   scope is a scope question.

### Our recommended default

- **Standard:** we proceed on the recalled uncoated-external column, and **a human obtains a primary
  copy before G1**. This is a task, not an assumption — it is on the pre-fab checklist as a hard gate.
- **Coating: NO.** The conservative direction. Uncoated demands wider gaps, which is safe if we later
  coat, whereas designing to coated spacing and then skipping the coating is a flashover.
- **Connector: SHV.** 5 kV rating; its reversed gender and protruding insulator make it mechanically
  **unable** to mate a BNC (MHV can — which is why MHV is deprecated); the live conductor is
  untouchable when unmated; and it is the detector-physics default so no adapter is ever needed.
- **Enclosure: assume it exists and is bought**, and we deliver a mechanical drawing plus the six
  requirements above.

### If we proceed on this default without hearing from you

An uncoated board with generous gaps — larger than necessary but safe — and a set of enclosure
requirements you must satisfy. **The one thing that cannot be deferred: someone must read the primary
standard before G1.**

---

# (e) Everything else that genuinely blocks

## Q6 — For a welded or shorted switch: is DETECTION sufficient, or is PREVENTION required?

> **◀ NOT ANSWERED at G0. STILL OPEN — proceeding on the §6 default (detection is sufficient, with a
> mandatory power-up self-test).** G0-A1 narrows it: with the solid-state candidate eliminated by
> G0-A2, only the **welded relay contact** case survives — and the §Q6 asymmetry note now works in our
> favour, because a welded contact **stays exclusive** whereas the shorted-MOSFET case (which did not)
> no longer exists on this board.
> **G0-A4 adds a second welded-contact case that did not exist before:** a welded or mis-positioned
> **MODE routing element** is the one fault that can put both modules on the same node while the
> interlock believes mode 2 is in force. That is why the mode permissive must come from the armature's
> **physical position**, and it must be inside the power-up self-test.
> **◀ G0-A5 SHRINKS THIS CASE SUBSTANTIALLY.** With the mode set by a **physical switch** whose LV aux
> poles and HV poles are **moved by the same armature**, the "welded contact vs. disagreeing interlock"
> fault **cannot arise from a disagreement** — there is nothing to disagree with. What survives is
> narrower and must still be tested: a **welded HV pole** on the mode switch (the switch is turned but
> one HV pole stays made) and an **intermediate/between-detent position**. Both stay in the power-up
> self-test; neither is the "software believes the wrong mode" class, which A5 **eliminates**.

### Why it matters

**This can eliminate every candidate on the panel.**

Every topology we studied can be defeated by one mechanical or semiconductor fault: a welded relay
contact, or a shorted MOSFET, leaves one module permanently connected to the output. Selecting the
other module then puts both on the output — a violation of non-negotiable invariant (a) from a
**single** fault.

No contact-based or solid-state topology on the panel can *prevent* this. They can only *detect* it,
via a power-up self-test that energises one module and requires the output to stay at zero. Our
recommendation is built on detection, with bounding arguments (15–30× inrush margin, 10⁸-operation
cold-switch life ≈ 2 700 years at 100 changeovers/day, and — importantly — the modules cannot sustain
an arc at 0.75 mA, three orders below the ~1 A a tungsten arc needs).

There is also an asymmetry worth knowing: a **welded relay contact stays exclusive** (it is stuck in
one position), whereas a **shorted MOSFET does not**, and its symptom is a *silent zero output* that
is indistinguishable from "the module has not ramped yet".

### Our recommended default: **detection is sufficient**, with the self-test mandatory at every power-up

Justified by the arc argument and the operation-count margin. Note that the self-test as originally
designed **cannot execute** — two independent reviewers found that the circuit as drawn has no
reachable both-off state, and that with no per-branch monitor the test cannot distinguish "stimulus
applied and blocked" from "no stimulus was ever applied". Both fixes are cheap (~$22 and one switch)
and are already mandatory corrections in `COMBINER_STUDY.md` §5.2.

### If we proceed on this default without hearing from you

A board where a welded contact is improbable, bounded, and caught at power-up — but not prevented. If
your safety case requires *prevention*, tell us at G0 and we re-open the topology study, because
**none of the five candidates survives that requirement.**

---

## Q7 — Who owns the iseg conversation, and may we commit to long-lead parts at G1?

> **◀ PARTIALLY OVERTAKEN BY EVENTS, not answered.** G0-A2 removes the **procurement half (ii)
> entirely for the dominant BOM line**: the modules are **already owned**, so no iseg quote, lead time
> or MOQ is needed for them, and the schedule is no longer unbounded on that line. The **relay and HV
> passive** lead-time risk (R-7) is untouched and still binds.
>
> The **three technical questions (i) remain open**, but two of them have been **defanged** by G0-A1
> and one has been **re-scoped**:
> - *Reverse voltage on an OFF module's HV pin* — this decided **whether diode-OR was legal at all**.
>   Diode-OR is now rejected outright (G0-A1), and in the relay topology the deselected module's HV pin
>   is clamped to its own bleed by the NC contact, so it never sees the other polarity. **The question
>   stops being topology-deciding** and becomes a bounding check on the open-contact condition.
> - *GND-to-earth / case isolation rating* — foreclosed two topologies that are now rejected anyway.
>   Still worth asking, still not permission-in-absence.
> - *The current-monitor discrepancy* — **unchanged and still open** (PART-20).
>
> **New**: three of the four "nobody can answer this from a keyboard" module numbers are now
> **measurable on the bench, because the modules are in hand.** That converts a vendor dependency into
> an afternoon of work.

### Why it matters

Two things nobody could do from a keyboard this session, and both gate the schedule rather than the
design:

**(i) Three questions must go to iseg**, and one of them can invalidate a topology:
- *What reverse voltage can an OFF module's HV pin tolerate?* Because disabling a module does **not**
  disconnect it (the enable pin grounds an internal set node; the HV pin stays connected to the
  multiplier), any shared-output combiner presents the other module's full voltage across it,
  reversed. **This single unknown decides whether opposite-polarity diode-OR is legal at all.**
- *Is there any GND-to-earth / case isolation rating?* Its absence currently forecloses two topologies
  and any future series-stacking.
- *The current-monitor discrepancy:* the specification table gives a "current monitor accuracy" but
  the pin table lists seven pins and **none is a current monitor**. Four agents found this
  independently and none resolved it. It decides whether output-current readback exists at all.

**(ii) Procurement.** No agent obtained an iseg quote (class × polarity × lead time × MOQ), and the
modules are the dominant BOM line in every candidate. Separately: the recommended relay is
build-to-order and **two independent agents failed to price it** (three site timeouts and an HTTP
403); the verified in-stock alternatives carry 10- and 18-week manufacturer leads; and across four
agents' searches, HV resistors came back **0-stock, obsolete, or 13-week lead** on nearly every part
checked — exactly one was verified genuinely in stock.

### Our recommended default

Send the three technical questions to iseg now, request a quote now, and **authorise ordering
long-lead parts at G1 rather than at fab**. Ordering at fab is how a four-week board becomes a
four-month board.

### If we proceed on this default without hearing from you

We design against the conservative assumptions (no reverse rating ⇒ never present reverse voltage to
an off module; no isolation rating ⇒ never float a module; no current monitor ⇒ measure it ourselves
if needed) and the design is safe. **But the schedule is unbounded**, because the dominant BOM line
has no quoted lead time.

---

# 6. What we will do if you say nothing → **what actually happened**

*(Pre-answer text retained; the right-hand column is the 2026-07-23 outcome.)*

We can proceed on defaults for **six of the seven**. Not Q1.

| # | Default we would proceed on | **Outcome at G0, 2026-07-23** |
|---|---|---|
| **Q1 through-zero** | **⚠ We would assume set-and-hold with polarity changeover.** This is the one default we are least comfortable assuming — it selects the topology and may select the part family. **Please answer this one even if you answer nothing else.** | ✅ **ANSWERED — default CONFIRMED.** Set-and-hold, ~1 s dead-band clamped to ground. `hv-relay-changeover` adopted; three topologies rejected permanently. |
| Q2 module class | Size everything for the worst case **1 kV / 0.5 mA / 0.5 W**; recommend the **1 W / 12 V** family at the lowest Vnom meeting your requirement. Choose the relay combiner, which spans the whole family. **Cannot order modules.** | ✅ **ANSWERED — recommendation OVERTURNED, sizing assumption CONFIRMED.** Modules already owned: `AP010504P05`/`N05` = **1 kV / 0.5 mA / 0.5 W / 5 V in / Vref 2.5 V**. The 12 V-family recommendation is dead; the 3.3 V hazard it existed to avoid is now the design condition. "Cannot order modules" is moot. |
| Q3 output spec | Full scale = module Vnom · **`C_load ≤ 10 nF` as a hard interface constraint** · no bulk HV output capacitor · budget ≤50 % of Inom to the load · ripple as the module gives it. | ⬜ **NOT ANSWERED — proceeding on this default.** Full scale now pinned by G0-A2 to ±1000 V; `C_load` and required ripple still unknown. |
| Q4 comms | Serial with full write authority; network **read-only telemetry, default OFF**; write authority behind a physical switch. | ✅ **ANSWERED — OVERTURNED.** Both transports, **full write authority on both**. The "low-risk default" framing no longer applies; hardware carries the whole safety case. |
| Q5 safety | **SHV** connector · **no conformal coating** (conservative) · assume the enclosure is bought, deliver a drawing and six requirements · **a human reads the primary clearance standard before G1 — this is a task, not an assumption.** | ⬜ **NOT ANSWERED — proceeding on these defaults**, but now **two SHV connectors** (G0-A4), a **seventh enclosure requirement** (mode indication), and the standards task is **more** load-bearing because the 2 kV gap is permanent. |
| Q6 weld | **Detection**, via a mandatory power-up self-test, plus the two corrections that make that test actually executable. | ⬜ **NOT ANSWERED — proceeding on this default.** Scope grows: the **mode routing element** joins the self-test. |
| Q7 iseg / procurement | Design against conservative assumptions and **order long-lead parts at G1, not at fab**. Schedule remains unbounded until someone gets a quote. | ◐ **OVERTAKEN IN PART.** Modules owned ⇒ the dominant BOM line is no longer a schedule risk and three of its four unknowns are now bench-measurable. Relay/HV-passive lead time (R-7) and the three iseg technical questions remain. |

Alongside these defaults, roughly **45 further assumptions** are already logged as
`assumed-pending-G0` rows in `docs/DECISIONS.md`, each with its evidence and the agent that logged
it. They are not repeated here because none of them changes the design — but they are all overturnable
at G0 at low cost, and they are all in one place so nothing was lost.

---

## Four things we should do regardless of your answers

Recorded here so they are not mistaken for questions:

1. **Someone must read a primary copy of the clearance standard before G1.** Our numbers are
   `[recalled]` and their self-declared "independent cross-check" was shown to be circular.
   **STILL OPEN after G0, and now MORE load-bearing** — G0-A4 makes the 2 kV `HV_POS`↔`HV_NEG` gap a
   permanent normal condition rather than a topology-conditional worst case.
2. **Bench-measure four numbers on one physical module**: set-input step response, HV output
   capacitance, internal bleeder resistance, and turn-on time. iseg publishes **none** of them, and
   three of the four numbers that set every discharge and changeover figure in this project are
   currently assumptions. One afternoon.
   **STILL OPEN — but G0-A2 makes it ACTIONABLE:** the modules are in hand. Session 2 writes the
   procedure. There is no longer any excuse for these staying assumptions past G1.
3. **Measure one physical module with calipers.** Nothing in this project has ever touched hardware.
   Our land pattern spends its tolerance allowance on a pin-position tolerance the vendor does not
   publish. **STILL OPEN — and now ACTIONABLE for the same reason** (PART-14, PART-23, LIB-03, LIB-18).
4. ~~**Close the Phase 0 gate.**~~ ✅ **DONE, same session.** The throwaway board now produces 24
   gerber layers + `.gbrjob` + `.drl`, after zone fill (2178.23 mm²) and DRC (0 violations, 0
   unconnected). `docs/ENVIRONMENT.md` records the verified stack, the exact command surface, and
   what each gate cannot see. Four process findings came out of it — `PIPELINE_LOG.md` PL-29…PL-32.

---

# 7. What is STILL OPEN after G0 — carry these forward, flagged

G0 is signed off. It did **not** close everything. Nothing in this list may be silently resolved.

| # | Still open | Why it survived G0 | Owner gate |
|---|---|---|---|
| **O-1** | **The clearance/creepage constants are `[recalled]` and their claimed internal cross-check was shown to be circular** (`STATUS.md` 1.2, `DECISIONS.md` NUM-01). | Q5 was not answered, and no answer could have fixed it — it needs a **primary document**, not a decision. Every clearance number keeps the tag **`[unverified-primary]`**; DRC values stay conservative. | **Human reads a primary copy before G1 closes.** |
| **O-2** | **Four module parameters iseg does not publish**: `VSET` step response, HV output capacitance, internal bleeder resistance, turn-on time from `+VIN`. | Vendor never asked; but G0-A2 puts the modules **in hand**, so these are now measurable. | Bench, before G1. Session 2 writes the procedure. |
| **O-3** | `C_load` and required ripple (Q3). | Not answered. | G1 / interface contract. |
| **O-4** | Conformal coating yes/no; working standard; enclosure ownership (Q5). | Not answered. Defaults stand: **no coating**, SHV, enclosure bought. Note the standing internal tension: ARCH-14 *mandates* coating over the divider region for leakage while NUM-18 assumes **no** coating for clearance — both cannot be true and it must be resolved before layout. | G1, **before layout**. |
| **O-5** | Weld: detection vs prevention (Q6). | Not answered. Default = detection + mandatory power-up self-test. If prevention is ever required, **every candidate on the panel dies** and the topology study reopens. | Human ruling; TOPO-10. |
| **O-6** | The three technical questions for iseg (reverse voltage on an OFF HV pin; GND-to-earth isolation; the current-monitor discrepancy PART-20). | Q7 not answered. Two are defanged by G0-A1; PART-20 is untouched. | One email, before schematic freeze. |
| ~~**O-7**~~ | ~~**NEW, created by G0-A4: which mode mechanism — (a) physical human-set element, or (b) relay with an armature-position sense contact?**~~ | ✅ **CLOSED SAME DAY by G0-A5: mechanism (a), a PHYSICAL SWITCH.** The trade session 1 stated was **false** — remote mode selection could never have worked, because changing modes requires physically re-cabling the instrument. **There is no mode relay and no sense path to analyse.** | ✅ **ANSWERED.** `DECISIONS.md` MODE-04 → `frozen-by-G0` (A5). |
| **O-10** | **NEW, created by G0-A5: WHICH physical element, and can it be sourced?** A panel switch rated **1 kV working per pole and 2 kV between opposite-polarity poles**, with **auxiliary LV poles**, is an awkward part class. Candidates to evaluate: HV rotary switch · ceramic wafer switch · **HV-rated link block** · **HV cable re-plug as the selector**. | G0-A5 fixed the *mechanism*, not the *part*. Every MPN stays `[unverified-MPN]`. **If no suitable panel switch is procurable, a link block or connector re-plug is legitimate and should be recommended rather than forced** — the requirement is "a physical thing the operator moves". | **G1**, with R-7's sourcing risk. `DECISIONS.md` MODE-13. |
| **O-11** | **NEW, created by G0-A5: the contact-timing specification.** The LV aux poles must **BREAK BEFORE** the HV poles **MAKE**, with a stated margin, so the interlock disables both modules before any HV re-routing. What happens if a switch not meeting it is fitted must be stated. | This is the one genuinely subtle requirement A5 creates. **Bounded, not unbounded:** at ≈0.75 mA the worst case is a **current-limited polarity fight, not an energetic fault** (PART-13) — report that honestly, design for it anyway. | **G1**, before the switch MPN is frozen. `DECISIONS.md` MODE-15. |
| **O-8** | **NEW, created by G0-A3: the network write path is a remote-code path to a kilovolt supply.** Bounded parser, auth, session management, OTA security, arm/disarm, comms-loss watchdog are now **scoped work**. | The human accepted this risk knowingly. It is not re-litigable — but it is also not free. | Firmware phase; `SCOPE.md` R-10. |
| **O-9** | Relay and HV-passive availability (R-7): 0-stock / obsolete / 10–18 week leads across four agents' searches; the recommended Form-C relay could not be priced. | Untouched by G0-A2, which only removed the *module* line from the schedule risk. | Order at **G1, not at fab**. |
