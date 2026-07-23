# PLAN — from here to fab

Mapped onto `EE_PROJECT_BOOTSTRAP.md` v1.0 Phases 0–7, with its gates named. Collapsed machinery is
declared in `SCOPE.md` §0 — **one session runs both lanes; every gate is retained.**

**Current position: G0 SIGNED. Phase 2 drafted. Standing at GATE G1 — and G1 is not ready to sign
(`docs/STATUS.md` §1, `docs/G1_REVIEW.md` §0).**

Legend: **[G]** = a gate. **Human-only** gates cannot be closed by any session.

---

## Phase 0 — Environment proof · ✅ **CLOSED**

*Bootstrap gate: "the throwaway board produces gerbers."* **MET.** 24 gerber layer files + `.gbrjob`
+ `env_proof.drl`, all non-zero, after `fill_zones.py` (2 zones, 2178.23 mm²) and `pcb drc`
(**0 violations, 0 unconnected**) `[verified-run]`. 3D render 1568 × 872, 136 distinct colours.
`docs/ENVIRONMENT.md` exists.

**Standing environment facts** (do not re-derive them — `docs/ENVIRONMENT.md`):
PY_KICAD 3.11.5 · pcbnew / `kicad-cli` 10.0.3 · fitz + PIL + numpy present · **no scipy** ·
schematic schema **20260306**, board/footprint **20260206** · **the shipped demos are a STALE
ORACLE at 20250610–20260101** · `kicad-cli pcb drc` **exits 0 on violations** unless
`--exit-code-violations` is passed · FreeRouting absent and not used (and needs Java 25 where `PATH`
java is Java 8).

---

## Phase 1 — Scope and frozen numbers · ✅ **done**

`SCOPE.md`, `DECISIONS.md`, `COMBINER_STUDY.md`, `INTERFACES.md`, `PART_iseg_APS.md`,
`CONTROL_ARCHITECTURE.md`, `REFERENCE_BOARD_AUDIT.md`, five topology studies, three judge rankings.
`NUMBERS_PROBE.md` rewritten and now **generated from the probe's printed output** (PL-33) —
74 assertions, 74 pass, exit 0, byte-identical across runs, 8/8 mutations caught.

### **[G] GATE G0 — human scope sign-off · ✅ SIGNED 2026-07-23**

**Frozen: A1** set-and-hold with polarity changeover, no through-zero, ~1 s dead band clamped to
ground, **HV relay changeover** (diode-OR / series-stack / single-module-reversing REJECTED) ·
**A2** the human owns both `AP010504P05` and `AP010504N05` · **A3** serial **and** network, **both
write-authoritative**, over a recommended read-only default ⇒ *"the hardware interlock, hardware
`VSET` clamp and soft limits carry the entire safety case"* · **A4** dual mode; in unipolar ±1 kV
coexist as a **normal** steady state, so **2 kV is the binding normal case** · **A5** mode selection
is a **PHYSICAL SWITCH**, no mode relay, one armature, powered-down cables-off mode change.

> ⛔ **Q3, Q5 and Q6 were NEVER ANSWERED and the design is proceeding on documented defaults.**
> **Q3** output spec (max load current, load capacitance, required ripple) → proceeding on a
> **declared `C_load ≤ 10 nF` / ≤10 m constraint that nothing physically enforces**.
> **Q5** safety envelope → proceeding on `[recalled]` 60 V / 5 s / 350 mJ / 50 µC.
> **Q6** weld: detection vs prevention → **the design DETECTS and CANNOT PREVENT.** If prevention is
> ever required, **this topology dies and so does every other candidate** (TOPO-10).
> **Q6 must be answered before G1, in writing.**

---

## Phase 2 — Golden netlist as code, libraries, pin maps · ⚠ **DRAFTED, NOT REVIEWED**

*The highest-consequence, lowest-feedback work in the project (bootstrap §II).*

### 2.1 Delivered

