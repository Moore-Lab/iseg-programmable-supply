# Audit — McGill PHYS 439 alpha-lab Arduino shield

**Subject:** `references/Phys439-alpha-lab/` (read-only third-party material)
**Audited:** 2026-07-23
**Purpose:** establish what the existing, working reference board actually does, in numbers,
so that the new bipolar iseg HV controller improves on evidence rather than on impression.

Design authority for the reference board: Eamon Egan, McGill University Physics Department,
Electronics Design Support Team. Schematic rev 1.0 dated 2020-07-27; the on-disk KiCad set is
rev **1.0a**, "rev 1.0 showing board mods".

Module datasheet citations are to **iseg APS series technical documentation v2.5, 2024-08-20**
(`references/iseg_manual_APS_en.pdf`), re-read directly this session.

---

## 0. Method, instruments, and what they cannot see

| Instrument | What it established | What it structurally cannot see |
|---|---|---|
| `fitz` (PyMuPDF 1.28, bundled with KiCad 10) rendering `doc/PHYS 439 alpha lab shield schematic.pdf` at 3×/9× | The rev 1.0 topology, visually | Nothing about rev 1.0a; the PDF has **no extractable text** (pure vector art) and is one revision behind the `.sch` |
| Direct read of `alpha-shield.sch`, `double_lpf.sch` (EESchema v4 text) | Component values, hierarchy, per-instance annotation, the hand-mod annotations | Whether the mods were actually performed on the physical hardware |
| Purpose-written stdlib s-expression parser + re-implemented distance math over `alpha-shield.kicad_pcb` | Real copper geometry and clearances in mm | Solder mask geometry, silkscreen, assembly reality, conformal coating (if any was later applied) |
| Closed-form residues **and** RK4 integration of the filter transfer function (cross-checked, max divergence 4.2e-13) | Settling times, overshoot, ripple rejection | Real op-amp slew/saturation, real capacitor tolerance (1 µF ceramics are typically ±10–20 % and X7R loses capacitance with DC bias), real PWM frequency |
| Direct read of `alpha-shield.ino` + the vendored `Vrekrer_scpi_parser` | SCPI surface, control maths, latent defects | Runtime behaviour — **nothing here was executed**; no board, no Arduino, no serial link |
| Text extraction from `doc/…documentation.docx` | The designer's own stated intent and known limits | — |

`pcbnew` under `PY_KICAD` **hangs** on `LoadBoard()` of this KiCad-5-era (`version 20171130`)
file: >120 s wall clock with **zero** stdout — it never reached the first `print()` after the
load call — and had to be killed. All PCB geometry below therefore comes from the stdlib parser,
whose numbers are independent of KiCad's DRC engine. Round-rect pads are modelled exactly
(inner rectangle grown by `roundrect_rratio × min(size)`), not approximated as sharp rectangles.

**No claim below is a bench measurement.** Every number is derived from files on disk.

---

## 1. What is actually on this board — and what is not

Three corrections to the working assumptions in the project brief, all `[verified-artifact]`:

1. **Only ONE iseg module is populated.** `M2` carries the value string
   `AP0vv255x05 (DNP)` and appears as `DNP` in `alpha-shield.csv`. The M2 site was later
   *repurposed*: schematic note "READ2 (pressure gauge) input, 0-10V / R45 added / Header pins
   placed in M2-4,5". So this is a one-module unipolar board, not a two-module board.
2. **There are no relays and no PTC fuses on this board.** A grep of all four `.sch` files for
   `SRD|RXEF|LVR100|Relay|PTC|Fuse` returns exactly one hit: the text annotation
   `Relay control` next to header J6. `SRD-12VDC-xx-x_ETC.pdf`, `RXEF050` and `LVR100S240` sit in
   `circuit/parts/` as *candidate* datasheets that never made it into the netlist. The
   documentation confirms it: relays are an **external** module ("Sunfounder 2 Channel Relay"),
   driven active-low from J6 pins 1 and 5, with +5 V and GND supplied from the shield.
3. **`bias_supply.sch` and `PWMFilter.sch` are orphans.** The root sheet contains exactly two
   `$Sheet` blocks (`U 5F1ED63B` and `U 5F19B79F`), both pointing at `double_lpf.sch`. Neither
   orphan file is in the design hierarchy. They are dead files in the repo.

**And a fourth, which matters more than the other three:**

4. **The `.kicad_pcb` does not describe the board that works.** Six parts exist in the schematic
   as documented modifications but are **absent from the layout entirely**:

   | Ref | Value | Role | In `.sch` | In `.kicad_pcb` |
   |---|---|---|---|---|
   | R46 | 100 Ω 1/4 W | VSET pull-down (fail-safe) — **load-bearing** | yes | **no** |
   | R47 | 100 Ω 1/4 W | same, second instance (not fitted) | yes | **no** |
   | Q1 | BUW48 NPN | emitter follower on the 0–20 V valve output | yes | **no** |
   | Q2 | BUW48 NPN | same, second instance (not fitted) | yes | **no** |
   | R45 | 3.3 K | pressure-gauge input network | yes | **no** |
   | J7 | 1×02 header | pressure-gauge input, in M2 pads 4/5 | yes | **no** |

   Plus two copper-level modifications recorded only as text notes:
   *"pin 4 drilled out to isolate from GND"* (M1's `/ON` pad — on the PCB, `M1.4` is still on
   net 1 = GND), and two bodge wires annotated simply `wire`.
   The artifact of record and the hardware of record diverged, and the divergence is exactly where
   the safety behaviour lives.

---

## 2. The HV signal chain, end to end

### 2.1 Topology (rev 1.0a, the built configuration)

```
Arduino Due D5 ──R1 220k──┬── IN1 ─────────────────────────────────────► sheet 5F1ED63B (double_lpf.sch)
   (12-bit PWM)           │
                    R9 100k ∥ C1 1µF to GND          [passive RC, single pole]
                                │
                                ▼
                    U1A LM324, non-inverting: R13 1k feedback, R11 2.7k to GND   [gain 1.3704]
                                │
                                ▼
                    U1B LM324 Sallen-Key LP: R15 100k, R17 100k, C6 1µF, C8 1µF
                                             gain-set R21 680 / R19 1.1k          [gain 1.6182, 2 poles]
                                │
                    R39 0 Ω ────┼──── D2 BZX79C2V4 (2.4 V zener) to GND      [VSET over-voltage clamp]
                                ├──── R46 100 Ω to GND  *hand-added, not in layout*
                                ▼
                       M1 pin 2  VSET
                       M1 pin 1  +VIN ← Arduino +5 V rail (no decoupling anywhere)
                       M1 pin 3  GND
                       M1 pin 4  /ON  ← pad drilled out from GND, bodge wire to JP2 common ← Due D15
                       M1 pin 5  VMON → R37 1k → Due A0
                       M1 pin 6  HV ──R43 10k (0805)── [D6 zener footprint, DNP] ── J1-1
                       M1 pin 7  GND
```

