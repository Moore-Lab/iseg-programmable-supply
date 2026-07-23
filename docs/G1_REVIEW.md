# G1_REVIEW — the gate package

**Gate G1 = values/interface freeze + human netlist-intent review + human pin-map review.**
**HUMAN-ONLY. No session may close it.** After G1, **changing `hardware/hvctl/board_spec.py`
requires a gate** — so what you sign here is the thing every later phase is measured against.

**Assembled 2026-07-23, end of session 2.** Reviewer: the human. Estimated read: **3–4 hours** for
§3 (netlist intent) + §4 (pin maps), which are the two parts only a human can do.

---

## 0. ⛔ READ THIS BEFORE ANYTHING ELSE — G1 IS NOT READY TO SIGN

Six load-bearing claims were put to **three independent skeptics each, every one tasked with
refuting rather than reviewing**. **All six were refuted.** Not one survived.

| Claim | Skeptics | Verdict |
|---|:-:|---|
| The physical mode switch is a real, obtainable part genuinely rated for this application | 3/3 refuted | ❌ **no part is specified at all**, and the one MPN named is rated 28 VDC |
| The mode-aware interlock makes the forbidden state unreachable in hardware, in both modes, in every ESP32 state | 3/3 refuted | ❌ **one welded HV reed reaches it**, and the executable proof never evaluates pseudo-bipolar |
| The design is safe if a human moves the mode switch at the worst moment | 3/3 refuted | ❌ **the derived timing margin is not met**, by 2×–19× |
| The `VSET` clamp makes commanding over-range impossible, and its failure modes are safe | 3/3 refuted | ❌ **the repo's own probe says otherwise**; one fault reaches 201 % of Vnom |
| The independent monitors load acceptably, beat `VMON`, and are independent | 3/3 refuted | ❌ all three legs fail, for three different reasons |
| `board_spec.py`'s domain assertions genuinely can fail; its pin numbering agrees with symbol and footprint | 2/3 refuted | ❌ assertions fire, **but four escape routes exist** and the footprint half is unchecked |

**Coverage:** every claim received **3 skeptic reports**. There is **no inconclusive claim** and no
coverage gap in this verification round.

> ## THESE ARE STOP-THE-LINE FINDINGS FOR A 1 kV INSTRUMENT.
>
> A refuted **interlock**, a refuted **`VSET` clamp** and an unsourced **mode switch** are the three
> elements the entire safety case rests on. G0-A3 deliberately gave both the serial link **and** the
> network **full write authority** over a recommended read-only default, and recorded that *"the
> hardware interlock, hardware `VSET` clamp and soft limits therefore carry the entire safety case."*
> **Two of those three are now refuted and the third has no part number.**
>
> **Do not sign G1 as a whole.** §7 lists exactly what must be repaired first. §1 and §3 are
> reviewable *now* and should be reviewed now — the refutations do not invalidate the netlist
> structure, they invalidate specific claims *about* it.

The full refutation text, with the corrections that now govern, sits in **correction banners at the
top of each owning design document** (`COMBINER_DESIGN.md` C-1…C-5, `SETPOINT_PATH.md` S-1…S-7,
`MONITOR_AND_BLEED.md` M-1…M-4, `CONTROLLER_AND_POWER.md` §9.2 SUPERSEDED, `board_spec.py`
D-7…D-10). §7 of this file is the consolidated action list.

**Also, plainly: G0 questions Q3, Q5 and Q6 were never answered and the design is proceeding on
documented defaults.** See §6.4.

---

## 1. The frozen values table

Sign this table row by row. **A row you are not willing to defend is a row that must not freeze.**
Evidence tags are per `CLAUDE.md` rule 4; the "cannot see" column is the honest limit of each
instrument.

### 1.1 The module (`AP010504P05` / `AP010504N05`) — G0-A2, both in hand

| Value | Frozen as | Evidence | The instrument cannot see |
|---|---|---|---|
| Pin map `1 +VIN · 2 VSET · 3 GND · 4 /ON · 5 VMON · 6 HV · 7 GND` | **FROZEN** | `[verified-artifact]` Table 4 p.9 extracted verbatim by 5 independent agents across 2 sessions; Figure 1's own top-view panel re-rendered as an *independent* statement of the same fact; the 2019 v2.1 revision agreeing pin-for-pin 5 years apart; 3 separate parsers. **Survived 3/3 skeptics, session 1.** | Whether iseg's own table is right. **No physical module has been probed.** The source table is captioned *"Technical data: options and order information"* — a copy-paste error, i.e. this vendor document **does** contain uncorrected editorial mistakes. |
| `Vnom` = **1000 V**, `Inom` = **0.5 mA**, `Iout` ≤ ≈**0.75 mA** | **FROZEN** | `[verified-artifact]` Table 1 | — |
| `Vin` = **5 V**, `Iin` < **180 mA** per module at Vnom loaded | **FROZEN** | `[verified-artifact]` Table 1 | Typical vs max not separated for all rows |
| `Vref` (internal) = **2.5 V ±1 %**; `Vset` 0…2.5 V; `Vmon` 0…2.5 V | **FROZEN** | `[verified-artifact]` Table 1 p.7, extracted by 3 skeptics this session | **The ±1 % is load-bearing** — see §1.4 and `SETPOINT_PATH` banner S-2 |
| `VMON` accuracy = **1 % · Vnom = 10 V** | **FROZEN** | `[verified-artifact]` | This is the number the independent monitor exists to beat. See §1.4. |
| Ripple/noise guaranteed **only for 2 %·Vnom < Vout ≤ Vnom**, i.e. **only above 20 V** | **FROZEN** | `[verified-artifact]` | **Below 20 V the output is UNSPECIFIED, not merely worse.** Every low-end figure in the project inherits this. |
| `VSET` internal ≈**10 kΩ pull-up to Vref** ⇒ **open `VSET` commands FULL SCALE** | **FROZEN** | `[verified-artifact]` + algebra: the `Rset` formula uniquely pins the node's Thévenin equivalent to (Vref, 10 kΩ) — pull-down and current-source hypotheses were coded and **both diverge**; the control-principle figure at native resolution shows the resistor. **Survived 3/3 skeptics.** | The **tolerance** of the 10 kΩ is unpublished — **O-A: the `VSET` fail-open criterion breaks at 7.83 kΩ.** MEASURABLE-NOW. |
| `/ON` is **ACTIVE-LOW** ⇒ floating `/ON` turns HV **ON** | **FROZEN** | `[verified-artifact]` | — |
| Output **"internally not limited"** above Vref | **FROZEN** | `[verified-artifact]`, verbatim in **both** document revisions | — |
| **3.3 V on `VSET` ⇒ 3.3/2.5 = 132 % ⇒ ≈1320 V** | **FROZEN** | arithmetic over the two rows above | — |
| Footprint: body **39.60 × 15.70 × 11.00 mm**, pins **0.64 mm square**, pitch **2.54**, column sep **34.80**, body offset **+0.60 / +0.23 mm** from the pin centroid, **not mirrored** | **FROZEN** | `[verified-artifact]` two *independent* pixel-metrology passes at different zooms agreeing to 0.02 mm; extension-line-to-feature tracing; signed-cross-product chirality check; `pcbnew` readback; 8/8 mutation test. **Survived 3/3 skeptics.** | **It measured the vendor's ARTWORK, not a module.** Cannot detect an error in iseg's drawing, cannot see tolerances, bracket ≈±0.5 mm on body dimensions. **⇒ `docs/BENCH_MEASUREMENTS.md` M5.** |
| Land pattern: drill **1.30 mm**, pad **2.10 mm**, radial float **0.197 mm** | **FROZEN** | derived; reference board's 1.143 mm evaluated and rejected | **iseg publishes NO pin-position tolerance.** The float is spent covering a number nobody has. **⇒ M5.** |

### 1.2 Clearance and touch safety — **NONE of this is frozen**

| Value | Status | Evidence |
|---|---|---|
| `C_HV` = **7.5 mm** single-ended at 1000 V | **`[unverified-primary]` — NOT FROZEN** | `[recalled]` + two secondary web reproductions **later shown to be the same web page**. Session 1's "independent cross-check between two standards families" was an **algebraic tautology** (above 500 V both expressions reduce to `0.005·V`, so the four assertions could not fail for *any* input). **It was DELETED and no replacement was invented**, because there was nothing honest to put there. |
| `C_HV_PAIR` = **15.0 mm** pairwise `HV_POS`↔`HV_NEG`, `HV_OUT_A`↔`HV_OUT_B`, and two NEW rules `HV_M`↔`HV_OUT_B`, `HV_X`↔`HV_OUT_A` | **`[unverified-primary]` — NOT FROZEN** | as above. A netclass **cannot** express a pairwise rule; these must be `.kicad_dru` rules (NUM-03). |
| Touch-safe **60 V within 5 s**; hazardous energy **350 mJ**; **50 µC** | **`[recalled]` — NOT FROZEN, NO SOURCE AT ALL** | The whole Phase-7 safety argument rests on these three numbers and **not one has a primary source.** |

