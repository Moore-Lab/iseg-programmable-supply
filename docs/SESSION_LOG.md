# SESSION_LOG

Append-only. Absolute dates. Sessions boot cold from files; nothing lives only in a conversation.

---

## Session 1 — 2026-07-23

**Phase:** 0 (incomplete remainder) + 1 (complete).
**Ends at:** GATE G0, awaiting human scope sign-off.
**Bootstrap:** `EE_PROJECT_BOOTSTRAP.md` v1.0 — this project's first field test.

### What was done

**Phase 1 studies (4).**
- `docs/PART_iseg_APS.md` — the authoritative part reference. Both PDF revisions re-read from
  primary; complete pin/spec/configuration tables; item-code decoder with all ten `Inom` fields
  decoded and checked; the mechanical drawing transcribed to explicit numbers in three coordinate
  frames; a design-consequences section; a 16-item "what the datasheet does NOT say" section; a
  ranked question list for iseg. Ships with two zero-arg acceptance checks in `tools/`.
- `docs/REFERENCE_BOARD_AUDIT.md` (677 lines) — the McGill PHYS 439 alpha-shield board audited end to
  end: schematic, PCB copper geometry, firmware, vendored SCPI parser, schematic PDF, designer's
  `.docx`. Corrects three of the brief's characterisations of that board.
- `docs/CONTROL_ARCHITECTURE.md` + `docs/studies/{control_arch_numbers,control_arch_divider}.py` —
  set path, monitor path, interlock, protocol, with re-runnable arithmetic.
- `docs/NUMBERS_PROBE.md` + `hardware/hvctl/numbers_probe.py` — 1630-line stdlib-only probe over
  seven areas (clearance, netclass rules, bleed/discharge/stored energy, monitor divider, power
  budget, `VSET` clamp, set-point resolution), parameterised over all five voltage classes and both
  families. 141 assertions, 141 pass, exit 0, byte-identical across two runs.

**Combiner study.** Five topologies analysed independently, then ranked by **three independent judge
sessions under three explicitly different lenses** (safety/failure-modes · electrical/through-zero ·
buildability/cost/risk), none seeing the others' work. Synthesised into `docs/COMBINER_STUDY.md`.

**Libraries (3 generators).** Symbol library, footprint library, 3D model — each with its own
executable acceptance checks and each mutation-tested.

**Adversarial verification.** Five load-bearing claims each attacked by 2–3 independent skeptic
sessions tasked with **refuting** rather than reviewing. Three survived, two were refuted.

**Synthesis (this agent).** Nine documents written: `SCOPE.md`, `DECISIONS.md`, `COMBINER_STUDY.md`,
`PLAN.md`, `INTERFACES.md`, `PIPELINE_LOG.md`, `STATUS.md`, `G0_QUESTIONS.md`, and this entry.

### What was verified, and by which instrument

| Claim | Instrument | Result |
|---|---|---|
| Pin map `1 +VIN · 2 VSET · 3 GND · 4 /ON · 5 VMON · 6 HV · 7 GND`, consistent symbol↔footprint | 3 skeptics: verbatim PDF text; **Figure 1's own top-view panel** re-rendered (an independent statement inside the same document); the 2019 v2.1 revision; three separate parsers (stdlib s-expression reader, KiCad's SVG plotter, `pcbnew.FootprintLoad()`); a third-party footprint from a built board | ✅ **SURVIVES 3/3** |
| Footprint geometry incl. the **+0.60 / +0.23 mm** body offset and its direction; not mirrored | 3 skeptics: independent recomputation (outward-from-centroid vs inward-from-body); **two independent pixel-metrology passes** agreeing to 0.02 mm; extension-line-to-feature tracing; signed-cross-product chirality check; `pcbnew` readback; 8/8 mutation test | ✅ **SURVIVES 3/3** |
| `VSET` internal 10 kΩ pull-up ⇒ open `VSET` commands full scale; output not internally limited above Vref | 3 skeptics: `Rset` formula algebra (three topology hypotheses coded, two diverge); native-resolution figure render; verbatim text in **both** revisions | ✅ **SURVIVES 3/3** |
| Clearance numbers correctly derived, worst case = 2× full scale | 3 skeptics, each re-deriving the full table independently | ❌ **REFUTED 3/3** — arithmetic correct, **premise wrong**: the "independent cross-check" is an algebraic tautology, both sources are the same web page, the IEC column is likely mis-transcribed, and the probe's own §6.1 shows a single `VSET` fault gives 132–200 % of Vnom against copper sized for 100 % |
| Phase 0 environment proof accurate; the throwaway board produced gerbers | 3 skeptics, whole-repo searches + generator greps | ❌ **REFUTED 3/3** — `docs/ENVIRONMENT.md` does not exist; **zero gerbers, zero drill files, no DRC, no render** exist anywhere; no Phase-0 generator contains the string `gerber`. The step was never implemented. **The Phase 0 gate is NOT met.** |
| 3D model lands at the correct position on a real board | `kicad-cli pcb export vrml` world-space re-measurement | ✅ 0.000 mm pin-to-pad error; all four case setbacks exact |
| Generators deterministic / stdlib-only | SHA-256 across process invocations; AST walk over imports | ✅ deterministic; stdlib-only **inferred from the import set, not demonstrated on a second interpreter** |
| Acceptance checks actually fire | 17 injected mutations across two generators | ✅ 17/17 caught with intended exit codes |

