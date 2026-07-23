# BENCH_MEASUREMENTS — the five things a human must measure on a real module

**Written 2026-07-23 (session 2).** The modules are **in hand** (G0-A2: `AP010504P05` and
`AP010504N05`, both polarities). Every parameter below is tagged **MEASURABLE-NOW** somewhere in
`docs/design/`, which means *"an assumption today, a measurement this afternoon"*.

**Nothing in this repository has ever been measured, energised or touched with an instrument.**
This document is the procedure that changes that. It is written as a checklist to be followed with a
pen, not read as prose.

| # | Parameter | Currently | Tag | Instrument time |
|---|---|---|---|---|
| **M1** | `VSET` step response, settling to 0.1 % | `[recalled]` τ ≈ 100 ms, **inferred from a figure captioned "control principle"** | MEASURABLE-NOW | 30 min |
| **M2** | HV output capacitance `C_module` | `[ASSUMED]` — **1 nF** in `COMBINER_DESIGN`, **100 pF** in `MONITOR_AND_BLEED`. The two live documents disagree by 10× | MEASURABLE-NOW | 30 min (shares a rig with M3) |
| **M3** | Internal bleeder resistance | `[ASSUMED]` ~20 MΩ, existence unknown | MEASURABLE-NOW | 20 min |
| **M4** | Turn-on time from `+VIN` | `[ASSUMED]` 150 ms | MEASURABLE-NOW | 20 min |
| **M5** | **Caliper check of a real module against our footprint** | **never done** — the land pattern was derived entirely from vendor *artwork* | see §7 | 20 min, **no HV** |

> **M5 needs no high voltage, no bench supply and no scope.** If you only have twenty minutes, do M5.
> It retires the single risk this project cannot retire any other way (§7).

---

# PART 0 — SAFETY. THIS SECTION IS NOT OPTIONAL AND NOT SUMMARISABLE.

**This is 1000 V DC on an open bench.** Every number in the rest of this document assumes the
following are already true.

## 0.1 ⛔ THE PROBE. READ THIS BEFORE YOU PLUG ANYTHING IN.

> ## A STANDARD 10× OSCILLOSCOPE PROBE IS RATED ~300–600 V. IT **WILL FAIL** AT 1 kV.
>
> This is not a derating discussion. A common 10× passive probe (Tektronix P2220-class,
> Rigol/Siglent bundled probes) carries a **300 V CAT II** or at best **600 V CAT I** marking on the
> body. Putting 1000 V DC on it is **outside its insulation rating**, not merely outside its
> accuracy spec. The failure is a **flashover across the probe body or the compensation box into
> your hand**, and it is not preceded by a warning.
>
> **AN HV PROBE IS MANDATORY.** Required: a **1000:1 HV probe rated ≥ 5 kV DC**
> (Tektronix P6015A-class, or a 1000:1 / 40 kV divider probe) `[unverified-MPN — check the marking
> on the actual probe in your lab before use]`.
>
> **Check the marking on the probe body itself. Do not trust the drawer it lives in, the label on the
> case, or anyone's memory.** If the probe body does not carry a printed voltage rating ≥ 2 kV,
> **it is the wrong probe and the measurement does not happen today.**

**The same rule applies to the DMM.** A bench DMM's DC-V input is typically 1000 V CAT II — usually
adequate — **but the test leads and the probe tips are the weak point.** Use leads with an explicit
≥1 kV marking, and use the **one-hand rule** (§0.4) regardless.

**Do not measure the HV node with a 10 MΩ DMM directly if you can avoid it.** At 1 kV a 10 MΩ meter
draws 100 µA = **20 % of the module's 0.5 mA Inom**, which perturbs the very thing you are measuring
(and, in M3, is the same order as the parameter you are trying to extract). Use the HV probe, or a
known high-value divider you built and measured yourself.

## 0.2 Pre-flight checklist — tick every box, in order

- [ ] **A second person is present in the room and knows what you are doing.** This is not a
      solo-work task. They must know where the bench power switch is.
- [ ] The HV probe body carries a printed rating **≥ 2 kV**. *Read it. Now.*
- [ ] The HV probe's **ground lead is connected to the module GND (pins 3 and 7) and to the bench
      supply's return**, before the module is powered.
- [ ] A **discharge stick** exists on the bench: a ≥10 MΩ, ≥5 kV-rated resistor on an insulated
      handle with a clip lead to ground. **Not a screwdriver. Not a wire.** A hard short into a
      charged capacitance is how contacts weld and how eyes get hurt.
- [ ] The HV output node and everything galvanically attached to it is **physically inaccessible**
      during energisation — a lid, a box, a barrier. Not "I'll be careful."
- [ ] **No metal on hands or wrists.** Rings, watch, bracelet off.
- [ ] The bench supply feeding `+VIN` has a **hard switch you can reach without leaning over the
      HV node**.
