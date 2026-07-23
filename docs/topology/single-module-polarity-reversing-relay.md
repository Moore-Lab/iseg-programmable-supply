<!-- SESSION-2 BANNER -- do not edit the body of this file. -->
> ## ⚠ HISTORICAL DOCUMENT — superseded by G0 (signed off 2026-07-23)
>
> This is a **pre-G0 candidate study**, preserved as the evidence behind the combiner decision.
> It is **not** a live design document and its numbers are **not** the project's numbers.
>
> **G0-A1 selected HV RELAY CHANGEOVER.** The series-stack/driven-midpoint, diode-OR and
> single-module-reversing topologies are **REJECTED and must not be revived**.
> **G0-A4** additionally made the instrument switchable between a single *pseudo-bipolar*
> output and *two independent unipolar* outputs that **may both be energised at once**, so
> ±1000 V now coexist on the board as a **normal steady-state condition**.
>
> ### ⚡ The clearance number in this file is WRONG and is superseded
>
> `STATUS.md` §1.2 finding 7: **four documents in this repo carried four mutually
> incompatible IPC-2221 numbers, three of them more permissive than the probe's.**
> This file's §"Creepage / clearance" claims *"IPC-2221B, external uncoated component leads/terminations, > 500 V: 2.5 mm at 500 V plus 0.00250 mm/V above ⇒ at 1000 V, **3.75 mm minimum**"*. It takes **column B2's base** and **column B1's slope**. On the transcription used by the probe, B2 at 1000 V is **5.000 mm** bare and **7.5 mm** recommended — so this file is **2× permissive**.
>
> **The single live source for every clearance/creepage number is
> `docs/NUMBERS_PROBE.md`, generated from `hardware/hvctl/numbers_probe.py`.**
> At the frozen part (AP010504, Vnom = 1000 V) the live values are
> **7.5 mm** HV-to-anything and **15.0 mm** HV_POS↔HV_NEG (and HV_OUT_A↔HV_OUT_B),
> every one of them tagged **`[unverified-primary]`** pending a human reading a primary copy
> of IPC-2221B Table 6-1. Do not quote this file's figure anywhere.

# Combiner topology study — single module + output polarity-reversing relay

**Status:** Phase-1 candidate analysis, G0. One of N parallel topology studies.
**Candidate:** ONE unipolar iseg APS module + an HV changeover relay pair that reverses which
terminal of the module is grounded.
**Role in the study:** deliberate control case. The brief's requirement 1 states *two* modules of
opposite polarity. This candidate questions that premise. The deliverable is therefore explicitly
"what are we giving up", and a well-argued rejection is a valid result.

**Bottom line up front: REJECT for this brief. Score 3/10.**
Not because it cannot be built — sub-variant B below is a legitimate, standard HV-instrumentation
architecture — but because (i) the cost saving it exists to deliver evaporates once the isolation
barrier is priced, (ii) it makes wrong-polarity output a *single-MOSFET* fault where the two-module
scheme makes it a two-fault event, (iii) it puts the module's metal case, which iseg bond to GND,
at up to 1 kV, which is undocumented and unwarrantable operation, and (iv) it cannot do through-zero.

---

## 0. Evidence basis

Everything cited as *iseg* below was re-extracted from the PDF **this session** with
`fitz` under `PY_KICAD`, not recalled:

- `"C:/Program Files/KiCad/10.0/bin/python.exe"` + `fitz`, full text of all 10 pages of
  `references/iseg_manual_APS_en.pdf` → `[verified-artifact]`
- Page 9 (`Figure 2: Control principle`) is **vector art with no extractable text**. Rendered at
  `fitz.Matrix(18,18)`, `clip=fitz.Rect(140,360,310,520)` and read visually → `[verified-artifact]`.
  **This figure had not previously been mined and it contains three numbers that change the
  analysis.** See §1.
- Pickering Series 67/68 datasheet (Issue 1.4, Apr 2022): fetched as a PDF, extracted locally with
  `fitz` → `[verified-artifact]`
- DigiKey product pages read live this session for two parts → `[verified-distributor]`
- Pickering distributor pages (Farnell) **timed out twice**; `pickeringrelay.com` returns HTTP 403 to
  the fetcher. Relay *prices* below are therefore `[unverified-MPN]`. Relay *specifications* are
  `[verified-artifact]` from the datasheet PDF I extracted.

Citation for the module throughout: *iseg APS series technical documentation v2.5, 2024-08-20*.

---

## 1. New ground truth extracted from Figure 2 (control principle)

This was previously an unread figure. Reading it changes the timing analysis and adds two
failure modes. All `[verified-artifact]`.

```
                 (inside the APS, dashed boundary)
   VMON o──[20k]──┬──────────────┐
                  │              │
                (10k)          (REF)  2.5 V (0.5 W family) / 5 V (1 W family)
                  │              │
   VSET o─────────┴──[100k]──┬───┴── GND
                             │
                          ┌──┴──┐
   /ON  o───────────────► SW    ═╪═ 1 µF
                          └──┬──┘  │
                            GND   GND
```