> ⛔ **A human must obtain and read a primary copy of IPC-2221B Table 6-1 and IEC 60664-1 / 62368-1
> before layout.** This is **decision-relevant, not bookkeeping**: the printed-board reading fits a
> 100 × 100 mm fab tier (78.4 × 91.7 mm) and the material-group-IIIa reading does **not**
> (108.4 × 106.7 mm). A wrong constant becomes a DRC rule and is **undiscoverable after fab.**
> **Signing G1 does NOT freeze these.**

### 1.3 The HV network as built (`board_spec.py` `HV_STRINGS`) — 12 strings, 80 elements

| String | Value | Construction | Role | Status |
|---|---|---|---|---|
| `BLDA` / `BLDB` | 20.0 MΩ | 2 ∥ (2 × 20.0 MΩ), 2512 | output-node bleed (S1) | ⚠ **CONFLICT — see below** |
| `BLDP` / `BLDN` | 20.0 MΩ | 2 ∥ (2 × 20.0 MΩ), 2512, **on the relay NC contact** | module-branch park bleed (S4) | ⚠ **CONFLICT — see below** |
| `BLDX` / `BLDM` | 400 MΩ | 2 ∥ (2 × 400 MΩ), 2512 | mode-switch stub bleeds; cover the SAFE detent | **Not mentioned anywhere in `MONITOR_AND_BLEED.md`** — they are why the real load is 12.40 %, not 11.40 % |
| `MONA` / `MONB` | 200 MΩ | 2 ∥ (10 × 40 MΩ), **1206** | invariant-(c) independent monitor (S2) | N = 10 set by **VCR (goes as 1/N)** and the pad-gap screen at 100 V/element — **not** by resistance |
| `CLDA` / `CLDB` | 1.00 GΩ | 2 ∥ (2 × 1.00 GΩ), 2512 | COLD permissive (S3) | deliberately **5× lighter** than the monitor: it needs 20:1 discrimination, not 0.03 % |
| `BRNP` / `BRNN` | 1.00 GΩ | 2 ∥ (2 × 1.00 GΩ), 2512 | per-branch monitor (S5), **upstream of the relays** | this is what makes the weld self-test real rather than a silent false-pass |

**Every string is TWO PARALLEL SUB-STRINGS (NUM-09 / SA-9).** That is the frozen rule you are
signing: *a single open element costs a factor, never the path.* A single open element in a bleed
costs ~1.6× in discharge time; a single open element in the COLD string **doubles the threshold**
(still a cold switch) rather than forcing COLD true.

> ⚠ **CONFLICT D-1 — YOU MUST ADJUDICATE THIS AT G1.** `COMBINER_DESIGN.md` §5.1 says the
> module-side bleeds sit **upstream of the relay at 40 MΩ**, and §5.2/§5.3 sum **both** the
> module-side and output-side bleed onto the same live node (17.24 MΩ closed). But
> `COMBINER_DESIGN.md`'s **own block diagram** draws `K1 NC → R_bleed_POS → GND` — on the
> **normally-closed contact** — and `MONITOR_AND_BLEED.md` §6 **requires** that arrangement, because
> the weld self-test raises a *parked* module to 200–1000 V and needs it to actually get there.
> **The two readings cannot both be true.** `board_spec.py` builds the **NC-contact** arrangement at
> **20.0 MΩ**. Consequence to propagate: `COMBINER_DESIGN.md` §5.3's "relay closed = 17.24 MΩ" is
> then **optimistic by ~1.76×**. Reported, not patched. **This changes the netlist. Decide.**

**Resistor working-voltage ratings — `[ASSUMED]`, never read from a datasheet, no MPN exists:**
1206 = 800 V, 2512 = 1500 V. `board_spec_parts.py` says so verbatim. The string element counts are
derived *from* those assumptions.

### 1.4 The set-point path and the monitor

| Value | Frozen as | Evidence / caveat |
|---|---|---|
| Clamp mechanism: **the 2.500 V rail that powers the `VSET` buffers' output stages IS the clamp** (a rail-to-rail output stage cannot exceed its own rail; **no component in the signal path**, so ARCH-04 is not violated) | **FROZEN as a mechanism** | `[verified-run]` 52/52 assertions. **Candidate D (DAC referenced to the module's Vref pin) was DROPPED, not invented — there is no Vref pin.** Table 4 lists exactly 7 pins. |
| Clamp ceiling **2.501525 V** | **FROZEN** | `2.500 × (1 + 5e-4 initial + 6e-5 tempco/20 K + 5e-5 long-term)`, derived two independent ways agreeing to 0.001 % |
| Over-range **"+0.061 % = 1000.6 V"** | ❌ **DO NOT FREEZE — WRONG** | divides by a **nominal** 2.500 V. At the datasheet's `Vref = 2.475 V` the same ceiling commands **1010.7 V = +1.07 %, 17× the quoted figure**. `numbers_probe.py` independently rates it **100.30 %**. **Freeze +1.07 %, worst-case Vref.** |
| Clamp fail-open holds `VSET` at **47.6 V** via duplicated 2 × 1.00 kΩ at the pin | **FROZEN** | survives all three skeptics; **but inherits O-A** (module pull-up tolerance) — MEASURABLE-NOW |
| `VSET` drive impedance **≤ 10 Ω** to the pin; **no series resistor** between buffer and pin | **FROZEN** | ARCH-04: a 1 kΩ there is 91 V of uncommanded output |
| Monitor divider: `α = 8.1899e-4`, `Zsrc = 163.80 kΩ`, `tap0 = 2.04747 V`, FS = ±2500.7 V, LSB = 0.0763 V | **FROZEN (arithmetic)** | independently reproduced by 3 skeptics |
| Monitor **"31× better than `VMON`"** | ❌ **DO NOT FREEZE** | `numbers_probe.py` still prints 31.0× on an α the design document itself disowns. `MONITOR_AND_BLEED` §4.4 says 6.6×. **Including the 5.0 V long-term drift §4.4 excludes gives ~2×.** On bare FR-4 with no guard it is **20.0 V — worse than `VMON`.** The 100× guard factor is `[ASSUMED]` and unmeasured. **Freeze ~2×, conditional on the guard.** |
| Hardware OVP trip = **105 % = 1050 V** per output, **latched**, feeds `nOVP` into `ARM` | **FROZEN** | closes session 1's open fault 15 |
| Standing HV load per module | ⚠ **four different numbers in the repo** | probe **11.00 %** · `MONITOR_AND_BLEED` §8 **11.40 %** · `COMBINER_DESIGN` §5.2 **12.60 %** · with the `BLDX`/`BLDM` stubs **12.40 %** (PB) / **11.90 %** (UNI-neg). All under 15 %. **Pick one, assert it, regenerate.** |

### 1.5 Timing and interface limits

| Value | Frozen as | Caveat |
|---|---|---|
| `C_load` interface limit **≤ 10 nF**, cable ≤ **10 m** | **FROZEN as a declared interface constraint** | Nothing enforces it physically. `COMBINER_DESIGN` F-33 suggests a permanently-fitted in-line HV series resistor in the output cable. **Consider making it physical.** |
| Decay 1000 V → 10 V: **96.9 ms** bare / **954.4 ms** at the `C_load` limit | **FROZEN (arithmetic)** | **assumes `C_module` = 1 nF — MEASURABLE-NOW, and `MONITOR_AND_BLEED` assumes 100 pF instead.** |
| Discharge to 60 V within **5 s**, board unpowered, incl. one bleed string open | **FROZEN as a target** | the 60 V/5 s threshold itself is `[recalled]` with no source |
| Changeover dead-band ≈**1 s** nominal; `T_dwell_hw` = **0.5 s** | **FROZEN** | at `C_module` = 10 nF it becomes **≈2.0 s** — a requirements breach against G0-A1. MEASURABLE-NOW. |
| Heartbeat: `EN_HB` falls **≈79 ms** after the toggle stops (100 nF / 1 MΩ, τ = 100 ms) | **FROZEN** | faster than the module's own 100 ms set-node pole |
| Required mode-switch lead-break margin: **≥0.2 s bare, ≥1.0 s at the `C_load` limit** | **FROZEN as a REQUIREMENT** | ❌ **and it is NOT MET.** The mechanism offered is ~100 ms of SAFE-detent dwell, `[recalled]`. See §7. |
| 5 V rail total **1094 mA** ⇒ **5 V / 2.5 A** supply at 2.0× margin | **FROZEN** | corrects `NUMBERS_PROBE` §6.2's 1.8 A; **the probe must be regenerated, not patched** |

