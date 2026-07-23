# HV_SAFETY_ENVELOPE — connector, enclosure, labelling, and the Phase-7 bench procedure

> **This file is HAND-WRITTEN. It is not generated and must not be regenerated.**
> Its sibling `docs/NUMBERS_PROBE.md` **is** generated, from
> `hardware/hvctl/numbers_probe.py`. The split is deliberate: **arithmetic that a tool can
> assert belongs in the probe; engineering judgement that a tool cannot assert belongs here.**
> Every *number* quoted below is taken from the probe's generated output and is marked with
> the section it came from — if the probe's number moves, this file is wrong until updated.

**Provenance, stated plainly.** Sections 1–4 of this file were **Part B of session 1's
`docs/NUMBERS_PROBE.md`**. When session 2 re-pinned the probe to the frozen part and made the
document generated-from-the-run, this prose had no generated source and would have been silently
deleted. It was recovered verbatim from the pre-overwrite file and is preserved here, **amended
for G0**. Amendments are marked **⬛ G0**. Nothing was invented in the move.

**Status: pre-G1 DRAFT reviewed by nobody.** Two of its own prerequisites (§4, items P1/P2) are
the unverified standards constants that `STATUS.md` §1.2 refuses to freeze.

---

## 1. HV output connector — recommendation: **SHV**

| | SHV | MHV | LEMO (HV series) |
|---|---|---|---|
| DC rating | 5 kV DC typical, single connector `[verified-web]` | up to 5 kV DC `[verified-web]` | series-dependent; HV series to ~20 kV `[recalled]` |
| AC rating | ~3.5 kV `[verified-web]` | — | — |
| mates with BNC? | **No** — protruding insulator and reversed gender prevent it `[verified-web]` | **Yes, mechanically** — this is the problem `[verified-web]` | No |
| live pin touchable when unmated? | No — recessed/protruding-insulator geometry `[verified-web]` | **Yes** — the male pin is exposed `[verified-web]` | No |
| break order on disconnect | HV contact breaks **before** ground `[verified-web]` | not specified | varies |
| detector-physics default | **yes** | legacy | no |

**Recommendation: SHV, unconditionally.** Three reasons, in order of weight:

1. **It cannot be mated into a BNC.** MHV shares BNC's bayonet geometry closely enough that an
   MHV plug can be forced onto a BNC jack — putting kilovolts onto a signal cable someone will
   later pick up. SHV's reversed gender and protruding insulator make that mechanically
   impossible. This is a *design-for-error* property, not a rating, and it is why SHV exists.
2. **The live conductor is not touchable when unmated**, and the HV contact opens before the
   ground contact on disconnect. Both matter on a bench where the cable gets unplugged with the
   supply live by someone who assumed it was off.
3. **It is the detector-physics default.** Every PMT base, drift chamber and NIM HV distribution
   box in the building already speaks SHV. Choosing anything else guarantees an adapter, and an
   adapter is the thing that ends up unmated and live.

**Margin:** 5 kV rating against a 1000 V maximum output is **5×**. Even under the conservative
material-group-IIIa reading of the board clearances, the connector is nowhere near binding.

**Do not use MHV.** It is deprecated for exactly the BNC-mating hazard above. A legacy instrument
in the lab having MHV is a reason for a clearly-labelled adapter *cable*, not a reason to fit MHV.

**LEMO** is rejected on availability and ecosystem, not capability. If enclosure volume ever
becomes binding this is the fallback — it would need a live-distributor check at Phase 6.

