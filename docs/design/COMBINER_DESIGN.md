# COMBINER_DESIGN — HV routing matrix and mode-aware hardware interlock

**Status:** detailed design, session 2, 2026-07-23. Written against the **frozen G0 answers**
(`docs/G0_QUESTIONS.md`, `docs/DECISIONS.md` §5A). This is a **live design document**, not a study.
It supersedes `docs/topology/hv-relay-changeover.md` (bannered historical) as the description of the
circuit, and it is the artefact `COMBINER_STUDY.md` §5A names as the one that must carry the
dual-mode safety case: *"the mode-aware interlock truth table is what must carry it."*

---

> # ⛔ CORRECTION BANNER — added 2026-07-23 (session 2 verification). READ BEFORE ANY SECTION BELOW.
>
> Three claims made by this document were put to **three independent skeptics each, tasked with
> refuting them. All three claims were refuted, 3/3, at high confidence.** The refutations are
> recorded in `docs/STATUS.md` §1 and `docs/G1_REVIEW.md` §7. The affected text below is **left in
> place, not deleted**, so the review can see what was claimed and what was found — but it is
> **wrong as written** and the corrections here govern.
>
> **This is a STOP-THE-LINE finding for a 1 kV instrument.** No layout, no procurement of the mode
> element, and no G1 signature may proceed on the uncorrected text.
>
> **C-1 — §1.3's THEOREM is FALSE AS WRITTEN, and it contradicts this document's own §7.5 and F-15.**
> §1.3 says the forbidden state needs *"a weld on one of the two HV reeds **plus** a coincident second
> fault."* §7.5(c) and §8 F-15 both say the weld **alone** suffices: `K1` welded at NO puts POS
> permanently on `OUT_A`, and the next NEG selection in pseudo-bipolar puts both modules on `OUT_A`.
> **§7.5's own "HONEST FORMULATION" is the correct statement; §1.3 is not.** Read §1.3 as:
> *unreachable through any electrical, logic, firmware, network, driver or wiring fault, and through
> any single fault of the mode element; **reachable through a single welded HV reed contact**, which
> is detected and not prevented.* G0 Q6 (detection vs prevention) was never answered — see §14.
>
> **C-1a — the executable proof of the invariant is VACUOUS in the mode at risk.**
> `board_spec.py:assert_a_no_shared_output_node()` filters with `if not (pp and pn): continue`, and
> `PERMIT_P · PERMIT_N ⇒ MODE_UNI` by construction, so the assertion evaluates **only UNI states —
> zero pseudo-bipolar states**. Independently reproduced by two skeptics against the file's own
> `reachable_states()` / `_adjacency()`: in `mode=PB, K1=1, K2=1` both `HV_POS` and `HV_NEG` reach
> `HV_OUT_A`, and that state is never examined. The assertion cannot detect the F-15 weld it is
> nominally the proof against. **Repair before G1** (drop the `pp/pn` filter and assert on *galvanic*
> reachability), or state plainly that assertion (a) covers unipolar only.
>
> **C-2 — §3.6 is factually wrong about the one part it names, and NO part is actually specified.**
> The BOM (§10) row for `SW1` is *"3-position ceramic wafer switch … or the §3.7 link block —
> `[unverified-MPN]`, O-10 open"*: **the claim "a real, obtainable part rated for this application"
> has no referent.** For the one MPN floated as "the most likely answer", **Electroswitch
> `D4C0212N`**, three skeptics independently fetched the manufacturer's own catalogue PDF and read,
> verbatim: *"Make and break resistive load 1.5 amps @ 28 VDC; 0.5 amp @ 115 VAC"* and
> *"Dielectric Strength: 1,500 VAC between current carrying parts and ground."* Therefore:
> - §3.6's *"28 V DC / 1.5 A — a **current** rating, not a standoff rating"* is **wrong**: the
>   catalogue line is a voltage **and** current rating, and 115 VAC / 28 VDC is the only working
>   voltage published for the family.
> - §3.6's *"the dielectric capability … is much higher but … must be obtained from the
>   manufacturer"* is **wrong twice**: it **is** published, in the free catalogue, and it is
>   **1,500 VAC — lower than SW-R3's ≥2000 V proof requirement, not higher.** No contact-to-contact
>   figure is published at any voltage, so SW-R3's 2 kV pole-to-pole case is entirely unaddressed.
>   The best ceramic part in the whole Electroswitch line (E4C) reaches 3000 VAC **to ground** and
>   still publishes no DC working voltage above 28 V.
> - The *"use every fourth position"* fix in the boxed paragraph **cannot rescue the rating.** The
>   published 1,500 VAC figure is contact-to-**ground**, set by rotor/shaft/bushing/strut geometry;
>   skipping contacts improves only contact-to-**contact** pitch. A ruler check on the received part
>   does not qualify it. Keep the fix as a necessary condition; do not treat it as sufficient.
> - Ross Engineering is a real vendor but its range is **2 kV–450 kV**, not §3.6's "13–20 kV", and it
>   ships **one SPDT auxiliary contact** as standard against the **four** LV poles SW-R3 needs.
> - The comparison instrument that *does* exist: NSF Controls' MSD wafer datasheet publishes
>   *"Maximum Working Voltage: 250 Vac"* **and** *"Proof Voltage: 2000 Vdc for 1 minute"* — the exact
>   working-vs-hipot split, 8× apart, that a single dielectric-strength number hides.
>
> **What §3.6/§3.7 got RIGHT and keeps:** every MPN is tagged `[unverified-MPN]`, O-10 is logged
> open, **SW-R8 forbids fitting a non-conforming switch**, and §3.7 offers the link block as
> *co-equal* and *"may be the better answer"*. No toggle switch is forced by this document.
> **ACTION for G1: make §3.7 Option B (guarded link block with captive interlock key) the BASELINE,
> and Option A the contingency**, unless a vendor supplies a contact-to-contact **DC working**
> specification ≥1000 V in writing.
>
> **C-3 — §3.5's SAFE-detent margin does NOT meet the requirement §3.5 itself derives.**
> §3.5 derives *"≥ 0.2 s bare, ≥ 1.0 s at the C_load limit"* and then satisfies it with *"the
> operator's dwell in the SAFE detent … of order 100 ms even for a fast, careless turn"* `[recalled]`.
> **100 ms is 2× short of this file's own bare-board figure, 10× short of its loaded figure, and
> ~19× short of `numbers_probe.py` §3.7's independently-budgeted 1.877 s.** The shortfall is
> reconciled nowhere in this file (three skeptics grepped for it). Two skeptics recomputed the
> consequence with a **fully conforming** switch: at the documented `C_load` interface limit,
> τ ≈ 0.21–0.45 s, so a 100 ms transit leaves **~620–800 V per module still standing as the HV poles
> make.** §3.8 frames that hot-make as the consequence of a **non-conforming** switch; the arithmetic
> shows a conforming one reaches it too on a fast turn **with a cable attached**.
> §3.5's *"converts an unspecifiable contact-timing requirement into a mechanical certainty"* is
> therefore **overstated and must not be read as a met requirement.**
> **What actually carries this case is (i) §3.8's consequence bound — 1.5 mA into 20 kΩ = 30 mW, no
> arc available at 0.75 mA, ~11 mJ vs the 350 mJ threshold, i.e. a contact-plating/weld risk and not
> an energetic or shock hazard — and (ii) the PROCEDURE MODE-17 (powered down, cables off, so
> `C_load ≈ 0` and 100 ms suffices). The residual protection here is PROCEDURAL, not structural.**
> Say so on the panel and in the manual. Either add a *checkable* mechanical requirement that bounds
> SAFE dwell ≥ 1 s (detent torque + stop geometry), or adopt §3.7 Option B where the LV plug
> physically blocks the links and the timing question is vacuous.
>
> **C-4 — this document and `CONTROLLER_AND_POWER.md` §9.2 specify DIFFERENT, INCOMPATIBLE SWITCHES.**
> §3.5/SW-R1/SW-R3 here require **3 positions and ≥7 poles**; `board_spec.py` builds `SW1A…SW1G`
> = 7 poles, 3 positions. `CONTROLLER_AND_POWER.md` §9.2 still specifies **"Poles: 4 total … Positions:
> 2, detented"** with a `MODE_MID` series-HV arrangement that does not exist in the netlist, and its
> §0.4 reconciliation table omits the mode selector entirely. **A purchaser following §9.2 buys a
> 2-position part with no SAFE detent — deleting the sole mechanism §3.5 relies on.** §9.2 is
> superseded and now carries its own banner; it must be struck or rewritten before procurement.
>
> **C-5 — §6.1's signal-inventory rows for `MODE_PB`/`MODE_UNI` do not match the netlist.**
> §6.1 lists `MODE_UNI` as *"`SW1` pole `S5`, contact to +3.3 V"*. In `board_spec.py`, `S5` (`SW1E`)
> drives **`MODE_B`**, and `MODE_UNI` is a **74HCT08 output** (`U33` pins 1,2 → 3 =
> `MODE_B · nMODE_A`). Consequently §7.5(b)'s *"three faults"* count is **two** (`U33a` stuck high +
> `S7` welded, or a solder bridge between adjacent `J6` pins 7/8). Fix §6.1's table to name
> `MODE_A`/`MODE_B` as the contact signals and `MODE_UNI` as a derived gate output, and re-count
> §7.5(b).

**Scope.** The HV routing elements (two changeover relays + one physical mode switch), the bleed and
discharge network attached to them, the hardware interlock that governs them, and the state machine
that sequences them. **Out of scope and referenced only:** the `VSET` clamp (ARCH-06/PART-33), the
DAC/ADC chain, the protocol, the enclosure. Numbers from those documents are cited, not re-derived.

---

## 0. Evidence key, and what this document is as an instrument

| Tag | Meaning here |
|---|---|
| `[verified-run]` | executed this session; the arithmetic tool is `docs/studies/combiner_design_numbers.py` (stdlib-only, zero-arg, deterministic) — see §12 |
| `[verified-artifact]` | a file was opened this session and the stated text read out of it |
| `[verified-web]` | read off a live page this session |
| `[recalled]` | background knowledge, **unverified** — a hypothesis |
| `[unverified-MPN]` | part number not re-verified against a live distributor page (project rule, `DECISIONS.md`) |
| `[unverified-primary]` | clearance/creepage constant whose primary standard nobody on this project has read (NUM-01) |
| `MEASURABLE-NOW` | depends on one of the four unmeasured module parameters; the modules are in hand (G0-A2) |

**What this document has NOT done.** Nothing was simulated, breadboarded or measured. No relay was
energised, no switch was scoped, no contact-timing figure was observed. Every clearance number stays
`[unverified-primary]`. The four module parameters (VSET step response, output capacitance, internal
bleeder, turn-on time) are still assumptions — §11 states what the design does at their pessimistic
end. `Exit 0` on the arithmetic tool means the arithmetic is self-consistent, which is a far weaker
claim than "this circuit is safe".

---

## 1. The requirement, and the one theorem this document must prove

### 1.1 The two modes (MODE-01, frozen by G0-A4)

| | **PSEUDO-BIPOLAR** (mode 1) | **UNIPOLAR / DUAL-OUTPUT** (mode 2) |
|---|---|---|
| Terminals in use | `OUT_A` only | `OUT_A` **and** `OUT_B` |
| POS module `AP010504P05` | → `OUT_A` when selected | → `OUT_A`, always |
| NEG module `AP010504N05` | → `OUT_A` when selected | → `OUT_B` |
| Simultaneous energisation | **forbidden** | **required — it is the point of the mode** |
| `OUT_B` | **bonded to ground and bled** (§3.4) | live, −1000 … 0 V |
| Deselected module | bled to ground through its relay's NC contact | n/a |

Terminology is the human's own (G0-A5): **pseudo-bipolar**, because the instrument does not pass
smoothly through zero — it switches polarity across a dead band, and the band
`0 < |Vout| < 20 V` is **unspecified by iseg, not merely worse** (PART-10/PART-32). Every low-end
number below inherits that clause.

### 1.2 The invariant (MODE-02, frozen)

> **It must be impossible for both modules to be connected to the SAME output node simultaneously.**

### 1.3 The theorem

> **THEOREM.** In this circuit, the state *"both K1 and K2 closed onto one node"* is not reachable
> from any combination of logic levels, gate failures, firmware states, network messages, broken
> control wires, or single mechanical faults. It requires **two independent mechanical faults on the
> mode switch**, or a weld on one of the two HV reeds *plus* a coincident second fault.

The proof is §7.5. It rests on one structural fact and one derived one:

1. **In the pseudo-bipolar position, the only power that can reach either HV relay coil passes
   through a single armature (`K_S`).** One piece of metal cannot touch both throws. This is not a
   truth table; it is a statement about metal.
2. **What releases that exclusivity is not a logic signal.** It is a pair of *power-bridging
   contacts on the mode switch itself* (`S6`, `S7`), closed only in the unipolar position — the same
   armature that has already routed the two modules to physically different nodes. A firmware fault,
   a stuck GPIO, a network command, or a stuck gate output cannot close them.

**There are therefore two distinct "mode permissives" in this design, and they are different
objects.** The *logic* permissive `MODE_UNI` relaxes the `/ON` gate; the *power* permissive
`S6`/`S7` relaxes the coil and `+VIN` exclusivity. **The forbidden state needs both to be wrong at
once.** Session 1's interlock had a single mechanism; this is the change G0-A4 forced and it is the
most important structural decision in this document.

---

## 2. Architecture at a glance