### 1.6 Interfaces frozen by G0, not re-litigated here

- **G0-A1** set-and-hold with polarity changeover; smooth through-zero **NOT** required; ~1 s
  dead-band with the output **clamped to ground**. Combiner = **HV RELAY CHANGEOVER**. Diode-OR,
  series-stack and single-module-reversing are **REJECTED**.
- **G0-A3** serial **and** network, **both write-authoritative**, chosen deliberately over a
  recommended read-only-network default.
- **G0-A4** dual mode. In unipolar, **+1 kV and −1 kV coexist as a NORMAL steady state**, so the
  **2 kV `HV_POS`↔`HV_NEG` differential is the binding NORMAL case, not a fault case.**
- **G0-A5** mode selection is a **PHYSICAL SWITCH**. There is **no mode relay**. HV routing and the
  interlock permissive move on the **same armature**, so they cannot disagree by construction. Mode
  change is a **powered-down, cables-off** operation.

---

## 2. What `board_spec.py` currently is

```
  components : 441          (the brief circulating in this session said 419 — STALE)
  nets       : 321          (said 314 — STALE)
  netclasses : 10           Default, HV_M, HV_NEG, HV_OUT_A, HV_OUT_B, HV_POS,
                            HV_SENSE, HV_SW_G, HV_X, PWR
  HV strings : 12, 80 elements
  reachable mechanical states evaluated : 24
  TIER-C (borrowed pinout) components   : 44     (said 42 — STALE)
  exit 0   [verified-run, this session]
```

It self-reports **9 assertions that are NOT structurally expressible** — recorded, not dropped:
SA-9 placement · graded string spacing · **HCT vs HC** · push-pull comparators · **relay coil
polarity** · **K1/K2 orthogonal mounting** · **weld detection** · **discharge TIME** · SA-12 dump
sizing. Each needs a generator invariant, a BOM property, or a bench test. **Four of those nine are
safety properties that no file in this repo can check.**

And its own banner: *"WHAT EXIT 0 DOES NOT MEAN: no value was verified, no part was confirmed to
exist, no TIER-C borrowed pinout was checked against a datasheet, and nothing was simulated, built
or measured."*

---

## 3. THE NETLIST INTENT — block by block

**This is the part of G1 only a human can do, and it is the reason the gate exists.** A wrong
netlist intent produces a netlist that is perfectly self-consistent and a board that is perfectly,
self-consistently wrong. ERC, DRC, parity checks and the domain assertions are all **blind** to it.

**Do not read 321 nets.** Read the twelve blocks below against your own mental model of the circuit,
and for each one answer the question at its end. If the prose describes a circuit you would not have
drawn, **say so** — that is exactly the defect this gate catches.

---

### Block 1 — Input and power tree (`board_spec.py` §9.1)

**Intent.** One **12 V DC** input at a 2.1 mm locking barrel jack (`J1`). It passes a 2 A(T) fuse, a
**P-FET reverse-blocking / soft-start** element (`Q1`), an SMBJ15A TVS and a 470 µF bulk cap; that
node is `+12V`. Three converters hang off it in parallel, deliberately **not** cascaded:

- `U10` **buck 12 → 5.00 V** (`+5V_MOD`) — feeds **everything safety-relevant**: the whole 74HCT
  interlock array, the three TPS3701 rail supervisors, the relay-coil load switch and both module
  `+VIN` load switches.
- `U11` **buck 12 → 3.30 V** (`+3V3`) — ESP32-S3, W5500, CP2102N, the 74LVC level parts, and an
  `LP5907` cascaded to `+3V3_A` for the two ADCs.
- `U12` **LDO 12 → 5.00 V low-noise** (`+5V_A`) — exists **only** because µV-class analogue cannot
  share a switcher's return: `REF5025` → `VREF_2V500`, the monitor buffers, the guard drivers and
  the comparators live here.

`RAIL_OK` is a **wire-AND of three open-drain supervisor outputs** and is one of the seven `ARM`
terms.

> **The safety property.** The interlock runs from **5 V**, not 3.3 V, so **losing the 3.3 V rail
> cannot float any interlock input** — every ESP32-sourced signal has duplicated pull-downs to GND
> and reads 0. And every gate is **74HCT, not 74HC**: at Vcc = 5 V a 74HC part wants
> `V_IH` = 3.5 V, which a 3.3 V output does not meet — **an HC part appears to work at room
> temperature and fails at a corner.** This is a **BOM-value property** the symbol cannot express
> and ERC cannot catch; it is one of the nine non-expressible assertions.

**Ask yourself:** *is a single 12 V input with three parallel converters right, or would you have
fed the analogue LDO from the 5 V buck?* (Answer intended: from 12 V, so the switcher's ripple never
enters the analogue rail at all.) *Is `RAIL_OK` in the `ARM` chain, or merely reported?* (It is in
the chain.) *Note the conflict:* `INTERFACES.md` §2.2 still says *"5 V only — there is no +12 V
rail"* (deviation **D-6**) — **that line is stale and needs your edit.**

---

### Block 2 — Module supply chain (`§9.2`) — the exclusivity that carries the invariant

**Intent.** `+5V_MOD` → **`Q_ARM`** (a load switch gated by `ARM`) → **`VIN_ARMED`**. That single
node feeds **`K_S` pole A**, a Panasonic `TQ2SA-5V` 2-Form-C relay. Pole A's NO throw is
`VIN_P_PRE`; its NC throw is `VIN_N_PRE`. Each of those goes through **its own load switch**
(`U_P` / `U_N`, `TPS22918`-class, `EN = PERMIT_P` / `PERMIT_N`), then a ferrite, then the
**datasheet-mandated 22 µF** (PART-18), then module pin 1.

`K_S` **pole B** does the same job for the **relay coil feed**: `COIL_ARMED` → NO = `COIL_FEED_P`,
NC = `COIL_FEED_N`.

> **This is the structural fact the whole theorem rests on: in pseudo-bipolar, the only power that
> can reach either HV relay coil passes through ONE ARMATURE. One piece of metal cannot touch both
> throws. That is not a truth table; it is a statement about metal.**
>
> **What releases it is not a logic signal.** It is `SW1` poles **S6** (`SW1F`, bridging
> `VIN_P_PRE` ↔ `VIN_N_PRE`) and **S7** (`SW1G`, bridging `COIL_FEED_P` ↔ `COIL_FEED_N`), closed
> **only in the UNIPOLAR detent** — the same armature that has already routed the two modules to
> physically different nodes. **A firmware fault, a stuck GPIO, a network command or a stuck gate
> output cannot close a mechanical contact.**

`K_S` transfers **cold, for free**: `KS_SEL`'s latch enable includes `nARM`, and `Q_ARM` is gated by
`ARM`, so whenever the armature is allowed to move `VIN_ARMED` = 0 V and the contact transfers with
**no source behind it**. The 22 µF sits **downstream** of `U_P`/`U_N`, never on the `K_S` contacts.

**Ask yourself:** *if firmware falsely asserts `MODE_UNI` while the switch is physically in
pseudo-bipolar, what happens?* (Both modules can internally make HV, but `S6`/`S7` are open so only
one is connected to any output node — abnormal, detectable, **not** the forbidden state.) *And are
`S6`/`S7` really on the same armature as `S1`/`S2`/`S3`, or are they four separate switches in a
harness?* — **`board_spec.py` puts all four LV poles on ONE 8-way header `J6`, with
`COIL_FEED_P/N` on ADJACENT pins 7/8. A solder bridge there is an ordinary defect that welds `S7`.**

---

### Block 3 — The two HV modules (`§9.3`)

**Intent.** `U1` = `AP010504P05` (positive), `U2` = `AP010504N05` (negative). Two **different
symbols** extending one base, so the polarity is carried in CAD identity and not in a value string.
Each: pin 1 `+VIN_P/N`, pin 2 `VSET_P/N`, pins **3 and 7 both to GND, routed independently to the
pour** (PART-16 — not daisy-chained), pin 4 `nON_P/N`, pin 5 `VMON_P/N`, pin 6 `HV_POS` / `HV_NEG`.