### What is unverified

- **Nothing has been measured on hardware, energised, or bench-verified.** Every electrical claim is
  a reading of vendor documentation or arithmetic over it.
- **No physical iseg module has ever been touched** — no caliper, no meter.
- **Not one MPN has been checked against a live distributor page since it was written down.** All
  carry `[unverified-MPN]` and must keep it until Phase 6. One agent recorded a distributor
  deep-link returning a confident, well-formatted spec report **for an entirely different product**.
- **No iseg quote, lead time, or MOQ** — the dominant BOM line in every candidate.
- **Four module parameters that set every timing and discharge figure are unmeasured and
  unpublished:** output capacitance, internal bleeder, set-input step response, turn-on time.
- **Clearance constants and touch-safety thresholds are `[recalled]`** with no primary source.
- **`NUMBERS_PROBE.md` has not been rewritten** to reflect its own refutation; `DECISIONS.md` NUM-01
  carries the correction.
- **The Phase-7 bench procedure is a DRAFT reviewed by nobody.**

### Decisions taken

Recorded in full in `docs/DECISIONS.md` (~120 rows, 7 sections). Headline:

- **Frozen:** the pin map · the footprint geometry including the asymmetric body · the land pattern
  (1.30 mm drill / 2.10 mm pad, with the reference board's numbers evaluated and rejected) · CAD
  identity and lib-table wiring · `+VIN` removal as the primary disable with `/ON` secondary ·
  `VSET` pull-down at the pin and a clamp implemented as the buffer's own reference rail ·
  ≤10 Ω drive impedance to `VSET` · duplicated safe-state pull elements as an ERC rule ·
  two-parallel-string bleeds and dividers · dump elements sized against 1.5×Inom · the pairwise
  HV rule must be a `.kicad_dru` rule because a netclass cannot express it.
- **Recommended, conditional:** `hv-relay-changeover` — **unanimous #1 across all three judge lenses
  at exactly 7/10 each**, with four mandatory corrections, conditional on Q1.
- **Eliminated:** `diode-or` (structurally non-functional — the idle leg's blocking diode is
  forward-biased in exactly the condition it exists to block; 0 mA of available load current), its
  carry-forward diode recommendation (struck — it would break the winner's structural bleed
  guarantee), `series-stack` Variant A (permanently), Variant B (unless invariant (a) is amended in
  writing **and** the load is capacitive at <10 µA), and `single-module-polarity-reversing-relay`.
- **~45 assumptions logged** as `assumed-pending-G0` rows, each with a stated default, so the project
  could proceed rather than stall.

### Pipeline log

`docs/PIPELINE_LOG.md` created — **26 deduplicated entries**, eight written as drop-in amendments to
`EE_PROJECT_BOOTSTRAP.md`. Four record independent convergence across 2–4 uncoordinated agents; those
are the most trustworthy. Twelve candidate entries were rejected by the litmus test as circuit facts
and moved to `DECISIONS.md`.

Highest-value entries: **PL-02** (round-trip every emitted KiCad text file through `kicad-cli` and
byte-compare — "it loads" is a weak gate, and it caught four wrong format conventions);
**PL-07** (datasheet figures carry engineering facts text extraction is structurally blind to — four
agents, and it changed conclusions every time); **PL-10** (facts inherited from a brief are
`[recalled]`, not `[verified]` — three agents, and one inherited constant was wrong in the permissive
direction); **PL-11** (how to handle a paywalled standard — including the failure mode where the
cross-check is an unfalsifiable tautology); **PL-14** (mutation-test your own acceptance check — two
agents, 17/17); **PL-26** (multi-lens adversarial review found 23 defects the analysts missed, four of
them present in all five studies).

Environment deltas from the bootstrap's stated stack, each logged: **PL-01** (no scipy — Part II
contradicts Part III), **PL-04** (schema is 20260306/20260206, not the stated 20250610 — and the demo
corpus is a *stale oracle* that produces false mismatches), **PL-05** (`kicad-cli` sub-command surface
is narrower than assumed), **PL-06** (FreeRouting absent and deliberately not used).