| Artifact | State |
|---|---|
| `hardware/hvctl/board_spec.py` | **441 components / 321 nets / 10 netclasses / 12 HV strings, 80 elements / 44 TIER-C.** Exit 0. Self-reports **9 non-structurally-expressible assertions** and deviations **D-1…D-10**. |
| `docs/design/COMBINER_DESIGN.md` | routing + mode-aware interlock — **carries correction banner C-1…C-5** |
| `docs/design/SETPOINT_PATH.md` | `VSET` clamp — **carries banner S-1…S-7** |
| `docs/design/MONITOR_AND_BLEED.md` | monitors + discharge — **carries banner M-1…M-4** |
| `docs/design/CONTROLLER_AND_POWER.md` | ESP32 / power / comms / connectors — **§9.2 SUPERSEDED**; never adversarially reviewed |
| `docs/PIN_MAPS.md` | **generated** from `board_spec.py` + the symbol libs; the human review surface |
| `docs/G1_REVIEW.md` · `docs/BENCH_MEASUREMENTS.md` | **new — the gate package and the bench procedure** |

### 2.2 Carried remainder — **must clear before G1 closes**

Ordered by consequence. Full detail in `G1_REVIEW.md` §7.

| # | Task | Owner | Why it cannot wait |
|---|---|---|---|
| **2.2a** | **Answer G0 Q6 — weld detection or prevention.** | human | If prevention, the topology reopens and Phase 2 is void. |
| **2.2b** | **Decide the mode element.** Adopt the §3.7 **link block** as baseline, or fund a search for a switch with a **published contact-to-contact DC working ≥1000 V**. **No part is currently specified**, and the one MPN named is rated **28 V DC** (`STATUS.md` §1.1). | human | It is the armature the invariant rests on. |
| **2.2c** | **Obtain a primary copy of IPC-2221B Table 6-1 and IEC 60664-1 / 62368-1** and re-derive `C_HV`, `C_HV_PAIR` and the touch thresholds. | human | A wrong constant becomes a DRC rule and is **undiscoverable after fab**. It also selects the fab tier. **Highest project risk.** |
| **2.2d** | **Bench-measure five things on the modules in hand** — `docs/BENCH_MEASUREMENTS.md`. **M5 (caliper vs our land pattern) needs no HV and takes 20 min.** | human | Eight numbers are MEASURABLE-NOW; two live documents disagree on `C_module` by **10×**. |
| **2.2e** | **Repair the four assertion escape routes** (D-7…D-10): assertion (a) never evaluates pseudo-bipolar; `assert_a_mode_origin()`'s three bypasses; `hv_energisable_nets()`'s hand-list; monitor-A-vs-B never compared. | session | **After G1, changing `board_spec.py` requires a gate.** Do it before. |
| **2.2f** | **Commission the 11 missing footprints** (incl. `K1`/`K2`) and add a **symbol↔footprint pad-set cross-check** — `board_spec.py` never opens a `.kicad_mod`. | session | layout cannot start without them |
| **2.2g** | **Check all 44 TIER-C borrowed pinouts against real datasheets** (`G1_REVIEW.md` §4.3). | human | a wrong pin map produces a self-consistently wrong board |
| **2.2h** | **Adjudicate D-1 (bleed 20 MΩ-on-NC vs 40 MΩ-upstream) and D-4 (ESP32 GPIO remap).** Both **change the netlist**. | human | the netlist |
| **2.2i** | **Fix the design documents whose body text still asserts a refuted claim** — banners record the corrections; the bodies still need editing. | session | nobody should read a refuted claim as live |
| **2.2j** | **Promote `docs/studies/combiner_design_numbers.py` into `hardware/hvctl/`** with an acceptance check and a mutation test. It is arithmetic with no independent source of truth and **is not mutation-tested**, yet `COMBINER_DESIGN.md` quotes it throughout. | session | freezing its outputs |
| **2.2k** | **One email to iseg**: reverse-voltage rating on pin 6 (PART-27) · GND/case isolation rating · the current-monitor discrepancy (PART-20). | human | Q1 decides whether an OFF module tolerates the F-31 magnetic fault |
| **2.2l** | **One iseg quote**: class × polarity × lead time × MOQ. | human | dominant BOM line; the item code makes class **and** polarity irreversible at order time |
| **2.2m** | **Resolve NUM-18 / ARCH-14** — conformal coating assumed absent for clearance, mandated present for divider leakage. Two more guard-ringed regions were added this session. | human | before layout |
| **2.2n** | **Adversarially review `CONTROLLER_AND_POWER.md`** — 131 kB, one agent's word, never challenged. | session | it carries the power tree and the comms surface |