Op-amp supply: `VCC` of the `double_lpf` sheet is tied to **+24 V**, brought onto the board from
outside through J2-1 / J4-1 (D1, the +5 V-to-+24 V bridge diode, is DNP). C3 = 1 µF decoupling.

### 2.2 The real numbers

All from the rev 1.0a values in `double_lpf.sch` and `alpha-shield.sch`. `[verified-run]`
(`scratchpad/filter_math.py`, executed this session under `PY_KICAD`; the maths is stdlib-only).

**DC transfer, D5 → VSET:**

| Stage | Expression | Value |
|---|---|---|
| Input attenuator | R9/(R1+R9) = 100k/320k | 0.312500 (1/3.2) |
| U1A non-inverting | 1 + R13/R11 = 1 + 1k/2.7k | 1.370370 |
| U1B Sallen-Key | 1 + R21/R19 = 1 + 680/1100 | 1.618182 |
| **Total** | | **0.692971** |

**The firmware's `bias_gain = 0.69299` is CORRECT.** It agrees with the schematic component
values to **+0.0027 %**. This is not a finding against the board — it is evidence that the
firmware constant was derived from the components and not guessed. (It is corroborated a third
time by the designer's own gain table in the `.docx`, which gives 0.69299 from the same chain.)
Note the configuration dependency: `R11` is populated at 2.7 k **only** for a 3.3 V Due; with
`R11` open — the intended 5 V Mega/Uno build — the gain is **0.505682**, and the firmware constant
would be wrong by 37 %.

**Filter poles:**

| Section | Parameter | Value |
|---|---|---|
| Passive RC | R_th = R1‖R9 = 68.75 kΩ, C1 = 1 µF | τ = **68.75 ms**, f_c = **2.3150 Hz** |
| Sallen-Key | R = 100 kΩ, C = 1 µF, K = 1.61818 | f₀ = **1.5915 Hz**, ω₀ = 10.000 rad/s |
| | Q = 1/(3−K) | **0.72368** (ζ = 0.69091) |

The schematic annotation "1/Q = 3 − G = 1.4 … for critical damping, Q = 0.707" is loose: the
actual Q is 0.7237, slightly *above* Butterworth, so the response is mildly under-damped.

**Step response of the whole D5→VSET chain** (unit step; RK4 and closed-form residues agree to
4.2 × 10⁻¹³):

| Metric | Value |
|---|---|
| 10–90 % rise time | **0.255 s** |
| Settling to 10 % | 0.348 s |
| Settling to 1 % | 0.730 s |
| **Settling to 0.1 %** | **1.093 s** |
| Settling to 0.05 % | 1.165 s |
| Peak overshoot | 3.29 % at t = 0.541 s |

0.1 % of full scale is 0.20 V of HV output. **A commanded bias change takes about 1.1 seconds to
settle to 0.2 V**, and overshoots by ~6 V of HV on the way (3.29 % of 183 V) before recovering.
There is no firmware interlock preventing a read of VMON during this second.

**What the filter buys for that second:** at an assumed 1 kHz PWM carrier the chain attenuates by
**−157.7 dB**; at 490 Hz, **−139.1 dB**. The worst-case fundamental (2.10 V peak at 50 % duty)
arrives at VSET as **2.7 × 10⁻⁸ V**, i.e. **2 µV** of HV output. One PWM LSB is 0.045 V of HV.
About 60 dB of rejection would already bury the ripple below the quantisation floor; the design
delivers 139–158 dB. **The filter is over-designed by roughly 80–100 dB, and the price is paid in
settling time.** (The PWM frequency is `[recalled]`, not verified — Arduino Due `analogWrite` on
D5 defaults to ~1 kHz. The conclusion is insensitive to the exact value: even at 100 Hz the
attenuation is enormous.)

### 2.3 The range defect

`bias_factor = analogwrite_maxcount / vcc × bias_maxvoltage / bias_maxsetting / bias_gain`
= 4095/3.3 × 2.5/200/0.69299 = **22.383 counts per volt**.

- `BIAS 200` requests **4476.6 counts**. `analogWrite` maximum is **4095**. The firmware's own
  `constrain()` silently clamps it.
- 100 % duty gives VSET = 3.3 × 0.692971 = **2.2868 V** against a module V_ref of 2.5 V.
- Maximum reachable output = **182.94 V of the 200 V nominal — 91.5 % of range**.
- `BIAS?` still returns **200.00000**.

This is a *known* limitation: the designer's documentation states "on a 200V ISEG module, the top
output voltage will be approximately 180V". It was never propagated into the firmware.

---

## 3. `/ON` control — the enable

**As fabricated (PCB copper):** `M1` pad 4 and `M2` pad 4 are both on **net 1 = GND**. In the
original rev 1.0 build, both modules' `/ON` pins were hard-wired to ground, and per Table 4 of the
manual, `/ON` LOW ⇒ **HV ON**. There was no enable control at all: the modules produced HV
whenever +5 V was present.

**As modified (rev 1.0a):** M1's pin-4 pad was *physically drilled out* to break it from the GND
pour, and a bodge wire runs from the common pin of solder jumper **JP2** to that pin. JP2 is a
`SolderJumper_3_Bridged12` — bridged 1–2 from the factory — selecting Arduino **D15 (RX3)**.
The firmware agrees: `const int biasControl = 15;` and `digitalWrite(biasControl, !biasState)`.

**Answering the question the brief asked:** in the *design intent* both modules are driven by the
single net that JP2 feeds, so yes, one enable line would have served both. In the *hardware as
built* it is worse than a shared enable: **M2's `/ON` is still hard-tied to GND in copper**. Had
M2 ever been populated, it would have been permanently, unconditionally ON while M1 was
switchable. There is no configuration of this board in which "both modules off" is reachable.

**Four consequences for our bipolar design, in descending severity:**

1. **A single `/ON` line makes both-enabled the default state, which our brief forbids outright.**
   Our interlock must be a hardware structure — complementary drive with a physical exclusion
   (e.g. a DPDT relay's own contact geometry, a cross-coupled latch with an enforced dead time, or
   an analogue-mux/SPDT topology in which "both" is not a representable state) — not two GPIOs and
   a promise.
2. **The module's default is ON, not OFF.** The manual is explicit: `/ON` = "LOW **or n.c.**
   ⇒ HV ON". Every de-energised, unplugged, floating, or pre-boot condition commands high voltage.
   On this board, between MCU reset and `ConfigureHardware()` completing, D15 is a high-impedance
   input, so the module is enabled at every power-up and every reset. Our board needs a pull-up to
   the module's own supply on every `/ON` net so that "no controller" means "off".
3. **The drive level has 0.8 V of margin, in the fail-dangerous direction.** The threshold is
   "HIGH > 2.5 V, ≤ 5.5 V". A 3.3 V Due output holds OFF with 0.8 V of headroom; any V_OH sag,
   series drop, or level-shifter leak walks toward ON. Our ESP32 is also 3.3 V — this needs an
   explicit level shift to the module's 5 V/12 V rail, not a direct connection.
4. **`/ON` HIGH means "V_out = 0", not "output disconnected".** The manual specifies the output
   voltage goes to zero; it says nothing about the output impedance or discharge rate in that
   state. Disabling a module is *not* a substitute for a bleed path (see §5.3).

---

## 4. Monitoring — what is measured versus what is remembered

**VMON is wired to an ADC.** `M1` pin 5 → net 89 → `R37` (1 kΩ, 0805) → net `/A0` → `P2` pin 1 =
Arduino **A0**. `[verified-artifact]`, from the PCB netlist. The brief's suspicion that VMON was
unwired is wrong; the connection exists and always did.

The chain is, however, unused for its purpose and unscaled:

| Property | Value |
|---|---|
| VMON range | 0–2.5 V for 0–200 V (0.5 W family, manual Table 4) |
| Series resistance to ADC | 1 kΩ, no buffer, no anti-alias filter, no clamp |
| ADC | Due, 12-bit, 3.3 V reference |
| ADC LSB | 0.806 mV = **0.0645 V of HV** |
| Fraction of ADC span used | 75.8 % |
| Module's own VMON accuracy spec | **1 % × V_nom = 2.0 V** |

`BIAS?` calls `GetBias()`, which is four lines long:

```cpp
void GetBias(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  int channel = 1;
  if (channel >= 1 && channel <= 2) {
    interface.println(bias_settings[channel-1], 5);
  }
}
```

`bias_settings[0]` is written only by `SetBias`. **`BIAS?` reports what was asked for, to five
decimal places, never what happened.** It reports 200.00000 for a supply producing 183 V. It
reports the last commanded value if `/ON` is HIGH and the output is at zero. It reports the last
commanded value if the module is unplugged, dead, or in current limit.

The measured value *is* reachable — `VOLTAGE1?` returns A0 in volts — but:
- the scaling to HV volts is not applied anywhere (the comment even says
  `// not considering voltage divider 13.33/3.33`, which is the *pressure-gauge* divider, not this one);
- nothing cross-checks setting against measurement;
- the readback is the module's own opinion of its output. There is **no measurement independent of
  the module**. A module whose internal divider has drifted, or whose HV output is open-circuit at
  the connector, reports a healthy VMON.

**The HV output itself is measured nowhere.** Net 86 (the J1-side HV node) connects to exactly
three pads: `R43.1`, `J1.1`, and `D6.1` (DNP). No divider, no sense, no ADC.

---

## 5. Protection, safety, and actual copper clearances

### 5.1 HV creepage and clearance — measured, in millimetres

The board is 2-layer, 101.60 × 53.34 mm, **zero copper zones** (`(zones 0)` — GND is routed as
0.25/0.381 mm tracks, 38 segments, no plane). The global DRC rule is
`(trace_clearance 0.2)` `(trace_min 0.2)`, and **there is no netclass distinguishing the HV net.**

The HV chain is two nets: **88** (`M1.6` → `R43.2`) and **86** (`R43.1` → `D6.1` → `J1.1`),
routed entirely on F.Cu at **0.254 mm track width**, ~21 mm of run.

Measured minimum copper-to-copper clearances from the 200 V chain
(`[verified-run]`, `scratchpad/hv_clear.py` + `hv_detail.py`, exact round-rect geometry):

| Neighbour net | Minimum gap | Where |
|---|---|---|
| **`/14(Tx3)`** (Arduino Serial3 TX) | **0.200 mm** | `R43` pad 1 and pad 2 ↔ track; `D6` pad 1 ↔ track |
| **`/20(SDA)`** (Arduino I²C data) | **0.200 mm** | `D6` pad 1 ↔ track; 0.289 mm at `J1` pad 1 |
| `Net-(C9-Pad1)` | 0.681 mm | `M1` pad 6 ↔ track |
| `GND` | **0.840 mm** | `J1` pad 1 ↔ `J1` pad 2, i.e. across the output header itself |
| Board edge (Edge.Cuts) | 8.444 mm | comfortable |
| `R43` own pad-to-pad (0805) | 0.900 mm | |

The board is **DRC-clean against its own rule** — the rule is simply the wrong rule. Every gap
sits at exactly 0.200 mm because that is what the router was told to hold.

Against IPC-2221 Table 6-1 for **171–250 V** (**`[unverified-primary]`** — the standard is not on
disk here and **nobody on this project has read a primary copy**; see the note below):

> **Session-2 reconciliation.** These two values **agree exactly** with the transcription in
> `hardware/hvctl/numbers_probe.py` (§1.1: B4 = 0.400 mm, B2 = 1.250 mm in the 171–250 V band), so
> nothing in this audit's conclusion moves. That agreement is **not** evidence the values are right:
> both came from the same secondary web reproduction, and session 1's claimed "independent
> cross-check between two standards families" was proved to be an **algebraic tautology** and has
> been deleted (`STATUS.md` §1.2, `NUMBERS_PROBE.md` §1.5). Every IPC number in this repository now
> carries **`[unverified-primary]`** until a human reads IPC-2221B Table 6-1 in the original.
> **The single live source for clearance numbers is `docs/NUMBERS_PROBE.md`.** Do not re-derive them
> here or anywhere else.

| Condition | Required | Actual | Shortfall |
|---|---|---|---|
| B4 — external, permanent polymer coating (solder-masked track) | 0.4 mm | 0.200 mm | **2× under** |
| B2 — external, uncoated (exposed pad) | 1.25 mm | 0.200 mm | **6.25× under** |

**And the sharpest point: every sub-0.3 mm approach involves an exposed HV *pad*** — `R43` pads,
`D6` pads, `J1` pad 1. Mask covers the track but not the pad, so B2 (1.25 mm) is the applicable
row at exactly the places where the gap is 0.200 mm. There is no soldermask credit to be had.

The failure mode is not academic. The nets at 0.200 mm are `Serial3 TX` and `I²C SDA` — a
flashover puts 200 V onto MCU I/O pins that are galvanically continuous with the USB host.

The designer's own documentation asserts *"Trace clearance should be adequate for ±200V but may
not be for 1kV"*. Measured against IPC-2221, that assertion does not hold at 200 V either.

### 5.2 HV component ratings

- **`R43` = 10 kΩ in an `R_0805_2012Metric` footprint.** Standard thick-film 0805 parts are rated
  150 V maximum working voltage and 0.125 W (`[recalled]` — typical of e.g. Vishay CRCW0805;
  verify against the actual part before reusing the topology). Under normal high-impedance load
  the drop across R43 is small. Under an output short the module current-limits at
  ≈1.5 × I_nom = 3.75 mA, giving 37.5 V across R43 and **0.14 W in a 0.125 W part** — a sustained
  overload, and a resistor whose failure mode is to go *open* or to *short*, either of which is
  unannounced.
- **`D6`, the HV clamp, is DNP.** The schematic carries the note "Zener limits bias voltage. Shown
  for positive bias module. Reverse zener if bias is negative" and the BOM lists `D6, D7` as `DNP`.
  So the one component intended to bound the HV output against the manual's explicit warning
  ("Output voltage is internally not limited!") is not fitted.
- **`J1` is a 2.54 mm pin header** (`PinHeader_1x02_P2.54mm_Vertical`) with pin 1 = HV and
  pin 2 = GND, 0.840 mm of bare copper between two exposed pads at 200 V, unshrouded, on an open
  Arduino shield. There is no HV connector, no shroud, no keying, no barrier.

### 5.3 There is no bleed path

Net 86 (the HV output node) has exactly three pads on it: `R43.1`, `J1.1`, `D6.1`. `D6` is not
fitted. **There is no resistor from the HV output to ground anywhere on the board.** When `/ON`
goes HIGH the module drives its output to zero, but the cable, the connector, and the detector
capacitance are left to whatever leakage happens to exist. On disable, and on any loss of +5 V,
the stored charge on the external load has no defined path to ground.

### 5.4 The one genuinely good protection idea on the board

`R46`, the hand-added 100 Ω from VSET to GND, is the smartest thing on this board and we should
steal it.

Manual Table 1, control version 1: `R_set = V_out · 10 kΩ / (V_nom − V_out)` between VSET and GND
— which is a statement that **VSET carries an internal 10 kΩ pull-up to V_ref (2.5 V)**. So an
open VSET node commands **full-scale output**. If the op-amp is unpowered, the board is half
assembled, a solder joint fails, or a connector is unmated, the module goes to 200 V.

With R46 fitted, an open driver leaves VSET at 2.5 × 100/10100 = **24.8 mV**, i.e. **1.98 V of
HV** instead of 200 V. The designer arrived at the same conclusion empirically: *"in order to
provide a low enough voltage when the setting is put to zero, it's necessary to place a 100 Ω
resistor across D2, to sink current from the ISEG module … the output voltage can be set under
2 V"*. (Their prose says the pull-up goes to 5 V; the manual says V_ref = 2.5 V, and their own
measured "under 2 V" result is consistent with 2.5 V, not 5 V. The manual is right.)