### Process notes

- One agent disclosed running a single read-only `git status --short` despite the no-git instruction.
  It mutated nothing and staged nothing. Recorded rather than omitted (`DECISIONS.md` PROC-08).
- A shared generator constant was observed changing on disk mid-session, edited by a concurrent
  agent. The end state is correct and consistent; the race is logged as PL-27.
- Two `__pycache__/` directories exist inside the repo tree and must be gitignored.

### Handoff state

**Ready for GATE G0.** `docs/G0_QUESTIONS.md` is the deliverable to the human: seven questions, each
with a recommended default and a stated consequence of proceeding on it.

The next session should, **before** and independently of G0: close the Phase 0 gate (gerbers **and**
drill, plus fill/DRC/render, plus write `docs/ENVIRONMENT.md`); attach the 3D model to the footprint
in its generator; gitignore `__pycache__/`.

It should **not** start Phase 2 (`board_spec.py`) until Q1 is answered — the golden netlist is a
function of the topology, and the topology is a function of Q1.

Four things need a human or a bench and should start in parallel with G0: obtain a primary copy of
the clearance standard; email iseg (reverse-voltage rating on the HV pin, GND/case isolation rating,
the current-monitor discrepancy); request an iseg quote with lead time and MOQ; bench-measure the
four unpublished module parameters and caliper one physical module.

**Nothing in this session claims the Phase 7 gate, and nothing in this session has been energised.**

---

## Session 2 — 2026-07-23

**Phase:** 0 (closed) + 1 (closed) + 2 (drafted).
**Ends at:** GATE G1, **not ready to sign**.
**Gate package:** `docs/G1_REVIEW.md`.

### What was done

**Phase 0 closed.** Gerber + drill export added, fill → DRC → render chain completed, and
`docs/ENVIRONMENT.md` written: 24 gerber layers + `.gbrjob` + `env_proof.drl`, all non-zero;
`fill_zones.py` 2 zones / 2178.23 mm²; `pcb drc` 0 violations / 0 unconnected; 3D render 1568 × 872
with 136 distinct colours `[verified-run]` `[verified-artifact]`. **The Phase 0 gate is MET.**

**G0 signed by the human.** A1–A5 frozen (see `PLAN.md`). **Q3, Q5 and Q6 were never answered**, and
the design proceeds on documented defaults — recorded everywhere it matters, not buried.

**`NUMBERS_PROBE.md` rewritten in the generator**, not patched: the session-1 refutation's seven
defects were addressed in `numbers_probe.py`, and the document is now **generated from the probe's
actual printed output** (PL-33). 74 assertions, 74 pass, exit 0, byte-identical across two runs,
8/8 mutations caught `[verified-run]`. The tautological "independent cross-check" was **DELETED with
no replacement invented**, and a **tripwire** now asserts that the suspected mis-transcribed IEC
column is still present, so a silent fix cannot orphan the flag (PL-35).

**Phase 2 drafted — four design documents and the golden netlist.**

- `docs/design/COMBINER_DESIGN.md` (~96 kB) — HV routing matrix, the `M`-node arrangement that
  splits a 2000 V stress into two 1000 V gaps, the mode-aware interlock, the cold-switch latches, a
  33-row single-fault analysis, the state machine and the power-up self-tests.
- `docs/design/SETPOINT_PATH.md` (~69 kB) — four clamp candidates evaluated, one adopted: the clamp
  is the buffer's own 2.500 V rail, so no component sits in the signal path.
- `docs/design/MONITOR_AND_BLEED.md` (~79 kB) — two independent monitor chains, the separate COLD
  string that breaks F-3's single-fault chain, and the load budget summed for the first time since
  G0.
- `docs/design/CONTROLLER_AND_POWER.md` (~131 kB) — ESP32-S3, three-converter power tree, comms,
  arm/watchdog, connectors.
- `hardware/hvctl/board_spec.py` — **the golden netlist**: 441 components, 321 nets, 10 netclasses,
  12 HV strings / 80 elements, 44 TIER-C parts, 24 reachable mechanical states, exit 0. It
  self-reports **9 assertions that are not structurally expressible** and **10 deviations,
  D-1…D-10**.