### **[G] GATE G1 — values/interface freeze + human netlist-intent review + human pin-map review · HUMAN-ONLY**

**Package: `docs/G1_REVIEW.md`.** *After G1, changing `board_spec.py` requires a gate.*
Also gated here: **2.2a–2.2n closed**, and **long-lead parts ordered now, not at fab** (R-7 — relays
unpriced, ~60 HV passives 0-stock/obsolete/13-week, the mode element unsourced).

> 🔴 **G1 IS NOT READY.** All six claims put to adversarial verification were refuted, including the
> **interlock** and the **`VSET` clamp** — the two elements G0-A3 made load-bearing for the entire
> safety case. **Partial signature is the expected outcome:** §1 (frozen values) and §3 (netlist
> intent) of the package are reviewable now.

---

## Phase 3 — Schematic generation

Generator turns `board_spec.py` into human-auditable `.kicad_sch`. Built-in gates **in order**:

1. diagonal-wire rejection
2. **pre-flight connectivity** — union-find over drawn geometry vs the golden netlist, run *before*
   writing files (a wrong netlist must never reach disk)
3. write
4. **legibility gate** — run *after* writing, so a cosmetic failure can still be rendered

Then external gates: ERC (errors-only, `erc_exclusions` confirmed empty, `pin_not_connected` at
error) → **netcmp** (pin-exact, both directions) → hierarchy-path integrity.

**Domain safety assertions promoted from review-only into build failure** (the R-5 pattern) — most
are already in `board_spec.py`; these are the ones it declares **not structurally expressible** and
which must therefore become **generator invariants, BOM properties or bench tests**:

| Assertion | Retires | Where it must live |
|---|---|---|
| Every `/ON` net has ≥2 parallel pull-ups to that module's **own** `+VIN`, within 5 mm of pin 4 | ARCH-17/18, F-19 | placement invariant |
| **SA-9 placement** — duplicated pull elements ≥5 mm apart | one solder defect taking both | placement invariant |
| **Graded string spacing** — each HV sub-string placed **collinearly in electrical order** | the `HV_SENSE` trap: a per-net 7.5 mm clearance would stretch the string ~10× and multiply the leakage area that dominates the error budget. **DRC has no "adjacent in string" predicate, and a pattern rule is UNSAFE** (both ends of a string match the same pattern and are 800 V apart) | generator invariant |
| **HCT, not HC**, on every input reachable from the ESP32 | an HC part at Vcc = 5 V wants `V_IH` = 3.5 V; a 3.3 V output does not meet it — **it works at room temperature and fails at a corner** | **BOM property** |
| **Push-pull comparators only, never open-drain** | an open-drain failure pulls up to a **false COLD = 1** | **BOM property** |
| **Relay coil polarity** — the `/5D` suffix means an internal coil diode | reversed coil ⇒ dead relay or shorted driver | **BOM + footprint** |
| **`K1`/`K2` mounted with long axes ORTHOGONAL** | reed sensitivity is strongly axial (F-4, R-6). **Free at layout, impossible to add later.** | placement invariant |
| **Weld detection** | F-15/TOPO-10 — the topology's admitted unremovable weakness | **bench test** (§9.4 self-tests) |
| **Discharge TIME** | an open bleed is silently undetectable (NUM-09) | **bench test** — the commanded-dump τ self-test (NUM-10) |
| **SA-12 dump sizing** | — | BOM, if the dump is ever fitted |
| No net is in both an `HV_*` netclass and a non-HV one | clearance-rule evasion | already asserted |
| Both GND pins (3, 7) of each module route **independently** to the pour | PART-16 | already asserted |
| Nothing HV-relevant on an ESP32 strapping pin (GPIO0/3/45/46) or USB (19/20) | boot-time GPIO hazard | already asserted |