Costs: the op-amp must source **22.9 mA** at full scale into R46 (52 mW dissipated in it), which
is near the guaranteed source capability of an LM324 and forces a genuine output stage.

### 5.5 Miscellaneous

- **No decoupling on the module's supply.** Net 2 (`+5V`) has *no capacitor on it at all* —
  members are `D1.2, J5.3, J6.3, M1.1, M2.1, P1.5`. The manual's note 2 explicitly recommends
  *"22 µF near pin +VIN"* for input-line ripple rejection. It is not there.
- **Power-on transient.** The designer's documentation records: *"A transient of up to ±7 V
  (depending on the ISEG module polarity) is produced when the 5V supply is connected."* HV
  appears before any firmware exists to command it.
- **Op-amp rail vs. module input.** The LM324 runs from +24 V and drives a pin rated 0–2.5 V.
  A saturated output would deliver ~22 V into VSET. `D2` (BZX79C2V4, 2.4 V) is the only thing
  standing between an op-amp fault and V_out ≫ V_nom. It *is* fitted — good — but it is a bare
  zener with no series impedance except `R39` = **0 Ω**, so a hard op-amp saturation dumps
  (22 − 2.4)/0 amps into it. The clamp will not survive the fault it exists to catch.
- **Part identity is ambiguous.** `U1`/`U2` value fields say `LM324` in the on-disk rev 1.0a,
  `LT1014` in the rev 1.0 PDF, and the CSV BOM emits the self-contradictory row
  `"U1,U2","2","LM324,LT1014"` plus a second row `"U2","1","LT1014"`. The datasheet field points
  at the LM2902/LM324. The BOM cannot be built from as-is. (LM324 V_os ≈ 2–7 mV vs LT1014
  ≈ 60–150 µV — at 80 V/V from VSET to HV that is the difference between 0.6 V and 12 mV of
  output offset, so it is not a cosmetic distinction.)

