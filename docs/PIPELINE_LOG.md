# PIPELINE_LOG

Append-only. Any session writes. Mandatory from session one (`EE_PROJECT_BOOTSTRAP.md` Part 0).

**Litmus test, applied ruthlessly:** *would this entry have helped on a completely different board —
or a different domain entirely?* If yes it belongs here. If it is a fact about **this circuit** it
belongs in `docs/DECISIONS.md` and has been dropped from this file. Twelve candidate entries were
rejected on that test this session (module class, bleed values, clearance numbers, part choices,
topology conclusions) — they are all in `DECISIONS.md`.

**Deduplicated.** Where two or more agents hit the same process problem independently, it is **one
entry**, and the multiplicity is recorded — independent convergence is the strongest signal that a
lesson is general rather than incidental.

**Scope:** `G` general · `C:<class>` class-specific · `P` this project only.

Session 1 harvest: **26 entries.** Eight are direct amendments to the bootstrap's own text; four
record convergence across 2–4 uncoordinated agents.

Session 2 harvest: **PL-33 … PL-37**, plus **two RECURRENCES logged on existing entries rather than
duplicated** — PL-04 (the stale demo oracle, hit again in session 2 *in the very document PL-04's
own amendment told us to write*) and PL-29 (a workflow reporting failure while the deliverable sat
complete on disk, recurring with a completely different root cause — see PL-36). **A recurrence on
an existing entry is more informative than a new entry: it says the lesson was written down and did
not arrive.**

---

## PL-01 — The bootstrap contradicts itself on the numbers probe: scipy vs the interpreter fork
date / session:   2026-07-23 / session 1 (bootstrap v1.0 first field test)
trigger:          Part II Phase 1 instructs "a throwaway scipy/numpy script that verifies every value
                  the design will freeze", while Part III states plainly that KiCad's bundled Python
                  has "no scipy, no matplotlib" and that zero third-party dependencies is the design.
                  Confirmed `[verified-run]`: `import scipy` fails under PY_KICAD, and plain `python`
                  is not on PATH, so there is no other interpreter to fall back to. Separately,
                  "throwaway" is wrong on its own terms: the probe is the standing evidence behind
                  every frozen number in `DECISIONS.md`.
resolution:       Wrote `hardware/hvctl/numbers_probe.py` stdlib-only (imports: math, os, sys, json,
                  traceback — confirmed by an AST walk over the finished file). 141 assertions, exit 0,
                  two consecutive runs byte-identical. Treated as a first-class generated tool under
                  Part IV, not as a scratch script.
bootstrap Δ:      In Part II Phase 1, replace "a throwaway scipy/numpy script" with
                  "a **stdlib-only** Python script (see Part III — there is no scipy)". Append:
                  "The numbers probe is **not throwaway**. It is the standing evidence for
                  `DECISIONS.md` and must be re-runnable, deterministic, and carry assertions like
                  any other generated tool (Part IV)."
scope:            G
status:           logged

---

## PL-02 — For any KiCad text format, "the tool loads it" is a weak gate; round-trip and byte-compare
date / session:   2026-07-23 / session 1
trigger:          A symbol library that loaded cleanly, exported SVG cleanly, and passed a bespoke
                  geometry checker still differed from what KiCad itself would write. Every such
                  difference produces a **phantom git diff the first time a human opens the library in
                  the GUI and presses Ctrl+S** — which destroys "regenerate and `git diff`" as a
                  regression test, the property Part IV convention 4 exists to buy.
resolution:       Added a seventh gate to the generator: run
                  `kicad-cli sym upgrade -o TMP --force <file>` and byte-compare TMP against our own
                  output. It failed immediately and taught four real KiCad 10.0 conventions that had
                  been guessed wrong: (1) default-valued blocks are **omitted** — KiCad drops
                  `(pin_names (offset 0.508))` because 0.508 is the default; (2) every `(xy ..)` of a
                  `(pts ...)` list goes on **one line**, not one per line; (3) canonical property
                  order is Reference, Value, Footprint, Datasheet, Description, user fields in
                  insertion order, then `ki_keywords`/`ki_fp_filters` **last**; (4) symbols are stored
                  sorted alphabetically and pins sorted by number regardless of emission order.
                  Every one of these loaded fine and would have reformatted on first save.
bootstrap Δ:      Add to Part IV as convention 11: "**Round-trip every emitted KiCad text file
                  through `kicad-cli` and byte-compare against your own output.** `<subcmd> upgrade
                  -o TMP --force` then diff. 'It loads' is not the gate — 'KiCad would have written
                  exactly these bytes' is. A file that loads but reformats on first GUI save silently
                  destroys the regenerate-and-diff regression test."
scope:            G
status:           logged

---

## PL-03 — To learn an unfamiliar CAD schema, BUILD the object in the vendor tool and save it
date / session:   2026-07-23 / session 1
trigger:          Part III says to take schema and formatting from a file KiCad itself wrote, using
                  the demo corpus as reference. That is necessary but **not sufficient**: a hand-picked
                  example never exercises rarely-used tokens. Zero stock footprints use a per-pad
                  `(clearance …)`; zero use the `Cmts.User` layer. Grepping the stock libraries would
                  have found neither, and both were needed.
resolution:       Wrote a ~40-line `pcbnew` script that constructs a throwaway footprint with exactly
                  the features needed and saves it. Reading the resulting bytes yielded
                  `(version 20260206)`, `(generator_version "10.0")`, `(clearance N)`, `Cmts.User`,
                  `(fill yes)`, `(embedded_fonts no)` and the property-block layout in one shot.
bootstrap Δ:      Amend Part III "File-format ground truth": "The demo corpus is the *reference*, not
                  the *oracle* — a hand-picked example never exercises rarely-used tokens. When you
                  need a token the demos do not contain, **build the object in the vendor tool and
                  save it**, then read the bytes. Verify the result by round-trip (Part IV
                  convention 11)."
scope:            G
status:           logged

---

## PL-04 — Environment delta: the bootstrap's schema version is stale, and the demo corpus is a stale ORACLE
date / session:   2026-07-23 / session 1
trigger:          Part III states "Current known-good schematic schema: `(version 20250610)`".
                  KiCad 10.0.3 on this machine writes **`20260306`** for `.kicad_sch` and
                  **`20260206`** for `.kicad_pcb`/`.kicad_mod`. Worse, the natural check — compare
                  against the demo corpus — produces a **false mismatch**: the shipped demos read
                  20250114 to 20260101, and `20260306` appears nowhere in them. Four agents hit this
                  independently; two nearly "fixed" a correct generator to match a stale demo.
resolution:       Established the correct oracle: copy a demo to scratch and run
                  `kicad-cli sch upgrade --force` on it. It rewrites 20250114/20250610 → **20260306**,
                  proving that is the native write format of the installed eeschema. Same technique
                  for `.kicad_mod` via `fp upgrade --force`.
bootstrap Δ:      Replace the sentence in Part III with: "Schema versions **drift between KiCad
                  patch releases and the shipped demos lag them**. Do not hard-code a version and do
                  not trust the demo corpus as an oracle. Determine it at Phase 0 by copying one demo
                  to scratch and running `kicad-cli <sch|pcb|sym|fp> upgrade --force` on it; the
                  version it rewrites to is what your generators must emit. Record it in
                  `docs/ENVIRONMENT.md`."
scope:            G
status:           logged   *(hit independently by 4 agents in session 1; **RECURRED in session 2**)*

RECURRENCE — 2026-07-23 / session 2.  **The lesson was logged, the bootstrap amendment was
                  written, and the mistake was made anyway — in the very document this entry's own
                  amendment told us to create.**  `docs/ENVIRONMENT.md` was written recording the
                  schematic schema as **`20250610`**, sourced by reading three `.kicad_sch` files
                  out of KiCad's own shipped demo corpus.  Those files ARE vendor-written, which is
                  what makes the oracle so persuasive — and they are STALE.  The installed eeschema
                  writes **`20260306`**, proved by the procedure this entry already prescribes:
                  copy a demo to scratch and run `kicad-cli sch upgrade --force`, which rewrites
                  `20250610 -> 20260306` `[verified-run]`.  The generators were already correct;
                  only the document that describes the environment was wrong, which is the worst
                  place for it to be, because every later session boots from that document rather
                  than from the tool.
                  The sharper statement of the lesson, added here because session 2 needed it:
                  **READING A VENDOR-SHIPPED EXAMPLE IS A WEAKER INSTRUMENT THAN MAKING THE VENDOR
                  TOOL WRITE THE ARTIFACT.**  An example ships once and then ages; the tool is the
                  thing whose current behaviour you actually depend on.  Where a fact can be
                  obtained either by reading a sample or by making the tool emit one, ALWAYS make
                  the tool emit one — and record the COMMAND, not the value.
                  Consequence recorded, not hidden: this fact had been tagged `[verified]`.  A
                  `[verified]` tag records that an instrument ran, not that the RIGHT instrument
                  ran.  See PL-37.