Three consequences:

1. **`VMON` has a 20 kΩ series resistor inside the module.** Treat `VMON` as a 20 kΩ source.
   Loading it with a 1 MΩ ADC input divider gives a −2 % reading error — *twice* the module's own
   1 %·Vnom monitor accuracy spec. `VMON` must be buffered by a low-bias op amp, or read by an ADC
   with sub-nA input current and no resistive divider. Topology-independent, easy to get wrong.
2. **The 10 kΩ pull-up on `VSET` goes to `REF`.** This confirms, from the schematic and not just
   from the Rset formula, that **an open `VSET` node commands full-scale output.**
3. **`100 kΩ × 1 µF = 100 ms` is the module's internal set-point time constant**, and `/ON` HIGH
   *shorts that 1 µF to ground*. So:
   - enable → output reaches 95 % in 3τ = **300 ms**, 99 % in 4.6τ = **460 ms**;
   - `/ON` HIGH collapses the *demand* in microseconds, but `/ON` is **not an output crowbar** —
     the HV node itself then decays only through its own internal loading, the external load, and
     whatever bleed we provide.

**What the manual does NOT give, anywhere in 10 pages:** the module's HV output capacitance, any
output rise/fall time, and any isolation rating between GND/case and the outside world. Every
discharge-time number in §5 is parametric in an unmeasured C. That is a mandatory G1 bench
measurement, in *any* topology.

Also re-confirmed:
- `Case is connected to GND` (Table 4 note) — central to this study.
- `Output voltage is internally not limited! At Vset > Vref → Vout > Vnom is possible!` (Table 1).
- `/ON: LOW or n.c. → HV ON`, `5.5 V ≥ V/ON > 2.5 V (HIGH) → HV OFF` (Table 1). Note the **5.5 V
  absolute ceiling** on `/ON` — on the 12 V family you must *not* pull `/ON` up to +VIN.
- `Iout is limited to approx. 1.5 · Inom` (Table 2, Note 1).
- `Overload and short circuit protected` (Table 1).
- Table 1 specifies **`Current monitor accuracy 1 % · Inom`** but **Table 4 lists no current-monitor
  pin** on this 7-pin part. **Flagged, not resolved.** Either a copy-paste from a larger iseg family
  or an undocumented function. Ask iseg. Do not design against it.

---

## 2. The two sub-variants, and why only one survives

The phrase "polarity-reversing relay" hides a fork that decides the whole thing: *which side of the
module do you reverse?*

### Variant A — reverse the load (module GND stays at board ground)

```
   APS pin 6 (HV) ──┬── K1.COM       K1.NC ── OUT_B
                    │                K1.NO ── OUT_A
   board GND ───────┼── K2.COM       K2.NC ── OUT_A
                    │                K2.NO ── OUT_B
   load connects between OUT_A and OUT_B
```
Coil off: `OUT_A = 0`, `OUT_B = +V` ⇒ V(A→B) = −V. Coil on: the mirror ⇒ +V.

**Dead on arrival.** Neither output terminal is a permanent ground. The load must be fully floating.
The moment the load's return is chassis-bonded — which it is for every detector, every SHV or BNC
cable (grounded shell), every chassis-referenced electrometer — one of the two polarity states
connects the module's HV pin to chassis. That is a short. The module survives (short-circuit
protected) and the output is simply 0 V in that state, so it is not destructive; it is merely
useless. You also cannot use SHV at all, and you lose cable shielding.

This is exactly the "floating load only" limitation the task named. It is fatal for detector
biasing. **Variant A is eliminated here and not analysed further.**

Note both poles need full standoff even in Variant A: in each state the *open* contact of each pole
faces the other terminal, so both gaps see Vnom.

### Variant B — float the module (load return is permanently chassis)

This is the only version that competes, and it is a real architecture: floating source + reversing
switch, as used in SMUs and electrometers.

```
  ┌───────────── FLOATING ISLAND, reference = MOD_GND ──────────────┐
  │                                                                 │
  │   iso 5 V ──┬── APS pin1 (+VIN) ── 22 µF ── MOD_GND             │
  │             ├── 10k ── APS pin4 (/ON)  ◄── digital isolator     │
  │             │          (pull-up: open ⇒ HIGH ⇒ HV OFF)          │
  │   VSET buf ─┴── APS pin2 (VSET) ── 200 Ω ── MOD_GND             │
  │             (buffer rail = Vref, so it CANNOT exceed Vref)      │
  │   VMON buf ──── APS pin5 (VMON)   [source Z = 20 k, see §1]     │
  │                                                                 │
  │   APS pin6 (HV) ──[10k]── K1.COM     APS pins 3,7 + CASE = MOD_GND
  └──────────────────────┬──────────────────────────┬───────────────┘
                         │                          │
                    K1.NC ── CHASSIS           K2.COM = MOD_GND
                    K1.NO ── OUT_HOT           K2.NC ── OUT_HOT
                                               K2.NO ── CHASSIS

   K3.COM ── OUT_HOT ,  K3.NC ──[10k]── CHASSIS      (fail-safe crowbar)
   R_bleed  100 MΩ  OUT_HOT → CHASSIS                (unconditional)
   R_ref    100 MΩ  MOD_GND → CHASSIS                (defines float node mid-transit)
   Divider  1 GΩ : 1 MΩ  OUT_HOT → CHASSIS → offset amp → bipolar ADC   (invariant c)

   OUT_RTN is permanently CHASSIS.  Load may be grounded.  SHV works.
```

