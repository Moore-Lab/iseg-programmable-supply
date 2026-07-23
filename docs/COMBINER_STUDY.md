# COMBINER STUDY — ⬛ **DECISION MADE. THE ALTERNATIVES ARE CLOSED.** ⬛

> # ✅ ADOPTED: **`hv-relay-changeover` (T1)**
> ### Decided at GATE G0, **2026-07-23**, by the human. Not a recommendation — a decision.
>
> **`G0-A1`:** *set-and-hold with polarity changeover is acceptable; a ~1 s dead-band at each polarity
> crossing is acceptable, with the output actively clamped to ground while it happens.*
> **`G0-A2`:** *the modules are already owned — `AP010504P05` + `AP010504N05`, i.e. 1 kV / 0.5 mA /
> 0.5 W / 5 V in / Vref 2.5 V.*
>
> | Candidate | Verdict after G0 |
> |---|---|
> | **T1 `hv-relay-changeover`** | ✅ **ADOPTED.** Its condition (set-and-hold) is satisfied by G0-A1. Corrections C-1…C-4 are now **unconditional**, plus a fifth for dual-mode (§5.2). |
> | T2 `hv-mosfet-optocoupler-switch` | ⛔ **ELIMINATED by G0-A2.** Blocked above **600 V** by the switch; the modules are **1 kV**. Its parts do not reach. **The "re-run the T1-vs-T2 vote at ≤600 V" branch is CLOSED and cannot be reopened without changing modules.** |
> | T3 `series-stack-driven-midpoint` | ⛔ **REJECTED by G0-A1.** It existed only to serve smooth through-zero, which is not required. Variant A was already physically broken; Variant B required amending invariant (a) in writing, which did not happen. |
> | T4 `single-module-polarity-reversing-relay` | ⛔ **REJECTED.** Unanimous across all three judges before G0; nothing in G0 revives it. |
> | T5 `diode-or` | ⛔ **REJECTED.** Structurally non-functional (TOPO-02); its carry-forward recommendation is **struck** (TOPO-03). |
>
> **⚠ THESE ALTERNATIVES MUST NOT BE REVIVED.** §§1–4 and §6 below are retained **as the record of
> WHY** — so a future session can see the reasoning without re-deriving it — **not as live options.**
> The decision tree that used to be this document's honest deliverable has been **collapsed to its
> branch A** and moved to **Appendix A**.
>
> **⬛ ONE THING GREW AT G0 THAT THIS STUDY NEVER CONSIDERED.** `G0-A4` added a **scope change**: the
> instrument must be switchable between **one combined pseudo-bipolar output** and **two independent
> unipolar outputs, both energisable at once**. **No candidate in this study was analysed against that
> requirement.** See **§5A — Dual-mode: what the adopted topology must now also do**, which is new work,
> not a re-reading of the old work.
>
> **⬛ AND ONE THING SHRANK, LATER THE SAME DAY.** `G0-A5`: **the mode is selected by a PHYSICAL SWITCH
> the operator moves. There is NO mode relay.** This study is a study of **HV switching elements**, so
> A5 lands directly on it: the second HV routing element that A4 added is **not a relay this study
> would have had to evaluate** — it is a panel part, moved by a human, on a powered-down instrument.
> **§5A is revised accordingly, and it got shorter.**
>
> **TERMINOLOGY (G0-A5), used from here on:** **"pseudo-bipolar"** = mode 1, single output, polarity
> changed by switching across zero — the honest word, since G0-A1 means we do **not** pass smoothly
> through zero. **"unipolar / dual-output"** = mode 2.

Five candidate topologies were analysed independently, then ranked by three independent judge sessions
under three different lenses. This document presents the candidates, all three rankings, **where the
lenses agreed and where they conflicted**, the fatal flaws the judges found that the analysts missed,
and (in the appendix) the decision tree that the G0 answers collapsed.

Source documents: `docs/topology/{diode-or, hv-relay-changeover, hv-mosfet-optocoupler-switch,
series-stack-driven-midpoint, single-module-polarity-reversing-relay}.md`.

---

## 0. Read this first — the finding that outranked the vote, **and how G0 resolved it**

> **✅ RESOLVED AT G0.** Session 1 wrote: *"`G0-1` must be answered before this recommendation is
> actionable, and the honest deliverable is §6's decision tree rather than a single answer."*
> **G0-A1 answered it: set-and-hold is acceptable, through-zero is NOT required.**
> ⇒ **The APS family is NOT disqualified. The recommendation IS actionable. T1 is adopted.**
>
> The finding below is retained in full because it is *why the answer mattered*, and because its three
> module facts remain binding on the adopted design — most of all fact 1, which is now a **permanent
> operating restriction** rather than an argument: **we stay out of the ±20 V band instead of trying to
> traverse it.**

Three of the five analysts and all three judges independently reached the same conclusion, so it is
stated before the comparison rather than buried inside it:

> **If smooth through-zero operation is required, the iseg APS module family is itself disqualified,
> and this entire comparison is moot.**
>
> **◀ The antecedent is FALSE (G0-A1). The comparison stands; the family stands.**

The reasons are properties of the module, not of any combiner:

1. **Manual Table 1, note 1, verbatim** `[verified-run ×4]`:
   *"Specifications for stability, ripple and noise are guaranteed in the range 2 %·Vnom < Vout ≤ Vnom."*
   On a 1 kV module that is a **±20 V band in which the output is not specified** — not merely worse,
   *unspecified*. No combiner can fix it.
   **→ Post-G0 status: BINDING, and now numeric.** G0-A2 confirms Vnom = 1000 V, so the unspecified
   band is **±20 V exactly**. Quote this clause wherever a low-end spec is quoted anywhere in this
   project (`DECISIONS.md` PART-32).
2. **The module cannot sink.** It is a resonant converter with a rectifier/multiplier output. Falling
   edges are set by the load plus an unpublished internal bleed, so rise and fall are governed by
   different mechanisms with different time constants.
   **→ Post-G0 status: BINDING, and the "unpublished internal bleed" is now MEASURABLE** — the modules
   are in hand (G0-A2 consequence 4; `DECISIONS.md` PART-24).
3. **The module's own set-node pole is ~100 ms** (100 kΩ into 1 µF, Figure 2, `[verified-artifact ×4]`),
   giving ~460–690 ms to settle. The fastest solid-state switch on the panel turns off in 0.04 ms —
   **12 500× faster than the module settles.** Switching speed is not a discriminator.
   **→ Post-G0 status: BINDING, and it is what makes G0-A1's ~1 s dead-band a MODULE property rather
   than a combiner shortcoming.** No combiner we could have chosen would have been faster.

**One counter-intuitive result, worth restating now that the decision is made:** the switched topology's
zero is *both modules unpowered, terminal tied to ground through a bleed* — **exactly 0.000 V, zero
tempco, zero ripple** — whereas the through-zero topology reached zero by cancelling two live rails and
drifted **14–28 mV/K**. **The "no through-zero" penalty is entirely a penalty on TIME, not on the
accuracy of zero.** G0-A1 accepted the time; the accuracy was never the thing being traded away.

---