---

## PL-05 — Environment delta: the `kicad-cli` sub-command surface is narrower than assumed
date / session:   2026-07-23 / session 1
trigger:          Time lost searching for validation verbs that do not exist. Sessions assumed a
                  `sym check` / `fp check` by analogy with `sch erc` and `pcb drc`.
resolution:       Enumerated the surface `[verified-run]`. `sym` has exactly
                  `{upgrade [-o OUT] [--force] IN, export svg [...] IN}` — **no `sym check`, no
                  `sym erc`**. `fp` has exactly `{export svg, upgrade}` — no load/validate verb.
                  Practical consequences: (a) the best CLI loadability proxy for a symbol/footprint
                  is `upgrade --force` plus re-reading the `(version …)`; (b) a strictly stronger
                  check exists where PY_KICAD is available — `pcbnew.PCB_IO_MGR.FindPlugin(KICAD_SEXP)
                  .FootprintLoad()` returns actual pad objects, not merely "the file parsed".
bootstrap Δ:      Add to Part III: "**Enumerate the `kicad-cli` sub-command surface at Phase 0 and
                  record it in `docs/ENVIRONMENT.md`.** It is narrower than the `sch erc` / `pcb drc`
                  pattern suggests: as of 10.0.3 there is no `sym check` and no `fp` validate verb.
                  Where PY_KICAD is available, a `pcbnew` object readback is a strictly stronger
                  instrument than any CLI verb."
scope:            C:kicad
status:           logged

---

## PL-06 — Environment delta: FreeRouting is neither present nor appropriate here
date / session:   2026-07-23 / session 1
trigger:          Part III and Phase 4 assume FreeRouting 2.2.4 + Temurin JRE, with a dead-proxy
                  workaround. Neither is installed on this machine, and Phase 0's confirmation step
                  for it was never performed.
resolution:       Declared in `SCOPE.md` §0 that HV routing is done explicitly in the generator and
                  FreeRouting is not used at all. The reason is domain, not availability: an
                  autorouter has no concept of creepage-versus-clearance, no notion that a 15 mm gap
                  between two nets is a safety requirement rather than a preference, and no way to
                  express "this gap must be a milled slot".
bootstrap Δ:      Add to Phase 4: "**Never autoroute nets that carry a safety-derived spacing
                  requirement.** An autorouter optimises against DRC minima; a creepage rule is a
                  floor with reasoning behind it that the router cannot see. Route those explicitly in
                  the generator. Autorouting remains appropriate for dense low-voltage signal fabric."
                  Also make FreeRouting's Phase-0 confirmation explicitly conditional on the project
                  planning to use it.
scope:            G
status:           logged

---

## PL-07 — Vector and raster figures in datasheets carry engineering facts that text extraction is structurally blind to
date / session:   2026-07-23 / session 1
trigger:          **Four agents independently, and it changed conclusions every time.** `get_text()`
                  on the control-principle page returned only a heading and a caption. The entire
                  internal input network — a 10 kΩ pull-up to the internal reference, a 100 kΩ + 1 µF
                  filter, the mechanism by which the enable pin actually works, and a 20 kΩ series
                  resistance on the monitor output — was invisible. Those four numbers changed the
                  DAC-vs-PWM conclusion, the interlock glitch analysis, the ADC front end, and every
                  timing budget in the project. **The absence of text is not a signal that the page
                  is empty.**
resolution:       Enumerate figures with `page.get_image_info(xrefs=True)` (**not**
                  `page.get_images()`, which returns *document*-level images including ones not on
                  that page), then render and **look**:
                  `page.get_pixmap(matrix=fitz.Matrix(z,z), clip=fitz.Rect(...))` at z = 5–24.
                  **Trap:** `fitz.Pixmap(doc, xref)` / `extract_image(xref)` returns an **all-black**
                  image when the image carries an SMask (alpha). Two agents lost a cycle to this.
                  Rendering the *page region* composites the mask correctly.
bootstrap Δ:      Add to Part V as a new subsection **V.9 Datasheet mining**: "For every datasheet a
                  design depends on, **enumerate the figures and render each one at high zoom and look
                  at it.** Budget this as mandatory work, not as a fallback when text extraction
                  fails. Text extraction finds *content*; only the raster shows *topology*. Trap:
                  extracting an image by xref returns black if it carries an SMask — render the page
                  region instead. Locate figures with `get_image_info(xrefs=True)`, not
                  `get_images()`."
scope:            G
status:           logged   *(hit independently by 4 agents)*

---

## PL-08 — `get_text()` is structurally blind to table cell SPANS
date / session:   2026-07-23 / session 1
trigger:          A merged cell spanning two columns of a specification table is **indistinguishable
                  in the text stream** from a value belonging to one column. Here it would have
                  attributed an absolute-maximum voltage on a control pin to only one product family.
                  A design for the other family would then have driven that pin from a rail more than
                  twice its absolute maximum.
resolution:       Rasterised the table at 4× and read it visually. The merge is obvious in the image
                  and invisible in the text.
bootstrap Δ:      Append to V.9: "Any specification transcribed from a **multi-column** datasheet
                  table must be re-confirmed by rasterising the table and reading it visually before
                  it becomes load-bearing. Text extraction is for finding content; the raster is for
                  **attributing** it."
scope:            G
status:           logged

---

## PL-09 — Verifying a mechanical transcription when the dimension labels are outlined artwork
date / session:   2026-07-23 / session 1
trigger:          Vendor dimensional drawings frequently carry their dimension labels as **outlined
                  vector artwork or raster**, not text — nothing in the PDF text stream contained any
                  of the numbers. So "I read the drawing and typed it in" had no instrument behind it
                  at all, on the highest-consequence, lowest-feedback data in the project.
resolution:       A repeatable metrology recipe that needs no OCR: (1) rasterise at high zoom;
                  (2) use a **known repeated feature as the internal ruler** — here the pin pitch,
                  which measured 182.00 px with 0.00 px deviation across all four gaps; (3) report
                  every dimension referenced to a thick stroke as a **bracket** `[stroke centreline ..
                  stroke outer edge]` rather than a single number, and make bracket containment the
                  pass criterion; (4) prefer **scale-free ratios** where possible, since they are
                  immune to calibration error. Two agents did this independently on the same drawing
                  and agreed to within 0.02 mm. Sub-technique: when blob-finding features, pins that
                  touch leader lines or case walls **merge with them and vanish** from a
                  connected-component pass — component labelling found 3 of 7 pins; restricting the
                  search to a narrow strip just inside the known wall and requiring a nearly-fully-dark
                  run of minimum length found all 7.
bootstrap Δ:      Append to V.9: "Dimension labels in vendor drawings are often artwork, not text.
                  Verify a mechanical transcription by rasterising at high zoom, calibrating on a
                  **known repeated feature** in the same image (never on a label you are trying to
                  verify), and reporting stroke-referenced dimensions as brackets with containment as
                  the pass criterion. This turns 'I read the drawing' into an executable check, and it
                  **self-reports its own resolution limit** — which is exactly the blind-instrument
                  disclosure Principle 11 demands."
scope:            G
status:           logged   *(hit independently by 2 agents)*

---

## PL-10 — Facts inherited from a brief or an upstream session are `[recalled]`, not `[verified]`
date / session:   2026-07-23 / session 1
trigger:          **Three agents, three different ways.** (a) A task brief supplied a block of
                  pre-extracted datasheet facts framed as authoritative; the datasheet block survived
                  re-extraction intact but an accompanying **standards constant was wrong in the
                  permissive direction** — it named one column of a table while quoting a different
                  column's formula, giving roughly a third of the required spacing. (b) A brief's
                  characterisation of a reference board was wrong on **three of four** counts, all
                  settled by cheap greps in minutes. (c) A handed-down "ground truth" extract was
                  *correct but materially incomplete*, missing four figure-only values that changed
                  several conclusions (PL-07).
resolution:       Re-extracted everything load-bearing from primary sources. Every correction is in
                  `DECISIONS.md` with the instrument named.
bootstrap Δ:      Amend Part 0's evidence discipline: "**Facts inherited from a task brief or an
                  upstream session carry the epistemic status of `[recalled]`, not `[verified]`,
                  until this session re-derives them from the primary artifact.** Re-verify anything
                  load-bearing before using it. A wrong constant in a brief is indistinguishable from
                  a right one — and note that an inherited extract being *correct* does not make it
                  *complete*."
scope:            G
status:           logged   *(hit independently by 3 agents)*

---

## PL-11 — "Compare against an independent source of truth" has no recipe when the ground truth is paywalled
date / session:   2026-07-23 / session 1
trigger:          Part IV convention 5 and Principle 14 both require comparing against an independent
                  source of truth. For a safety-standard-bound design the ground truth is a document
                  that costs money and is not on the machine. The bootstrap offers no procedure, and
                  the vacuum invites the worst outcome: a recalled constant written into a DRC rule.