K1/K2 coils in parallel on one low-side driver Q1. K3 on its own driver Q3.

- **De-energized (NC): `HV→CHASSIS`, `MOD_GND→OUT_HOT` ⇒ `OUT_HOT = −V`.** Negative is the default
  state. (The module makes +V from HV to its own GND; hold HV at 0 and its GND sits at −V.)
- **Energized (NO): `HV→OUT_HOT`, `MOD_GND→CHASSIS` ⇒ `OUT_HOT = +V`.**

Everything below concerns Variant B.

---

## 3. The relay — and the finding that breaks the safety argument

The whole safety appeal of "one DPDT relay" is the **single armature**: one moving part, mechanically
incapable of being in both positions, break-before-make guaranteed by physics. That is a much better
interlock story than any logic gate.

**It does not exist in this voltage class.**

Pickering Series 67/68 datasheet, Issue 1.4 Apr 2022, extracted this session `[verified-artifact]`:

> `1 Form A and 1 Form C configurations`

| Switch | Form | Power | Max switch I | Max carry I | Max switching V | Min stand-off V | Operate (incl. bounce) | Release |
|---|---|---|---|---|---|---|---|---|
| 1 | A | 50 W | 3 A | 3.5 A | 3500 | 5000 | 3 ms | 2 ms |
| 2 | A | 50 W | 3 A | 3.5 A | 7500 | 10000 | 3 ms | 2 ms |
| 4 (67 only) | A | 200 W | 3 A | 5 A | 6000 | 8000 | 6 ms | 2 ms |
| **5 (67 only)** | **C** | **100 W** | **3 A** | **3.2 A** | **2500** | **5000** | **6 ms** | **6 ms** |

Coils (Series 67): 5 V/40 Ω, 12 V/150 Ω, 24 V/600 Ω. Contact R ≤ 0.5 Ω initial (Form C).
Insulation resistance ≥ 1×10¹⁰ Ω switch-to-coil and across switch. Package 58.4 × 12.6 mm SIL,
13.58 g. Life > 1×10⁸ ops cold-switched or < 1 mA; ~1×10⁶ ops at up to 50 W.
Must-operate ≤ 3.75 V and must-release ≥ 0.5 V on the 5 V coil.

Standex's HV ranges (HE, HM, MHV, SHV) show only Form A and Form B at kV ratings in the distributor
listings I searched. **No vendor in this class offers 2 Form C.**

So a "DPDT HV relay" must be built from **two independent 1 Form C relays**. Consequences:

- Break-before-make is guaranteed **within** each relay (a Form C reed blade is physically one
  moving contact). Good.
- There is **no mechanical coordination between K1 and K2**. Worst-case skew ≈ 6 ms (operate max
  6 ms, release max 6 ms, plus unit-to-unit spread).
- **The single-armature argument is gone.** Whatever interlock claim this topology makes now rests
  on two separate mechanisms plus a shared coil driver — i.e. on a *common-cause* element (§7a).

### Contact stress arithmetic

- **Standoff margin:** 5000 V rating vs 1000 V max application = **5×**. Switching 2500 V vs 1000 V
  = **2.5×**. Comfortable, and unchanged if we pick the 200 V or 400 V module class.
- **Leakage across an open contact:** 1000 V / 1×10¹⁰ Ω = **100 nA**. Against the worst-case module
  (`AP010504x05`, Inom = 0.5 mA) that is **0.02 % of Inom**. Even at 10× degradation at high
  temperature (the datasheet warns IR falls with temperature) it is 0.2 %. **Negligible.** PCB
  surface leakage across 4 mm of FR-4 at 1 kV and 60 % RH will exceed it; add a guard ring.
- **Hot-switching is forbidden, and the datasheet says so:**
  > `Note1: ... At these high voltages, even stray capacitance can generate very high current
  > pulses, which can damage the contact plating causing welding of the reed switch.`

  Arithmetic: switching 1 kV into ~1 nF of module + cable + detector capacitance stores
  ½CV² = **0.5 mJ**, and the peak current is limited only by loop resistance — with 0.5 Ω contact
  plus a few Ω of wiring, I_pk is in the **hundreds of amps for tens of ns**, ~100× the 3 A rating.
  **Fix:** 10 kΩ in series with K1.COM. That caps I_pk at 1000 V / 10 kΩ = **100 mA**, comfortably
  inside 3 A. The cost is a 10 kΩ × Inom offset: at 0.5 mA that is **5 V**, i.e. 0.5 % of a 1 kV
  full scale — already inside the module's own ±1 % adjustment accuracy, and it is a *fixed*
  calibratable term. Cheap insurance; keep it even though the sequence should make it unnecessary.

