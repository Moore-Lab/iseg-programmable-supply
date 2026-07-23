# EE Project Bootstrap — v1.0

**What this file is.** Standing instructions for setting up and running a Claude Code workspace for end-to-end **circuit-board development** — from concept to fabrication-ready outputs — with minimal human intervention. You prepend this file to a **project brief** (the specific board, its requirements, its success criteria). This file supplies *how*; the brief supplies *what*.

**Lineage.** This is the board specialization of the generic `AI_PROJECT_BOOTSTRAP.md`, whose skeleton it incorporates (you do not need both). Its domain content was harvested from the session debriefs of two completed board projects — a 12-channel Cremat SiPM preamp/shaper (`twelve-channel` lane) and `ramp_amp_proto` (`schematic` lane). Where both projects independently converged on a rule, it is marked **[convergent]** — treat those as the most trustworthy content in this file.

**Companion files.** Place the two debriefs at `docs/playbook/` alongside this file:
`EE_DEBRIEF_twelve-channel.md` · `EE_DEBRIEF_schematic_lane.md`.
They are the **exemplar corpus**: full source for the canonical tools (§IV), worked examples, and the long-form version of every gotcha here. This file tells you what is true; the debriefs show it.

---

## Part 0 — The bootstrap is itself under development

Read this before the engineering parts, because it is a standing task in every project run under this file.

We are developing two things at once: **the board**, and **this bootstrap**. The end goal is a bootloader that enables complete development from nothing but a high-level brief and the design decisions the human makes at gates. Every project run is also a test of the bootstrap, and every novel *development-pipeline* problem you solve is material for the next revision.

**The pipeline log.** Maintain `docs/PIPELINE_LOG.md`, append-only, any session writes. When you hit a problem this bootstrap did not cover, covered wrongly, or made harder — and you solve it — log it in the same session:

```
## PL-<n> — <one-line title>
date / session:
trigger:      what broke or was missing in the PROCESS (not the circuit)
resolution:   what was done, exactly — commands, workaround, new tool
bootstrap Δ:  the proposed amendment, written as a drop-in edit to this file
scope:        G | C:<class> | P
status:       logged        (orchestrator sets → adopted-v<next> at harvest)
```

**What qualifies.** The litmus test: *would this entry have helped on a completely different board — or a different domain entirely?* If yes, it is a pipeline lesson and belongs here. If it is a fact about this circuit (a part choice, a topology decision, a measured value), it belongs in `docs/DECISIONS.md` instead. Examples of pipeline lessons: a vendor tool's blind spot, a coordination failure between sessions, a check that passed while the artifact was broken, a rendering/review friction, an environment trap. Examples of things that are **not**: "we chose the 2 kV module", "the combiner needs a bleed resistor".

**Log and continue.** Never block engineering work on bootstrap philosophy. Solve the problem, log it, keep moving. The log entry is five minutes; the harvest happens later.

**The harvest gate.** At project end (or at the fab-commit gate, whichever comes first), the orchestrator compiles all `logged` entries into a proposed revision block — the concrete edits to this file — and hands it to the human. The human feeds it to the chat session that maintains this file, which emits the next version. This file carries its version in the title; the number of pipeline-log entries per project is the metric that should fall toward zero as the bootstrap converges.

**Evidence discipline in working sessions.** Both debriefs independently recommended promoting their own debrief protocol into live work **[convergent]**: when you claim something is verified, tag it. `[verified-run]` = you executed it this session and it behaved as stated. `[verified-artifact]` = the output exists on disk and you inspected it. `[recalled]` = from context, unverified. "Verified clean" meaning "a command exited 0" cost real trust in both projects; say which instrument said clean, and what that instrument cannot see.

---

## Part I — Operating principles

The generic eight, compressed (they still bind): **(1)** spec before code; **(2)** coordination is filesystem/git-mediated — sessions boot cold from files; **(3)** single source of truth per fact; **(4)** definition of done is executable; **(5)** autonomous within loops, gated at the edges; **(6)** right-size the machinery; **(7)** ask blocking unknowns once in a batch, log assumptions in `DECISIONS.md` and proceed; **(8)** no single turn is load-bearing — emit whole files, resume from committed state.

The board principles, learned the expensive way:

9. **Fabrication is the irreversible act.** Final acceptance is physical: real money, real weeks, and a wrong board is scrap. Order every gate so confidence is bought cheaply upstream; the gates that matter most (netlist intent, pin maps, schematic audit) sit *before* any board file exists.