> ### ⬛ G0-A4 — there are now **TWO** output connectors, not one
>
> In dual-unipolar mode `OUT_A` carries **+1000 V** and `OUT_B` carries **−1000 V**
> **simultaneously**, as normal operation. Consequences, all from `NUMBERS_PROBE.md` §1.6:
>
> - **Panel spacing is the SINGLE-ENDED requirement per connector (7.5 mm class), not the
>   15.0 mm span** — because an SHV bulkhead's **shell is at chassis ground** (`[ISEG]` Table 4:
>   *"Case is connected to GND"*), so shell-to-shell is 0 V and each centre conductor sees
>   1000 V to *its own* shell. **The grounded shells are the guard ring, for free.** IPC-2221
>   does not rate panel air gaps at all — it is a PCB standard.
> - **The board-side wiring from each output net to its bulkhead DOES carry the full 2000 V**
>   differential and stays inside the 15.0 mm corridor rule like any other HV copper.
> - **Two separate HV leads, routed apart. Never in one bundle, never in one sleeve.**
> - The two connectors must be **unambiguously labelled per mode** — see §3.

**Mechanical note for Phase 4.** Prefer a **panel-mount SHV bulkhead** wired to the board with a
short HV lead over a board-mount SHV. A board-mount connector puts the full mechanical load of
cable insertion into the PCB and drags the HV keep-out through the board edge. Either way the MPN
and its rating must be re-verified against a live distributor page at Phase 6 —
**`[unverified-MPN]`**; both prior board projects found provisional part numbers that were
obsolete, wrong-package, or fictional.

**The `/ON` and set-point interface must not use an HV-looking connector.** Keep the control
interface on something visually and mechanically distinct (a keyed 0.1″ header or a JST
connector), so no one ever plugs the HV lead into the control header or vice versa.

---

## 2. Touch safety and enclosure

**Classification.** The output is 1000 V, far above 60 V DC, so it is a hazardous *voltage*
source and must be inaccessible. `NUMBERS_PROBE.md` §3.6 sharpens this into a specific answer:

- **Stored energy is a STARTLE hazard, not a shock hazard.** Worst credible stored energy is
  **5.56 mJ against the 350 mJ threshold (63× below)** and **11.12 µC against 50 µC** (§3.6).
  The **charge** criterion binds first, and it does so at **50 nF**.
  **Design limit: keep total output capacitance below 50 nF *per output*.** Concretely, **do not
  fit a bulk HV filter capacitor** — `[ISEG]` already delivers <30 mVp-p ripple above 20 V, and a
  filter cap would buy a little ripple and sell the stored-energy classification.
- **The sustained source IS the shock hazard.** `[ISEG]` limits Iout to ≈1.5·Inom =
  **0.75 mA**, available continuously at up to 1000 V — and **⬛ G0-A4: from BOTH outputs at once
  in dual-unipolar mode.** 0.75 mA DC is above the let-go threshold for a hand-to-hand path. The
  current limit reduces the *consequence* of contact; it does **not** make contact acceptable and
  it is **not** an alternative to an enclosure.
- **⬛ G0-A4 bridging case.** A person or dropped tool bridging `OUT_A` to `OUT_B` sees **2000 V**
  across the series combination of the two output capacitances. Energy **doubles**, charge is
  unchanged, and both stay below threshold (§3.6) — but the *voltage* doubles, and that is the
  term that matters for the shock path.

### Enclosure requirements

1. **Fully enclosed metal chassis, bonded to protective earth.** `[ISEG]` Table 4: *"Case is
   connected to GND"* — the module cases, board GND and chassis are **one node**, and that node
   must be **earthed, not floating**. The module case is a **touchable grounded conductor**;
   this is why the chassis bond is a safety requirement and not an EMC nicety
   (`NUMBERS_PROBE.md` §1.7).
2. **No user-accessible opening reaches HV copper.** Both module HV pins, the changeover relay,
   the four bleed strings, both divider top legs and both output connectors' rears are inside the
   chassis. Only the SHV bulkheads' mated faces are outside.
3. **Tool-required access.** The lid is screwed, not latched. Captive-screw lid is the minimum bar.
4. **A lid interlock is *recommended but not sufficient*.** If fitted it must break `/ON` in
   **hardware** (drive it HIGH), not signal firmware. **Given `[ISEG]`'s `/ON` polarity, a lid
   switch that *opens* on lid-removal is exactly wrong** — the pin floats and HV comes **ON**. It
   must *close* a path that pulls `/ON` HIGH. Better still, it should break **+VIN**, which is the
   primary disable (`DECISIONS.md` ARCH-19): a module with no input power cannot make HV at all.