**[G] Phase 3 gate — HUMAN-ONLY:** a human reads the schematic PDF **and opens the project in the
KiCad GUI**. Loop under Principle 13 (retire the class, not the defect) until signed. Batch fixes per
round (Principle 15); re-run the **electrical** gate after every cosmetic change.

---

## Phase 4 — Layout

No tiler (`SCOPE.md` §0). No autorouting of HV.

Placement order: SHV jacks + power entry pinned by the enclosure → HV modules → combiner → HV
dividers and bleed strings → LV control → MCU. **HV kept on ONE layer** (NUM-04: a `.kicad_dru`
clearance constraint is per-layer 2-D and cannot express top-vs-bottom, where the separation is
1.6 mm of dielectric).

**The HV area floor is ~37 cm²** and it is a floor, not an estimate — ~64–80 HV passive elements
drive it. **Re-run the area model before placement.**

Pre-route gate: courtyard/edge DRC + a **3D render** (catches connectors facing inward faster than
reading coordinates). Zones filled in a **separate process** (in-process `ZONE_FILLER.Fill()`
segfaults at exit 139 on a real board — PL-30).

**[G] Phase 4 gates** — all closeable by a session except where noted:

| Gate | Retires |
|---|---|
| DRC 0/0 — **with `--exit-code-violations`**, or it exits 0 on violations | geometric violations, and the exit-code trap |
| **Netclass-really-applied — MEASURE THE COPPER**, not "DRC passed" | bootstrap §V.3: a flattened `.kicad_pro` makes DRC pass **vacuously** |
| The four `.kicad_dru` pairwise HV rules verified by **measuring an actual gap** — `HV_POS`↔`HV_NEG`, `HV_OUT_A`↔`HV_OUT_B`, and the two NEW ones `HV_M`↔`HV_OUT_B`, `HV_X`↔`HV_OUT_A` | NUM-03. **Ruling only the first two leaves the mode-switch wiring silently spaced for 7.5 mm.** |
| Pad-net parity vs the exported netlist (own tool — `--schematic-parity` does **not** compare pad nets) | the class `kicad-cli` is blind to |
| Footprint↔symbol path bijection · census counts | UUID linkage; silently dropped parts |
| Guard ring at tap potential, **driven from the buffer output**, present on **both** monitor chains | ARCH-14 surface leakage — **without it the monitor is worse than `VMON`** |
| `iseg_APS_THT.kicad_mod`'s **5.00 mm per-pad clearance override on pad 6** removed — it silently replaces the 7.5 mm netclass value | fix **the generator**, not the artifact |
| 3D render both sides, inspected | wrong/absent 3D model (fails **silently**); mechanical nonsense |

---

## Phase 5 — Review artifacts

Schematic PDF (`sch export pdf`), mm-addressed zoomed crops of every dense region (the HV combiner,
the divider strings, the module pin fields, the `/ON` and `VSET` pull networks, **the mode-switch
pole ordering `S1–S3–S2`**), 3D renders both sides.

**[G] Phase 5 gate — HUMAN-ONLY:** *a human opens the project in the KiCad GUI and reads it.*
The GUI, not a render — it is the only instrument that sees `.kicad_pro`-scoped defects, GUI-strict
connectivity, legibility and mechanical sense (bootstrap §V.6).

---

## Phase 6 — Fab package