---

## 6. Firmware

`code/alpha-shield/alpha-shield.ino` + a vendored copy of `Vrekrer_scpi_parser`.
Target: **Arduino Due** (`vcc = 3.3`, `analogWriteResolution(12)`, `DAC0(A12)/DAC1(A13)` in the
schematic). Transport: `Serial` (programming port UART) at **9600 baud**.

### 6.1 The SCPI surface

| Command | Behaviour |
|---|---|
| `*IDN?` | `McGill,PHYS 439 Alpha Experiment Apparatus,#00,v1.0` |
| `BIAS <v>` | set bias, `constrain(v, 0, 200)`, PWM on D5 |
| `BIAS?` | **returns the stored setting**, 5 dp |
| `BIAS:ON` / `BIAS:OFF` / `BIAS:ONOFF?` | drive/report `/ON` (active low) |
| `RELAY <0\|1>` / `RELAY?` | external relay module, active low |
| `VALVE <%>` / `VALVE?` | 0–20 V proportional valve, stored setting |
| `VREF:ON` / `VREF:OFF` / `VREF:ONOFF?` | drive A7 high and A4 low **as digital outputs** |
| `PWM<n> <v>` / `PWM<n>?` | raw PWM in volts |
| `COUNT<n>?` | raw ADC counts, A0–A7 |
| `VOLTAGE<n>?` | ADC in volts, unscaled |
| `PRESSURE<n>?` | pressure with sensor-specific conversion |
| `*DEBUG?` | dumps the parser's command hash table |

### 6.2 What is good, and should be carried forward

- **A real SCPI parser, not ad-hoc string matching.** Hierarchical command trees, `?` queries,
  numeric suffixes (`VOLTAGE3?`), long/short forms, `SetCommandTreeBase`. Working against
  `references/Phys439-alpha-lab/references/scpi-99.pdf`, this is the right family of interface for
  lab instrumentation and it is why the board is usable from any host language with a serial port.
- **`*IDN?` implemented and correctly formatted** (four comma-separated fields).
- **The gain constants are derived from component values and documented as such**
  (`// amplifier gain (nominal, by component values)`), and they are *right* to 0.003 %.
- **Range clamping exists** (`constrain(setting, 0.0, bias_maxsetting)`), so a typo cannot command
  1000 V into a 200 V module.
