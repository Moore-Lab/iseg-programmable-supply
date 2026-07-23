# SCOPE — iseg Bipolar HV Controller

**Phase 1 deliverable (bootstrap §II Phase 1). Status: ✅ GATE G0 SIGNED OFF, 2026-07-23.**
Session 1 wrote this against an undecided gate. Session 2 collapsed the conditionals to the decided
reality. Bootstrap `EE_PROJECT_BOOTSTRAP.md` v1.0, first field test.

> ### ⬛ What G0 decided (verbatim answers in `docs/G0_QUESTIONS.md`)
>
> - **G0-A1 — set-and-hold with polarity changeover.** ~1 s dead-band, output clamped to ground.
>   ⇒ combiner is **HV relay changeover**; series-stack, diode-OR and single-module-reversing are
>   **rejected permanently**.
> - **G0-A2 — the modules are ALREADY OWNED: `AP010504P05` + `AP010504N05`** ⇒
>   **1 kV / 0.5 mA / 0.5 W / 5 V in / Vref 2.5 V**, both polarities, in hand.
> - **G0-A3 — both serial AND network, FULL WRITE AUTHORITY on both.**
> - **G0-A4 — ⚠ SCOPE CHANGE: switchable single-bipolar-output *or* two-independent-unipolar-outputs.**
>   **This amends the original brief**, which said "explicitly *not* two independent unipolar outputs".
> - **G0-A5 — MODE SELECTION IS A PHYSICAL SWITCH. There is NO mode relay.** The question A4 created
>   (mechanism (a) vs (b)) was **answered the same day** in favour of (a), because the remote
>   flexibility (a) appeared to cost was **illusory — mode change requires re-cabling anyway.**
>
> **Q3 (output spec), Q5 (safety envelope), Q6 (weld) and Q7 (procurement) were NOT answered** — those
> proceed on the stated defaults and remain flagged. See `G0_QUESTIONS.md` §7.
>
> ### ⬛ TERMINOLOGY — the human's words, adopted project-wide (G0-A5)
>
> **"pseudo-bipolar"** = mode 1, single output, polarity changed **by switching across zero**. The word
> is deliberately honest: this instrument does **not** pass smoothly through zero (G0-A1).
> **"unipolar / dual-output"** = mode 2, two outputs, both energisable at once.
> Text below written before A5 says "BIPOLAR COMBINED" for mode 1; read it as **pseudo-bipolar**.

---

## 0. Machinery being collapsed, and why