## 1. The candidates

> **◀ RECORD, NOT A MENU.** T2–T5 are closed (see the banner). They are described here so a future
> session can see what was considered and why it lost, without re-deriving five analyses. **Reopening
> any of them requires a new gate and, for T2 and T3, different modules.**

| # | Topology | One line |
|---|---|---|
| **T1** | **`hv-relay-changeover`** | Two HV 1-Form-C reed relays. Each module's output goes to its relay's COM: NO drives the shared bus, **NC clamps that module to its own 20 MΩ bleed** — so no HV node is ever floating-and-charged. A single LV 2-Form-C armature routes *both* the only `+VIN` that reaches either module *and* the only coil power. A transparent latch with LE = "bus is cold" freezes the armature while HV is live. |
| **T2** | **`hv-mosfet-optocoupler-switch`** | Three 1500 V bidirectional PhotoMOS relays (branch-P, branch-N, output-dump). Exclusivity is enforced by wiring the two branch LED strings **anti-parallel** across one H-bridge node pair, so current *direction* — not logic — makes both-enabled unexpressible. Enable rail is generated by an AC-coupled charge pump the firmware must keep pumping. |
| **T3** | **`series-stack-driven-midpoint`** | *Variant A:* true anti-series stack, one module's LV domain and case floating. *Variant B:* both module GNDs at board ground, outputs joined through 1.5 MΩ ballasts, output taken at the driven midpoint, with a constant-sum control law `Vp + Vn = const`. |
| **T4** | **`single-module-polarity-reversing-relay`** | One module and a "DPDT" HV changeover that swaps which module terminal is grounded. *Variant A:* reverse the load. *Variant B:* float the module. |
| **T5** | **`diode-or`** | One series HV blocking diode per module into a common output node. |

---

## 2. The three rankings

Three judge sessions, each given all five studies, each with one lens, none seeing the others' work.

| Rank | **Judge A — safety & failure modes** | **Judge B — electrical performance & through-zero** | **Judge C — buildability, cost, risk** |
|---|---|---|---|
| 1 | **T1 relay — 7** | **T1 relay — 7** | **T1 relay — 7** |
| 2 | T2 PhotoMOS — 6 | T3 series-stack B — 6 | T2 PhotoMOS — 6 |
| 3 | T3 series-stack — 3 | T2 PhotoMOS — 5.5 | T3 series-stack — 3 |
| 4 | T4 single-module — 2 | T4 single-module — 4.5 | T4 single-module — 2 |
| 5 | T5 diode-OR — **0** | T5 diode-OR — 1 | T5 diode-OR — 1 |

### 2.1 Where the lenses AGREED

Convergence across three uncoordinated lenses is the strongest signal this panel produced.

- **T1 is first, unanimously, at exactly 7/10 in all three.** Three lenses, three different reasons,
  identical score. None of the three accepted its analyst's self-assessment of 8.
- **T5 is last, unanimously**, and all three treat it as *structurally non-functional* rather than
  merely inferior. Judge A gave it a hard 0.
- **T4 is rejected by all three**, though for entirely different reasons (see §2.2).
- **All three independently flagged that the through-zero question outranks the topology vote**, and
  all three re-verified the `2 %·Vnom` clause verbatim from the PDF rather than trusting the studies.
- **All three found that no candidate's changeover is as fast as its analyst claimed**, because the
  module's own 100 ms pole was under-counted (T1's 0.68 s → 0.89–1.12 s; T4's 0.505 s → ~0.7–1.0 s).
  Only T2's analyst had already accounted for it — and that analyst gets explicit credit from Judge B
  for having used the right instrument.
- **All three found that a welded or shorted switch defeats invariant (a) in every candidate**, and
  that no topology on the panel can *prevent* it — only detect it.

### 2.2 Where the lenses CONFLICTED — the interesting part

These are not smoothed over. Each is a real disagreement with a real cause.

---

**CONFLICT 1 — T3 series-stack: 6/10 (electrical) vs 3/10 (safety) and 3/10 (buildability).**
The widest split on the panel, and the only candidate whose rank changes by two places between lenses.

- **Judge B ranks it second** because it is *the only candidate that delivers genuine continuous
  through-zero*: 0 ms dead-band, 0 V discontinuity, monotonic by construction, no changeover event to
  glitch, no diode drop, no contact resistance, no off-state leakage, plus the best ripple story on
  the panel (7.07 mVpp typical at the output, re-derived and confirmed) and a free 21 Hz output pole
  no other topology can afford.
- **Judges A and C rank it fourth-from-top** because it fails invariant (a) outright — both modules
  are always enabled, so *the forbidden state is the operating mode* — and a single dead module drives
  the output to **half-scale of the opposite polarity**, where every switched topology gives 0 V.

**Resolution: Judge B's own analysis contains the tiebreaker, and it favours the switched topologies.**
Judge B computed something no analyst had: the module's ±50 ppm/K tempco, applied to two *independent*
modules whose difference forms the output, gives **14–28 mV/K of zero-point drift** — 141–283 mV over
a 10 K lab swing, up to 1.13 V over the specified 0–40 °C range. Meanwhile a switched topology's zero
is *both modules unpowered with the terminal tied to ground through a bleed*: **exactly 0.000 V, zero
tempco, zero ripple.** So the one topology sold on through-zero has, by a factor of ~10³, the **worst
zero** on the panel. Judge B states the correction explicitly: *"the switched topologies' 'no
through-zero' penalty is entirely a penalty on TIME, not on the accuracy of zero."*

That reframing is why T3 does not win even under the lens that likes it most, and it is the single
most useful thing the judge panel produced.

---

**CONFLICT 2 — T2 PhotoMOS: 2nd (safety, 6) and 2nd (buildability, 6) vs 3rd (electrical, 5.5).**

- Judges A and C rank it second on the strength of two mechanisms they call the best individual
  safety designs on the panel: the anti-parallel LED loop (exclusivity by Kirchhoff, no logic gate to
  fail) and the AC-coupled charge-pump enable rail (a static GPIO level *cannot* hold HV on).
- Judge B drops it below T3 on off-state leakage: **10 µA spec = 1.25 % of Inom**, versus the relay's
  100 nA = 0.02 %, and that leakage roughly doubles per 10 K, so the current budget is a 10×-varying
  function of ambient rather than a constant.

**Resolution: not load-bearing.** All three place T2 second or third and all three make its adoption
conditional on the same thing — the ≤600 V ceiling. The disagreement is about *why* it is second,
not about whether.

---

**CONFLICT 3 — T4 single-module: 2 / 4.5 / 2.**

Judge B scores it more than twice as high as the other two, on a ground **no analyst and no other
judge identified**: with one module serving both polarities there is **no module-to-module matching
term**. Every two-module candidate silently carries up to **2 %·Vnom of polarity asymmetry**
(±20 V at 1 kV) unless firmware keeps a *separate calibration table per polarity* — and not one of
the five analyses mentions per-polarity calibration.