```
     +5V_MOD                                                                 ,--> SHV  OUT_A
        |                                                                    |
   [Q_ARM]  <-- ARM  (C-1: fail-safe-open switch in the module supply rail)   |
        |                                                        BUS_A ------+
   VIN_ARMED                                                          ^
        |                                                             |
   K_S pole A  COM                                                    |  [S2] closed in PSEUDO-BIPOLAR
      NO -+----------------.                                          |   |
      NC -+---.            |                                          |   |
           |  |            |                              R_M1 10k    |   |
        [S6] bridge (UNI)  |                          M ---/\/\/---[S2]---'
           |  |            |                          |
   VIN_N_PRE  VIN_P_PRE    |                       [S3] SPDT, COMMON = GND via R_G 10k
        |         |        |                          |  PB throw --> OUT_B
      [U_N]     [U_P]  <-- per-module load switches   |  UNI throw --> M
        |         |            EN = PERMIT_N / _P     |
   +VIN_N     +VIN_P                                  |
    22uF       22uF                                   |
        |         |                                   |
  +-----+---+ +---+-----+                        [S1] SPDT, COMMON = X
  | AP010504| |AP010504 |                             |  PB throw --> M
  |  N05    | |  P05    |                             |  UNI throw --> OUT_B
  +----+----+ +----+----+                             |
  HV_NEG|          |HV_POS                            |
        |          |                                  |
   R_S 10k     R_S 10k                                |
        |          |                                  |
   K2 COM      K1 COM      (Pickering 67-1-C-5/5D, 1 Form C, 5 kV stand-off)
   K2 NC -> R_bleed_NEG 40M -> GND        K1 NC -> R_bleed_POS 40M -> GND
   K2 NO -> X ---------------------------'  K1 NO -> BUS_A
                                                                      ,--> SHV OUT_B
   BLEEDS (permanent, each 2 parallel strings -- NUM-09):             |
     R_bleed_POS 40M @HV_POS   R_bleed_NEG 40M @HV_NEG                |
     R_bleed_A   40M @OUT_A    R_bleed_B   40M @OUT_B ----------------+
     R_X 400M @X               R_M 400M @M     (stub bleeds, cover the SAFE detent)

   MEASUREMENT (four independent HV strings per output pair):
     invariant-(c) monitor   200M : offset network -> buffer -> ADC-A      (OUT_A, OUT_B)
     COLD permissive         500M : offset network -> window comparator    (OUT_A, OUT_B)
     per-branch monitor      1G   -> buffer -> ADC-B    (HV_POS, HV_NEG -- weld self-test, F-2)

   MODE SWITCH SW1 -- 3 positions: PSEUDO-BIPOLAR . SAFE . UNIPOLAR
     HV poles : S1, S2, S3          (above)
     LV logic : S4 = MODE_PB, S5 = MODE_UNI   -> interlock gate array AND ESP32 (read-only)
     LV power : S6 bridges VIN_P_PRE<->VIN_N_PRE ; S7 bridges the two coil feeds  (UNI only)
```

---

## 3. The mode element

### 3.1 Which module does the switch route? — **the negative module only. Asymmetric. Defended.**

The task asks whether the switch should route the negative module (asymmetric) or both
(symmetric). **The asymmetry is not a choice made by the switch arrangement; it is forced by the
requirement**, and pretending otherwise costs poles for nothing:

- Pseudo-bipolar mode uses **one** terminal. That terminal is `OUT_A` by definition.
- The POS module drives `OUT_A` in **both** modes. There is no position of any switch in which the
  POS module should go anywhere else.
- ⇒ A pole in the POS path would have both throws landing on `OUT_A`. It is degenerate. It buys no
  function, adds a contact in the highest-current-margin path, adds a weld site, and adds a part
  that must hold 1 kV.

**The genuinely symmetric alternative was considered and rejected.** It is: *let the mode switch
parallel `OUT_A` and `OUT_B` in pseudo-bipolar mode* (one SPST pole, `OUT_A ↔ OUT_B`, closed in
PB). That is the smallest circuit on the table — one HV pole instead of three. It is rejected for
three reasons, in order of weight:

1. **It leaves a second live, unmated terminal in pseudo-bipolar mode.** The task's own requirement
   is explicit: *"OUT_B must be bonded to ground and bled, never left floating and unterminated."*
   Paralleling makes `OUT_B` live at up to ±1 kV whenever `OUT_A` is. SHV's untouchable-when-unmated
   geometry (`HV_SAFETY_ENVELOPE` §1) makes that *tolerable*, not *good*.
2. **It doubles the exposed HV surface for zero function**, and it makes the panel legend say
   "both terminals live, same potential", which is a worse answer to MODE-09 than "A live, B
   grounded".
3. **It puts the full 2000 V across a single open contact of the mode switch** in unipolar mode,
   with no way to split it (§3.2). The three-pole arrangement below reduces the worst contact stress
   to **1000 V**.

**Consequence of the asymmetry, stated so nobody is surprised at commissioning:** `OUT_A` and
`OUT_B` do **not** have identical electrical properties. `OUT_A` carries either polarity in PB and
positive only in UNI; `OUT_B` is grounded in PB and negative only in UNI. The negative path carries
one extra series limiter (`R_M1`, §3.3), so the NEG-to-`OUT_A` path drops **15.0 V** at the 0.75 mA
limit against **7.5 V** for the POS path `[verified-run]` — 1.50 % vs 0.75 % of Vnom. Both drops sit
*upstream* of the independent monitors, so both are **measured, not guessed**, and both fall out in
the per-output calibration that F-20 already requires. **Do not treat the two outputs as
interchangeable in firmware, in calibration, or on the panel.**

### 3.2 The 2000 V problem inside the switch — and its elimination

The naive arrangement is one SPDT pole with its common on the NEG side and its throws on `OUT_A`
and `OUT_B`. In unipolar mode that pole's *open* contact sits between the NEG module (−1000 V) and
`OUT_A` (+1000 V): **2000 V, continuously, as normal operation.** MODE-13 says to prefer an
arrangement that does not create such a pair. This one does.

**The 2000 V cannot simply be removed** — it is topologically necessary. Pseudo-bipolar mode
requires a conducting path from the NEG module to `OUT_A`; unipolar mode requires that path to be
open while both ends are at full opposite polarity. *Some* open element must hold 2 kV.

**But it can be split, by the same grounded-guard-conductor argument `NUMBERS_PROBE` §1.6 makes for
board copper — applied inside the switch.** Insert an intermediate node `M` in the NEG-to-`OUT_A`
path, break it in *two* places, and **ground `M` in the position where both breaks are open**:

| pole | function | PSEUDO-BIPOLAR | SAFE (centre) | UNIPOLAR |
|---|---|---|---|---|
| **S1** | SPDT, common = `X` (= K2 NO) | closed to `M` | open | closed to `OUT_B` |
| **S2** | SPST, `M` ↔ `BUS_A` (via `R_M1`) | closed | open | **open** |
| **S3** | SPDT, common = GND (via `R_G`) | closed to `OUT_B` | open | closed to `M` |

Worst-case voltage across every open contact, by position `[verified-run]`:

| position | S1 open throw | S2 | S3 open throw | **max** |
|---|---|---|---|---|
| PSEUDO-BIPOLAR | `OUT_B` = 0 V (grounded by S3) vs `X` = ±1 kV → **1000 V** | closed | `M` = ±1 kV vs GND → **1000 V** | **1000 V** |
| SAFE | all nodes bled to < 60 V within ~1 s | — | — | ≈0 V |
| UNIPOLAR | `M` = 0 V (grounded by S3) vs `X` = −1 kV → **1000 V** | `M` = 0 V vs `BUS_A` = +1 kV → **1000 V** | `OUT_B` = −1 kV vs GND → **1000 V** | **1000 V** |

> **⬛ RESULT: the 2000 V differential never appears across any contact, or between any two poles, of
> the mode switch.** It appears only between board copper (`HV_POS` region vs `HV_NEG` region, and
> `OUT_A` vs `OUT_B`), where it is handled by the two pairwise `.kicad_dru` rules at
> **15.0 mm `[unverified-primary]`** (NUM-03, F-4). **MODE-13's "prefer an arrangement that does not
> create an opposite-polarity pair" is satisfied, not merely attempted.**

**One mechanical caveat that the table does not show, and that must be a build rule.** Even with no
*contact* holding 2 kV, `S1`'s common carries −1 kV while `S2` carries +1 kV. If those two poles sit
on adjacent decks or adjacent wafer sectors, the *pole-to-pole* stress is 2 kV regardless of the
contact algebra.

> **BUILD RULE SW-1.** `S3` — the grounded pole — must be **physically interposed** between `S1` and
> `S2`: middle deck of a three-deck stack, or a grounded unused sector between them on one wafer.
> The grounded conductor then does inside the switch exactly what the guard trace does on the board.
> **A build that puts `S1` and `S2` adjacent with `S3` on the end is under-insulated by 2× and will
> not look wrong.**

### 3.3 Series limiting elements in the mode paths

| ref | value | rating | where | why |
|---|---|---|---|---|
| `R_S` ×2 | 10 kΩ | ≥2 kV working | module HV pin → relay COM | limits the capacitive make-discharge Pickering Note 1 warns about `[verified-artifact]`. 100 mA at 1 kV, 200 mA at the 2 kV fault, vs a **3 A** max-switch-current rating = **30× / 15×** `[verified-run]` |
| `R_M1` | 10 kΩ | ≥2 kV working | in the `M` ↔ `BUS_A` leg, at `S2` | the UNI→PB transition, done wrongly on a live instrument, closes `S1`+`S2` between two oppositely-charged output capacitances. Without `R_M1` the peak current is set only by contact resistance. With it, **200 mA at 2000 V** `[verified-run]` |
| `R_G` | 10 kΩ | ≥2 kV working | `S3` common → GND | makes `OUT_B`'s pseudo-bipolar ground bond **defined and current-limited**. A module driving into it at the 0.75 mA limit lifts `OUT_B` by **7.5 V** — still touch-safe, still a hard bond, and no contact ever sees an unlimited discharge |

Candidate part for all four: an axial HV film resistor, e.g. **Ohmite MOX-400 series, 10 kΩ, 3.5 kV
working** `[unverified-MPN]`. A chip alternative needs N = 10 standard 2512 elements at the verified
200 V/element rating (ARCH-12) and is not worth the area.

### 3.4 What `OUT_B` is in pseudo-bipolar mode — **grounded by `S3`, and bled by `R_bleed_B`**

Three separate things hold `OUT_B` at ground in pseudo-bipolar mode, and they are named so the
design review can check each:

1. **`S3`, the mode switch's grounded-common pole**, closed to `OUT_B` in the PB position, through
   `R_G` = 10 kΩ. This is the **bond**. It is a hard, low-impedance connection to chassis/board
   ground, made by the same armature that routed the NEG module away from `OUT_B`.
2. **`R_bleed_B`, 40 MΩ permanent**, two parallel 80 MΩ strings (NUM-09). This is the **bleed**. It
   is present in every position and every power state, including with the switch between detents and
   with the instrument unpowered.
3. **`S1` in the PB position routes `X` to `M`, not to `OUT_B`** — so nothing can drive `OUT_B` at
   all. The grounding is not fighting a source; it is terminating an idle node.

`OUT_B` is therefore never floating, never unterminated, and never charged in pseudo-bipolar mode,
and that is true **structurally** (invariant (b), MODE-10) rather than by a timer or a firmware step.

### 3.5 The SAFE centre detent — how MODE-15's timing requirement is actually met

MODE-15 requires the **LV aux poles to break before the HV poles make**, "with a stated margin".
O-11 asks what that margin is. **Deriving it honestly produces a number a contact sequence cannot
deliver, and that finding changes the part specification.**

The margin must cover the time from *"the interlock commanded both modules off"* to *"the module
outputs are actually below `V_safe`"*:

| step | time | source |
|---|---:|---|
| aux pole opens → `VALID` = 0 → `ARM` = 0 | < 100 ns | 74HCT gate delays |
| `ARM` = 0 → `Q_ARM` off, `/ON` high | < 100 µs | load-switch `t_off` `[unverified-MPN]` |
| module output decays 1000 V → 10 V, bare board + 2 m cable | **97 ms** | `[verified-run]`, **MEASURABLE-NOW** (assumes C_module = 1 nF) |
| same, with a 10 nF load on 10 m of cable | **954 ms** | `[verified-run]` |
| **⇒ required lead-break margin** | **≥ 0.2 s bare, ≥ 1.0 s at the C_load interface limit** | |

**No rotary or toggle switch specifies contact lead in units of 200–1000 ms.** Contact sequencing on
a hand-operated switch is an *angular* property; the elapsed time depends on how fast a human turns
the knob and is unbounded below. Specifying "the aux poles must lead by 200 ms" would be specifying
something unpurchasable and unverifiable.

> ### ⬛ DESIGN ANSWER: make the mode element a **THREE-position** device — `PSEUDO-BIPOLAR · SAFE · UNIPOLAR` — with `SAFE` a real detent that the operator must pass through.
>
> - In `SAFE`, **`S4` and `S5` are both open** ⇒ `MODE_PB = MODE_UNI = 0` ⇒ `VALID = 0` ⇒ `ARM = 0`
>   ⇒ both modules off, both `+VIN` removed, both `/ON` high, both HV relays released to their NC
>   bleeds, all four output/branch bleeds engaged, `X` and `M` on their stub bleeds.
> - In `SAFE`, **all three HV poles are open** (non-shorting switch action).
> - The "margin" is therefore **the operator's dwell in the SAFE detent**, which is bounded below by
>   detent torque and human hand speed — of order **100 ms even for a fast, careless turn**
>   `[recalled]` — and which the operating procedure (MODE-17, powered-down mode change) makes
>   arbitrarily long in normal use.
>
> **This converts an unspecifiable contact-timing requirement into a mechanical certainty, and it
> makes MODE-18's "intermediate position" a *designed* position rather than an accident.** It is the
> single most useful thing in this section.

**Switch selection requirements, in the form a purchaser can check:**

| id | requirement | why |
|---|---|---|
| **SW-R1** | **3 positions**, detented, `PB · SAFE · UNI`, `SAFE` between the others. | §3.5 |
| **SW-R2** | **Non-shorting (break-before-make) between adjacent positions**, on every pole, HV and LV. | a shorting pole would bridge `OUT_A` to `OUT_B` in transit |
| **SW-R3** | **≥ 3 HV poles** rated ≥ 1000 V working, ≥ 2000 V proof, contact-to-contact and contact-to-frame; **≥ 4 LV poles** (`S4`…`S7`) with `S6`/`S7` rated ≥ 500 mA at 5 V DC. | §3.2, §6 |
| **SW-R4** | Pole order **`S1 – S3 – S2`** with the grounded pole between the two HV poles. | BUILD RULE SW-1 |
| **SW-R5** | Contact-to-contact spacing on the HV decks **≥ 7.5 mm `[unverified-primary]`** — the same rule this project imposes on its own board copper. | §3.6 |
| **SW-R6** | Ceramic or equivalent tracking-resistant insulation on the HV decks; no phenolic. | 1 kV over a bench-lab surface |
| **SW-R7** | Guarded/covered actuator, and a panel legend stating that mode change is a **powered-down, cables-off** operation (MODE-17, NUM-23 requirement 8). | |
| **SW-R8** | If a switch that does **not** meet SW-R1/SW-R2 is the only procurable part, **it must not be fitted.** See §3.7 for the fallback and §3.8 for the honest consequence statement. | MODE-15 |