### Coil power — the number nobody expects

| Coil | R | I | P each | 3 relays (K1,K2,K3) |
|---|---|---|---|---|
| 5 V | 40 Ω | 125 mA | 0.625 W | **1.88 W** |
| 12 V | 150 Ω | 80 mA | 0.96 W | 2.88 W |
| 24 V | 600 Ω | 40 mA | 0.96 W | 2.88 W |

The APS module's own worst-case input is `< 180 mA at 5 V` = **0.90 W**. So **the relay coils
dissipate roughly twice the entire HV module's input power**, continuously, in one of the two
polarity states (K1/K2 energized = positive; K3 energized = "HV permitted"). The 5 V rail must now
source ~250 mA more than the module needs.

Mitigation: coil economiser. Must-release on the 5 V coil is ≥ 0.5 V, must-operate ≤ 3.75 V, so a
PWM/series-R hold at 2.5 V gives 5× release margin at 2.5²/40 = **0.156 W** each ⇒ **0.47 W** for
three. Adds circuitry, and PWM'ing a coil next to a module specified at 10 mVpp ripple is an EMI
question you have to answer on the bench.

Thermal note: APS operating range is 0–40 °C ambient, max case 120 °C, tempco < 50 ppm/K. A ~2 W
coil load in a small enclosure is a real thermal item, and it is **polarity-dependent** (positive
state hot, negative state cold), so the module self-heats differently in the two polarities. At
1 kV, a 10 K differential × 50 ppm/K = **0.5 V** — negligible against the ±10 V accuracy spec, but
worth knowing it exists.

### Board area

Three 58.4 × 12.6 mm SIL relays = **2208 mm² of relay body alone**, against a 39.6 × 15.7 mm
(622 mm²) module. Plus 3.75 mm HV keepouts (§6) and a floating-island copper region with a barrier
slot. **The relays, not the HV modules, dominate the board.** The two-module baseline is
dramatically smaller.

---

## 4. Invariant (a) — hardware interlock. PASSES LITERALLY, FAILS IN SPIRIT.

The invariant as written: *"an interlock making it impossible to enable both modules into the output
simultaneously, enforced in hardware."*

**Literal verdict: satisfied vacuously and perfectly.** There is no second module. The state is not
interlocked-against, it is *nonexistent*. No component can fail in a way that creates it. On a
literal reading this topology beats every two-module scheme.

**That is a lawyer's answer, and I do not think the judges should accept it.** The hazard the
invariant protects against is *the load seeing a voltage of the wrong sign, or two sources fighting
into one node*. Restate it in hazard terms — **"the output shall never present a polarity other than
the commanded one"** — and this topology performs **worse** than the thing it replaces:

| | wrong-polarity output requires… |
|---|---|
| two modules + diode-OR / relay-OR | the *wrong* module's `/ON` asserted low — a fault on a line the ESP32 can read back, corroborated by that module's own `VMON` reading non-zero. Two independent facts must both lie. |
| **this topology** | **one MOSFET (Q1) stuck.** No aux contact is available on a Pickering Form C. The only contradicting evidence is the HV divider — and `VMON` cannot help because it reports \|Vout\| with **no sign information** (Table 4). |

And the two-module interlock is nearly free: drive both `/ON` lines from the two complementary
outputs of a single `74LVC1G3157` SPDT analog switch, or from the NC/NO of one small signal relay.
One part, well under $1, physically incapable of asserting both lines low.

**So: this topology converts a two-fault hazard into a single-fault hazard, and calls it a pass
because of a wording technicality.** That is the finding.

Partial mitigation, and it is genuinely decent: exploit the module's own 100 ms internal ramp (§1).
Command 2 % of Vnom, wait 500 ms, read the **sign** on the independent HV divider, and only then
ramp to the set point. A wrong-polarity fault is then caught at 20 V instead of 1000 V, which most
detectors survive. This is a firmware mitigation for a hardware hazard, which is exactly what the
brief says is not sufficient — but it is better than nothing and it should be specified regardless
of which topology wins.

---

## 5. Invariant (b) — discharge on changeover and disable. PASSES, and passes well.

Two layers, one of which has no active element at all:

1. **Unconditional passive bleed.** `R_bleed = 100 MΩ`, OUT_HOT → CHASSIS, permanently.
   Load current 1000 V / 100 MΩ = **10 µA = 2 % of Inom** on the worst-case 0.5 mA module.
   Dissipation V²/R = **10 mW**. With C_total ≈ 1.2 nF (assumed module C + 2 m of SHV cable at
   ~100 pF/m + load), τ = **120 ms**, and 1000 V → 10 V is 4.6τ = **550 ms**.