resolution:       A three-step pattern was invented and used — and then **a skeptic pass showed that
                  one of its three steps had failed silently**, which is itself the most useful part
                  of this entry. (a) Reconcile two **independent** secondary reproductions and use
                  only the columns where they agree exactly. (b) Find a quantity two **different**
                  standards families must agree on from first principles and assert their agreement.
                  (c) Tag the constant `[verified-web, secondary]` and put "a human must open a
                  primary copy before the fab-commit gate" on the pre-fab checklist.
                  **Step (b) is where it broke.** The chosen cross-check was an **algebraic
                  tautology** — both expressions reduce to exactly the same linear form above the
                  breakpoint, so the assertions could not fail for any input — *and* both "independent"
                  columns had been copied from the **same web page**, so it was single-source as well.
                  The document's own verdict block called it "the only internal evidence that the
                  transcription is right". It was zero evidence.
bootstrap Δ:      Add to Part V: "**Standards-bound constants.** When the primary standard is
                  paywalled: (a) reconcile two genuinely independent secondary reproductions and use
                  only columns where they agree exactly — *verify the sources are actually different
                  documents, not two quotations of one page*; (b) cross-check against a different
                  standards family, and **prove the check is falsifiable before trusting it** — if
                  both sides reduce to the same algebraic form, the assertion cannot fail and is
                  worthless; (c) tag `[verified-web, secondary]`. Add to the §V.7 pre-fab checklist:
                  **every standards-derived constant traced to a primary document.**"
scope:            G
status:           logged

---

## PL-12 — Computed numbers must be interpolated into prose by the generator, never typed alongside it
date / session:   2026-07-23 / session 1
trigger:          A session wrote an explanatory bullet asserting that a particular mitigation "costs
                  board area". When the generator was made to *compute* the figures rather than
                  assert them in prose, the arithmetic showed the two options were exactly equal —
                  the mitigation was free. **The prose was wrong and its own adjacent arithmetic
                  caught it.** The same document also shipped an accuracy claim that its own parts
                  footnote contradicted, because the two were typed independently.
resolution:       Every number in the generated document is now formatted through the same expression
                  that computes it. A second half of the same idea, from a different agent: a **prose
                  reference document should ship with its own zero-arg acceptance checks**, exactly
                  like a generator — one that re-derives every derived quantity from a handful of
                  primitives **and string-matches the result against the text actually printed in the
                  document**, so a hand-edited coordinate fails the check.
bootstrap Δ:      Add to Part IV conventions: "**Any tool that emits an explanatory document must
                  format every number through the same expression that computes it.** Prose typed
                  next to a number is an unchecked assertion; interpolated prose is contradicted in
                  its own sentence when it is wrong. Extend this to hand-written reference documents:
                  ship them with a zero-arg check that re-derives every quantity **and string-matches
                  the result against the document's own text**, making prose and arithmetic a single
                  verified artifact instead of two things that drift."
scope:            G
status:           logged   *(hit independently by 2 agents)*

---

## PL-13 — Put the arithmetic in a committed zero-arg script from the first line, not after the numbers stabilise
date / session:   2026-07-23 / session 1
trigger:          A study required two full verification passes because its first-pass design was
                  invalidated by a datasheet read performed during the second pass. Numbers do not
                  stabilise — that is the normal case, not the exception.
resolution:       Because the arithmetic already lived in a committed re-runnable script, the
                  correction was a five-minute re-run instead of a rewrite of the prose.
bootstrap Δ:      Add to Phase 1: "For study documents, put the arithmetic in a committed zero-arg
                  script **from the first line**, not once the numbers stabilise. The whole point is
                  that they do not stabilise."
scope:            G
status:           logged

---

## PL-14 — Mutation-test your own acceptance check before reporting exit 0
date / session:   2026-07-23 / session 1
trigger:          **Two agents, independently.** An acceptance check that has never been observed to
                  fail is an untested assertion, and "exit code 0" from it means nothing. Principle 11
                  says every check must declare what it cannot see; this is the executable version.
resolution:       Both agents deliberately corrupted their own artifacts and confirmed each gate
                  fired with the intended exit code — nine mutations for the symbol library (wrong pin
                  name, renumbered pin, invalid pin style, stale schema, off-grid pin, colliding
                  names, ground pin inside the HV keepout, extra pin on the HV row, reintroduced
                  formatting drift) and eight for the footprint (**including injecting the exact
                  defect the footprint was written to fix**, and a sign flip on the body offset).
                  17/17 caught. Two secondary findings worth transmitting: (i) one "failure" turned
                  out to be a malformed mutation rather than a wrong gate — only trying revealed
                  which; (ii) one branch was **unreachable by any artifact mutation** because the
                  geometry it guards is fixed by the part, so it had to be exercised by forcing the
                  *requirement* instead.
bootstrap Δ:      Add to Part IV convention 5: "**Mutation-test the acceptance check in the same
                  session that writes it.** Inject the specific defect the tool exists to prevent and
                  confirm the check fires with the intended exit code. A check that has never been
                  observed to fail is an untested assertion. If a branch cannot be reached by mutating
                  the artifact, exercise it by mutating the requirement, and say so."
scope:            G
status:           logged   *(hit independently by 2 agents)*

---

## PL-15 — An independent recomputation must be a different PATH, not the same arithmetic retyped
date / session:   2026-07-23 / session 1
trigger:          Principle 14 forbids comparing a generator's output against the generator's own
                  assumptions, but a check that re-reads `build()`'s variables and re-does the same
                  algebra satisfies the letter and none of the intent: a sign error or a transposed
                  term cancels perfectly.
resolution:       Two working instances. (a) Footprint: `build()` works **outward from the pin-array
                  centroid**, `check()` works **inward from the body rectangle**; the two share only
                  five drawing primitives, so a transposition shows up as a disagreement.
                  (b) Filter dynamics: computed both by RK4 integration and by closed-form
                  partial-fraction residues — two methods sharing no code — agreeing to 4.2e-13,
                  which is what made the settling figure quotable.
bootstrap Δ:      Add to Part IV convention 5: "'Independent' means a **different derivation path**,
                  not the same arithmetic retyped. Build outward, check inward. For any dynamic
                  result, compute it twice by structurally different methods (e.g. numerical
                  integration and a closed form) — cheap, and it converts `[recalled]` into
                  `[verified-run]`."
scope:            G
status:           logged   *(hit independently by 2 agents)*

---

## PL-16 — A probe's assertions are RESULTS, not a build gate — and the exit-code contract invites the wrong instinct
date / session:   2026-07-23 / session 1
trigger:          The exit-code contract (`0` ok / `1` verification failed / `2` structural /
                  `3` legibility) reads naturally as "make it exit 0". For a Phase-1 numbers probe
                  that instinct is **actively harmful**: a failing assertion is the most valuable
                  output the probe can produce, and tuning a threshold until it passes launders a real
                  design constraint into a green check.
resolution:       Two design choices made it workable: (a) the harness **collects** all assertion
                  results and evaluates every one rather than aborting at the first failure, so one
                  failure never hides nine others; (b) claims that are *expected* to fail (a rejected
                  divider topology, a rejected package) are computed and printed as **FINDINGS**
                  rather than asserted, so the assertion set stays meaningful while the failure stays
                  on the record.
bootstrap Δ:      Add a note under the Part IV exit-code contract: "For a Phase-1 **numbers probe**,
                  a failing assertion is a *result*, not a bug — never tune a threshold to make it
                  pass. Collect all assertion results rather than aborting on the first; print
                  expected-to-fail claims as FINDINGS rather than asserting them."
scope:            G
status:           logged

---

## PL-17 — `pcbnew` cannot open legacy boards from the Python API; go straight to a stdlib parser
date / session:   2026-07-23 / session 1
trigger:          Auditing a KiCad-5-era reference board (file version 20171130): `LoadBoard()` hung
                  for >120 s with zero stdout, never reaching the first `print()` after the call, and
                  had to be killed.
resolution:       Wrote a purpose-built stdlib s-expression parser for all geometry queries. This is
                  also what the project rules prefer, so the fallback was the right answer anyway —
                  and it had a further benefit: being independent of KiCad's own DRC engine is exactly
                  what made the resulting clearance measurements evidence rather than a restatement.
bootstrap Δ:      Add to Part III: "`pcbnew` (KiCad 10) can **hang indefinitely** on boards written by
                  much older KiCad versions. When auditing a legacy reference board, go straight to a
                  stdlib s-expression parser rather than burning a timeout — and note that an
                  independent parser is the *better* instrument anyway when the thing being measured
                  is something KiCad's own DRC is supposed to check."
scope:            C:kicad
status:           logged

---