**Ask yourself:** *are both GND pins independently routed?* *Is the polarity distinction visible in
the schematic without reading a value field?*

---

### Block 4 — HV routing matrix (`§9.4`) — the circuit the invariant is about

**Intent, in signal order:**

```
  HV_POS ─[R_S_P 10k]─ HV_POS_COM ─ K1 COM
                                     K1 NC (12) ─ HV_POS_PARK ─[BLDP 20M]─ GND
                                     K1 NO (14) ─────────────────────────► HV_OUT_A

  HV_NEG ─[R_S_N 10k]─ HV_NEG_COM ─ K2 COM
                                     K2 NC (12) ─ HV_NEG_PARK ─[BLDN 20M]─ GND
                                     K2 NO (14) ─────────────────────────► HV_X

  SW1A (S1) SPDT, COMMON = pin 2 = HV_X :  PB throw → HV_M   |  UNI throw → HV_OUT_B
  SW1B (S2) SPST           HV_M1 ↔ HV_OUT_A                  closed in PB only
  SW1C (S3) SPDT, COMMON = pin 2 = HV_SW_G (= GND via R_G 10k):
                            PB throw → HV_OUT_B   |  UNI throw → HV_M
  R_M1 10k : HV_M → HV_M1        R_G 10k : HV_SW_G → GND
  J2 = SHV bulkhead A on HV_OUT_A      J3 = SHV bulkhead B on HV_OUT_B
```

**Three things to understand here, because they are the design's cleverest parts:**

1. **The `M` node exists ONLY to split a 2000 V stress into two 1000 V gaps.** Pseudo-bipolar needs
   a conducting path from the NEG module to `OUT_A`; unipolar needs that path open while its two
   ends sit at opposite full polarity. **Some** open element must hold 2 kV. Breaking the path in
   *two* places and **grounding the intermediate node in the position where both breaks are open**
   means **no contact and no pole pair of the mode switch ever sees more than 1000 V.** The 2000 V
   appears only between board copper, where the two pairwise `.kicad_dru` rules handle it.
2. **`S3`'s common is GROUND.** Therefore **every weld of `S3` fails toward "that output is
   grounded"** — the safe direction, by construction. And `OUT_B` in pseudo-bipolar is held at
   ground by **three independent things**: the `S3` bond through `R_G`; the permanent `BLDB` bleed
   present in every position and every power state including unpowered; and the fact that `S1`
   routes `X` to `M`, so **nothing can drive `OUT_B` at all**. It is never floating, never
   unterminated, never charged — **structurally**, not by a timer or a firmware step.
3. **The asymmetry is forced, not chosen.** The POS module drives `OUT_A` in **both** modes, so a
   pole in the POS path would have both throws landing on the same node — degenerate, and it would
   add a weld site in the highest-margin path. **Consequence, and do not be surprised at
   commissioning:** the NEG path carries one extra series limiter (`R_M1`), so NEG→`OUT_A` drops
   **15.0 V** at the 0.75 mA limit against **7.5 V** for POS. Both drops are **upstream** of the
   independent monitors, so both are measured rather than guessed, and both fall out in per-output
   calibration. **`OUT_A` and `OUT_B` are NOT interchangeable — not in firmware, not in calibration,
   not on the panel.**

> **BUILD RULE SW-1, and it will not look wrong if you get it wrong:** `S3` (the grounded pole) must
> be **physically interposed between `S1` and `S2`** — middle deck of three, or a grounded unused
> sector between them on one wafer. Otherwise the *pole-to-pole* stress is 2 kV regardless of the
> contact algebra, and the board is **under-insulated by 2×**.

**Ask yourself:** *`Switch:SW_SPDT`'s common is **pin 2**, not pin 1.* Check `SW1A` and `SW1C` in
`PIN_MAPS.md`. Assuming "pin 1 is the common" would swap a throw with the common on every HV pole.
*Also:* `QK1`/`QK2` are specified in `COMBINER_DESIGN` §6.3 as **2N7002 (~115 mA) for a 125 mA
coil** — `board_spec.py` flags this **UNDER-RATED** and demands a ≥300 mA part. **Confirm the
change.**

---

### Block 5 — HV strings (`§9.4` tail) — 12 strings, 80 elements, generated not typed

**Intent.** Every bleed and every divider top leg is **data in a table**, so that (a) elements are
generated rather than typed, (b) every interior node's **potential** is derivable from its position
in the string, and (c) the per-element working voltage is **checkable against the package rating**
instead of asserted in prose. See §1.3 for the schedule.

**Ask yourself:** *is 2 ∥ N the right redundancy rule?* It costs 2× the parts and 2× the standing
current, and it buys: an open element becomes a **factor**, not a lost path. *And are the four
output/branch nodes the right four nodes to bleed?* (`HV_OUT_A`, `HV_OUT_B`, and the two **parked**
module branches on the relay NC contacts — the parked bleed is engaged **whenever the relay is
de-energised, which is the unpowered default state**.)

---

### Block 6 — Independent monitors (`§9.5`) — invariant (c)

**Intent, per output.** `HV_OUT_x` → `MONx` 200 MΩ string → `HVDIV_TAP_x`. At the tap, three
resistors meet: `RMB_x` 909 k to GND, **`RMO_x` 200 k to `VREF_2V500`** (offset injection — so a
**negative** output produces an in-range tap, making the reading **sign-aware**), and `RMS_x` 1.00 M
into a 1 nF C0G anti-alias pole. The filtered tap goes to a **unity-gain sub-nA-bias buffer** and
then to **ADC-A**. Each chain has its **own driven guard ring at tap potential**.

> **The guard ring is a REQUIREMENT of this monitor, not a refinement.** At `Rt` = 200 MΩ a 10 GΩ
> board leakage path injects **20.0 V** of error — **larger than the 10.0 V `VMON` accuracy the
> divider exists to improve on.** Unguarded, the independent monitor is *worse than the thing it
> replaces.* And the 100× guard improvement factor is **`[ASSUMED]` and has never been measured.**

**The reason this chain exists at all:** `VMON` has **no sign information**. A broken `SEL` wire
makes the terminal produce the wrong polarity, and **only a sign-aware independent monitor can see
it** (`COMBINER_DESIGN` F-2). That is the concrete justification for the whole block.

**Ask yourself:** *is it genuinely independent?* — **Not entirely.** `RMO_x` (monitor offset) and
`RCO_x` (COLD offset) both feed from **the same `REF5025`**, and the file's own independence
assertion passes only because `VREF_2V500` is **whitelisted**. **One `OPA2192` (`UGD`) drives BOTH
guard rings** — a single package failure degrades both "independent" monitors at once. *And:*
`MON_TAP_A/B` also feed the **hardware OVP** comparators, so **one open S2 element halves the
reading and pushes the 1050 V trip to ≈2100 V** — blinding the monitor and the OVP together. **None
of these three is in `MONITOR_AND_BLEED` §10's fault table. Decide whether you accept them.**

---

### Block 7 — COLD permissive and branch monitors (`§9.6`) — correction C-2

**Intent.** A **physically separate** 1.00 GΩ string per output (`CLDA`/`CLDB`) → its own offset
network → its own **window comparator** (`|V_tap − V_ref| < threshold`, i.e. **sign-blind by
design**, which is exactly what *"is this node cold?"* asks). `COLD = COLD_A · COLD_B`.

**Why it must be separate.** F-3: with COLD derived from the *same* divider as invariant (c), **one
open HV resistor** makes the monitor read "0 V", which forces COLD permanently TRUE, which makes the
cold-switch latch permanently transparent, which makes **hot switching possible on every
changeover** — and hot switching is the mechanism that welds contacts. **One cracked resistor
converts a random 10⁸-operation wear-out into a systematic consequence of normal operation, while
removing the monitor that would have shown it.** Three changes break that chain: the separate
string; the 2-parallel construction (one open string **doubles the threshold** rather than forcing
COLD true — still a cold switch); and an **executable self-test at every enable** (command a known
non-zero output, require COLD to go false). Comparators must be **push-pull, never
open-drain-with-pull-up** — an open-drain failure pulls up to a **false COLD = 1**, the wrong
stuck-state.

**Branch monitors** `BRNP`/`BRNN` (1 GΩ) sit on `HV_POS`/`HV_NEG` **upstream of the relays**. They
are what turns the weld self-test from a detector with a silent false-pass into a real one.