- `docs/PIN_MAPS.md` — generated from `board_spec.py` plus the symbol libraries; the human pin-map
  review surface.

**Adversarial verification — six claims, three independent skeptics each, every one tasked with
refuting rather than reviewing. All six were refuted. 18 reports, no coverage gap.**

**Synthesis (this agent).** `docs/G1_REVIEW.md` and `docs/BENCH_MEASUREMENTS.md` written;
`STATUS.md` and `PLAN.md` rewritten to post-G0 / pre-G1 reality; **correction banners added to all
four design documents, and D-7…D-10 added to `board_spec.py`**, so that no document in this repo
asserts a refuted claim without the correction adjacent to it. `PIN_MAPS.md` regenerated;
`board_spec.py` and `numbers_probe.py` both re-run at exit 0 afterwards.

### What was verified, and by which instrument

| Claim | Instrument | Result |
|---|---|---|
| The mode switch is a real, obtainable, adequately-rated part | 3 skeptics; **the manufacturer's own 63-page catalogue PDF fetched and text-extracted with PyMuPDF under PY_KICAD**; distributor listings; an NSF Controls wafer datasheet as a contrast case | ❌ **REFUTED 3/3.** No part is specified at all. The one MPN named (`D4C0212N`) is real and stocked but publishes **28 VDC / 115 VAC working** and **1,500 VAC dielectric strength to GROUND** — and **no contact-to-contact figure at any voltage**. §3.6's premise that the ceramic figure *"is much higher"* is **wrong**: it is published, and it is **lower** than the requirement. |
| The mode-aware interlock makes the forbidden state unreachable in hardware, in both modes, in every ESP32 state | 3 skeptics, each writing its **own probe that imports `board_spec` and calls the file's own `reachable_states()` / `_adjacency()`** | ❌ **REFUTED 3/3.** One welded HV reed reaches it — the document's own §7.5 and F-15 say so, and **§1.3's theorem contradicts them.** And `assert_a_no_shared_output_node()` filters out **every pseudo-bipolar state**, so the executable proof never examines the mode at risk. **The logic half survived every attack.** |
| The design is safe if a human moves the mode switch at the worst possible moment | 3 skeptics; the decay recomputed against the file's own numbers | ❌ **REFUTED 3/3.** §3.5 derives ≥0.2 s / ≥1.0 s and then meets it with **~100 ms** of `[recalled]` detent dwell — 2× to 19× short. With a **conforming** switch at the `C_load` limit, 100 ms leaves **~620–800 V** standing as the HV poles make. **Between-detents behaviour and the runtime-trip behaviour both survived.** |
| The `VSET` clamp makes commanding over-range impossible, and fails safe | 3 skeptics; **this repo's own `numbers_probe.py`**; datasheet p.7 re-extracted | ❌ **REFUTED 3/3.** The probe itself prints *"NO candidate makes over-voltage mathematically impossible."* The "+0.061 %" headline divides by a **nominal** Vref; at the datasheet's −1 % limit the same ceiling commands **+1.07 %**. One modelled fault reaches **2012 V — worse than no clamp at all.** **The Vref-pin attack failed: §2.3 had already dropped that candidate rather than inventing a pin.** |
| The independent monitors load acceptably, beat `VMON`, and are independent | 3 skeptics; the divider algebra recomputed; `board_spec.py`'s own string table read | ❌ **REFUTED 3/3.** The load sum omits the two 400 MΩ mode-switch stub bleeds (**12.40 %**, not 11.40 %) and **breaches the probe's own ≤15 % assertion** once the assumed internal bleeder is added. Accuracy is **~2×** with long-term drift included, and **20 V — worse than `VMON`** — without the `[ASSUMED]` 100× guard factor. Both offset legs share one reference; **one op-amp package drives both guard rings**; and one open element blinds the monitor **and** the OVP together. |
| `board_spec.py`'s assertions genuinely can fail; its pin numbering agrees with symbol and footprint | 3 skeptics, **three independent mutation harnesses**, 24 mutations applied to in-memory boards with caches cleared | ❌ **REFUTED 2/3.** The assertions **do** fire — 13/13 in-scope mutations caught, naming the exact state and mode. But **four escape routes** exist (D-7…D-10), **`board_spec.py` never opens a `.kicad_mod`**, and **11 named footprints do not exist**, including `K1`/`K2`'s. **Symbol↔spec pin agreement holds, both directions, confirmed by three independent parsers.** |

**Also established:** the component / net / TIER-C counts circulating in this session's briefs
(419 / 314 / 42) were **STALE**. The file reports **441 / 321 / 44** `[verified-run]`.