## PL-18 — `pcbnew` API traps that each look like a broken script
date / session:   2026-07-23 / session 1
trigger:          Three separate dead ends, each producing an error message that pointed away from the
                  cause.
resolution:       (a) **The API reports user-facing layer names** (`F.Silkscreen`, `F.Courtyard`,
                  `User.Comments`) while the **file format uses short names** (`F.SilkS`, `F.CrtYd`,
                  `Cmts.User`). A readback check that string-matches file-format names against API
                  output produces a **false failure** — which is exactly what happened. Compare
                  numeric layer ids, or carry an alias table.
                  (b) Module-level `pcbnew.FootprintSave()` / `FootprintLoad()` route through
                  `GetPluginForPath()`, which guesses the plugin from directory contents and returns
                  `None` for an **empty** `.pretty` — yielding the useless
                  `AttributeError: 'NoneType' object has no attribute 'FootprintSave'`. Go explicit:
                  `PCB_IO_MGR.FindPlugin(PCB_IO_MGR.KICAD_SEXP)`. Also: the method is `FindPlugin`,
                  **not** `PluginFind`, in KiCad 10.
                  (c) `PAD.SetLocalCoord()` does not exist in `pcbnew` 10. Add the pad to the
                  `FOOTPRINT` first, then `SetPosition()` in board coordinates; the local coordinate
                  is derived.
bootstrap Δ:      Add a short "pcbnew API traps" list to Part III with these three items, prefaced:
                  "Each of these produces an error that points away from its cause."
scope:            C:kicad
status:           logged

---

## PL-19 — How to satisfy "stdlib-only tool" and "KiCad is the instrument of record" at the same time
date / session:   2026-07-23 / session 1
trigger:          Part III mandates that text-emitting tools be stdlib-only and run on any Python 3.
                  Part IV convention 5 mandates that the acceptance check compare against an
                  independent source of truth. For a footprint the strongest available truth is
                  `pcbnew`'s own loader — which is locked to KiCad's interpreter. The two rules pull
                  in opposite directions and the bootstrap does not resolve the tension.
resolution:       Keep the `pcbnew` code as a **module-level string**, write it to a tempfile, run it
                  under `PY_KICAD` via `subprocess`, and parse JSON back. The generator then imports
                  on any Python 3 with zero third-party dependencies (AST scan of the finished file:
                  `fnmatch, json, math, os, re, subprocess, sys, tempfile, uuid` — `pcbnew` never
                  appears as an import) while the strongest available check still runs.
bootstrap Δ:      Add to Part III after the interpreter fork: "**When a stdlib-only tool needs a
                  KiCad-API check**, keep the `pcbnew` code as a module-level string, write it to a
                  tempfile, run it under `PY_KICAD` via `subprocess`, and parse JSON back. The tool
                  stays dependency-free and portable; the check stays authoritative. This is the
                  standard resolution of the fork's central tension."
scope:            G
status:           logged

---

## PL-20 — Verifying that a 3D model actually landed where you think: the instrument and its four traps
date / session:   2026-07-23 / session 1
trigger:          §V.5 says wrong 3D-model paths fail **silently** and "the render is the check". A
                  render is not enough — it cannot resolve a 0.23 mm placement error, and placement
                  error is the whole failure mode for an asymmetric part.
resolution:       **`kicad-cli pcb export vrml --units mm --user-origin 0x0mm` is the numeric
                  instrument.** It resolves both `.step` and `.wrl` models into one explicit
                  world-space point list, so a script can measure where a model actually landed
                  relative to the pads. `--user-origin 0x0mm` additionally lets the tool self-calibrate
                  the frame from the board outline instead of assuming it. Four traps, each of which
                  looks exactly like "the model failed to load":
                  (1) **KiCad negates Y between footprint and model coordinates** (model +Y =
                  footprint −Y). A symmetric test part cannot detect this; determine it empirically
                  per KiCad version by reading the `AXIS2_PLACEMENT_3D` inside the component's
                  `ITEM_DEFINED_TRANSFORMATION` in a `pcb export step`.
                  (2) **KiCad's VRML unit is 0.1 inch**, so `.wrl` geometry must be written as mm/2.54
                  — self-evidencing, because `--units mm` wraps the whole scene in `scale 2.54 2.54 2.54`.
                  (3) KiCad emits each distinct model once with `DEF` and instances the repeats with
                  `USE`; a parser that ignores `USE` sees **zero geometry** for every instance after
                  the first.
                  (4) Classify geometry **per `IndexedFaceSet`**, not per point, or board-wide
                  copper/mask/silk groups contaminate a footprint's bounding box and give
                  plausible-but-wrong dimensions.
                  Separately: `pcb export step` writes an **assembly** — each component's geometry
                  stays in its own local frame — so a naive bounding box over `CARTESIAN_POINT`s
                  reports every component sitting at the origin, which is a very convincing wrong
                  answer. And `--no-board-body` alone fails outright; keep the board body and use
                  `--component-filter`.
bootstrap Δ:      Add to §V.5: "**A render is not a placement check.** To prove a 3D model landed
                  correctly, export VRML (`--units mm --user-origin 0x0mm`) and measure the model's
                  world-space extents against the pads. Four traps: KiCad negates Y between footprint
                  and model frames; the VRML unit is 0.1 inch; repeated models use `DEF`/`USE`;
                  classify per-`IndexedFaceSet`. `pcb export step` is an assembly — placement lives in
                  the `ITEM_DEFINED_TRANSFORMATION`, not in the point coordinates."
scope:            C:kicad
status:           logged

---

## PL-21 — Hand-writing a real B-rep for rectangular parts, with a self-check that catches inside-out shells
date / session:   2026-07-23 / session 1
trigger:          Needed a vendor-independent 3D model. The assumption was that hand-writing STEP
                  meant falling back to `FACETED_BREP` or a mesh.
resolution:       A box needs only **planar** faces, so a true `ADVANCED_BREP` (`VERTEX_POINT` /
                  `LINE` / `EDGE_CURVE` / `ADVANCED_FACE` on `PLANE` / `CLOSED_SHELL` /
                  `MANIFOLD_SOLID_BREP`) is mechanical and needs **no PCURVEs**. OpenCASCADE reads it
                  fine. The whole helper is ~120 lines and gives the correct entity types for free.
                  **Cheap, strong self-check:** compute the enclosed volume from the emitted face
                  loops by the divergence theorem and compare against the analytic volume. It catches
                  inside-out shells, wrongly-ordered edge loops and dropped faces in a single number,
                  and it runs on the file just written rather than on the in-memory model. Determinism
                  trap: STEP's `FILE_NAME` carries a timestamp — the obvious `datetime.now()` silently
                  breaks byte-identical regeneration, which is the property Part IV convention 4 buys.
bootstrap Δ:      Add to §V.5: "Vendor 3D models can be dimensionally wrong in ways **no `(offset)`
                  can fix** (e.g. an internally mis-centred feature). For rectangular parts, generating
                  a true `ADVANCED_BREP` is ~120 lines of planar faces with no PCURVEs. Self-check by
                  the **divergence theorem** — enclosed volume from the emitted loops versus analytic
                  volume catches inside-out shells, bad loop ordering and dropped faces in one number.
                  Hard-code the STEP `FILE_NAME` timestamp or determinism is silently lost."
scope:            C:mechanical
status:           logged

---

## PL-22 — Rendering and actually LOOKING is not redundant with geometry checks
date / session:   2026-07-23 / session 1
trigger:          A legibility checker passed a symbol that had a free-standing text label printed
                  **on top of** a pin name, because the checker only knew about pins. One glance at
                  the render caught it, along with a second defect the checker also could not see.
resolution:       Rendered all three symbols to PNG and looked. Then — and this is the part that
                  matters — **encoded the newly-discovered failure class as a new gate** so the next
                  person does not need the same eye. Same pattern on the footprint: the SVG render
                  confirmed visually what the numeric check confirmed numerically, and the two see
                  different things.
bootstrap Δ:      Reinforce §V.2's legibility gate with: "**Render and look at every generated symbol
                  and footprint, every round.** Machine legibility checks only know about the element
                  classes you told them about; the eye finds the class you have not thought of yet.
                  Then encode the newly-found class as a gate (Principle 13) — the looking is what
                  *discovers* classes, not what *retires* them."
scope:            G
status:           logged

---

## PL-23 — When re-implementing vendor geometry math, model the exact shape; a conservative approximation manufactures false positives
date / session:   2026-07-23 / session 1
trigger:          A clearance audit that modelled roundrect pads as sharp rectangles reported a
                  0.099 mm gap and an apparent DRC violation. Exact geometry (inner rectangle grown by
                  `roundrect_rratio × min(size)`) gives 0.200 mm and no violation.
resolution:       Corrected the parser and re-ran **before writing anything down**. A conservative
                  approximation is not safe when the output is a finding you are going to publish: it
                  manufactures false positives that damage the credibility of the true positives
                  beside them.