- [ ] `VSET` is at **0 V and confirmed at 0 V with a meter** before `+VIN` is applied.
      **Remember: `VSET` open-circuit commands FULL SCALE** (internal ~10 kΩ pull-up to Vref,
      PART-04, survived 3/3 skeptic passes). An unconnected `VSET` wire is a 1000 V command.
- [ ] `/ON` (pin 4) is **driven high or tied high through ≥2 parallel 10 kΩ to `+VIN`**.
      **`/ON` is ACTIVE-LOW: a floating `/ON` turns HV ON.**
- [ ] You have written down, on paper, **which pin is which**, from `docs/PIN_MAPS.md` §2:
      `1 +VIN · 2 VSET · 3 GND · 4 /ON · 5 VMON · 6 HV · 7 GND`.

> **The module's un-driven default state is ENERGISED AT OVER-RANGE.** Both undriven-input hazards
> point the same way. Wire the safe states *first*, power *second*.

## 0.3 ⚡ DISCHARGE BEFORE TOUCH — every single time

**Between every step, and before any hand goes near the HV node:**

1. `VSET` → 0 V.
2. `/ON` → high (HV off).
3. **Remove `+VIN`** (the primary disable — `+VIN` removal is ARCH-19's primary mechanism, `/ON` is
   secondary).
4. **Wait for the measured decay**, watching the HV probe, until the reading is **< 10 V**.
5. **Then** apply the discharge stick to the HV node for **≥5 s**.
6. **Then** verify **< 10 V with the meter, with your own eyes, on this occasion.** Not "it should
   be down by now."
7. **Then** touch.

**Steps 4–6 are three independent instruments and none is redundant.** The wait can be wrong if the
bleeder is absent (§0.5); the stick can be wrong if a clip has fallen off; the meter can be wrong if
it is on the wrong range.

## 0.4 The one-hand rule

**One hand behind your back, or in your pocket, whenever the HV node is or might be live.** The
lethal path is hand-to-hand across the chest. This costs nothing and is the single highest-value
habit in this document.

Corollary: **set up the probe, the clips and the leads with the module unpowered**, so that no
adjustment is ever needed while energised. If you find yourself reaching in to fix something, power
down first — every time, without exception, including the time it seems obviously unnecessary.

## 0.5 ⛔ WHAT TO DO IF THE INTERNAL BLEEDER TURNS OUT TO BE ABSENT OR VERY LARGE

This is the outcome M3 exists to find, and **it changes the safety procedure for M1, M2 and M4** —
which is why M3 is done **before** them, even though it is the least interesting number.

`PART-24` assumes the module has an internal bleeder of ~20 MΩ. **iseg does not publish one, and it
may not exist.** If it does not:

| M3 result | What it means on the bench | What you must do |
|---|---|---|
| **≈ 20 MΩ** (the assumption) | 1000 V → 10 V in ~0.1 s on a bare module. Charge does not persist. | Proceed. Still follow §0.3 in full. |
| **≥ 1 GΩ, or no measurable path** | The module's own output **holds charge essentially indefinitely.** A bare module you set down at 1000 V is **still at ~1000 V an hour later**, and it looks exactly like a discharged one. | **STOP and change the rig.** ① Fit a **permanent external 20 MΩ / ≥5 kV bleed across the HV node for the whole session** — build it before the first energisation, not after this discovery. ② Add a **"HOT — 1 kV, NO INTERNAL BLEED" tag** physically hung on the module. ③ Extend the §0.3 step-4 wait to the measured τ of *your external* bleed × 5, and never rely on the stick alone. ④ Record it: it makes `MONITOR_AND_BLEED` §7.5's "the bleed alone does not satisfy the discharge invariant" **structurally load-bearing**, not conservative. |
| **≤ 5 MΩ** | The module eats > 40 % of its own Inom internally. | Safer on the bench; **worse for the design** — see M3's design-impact row. |

**Until M3 is done, assume there is NO internal bleeder.** That is the safe assumption in both
directions: it is the conservative bench posture *and* it is the conservative design posture (the
external bleeds in `board_spec.py` were sized **without** crediting it).

## 0.6 Session hygiene

- [ ] Write every reading **on paper, as you take it**, with the date and the module serial number.
      Several of these numbers become **per-module calibration constants** (`SETPOINT_PATH` §2.3):
      *a measurement not tied to a serial number is worthless when the module is replaced.*
- [ ] Photograph each scope trace. "τ looked like about 100 ms" is not a measurement.
- [ ] Measure **both** modules (`P05` and `N05`). Do not assume the negative unit matches the
      positive one; the design already treats `OUT_A` and `OUT_B` as electrically non-interchangeable
      (`COMBINER_DESIGN` §3.1).