### What is unverified

- **Nothing has been measured, energised or built. No physical iseg module has been touched** — and
  **both modules are in hand.** `docs/BENCH_MEASUREMENTS.md` is the procedure; **M5 (caliper against
  our land pattern) needs no high voltage and takes twenty minutes.**
- **Eight parameters are MEASURABLE-NOW**: `VSET` step response · HV output capacitance (**two live
  documents disagree by 10×**) · internal bleeder · turn-on time from `+VIN` · the module's `VSET`
  pull-up tolerance (the fail-open criterion **breaks at 7.83 kΩ**) · divider `k_VCR` · the
  guard-ring improvement factor · **the physical module against our land pattern**.
- **Every clearance and touch-safety constant is `[unverified-primary]`.** There is currently **no
  evidence the clearance constants are the right constants.**
- **Not one MPN has been checked against a live distributor page.** The mode switch has **no MPN**;
  `U4` (the clamp) is **unselected**; the Pickering relays are **unpriced**; **no iseg quote, lead
  time or MOQ exists.**
- **44 TIER-C borrowed pinouts have never been checked against a datasheet** — including both HV
  relays, `K_S` (the single armature), the four `+VIN` load switches (the primary disable), all
  seven comparators and every interlock gate.
- **G0 Q3, Q5 and Q6 were never answered**; the design proceeds on documented defaults.
- **`CONTROLLER_AND_POWER.md` (131 kB) was never adversarially reviewed** — one agent's word.
- `docs/studies/combiner_design_numbers.py` is **arithmetic, not verification**, and is **not
  mutation-tested**, yet `COMBINER_DESIGN.md` quotes it throughout.

### Decisions taken

- **Correction banners, not deletions.** Every refuted claim is left in place with the correction
  adjacent, because deleting the claim would erase the evidence that the verification phase worked.
- **`board_spec.py` deviations reported, not patched** (D-1…D-10) — including two that **change the
  netlist** (`D-1` bleed topology and value, `D-4` the ESP32 GPIO remap) and are therefore **G1
  decisions, not a session's**.
- **`CONTROLLER_AND_POWER.md` §9.2 marked SUPERSEDED** rather than rewritten: it specifies a
  2-position, 4-pole switch against the built 3-position, 7-pole part, and a purchaser following it
  would **delete the SAFE detent** the timing argument depends on.
- **`MONITOR_AND_BLEED.md` §5.4's 2-of-2 COLD AND was NOT built** (D-2), because implementing it
  would silently break the **frozen** assertion SA-8. Carried forward as open, with the unmitigated
  residual stated rather than absorbed.

### Process notes

- An agent that had already written `board_spec.py` (~134 kB, runs clean, exit 0) **failed on its
  StructuredOutput return — five retries, no valid output — which aborted the whole workflow.** The
  work was complete and correct; only the reporting channel died. Logged as **PL-36**, and it
  reinforces **PL-29** (inventory the filesystem before concluding work was lost).
- `docs/ENVIRONMENT.md` initially recorded the schematic schema as **20250610**, read from KiCad's
  own shipped demo files. **The demos are KiCad-written but STALE — a stale oracle.** The installed
  eeschema writes **20260306**, provable by copying a demo and running
  `kicad-cli sch upgrade --force`. **PL-04 logged exactly this lesson in session 1, and the mistake
  was made anyway — in the very document PL-04's own bootstrap amendment told us to write.** Logged
  as a **recurrence on PL-04** rather than a duplicate, plus **PL-37** on the general failure of a
  logged lesson to reach the artifact that consumes it.

### Handoff state

**Ready for GATE G1 REVIEW, not for G1 SIGNATURE.** `docs/G1_REVIEW.md` is the deliverable: the
frozen-values table with per-row evidence and per-row "what this instrument cannot see"; the netlist
intent in **twelve reviewable blocks** rather than a dump of 321 nets; the pin-map review procedure
with all **44 TIER-C** rows called out explicitly; **eighteen** "what would make this wrong?"
questions; an explicit statement of what signing does **not** freeze; and a **partial-signature
block**, because partial signature is the expected outcome.

The next session should: put `G1_REVIEW.md` in front of the human; get **G0 Q6** answered (it can
kill the topology); get the **mode-element decision**; **repair the four assertion escape routes
before G1 closes `board_spec.py` behind a gate**; and get the bench afternoon done.

**Nothing in this session claims the Phase 7 gate, nothing has been energised, and every one of the
six claims put to adversarial verification was refuted.**