- **The active-low conventions are stated in comments at every use site** — `/ON` and the relay
  inputs — which is exactly the discipline that prevents a polarity inversion during a rewrite.
- **The TODO block is honest**, and names most of the real gaps itself.

### 6.3 What is missing or broken

**Missing (the TODO block admits the first four):**

1. No readback of measured HV; `BIAS?` cannot fail-detect anything.
2. No soft limits beyond the hard-coded 200 V ceiling; no configurable lower limit.
3. No calibration storage — no offset/gain trim, no two-point calibration, nothing in flash.
4. No `*RST`, no `*CLS`, no `*ESR?`, no `*OPC`, **no error queue and no `SYSTem:ERRor?`**.
   SCPI-99 mandates an error queue; without it an unrecognised command is answered with *silence*
   (see below), which converts every host-side typo into a read timeout.
5. **No ramping.** `BIAS 0` → `BIAS 180` is a step command into a 1.1-second filter with 3.3 %
   overshoot. dV/dt at the load is uncontrolled and un-commandable.
6. No polling/streaming mode; no timestamping.

**Broken or latent (all `[verified-artifact]`, from reading the source; none executed):**

7. **Blocking query handlers.** `ReadAnalog`, `ReadA`, `ReadAnalogPressure1/2` each do
   `analogRead(pin); delay(50);` then **1000** further `analogRead` calls in a tight loop. `loop()`
   is a single call to `ProcessInput`, so the entire instrument is unresponsive for ≥50 ms per
   query while incoming serial bytes accumulate in a hardware FIFO. There is no reason for a 50 ms
   settle *and* a 1000-sample average on a 1 kΩ source; the averaging is over an interval far
   shorter than the 1.1 s the analogue chain needs anyway, so it buys precision on a signal that is
   still moving.
8. **Out-of-bounds array read on a malformed query.** `getSuffix()` returns **−1** when `sscanf`
   fails. `ReadA()` does not bounds-check at all:
   ```cpp
   int channel = getSuffix(commands);
   int pin = analogPins[channel-1];   // channel == -1  ->  analogPins[-2]
   ```
   `ReadAnalog()` checks only the upper bound (`if (channel > NELS(analogPins)) return;`). A bare
   `VOLTAGE?` reads two ints before the array.
9. **Unbounded buffer write from the serial port.** In `Vrekrer_scpi_parser.cpp::GetMessage()`:
   ```cpp
   msg_buffer[msg_counter] = interface.read();
   //TODO check msg_counter overflow
   ++msg_counter;
   ```
   `msg_buffer` is `char[64]` and is the **last** member of `SCPI_Parser`. Any serial line longer
   than 63 bytes before `\n` writes past the end of the object into adjacent globals. On a device
   that commands 200 V, an over-long line is a memory-corruption primitive reachable from the port.
10. **The command table is one entry from overflowing, with no bounds check.**
    `SCPI_MAX_COMMANDS` is 20; the sketch registers **19**. `RegisterCommand` writes
    `valid_codes_[codes_size_]` and `callers_[codes_size_]` with no comparison against the limit.
    Adding two commands corrupts memory at boot, silently.
11. **Unknown commands produce no response.** `Execute()` iterates the hash table and, on no
    match, simply returns. Combined with (4), the host cannot distinguish "not supported" from
    "device hung".
12. **Command dispatch is by 32-bit hash, not by string compare.** A hash collision dispatches the
    wrong handler with no diagnostic. Low probability, unbounded consequence.
13. **`VREF:ON` collides with the ADC channel map.** It calls `pinMode(A7, OUTPUT)` and
    `pinMode(A4, OUTPUT)`, but `A4` and `A7` are entries 5 and 8 of `analogPins[]`. After
    `VREF:ON`, `VOLTAGE5?` and `VOLTAGE8?` read pins configured as outputs. Also, using a GPIO as
    a "voltage reference" gives you the MCU's supply rail plus its output impedance, which is not
    a reference.
14. **`while (!Port);` in `setup()`.** Harmless on the Due's `Serial` (UART, always truthy) but a
    permanent hang if the port is ever switched to `SerialUSB`, which the commented-out lines
    invite. And crucially, everything before `ConfigureHardware()` runs with `/ON` floating.
15. **9600 baud.** A 1000-sample averaged query already costs ≥50 ms; the transport adds more.
16. **`String` used in command paths** on a heap-fragmenting embedded target; the TODO notes it.

---

## 7. Power architecture, and the module variant it implies

Three rails, **none generated on this board**:

| Rail | Source | Users | Notes |
|---|---|---|---|
| **+5 V** | Arduino header P1-5 (Due/Mega on-board regulator) | `M1.1`, `M2.1` (module +VIN), J5-3, J6-3 (external relay module VCC) | 0.635 mm tracks, 23 segments, **no decoupling at all** |
| **+3.3 V** | Arduino header P1-4 | **nothing** — net 41 has one pad and zero track segments | Dead net; the Due's own 3.3 V logic is what `vcc = 3.3` refers to |
| **+24 V** | *external*, in through J2-1 / J4-1 | `U1.4`, `U2.4` (op-amp V+), Q1 collector | `D1` (the +5 V → +24 V substitute path) is **DNP**, so +24 V is mandatory for the analogue chain |
| `Vin`, `IOREF` | P1-8, P1-2 | nothing | dead nets |

**Module variant implied: the 0.5 W / 5 V family.** `M1` pin 1 is on the +5 V net, and the
firmware uses `bias_maxvoltage = 2.5` (V_ref) with `bias_maxsetting = 200`. Decoding the item code
per manual Table 3 (I_nom in nA, two significant digits + number of zeros): `255` = 25 × 10⁵ nA =
**2.5 mA**; `002` = **200 V**; `05` = **5 V input**. The documentation states it outright:
**`AP002255p05` or `AP002255n05`** — 200 V, 2.5 mA, 5 V in, 0.5 W, polarity factory-fixed.

Load implication: the manual gives I_in < 180 mA at V_nom with load for the 0.5 W family. That
current is drawn from the Arduino's 5 V rail — shared with the relay module and, on USB power,
with the 500 mA host budget — through 0.635 mm traces, with no bulk capacitance anywhere, on a
board with no ground plane. For our two-module bipolar design the equivalent figure is
**2 × 180 mA = 360 mA of 5 V**, or 2 × 150 mA of 12 V if we move to the 1 W family. That is a
dedicated regulator, not a header pin.

---

## 8. What the old board got right (evidence — it works; keep these)

1. **The `/ON` + VSET control split.** Enable and level are independent. Do not merge them.
2. **`R46` — the 100 Ω VSET pull-down.** The single best idea on the board. It converts the
   module's fail-dangerous internal 10 kΩ pull-up to V_ref into a fail-safe. §5.4.