2. **Fail-safe active crowbar** on K3's **NC** contact: `OUT_HOT —[R_cb]— CHASSIS` when K3 is
   de-energized. De-energized is the state an unpowered or resetting ESP32 produces, so **loss of
   control ⇒ output clamped.** That is the right polarity of failure.

**R_cb sizing — and a bug I found in my own first pass.** My instinct was 1 MΩ. That is wrong.
If K3's driver fails and the crowbar is stuck closed while HV is live, the module current-limits at
1.5·Inom = 0.75 mA and the output settles at `0.75 mA × R_cb`:

| R_cb | stuck-closed residual output | I_pk when crowbarring 1 kV | τ (1.2 nF) | 1 kV → 10 V |
|---|---|---|---|---|
| 1 MΩ | **750 V — not a clamp at all** | 1 mA | 1.2 ms | 5.5 ms |
| 100 kΩ | 75 V | 10 mA | 120 µs | 0.55 ms |
| **10 kΩ** | **7.5 V** | **100 mA** (vs 3 A rating) | **12 µs** | **55 µs** |

**Use 10 kΩ.** A stuck-closed crowbar then holds the output at 7.5 V, which is genuinely safe, and
the discharge is essentially instantaneous. Peak current is 30× inside the contact rating.

### Changeover dead-band budget (Variant B, 1 kV class, R_cb = 10 kΩ)

| step | worst case |
|---|---|
| `/ON` → HIGH via digital isolator; internal 1 µF shorted | 1 ms |
| K3 operate (crowbar closes) | 6 ms |
| decay 1000 V → 10 V through 10 kΩ | 0.06 ms |
| verify < 10 V on the **independent** monitor, ADC + firmware margin | 20 ms |
| K3 release (crowbar opens) | 6 ms |
| K1/K2 changeover incl. worst-case 6 ms inter-relay skew + settle | 12 ms |
| `/ON` → LOW, module ramp to 99 % (τ = 100 ms, 4.6τ) | **460 ms** |
| **total** | **≈ 505 ms** |

Passive-bleed-only (no K3): the 0.06 ms line becomes 550 ms ⇒ **≈ 1.05 s**.

**The budget is dominated by the module's own 100 ms internal RC, not by the relays.** That is a
useful, non-obvious result: making the relays faster buys nothing. It also means *every* topology
that toggles `/ON` pays ~460 ms, so this is not a fair point against the relay specifically —
what *is* specific to the relay is that the output is hard-disconnected and clamped for that time.

**Caveat that must not be lost:** the module's output capacitance is not specified anywhere in the
manual. If C is 10 nF rather than 1 nF, the passive figures scale ×8 (τ = 1 s) while the 10 kΩ
crowbar figures stay sub-millisecond. **G1 bench measurement: disable and record decay through a
known R.** This is required in any topology.

---

## 6. Invariant (c) — independent output monitoring. PASSES, with a loss of redundancy.

Mechanism: HV divider OUT_HOT → CHASSIS, 1 GΩ (10 × 100 MΩ) over 1 MΩ, ratio 1001:1, giving ±1 V
for ±1 kV. Sum into mid-rail with a precision offset amp, into a bipolar-capable ADC on the
**grounded** side, wholly independent of the module's `VMON`. Divider loading at 1 kV = 1 µA =
**0.2 % of Inom** on the 0.5 mA module. That is 10× more load than the bleed and it must be included
in the error budget, but it is acceptable.

**The redundancy loss.** `VMON` reports 0…Vref for 0…\|Vout\| — **magnitude only, no sign**
(Table 4). In the two-module architecture the sign is *also* known digitally, from which module you
enabled, so the independent divider is a genuine cross-check on an already-known quantity. Here,
**the sign of the output is a property of a relay armature and nothing else**, and the divider is
not a cross-check — it is the *sole* sign measurement in the entire instrument.

Invariant (c) is nominally met. Defence-in-depth is quietly reduced from two independent
sign sources to one. That degradation is caused by choosing this topology and should be counted
against it.

Plus the §1 finding: **`VMON` is a 20 kΩ source** — buffer it or your "module readback" is 2 % low
before you start.

### Creepage / clearance, and the live case

IPC-2221B, external uncoated component leads/terminations, > 500 V: 2.5 mm at 500 V plus
0.00250 mm/V above ⇒ at 1000 V, **3.75 mm minimum**.

In Variant B the module's **metal case is bonded to MOD_GND (Table 4 note) and therefore floats to
−1000 V**. So a 39.6 × 15.7 × 11 mm bare steel box on the PCB is live, and needs a ≥3.75 mm keepout
ring on every layer, and cannot be touched. The whole assembly must be inside a grounded, interlocked
enclosure with no service access. In the two-module baseline the cases are at ground and need
**zero** keepout — only the HV net, the connector and the combiner are live.

---

## 7. Single-fault analysis (Variant B)

Active elements: Q1 (K1/K2 coil driver), Q3 (K3 coil driver), the isolated DC-DC, the digital
isolator carrying `/ON`, the isolated DAC driving `VSET`, K1/K2/K3, the ESP32, R_bleed, R_ref.