5. **Ventilation.** `[ISEG]` operating range is 0–40 °C ambient, 120 °C maximum case temperature.
   Worst-case board input power is **4.44 W** (`NUMBERS_PROBE.md` §6.2), essentially all of it
   heat. In a sealed box that needs convection slots — **baffled or louvred so they do not
   compromise item 2** — or a chassis large enough to sink it. Compute properly at Phase 4.
6. **Bleed indication.** A neon or high-value-resistor-fed LED across **each** output, inside the
   chassis and visible through a window, lit whenever HV is present. It is the only pre-touch
   indication that does not depend on firmware being alive. **⬛ G0-A4: one per output.**

### The two pin facts that invert the usual assumption

> **`/ON` is *"LOW or n.c. → HV ON"*.** An **un-driven `/ON` pin turns the module ON.** Every
> `/ON` net needs a hard pull-up **to the module's own +VIN** (ARCH-17), within 5 mm of pin 4,
> and the interlock must be arranged so that **losing the logic rail turns HV OFF**.

> **An open `VSET` node commands FULL SCALE**, because of the internal 10 kΩ pull-up to Vref. A
> broken track, a lifted pad, a dead op-amp with a high-Z output, or an unpowered driver all
> command Vnom. Mitigated by **two 1 kΩ pull-downs in parallel (= 500 Ω)** at VSET → **4.8 %** of
> Vnom instead of 101 % (`NUMBERS_PROBE.md` §5.1). **Duplicated on purpose**: with the pair fitted,
> **one element going open degrades that only to 9.2 %** — still safe, and that is the whole point.
> A *single, un-duplicated* pull-down going open would silently restore the documented unsafe
> default, and an open pull-down is not observable from anywhere else on the board.
> **Quote both numbers; neither alone is the answer.**

**Together: the module's un-driven default state is ENERGISED AT OVER-RANGE.** "Unpowered = safe"
is **false** for this part. That is the single highest-consequence fact in the datasheet.

> ### ⬛ G0-A5 — the mode switch is a physical part of the safety envelope
>
> Mode selection is a **physical switch or link block**, never a relay and never a software bit.
> Enclosure-level requirements that follow:
> - **A guard or cover over the mode selector**, and a panel legend stating that mode change is a
>   **powered-down, cables-off** operation.
> - The selector's **auxiliary LV contacts must BREAK BEFORE the HV poles MAKE**, so the interlock
>   has already commanded both modules off before any HV re-routing occurs. If a switch that does
>   not meet that timing is fitted, the worst case is a **current-limited polarity fight at
>   0.75 mA**, not an energetic fault — stated honestly rather than overstated, but designed for
>   anyway.
> - **Illegal/intermediate positions** (between detents) must read as *neither* valid mode and
>   must force HV OFF.
> - Firmware reads the mode **at boot and continuously**; a mode change detected at runtime forces
>   **HV OFF immediately**, never a graceful transition.
> - **`[unverified-MPN]`** — no HV-rated rotary/wafer switch or link block has been selected. The
>   requirement is "a physical thing the operator moves", not specifically a toggle switch; if a
>   link block or a re-plugged HV cable is better engineering than an expensive panel switch,
>   that is an acceptable answer. **Open at Phase 6.**

---

## 3. Labelling

Minimum set, all permanent (engraved, or printed label under clear overlay — **not marker**):

