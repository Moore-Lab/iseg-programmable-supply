# STATUS — 2026-07-23, end of session 2

**Position: G0 is SIGNED OFF. Phase 2 is drafted. Standing at GATE G1 — and G1 is NOT ready to
sign.** The gate package is `docs/G1_REVIEW.md`.

---

# ⛔ 1. STOP-THE-LINE FINDINGS — read before using any document in this repo

Six load-bearing claims were put to **three independent skeptic sessions each, every one tasked with
REFUTING rather than reviewing.** Coverage was complete: **18 skeptic reports, 3 per claim, no
inconclusive claim, no coverage gap.**

## **ALL SIX WERE REFUTED. NOT ONE SURVIVED.**

| # | Claim | Skeptics | Verdict |
|---|---|:-:|---|
| 1 | The physical mode switch specified in `COMBINER_DESIGN.md` is a real, obtainable part genuinely rated for this application | **3/3 refuted** | ❌ **NO PART IS SPECIFIED AT ALL** |
| 2 | The mode-aware interlock makes the forbidden state unreachable in hardware, in both modes, in every ESP32 state | **3/3 refuted** | ❌ **one welded HV reed reaches it** |
| 3 | The design is safe if a human moves the mode switch at the worst possible moment | **3/3 refuted** | ❌ **the derived margin is not met, by 2×–19×** |
| 4 | The `VSET` clamp makes commanding over-range impossible in hardware, and its own failure modes are safe | **3/3 refuted** | ❌ **the repo's own probe says otherwise** |
| 5 | The independent monitors load acceptably, beat `VMON`, and are electrically independent | **3/3 refuted** | ❌ **all three legs fail** |
| 6 | `board_spec.py`'s domain assertions genuinely can fail, and its pin numbering agrees with symbol and footprint | **2/3 refuted** | ❌ **four escape routes; footprint half unchecked** |

> ## THESE ARE STOP-THE-LINE FINDINGS FOR A 1 kV INSTRUMENT.
>
> G0-A3 gave **both** the serial link **and** the network **full write authority**, over a
> recommended read-only-network default, and recorded explicitly that *"the hardware interlock,
> hardware `VSET` clamp and soft limits therefore carry the entire safety case."*
>
> **Two of those three are now refuted, and the third — the mode switch — has no part number.**
>
> **No layout. No procurement of the mode element. No G1 signature on the affected sections.**
> The corrections below now govern, and each is written into a **correction banner at the top of the
> owning design document.** Any document in this repo that still asserts a refuted claim in its body
> text is **wrong**, and the banner says so.

## 1.1 ❌ REFUTED — the mode switch is not a specified part, and the one MPN named is rated 28 V DC

**Owner: `docs/design/COMBINER_DESIGN.md` §3.6 — corrected in banner C-2.**

1. **The claim has no referent.** The BOM row for `SW1` reads *"3-position ceramic wafer switch …
   **or** the §3.7 link block — `[unverified-MPN]`, O-10 open"*, and §3.6 says *"Every MPN above
   stays `[unverified-MPN]`. No distributor page was read."*
2. **The one MPN floated as "the most likely answer" — Electroswitch `D4C0212N` — is real and stocked
   but NOT rated for this.** Three skeptics independently fetched the manufacturer's own catalogue
   PDF and extracted, verbatim: *"Make and break resistive load 1.5 amps @ 28 VDC; 0.5 amp @
   115 VAC"* and *"Dielectric Strength: 1,500 VAC between current carrying parts and ground."*
   Against SW-R3 (≥1000 V working, ≥2000 V proof, contact-to-contact **and** contact-to-frame) it
   fails all three: 1500 < 2000 proof; **no working voltage above 28 V DC anywhere in 63 pages**;
   **no contact-to-contact figure at any voltage**, so the 2 kV pole-to-pole case is unaddressed.
3. **§3.6's premise is factually wrong, twice.** It calls 28 V DC *"a current rating, not a standoff
   rating"* — the catalogue line is a voltage **and** current rating. And it claims the dielectric
   figure *"is much higher but must be obtained from the manufacturer"* — **it is published, in the
   free catalogue, and it is 1,500 VAC: lower than the requirement, not higher.**