**Ask yourself:** ⚠ *`board_spec.py` D-2 declines to build `MONITOR_AND_BLEED` §5.4's proposed
2-of-2 AND* (COLD = S3 window **AND** a comparator on the S2 tap), because implementing it would
**silently break the frozen assertion SA-8** ("the COLD divider shares no component with the
invariant-(c) monitor"). **The consequence of not building it:** §10 rows 10 and 12 claim STUCK-SAFE
*solely* via that AND, so they are **unmitigated as built** — one open S3 element doubles the COLD
threshold from ±36.8 V to ≈±74 V, **above the 60 V touch limit**, silently. **This is a G1 decision:
reword SA-8 and build the AND, or accept the residual in writing.** ⚠ *And D-3:* §5.2's published
COLD values are **unrealisable** and were moved (`Ro` 1.24 M → 1.58 M, node centre 2.046 → 1.950 V),
with values that are **nominal-E96 and have never been through a numbers probe.**

---

### Block 8 — References and the `VSET` clamp (`§9.7`, `§9.8`)

**Intent.** `REF5025` on `+5V_A` gives `VREF_2V500`. **`U3` is a rail-force amplifier** — unity
gain, `V+ = +5 V`, Kelvin-sensed — that turns that reference into a **low-impedance `VCLAMP` rail**
capable of sourcing the clamp current. **It is MANDATORY, and the numbers probe is what found it:**
the clamp must sink the module's internal pull-up at **250 µA per channel**, which a bare reference
cannot do.

**`U4` IS THE CLAMP.** A rail-to-rail-output dual op-amp **whose V+ is `VCLAMP` (2.500 V)**. A
rail-to-rail output stage **cannot exceed its own positive rail**. That is the entire mechanism, and
crucially it puts **no component in the signal path**, so ARCH-04's ≤10 Ω drive-impedance rule is
not violated. `DAC8552` (dual 16-bit, `VDD` = +5 V, `VREF` = `VCLAMP`) drives `U4` through 1 kΩ into
the **non-inverting** input; `U4` force/senses to the module pin with `R_local` 10 kΩ in the local
loop and a 10 Ω element **inside** the Kelvin loop.

**At the module pin, in this physical order:** `2 × 1.00 kΩ` pull-down to GND (ARCH-18 duplication —
this is what turns *clamp fails open* from 1000 V into **47.6 V**), a **`BAT54` cathode-to-`VSET`,
anode-to-GND** (clamps negative excursions and **fails safe in both directions**: short ⇒ `VSET` = 0,
open ⇒ only the protection is lost), a 100 nF C0G, and a **2N7002 shunt whose gate is `/ON_P`** —
so a **disabled module has `VSET` grounded in hardware**.

**`U5`** is a window comparator on the clamp rail (thresholds 2.430 / 2.551 V, from an
**LM4040-2.048 — a DIFFERENT device from the `REF5025`**) that catches the one fault the rail clamp
structurally cannot: **the rail itself rising.** **`U7`** is a second comparator directly on `VSET`
at 2.551 V.

**Ask yourself:** *does making the clamp rail and the DAC reference the SAME node worry you?*
`PART_iseg_APS.md` §8.2 warned about exactly that (*"a shared reference failure would raise the clamp
and the command together"*) and ARCH-06 deliberately makes them the same node. **Both are right and
the repo contains a genuine tension** — the resolution is `U5`, whose reference is a different
device. **Is that enough?** `numbers_probe.py` says a reference-shorted-to-5 V fault reaches
**201 % of Vnom = 2012 V — worse than the un-clamped 3.3 V case** — and `U5`'s stuck-HIGH failure is
**undetectable in service**. ⚠ *Also:* **`U4` has no part number** (`**UNSELECTED RRIO dual**`), and
`CONTROLLER_AND_POWER` §5.3 still specifies a **shunt LM4040-2.5 clamp rail that `board_spec.py`
does not build**. One of the two must change.

---

### Block 9 — The interlock gate array (`§9.9`) — the safety case in silicon

**Everything on `+5V_MOD`. Everything 74HCT.** Read the algebra, then read the two paragraphs after
it, because the second one matters more than the first.

```
  MODE_VALID = MODE_A  XOR  MODE_B                        U32 74HCT86
       (1,0) = pseudo-bipolar        (0,1) = unipolar
       (0,0) = SAFE detent / in transit / both aux wires broken  → INVALID
       (1,1) = mechanically impossible → a shorted aux           → INVALID

  ARM = NAND8( EN_HB, ARM_EN, INTLK, nOVP, SETTLE, RAIL_OK, MODE_VALID, tied-HIGH )
                                                          U30 74HCT30 → nARM → U31 → ARM
       Seven terms, of which THREE ARE PHYSICAL: the INTLK loop, MODE_VALID from the
       panel switch's own contacts, and — through EN_HB — firmware liveness.

  MODE_UNI = MODE_B · nMODE_A                             U33a 74HCT08
  PERMIT_P = ARM_OUTEN · (MODE_UNI + nSEL)                U34a 74HCT32 + U33c
  PERMIT_N = ARM_OUTEN · (MODE_UNI +  SEL)                U34b        + U33d

  ⇒ PERMIT_P · PERMIT_N = ARM · EN_P · EN_N · MODE_UNI
```

> **Read the safety property straight off the algebra:** both modules can be *permitted* **only when
> `MODE_UNI` = 1**, i.e. only when the switch's own aux pole says the armature is in the position
> that has **already put the two modules on different nodes**. When `MODE_UNI` = 0 the expression
> collapses **bit for bit** to a plain `SEL` / `¬SEL` gate, so pseudo-bipolar behaviour is unchanged.
> **`MODE_CMD` does not exist and appears nowhere** (MODE-12): firmware cannot command the mode.

> **And the part that matters MORE than the algebra:** `MODE_UNI` is **not** what makes the forbidden
> state physically possible. Even with `MODE_UNI` **falsely stuck at 1** while the switch is in
> pseudo-bipolar, `S6` and `S7` are open, so `K_S` still routes `+VIN` and coil power **exclusively**
> and only one HV relay can close. **There are two mode permissives in this design and they are
> different objects: a LOGIC one that relaxes `/ON`, and a POWER one (`S6`/`S7`) that relaxes coil
> and `+VIN` exclusivity. The forbidden state needs both to be wrong at once.**

**Downstream of the permissive:**

- `/ON_P`, `/ON_N` from an **open-drain** 74HCT03, pulled up by **2 × 10 kΩ to each module's OWN
  `+VIN`, within 5 mm of pin 4** (ARCH-17) — so the pull-up **cannot outlive the module's supply**.
- **Cold-switch latches** (74HCT75, transparent when LE high):
  `REL_EN_P = LATCH(D = PERMIT_P, LE = COLD_A)`, `REL_EN_N = LATCH(D = PERMIT_N, LE = COLD_A·COLD_B)`,
  `KS_SEL = LATCH(D = SEL, LE = COLD_A · COLD_B · nARM)`.
  **Separating the module enable from the relay enable, and latching only the latter, is what gives
  cold MAKE and cold BREAK with no circularity** — the thing that makes the node cold (removing
  `+VIN`, raising `/ON`) is **not** the thing that is latched. Turning an output *off* leaves its
  relay **closed** until the node is cold, which puts the module-side and output-side bleeds in
  parallel: **the "stuck closed" interval is helping.**
- **`Q_COIL`**, the coil-rail load switch (correction C-1), gated by `EN_HB · INTLK · MODE_VALID`
  (`U43`) — **deliberately NOT the full `ARM`.** Reason: a coil rail that dropped on every `nOVP` or
  disarm event would force a **hot break on every trip**. `EN_HB`, `INTLK` and `MODE_VALID` are
  precisely the three inputs for which *"drop the coils immediately"* is the right answer. **The
  design rule: guarantee cold MAKE absolutely; tolerate a hot BREAK on emergency paths only, never
  on a normal-operation path.** C-1 also makes **both-coils-off reachable**, which is what lets the
  weld self-test execute at all.
- **Heartbeat (C-3):** `GPIO_HB` → **two 22 nF coupling caps IN SERIES** (a single shorted capacitor
  still leaves one, so a static GPIO level cannot hold `EN_HB`) → diode pump → 100 nF reservoir with
  **2 × 2 MΩ** to GND → Schmitt. τ = 100 ms ⇒ `EN_HB` falls **≈79 ms** after the toggle stops.
  `EN_HB = pump_ok · WDT_OK`, and `WDT_OK` comes from a **windowed** watchdog that faults on kicks
  that are **too fast** as well as too slow — which is what catches a free-running peripheral.
  **`GPIO_HB` must be toggled ONLY from the main loop**, never from LEDC/RMT/a timer/an ISR: a
  peripheral free-runs straight through the application hang the pump exists to detect.
- **`SETTLE`** is a 74HCT123 monostable driven by an RC-XOR **edge detector** on `SEL`, `MODE_A` and
  `MODE_B`. It is taken from **~Q**: HIGH at rest, LOW for `T_dwell` after any edge, **and LOW when
  unpowered** — all three fail-safe.
- **`INTLK`** is key + lid + mode guard **in series**, closed = 1.
- **Safe-state pull-downs on every ESP32-sourced interlock line, duplicated** (C-4 / ARCH-18):
  `ARM_CMD`, `SEL`, `EN_P`, `EN_N`, `MODE_A`, `MODE_B`, `INTLK`, `HB_RESERVOIR`, `VSET_P`, `VSET_N`,
  and every FET gate. **An open pull element restores the module's documented unsafe default.**

**Ask yourself:** *why are the mode aux contacts wired to +3.3 V and not to ground?* (A **broken
wire** — the likelier panel-harness fault — then reads **0**; both broken reads `(0,0)` = "no valid
mode" = `ARM` = 0. Wiring closed-to-ground with pull-ups would make a broken wire read *"in this
mode"*, which is the wrong direction.) *Why decode BOTH modes positively instead of `PB = ¬UNI`?*
(One extra contact and one XOR cover the intermediate position, a shorted aux **and** a broken aux
**simultaneously.**) *Is seven terms into one 8-input NAND right, or does it hide which term
tripped?* (It does hide it — the readback shift register is what recovers observability.)
⚠ **And note the documentation defect:** `COMBINER_DESIGN` §6.1's table calls `MODE_UNI` *"`SW1` pole
`S5`"*. **It is not** — `S5` (`SW1E`) drives `MODE_B`, and `MODE_UNI` is a **gate output**. That
error makes §7.5(b)'s fault count read 3 when it is **2**.

---

### Block 10 — Controller and readback (`§9.10`)

**Intent.** ESP32-S3-WROOM-1 (`U50`). **No interlock signal sits on a strapping pin (GPIO0/3/45/46)
or on the USB pins (19/20)** — that is an *asserted, checked* property, not a review item.
`W5500` and `CP2102N` are **out of scope for spec_version 1** (deviation **D-5**): their 48- and
29-pin reference designs contain no HV safety content and could only have been authored **from
recall**, which is exactly the highest-consequence/lowest-feedback work this project's rules forbid.
Their board-boundary nets are real and are brought to two headers.

**Status readback goes through two cascaded 74LVC165 shift registers** rather than straight into
GPIOs, with **two deliberate pattern bits** so that a stuck/absent register is distinguishable from
a plausible-looking all-zeros read. The ESP32 sees `MODE_A_BUF` / `MODE_B_BUF` through 0 Ω links —
**read-only.** Nothing the ESP32 drives reaches `MODE_A`, `MODE_B` or `MODE_VALID`; there is an
assertion for it (**and §7 records that the assertion has three bypasses**).

⚠ **Deviation D-4:** `CONTROLLER_AND_POWER` §2.3 puts `MODE_A_RB` on GPIO33 and `MODE_B_RB` on
GPIO34. **The ESP32-S3-WROOM-1 symbol in KiCad 10.0.3 has no module pin for IO33 or IO34**, so the
map was shifted (→ IO35/36/37/38/47/48). **That claim rests on the KiCad symbol, not a datasheet
read. Confirm it at G1, before layout.**

---

### Block 11 — Panel indication (`§9.11`)

**Intent.** Two indicators are **deliberately not on a GPIO** — an HV-live lamp driven by hardware
cannot lie about HV being live when firmware has hung. Mode indication is derived from the switch's
own contacts.

**Ask yourself:** *does the panel legend state that mode change is a **powered-down, cables-off**
operation?* (MODE-17 / SW-R7 — and per §7 that procedure is now **load-bearing**, not advisory.)

---

### Block 12 — DNP and mechanical-only parts (`§9.12`)

Four deliberate non-fits, each recorded **with a falsifiable condition for fitting it**:
(i) the CP2102N **auto-reset jumper, SHIPPED REMOVED**; (ii) the **switched dump, NOT FITTED** — the
condition is `C_module` measuring high (**MEASURABLE-NOW**, `BENCH_MEASUREMENTS.md` M2); (iii) the
`VSET` pull-down contingency; (iv) mounting holes — mechanically real, electrically not absent.

**Ask yourself:** *is "not fitted, with a stated condition under which it would be fitted" the right
call for the dump, or would you rather pay 18 cm² and $90 per node now than respin?*

---

## 4. How to review `docs/PIN_MAPS.md`

**115 kB, 441 parts. Do not read it linearly.** It is a **generated file** (from `board_spec.py` +
the symbol libraries on disk) — **never hand-edit it; fix `gen_pin_maps.py` and regenerate.**

### 4.1 What the machine already checked, and what it structurally cannot

`board_spec.py` re-parses each `.kicad_sym` **on every run** and asserts **set equality both ways**
between the pin numbers in the hand-authored map and the pin numbers the symbol actually has: no
invented pin, no forgotten pin, every deliberately-unconnected pad explicitly declared. It also
cross-checks **pin NAMES** as an independent axis (this is what catches a `VSET`/`VMON` swap).

**It cannot see whether the symbol matches the physical part.** `kicad-cli` will happily load a
library with `VSET` and `VMON` swapped. **That is your job, and only yours.**

**It also never opens a `.kicad_mod`** (`grep -c kicad_mod board_spec.py` = **0**). Symbol↔footprint
pad-set agreement is **unverified by this repo** for every part except the iseg module.

### 4.2 The order to read it in

1. **§1 TIER C first** — 44 components, 17 part classes. **A borrowed pinout is a CLAIM, NOT A READ.**
2. **§2 TIER A next** — one part, two symbols, and it is the **1 kV source**. If `U1`/`U2` are wrong,
   everything downstream is wrong.
3. **§3 TIER B last**, and it can be **sampled** rather than read exhaustively — those maps came from
   a KiCad stock symbol which is itself a transcription. Second-hand, but *checkable*: the file is on
   disk and `board_spec.py` re-reads it every run.

### 4.3 ⛔ THE 44 TIER-C BORROWED PINOUTS — the highest-risk subset, listed explicitly

**Not one of these has been checked against a datasheet by anyone.** Each row is the assertion
*"part X shares part Y's pinout"*, made by an agent, never verified.

| Part class | n | Refs | Symbol borrowed | Why it matters |
|---|--:|---|---|---|
| **`RELAY_HV`** | **4** | **`K1`, `K2`**, `K3`, `K4` | `Relay:Relay_SPDT` (A1/A2 coil; 11 COM, 12 NC, 14 NO) | ⛔ **HIGHEST RISK IN THE DOCUMENT.** `K1`/`K2` are the HV routing relays — **the invariant is about these two parts.** The Pickering datasheet was read for *ratings* in a prior session but **its pin numbering was never transcribed.** The **`/5D` suffix means an INTERNAL COIL DIODE, so COIL POLARITY IS MANDATORY** — and reversed coil polarity is one of the nine assertions no file can check. **The named footprint `Relay_THT:Relay_Pickering_Series67` DOES NOT EXIST in any library.** |
| **`RELAY_LV`** | 1 | **`KS`** | `Relay:Relay_DPDT` (11/12/14, 21/22/24) | ⛔ **`K_S` IS THE SINGLE ARMATURE.** *"TQ2SA-5V pin numbering NOT read."* If pole A and pole B are swapped, or NO/NC inverted, **the exclusivity that carries the theorem is wired wrong** and nothing in this repo would notice. Its footprint `Relay_THT:Relay_DPDT_Panasonic_TQ` **does not exist** either. |
| **`TPS22918`** | 4 | `U14`, `U15`, `U16`, `U17` | `TPS22917DBV` SOT-23-6 | ⛔ **These are the module `+VIN` interlock elements (ARCH-19 / SA-6) — the PRIMARY disable.** The claim *"TPS22918 shares the TPS22917 pinout"* is **NOT VERIFIED.** A swapped `ON`/`VIN` here defeats the primary disable. |
| **`TLV3202`** | 7 | `UCC_A`, `UCC_B`, `UBR`, `U5`, `U7`, `U8`, `U9` | `Comparator:LM393` | ⛔ Two COLD windows, the clamp-rail window, the `VSET` over-range detector and **both hardware OVP comparators**. The design **requires push-pull outputs, never open-drain** — and **LM393 IS open-drain**, so the borrowed symbol is from a part with the *wrong output structure*. Confirm the real TLV3202 pinout **and** that the fitted part is push-pull. |
| **`TPS3701`** | 3 | `U40`, `U41`, `U42` | `Power_Supervisor:TPS3702` SOT-23-6 | The three rail supervisors whose wire-AND is `RAIL_OK`, an `ARM` term. |
| **`OPA2192`** | 5 | `UMB_A`, `UMB_B`, **`UGD`**, `UVM`, `U3` | `Amplifier_Operational:OPA2196xD` SOIC-8 | Monitor buffers, **both guard drivers in ONE package (`UGD`)**, the `VMON` buffer, and **`U3` the mandatory rail-force amp**. |
| **`OPA_CLAMP`** | 1 | **`U4`** | `Amplifier_Operational:OPA2196xD` SOIC-8 | ⛔ **THIS IS THE `VSET` CLAMP — a primary safety element — and its value field literally reads `**UNSELECTED RRIO dual**`.** No part number exists (O-D: the 250 µA output current at a 2.5 V supply disqualifies most precision amps). |
| **`SHV`** | 2 | `J2`, `J3` | `Connector:Conn_Coaxial` (1 = centre, 2 = shell) | The two 1 kV output bulkheads. `fp = ''` — chassis parts, wired to the board. |
| **`74HCT08`** | 3 | **`U33`**, `U38`, `U43` | `74xx:74LS08` | ⛔ `U33` **is the mode-aware permissive** (`PERMIT_P`/`PERMIT_N`); `U43` **is the C-1 coil-rail gate**. |
| **`74HCT30`** | 1 | **`U30`** | `74xx:74LS30` | ⛔ **The 8-input NAND that IS the `ARM` chain.** |
| **`74HCT86`** | 1 | **`U32`** | `74xx:74HC86` | ⛔ **`MODE_VALID` = `MODE_A` XOR `MODE_B`** — the mode decode. |
| **`74HCT03`** | 1 | **`U36`** | `74xx:74LS03` | ⛔ **Open-drain** `/ON_P` / `/ON_N` drivers. The borrowed symbol must actually be the open-drain variant, not the push-pull `'08`. |
| **`74HCT32`** | 1 | `U34` | `74xx:74LS32` | the `MODE_UNI + SEL` OR terms |
| **`74HCT14`** | 1 | `U31` | `74xx:74HC14` | inverters incl. `nARM`, `nMODE_A`, `nSEL` |
| **`74HCT75`** | 2 | `U39`, `U44` | `74xx:74LS75` | ⛔ **the cold-switch latches** — `REL_EN_P/N` and `KS_SEL` |
| **`74LVC14`** | 5 | `U47`, `U48`, `U49`, `U51`, `U52` | `74xx:74HC14` | 3.3 V-side buffers |
| **`74LVC165`** | 2 | `U45`, `U46` | `74xx:74HC165` | the status readback chain |

**Note the `74xx` borrows are doubly indirect:** `74HCT30` borrows the **`74LS30`** symbol,
`74HCT08` borrows `74LS08`, `74HCT03` borrows `74LS03`, `74HCT75` borrows `74LS75`. Pinouts are
generally common across families **but that is exactly the kind of "generally true" the pin-map gate
exists to stop.** Check each against a real 74HCT datasheet.

### 4.4 The procedure

For **each** TIER-C row: open a **real datasheet** for the **actual part named in the `val` field**
(not the borrowed symbol's part), and for **every pin** confirm number → function. **Tick it on
paper.** Where it matches, mark the row `[verified-artifact, <datasheet>, <date>]`; where it does
not, **fix `board_spec.py` and regenerate `PIN_MAPS.md`** — never edit the generated file.

Then **§2, TIER A**, the iseg module — the pin map that survived 3/3 skeptics. **Read it anyway.**
It is the one part whose transcription being wrong is unrecoverable, and `docs/BENCH_MEASUREMENTS.md`
M5 gives you a physical cross-check that costs twenty minutes.

Then **sample §3, TIER B** — ten rows chosen at random is a genuine test; reading all 380 is not a
better one.

### 4.5 ⛔ Eleven footprints named in the netlist DO NOT EXIST

`Relay_THT:Relay_Pickering_Series67` (`K1`,`K2`,`K3`,`K4`) ·
`Relay_THT:Relay_DPDT_Panasonic_TQ` (`KS`) · `Inductor_SMD:L_Bourns_SRP7028A` (`L1`,`L2`) ·
`Package_SO:MSOP-12-1EP…` (`U12`) · `Package_SO:VSSOP-10_3x3mm…` (`UADCA`,`UADCB`) ·
the CK KMR2 switch (`SWB`).

**`PIN_MAPS.md` flags "DOES NOT EXIST" for `K1`–`K4` only.** The other seven are silent.
**G1 must commission these footprints** (with the same generator + mutation-test discipline the iseg
footprint got) **and add a symbol↔footprint pad-set cross-check to `board_spec.py`.**

---

## 5. The questions the reviewer should try to answer

Phrase each as *"what would make this wrong?"* — you are trying to **break** the design, not approve
it. A question you cannot answer is a finding.

### 5.1 On the invariant
1. **The forbidden state is reachable through ONE welded HV reed. Do you accept detection instead of
   prevention?** G0 **Q6 was never answered.** If prevention is ever required, **this topology dies —
   and so does every other candidate** (TOPO-10). *Answer it now, in writing.*
2. `board_spec.py`'s assertion (a) **never evaluates pseudo-bipolar.** Do you accept a machine proof
   that covers one of two modes, or must it be repaired before you sign?
3. `S6` and `S7` are on **adjacent pins 7/8 of one 8-way header `J6`**. Does "one armature" survive a
   solder bridge, a crushed cable, or a connector inserted one pin over? Should the four LV poles be
   split across **two** connectors, or keyed?
4. In unipolar, `HV_X` sits at −1000 V while `HV_OUT_A` sits at +1000 V, **as normal steady state**.
   Are you comfortable that a **`[unverified-primary]` 15.0 mm** rule is what stands between them?

### 5.2 On the mode element
5. **No part is specified.** Do you take §3.7's **link block** as the baseline (stronger on timing,
   weaker on convenience), or do you fund a search for a switch with a published **contact-to-contact
   DC working voltage ≥1000 V**? *There is no third option that is honest.*
6. If you take the link block: **it has no armature.** `CONTROLLER_AND_POWER` §9.2 says this loses
   the by-construction agreement between HV routing and interlock permissive — *"the entire reason
   G0-A5 is stronger than G0-A4."* **Do you accept that weakening, in writing?**
7. The SAFE-detent timing argument does not meet its own requirement. **Is "powered down, cables off"
   an acceptable load-bearing procedural control on an instrument two people will share?**

### 5.3 On the set-point path
8. The clamp bounds output to ≤ Vnom **only through a firmware code clamp**, and G0-A3 put firmware
   inside the untrusted boundary. **Is a hardware ceiling of ~+1 % acceptable, or does the design owe
   a hardware element that bounds it to ≤100 %?**
9. A `VSET`-to-+3V3 solder bridge reaches **1320 V** and is prevented by **a layout keep-out**.
   Is a keep-out a safety element you are willing to sign?
10. One modelled fault reaches **2012 V — worse than no clamp at all.** Its only cover has an
    **undetectable** stuck-high mode. Accept, or add a layer?

### 5.4 On the monitors
11. Both guard drivers are in **one package**. Both offset legs share **one reference**. Is that
    "independent" in the sense invariant (c) means?
12. **One open monitor element blinds the monitor AND pushes the OVP trip to ≈2100 V.** Should the
    OVP have its own divider, i.e. a **fourth** HV string per output?
13. `MONITOR_AND_BLEED` §5.4's 2-of-2 AND is **not built** because it would break the frozen SA-8.
    **Reword SA-8 and build it, or accept that §10 rows 10 and 12 are unmitigated?**

### 5.5 On values and process
14. **D-1: 20 MΩ on the NC contact, or 40 MΩ upstream?** The two live documents disagree and this
    **changes the netlist**.
15. **D-4: the ESP32 GPIO remap rests on a KiCad symbol, not a datasheet.** Confirm or reject.
16. Four different standing-load numbers exist (11.00 / 11.40 / 12.40 / 12.60 %). **Which one gets
    asserted?**
17. `QK1`/`QK2`: the design document says 2N7002 (~115 mA) for a **125 mA** coil. `board_spec.py`
    calls it under-rated and demands ≥300 mA. **Confirm.**
18. `TLV3202` borrows the **LM393** symbol, but LM393 is **open-drain** and this design **requires
    push-pull**. Is that a symbol borrow or a **part** error?

---

## 6. What this gate does NOT cover

**Signing G1 freezes values, interfaces, netlist intent and pin maps. It freezes NOTHING below.**

### 6.1 Still `[unverified-primary]` — no primary standard has been read
- **Every clearance and creepage number**: `C_HV` 7.5 mm, `C_HV_PAIR` 15.0 mm and the two new
  pairwise rules, the 2.50 mm pad-gap screen, and the fab-tier consequence.
- **Every touch-safety threshold**: 60 V / 5 s, 350 mJ, 50 µC. **The entire Phase-7 safety argument
  rests on three numbers with no source.**
- Session 1's claimed internal cross-check was an **algebraic tautology** and was **deleted with no
  replacement invented**. **There is currently NO evidence the clearance constants are the right
  constants.** A human must read a primary copy. **This is the highest single risk in the project.**

### 6.2 Still MEASURABLE-NOW — the modules are in hand and nothing has been measured
`VSET` step response · HV output capacitance (**the two live documents disagree by 10×**) · internal
bleeder resistance · turn-on time from `+VIN` · module `VSET` pull-up tolerance (O-A, the criterion
**breaks at 7.83 kΩ**) · divider `k_VCR` (O-M5) · guard-ring improvement factor (O-M6, `[ASSUMED]`
100×) · **the physical module against our land pattern** (M5). **Procedure: `docs/BENCH_MEASUREMENTS.md`.
One afternoon.**

### 6.3 Still `[unverified-MPN]` — not one part number has been checked against a live distributor page
**Every MPN in every document**, including: the Pickering `67-1-C-5/5D` (**unpriced**), the mode
switch (**no MPN at all**), every HV passive (~60 of them; four agents found **0-stock / obsolete /
13-week lead** across the class), `U4` the clamp amplifier (**unselected**), the windowed watchdog,
and every 74HCT part. **Precedents from this project:** a distributor deep-link returned a complete,
confident spec report **for an entirely different product** with nothing signalling the mismatch; a
recalled MPN **did not exist** from the named manufacturer; the best-documented candidate was stamped
**Not For New Designs**. **No iseg quote, lead time or MOQ exists** — the dominant BOM line.

### 6.4 ⛔ G0 questions never answered — the design is proceeding on documented defaults
- **Q3 — the output specification.** Maximum load current, load capacitance, required ripple.
  **Never answered.** The design proceeds on `C_load ≤ 10 nF` / ≤10 m cable as a *declared* interface
  constraint that **nothing physically enforces**, and on the module's own 0.75 mA limit.
- **Q5 — the safety envelope.** **Never answered.** Proceeding on `[recalled]` 60 V / 5 s / 350 mJ.
- **Q6 — weld: detection versus prevention.** **Never answered.** The design **detects** (power-up
  self-tests plus continuous branch monitoring) and **cannot prevent**. **If prevention is required,
  the topology study reopens and every candidate fails.**

### 6.5 Not covered by any gate yet
- **Nothing has been simulated, breadboarded, energised or built.** No relay energised, no switch
  scoped, no contact-timing figure observed.
- **The nine non-structurally-expressible assertions**, four of which are safety properties: SA-9
  placement, graded string spacing, **HCT vs HC**, push-pull comparators, **relay coil polarity**
  (mandatory — internal diode), **K1/K2 orthogonal mounting** (reed sensitivity is strongly axial;
  free at layout, **impossible to add later**), **weld detection**, discharge **TIME**, SA-12 dump
  sizing.
- **`docs/studies/combiner_design_numbers.py` is arithmetic, not verification** — it has no
  independent source of truth to check itself against and **is not mutation-tested**. Its outputs
  are quoted throughout `COMBINER_DESIGN.md`. **Promote it into `hardware/hvctl/` with an acceptance
  check and a mutation test before any of its outputs are frozen.** That is the project standard and
  it is not met.
- **`MONITOR_AND_BLEED.md`'s new arithmetic ran in two throwaway scripts that were not retained.**
  Treat those numbers as computed-and-checked-once, **not probe-grade**.
- The **magnetic environment** (R-6) — reed relays, and no solid-state escape route.
- **PART-27**, an OFF module's reverse-voltage tolerance on pin 6 — **unpublished, ask iseg.**
- **NUM-18 / ARCH-14**: conformal coating is **assumed absent** for clearance and **mandated present**
  for divider surface leakage. **Still contradictory, still unresolved**, and this design adds two
  more guard-ringed regions so the tension is worse. **Resolve before layout.**
- `iseg_APS_THT.kicad_mod` still carries a **5.00 mm per-pad clearance override on pad 6**, silently
  replacing the 7.5 mm netclass value. **Fix the generator, not the artifact.**

---

## 7. The consolidated action list — what must happen before G1 can be signed

Ordered by consequence.

| # | Action | Owner | Blocks |
|---|---|---|---|
| **A1** | **Answer G0 Q6 in writing: weld detection or prevention?** If prevention, the topology reopens. | human | everything |
| **A2** | **Decide the mode element**: §3.7 link block as baseline, or fund a search for a switch with a published **contact-to-contact DC working ≥1000 V**. **Do not fit an Electroswitch D4 or any part rated 28 VDC.** | human | procurement, layout |
| **A3** | **Read a primary copy of IPC-2221B Table 6-1 and IEC 60664-1/62368-1.** Re-derive `C_HV`, `C_HV_PAIR` and the touch thresholds. | human | layout, DRC rules |
| **A4** | **Repair `assert_a_no_shared_output_node()`** — drop the `pp/pn` filter, assert galvanic reachability — **or** state in writing that assertion (a) covers unipolar only. | session, then gate | the invariant's proof |
| **A5** | **Repair `assert_a_mode_origin()`'s three bypasses** (D-8) and `hv_energisable_nets()`'s hand-list (D-9a). | session, then gate | firmware-cannot-reach-mode |
| **A6** | **Fix `COMBINER_DESIGN` §1.3** so it agrees with its own §7.5/F-15, and **§6.1** so `MODE_UNI` is named as a gate output. | session | review honesty |
| **A7** | **Restate `SETPOINT_PATH` §2.4/§14 over-range as +1.07 %** (worst-case Vref) and stop calling the clamp sufficient. | session | the safety case |
| **A8** | **Strike or rewrite `CONTROLLER_AND_POWER` §9.2** (2-position switch) before anyone procures from it. | session | procurement |
| **A9** | **Adjudicate D-1** (bleed 20 MΩ-on-NC vs 40 MΩ-upstream) and **D-4** (GPIO remap). Both change the netlist. | human | the netlist |
| **A10** | **Do `docs/BENCH_MEASUREMENTS.md` M1–M5.** One afternoon. **M5 needs no HV.** | human | Phase 6 gate |
| **A11** | **Commission the 11 missing footprints** and add a symbol↔footprint pad-set cross-check. | session | layout |
| **A12** | **Check all 44 TIER-C pinouts against real datasheets** (§4.3). | human | everything |
| **A13** | **Order long-lead parts** — relays, ~60 HV passives, the modules' spares. R-7: 0-stock / obsolete / 13-week leads were found across the HV-passive class. **Order at G1, not at fab.** | human | schedule |
| **A14** | **Promote `combiner_design_numbers.py` into `hardware/hvctl/` with an acceptance check and a mutation test.** | session | freezing its outputs |

---

## 8. The signature block

Sign only what you have actually checked. **Partial signature is the expected outcome of this gate.**

```
  [ ] §1.1  Module values and pin map              reviewed / accepted        _______  date ______
  [ ] §1.3  HV network values                      reviewed / accepted        _______  date ______
        ( D-1 adjudicated:  20 MOhm on NC  /  40 MOhm upstream  -- circle one )
  [ ] §1.4  Set-point and monitor values           reviewed / accepted        _______  date ______
        ( over-range frozen at:  +0.061 %  /  +1.07 %  -- circle one )
  [ ] §1.5  Timing and interface limits            reviewed / accepted        _______  date ______
  [ ] §3    NETLIST INTENT, all 12 blocks          reviewed / accepted        _______  date ______
  [ ] §4    PIN MAPS -- 44 TIER-C rows checked
            against real datasheets                reviewed / accepted        _______  date ______
  [ ] §5    Questions 1-18 answered in writing                                _______  date ______
  [ ] §7    Actions A1-A14 dispositioned                                      _______  date ______

  NOT FROZEN BY THIS SIGNATURE, and I have read section 6:
      every clearance and touch-safety constant   [unverified-primary]
      every part number                           [unverified-MPN]
      eight module/board parameters               MEASURABLE-NOW
      G0 Q3, Q5, Q6                               NEVER ANSWERED, proceeding on defaults

                                        signed ______________________  date ______
```