### 3.6 Candidate parts — and the argument that decides between them

Nobody on this project had searched this part class (`SCOPE.md` R-14, O-10). Candidates found this
session, with what is and is not known about each:

| candidate | rating | verdict |
|---|---|---|
| **Ross Engineering Corp HV rotary switches** `[unverified-MPN]` `[verified-web]` — the vendor publishes a dedicated HV-rotary product line in the **13–20 kV** class | far above requirement | **Over-specified.** These are power-industry parts: large, expensive, and almost certainly without the 4 low-voltage aux poles this design needs. Quote it, but expect to reject it on size and cost. |
| **Ceramic wafer rotary switches, transmitter/RF grade** (e.g. the ceramic-wafer stock at Surplus Sales of Nebraska) `[verified-web]`, `[unverified-MPN]` | typically 1–3 kV working `[recalled]` | **The right class, wrong supply.** Surplus stock is non-repeatable and unqualifiable. Usable for a one-off; not for a documented build. |
| **Electroswitch ceramic-insulated wafer switches** (e.g. `D4C0212N`, 2-pole 2–12-position, ceramic insulation, non-shorting) `[unverified-MPN]` `[verified-web]` | catalogue rating quoted as **28 V DC / 1.5 A** — a *current* rating, not a standoff rating | **The most likely answer, with one modification (below).** The published rating is about contact current; the dielectric capability of a ceramic wafer is much higher but is stated as a proof-voltage figure that must be obtained from the manufacturer, not inferred. |
| **Grayhill Series 56 / 71** `[verified-web]` | no HV rating published | **Reject.** Phenolic/plastic wafers, low-voltage catalogue parts. |
| **HV link block / re-plugged HV cable** | n/a | **The fallback, and it may be the better answer — see §3.7.** |