3. **A zener clamp footprint on VSET (`D2`, fitted).** The correct place to bound the output is
   the *set* input, because the module has no internal limit. Keep the concept; fix the series
   impedance (`R39` = 0 Ω is wrong).
4. **A series resistor in the HV output (`R43`).** Right idea (fault current limiting, and it
   makes a downstream zener workable). Wrong package.
5. **Gain constants derived from component values and cross-checked against the schematic.**
   0.69299 vs 0.692971 — three independent sources agree. This is what a maintainable analogue
   chain looks like.
6. **A real SCPI parser with `*IDN?` and numeric suffixes.** §6.2.
7. **Solder-jumper option straps for pin assignment** (`JP1`–`JP4`, `SolderJumper_3_Bridged12`) and
   an explicit DNP strategy that lets one layout serve 3.3 V and 5 V hosts and either PWM or DAC
   drive. That is genuine, cheap configurability.
8. **The symbol's pin mapping is exactly right.** `alpha-shield.lib`, `DEF AP0vv255x05`:
   1 `+VIN`, 2 `VSET`, 3 `GND`, 4 `~ON`, 5 `Vmon`, 6 `HV`, 7 `GND` — matches manual Table 4
   pin-for-pin, including the overbar on `/ON`.
9. **A designer's write-up that states the known limits honestly** — including "the top output
   voltage will be approximately 180 V" and the ±7 V power-on transient. Facts we would otherwise
   have had to discover on the bench.
10. **The 3D model placement is right even though the 2D outline is wrong.** In
    `ISEG_HV_MODULE.kicad_mod` the fab/silk/courtyard body is drawn **centred** on the pin array
    (±19.812 × ±7.874), which is 0.6 mm out along the long axis and ~0.23 mm out along the short
    axis versus manual Figure 1. But the STEP model offset is `(-19.2278, -7.62, 0)` — and 19.199
    and 7.62 are precisely the *asymmetric* body edges from the manual, not the centred ones. So
    `alpha-shield.3dshapes/ISEG_HV_MODULE.step` was placed against the true drawing and is
    probably reusable. (KiCad's 3D-offset sign convention was not verified this session; check
    before trusting the axis assignment.)

---

## 9. Improvements for the new board — prioritised by consequence

Ranked by what happens if we do not do it. Cost estimates are `[recalled]` order-of-magnitude
figures for a one-off lab build, not quotes.

---

### P0 — safety and correctness. Not optional.

**I-1. Enforce the both-off / one-on interlock in a physical structure, not in two GPIOs.**
*Old board:* one enable net for the design, and in copper M2's `/ON` permanently tied to GND —
"both on" is not merely reachable, it is the wiring.
*Why it matters:* two opposite-polarity modules simultaneously enabled into one combiner node is
a direct short of +V_nom to −V_nom through whatever the combiner is, and it is exactly the state
the brief forbids.
*Instead:* make "both enabled" un-representable. Candidates, in order of preference:
(a) a single DPDT/changeover relay whose contact geometry physically cannot connect both modules —
the interlock is the mechanism; (b) a single SPDT selection line feeding complementary `/ON`
drivers through an inverter, so one signal has one state; (c) if separate lines are unavoidable,
an AND/exclusion gate in hardware plus a monitored dead-time. In every case the *disabled* state
must be the state with no controller present.
*Cost:* a changeover relay with adequate HV contact rating plus its driver, ~$8–20 and ~400 mm²;
gate-based options ~$1 and ~50 mm². Both are cheaper than the failure.

**I-2. Pull every `/ON` net to the OFF state at the module's own supply, and level-shift it.**
*Old board:* `/ON` floats from reset until `ConfigureHardware()` runs, and the manual says
"LOW **or n.c.** ⇒ HV ON". The board comes up energised, every time.
*Why it matters:* our default must be de-energised. ESP32 boot, brownout, firmware crash, and an
unplugged controller must all mean OFF.
*Instead:* pull-up to +5 V (or +12 V) on each `/ON`, sized against the module's TTL input, driven
by an open-drain low-side device that must be *actively* pulled low to enable. Add a hardware
watchdog/heartbeat that releases the pull-down if the MCU stops toggling it.
*Cost:* two resistors, two small MOSFETs, one retriggerable monostable or supervisor. ~$3.

**I-3. Give the HV net its own netclass and make the clearance rule executable.**
*Old board:* one global 0.2 mm rule; the 200 V net runs at **0.200 mm** from `Serial3 TX` and
`I²C SDA`, at *exposed pads*. DRC passes. §5.1.
*Why it matters:* this is precisely the failure our `CLAUDE.md` non-negotiable anticipates —
"HV creepage/clearance encoded as DRC netclass rules, so the check is executable". The old board
proves what happens without it: a clean DRC report on an unsafe board.
*Instead:* a dedicated `HV` netclass with clearance set from IPC-2221 for our chosen V_nom
(re-derived from the standard, not from memory), applied in the generator, plus a bespoke check
that re-measures the copper independently — the parser written for this audit
(`hv_clear.py`) is the seed of that check. Consider also: mask-free HV keepout, milled slots at
the tightest crossings, and routing HV on one layer with no signals on the opposite layer beneath.
Remember the playbook's most expensive fact: a netclass must carry its schematic fields or it
silently breaks eeschema connectivity.
*Cost:* generator work only, plus board area. Zero BOM cost.

**I-4. Provide a defined bleed path on the HV output, always present, not switched.**
*Old board:* net 86 has three pads — `R43.1`, `J1.1`, `D6.1` (DNP). No bleed resistor exists. §5.3.
*Why it matters:* the brief requires "a defined discharge/bleed path on changeover and on disable".
Disabling a module drives its own output to zero but says nothing about the cable and detector
capacitance on our side of the connector.
*Instead:* a permanent HV bleed to ground sized for a defined time constant at the output node
(a series string of HV-rated resistors — never a single 0805), *plus* an active crowbar/discharge
switch asserted on disable and on every polarity changeover, with the discharge complete before
the opposite module can be enabled. The changeover sequence must be
`disable → discharge → verify < threshold → switch → enable`, and the "verify" step must use the
independent monitor (I-5), not a timer.
*Cost:* HV resistor string ~$3, HV-rated MOSFET/opto/reed for the active discharge ~$5–15.