| location | text |
|---|---|
| chassis exterior, adjacent to **each** SHV connector | `⚠ HIGH VOLTAGE — ±1000 V DC MAX` with the IEC 60417-5036 lightning-bolt-in-triangle symbol |
| chassis exterior, adjacent to **each** SHV connector | `OUTPUT POLARITY IS SWITCHED — CHECK BEFORE CONNECTING` |
| **⬛ at the mode selector** | `MODE: [PSEUDO-BIPOLAR — OUT_A ONLY] / [UNIPOLAR — OUT_A = +, OUT_B = −]` and `CHANGE ONLY WITH POWER OFF AND CABLES REMOVED` |
| **⬛ at OUT_B** | `LIVE IN UNIPOLAR MODE ONLY — DEAD IN PSEUDO-BIPOLAR MODE. VERIFY WITH A METER.` |
| chassis lid, exterior | `⚠ HAZARDOUS VOLTAGE INSIDE — DISCONNECT SUPPLY AND WAIT 5 s BEFORE OPENING` |
| chassis lid, interior | `HV present at marked nodes. Bleed time to <60 V is <0.7 s worst case at the output; the bleed is NOT a substitute for measurement. VERIFY WITH A METER.` |
| PCB silkscreen, around every HV net | hatched keep-out border + `HV` |
| PCB silkscreen, at each module | `MODULE A: POSITIVE (AP010504P05)` / `MODULE B: NEGATIVE (AP010504N05)` |
| PCB silkscreen, at each HV output pad | `HV OUT A` / `HV OUT B` and the maximum voltage |
| rear panel | `5 V / 1.8 A` (`NUMBERS_PROBE.md` §6.2) and an earth-bond symbol |

**The polarity and mode labels are not decoration.** The same terminal carries either sign, and
**which terminal is live differs between modes** — a user who assumes the sign or the terminal
they saw last time is the failure mode this design invites. **⬛ G0-A4 consequence 6.**

---

## 4. DRAFT bench energization procedure — Phase 7

> **This is a DRAFT for review, not an approved procedure.**
> **First energization is human-present. No session ever claims this gate.** (`CLAUDE.md`.)

Bracketed values are from `docs/NUMBERS_PROBE.md` at the frozen part and are
**`[unverified-primary]`** where they derive from the clearance constants.

### Before the day

- [ ] **P0.** Someone other than the board's author has read the schematic and this document.
- [ ] **P1.** A **primary** copy of IPC-2221B Table 6-1 has been checked. **⬛ STILL OPEN** — and
      §1.6 of the probe shows the two candidate readings put the board on **different fab
      tiers**, so this must be resolved **before layout**, not before fab.
- [ ] **P2.** The 60 V DC touch-safe threshold and the 350 mJ / 50 µC energy thresholds have been
      confirmed against the actual standards, not recalled. **⬛ STILL OPEN.**
- [ ] **P3.** A written emergency plan exists: who cuts power, from where, and where the nearest
      person trained in electrical rescue is. **Nobody works alone.**
- [ ] **P4.** An **insulated HV probe / meter rated ≥2 kV DC** is present, battery good. A 600 V
      handheld DMM is **not** adequate. **⬛ In unipolar mode a probe may see 2000 V across the
      two outputs — rate for that, not for 1000 V.**
- [ ] **P5.** A **grounding stick** (high-value resistor in series with an earthed lead on an
      insulated handle) is present. **The bleed resistor is a design feature, not a procedure.**

### Stage 1 — dead board, no modules

- [ ] **1.1** Modules **not** fitted. HV supply **not** connected.
- [ ] **1.2** Visual: HV keep-out regions clear of stray copper, flux, solder balls, silkscreen
      artefacts. Clean with IPA and inspect under magnification. **Flux residue across a
      [7.5] mm gap at 1000 V is a leakage path the probe has no term for** — and
      `NUMBERS_PROBE.md` §4.4 shows surface leakage is already the *dominant* monitor error term.
- [ ] **1.3** DMM, board unpowered: `HV_POS ↔ HV_NEG` open · `HV_POS ↔ GND`, `HV_NEG ↔ GND`,
      `HV_OUT_A ↔ GND`, `HV_OUT_B ↔ GND` each read the bleed value **[20.0 MΩ]**.
      **A short here is the cheapest failure of the day.**
