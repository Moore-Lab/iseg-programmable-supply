# NUMBERS_PROBE — the frozen numbers for AP010504

> **⚠ THIS FILE IS GENERATED. DO NOT EDIT IT.**
> It is produced by `hardware/hvctl/gen_numbers_probe_doc.py`, which **runs**
> `hardware/hvctl/numbers_probe.py` and embeds its output verbatim. Fix the probe and
> regenerate; never edit this file. (`CLAUDE.md` rule 1; `docs/PIPELINE_LOG.md` PL-12 —
> session 1's version of this document was typed *alongside* the probe rather than generated
> *from* it, and the two drifted until the document described a run that no longer existed.)

```
# either interpreter works -- probe and generator import only stdlib
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/numbers_probe.py               # the run itself
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/gen_numbers_probe_doc.py       # regenerate this file
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/mutation_test_numbers_probe.py # prove the assertions can fail
```

Exit codes, both tools: `0` ok · `1` verification failed · `2` structural failure ·
`3` legibility failure.

## What this run was

| | |
|---|---|
| **Part** | **AP010504P05 / AP010504N05** — 1000 V, 0.5 mA, 0.5 W, 5 V in, Vref 2.5 V. The modules the human physically owns. **Frozen by G0-A2.** |
| **Gate** | **G0 is SIGNED OFF** (2026-07-23). Behaviour, module, comms and dual-mode are frozen facts, not assumptions. |
| **Assertions** | **74 passed / 0 failed** of 74 · exit code **0** |
| **Determinism** | two consecutive runs **byte-identical**, checked by the generator before it wrote this file |
| **Mutation-tested** | **8 of 8** perturbations of input constants caught — see *Mutation testing* below |
| **Findings** | 10 |
| **Declared blind spots** | 7 |

## What this probe is, as an instrument