- [ ] When done, **write the results into the files named in the "lands in" column of each section
      below, and re-run `numbers_probe.py` and `board_spec.py`.** A measurement that does not reach
      the probe has not been made.

---

# PART 1 — THE RIG

One rig serves M1–M4. Build it once, unpowered, and verify it before the first energisation.

```
   bench PSU 5.0 V ──[SW_VIN, a real toggle you can see]──┬──► pin 1  +VIN
                                                          │
                                                        22 µF   (PART-18: the datasheet
                                                          │      MANDATES a blocking cap)
                                                         GND
   bench DAC / precision source 0…2.5 V ─────[10 Ω]──────► pin 2  VSET
        (or a 10-turn pot from a 2.500 V reference)
        ⚠ NEVER from a 3.3 V or 5 V rail: 3.3 V commands ~1320 V.
        ⚠ NEVER leave open: open = FULL SCALE.
                                                        ► pin 4  /ON   ──[2 × 10 k]──► +VIN
                                                                        (high = OFF)
                                                                        pull LOW to turn HV ON
   DMM #2 (10 MΩ, harmless here) ───────────────────────► pin 5  VMON  (0…2.5 V, LV — safe)
   pins 3 and 7 ───────────────────────────────────────► GND (BOTH pins, separately — PART-16)

   pin 6  HV ──┬── R_load  100 MΩ ±1 %, ≥5 kV, on an insulated standoff ──► GND
               │        (switchable OUT of circuit for the M3 pair-measurement)
               ├── HV PROBE 1000:1, ≥5 kV ──► scope CH1
               └── [external 20 MΩ bleed, MANDATORY if §0.5 says so]
```

**Rig verification, unpowered:**
- [ ] Continuity: pin 6 → `R_load` → GND reads ≈100 MΩ on the DMM.
- [ ] Continuity: pin 4 → 10 kΩ → pin 1 (both resistors present).
- [ ] `VSET` source set to 0.000 V and **measured** at the pin.
- [ ] Probe ground clip on GND, at the module, not on a distant rail.
- [ ] Scope: CH1 DC coupled, 1000:1 attenuation **entered in the channel settings** (a probe set to
      1× in the menu turns 1000 V into an unreadable trace and a wrong number).

**First energisation:** `VSET` = 0, `/ON` high, apply `+VIN`, confirm `VMON` ≈ 0 and the HV probe
reads ≈0. **Only then** pull `/ON` low. Bring `VSET` up to **0.050 V (≈20 V out)** first and confirm
the sign and magnitude on the probe before going anywhere near full scale.

> **Do not operate below 20 V for any measurement that matters.** iseg guarantees ripple/noise only
> for `2 % · Vnom < Vout ≤ Vnom`. Below 20 V the output is **unspecified, not merely worse**
> (PART-10/PART-32). Take every reading in the **200–1000 V** band and extrapolate, rather than
> characterising a region the vendor does not specify.

---

# M3 — INTERNAL BLEEDER RESISTANCE  *(do this FIRST — it sets the safety posture)*

**Why first:** §0.5. Until you know, you must assume the module holds charge forever.

### Setup
Rig of Part 1, with `R_load` **switchable**. Nothing else changes.

### Steps

1. [ ] `R_load` **IN circuit** (100 MΩ ±1 %). Bring the output to **800 V** (`VSET` ≈ 2.000 V).
2. [ ] Let it settle 10 s. Record `V_start` from the HV probe.
3. [ ] **Turn HV off by removing `+VIN`** (`SW_VIN` open) — *not* by ramping `VSET` down, which
       measures the set-node pole instead. Capture the decay on the scope, single-shot, 5 s window.
4. [ ] Fit an exponential. Record **τ_loaded**.
5. [ ] **Discharge per §0.3.** Verify < 10 V. **Then** switch `R_load` **OUT**.
6. [ ] Repeat steps 1–4 with no external load. Record **τ_unloaded**.
7. [ ] Solve the pair simultaneously:
       - `τ_loaded  = C · (R_load ∥ R_int)`
       - `τ_unloaded = C · R_int`
       - ⇒ `R_int = R_load · τ_unloaded / (τ_unloaded − τ_loaded)` and `C = τ_unloaded / R_int`
       **This one pair of traces yields M3 and M2 together.**
8. [ ] Sanity check: `R_int` must be **positive and larger than `R_load`** if `τ_unloaded > τ_loaded`.
       If `τ_unloaded ≈ τ_loaded`, the internal bleeder **dominates** and is ≲ 10 MΩ. If
       `τ_unloaded` is so long you cannot capture it, **the internal bleeder is effectively absent —
       go to §0.5 immediately, before touching anything.**

### Expected range
**20 MΩ to ∞.** The honest prior is *"probably nothing, possibly a few tens of MΩ."* A value below
5 MΩ would be surprising.

### ⛔ What result invalidates a decision already made