- [ ] **1.4** Calipers at closest approach: `HV_POS ↔ HV_NEG` **≥ [15.0] mm**; **⬛
      `HV_OUT_A ↔ HV_OUT_B` also ≥ [15.0] mm**; every HV net to anything else **≥ [7.5] mm**.
      Record all three.
- [ ] **1.5** Chassis bonded to protective earth: **<0.1 Ω** chassis to earth pin.
- [ ] **1.6** **⬛ Verify the mode selector's contact timing.** With a continuity tester on the
      aux poles and the HV poles, move the selector slowly and confirm the **aux contacts BREAK
      BEFORE the HV contacts MAKE**. Confirm the intermediate position reads as **neither** mode.

### Stage 2 — logic only, modules still not fitted

- [ ] **2.1** Logic supply only. Rails: 3.3 V, 5 V, precision reference at **[2.500] V ±[0.1] %**.
- [ ] **2.2** **Verify `/ON` defaults to HIGH.** ESP32 held in reset, measure both `/ON` nets:
      both >2.5 V and ≤5.5 V. **If either reads LOW or floats, STOP.** This is the condition that
      would turn HV on with no controller running.
- [ ] **2.3** VSET buffer outputs sit at 0 V with the DAC at code 0, and **both** pull-downs are
      fitted — measure **[500] Ω** to GND (two 1 kΩ in parallel) with the buffer unpowered.
      **Measuring 1 kΩ means one of them is missing.**
- [ ] **2.4** **Exercise the hardware interlock with a meter, at logic level, before any HV
      exists.** Command every combination of the two enables and confirm at the module `/ON` pins
      that **both modules connected to the SAME output node is unreachable**. Try to force it.
      **Record the measured truth table.** **⬛ Do this in BOTH mode positions** — the interlock is
      mode-aware, and mode 2 legitimately permits both modules on *different* nodes.
- [ ] **2.5** **Verify the over-voltage comparator trips:** inject **[2.625] V** at the VMON sense
      node with the ESP32 held in reset and confirm `/ON` goes HIGH **in hardware**. Confirm its
      threshold reference is **not** the reference that feeds the DAC (`NUMBERS_PROBE.md` §5.5
      condition 1 — a comparator on that node fails in the same event it exists to catch).
- [ ] **2.6** **⬛ Verify the mode sense is COMBINATIONAL.** With the ESP32 held in reset, move the
      selector and confirm the interlock permissive follows the **aux contacts** immediately, with
      nothing latched and nothing cached.

### Stage 3 — first HV, one module, lowest setting

- [ ] **3.1** Fit **one** module only — the positive one. Negative socket empty.
      **⬛ Selector in PSEUDO-BIPOLAR.**
- [ ] **3.2** Lid on. Nothing connected to either SHV output. Second person present and briefed.
- [ ] **3.3** DAC at code 0 **before** enabling. Confirm VSET = 0 V at the module pin.
- [ ] **3.4** Enable. Read VMON, the independent divider, and the SHV output on the HV probe.
      **All three must agree within [20] V** (the §4.5 trip threshold, 2 % of Vnom). Record all
      three. Note legitimate quadrature disagreement is **[10.007] V**, so a 20 V trip has only
      **2×** margin — do not treat a 12 V spread as nothing.
- [ ] **3.5** Command 10 % of full scale, repeat the three-way comparison, then 25 %, 50 %, 100 %.
      **Stop at the first disagreement.** **⬛ Do NOT characterise below [20] V** — `[ISEG]`
      does not specify the output there, so a discrepancy in that band is not evidence of a fault.
- [ ] **3.6** **Disable and time the discharge.** HV probe on the output, disable, measure time to
      fall below 60 V. Expected **[<0.018] s** with a 2 m lead and no load, rising to
      **[<0.63] s** with a 10 m lead and a 10 nF load (§3.3). **The HV probe's own capacitance is
      part of the measurement.** If it takes *seconds*, the bleed is not connected where you think
      it is — and if the fall is instant and the reading then creeps back up, something is
      charging the node.