bootstrap Δ:      Add to Part IV: "When re-implementing a vendor's geometry math to produce a
                  **finding**, model shapes exactly. Pessimistic approximations are fine for a filter
                  and dangerous for a report — a false positive beside a true one discredits both.
                  Verify the shape model before quoting any number derived from it."
scope:            G
status:           logged

---

## PL-24 — A reference design's own artifacts contradict each other, and every such delta is itself a finding
date / session:   2026-07-23 / session 1
trigger:          **Three independent instances in one reference project.** (a) The rendered schematic
                  PDF in `doc/` was a **different revision** from the `.sch` files it was exported
                  from — reading only the PDF yields the wrong circuit (a unity buffer instead of a
                  gain stage, no enable control, a different clamp part). (b) The `.kicad_pcb` was a
                  revision behind the `.sch`, with six parts existing only in the schematic —
                  including the safety-critical pull-down — and two copper modifications recorded only
                  as **text annotations**. Anyone auditing the layout alone would draw the opposite
                  safety conclusion. (c) A footprint **contradicted itself**: its silk/fab outline was
                  centred on the pin array while its own 3D-model `(offset (xyz …))` matched the
                  datasheet's asymmetric corner to 0.028 mm.
resolution:       Derived every number from the text sources and **diffed the artifacts against each
                  other**, reporting each delta explicitly. Instance (c) generalises into a cheap,
                  high-value check for any inherited library.
bootstrap Δ:      Add to §V.8: "**On a reference or inherited design, diff its artifacts against each
                  other; every delta is a finding.** Use rendered PDFs only to orient yourself, then
                  derive from the text sources. Cross-check the PCB's footprint list against the
                  BOM/schematic refs and report the **set difference** explicitly. And diff a
                  footprint's `(offset (xyz ...))` against its own outline extents — a fast way to
                  catch centred-versus-asymmetric body errors, which produces a citable, non-arguable
                  defect rather than an opinion."
scope:            G
status:           logged   *(three instances in one project)*

---

## PL-25 — A vendored third-party library is part of the audit surface
date / session:   2026-07-23 / session 1
trigger:          The reachable memory-safety defects in a reference firmware were **not** in the
                  application source: an unbounded buffer write and an unbounded command-table write
                  both lived in a third-party parser copied into the firmware directory. Auditing only
                  the project's own source would have missed the worst findings.
resolution:       Audited the vendored source line by line alongside the application.
bootstrap Δ:      Add to the firmware/host lane note in Part II: "**Vendored third-party source is
                  part of the audit surface, not a dependency you may treat as reviewed.** On safety-
                  relevant devices, audit copied-in libraries with the same rigour as your own code —
                  the reachable defects are disproportionately there, because nobody feels
                  responsible for them."
scope:            G
status:           logged

---

## PL-26 — Multi-lens adversarial review finds defects a single lens structurally cannot
date / session:   2026-07-23 / session 1
trigger:          Five topology studies, each with its own acceptance reasoning, each having passed
                  its own author's review. Three independent judge sessions were then run under three
                  different lenses (safety/failure-modes, electrical/performance, buildability/cost),
                  plus five adversarial skeptic passes each tasked with **refuting** a specific claim.
resolution:       The panel found **23 substantive defects the analysts missed**, including four
                  present in *all five* studies simultaneously. The critical structural observation:
                  all three judges scored the winner identically at 7/10 but **for non-overlapping
                  reasons** — one deducted for an unreachable safe state, one for a load-dependent
                  droop, one for procurement. A single-lens review would have found roughly **one
                  third** of the defect list. Separately, the skeptic passes refuted 2 of 5 claims
                  outright, including one where a document's self-declared "strongest evidence" was an
                  algebraic tautology (PL-11), and one where a claimed gate had simply never been run
                  (PL-05's sibling: no gerbers existed anywhere despite the phase being reported
                  complete). Cost: five extra sessions. It bought a defect list no amount of
                  self-review would have produced, because self-review shares the author's blind spots
                  by construction.
bootstrap Δ:      Add to Part II, before the fab-commit gate: "**Where a decision is expensive and
                  irreversible (topology selection, part-family selection, fab commit), run a
                  multi-lens review: N independent analyses, then M independent judges under
                  *explicitly different* lenses, then adversarial passes tasked with refuting specific
                  named claims rather than reviewing generally.** Judges must not see each other's
                  work. Two structural results transfer: identical scores from different lenses
                  usually rest on *non-overlapping* reasons, so the union of the deductions is the
                  real defect list; and 'refute this specific claim' finds a class that 'review this
                  document' does not — notably claims whose evidence is circular or whose gate was
                  never executed."
scope:            G
status:           logged

---

## PL-27 — Cross-generator name coupling: check for sibling generators before inventing names, and expect live mutation
date / session:   2026-07-23 / session 1
trigger:          A symbol generator was about to emit a footprint name of its own invention. A
                  sibling generator in the same directory had already established a different name.
                  Had the first guess shipped, the symbol's `Footprint` field would have pointed at a
                  footprint nobody was going to build, and the failure would have surfaced only at
                  **netlist import**. Separately and more sharply: the *same constant* was observed
                  changing on disk between two reads within one session, edited by a concurrent agent.
                  The end state is correct and consistent, but concurrent generator sessions can race
                  on a shared constant with no locking and no notification.
resolution:       Adopted the sibling's name; added a non-fatal `warn_project_integration()` that
                  re-checks the cross-generator contract on every run. Two independent generators
                  written from the same drawing later agreed to the micron without coordinating —
                  which is the good outcome this check exists to guarantee rather than hope for.
bootstrap Δ:      Add to Part IV: "**Check the working directory for sibling generators before
                  inventing any name that crosses a tool boundary** (footprint↔3D model↔symbol field).
                  Give each generator an explicit commented constant naming its counterpart, and a
                  non-fatal runtime check that the counterpart still agrees. In multi-session runs,
                  assume a shared constant can change under you mid-session; the runtime check is what
                  makes that safe."
scope:            G
status:           logged

---

## PL-28 — Small standing gates: markdown table integrity, PowerShell quoting, `__pycache__` hygiene
date / session:   2026-07-23 / session 1
trigger:          Three small process frictions that each cost a round-trip and each recur on every
                  project.
resolution:       (a) **Markdown tables silently break on unescaped pipes**, and absolute-value
                  notation (`|X| < Y`) is a common source in EE documents — **including inside
                  backtick code spans, where escaping is still required**. A ~20-line stdlib checker
                  that walks fenced/unfenced regions and compares column counts per table caught it
                  and confirmed 33 tables well-formed. Worth adopting as a standing cheap gate on any
                  generated `.md`, in the same spirit as the CAD acceptance checks.
                  (b) **PowerShell 5.1 mangles any `python -c` one-liner containing both single and
                  double quotes** (`The string is missing the terminator`). Use a git-bash heredoc:
                  `"C:/.../python.exe" - <<'EOF'`. `CLAUDE.md` names the two shells but not this
                  specific failure, which cost two round-trips.
                  (c) Importing a generator via `importlib` for testing leaves `__pycache__/` inside
                  the repo tree; two exist and must be gitignored, or the orchestrator commits build
                  cruft.
bootstrap Δ:      Add to Part IV: "Ship a **markdown structural check** (per-table column-count
                  comparison, fence balance) as a standing gate on any generated `.md`; unescaped
                  pipes from absolute-value notation break tables silently, including inside code
                  spans." Add to Part III shell discipline: "PowerShell 5.1 cannot parse a `python -c`
                  one-liner mixing quote types — use a git-bash heredoc for throwaway Python." Add
                  `__pycache__/` to the bootstrap's recommended `.gitignore`.
scope:            G
status:           logged