| # | fault | output does what |
|---|---|---|
| a | **Q1 stuck ON** | output permanently **POSITIVE** at the commanded magnitude. Firmware commanding −1 kV gets +1 kV. **Worst fault in the design.** Detected by the HV divider; **not prevented.** |
| b | **Q1 stuck OFF** | output permanently **NEGATIVE**. Same class, opposite sign. |
| c | **Q1 gate line broken** | with a mandatory gate pull-down: de-energized ⇒ NEGATIVE. Deterministic and known. Without the pull-down: indeterminate. **The pull-down is not optional.** |
| d | **K1 or K2 coil open, or one armature stuck** | *any single relay in the wrong state ties both module terminals to the same node* ⇒ module output shorted (short-circuit protected, Vout → 0) **and OUT_HOT disconnected from the module**. R_bleed then takes OUT_HOT to 0 with τ = 120 ms. **Benign and self-safing.** This is the topology's genuinely good property and it should be stated in its favour. |
| e | **Q3 stuck OFF ⇒ crowbar permanently closed** | with R_cb = 10 kΩ, output held at 1.5·Inom × 10 kΩ = **7.5 V**. Safe. (With 1 MΩ it would have been 750 V — see §5.) |
| f | **Q3 stuck ON / K3 welded open** | no fast discharge; R_bleed still works, τ = 120 ms. Changeover just gets slower. **Benign, degraded.** Detectable by watching the decay rate on the independent monitor. |
| g | **Isolated DC-DC fails** | module unpowered ⇒ Vout = 0. R_ref still defines the float node. Benign. |
| h | **Digital isolator carrying `/ON` fails, or floating-side power is lost** | **`/ON` floating = HV ON.** MUST have a 10 kΩ pull-up from `/ON` to the *floating* 5 V. Then an open isolator output ⇒ HIGH ⇒ HV OFF. Also select the fail-safe-HIGH option of the isolator. **On the 12 V module family the pull-up must go to a separate 5 V rail on the floating island — `/ON` absolute max is 5.5 V and +VIN is 12 V.** Easily-missed trap. |
| i | **Isolated DAC / VSET buffer fails open** | `VSET` pulled to Vref by the internal 10 kΩ ⇒ **FULL SCALE OUTPUT**. Mandatory mitigation: 200 Ω fail-safe pull-down **physically at the module's VSET pin**, giving 2.5 V × 200/10200 = 49 mV = **2 % of full scale = 20 V** instead of 1000 V. Cost: the buffer sinks 250 µA from the internal pull-up and sources 12.5 mA into 200 Ω at full scale — trivial for an RRO op amp. |
| j | **VSET driver rails above Vref** | `Vout > Vnom`, **internally unlimited**. Hardware clamp: **power the VSET buffer from a rail that *is* Vref** (2.5 V for the 0.5 W family, 5 V for the 1 W family). A rail-to-rail-output op amp cannot exceed its own rail — this is a true hardware clamp, not firmware. Belt-and-braces: an LM4040-2.5 shunt clamp on VSET. Topology-independent; should be a project-wide rule. |
| k | **ESP32 in reset** (GPIOs high-Z during reset and ~200 ms of boot) | gate pull-downs ⇒ K1/K2 de-energized (NEGATIVE), K3 de-energized (**crowbar closed**); `/ON` pull-up ⇒ HV OFF. Net: **output clamped to ground through 10 kΩ, HV disabled.** Correct — *provided all three pull resistors exist*. Do not use ESP32 strapping pins (GPIO0/2/5/12/15) for these lines; GPIO0 in particular carries an internal pull-up and is driven by the USB-serial auto-reset circuit. |
| l | **ESP32 unpowered while HV rails are up** | identical to (k), because every safing element is a passive pull to a rail that is still alive. If instead the +5 V logic rail is what died, the isolated DC-DC primary dies with it ⇒ module unpowered ⇒ Vout = 0. Consistent in both directions. |
| m1 | **broken wire: Q1 gate** | → NEGATIVE, deterministic (see c). |
| m2 | **broken wire: Q3 gate** | → crowbar closed, output clamped. Safe. |
| m3 | **broken wire: `/ON`** (isolator → pin 4) | pull-up wins ⇒ HV OFF. **Without the pull-up this is the single most dangerous broken wire in the instrument: HV comes ON at whatever VSET says.** |
| m4 | **broken wire: `VSET`** | if the break is upstream of the 200 Ω pull-down: 2 % of scale. If between the pull-down and the pin: **full scale**. Unavoidable — so make that a ~1 mm trace and keep the pull-down at the pin. |
| m5 | **broken wire: `VMON`** | monitor reads 0 while the output may be live. **This is precisely why invariant (c) exists**; the independent divider catches it. |
| m6 | **R_bleed open** | no passive discharge. Detected by an anomalously slow decay after disable. Note a *series chain* of 10 HV resistors has 10 chances to go open — use **two parallel chains** so one open doubles τ instead of removing the path. Cost: 20 HV resistors. |
| m7 | **R_ref open** | MOD_GND float node undefined during the few-ms mid-transit window only; leakage-defined. Minor. |
| n | **firmware skips the dead-band and hot-switches** | 1 kV into ~1 nF: per Pickering Note 1, welds the reed. A welded relay lands in case (d) — self-safing — but is otherwise **undetectable** except by the independent monitor. The 10 kΩ in K1.COM caps I_pk at 100 mA. Also: the float node slews 1 kV in ~1 µs of contact transit, and with C_iso ≈ 40 pF (isolated DC-DC 10–60 pF + isolator ~2 pF + 2 × 3 pF contact-to-coil + PCB) that is **40 mA of common-mode current dumped into the ESP32's ground**. It will reset the ESP32 at best. Third independent reason hot-switching is forbidden. |
| o | **APS output stuck at Vnom** (failure downstream of the internal `/ON` shunt) | `/ON` no longer helps. The 10 kΩ crowbar loads it to 1.5·Inom ⇒ **7.5 V**. **The crowbar is the only defence against a runaway module, and it works.** |
| p | **mechanical shock > 50 g** | a closed reed momentarily opens ⇒ case (d) ⇒ output floats, module shorts, bleed pulls to 0. Safe, but a bench knock silently drops the bias mid-run. A data-quality failure, not a safety one. |