It is **arithmetic over datasheet numbers**, plus three reads of files on disk that act as
independent sources of truth at runtime (KiCad's stock chip-resistor land patterns, this
project's own module footprint, and a `.kicad_pro` KiCad itself wrote). It has **measured
nothing**, **simulated nothing**, and **selected no part by MPN** — and the modules that *are*
in hand have **not been touched**. `Exit 0` means every arithmetic assertion holds, which is a
far weaker claim than "the design is safe".

**Both standards it leans on are `[unverified-primary]`.** Session 1's claimed "independent
cross-check between two standards families" was an **algebraic tautology**; §1.5 below proves it
and **deletes** it, and **no replacement cross-check has been invented**. There is currently *no*
evidence that the clearance constants are the right constants. A human must read a primary copy
of IPC-2221B Table 6-1 and IEC 60664-1 / 62368-1 **before G1**. §1.6 shows this is
decision-relevant rather than bookkeeping: the two candidate readings of the standard put the
board on **different fab tiers**.

## Sections

| § | title |
|---|---|
| §0 | THE FROZEN PART (G0 signed off 2026-07-23) |
| §1 | CREEPAGE AND CLEARANCE (primary case: HV_POS <-> HV_NEG at 2000 V) |
| §2 | HV NETCLASS RULES (.kicad_pro net_settings.classes + .kicad_dru) |
| §3 | BLEED / DISCHARGE / STORED ENERGY at 1000 V |
| §4 | INDEPENDENT HV MONITOR DIVIDER (one PER OUTPUT -- G0-A4 doubles it) |
| §5 | THE VSET CLAMP  (PRIMARY SAFETY ELEMENT) |
| §6 | POWER BUDGET ON THE 5 V RAIL |
| §7 | SET-POINT RESOLUTION |
| §8 | OTHER CLASSES, KEPT ONLY WHERE THE COMPARISON IS INFORMATIVE |

## Findings raised by this run

| id | finding |
|---|---|
| **F-1** | The 'independent cross-check between two standards families' in session 1's NUMBERS_PROBE.md section 1.5 is an ALGEBRAIC TAUTOLOGY and has been DELETED, not repaired. Above 500 V both expressions reduce to 0.005*V identically, so its four assertions could not fail for any input; and the check is invariant under any common rescaling of both columns, which is precisely the failure mode implied by both columns having come off one web page. NO REPLACEMENT CROSS-CHECK HAS BEEN INVENTED. The clearance constants are [unverified-primary] and stay that way until a human reads a primary copy of the standard. |
| **F-2** | The IEC PD2 'printed boards' creepage column transcribed in this probe is numerically identical to the 'material group I' column at 2 of 3 anchors, the signature of reading the wrong column. FLAGGED, NOT CORRECTED -- no guess has been substituted. Consequence is bounded today because IEC_pcb never exceeds IPC B2 at 1000 or 2000 V and therefore never governs; a human reading the primary copy must confirm that remains true. |
| **F-3** | hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod carries a per-pad local clearance override of 5.00 mm on pad 6 (HV). A KiCad pad-level clearance REPLACES the netclass clearance, so with the netclass at 7.5 mm the most critical pad on the board is silently checked at 5.00 mm -- the bare IPC B2 value with the 1.5x design margin dropped. FIX THE GENERATOR gen_lib_footprints.py (its CREEPAGE_MM constant) and regenerate; do not hand-edit the artifact. Deliberately NOT fixed by this probe. |
| **F-4** | G0-A4 adds a SECOND pairwise DRC rule that did not exist in session 1: HV_OUT_A <-> HV_OUT_B must also hold 15.0 mm, because in dual-unipolar mode the two OUTPUT nets are simultaneously live at opposite polarity. Ruling only the HV_POS<->HV_NEG module pair leaves every net downstream of the changeover relay silently spaced for 7.5 mm instead of 15.0 mm. |
| **F-5** | Bleed/divider part '1206 HV series' is REJECTED at 1000 V: a working-voltage rating high enough to need only N=3 elements puts 333 V across a package whose own pad-to-pad gap is 1.925 mm, below the 2.500 mm IPC-2221 B2 clearance that voltage demands. |
| **F-6** | Session 1's probe rated a standard 2512 chip resistor at 500 V working voltage. DECISIONS ARCH-12, which is [verified-artifact] from the actual Yageo RC datasheet, says 200 V -- and that upsizing 1206->2010->2512 buys power, not volts. The corrected rating changes the standard-part series count at 1000 V from N=4 to N=10. This probe uses the verified number; the two documents disagreed and the datasheet wins. |
| **F-7** | At 1000 V this instrument is a SUSTAINED-SOURCE shock hazard and a STORED-ENERGY startle hazard. Worst credible stored energy is 5.560 mJ against the 350 mJ threshold (63x below) and 11.12 uC against 50 uC; the sustained 0.75 mA at up to 1000 V -- from BOTH outputs simultaneously in mode 2 -- is the thing that hurts. Design limit: total output capacitance < 50 nF per output, i.e. no bulk HV filter capacitor. |
| **F-8** | Surface leakage is the dominant, non-obvious error term of the independent monitor at this class. With Rt = 200 Mohm forced by the 1.00 %-of-Inom loading budget, a 10 Gohm board leakage path injects 20.0 V of ratio error -- on its own larger than the 10.0 V VMON accuracy the divider exists to improve on. A DRIVEN GUARD RING AT TAP POTENTIAL IS THEREFORE A REQUIREMENT OF THE MONITOR, not a refinement, and it must be in the netclass/DRC rules and in the generator's invariants. |
| **F-9** | The VSET clamp is a necessary but NOT SUFFICIENT safety element. The best candidate (RRIO buffer powered from the precision reference) still passes 2 of 7 modelled single faults, including a reference-to-5 V short that reaches 201 % of Vnom = 2012 V -- worse than the un-clamped 3.3 V case, because the fault is in the clamp's own reference. The independent VMON comparator, on its OWN reference and driving /ON in hardware, is what closes the set, and +VIN removal is the primary disable. With a network carrying write authority (G0-A3) this chain IS the safety case. |
| **F-10** | The ESP32's WiFi TX burst reflects 388 mA onto the 5 V rail -- more than both HV modules at full load combined (360 mA). G0-A3 chose a network interface with write authority, so this current is real and continuous-duty, not a curiosity. Sizing the supply from the HV modules alone under-sizes it by roughly a factor of two. |

## Mutation testing

Every assertion in this probe must be one that **can fail**. Eight perturbations were applied to
**input constants**, one at a time, and the probe re-run. Re-runnable, zero-arg:
`hardware/hvctl/mutation_test_numbers_probe.py` (it writes a throwaway
`_mutant_numbers_probe.py` *beside* the real probe — not in a scratch directory — because the
probe reads three sibling artifacts by relative path, and removes it in a `finally`).
`[verified-run]`

| # | mutation | caught by |
|---|---|---|
| M1 | monitor-divider loading budget `1 % → 5 %` of Inom | 3 assertions, exit 1 |
| M2 | bleed budget `10 % → 0.2 %` of Inom (R_bleed 20 MΩ → 1 GΩ) | 2 assertions, exit 1 |
| M3 | MCU logic rail `3.3 V → 2.4 V` (i.e. *below* the module Vref) | 3 assertions, exit 1 |
| M4 | clearance design margin `1.5× → 0.8×` | 3 assertions, exit 1 |
| M5 | IEC printed-board column de-duplicated from material-group I | 2 assertions, exit 1 — **including the deliberate tripwire** |
| M6 | ESP32 peak `500 mA → 150 mA` | 1 assertion, exit 1 |
| M7 | VSET fail-safe pull-down `1 kΩ → 100 kΩ` | 1 assertion, exit 1 |
| M8 | divider top-leg element count `10 → 1` | 2 assertions, exit 1 — **only after the hole M8 exposed was fixed** |

**M8 initially SURVIVED, and that is the most useful result of the exercise.** Driving the
top-leg element count to 1 puts the full 1000 V across a single 1206 chip resistor, and nothing
fired. Two real defects were behind it, both now fixed **in the generator**:

1. **A duplicated constant.** The element count existed as `N_TOP_ELEMENTS = 10` (used by the
   error budget, where the VCR term goes as `1/N`) *and* as a separate literal `n_div = 10`
   (used by the string geometry, which sets the per-element voltage). Perturbing one moved the
   error budget while the geometry screens went on evaluating the other. There is now **one**
   definition, and an assertion that the two consumers agree.
2. **A missing class of check.** The *bleed* string was screened against its element's
   working-voltage rating; the *monitor divider* string was screened only on package clearance.
   A **rating** and a **clearance** are different constraints, and the divider now has both.

Neither defect changed a single number in this run — they were latent, and only a mutation
found them. That is the argument for mutation-testing an arithmetic tool at all.

## The verbatim run

Everything below this line is the probe's stdout, unedited, byte-for-byte as captured by the
generator. The generator refuses to write this file unless the probe exits 0, unless two
consecutive runs are byte-identical, and unless an **independent regex line-count** of
`[PASS]`/`[FAIL]` lines agrees with the count the probe prints in its own verdict block — two
countings of the same run, one over a list of objects and one over a stream of text.

---

```text
============================================================================================
iseg BIPOLAR HV CONTROLLER -- NUMBERS PROBE, PINNED TO AP010504
============================================================================================
Every number the design freezes, with its formula and its source.
PRIMARY CASE: AP010504P05 / AP010504N05 -- the modules the human owns. Computed in full.
Other voltage classes and the 1 W family appear ONLY in section 8, and only where
the comparison explains a number rather than offering an option.

G0 is signed off. The behaviour is set-and-hold with polarity changeover; the
combiner is an HV relay changeover; comms are serial AND network, both with write
authority; and the instrument is switchable between one combined bipolar output
and two independent unipolar outputs that may BOTH BE ENERGISED AT ONCE.

Runtime artifact reads used as independent sources of truth this run:
   chip-resistor land patterns : KiCad 10.0 stock library [verified-artifact]
   module footprint            : hardware/hvctl/lib/iseg.pretty [verified-artifact]
   KiCad netclass field set    : hardware/phase0_env_proof/env_proof.kicad_pro [verified-artifact]
     0805   pad gap 0.8250 mm   land extent 2.8250 mm
     1206   pad gap 1.9250 mm   land extent 3.9250 mm
     2010   pad gap 3.6250 mm   land extent 5.6250 mm
     2512   pad gap 4.9250 mm   land extent 6.9250 mm

============================================================================================
SECTION 0 -- THE FROZEN PART (G0 signed off 2026-07-23)
============================================================================================
Decoded from [ISEG] Table 2 / Table 3 against the modules the human physically owns:
    AP010504P05  (positive)      AP010504N05  (negative)
    AP | 010 = 1000 V Vnom | 504 = 0.50 mA Inom | polarity P/N | 05 = 5 V input

    Vnom                  1000.0 V
    Inom                   0.500 mA          Iout limit = 1.5*Inom = 0.750 mA
    Pnom                    0.50 W
    Vin                      5.0 V   (4.5 .. 5.5 V)  <-- 5 V, NOT 12 V
    Vref                    2.50 V   +/-1 %      <-- 2.5 V, and the MCU rail is 3.3 V
    Vset, Vmon          0 .. 2.5 V full scale
    Iin  @Vout=0        <    5.0 mA
    Iin  @Vnom no load  <   25.0 mA
    Iin  @Vnom loaded   <  180.0 mA   <-- the number the supply is sized on
    Adjustment accuracy +/-1 % = 10.0 V at Vnom
    VMON accuracy        1 % * Vnom = 10.0 V
    Tempco              < 50 ppm/K = 0.050 V/K at Vnom

-- 0.1  The ripple spec has a FLOOR, and below it the output is UNSPECIFIED ----------------
     [ISEG] ripple/noise: typ < 10 mVpp, max < 30 mVpp (f > 10 Hz),
     < 5 mVpp (f > 2 kHz) -- GUARANTEED ONLY FOR 2 % * Vnom < Vout <= Vnom.
     At this part that floor is 20 V. BELOW 20 V THE OUTPUT IS UNSPECIFIED -- not
     merely worse. Every low-end number in this document must say so, and the host
     protocol must refuse to present 0 < |Vout| < 20 V as a specified operating point.
  [PASS] the unspecified low-output band is a real, non-empty band  --  0 .. 20 V of a 1000 V range = 2 % of full scale is UNSPECIFIED

-- 0.2  The 3.3 V hazard is now real, load-bearing, and specific to THIS part --------------
     Vref = 2.5 V. The MCU rail is 3.3 V. Vout/Vnom = Vset/Vref, and [ISEG] states
     verbatim: 'Attention! Output voltage is internally not limited!'
     A logic-level fault that puts 3.3 V on VSET commands 3.3/2.5 = 132 % of Vnom
     = 1320 V on a 1000 V module.
     Compounding it, the module's UN-DRIVEN DEFAULT STATE IS ENERGISED AT OVER-RANGE:
       * internal 10 kohm pull-up to Vref  ==> an OPEN VSET commands FULL SCALE
       * /ON is active LOW and 'LOW or n.c.' ==> a FLOATING /ON turns HV ON
     The 1 W family (Vref 5.0 V) would be immune to a 3.3 V rail. THAT FAMILY IS NOT
     AVAILABLE: the human owns the 0.5 W / 5 V part. The hazard is not designed away,
     it is clamped -- see section 5, which treats the clamp as a primary safety element.
  [PASS] un-clamped 3.3 V drive on VSET is a >30 % over-voltage on the OWNED part  --  132 % of Vnom = 1320 V
  [PASS] module Vref sits BELOW the MCU logic rail (this is what creates the hazard)  --  Vref 2.5 V < rail 3.3 V

-- 0.3  What G0-A4 (dual-mode) changes in one sentence -------------------------------------
     MODE 1 bipolar combined : one output terminal, one module at a time,
                               break-before-make, deselected module bled to ground.
     MODE 2 dual unipolar    : positive module -> OUT_A, negative module -> OUT_B,
                               BOTH ENERGISED SIMULTANEOUSLY. That is the point of it.

     ==> +1000 V and -1000 V coexist on this board as a NORMAL STEADY-STATE CONDITION.
     ==> the HV_POS<->HV_NEG differential is 2000 V, permanently, not as a fault.
     ==> the safety invariant is RESTATED, not discarded:
           'it must be impossible for both modules to be connected to the SAME
            output node simultaneously'
         which forbids the mode-1 both-enabled state exactly as before, and is
         satisfied STRUCTURALLY in mode 2 because the nodes are physically different.
     ==> the interlock permissive must be derived from the ACTUAL PHYSICAL POSITION of
         the mode routing element, never from a commanded mode bit. Numbers below
         assume mode 2 throughout, because mode 2 is the binding case for every one.

============================================================================================
SECTION 1 -- CREEPAGE AND CLEARANCE (primary case: HV_POS <-> HV_NEG at 2000 V)
============================================================================================
Source, IPC:  IPC-2221 / IPC-2221B Table 6-1 'Electrical Conductor Spacing'. [unverified-primary] -- the primary standard is PAYWALLED and has NOT been read. The values here came off secondary web reproductions in session 1, and the two 'independent' reproductions were later shown to be the same page. NO INTERNAL EVIDENCE SUPPORTS THIS TRANSCRIPTION. A human must read a primary copy before G1.
Source, IEC:  IEC 62368-1 / IEC 60664-1 creepage, pollution degree 2, basic insulation. [unverified-primary] -- same status as IPC2221, same single secondary source. The 'printed boards' column is additionally SUSPECTED MIS-TRANSCRIBED (section 1.5). Values above 1000 V are OUR OWN LINEAR EXTRAPOLATION, not a quotation.

*** READ THIS BEFORE USING ANY NUMBER IN THIS SECTION ***
EVERY constant below is [unverified-primary]. Neither standard has been read in the
original by anyone on this project. Session 1's document claimed an 'independent
cross-check between two standards families' as evidence; section 1.5 below PROVES
that check had zero discriminating power, and it has been DELETED. No replacement
cross-check has been invented, because there is nothing honest to put there.
The numbers are kept CONSERVATIVE and stay unfrozen until a human reads a primary
copy of IPC-2221B Table 6-1 and IEC 60664-1 / 62368-1.

-- 1.1  IPC-2221 Table 6-1 as transcribed here (mm) ----------------------------------------
     B1 internal | B2 external uncoated <=3050 m | B3 external uncoated >3050 m |
     B4 external w/ permanent polymer coating | A5 external w/ conformal coating |
     A6 external component lead uncoated | A7 external component lead coated

     band (V)          B1      B2      B3      B4      A5      A6      A7
     0-15           0.050   0.100   0.100   0.050   0.130   0.130   0.130
     16-30          0.050   0.100   0.100   0.050   0.130   0.250   0.130
     31-50          0.100   0.600   0.600   0.130   0.130   0.400   0.130
     51-100         0.100   0.600   1.500   0.130   0.130   0.500   0.130
     101-150        0.200   0.600   3.200   0.400   0.400   0.800   0.400
     151-170        0.200   1.250   3.200   0.400   0.400   0.800   0.400
     171-250        0.200   1.250   6.400   0.400   0.400   0.800   0.400
     251-300        0.200   1.250  12.500   0.400   0.400   0.800   0.800
     301-500        0.250   2.500  12.500   0.800   0.800   1.500   0.800
     >500 (/V)    0.00250 0.00500 0.02500 0.00305 0.00305 0.00305 0.00305

     >500 V rule:  spacing(V) = spacing(301-500 band) + per_volt[col] * (V - 500)
       B2 @ 1000 V = 2.500 + 0.00500*(1000-500) =  5.000 mm  <- single-ended, this part
       B2 @ 2000 V = 2.500 + 0.00500*(2000-500) = 10.000 mm  <- HV_POS<->HV_NEG, mode 2
       B4 @ 2000 V = 0.800 + 0.00305*(2000-500) =  5.375 mm  <- if conformally coated

-- 1.2  D-2, still open: the task brief's IPC column labelling -----------------------------
     The original brief described 'the B4 external-uncoated >500 V rule
     (0.25 mm + 0.0025 mm per volt above 500 V)'. The transcription used here says
     B4 is the COATED external column at 0.80 + 0.00305/V, and that 0.25 + 0.0025/V
     is B1, the INTERNAL-conductor rule. Both readings cannot be right and NEITHER
     has been checked against a primary copy. Unresolved. Carried forward.

-- 1.3  The voltages that appear on this board -- SETTLED by G0-A4 -------------------------
     node pair                      V across   when
     HV_POS   <-> GND                   1000   always, either mode
     HV_NEG   <-> GND                   1000   always, either mode
     HV_OUT_A <-> GND                   1000   mode 1 and mode 2
     HV_OUT_B <-> GND                   1000   mode 2 only
     HV_POS   <-> HV_NEG                2000   *** NORMAL STEADY STATE in mode 2 ***
     MODULE_CASE <-> GND          0 (bonded)   see 1.7 -- UNRATABLE, component-internal

     Session 1 called the 2000 V span a SINGLE-FAULT condition, conditional on the
     combiner topology, and sized for it only as insurance against interlock failure.
     G0-A4 removes the conditional. In dual-unipolar mode the two opposite-polarity
     outputs are live SIMULTANEOUSLY as the intended normal operating condition. The
     2000 V differential is therefore the BINDING NORMAL CASE. It sizes the board, the
     netclass rules, and the spacing between the two output connectors.

-- 1.4  Required clearance for the frozen part ---------------------------------------------
     governing   = max( IPC-2221 B2(V), IEC PD2 printed-board creepage(V) )
     recommended = ceil_to_0.5mm( governing * 1.5 )
     The 1.5x is a judgement call, itemised: (a) IPC's own >500 V numbers extrapolate
     a table whose measured data stops at 500 V; (b) no conformal coating is assumed,
     so we sit in column B2; (c) etch + mask registration + route tolerance, order
     0.05 mm each; (d) [ISEG] permits 70 % RH non-condensing and a bench lab makes
     pollution degree 2 an assumption; (e) no board-level HV proof test is planned
     before first energization; and now (f) THE CONSTANTS THEMSELVES ARE UNVERIFIED,
     which is the largest single reason to keep the margin where it is.

     node pair                 V across   IPC_B2   IPC_B1   IPC_B4   IEC_pcb  IEC_IIIa      REC
                                    (V)       mm  mm(int) mm(coat)        mm        mm   DRC mm
     HV_* <-> GND (1x Vnom)        1000    5.000    1.500    2.325     5.000    10.000      7.5
     HV_POS <-> HV_NEG (2x)        2000   10.000    4.000    5.375    10.000    20.000     15.0   (IEC extrapolated)
     MODULE_CASE <-> GND              0      n/a      n/a      n/a       n/a       n/a UNRATABLE   <- 1.7

     FROZEN-PENDING-PRIMARY-STANDARD numbers for AP010504:
        HV net to anything else        >= 7.5 mm
        HV_POS to HV_NEG specifically  >= 15.0 mm   (pairwise -- NOT expressible as a
                                                    netclass; see section 2)
     IEC_IIIa is the conservative read: treat bare uncoated FR-4 as an ordinary
     material-group-IIIa insulator rather than 'printed board'. If an auditor takes
     that view every number DOUBLES (15.0 / 30.0 mm) and the 1.5x margin is consumed
     by that alone. Section 1.6 shows that is not academic -- it decides the board tier.
  [PASS] the mode-2 pairwise span demands more spacing than any single-ended HV net  --  15.0 mm vs 7.5 mm
  [PASS] recommended single-ended DRC value is not below the bare IPC B2 requirement  --  7.5 >= 5.000 mm
  [PASS] recommended pairwise DRC value is not below the bare IPC B2 requirement  --  15.0 >= 10.000 mm
  [PASS] IPC-2221 column B1 is monotonic non-decreasing in voltage
  [PASS] IPC-2221 column B2 is monotonic non-decreasing in voltage
  [PASS] IPC-2221 column B3 is monotonic non-decreasing in voltage
  [PASS] IPC-2221 column B4 is monotonic non-decreasing in voltage
  [PASS] IPC-2221 column A5 is monotonic non-decreasing in voltage
  [PASS] IPC-2221 column A6 is monotonic non-decreasing in voltage
  [PASS] IPC-2221 column A7 is monotonic non-decreasing in voltage
  [PASS] coated external (B4) is less demanding than uncoated external (B2) at the span  --  5.375 < 10.000 mm, a 1.86x reduction if we commit to conformal coating

-- 1.5  DELETED: the 'independent cross-check between two standards families' --------------
     Session 1's NUMBERS_PROBE.md section 1.5 asserted four checks of the form
         IPC-2221 B2(V)  ==  IEC PD2 printed-board creepage(V)
     and called their agreement 'the strongest evidence in this section' and 'the
     transcription's only internal evidence'. It is neither. Above 500 V:
         IPC B2(V)  = 2.50 + 0.005*(V-500)              = 0.005 * V   identically
         IEC pcb(V) = 2.50 + (5.0-2.5)/500 * (V-500)    = 0.005 * V   identically
     so the two expressions are the SAME FUNCTION and the check cannot fail for any
     input. It is an algebraic tautology, not evidence.

     Worse than merely uninformative: the check is INVARIANT UNDER ANY COMMON
     RESCALING of both columns. That is exactly the error mode we are exposed to,
     because both columns were transcribed from the SAME web page. Demonstrated:

       scale k     k*IPC_B2(1kV) k*IEC_pcb(1kV)  old check
       0.25               1.250          1.250      PASSES
       0.50               2.500          2.500      PASSES
       1.00               5.000          5.000      PASSES
       2.00              10.000         10.000      PASSES
       10.00             50.000         50.000      PASSES

     A transcription error that scaled BOTH columns by 4x -- e.g. reading a column
     printed in a different unit, or reading the reinforced-insulation column instead
     of the basic-insulation one -- would sail through the old check untouched while
     putting every HV gap on this board at a quarter of its requirement.
  [PASS] PROOF the deleted cross-check had zero discriminating power (it passes under every common rescaling, including 0.25x and 10x)  --  5 of 5 rescalings still 'PASS'
  [FINDING] The 'independent cross-check between two standards families' in session 1's NUMBERS_PROBE.md section 1.5 is an ALGEBRAIC TAUTOLOGY and has been DELETED, not repaired. Above 500 V both expressions reduce to 0.005*V identically, so its four assertions could not fail for any input; and the check is invariant under any common rescaling of both columns, which is precisely the failure mode implied by both columns having come off one web page. NO REPLACEMENT CROSS-CHECK HAS BEEN INVENTED. The clearance constants are [unverified-primary] and stay that way until a human reads a primary copy of the standard.

-- 1.5b  The IEC 'printed boards' column is probably MIS-TRANSCRIBED -- flagged only -------
     working V               pcb       MG I      MG II    MG IIIa
       250                  1.00       1.25       1.80       2.50   
       500                  2.50       2.50       3.60       5.00   <-- IDENTICAL to MG I
       1000                 5.00       5.00       7.10      10.00   <-- IDENTICAL to MG I

     The 'printed boards' column and the 'material group I' column are numerically
     IDENTICAL at 2 of the 3 transcribed anchors. In IEC 60664-1 those are different
     columns of the same table, and printed-board creepage is normally SMALLER than
     the material-group columns. Identical values are the classic signature of the
     eye sliding one column across while copying. FLAGGED, NOT GUESSED AT: this probe
     does not invent a corrected column.
     Bounded consequence, stated so the flag is not read as alarm: the recommendation
     is max(IPC_B2, IEC_pcb), and at both voltages that matter here the two are equal
     (5.000 / 10.000 mm), so IEC_pcb never binds and NO RECOMMENDED VALUE MOVES if the
     column turns out to be wrong -- UNLESS the corrected column is LARGER than IPC B2,
     which is exactly what a human reading the primary copy has to check.
  [PASS] TRIPWIRE: the IEC pcb/MG-I column duplication is still present in this table (this assertion FIRES when someone corrects the table, forcing a doc update)  --  2 of 3 anchors identical
  [FINDING] The IEC PD2 'printed boards' creepage column transcribed in this probe is numerically identical to the 'material group I' column at 2 of 3 anchors, the signature of reading the wrong column. FLAGGED, NOT CORRECTED -- no guess has been substituted. Consequence is bounded today because IEC_pcb never exceeds IPC B2 at 1000 or 2000 V and therefore never governs; a human reading the primary copy must confirm that remains true.

-- 1.6  What the 2000 V NORMAL case costs in board area ------------------------------------
     Two ways to hold 2000 V apart, and they are not equal:
       (i)  one bare 15.0 mm gap between the HV_POS and HV_NEG regions;
       (ii) a GROUNDED GUARD CONDUCTOR between them, which converts one 2000 V gap
            into two 1000 V gaps of 7.5 mm each, plus the guard's own copper.

       corridor, bare gap        = 15.0 mm
       corridor, guarded         = 2 x 7.5 + 1.0 (guard trace) = 16.0 mm
       cost of guarding          = +1.0 mm

     Session 1 claimed the guard-ring split is 'free in area'. At THIS class that is
     almost true but not exactly: it costs the guard conductor's own width, 1.0 mm,
     because the recommended clearance is linear in voltage above 500 V and so the
     two halves sum to the whole. 1.0 mm is the correct answer and 'free' is not.
     RECOMMENDED ANYWAY, for the failure behaviour rather than the area: a flashover
     goes to the grounded guard instead of into the other module's output stage, and
     in mode 2 that other stage is ENERGISED, which was not true before G0-A4.
  [PASS] guard-ring split costs exactly the guard conductor width, not double the gap  --  16.0 mm guarded vs 15.0 mm bare = +1.0 mm, i.e. 1.0 mm and not 'free'

     BOARD WIDTH MODEL. Two HV islands side by side, guarded corridor between them,
     HV-to-edge clearance on both outer sides:

       module body                           39.60 x  15.70 mm   [verified-artifact, read from the footprint]
       island width = body + 2 x 4.0 mm      23.70 mm            [ASSUMED margin]
       guarded corridor                      16.00 mm
       HV-to-board-edge, each side            7.50 mm
       ------------------------------------------------
       w_min = 2*7.5 + 2*23.70 + 16.00     =  78.40 mm

     BOARD LENGTH MODEL. Along each island: the bleed string and the monitor divider
     string run SIDE BY SIDE, not end to end, then the changeover relay, then the
     output lead-out. Side by side is legitimate here and the reason is worth stating:
     both strings hang off the SAME HV node and grade to GND over the same distance,
     so if they are CO-GRADED -- laid out so that equal positions along the island sit
     at equal potential -- the voltage BETWEEN them is small everywhere and they need
     no HV gap from each other. That is a layout obligation, not a free lunch: it is
     a generator invariant, and a rotated or reversed string breaks it silently.
     String lengths are COMPUTED in sections 3 and 4 from measured land patterns:
       bleed string              16.35 mm  (2 x 2512 elements + 1 x 2.500 mm inter-element clearance)
       divider string            44.65 mm  (10 x 1206 elements + 9 x 0.600 mm inter-element clearance)
       two strings side by side, width        4.00 mm  (1.00 + 1.00 + 2 x 1.00)
       changeover relay                      20.00 mm            [ASSUMED]
       output lead-out to the bulkhead       12.00 mm            [ASSUMED]
       HV run per island                     76.65 mm
       module body along the same axis       39.60 mm
       ------------------------------------------------
       l_min = 2*7.5 + max(39.60, 76.65)     =  91.65 mm
  [PASS] the two co-graded HV strings fit side by side inside the module's own body width, so putting them in parallel costs no island width at all  --  4.00 mm of strings vs a 15.70 mm module body

     PLAIN ANSWER: the 2000 V normal case forces a board of at least
     79 x 92 mm, i.e. it consumes the 100 x 100 mm fab tier and rules out
     anything smaller. The corridor alone -- copper-free board that exists only to
     hold the two polarities apart -- is 16.00 mm x 76.65 mm = 1226 mm2 = 12.3 % of a
     100 x 100 mm board.
  [PASS] the design fits the 100 x 100 mm fab tier under the printed-board reading  --  78.40 x 91.65 mm required

     THE SAME MODEL UNDER THE CONSERVATIVE MG IIIa READING (every number doubles):
       HV-to-GND 15.0 mm, span 30.0 mm, corridor 31.0 mm
       w_min = 108.40 mm    l_min = 106.65 mm
       ==> DOES NOT FIT the 100 mm tier.

     THIS IS WHY THE UNVERIFIED STANDARD MATTERS. Under the printed-board reading the
     board fits the cheap tier; under the material-group-IIIa reading it does not.
     The open question in 1.5 is not academic bookkeeping -- it decides board size,
     fab tier and enclosure. Resolve it BEFORE layout, not at the fab-commit gate.
  [PASS] the two candidate readings of the standard give DIFFERENT board tiers, so the unresolved standards question is decision-relevant and not bookkeeping  --  printed-board 78.4 x 91.7 mm fits; MG IIIa 108.4 x 106.7 mm does not fit 100 mm

     THE TWO OUTPUT CONNECTORS -- and a result that saves a lot of panel.
     Mode 2 puts +1000 V on OUT_A and -1000 V on OUT_B at the same time, so the naive
     reading is that the two bulkheads must be 15.0 mm apart. They must not:
       * an SHV bulkhead's SHELL is at chassis ground, and the chassis is bonded to
         GND ([ISEG] Table 4: 'Case is connected to GND'), so shell-to-shell is 0 V;
       * each centre conductor sees 1000 V to its OWN shell, not 2000 V to the other
         centre conductor, because the grounded shells sit between them;
       * i.e. the connectors' own grounded bodies ARE the guard ring of 1.6, for free.
     So the panel requirement is the SINGLE-ENDED one per connector (7.5 mm class,
     comfortably inside SHV's own 5 kV rating), and IPC-2221 does not rate panel air
     gaps at all -- it is a PCB standard. What DOES carry the 2000 V is the board-side
     wiring from each output net to its bulkhead, and that stays inside the 15.0 mm
     corridor rule like any other HV copper. Two separate HV leads, routed apart,
     never in one bundle, never in one sleeve.
  [PASS] grounded connector shells reduce the panel problem from the 2x span to the 1x span  --  panel needs the 7.5 mm class per connector, not the 15.0 mm span

-- 1.7  MODULE_CASE <-> system GND -- an UNRATABLE, component-internal item ----------------
     [ISEG] Table 4 note: 'Case is connected to GND'. So the module case, board GND
     and (per the enclosure spec) the chassis are ONE node at 0 V. There is no
     board-level clearance to compute between them: the pair is at zero volts.

     THAT IS NOT THE INTERESTING NUMBER. The interesting number is how far the
     module's own HV pin sits from its own grounded case, because that distance is
     INSIDE the component, is set by iseg, and is NOT ratable by IPC-2221 or
     IEC 60664-1 -- those standards rate printed boards and insulation systems we
     control, not the internals of a purchased module.
     Measured from this project's own footprint [ISEGFP], body centre offset
     +0.60 / +0.23 mm from the pin centroid:
       pad 6 (HV)  at (+17.40, +5.08) mm, pad 2.10 mm dia
       pad 7 (GND) at (+17.40, -5.08) mm
       body edges   x = +20.40 mm, y = +8.08 mm
       HV pin to nearest grounded case edge = 3.00 mm
       HV pad to GND pad, copper edge to copper edge = 10.16 - 2.10 = 8.06 mm

     So at 1000 V the module holds its HV pin 3.00 mm from its own grounded case,
     while this design demands 7.5 mm between HV copper and GND copper on the
     board -- 2.5x more. The module is not wrong and we are not wrong: iseg is
     potting/encapsulating an internal insulation system whose withstand voltage
     they type-test and DO NOT PUBLISH, and we are spacing bare air over uncoated
     laminate. The two are not comparable and must not be compared.

     WHAT THIS MEANS IN PRACTICE, stated as rules rather than as a number:
       1. Do NOT apply the board clearance rule to the module's own pin field.
          A DRC that flags pad 6 against pad 7 at 7.5 mm is flagging iseg's
          construction, not ours. Our footprint must nonetheless CLEAR it --
          see the assertion below, which passes here and would not at 2 kV.
       2. Do NOT run board copper into the 3.00 mm shadow around pad 6. The
          board-side requirement is still 7.5 mm; the module's internals do not
          license us to be tighter.
       3. The module case is a TOUCHABLE grounded conductor. It is the reason the
          chassis bond is a safety requirement and not an EMC nicety.
       4. iseg publishes NO isolation/withstand rating for HV-pin-to-case. That
          question is on the open list to ask iseg (D-1 companion). Until it is
          answered this row stays UNRATABLE, and no session may substitute a
          board-standard number for it.
  [PASS] the module's own HV-pad-to-GND-pad copper gap clears our board rule at 1000 V  --  8.06 mm available vs 7.5 mm required -- 0.56 mm margin (this FAILS at any class above 1075 V)
  [PASS] the module's INTERNAL HV-pin-to-case distance is tighter than our board rule, which is exactly why this row is unratable rather than merely lenient  --  3.00 mm internal vs 7.5 mm board rule = 2.5x

     *** DEFECT FOUND IN A COMMITTED ARTIFACT, reported not silently fixed ***
     The footprint carries a PER-PAD local clearance override on pad 6 of
     5.00 mm. In KiCad a pad-level (clearance ...) REPLACES the netclass value
     for that pad. The netclass value this probe recommends is 7.5 mm.
     5.00 mm is the BARE IPC B2 value at 1000 V with the 1.5x design margin
     omitted -- so the single most critical pad on the board would be DRC'd at
     5.00 mm while every other HV net is held to 7.5 mm, silently.
     Fix in hardware/hvctl/gen_lib_footprints.py (CREEPAGE_MM must carry the
     design margin) and REGENERATE. Never hand-edit the .kicad_mod. Not fixed
     here: this is the numbers probe, and silently editing another generator
     inside this task is how a finding gets buried.
  [FINDING] hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod carries a per-pad local clearance override of 5.00 mm on pad 6 (HV). A KiCad pad-level clearance REPLACES the netclass clearance, so with the netclass at 7.5 mm the most critical pad on the board is silently checked at 5.00 mm -- the bare IPC B2 value with the 1.5x design margin dropped. FIX THE GENERATOR gen_lib_footprints.py (its CREEPAGE_MM constant) and regenerate; do not hand-edit the artifact. Deliberately NOT fixed by this probe.
  [BLIND SPOT] this section cannot see: whether the fabricator can hold the spacing (no DFM query run); the real surface resistivity of the chosen laminate; altitude (column B3 is 5x B2 above 3050 m -- irrelevant at New Haven, 12 m); the module's internal withstand voltage, which iseg does not publish; and whether the transcribed standards values are the right values at all, which is the open item of 1.5.

============================================================================================
SECTION 2 -- HV NETCLASS RULES (.kicad_pro net_settings.classes + .kicad_dru)
============================================================================================
Source for the required field set: KiCad 10.0 net_settings.classes field set, measured at runtime from a project file KiCad itself wrote: hardware/phase0_env_proof/env_proof.kicad_pro. [verified-artifact]

-- 2.1  HV track width is not an ampacity question -----------------------------------------
     Worst-case HV current on this board = 1.5 x Inom = 0.75 mA ([ISEG] Table 2 note).
     A 0.5 mm track in 1 oz external copper carries 1.44 A at a 10 C rise
     (IPC-2221 fit I = 0.048 * dT^0.44 * A^0.725, A in mil^2). Headroom = 1921x.
     HV track width is therefore chosen for etch-defect robustness, edge-field
     uniformity and inspectability -- 0.5 mm minimum, rounded corners, no acute
     angles. DRC cannot check corner geometry, so that half is a generator invariant.
  [PASS] 0.5 mm HV track has >100x ampacity headroom  --  1.44 A capacity vs 0.75 mA demand

-- 2.2  Class definitions for the frozen part ----------------------------------------------
     class           clearance  track_width   carries
     HV_POS               7.5mm         0.5mm   positive module HV pin -> changeover relay
     HV_NEG               7.5mm         0.5mm   negative module HV pin -> changeover relay
     HV_OUT_A             7.5mm         0.5mm   output A: combined bipolar (mode 1) or positive (mode 2)
     HV_OUT_B             7.5mm         0.5mm   output B: dead (mode 1) or negative (mode 2)

     All four take the SINGLE-ENDED 7.5 mm value, not the 15.0 mm span value,
     because a KiCad netclass clearance is a MINIMUM AGAINST EVERYTHING. Putting
     15.0 mm here would also push every HV net 15.0 mm away from GND, which is twice
     what GND needs and would waste the board twice over.

     NOTE the mode-2 consequence: HV_OUT_B is a REAL, PERMANENTLY-CLASSED HV net now.
     Session 1 had one output net. Two outputs means two HV classes, two bleed paths,
     two monitor dividers and two connectors -- all of it doubled, none of it shared.

-- 2.3  The pairwise rule a netclass structurally cannot express ---------------------------
     KiCad's netclass 'clearance' is a per-class minimum against all other copper. It
     has no pairwise form. The 15.0 mm HV_POS<->HV_NEG requirement therefore lives in
     hardware/hvctl/hvctl.kicad_dru:

        (version 1)
        (rule "HV_POS to HV_NEG bipolar span"
          (constraint clearance (min 15.0mm))
          (condition "A.NetClass == 'HV_POS' && B.NetClass == 'HV_NEG'"))
        (rule "HV_OUT_A to HV_OUT_B bipolar span"        ; mode 2, both live
          (constraint clearance (min 15.0mm))
          (condition "A.NetClass == 'HV_OUT_A' && B.NetClass == 'HV_OUT_B'"))
        (rule "HV nets to board edge"
          (constraint edge_clearance (min 7.5mm))
          (condition "A.NetClass == 'HV_POS' || A.NetClass == 'HV_NEG' || A.NetClass == 'HV_OUT_A' || A.NetClass == 'HV_OUT_B'"))

     TWO pairwise rules now, not one. G0-A4 added the second: in mode 2 the two
     OUTPUT nets are simultaneously live at opposite polarity, exactly like the two
     module nets. A design that rules only the module pair is under-spaced
     everywhere downstream of the relay.
  [FINDING] G0-A4 adds a SECOND pairwise DRC rule that did not exist in session 1: HV_OUT_A <-> HV_OUT_B must also hold 15.0 mm, because in dual-unipolar mode the two OUTPUT nets are simultaneously live at opposite polarity. Ruling only the HV_POS<->HV_NEG module pair leaves every net downstream of the changeover relay silently spaced for 7.5 mm instead of 15.0 mm.

     And never infer 'the rule applied' from 'DRC passed'. kicad-cli pcb drc EXITS 0
     ON VIOLATIONS unless --exit-code-violations is passed (docs/ENVIRONMENT.md), so
     the check must read the report back and look for the rule BY NAME.

-- 2.4  Every class must carry its schematic fields ----------------------------------------
     Required field set, measured from a project file KiCad 10.0 wrote itself:
       bus_width, clearance, diff_pair_gap, diff_pair_via_gap, diff_pair_width, line_style, microvia_diameter, microvia_drill, name, pcb_color, priority, schematic_color, track_width, tuning_profile, via_diameter, via_drill, wire_width
     Of these the SCHEMATIC-side fields are: wire_width, bus_width, line_style, schematic_color
  [PASS] class HV_POS carries the complete KiCad 10 field set  --  17/17 fields
  [PASS] class HV_NEG carries the complete KiCad 10 field set  --  17/17 fields
  [PASS] class HV_OUT_A carries the complete KiCad 10 field set  --  17/17 fields
  [PASS] class HV_OUT_B carries the complete KiCad 10 field set  --  17/17 fields
  [PASS] hardcoded field list matches the field set KiCad 10.0 actually wrote  --  read from env_proof.kicad_pro

-- 2.5  Assignment patterns ----------------------------------------------------------------
     netclass_patterns uses globs. Hierarchical net names need the sheet wildcard or
     the pattern silently matches nothing (bootstrap V.3):
         {"netclass": "HV_POS", "pattern": "*/HV_POS*"}
         {"netclass": "HV_NEG", "pattern": "*/HV_NEG*"}
         {"netclass": "HV_OUT_A", "pattern": "*/HV_OUT_A*"}
         {"netclass": "HV_OUT_B", "pattern": "*/HV_OUT_B*"}
  [BLIND SPOT] this section cannot see: whether KiCad actually applied the class (only reading back track widths and running DRC with the named custom rule proves that); whether any pattern matched any net; per-pad local clearance overrides, which SILENTLY REPLACE the netclass value and which section 1.7 caught on pad 6 of the module footprint.

============================================================================================
SECTION 3 -- BLEED / DISCHARGE / STORED ENERGY at 1000 V
============================================================================================
Touch-safe threshold: 60 V DC.  Touch-safe DC threshold 60 V DC: the accessible-part limit used by IEC 61010-1 and the ES1 d.c. voltage limit of IEC 62368-1. [recalled -- confirm clause numbers against the standard before Phase 7]
Hazardous-energy thresholds: 350 mJ and 50 uC.  Hazardous stored-energy thresholds 350 mJ and 50 uC (IEC 62368-1 electrical energy source classification / IEC 61010-1). [recalled -- confirm before Phase 7]

-- 3.1  Output capacitance -- the assumption, and it is MEASURABLE NOW ---------------------
     [ISEG] specifies NO output capacitance. Everything in this section inherits that
     gap. Session 1 could only assume; THE MODULES ARE NOW IN HAND, so every term
     below is a bench measurement away from being a fact.

       board stray (HV copper, connector, divider top node)      20 pF   [ASSUMED]
       module internal output capacitance                       100 pF   [ASSUMED -- *** MEASURABLE NOW ***]
       SHV coaxial lead                                     100 pF/m   [ASSUMED]
       detector / load                                   0 ..   10 nF   [interface limit NUM-13]

       C1  bare board, no cable           C_total =     0.120 nF
       C2  2 m SHV lead, no load          C_total =     0.320 nF   <- NOMINAL
       C3  2 m SHV lead + 1 nF load       C_total =     1.320 nF
       C4  10 m lead + 10 nF load         C_total =    11.120 nF   <- WORST

-- 3.2  R required for a chosen discharge time -- the question as asked --------------------
     R(t) = t / ( C * ln(V0/V_safe) ),  V0 = 1000 V, V_safe = 60 V,
     ln(1000/60) = 2.8134

     t (s)      R at C_nom      I_bleed   R at C_worst      I_bleed
                (0.320 nF)  (% of Inom)     (11.12 nF)  (% of Inom)
     1             1.11 Gohm      0.1801 %       31.96 Mohm      6.2570 %
     5             5.55 Gohm      0.0360 %      159.82 Mohm      1.2514 %
     30           33.32 Gohm      0.0060 %      958.92 Mohm      0.2086 %

     READ THIS THE RIGHT WAY ROUND. A 5 s discharge from 1000 V needs 5.6 Gohm at
     the nominal capacitance -- a resistance so high that board surface leakage would
     swamp it and a real part would not hold its value. DISCHARGE TIME IS NOT THE
     CONSTRAINT AT THIS CLASS. The constraints are the permanent-load budget and the
     resistor's working-voltage rating. That inverts the usual bleed-design intuition
     and is only visible with the numbers on the page.

-- 3.3  The bleed we actually fit, sized by the permanent-load budget ----------------------
     R_bleed = Vnom / (f * Inom),  f = 0.10
             = 1000 / (0.10 * 0.0005) = 20.0 Mohm
     I_bleed = 50.0 uA = 10.00 % of Inom      P_bleed = 50.0 mW
     tau     = R*C = 6.4 ms at C_nom, 222.4 ms at C_worst

     The bleed is PERMANENT. A switched bleed can fail open, and a bleed that only
     runs on command is not a bleed. So f is a real budget, spent forever.

     capacitance scenario                  t to 60 V      verdict
     bare board, no cable                  0.0068 s            ok
     2 m SHV lead, no load                 0.0180 s            ok
     2 m SHV lead + 1 nF load              0.0743 s            ok
     10 m lead + 10 nF load                0.6257 s            ok
  [PASS] the 20.0 Mohm bleed reaches 60 V within 5 s in every capacitance scenario  --  worst 0.6257 s at 11.12 nF
  [PASS] bleed current is exactly the budgeted fraction of Inom  --  50.0 uA of a 500.0 uA Inom = 10.00 %

-- 3.4  How many bleeds, and where -- G0-A4 doubles this -----------------------------------
     One bleed PER MODULE, on that module's own HV pin, UPSTREAM of the changeover
     relay. A bleed only downstream cannot discharge the node behind an open contact,
     and in mode 1 that node is exactly the one holding full voltage after disable.
     PLUS one bleed per OUTPUT node, downstream, to cover the cable and the load.

     Mode 1 (one output):  2 module bleeds + 1 output bleed = 3
     Mode 2 (two outputs): 2 module bleeds + 2 output bleeds = 4
     Fit 4. The mode is switchable at runtime, so the board must carry the mode-2 set.

     PERMANENT LOAD PER MODULE, both loads present at once in mode 2:
       bleed            10.00 % of Inom = 50.0 uA
       monitor divider  1.00 % of Inom = 5.0 uA   (section 4 -- the binding one)
       ------------------------------------------
       total            11.00 % of Inom = 55.0 uA, leaving 445.0 uA = 89.00 % for the load
     In mode 2 EACH module carries its own copy of this. The budgets do not share and
     do not average: two outputs means two full sets of permanent load.
  [PASS] permanent load per module (bleed + divider) stays under 15 % of Inom  --  11.00 % = 55.0 uA of 500.0 uA

     And per DECISIONS NUM-09 each bleed is TWO PARALLEL STRINGS, never one chain:
     an N-element series chain has N chances to go open and an open bleed is silently
     undetectable. Two 40.0 Mohm strings in parallel give the 20.0 Mohm target and
     degrade tau by 2x on a single open instead of removing the path entirely.

-- 3.5  Working-voltage rating and the series-string count -- the binding constraint -------
     A resistor's WORKING VOLTAGE rating, not its power rating, is what limits it at
     1000 V.  N = ceil( V / (V_rating * derate) ),  derate = 0.50.
     Ratings tagged [ARCH12] come from the Yageo RC datasheet PDF, read locally.

     part option                     V_rated     N  V/element  P/element     pad gap   IPC B2
     0805 thick film (Yageo RC)         150V    14      71.4V     3.57 mW    0.825 mm   0.600 mm  OK
     1206 thick film (Yageo RC)         200V    10     100.0V     5.00 mW    1.925 mm   0.600 mm  OK
     2010 thick film (Yageo RC)         200V    10     100.0V     5.00 mW    3.625 mm   0.600 mm  OK
     2512 thick film (Yageo RC)         200V    10     100.0V     5.00 mW    4.925 mm   0.600 mm  OK
     1206 HV series                     800V     3     333.3V    16.67 mW    1.925 mm   2.500 mm  *** REJECTED ***
     2512 HV series                    1500V     2     500.0V    25.00 mW    4.925 mm   2.500 mm  OK

     1 of 6 candidates are rejected ON THEIR OWN PAD GAP. A part's voltage RATING
     and its PACKAGE CLEARANCE are independent constraints and only the first is on
     the datasheet: a rating high enough to need few elements puts a large voltage
     across a small package.
  [FINDING] Bleed/divider part '1206 HV series' is REJECTED at 1000 V: a working-voltage rating high enough to need only N=3 elements puts 333 V across a package whose own pad-to-pad gap is 1.925 mm, below the 2.500 mm IPC-2221 B2 clearance that voltage demands.
  [PASS] the pad-gap screen actually rejects something (proves it is not vacuous)  --  1 rejected: 1206 HV series

     RECOMMENDED BLEED PART: 2512 HV series.
       N = 2, 500 V per element, 25.00 mW per element
       pad gap 4.925 mm vs IPC B2 requirement 2.500 mm at 500 V
       string length = 2 x 6.925 mm land + 1 x 2.500 mm inter-element = 16.35 mm
       x2 for the parallel-string rule -> two strings side by side, not end to end.
  [PASS] recommended bleed part clears its own pad gap at the per-element voltage  --  N=2, 500 V/element, gap 4.925 mm vs need 2.500 mm
  [PASS] the ARCH-12 correction has teeth: a 200 V-rated 2512 needs more elements than the 500 V figure session 1's probe used  --  N=10 at the verified 200 V rating vs N=4 at the folklore 500 V rating
  [FINDING] Session 1's probe rated a standard 2512 chip resistor at 500 V working voltage. DECISIONS ARCH-12, which is [verified-artifact] from the actual Yageo RC datasheet, says 200 V -- and that upsizing 1206->2010->2512 buys power, not volts. The corrected rating changes the standard-part series count at 1000 V from N=4 to N=10. This probe uses the verified number; the two documents disagreed and the datasheet wins.

-- 3.6  Stored energy: shock hazard, or startle hazard? ------------------------------------
     E = 0.5*C*V^2 ,  Q = C*V .  Thresholds 350 mJ / 50 uC.

     scenario                            V (V)       E (mJ)       Q (uC)    verdict
     bare board, no cable                 1000      0.06000       0.1200      below
  [PASS] stored energy and charge below the hazard thresholds (bare board, no cable)  --  E=0.06000 mJ (<350), Q=0.1200 uC (<50)
     2 m SHV lead, no load                1000      0.16000       0.3200      below
  [PASS] stored energy and charge below the hazard thresholds (2 m SHV lead, no load)  --  E=0.16000 mJ (<350), Q=0.3200 uC (<50)
     2 m SHV lead + 1 nF load             1000      0.66000       1.3200      below
  [PASS] stored energy and charge below the hazard thresholds (2 m SHV lead + 1 nF load)  --  E=0.66000 mJ (<350), Q=1.3200 uC (<50)
     10 m lead + 10 nF load               1000      5.56000      11.1200      below
  [PASS] stored energy and charge below the hazard thresholds (10 m lead + 10 nF load)  --  E=5.56000 mJ (<350), Q=11.1200 uC (<50)

     MODE-2 BRIDGING CASE, which did not exist before G0-A4: a person or a dropped
     tool bridging OUT_A to OUT_B sees 2000 V across the SERIES combination of the
     two output capacitances, C_A*C_B/(C_A+C_B) = C/2 for equal outputs:
       bare board, no cable           C_series    0.060 nF   E =   0.12000 mJ   Q =   0.1200 uC
  [PASS] mode-2 OUT_A-to-OUT_B bridging stays below the hazard thresholds (bare board, no cable)  --  E=0.12000 mJ, Q=0.1200 uC at 2000 V
       2 m SHV lead, no load          C_series    0.160 nF   E =   0.32000 mJ   Q =   0.3200 uC
  [PASS] mode-2 OUT_A-to-OUT_B bridging stays below the hazard thresholds (2 m SHV lead, no load)  --  E=0.32000 mJ, Q=0.3200 uC at 2000 V
       2 m SHV lead + 1 nF load       C_series    0.660 nF   E =   1.32000 mJ   Q =   1.3200 uC
  [PASS] mode-2 OUT_A-to-OUT_B bridging stays below the hazard thresholds (2 m SHV lead + 1 nF load)  --  E=1.32000 mJ, Q=1.3200 uC at 2000 V
       10 m lead + 10 nF load         C_series    5.560 nF   E =  11.12000 mJ   Q =  11.1200 uC
  [PASS] mode-2 OUT_A-to-OUT_B bridging stays below the hazard thresholds (10 m lead + 10 nF load)  --  E=11.12000 mJ, Q=11.1200 uC at 2000 V
     Energy doubles (half the C, four times the V^2) and charge is unchanged.

     Inverted -- the capacitance at which 1000 V BECOMES a hazardous stored-energy
     source:  charge criterion  C = Q/V    =   50.0 nF
              energy criterion  C = 2E/V^2 =  700.0 nF
     The CHARGE criterion binds first.
  [PASS] the charge criterion binds before the energy criterion at 1000 V  --  50.0 nF (charge) vs 700.0 nF (energy)

     *** THE ANSWER TO 'SHOCK OR STARTLE' ***
     STORED energy is a STARTLE hazard here, not a shock hazard: 5.56000 mJ worst case
     against a 350 mJ threshold, 63x below, and 11.12 uC against 50 uC.
     THE SUSTAINED SOURCE IS THE SHOCK HAZARD: [ISEG] limits Iout to ~1.5*Inom =
     0.75 mA, available continuously at up to 1000 V, and in mode 2 from BOTH outputs
     at once. 0.75 mA DC through a body is above the let-go threshold for a hand-to-
     hand path. The current limit reduces the CONSEQUENCE of contact; it does not
     make contact acceptable, and it is not an alternative to enclosure.

     DESIGN LIMIT that falls out of this: keep total output capacitance below 50 nF
     per output. Concretely, fit NO bulk HV filter capacitor: [ISEG] already delivers
     <30 mVpp ripple above 20 V, and a filter cap would buy a little ripple and
     sell the stored-energy classification.
  [FINDING] At 1000 V this instrument is a SUSTAINED-SOURCE shock hazard and a STORED-ENERGY startle hazard. Worst credible stored energy is 5.560 mJ against the 350 mJ threshold (63x below) and 11.12 uC against 50 uC; the sustained 0.75 mA at up to 1000 V -- from BOTH outputs simultaneously in mode 2 -- is the thing that hurts. Design limit: total output capacitance < 50 nF per output, i.e. no bulk HV filter capacitor.

-- 3.7  A MODE CHANGE is a new transition and needs its own bleed dwell --------------------
     G0-A4 consequence 4. Moving the mode routing element while either output is live
     hot-switches a 1000 V contact and can weld it. The transition must be:
       1. command both set-points to zero
       2. disable both modules (+VIN removal primary, /ON secondary)
       3. DWELL for the bleed, then VERIFY both outputs below 60 V on the
          INDEPENDENT monitors -- verify, do not merely wait
       4. move the mode element COLD
       5. read the mode element's PHYSICAL position back before re-enabling anything

     Dwell budget: 3 x the worst-case bleed time = 3 x 0.6257 s = 1.877 s. Round up to
     2.0 s in the state machine and TRIP -- do not fall through -- on timeout.
     Per DECISIONS ARCH-24 the DISCHARGE->CHANGEOVER edge is the one transition that
     must never fall through on timeout, because 'off' is not where a timeout leaves
     you -- a stuck-live node plus a moving contact is. MODE CHANGE inherits that.
  [PASS] a 3x-bleed-time mode-change dwell is shorter than the touch-safe target, i.e. the dead-band is bounded by the relay, not by the bleed  --  1.877 s dwell vs 5 s target
  [BLIND SPOT] this section cannot see: the module's real output capacitance and internal bleeder (both unpublished, both MEASURABLE NOW); the load's actual capacitance; board surface leakage, which at 1000 V across a contaminated 7.5 mm gap can rival the bleed itself; and any of this under fault, since the model assumes the bleed is intact.

============================================================================================
SECTION 4 -- INDEPENDENT HV MONITOR DIVIDER (one PER OUTPUT -- G0-A4 doubles it)
============================================================================================
Brief invariant (c): output voltage monitored INDEPENDENTLY of the module readback.
Target to beat: [ISEG] VMON accuracy = 1 % * Vnom = 10.0 V.
ADC assumed: ADS1115-class (16-bit delta-sigma, I2C), FS +/-2.048 V, 16 bit.

-- 4.1  The binding constraint, stated first because everything follows from it ------------
     Inom is 500.0 uA. A divider drawing 5.0 uA is EXACTLY 1.00 % of it.
     At the 1 kV / 0.5 mA class the monitor's own load is a first-order claim on the
     output current budget, not a rounding error. That is what makes this class the
     deliberate worst case, and it is why the loading budget -- not accuracy, not
     resolution -- sets the divider's top-leg resistance.

         Rt = Vnom / (f * Inom),  f = 0.01
            = 1000 / (0.01 * 0.0005) = 200.0 Mohm
  [PASS] the divider draws exactly 5.0 uA, which is exactly 1.00 % of the 0.5 mA Inom  --  5.0000 uA = 1.0000 % of Inom

     AND IN MODE 2 THERE ARE TWO OF THESE, one per output, each loading ITS OWN
     module by the same 1.00 %. The budgets do not share. Total monitor load across
     the instrument is 10.0 uA, but the number that matters is the per-module 5.0 uA.

-- 4.2  Ratio, string composition and per-resistor voltage ---------------------------------
     Topology (passive, bipolar-capable, single-supply ADC, no negative rail):
         HV_OUT --[Rt]--+--[Rb]-- GND       V_node = (V_hv/Rt + VREF/Ro) / G
                        +--[Ro]-- VREF      G = 1/Rt + 1/Rb + 1/Ro
                        +--> unity buffer --> ADC
     The offset leg puts V_hv = 0 at mid-scale so -1000..+1000 V maps to 0..2.048 V
     with no negative rail and NO POLARITY FLAG -- the monitor reports the SIGN, which
     is exactly what a polarity-switching instrument has to verify.

       attenuation A = ADC_FS / (2*Vnom)        = 1.024000e-03  (976.6 : 1)
       Rt  (top leg, HV)                        =     200.00 Mohm
       Rp  = Rb || Ro = Rt*A/(1-A)              =     205.01 kohm
       Ro  (offset leg to VREF 2.500 V)          =     500.00 kohm
       Rb  (bottom leg to GND)                  =     347.49 kohm
       I_div at +Vnom                           =      5.000 uA

     TOP-LEG STRING COMPOSITION: N = 10 series elements
       per element  R = 20.00 Mohm    V = 100.0 V    P = 0.500 mW    dT_self = 0.0300 K
       part 1206 HV series, package 1206, working-voltage rating 800 V [ASSUMED]
       package 1206: pad gap 1.925 mm vs IPC B2 need 0.600 mm at 100.0 V per element -> OK
       string length = 10 x 3.925 mm land + 9 x 0.600 mm inter-element = 44.65 mm
  [PASS] divider element package clears its own pad gap at the per-element voltage  --  gap 1.925 mm vs need 0.600 mm at 100.0 V
       working voltage: 100.0 V per element vs 800 V rating x 0.50 derate = 400.0 V
  [PASS] divider element stays inside its own derated working-voltage rating  --  100.0 V per element vs 400.0 V allowed (800 V rating, 2x derate) at N=10
  [PASS] the string geometry and the error budget use the SAME element count  --  geometry N=10, error budget N=10

     WHY NOT ORDINARY 1 % CHIP RESISTORS: [ARCH12] says the Yageo RC +/-1 % range
     stops at 2.2 Mohm. A 200 Mohm top leg out of ordinary parts would need
       ceil(200 Mohm / 2.2 Mohm) = 91 elements in series.
     That is not a divider, it is a liability: 91 chances to go open, 182 joints, and
     a physical length of 411 mm. Purpose-made HV divider elements are not a luxury
     at this class, they are the only way the part count is sane.
  [PASS] independently reproduces DECISIONS ARCH-12's '>=91 parts' figure for a top leg built from ordinary 1 % chip resistors  --  200 Mohm / 2.2 Mohm = 91 elements

-- 4.3  Error budget, referred to the HV output, at full scale -----------------------------
       VCR         : err = V_hv * k_vcr * (V_hv/N)  <- the 1/N is the whole design.
                     A resistor's voltage coefficient acts on the voltage across THAT
                     element. Splitting the top leg into N puts V_hv/N across each, so
                     the leg's fractional error is k*V_hv/N and the error referred to
                     the output is k*V_hv^2/N -- QUADRATIC in voltage, INVERSE in
                     element count. It is the single most effective lever and it is
                     invisible unless you write it down.
       TCR mismatch: err = V_hv * dTCR * dT
       self-heating: err = V_hv * dTCR * (I^2 * R_element * Rth)
       ADC INL     : err = INL_lsb * LSB / A
       ADC gain    : err = V_hv * gain_drift * dT   (initial gain calibrated out)
       offset ref  : err = dVREF * (Rpar/Ro) / A

     term                        error (V)      % of Vnom
     VCR (k*V^2/N)                  0.1000        0.0100 %
     TCR mismatch                   0.2000        0.0200 %
     self-heating                   0.0003        0.0000 %
     ADC INL                        0.0610        0.0061 %
     ADC gain drift                 0.1000        0.0100 %
     offset ref drift               0.2000        0.0200 %
                              ------------   ------------
     RSS                            0.3221        0.0322 %

     ACHIEVED ACCURACY: 0.322 V at 1000 V output, calibrated, guarded, clean board.
     MODULE VMON:       10.0 V (1 % * Vnom).   RATIO: 31.0x better.
  [PASS] the divider beats the module's own VMON accuracy (clean, guarded)  --  0.3221 V RSS vs 10.0 V, 31.0x

     Monitor resolution: 1 ADC LSB (62.5 uV) referred to HV = 0.0610 V.
     Self-heating is 0.0300 K and contributes 0.00030 V. Every instinct that says 'HV
     divider, watch the self-heating' is imported from a higher-current problem and
     is wrong here -- at 5.0 uA the top leg dissipates 0.500 mW per element.

-- 4.4  SURFACE LEAKAGE -- the term that decides whether any of the above is true ----------
     A leakage path R_leak from the HV node to the tap or to GND sits in PARALLEL
     with the 200 Mohm top leg. Fractional ratio error = Rt / R_leak, so referred to
     the output:   err = V_hv * Rt / R_leak

     board condition                        R_leak        err (V)     vs VMON 10 V
     clean, conformally coated            1e+12 ohm         0.200               ok
     bench-clean bare FR-4                1e+10 ohm        20.000            WORSE
     contaminated / humid                 1e+09 ohm       200.000            WORSE

     At bench-clean bare FR-4 the leakage term ALONE is 20.0 V -- larger than every
     other term put together and larger than the 10 V VMON accuracy this divider
     exists to improve on. An unguarded 200 Mohm divider at 1000 V is not an
     independent monitor, it is a humidity sensor.

     MITIGATION, and it is mandatory, not optional:
       1. A GUARD RING at TAP POTENTIAL, driven from the buffer output, surrounding
          the tap node and running alongside the whole top-leg string. Leakage then
          flows HV -> guard (driven, harmless) instead of HV -> tap, and the residual
          guard-to-tap path sits across ~0 V. Assumed improvement 100x [ASSUMED].
       2. Conformal coating over the divider region specifically.
       3. The divider gets its OWN netclass clearance, not the generic HV one.

     condition                            leak err (V)  TOTAL RSS (V)
     clean, conformally coated                  0.2000         0.3791
     clean, conformally coated + guard ring         0.0020         0.3221
     bench-clean bare FR-4                     20.0000        20.0026   <-- FAILS to beat VMON
     bench-clean bare FR-4 + guard ring         0.2000         0.3791
     contaminated / humid                     200.0000       200.0003   <-- FAILS to beat VMON
     contaminated / humid + guard ring          2.0000         2.0258
  [PASS] an UNGUARDED divider on bench-clean bare FR-4 is WORSE than the module's own VMON, which is the proof that the guard ring is a requirement and not a polish  --  leakage term 20.0 V alone vs VMON 10.0 V
  [PASS] WITH the guard ring the divider beats VMON even on bench-clean bare FR-4  --  0.3791 V total vs 10.0 V, 26.4x
  [FINDING] Surface leakage is the dominant, non-obvious error term of the independent monitor at this class. With Rt = 200 Mohm forced by the 1.00 %-of-Inom loading budget, a 10 Gohm board leakage path injects 20.0 V of ratio error -- on its own larger than the 10.0 V VMON accuracy the divider exists to improve on. A DRIVEN GUARD RING AT TAP POTENTIAL IS THEREFORE A REQUIREMENT OF THE MONITOR, not a refinement, and it must be in the netclass/DRC rules and in the generator's invariants.

-- 4.5  Independence, and the disagreement threshold ---------------------------------------
     This divider shares NOTHING with the module's VMON path: different node, different
     reference, different ADC channel, different rail. Firmware must compare the two
     and fault on disagreement -- that comparison IS the value of the independent
     monitor.
       legitimate disagreement, quadrature = sqrt(10.0^2 + 0.379^2) = 10.007 V
       trip threshold, DECISIONS ARCH-23 = 2 % * Vnom = 20.0 V
       margin over legitimate disagreement = 2.00x
     It catches an open divider element, a stuck relay, a module in current limit, an
     ADC reference collapse and partial HV breakdown -- none of which either monitor
     detects alone.
  [PASS] the 2 %-of-Vnom disagreement trip sits above legitimate quadrature disagreement  --  20.0 V trip vs 10.007 V legitimate, 2.00x margin

     MODE 2 ADDS A SECOND COMPARISON AND A THIRD CHECK. With two outputs live there
     are two independent monitors and two VMONs, so firmware must also verify that
     OUT_A reads POSITIVE and OUT_B reads NEGATIVE. A sign disagreement means the
     mode element is not where the mode bit says it is -- which is precisely the
     failure G0-A4 warns about, and the independent monitor is the only thing on the
     board that can see it.
  [BLIND SPOT] this section cannot see: resistor VCR is a datasheet parameter this probe assumes, not measures; the real surface resistivity of the finished board (the term that dominates 4.4); ADC noise in the presence of the module's switching converter; and the calibration it assumes, which has not been performed.

============================================================================================
SECTION 5 -- THE VSET CLAMP  (PRIMARY SAFETY ELEMENT)
============================================================================================
[ISEG] Table 1, verbatim: 'Attention! Output voltage is internally not limited!'
                          'At Vset > 2.5 V -> Vout > Vnom is possible!'
                          'Do not use Vset > 2.5 V !'
[ISEG] implies an internal 10 kohm pull-up from VSET to Vref (the Rset formula has
no other consistent reading -- STATUS.md 1.1, survived 3 skeptics) and requires any
driver to have Ri << 10 kohm.

G0-A3 put HV set-point and enable commands on a NETWORK WITH WRITE AUTHORITY. The
human made that choice with the risk stated. The consequence is that the hardware
interlock, THIS CLAMP, and the soft limits carry the entire safety case. This section
is therefore written as a safety analysis, not as a component selection.

-- 5.1  The un-clamped hazard, quantified on the frozen part -------------------------------
     condition                              Vset (V)         Vout
     3.3 V logic rail on VSET                 3.3000      1333 V  (133 % of Vnom)
     5 V rail on VSET                         5.0000      2020 V  (202 % of Vnom)
     VSET open -> internal pull-up            2.5000      1010 V  (101 % of Vnom)
     VSET open, R_pd BOTH fitted (500 ohm)       0.1190        48 V  (4.8 % of Vnom)
     VSET open, ONE R_pd open (1000 ohm)       0.2273        92 V  (9.2 % of Vnom)

     Two inversions of ordinary intuition, both from [ISEG], both load-bearing:
       * an OPEN VSET commands FULL SCALE, because of the internal pull-up to Vref;
       * /ON is 'LOW or n.c. -> HV ON', so a FLOATING /ON turns HV ON.
     The module's un-driven default state is ENERGISED AT OVER-RANGE. 'Unpowered =
     safe' is false for this part.
  [PASS] the fitted pull-down PAIR holds the driver-dead output below 10 % of Vnom  --  4.8 % = 48 V instead of 1000 V, at R_pd(pair) = 500 ohm

     R_pd must be DUPLICATED (two 1000 ohm in parallel = 500 ohm) per DECISIONS
     ARCH-18. State BOTH numbers, because they are different arguments:
       * the PAIR is what is fitted, so 4.8 % is the driver-dead output in service;
       * ONE element going open degrades that to 9.2 % -- still safe, and that is
         the POINT of the duplication. A SINGLE pull-down going open would restore
         the documented unsafe default (101 % of Vnom) silently, and an open
         pull-down is not observable from anywhere else on the board.
  [PASS] a SINGLE-OPEN pull-down still holds the driver-dead output below 10 % of Vnom, which is what makes the duplication a fail-safe rather than a fail-over  --  9.2 % (one open) vs 4.8 % (both fitted) vs 101 % (none)

-- 5.2  Residual set-point error injected by each candidate clamp --------------------------
     Any series resistance in the VSET path divides against the internal 10 kohm:
         error = (Vref - Vdrive) * Rs / (10 k + Rs),   worst at Vdrive = 0

     Rs (ohm)   err @Vset=0 (mV)     err (% FS)    -> Vout error
     0                     0.000        0.0000 %          0.00 V
     10                    2.498        0.0999 %          1.00 V
     47                   11.695        0.4678 %          4.68 V
     100                  24.752        0.9901 %          9.90 V
     470                 112.225        4.4890 %         44.89 V
     1000                227.273        9.0909 %         90.91 V

     A 1 kohm series resistor -- an utterly ordinary value, and exactly what an RC
     filter on VSET would put there -- produces 91 V of output when ZERO was
     commanded. That is [ISEG]'s 'Ri << 10 kohm' warning made quantitative. It is why
     DECISIONS ARCH-04 forbids ANY resistor between the buffer and the VSET pin: the
     budget is <= 10 ohm, which in practice means 'a track, not a component'.
  [PASS] a 1 kohm series element in the VSET path is disqualifying on its own  --  91 V of uncommanded output at zero command
  [PASS] Rs <= 10 ohm keeps the zero-offset error under 0.11 % of full scale  --  2.498 mV = 0.0999 % FS = 1.00 V at the output

     RESIDUAL ERROR PER CANDIDATE, referred to the output at 1000 V:
     candidate                                           err (V)    % of Vnom    vs +/-1 %
     N  no clamp (DAC straight off the 3.3 V rail)        20.000      2.0000 %        0.50x
     A  series R (10 ohm) + Schottky to precision ref        1.414      0.1414 %        7.07x
     B  RRIO buffer powered FROM the precision ref         1.416      0.1416 %        7.06x
     C  fixed 0.98 attenuator before the buffer            2.450      0.2450 %        4.08x

     Read the last column as 'how much of the module's own +/-1 % (10 V) adjustment
     accuracy the clamp costs'. Candidate B costs about a seventh of it. That is the
     price of making a 1333 V command structurally impossible, and it is cheap.
  [PASS] candidate B's residual set-point error is well inside the module's own accuracy  --  1.416 V vs 10.0 V, 7.1x headroom

-- 5.3  How each candidate CLAMPS, in the no-fault case ------------------------------------
     Module Vref is 2.500 V +/-1 %, i.e. 2.4750 .. 2.5250 V. The clamp ceiling must be
     compared against the LOW end, 2.4750 V, because that is where a given Vset
     commands the largest fraction of Vnom.

     candidate                                     ceiling (V)       max Vout   range lost
     A  Schottky to ref: Vref_ext + Vf                  2.8025       1132 V (113.2 %)       1.09 %
     B  buffer rail: Vref_ext - Vsat                    2.4825       1003 V (100.3 %)       1.88 %
     C  attenuator: Vref_ext * a                        2.4574        993 V (99.3 %)       4.05 %

     A leaves 13.2 % of over-voltage on the table even when it works, because a
     Schottky clamps at Vref + Vf, not at Vref.
     B is structural: a rail-to-rail output physically cannot exceed its own positive
     rail, and that rail IS the precision reference that also feeds the DAC. One part,
     two jobs, and they cannot drift apart because they are the same node. It adds
     ZERO components to the signal path, so it does not violate the <=10 ohm rule.
     C gives a genuinely ONE-SIDED bound (-0.71 % -- guaranteed under Vnom) but pays
     2 % of range for it, unconditionally, and adds a ratio-drift error term.
  [PASS] candidate B's no-fault ceiling is inside the module's own +/-1 % accuracy  --  100.30 % of Vnom = 1003 V
  [PASS] the Schottky candidate clamps LESS tightly than the buffer-rail candidate  --  113.2 % vs 100.30 % of Vnom
     NOTE, said plainly rather than claimed away: NO candidate makes over-voltage
     mathematically impossible. Two references with independent tolerances cannot be
     ordered with certainty. B converts a 133 % hazard into a 0.30 % irrelevance.

-- 5.4  *** SINGLE-FAULT SURVIVAL -- the analysis this section exists for *** --------------
     Each row is ONE fault, from an otherwise-correct board. The number is the
     resulting output as a percentage of Vnom. 'ok' means <= 110 % of Vnom.

     single fault                                      none         A         B         C
     F1 firmware/network commands full DAC code        133%      113%      100%       99%
     F2 VSET net shorted to the 3.3 V rail             133%      133%      133%      133%
     F3 VSET net open (broken track, lifted pad)       101%        5%        5%        5%
     F4 buffer dead / output high-Z                    101%        5%        5%        5%
     F5 precision reference shorted to the 5 V rail      202%      214%      201%      198%
     F6 ONE R_pd open (pair fitted, ARCH-18)             9%        9%        9%        9%
     F7 R_pd NOT duplicated, then it opens             101%      101%      101%      101%

       F1 firmware/network commands full DAC code   the G0-A3 network-write case
       F2 VSET net shorted to the 3.3 V rail        a hard short to a rail is downstream of every clamp
       F3 VSET net open (broken track, lifted pad)  internal pull-up; R_pd saves it
       F4 buffer dead / output high-Z               same node state as F3
       F5 precision reference shorted to the 5 V ra the clamp's own reference becomes the hazard
       F6 ONE R_pd open (pair fitted, ARCH-18)      LATENT, and covered: the surviving element still holds it down
       F7 R_pd NOT duplicated, then it opens        NOT a fault -- a DESIGN CHOICE that turns F6 into a 101 % event

     FAULTS THAT SURVIVE EACH CLAMP (output above 110 % of Vnom):
       none   3 of 7 :  F1, F2, F5
       A      3 of 7 :  F1, F2, F5
       B      2 of 7 :  F2, F5
       C      2 of 7 :  F2, F5

     *** THE RESULT, STATED WITHOUT SOFTENING ***
     The best clamp still lets 2 of 7 single faults through, and one of them (F5)
     reaches 201 % of Vnom = 2012 V, WORSE than the un-clamped 3.3 V case, because
     the fault is IN the clamp's own reference. A clamp that shares a node with the
     thing it protects against fails in the direction of the hazard.
  [PASS] no VSET clamp survives every single fault -- proving the clamp alone is NOT the safety case and an independent backstop is mandatory  --  candidate B (the best) still passes 2 of 7 faults: F2, F5
  [PASS] the clamp is nevertheless worth fitting: it strictly reduces the surviving set  --  2 surviving with clamp B vs 3 with no clamp

-- 5.5  The backstop that covers what the clamp cannot -------------------------------------
     An INDEPENDENT hardware comparator on VMON -- not on the DAC code, not in
     firmware -- that drives /ON HIGH (= HV OFF) when VMON exceeds its threshold.
       trip at 105 % of VMON full scale = 2.625 V  =>  1050 V at the output
       margin over the module's own VMON accuracy (10.0 V) = 40.0 V

     It catches every surviving fault above, because all of them are above 105 %:
       F2 VSET net shorted to the 3.3 V rail           133 % -> tripped
       F5 precision reference shorted to the 5 V ra    201 % -> tripped
  [PASS] the 105 % VMON comparator trips on every fault that survives clamp B  --  smallest surviving over-voltage 133 % vs 105 % trip

     FOUR CONDITIONS ON THE COMPARATOR, or it is decoration:
       1. Its threshold reference must NOT be the same precision reference that
          feeds the DAC and the buffer rail. F5 takes that reference out; a
          comparator referenced to it fails in the same event it exists to catch.
       2. Its output must drive /ON HIGH in HARDWARE, with no firmware in the path.
       3. It must be powered from a rail that survives the faults it covers, and
          losing that rail must ALSO turn HV off (open-drain, pull-up to the module's
          own +VIN per DECISIONS ARCH-17).
       4. It must be TESTABLE without HV: inject 2.625 V at the VMON sense node with
          the MCU held in reset and confirm /ON goes HIGH. That is Stage 2.5 of the
          bench procedure and it is the only cheap moment to prove it.

     AND THE PRIMARY DISABLE IS STILL +VIN REMOVAL, NOT /ON (DECISIONS ARCH-19). A
     module with no input power cannot make HV at all, so the 'LOW or n.c. -> HV ON'
     trap stops being the last line of defence.

-- 5.6  RECOMMENDATION ---------------------------------------------------------------------
     Candidate B + duplicated fail-safe pull-down + independent VMON comparator:
       1. ONE precision reference (0.1 %, low drift) at 2.500 V. It is the DAC
          reference AND the VSET buffer's positive rail. Same node, cannot drift apart.
       2. DAC -> RRIO buffer (unity gain) -> VSET, series resistance <= 10 ohm, i.e.
          a track and not a component. NO RC filter on VSET, ever.
       3. TWO 1000 ohm pull-downs in parallel (= 500 ohm) at the VSET pin:
          driver-dead output becomes 4.8 % of Vnom instead of 101 %, and ONE
          going open degrades that only to 9.2 % -- it does NOT restore the
          unsafe default. Both numbers are stated in 5.1; do not quote one alone.
       4. Independent VMON comparator per 5.5, on its own reference.
       5. /ON open-drain with a pull-up to the module's OWN +VIN, within 5 mm of pin 4.
       6. +VIN switching as the primary disable.
     The buffer must SINK the pull-up current at Vset = 0:
       sink = Vref/10k + 2*Vref/1000 = 250 uA + 5000 uA = 5.25 mA
     Trivial for any RRIO part, but it must be one that SINKS to its negative rail --
     check the datasheet's output-sink curve, not the 'rail-to-rail' marketing line.
  [FINDING] The VSET clamp is a necessary but NOT SUFFICIENT safety element. The best candidate (RRIO buffer powered from the precision reference) still passes 2 of 7 modelled single faults, including a reference-to-5 V short that reaches 201 % of Vnom = 2012 V -- worse than the un-clamped 3.3 V case, because the fault is in the clamp's own reference. The independent VMON comparator, on its OWN reference and driving /ON in hardware, is what closes the set, and +VIN removal is the primary disable. With a network carrying write authority (G0-A3) this chain IS the safety case.
  [BLIND SPOT] this section cannot see: op-amp behaviour during supply ramp (an RRIO part can transiently drive above its settled rail, or go high-Z as the reference starts -- the pull-down covers high-Z, nothing here covers a transient overshoot); reference start-up overshoot; multiple simultaneous faults; and any of this in silicon rather than on paper.

============================================================================================
SECTION 6 -- POWER BUDGET ON THE 5 V RAIL
============================================================================================
Module input currents are [ISEG] Table 1 MAXIMA, not typicals. Vin is 5 V, not 12 V:
the modules and the logic share one rail and there is no galvanic separation between
the HV converter's switching current and the ADC's ground reference.

-- 6.1  Both modules loaded, or one plus margin? -- SETTLED, and the reason CHANGED --------
     one loaded + one at Vout=0  = 180 + 5 =  185.0 mA = 0.93 W
     both loaded                 = 2 x 180    =  360.0 mA = 1.80 W
     delta                                     =  175.0 mA = 0.875 W

     Session 1 argued for BOTH on three grounds that were all about faults and
     transients: overlap during changeover, wanting the MCU alive during an interlock
     failure, and the delta being cheap. Those arguments were correct but they were
     arguments about MARGIN.

     *** G0-A4 REPLACES THEM WITH A REQUIREMENT. ***
     In dual-unipolar mode BOTH MODULES ARE AT FULL OUTPUT SIMULTANEOUSLY AS NORMAL
     OPERATION. Sizing for one-plus-margin is not conservative-or-not, it is WRONG:
     it under-sizes the supply for the instrument's own advertised mode. The
     'only one is ever enabled, so size for one plus margin' argument is DEAD and
     must not be revived under the changeover topology either, because the changeover
     topology is only mode 1 of two.
  [PASS] sizing for both modules loaded is the binding case, not a margin choice  --  360 mA (mode 2 normal operation) vs 185 mA (mode 1 one-plus-idle), +175 mA

-- 6.2  Rail-by-rail worst case ------------------------------------------------------------
     load                                             mA @ 5 V          W
     2 x module, both loaded, [ISEG] maximum             360.0      1.800
     ESP32 500 mA peak on 3.3 V via an 85 % buck         388.2      1.941
     analog: refs, DACs x2, buffers, ADCs x2, comparators       60.0      0.300
     4 relay coils at 20 mA                               80.0      0.400
                                                      --------   --------
     SINGLE 5 V RAIL TOTAL                               888.2      4.441

     RECOMMENDED SUPPLY: 5 V / 1.8 A  (2.0x margin over 888.2 mA)

     Arrangement: one 5 V / 1.8 A external brick
       -> module rail taken DIRECTLY from the brick, each module behind its own series
          ferrite and 22 uF blocking capacitor at +VIN ([ISEG] Table 1 note 2), and
          behind the +VIN disable switch (ARCH-19, primary disable)
       -> separate buck 5 -> 3.3 V for the ESP32
       -> separate LOW-NOISE LDO from 5 V for the analog / reference rail
     The modules and the ESP32 share one rail. The resonant converter's switching
     current and the WiFi TX burst are both on it. Per-module ferrite + bulk cap is
     not optional decoration at 5 V input.
  [PASS] the recommended supply covers 2.0x the computed worst case  --  1.8 A rating vs 888.2 mA x 2.0 = 1776 mA

-- 6.3  The ESP32 burst, and why a capacitor is not the answer -----------------------------
     C = I*dt/dV for a 100 mV droop:
        0.05 ms burst of 500 mA  ->  C =    250.0 uF
        2.00 ms burst of 500 mA  ->  C =  10000.0 uF
     A 50 us RF envelope peak is capacitor territory. A full 2 ms 802.11b frame is
     not -- it needs 10000 uF, which nobody fits.
     CONCLUSION: SIZE THE REGULATOR for >= 500 mA continuous on 3.3 V and fit
     22 uF bulk + 100 nF local. Do not try to solve a 2 ms event with bulk C.
  [PASS] the ESP32 WiFi TX burst is a LARGER 5 V load than both HV modules combined  --  388.2 mA reflected vs 360 mA for two loaded modules
  [FINDING] The ESP32's WiFi TX burst reflects 388 mA onto the 5 V rail -- more than both HV modules at full load combined (360 mA). G0-A3 chose a network interface with write authority, so this current is real and continuous-duty, not a curiosity. Sizing the supply from the HV modules alone under-sizes it by roughly a factor of two.
  [BLIND SPOT] this section cannot see: inrush at power-on (both module converters and the buck start together; this model is steady-state only); HV converter efficiency versus load, which iseg does not publish; regulator thermal rise; relay coil inrush and back-EMF; and whether the [ISEG] maxima hold across the whole temperature range.

============================================================================================
SECTION 7 -- SET-POINT RESOLUTION
============================================================================================
[ISEG] control version 2: 0 <= Vset <= Vref maps to 0 <= |Vout| <= Vnom.
With a DAC whose reference IS the same 2.5 V the module uses (section 5.6), the
mapping is exact and independent of the reference value:
      LSB_out = Vnom / 2^bits
because the DAC's full scale and the module's full scale become the same node. That
is a design property worth stating: referencing the DAC to Vref removes the reference
from the resolution equation entirely.
Computed INDEPENDENTLY of docs/CONTROL_ARCHITECTURE.md. Disagreement is a finding.

-- 7.1  Volts at the output per LSB, into a 0..2.5 V Vset ----------------------------------
     bits        LSB at Vset  LSB at output        % of Vnom vs +/-1 pct (10 V)
     8           0.009766 V     3.90625 V         0.39062 %         0.3906x
     12          0.000610 V     0.24414 V         0.02441 %         0.0244x
     16          0.000038 V     0.01526 V         0.00153 %         0.0015x

     bits        vs ripple max   vs monitor LSB            verdict
                       (30 mV)       (0.0610 V)
     8               130.2083x         64.0000x  the ESP32's own DAC lives here -- steps visible on a sweep
     12                8.1380x          4.0000x  below the module's accuracy, above the monitor LSB: the sweet spot
     16                0.5086x          0.2500x  below the ripple floor AND below the monitor LSB: unobservable
  [PASS] 12-bit LSB is finer than the module's own +/-1 % adjustment accuracy  --  0.2441 V vs 10.0 V, 41x finer
  [PASS] a 12-bit set-point step is RESOLVABLE in the independent monitor readback  --  set LSB 0.2441 V vs monitor LSB 0.0610 V, 4.0x
  [PASS] a 16-bit set-point step is NOT observable -- below both the monitor LSB and the module's own ripple floor  --  set LSB 0.01526 V vs monitor LSB 0.0610 V and ripple 0.030 V
  [PASS] 8-bit is coarser than 0.1 % of full scale, i.e. insufficient  --  3.9062 V steps vs a 1.000 V target

-- 7.2  The bottom of the range is UNSPECIFIED, and the DAC must know it -------------------
     [ISEG] guarantees ripple/noise only for 2 % * Vnom < Vout <= Vnom, i.e. above
     20 V. On a 12-bit path that is codes 0 .. 81 -- 82 of 4096 codes, 2.0 % of
     the command space -- addressing an output region iseg DOES NOT SPECIFY.
     This is not 'slightly worse performance at low output'. It is 'no guarantee'.
     Consequences that belong in the protocol and the firmware, not in a footnote:
       * the host must be able to command 0 (fully off) and anything >= 20 V,
         and a request in between must return an explicit WARNING, not a silent clamp
         and not a silent acceptance (DECISIONS REF-05: no silent clamping, ever);
       * the monitor-disagreement trip and the discharge self-test both operate in
         this band and must not treat unspecified behaviour as a fault;
       * every accuracy number in this document is quoted at full scale and NONE of
         them is claimed below 20 V.
  [PASS] the unspecified band is a real, bounded region of the 12-bit command space  --  82 of 4096 codes (0 .. 20 V)

-- 7.3  RECOMMENDATION ---------------------------------------------------------------------
     12-bit set path, 16-bit monitor path. TWO of each in mode 2 -- two DACs and two
     monitor channels, since both outputs are independently commanded and measured.
     The monitor must be FINER than the set path so a set-point step is resolvable in
     readback: 0.2441 V set LSB against 0.0610 V monitor LSB satisfies that by 4x.
     16-bit setting buys resolution below the module's own ripple; 8-bit -- including
     the ESP32's internal DAC -- gives 3.91 V steps at 1000 V.
  [BLIND SPOT] this section cannot see: DAC INL and DNL (LSB size is not accuracy); the module's own 50 ppm/K tempco, which at 1000 V is 0.050 V/K and swamps a 16-bit LSB after 0.31 K; and VSET settling time, which iseg does not publish and which is MEASURABLE NOW.

============================================================================================
SECTION 8 -- OTHER CLASSES, KEPT ONLY WHERE THE COMPARISON IS INFORMATIVE
============================================================================================
The part is FROZEN at AP010504. Nothing here is a design option. These three comparisons
are kept because each explains WHY a number above is what it is; every other
parameterisation from session 1 has been deleted as noise.

-- 8.1  Clearance across the 0.5 W range -- what the 1 kV choice costs in board ------------
     NOTE THE COLUMN LABEL. It is MODULE Vnom, not 'FS'. Session 1 never disambiguated
     module nominal voltage from OUTPUT full scale, and under the (now rejected)
     series-stack topology the two differed by 2x. On the frozen design they are equal
     -- one module drives the output at a time -- but the label must say which.

     module Vnom   HV<->GND (mm)         span V HV+<->HV- (mm)     corridor
     200                     2.0            400            4.0         5.0 mm
     400                     4.0            800            6.0         9.0 mm
     600                     4.5           1200            9.0        10.0 mm
     800                     6.0           1600           12.0        13.0 mm
     1000                    7.5           2000           15.0        16.0 mm   <- FROZEN

     The 1 kV class costs 16.0 mm of guarded corridor against 5.0 mm at 200 V --
     3.2x. That is the price of the part the human owns, and it is paid in exactly
     one region of the board.

-- 8.2  Monitor loading -- why 1 kV / 0.5 mA is the binding class --------------------------
     Hold the divider at 1.00 % of Inom at every class and watch Rt:

     module Vnom   Inom (mA)     1 % (uA)    Rt (Mohm)  leak err @10G      vs VMON
     200                2.50        25.00          8.0         0.160 V           ok
     400                1.20        12.00         33.3         1.333 V           ok
     600                0.80         8.00         75.0         4.500 V           ok
     800                0.60         6.00        133.3        10.667 V        WORSE
     1000               0.50         5.00        200.0        20.000 V        WORSE

     Rt grows 25x from the 200 V class to the 1 kV class, because Vnom rises 5x
     while Inom falls 5x. The unguarded surface-leakage error therefore grows as the
     SQUARE of the class, and it crosses the module's own VMON accuracy at 800, 1000 V.
     THIS is why section 4.4 makes the guard ring a requirement: at a lower class the
     same design would have been merely untidy.
  [PASS] the frozen 1 kV class is one where unguarded divider leakage beats VMON, which is what makes the guard ring mandatory rather than optional  --  classes where unguarded leakage exceeds VMON: 800, 1000 V

-- 8.3  The 1 W / 12 V family -- kept ONLY to show the hazard is family-specific -----------
     The 1 W family runs Vref = 5.0 V. A 3.3 V rail on VSET would then command
     3.3/5.0 = 66 % of Vnom -- UNDER full scale, not over. The entire section-5
     over-voltage hazard is an artefact of a 2.5 V reference sitting below a 3.3 V
     logic rail.

     *** THAT FAMILY IS NOT AVAILABLE. *** The human owns AP010504P05 and AP010504N05.
     This is recorded so that nobody re-derives 'we should have bought the 1 W part'
     as though it were an open decision, and so that the clamp is understood as
     compensating for a fixed property of the hardware in hand rather than as a
     precaution someone could trade away.
  [PASS] the 3.3 V VSET hazard exists for the owned 2.5 V-Vref part and would not for a 5 V-Vref part -- i.e. it is a property of THIS part, not of the architecture  --  132 % of Vnom on the owned part vs 66 % on the 1 W family

============================================================================================
DISCREPANCY REGISTER -- flagged, deliberately NOT resolved
============================================================================================
D-1  [ISEG] Table 1 specifies 'Current monitor accuracy 1 % * Inom', but Table 4
     lists only seven pins and NO current-monitor pin:
       1 +VIN | 2 VSET | 3 GND | 4 /ON | 5 VMON | 6 HV | 7 GND
     Either the spec is inherited boilerplate from a larger iseg family, or there
     is an undocumented output. DO NOT design a current readback against it.
     Action: ask iseg. NOW MEASURABLE: the modules are in hand, so the seven pins
     can be probed directly and the question answered on the bench.

D-2  IPC-2221 column labelling: the task brief's description of column B4 matches
     column B1's formula. See section 1.2. Unresolved; needs a primary copy.

D-3  [ISEG] gives no output capacitance, no output impedance, no internal bleeder,
     no VSET step response and no turn-on time. Sections 3 and 7 rest on
     assumptions for all five. ALL FIVE ARE NOW MEASURABLE -- see the
     MEASURABLE-NOW register below.

D-4  Dimensional: the datasheet spec table rounds the body to 40/16/11 mm while
     Figure 1 dimensions it 39.6/15.7/11 mm. Use Figure 1. The footprint study
     owns this and has resolved it; recorded here for completeness.

D-5  MODULE_CASE <-> internal HV: iseg publishes NO dielectric withstand or
     isolation rating between the HV pin and the grounded case, and section 1.7
     measures the internal spacing at a fraction of what this design demands on
     the board. The row is UNRATABLE by any board standard. Ask iseg. Until
     answered, no session may substitute a board-standard number for it.

D-6  The clearance/creepage constants are [unverified-primary] and session 1's
     internal evidence for them was proved circular (section 1.5). Section 1.6
     shows the two candidate readings give DIFFERENT board tiers, so this is a
     blocking item for layout, not for fab.

============================================================================================
MEASURABLE-NOW REGISTER -- the modules are in hand (G0-A2 consequence 4)
============================================================================================
Everything session 1 listed as 'unmeasurable, assumed' is now a bench afternoon.
Each entry names the quantity, the assumed value in use, and how to measure it.

  M-1  Module internal output capacitance (assumed 100 pF). Measure with an LCR meter on the HV pin of an UNPOWERED, BLED module, or by timing the decay against a known bleed resistor. The second method also yields the internal bleeder resistance, which iseg also does not publish.
  M-2  Module internal bleeder resistance (unpublished). Charge the output, disable, and time the open-circuit decay with an HV-rated 1000:1 probe of KNOWN input impedance; subtract the probe.
  M-3  VSET step response / settling time (unpublished). Step VSET 10 % -> 90 % and watch VMON on a scope. This sets the changeover dead-band budget and the state machine's DISCHARGE timeout.
  M-4  Turn-on time from +VIN (unpublished). Time from +VIN valid to VMON settled with /ON already asserted. This sets the power-on sequencing requirement.

  M-5  Pin positions and body dimensions: CALIPER-MEASURABLE. The footprint has
       survived three adversarial skeptics against the VENDOR ARTWORK, which is
       not the same as against a module. Measure one.
  M-6  The D-1 current-monitor question: probe all seven pins on a live module.

  SAFETY NOTE ON ALL OF THE ABOVE: these measurements energise a 1000 V source.
  They are Phase-7-class work, human-present, with an HV-rated probe and a
  grounding stick. Several (output capacitance, internal bleeder) can be done
  UNPOWERED and should be done that way first.

============================================================================================
ASSUMPTIONS LOGGED (each needs G1 confirmation)
============================================================================================
  A-1  Board stray output capacitance 20 pF.
  A-2  SHV lead capacitance 100 pF/m.
  A-3  Touch-safe target: discharge to 60 V DC within 5 s of disable.
  A-4  Bleed permanent-load budget: <= 10 % of Inom.
  A-5  Monitor ADC is an ADS1115-class 16-bit device at +/-2.048 V FS.
  A-6  Temperature excursion about the calibration point: +/-20 K.
  A-7  Divider element VCR 1 ppm/V and top/bottom TCR tracking 10 ppm/K.
  A-8  ESP32 peak 500 mA / TX-average 240 mA / idle 80 mA.
  A-9  Analog rail 60 mA; 4 relay coils at 20 mA; buck efficiency 85 %.

============================================================================================
SOURCES
============================================================================================
  [ARCH12]
      docs/DECISIONS.md ARCH-12, itself [verified-artifact] from the Yageo RC-series datasheet PDF extracted locally: max working voltage 0805/150 V, 1206/200 V, 2010/200 V, 2512/200 V; the +/-1 % range stops at 2.2 Mohm.
  [ASSUMED]
      Engineering assumption made by this probe.
      Listed in ASSUMPTIONS.
  [ENERGY]
      Hazardous stored-energy thresholds 350 mJ and 50 uC (IEC 62368-1 electrical energy source classification / IEC 61010-1).
      [recalled -- confirm before Phase 7].
  [FOOTPRINT]
      SMD chip-resistor pad geometry measured at runtime from the KiCad 10.0 stock library Resistor_SMD.pretty.
      gap = 2*(pad_cx - pad_w/2); extent = 2*(pad_cx + pad_w/2).
      [verified-artifact].
  [G0]
      Human answers to docs/G0_QUESTIONS.md, signed off 2026-07-23.
      Part identity, dual-mode requirement, comms authority.
      [frozen].
  [IEC]
      IEC 62368-1 / IEC 60664-1 creepage, pollution degree 2, basic insulation.
      [unverified-primary] -- same status as IPC2221, same single secondary source.
      The 'printed boards' column is additionally SUSPECTED MIS-TRANSCRIBED (section 1.5).
      Values above 1000 V are OUR OWN LINEAR EXTRAPOLATION, not a quotation.
  [IPC2221]
      IPC-2221 / IPC-2221B Table 6-1 'Electrical Conductor Spacing'.
      [unverified-primary] -- the primary standard is PAYWALLED and has NOT been read.
      The values here came off secondary web reproductions in session 1, and the two 'independent' reproductions were later shown to be the same page.
      NO INTERNAL EVIDENCE SUPPORTS THIS TRANSCRIPTION.
      A human must read a primary copy before G1.
  [ISEG]
      iseg APS series technical documentation v2.5, last changed 2024-08-20 (references/iseg_manual_APS_en.pdf).
      Table 1 p.7 (specifications), Table 2 p.8 (configurations), Table 3 p.8 (item code), Table 4 p.9 (pins).
      [verified-artifact: text extracted with PyMuPDF in session 1, re-read by 3 skeptics].
  [ISEGFP]
      This project's own module footprint hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod, parsed at runtime.
      Pin map and body offset survived 3 adversarial skeptics (STATUS.md 1.1).
      [verified-artifact].
  [KICAD]
      KiCad 10.0 net_settings.classes field set, measured at runtime from a project file KiCad itself wrote: hardware/phase0_env_proof/env_proof.kicad_pro.
      [verified-artifact].
  [TOUCH]
      Touch-safe DC threshold 60 V DC: the accessible-part limit used by IEC 61010-1 and the ES1 d.c.
      voltage limit of IEC 62368-1.
      [recalled -- confirm clause numbers against the standard before Phase 7].

============================================================================================
FINDINGS
============================================================================================
  F-1  The 'independent cross-check between two standards families' in session 1's NUMBERS_PROBE.md section 1.5 is an ALGEBRAIC TAUTOLOGY and has been DELETED, not repaired. Above 500 V both expressions reduce to 0.005*V identically, so its four assertions could not fail for any input; and the check is invariant under any common rescaling of both columns, which is precisely the failure mode implied by both columns having come off one web page. NO REPLACEMENT CROSS-CHECK HAS BEEN INVENTED. The clearance constants are [unverified-primary] and stay that way until a human reads a primary copy of the standard.
  F-2  The IEC PD2 'printed boards' creepage column transcribed in this probe is numerically identical to the 'material group I' column at 2 of 3 anchors, the signature of reading the wrong column. FLAGGED, NOT CORRECTED -- no guess has been substituted. Consequence is bounded today because IEC_pcb never exceeds IPC B2 at 1000 or 2000 V and therefore never governs; a human reading the primary copy must confirm that remains true.
  F-3  hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod carries a per-pad local clearance override of 5.00 mm on pad 6 (HV). A KiCad pad-level clearance REPLACES the netclass clearance, so with the netclass at 7.5 mm the most critical pad on the board is silently checked at 5.00 mm -- the bare IPC B2 value with the 1.5x design margin dropped. FIX THE GENERATOR gen_lib_footprints.py (its CREEPAGE_MM constant) and regenerate; do not hand-edit the artifact. Deliberately NOT fixed by this probe.
  F-4  G0-A4 adds a SECOND pairwise DRC rule that did not exist in session 1: HV_OUT_A <-> HV_OUT_B must also hold 15.0 mm, because in dual-unipolar mode the two OUTPUT nets are simultaneously live at opposite polarity. Ruling only the HV_POS<->HV_NEG module pair leaves every net downstream of the changeover relay silently spaced for 7.5 mm instead of 15.0 mm.
  F-5  Bleed/divider part '1206 HV series' is REJECTED at 1000 V: a working-voltage rating high enough to need only N=3 elements puts 333 V across a package whose own pad-to-pad gap is 1.925 mm, below the 2.500 mm IPC-2221 B2 clearance that voltage demands.
  F-6  Session 1's probe rated a standard 2512 chip resistor at 500 V working voltage. DECISIONS ARCH-12, which is [verified-artifact] from the actual Yageo RC datasheet, says 200 V -- and that upsizing 1206->2010->2512 buys power, not volts. The corrected rating changes the standard-part series count at 1000 V from N=4 to N=10. This probe uses the verified number; the two documents disagreed and the datasheet wins.
  F-7  At 1000 V this instrument is a SUSTAINED-SOURCE shock hazard and a STORED-ENERGY startle hazard. Worst credible stored energy is 5.560 mJ against the 350 mJ threshold (63x below) and 11.12 uC against 50 uC; the sustained 0.75 mA at up to 1000 V -- from BOTH outputs simultaneously in mode 2 -- is the thing that hurts. Design limit: total output capacitance < 50 nF per output, i.e. no bulk HV filter capacitor.
  F-8  Surface leakage is the dominant, non-obvious error term of the independent monitor at this class. With Rt = 200 Mohm forced by the 1.00 %-of-Inom loading budget, a 10 Gohm board leakage path injects 20.0 V of ratio error -- on its own larger than the 10.0 V VMON accuracy the divider exists to improve on. A DRIVEN GUARD RING AT TAP POTENTIAL IS THEREFORE A REQUIREMENT OF THE MONITOR, not a refinement, and it must be in the netclass/DRC rules and in the generator's invariants.
  F-9  The VSET clamp is a necessary but NOT SUFFICIENT safety element. The best candidate (RRIO buffer powered from the precision reference) still passes 2 of 7 modelled single faults, including a reference-to-5 V short that reaches 201 % of Vnom = 2012 V -- worse than the un-clamped 3.3 V case, because the fault is in the clamp's own reference. The independent VMON comparator, on its OWN reference and driving /ON in hardware, is what closes the set, and +VIN removal is the primary disable. With a network carrying write authority (G0-A3) this chain IS the safety case.
  F-10 The ESP32's WiFi TX burst reflects 388 mA onto the 5 V rail -- more than both HV modules at full load combined (360 mA). G0-A3 chose a network interface with write authority, so this current is real and continuous-duty, not a curiosity. Sizing the supply from the HV modules alone under-sizes it by roughly a factor of two.

============================================================================================
VERDICT
============================================================================================
  assertions evaluated : 74
  passed               : 74
  FAILED               : 0

  What this probe structurally CANNOT see, taken as a whole:
    * it is arithmetic on datasheet numbers. Nothing has been measured, nothing
      simulated, no component selected by MPN, no MPN checked against a live
      distributor page -- and the modules that ARE in hand have not been touched;
    * BOTH standards it leans on are [unverified-primary]. Session 1's internal
      evidence for them was an algebraic tautology (section 1.5) and has been
      deleted rather than replaced. There is currently NO evidence that the
      clearance constants are the right constants;
    * it assumes the module behaves as specified across its whole range, and
      [ISEG] explicitly does NOT specify behaviour below 20 V of output;
    * it says nothing about whether the mode-position sense path is trustworthy,
      which is the central new safety question G0-A4 opened;
    * it cannot see per-pad clearance overrides applied elsewhere in the design,
      only the one it happened to read in section 1.7;
    * exit code 0 here means 'every arithmetic assertion holds', which is a much
      weaker claim than 'the design is safe'.
```

---

## What is NOT in this file, and where it went

This document is **generated**, so it can only contain what the probe **prints**. Session 1's
version also carried hand-written engineering prose that no tool can assert — the SHV connector
recommendation, the enclosure and touch-safety requirements, the labelling set, and the DRAFT
Phase-7 bench energization procedure. That material now lives in **`docs/HV_SAFETY_ENVELOPE.md`**,
which is **hand-written and must not be regenerated**, and which quotes its numbers from this
file section by section.

**The split is the point:** arithmetic a tool can assert lives here; judgement a tool cannot
assert lives there. If the two disagree, this file is right about the *numbers* and that file is
right about the *reasoning* — and the disagreement itself is a finding.

---

## What is still open after this run

These are carried forward **flagged**, not closed. No session may close them by re-deriving
them; each needs a document or a bench that this probe does not have.

| open item | why it is still open | who closes it |
|---|---|---|
| **Clearance/creepage constants** | `[unverified-primary]`. Both standards are paywalled; the two "independent" secondary sources were one web page; session 1's internal cross-check was a tautology and is deleted. §1.6 shows the two candidate readings give **different fab tiers**. | a human, reading a primary copy of IPC-2221B Table 6-1 and IEC 60664-1/62368-1, **before G1** |
| **IEC printed-board column** | Numerically identical to the material-group-I column at 2 of 3 anchors — the signature of reading the wrong column. **Flagged, not guessed at.** A tripwire assertion fires if anyone corrects the table without updating this document. | same human, same primary copy |
| **60 V / 350 mJ / 50 µC thresholds** | `[recalled]`. The whole Phase-7 touch-safety argument rests on them and the clause numbers have never been checked. | a human, before Phase 7 |
| **Module output capacitance** | iseg does not publish it. §3 assumes 100 pF. **MEASURABLE NOW** — the modules are in hand (M-1). | a bench afternoon |
| **Module internal bleeder** | Unpublished. **MEASURABLE NOW** (M-2). | a bench afternoon |
| **VSET step response** | Unpublished. Sets the changeover dead-band and the state-machine DISCHARGE timeout. **MEASURABLE NOW** (M-3). | a bench afternoon |
| **Turn-on time from +VIN** | Unpublished. Sets the power-on sequencing requirement. **MEASURABLE NOW** (M-4). | a bench afternoon |
| **D-1 current-monitor pin** | Table 1 specifies a current-monitor accuracy; Table 4 lists no such pin. **Do not design a current readback against it.** **MEASURABLE NOW** (M-6). | ask iseg, or probe the seven pins |
| **D-5 HV-pin-to-case withstand** | iseg publishes no isolation rating between the HV pin and the grounded case. The `MODULE_CASE ↔ GND` row is **UNRATABLE by any board standard** and no session may substitute one. | ask iseg |
| **Every MPN** | `[unverified-MPN]`. Not one part number in this document has been checked against a live distributor page. | Phase 6 |

## Single-source rule for clearance numbers

`STATUS.md` §1.2 finding 7 recorded that **four documents in this repository carried four
mutually incompatible IPC-2221 numbers**, three of them more permissive than the probe's. That is
resolved by making this file the **only** live source:

- The five `docs/topology/*.md` candidate studies are **historical** (G0-A1 selected HV relay
  changeover). Each now carries a banner naming its own wrong figure and how permissive it was,
  rather than being edited line by line — they are the evidence behind a decision, not designs.
- `docs/INTERFACES.md` carries the netclass and `.kicad_dru` values and points here.
- `docs/REFERENCE_BOARD_AUDIT.md`'s 171–250 V values agree exactly with §1.1 of this run; that
  agreement is reconciliation, **not** independent evidence, and is labelled as such.

**Working values at the frozen part, all `[unverified-primary]`:** **7.5 mm** HV-to-anything,
**15.0 mm** `HV_POS`↔`HV_NEG` *and* `HV_OUT_A`↔`HV_OUT_B`, **16.0 mm** guarded corridor,
**≥ 78.4 × 91.7 mm** board.