## PL-29 — A subagent that dies mid-run leaves a half-built gate, and the gate must be re-checked against disk
date / session:   2026-07-23 / session 1 (bootstrap v1.0 first field test)
trigger:          The Phase-0 environment-proof agent died on an API transport error ("Connection closed
                  mid-response") after writing its generators and running ERC + netlist export, but before
                  implementing gerber export or writing `docs/ENVIRONMENT.md`. The orchestration layer
                  reported a failed agent and passed `null` downstream. Two failure modes were then
                  available, and only one was avoided: (a) treat the agent's absence as "Phase 0 not done"
                  and re-run everything, discarding correct work already on disk; (b) treat the partial
                  artifacts as complete because generators existed and ERC passed. What saved the session
                  is that the verification phase checked the GATE ("does a gerber file exist?") rather than
                  the AGENT ("did the phase complete?"), and correctly reported the gate unmet while the
                  generators sat there working.
resolution:       Inventoried `hardware/phase0_env_proof/` on disk, found schematic + PCB + netlist + ERC
                  present and valid, finished only the missing links (fill → DRC → PDF/SVG/render →
                  gerbers + drill) directly, then wrote the missing `ENVIRONMENT.md`. Roughly 10 minutes
                  versus ~40 for a clean re-run. The partial work was sound; only the tail was missing.
bootstrap Δ:      Add to Part 0 (new "Part 0.1 — when a session or agent dies"): "**A dead session is not
                  an empty one.** When any unit of work fails mid-run, the next actor MUST inventory the
                  filesystem before deciding to re-run — generated artifacts are the handoff medium
                  (Principles 2 and 8: 'no single turn is load-bearing — resume from committed state'), and
                  that principle only pays off if resumption is actually attempted. Re-running from scratch
                  after a partial failure discards exactly the work Principle 8 exists to protect." And to
                  Part II: "**Gates are evaluated against artifacts, never against reports.** Phrase every
                  gate as a question about a file on disk ('does a gerber exist and is it non-empty?'),
                  never about an actor ('did the phase complete?'). A gate phrased about an actor cannot
                  distinguish 'nobody ran it' from 'it ran and failed' from 'it ran, half succeeded, and
                  the half that matters is fine'."
scope:            G
status:           logged   *(**RECURRED in session 2, with a different root cause** — see PL-36)*

RECURRENCE — 2026-07-23 / session 2.  The same *shape* of failure recurred with a completely
                  different mechanism: not a dead agent, but a LIVE one whose RETURN CHANNEL failed
                  after the work was finished and on disk (PL-36).  The resolution was identical and
                  worked for the same reason: inventory the filesystem, evaluate the GATE, resume.
                  **Two independent mechanisms now produce "a workflow reported failure while the
                  deliverable sat complete on disk."**  That makes the filesystem-inventory rule
                  general rather than specific to transport errors, and it is the strongest kind of
                  evidence this log records: independent convergence on the same lesson.

## PL-30 — A minimal repro can FALSELY REFUTE a real trap, which is worse than not testing at all
date / session:   2026-07-23 / session 1 (bootstrap v1.0 first field test)
trigger:          Testing the bootstrap's own §IV.8 claim that `ZONE_FILLER.Fill()` segfaults when called in
                  the process that built the board. Following the bootstrap's `gen_test.py` technique —
                  "generate the smallest project that isolates it" — the first repro was
                  `CreateEmptyBoard()` plus one bare `ZONE` with a hand-appended outline, filled in-process.
                  **It survived and returned `True`.** Read literally that refutes a documented trap on the
                  current toolchain, and the obvious next action is to write "does not reproduce on KiCad
                  10.0.3" into `ENVIRONMENT.md` and delete `fill_zones.py` as obsolete ceremony. Re-testing
                  against the REAL `gen_pcb.build()` path — same fill call, but on a board whose footprints
                  had been loaded from a library in that process — **segfaulted, exit 139**. The trap is
                  real; the reduction had removed the very subsystem (footprint/library IO) that makes it
                  fire.
resolution:       Kept `fill_zones.py` as a separate process. Recorded BOTH results in `ENVIRONMENT.md`
                  §3.1 — including the survival of the reduced case, because "the minimal version passes"
                  is the finding a future session will otherwise rediscover and misread the same way.
bootstrap Δ:      Amend §IV `gen_test.py (technique)` and §V.8: "**Minimal repro is a tool for CONFIRMING a
                  hypothesis about a mechanism, not for REFUTING the existence of a defect.** A reduction
                  that fails to reproduce proves only that the removed elements mattered — never that the
                  defect is absent. Reduce toward the bug from a case that DOES reproduce, never outward
                  from one that does not; when a reduced case passes, the required next step is to re-add
                  elements until it fails and identify which one is load-bearing. **A documented trap may
                  only be retired by reproducing the ORIGINAL failing configuration and showing it now
                  passes.**" Also add to Part 0 evidence discipline: `[verified-run]` on a simplified
                  stand-in is not `[verified-run]` on the real path — say which one you ran.
scope:            G
status:           logged

## PL-31 — Tool-to-runtime version coupling, and the `PATH` entry that is present but wrong
date / session:   2026-07-23 / session 1 (bootstrap v1.0 first field test)
trigger:          The bootstrap's stack line reads "FreeRouting 2.2.4 + Temurin JRE", which implies any
                  Temurin will do. FreeRouting 2.2.4 (build 2026-05-13) is compiled to **class file version
                  69 = Java 25**. This machine has three JREs: `java` on `PATH` is **Oracle Java 8**
                  (`1.8.0_491`) and dies with `UnsupportedClassVersionError`; **Temurin 21** also dies
                  (class version ≤ 65); only **Temurin 25** runs it. The sharp edge is that the `PATH` entry
                  is not merely absent but present and wrong — `java -jar ...` then produces a confident,
                  specific-looking error that reads like a corrupt jar rather than a runtime mismatch, and
                  the bootstrap's "nothing KiCad is on PATH → use absolute paths" discipline was never
                  extended to non-KiCad tools. Separately, `--help` is **not** a valid FreeRouting argument:
                  it logs `Unknown command line argument: --help` and then launches anyway, so it is not a
                  usable route to flag discovery. The dead-proxy workaround does behave as documented
                  (`ConnectException` at +0.13 s, then aggregated hourly).
resolution:       Recorded the exact working JRE path and invocation in `ENVIRONMENT.md` §4, with both
                  failing JREs named so nobody re-tests them.
bootstrap Δ:      Part III: pin the runtime, not just the tool — "FreeRouting 2.2.4 requires **Java 25**
                  (class file v69); Temurin 21 is NOT sufficient." Generalize the absolute-path rule beyond
                  KiCad: "**Never invoke a build-chain tool through a bare `PATH` name.** A `PATH` entry
                  that exists but is the wrong version fails with an error describing the artifact rather
                  than the runtime, which sends you to debug the wrong thing. Record the absolute
                  runtime path for every external tool in `ENVIRONMENT.md` next to the version proven
                  against it." Add: "`--help` is not guaranteed to be a safe probe — some tools treat an
                  unknown flag as a warning and proceed to run."
scope:            G
status:           logged

## PL-32 — Exit-code hygiene: the flag that lets a check fail, and the pipe that hides a crash
date / session:   2026-07-23 / session 1 (bootstrap v1.0 first field test)
trigger:          Two independent ways an exit code lied, in one session.
                  (1) `kicad-cli pcb drc` exits **0 whether or not it finds violations** unless
                  `--exit-code-violations` is passed. A session or CI step that runs bare `pcb drc` and
                  checks `$?` has built a check that cannot fail — precisely the structural blindness
                  Principle 11 is about, wearing the costume of a passing gate.
                  (2) While testing the segfault, the command was piped through `grep` to filter KiCad's
                  wxWidgets banner noise: `python.exe -c "..." 2>&1 | grep -v "duplicate image handler"`.
                  In POSIX shells `$?` after a pipeline is the status of the **last** command, so the
                  segfaulting Python reported `EXIT=0` via grep's success. The crash was visible only as
                  *missing stdout* — the "SURVIVED" line simply never printed — and was first misread as a
                  quiet pass. Re-running without the pipe surfaced `Segmentation fault ... 139`.
resolution:       Documented `--exit-code-violations` as mandatory in `ENVIRONMENT.md` §2/§3.2. For exit
                  codes under test, redirect to files and read back (`cmd >out 2>err; echo $?`) rather than
                  piping, or use `${PIPESTATUS[0]}`.
bootstrap Δ:      Add to Part III (shell discipline) and §V.6 (blind-instrument table): "**Before quoting an
                  exit code, prove the command CAN return non-zero.** Many CLIs report findings on stdout
                  while exiting 0 by default — `kicad-cli pcb drc` requires `--exit-code-violations`. Verify
                  by running the tool once against deliberately-broken input and confirming non-zero exit; a
                  check never observed failing is not a check (cf. PL-14 — same principle, applied to vendor
                  tools rather than your own)." And: "**Never pipe a command whose exit status you are
                  testing.** `$?` after a pipeline is the last stage's status, so filtering noise through
                  `grep` converts a segfault into a silent pass."
scope:            G
status:           logged

## PL-33 — A document that CLAIMS to reproduce a run cannot be checked; generate it FROM the run
date / session:   2026-07-23 / session 2
trigger:          `docs/NUMBERS_PROBE.md` was written ALONGSIDE `hardware/hvctl/numbers_probe.py`,
                  not FROM it. The two drifted silently and undetectably: the document quoted a
                  141-assertion run, a five-class x two-family parameter sweep, and a "Part C --
                  Verbatim probe output" block that no longer matched what the probe printed. The
                  document even carried the phrase "Pasted unedited", which is a claim no reader
                  can verify and no tool was checking.
                  This is exactly PL-12 (generated artifacts are build outputs) applied to PROSE
                  rather than to CAD -- and it was missed because a `.md` file does not look like a
                  build artifact.
resolution:       Wrote `hardware/hvctl/gen_numbers_probe_doc.py`: zero-arg, stdlib-only. It RUNS
                  the probe, refuses to write unless it exits 0, runs it a SECOND time and refuses
                  unless the two are byte-identical, embeds stdout verbatim, then RE-READS the file
                  it wrote and byte-compares the embedded block against the capture. The document
                  now opens with "THIS FILE IS GENERATED. DO NOT EDIT IT."
                  Its acceptance check uses an INDEPENDENT source of truth in the strict sense: it
                  counts `[PASS]`/`[FAIL]` lines by REGEX OVER THE STREAM and compares that against
                  the counts the probe PRINTS from its own list of objects. Two countings of one
                  run, by two different mechanisms. Mutation-tested 4/4: a failing probe -> exit 1,
                  a non-deterministic probe -> exit 1, a probe that MISREPORTS its own verdict
                  count -> exit 1, an unformatted percent-specifier reaching the output -> exit 3.
bootstrap Δ:      Add to Part I: "**If a document quotes a tool's output, GENERATE the document
                  from the tool.** The moment a document says 'pasted unedited' or 'verbatim', it
                  has made a claim no reader can check and no tool is checking. Emit it from a
                  generator that runs the tool, refuses to write on a failing or non-deterministic
                  run, and re-reads its own output to prove the embedding. Treat `.md` files that
                  quote tool output as build artifacts -- they are, and they do not look like it."
                  Also: "**Split generated numbers from hand-written judgement into two files.**
                  When a document is made generated, any hand-written prose in it has no generated
                  source and will be silently deleted. Move it out FIRST, deliberately, and say
                  where it went."
scope:            G
status:           logged

## PL-34 — A duplicated constant hides from every assertion; only a mutation finds it
date / session:   2026-07-23 / session 2
trigger:          Eight mutations were applied to input constants of the numbers probe to prove its
                  assertions can fail. Seven were caught. **M8 -- driving the monitor divider's
                  top-leg element count from 10 to 1, i.e. putting the full 1000 V across a single
                  1206 chip resistor -- SURVIVED at exit 0 with 71/71 passing.**
                  Two defects were behind it, and neither changed a single printed number, so
                  neither was findable by reading the output:
                  (1) the element count existed TWICE -- `N_TOP_ELEMENTS = 10` consumed by the error
                  budget (where the voltage-coefficient term goes as 1/N) and a separate literal
                  `n_div = 10` consumed by the string geometry (which sets per-element voltage).
                  Perturbing one moved the error budget while the geometry screens went on
                  evaluating the other. The two consumers could disagree indefinitely and every
                  assertion would still pass.
                  (2) a whole CLASS of check was missing on one path: the bleed string was screened
                  against its element's WORKING-VOLTAGE RATING, the divider string only against
                  PACKAGE CLEARANCE. A rating and a clearance are different constraints, and a tool
                  that checks one is not checking the other.
resolution:       One definition of the element count, one row of the parts table supplying BOTH
                  package and rating (`res_option()` raises rather than falling back, so a renamed
                  part is a structural failure), plus two new assertions: the divider element stays
                  inside its derated rating, and the geometry and the error budget use the SAME N.
                  M8 now fires 2 assertions. Harness kept in-repo as
                  `hardware/hvctl/mutation_test_numbers_probe.py`, zero-arg and re-runnable.
                  A third defect fell out of the same pass: the VSET fail-safe pull-down was quoted
                  at 1 kOhm in one subsection while the recommendation fitted TWO in parallel and
                  the sink-current calculation assumed the pair -- three different R_pd in one
                  section. Now one derivation, both numbers printed, and the single-fault table
                  distinguishes "one of the pair opens" (9.2 %, covered) from "the pull-down was
                  never duplicated" (101 %, a design choice and not a fault).
bootstrap Δ:      Add to §V (verification): "**Mutation-test the arithmetic, not just the parser.**
                  Perturb INPUT CONSTANTS one at a time and require each to flip at least one
                  assertion. A surviving mutation is not a nuisance -- it is the only cheap way to
                  find a constant that is defined twice, or a class of check that exists on one
                  code path and not on its sibling. Neither defect changes any printed number, so
                  neither is findable by reading the output, and both are invisible to a test that
                  only compares outputs against expected values."
                  And: "**A constant consumed by two subsystems must be defined once.** If the
                  error model and the geometry model each carry their own copy, they can disagree
                  forever and every assertion will still pass. Assert that the consumers agree."
scope:            G
status:           logged

## PL-35 — "Independent cross-check" is a claim that must itself be attacked
date / session:   2026-07-23 / session 2 (closing a session-1 refutation)
trigger:          Session 1's numbers probe asserted four checks of the form
                  `IPC-2221 B2(V) == IEC PD2 printed-board creepage(V)` and called their agreement
                  "the strongest evidence in this section" and "the transcription's only internal
                  evidence". Above 500 V both expressions reduce to `0.005*V` IDENTICALLY, so the
                  four assertions could not fail for ANY input. Worse than merely uninformative:
                  the check is INVARIANT UNDER ANY COMMON RESCALING of both columns -- and both
                  columns had been transcribed from the SAME web page, so a common-mode
                  transcription error is precisely the failure it was claimed to exclude.
resolution:       DELETED, not repaired, and **no replacement cross-check was invented** -- there
                  was nothing honest to put there. In its place the probe now PRINTS THE PROOF that
                  the old check had no discriminating power: a table showing it still "passes" when
                  both columns are scaled by 0.25x, 0.5x, 1x, 2x and 10x, with an assertion over
                  that table. The constants are tagged `[unverified-primary]` and the section opens
                  by saying no internal evidence supports them.
                  A second tripwire was added for a related flag: the suspected mis-transcribed IEC
                  column asserts that the SUSPICIOUS DUPLICATION IS STILL PRESENT, so the assertion
                  FIRES when someone corrects the table -- forcing the document to be updated rather
                  than letting a silent fix orphan the flag.
bootstrap Δ:      Add to §V.6 (blind-instrument table): "**Before calling two sources an independent
                  cross-check, prove the check can FAIL.** Feed it a deliberately wrong input. If
                  both sides are algebraically the same function, or share a provenance, agreement
                  is a tautology and 'they agree exactly' is evidence of NOTHING. Test specifically
                  for invariance under a COMMON-MODE error -- the error two sources sharing one
                  origin will actually make. When such a check is found, DELETE it and say so; do
                  not invent a replacement to fill the hole, because an unverified constant with an
                  honest tag is safer than one with fabricated evidence."
                  And: "**When you flag a defect you are deliberately NOT fixing, leave a TRIPWIRE
                  that fires when someone fixes it.** Assert the defect is still present. Otherwise
                  the eventual correction silently orphans every document that cites the flag."
scope:            G
status:           logged

## PL-36 — An agent's RETURN CHANNEL is a failure mode of its own; keep returns small and treat the artifact on disk as the deliverable
date / session:   2026-07-23 / session 2
trigger:          A Phase-2 agent authored `hardware/hvctl/board_spec.py` — ~134 kB, 441 components,
                  321 nets, running clean at exit 0 with every domain assertion passing — wrote it to
                  disk, and then **failed on its structured return. Five retries, no valid output.**
                  The orchestration layer treated the agent as failed and **aborted the whole
                  workflow.** Nothing was wrong with the work. The reporting channel died.
                  The failure has a specific shape worth naming: **the agents most likely to blow a
                  large structured return are exactly the agents that just wrote a large artifact**,
                  because the same instinct that produces a thorough file produces a thorough
                  summary — component inventories, per-assertion results, deviation lists — and a
                  return schema is a much less forgiving container than a file. The return is also
                  the ONLY part of the work with no retry semantics that preserve partial progress:
                  a file half-written can be finished, a return half-emitted is nothing.
                  This is PL-29's shape with a different mechanism. PL-29 was a DEAD agent leaving a
                  half-built gate. This is a LIVE agent leaving a FULLY-built gate that nobody was
                  told about. Both produce "the workflow reported failure while the deliverable sat
                  complete on disk", and both are resolved the same way.
resolution:       Recovered by ignoring the report and inventorying the filesystem: `board_spec.py`
                  was present, ran at exit 0, and its self-reported census (441/321/44) was the real
                  one — the numbers being carried forward in the orchestrator's own brief (419/314/42)
                  were stale, which is a second, quieter consequence of a lost return.
                  Two standing rules adopted for the rest of the project:
                    (1) **Returns are receipts, not reports.** An agent that writes files returns
                        paths, a one-line status, and at most a handful of short findings. Everything
                        else goes IN the file. If a return would be long enough to be worth reading
                        on its own, it should have been a file.
                    (2) **Never conclude work was lost from a failed return.** Inventory the
                        filesystem first, every time, and evaluate the GATE (does the artifact exist,
                        does it run, what does it self-report) rather than the ACTOR.
bootstrap Δ:      Add to Part 0.1 (the "when a session or agent dies" section PL-29 creates):
                  "**A failed RETURN is not a failed RUN.** Distinguish three states: the work never
                  started; the work started and is partial; the work COMPLETED and only the report
                  was lost. Only a filesystem inventory can tell them apart, and the third is
                  common — an agent that has just written a large artifact is precisely the agent
                  most likely to overrun or malform its structured return."
                  And: "**Bound every agent's return.** State an explicit budget in the task — file
                  paths only, plus N findings of M characters — and say plainly that THE FILE ON
                  DISK IS THE DELIVERABLE and the return is a receipt. An agent asked for both a
                  large artifact and a large structured summary has been given two deliverables and
                  will spend its care on the wrong one."
scope:            G
status:           logged   *(reinforces PL-29 — independent convergence on the filesystem-inventory rule)*

---

## PL-37 — A logged lesson does not propagate itself; check the log against the artifact that CONSUMES the lesson
date / session:   2026-07-23 / session 2
trigger:          PL-04 was written in session 1. It states that the shipped KiCad demo corpus is a
                  **stale oracle**, gives the correct procedure (`kicad-cli sch upgrade --force` on a
                  copied demo), names the right answer (`20260306`), and its own bootstrap amendment
                  ends with the instruction *"Record it in `docs/ENVIRONMENT.md`."*
                  In session 2, `docs/ENVIRONMENT.md` was written — **recording `20250610`, read from
                  the shipped demos.** The exact error, in the exact document the entry told us to
                  create, one session after the entry was written, by an actor that had the log
                  available. The lesson was logged and did not arrive.
                  Two things made it possible, and both generalise well beyond this repo:
                    (a) **A pipeline log is written in the voice of the session that hit the problem,
                        not in the voice of the session that will need it.** PL-04's title is about a
                        stale bootstrap and a stale oracle; nothing in it is indexed under "things to
                        get right when writing ENVIRONMENT.md". An entry filed by CAUSE is invisible
                        to someone searching by TASK.
                    (b) **The fact carried a `[verified]` tag.** It had been read out of a real file
                        with a real parser, which is exactly what `[verified-artifact]` means. **The
                        tag records that an instrument ran, not that the RIGHT instrument ran** — and
                        a wrong-instrument reading is far more dangerous than an untagged one,
                        because it survives review.
resolution:       Logged as a RECURRENCE on PL-04 rather than a duplicate entry, per this file's
                  deduplication rule, and the recurrence text adds the sharper form of the lesson:
                  **reading a vendor-shipped EXAMPLE is a weaker instrument than making the vendor
                  TOOL WRITE the artifact.** An example ships once and then ages; the tool is what
                  you actually depend on. Where a fact is obtainable either way, make the tool emit
                  it, and **record the COMMAND, not the value** — a recorded command re-derives
                  itself on the next machine and the next release; a recorded value silently rots.
bootstrap Δ:      Add to Part 0: "**Every entry in the pipeline log must name the ARTIFACT it will
                  be needed for, not only the problem it came from.** Add a `consumed by:` line —
                  the file, gate or step where the lesson has to land. Before writing any artifact
                  named in a `consumed by:` line, re-read those entries. A log filed only by cause
                  is unsearchable by the person who needs it, and a lesson nobody retrieves is a
                  lesson nobody learned."
                  And to §V.6 (the blind-instrument table): "**`[verified]` records that an
                  instrument ran, not that the right instrument ran.** For every verified fact, also
                  record WHICH instrument and WHAT it is structurally blind to. 'I read it out of a
                  file the vendor shipped' and 'I made the vendor's tool write it' both produce
                  `[verified-artifact]`, and only one of them is current."
                  And: "**Prefer facts that re-derive themselves.** Where a constant can be obtained
                  by running a command, record the COMMAND. A recorded value is a snapshot with no
                  expiry date on it."
scope:            G
status:           logged

---

## PL-38 — A mutation test that edits the real source in place will corrupt it; and read-only agents write read-write tools
date / session:   2026-07-23 / session 2
trigger:          After the verification workflow reported 19/19 agents complete with no errors, the
                  orchestrator re-ran `board_spec.py` as a matter of routine. **Exit 1, two failures:**
                      net VIN_P_UNUSED has 1 connection(s); every net needs >= 2   [FB1.2]
                      SA-6: VIN_P is not fed through its ferrite FB1
                  `FB1` read `VIN_P_SW -> VIN_P_UNUSED` where its mirror `FB2` correctly read
                  `VIN_N_SW -> VIN_N`, i.e. the POSITIVE module's +VIN no longer passed through its
                  interlock load switch — a safety-relevant break in the exact element the interlock
                  depends on.
                  **The first diagnosis was wrong, and the way it was wrong is the point.** The obvious
                  reading was "the packaging agent edited the file, claimed 're-ran clean, exit 0', and
                  the claim was false". That reading was written up and had to be retracted, because
                  grepping for the bad string found it *verbatim* in a sibling file:
                  `mutation_test_board_spec.py`, as MUTATION `sa6`, whose stated purpose is to prove
                  SA-6 can fail. The tool applies each mutation **in place to the real
                  `board_spec.py`**, runs it, and writes the original back:
                      io.open(path,"w").write(base.replace(old,new,1)); run(); io.open(path,"w").write(base)
                  wrapped in `try/finally`. So the leaked mutation was not a wiring error by any agent.
                  It was this tool failing to restore. `try/finally` covers an ordinary exception but
                  NOT a process kill — and, decisively, it is **not concurrency-safe**: the orchestrator
                  had fanned out **three independent skeptics on the same claim in parallel**, and any
                  two of them running this tool against the one shared file race — B reads an
                  already-mutated file as its "baseline", A restores, B later writes its corrupted
                  baseline back, and the mutation becomes permanent.
                  Three lessons, in ascending order of generality.
                  (1) The safety assertion WORKED. SA-6 exists precisely to catch "+VIN reaches a module
                  without passing the interlock element" and it fired on the first real instance. Had
                  the leaked mutation instead been one the assertions do NOT cover, it would have
                  corrupted the golden netlist silently — a verification tool whose failure mode is
                  undetectable corruption of the artifact it verifies.
                  (2) "You are READ-ONLY, do not modify any file" constrains the AGENT, not the TOOLS
                  THE AGENT WRITES. A skeptic told to verify that assertions can fail will reach for
                  mutation testing, because that is the correct technique — and mutation testing is
                  inherently a write operation. The instruction and the task were in direct conflict and
                  nobody noticed, including the orchestrator who wrote both.
                  (3) The defect was found only because the orchestrator re-ran the tool instead of
                  believing a clean report — the same reflex that recovered Phase 0 (PL-29) and caught
                  the stale schema version (PL-04). Three recoveries this project, one reflex.
resolution:       Fixed in the GENERATOR, one net name, per CLAUDE.md rule 1 — never patch the
                  artifact. Re-ran: exit 0; SA-1..SA-13 and domain assertions (a)/(b)/(c) all hold.
                  The original misattribution to the packaging agent was retracted rather than left
                  standing, since a wrong causal story in the log would send the next session to
                  audit the wrong thing.
                  Then the DEFECT CLASS was retired, not just the defect (bootstrap Principle 13):
                  `mutation_test_board_spec.py` now copies the tree to a private
                  `tempfile.mkdtemp()` per invocation, mutates and runs THERE, deletes it, and ends
                  with a guard that re-reads the real `board_spec.py` and aborts if its bytes changed.
                  Verified `[verified-run]`: **35/35 mutations caught, exit 0**, and the real
                  `board_spec.py` SHA-256 is byte-identical before and after the run
                  (`a5b37a9b4ebaae1e`). Concurrent invocations can no longer collide, and a process
                  kill can no longer leave a mutation behind, because nothing outside the sandbox is
                  ever opened for writing.
bootstrap Δ:      Add to Part IV as a convention: "**A mutation test must never mutate the real
                  artifact.** Copy the source tree to a private temp directory, mutate and run THERE,
                  and delete it. `try/finally` restoration is not sufficient: it does not survive a
                  process kill, and it is not safe under concurrency — two agents mutating one shared
                  file will race and can make a mutation permanent. The failure mode of an in-place
                  mutation tester is silent corruption of the very artifact it certifies."
                  Add to Part VI (lanes/sessions): "**'Read-only' is a property of a TOOL, not a
                  promise from an agent.** An agent instructed not to modify files can still author and
                  run a tool that does — and verification techniques (mutation testing, fault
                  injection, upgrade round-trips) are write operations by nature. When fanning out
                  concurrent verifiers over a shared tree, give them worktree isolation, or require
                  that any tool they write operate on a private copy. Verify the invariant by checking
                  the tree afterwards, not by asking."
                  And to Part II: "**After any fan-out completes, re-run the executable gates before
                  reading the reports.** Agents can complete successfully and still leave the tree
                  broken."
scope:            G
status:           logged