The bootstrap requires this statement up front (§VI, final line: *"State up front which parts of
the machinery you are collapsing for the project's size, and why"*). Here is the complete list.
**Every gate is retained. Only the lane topology and the tool count are collapsed.**

| Machinery | Bootstrap default | This project | Why |
|---|---|---|---|
| **Lane split** | Two parallel sessions: *schematic lane* (golden netlist → symbols → schematic → netcmp/legibility) and *board lane* (cell → tiling → routing → DRC/parity → fab) | **ONE session runs both, sequentially** | §VI explicitly permits it: *"Small boards collapse to one session (Principle 6) — but the gates never collapse."* This board is ~1 sheet, ~120 components, 2 HV modules, 1 MCU. The two-lane split exists to parallelise a 12-channel board with 400+ parts and a repeated-cell tiler. Here the coordination overhead (shared `board_spec.py` contract, cross-session `git` handoffs, two cold boots) would exceed the work being parallelised. **The gates G1, Phase-3 human schematic read, Phase-4 DRC/parity, Phase-5 GUI read, Phase-6 fab commit, Phase-7 bench all remain, in the same order, with the same human in them.** |
| **Cell-then-replicate tiler** (§V.4, "the single most important layout decision") | Route one cell, replicate programmatically | **NOT USED** | There is no repeated block. Two HV branches are mirror-image, not identical (opposite polarity, different netclass assignments, asymmetric bleed placement). A 2-instance tiler is more code than two hand-placed branches and hides the asymmetry that is the whole point of the design. |
| **FreeRouting** (§III) | Headless jar + JRE + dead-proxy workaround | **NOT USED — hand-route in the generator** | Autorouting an HV board is unsafe: FreeRouting has no concept of creepage-vs-clearance, no notion that a 15 mm gap between `HV_POS` and `HV_NEG` is a safety requirement rather than a DRC preference, and no way to express "this gap must be a slot". Every HV net is routed explicitly in `gen_pcb.py`. Low-voltage digital may be autorouted later if the part count justifies it; that is a Phase-4 decision, not a Phase-1 one. |
| **`ARCHITECTURE.md`** | "where warranted" | **Folded into `INTERFACES.md` + `COMBINER_STUDY.md`** | One board, one MCU. A separate architecture document would restate the combiner study and the interface contract with nothing added. |
| **`tasks/` + `roles/` directories** | Per-lane task briefs | **NOT CREATED** | Artefacts of the two-lane split. With one session, `PLAN.md` + `STATUS.md` carry the same information without a second place for it to go stale. |
| **`docs/PIPELINE_LOG.md`** | Mandatory | **RETAINED — created this session, 14 entries** | Not collapsible. This run *is* the bootstrap's first field test; the log is the deliverable that feeds v1.1. |
| **Numbers probe** | "a throwaway scipy/numpy script" | **RETAINED but NOT throwaway, and stdlib-only** | Two corrections to the bootstrap, both logged (PL-01). KiCad's bundled Python has no scipy; and the probe is standing evidence for `DECISIONS.md`, so it must be re-runnable and deterministic like any other generated tool. |

**What this collapse costs.** One session cannot review its own schematic. The bootstrap's answer
is not "a second AI lane" — it is Principle 12, *the human at the GUI is a different instrument*.
The collapse therefore increases, not decreases, dependence on the human review gates. That is the
trade being made explicitly.

---

## 1. Objective — **AMENDED AT G0**

A benchtop **dual-mode high-voltage controller** built from two iseg **`AP010504`** modules of opposite
factory polarity (`P05` and `N05`, **both already owned**), **±1000 V, 0.5 mA, 0.5 W, 5 V input,
Vref 2.5 V**. Commanded and read back by an **ESP32** over **serial and network, both with full write
authority** (G0-A3).

**Two operating modes, selectable** (G0-A4):

| Mode | Behaviour |
|---|---|
| **MODE 1 — PSEUDO-BIPOLAR** *(single output)* | Both modules route to **ONE** output terminal, one at a time, break-before-make, with the deselected module bled to ground. Polarity crossing is a **set-and-hold changeover** with a ~1 s dead-band during which the output is actively clamped to ground (G0-A1). Smooth through-zero is **not** required — hence *pseudo*-bipolar. |
| **MODE 2 — UNIPOLAR / DUAL-OUTPUT** | The positive module drives **output A**, the negative module drives **output B**, **independently**, and **BOTH MAY BE ENERGISED SIMULTANEOUSLY.** That is the point of the mode. |

**Mode is selected by a PHYSICAL SWITCH the operator moves (G0-A5).** It is not commandable over serial
or network, at all, by design. Mode change is a **powered-down, cables-off** operation.

> ⛔ **Session 1 wrote: *"Explicitly **not** two independent unipolar outputs. The combiner is the
> design."* — THAT SENTENCE IS SUPERSEDED.** It was a faithful restatement of the original brief;
> **G0-A4 amends the brief.** Dual-mode is a **first-class requirement**, not a bolt-on.
>
> ⬛ **AND THE A4 PASS'S OWN FOLLOW-ON SENTENCE IS NOW ALSO SUPERSEDED.** It read: *"the combiner is now
> one of two HV routing problems — the second being the **mode routing element**, which is the more
> safety-critical of the two."* **G0-A5 overturns that assessment.** With the mode set by a physical
> switch whose HV poles and LV interlock poles are **moved by the same armature**, the mode element
> **cannot disagree with the interlock by construction** — so it is **not** the more safety-critical of
> the two; the **polarity combiner is**, and it is the one that still hot-switches, still welds, and
> still needs the S5→S6 discharge interlock. **The mode element's danger came entirely from it being
> firmware-commanded, and A5 removed that.**

---

## 2. Constraints

### 2.1 Non-negotiable (from `CLAUDE.md`, restated because everything below serves them)

| # | Invariant | Status after G0 (2026-07-23) |
|---|---|---|
| **(a)** ⬛ | ⛔ ~~Both modules enabled into the output simultaneously must be **unreachable in hardware**.~~ **RESTATED AT G0-A4, NOT DISCARDED:** **it must be impossible for both modules to be connected to the SAME OUTPUT NODE simultaneously**, enforced in hardware. Firmware agreement is not sufficient. | **Why the restatement.** Read literally, mode 2 *violates* the old wording — both modules energised at once is mode 2's whole purpose. The generalisation preserves the entire safety intent: in **mode 1** it forbids the both-enabled state **exactly as before**; in **mode 2** it is satisfied **structurally**, because the two modules are on physically different nodes. **The cost of the restatement is that the MODE becomes a SAFETY INPUT**, and therefore the interlock permissive **must be derived from the mode element's ACTUAL PHYSICAL POSITION**, **never from a commanded mode bit** — otherwise a firmware fault, a stuck GPIO, or a network command (G0-A3 grants network write authority) can assert "mode 2, both permitted" while the HV routing is physically still in the mode-1 position, which *is* the forbidden state. `DECISIONS.md` MODE-02, MODE-03. Satisfiable with the adopted relay topology (G0-A1). **⬛ G0-A5 PAYS THIS COST IN FULL AND CHEAPLY.** The mode is a **physical switch** (MODE-04): its **HV poles and its LV interlock poles are moved by the same armature**, so the permissive and the routing **cannot disagree by construction** — strictly stronger than the sensed-relay-position scheme the A4 pass specified, which could disagree if a sense contact were mis-wired to the coil command. **And there is no commanded mode bit at all**, so the hazard is not defended against, it is **unreachable**. What remains to engineer: aux-pole **lead-break timing** (MODE-15), **intermediate-position** decode (MODE-18), and the **runtime-change trip** (MODE-16). |
| **(b)** | Defined discharge/bleed path **on changeover and on disable** — **and now on MODE CHANGE, at BOTH output nodes**. | Satisfiable, and cheaply, for the polarity changeover: the adopted topology satisfies it *structurally* (through the relay's own NC contact) rather than by a firmware timer. **G0-A4 adds a transition that did not exist in session 1's state machine**: a mode change must be as safe as a polarity changeover — both outputs to zero, both modules disabled, dwell for bleed, **then** move the element **cold**. ⬛ **G0-A5 KEEPS THE PHYSICS AND DELETES THE STATE MACHINE.** With no relay to command there is **nothing for firmware to move**, so *"its own timeouts, and a discharge timeout must TRIP rather than fall through"* **has no subject** — that transition does not exist. The identical sequence survives as a **powered-down OPERATING PROCEDURE** (MODE-08, MODE-17), enforced by a **guard over the switch** and a **panel legend**, and backstopped by **MODE-16** (a mode change seen at runtime forces HV **OFF immediately**, never gracefully) and by the switch's own **lead-break** contacts (MODE-15). `DECISIONS.md` MODE-08, MODE-10, MODE-15…18. |
| **(c)** | Output voltage monitored **independently** of the module readbacks — **now on TWO outputs**. | Satisfiable, but **still** over-claimed as drawn. A skeptic showed the proposed dividers feed an ADS1115 with no buffer, giving 7–17 % loading error — worse than the 1 %·Vnom module monitor it exists to check. One ~$1 op-amp fixes it (ARCH-08). **G0-A4 doubles the requirement**: a second independent divider string, each loading its own module by **1.00 % of the 0.5 mA Inom** at 1 kV — exactly at the adopted budget, with no margin left (G0-A2 makes this binding, not hypothetical). One ADS1115 no longer covers the channel count. `DECISIONS.md` MODE-07. |
| **(d)** | HV creepage/clearance encoded as **DRC netclass rules** (executable), and netclasses must carry their **schematic** fields or eeschema connectivity silently breaks (bootstrap §V.3). | **Still partially blocked, and now MORE load-bearing.** The arithmetic is done; the *governing constant* is `[recalled]` `[unverified-primary]` and its worst-case premise was refuted (R-1). **What G0 settled:** the class is 1 kV (G0-A2) **and the 2 kV `HV_POS`↔`HV_NEG` gap is now the NORMAL STEADY-STATE condition, permanently** (G0-A4) — not a fault case, not topology-conditional. **What G0 did not settle: the number itself.** No human answer can; only a primary document can. |
| **(e)** | First energization is human-present. **No session ever claims the Phase 7 gate.** | Held. **G0-A3 makes it more pointed**: the network can command HV, so "human-present" must mean present *at the instrument*, and the arm/disarm step (ARCH-35) is what makes that enforceable rather than aspirational. |

### 2.2 Part constraints — **the part is now known exactly** (G0-A2)

**`AP010504P05` and `AP010504N05`, one of each, IN HAND.** Decoded per `DECISIONS.md` PART-12:
`AP` · `010` = 1 kV · `504` = 0.5 mA · `P`/`N` · `05` = 5 V in ⇒ **the 0.5 W / 5 V family**.

| Parameter | Frozen value |
|---|---|
| `Vnom` | **1000 V** per module · `Inom` **0.5 mA** · `Iout` ≤ **0.75 mA** (1.5 × Inom) |
| `Vin` | **5 V** (4.5–5.5 V). ⛔ **NOT 12 V** — every 12 V-family statement in this repo is *wrong*, not superseded |
| `Vref` | **2.5 V ±1 %**. ⛔ **NOT 5 V** · `Vset`, `Vmon` full scale **0…2.5 V** |
| `Iin` | <5 mA at Vout=0 · <25 mA at Vnom no load · **<180 mA at Vnom loaded**, **per module** |
| Ripple/noise | typ <10 mVpp, max <30 mVpp (f>10 Hz), <5 mVpp (f>2 kHz) — **only above 20 V; see below** |
| Accuracy | adjustment ±1 % = **10 V** · VMON 1 %·Vnom = **10 V** |

- **Polarity is factory-fixed** by a letter in the item code (`P`/`N`). One module = one polarity,
  permanently. Both are owned, so this is spent, not pending.
- **`/ON` is active-LOW and floats to ON.** Table 4, verbatim: *"LOW or n.c. → HV ON"*. The module's
  default with an undriven pin is HV **on**. Every safe state must be actively held. **`+VIN` is 5 V,
  which sits inside the module's own 2.5–5.5 V `/ON`-HIGH window** — so pulling `/ON` up to the
  module's own `+VIN` (ARCH-17) is directly legal and **no dedicated ≤5.5 V rail is needed**. That
  simplification is a direct gain from G0-A2.
- **An open `VSET` node commands FULL SCALE.** Internal 10 kΩ pull-up to Vref.
  `[verified — 3 independent skeptics, see §4]`
- ⬛ **Output voltage is internally NOT limited** above Vref (datasheet's own bold warning, with **no
  stated ceiling**). `Vset > Vref → Vout > Vnom`. **G0-A2 makes this the design condition rather than a
  scenario:** Vref is **2.5 V** and the ESP32 is a **3.3 V** part, so a logic fault, a mis-set DAC
  reference, or a floating node pulled to 3.3 V commands **3.3/2.5 = 132 % ⇒ ≈1320 V**. Composed with
  the two facts above, **the module's un-driven default state is ENERGISED AT OVER-RANGE.**
  ⇒ **The hardware `VSET` clamp is a PRIMARY SAFETY ELEMENT of this design and gets its own
  verification** (`DECISIONS.md` PART-33, ARCH-06). Session 1 recommended the 1 W / 12 V family
  *specifically* to avoid this; G0 answered the other way, so it must be engineered, not avoided.
- **Specifications for stability, ripple and noise are guaranteed only for `2 %·Vnom < Vout ≤ Vnom`,
  i.e. only above 20 V.** Below 20 V the output is **UNSPECIFIED, not merely degraded** — quote that
  sentence wherever a low-end spec is quoted. This is the fact that governed the through-zero question,
  and G0-A1's answer means we now simply **stay out of that band** rather than trying to traverse it.
- **The module has an internal ~100 ms set-node time constant** (100 kΩ into 1 µF, Figure 2). Full-scale
  settle ≈460 ms (1 %) / 690 ms (0.1 %). This dominates every timing budget in the project; no combiner
  is faster than the module — which is why G0-A1's ~1 s dead-band is a *module* property, not a
  combiner shortcoming.
- **The case is bonded to GND** (pins 3 and 7). Floating a module means floating a bare steel can —
  and G0-A1 rejects every topology that would have required it, so **no module is ever floated**
  (`DECISIONS.md` PART-26, now frozen).
- **The modules are IN HAND** ⇒ the four unpublished parameters (VSET step response, HV output
  capacitance, internal bleeder resistance, turn-on time from `+VIN`) and the pin geometry are now
  **bench- and caliper-measurable**. See R-4 and `DECISIONS.md` LIB-18.

### 2.3 Environment constraints (`CLAUDE.md` rules 1–4)

Generated CAD is a build artifact — fix the generator, never the file. Board-geometry tools import
`pcbnew` and run under `PY_KICAD`; everything else is stdlib-only and runs on any Python 3.
`ZONE_FILLER.Fill()` never runs in the process that built the board. Deterministic identity from
`uuid5`, never `uuid4`. Absolute forward-slash paths, quoted (the repo path contains a space).

---

## 3. Success criteria

Inherited from the brief, tightened where session 1 produced a number. Anything still bracketed is
frozen at G0/G1, not now.

| # | Criterion | Instrument | Frozen at |
|---|---|---|---|
| S-1 | Fab-ready outputs passing the full bootstrap gate set (§V.7 pre-fab checklist, every line) | the checklist | now |
| S-2 | Bench-commanded bipolar sweep across full range from the ESP32 — **over BOTH interfaces, since both now have write authority (G0-A3)** | Phase 7, human present | **range FROZEN by G0-A2 at ±1000 V** (mode 1); interface G1 |
| S-2b | **NEW (G0-A4):** both outputs energised **simultaneously** in dual-unipolar mode, +1 kV on A and −1 kV on B, held, and both read back independently | Phase 7, human present | now |
| S-3 | ⬛ **RESTATED (G0-A4), RE-SCOPED (G0-A5).** **No state in which both modules are connected to the SAME output node** — demonstrated by *attempting* to reach it and observing **hardware** refusal, not by reading firmware. (i) in **pseudo-bipolar** mode, attempt both-enabled — hardware must refuse. (ii) ⛔ ~~command mode 2 while the routing element is physically held in the mode-1 position and observe the interlock refuse~~ **— STRUCK: UNPERFORMABLE. G0-A5 means there is no way to command a mode**, which is precisely why the fault it tested for cannot occur. **Replaced by three performable tests:** (ii-a) **aux poles break before HV poles make** — scoped on the actual switch (MODE-15); (ii-b) **switch parked between detents ⇒ both modules off, both outputs bled** (MODE-18); (ii-c) **switch moved while energised ⇒ HV off immediately** (MODE-16). **(ii-a) is now the single most important test on the board**, because it is the one thing standing between an off-procedure mode change and both modules on one node | Phase 7 + a power-up weld/stuck-contact self-test + **oscilloscope on the mode switch's contact sequence** | now |
| S-4 | Readback agreeing with a DMM within a tolerance frozen at G1 — **on both outputs** | DMM vs `MEASure:VOLTage?` | G1. Target: independent monitor better than **0.2 % of full scale**, i.e. ≥5× tighter than the module's own **10 V** (1 %·Vnom at the now-confirmed 1 kV). Currently *not* met by the proposed circuit (see R-3). |
| S-5 | Safe discharge on disable verified — output below **60 V within 5 s** with the board **unpowered** — **at BOTH output terminals, and after a MODE CHANGE as well as after a disable** | stopwatch + DMM, Phase 7 | now (the 60 V/5 s numbers are `[recalled]` `[unverified-primary]`, R-2) |
| S-6 | Every MPN re-verified against a live distributor page at Phase 6 | distributor page | now |
| S-7 | `docs/PIPELINE_LOG.md` harvested into proposed bootstrap v1.1 edits at fab commit | the log | now |
| S-8 | **NEW (G0-A2/A3):** the **hardware `VSET` clamp** is verified independently — drive the set path to its electrical limit and confirm the output cannot exceed Vnom. This is a **primary safety element** (PART-33), not a design note, and it is the barrier that stands between a 3.3 V logic fault (or a hostile network write) and ≈1320 V | Phase 7, human present, on the buffered set path | now |

---

## 4. What is frozen vs what waits for G0

**Frozen** = decided, with evidence, and changing it now requires a gate.
**Assumed-pending-G0** = we are proceeding on a stated default; the human may overturn it at G0 at
low cost. **Open** = genuinely blocks; batched into `docs/G0_QUESTIONS.md`.
Full detail, with evidence per row, is in `docs/DECISIONS.md`.

### 4.1 FROZEN

| Area | Decision |
|---|---|
| Part family | iseg APS series, 7-pin, analog control (`VSET`/`VMON`//`ON`). The pin map is verified — see below. |
| Pin map | 1 `+VIN`, 2 `VSET`, 3 `GND`, 4 `/ON` (active-low), 5 `VMON`, 6 `HV`, 7 `GND`. **[verified — 3 independent skeptics, incl. re-render of Figure 1's top view, agreement with the 2019 v2.1 revision, KiCad's own renderer, pcbnew's loader, and a third-party footprint from a board that was actually built]** |
| Footprint geometry | Body 39.60 × 15.70 × 11 mm, **off-centre** from the pin array by **+0.60 mm** (long axis, toward the pins 6/7 end) and **+0.23 mm** (short axis, toward pin 5). **[verified — 3 independent skeptics, two by independent pixel metrology of the vendor artwork, one confirming the dimension→edge attachment feature-by-feature]** Not mirrored. |
| CAD identity | Symbol `iseg:APS_HV_MODULE` (+ `_P`/`_N` derived), footprint `iseg:iseg_APS_THT`, 3D model `iseg_APS_THT.step` at `(offset 0 0 0)`. |
| Land pattern | 1.30 mm drill (0.395 mm diametral over the 0.905 mm square-pin diagonal), 2.10 mm pad (0.40 mm annulus). Reference board's 1.143/1.778 evaluated and **rejected** — no budget for the module's undocumented pin-position tolerance. |
| Two safety facts that drive schematic topology | `/ON` open ⇒ HV ON, and `VSET` open ⇒ FULL SCALE. Both **[verified]**. Consequences: `/ON` gets a redundant pull-up to a ≤5.5 V rail *at the module pin*; `VSET` gets a pull-down at the pin; `+VIN` removal is the primary disable, not `/ON`. |
| Set-path clamp mechanism | The `VSET` buffer op-amp is powered **from the precision reference itself**, so its output physically cannot exceed Vref. Zero added components in the signal path. |
| `VSET` drive impedance | ≤ 10 Ω from driver to pin. Not a preference: any series R divides against the internal 10 kΩ and injects a *positive* offset — 1 kΩ puts 91 V on a 1 kV module when zero was commanded. |
| Combiner topology | ✅ **`hv-relay-changeover`, ADOPTED (G0-A1).** ~~conditional on set-and-hold being acceptable~~ — **the condition is satisfied.** Unanimous #1 across all three judge lenses at exactly 7/10 each. Its four mandatory corrections (TOPO-08) are now unconditional. |
| **Module** | ✅ **`AP010504P05` + `AP010504N05`, IN HAND (G0-A2).** 1 kV / 0.5 mA / 0.5 W / 5 V in / **Vref 2.5 V**. Not orderable, not choosable — owned. |
| **Behaviour** | ✅ **Set-and-hold with polarity changeover (G0-A1).** ~1 s dead-band, output clamped to ground during it. Smooth through-zero is **not** required and is **not** being built. |
| **Comms** | ✅ **Both serial and network, FULL WRITE AUTHORITY on both (G0-A3).** Deliberate, risk-stated. An explicit **arm/disarm** step and a **comms-loss watchdog failing to HV-OFF** are consequently **required**, not optional. |
| **Output modes** | ✅ **Two, switchable (G0-A4):** **pseudo-bipolar** (one terminal) **or** **unipolar / dual-output** (two terminals, both may be live). |
| **Mode mechanism** | ✅ **A PHYSICAL SWITCH the operator moves (G0-A5). There is NO mode relay — do not design one.** Not commandable over serial or network, by design. Mode change is a **powered-down, cables-off** operation, guarded and legended (MODE-04, MODE-17). |
| **Interlock derivation** | ✅ **The mode permissive comes from an AUXILIARY LV POLE of that switch — the same armature that moves the HV poles (G0-A5 / MODE-03, MODE-14).** Combinational, never latched, never cached. ~~*Which* mechanism provides it is a G1 decision~~ **— decided at G0-A5.** What remains at G1 is the **part** (MODE-13) and the **timing margin** (MODE-15). |
| **Set-path clamp status** | ✅ **PRIMARY SAFETY ELEMENT (G0-A2 / PART-33)** — promoted from "a nice property of the DAC" because Vref = 2.5 V against a 3.3 V MCU makes 132 % of Vnom a one-fault condition. |
| **Supply sizing rule** | ✅ **Both modules loaded simultaneously (G0-A4 / NUM-22).** The "only one is ever enabled" argument is dead. |
| Pipeline discipline | `PIPELINE_LOG.md` exists and is append-only. Round-tripping through `kicad-cli` and byte-comparing is now a standing requirement for every KiCad text emitter (PL-02). |

### 4.2 STILL ASSUMED after G0 — because the human did not answer Q3, Q5, Q6 or Q7

*(Session 1's list, with the resolved entries struck and the survivors annotated with **why** they
survived. Full evidence per row in `DECISIONS.md`.)*

**Resolved by G0 — no longer assumptions:** ~~module class 1 kV / 0.5 mA / 0.5 W~~ (**confirmed exactly,
G0-A2 — the worst-case sizing assumption turned out to be the real part, so no number needed
rescaling**) · ~~behaviour set-and-hold~~ (**G0-A1**) · ~~module GND at board ground, not floated~~
(**G0-A1 rejects every topology that would have floated it**) · ~~supply sized for both modules loaded~~
(**G0-A4 makes it a normal operating requirement, not a margin choice**) · ~~comms posture~~ (**G0-A3**).

**Still assumed, and why each survives:**

| Assumption | Why it survived G0 |
|---|---|
| MCU **ESP32-S3** | G0 never asked about the MCU. G0-A3 raises the bar it must clear (dual-core safety-supervisor isolation is now load-bearing, not a nicety) and G0-A4 adds GPIO ~~(mode command **plus** mode position-sense)~~ — **G0-A5 halves that: no mode-command output exists (no relay to drive), only mode position-sense INPUTS from the switch's aux poles.** → G1. |
| Module output capacitance **100 pF–1 nF**, internal bleeder **~20 MΩ**, restart **~150 ms**, VSET step response | iseg publishes none of them and nobody asked the vendor. **But G0-A2 makes all four bench-measurable — the modules are in hand.** These must not survive G1. |
| Load capacitance **≤10 nF** as a declared hard interface limit | **Q3 was not answered.** This remains a limit *we impose*, not a fact about the user's load. Now applies **per output** (two cables, two loads). |
| Touch-safe **60 V / 5 s**; stored-energy **350 mJ / 50 µC** | **Q5 was not answered** — and no human answer could fix these. They need a **primary standards document**. Tagged `[unverified-primary]`. |
| Clearance margin **1.5×**; **no conformal coating** | **Q5 was not answered.** ⚠ Note the standing contradiction: ARCH-14 *mandates* coating over the divider region for leakage control while NUM-18 assumes *no* coating for clearance. **Both cannot be true. Resolve before layout.** |
| Bleed budget **10 % of Inom**, monitor budget **≤1 % of Inom** | Engineering choices, not questions that were asked. **G0 removed the slack**: at the confirmed 1 kV / 0.5 mA a 5 µA divider is *exactly* 1.00 %, and G0-A4 requires two such strings. |
| **No current readback exists** on the 7-pin part | **Q7 was not answered**; nobody emailed iseg; PART-20's Table 1 / Table 4 contradiction is untouched. |
| Weld: **detection, not prevention** | **Q6 was not answered.** Default stands. If prevention is ever required, **every candidate on the panel dies** and the topology study reopens. |
| Connector **SHV** | Q5 not answered; default stands — **but the count is now two** (G0-A4), spaced for 2 kV. |
| Resistor package voltage ratings, ADS1115/CRHV coefficients, strapping-pin lists, surface leakage | Datasheet reads and board measurements, not human decisions. → G1. |

≈30 further rows, every one traceable to the agent that logged it, in `DECISIONS.md`.

### 4.3 OPEN after G0 — carried forward, flagged

*(Session 1's G0-1…G0-5 are struck where answered. Full list and reasoning: `G0_QUESTIONS.md` §7.)*

| # | Question | Status |
|---|---|---|
| ~~**G0-1**~~ | ~~Is smooth through-zero required, or is set-and-hold acceptable?~~ | ✅ **ANSWERED — set-and-hold (G0-A1).** Relay changeover adopted; three topologies permanently rejected; the APS family is **not** disqualified. |
| ~~**G0-2**~~ | ~~Module class and family~~ | ✅ **ANSWERED — the modules are owned (G0-A2).** 1 kV / 0.5 mA / 0.5 W / **Vref 2.5 V**. Session 1's *recommendation* of the 1 W / 12 V family is **overturned**; its worst-case *sizing assumption* is **confirmed**. |
| **G0-3** | Output spec: maximum load current, **load capacitance**, required ripple | ⬜ **NOT ANSWERED.** Full scale is now pinned by G0-A2 to ±1000 V and load current by Inom = 0.5 mA; `C_load` and ripple remain unknown. Proceeding on the §4.2 defaults. |
| ~~**G0-4**~~ | ~~Comms and write authority~~ | ✅ **ANSWERED — both transports, full write authority on both (G0-A3).** Session 1's read-only-network recommendation is **overturned deliberately**; do not quietly reinstate it. |
| **G0-5** | Safety envelope: working standard, conformal coating yes/no, enclosure ownership | ⬜ **NOT ANSWERED, and now MORE load-bearing** — G0-A4 makes the 2 kV gap permanent, so the unverified constant governs a *normal* condition. Coating remains a pre-layout process commitment **and contradicts ARCH-14**. |
| **G0-6** | Weld: detection or prevention? | ⬜ **NOT ANSWERED.** Default = detection + mandatory power-up self-test. G0-A4 adds the **mode routing element** to the set of things that can weld — the worst member of the set. |
| **G0-7** | iseg technical questions + relay/HV-passive procurement | ◐ **PARTIALLY OVERTAKEN.** G0-A2 removes the *module* line from the schedule risk entirely (owned) and makes three of its four unknowns bench-measurable. **PART-20 (current-monitor contradiction) and R-7 (relay / HV resistor lead times) are untouched.** |
| ~~**O-7**~~ | ~~**Mode mechanism: (a) physical human-set element, or (b) relay with armature-position sense?**~~ | ✅ **ANSWERED SAME DAY — (a), a PHYSICAL SWITCH (G0-A5).** Session 1's framing of the trade was **wrong**: (a) does not cost remote flexibility, because *"we would need to physically change cables, anyways"*. **No mode relay; no sense path; no sense-path failure analysis.** |
| **O-10 (NEW)** | **Which physical element, and can it be sourced?** 1 kV working per HV pole, **2 kV between opposite-polarity poles** if the arrangement creates such a pair, **plus auxiliary LV poles**. Candidates: HV rotary · ceramic wafer · **HV link block** · **HV cable re-plug**. | ⬜ **NEW AT G0-A5.** A genuinely awkward part class. **If no suitable panel switch is procurable, a link block or connector re-plug is legitimate engineering and should be recommended** — the requirement is "a physical thing the operator moves", not a toggle. Joins **R-7**. `DECISIONS.md` MODE-13. |
| **O-11 (NEW)** | **The contact-timing margin: how far must the LV aux poles LEAD the HV poles?** | ⬜ **NEW AT G0-A5.** The requirement (aux **break before** HV **make**) is frozen; the **margin** and the behaviour of a non-conforming switch are not. Bounded hazard: at ≈0.75 mA the worst case is a **current-limited polarity fight, not an energetic fault**. `DECISIONS.md` MODE-15. |
| **O-8 (NEW)** | **Scoping the network write path**: bounded parser, authentication, session management, OTA security, arm/disarm, comms-loss watchdog | ⬜ **NEW AT G0, created by G0-A3.** The human accepted the risk knowingly — that makes the work **mandatory**, not optional. |

---

## 5. Risks

Ordered by what they cost if they bite. Each names the instrument that would catch it.

| ID | Risk | Severity | Mitigation / owner gate |
|---|---|---|---|
| **R-1** | **The governing clearance constant is `[recalled]`, and its worst-case premise was refuted.** IPC-2221B and IEC 60664-1 are both paywalled and neither is on this machine. The probe's own "independent cross-check between two standards families" was shown by three skeptics to be an **algebraic tautology** (both sides reduce to exactly 0.005·V above 500 V) *and* single-source (both columns came off the same web page). Worse: the probe sizes HV-to-GND for 1×Vnom while its own §6.1 asserts that a single VSET wiring fault gives **132–200 % of Vnom**. Four sibling documents carry four mutually incompatible IPC numbers. **⬛ G0 MADE THIS WORSE IN TWO WAYS AND FIXED NEITHER.** (i) **G0-A4**: the 2 kV `HV_POS`↔`HV_NEG` gap is now the **NORMAL STEADY-STATE condition, permanently** — not a fault case, not a topology-conditional worst case — so the gap most dependent on the unverified constant is also the gap that is always energised. (ii) **G0-A2**: the "132–200 % of Vnom" VSET-fault figure is no longer a range spanning two candidate families — **Vref is confirmed 2.5 V against a 3.3 V MCU, so 132 % ⇒ ≈1320 V is the specific one-fault number this board must survive.** **No human answer can freeze the constant; only a primary document can.** | **Highest, and raised by G0.** A wrong number in a DRC file is undiscoverable after fab. | A human obtains a primary copy of the working standard **before G1 closes**. Until then **no netclass number is frozen**, every clearance number keeps the tag **`[unverified-primary]`**, and DRC values stay **conservative**. Pre-fab checklist gains "every standards-derived constant traced to a primary document". |
| **R-2** | Touch-safety thresholds (60 V DC, 5 s; 350 mJ; 50 µC) are `[recalled]` with no primary source. The whole Phase-7 safety argument rests on them. **Unchanged by G0 — Q5 was not answered.** Scope doubled by G0-A4: the criterion must now be met **at both output terminals**, and after a **mode change** as well as after a disable. | High | Confirm against IEC 61010-1 / 62368-1 before Phase 7. Already checklist items P1/P2 in `NUMBERS_PROBE.md`. |
| **R-3** | **Invariant (c) is currently nominal, not real.** Every proposed monitor hangs an ADS1115 straight off a 0.4–1.25 MΩ divider leg. TI's own datasheet gives 2.4–22 MΩ input impedance and says buffering *can be necessary*; the resulting 7–17 % gain error is worse than the 1 %·Vnom module monitor the divider exists to check. Divider **voltage coefficient** is uncosted in all five topology studies. **G0 doubles the exposure and removes the margin:** G0-A4 requires **two** independent monitor chains (one per output), and G0-A2 confirms the 1 kV / 0.5 mA class in which a 5 µA divider is **exactly 1.00 % of Inom** — the loading budget is now *at* its limit, per output, with nothing in hand. One ADS1115 no longer covers the channel count. | **High, and raised by G0.** | One sub-nA-bias unity-gain buffer (~$1) **per monitor, per output**, mandatory. Divider VCR must be read from the chosen part's datasheet at G1. Second ADC (different I²C address) is now **required**, not contingent. |
| **R-4** | **Every timing and discharge number in the project is parametric in numbers iseg does not publish.** Four agents independently confirmed the absence: no output capacitance, no internal bleeder, no discharge time, no slew rate, no restart time, no reverse-voltage rating on pin 6, no GND/case isolation rating. **⬛ G0-A2 DOWNGRADES THIS RISK — the modules are IN HAND.** What was "a vendor dependency we cannot resolve" is now "an afternoon on the bench", and there are **two** units (P and N), which additionally permits unit-to-unit comparison rather than a single sample. **The risk is now one of *not doing the work*, not of being unable to.** | **High → Medium**, conditional on the bench session actually happening before G1. | **Bench-measure four numbers before G1** (VSET step response, output C, internal bleeder, turn-on time) — plus **calipers** on both modules (closes LIB-15/17/18 and PART-23). Session 2 writes the procedure. Still one email to iseg for the two ratings and the current-monitor discrepancy (PART-20). |
| **R-5** | **Phase 0 gate is NOT met.** The bootstrap defines it as *"the throwaway board produces gerbers"*. Zero gerbers exist anywhere in the repo, no DRC report, no render, and `docs/ENVIRONMENT.md` does not exist. Three independent skeptics confirmed. The board *can* produce gerbers (all three exported them successfully to scratch), so this is missing work, not a broken toolchain. | Medium | Close in the first 30 minutes of session 2: add gerber + **drill** export to `gen_pcb.py`, commit outputs, write `ENVIRONMENT.md`. (Note the board has 1 via — a gerber set without a `.drl` is unmanufacturable.) |
| **R-6** | **Reed relays are magnetically operable.** A stray magnet closes an HV contact with **no coil current**, which bypasses *all three* of the recommended topology's interlock layers at once (two of them gate coil power, and a magnet needs none). This lab plausibly contains cryostats and magnetic mounts. **⛔ G0-A2 REMOVES THE ESCAPE ROUTE.** Session 1's mitigation ended *"if the environment is magnet-rich, the solid-state combiner becomes competitive at ≤600 V"* — **the solid-state combiner is eliminated at 1 kV** (its parts do not reach), so **this failure mode must be mitigated in place. There is no longer an alternative topology that lacks it.** ~~G0-A4 adds a second magnetically-operable element: the **mode routing relay**, whose spurious closure is worse than a polarity relay's because it can put both modules on one node.~~ ⛔ **STRUCK BY G0-A5 — and this is a real risk reduction, not a relabel. The mode element is a MECHANICAL SWITCH with no coil and no reed: a magnet cannot operate it.** The magnetically-operable set is back to the **two polarity reeds**, exactly as before A4. | **Medium → Medium-High** (from A2's loss of the T2 escape route), **not raised further by dual-mode.** Mitigation-only, no alternative. | Mu-metal-screened parts, ≥5 mm relay spacing, enclosure note, power-up self-test. Ask the human directly whether cryostats/magnetic mounts sit within ~100 mm of the enclosure — that question is now consequential rather than informational. |
| **R-7** | **HV passive availability.** Across four agents' live searches: 0-stock, obsolete, and 13-week-lead on nearly every HV resistor checked. Exactly **one** was verified genuinely in stock. The recommended relay is Form C, build-to-order, and two independent agents failed to price it (three timeouts + an HTTP 403). **G0-A2 removes the modules from this risk entirely — they are owned.** But **G0-A4 adds parts to it**: a second HV divider string, a second bleed network, a second SHV connector — all drawn from the same scarce supply. **⬛ G0-A5 CHANGES ONE LINE AND IT IS NOT OBVIOUSLY AN IMPROVEMENT — say so rather than banking a win.** The mode element is **no longer an HV relay** (which would have come from the same scarce, unpriceable Form-C supply as the polarity relays) but **an HV-rated PANEL SWITCH with auxiliary LV poles rated 1 kV per pole and possibly 2 kV between poles** — **a different scarce part class, and one nobody in this project has yet searched.** It may be easier to source than a kV Form-C relay, or harder. **Unknown, and it must be searched at G1 before it is assumed benign** (MODE-13, O-10). **The honest fallback is real and should be priced alongside it: an HV link block or a re-plugged HV cable**, which needs no switch at all. **Net: the schedule risk moved off the module line and onto the HV passive/relay/switch line, which was already the harder one to source.** | Medium | Order long-lead parts at **G1, not at fab**. Freeze the HV resistor architecture around the one verified-stocked family. **Search the mode-switch part class at G1 and price the link-block fallback in parallel.** ~~Get an iseg quote~~ **— no longer needed, the modules are in hand.** |
| **R-8** | A **welded HV contact** violates invariant (a) with one mechanical fault. No contact-based topology can *prevent* this, only detect it — and the proposed self-test is currently unsound (see `COMBINER_STUDY.md` flaw F-2). ~~**⬛ G0-A4 CREATES A WORSE INSTANCE:** a welded or mis-positioned **MODE routing element** is the single fault that can put **both modules on the same node** while the interlock believes mode 2 is in force.~~ ⛔ **THAT INSTANCE IS DELETED BY G0-A5, not merely mitigated.** It had two ingredients: *the element is in the wrong position*, **and** *the interlock believes something different about that position*. With a physical switch the HV poles and the interlock's aux poles are **on the same armature**, so the second ingredient **cannot occur.** **What survives is the ordinary case this risk already covered**: a **welded HV pole on the mode switch** — the switch turns, the aux poles move, the interlock correctly re-derives, but one HV pole stays made. Same class as a welded polarity reed, same detection. **The "worse instance" characterisation is withdrawn.** | **Medium → High** (from the polarity relay alone), **not raised further by dual-mode.** | Fix the self-test (needs per-branch monitors and a reachable both-coils-off state) **and add the three performable mode-switch tests of S-3**: aux-lead-break timing, intermediate-position decode, runtime-change trip. **Q6 was NOT answered** — if the safety case ever demands *prevention* rather than detection, every candidate on the panel dies and the study reopens. |
| **R-9** | A single session cannot review its own schematic; the collapse in §0 increases dependence on the human GUI gate. **G0-A4 increases the review surface** (second output chain, mode element, mode-aware interlock truth table). | Medium | Phase-3 and Phase-5 human GUI reads are non-negotiable and are named explicitly in `PLAN.md`. The **mode-aware interlock truth table** is now a named item for the human read. |
| **R-10** | **Firmware is an attack surface on a device that can kill.** The reference board's vendored SCPI parser has an unbounded `msg_buffer` write reachable from the control port, and out-of-bounds array reads. ~~If network *control* is in scope, this is an RCE path to HV.~~ ⬛ **G0-A3 PUTS IT IN SCOPE: full write authority on the network, deliberately, with the risk stated.** The conditional is spent. **The hardware interlock, the hardware `VSET` clamp and the soft limits now carry the ENTIRE safety case** — a firmware defect is no longer *a* path to HV, it is *the* expected path. ~~Compounding it, **G0-A4 makes the MODE commandable over that same path**, and a mode command asserted against a physically-unmoved routing element is the forbidden state (MODE-03).~~ ⛔ **STRUCK BY G0-A5 — the mode is NOT commandable over any path. It is a physical switch, and the network cannot reach it** (MODE-04, MODE-12). **This is the one place where a G0 answer made the network write path LESS dangerous rather than more**, and it removed the worst thing on the remote attack surface: the ability to make the hardware's own safety input lie. **The rest of R-10 is unchanged and still binds** — setpoint and enable remain network-writable. | **Medium → High.** Accepted knowingly by the human; not re-litigable, but not free. | Do not vendor the reference parser. **Bounded parser, fuzz the command surface** — now mandatory scoped work, not a contingency. ~~network defaults to read-only telemetry with write authority behind a physical switch~~ **— STRUCK, overturned by G0-A3; do not quietly reinstate it.** Required instead: explicit **arm/disarm** (ARCH-35), **comms-loss watchdog failing to HV-OFF** (ARCH-36), enforced **soft limits** that error rather than clamp (ARCH-37), authentication/session management, and OTA security. |
| **R-11** | `docs/NUMBERS_PROBE.md`'s "FS" column is never defined as module Vnom vs output full scale. ~~Under one candidate topology, ±400 V out requires 800 V modules — a reader indexing by output FS under-sizes clearance by exactly 2×.~~ **G0 largely defuses this: the topology that made Vnom ≠ output FS (series-stack, 800 V modules for ±400 V out) is rejected by G0-A1, and G0-A2 fixes Vnom = 1000 V = output FS.** The ambiguity is now cosmetic rather than dangerous — **but fix the label anyway**, because a future reader will not know the aliasing was ever benign. | Low, and lowered by G0 | One-line fix at G1: label the column "module Vnom". |
| **R-12** | Board area. The recommended relays occupy ~37 cm² of HV real estate — the relays, not the HV modules, dominate the board. **⬛ G0-A4 ADDS HV AREA ON TOP OF THAT, AND NOBODY HAS RE-RUN THE ESTIMATE**: ~~a mode routing element,~~ a second SHV connector spaced for **2 kV** from the first, a second monitor divider string with its own guard ring, and a second bleed network. **⬛ G0-A5 moves the mode element OFF the board** — it is a **panel** switch (MODE-04) — **so the on-board area uplift is smaller than the A4 pass assumed. But it does not vanish; it MIGRATES**: the HV routing now leaves and re-enters the board through a **panel harness**, which adds board-side connectors and puts the 1 kV/2 kV clearance problem into the **enclosure and the wiring**, where `.kicad_dru` cannot see it. **HV clearance cannot be recovered by rerouting** — if the area does not fit, it is a G1 problem, not a Phase-4 one. | **Low → Medium.** | **Re-run the HV area estimate for dual-mode BEFORE placement begins** (`DECISIONS.md` LIB-19), **including where the mode-switch harness lands and whether any two conductors in it carry opposite polarities.** Confirm the enclosure at Q5 — **which the human did not answer** — before layout. |
| ~~**R-13**~~ | ⬛ ~~**NEW (G0-A4): THE MODE IS A SAFETY INPUT, AND ITS SENSE PATH IS A NEW SAFETY-CRITICAL SUBSYSTEM WITH NO PRIOR ART IN THIS PROJECT.** If mechanism (b) is chosen — a relay whose armature position feeds the interlock — then the sense contact, its wiring, its pull elements and its power-loss behaviour all become part of the safety case. Specific failures nobody has analysed yet: a sense contact wired to report the **coil command** rather than the armature; an open or shorted sense line; a sense path that loses its own supply while HV lives.~~ ⛔ **RETIRED BY G0-A5, ONE DAY AFTER IT WAS RAISED. Mechanism (a) was chosen: there is no mode relay, therefore no sense path, therefore no sense-path failure modes.** The "sense contact reporting the coil command rather than the armature" fault — the nastiest one on the list, because it is invisible in normal operation — **cannot exist when the interlock pole and the HV pole are the same piece of metal.** Retained struck so a future session sees what was avoided and does not re-introduce a mode relay thinking it is free. | ~~High~~ **RETIRED** | ✅ **Closed by `DECISIONS.md` MODE-04.** **Superseded by R-14, which is a smaller and better-bounded risk.** |
| **R-14** | ⬛ **NEW (G0-A5): the mode switch's CONTACT TIMING and its PROCUREMENT are what is left of R-13.** Two residues. **(i) Timing:** the LV aux poles must **BREAK BEFORE** the HV poles **MAKE** (MODE-15). If a switch with unspecified or wrong-order timing is fitted, a **unipolar → pseudo-bipolar** change performed while both modules are live routes both onto one node during the transit. **Bounded, and stated honestly rather than dramatised:** the modules are short-circuit protected at **≈0.75 mA**, so the outcome is a **current-limited polarity fight, not an energetic fault**, and at that current the contacts cannot sustain an arc. **(ii) Procurement:** a panel switch rated 1 kV/pole with aux poles is an unsearched part class (O-10, R-7). | **Medium** — bounded consequence, unbounded sourcing. | **Specify the timing margin at G1 and make it a switch-selection gate, not a preference** (MODE-15). **Scope the contact sequence on the actual part at Phase 7** (S-3 ii-a). **Price the HV link block / cable re-plug fallback in parallel** — it needs no timing spec at all, because there is no transit under power. If a non-conforming switch must be used, the weakening is carried by MODE-16 + MODE-17 (guard + runtime trip) and **must be recorded, not absorbed**. |

---

## 6. Out of scope

Detector/load design · the HV cable assembly beyond declaring `C_load ≤ 10 nF` **per output** as an
interface constraint · any claim about Phase 7 · mains-powered supply design (a bench brick feeds the
board) · series-stacking two modules for higher voltage (foreclosed until iseg publishes a GND-to-earth
rating, **and now doubly foreclosed by G0-A1's rejection of every stacking topology**) · **smooth
through-zero operation** (G0-A1: explicitly not required and explicitly not being built; a ~1 s
dead-band clamped to ground is the specified behaviour) · **module procurement** (G0-A2: the modules are
owned; the item code is spent).

**Changes to this list at G0:**

- ⛔ **REMOVED FROM "OUT OF SCOPE": two independent unipolar outputs.** Session 1 recorded the brief's
  *"explicitly not two independent unipolar outputs"*; **G0-A4 amends the brief and makes dual-mode a
  first-class requirement.** See §1.
- **`SIMPLE` integration:** session 1 wrote *"unless G0-4 says otherwise"*. **G0-A3 answered the comms
  question but did not mention SIMPLE**, so integration remains **out of scope** — and that is now a
  recorded non-answer, not a live conditional. If SIMPLE is wanted, it is a new request.
- **Newly IN scope, from G0-A3:** authentication, session management and OTA security for the network
  write path, and the bounded command parser and its fuzzing. These are **real, maintained work** that
  session 1's recommended read-only default was chosen to avoid, and the human took the other branch
  knowingly.
- **Newly IN scope, from G0-A4:** ~~the mode routing element and its position-sense path~~ **the mode
  SWITCH (a panel part) and its auxiliary LV poles** (G0-A5); a second output chain end-to-end
  (connector, bleed, monitor, guard ring); ~~the mode-change state transition~~ **the mode-change
  OPERATING PROCEDURE, its guard and its legend** (G0-A5 — there is no state transition); and panel
  mode indication, **which the switch itself provides**.
- ⛔ **Newly OUT of scope, from G0-A5 — and these are DELETIONS, not deferrals:** a **mode relay** and
  its coil rail · a **mode position-sense subsystem** and its failure analysis · a **`MODE` set command**
  on any interface · a **mode-change state-machine transition** with its own timeouts and TRIP rule ·
  the **`MODE_POS` vs `MODE_CMD` disagreement trip**. **Do not re-introduce any of these**; each was
  designed against a hazard that G0-A5 removed rather than mitigated.