| Result | Decision it invalidates | What must change |
|---|---|---|
| **≤ 5 MΩ** | **`MONITOR_AND_BLEED` §8's load budget.** The internal bleeder then consumes **> 40 % of Inom** on its own, on top of the external **11.40 %** published (**12.40 %** once the `BLDX`/`BLDM` stub bleeds the document omits are counted — see that file's correction banner M-1). | §8's own table says: **raise `S1` from 20 MΩ to 40 MΩ**, reclaiming 5.00 %. And **the deliverable output current specification changes and the human must be told** — do not quietly reduce the bleed below 40 MΩ. |
| **≈ 20 MΩ** | Nothing structurally — **but** it takes the summed load to **21.40 % (22.40 % with the stubs)**, which **BREACHES `numbers_probe.py`'s own ≤15 % assertion.** `MONITOR_AND_BLEED` §8 currently calls this *"acceptable — no change"* without noting the breach. | Either the assertion's threshold is re-derived and re-justified, or the bleed values change. **A passing assertion that would fail on the measured value is not a passing assertion.** G1 must adjudicate. |
| **Absent / ≥ 1 GΩ** | Nothing in the design (the external bleeds were sized without crediting it) — **but it invalidates the BENCH procedure**, see §0.5, and it makes every discharge figure in `COMBINER_DESIGN` §5.3 **exact rather than conservative**. | Rewrite §0.5's posture into the Phase-7 energisation procedure as a hard requirement, not a note. |

### Lands in
`docs/design/MONITOR_AND_BLEED.md` §8 (load budget table) and §12.3 **O-M2** ·
`docs/design/COMBINER_DESIGN.md` §5.3 and §11 (row 2) ·
`hardware/hvctl/numbers_probe.py` §3.4 (the ≤15 % assertion) ·
`docs/DECISIONS.md` **PART-24**.

---

# M2 — HV OUTPUT CAPACITANCE

**Falls out of M3's two traces for free** (step 7). Do it as a separate deliberate check anyway,
because **the two live design documents disagree by 10×** and one of them is wrong:
`COMBINER_DESIGN` §5.3/§11 assume **1 nF**; `MONITOR_AND_BLEED` §12.3 O-M1 assumes **100 pF**.

### Setup
As M3. Optionally cross-check with a **second, independent method**: charge to 800 V through a known
series resistance and measure the *rise* τ, or discharge into a known capacitance and use charge
sharing. **Two methods, because a single exponential fit is easy to get wrong by a factor of 2 with
the wrong cursor placement.**

### Steps
1. [ ] Take `C = τ_unloaded / R_int` from M3 step 7.
2. [ ] Independently: with `R_load` = 100 MΩ **in**, `C_measured = τ_loaded / (R_load ∥ R_int)`.
3. [ ] The two must agree to **better than 20 %**. If they do not, the fit is bad — re-take the
       traces with a longer window and the cursors on 1/e, not on "looks about right".
4. [ ] **Subtract the rig.** The HV probe (typically 3 pF), the standoff and 200 mm of wire add
       **tens of pF**. Measure the rig capacitance with the module removed and subtract it.
       *At the 100 pF end of the disagreement, the rig is the same size as the answer.*

### Expected range
**100 pF to 5 nF.** Anything above 10 nF would be extraordinary for a 5 W potted module.

### ⛔ What result invalidates a decision already made

| Result | Decision it invalidates | What must change |
|---|---|---|
| **≈ 100 pF** | Nothing — every timing figure becomes conservative. **But it settles the 10× documentation conflict in favour of `MONITOR_AND_BLEED`**, and `COMBINER_DESIGN` §5.3/§11 must be regenerated, not patched. | Fix the constant in one place and re-run both instruments. |
| **≈ 1 nF** | Nothing. Confirms `COMBINER_DESIGN`'s assumption. | Retag `[ASSUMED]` → `[verified-bench]` and delete the other document's 100 pF. |
| **≥ 10 nF** | **The changeover dead-band.** `COMBINER_DESIGN` §11: closed-node τ becomes 190 ms, T1 becomes **875 ms**, and the nominal dead-band goes to **≈2.0 s** — against G0-A1's *"~1 s"*. **This is a requirements breach, not a tuning issue.** | §11's own answer: **do NOT shrink the bleed** (the load budget has ~2.4 points of headroom). Fit the **switched crowbar** costed and rejected in session 1: one more Form-C relay per node with a 10 kΩ dump (NUM-08, sized against 1.5·Inom — **not** against τ). **Cost +$90 and +18 cm² per node.** Decide after the measurement, never before. **And tell the human that the dead-band is now 2 s.** |
| **> 50 nF** | **`MONITOR_AND_BLEED` §7.4's classification of stored energy as "a startle hazard, not an energy hazard."** | The enclosure requirements escalate (O-M1). Re-run the stored-energy arithmetic against the 350 mJ threshold `[recalled, unverified-primary]` **before** the next energisation. |