**Resolution: the finding survives even though the topology does not.** T4 is rejected on grounds
Judge B does not dispute (single-MOSFET wrong-polarity fault; a single-armature kV DPDT that does not
exist at any vendor; a kilovolt-live LV harness on a human-present bench; an isolation barrier its own
analyst could not source). But **per-polarity calibration is now a requirement on the winner**, and
that is a direct transfer from a losing candidate.

---

**CONFLICT 4 — the source of T1's 3-point deduction differs by lens, and the union is what matters.**
All three scored T1 at 7, but for non-overlapping reasons: Judge A deducted for the missing both-off
state and the unexecutable weld self-test; Judge B for the load-dependent droop of the series limiter
and an over-claimed monitor accuracy; Judge C for an unpriceable relay, a missing 12 V rail, and
37 cm² of board. **A single-lens review would have found roughly one third of the defect list.**

---

## 3. Fatal flaws the judges found that the analysts missed

These are the panel's highest-value output. Every one is a defect in a document that had already
passed its own author's acceptance checks.

> **◀ POST-G0 TRIAGE.** The flaws split three ways now:
> - **F-1 … F-6 (T1) are LIVE DEFECTS in the adopted design.** They must all be fixed. C-1…C-4 in §5.2
>   retire them and are now unconditional.
> - **F-7 … F-17 belong to eliminated candidates (T2, T3, T4) and are MOOT as defects** — but three of
>   them carry lessons that transfer and are cited elsewhere: **F-7** (proving exclusivity of the
>   *drive* is not proving exclusivity of the *switch* → `DECISIONS.md` MODE-03), **F-12** (a
>   compensating dump sized against the wrong impedance leaves a hazardous voltage), **F-13** (a monitor
>   that goes blind exactly at the operating point it exists to guard).
> - **F-18 … F-23 are PANEL-WIDE and all still apply**, because they are properties of the problem, not
>   of a candidate. **F-20, F-21 and F-22 get worse at G0-A4** — per-polarity calibration now means
>   per-*output* calibration, and the buffer and VCR findings apply to **two** monitor chains.
> - **F-23 is partly retired by G0-A2:** *"not one analyst obtained an iseg quote"* no longer matters —
>   **the modules are owned.** The four cost rankings differing by less than the uncertainty in the
>   module line is now a historical embarrassment rather than a live risk. The relay and HV-passive
>   sourcing problem (R-7) is untouched.