**Pattern worth naming:** every *relay* fault is benign (case d). Every *driver* fault is a
wrong-polarity or wrong-magnitude fault. The mechanical parts are the reliable ones here; the
semiconductors around them are not.

---

## 8. Through-zero: categorically NO

- **Time dead-band ≈ 505 ms** at every zero crossing (§5), during which the output is
  hard-disconnected from the source and actively clamped to ground.
- Independently, the module's ripple/stability specs are guaranteed only for
  `2 %·Vnom < Vout ≤ Vnom` — for a 1 kV module the bottom **20 V is unspecified**. This applies to
  *every* topology using this module, so it is not a mark against the relay; but it means
  "through-zero" with an APS is already compromised before the combiner is chosen.
- Net: **±20 V of unspecified voltage plus a ~0.5 s hole in time.**

If the application is set-and-hold with occasional polarity changeover, 505 ms is entirely
acceptable and this is a non-issue. If it needs a continuous sweep through zero, this topology is
eliminated outright.

**This is the single question that decides the ranking, and the brief lists it as an open G0
question.** This candidate cannot be finally ranked until a human answers *"is smooth through-zero
required?"*.

---

## 9. Cost

Prices marked `[verified-distributor]` were read from a live page this session. Everything else is
an assumption and is flagged.

| item | qty | unit | line | evidence |
|---|---|---|---|---|
| iseg APS `AP010504P05` (1 kV, 0.5 mA, +5 V) | 1 | ~€250 | €250 | **ASSUMED.** No public price exists; iseg quote direct / via Instrumentcenter. Comparable PCB-mount 1 kV modules run $150–400. |
| Pickering `67-1-C-5/5D` (K1, K2, K3) | 3 | ~$40 | $120 | specs `[verified-artifact]`; **price `[unverified-MPN]`** — Farnell timed out twice, pickeringrelay.com returns 403 |
| Stackpole `HVCB2010FDC100M` 100 MΩ 1 % 1 W 2010 HV | 13 | $5.24 @10 | $68 | `[verified-distributor]` DigiKey: $6.73 @1, $5.24 @10, **0 in stock, 13-week factory lead** |
| Isolated DC-DC, ≥1 kV **continuous working** (not 1 s test) | 1 | ~$40 | $40 | ASSUMED |
| `Si8641` quad digital isolator, DW-16 wide body | 1 | ~$5 | $5 | `[unverified-MPN]`; datasheet revision note gives DW-16 VIOWM **1500 Vrms / 2121 VDC** |
| isolated-side DAC + ADC + op amps | — | — | $20 | ASSUMED |
| coil drivers, pull resistors, 5 V rail uprate, misc | — | — | $10 | ASSUMED |
| **total** | | | **≈ $265 + €250 ≈ $530** | |

Two-module baseline for comparison:

| item | line |
|---|---|
| 2 × iseg APS (one P, one N) | €500 |
| 2 × HV blocking element (2 × `67-1-A-5/1D`, or 2 × 2 kV HV diode < $2 each) | $30–80 |
| same bleed + same divider HV resistors | $70 |
| hardware interlock (one `74LVC1G3157` or one signal DPDT) | $1 |
| **total** | **≈ $600** |

**Delta ≈ $70, i.e. ~12 % of board BOM — and that is entirely inside the uncertainty of my assumed
module price.** You save €250 on a module and immediately spend ~$180 of it on the isolation
barrier, the third relay and the extra HV resistors, and what you buy for the difference is a
strictly worse machine: a live kilovolt case, a 3.75 mm keepout ring, ~2 W of coil heat, 2208 mm² of
relay, a 505 ms dead-band, and wrong-polarity as a single-MOSFET fault.

**The topology's entire economic premise — "one module instead of two" — does not survive contact
with the bill of materials.**