### Lands in
`docs/design/COMBINER_DESIGN.md` §5.3, §9.2 (dead-band budget), §11 (row 1) ·
`docs/design/MONITOR_AND_BLEED.md` §7, §12.3 **O-M1** ·
`hardware/hvctl/numbers_probe.py` §3 (discharge) · `docs/DECISIONS.md` **PART-24**.

---

# M4 — TURN-ON TIME FROM `+VIN`

### Setup
Rig of Part 1. Scope **CH1 = HV probe**, **CH2 = `+VIN` at pin 1** (LV, ordinary probe is fine here),
triggered on CH2's rising edge. `VSET` preset to **2.000 V (≈800 V)** *before* `+VIN` is applied,
`/ON` already low.

### Steps
1. [ ] Discharge per §0.3. Confirm the HV node is at 0 V.
2. [ ] Arm the scope single-shot, 2 s window, trigger on CH2 rising.
3. [ ] Close `SW_VIN`. Capture.
4. [ ] Record **t_first-motion**: `+VIN` crossing 4.5 V → HV output first departs 0 V by > 5 V.
5. [ ] Record **t_settled**: `+VIN` rising → output within **0.1 %** of final.
6. [ ] Repeat **3 times**, and repeat with `VSET` = 0.500 V (≈200 V). Record all six.
7. [ ] Repeat with the **other polarity module**.

### Expected range
**50 ms to 500 ms** for first motion. The `[ASSUMED]` value is **150 ms**.

### ⛔ What result invalidates a decision already made

| Result | Decision it invalidates | What must change |
|---|---|---|
| **≤ 150 ms** | Nothing. Confirms the assumption. | Retag. |
| **≈ 500 ms** | The **dead-band budget only.** `COMBINER_DESIGN` §11: dead-band becomes **1.57 s** nominal. | **No hardware change.** Report the real dead-band in the manual and in the `MEAS:` timing. Update `COMBINER_DESIGN` §9.2 step 8 and every timeout derived from it. |
| **Seconds** | **G0-A1 itself.** The human accepted *"~1 s dead-band with the output clamped to ground"*. A multi-second turn-on breaks that acceptance, and **`MONITOR_AND_BLEED` O-M4 states plainly: there is NO design fix — it is the module's own physics.** | **Escalate to the human. Do not paper over it.** The options are (a) accept a longer dead-band in writing, or (b) keep both modules powered and gate only `/ON` — which **changes the primary-disable decision ARCH-19** and must go back through a gate. |

### Lands in
`docs/design/COMBINER_DESIGN.md` §9.2 (step 8 / T7), §11 (row 3) ·
`docs/design/MONITOR_AND_BLEED.md` §7.7, §12.3 **O-M4** · `docs/DECISIONS.md` **PART-25**.

---

# M1 — `VSET` STEP RESPONSE, SETTLING TO 0.1 %

**The weakest-provenance number in the project.** τ ≈ 100 ms was **inferred from a datasheet figure
captioned "control principle"** — an illustrative diagram, not a specification. Every ramp rate,
every timeout and the 300 ms minimum step in `COMBINER_DESIGN` §9.2 scale with it.

### Setup
Rig of Part 1, plus a **clean, fast, bounded step source on `VSET`**:
- A DAC or function generator whose output **cannot exceed 2.500 V** — put a **2.5 V rail-referenced
  buffer or a hard clamp in the path**, exactly as `SETPOINT_PATH.md` specifies for the product.
  ⚠ **A function generator set to 0–3.3 V commands 1320 V.** Set the amplitude, then **verify it at
  the pin with a meter** before connecting to pin 2.
- Scope CH1 = HV probe, CH2 = `VSET` at the pin. Trigger on CH2.

### Steps
1. [ ] Step `VSET` **0.500 V → 2.000 V** (200 V → 800 V). Both endpoints are above the 20 V
       specification floor.
2. [ ] Capture 2 s single-shot. Fit the rise. Record **τ_up**.
3. [ ] Step **2.000 V → 0.500 V**. Record **τ_down**. *They need not be equal* — a module with an
       output bleeder and no active pull-down falls on a different time constant than it rises on.
       **Record both. The design cares about the slower one.**
4. [ ] Measure **t_0.1 %**: time from the step edge until the output stays inside ±0.1 % of final
       (±0.8 V at 800 V). **Use the HV probe's own noise floor as the tie-breaker** — if 0.1 % is
       below your probe's resolution, say so and record the tightest band you can actually resolve.
       *An unresolvable number honestly reported is worth more than a fitted one.*
5. [ ] Repeat with a **small step** (2.000 V → 2.050 V) — large-signal slew and small-signal
       settling are different numbers and §9.2 uses both.