10. **Generated CAD files are build artifacts. Never hand-edit them.** **[convergent]** Every defect — electrical or cosmetic — is fixed in the generator and regenerated. Commit generator and artifact together so every commit is a self-consistent pair. Hand-editing a generated file forks the truth and the next regeneration destroys the fork.

11. **Every check must declare what it cannot see.** **[convergent]** The worst failure in both projects was not a broken tool but a suite of green checks structurally blind to the defect. Before quoting a check as evidence, ask *what class of defect can this never see?* The vendor's OK is not proof: where `kicad-cli` is known lenient, write the stricter check yourself.

12. **The human at the GUI is a different instrument, not a slower one.** **[convergent]** It sees project-file-scoped defects, GUI-strict connectivity, legibility, and mechanical sense — classes no headless check reaches. When the human contradicts your green checks, assume they are right and ask which of your checks cannot see what they see. Drive the human like an instrument: "open this file, click this stub, tell me the net name" — not "please review".

13. **Retire defect classes, not defects.** **[convergent]** When a reviewer reports a defect, the deliverable is not the fix — it is a check that fails on the whole class, plus the fix, and the check stays. This single rule is the difference between six review rounds and two. If a class genuinely cannot be checked, say so explicitly and record why.

14. **Checks calibrate against machine-readable ground truth, and compare against an independent source of truth.** A checker calibrated by eyeballing a render, or comparing a generator's output against the generator's own assumptions, launders defects as verified — worse than no checker. Text metrics come from the SVG's own attributes; connectivity compares against the golden netlist; netclass application is proven by measuring the copper.

15. **Batch changes per review round.** Regeneration is seconds; a human review is the expensive round-trip. Accumulate fixes, regenerate once, request one review. Never ping per tweak. And re-run the **electrical** gate after every cosmetic change — both projects shipped shorts from purely cosmetic edits that only the gate caught.

---

## Part II — Phases and gates

A board project's pipeline, merged from both debriefs. Phases 2–5 are **loops with a human in them** — that is the plan, not rework. Firmware/host-software lanes inside a board project (e.g. an MCU controller) follow the generic software rules; this part governs the CAD lanes.

**Phase 0 — Environment proof.** Before any design: prove the toolchain end-to-end on a throwaway two-resistor board. Generate schematic → ERC → netlist → generate PCB → fill zones → DRC → render → gerbers. Confirm the interpreter fork (§III), the KiCad install paths, FreeRouting if routing will be automated. *Gate: the throwaway board produces gerbers.* If `pcbnew` doesn't import or `ZONE_FILLER` segfaults, learn it now, not at hour 200.

**Phase 1 — Scope and frozen numbers.** The generic Phase 0: objective, constraints, success criteria, risks — plus a **numbers probe**: a throwaway scipy/numpy script that verifies every value the design will freeze (gains, corner frequencies, dividers, power dissipation, creepage distances). Frozen numbers enter `DECISIONS.md` with the probe as evidence. *GATE G0 — human scope sign-off.*

**Phase 2 — Golden netlist as code, libraries, pin maps.** Author the netlist as a data structure (`board_spec.py` pattern: `build_board()` → components with `{ref, sym, val, fp, pins:{pad:net}, dnp, nc, fields}`) **before any CAD file exists**. Every downstream artifact becomes a function of it, and acceptance becomes pin-exact diffing. In parallel: project symbol/footprint libraries for parts the stock libs lack, every pin map carrying a dated datasheet citation. Pin maps are the highest-consequence, lowest-feedback work in the project — a wrong one produces a schematic and PCB that are perfectly self-consistent and perfectly wrong, and only a human reading the datasheet (or a dead board) catches it. *GATE G1 — values/interface freeze + human netlist-intent review + human pin-map review.* After G1, changing `board_spec.py` requires a gate.

**Phase 3 — Schematic generation.** The generator turns the golden netlist into human-auditable `.kicad_sch`. Its built-in gates, in order: diagonal-wire rejection → **pre-flight connectivity** (union-find over drawn geometry vs golden netlist, run *before* writing files — a wrong netlist must never reach disk) → write → **legibility gate** (run *after* writing, so a cosmetic failure can still be rendered and inspected). Then external gates: ERC (errors-only, exclusions confirmed empty) → **netcmp** (pin-exact, both directions, + domain safety assertions) → hierarchy-path integrity. *Gate: a human reads the schematic PDF and opens the project in the KiCad GUI.* Loop with Principle 13 until the human signs.