- [ ] **3.7** **Apply the grounding stick before touching anything, every time, regardless of 3.6.**

### Stage 4 — second module, polarity handoff, and mode change

- [ ] **4.1** Power down, discharge, ground, fit the negative module.
- [ ] **4.2** Repeat Stage 3 for the negative module alone, at negative polarity.
- [ ] **4.3** **The handoff test.** HV probe on `OUT_A`, command +50 % → −50 %. Record: does the
      output pass through a **defined discharged state**? How long? Does either module's HV node
      exceed its own full scale?
- [ ] **4.4** **Try to break the interlock with HV live.** Command both enables simultaneously in
      **pseudo-bipolar** mode. Confirm the output does not exhibit both polarities and no fault
      current flows. **Have the supply current meter in view — a sudden input-current rise is the
      first sign of a fight.**
- [ ] **4.5** **⬛ THE MODE-CHANGE TRANSITION — a first-class transition with its own timeouts.**
      From pseudo-bipolar to unipolar: command both set-points to zero → disable both modules
      (**+VIN removal primary, `/ON` secondary**) → **dwell [2.0] s** (3× the worst-case bleed
      time of [0.626] s) and **VERIFY both outputs below 60 V on the independent monitors — verify,
      do not merely wait** → move the selector **COLD** → **read the selector's physical position
      back before re-enabling anything**. **TRIP on timeout; do not fall through** (ARCH-24: "off"
      is not where a timeout leaves you — a stuck-live node plus a moving contact is).
- [ ] **4.6** **⬛ Dual-unipolar first energization.** Selector in UNIPOLAR. Enable **one** module,
      verify, then the second. With both live, confirm the independent monitors read **`OUT_A`
      POSITIVE and `OUT_B` NEGATIVE**. **A sign disagreement means the selector is not where
      firmware thinks it is** — this is the failure G0-A4 warns about and the independent monitor
      is the only thing on the board that can see it.
- [ ] **4.7** **⬛ Attempt the forbidden mode change.** With both outputs live in unipolar mode,
      move the selector toward pseudo-bipolar. **The aux contacts must command both modules off
      before any HV pole makes.** Watch the supply current. Worst case if the timing is wrong is a
      **current-limited 0.75 mA polarity fight**, not an energetic fault — but it is still a
      welded-contact risk and this is the moment to prove it does not happen.
- [ ] **4.8** **Pull-the-plug test.** At full scale, remove the **logic** supply — confirm HV
      collapses and both outputs discharge. Separately, at full scale, remove the **module**
      supply — confirm the same. **⬛ Do both in both modes.**

### Stage 5 — into a load

- [ ] **5.1** Connect the intended load through an SHV lead. Full sweep, both polarities.
- [ ] **5.2** Compare readback against a DMM at ≥5 points per polarity. Record the residuals —
      this is the acceptance evidence the brief asks for.
- [ ] **5.3** **⬛ Both outputs loaded simultaneously in unipolar mode**, at full scale, for
      30 minutes. Measure module case temperature (well under the 120 °C `[ISEG]` limit),
      **measure the 5 V rail current against the predicted [888] mA** (§6.2), and re-check
      readback agreement — drift here is the tempco and self-heating terms showing up in reality.

### Also do, while the modules are on the bench

The **MEASURABLE-NOW register** (`NUMBERS_PROBE.md`) lists six quantities that session 1 could only
assume and that are now a bench afternoon: **module output capacitance (M-1)**, **internal bleeder
(M-2)**, **VSET step response (M-3)**, **turn-on time from +VIN (M-4)**, **caliper the pin field
(M-5)**, and **the D-1 current-monitor question (M-6)**.
**M-1, M-2 and M-5 can be done UNPOWERED and should be done that way first.**

### After

- [ ] **6.1** Record every measured number against the predicted number.
      **Every place reality disagrees with `NUMBERS_PROBE.md` is a finding**, and belongs in
      `docs/DECISIONS.md` — or, if it is a lesson about the *process*, in `docs/PIPELINE_LOG.md`.