> ### ⬛ THE MODIFICATION THAT MAKES AN ORDINARY CERAMIC WAFER SWITCH MEET A KILOVOLT SPEC
>
> A standard 12-position wafer places contacts every 30° on a contact circle of radius ~10 mm, i.e.
> an arc pitch of ≈ 5.2 mm and, after subtracting ~2 mm of contact width, a **contact-to-contact gap
> of order 3 mm** `[recalled — the radius and contact width are assumed; measure the actual wafer]`.
> **3 mm fails SW-R5 by 2.5×.** It is also below what this project demands of its own board copper
> at 1000 V (7.5 mm `[unverified-primary]`), which is the decisive way to state it: *we would reject
> this spacing in our own layout.*
>
> **Fix: buy a 12-position wafer and use only every fourth position** — 1, 5, 9 — as
> `PB`, `SAFE`, `UNI`, with the unused contacts either omitted or **tied to ground** (which also
> supplies SW-R4's interposed guard for free). Angular pitch becomes 90°, arc pitch ≈ 15.7 mm, gap
> ≈ **13.7 mm** `[recalled geometry, verified-run arithmetic]`. Fit the switch's own **stop ring** to
> limit travel to those three detents.
>
> This is the cheapest route to a kilovolt-capable, multi-pole, three-position, non-shorting mode
> element, and it makes SW-R5 checkable with a ruler on the received part.

**Every MPN above stays `[unverified-MPN]`.** No distributor page was read for stock or price this
session, and the Electroswitch and Ross figures came from search-result summaries, not from
datasheets. **O-10 is not closed by this section; it is narrowed.**

### 3.7 The fallback, recommended as a co-equal option: a guarded link block with a captive key

MODE-13 explicitly invites this and says to recommend it if it is better engineering. **It is better
on the one requirement that is hardest to buy — the timing.**

```
   Behind a captive, tool-secured cover on the rear panel:
     an HV terminal block with three fixed studs  X , M , OUT_B  and one ground stud G ,
     plus two insulated HV shorting links on a moulded carrier with two positions:
        PB position  : link1 = X-M , link2 = G-OUT_B
        UNI position : link1 = X-OUT_B , link2 = G-M
   The cover is retained by a CAPTIVE INTERLOCK PLUG that also carries the LV loop.
   Removing the plug opens INTLK -> ARM = 0 -> both modules off, everything bleeds.
   The plug PHYSICALLY BLOCKS access to the links; the links cannot be reached with it fitted.
   Two microswitches under the carrier read the carrier's position -> MODE_PB, MODE_UNI.
```

- **The lead-break requirement becomes vacuous.** It is impossible to move a link before the LV loop
  has opened, because the LV plug is in the way. **Geometry, not contact sequencing.** MODE-15's
  margin question (O-11) is answered by construction and needs no timing spec at all.
- `S2` and `R_M1` collapse into link1's `X–M` position, `S3` into link2. The pole count drops from 3
  HV poles to 2 HV links.
- **Cost:** the operator needs a tool, and a wrong-position link is possible in a way a detented
  switch prevents (mitigated by the two position microswitches + the XOR decode of §6.2, which
  makes "neither valid" the default and safe).
- **This is not a concession.** The human's requirement is *"a physical thing the operator moves"*,
  and a mode change already requires re-cabling the instrument.

> **RECOMMENDATION.** Price both at G1. **Adopt Option A (three-position ceramic wafer switch, every
> fourth contact) if a part meeting SW-R1…SW-R6 can be sourced within the schedule; otherwise adopt
> Option B (guarded link block with captive interlock key), which is strictly stronger on timing and
> weaker only on operator convenience.** Do not adopt a two-position switch of unknown contact
> sequence in either case.

### 3.8 If a non-conforming switch is fitted anyway — the honest consequence

MODE-15 requires this to be stated without hiding it and without overstating it.

The dangerous transition is **UNIPOLAR → PSEUDO-BIPOLAR performed with both modules energised**. If
the aux poles do *not* lead, `S1`+`S2` close while the NEG module is at −1000 V and `OUT_A` is at
+1000 V. Then:

- **The steady-state outcome is a current-limited polarity fight, not an energetic fault.** Both
  modules are short-circuit protected and limited to ≈0.75 mA (PART-13). Total 1.5 mA into a
  20 kΩ series path (`R_S` + `R_M1`) — 30 mW. Nothing is destroyed.
- **A metallic arc is not physically available.** 0.75 mA is three orders of magnitude below the
  ~1 A minimum a tungsten arc needs `[recalled]` (TOPO-01).
- **The transient is the real stress and it is bounded by `R_M1`.** Two output capacitances at
  ±1000 V, worst credible 11.12 nF each (NUM-06), give 2000 V across the closing contact and
  **200 mA peak through `R_M1`** `[verified-run]` — 15× below the 3 A max-switch-current rating of
  the Pickering reeds and comfortably inside any wafer-switch contact. Energy 2 × 5.56 mJ = 11 mJ,
  63× below the 350 mJ hazardous-energy threshold `[recalled, unverified-primary]` (NUM-16).
- **What is actually at risk is contact plating**, exactly as Pickering Note 1 warns
  `[verified-artifact]`: repeated capacitive make-discharges degrade the plating and can weld.
  `R_M1` is what stands between that warning and this circuit.

**⇒ The consequence of a non-conforming switch is degradation and a detectable weld, not an
energetic hazard. That bounds it; it does not license it.** Record the weakening explicitly if it
ever happens (MODE-15's "must be recorded, not absorbed").

---

## 4. The HV relays K1 and K2

### 4.1 Selection

**Pickering Electronics `67-1-C-5/5D`** — Series 67, 1 Form C, switch #5, **5 V coil**, internal
diode. Read from the Series 67/68 datasheet, Issue 1.4 Apr 2022, this session `[verified-artifact]`:

| parameter | value | margin against this design |
|---|---|---|
| Switch form | 1 Form C (changeover) | NC → bleed, NO → bus: invariant (b) satisfied structurally |
| **Min. stand-off** | **5000 V** | vs the 2000 V worst-case fault across an open contact — **2.5×** |
| **Max. switching volts** | **2500 V** | vs 2000 V worst case — **1.25×**; vs the 1000 V normal case — **2.5×** |
| Power rating | 100 W | vs 0.75 W — 133× |
| Max switch current | **3 A** | vs 200 mA worst-case make through `R_S` — **15×** `[verified-run]` |
| Max carry current | 3.2 A | vs 0.75 mA — 4267× |
| **Operate time inc. bounce (max)** | **6 ms** | budgeted in §9.2 |
| **Release time** | **6 ms** | budgeted in §9.2 |
| Max contact resistance (initial) | 0.5 Ω | 0.375 µV at 0.75 mA — irrelevant |
| Insulation resistance (min, 25 °C) | 10¹⁰ Ω | 100 nA at 1 kV = 0.02 % of Inom, vs 1.25 % for the eliminated solid-state alternative |
| Life expectancy | **10⁸ ops** typical when cold-switching or below 1 mA; 10⁶ ops at up to 50 W resistive; *"considerably"* less under capacitive inrush | this design cold-switches and carries 0.75 mA — the 10⁸ column |
| Coil | **5 V, 40 Ω → 125 mA, 0.625 W** | §4.2 |
| Must-operate / must-release | ≤ 3.75 V / ≥ 0.5 V at 25 °C | 25 % pull-in margin on a 5 V rail |
| Screening | **internal mu-metal magnetic screen** | §4.3 |
| Contacts | tungsten-plated | the plating Note 1 warns about |
| Package | 58.4 × 12.6 × 14.5 mm, 13.58 g, SIL, Package Type 2, pins 1/3/5/7 | the long body supplies most of its own creepage for free |
| Operating temperature | −20 … +85 °C | bench |

**Availability remains the largest unpriced line in the combiner (R-7).** Session 1 established that
DigiKey does not list Pickering at all and that Newark lists `67-1-C-12/5` as SKU **40AK2389** but
would not serve a price to two independent agents `[verified-artifact]`. **This session did not price
it either.** Order at G1, not at fab.

### 4.2 Coil voltage — **TOPO-08's open question is closed here: 5 V coils**

TOPO-08/C-1 was written as *"the 12 V coil rail"* when a 12 V module family was assumed, and G0-A2
made that wrong (PART-30: there is no 12 V rail on this board). The datasheet decides it cleanly
`[verified-artifact, verified-run]`:

| option | coil R | current | **power** |
|---|---:|---:|---:|
| `67-1-C-5/5D` | 40 Ω | 125.0 mA | **0.625 W** |
| `67-1-C-12/5D` | 150 Ω | 80.0 mA | 0.960 W |
| `67-1-C-24/5D` | 600 Ω | 40.0 mA | 0.960 W |

**The 5 V coil is simultaneously the lowest-power option and the only one that needs no additional
rail.** Judge C's "missing 12 V rail" criticism is retired by choosing the part, not by generating a
rail. Specify the **`D` suffix** (internal flyback diode) — with an internal diode the coil polarity
is not optional and must be observed `[verified-artifact]`.

> **⬛ FINDING, REPORTED NOT SILENTLY ABSORBED.** `NUMBERS_PROBE.md` §6.2 budgets *"4 relay coils at
> 20 mA = 80 mA"*. The real figure for two Form-C coils simultaneously energised (which is normal in
> unipolar mode) is **250 mA**, plus ≈36 mA for the `K_S` interlock relay. The 5 V rail total moves
> from **888 mA to 1094 mA**, and the recommended supply from **5 V / 1.8 A to 5 V / 2.5 A** at the
> project's own 2.0× margin `[verified-run]`. **NUM-11 / NUM-21 must be re-run in the probe; this
> document does not edit the probe, per `CLAUDE.md` rule 1.**
>
> A coil economiser (series resistor bypassed by a capacitor, dropping hold current after pull-in)
> would recover ~60 % of the coil power. **Not adopted for the first build** — the must-release
> voltage is 0.5 V, so an economiser that overshoots drops the armature, and the failure is silent.
> Revisit only if the thermal budget forces it.

### 4.3 Magnetic exposure — the failure mode with no solid-state escape route (F-4, R-6)

A reed is closed by a magnetic field. **A stray magnet closes an HV contact with no coil current at
all**, and every coil-gating interlock layer is blind to it. Since G0-A2 eliminated the solid-state
combiner (TOPO-07), this must be mitigated in place; there is no alternative topology that lacks it.

**What this design does better than session 1's, and it is not nothing.** Session 1 wrote that a
magnet *"bypasses all three interlock layers at once, since every layer gates coil power"*. **That is
no longer true here**, because one layer does not gate coil power:

| layer | magnet-defeatable? |
|---|---|
| `K_S` pole B → HV relay coil exclusivity | **yes** — a magnet needs no coil current |
| Two Form-C reed armatures | **yes** |
| **`K_S` pole A + `U_P`/`U_N` → module `+VIN`** | **NO.** A magnet acting on a reed does not deliver input power to a module. `K_S` is a clapper-type relay with a return spring, not a reed. |
| **`/ON` open-drain drivers** | **NO** |
| **Mode switch HV poles `S1`/`S2`/`S3`** | **NO** — a magnet cannot turn a mechanical detent |

**Worst residual case, stated precisely.** Pseudo-bipolar mode, POS selected and at +1000 V; a
magnet closes `K2`. The NEG module has **no `+VIN`** (`K_S` pole A routes it to POS, and `S6` is
open in PB), so it produces nothing. What actually happens is that the NEG module's HV pin is
**connected to +1000 V through `R_S`**, and its own bleed is disconnected by the same contact. That
is not a both-modules-live fault; it is a **reverse-bias stress on an unpowered module output stage
whose reverse tolerance iseg does not publish** (PART-27, still open). It also removes the NEG
branch's bleed, which the per-branch monitor (§5.3) will see as `HV_NEG` following `OUT_A`.

**In unipolar mode a magnetically closed reed is not a fault at all** — it connects each module to
the output it belongs on.

**Mitigations, all specified:**

1. **The part is internally mu-metal screened** `[verified-artifact]`. This is the primary
   mitigation and it came free with the part choice.
2. **≥ 7.5 mm relay-to-relay spacing**, already forced by the HV clearance rule
   `[unverified-primary]`, which exceeds the ≥5 mm session 1 asked for.
3. **⬛ NEW: mount `K1` and `K2` with their long axes ORTHOGONAL.** A reed's sensitivity is strongly
   axial. Two relays at 90° cannot both be optimally coupled to one uniform stray field, so the field
   needed to close both simultaneously is much larger than the field needed to close one
   `[recalled — the axial-sensitivity ratio was not measured]`. This costs nothing at layout time and
   cannot be added later.
4. **Power-up weld/position self-test** (§9.4) detects a magnetically *held* contact exactly as it
   detects a welded one — but only at power-up, so a magnet applied mid-run is invisible to it.
   **Continuous detection comes from the per-branch monitors**: a parked branch that follows the
   output bus is a closed contact, and firmware checks it every acquisition cycle. **That is a
   genuine improvement over session 1, where a mid-run magnet was undetectable.**
5. **Enclosure requirement:** a mu-metal or steel shield can over the HV relay region if the lab is
   magnet-rich.

> ### ⬛ QUESTION FOR THE HUMAN — this one is consequential and has no fallback
>
> **What magnetic sources sit within ~1 m of where this instrument will live?** Specifically:
> permanent magnets (NdFeB blocks, magnetic bases/mounts, magnetic stirrers), superconducting magnet
> dewars or cryostats, ion pumps, unshielded transformers, or a magnetically levitated /
> magnetically trapped experiment. A 25 mm NdFeB disc produces of order **10 mT at 50 mm**
> `[recalled]`, and reed pull-in for this class is of order **1–5 mT** `[recalled — not measured, and
> Pickering publishes pull-in in ampere-turns, not tesla]`.
>
> **If the answer is "yes, routinely":** add the shield can (5) as a hard requirement, add a
> continuous magnetometer-free check by making the per-branch monitor comparison a **trip** rather
> than a log, and consider mounting the instrument at a stated minimum distance with a panel label.
> **There is no topology change available** — the solid-state alternative is gone (TOPO-07).

---

## 5. The HV network — values, ratings and the summed load budget

### 5.1 Component schedule

| ref | value | construction | rating | node |
|---|---|---|---|---|
| `K1`, `K2` | — | Pickering `67-1-C-5/5D` `[unverified-MPN]` | 5 kV standoff / 2.5 kV switching | POS, NEG |
| `R_S_P`, `R_S_N` | 10 kΩ | 1 × axial HV film (Ohmite MOX-400 class `[unverified-MPN]`) | ≥2 kV working | module HV pin → relay COM |
| `R_M1` | 10 kΩ | same | ≥2 kV working | `M` → `S2` |
| `R_G` | 10 kΩ | same | ≥2 kV working | `S3` common → GND |
| `R_bleed_POS`, `R_bleed_NEG` | 40 MΩ | **2 parallel strings of 2 × 40 MΩ**, 2512 HV (1500 V rated, 500 V/element, pad gap 4.925 mm vs 2.5 mm required) | per NUMBERS_PROBE §3.5 | `HV_POS`, `HV_NEG` (module side, **upstream of the relay**) |
| `R_bleed_A`, `R_bleed_B` | 40 MΩ | same | same | `OUT_A`, `OUT_B` |
| `R_X`, `R_M` | 400 MΩ | 2 parallel strings of 2 × 400 MΩ, 2512 HV | same | mode-switch stub nodes |
| `R_mon_A/B` (top) | 200 MΩ | **10 × 20 MΩ, 1206 HV**, 100 V/element — element count set by VCR, which goes as 1/N (ARCH-11) | 800 V rated part at 100 V used | invariant-(c) divider |
| `R_cold_A/B` (top) | 500 MΩ | 2 parallel strings of 2 × 500 MΩ, 2512 HV | 1500 V rated | **separate string**, C-2 |
| `R_branch_P/N` (top) | 1 GΩ | 2 parallel strings of 2 × 500 MΩ, 2512 HV | 1500 V rated | per-branch monitor, F-2 |

Bottom/offset networks for the monitor dividers are `NUMBERS_PROBE` §4.2's: `Ro` = 500 kΩ to a
2.500 V reference, `Rb` = 347.49 kΩ to GND, giving 0 V at mid-scale and a **sign-aware** ±1000 V →
0…2.048 V map. **Two of them, one per output** (MODE-07), each behind its **own** unity-gain
sub-nA-bias buffer (ARCH-08) and its **own driven guard ring at tap potential** (ARCH-14/F-8 — at
Rt = 200 MΩ a 10 GΩ board leakage path injects **20.0 V** of error, larger than the 10.0 V VMON
accuracy the divider exists to improve on; the guard ring is a requirement of the monitor, not a
refinement).

**Total HV passive count ≈ 64 elements.** That is the dominant contributor to the ~37 cm² HV-area
*floor* (`COMBINER_STUDY.md` §4, LIB-19, R-12). **Re-run the area model before placement.**

### 5.2 Standing load per module — summed for the first time since G0

`CONTROL_ARCHITECTURE.md` §2.10 records that *"nobody has summed the total standing and transient
load per module since G0"* and cites F-11 as the precedent for what happens when a load budget is
never actually summed. **Summed** `[verified-run]`:

| item | R | I at 1 kV | % of Inom |
|---|---:|---:|---:|
| **POS module → `OUT_A` (either mode)** | | | |
| module-side bleed | 40 MΩ | 25.00 µA | 5.00 % |
| per-branch monitor | 1 GΩ | 1.00 µA | 0.20 % |
| `OUT_A` output bleed | 40 MΩ | 25.00 µA | 5.00 % |
| `OUT_A` invariant-(c) divider | 200 MΩ | 5.00 µA | 1.00 % |
| `OUT_A` COLD divider | 500 MΩ | 2.00 µA | 0.40 % |
| **total** | | **58.00 µA** | **11.60 %** |
| **NEG module → `OUT_A` (pseudo-bipolar)** — adds the two stub bleeds | | **63.00 µA** | **12.60 %** |
| **NEG module → `OUT_B` (unipolar)** — `M` is grounded, only `X` loads | | **60.50 µA** | **12.10 %** |

**Worst standing load = 12.60 % of Inom, leaving 437 µA = 87.4 % for the user's load.** Budget was
15 % (`NUMBERS_PROBE` §3.4 uses 11 % for bleed + divider only). **PASS, but with only 2.4 points of
headroom — and in unipolar mode both modules carry a full copy of this. The budgets do not share and
do not average.**

The single biggest line is the bleed, at 5 % per node and 10 % when a relay is closed and both the
module-side and output-side bleeds sit on the same node. That is the price of NUM-09's
two-parallel-strings rule and of invariant (b) applying to four nodes.

### 5.3 Discharge — every node, every capacitance scenario `[verified-run]`

Effective node resistances: relay **closed** (module and output bleeds in parallel with all three
divider strings) = **17.24 MΩ**; relay **open** (output node alone) = **31.25 MΩ**; relay open with
**one of the two parallel bleed strings failed open** = **51.28 MΩ**.

| scenario (C) | relay closed → 60 V | relay open → 60 V | one string open → 60 V |
|---|---:|---:|---:|
| bare board (20 pF) | 0.049 s | 0.002 s | 0.003 s |
| 2 m SHV, no load (220 pF) | 0.059 s | 0.019 s | 0.032 s |
| 2 m SHV + 1 nF load | 0.108 s | 0.107 s | 0.176 s |
| **10 m SHV + 10 nF load (the NUM-13 interface limit)** | **0.583 s** | **0.969 s** | **1.590 s** |

**All well inside the 5 s touch-safety target `[recalled, unverified-primary]` (NUM-15), including
with a bleed string failed open.** This is the payoff of NUM-09: a single open element costs a factor
of ~1.6 in discharge time instead of removing the path.

`C_module` = 1 nF is **assumed** and is one of the four **MEASURABLE-NOW** parameters (PART-24). §11
states what changes if it comes back high.

### 5.4 Clearance and netclass consequences of this arrangement

Unchanged from `NUMBERS_PROBE` §2 except that this design **adds two HV nets** the probe's class
list does not have:

```
(rule "HV_POS to HV_NEG bipolar span"        (constraint clearance (min 15.0mm))
  (condition "A.NetClass == 'HV_POS' && B.NetClass == 'HV_NEG'"))
(rule "HV_OUT_A to HV_OUT_B bipolar span"    (constraint clearance (min 15.0mm))
  (condition "A.NetClass == 'HV_OUT_A' && B.NetClass == 'HV_OUT_B'"))
(rule "HV_M to HV_OUT_B span"                (constraint clearance (min 15.0mm))   ; NEW
  (condition "A.NetClass == 'HV_M' && B.NetClass == 'HV_OUT_B'"))
(rule "HV_X to HV_OUT_A/BUS_A span"          (constraint clearance (min 15.0mm))   ; NEW
  (condition "A.NetClass == 'HV_X' && B.NetClass == 'HV_OUT_A'"))
```

**Rationale for the two new pairwise rules, which is exactly F-4's argument one level further in:**
in unipolar mode `X` carries −1000 V while `BUS_A`/`OUT_A` carries +1000 V, and in pseudo-bipolar
mode `M` carries ±1000 V while `OUT_B` is at ground — so `X`↔`OUT_A` is a permanent 2000 V pair, and
`M`↔`OUT_B` is a 1000 V pair that becomes 2000 V only under an `S3` failure. **Ruling only the two
pairs `NUMBERS_PROBE` already has leaves the mode-switch wiring silently spaced for 7.5 mm.** Every
number here is **`[unverified-primary]`** and inherits NUM-01/NUM-02.

Also inherited, unchanged: NUM-04 (a `.kicad_dru` clearance constraint is per-layer 2-D, so all HV
copper must be single-layer, enforced as a generator invariant) and the F-3 defect in
`iseg_APS_THT.kicad_mod`'s 5.00 mm per-pad override (fix the generator, not the artifact).

---

## 6. The interlock — gate level

### 6.1 Signal inventory and fail-safe polarity

**The entire interlock gate array runs from +5 V and uses 74HCT-family parts**, so that (a) the
3.3 V ESP32 outputs meet `V_IH` = 2.0 V, and (b) **loss of the 3.3 V rail does not float any
interlock input** — every ESP32-sourced signal has duplicated pull-downs to GND and reads 0.

| signal | source | asserted = | fail-safe value | pull element (ARCH-18: **two in parallel**, placed apart) |
|---|---|---|---|---|
| `HB` | ESP32 GPIO, main-loop-serviced toggle | — | stops | pump reservoir 2 × 2 MΩ to GND |
| `EN_HB` | diode pump + Schmitt + **windowed watchdog** | firmware alive | **0** | §6.6 |
| `INTLK` | lid/door loop, **closed = 1** | safe to run | **0** | 2 × 10 kΩ to GND |
| `nOVP_A`, `nOVP_B` | latched hardware OVP per output | not tripped | **0** | latch resets to tripped on power-up |
| `SETTLE` | 74HCT123 retriggerable monostable | stable | **0** | — |
| `ARM_CMD` | ESP32 GPIO | armed | **0** | 2 × 100 kΩ to GND |
| `SEL` | ESP32 GPIO | 1 = NEG | **0 (= POS)** | 2 × 100 kΩ to GND |
| `EN_P`, `EN_N` | ESP32 GPIO | enable that module | **0** | 2 × 100 kΩ to GND |
| **`MODE_PB`** | **`SW1` pole `S4`**, contact to **+3.3 V** | switch is in PSEUDO-BIPOLAR | **0** | 2 × 100 kΩ to GND |
| **`MODE_UNI`** | **`SW1` pole `S5`**, contact to **+3.3 V** | switch is in UNIPOLAR | **0** | 2 × 100 kΩ to GND |
| `COLD_A`, `COLD_B` | window comparator on the **dedicated** COLD divider | \|V\| < ≈10 V | **0** | §6.5 |

**Why the mode aux contacts are wired to +3.3 V and not to ground.** A *broken wire* — the more
likely mechanical fault on a panel-mounted switch harness — then reads **0** on that pole. Both poles
broken reads `(0,0)` = "no valid mode" = `ARM` = 0. Wiring closed-to-ground with pull-ups would make
a broken wire read "in this mode", which is the wrong direction. Loss of the +3.3 V rail likewise
gives `(0,0)` and shuts HV off, which is correct (the heartbeat would stop anyway).

**Pin assignment constraint (§3.2 of `CONTROL_ARCHITECTURE.md`, ARCH-29):** none of `HB`, `ARM_CMD`,
`SEL`, `EN_P`, `EN_N`, `MODE_PB`, `MODE_UNI` may sit on an ESP32-S3 strapping pin (GPIO0, 3, 45, 46)
or on the USB pins (19, 20). Use the GPIO4–GPIO18 band. **This must be an executable check in the
schematic generator, not a review item.**

### 6.2 The logic

```
  ---- mode decode: POSITIVE decode of BOTH modes (MODE-18) -----------------
  VALID     = MODE_PB  XOR  MODE_UNI                       74HCT86
              (1,0)=pseudo-bipolar   (0,1)=unipolar
              (0,0)=SAFE detent / in transit / both wires broken  -> INVALID
              (1,1)=mechanically impossible -> a shorted aux      -> INVALID

  ---- the ARM chain -------------------------------------------------------
  ARM       = EN_HB . INTLK . nOVP_A . nOVP_B . SETTLE . VALID . ARM_CMD
              2 x 74HCT11 (triple 3-input AND), cascaded

  ---- the mode-aware permissive ------------------------------------------
  nSEL      = NOT SEL                                      74HCT14
  PERMIT_P  = ARM . EN_P . ( MODE_UNI + nSEL )             74HCT32 + 74HCT08
  PERMIT_N  = ARM . EN_N . ( MODE_UNI + SEL  )

  ---- module control -----------------------------------------------------
  /ON_P     = NOT PERMIT_P    open-drain (74HCT03), 2 x 10k pull-up to +VIN_P
  /ON_N     = NOT PERMIT_N    open-drain,           2 x 10k pull-up to +VIN_N
  U_P.EN    = PERMIT_P        per-module +VIN load switch  (primary disable, ARCH-19)
  U_N.EN    = PERMIT_N
  VSET_P shunt FET gate = /ON_P     (CONTROL_ARCHITECTURE 3.6 -- unchanged, still correct)
  VSET_N shunt FET gate = /ON_N

  ---- cold-switch latches (transparent; LE high = transparent) -----------
  REL_EN_P  = LATCH( D = PERMIT_P , LE = COLD_A )                  -> drives Q_K1
  REL_EN_N  = LATCH( D = PERMIT_N , LE = COLD_A . COLD_B )         -> drives Q_K2
  KS_SEL    = LATCH( D = SEL      , LE = COLD_A . COLD_B . nARM )  -> drives K_S coil

  ---- rails --------------------------------------------------------------
  Q_ARM   (module +5 V rail switch)  EN = ARM
  Q_COIL  (relay coil rail switch)   EN = EN_HB . INTLK . VALID        <-- C-1
```

**Read the safety property straight off the algebra.**

```
  PERMIT_P . PERMIT_N  =  ARM . EN_P . EN_N . ( MODE_UNI + nSEL ) . ( MODE_UNI + SEL )
                       =  ARM . EN_P . EN_N . ( MODE_UNI + SEL.nSEL )
                       =  ARM . EN_P . EN_N . MODE_UNI
```

Both modules can be *permitted* only when `MODE_UNI` = 1, i.e. only when the switch's own aux pole
says the armature is in the position that has already put the two modules on **different nodes**.
When `MODE_UNI` = 0 the expression collapses **bit for bit** to session 1's `SEL`/`¬SEL` gate, so
pseudo-bipolar behaviour is unchanged. `MODE_CMD` does not exist and appears nowhere (MODE-12).

**And — the part that matters more than the algebra — `MODE_UNI` is not what makes the forbidden
state physically possible.** Even with `MODE_UNI` falsely stuck at 1 while the switch is in
pseudo-bipolar, `S6` and `S7` are open, so `K_S` still routes `+VIN` and coil power exclusively and
only one HV relay can close. §7.5.

### 6.3 `K_S` — the single armature, and how it is released

**`K_S` = Panasonic `TQ2SA-5V`, 2 Form C, 5 V coil** `[unverified-MPN]`; session 1 verified it live
at DigiKey, 14 805 in stock, $2.65, 4 ms operate / 4 ms release `[verified-live-page, session 1]`.

| pole | COM | NO (`KS_SEL` = 0 → POS) | NC (`KS_SEL` = 1 → NEG) | bridged in UNIPOLAR by |
|---|---|---|---|---|
| **A** | `VIN_ARMED` (from `Q_ARM`) | `VIN_P_PRE` → `U_P` → `+VIN_P` | `VIN_N_PRE` → `U_N` → `+VIN_N` | **`S6`** shorts `VIN_P_PRE` ↔ `VIN_N_PRE` |
| **B** | `COIL_ARMED` (from `Q_COIL`) | `K1` coil high side | `K2` coil high side | **`S7`** shorts the two coil-feed nodes |

Coil low sides go to `Q_K1` / `Q_K2` (2N7002 `[unverified-MPN]`, gate = `REL_EN_P` / `REL_EN_N`,
2 × 100 kΩ gate pull-downs). So each HV relay needs **both** a high-side feed (from `K_S` or `S7`)
**and** its own low-side driver — two independent things, from two different control paths.

Contact loading `[verified-run]`: pole A carries ≤ 180 mA (one module) or, when `S6` bridges,
0 mA (the bridge carries it); pole B carries 125 mA (one coil). Against a 500 mA rating
`[unverified-MPN, confirm]` — 36 % and 25 %.

**F-5 (hot-making the LV armature into 22 µF) is retired, for free.** `KS_SEL`'s latch enable
includes `nARM`, and `Q_ARM` is gated by `ARM`; therefore whenever the armature is allowed to move,
`VIN_ARMED` = 0 V and the contact transfers **with no source behind it**. Additionally the 22 µF
datasheet-mandated blocking capacitors (PART-18) sit **downstream of `U_P`/`U_N`**, not on the `K_S`
contacts. Specify ≤ 1 µF on `VIN_P_PRE`/`VIN_N_PRE`.

### 6.4 Where the four mandatory corrections live in this circuit

| correction | where it is, concretely |
|---|---|
| **C-1** — fail-safe-open switch in the **relay coil rail**, gated by the same ALIVE/ARM element as the module supply switch | **`Q_COIL`**, a load switch in the 5 V coil rail with `EN = EN_HB · INTLK · VALID`. Both-coils-off is now reachable (stop the heartbeat), so **the weld self-test of §9.4 can execute** (retires F-1 and F-2's first half). ⚠ **Deliberate difference from C-1 as written, stated rather than hidden:** `Q_COIL` is gated by `EN_HB · INTLK · VALID`, **not** by the full `ARM`. Reason in §6.7 — a coil rail that drops on every `nOVP`/`ARM_CMD` event would force a **hot break** on every trip. `EN_HB`, `INTLK` and `VALID` are the three inputs for which "drop the coils immediately" is the right answer. |
| **C-2** — the COLD permissive gets its **own divider string**, physically separate from the invariant-(c) string; plus per-branch monitor dividers | `R_cold_A` / `R_cold_B` (500 MΩ, 2512 HV, two parallel strings) feeding two window comparators, **sharing no element, no reference and no buffer** with `R_mon_A/B`. Per-branch monitors `R_branch_P/N` (1 GΩ) on `HV_POS` and `HV_NEG` **upstream of the relays**. §6.5 shows the single-fault chain F-3 described is broken. |
| **C-3** — heartbeat from a **main-loop-serviced toggle** plus a **windowed** watchdog, not from an ESP32 timer/LEDC/RMT peripheral | §6.6. |
| **C-4** — every safe-state pull element **duplicated**, as an ERC rule | §6.1's table (every row) plus §6.8's executable rule. |

### 6.5 The COLD permissive, and why F-3's single-fault chain is broken

**What F-3 said.** With COLD derived from the *same* divider as invariant (c), one open HV resistor
makes the monitor read "0 V", which forces COLD permanently TRUE, which makes the latch permanently
transparent, which makes **hot switching possible on every changeover** — and hot switching is the
mechanism that welds the contact. One cracked resistor converts a random 10⁸-op wear-out into a
systematic consequence of normal operation, while removing the monitor that would show it.

**What this design does.** Three changes, and all three are needed:

1. **Separate string** (C-2). `R_cold` and `R_mon` are physically different parts on different nets
   with different values, different element counts, and different bottom/offset networks fed from
   **different references**. One open element can blind one, never both. The monitor-disagreement
   trip at 2 %·Vnom (ARCH-23) then sees it.
2. **⬛ `R_cold` is built as two parallel 1 GΩ strings (NUM-09), and that turns the catastrophic
   fault into a bounded error.** If one string opens, the divider ratio doubles: COLD then asserts
   at up to **20 V instead of 10 V** `[verified-run]`. **20 V is still a cold switch** — it is well
   under the tens-of-volts threshold at which reed-contact make-discharge matters, and the energy in
   a 11 nF node at 20 V is 2.2 µJ. **A single open element in the COLD string degrades the threshold
   by 2×; it does not force COLD true.** That is the difference between a defect and a hazard.
3. **An executable self-test at every enable** (§9.4 test 4): command a known non-zero output and
   require COLD to go **false**. A COLD comparator stuck at 1 (fault 20 in session 1's table) is
   then caught before any changeover. Comparator choice reinforces this: **push-pull output
   (TLV3201/TLV3202 `[unverified-MPN]`), never open-drain-with-pull-up** — an open-drain failure
   pulls up to a false COLD = 1, which is the wrong stuck-state.

**COLD divider design** `[verified-run]`: `Rt` = 500 MΩ, `Rb` = 1.0 MΩ ⇒ ratio **501 : 1**.
`V_safe` = 10 V → **19.96 mV** at the tap; 1000 V → 1.996 V. With a TLV3201's 1.0 mV typical
(3.5 mV max) input offset, the threshold uncertainty referred to the HV node is **±0.50 V typical,
±1.75 V worst** — 5 % to 17 % of the 10 V threshold, which is fine because the threshold itself is
a soft "tens of volts" criterion. The divider needs the same offset-leg trick as the monitor (its own
1.25 V reference, e.g. REF3012 `[unverified-MPN]`) so that a **negative** output produces an
in-range tap; COLD is then a genuine **window** comparator (`|V_tap − V_ref| < 20 mV`), i.e. it is
sign-blind by design, which is exactly what a "is this node cold?" question wants.

`COLD = COLD_A · COLD_B` where each is the AND of its window's two halves.

### 6.6 The heartbeat (C-3)

```
  GPIO_HB --[22nF]--[22nF]--+--|<|--+-- EN_HB_RAW --+-- 74HCT14 --> pump_ok
       (two caps IN SERIES) |       |               |
                           |<|    100nF          2 x 2M
                            |       |               |
                           GND     GND             GND

  EN_HB = pump_ok  .  WDT_OK
```

- **Two coupling capacitors in series** (22 nF each ⇒ 11 nF effective): a single shorted capacitor
  still leaves one, so a static GPIO level cannot hold `EN_HB`.
- **Reservoir 100 nF / 2 MΩ ∥ 2 MΩ = 1 MΩ**, τ = 100 ms ⇒ `EN_HB` falls below the HCT threshold
  **≈79 ms** after the toggle stops `[verified-run, session 1]`. Shorter than the module's own
  100 ms set-node pole (PART-07), so the hardware chop is faster than the module could have ramped.
- **`GPIO_HB` is toggled ONLY from the main loop.** Not from LEDC, RMT, a hardware timer, or an ISR.
  A peripheral free-runs through the exact application hang the pump exists to detect (ARCH-20).
- **`WDT_OK` comes from a separate WINDOWED watchdog supervisor** (e.g. `MAX6746`-class
  `[unverified-MPN]`) that faults on kicks that are **too fast** as well as too slow. This is what
  catches a peripheral that *is* free-running: a hardware-timer-driven toggle is *too regular and
  too fast* relative to a main loop that also services I²C, SPI and the network stack.
- `EN_HB` = `pump_ok · WDT_OK`. Either failing drops `ARM` **and** `Q_COIL`.

### 6.7 Cold make, cold break, and the trap that must not recur

Session 1 documented a "showstopper trap" it fell into: gating the coil supply with "bus is cold"
means that as soon as the output rises, the gate opens and the relay drops out **while HV is live**.
Its fix was a transparent latch with `LE = COLD`. **That fix is correct and is kept, but it is not
sufficient once each output can be enabled independently**, because dropping `EN_P` in unipolar mode
would otherwise release `K1` into a hot `OUT_A`.

**The resolution — and it is the design's neatest result — is to separate the module enable from the
relay enable and latch only the latter:**

```
  PERMIT_P   (module: +VIN and /ON)   free to change at any instant
  REL_EN_P = LATCH(D = PERMIT_P, LE = COLD_A)   (relay coil)
```

| action | what happens | is the contact cold? |
|---|---|---|
| **turn ON** `OUT_A` | `OUT_A` was off ⇒ `COLD_A` = 1 ⇒ latch transparent ⇒ `K1` closes in 6 ms; the module then takes ≥150 ms to start and ≥100 ms/τ to ramp | **yes** — the relay closes before any HV exists |
| **turn OFF** `OUT_A` | `PERMIT_P` → 0 ⇒ module dead immediately; `OUT_A` is hot ⇒ `COLD_A` = 0 ⇒ **latch opaque ⇒ `K1` stays closed** ⇒ module-side and output-side bleeds are in **parallel**, discharging faster (17.24 MΩ vs 31.25 MΩ); when `COLD_A` asserts, the latch goes transparent and `K1` releases | **yes** — and the "stuck closed" interval is *helping* |
| **polarity changeover** | `EN_P`→0, wait for `COLD_A`, `K1` releases cold; `SEL` toggles ⇒ `SETTLE`→0 ⇒ `ARM`→0; `KS_SEL` latch (`LE = COLD_A · COLD_B · nARM`) transfers `K_S` **with zero volts on it**; `EN_N`→1 ⇒ `K2` closes cold | **yes, at every contact** |

**There is no circularity**, because the thing that makes the node cold (removing `+VIN` and raising
`/ON`) is *not* the thing that is latched.

**The one place a hot break is still possible, stated rather than papered over.** `Q_COIL` is gated
by `EN_HB · INTLK · VALID`. If firmware dies, the lid opens, or the mode switch moves, `Q_COIL`
opens and **both relays release immediately, possibly at up to 1000 V.** That is deliberate:

- A hot **break** at 0.75 mA cannot sustain an arc — three orders below the ~1 A a tungsten arc
  needs `[recalled]` — and the mechanism Pickering's Note 1 warns about is the **capacitive make**
  discharge, not the break `[verified-artifact]`.
- The alternative — keeping the coils alive through a lid-open or firmware-death event so the
  contacts can cool — would mean **holding a module bonded to an output terminal while nothing is
  supervising it.** That is worse.

> **DESIGN RULE.** *Guarantee cold MAKE absolutely. Tolerate a hot BREAK on emergency paths only,
> and never on a normal-operation path.* Every normal-operation break in §9 is cold.

### 6.8 The duplicated-pull rule, made executable (C-4)

Nets that carry a safe-state pull element, each of which **must** have exactly two parallel resistors
of equal value to the same rail, placed at least 5 mm apart so one solder defect cannot take both:

`ON_P`, `ON_N` (pull-**up** to each module's own `+VIN`, within 5 mm of pin 4 — ARCH-17),
`ARM_CMD`, `SEL`, `EN_P`, `EN_N`, `MODE_PB`, `MODE_UNI`, `INTLK`, `HB_RESERVOIR`,
`VSET_P`, `VSET_N` (pull-**down** at the module pin — ARCH-05/REF-03),
`Q_K1_GATE`, `Q_K2_GATE`, `Q_ARM_EN`, `Q_COIL_EN`.

> **Implement as a domain assertion in `board_spec.py`** (`INTERFACES.md` §1.3 — promoted from review
> to build failure), not as a schematic-review checklist item:
> ```python
> SAFE_STATE_PULLS = { "/ON_P": ("+VIN_P", "up"), "/ON_N": ("+VIN_N", "up"),
>                      "ARM_CMD": ("GND", "down"), "SEL": ("GND", "down"), ... }
> def assert_duplicated_pulls(spec):
>     for net, (rail, sense) in SAFE_STATE_PULLS.items():
>         rs = [r for r in spec.resistors if r.connects(net, rail)]
>         assert len(rs) == 2, f"{net}: {len(rs)} pull elements, need exactly 2 (ARCH-18)"
>         assert rs[0].value == rs[1].value
>         assert spec.distance(rs[0], rs[1]) >= 5.0
> ```
> Exit 1 on failure. **An open pull element restores the module's documented unsafe default:
> `/ON` open ⇒ HV ON (PART-02); `VSET` open ⇒ full scale (PART-04); and on a 2.5 V-Vref module a
> node pulled to 3.3 V commands ≈1320 V (PART-33).**

---

## 7. Truth tables

### 7.1 Mode decode — every combination of the two aux poles

| `MODE_PB` | `MODE_UNI` | physical reality | `VALID` | `ARM` | `S6`/`S7` bridges | HV poles | verdict |
|:-:|:-:|---|:-:|:-:|---|---|---|
| 1 | 0 | switch in **PSEUDO-BIPOLAR** | **1** | permitted | **open** | `X`→`M`→`BUS_A`; GND→`OUT_B` | normal mode 1 |
| 0 | 1 | switch in **UNIPOLAR** | **1** | permitted | **closed** | `X`→`OUT_B`; GND→`M`; `S2` open | normal mode 2 |
| 0 | 0 | **SAFE detent**, in transit, both wires broken, or +3.3 V lost | **0** | **0** | open | all open | **both modules OFF, all four nodes bled** (MODE-18) ✓ |
| 1 | 1 | mechanically impossible ⇒ a **shorted or welded aux contact** | **0** | **0** | (per real position) | (per real position) | **fault detected and safe** ✓ |

> **The `(1,1)` row is why MODE-18 demands positive decode of *both* modes.** If unipolar were encoded
> as "the absence of pseudo-bipolar", a single shorted `MODE_UNI` line would read as a valid unipolar
> mode while the switch was physically in pseudo-bipolar. With the XOR, that same fault produces
> `(1,1)` ⇒ `VALID` = 0 ⇒ `ARM` = 0. **One extra contact and one XOR gate convert the worst
> single-fault on the mode path into a benign shutdown.**

### 7.2 The `ARM` chain — every input, one at a time

| `EN_HB` | `INTLK` | `nOVP_A` | `nOVP_B` | `SETTLE` | `VALID` | `ARM_CMD` | `ARM` | `Q_ARM` | `Q_COIL` | outcome |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| **0** | X | X | X | X | X | X | **0** | off | **off** | both modules unpowered, both relays release to NC bleeds |
| X | **0** | X | X | X | X | X | **0** | off | **off** | lid open ⇒ same, **with no firmware involvement** |
| 1 | 1 | **0** | X | X | X | X | **0** | off | on | OVP_A latched; relays hold until cold, then release (§6.7) |
| 1 | 1 | X | **0** | X | X | X | **0** | off | on | OVP_B latched; same |
| 1 | 1 | 1 | 1 | **0** | X | X | **0** | off | on | any `SEL` or `MODE` edge ⇒ dwell; both modules off |
| 1 | 1 | 1 | 1 | 1 | **0** | X | **0** | off | **off** | no valid mode ⇒ everything off and bled |
| 1 | 1 | 1 | 1 | 1 | 1 | **0** | **0** | off | on | disarmed (ARCH-35): relays may hold, modules cannot power |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | **1** | on | on | armed |

### 7.3 The permissive — every reachable operating combination

`ARM` = 1 throughout. `X` = don't care.

| # | `MODE_PB` | `MODE_UNI` | `SEL` | `EN_P` | `EN_N` | `PERMIT_P` | `PERMIT_N` | `K_S` A/B | `K1` | `K2` | node(s) occupied | verdict |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|:-:|:-:|---|---|
| 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | POS | open | open | none — both bled | idle, mode 1 |
| 2 | 1 | 0 | 0 | **1** | 0 | **1** | 0 | POS | **closed** | open | `OUT_A` ← POS | mode 1, positive ✓ |
| 3 | 1 | 0 | 0 | 1 | **1** | **1** | **0** | POS | closed | open | `OUT_A` ← POS | **firmware asked for both; hardware gave one.** `PERMIT_N` = 0 because `MODE_UNI` = 0 and `SEL` = 0 ✓ |
| 4 | 1 | 0 | **1** | 0 | 1 | 0 | **1** | NEG | open | **closed** | `OUT_A` ← NEG (via `X`,`M`,`S2`) | mode 1, negative ✓ |
| 5 | 1 | 0 | 1 | **1** | 1 | **0** | **1** | NEG | open | closed | `OUT_A` ← NEG | both asked, one given ✓ |
| 6 | 0 | 1 | X | 1 | 0 | **1** | 0 | bridged | **closed** | open | `OUT_A` ← POS; `OUT_B` idle+bled | mode 2, A only ✓ |
| 7 | 0 | 1 | X | 0 | 1 | 0 | **1** | bridged | open | **closed** | `OUT_B` ← NEG; `OUT_A` idle+bled | mode 2, B only ✓ |
| 8 | 0 | 1 | X | **1** | **1** | **1** | **1** | bridged | **closed** | **closed** | `OUT_A` ← POS, `OUT_B` ← NEG | **mode 2, both live — permitted, and safe because the armature has physically split the nodes** ✓ |
| 9 | 0 | 0 | X | 1 | 1 | 0 | 0 | — | open | open | none | SAFE detent ✓ |
| 10 | 1 | 1 | X | 1 | 1 | 0 | 0 | — | open | open | none | aux fault ✓ |
| — | — | — | — | — | — | **1** | **1** | with `MODE_PB` = 1 | — | — | — | **UNREACHABLE**: requires `MODE_UNI` = 1 ∧ `MODE_PB` = 1 ⇒ `VALID` = 0 ⇒ `ARM` = 0 ⇒ both permissives 0 |

**Rows 3 and 5 are the ones to look at.** They are the states in which firmware has asserted both
enables in pseudo-bipolar mode — the exact "two signals firmware promised never to co-assert"
scenario the task warns about. **The hardware does not need firmware to have kept that promise**:
`PERMIT_P · PERMIT_N = ARM · EN_P · EN_N · MODE_UNI` is zero whenever `MODE_UNI` is zero, and
`MODE_UNI` is a contact on the mode switch.

### 7.4 Degenerate power/boot states

| condition | what every relevant node does | outcome |
|---|---|---|
| **ESP32 held in reset** (all GPIO high-Z) | `ARM_CMD`, `SEL`, `EN_P`, `EN_N` → 0 via duplicated 100 kΩ pull-downs; `HB` stops ⇒ `EN_HB` → 0 in **79 ms**; `MODE_*` unaffected (they come from the switch, not the MCU) | `ARM` = 0, `Q_ARM` off, `Q_COIL` off, both relays to NC, all four nodes bled. **< 60 V within 0.06–0.97 s** depending on `C_load` `[verified-run]` ✓ |
| **ESP32 unpowered while the 5 V HV rails are up** (3.3 V buck failed) | identical to reset. The interlock array runs from **5 V**, so its own inputs do not float; the pull-downs are to GND | ✓ **This is why the gate array is 74HCT on 5 V and not 74HC on 3.3 V.** |
| **Mid-boot, strapping pins driven by the boot ROM** | no interlock signal sits on a strapping pin (§6.1); `EN_HB` is 0 until the main loop starts toggling | ✓ |
| **Firmware alive but hung with GPIOs stuck high** | `HB` stops toggling ⇒ pump decays; **and** the windowed watchdog faults if a free-running peripheral is still toggling it | ✓ **This is the case C-3 exists for.** |
| **5 V logic rail lost while HV rails up** | impossible in isolation — the modules run from the same 5 V. Under a partial brown-out: open-drain `/ON` drivers release, pull-ups to each module's own `+VIN` (which is collapsing with them) hold `/ON` high; coil rail collapses; relays release to NC | ✓ |
| **`SW1` moved while energised** | first aux-pole edge ⇒ `SETTLE` → 0 **and** `VALID` → 0 (the SAFE detent) ⇒ `ARM` = 0 within < 100 ns, `Q_ARM` and `Q_COIL` off within < 100 µs, relays released within 6 ms | ✓ hardware-only. Firmware additionally latches a trip — §9.3 |
| **Mode switch parked between detents indefinitely** | `(0,0)` ⇒ `VALID` = 0 permanently; `X` and `M` held by `R_X`/`R_M`; `OUT_A`/`OUT_B` on their own bleeds | ✓ MODE-18 satisfied |

### 7.5 Proof of the theorem (§1.3)

The forbidden state is **both `K1` and `K2` closed AND the HV routing joining their far sides**.
Enumerate what each requires.

**`K1` closed** requires: `Q_COIL` on **AND** `K_S` pole B at NO (or `S7` closed) **AND** `Q_K1` on
(`REL_EN_P` = 1).
**`K2` closed** requires: `Q_COIL` on **AND** `K_S` pole B at NC (or `S7` closed) **AND** `Q_K2` on.

⇒ **Both closed requires either `S7` closed, or `K_S` pole B touching NO and NC simultaneously.**

1. **`K_S` pole B touching both throws is a single-armature contradiction.** Not a truth table — one
   moving contact. Defeated only by a physical bridge/weld across the pole, which is a mechanical
   fault, not a logic state, and which the power-up self-test detects (§9.4 test 5).
2. **`S7` closed requires the mode switch to be physically in the UNIPOLAR detent** — and in that
   detent `S1` routes `X` to `OUT_B`, `S2` is open, and `S3` grounds `M`. **`K1`'s far side is
   `OUT_A`; `K2`'s far side is `OUT_B`. Different nodes.** The invariant holds.
3. **No gate output, stuck or otherwise, appears in either requirement.** `Q_K1`/`Q_K2` are gated by
   `REL_EN_P`/`REL_EN_N`, but those are *necessary*, not *sufficient* — the high-side feed is the
   binding term and it is mechanical.
4. **No firmware or network state appears.** `MODE_CMD` does not exist (MODE-12). A falsely asserted
   `MODE_UNI` *logic* line relaxes `/ON` but does **not** close `S6` or `S7`, so it produces "both
   modules internally making HV" with **only one of them connected to any output node** — an
   abnormal, detectable, non-forbidden state (§8 row F-11).

**To reach the forbidden state you need**, at minimum: *(a)* a welded/bridged `K_S` pole B **and** a
welded `Q_K1` or `Q_K2` (two faults, in pseudo-bipolar mode); or *(b)* a welded `S7` **and** a false
`MODE_UNI` **and** the switch in pseudo-bipolar (three faults); or *(c)* a welded HV reed contact —
which puts one module permanently on `OUT_A` and makes the *next* selection of the other module a
violation (one mechanical fault, **the topology's admitted and unremovable weakness**, TOPO-10/R-8,
detected by §9.4 test 1 and continuously by the per-branch monitors).

> **HONEST FORMULATION FOR THE GATE REVIEW.** *This circuit makes the forbidden state unreachable
> through any electrical, logic, firmware, network, driver or wiring fault, and through any single
> fault of the mode element. It remains reachable through a welded HV reed contact, which is
> detectable at power-up and continuously, and which no contact-based topology can prevent.* Q6 was
> **not answered at G0** — if prevention is ever required rather than detection, this design dies with
> every other candidate (TOPO-10).

---

## 8. Single-fault analysis

Format: fault → what the circuit does → what the **output terminals** do → verdict.

| # | fault | behaviour | verdict |
|---|---|---|---|
| **Broken wires, one per control line** | | | |
| F-1 | `ARM_CMD` open | duplicated pull-downs ⇒ 0 ⇒ `ARM` = 0 | both off, all bled ✓ |
| F-2 | `SEL` open | pull-downs ⇒ 0 ⇒ `K_S` latch (when transparent) writes POS; `PERMIT_N` = 0 in pseudo-bipolar | NEG becomes unselectable. **If firmware believed NEG was selected, the terminal produces the wrong polarity.** Caught only by the **sign-aware** independent monitor (ARCH-10) and the disagreement trip (ARCH-23). **This is the concrete reason the monitor must report sign.** ⚠ |
| F-3 | `EN_P` or `EN_N` open | pull-downs ⇒ that module never enables | that output dead ✓ |
| F-4 | `HB` open | pump decays ⇒ `EN_HB` = 0 in 79 ms ⇒ `ARM` = 0 **and** `Q_COIL` off | both off within ≈85 ms ✓ **the payoff of AC-coupling** |
| F-5 | `INTLK` loop open | `ARM` = 0, `Q_COIL` off, no firmware involved | both off ✓ |
| F-6 | `MODE_PB` open, switch in PSEUDO-BIPOLAR | reads `(0,0)` ⇒ `VALID` = 0 | instrument refuses to arm. **Safe, and loudly broken rather than quietly wrong** ✓ |
| F-7 | `MODE_UNI` open, switch in UNIPOLAR | in that detent `S4` is open anyway, so the pair reads `(0,0)` ⇒ `VALID` = 0 ⇒ `ARM` = 0. The HV poles are correctly in the unipolar position but nothing is permitted | instrument refuses to arm ✓ |
| F-8 | `MODE_UNI` open **and** `MODE_PB` shorted to +3.3 V, switch in UNIPOLAR | reads `(1,0)` = "pseudo-bipolar". Logic enforces exclusivity, but `S6`/`S7` **are** closed (real position) and the HV poles route to two nodes. Only one module can be enabled at a time; both terminals still work, one at a time. **`MODE?` reports the wrong mode — a shock-hazard-relevant lie (MODE-09).** | **two faults**, but see the boot cross-check below ⚠ |
| F-9 | `/ON_P` harness open, module side | `/ON` floats ⇒ **HV ON** per PART-02 | **Unsafe on that pin alone** — mitigated because `+VIN` is the primary disable (ARCH-19) and `U_P` is off. Route `/ON` and `+VIN` in one bundle; sequence the connector so `+VIN` breaks first. Accepted residual, unchanged from session 1 |
| F-10 | `VSET` open | internal 10 kΩ to Vref ⇒ **full scale** (PART-04) | module ramps toward 1000 V; **`nOVP` fires at 1050 V and latches ⇒ `ARM` = 0 ⇒ `Q_ARM` off**. Overshoot bounded by the 100 ms set-node pole: the output reaches the trip point ~159 ms after the fault and the comparator responds in µs. **The hardware OVP closes session 1's open fault 15.** ✓ |
| **Stuck/short faults** | | | |
| F-11 | `MODE_UNI` **shorted to +3.3 V** while in PSEUDO-BIPOLAR | `(1,1)` ⇒ `VALID` = 0 ⇒ `ARM` = 0 | **the worst-looking fault on the mode path is benign** ✓ (§7.1) |
| F-12 | `S6` (`+VIN` bridge) **welded closed** while in PSEUDO-BIPOLAR | both modules can receive `+VIN`; but `PERMIT_P·PERMIT_N` = 0 (`MODE_UNI` = 0), so only one has `/ON` low, and `K_S` pole B still feeds one coil | one module on `OUT_A`. **Invariant holds** ✓ |
| F-13 | `S7` (coil bridge) welded closed while in PSEUDO-BIPOLAR | both coils can be fed; but `REL_EN_P·REL_EN_N` requires `PERMIT_P·PERMIT_N` = 0 | one relay closes ✓ |
| F-14 | **`S6` and `S7` both welded** while in PSEUDO-BIPOLAR | still requires `PERMIT_P·PERMIT_N`, which requires `MODE_UNI` = 1, which with `MODE_PB` = 1 gives `VALID` = 0 | ✓ — **three faults needed** |
| F-15 | `K1` HV contact **welded at NO** | POS permanently on `BUS_A`/`OUT_A`. Selecting NEG in pseudo-bipolar then puts both on one node | **the topology's central weakness.** Bounded by 15–30× make-current margin and 10⁸-op cold-switch life. **Detected** at power-up (§9.4 test 1) and continuously by the per-branch monitor. **Not preventable** (TOPO-10) |
| F-16 | `K1` armature stuck at NC / coil open | POS never reaches the output; the POS module, if enabled, sits at up to 1 kV into its own 40 MΩ bleed | fail-safe at the terminal; **visible** on the per-branch monitor — this is what the C-2 per-branch dividers are for ✓ |
| F-17 | `Q_K1` FET drain–source short | `K1` coil low side permanently grounded; still needs the high-side feed from `K_S`/`S7` | degrades to one layer, still exclusive ✓ |
| F-18 | `U_P` load switch shorted (stuck ON) | POS module powered whenever `K_S` selects it; HV then depends on `/ON`, which defaults HIGH via duplicated pull-ups | still off ✓ |
| F-19 | `Q_ARM` shorted | modules powered whenever the board is; `/ON` still high; `K_S` still exclusive | still off ✓ |
| F-20 | `Q_COIL` shorted | coil rail always live; both-coils-off no longer reachable ⇒ **the weld self-test cannot run** | **detect it**: the self-test's first step is "de-assert `EN_HB`, confirm both branch monitors show the relays released". If they do not, latch a fault and refuse to arm. **A self-test whose precondition is unverified is F-2 all over again** |
| F-21 | COLD comparator stuck at 1 | latches always transparent ⇒ hot switching becomes possible | caught by §9.4 test 4 (raise HV, require COLD to fall). Push-pull comparator so the *likely* failure sits at 0 |
| F-22 | COLD comparator stuck at 0 | no changeover ever possible | stuck-safe ✓ |
| F-23 | one of `R_cold`'s two parallel strings opens | ratio doubles ⇒ COLD asserts up to 20 V instead of 10 V | **still a cold switch** `[verified-run]` ✓ — NUM-09 doing its job |
| F-24 | invariant-(c) divider top string open | monitor reads "0 V" while the output may be at full scale | **does NOT force COLD true** (separate string, C-2) — **F-3's single-fault chain is broken.** Caught by the disagreement trip vs VMON (ARCH-23) and by the enable-time self-test |
| F-25 | `R_bot` of a monitor divider open | tap rises toward the bus | prevented by the mandatory 100 kΩ + BAV99 clamp to rails + 3.6 V TVS, and `R_bot` built as 2 × 2 MΩ in parallel |
| F-26 | one bleed string open (any of the four nodes) | τ rises from 344 ms to 565 ms at the worst capacitance ⇒ 60 V in **1.59 s** instead of 0.97 s | ✓ inside the 5 s target. **An open bleed is silently undetectable** (NUM-09) ⇒ NUM-10's decay-τ self-test is mandatory (§9.4 test 3) |
| F-27 | `S3` fails open (mode switch) in PSEUDO-BIPOLAR | `OUT_B` loses its ground **bond** but keeps its 40 MΩ bleed; nothing drives it | `OUT_B` stays within µV of ground. **Degraded, not hazardous** ✓ |
| F-28 | `S3` welded (either throw) | the welded node is permanently grounded ⇒ that output/`M` cannot rise | **every mode-switch weld fails toward "output grounded"** — a direct consequence of giving `S3` a grounded common. Detected by §9.4 test 6 ✓ |
| F-29 | `S2` welded closed while in UNIPOLAR | `M` ↔ `BUS_A` closed, but `S3` grounds `M` ⇒ `OUT_A` is grounded through `R_G` + `R_M1` = 20 kΩ | POS output cannot rise; **detected**, and the failure direction is safe ✓ |
| F-30 | `S1` welded (both throws) while in UNIPOLAR | `X` connects to both `M` (grounded) and `OUT_B` ⇒ NEG output grounded through 10 kΩ | detected, safe ✓ |
| F-31 | **stray magnet closes `K2` in pseudo-bipolar with POS live** | NEG module has no `+VIN` ⇒ makes nothing; its HV pin is reverse-stressed to +1000 V through `R_S`, and its bleed is disconnected | **PART-27 (reverse tolerance) is unpublished and still open.** Detected by the per-branch monitor (`HV_NEG` follows `OUT_A`). §4.3 |
| F-32 | HV relay coil shorted turn | 125 mA nominal becomes higher through `Q_COIL` | `Q_COIL` is a current-limited load switch with a 500 mA limit; alternatively a 500 mA polyfuse in the coil rail |
| F-33 | `C_load` far above the interface limit (e.g. 1 µF) | 60 V not reached within 5 s; capacitive make energy exceeds the `R_M1`/`R_S` design point | bounded **only** by the declared `C_load ≤ 10 nF` interface constraint (NUM-13). **Consider a permanently-fitted in-line HV series resistor in the output cable** to enforce it physically |

---

## 9. State machine, sequences and timeouts

### 9.1 Structure — a supervisor plus two per-output machines (Gap 2, `CONTROL_ARCHITECTURE.md` §5.1)

Session 1's single machine is written for one output. **In unipolar mode the two outputs are
independent**, so:

```
SUPERVISOR                        PER-OUTPUT (one instance for A, one for B)
  G0 SAFE       (ARM_CMD = 0)       O0 OFF        PERMIT = 0, relay released, node bled
  G1 SELFTEST   (§9.4)              O1 RAMP       PERMIT = 1, DAC stepping
  G2 ARMED      (ARM_CMD = 1)       O2 REG        at setpoint, inside the window
  G3 RUN                            O3 RAMP_DOWN  target forced to 0
  G7 TRIP       (latched)           O4 DISCHARGE  PERMIT = 0, waiting on a MEASUREMENT
                                    O5 CHANGEOVER (pseudo-bipolar only; §9.2)
```

The supervisor owns everything shared: `ARM_CMD`, the interlock, both OVPs, the mode reading, the
trip latch. In **pseudo-bipolar** mode output B's machine is forced to `O0` and its commands are
**rejected with an error**, never silently ignored (MODE-12, REF-05 anti-pattern). In **unipolar**
mode the two machines run independently and `O5` is unreachable.

**This split is a design decision, made here explicitly rather than left to whoever writes the
firmware first** (Gap 2's warning).

### 9.2 Pseudo-bipolar polarity changeover, step by step

| step | action | guard / timeout | on timeout |
|---|---|---|---|
| 1 | `O3`: ramp the active output's DAC to 0 at ≥300 ms/step (PART-07: the set node's τ is 100 ms; stepping faster makes \|MEAS−target\| meaningless) | `\|Δ\|/slew + 3 s` | → `G7` `+106` |
| 2 | `O4`: `EN_x` → 0 ⇒ `PERMIT_x` → 0 ⇒ `+VIN` removed and `/ON` high **immediately**. `K1`/`K2` stay closed (latch opaque) so both bleeds work in parallel | — | — |
| 3 | wait for `\|MEAS\| < V_safe` = 10 V **sustained 500 ms**, measured on the **independent** monitor. Nominal **97 ms**, worst **954 ms** `[verified-run]` | **30 s** | **→ `G7` `+103`. TRIP. Do NOT switch. ARCH-24 / §5.3 — this is the one transition that must never fall through.** |
| 4 | `COLD_A` (and `COLD_B`) assert ⇒ `REL_EN` latches transparent ⇒ the closed relay releases **cold** | 200 ms to observe the branch monitor change | → `G7` |
| 5 | toggle `SEL` ⇒ the RC-XOR edge detector fires the 74HCT123 ⇒ `SETTLE` = 0 for **`T_dwell_hw` = 0.5 s** ⇒ `ARM` = 0 ⇒ `Q_ARM` off | — | — |
| 6 | with `ARM` = 0 and both COLDs true, `KS_SEL`'s latch is transparent ⇒ `K_S` transfers, **4 ms operate / 4 ms release, with 0 V on its contacts** | 200 ms | → `G7` `+103` |
| 7 | `SETTLE` re-asserts ⇒ `ARM` = 1 ⇒ `EN_y` → 1 ⇒ the new relay closes (**6 ms incl. bounce**) into a cold node, then `+VIN` is applied | 200 ms | → `G7` |
| 8 | `O1`: module restart (**150 ms, assumed, MEASURABLE-NOW**) + set-node charge (4.6 τ = 460 ms to 1 %, 6.9 τ = 690 ms to 0.1 %) | as step 1 | → `G7` `+106` |

**Dead-band budget** `[verified-run]`:

| term | nominal | worst (10 m cable + 10 nF load) |
|---|---:|---:|
| T1 decay to 10 V | 96.9 ms | 954.4 ms |
| T2 disable | 10.0 ms | 10.0 ms |
| T_dwell (hardware '123, covers `K_S` 8 ms + reed 12 ms + settle) | 500.0 ms | 500.0 ms |
| T7+T8 restart + settle | 610.0 ms | 840.0 ms |
| **TOTAL** | **1.217 s** | **2.304 s** |

**Against G0-A1's "a dead-band of order 1 second is acceptable": the nominal case passes at 1.22 s;
the worst case at the `C_load` interface limit is 2.3 s and must be reported to the human, not
buried.** The relay and switch hardware contribute **20 ms of 1217 ms — 1.6 %.** Everything else is
the module: it cannot sink current (T1) and its restart is undocumented (T7/T8). **The relay is not
what makes this slow. The modules are** — unchanged from session 1's finding, and now with a better
bleed (40 MΩ per node rather than 90.9 MΩ effective) the T1 term has fallen from 327 ms to 97 ms.

`T_dwell_hw` = 0.5 s from a 74HCT123 with **R = 1.1 MΩ, C = 1 µF** (`t ≈ 0.45·R·C` for HC-family
`[recalled — confirm the coefficient from the datasheet at G1]`). Firmware's own dwell must be
**longer** (use 0.8 s) so the hardware is a backstop, never the normal path.

**The `SETTLE` monostable must be triggered by `SEL`, `MODE_PB` **and** `MODE_UNI` edges** — three
RC-XOR edge detectors (74HCT86, 10 kΩ / 1 nF, ≈10 µs pulse) OR'd into the '123's retrigger input.
Session 1's version watched `SEL` only; §3.3a of `CONTROL_ARCHITECTURE.md` flags the gap.

### 9.3 Mode change — a procedure, plus two hardware backstops

**There is no runtime mode-change transition and none must ever be written** (MODE-08, G0-A5). The
sequence is identical in physics and is executed by a human:

> **OPERATING PROCEDURE (panel legend, MODE-17):**
> 1. Set both outputs to 0 V and disarm.
> 2. Confirm both monitors read < 10 V.
> 3. **Power the instrument down.**
> 4. **Disconnect both HV cables.**
> 5. Remove the switch guard / interlock plug.
> 6. Turn `SW1` through `SAFE` to the new position. **Pause in `SAFE`.**
> 7. Replace the guard, re-cable per the new mode's legend, power up.

**Backstop 1 — hardware, works with no firmware.** Any aux-pole edge fires `SETTLE` and, an instant
later, the `SAFE` detent forces `VALID` = 0. `ARM` and `Q_COIL` both drop. Both modules lose `+VIN`,
both `/ON` go high, both relays release to their NC bleeds, `X` and `M` fall onto their stub bleeds.
Elapsed: < 100 µs to command, 6 ms to release, then the discharge times of §5.3.

**Backstop 2 — firmware (MODE-16).** Firmware reads `MODE_PB`/`MODE_UNI` at boot **and on every
supervisor tick (≤ 10 ms)**. Any change while not in `G0 SAFE` ⇒ **latched `G7 TRIP`, error
`+107 mode switch moved while energised`**, clearable only by `OUTP:PROT:CLE`. **Never a graceful
ramp-down** — a graceful ramp keeps HV alive during exactly the contact transit the design is racing.

**What firmware must NOT do:** cache the mode, act on a mode read older than one tick, or treat the
mode as settable. `MODE?` reports the physically-read value and there is no `MODE <x>` command
(MODE-12).

### 9.4 Power-up self-test suite — and why each test cannot silently false-pass

F-2's lesson is that a detector with a silent false-pass is worse than no detector: session 1's weld
test could not distinguish *"stimulus applied and blocked"* from *"no stimulus was ever applied"*.
**Every test below is stated with its own falsifiability condition.**

| # | test | procedure | pass requires **both** | catches |
|---|---|---|---|---|
| **0** | coil rail is really switchable | de-assert `EN_HB`; wait 100 ms | both branch monitors show their module's HV pin bonded to its bleed (relays at NC) — verified by injecting nothing and checking the *bleed* path in test 3 | **F-20**, a shorted `Q_COIL`. Without this, every later test's precondition is unverified |
| **1** | `K1` weld / magnetic hold | both coils off; enable POS to **+200 V** | (a) `HV_POS` branch monitor reads 200 ± 20 V — *the stimulus was applied* — **and** (b) `OUT_A` monitor reads < 10 V — *the contact is open* | welded `K1`, magnetically held `K1`, **and** a dead module / open `/ON` / open `R_S`, which the (a) half distinguishes |
| **2** | `K2` weld | same for NEG, checking `OUT_A` (pseudo-bipolar) or `OUT_B` (unipolar) | as test 1 | as test 1 |
| **3** | bleed integrity (NUM-10) | with a relay closed, raise to 200 V, disable, and **measure the decay τ** against the independent monitor | τ within ±40 % of the computed value for the present configuration | a cracked bleed resistor; distinguishes 20 ms / 40 ms / ∞ |
| **4** | COLD is not stuck | raise either output to 200 V | `COLD_x` observed **FALSE**, then TRUE again after the bleed | **F-21**, a COLD comparator stuck at 1, which would make every changeover a hot switch |
| **5** | `K_S` exclusivity | in pseudo-bipolar: drive `KS_SEL` = 0, confirm only `HV_POS` can be energised; then `KS_SEL` = 1, confirm only `HV_NEG` can | both halves | a bridged/welded `K_S` pole |
| **6** | **mode routing — the test that resolves F-8** | enable **NEG** to 200 V and see **which output monitor responds** | pseudo-bipolar ⇒ `OUT_A` responds and `OUT_B` stays < 10 V; unipolar ⇒ `OUT_B` responds and `OUT_A` stays < 10 V | **a lying `MODE_*` line, a welded or mis-positioned mode pole, and a mis-wired switch** — this is the only test that checks the aux poles against physical reality, and it is decisive because the two modes route NEG to *different terminals* |
| **7** | duplicated-pull integrity | not testable in-circuit | — | **declared blind spot.** Covered by the `board_spec.py` assertion (§6.8) and by visual inspection at build |

Total self-test time ≈ 20 s at 200 V. **Run it at every power-up and refuse to arm on any failure**
(`G1 SELFTEST` → `G7 TRIP`). At 200 V the modules are inside their specified band (> 2 %·Vnom = 20 V,
PART-10) so the readings are meaningful — **a self-test at 10 V would be run in the unspecified
region and would not be**.

---

## 10. Bill of materials for the routing and interlock subsystem

| qty | ref | part | note |
|---:|---|---|---|
| 2 | `K1`, `K2` | Pickering `67-1-C-5/5D` `[unverified-MPN]` | **unpriced** (R-7). Newark lists the 12 V sibling as SKU 40AK2389. Order at G1 |
| 1 | `K_S` | Panasonic `TQ2SA-5V` `[unverified-MPN]` | $2.65, 14 805 in stock `[verified-live-page, session 1]` |
| 1 | `SW1` | 3-position ceramic wafer switch, 3 HV + 4 LV poles, **or** the §3.7 link block | **`[unverified-MPN]`, O-10 open** |
| 4 | `R_S_P/N`, `R_M1`, `R_G` | 10 kΩ axial HV film, ≥2 kV (Ohmite MOX-400 class `[unverified-MPN]`) | |
| ≈60 | HV divider / bleed elements | 2512 HV (1500 V) and 1206 HV (800 V) chip strings | R-7: HV passives were 0-stock / obsolete / 13-week lead across four agents' searches |
| 2 | `U_P`, `U_N` | TPS22918-class load switch `[unverified-MPN]` | per-module `+VIN`, primary disable |
| 2 | `Q_ARM`, `Q_COIL` | load switch or P-FET + gate driver | C-1 |
| 2 | `Q_K1`, `Q_K2` | 2N7002 `[unverified-MPN]` | coil low-side |
| 1 set | logic | 74HCT86, 74HCT14, 2 × 74HCT11, 74HCT32, 74HCT08, 74HCT03, 74HCT123, 2 × 74HCT75 `[unverified-MPN]` | **all on +5 V** (§7.4) |
| 3 | comparators | TLV3202 ×2 (COLD windows), TLV3202 ×1 (OVP) `[unverified-MPN]` | push-pull outputs only |
| 1 | `WDT` | windowed watchdog supervisor, MAX6746-class `[unverified-MPN]` | C-3 |
| 2 | SHV bulkheads | `OUT_A`, `OUT_B` | NUM-12, MODE-05 |

**5 V rail total 1094 mA ⇒ recommend a 5 V / 2.5 A supply** at the project's 2.0× margin
`[verified-run]` — a correction to `NUMBERS_PROBE` §6.2's 1.8 A (§4.2).

---

## 11. What is measurable now, and what the design does at the pessimistic end

The modules are in hand (G0-A2). All four numbers below are **MEASURABLE-NOW** and none has been
measured.

| parameter | assumed | where it binds here | **if it comes back pessimistic** |
|---|---|---|---|
| **Module output capacitance** (PART-24; assumed **1 nF**) | 1 nF | T1 of the changeover (97 ms), every discharge time in §5.3, the `R_M1` transient in §3.8 | At **10 nF** the closed-node τ becomes 190 ms and T1 becomes 875 ms, pushing the nominal dead-band to ≈2.0 s — **still inside the "order 1 second, ~1 s acceptable" answer only if the human accepts 2 s.** The design response is **not** to shrink the bleed (the load budget has 2.4 points of headroom, §5.2); it is to fit the **switched crowbar** session 1 costed and rejected: one more Form-C relay per node with a 10 kΩ dump (NUM-08 — sized against 1.5·Inom, **not** against τ; 1 MΩ would give a 750 V "clamp"). Cost +$90 and +18 cm² per node. **Decide after the measurement, not before.** |
| **Internal bleeder** (PART-24; assumed **~20 MΩ**) | 20 MΩ | if it is real, every node discharges faster than §5.3 says and the numbers are conservative; if it does **not** exist, §5.3 is exact | **No design change either way** — the external bleeds were sized without crediting it. This is the one place the pessimistic answer costs nothing. |
| **Turn-on time after `+VIN`** (PART-25; assumed **150 ms**) | 150 ms | T7 of the changeover | At **500 ms** the dead-band becomes 1.57 s nominal. **No hardware change**; report the real dead-band in the manual and in `MEAS:...` timing. |
| **`VSET` step response** (PART-07; τ = 100 ms **inferred from a figure captioned "control principle"**) | 100 ms | T8 (460–690 ms), the ramp-timeout formula, the 300 ms minimum step | If τ is **much larger**, the ramp-step floor and every timeout in §9.2 scale with it. If τ is **much smaller**, the §3.5 lead-break margin *shrinks*, which makes the SAFE detent less critical but does not remove it. |

**Bench procedure to close all four in one afternoon** (add to `HV_SAFETY_ENVELOPE` §4 stage 3):
one module, `+VIN` from a bench supply through a switch, `VSET` from a bench DAC, HV output loaded
with a known 100 MΩ ± 1 % and monitored through a 1000:1 HV probe on a scope. Measure (a) the decay
τ with the known load ⇒ solves for `C_out` **and** for the internal bleeder simultaneously by
repeating with the load removed; (b) the time from `+VIN` rising to the output first moving; (c) the
step response of `Vout` to a `VSET` step, fitted for τ. **All four numbers, four traces.**

---

## 12. Reproducing the arithmetic

`docs/studies/combiner_design_numbers.py`, stdlib-only, zero-arg, deterministic (same home as session
1's `control_arch_numbers.py`). Run under any Python 3:

```
"C:/Program Files/KiCad/10.0/bin/python.exe" docs/studies/combiner_design_numbers.py
```

It prints, and this document quotes: the standing-load budget per module in all three routing cases;
node resistances and discharge times for four capacitance scenarios × three bleed states; the
changeover dead-band; make-current margins against the datasheet's 3 A rating; the coil and 5 V rail
budget from the datasheet's coil table; and the COLD window arithmetic. **All numbers in §3.2, §3.3,
§3.8, §4.2, §5.2, §5.3, §6.5 and §9.2 tagged `[verified-run]` come from that run.**

> ⚠ **This tool is arithmetic, not verification.** It has no independent source of truth to check
> itself against, unlike `numbers_probe.py` which reads three sibling artifacts at runtime. It is
> **not** mutation-tested. **Promote it into `hardware/hvctl/` with an acceptance check and a mutation
> test before any of its outputs are frozen** — that is the project standard and this document does
> not meet it yet.

---

## 13. Where this document disagrees with session 1, explicitly

`CLAUDE.md` and the task both require disagreements to be stated, not silently applied.

1. **`K_S` no longer routes "the only `+VIN` that reaches either module".** ARCH-16 mechanism (i)
   implements the *old* invariant and structurally forbids mode 2. Here `K_S` routes an *exclusivity
   gate* that the mode switch's own contacts bridge in unipolar mode. **The mechanism is preserved;
   its scope is now mode-conditional, and the condition is mechanical.**
2. **The bleed is 40 MΩ per node, not session 1's 20 MΩ NC bleed + 100 MΩ bus bleed.** Reason: there
   are now four nodes, not two, and both a module-side and an output-side bleed sit on the same node
   whenever a relay is closed. 40 MΩ each keeps the *combined* figure at the budgeted 10 % of Inom
   while giving every isolated node its own 5 % path. Session 1's numbers were correct for its own
   two-node topology.
3. **`T_dwell` (hardware) is 0.5 s, not 1 s.** Session 1 chose 1 s before the dead-band was
   recomputed. At 0.5 s the monostable still covers `K_S` (8 ms) + reed transfer (12 ms) + settle
   (20 ms) by 12×, and it recovers 0.5 s of a budget that TOPO-12 already stretched to 0.89–1.12 s.
4. **`Q_COIL` is gated by `EN_HB · INTLK · VALID`, not by the full `ARM`.** C-1 says "the same
   ALIVE/ARM element". Gating on the full `ARM` would force a hot break on every OVP trip and every
   disarm. §6.7 gives the reasoning and the compensating design rule.
5. **The coil voltage is 5 V, closing TOPO-08's open question**, and the datasheet shows the 5 V coil
   is the *lowest-power* option, not merely the one that avoids a rail. Session 1's C-1 text
   presumed 12 V.
6. **The `NUMBERS_PROBE` §6.2 relay-coil line (80 mA) is wrong by ~3×** for this part; the rail total
   moves 888 → 1094 mA and the supply 1.8 → 2.5 A. **Reported here; the probe must be fixed and
   regenerated, not patched** (`CLAUDE.md` rule 1).
7. **Session 1's fault 15 ("broken `VSET` wire ⇒ full scale, UNSAFE") is closed**, by the latched
   per-output hardware OVP feeding `nOVP` into `ARM`. Session 1 listed only firmware/comparator
   mitigations that "still let the module ramp to Vnom".
8. **The mode switch is 3-position, not 2.** G0-A5 did not specify a position count. §3.5 derives
   that a 2-position switch cannot meet MODE-15's margin, because the binding time is the module's
   own output decay and not any contact sequence. **This is new; O-11 should be closed with this
   answer, or the reasoning rebutted.**

---

## 14. Open items — carried forward, still flagged

| id | item | status after this document |
|---|---|---|
| **NUM-01/02** | Every clearance number is `[unverified-primary]`. The claimed internal cross-check was an algebraic tautology and was deleted. | **Unchanged and still binding.** §5.4 adds **two new pairwise DRC rules** at the same unverified 15.0 mm. A human must read a primary copy of IPC-2221B Table 6-1 **before layout** — it decides the fab tier (`NUMBERS_PROBE` §1.6). |
| **O-10** | Which physical mode element, and can it be sourced? | **Narrowed, not closed.** §3.6 gives four candidate classes with a decisive spacing argument and the "use every fourth contact" fix; §3.7 gives a fallback that may be better. **No MPN, no price, no stock read.** |
| **O-11** | The contact-timing margin (aux poles lead HV poles). | **Answered by construction** (§3.5): the requirement is met by a SAFE detent, not a timing spec. **Present this to the human for ratification; it changes the part specification.** |
| **PART-24/25, PART-07** | Four unmeasured module parameters. | **MEASURABLE-NOW.** §11 gives the procedure and the pessimistic-end response for each. |
| **PART-27** | Reverse-voltage tolerance of an OFF module's HV pin. | **Still open, and §4.3 makes it the residual magnetic-fault question.** Ask iseg. |
| **PART-20** | Table 1 specifies a current-monitor accuracy; Table 4 lists no current-monitor pin. | Untouched. Do not design against a current monitor. |
| **Q6 / TOPO-10 / R-8** | Weld: detection vs prevention. | **Not answered at G0.** This design detects (§9.4 tests 1, 2, 6 + continuous branch monitoring) and cannot prevent. If prevention is ever required, the topology study reopens. |
| **R-6** | Magnetic environment. | **§4.3 asks the human a specific, consequential question with no fallback topology.** |
| **R-7** | Relay + HV-passive procurement. | Worse, not better: ~60 HV passives, two unpriced Form-C relays, and one unsourced switch. **Order at G1.** |
| **NUM-18 / ARCH-14** | Conformal coating: assumed absent for clearance, mandated present for divider surface leakage. | **Still contradictory, still unresolved** (O-4). This design adds two more guard-ringed divider regions, so the tension gets worse. **Resolve before layout.** |
| **NUM-11 / NUM-21** | 5 V rail budget. | **Corrected here (§4.2, §10) and must be re-run in the probe.** |
| **F-3 (probe)** | `iseg_APS_THT.kicad_mod` carries a 5.00 mm per-pad clearance override on pad 6, silently replacing the 7.5 mm netclass value. | **Still unfixed.** Fix `gen_lib_footprints.py`, regenerate. |