**Phase 4 — Layout.** For any repeated-block design: **route one cell properly, then replicate programmatically** **[convergent — the single most important layout decision]**. An N-channel board is 1× the routing plus a tiler, and mechanical changes become one-constant edits. Placement order: mechanical/connectors first (pinned by the enclosure), signal chain left-to-right, decoupling adjacent to its pin. Pre-route gate: courtyard/edge DRC + a 3D render (catches connectors facing inward faster than reading coordinates). Route (FreeRouting DSN→SES for what isn't cloned; hand-route the common section explicitly in the generator). Fill zones in a **separate process**. *Gates: DRC 0/0 · pad-net parity (own tool) · footprint↔symbol path bijection · netclass-really-applied (measure the copper) · census counts.*

**Phase 5 — Review artifacts.** Schematic PDF (`sch export pdf` — not `pcb export pdf` misnamed), zoomed mm-addressed crops of every dense region, 3D renders both sides. *Gate: a human opens the project in the KiCad GUI and reads it. The GUI, not a render — this is the only instrument that sees project-file-scoped defects.*

**Phase 6 — Fab package.** Gerbers + drill; fab BOM/CPL (fitted SMD only) and hand-solder BOM; purchasing doc with spares. **Every MPN re-verified against a live distributor page** — both projects found provisional part numbers that were obsolete, wrong-package, or fictional. *GATE — fab commit: the pre-fab checklist (§V.7), the fab's own parts-preview for polarized-part rotation, then the order button. Human-only.*

**Phase 7 — Bench acceptance.** The real gate. For anything energized beyond SELV — and for HV especially — a written energization procedure and a human present at first power. No session ever claims this gate.

---

## Part III — Environment (known-good stack; confirm at Phase 0)

The reference stack both projects ran on — assume it, verify it in Phase 0, and log deltas in the pipeline log:

```
Windows 11 · KiCad 10.0.3 (C:/Program Files/KiCad/10.0/) · FreeRouting 2.2.4 + Temurin JRE
CLI = C:/Program Files/KiCad/10.0/bin/kicad-cli.exe        (nothing KiCad is on PATH)
PY  = C:/Program Files/KiCad/10.0/bin/python.exe           (bundled 3.11.5 — the ONLY pcbnew interpreter)
```

**The interpreter fork — the single most useful environment fact [convergent]:**
- A tool that manipulates **board geometry** needs `pcbnew` and is locked to KiCad's bundled Python. No venv, no `pip install pcbnew`, no PYTHONPATH tricks — call KiCad's interpreter by full path. Its bundled deps: `pcbnew`, `fitz` (PyMuPDF), `PIL`, `numpy`, `requests`. No scipy, no matplotlib.
- A tool that **emits or verifies files** needs no KiCad API at all: there is *no* schematic API — `.kicad_sch`/`.kicad_sym` are written as s-expression text — and verification shells out to `kicad-cli`. These tools run on any Python 3, stdlib only. **Prefer this path for everything that can be expressed as it**: dependency-free, diffable, immune to API churn.
- Consequence: **zero third-party dependencies is the design**, not an omission. There is no `requirements.txt` because there is nothing to pin. Preserve this — a fresh machine needs only a KiCad install.

**Shell discipline.** Two shells, not interchangeable: PowerShell 5.1 (no `&&`, no `grep/head/tail`; use `;`, `Select-String`) and git-bash (POSIX tools, but MSYS path translation). Git-bash paths (`/c/Users/...`, `/tmp/...`) are **not** Windows paths: bash utilities accept them, `kicad-cli.exe`, `msedge.exe`, and Python's `open()` do not. **State the shell in every command block and write all paths as `C:/...` forward-slash** — both shells and Python accept those. Plain `python` is not on PATH; use absolute interpreter paths always.

**File-format ground truth.** When generating any KiCad file, take the schema version and formatting from a file KiCad itself wrote — `C:/Program Files/KiCad/10.0/share/kicad/demos/` is the reference corpus. Current known-good schematic schema: `(version 20250610)`. A fictional/future version invites KiCad to treat your file as newer than itself; an older schema triggers an on-load upgrade-and-cleanup pass that can dissolve your geometry.

**Rendering loop (review tooling).** Schematic defects are invisible at page scale; make region rendering a scripted step, not an improvisation. Two working recipes: (a) `render_crop.py` — export PDF, rasterize an mm-addressed crop with KiCad's bundled PyMuPDF; (b) SVG route — `sch export svg --exclude-drawing-sheet`, splice a `viewBox`, rasterize with headless Edge (`--virtual-time-budget=5000` is mandatory or you get blank PNGs; fresh `--user-data-dir` per invocation; `file:///C:/...` URLs only). The SVG additionally carries `textLength`/`font-size` per run — the honest calibration source for text metrics.

**FreeRouting.** Headless jar + JRE; needs the dead-proxy workaround (point its phone-home at a non-routable proxy so it fails fast instead of hanging). DSN export / SES import via small pcbnew scripts; `serialize()` must keep `(net NAME` on one line — FreeRouting's Specctra parser requires it.

---

## Part IV — The kernel: generating task tools

Every stage is executed by small single-purpose Python tools the session writes. The conventions, merged from both lanes — a generated tool must satisfy all of these:

1. **Headless.** No GUI, no prompts. Runs to completion or exits non-zero.
2. **Single task.** If it needs "and then", it is two tools. One tool broke ⇒ one owner.
3. **Zero-arg by default.** Paths are module constants from `HERE = os.path.dirname(os.path.abspath(__file__))`; the tool lives next to its artifact (kills "ran it on the wrong board"). Diagnostics pointed at arbitrary files take one path argument; bootstrap-shipped generic tools accept `argv[1]` with the constant as default.
4. **Idempotent and deterministic.** Re-running with unchanged inputs is byte-identical. Identity from `uuid5` over a fixed namespace and a semantic key, never `uuid4` — then "regenerate and `git diff`" is a free regression test. **The one trap [convergent]:** in hierarchies, `(sheet)` UUIDs must be unique **per instantiation** — seed the uuid5 key per instance, never from anything constant across instances (filename, child uuid), or every instance collapses onto one path.
5. **Carries its own executable acceptance check**, run in-process before exit, capable of failing, comparing against an **independent source of truth** (the golden netlist — never the tool's own intermediate state). Asymmetry learned, not designed: electrical checks run *before* writing files; legibility checks run *after* (so a failure can still be rendered).
6. **Explicit units at every boundary.** `pcbnew` internal units are integer **nanometres**: `pcbnew.FromMM()` in, `/1e6` out, never a bare literal into a setter. Schematics are **mm as text** on a 1.27 mm (50 mil) grid: compute in grid units, multiply by `U = 1.27` only at emission, snap every coordinate.
7. **Fails loudly and specifically** (net, refdes, coordinate — itemized), prints a one-line summary of what it changed on success, and honors the exit-code contract: `0` ok · `1` verification failed · `2` structural failure · `3` legibility failure.
8. **Never hand-edits generated CAD files**, and never calls `ZONE_FILLER.Fill()` in the process that built the board — fills run as a separate process on the saved file (in-process fill segfaults headlessly).
9. **Emission goes through a format layer** (`sexpr.py`: tokenize/parse/serialize, quoted strings round-trip exactly). Read-side regex is fine for diagnostics; never for writing.
10. **Deferred resolution beats ordering constraints.** Drawing code may reference `"U4.3"` before U4 is placed; a single `resolve()` pass turns names into coordinates after all placement — and is the one place geometry (diagonals, collisions) gets validated.

**Blank template** (merged from both lanes — start every new tool here):

```python
#!/usr/bin/env python3
"""<One sentence: what this tool produces or proves, and when in the pipeline it runs.>
<Why it exists / non-obvious constraint (e.g. "separate process: in-process Fill segfaults").>

Acceptance: <the executable condition that means done>.  Exit 0 only if it holds.
  "C:/Program Files/KiCad/10.0/bin/python.exe" <tool>.py        # pcbnew tools
  python <tool>.py                                              # emission/verification tools
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "<board>.<ext>")
U = 1.27  # mm per schematic grid unit; convert ONLY at emission. pcbnew: FromMM in, /1e6 out.

def build():
    """The one job. Compute in grid units / nm. Guard every mutation so re-running is a no-op."""
    raise NotImplementedError

def check(artifact, truth):
    """Executable acceptance. Compare against the independent source of truth (golden netlist),
    never against build()'s own state. Return a list of specific problems; [] means pass."""
    return []

def main():
    truth = None  # board_spec.build_board() or the exported netlist
    artifact = build()
    problems = check(artifact, truth)
    if problems:
        print("FAIL (%d):" % len(problems))
        for p in problems[:40]: print("   " + p)
        return 2
    # save here, after electrical checks pass
    print("PASS — <one line with counts>")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**The canonical tool set.** Copy these from the companion debriefs (§04 of each) rather than rewriting them — they are verified against real defects:

| tool | from | what it is |
|---|---|---|
| `sexpr.py` | schematic lane | the 108-line format layer (preserve the `(net NAME` head-atom behavior) |
| `check_netlist.py` | schematic lane | pin-exact netcmp both directions vs golden netlist + pluggable domain-safety assertions (the R-5 isolation pattern: promote a safety property from review-only to build failure) |
| `check_paths.py` | schematic lane | hierarchy instance-path integrity — the check `kicad-cli` provably skips (duplicate sheet UUIDs, orphan paths, child carrying `sheet_instances`) |
| `check_parity.py` | twelve-channel | real board↔schematic parity: every pad's net vs the exported netlist + footprint↔symbol **path bijection** — because `--schematic-parity` does not compare pad nets |
| `fill_zones.py` | twelve-channel | separate-process zone fill + the `.kicad_pro` netclass self-heal guard |
| `render_crop.py` | twelve-channel | mm-addressed zoomed crops via bundled PyMuPDF — the most useful debugging tool either lane built |
| `gen_test.py` (technique) | schematic lane | minimal-repro harness: when a CAD-format question is contested, generate the smallest project that isolates it, run the real tool on good and deliberately-broken variants, read off the answer |
| reference grid (technique) | schematic lane | for any "which way does this render" question: render the exhaustive grid of style × rotation once and *look*, instead of reasoning about conventions |

---

## Part V — Domain playbook (the ECAD craft, distilled)

### V.1 Golden netlist as code
One machine-readable source of truth for *what connects to what*, authored before any CAD file, consumed by the schematic generator, the netlist checker, and the layout tools. Acceptance everywhere becomes a diff against it. If this bootstrap transmits one structural idea, it is this.

### V.2 Schematic generation and legibility
- **Wires, not labels.** A label-routed schematic is netlist-correct and unreviewable ("this prevents me from doing a review"). Draw real wire trees: H-trunk → V-trunk → L → Z → around-the-body offset lanes, every candidate segment validated against foreign pins, foreign wires, and **symbol body rectangles** (keyed per `(ref, unit)` — multi-unit parts break every group-by-refdes assumption). Fallback to stub+label is allowed, counted, printed, and driven toward zero.
- **T-taps [convergent — both lanes' #1-tier fact]:** KiCad's GUI cleanup merges collinear wires and deletes junctions not at ≥3 wire *endpoints*; a mid-span tap survives the file, passes the CLI, and dissolves on first GUI save. Pre-split every run at each attach point so all meetings are end-to-end; emit junctions only where ≥3 endpoints coincide; assert both invariants in the generator.
- **Left-to-right signal spine.** Reading order = signal order; connected parts adjacent so their net is a short wire; power banded top/bottom; enough inter-block gap that power symbols and labels sit outside bodies (under-spacing resurfaces later as text collisions — the fix is to move a part, not route harder). Pick paper size from the widest signal chain; nothing warns when content runs off the page.
- **Power symbols.** Emit with `(pin_numbers hide)` **and** `(pin_names (offset 0) hide)` or every rail name prints twice plus a stray "1" — a library-level bug that masquerades as a placement bug. Orientation must point *away* from the part: establish the rotation→direction map by rendering a reference grid (ground-style: 0=down, 90=right, 180=up, 270=left; supply-style is the exact inverse). Cluster same-net power pins on *different* parts within ~12 grid units into one symbol; never bus power pins on the *same* part (draws across interleaved pins and reads as a short). A local label does **not** merge with a global power net — fallbacks place a power symbol, never a label.
- **Text.** Rotated symbols mangle text two ways: justify mirrors at 180° (pre-flip it) and field angle needs `(360 − symbol_rot) % 360` to stay horizontal — with a known-unresolved residual at exactly 180° (see schematic-lane gotcha #10; add an SVG-driven "text renders upright" check before trusting a fix). `Device:D_Schottky` has horizontal pins at rot 0, unlike R/C — any verticality heuristic keyed on rotation is inverted for diodes.
- **The legibility gate.** Machine-check the classes a reviewer would otherwise find one at a time: **L1** power symbol pointing into a body (ray-sample along the pointing direction) · **L2** text-run collision (boxes + margin; character advance calibrated from the SVG's own `textLength/font-size` — use the top of the measured range so boxes never under-estimate) · **L3** label/value overprinting a foreign body · **L4** wire crossings over a per-sheet budget. Stage severity (fatal one class at a time while working off warnings; then all fatal). **L4 is a ratchet, not a zero:** some crossings are topological; record the current count as a budget that may only ever be lowered. The ratchet pattern generalizes to any quality metric that can't legitimately reach zero.
- **Hierarchy.** Only the **root** carries `(sheet_instances)` (listing only `/`); a child that declares it becomes the GUI's top sheet. `.kicad_pro` must set `schematic.top_level_sheets` to the root — `kicad-cli` ignores the key, so only the GUI misbehaves. Symbol identity is `/<root_uuid>/<sheet_uuid>`; one child file instantiated N times (shared symbol UUIDs, N-path `(instances)`) and N child files are both valid — N files makes footprint↔symbol paths unique by construction. Loader rejects raw newlines in quoted strings: multi-line notes are separate `(text …)` elements.

### V.3 Netclasses — the most expensive fact in either debrief
Netclasses live in `.kicad_pro` (`net_settings.classes`, assigned by glob in `netclass_patterns` — hierarchical names need the sheet wildcard `*/NET` or the pattern silently matches nothing). **A netclass must carry its SCHEMATIC fields** (`wire_width`, `bus_width`, `line_style`, `diff_pair_*`, `microvia_*`): a PCB-only class **breaks eeschema connectivity for every net in it**, silently, and only when the project is loaded — while ERC, netlist export, and every check built on them stay green, because **`kicad-cli` never reads `.kicad_pro`**. Corollaries: a GUI save can flatten the project file's netclasses (zone fill then uses default clearances and DRC passes vacuously — ship the self-heal guard); and never infer "the rule applied" from "DRC passed" — **measure the copper** (read back track widths on the class's nets).

### V.4 Layout
Cell-then-replicate for repeated blocks (§II Phase 4). Tiling is arithmetic: `Duplicate()` + `Move(0, n·pitch)`, restride refs *derived* from a role count (never hand-maintained), rewrite pad nets `/X → /chNN/X`, and set each footprint's path from the netlist as **`sheetpath.tstamps + component.tstamps`** — the component tstamp alone silently collapses all instances onto one path (flat boards hide this because sheetpath is `/`). Edge-launch connectors: the footprint carries its cutout on `Dwgs.User` (not `Edge.Cuts`, or 48 footprints each cut the board edge); the outline builder reads placed notches back and subtracts them; a `.kicad_dru` rule waives `edge_clearance` for exactly that footprint; the 3D model needs `(rotate (xyz 270 0 0))`. Silk: move refdes to `F.Fab` on dense boards — cosmetic, but it is the difference between a DRC report you read and one you ignore.

### V.5 Libraries
Project-local libs beside the `.kicad_pro`, wired by `sym-lib-table`/`fp-lib-table` with `${KIPRJMOD}` — both tables must exist or the GUI can't resolve them. Prefer stock symbols/footprints when pad geometry verifiably matches. Pin maps carry dated datasheet citations at the point of definition; re-verify anything load-bearing that has aged past its gate. `lib_footprint_mismatch` (as-built vs library drift): fix by exporting the **as-built** instance back into the library (normalize to origin/0°/`REF**`, strip nets, `FootprintSave`) — never by disturbing the routed board. 3D models attach per-footprint; wrong paths fail **silently** (the part is just absent) — the render is the check, count what you expect to see; substitute same-package stock models when the vendor ships none.

### V.6 The blind-instrument table [convergent]
Know what each gate cannot see before quoting it:

| gate | structurally blind to |
|---|---|
| `kicad-cli sch erc` | everything in `.kicad_pro` (never reads it); GUI-strict connectivity; accepted a deliberately malformed hierarchy identically to a correct one |
| `kicad-cli sch export netlist` | same; lenient about taps the GUI rejects; derives paths from each symbol's own `(instances)` without cross-checking the root's sheets |
| `kicad-cli pcb drc --schematic-parity` | **pad-net comparison** — footprint-level only; prints 0 while the GUI reports hundreds |
| own netcmp / parity tools | whatever consumes the CLI-exported netlist inherits the CLI's blindness; UUID linkage needs the separate bijection check |
| all headless checks together | **anything `.kicad_pro`-scoped**; legibility; polarized-part rotation; mechanical sense; golden-netlist-vs-intent |
| the human in the GUI | nothing above — which is why the GUI gate is non-negotiable |

ERC hygiene: `--severity-error` for the errors-only number, confirm `erc_exclusions` empty and `pin_not_connected` at error before trusting a 0 — and record *which* zero you mean ("ERC 0 errors, 1 expected warning"), or two sessions will disagree about whether it regressed.

### V.7 Fab package and the pre-fab checklist
Fab BOM (`Comment,Designator,Footprint,<fab> Part #`) and CPL (`Designator,Mid X,Mid Y,Layer,Rotation`) — **fitted SMD only**; hand-solder BOM for everything the assembler won't place. A BOM is *not* a projection of the netlist: it needs DNP variants, mechanically-real-but-electrically-absent parts (sockets), quantity tiers, and spares (`ceil(per_board × boards × 1.2)` for hand-soldered). Checklist as practiced: DRC 0/0 · ERC 0 errors (exclusions confirmed) · pad-net parity + path bijection · netclass-applied measured on copper · zones filled · census counts · BOM/CPL consistency (fitted-SMD count = CPL rows) · 3D render inspected both sides · polarized-part rotation eyeballed in the fab's preview (KiCad↔fab rotation conventions differ for polarized parts) · every MPN re-verified live · outline/slots within fab capability · **a human has opened the project in the GUI and read it**.

### V.8 Debugging protocol
When the GUI disagrees with your checks: build a **minimal generated project** that reproduces (root + one child + one instance of the construct), then bisect toward the real design **one variable at a time** — and hold the `.kicad_pro` fixed while bisecting the schematic files, because the project file is a variable (the worst bug in either project hid for weeks behind an uncontrolled `.kicad_pro` riding along in both test arms). Keep a known-good reference project as a permanent diff target — diffing against one eliminated four wrong hypotheses in one pass. Beware the correct-but-not-causal fix: a real improvement that doesn't move the symptom reads as "the fix didn't take" and sends you backward. And "fixed" is declared by **the instrument that saw the bug** — if the human's GUI saw it, only the human's GUI closes it. Shared-working-directory ritual: KiCad does not reload changed files (`File → Revert` doesn't reliably reload child sheets); when a session regenerates, the human closes the project **without saving** and reopens — a GUI save at the wrong moment can also flatten the project file (V.3).

---

## Part VI — Workspace, sessions, output contract

**Workspace.** The generic file set applies (`CLAUDE.md`, `docs/SCOPE.md`, `ARCHITECTURE.md` where warranted, `INTERFACES.md`, `PLAN.md`, `STATUS.md`, `DECISIONS.md`, `tasks/`, `roles/`) plus the board additions: `docs/PIPELINE_LOG.md` (Part 0) · `docs/playbook/` (this file + both debriefs) · `hardware/<board>/` (generators, checks, `board_spec.py`, generated CAD as committed build artifacts, `outputs/`) · `SESSION_LOG.md` (append-only, absolute dates; close every session with entry → commit → **push**; the remote is the handoff medium). `CLAUDE.md` must state, in its first lines: the build-artifact rule (edit generators, never `.kicad_*`), the interpreter paths, and the shell/path discipline.

**Lanes.** The proven split is a **schematic lane** (golden netlist → symbols → schematic → netcmp/legibility) and a **board lane** (cell → tiling/placement → routing → DRC/parity → fab package), with `board_spec.py` and `sexpr.py` as the shared, orchestrator-owned contract surface. Firmware/host lanes run under the generic rules. Small boards collapse to one session (Principle 6) — but the gates never collapse.

**Output contract for the bootstrapping session.** Handed this file plus a brief: (1) Phase 0 environment proof; (2) Phase 1 scope + numbers probe → **stop at G0**; (3) on sign-off, author `board_spec.py` + libraries + the workspace and task briefs (multi-turn per Principle 8, whole files only) → **stop at G1**; (4) hand off to the lanes, which run Phases 3–6 under the gates above. Log pipeline lessons throughout; harvest at fab commit.

State up front which parts of the machinery you are collapsing for the project's size, and why. Everything in this file is amendable through the pipeline log — that is what it is for.