4. **New hole, not in the document:** the *"use every fourth position"* fix **cannot rescue the
   rating**. The published figure is contact-to-**ground**, set by rotor/shaft/bushing geometry and
   unchanged by skipping contacts; the fix improves only contact-to-**contact** pitch.
5. Ross Engineering is real but spans **2 kV–450 kV** (not §3.6's "13–20 kV") and ships **one** SPDT
   aux contact against the **four** LV poles needed.
6. **The honesty check PASSES**, and this is worth recording: **SW-R8 forbids fitting a
   non-conforming switch**, O-10 is logged open, and §3.7 offers the link block as **co-equal** and
   *"may be the better answer"*. **No unsuitable part is forced by the document.**

**Action:** adopt **§3.7 Option B (guarded link block with a captive interlock key) as the
BASELINE**, unless a vendor supplies a contact-to-contact **DC working** spec ≥1000 V in writing.

## 1.2 ❌ REFUTED — the interlock: one welded HV reed reaches the forbidden state, and the machine proof never looks at pseudo-bipolar

**Owner: `docs/design/COMBINER_DESIGN.md` §1.3 / §7.5 — corrected in banners C-1 and C-1a.**

1. **The document contradicts itself.** §1.3's THEOREM says the forbidden state needs *"a weld on one
   of the two HV reeds **plus** a coincident second fault."* §7.5(c) and §8 **F-15** both say the
   weld **alone** suffices: `K1` welded at NO puts POS permanently on `OUT_A`, and the next NEG
   selection in pseudo-bipolar puts both modules on `OUT_A`. §7.5's own closing text says it:
   *"It remains reachable through a welded HV reed contact… which no contact-based topology can
   prevent."* **§1.3 is wrong by this document's own §7.5.**
2. **The executable proof is VACUOUS in the mode at risk.**
   `board_spec.py:assert_a_no_shared_output_node()` filters `if not (pp and pn): continue`, and
   `PERMIT_P · PERMIT_N ⇒ MODE_UNI` by construction, so **every pseudo-bipolar state is deleted
   before evaluation.** Three skeptics reproduced this against the file's own
   `reachable_states()` / `_adjacency()`: *"modes surviving the assertion-(a) filter = ['UNI']"*, and
   *"PB, K1=1 K2=1: `HV_POS`→`HV_OUT_A` True AND `HV_NEG`→`HV_OUT_A` True."*
   **The assertion cannot detect the F-15 weld it is nominally the proof against.**
3. **`S6`/`S7` — "one armature" — is a claim about a part nobody has bought**, and in the netlist the
   four LV poles land on **one 8-way header `J6`** with `COIL_FEED_P/N` on **adjacent pins 7/8**.
   A solder bridge there is an ordinary defect that welds `S7`.
4. **Doc/netlist divergence:** §6.1 lists `MODE_UNI` as *"`SW1` pole `S5`"*. In the netlist `S5`
   (`SW1E`) drives `MODE_B`, and `MODE_UNI` is a **74HCT08 output**. §7.5(b)'s *"three faults"* is
   therefore **two**.
5. **What SURVIVED every attack, and keeps its standing:** the **logic** half is sound. Floating
   inputs (duplicated 100 kΩ pull-downs, 74HCT on 5 V), ESP32 reset / unpowered / mid-boot, stuck-high
   gates, broken control lines, `(0,0)` and `(1,1)` aux decodes, the `K_S` transfer race, and the
   firmware-caching attack (`MODE_VALID` is combinational on the contacts; nothing the ESP32 drives
   reaches `MODE_A`/`MODE_B`) **all fail to break it.**

**Correct formulation, which is what §7.5 already says:** *unreachable through any electrical, logic,
firmware, network, driver or wiring fault, and through any single fault of the mode element;
**REACHABLE through a single welded HV reed — detected, not prevented.*** **G0 Q6 (detection vs
prevention) was never answered.**

## 1.3 ❌ REFUTED — the mode-switch timing margin is not met, and the residual protection is PROCEDURAL

**Owner: `docs/design/COMBINER_DESIGN.md` §3.5 / §3.8 — corrected in banner C-3.**

§3.5 derives its own requirement — **≥0.2 s bare, ≥1.0 s at the `C_load` limit** — and then satisfies
it with *"the operator's dwell in the SAFE detent … of order 100 ms even for a fast, careless turn"*
`[recalled]`, calling that *"a mechanical certainty"*.

- **100 ms is 2× short of the file's own bare-board figure, 10× short of its loaded figure, and
  ~19× short of `numbers_probe.py` §3.7's independently-budgeted 1.877 s.** The shortfall is
  reconciled **nowhere** in the file (three skeptics grepped for it).
- **Two skeptics recomputed the consequence for a FULLY CONFORMING switch:** at the documented
  `C_load` interface limit, 100 ms of SAFE dwell leaves **~620–800 V per module still standing as
  the HV poles make** — i.e. a hot make. §3.8 frames that as the consequence of a **non-conforming**
  switch; the arithmetic shows a conforming one reaches it too, on a fast turn, **with a cable
  attached**.
- **§3.8's consequence bound is correct and is what actually carries this case:** 1.5 mA into 20 kΩ
  = 30 mW steady; **no arc is physically available at 0.75 mA**; peak bounded by `R_M1` to 200 mA /
  ~11 mJ against a 350 mJ threshold. **This is a contact-plating and weld risk, NOT an energetic or
  shock hazard.** But a welded HV contact is precisely the topology's admitted unremovable weakness
  (§1.2 above).
- **The other thing carrying it is MODE-17: powered down, cables off ⇒ `C_load` ≈ 0 ⇒ 100 ms
  suffices. That makes the residual protection PROCEDURAL, not structural**, contrary to §3.5's own
  claim.

**Parts that SURVIVED and are not re-attacked:** *between-detents is genuinely safe and structural*
(all seven poles open in SAFE; `MODE_VALID` = XOR with positive decode of both modes; duplicated
pull-downs so a broken aux reads 0 — proved exhaustively by `assert_a_mode_decode()`); *a runtime
mode change forces HV off in hardware in <100 ns, relays released in 6 ms, firmware only logs — never
a graceful ramp-down*; and *`OUT_B` in pseudo-bipolar is NOT floating* — three independent
terminations.

## 1.4 ❌ REFUTED — the `VSET` clamp is necessary but NOT SUFFICIENT, and one fault is worse than no clamp

**Owner: `docs/design/SETPOINT_PATH.md` — corrected in banner S-1…S-7.**

**This repo's own probe refutes the claim.** `numbers_probe.py` §5.3 prints *"NO candidate makes
over-voltage mathematically impossible"*; §5.4 asserts *"[PASS] no VSET clamp survives every single
fault"*; §5.6 concludes *"the VSET clamp is a necessary but NOT SUFFICIENT safety element."*

- **The headline "+0.061 % (1000.6 V)" divides by a NOMINAL Vref.** The datasheet says
  **Vref = 2.5 V ±1 %**. At **2.475 V** the same clamp ceiling commands **1010.7 V = +1.07 %, ~17×
  the quoted figure**; the probe independently rates it **100.30 %**. §10 already uses 2.475 V —
  **the file is internally inconsistent.** ⇒ **Hardware alone does not bound the output to ≤ Vnom.**
  ≤ Vnom comes only from the **98 % firmware code clamp** — **and G0-A3 put firmware inside the
  untrusted boundary, which is the exact thing the hardware clamp existed to remove.**
- **A single fault DOES put 3.3 V on `VSET`:** a solder bridge, **1320 V**, *"not preventable by the
  set path"*. Mitigated by a **layout keep-out** and **detected** by `U7` — not prevented.
- **One modelled fault is WORSE than no clamp:** reference shorted to 5 V ⇒ **201 % of Vnom =
  2012 V**, against 1320 V un-clamped. Its only cover is `U5`, whose stuck-HIGH mode the file itself
  calls **undetectable in service**.
- **One un-mitigated open:** a break between the pull-down and pin 2 ⇒ **1000 V**, prevented by
  nothing.
- **Power-on / supply-ramp behaviour is a stated `[BLIND SPOT]`** in both instruments; the DAC's
  power-on-reset-to-zero state is `[recalled]`.
- **The clamp part has no part number** (`**UNSELECTED RRIO dual**`).

**What SURVIVED:** the **Vref-pin attack fails** — Table 4 lists exactly seven pins and §2.3 already
**dropped** candidate D rather than inventing one; the **duplicated 500 Ω pull-down** genuinely holds
a clamp-open failure at **47.6 V**; and commanded over-range **is** structurally bounded by `U4`'s
own rail.

## 1.5 ❌ REFUTED — the monitors: incomplete load sum, conditional accuracy, and not independent

**Owner: `docs/design/MONITOR_AND_BLEED.md` — corrected in banner M-1…M-4.**

- **LOADING.** §8 *did* sum the parallel strings (**11.40 %**) — that attack fails. But it **omits
  `BLDX`/`BLDM`**, the two 400 MΩ mode-switch stub bleeds `board_spec.py` builds, which in
  pseudo-bipolar **both load the active module**: the real figure is **12.40 %**. The document never
  mentions those nets (zero grep hits); the probe still asserts on **11.00 %**; `board_spec.py`
  asserts **no load budget at all**. Under 15 % on every reading — **but the published number is
  wrong and the assertion was passing on an incomplete sum.** With the `[ASSUMED]` ~20 MΩ internal
  module bleeder the total is **21.40 % (22.40 % with the stubs), which BREACHES the probe's own
  ≤15 % assertion** — and §8 calls that *"acceptable — no change"* without noting the breach.
- **ACCURACY.** "Beats the 10 V `VMON`" holds **only** with the driven guard, whose **100× factor is
  `[ASSUMED]` and never measured** — this file calls it *"the single least-supported number"*.
  **Unguarded on bare FR-4 the monitor is 20.0 V: worse than `VMON`.** Including the 5.0 V long-term
  drift §4.4 excludes gives **~2×**, not 6.6× and certainly not the **31×** the probe still prints.
  Working-voltage ratings (1206 @ 800 V, 2512 @ 1500 V) are `[ASSUMED]` with **no MPN**, so they
  cannot be checked against a real part at all. **New:** at the 2012 V fault the monitor is
  deliberately given headroom to read, but the co-located 2512 elements then sit at **1006 V against
  a 750 V 50 %-derate limit** — never analysed.
- **INDEPENDENCE.** §5.4 deliberately makes `COLD` = S3 window **AND** a comparator on the S2 tap —
  **a dependency**, which the file admits needs the **frozen** SA-8 reworded; `board_spec.py` **D-2
  declines to build it**, so §10 rows 10 and 12 are **unmitigated as built** (one open S3 element
  silently doubles the COLD threshold to ≈±74 V, **above the 60 V touch limit**). Both offset legs
  share **one `REF5025`** and the independence assertion passes only by **whitelisting**
  `VREF_2V500`. **One `OPA2192` (`UGD`) drives BOTH guard rings** — a single-package common mode with
  no row in §10. **And one open monitor element blinds the monitor AND pushes the OVP trip to
  ≈2100 V**, so the 1320 V `VSET` fault would no longer trip OVP.

## 1.6 ❌ REFUTED (2/3) — the netlist assertions fire, but four escape routes exist

**Owner: `hardware/hvctl/board_spec.py` — corrected in deviations D-7…D-10.**

**The assertions are NOT vacuous.** 13/13 in-scope mutations fired, naming the exact state and mode
— relay/switch throws onto the wrong node, gate rewires, every bleed detached, monitor/`VMON` chain
merges, an ESP32 pin placed on `MODE_A`. **That is a real, working checker.** And the **symbol** half
of the pin-numbering claim **holds**: three skeptics independently parsed `lib/iseg.kicad_sym` and
`lib/iseg.pretty/iseg_APS_THT.kicad_mod` with their own parsers and confirmed pads 1–7 = spec pins,
both directions.

**But four things escape a completely clean `check()`:**
1. **`assert_a_mode_origin()` has three bypasses** — it allow-lists `R_LV`/`HDR*`/`TP`/`C_LV` without
   following the far end; it skips every `74*` part with a comment that is **false** (only 8 of 20
   are in `LOGIC`, so 12 parts' **outputs** are silently transparent); and `esp_out` is a
   **hard-coded 6-name list** while ~25 other ESP32 nets are excluded. Five independent mutations
   putting the mode permissive under firmware control all return `check() == []`, exit 0.
2. **`hv_energisable_nets()` is NOT derived** — it is parameterised by two hand-lists, so an HV net
   outside both is invisible and an **unbled HV net passes assertion (b)**.
3. **`assert_c_monitor_independence()` never compares monitor A against monitor B.** Merging them
   passes.
4. **`board_spec.py` never opens a `.kicad_mod`** (`grep -c` = 0), and **11 parts name footprints
   that exist nowhere** — including **`K1`/`K2`, the two HV routing relays**, which therefore have no
   footprint for their pin numbering to agree *with*. `PIN_MAPS.md` flags only `K1`–`K4`.

**Also corrected here: the counts circulating in this session's briefs were STALE.**
`board_spec.py` reports **441 components / 321 nets / 44 TIER-C**, not 419 / 314 / 42.

---

## 1.7 Coverage statement

**18 skeptic reports, 3 per claim on all six claims. No claim received fewer than 2 reports, so
there is no `inconclusive` verdict and no coverage gap in this round.**

What *is* a coverage gap, stated so it is not read into a silence: **no claim about the power tree,
the comms surface, the state machine or the connectors was put to a skeptic at all.** Those parts of
`CONTROLLER_AND_POWER.md` (131 kB) are **one agent's word, unchallenged.**

---

## 2. Where the project actually is

| Phase | State |
|---|---|
| **Phase 0** — environment proof | ✅ **CLOSED.** `docs/ENVIRONMENT.md` exists; 24 gerber layers + `.gbrjob` + drill; fill (2 zones, 2178.23 mm²); `pcb drc` 0/0; 3D render 1568×872, 136 distinct colours. |
| **Phase 1** — scope and frozen numbers | ✅ done; `NUMBERS_PROBE.md` rewritten and now **generated from the probe's printed output** (74 assertions, 74 pass, exit 0, byte-identical across runs, 8/8 mutations caught). |
| **GATE G0** | ✅ **SIGNED OFF 2026-07-23.** A1–A5 frozen. **Q3, Q5 and Q6 were never answered.** |
| **Phase 2** — golden netlist, libraries, pin maps | ⚠ **drafted, not reviewed.** `board_spec.py` runs clean; four design documents written; `PIN_MAPS.md` generated. |
| **GATE G1** | 🔴 **NOT READY.** Package is `docs/G1_REVIEW.md`. Six refutations must be dispositioned first — see §1 and `G1_REVIEW.md` §7. |
| Phases 3–7 | not started |

### 2.1 On disk, new this session

| Path | What |
|---|---|
| `docs/ENVIRONMENT.md` | the verified toolchain; **the Phase 0 gate** |
| `docs/design/COMBINER_DESIGN.md` (~96 kB) | HV routing + mode-aware interlock — **carries banner C-1…C-5** |
| `docs/design/SETPOINT_PATH.md` (~69 kB) | `VSET` clamp and set-point path — **carries banner S-1…S-7** |
| `docs/design/MONITOR_AND_BLEED.md` (~79 kB) | independent monitors + discharge — **carries banner M-1…M-4** |
| `docs/design/CONTROLLER_AND_POWER.md` (~131 kB) | ESP32, power tree, comms, connectors — **§9.2 SUPERSEDED banner** |
| `hardware/hvctl/board_spec.py` (~137 kB) | **the golden netlist.** 441 comps / 321 nets / 10 netclasses / 12 HV strings / 44 TIER-C. Exit 0. Deviations **D-1…D-10**. |
| `hardware/hvctl/numbers_probe.py` (~151 kB) | 74 assertions, 74 pass, exit 0 `[verified-run]` |
| `docs/PIN_MAPS.md` (~116 kB) | **generated**; the human pin-map review surface |
| `docs/NUMBERS_PROBE.md` | **generated from the probe's own output** (PL-33) |
| **`docs/G1_REVIEW.md`** | **new — the G1 gate package** |
| **`docs/BENCH_MEASUREMENTS.md`** | **new — the procedure for the five things a human must measure** |

---

## 3. What is verified, and by which instrument

| Claim | Instrument | Structurally cannot see |
|---|---|---|
| Module pin map `1 +VIN · 2 VSET · 3 GND · 4 /ON · 5 VMON · 6 HV · 7 GND` | 3 skeptics (s1) + 3 more this session reading p.9 Table 4 directly: verbatim text, Figure 1's own top view, the 2019 v2.1 revision, three parsers, a built board's footprint | Whether iseg's table is right. **No physical module has been probed.** The source table is captioned *"Technical data: options and order information"* — this vendor document **does** contain editorial errors. |
| Footprint geometry incl. the **+0.60 / +0.23 mm** body offset, correct handedness | 2 independent pixel-metrology passes agreeing to 0.02 mm; extension-line tracing; signed-cross-product chirality; `pcbnew` readback; 8/8 mutation test | **It measured the vendor's ARTWORK.** No tolerances, ±0.5 mm bracket on body dimensions, **no physical module measured** ⇒ `BENCH_MEASUREMENTS.md` **M5** |
| `VSET` hazard (10 kΩ pull-up to Vref ⇒ open = full scale; not internally limited) | 3 skeptics: `Rset` formula algebra with three hypotheses coded (two diverge), native-resolution figure, verbatim in both revisions | The 10 kΩ **tolerance** — O-A, the fail-open criterion **breaks at 7.83 kΩ**. MEASURABLE-NOW. |
| `board_spec.py` symbol↔spec pin agreement, both directions | the file re-parses each `.kicad_sym` every run, set equality + **pin-NAME** cross-check; 13/13 mutations caught | **It never opens a `.kicad_mod`.** Whether a symbol matches the physical part. **44 TIER-C borrowed pinouts.** |
| Domain assertions (a)/(b)/(c) fire | 3 independent mutation harnesses, 24 mutations, in-memory boards, caches cleared | **Four escape routes — §1.6.** Assertion (a) never evaluates pseudo-bipolar. |
| Netclasses carry all 17 KiCad-10 fields | asserted at runtime | A flattened `.kicad_pro` would make DRC pass **vacuously** — Phase 4 must measure the copper |
| Arithmetic self-consistency | `numbers_probe.py` 74/74 exit 0, deterministic, 8/8 mutations; `setpoint_path_numbers.py` 52/52 | **Arithmetic over datasheet numbers.** Nothing measured, nothing simulated, no MPN checked. **Exit 0 means the algebra ran.** And two instruments **disagree with each other** (31× vs 6.6×; 11.00 vs 11.40 vs 12.40 vs 12.60 %). |
| Toolchain (Phase 0) | 24 gerbers + drill + DRC 0/0 + render, `[verified-run]` | Nothing about this design |
| **Clearance constants** | ❌ **NONE.** `[recalled]`; two "independent" web sources proved to be one page; the internal cross-check was an **algebraic tautology** and was **deleted with no replacement** | **Everything.** |
| **Touch-safety thresholds** (60 V / 5 s, 350 mJ, 50 µC) | ❌ **NONE.** `[recalled]` | **Everything. The whole Phase-7 safety argument.** |
| **Anything on hardware** | ❌ **NONE. Nothing has ever been measured, energised, or touched.** | — |

---

## 4. The honest list of what is NOT verified

1. **Nothing has been measured, energised or built.** Every electrical claim is a reading of vendor
   documentation or arithmetic over it. **No physical iseg module has been touched — not a caliper,
   not a meter** — even though **both modules are in hand.**
2. **Eight parameters are MEASURABLE-NOW and unmeasured:** `VSET` step response · HV output
   capacitance (**the two live design documents disagree by 10×**) · internal bleeder · turn-on time
   · module `VSET` pull-up tolerance (O-A) · divider `k_VCR` (O-M5) · guard-ring factor (O-M6) ·
   **the physical module against our land pattern** (M5). ⇒ `docs/BENCH_MEASUREMENTS.md`.
3. **Every clearance and touch-safety constant is `[unverified-primary]`.** There is currently **NO
   evidence the clearance constants are the right constants.** A human must read a primary copy.
   Decision-relevant: one reading fits a 100 × 100 mm fab tier and the other does not.
4. **Not one MPN has been checked against a live distributor page.** The mode switch has **no MPN**;
   `U4` (the clamp) is **unselected**; the Pickering relays are **unpriced**; ~60 HV passives came
   back 0-stock / obsolete / 13-week lead across four agents' searches. **No iseg quote, lead time or
   MOQ exists.** Precedents: a distributor deep-link returned a confident spec report **for an
   entirely different product**; a recalled MPN **did not exist**; one candidate was stamped **Not
   For New Designs**.
5. **44 TIER-C borrowed pinouts have never been checked against a datasheet** — including both HV
   relays, `K_S` (the single armature), the four `+VIN` load switches (the primary disable), all
   seven comparators, and every interlock gate. **11 named footprints do not exist**, including
   `K1`/`K2`'s.
6. **⛔ G0 Q3, Q5 and Q6 were never answered and the design is proceeding on documented defaults.**
   Q3 (output spec: max load current, load capacitance, required ripple) — proceeding on a **declared
   `C_load ≤ 10 nF` interface constraint that nothing physically enforces**. Q5 (safety envelope) —
   proceeding on `[recalled]` 60 V / 5 s / 350 mJ. **Q6 (weld: detection vs prevention) — the design
   DETECTS and CANNOT PREVENT; if prevention is required, every candidate topology fails.**
7. **Nine assertions are not structurally expressible** and four of those are safety properties:
   SA-9 placement · graded string spacing · **HCT vs HC** · push-pull comparators · **relay coil
   polarity** (mandatory — internal diode) · **K1/K2 orthogonal mounting** (free at layout,
   impossible to add later) · **weld detection** · discharge **TIME** · SA-12 dump sizing.
8. **`docs/studies/combiner_design_numbers.py` is arithmetic, not verification** — no independent
   source of truth, **not mutation-tested** — and `COMBINER_DESIGN.md` quotes it throughout.
   `MONITOR_AND_BLEED.md`'s new arithmetic ran in **two throwaway scripts that were not retained.**
9. **`CONTROLLER_AND_POWER.md` (131 kB) was never adversarially reviewed.** Power tree, comms,
   state machine, connectors: one agent's word.
10. **The Phase-7 bench procedure is a DRAFT reviewed by nobody**, and two of its own pre-day items
    are the unverified standards constants.
11. **NUM-18 / ARCH-14 remain contradictory:** conformal coating assumed **absent** for clearance and
    mandated **present** for divider surface leakage. This session added two more guard-ringed
    regions, so the tension is worse. **Resolve before layout.**

---

## 5. What the next session should do first

1. **Put `docs/G1_REVIEW.md` in front of the human.** §1 (frozen values) and §3 (netlist intent) are
   reviewable **now**; the refutations do not invalidate the netlist structure, they invalidate
   specific claims *about* it.
2. **Get the four human-only answers:** G0 **Q6** (weld: detect or prevent — it can kill the
   topology), the **mode element decision** (link block as baseline vs fund a switch search), a
   **primary clearance standard**, and the **D-1 / D-4 adjudications** (both change the netlist).
3. **Do the bench afternoon** — `docs/BENCH_MEASUREMENTS.md`. **M5 (caliper) needs no high voltage
   and retires the one risk no document review can touch.**
4. **Repair the four assertion escape routes** (D-7…D-10) — this is session work, but after G1 it
   needs a gate, so **do it before G1 closes.**
5. **Fix the documents that assert refuted claims in their body text** — the banners record the
   corrections; the bodies still need editing. **Fix the generator, never the artifact.**
6. **Order long-lead parts at G1, not at fab** (R-7).
7. **Do NOT start Phase 3** (schematic generation) until G1 is signed.

---

## 6. One-line summary

**G0 is signed and the golden netlist exists and runs clean — but all six claims put to adversarial
verification this session were refuted, including the interlock and the `VSET` clamp, which G0-A3
made load-bearing for the entire safety case. The mode switch has no part number. Nothing has ever
been measured, and both modules are sitting in the lab.**