6. [ ] Repeat with `R_load` **out**, to see whether settling is load-dependent.
7. [ ] Repeat on the other module.

### Expected range
**τ = 20 ms to 300 ms.** `t_0.1 %` ≈ **6.9 τ** if it is a single pole — **check that it actually is
one pole.** If the trace has a knee, a plateau or an overshoot, it is not, and **6.9 τ is then the
wrong formula and every timeout derived from it is wrong.**

### ⛔ What result invalidates a decision already made

| Result | Decision it invalidates | What must change |
|---|---|---|
| **τ ≈ 100 ms, single pole** | Nothing. Confirms the inference. | Retag `[recalled]` → `[verified-bench]` in `COMBINER_DESIGN` §9.2, `SETPOINT_PATH` §6, `numbers_probe.py`. |
| **τ ≫ 100 ms** | **Every timeout in `COMBINER_DESIGN` §9.2** and the **300 ms minimum ramp step**. `\|MEAS − target\|` becomes meaningless if you step faster than the node settles, so the ramp-timeout formula `\|Δ\|/slew + 3 s` under-allows. | Rescale every §9.2 timeout by the measured ratio and re-run the dead-band budget. **Firmware change, not hardware.** |
| **τ ≪ 100 ms** | **`COMBINER_DESIGN` §3.5's lead-break margin — in the WRONG direction for comfort.** A faster set node *shrinks* the required margin, which makes the SAFE detent less critical **but does not remove it**, because the binding term is the *output decay*, not the set node. | Re-derive §3.5's `≥0.2 s / ≥1.0 s` requirement with the measured value — **and note that the SAFE-detent argument is already refuted as insufficient** (see `COMBINER_DESIGN`'s correction banner **C-3**). A smaller required margin does **not** rescue it. |
| **Not a single pole** | The **6.9 τ → 0.1 %** relation used in §9.2 step 8 (460 ms / 690 ms) and in `SETPOINT_PATH` §6. | Replace the analytic settling figure with the **measured `t_0.1 %`** directly. Stop deriving it. |
| **The step overshoots above the commanded value** | **`SETPOINT_PATH`'s entire clamp argument.** The clamp bounds the *commanded* `Vset`; it says nothing about the module's own transient response above it. `numbers_probe.py` already prints a `[BLIND SPOT]` here. | **Report immediately.** An overshoot on a 1000 V command lands above Vnom on insulation sized for Vnom. This would be a new, unmitigated hazard and a G1 blocker. |

### Lands in
`docs/design/COMBINER_DESIGN.md` §9.2 (steps 1, 8), §11 (row 4) ·
`docs/design/SETPOINT_PATH.md` §6, §8.2 · `docs/design/MONITOR_AND_BLEED.md` §12.3 **O-M3** ·
`hardware/hvctl/numbers_probe.py` · `docs/DECISIONS.md` **PART-07**.

### Bonus, free, same rig, twenty seconds — measure Vref
With the module **unpowered and discharged**, disconnect `VSET` and measure the **open-circuit
`VSET` pin** with a 10 MΩ DMM. The internal ~10 kΩ pull-up puts **Vref** on that pin with a loading
error of `10k/(10k+10M)` = **0.100 %**, i.e. Vref known to **2.50 mV** (`SETPOINT_PATH` §2.3).

**This removes the module's ±1 % Vref initial-tolerance term — ±10 V of output error — from the
transfer function**, at the cost of a DMM reading and a line in a text file. It is a **10× accuracy
improvement**. Key it to the **module serial number**; replacing a module without recalibrating
reintroduces the full ±10 V, and that must appear on the panel label and in the service note.

**Also record the measured Vref against the clamp arithmetic.** `SETPOINT_PATH`'s headline
"+0.061 % over-range" divides by a **nominal** 2.500 V; at the datasheet's low limit of 2.475 V the
same clamp ceiling commands **1010.7 V (+1.07 %)**. **The measured Vref tells you which end of that
range this module actually sits at, and therefore what the real over-range is** — see that file's
correction banner **S-2**.

---

# M5 — CALIPER: A REAL MODULE AGAINST OUR FOOTPRINT

**No high voltage. No power. Twenty minutes. Do it even if you do nothing else in this document.**

## 7.1 Why this one matters more than it looks

The land pattern in `hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod` was derived **entirely
from vendor artwork** — Figure 1 of the manual, measured twice by pixel metrology at two zooms. That
work survived 3/3 skeptic passes and is almost certainly right about **the drawing**. But three
skeptics all recorded the same limitation, in the same words:

> *"It measures the **vendor's artwork**, not a module. It cannot detect an error in iseg's drawing,
> cannot see tolerances, and its bracket on body-referenced dimensions is ~±0.5 mm."*

**And iseg does not publish a pin-position tolerance at all.** Our land pattern spends its entire
mechanical allowance covering a tolerance the vendor never states:

```
  pin cross-section          0.64 mm SQUARE  ⇒ controlling diagonal 0.64 × √2 = 0.90510 mm
  finished hole              1.30 mm
  diametral allowance        1.30 − 0.90510 = 0.39490 mm
  RADIAL FLOAT               0.19745 mm            ← the entire budget
     less fab finished-hole tolerance   ±0.05 mm
     less plating/drill wander          (inside the above)
  ⇒ LEFT FOR PIN-POSITION ERROR         ≈ 0.15 mm   ← and nobody knows what iseg's is
```

**One caliper session retires that risk.** If the pins land where the drawing says, the assumption
is confirmed on a physical part and the risk is closed. If they do not, we find out **now**, on a
bench, instead of on a $2000 fab run where seven through-holes do not accept the module.

## 7.2 Instruments
- Digital caliper, **0.01 mm resolution**, jaws clean and zeroed **on this occasion** (close, zero,
  open, close, confirm 0.00).
- A flat reference surface.
- Optional and much better: a **pin-gauge or a drilled test coupon** — see §7.5.

## 7.3 Dimensions to check, and the pass/fail band

Measure on **both** modules. Take each dimension **three times** and record all three; a caliper on a
potted module is easy to rock.

| # | Dimension | Nominal (what we built to) | **PASS band** | If it fails |
|---|---|---:|---|---|
| **D1** | **Pin cross-section**, across the flats, both axes | **0.64 mm square** | **0.60 – 0.70 mm** | > 0.70 mm ⇒ diagonal > 0.990 mm and the **0.197 mm radial float collapses**. Redrill to 1.40 mm and re-check the pad annular ring (`PAD` 2.10 mm ⇒ ring falls 0.40 → 0.35 mm). |
| **D2** | **Pin pitch**, pins 1→2, 2→3, 3→4, 4→5 individually | **2.54 mm** | **2.49 – 2.59 mm** each | Any single gap out of band ⇒ the array is not on a 2.54 grid. **Stop and re-derive the whole pattern from the physical part.** |
| **D3** | **Pin 1 → pin 5 span** (4 × pitch — the accumulating one) | **10.16 mm** | **10.06 – 10.26 mm** | Out of band with D2 in band ⇒ a *systematic* pitch error. Rebuild the generator constant `PIN_PITCH_MM`. |
| **D4** | **Column separation**, pins 1..5 column ↔ pins 6/7 column | **34.80 mm** | **34.70 – 34.90 mm** | **This is the one to watch** — it is the longest dimension and any error here appears at full magnitude in the hole positions. Out of band ⇒ change `COLUMN_SEP_MM` and regenerate. |
| **D5** | **Pin 6 → pin 7 spacing** (same end of the module) | **10.16 mm** | **10.06 – 10.26 mm** | Also sets the **HV creepage**: pad 6 (HV) to pad 7 (GND) copper gap = `10.16 − 2.10 = 8.06 mm`. A shortfall here **eats HV clearance directly**. |
| **D6** | **Body length** | **39.60 mm** | **39.10 – 40.10 mm** (±0.5, the metrology bracket) | The **spec table rounds this to 40** — use the drawing. Out of band ⇒ courtyard and 3D model change; **not** an electrical failure. |
| **D7** | **Body width** | **15.70 mm** | **15.20 – 16.20 mm** | As D6. |
| **D8** | **Body height** | **11.00 mm** | **10.50 – 11.50 mm** | Enclosure only. |
| **D9** | **⬛ BODY OFFSET, long axis** — distance from the **pin 1..5 column** to the nearest body edge | **1.80 mm** | **1.55 – 2.05 mm** | **THE HIGH-VALUE CHECK.** The body is **not centred** on the pin array: `+0.60 mm` long axis, `+0.23 mm` short axis. If D9 comes back ≈ **3.00 mm** instead of 1.80 mm, **the offset is MIRRORED** and every courtyard, silkscreen and 3D placement is wrong-handed. |
| **D10** | **⬛ BODY OFFSET, short axis** — distance from **pin 1** to the nearest body edge along the short axis | **2.54 mm** | **2.29 – 2.79 mm** | As D9. Pin 1 sits at the corner where the case overhangs **least in both axes** (1.80 and 2.54); pin 6 at the corner where it overhangs **most in both** (3.00 and 3.00). **Confirm that mnemonic on the physical part — it is the whole chirality check.** |
| **D11** | **Pin length below the case** | **2.20 mm ± 0.40** | **1.80 – 2.60 mm** | < 1.8 mm on a 1.6 mm board leaves nothing to solder. Report; it changes the assembly note, not the pattern. |

## 7.4 ⛔ THE PIN-POSITION CHECK — the one that retires the actual risk

D1–D11 check *dimensions*. This checks **positions**, which is what the 0.197 mm radial float is
spent on.

1. [ ] Lay the module pins-up on the flat surface.
2. [ ] Using D2/D3/D4 above, compute each pin's **actual** position in the pin-array frame.
3. [ ] Compute each pin's **nominal** position: pins 1–5 at `x = 0`, `y = i·2.54`; pins 6 and 7 at
       `x = 34.80`.
4. [ ] For each of the 7 pins, compute the **radial error** `√(Δx² + Δy²)`.

| Worst radial error | Verdict | Action |
|---|---|---|
| **≤ 0.10 mm** | ✅ **PASS with margin.** Confirms the artwork on a physical part. | Retag the land pattern `[verified-artifact]` → `[verified-part]`. **The risk is closed.** |
| **0.10 – 0.15 mm** | ⚠ **PASS, no margin.** The pattern works but consumes the whole allowance. | Consider opening the drill **1.30 → 1.40 mm** (ring 0.40 → 0.35 mm, still above the reference board's 0.32 mm). A `board_spec.py`/generator change ⇒ **a G1 decision**. |
| **> 0.15 mm** | ❌ **FAIL.** The module will not seat, or will seat under stress. | **STOP.** Re-derive `DRILL_MM` from the measured worst case + fab tolerance, regenerate `gen_lib_footprints.py`, re-run its 8/8 mutation test, and re-run the pad-gap creepage screen (a larger drill on a fixed 2.10 mm pad shrinks the annular ring **and** the pad-to-pad copper gap that carries HV creepage). |
| **Pins visibly bent** | — | Straighten nothing on a module you intend to fit. Measure a second module. If both are out, it is the part, not handling. |

## 7.5 The better instrument, if you have twenty more minutes

**Drill a coupon and try it.** Take any scrap of 1.6 mm FR-4, drill seven 1.30 mm holes at the
nominal positions (a CNC, a drill press with a printed template, or the fab's own test coupon), and
**offer the module up to it**.

**This is a stronger instrument than the caliper**, for the same reason `PL-04` gives about schema
versions: it makes the *tool* produce the artifact instead of reading a description of it. It tests
the **whole pattern at once**, including accumulated error the per-dimension caliper checks can each
individually pass while the assembly still fails.

- [ ] Module seats fully, by hand, with no force ⇒ **PASS.**
- [ ] Needs persuasion ⇒ **marginal — treat as > 0.15 mm** in the table above.
- [ ] Will not seat ⇒ **FAIL**, and the caliper numbers tell you which dimension to fix.

## 7.6 What M5 does NOT tell you

- **It measures the two modules you own.** It says nothing about lot-to-lot variation, and iseg
  publishes no tolerance, so **`n = 2` is the entire dataset.** Record it as such.
- It cannot see anything about the module's **electrical** behaviour.
- It cannot validate the **3D model's** internal shape — only its footprint and outer envelope.

### Lands in
`hardware/hvctl/gen_lib_footprints.py` (constants `PIN_PITCH_MM`, `COLUMN_SEP_MM`, `BODY_L_MM`,
`BODY_W_MM`, `PIN_SQUARE_MM`, `DRILL_MM`, `PAD_MM`, the two overhang constants) — **fix the
generator and regenerate; never hand-edit the `.kicad_mod`** ·
`hardware/hvctl/gen_3d_model.py` · `docs/PART_iseg_APS.md` (mechanical section) ·
`docs/PIN_MAPS.md` §2 (regenerate) · `docs/DECISIONS.md` **LIB-*** rows.

---

# PART 8 — AFTER THE BENCH

- [ ] Every measured number written into the "lands in" files, **with the module serial number and
      the date**.
- [ ] Every `[ASSUMED]` / `[recalled]` / `MEASURABLE-NOW` tag on those numbers changed to
      `[verified-bench]` — **and only those.** Do not let a measurement of one parameter promote the
      tags of its neighbours.
- [ ] `hardware/hvctl/numbers_probe.py` re-run. **Expect assertions to FAIL** — that is the
      instrument working. In particular the ≤15 % load-budget assertion is expected to fail on an
      internal bleeder of ~20 MΩ (M3). **Do not relax an assertion to make it pass; adjudicate the
      design.**
- [ ] `hardware/hvctl/board_spec.py` re-run, exit 0.
- [ ] `docs/design/*.md` corrected where a measurement contradicts them — **in the generator/source,
      not by patching the prose** (`CLAUDE.md` rule 1).
- [ ] A line appended to `docs/SESSION_LOG.md` recording what was measured, on which serials, with
      which probe.

> **The four unmeasured parameters have blocked the fab-commit gate since session 1** (`PLAN.md`
> Phase 6: *"+ the four unmeasured module numbers have been measured"*). **This afternoon closes
> them.** M5 additionally closes the only risk in the project that no amount of document review can
> touch.