| ID | Candidate | Flaw | Consequence |
|---|---|---|---|
| **F-1** | T1 relay | **There is no both-coils-off state, and the de-energised default is "NEG module powered and bonded to the output bus."** The +12 V feed goes through a polyfuse *straight* to the interlock relay's COM — **no switch anywhere in the coil rail** — so whenever board 12 V is present and the armature is de-energised (power-up, reset, unpowered MCU, broken ARM wire, open coil), the NEG coil is energised, NEG is hard-connected to the bus, and pole A simultaneously routes +5 V to that same module. The only remaining barrier is `/ON`, the pin that turns HV **on** when open. | **This is exactly the defect the analyst used to reject a competing single-SPDT arrangement in his own §2.1 — then rebuilt one level down in the LV interlock and did not notice.** Two fault-table rows are consequently false. **Fix: put the ALIVE-gated switch in the 12 V coil rail too.** |
| **F-2** | T1 relay | **The weld self-test — the sole mitigation for the topology's one admitted invariant-(a) failure — cannot be executed in the circuit as drawn**, because it begins "with both coils de-energised", which F-1 makes unreachable. In the state it actually lands in, the NEG relay is closed onto the bus that the POS test signal is applied to. A second judge found an independent defect in the same test: with no monitor on the parked branch, a module that produced *no* HV at all, an open `/ON`, an open series limiter or a dead module **all yield the same "bus stayed at 0" PASS** — the test cannot distinguish "stimulus applied and blocked" from "no stimulus was ever applied". | Detection, not prevention, is the whole safety argument for a contact-based topology. A detector with a silent false-pass is the load-bearing defect. **The per-branch monitor dividers listed as a $22 "improvement" are a precondition, not an upgrade.** |
| **F-3** | T1 relay | **Single-fault chain from the monitor divider to the invariant-(a) violation, split across two fault-table rows and never joined.** The COLD permissive is derived from the *same* divider as invariant (c). An open top string makes the monitor read "0 V", which forces COLD permanently TRUE, which makes the latch permanently transparent, which makes **hot switching possible on every changeover** — and hot switching is the mechanism that welds the contact. One open HV resistor converts the weld from a random 10⁸-operation wear-out into a **systematic consequence of normal operation**, while removing the monitor that would show it. The analyst's "2 700 years at 100 changeovers/day" bound only holds if every switch is cold. | **Fix: COLD gets its own independent divider string.** |
| **F-4** | T1 relay | **Magnetic actuation bypasses all three interlock layers simultaneously.** Layers 1 and 2 gate *coil power*; a magnetically closed reed needs no coil. A magnet applied mid-run is also invisible to a power-up-only self-test. | Not a curiosity in a lab with cryostats and magnetic mounts. **No solid-state combiner has this mode.** |
| **F-5** | T1 relay | **The +VIN transfer hot-makes into 22 µF through the one armature the entire interlock depends on.** The analyst proves the *HV* reeds are always cold-switched and that 0.75 mA cannot sustain an arc — then hot-makes the LV relay, connecting a 5 V rail to a discharged 22 µF (datasheet-mandated, PART-18): tens of amps peak, ~110 µC, into a 500 mA-rated contact. | Welding the LV armature is *more* probable than welding a reed, and it is the single point on which invariant (a) rests. **Fix (free): require the load switch OFF across the armature transfer.** |
| **F-6** | T1 relay | The claim "no HV node is ever floating-and-charged in any state" is **false during the Form-C break-before-make transit**, whose duration Pickering does not specify and the analyst admits he cannot bound. | Low consequence while transfers are cold; becomes load-bearing the moment F-3 fires. |
| **F-7** | T2 PhotoMOS | **The anti-parallel interlock proves exclusivity of LED CURRENT, not of SWITCH CLOSURE.** The datasheet gives `Ton = 0.35 ms typ / 1.0 ms MAX` and `Toff = 0.04 ms typ / 0.2 ms MAX` — a **maximum turn-off but no minimum turn-on**. On a commanded direct reversal the departing switch is guaranteed open only after 0.2 ms while the arriving switch may close in an unspecified, unbounded-below time. **The datasheet permits an overlap window with no fault present at all.** What actually prevents it is step 1 of the firmware sequence — i.e. a firmware convention, which `CLAUDE.md` says is not sufficient. | **Fix: hardware-force the coast** with an RC/monostable guaranteeing a dead interval longer than `Toff(max)` on every direction change. |
| **F-8** | T2 PhotoMOS | **The topology never removes `+VIN` from either module**, so its entire defence against PART-02 is a pull-up resistor. Every `/ON`-path fault (broken track, shorted phototransistor, open pull-up) puts a module at full commanded output with no second layer. | The relay makes `+VIN` the primary disable precisely to avoid this. |
| **F-9** | T2 PhotoMOS | **The off-state switch stress is 1200 V — 100 % of the recommended rating — not the 600 V it was sized on**, in two faults the analyst classifies as benign. When a parked module sits at full output behind its open switch, that switch holds `\|HVP − HVOUT\| = +600 − (−600) = 1200 V` indefinitely. The analyst states the 1200 V differential in his own layout section and never carries it back into the part-rating table. | A direct internal inconsistency. The "50 % derating" safety argument does not survive two faults he calls non-hazardous. |
| **F-10** | T2 PhotoMOS | The central failure (shorted branch switch) leaves a module in **continuous short circuit at 0.72 W against a 0.5 W part with a 120 °C case limit** — the analyst runs exactly this thermal calculation for a *different* fault and writes "no damage" for this one. And the presenting symptom, "output reads zero", is indistinguishable from a module that has not ramped yet or from an open monitor divider. | **That combination is what makes an operator retry.** |
| **F-11** | T2 PhotoMOS | Arithmetic error in the standing-load budget: `50 MΩ ‖ 500 MΩ ‖ 100 MΩ = 31.25 MΩ`, not the stated 44.5 MΩ (which omits the active module's own bleed). 19.2 µA = 2.4 % of Inom, not 1.7 %. | Passes at 600 V/0.8 mA; evidence the budget was never summed. |
| **F-12** | T3 series-stack | **The compensating mechanism offered for the failed invariant (a) does not work, verified numerically.** The analyst asserts a stuck-closed 1 MΩ dump relay "clamps the output to ~0 V". Node analysis of his own circuit: dead-module fault at commanded zero gives **−111.9 V** after the dump closes; with the other module at full scale, **−223.8 V**. The dump removes ~42 % of the fault voltage, because 1 MΩ is the same order as the 1.5 MΩ ballast feeding it. Reaching <60 V needs ≤~100 kΩ. | The one mechanism proposed to make the topology acceptable **leaves a hazardous voltage on the terminal**. Its "<10 ms latency to safe" is latency to 200 V. |
| **F-13** | T3 series-stack | **The window comparator cannot distinguish "commanded zero" from "monitor divider top open" at exactly the operating point the topology exists to serve.** When the setpoint *is* zero, "monitor says 0" and "setpoint is 0" agree and the window is satisfied — while the constant-sum law has both modules at 400 V internally. **The board is most energised exactly when its monitor is least trustworthy.** | |
| **F-14** | T3 series-stack | **Zero-point tempco of 14–28 mV/K was never counted** (the analyst costed only ballast TCR mismatch). See Conflict 1. Also: no series interruption exists anywhere, so the terminal is galvanically connected to both modules through 1.5 MΩ in *every* state including unpowered. | |
| **F-15** | T4 single-module | **The live case is the small half of the hazard.** The analyst costs a 3.75 mm keepout ring around the steel can and stops — but the module's GND is one of the two switched nodes, so `+VIN`, `VSET`, `VMON`, `/ON`, the 22 µF can, both buffers, every test point and any debug header sit at up to −1 kV relative to chassis. **A ground-referenced scope probe clipped to VMON is a direct kilovolt-to-chassis short through the probe**, on a board whose brief says first energisation is human-present. No other candidate has an LV net above 12 V. | Also: no analyst costed the *commissioning* penalty — debugging requires a >1 kV differential probe or an isolated scope, which the lab may not own. |
| **F-16** | T4 single-module | **The primary safety barrier is a part the analyst searched for and could not find** — an isolated DC-DC with ≥1 kV **continuous** working voltage — yet it is carried at an assumed \$40 into the headline cost delta the rejection was argued on. | The correct verdict is *"cannot be sourced today"*, not *"the economics do not work"*. The distinction matters: a price change could reopen an economics argument; the sourcing failure would remain. |
| **F-17** | T4 single-module | The fail-safe crowbar is **hot-switched by design on every emergency operation**, exercising the exact welding mechanism the analyst quotes Pickering against — on the one contact whose correct operation is the last line of defence, and which is never exercised in normal use. | |
| **F-18** | T5 diode-OR | **The surviving carry-forward recommendation ("buy the diodes anyway") is refuted by its own author's theorem** and would inject a defect into whichever topology wins. The forward-bias argument applies unchanged downstream of an open relay contact. Concretely it would protect nothing, **break the reverse discharge direction of T1's NC-contact bleed** (defeating its structural invariant-(b) guarantee), and add 5–50 µA of reverse leakage = up to 10 % of Inom. | **Struck.** A judge who read only the carry-forward list would have adopted it. Recorded in `DECISIONS.md` TOPO-03 so it cannot return. |
| **F-19** | **ALL FIVE** | **Every candidate's safe state depends on a pull resistor at the module pins, and no analyst treats the pull element itself as a single-point failure in the unsafe direction.** An *open* pull restores the documented unsafe default: `/ON` open ⇒ HV ON; `VSET` open ⇒ full scale. Only one analyst noticed, only for `/ON`. | **Duplicate every safe-state pull element, and make it an ERC-checkable project rule** (`DECISIONS.md` ARCH-18). |
| **F-20** | **ALL FOUR two-module candidates** | **Polarity asymmetry is uncosted.** Up to 2 %·Vnom of asymmetry between +V and −V unless firmware keeps a per-polarity calibration table. Not one of the five analyses mentions it. | **Per-polarity calibration becomes a firmware requirement.** |
| **F-21** | **ALL FOUR resistive-monitor candidates** | **Invariant (c) is 7–17 % accurate, not 0.2 %**, because the ADC is hung straight off the divider with no buffer. TI SBAS444E, fetched and extracted by a judge, gives ADS111x input impedance 22/15/4.9/2.4 MΩ by FSR and states buffering "can be necessary". **The irony:** three analyses correctly insist on buffering `VMON` because of its 20 kΩ source, then hang the *safety* monitor off a source 25–60× higher with nothing in between. There is also a trap: shrinking the divider output to gain resolution forces a lower FSR, which has the **lowest** input impedance — resolution and accuracy trade the wrong way. | One ~$1 op-amp per monitor. `DECISIONS.md` ARCH-08. |
| **F-22** | **ALL FIVE** | **Nobody costs the voltage coefficient of the HV divider**, which is the dominant non-calibratable monitor error — and it is a *nonlinearity*, so a single-point gain calibration cannot remove it. One study mentions VCR in a parts footnote and then does not propagate it into its own accuracy claim; the other four mention it zero times. | Until VCR is on the table, **no candidate's independent monitor is demonstrably better than the module's own VMON** — which removes the main quantitative argument for invariant (c) being a real measurement rather than a redundant one. |
| **F-23** | **ALL FIVE** | **Not one analyst obtained an iseg quote, lead time, or MOQ**, yet the modules are the dominant BOM line in every candidate — and the item code encodes voltage class *and* polarity, so both decisions are irreversible at order time. **The four cost rankings differ by less than the uncertainty in the single line they all assumed.** | Escalated with the same priority as the through-zero question. |

---

## 4. Cost and area — with the honesty the panel demanded

Combiner-attributable BOM only. Every price is tagged. **`[unverified-MPN]` tags are not stripped.**

| | T1 relay | T2 PhotoMOS | T3 series-stack | T4 single-module | T5 diode-OR |
|---|---|---|---|---|---|
| Combiner BOM, qty 1 | ~\$243 | ~\$98 | ~\$82 | ~\$265 + module | ~\$10 |
| Dominant line | 2 × HV Form-C relay (**74 %**) | 9 × HV resistor (**40 %**) | HV resistors | 3 × HV relay + isolation | — |
| HV parts **verified in stock** | 0 of 2 relays | **both** (PhotoMOS 2223 pcs, HV resistor 1146 pcs) | 0 (0-stock + obsolete hits) | 0 (13-week lead) | diode yes, but EOL |
| HV board area | ~37 cm² | ~9 cm² | small | ~2208 mm² relay body alone | small |
| Coil / standing power | 0.96 W + 0.14 W | 0 | 0 | ~1.9 W | 0 |
| Forces module class? | **No** — spans 200 V–1 kV | **Yes** — caps at 600 V | **Yes** — doubles it (800 V for ±400 V out) | No | n/a |

**Cost is not a discriminator and anyone using it as one is optimising the wrong variable.** The two
APS modules dominate the BOM in every candidate and **nobody priced them** (F-23). T1's ~\$145
premium over T2 buys an **option on an unfrozen requirement** — and on a first build where fab is the
irreversible act, that option is cheap. T3's apparent \$50 saving is illusory: it forces 800 V modules,
almost certainly a several-hundred-dollar delta.

> **◀ POST-G0.** Two of the three sentences above are now settled facts rather than arguments:
> - **The module BOM line is \$0 — the modules are owned (G0-A2).** The "nobody priced them" objection
>   is retired for the dominant line. What is left unpriced is the **relay**, which two independent
>   agents failed to price (three timeouts + an HTTP 403) and which is **74 % of T1's combiner BOM**.
>   **That is now the single largest cost and schedule unknown in the combiner** (R-7).
> - **T1's \$145 premium bought an option, and G0 exercised it.** The option was on the voltage class;
>   G0-A2 landed at **1 kV**, where **T2 is not merely more expensive but unavailable** (its parts stop
>   at 600 V). **The premium turned out to be the price of the only workable candidate**, which is the
>   best possible outcome for an option and worth recording as such.
> - **The area row is now WRONG-LOW for the adopted design.** G0-A4 adds a mode routing element, a
>   second SHV connector spaced for 2 kV, a second monitor string with its own guard ring, and a second
>   bleed network. **~37 cm² is a floor, not an estimate** (`SCOPE.md` R-12, `DECISIONS.md` LIB-19).
>   **Re-run it before placement.**

---

## 5. ✅ DECISION (was: RECOMMENDATION)

### 5.1 The decision

> **Session 1 wrote: "Adopt `hv-relay-changeover` (T1), CONDITIONAL on `G0-1` answering 'set-and-hold
> with polarity changeover is acceptable'."**
> **G0-A1 answered exactly that, on 2026-07-23.**
> **⇒ THEREFORE: `hv-relay-changeover` (T1) IS ADOPTED. The condition is discharged. The four
> corrections C-1…C-4 below are UNCONDITIONAL, and a fifth (C-5) is added by G0-A4.**

**Reasoning** *(unchanged, and confirmed by the answers)*. Three uncoordinated lenses ranked it first at
the same score. Three properties no competitor has together:

1. **The OFF state is a physical air gap.** Leakage 100 nA = 0.02 % of Inom, versus 10 µA = 1.25 %
   for the solid-state alternative — and that alternative's leakage flows *into the disabled module's
   HV pin*, the exact stress its switch exists to prevent. The invariant-(c) killer (off-state leakage
   corrupting a microamp-scale output) simply does not exist here.
2. **Invariant (b) is satisfied STRUCTURALLY, not by a timer.** With per-module Form C, the deselected
   module is bled through its own NC contact automatically, at zero cost to the active module. There
   is no state in which an HV node is floating and unbled (modulo F-6).
3. **`+VIN` removal is the primary disable**, not `/ON`. It is the only candidate that does not stake
   the whole design on a pull-up resistor holding an active-low, open-means-ON input high.

Plus: at 0.75 mA the modules **cannot sustain an arc** (three orders below the ~1 A tungsten minimum),
so the relay dry-switches even in a hot-switch fault — a free pass a higher-power design would not get.
**G0-A2 confirms the 0.75 mA figure exactly** (Inom 0.5 mA × 1.5), so this argument is now `[frozen]`
rather than parametric.
~~And it is the only candidate that **does not pre-commit an undecided requirement**: 2.5 kV switching /
5 kV standoff spans the entire APS family.~~ **◀ That argument is SPENT, not wrong.** G0-A2 froze the
class at 1 kV, so the option T1 was bought for has been **exercised** — and it paid, because at 1 kV
the alternative it was hedging against (T2) turns out to be unavailable rather than merely costlier.

### 5.2 Mandatory corrections — **now UNCONDITIONAL**, and there are FIVE

~~(all four, before any schematic capture)~~ **All five, before any schematic capture. C-1…C-4 were
conditional on T1 being adopted; G0-A1 adopted it. C-5 is new, created by G0-A4.**

| # | Correction | Retires |
|---|---|---|
| **C-1** | Put a fail-safe-open switch in the **relay coil rail**, gated by the same ALIVE/ARM element as the 5 V load switch. ⚠ **G0-A2 opens a question inside this correction:** it was written as *"the **12 V** coil rail"* when a 12 V module supply was the recommended family. **There is no 12 V module rail on this board** — `+VIN` is **5 V** (`DECISIONS.md` PART-30). So either the relay coils are **5 V** parts, or a **dedicated 12 V coil rail must be generated and budgeted** (NUM-21). **Judge C's "missing 12 V rail" criticism therefore stands more strongly, not less. Decide and state the coil voltage explicitly at G1.** | F-1, F-2 (makes both-coils-off reachable, so the weld self-test can run) |
| **C-2** | Give the **COLD permissive its own divider string**, physically separate from the invariant-(c) string. Add per-branch monitor dividers. **G0-A4 doubles this**: per-output, per-branch. | F-3, F-2 (second half) |
| **C-3** | Generate the heartbeat from a **main-loop-serviced toggle**, add a **windowed** watchdog, two series coupling caps, and an independent hardware timer. **G0-A3 promotes this from good practice to load-bearing** — with the network able to command HV, the heartbeat is one of the few elements that does not trust firmware. | ARCH-20 / the free-running-peripheral hole |
| **C-4** | **Duplicate every safe-state pull element**; make it an ERC rule. **G0-A2 sharpens the stakes:** an open `VSET` pull element on a 2.5 V-Vref module restores a documented full-scale command, and a 3.3 V node reaching that pin commands ≈1320 V (PART-33). | F-19 |
| **C-5** ⬛ | **NEW (G0-A4), REWRITTEN (G0-A5).** ⛔ ~~The mode routing element joins the fail-safe coil-rail scheme and its de-energised position must be the SAFE mode~~ **— STRUCK: the mode element has NO COIL. It is a physical panel switch (MODE-04), so it cannot sit in a coil rail at all, and it is safe by *absence of energy* rather than by *correct de-energised position*.** ✅ **What survives, and it survives unchanged in principle:** *the interlock permissive must be taken from the element's ACTUAL PHYSICAL POSITION — never from a commanded bit.* **A5 satisfies that more strongly than A4 asked**, because the HV poles and the interlock's LV aux poles are **the same armature**, so they **cannot disagree by construction** — whereas a sensed relay position can (a sense contact mis-wired to the coil command is invisible in normal operation). **C-5 therefore becomes three concrete switch requirements:** **(i)** LV aux poles feed the interlock **combinationally**, never latched or cached (MODE-14); **(ii)** those aux poles must **BREAK BEFORE** the HV poles **MAKE** (MODE-15); **(iii)** any **intermediate/between-detent** position must decode to **both modules off, both outputs bled** (MODE-18). | The G0-A4 failure mode — *"mode 2 asserted in software while the routing element is physically in mode 1"* ⇒ **both modules on one node** — is **DELETED by A5, not mitigated**: there is no software mode assertion. **F-7's lesson still applies, but to the polarity relays, not to the mode element.** `DECISIONS.md` MODE-02/03/04/14/15/18. **Note this makes C-1 easier too**: the fail-safe coil rail now has to cover **two** relays, not three. |

Plus three panel-wide fixes that apply whatever wins: buffer the monitor ADC (F-21), cost the divider
VCR (F-22), and add per-polarity calibration (F-20) — **which G0-A4 turns into per-OUTPUT calibration,
since in mode 2 the two polarities are two physically different chains.**

### 5.3 Dependencies — **which are discharged and which still bind**

| Depends on | Status after G0 |
|---|---|
| **G0-1 = set-and-hold** | ✅ **DISCHARGED.** G0-A1 answered set-and-hold. Branch B is closed. |
| **G0-2 voltage class** | ✅ **DISCHARGED at 1 kV (G0-A2).** ⛔ The *"if ≤600 V, re-run the T1-vs-T2 vote"* clause is **CLOSED** — T2's parts stop at 600 V, so at 1 kV it is unavailable, not merely un-chosen. **Do not revive it.** |
| **Environment is not magnet-rich** | ⚠ **STILL BINDS, and its fallback is GONE.** Session 1's escape was *"T2 becomes competitive at ≤600 V"* — **T2 is eliminated.** F-4 must now be mitigated **in place** (screened part, ≥5 mm spacing, enclosure note, self-test). **Ask the human whether cryostats or magnetic mounts sit within ~100 mm of the enclosure — that question is now consequential** (`SCOPE.md` R-6). |
| **Detection is acceptable for a welded contact** | ⚠ **STILL OPEN — Q6 was NOT answered at G0.** Proceeding on detection + mandatory power-up self-test. If prevention is ever required, **every candidate dies** and the study reopens (TOPO-10). **G0-A4 adds the mode element to the set of things that can weld, and it is the worst member** (`SCOPE.md` R-8). |
| **Pickering Form C is procurable** | ⚠ **STILL BINDS, and is now the LARGEST unpriced line in the combiner**, since G0-A2 removed the modules from the BOM. Two agents failed to price it. If lead time >~6 weeks or price >~\$120 each, **there is no T2 to fall back to** — the fallback is a different Form-C source, not a different topology. It is still **not** four Form-A relays (\$241 *and* a worse circuit — it loses the structural bleed). |
| **The four unmeasured module numbers** | ⚠ **STILL BINDS — but is now ACTIONABLE.** Output C, internal bleeder, VSET step response, turn-on time. Three of the four numbers setting the dead-band are assumptions. **G0-A2 puts the modules in hand: measure them** (`DECISIONS.md` PART-24/25, TOPO-11). |
| ~~**NEW: the mode mechanism (G0-A4)**~~ | ✅ **DISCHARGED SAME DAY BY G0-A5 — mechanism (a), a PHYSICAL SWITCH.** ~~(a) safest, costs the remote flexibility the human asked for; (b) relay with armature-position sense.~~ **The stated cost of (a) was false**: mode change requires re-cabling the instrument, so remote mode selection could never have worked. **There is no mode relay.** `DECISIONS.md` MODE-04. |
| **NEW: the mode SWITCH is procurable, and its contacts break in the right order (G0-A5)** | ⚠ **OPEN → G1, and it is the replacement risk.** A panel switch rated **1 kV per HV pole** (and **2 kV between poles** if the arrangement creates an opposite-polarity pair) **with auxiliary LV poles** is an **unsearched part class in this project**. Whether it is easier or harder to source than the unpriceable Form-C relay is **unknown**. **The fallback is an HV link block or a re-plugged HV cable, and it is legitimate engineering, not a concession** — price it in parallel. Separately, the aux poles must **lead-break** the HV poles (MODE-15). `DECISIONS.md` MODE-13/15, `SCOPE.md` R-14, O-10/O-11. |

---

## 5A. ⬛ DUAL-MODE — what the adopted topology must now ALSO do (NEW at G0-A4)

> **⚠ THIS IS NEW WORK, NOT A RE-READING OF THE OLD WORK. No candidate in this study — including the
> winner — was analysed against a dual-mode requirement.** Session 1's entire panel assumed *one output
> terminal*, because that is what the brief said. **G0-A4 amends the brief.** What follows states the
> problem precisely so it is not mistaken for something already solved.

**The requirement.** The instrument must be switchable between:
- **MODE 1 — bipolar combined:** both modules → **one** terminal, one at a time, break-before-make,
  deselected module bled to ground. **This is exactly what T1 does today.**
- **MODE 2 — dual unipolar:** POS module → **output A**, NEG module → **output B**, independently,
  **both energisable at once.**

**Why T1 does not already do this.** T1's safety case rests on **ARCH-16 mechanism (i)**: *one armature
routes the only `+VIN` that reaches either module*, making both-enabled inexpressible. **That mechanism
implements the OLD invariant and therefore FORBIDS MODE 2** — under it, mode 2 is not merely unsupported,
it is structurally impossible. **The interlock must be re-derived, not extended.**

**The restated invariant it must satisfy** (`DECISIONS.md` MODE-02):

> **It must be impossible for both modules to be connected to the SAME output node simultaneously.**

In mode 1 this forbids the both-enabled state exactly as before. In mode 2 it is satisfied
**structurally**, because the modules sit on physically different nodes.

**The failure mode that defined the design — and how G0-A5 deleted it** (`DECISIONS.md` MODE-03/04):

> A firmware fault, a stuck GPIO, or a **network command** (G0-A3 grants network write authority) asserts
> *"mode 2 — both modules permitted"* while the HV routing element is **physically still in the mode-1
> position**. Both modules are then commanded onto **one node**. That is the forbidden state, reached
> through exactly the firmware-promise path `CLAUDE.md` forbids.

⇒ **The mode permissive MUST come from the mode element's ACTUAL PHYSICAL POSITION**, **never from a
commanded bit.** This is F-7's lesson transferred: *proving exclusivity of the drive is not proving
exclusivity of the switch.*

> ### ⬛ G0-A5: **THE FAILURE MODE ABOVE IS NOT MITIGATED — IT IS UNREACHABLE.**
>
> **The mode is set by a PHYSICAL SWITCH the operator moves.** Therefore:
> - **There is no software mode assertion to be wrong.** No `MODE` command exists on any interface
>   (`DECISIONS.md` MODE-12), so the network cannot reach the mode at all.
> - **The interlock's LV aux poles and the HV poles are MOVED BY THE SAME ARMATURE**, so the permissive
>   and the routing **cannot disagree by construction** — **strictly stronger** than the sensed-relay
>   scheme A4 specified, which *could* disagree if a sense contact were mis-wired to report the coil
>   command rather than the armature.
> - **The human's own reason, and it is the right one:** *"we would need to physically change cables,
>   anyways, so we can flip a physical switch. This will also make it fault tolerant."* A remote mode
>   command was never usable, so mechanism (b) bought **nothing** while carrying **the worst hazard in
>   the dual-mode design**.
>
> **What is left to engineer is smaller and better bounded:** switch **rating and sourcing** (MODE-13),
> aux-pole **lead-break timing** (MODE-15), **intermediate-position** decode (MODE-18), a **guard and
> legend** (MODE-17), and a **runtime-change trip** (MODE-16).

**What must be added to the T1 design, itemised** *(D-1 revised at G0-A5; D-2…D-4 unchanged; D-5…D-9 revised)*:

| # | Addition | Note |
|---|---|---|
| D-1 | ⛔ ~~**HV mode routing element**, with **position sense**. Its de-energised position must be the safe mode. Joins C-1's fail-safe coil rail. Another magnetically-operable reed to screen and space.~~ **REPLACED (G0-A5): an HV-rated PHYSICAL MODE SWITCH on the panel, with auxiliary LV poles.** | **Not a relay, not on the coil rail, not magnetically operable** — a magnet cannot move a mechanical switch, so **R-6's magnetically-operable set does NOT grow** (contrary to the A4 pass). Rating: **1 kV working per HV pole**, and **2 kV between poles** if the arrangement creates an opposite-polarity pair — **prefer an arrangement that does not** (MODE-13). Aux poles are **combinational** into the interlock (MODE-14) and must **break before** the HV poles make (MODE-15). **Fallback if unsourceable: an HV link block or a re-plugged HV cable — legitimate, and it needs no timing spec at all.** |
| D-2 | **Second HV output connector**, spaced for **2 kV** from the first | MODE-05. |
| D-3 | **Second bleed network** on the second output node | Invariant (b) applies to both nodes, on disable **and on mode change**. Two parallel strings each (NUM-09). MODE-10. |
| D-4 | **Second independent monitor chain**: divider + buffer + guard ring + ADC channel | Invariant (c) applies to both outputs. Each string loads its own module by **1.00 % of Inom** at the confirmed 1 kV / 0.5 mA — **at the budget limit, per output** (MODE-07). One ADS1115 no longer covers the channel count. |
| D-5 | ⛔ ~~**Mode-change state transition** with its own timeouts~~ **DELETED (G0-A5) — replaced by an OPERATING PROCEDURE plus two backstops.** | ~~Both outputs to zero → both modules disabled → dwell for bleed → **then** move the element **cold**, and a discharge timeout must TRIP~~ — **the physics is identical but there is nothing for firmware to move**, so there is **no transition, no timeout and no TRIP rule** (ARCH-24 loses its second instance). The same sequence is now a **powered-down, cables-off human procedure**, enforced by a **guard over the switch** and a **panel legend** (MODE-17), and backstopped by **MODE-16** — *a mode change detected at runtime forces HV OFF immediately, never gracefully* — and by the switch's **lead-break** aux poles (MODE-15). **Plus MODE-18: an intermediate position ⇒ both modules off, both outputs bled.** |
| D-6 | **Panel mode indication** — **satisfied by the switch itself (G0-A5)** | *Which terminal is live* differs by mode; a wrong assumption at 1 kV is a shock hazard, not a UX complaint. **The mode IS a panel switch, so its own position is the indication and it cannot lie** — there is no commanded bit for an indicator to be driven from wrongly. Reduces to **clear legending** plus the **guard** (MODE-17). Any LED echo comes from the **aux poles** (MODE-14), never from firmware state. Seventh and eighth enclosure requirements (NUM-23). MODE-09. |
| D-7 | **Protocol fork** — **and the mode surface is READ-ONLY (G0-A5)** | Mode 1 (pseudo-bipolar) keeps the single signed setpoint (ARCH-21). Mode 2 needs **output A and output B addressed separately** — **that fork is real and still to be designed**. ⛔ ~~A mode command must be **rejected**, not queued or clamped, unless both outputs are OFF and both measure below `V_safe`~~ **— STRUCK: THERE IS NO MODE COMMAND.** `MODE?` reports the **physical** position. **An immutable value needs no refusal logic, no settings-conflict path and no atomicity argument** — a strict simplification. MODE-12. |
| D-8 | **Supply re-sizing** | Both modules at full output simultaneously is now **normal**: 2 × <180 mA at 5 V for the modules alone, plus the WiFi TX burst. **The "only one is ever enabled" argument is dead** (NUM-22, NUM-11). |
| D-9 | **Clearance/area re-run** | The 2 kV `HV_POS`↔`HV_NEG` gap is now a **permanent normal condition**, not a fault case (MODE-06). ~37 cm² of HV area is a **floor**. **Re-run before placement — HV clearance cannot be recovered by rerouting** (LIB-19, R-12). |

**And one honest limitation.** The three judge lenses never scored a dual-mode design. **The 7/10 that
all three gave T1 is a score for the single-output design.** Nothing in this study establishes that the
dual-mode variant is as safe; that is a G1 review, and the **mode-aware interlock truth table** is the
artefact that has to carry it.

> **◀ G0-A5 REDUCES BUT DOES NOT REMOVE THAT LIMITATION, and the distinction matters.**
> A5 deletes the **largest unscored hazard** in the dual-mode variant — the commanded-mode-disagrees-
> with-physical-routing state — and it deletes it **structurally**, which is the kind of change a judge
> panel would have credited. **But the panel still has not scored:** two simultaneously-live HV outputs
> at a permanent 2 kV differential, two independent monitor chains at the 1.00 % loading limit, two
> bleed networks, and an HV panel switch in the output path with a **timing requirement** (MODE-15) that
> no candidate in this study ever had. **The G1 review still owes a dual-mode assessment**; it is simply
> a smaller and better-bounded one than the A4 pass faced. **Do not read A5 as retiring §5A.**

---

## 6. APPENDIX A — the decision tree, **COLLAPSED**

> **⚠ CLOSED. This tree is the record of how the decision was structured, not a live decision aid.**
> **G0-A1 = branch (A). G0-A2 = the "≥ 800 V / class unfrozen" sub-branch of (A).**
> **⇒ ADOPT T1 `hv-relay-changeover` + corrections C-1…C-5. Every other leaf is unreachable.**
> Retained verbatim so a future session can see **why** the alternatives lost without re-deriving five
> analyses. **Do not treat any struck leaf as re-openable without a new gate — and note that branch B
> and the ≤600 V leaf additionally require DIFFERENT MODULES, which are already bought.**

Session 1's framing, retained: *"The brief calls through-zero 'the key behavioral question' and says it
selects the combiner. It is unanswered. Presenting a single recommendation would be pretending
otherwise."* — **It is answered now, so a single answer is exactly what is presented.**

```
G0-1: Is smooth THROUGH-ZERO operation required?
│
├─ (A) NO — set-and-hold with polarity changeover is acceptable   ◄══ ✅ THE ANSWER (G0-A1)
│   │
│   ├─ G0-2 output spec ≥ 800 V, OR voltage class still unfrozen  ◄══ ✅ TAKEN (G0-A2 = 1 kV)
│   │      → ADOPT T1  hv-relay-changeover  + corrections C-1..C-4   [+ C-5, new at G0-A4]
│   │        Rationale: only candidate spanning the whole APS family; fab is irreversible;
│   │        ~$145/board is a cheap option on an unfrozen requirement.
│   │        Order the Form-C relays at G1, not at fab.
│   │        ▲ THE OPTION WAS EXERCISED AND IT PAID: at 1 kV, T2 is unavailable,
│   │          so the premium bought the only workable candidate.
│   │
│   └─ ⛔ G0-2 output spec FROZEN at ≤ 600 V                        ── UNREACHABLE (modules are 1 kV)
│          → RE-RUN the T1-vs-T2 vote. Default: T2 hv-mosfet-optocoupler-switch
│            + corrections F-7 (hardware-forced coast), F-8/F-9 mitigations,
│            + written confirmation from Panasonic of CONTINUOUS working voltage.
│            Rationale: only candidate with HV parts verified in stock, ~40% the cost,
│            ~1/4 the HV area, no coil power, no magnetic mode.
│            EXCEPT: if "survive any single component short without a silent
│            zero-output failure" is a requirement, T2 loses on F-10 and T1 wins anyway.
│            ▲ CLOSED BY G0-A2. Reopening requires buying different modules.
│              NOTE THE COST: T2 was the only candidate WITHOUT the magnetic-actuation
│              failure mode (F-4). Losing it means R-6 must be mitigated in place.
│
└─ ⛔ (B) YES — smooth through-zero is required                     ── UNREACHABLE (G0-A1 said NO)
    │
    │   ⚠  THE APS MODULE FAMILY IS DISQUALIFIED. See §0. This is not a combiner
    │      problem and no combiner on this panel solves it.
    │
    ├─ B1  Accept a ±2%·Vnom UNSPECIFIED band around zero (±20 V at 1 kV)
    │      and a ~1 s traverse?
    │      → then this is really answer (A) with a slow sweep. Go to (A).
    │      ▲ In effect this is what G0-A1 chose, stated directly rather than
    │        as a concession: we STAY OUT of the ±20 V band rather than traverse it.
    │
    ├─ B2  Load confirmed CAPACITIVE at < 5–10 µA, AND the human amends
    │      invariant (a) IN WRITING to "output magnitude and polarity bounded
    │      in hardware"?
    │      → T3 series-stack Variant B becomes the only candidate.
    │        Mandatory: dump element ≤ 100 kΩ (NOT 1 MΩ — F-12),
    │        a window trip that does not blind at zero (F-13),
    │        800 V modules for ±400 V out,
    │        and the zero re-specified in the brief as ±0.3 V per 10 K
    │        of ambient (F-14), not the ±0.1 V its analyst offered.
    │      ▲ CLOSED. The amendment never happened, the load was never confirmed,
    │        and 800 V modules were not what was bought.
    │        ⚠ DO NOT CONFUSE THIS WITH G0-A4. G0-A4 also amended an invariant —
    │          but it GENERALISED it ("not onto the SAME NODE") while preserving
    │          the intent, whereas B2 would have WAIVED it ("both always enabled
    │          onto one node IS the operating mode"). These are opposite moves.
    │
    └─ B3  Neither B1 nor B2 acceptable
           → STOP. Re-open module selection. This is a change of part family,
             not a change of combiner, and it is a G0 decision for the human.
           ▲ CLOSED. The human owns the modules.
```

---

## 7. What this study did NOT do — instrument limits

- **Nothing was simulated, breadboarded, built, or measured.** Every electrical claim is arithmetic
  over datasheet values, or a reading of a vendor figure captioned *"control principle"*.
- **No MPN was verified against a live distributor page by the judges**, and several were not verified
  by the analysts either. One analyst records that a distributor deep-link for a DAC returned a
  complete, confident spec report **for a 64-position ribbon cable assembly**, with nothing in the
  response signalling the mismatch. Every MPN in this document keeps its tag.
- **The `Ton`/`Toff` figures underpinning F-7 are second-hand to the judge who raised it.** The
  argument is structural (a maximum turn-off with no minimum turn-on cannot prove break-before-make)
  and survives unless Panasonic publishes a `Ton` minimum.
- **IEC 61010-1 was not opened.** The `<60 V within 5 s` and `350 mJ / 50 µC` thresholds are
  `[recalled]` throughout and are checklist items for Phase 7. **Unchanged by G0 — Q5 was not
  answered.**
- **The four module numbers that set every dead-band and discharge figure have never been measured**
  on hardware, and iseg publishes none of them. One afternoon on the bench with one module closes this.
  **⬛ G0-A2 makes that afternoon possible — the modules are in hand, and there are two of them.**
  This is now the difference between "we could not know" and "we did not look".

### 7.1 What this study did not do **that only became visible at G0**

- **It never evaluated a dual-mode design.** §5A states the gap explicitly. **The unanimous 7/10 is a
  score for the single-output topology.** Nothing here establishes that the dual-mode variant carries
  the same safety case; that is G1 work, and the mode-aware interlock truth table is what must carry it.
  **G0-A5 shrinks the gap** (the commanded-mode hazard is gone structurally) **but does not close it** —
  see §5A's closing note.
- **It never evaluated an HV element in the output path that a HUMAN moves.** Every candidate here is
  an electrically-actuated switch, and every timing argument in this study is about **coil and
  semiconductor** transitions. **G0-A5 introduces a hand-operated HV switch whose CONTACT SEQUENCE is a
  safety requirement** (aux poles must break before HV poles make, MODE-15). **No analyst and no judge
  ever considered that part class**, and nobody in this project has searched it. **This is new,
  unreviewed ground** — `SCOPE.md` R-14, `G0_QUESTIONS.md` O-10/O-11.
- **It never evaluated a design whose set-point is reachable from a network.** Every safety argument
  here assumes the adversary is a *fault*. **G0-A3 admits an adversary that is a *message*.** The
  hardware arguments (air-gap OFF, structural bleed, `+VIN` removal, the `VSET` clamp) survive that
  change unaltered — which is, in retrospect, the strongest thing that can be said for having chosen a
  hardware-first topology. The **firmware** arguments do not.
- **It priced a BOM in which the dominant line was unpriceable.** G0-A2 retires that specific
  embarrassment (the modules are owned) and leaves behind a sharper one: **the relay is now the largest
  unpriced line in the combiner, and two independent agents failed to price it.**