Also note the schedule risk: the HV resistor is **0 in stock with a 13-week lead** at the only
distributor page I could read. This topology needs 13 of them; the baseline needs 11. Not
discriminating, but it is a real procurement item for the project either way.

---

## 10. Showstoppers

1. **Off-datasheet operation of the module.** Manual page 4, *Intended Use*:
   > `The device may only be operated within the limits specified in the data sheet... Any other use
   > not specified by the manufacturer is not intended. The manufacturer is not liable for any
   > damage resulting from improper use.`

   Combined with Table 4's `Case is connected to GND`, Variant B runs the module with its GND and its
   bare steel case at up to −1000 V relative to system ground. The datasheet specifies **no isolation
   rating whatsoever** between GND/case and anything else, because in the intended use there is no
   barrier there. Whether the internal construction tolerates its own reference floating at kV is
   **undocumented and unanswerable from the datasheet**. This voids intended use and the 12-month
   warranty. It would need written confirmation from iseg before it could be designed in.
   *(Internal stress magnitude is arguably unchanged — HV-pin-to-case still sees Vnom, just with the
   sign of the reference swapped — but "arguably" is not a basis for a kilovolt design.)*
2. **The single-armature interlock does not exist.** No vendor offers a 2 Form C reed relay at
   ≥1 kV (Pickering: "1 Form A and 1 Form C configurations", `[verified-artifact]`; Standex HV
   ranges show only Form A/B). The DPDT must be two relays sharing one driver, so the safety
   argument reduces to trusting **one MOSFET**.
3. **Wrong-polarity output is a single-fault condition** (Q1 stuck), where the two-module scheme
   makes it a two-fault condition. For a photodetector or an APD, wrong-sign kilovolts is
   destructive. This is the invariant-(a) hazard reappearing in a new costume after being declared
   "vacuously satisfied".
4. **Violates a stated requirement, not an open question.** Brief requirement 1 is
   "Two unipolar iseg modules, opposite polarities". "Use one module and reverse it" is a
   **requirements change**, and must be put to the human as such — it is not something the
   combiner-topology study is authorised to decide.
5. **No through-zero.** ~505 ms clamped-to-ground hole at every crossing. Fatal if through-zero is
   required; harmless if not. Unresolved at G0.
6. **Variant A is unusable at all** for any chassis-referenced load, which is the normal case.
   Anyone who reaches for "just put a DPDT on the output" without noticing the module case is bonded
   to GND will build Variant A and discover this on the bench.

---

## 11. What is genuinely good here, and should be harvested regardless of the verdict

Even though the topology is rejected, four results from this study are topology-independent and
belong in `docs/DECISIONS.md`:

1. **`/ON` needs a 10 kΩ pull-up to a ≤5.5 V rail** so that any break or driver failure means HV OFF.
   On the 12 V family that rail must **not** be +VIN.
2. **`VSET` needs a ~200 Ω fail-safe pull-down at the module pin**, because the internal 10 kΩ
   pull-up to Vref makes an open VSET node command **full scale**. 200 Ω caps the runaway at 2 % of
   scale.
3. **The `Vset > Vref` hardware clamp is free:** power the VSET buffer from a rail that *is* Vref.
   An RRO op amp cannot exceed its own rail. This satisfies the brief's "hardware clamp, not a
   firmware nicety" with zero added parts.
4. **`VMON` is a 20 kΩ source** (Figure 2) and **carries no sign information** (Table 4). Buffer it,
   and never treat it as a polarity check.

Plus two open items for the human:
- **Ask iseg for the module's HV output capacitance and any GND/case isolation rating.** Every
  discharge-time number in this project is currently parametric in an unmeasured C.
- **Ask iseg about the `Current monitor accuracy 1 %·Inom` line in Table 1 with no current-monitor
  pin in Table 4.** Flagged, deliberately unresolved.

---

## 12. Verdict

**3 / 10. Reject.**

Sub-variant A (grounded module, floating load) is eliminated outright: with the module case bonded
to GND, reversing the load terminals means neither output terminal is ground, which breaks every
chassis-referenced detector, every SHV cable and every grounded electrometer.

Sub-variant B (floating module, grounded load) is a real and respectable architecture, and it wins
on two of the three invariants on a literal reading — discharge is excellent (fail-safe NC crowbar
plus unconditional passive bleed, 55 µs to safe), independent monitoring is straightforward, and
every *relay* failure mode is self-safing. It is not a silly idea.

It loses anyway, on four independent grounds, any one of which is sufficient:
the economics do not work (the saved module is spent again on the isolation barrier);
the interlock argument depends on a single-armature DPDT that no vendor sells at 1 kV, so
wrong-polarity becomes a single-MOSFET fault; floating a module whose case iseg bond to GND is
explicitly outside the manufacturer's *Intended Use*; and it contradicts a stated brief requirement
rather than answering an open one.

Recommend eliminating at G0 and recording the four harvested findings in §11, which apply to
whichever combiner topology does win.