**I-5. Measure the output voltage independently, and make the readback a measurement.**
*Old board:* `BIAS?` returns `bias_settings[0]` — a number written by `SetBias` and never
compared with reality. It reports 200.00000 for a supply that cannot exceed 182.94 V. §4, §2.3.
*Why it matters:* the brief requires "output voltage monitored INDEPENDENTLY of the module
readbacks". A supply that can report a voltage it is not producing cannot be trusted to report a
voltage it *is* producing, and cannot detect an open connector, a dead module, or a wrong-polarity
handoff.
*Instead:* an HV resistive divider on the combined output node (HV-rated series string, guarded,
with defined loading against our current budget) into a buffered, protected ADC — ideally a
separate ADC from the module VMON path so a single failure cannot corrupt both. `BIAS?` returns
the measurement; a separate query returns the setpoint; the firmware raises an error-queue entry
when they disagree beyond tolerance. Keep the module VMON too — two disagreeing sensors is
information.
*Cost:* divider string + precision buffer + a 16-bit ADC, ~$10–25 and ~600 mm².

**I-6. Bound the output in hardware against V_set overrange.**
*Old board:* `D2` fitted on VSET (good), but with `R39 = 0 Ω` in series, so the clamp has no source
impedance and cannot survive an op-amp saturation from the +24 V rail. `D6`, the HV-side clamp,
is DNP. §5.2.
*Why it matters:* the manual is unambiguous — *"Attention! Output voltage is internally not
limited! At V_set > 2.5 V ➜ V_out > V_nom is possible!"* A firmware `constrain()` does not survive
a firmware bug, a stuck DAC, or a broken solder joint.
*Instead:* (a) run the VSET driver from a rail that *cannot* exceed V_ref — a 2.5 V/5 V-referenced
buffer, not a 24 V op-amp; (b) keep a precision clamp on VSET with a real series resistor sized to
survive driver saturation; (c) fit the HV-side clamp, correctly polarised per module, in an
HV-rated package. The clamp must be *fitted*, not a footprint.
*Cost:* ~$4 and a design decision about the analogue supply rail.

---

### P1 — correctness and trustworthiness of the instrument.

**I-7. Drive VSET from a real DAC, and cover the full range.**
*Old board:* 12-bit PWM → 2.3 Hz RC → 1.59 Hz Sallen-Key. **1.093 s to settle to 0.1 %**, 3.3 %
overshoot, and −158 dB of ripple rejection where −60 dB would do. Full scale reaches only
**91.5 %** of V_nom, and the firmware clamps to 4095 counts without telling anyone. §2.2, §2.3.
Two DAC footprints (`R2`, `R6` from `DAC0`/`DAC1`) exist on the board and are DNP — the designer
even wrote "a filter is not necessary if a DAC output is used".
*Why it matters:* a second of settling per setpoint makes a bipolar sweep painful and makes
"readback agrees with a DMM" a timing puzzle. The 8.5 % range shortfall is a silent lie.
*Instead:* an external I²C/SPI DAC (≥16-bit, internal or external reference matched to the module
V_ref) driving a unity-gain buffer with a modest anti-glitch RC (~100 Hz, tens of ms), scaled so
that DAC full scale maps to **exactly** V_ref with a small margin, and a firmware assertion that
the commanded code is reachable. Then confirm the mapping on the bench against a DMM before
trusting it.
*Cost:* ~$4–8 per channel. It *removes* the LM324, the Sallen-Key, and eight passives per channel.

**I-8. Decouple the module supply as the manual requires, and give the board a ground plane.**
*Old board:* zero capacitors on the +5 V net; `(zones 0)` — no copper pours at all; GND is
38 track segments. Manual note 2: *"Blocking circuit is recommended … with 22 µF near pin +VIN"*.
§5.5, §7.
*Why it matters:* the module is a switching converter drawing up to 180 mA in bursts, on a board
whose analogue readback needs sub-mV resolution, with no return-current plane.
*Instead:* 22 µF bulk plus 100 nF within a few mm of each `+VIN`; a solid ground plane; separate
analogue and module return paths meeting at one point; and a dedicated regulator for the module
rails rather than a header pin shared with the MCU.
*Cost:* ~$2 of capacitors, one regulator (~$3), and layer discipline.

**I-9. Give the firmware an error queue and SCPI-99 mandated commands.**
*Old board:* unknown commands answer with silence; no `SYSTem:ERRor?`, no `*RST`, no `*CLS`,
no status registers. §6.3 items 4 and 11.
*Why it matters:* every host-side mistake becomes a read timeout, and a failed command is
indistinguishable from a hung instrument — during HV operation.
*Instead:* implement the SCPI-99 mandated set (`*CLS`, `*ESE`, `*ESR?`, `*IDN?`, `*OPC`, `*OPC?`,
`*RST`, `*SRE`, `*STB?`, `*TST?`, `*WAI`) plus `SYSTem:ERRor[:NEXT]?`, and make `*RST` a genuine
safe state: both modules disabled, discharge asserted, setpoints zeroed. Add
`SYSTem:VERSion?`. `references/Phys439-alpha-lab/references/scpi-99.pdf` is on disk.
*Cost:* firmware only; roughly a day.

**I-10. Fix the memory-safety and bounds defects before reusing any of this code.**
*Old board:* unbounded serial write into `char msg_buffer[64]`; `analogPins[-2]` on a bare
`VOLTAGE?`; command table one slot from a silent overflow. §6.3 items 8, 9, 10.
*Why it matters:* these are reachable from the control port on a device that commands high voltage.
*Instead:* if we reuse Vrekrer, take a current upstream release and re-audit it, or write a small
purpose-built parser. Bounds-check every suffix. Reject over-long lines with an error-queue entry
rather than writing them. Treat the control port as untrusted input.
*Cost:* firmware only.

**I-11. Make command handlers non-blocking, and separate acquisition from the command loop.**
*Old board:* `delay(50)` + 1000 `analogRead` calls inside query handlers; the instrument is deaf
for the duration. §6.3 item 7.
*Why it matters:* during a polarity changeover we need to be *sampling continuously*, and we need
`*RST`/abort to be honoured immediately.
*Instead:* a periodic acquisition task (timer or FreeRTOS task on the ESP32) maintaining filtered,
timestamped readings; query handlers return the latest value and never block. Every published
reading carries its timestamp and its age.
*Cost:* firmware architecture; the ESP32 makes this easy.

**I-12. Fix the ISEG footprint's body outline, and mark the HV pad.**
*Old board:* `ISEG_HV_MODULE.kicad_mod` draws the body centred on the pin rectangle
(±19.812 × ±7.874 mm), 0.6 mm out along the long axis and ~0.23 mm along the short axis versus
manual Figure 1. Pad 6 (HV) is identical to every other pad: 1.778 mm, `*.Cu *.Mask`, no local
clearance, nothing that would drive a rule. §8 item 10.
*Why it matters:* a 0.6 mm outline error is a mechanical-fit and courtyard-collision risk in an
enclosure, and an unmarked HV pad is how I-3 gets forgotten.
*Instead:* generate the footprint from the manual dimensions with the correct asymmetric body
offset; give pad 6 a local clearance override and a mask/keepout annotation; add a fab-layer HV
marking; carry the corrected outline into the courtyard. Reuse the existing STEP model, which
already sits at the right origin. Note in `DECISIONS.md` that the reference footprint's outline
error is *the* reason we generate our own.
*Cost:* generator work only.