Gerbers + drill · fab BOM (`Comment,Designator,Footprint,<fab> Part #`) and CPL — **fitted SMD
only** — plus a hand-solder BOM (the HV modules are `exclude_from_pos_files`, LIB-06) · purchasing
doc with spares (`ceil(per_board × boards × 1.2)` for hand-soldered).

**Every MPN re-verified against a live distributor page.** Not optional and not partial. Precedents
earned by this project: a distributor deep-link returned a confident, well-formatted spec report
**for an entirely different product** (PL-06); a recalled MPN **did not exist** from the named
manufacturer; one part was stamped **Not For New Designs**; and **0-stock / obsolete / 13-week-lead
results on most HV passives**.

### **[G] GATE — fab commit · HUMAN-ONLY**

Pre-fab checklist (bootstrap §V.7) **plus four additions this project earned**:

- DRC 0/0 (`--exit-code-violations`) · ERC 0 errors (exclusions confirmed empty) · pad-net parity +
  path bijection · netclass-applied **measured on copper** · zones filled · census counts · BOM/CPL
  consistency (fitted-SMD count = CPL rows) · 3D render inspected both sides · polarized-part
  rotation eyeballed in the fab's own parts preview · **every MPN re-verified live** ·
  outline/slots within fab capability · **a human has opened the project in the GUI and read it**
- **+ every standards-derived constant traced to a PRIMARY document** (NUM-01, NUM-15, NUM-16)
- **+ the module parameters have been MEASURED** (`docs/BENCH_MEASUREMENTS.md` M1–M5)
- **+ every TIER-C borrowed pinout confirmed against a datasheet**, and every named footprint
  confirmed to exist
- **+ `PIPELINE_LOG.md` harvested into proposed bootstrap v1.1 edits** (bootstrap Part 0)

---

## Phase 7 — Bench acceptance · **HUMAN-ONLY, no session ever claims this gate**

Written energization procedure (draft in `NUMBERS_PROBE.md` Part B; **reviewed by nobody**, and two
of its own pre-day items are the unverified standards constants). **`docs/BENCH_MEASUREMENTS.md`
Part 0 is the HV-safety section that draft lacks and should be folded into it.**

| Test | Criterion | Notes |
|---|---|---|
| Commanded bipolar sweep from the ESP32 over the chosen interface | S-2 | |
| **Attempt to command both-enabled and observe hardware refusal** — **in BOTH modes** | S-3 | Reading the firmware is not the test. **Note assertion (a) never checked pseudo-bipolar, so this bench test is the only instrument that covers it.** |
| Power-up weld/stuck-contact self-test executes and passes | S-3 | Requires C-1 (both-coils-off reachable) and C-2 (per-branch monitors). **The self-test's own precondition must be verified first** — F-20: a self-test whose precondition is unverified is no self-test. |
| Readback vs DMM, both polarities **and both outputs separately** | S-4 | **Per-output** calibration (F-20). `OUT_A` and `OUT_B` are **not** interchangeable — the NEG path carries `R_M1` and drops 15.0 V vs 7.5 V. |
| Discharge on disable, **board unpowered**, <60 V within 5 s, **and with one bleed string deliberately open** | S-5 | Threshold is `[recalled]` — confirm first |
| Commanded-dump self-test measures τ and detects a deliberately-open bleed string | NUM-10 | turns invariant (b) into an executable check |
| Polarity handoff with the independent monitor confirming **SIGN** | ARCH-10 | `VMON` cannot do this — it has no sign information |
| **Mode change performed at the worst moment, powered down and cables off**, per MODE-17 | new | the residual protection here is **procedural** — `STATUS.md` §1.3 |
| **`VSET` clamp bench verification** — command over-range and measure the ceiling | S-8 | the clamp is a **primary safety element** whose over-range figure is now restated at **+1.07 %** |

---

## Firmware and host lanes

Run under the **generic software rules**, not the CAD gates. Start after G1 (the protocol surface is
frozen in `INTERFACES.md` §3). Non-negotiable, from `DECISIONS.md`:

- Bounded command parser; **do not vendor the reference SCPI parser** (REF-07 — an unbounded write
  into the object's last member, reachable from the control port).
- **`GPIO_HB` toggled ONLY from the main loop** — never LEDC, RMT, a hardware timer or an ISR; a
  peripheral free-runs straight through the hang the pump exists to detect (ARCH-20/C-3). Windowed
  watchdog, faulting on kicks that are **too fast** as well as too slow.
- **The mode is READ-ONLY, always** (G0-A5, MODE-12). `MODE_CMD` does not exist. **Firmware must not
  cache the mode** — re-read within 10 ms.
- `MEASure:VOLTage?` returns the **independent** monitor; the module readback must be asked for by
  name (ARCH-22).
- **No `DISCHARGE → CHANGEOVER` timeout fall-through** — trip and tell a human (ARCH-24). This is the
  one transition that must never fall through.
- In pseudo-bipolar, output B's commands are **rejected with an error**, never silently ignored
  (MODE-12, REF-05 anti-pattern).
- **Per-output** calibration tables (F-20), keyed to **module serial number** (the Vref bench
  calibration is per-module; replacing a module without recalibrating reintroduces ±10 V).
- Soft limits as a **named safety element** (ARCH-37) — and note G0-A3 put both transports inside the
  untrusted boundary, so soft limits are the *last* software layer, not the first.
- **The 98 % code clamp is currently the only thing bounding the output to ≤ Vnom** (`STATUS.md`
  §1.4). Treat it accordingly.

---

## Defect-class retirement summary

Which gate is the *last* place each class can be caught.

| Defect class | Retired by | Phase |
|---|---|---|
| Wrong module pin map | dated-citation pin maps + 3 skeptic passes + **caliper on a physical part** | 2 / G1 / bench |
| **Wrong TIER-C borrowed pinout** | **a human with a datasheet, 44 rows** | **G1 — nothing else can see it** |
| Wrong footprint geometry | independent recomputation + pixel metrology + mutation test + **M5 caliper / drilled coupon** | 2 / bench |
| **Named footprint does not exist** | commission it + symbol↔footprint pad-set cross-check | **2.2f** |
| Wrong netlist intent | golden netlist as code + **human netlist-intent review** (`G1_REVIEW.md` §3) | 2 / G1 |
| **An assertion with an escape route** | **mutation-test the checker itself, adversarially** | **every phase — this is how D-7…D-10 were found** |
| Netlist ≠ schematic | pre-flight union-find, before writing | 3 |
| Schematic unreviewable | legibility gate + human PDF read | 3 |
| eeschema connectivity silently broken by a netclass | 17-field assertion + GUI open | 2 / 5 |
| Clearance rule wrong | **primary standard read by a human** | **G1 — still open** |
| Clearance rule not applied | measure the copper; verify all **four** pairwise gaps | 4 |
| Board ≠ schematic | pad-net parity + path bijection | 4 |
| Wrong/absent 3D model | render and **count what you expect to see** | 4 |
| Unsafe default state (`/ON` open ⇒ ON, `VSET` open ⇒ full scale) | duplicated pulls + domain assertions + **bench** | 3 / 7 |
| Both-enabled reachable | domain assertions **(pseudo-bipolar currently unchecked — 2.2e)** + Phase-7 attempt-and-refuse | 3 / 7 |
| **Welded HV reed** | ⛔ **detection only** — power-up self-test + continuous branch monitors. **Not preventable by any candidate topology. G0 Q6 unanswered.** | 7 |
| Bleed absent or open | two parallel strings + commanded-dump τ self-test | 4 / 7 |
| Monitor not actually independent / not actually better | ⚠ **currently fails both** — see `STATUS.md` §1.5 | G1 / 7 |
| Obsolete or fictional MPN | live distributor re-verification | 6 |
| A number resting on an unmeasured module parameter | **`docs/BENCH_MEASUREMENTS.md`** | before 6 |
| **A check that has never failed** | mutation-test every acceptance check | every phase |