---

### P2 — quality of the instrument.

**I-13. Ramping with a commanded slew rate, and a state machine for polarity changeover.**
*Old board:* setpoints are steps into a 1.1 s filter. No ramp, no changeover sequence, no
verification.
*Instead:* `VOLTage:SLEW` in V/s; a changeover state machine
(`disable → discharge → verify → switch → enable → ramp`) with every transition gated on a
*measured* condition and a timeout that fails safe. Expose the state via
`SYSTem:STATe?` so the host can see where it is.
*Cost:* firmware; some bench time to tune.

**I-14. Calibration storage and a two-point calibration procedure.**
*Old board:* nominal gains only, no trim, no storage. Module adjustment accuracy is ±1 %,
VMON accuracy 1 % × V_nom = 2 V on a 200 V part.
*Instead:* per-channel gain/offset for both the set path and each measurement path, stored in
ESP32 NVS, with `CALibration:*` commands and a documented DMM-referenced procedure. Store the
calibration date and the DMM used.
*Cost:* firmware plus an afternoon at the bench.

**I-15. Replace the 2.54 mm HV pin header with a real HV connector.**
*Old board:* `J1` = unshrouded 2.54 mm header, HV on pin 1, GND on pin 2, **0.840 mm** of bare
copper between exposed pads at 200 V, on an open shield. §5.2.
*Instead:* an SHV or MHV bulkhead connector (or, for a bare board, a shrouded HV-rated header with
adequate creepage), with the surrounding copper kept clear per I-3 and the connector body bonded
to chassis. Mechanical guarding is part of the electrical design here.
*Cost:* ~$10–20 per connector plus panel work.

**I-16. Settle the op-amp/analogue part identity, and specify offset.**
*Old board:* `LM324` in the schematic, `LT1014` in the PDF, `"LM324,LT1014"` in one BOM row.
Unbuildable as-is, and the two parts differ by ~50× in input offset. §5.5.
*Instead:* every part in our generator's BOM gets one MPN, and the offset/drift budget for the
set path and the measurement path is written down in `DECISIONS.md` with the resulting HV error
in volts.
*Cost:* none; it is a discipline.

**I-17. Never let the CAD artifact and the hardware diverge again.**
*Old board:* six parts and two copper modifications exist only as schematic annotations; the
`.kicad_pcb` describes a board nobody uses. §1 item 4.
*Why it matters:* our audit of the *safety-critical* pull-down R46 had to come from a text note.
Anyone reading only the layout would conclude the board has a fail-dangerous VSET node.
*Instead:* the rule already in `CLAUDE.md` — generated CAD is a build artifact, every defect is
fixed in the generator and regenerated, generator and artifact committed together. A bodge on the
bench becomes a generator change the same day, or it does not exist.
*Cost:* none, if we hold the line.

---

## 10. Discrepancies flagged, not resolved

1. **The manual specifies a "Current monitor accuracy 1 % • I_nom" (Table 1, p. 7) but Table 4
   (p. 9) lists seven pins with no current-monitor output.** Re-read directly from
   `references/iseg_manual_APS_en.pdf` this session. The 7-pin part exposes `+VIN, VSET, GND,
   /ON, VMON, HV, GND` and nothing else. Either the current-monitor row is inherited boilerplate
   from a larger iseg family, or there is an unpinned/optional monitor. **Do not design around a
   current readback from these modules until iseg confirms.** If we need output current, we must
   measure it ourselves — which the brief's "monitored independently" requirement points at anyway.
2. **`R46` = 100 Ω is described in the designer's documentation as sinking the module's
   "10 kΩ pullup to 5 V"**, while the manual gives V_ref = 2.5 V for the 0.5 W family and defines
   the pull-up through `R_set = V_out · 10 kΩ / (V_nom − V_out)`. The designer's own measured
   result ("output voltage can be set under 2 V") is consistent with 2.5 V, not 5 V. Treated here
   as V_ref = 2.5 V. Worth one multimeter measurement on a real module before we size our own
   pull-down.
3. **PWM carrier frequency** on Arduino Due `analogWrite(D5, …)` is taken as ~1 kHz `[recalled]`.
   Not verified from any file. The ripple-rejection conclusion is insensitive to it.
4. **IPC-2221 Table 6-1 values** in §5.1 are `[recalled]`. The standard is not on disk. They must
   be re-derived from the actual document before they are written into our netclass rules, because
   that number becomes an executable gate.
5. **`R43` 0805 voltage/power ratings** (150 V, 0.125 W) are `[recalled]` typical values, not the
   ratings of the specific part fitted, which is not identified beyond "10K".

---

## Appendix A — files read

```
references/Phys439-alpha-lab/README.md
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.sch          (root, rev 1.0a)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/double_lpf.sch            (instantiated ×2)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/bias_supply.sch           (ORPHAN)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/PWMFilter.sch             (ORPHAN)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.kicad_pcb    (v20171130, 5.1.5)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.csv          (BOM)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.lib          (symbols)
references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.pretty/ISEG_HV_MODULE.kicad_mod
references/Phys439-alpha-lab/code/alpha-shield/alpha-shield.ino
references/Phys439-alpha-lab/code/alpha-shield/Vrekrer_scpi_parser.{h,cpp}
references/Phys439-alpha-lab/doc/PHYS 439 alpha lab shield schematic.pdf        (rev 1.0, 3 pages)
references/Phys439-alpha-lab/doc/PHYS 439 alpha lab shield documentation.docx
references/iseg_manual_APS_en.pdf                                              (v2.5, pp. 7-9)
```

## Appendix B — analysis scripts

Written and executed this session; stdlib-only Python 3, run under `PY_KICAD` for convenience but
with no KiCad dependency. Kept in the session scratchpad, not in the repo. `hv_clear.py` is the
prototype for the executable HV-clearance check called for in I-3 and should be promoted into
`hardware/hvctl/checks/` when we have a board to check.

| Script | Purpose |
|---|---|
| `sexp.py` | s-expression tokenizer/parser for KiCad 5 `.kicad_pcb`; extracts nets, pads (with `roundrect_rratio`), tracks, vias, footprints |
| `hv_clear.py` | exact pad/track/via shape geometry and copper-to-copper distance; HV net identification and clearance scan |
| `hv_clear2.py`, `hv_detail.py` | full-chain scan, IPC comparison, offending-neighbour identification, DRC self-check |
| `power.py` | power-net membership and decoupling audit |
| `filter_math.py` | DC transfer, poles, step response by RK4 **and** closed-form residues (cross-checked), ripple rejection, range reachability |
| `render_sch.py`, `zoom.py` | `fitz` rendering of the schematic PDF |
