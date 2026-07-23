# Control, Comms and ESP32 Architecture Study

**Project:** iseg bipolar HV controller · **Phase:** 1 study · **Written:** 2026-07-23 (pre-G0) ·
**Pinned to the G0 answers:** 2026-07-23 (post-G0)
**Status:** study → **decision**. Numbers are reproducible (see Appendix A). Nothing here is fabricated
or built yet.

> ## ⬛ THIS DOCUMENT WAS WRITTEN PARAMETERISED. IT IS NOW PINNED.
>
> Session 1 wrote this study **over a family of modules** (0.5 W @ 5 V, Vref 2.5 V **vs** 1 W @ 12 V,
> Vref 5 V) and **over five voltage classes** (200 / 400 / 600 / 800 / 1000 V), because the part was
> unfrozen. **GATE G0 froze it on 2026-07-23.** Every table below that spans families or classes now has
> **exactly one row or one column that is real.** The rest is retained as the derivation — **do not read
> a struck row as an option.**
>
> ### The pinned parameter set — `AP010504P05` + `AP010504N05`, both owned (G0-A2)
>
> | | Pinned value | Consequence in this document |
> |---|---|---|
> | `Vnom` | **1000 V** | set-path gain = `Vnom/Vref` = **400 V/V**. The 1 kV row is the only row of §1.2, §1.3, §1.4, §2.3. |
> | `Inom` | **0.5 mA** (`Iout` ≤ 0.75 mA) | §2.4: the **`AP010504x05`** row is the only row — and it sits **exactly at the 1.00 % loading limit**. |
> | `Vref` | **2.5 V ±1 %** | **NOT 5 V.** Set/monitor full scale 0…2.5 V. **This is the number that makes §1.1 and §3 dangerous — see below.** |
> | `Vin` | **5 V** (4.5–5.5 V), `Iin` < **180 mA** loaded | **NOT 12 V.** `/ON` may be pulled up to `+VIN` directly (5 V is inside the 2.5–5.5 V HIGH window). |
> | Specified range | **2 %·Vnom < Vout ≤ Vnom, i.e. only above 20 V** | Below 20 V the output is **UNSPECIFIED, not merely worse.** |
>
> ### ⬛ The one change that is not a substitution — **the 3.3 V hazard is now REAL**
>
> Session 1 recommended the **1 W / 12 V family specifically because Vref = 5 V is immune to a 5 V logic
> rail**. **G0-A2 answered the other way.** With **Vref = 2.5 V** and a **3.3 V** ESP32:
> `3.3 / 2.5 = 132 %` of nominal ⇒ **≈1320 V**, on an input the datasheet says is *"internally not
> limited"* with **no stated ceiling** — composed with an internal 10 kΩ pull-up to Vref (**open `VSET`
> = FULL SCALE**) and active-low `/ON` (**floating `/ON` = HV ON**), so **the module's un-driven default
> state is ENERGISED AT OVER-RANGE.**
> ⇒ **§1.7's "free overvoltage protection by construction" is no longer a bonus. It is a PRIMARY SAFETY
> ELEMENT and requires its own executable verification** (`DECISIONS.md` PART-33, ARCH-06; `SCOPE.md` S-8).
>
> ### Three further answers this document was not written against
>
> - **G0-A3 — both serial AND network, FULL WRITE AUTHORITY on both.** **§4.3's recommendation
>   (read-only network, write behind a physical switch) is OVERTURNED.** See §4.3.
> - **G0-A4 — SCOPE CHANGE: switchable single-pseudo-bipolar-output *or* two independent unipolar
>   outputs, both energisable at once.** **§2.8 (channel map), §3 (interlock), §4.6 (command set) and
>   §5 (state machine) are all incomplete as written.** Each carries a post-G0 note at the gap.
> - **G0-A5 — THE MODE IS SET BY A PHYSICAL SWITCH. There is NO mode relay and NO `MODE` command.**
>   This lands hardest on **§3.3a** (the mode-aware interlock — the algebra is **unchanged**, but
>   `MODE_POS` now comes from a **switch aux pole**, and **`MODE_CMD` ceases to exist as a writable
>   bit**, making the attack row *unreachable* rather than *defeated*), on **§4.7a** (the mode surface
>   is **read-only**), on **§5.1** (Gap 1's mode-change transition is **deleted**, not designed), and on
>   **§6.1/§6.4**. Each is annotated in place.
>
> ### ⬛ TERMINOLOGY (G0-A5) — the human's words, used from here on
>
> **"pseudo-bipolar"** = mode 1, one output, polarity changed **by switching across zero**. Honest,
> because G0-A1 means this instrument does **not** traverse zero smoothly.
> **"unipolar / dual-output"** = mode 2. Pre-A5 text saying "bipolar combined" means **pseudo-bipolar**.

**Primary source:** iseg APS series technical documentation v2.5, 2024-08-20 —
`references/iseg_manual_APS_en.pdf` (Table 1 p.7, Table 2 p.8, Table 4 p.9, Figure 2 p.9).
**Reference board:** McGill PHYS 439 alpha-lab shield — `references/Phys439-alpha-lab/`.

### Evidence key

| Tag | Meaning |
|---|---|
| `[verified-artifact]` | I opened the file/PDF on disk this session and read the value out of it |
| `[verified-run]` | I executed the computation this session; the number is the program's output |
| `[web-verified]` | Read this session from the **manufacturer's own** page — specs only, **not** stock/availability |
| `[recalled]` | From background knowledge. **Unverified. Do not commit a BOM line to it.** |
| `[unverified-MPN]` | Part number not checked against any live distributor page. Availability unknown. |

> **No MPN in this document has been checked against a live distributor page.** Every part number
> is therefore `[unverified-MPN]` for *availability*, even where the *specification* is `[web-verified]`.
> Availability checking is a G0 action item, not a Phase-1 study output.

---

## 0. Three facts about the module that drive every decision below

Two of these are in the spec tables. The third is only in the *drawing* on manual p.9, was not in the
project's extracted ground truth, and changes several answers.

### 0.1 The `/ON` default is dangerous, and it is the *documented* behaviour

> `/ON: = 0 (LOW or open) ➜ VOUT according setting` — Table 1, p.7 `[verified-artifact]`

A floating `/ON` pin means **HV ON**. Every fail-safe below is built around inverting that default.

### 0.2 An open `VSET` node commands full-scale output

Table 1's `Rset = Vout • 10 kΩ / (Vnom − Vout)` alternative implies a 10 kΩ pull-up to the internal
reference. **Figure 2 confirms it explicitly** `[verified-artifact]`. An open VSET → `Vout = Vnom`.
Combined with 0.1: *an unpopulated board with both signals floating is a board commanding full-scale HV.*

### 0.3 Figure 2 (manual p.9) — the module's internal input network

I rendered the vector figure at 6× and read it directly `[verified-artifact]`:

```
                    +-----------------------------------------+
   VMON  o---[ 20k ]--+                                       |
                    |         +----+----(REF)                 |
                    |       [10k]  |    2.5 V / 5 V           |
                    |         |    |                          |
   VSET  o----------+---------+--[100k]--+----+               |
                    |                    |    |               |
   /ON   o------------------------> (switch)  |  1uF          |
                    |                    |    |               |
                    |                   GND  GND              |
                    +-----------------------------------------+
```

Four numbers nobody was designing against:

| Finding | Value | Consequence |
|---|---|---|
| VSET internal pull-up | **10 kΩ to REF** | Driver source impedance is a *direct offset error* — §1.4 |
| VSET internal filter | **100 kΩ + 1 µF → τ = 100 ms** | The module low-passes our set point at **1.59 Hz**. Sets all ramp timing. |
| `/ON` mechanism | switch **grounds the internal set node** | Turn-off dumps the 1 µF; turn-on re-charges through 100 kΩ |
| VMON output impedance | **20 kΩ series** | VMON is *not* buffered. Cannot drive a switched-cap ADC directly — §2.6 |

The 100 ms internal pole is the single most useful number in this document. It says:

- The set-point path never needs to be fast. Full-scale settling to 16-bit is **1.11 s**, dominated
  entirely by the module `[verified-run]`.
- Therefore an RC filter on a PWM set point costs **almost nothing in speed** (§1.5) — the classic
  objection to PWM DACs does not apply here.
- Therefore a logic race on `/ON` lasting nanoseconds is *physically* harmless (§3.5).

---

## 1. Set-point path — PWM vs. a real DAC

### 1.1 Which ESP32? (asked explicitly, and it matters)

**Assumed: ESP32-S3.** Justification in §4.3. The DAC question resolves as follows:

| Variant | Internal DAC | Notes |
|---|---|---|
| ESP32 (classic) | **2 × 8-bit**, GPIO25/26 `[web-verified, espressif docs]` | 8-bit ⇒ **3.92 V per LSB** at 1 kV. Unusable. Also noisy and rail-referenced. |
| ESP32-S3 | **None** `[web-verified, espressif docs]` | |
| ESP32-C3 | **None** `[recalled]` | |

**This is a non-issue.** Even the one variant that *has* a DAC has one too coarse to use: 8 bits gives
**5.1 codes across the module's entire ±1 % accuracy band** `[verified-run]`. An external DAC is
required regardless of variant, so "S3/C3 have no DAC" costs us nothing. Do not let it drive variant choice.

> ### ⬛ POST-G0: the ESP32-internal-DAC question must be re-answered, and the answer is STRONGER
>
> **Session 1 disqualified the internal DAC on RESOLUTION. G0-A2 disqualifies it on SAFETY, which is a
> different and much harder disqualification — and it would still hold at any resolution.**
>
> The classic ESP32's DAC is **referenced to its own 3.3 V rail**. The module's `Vref` is **2.5 V**
> (PART-31). Therefore:
>
> | | Internal DAC (3.3 V-referenced) | External DAC + REF5025 (2.500 V) |
> |---|---|---|
> | Full-scale output | **3.3 V** | **2.500 V** |
> | `Vout` commanded at full scale | `3.3/2.5 × 1000` = **1320 V** | `2.5/2.5 × 1000` = **1000 V** |
> | Over-range reachable? | **YES — 132 % of Vnom is a NORMAL code, not a fault** | **NO — structurally impossible** |
>
> **A 3.3 V-referenced DAC does not merely resolve badly; its top 24 % of codes command an over-range
> the datasheet says is "internally not limited" with no stated ceiling.** The over-range is not at the
> end of a fault chain — it is at the end of the *code range*. On a part with a 5 V Vref (the family
> session 1 recommended and did not get) the same DAC would have been merely coarse.
>
> **⇒ Do not use the ESP32 internal DAC. Do not use any 3.3 V-rail-referenced set-point source. Do not
> attenuate 3.3 V down to 2.5 V with a resistive divider either** — that reintroduces series resistance
> into `VSET`, which §1.4 shows is a first-order offset error (and ARCH-04 caps at **10 Ω**), *and* it
> makes the clamp depend on two resistor tolerances instead of on a rail that physically cannot be
> exceeded (§1.7, ARCH-06).
>
> **The same argument applies to the PWM fallback in §1.7** — a PWM DAC's full scale *is* the 3.3 V
> rail. §1.6 rejected PWM on **reference accuracy**; post-G0 it is also rejected on **over-range
> reachability**, which is a safety argument rather than an accuracy one. If the PWM fallback is ever
> revived, it **must** be followed by a buffer powered from the 2.500 V reference, or it commands
> 1320 V at full duty.

The ESP32 **ADC** is a separate and worse problem — §2.7.

### 1.2 Resolution table — 1 LSB expressed in volts at the HV output

~~Worst case:~~ **✅ THE CASE. G0-A2 confirms it exactly: 1 kV module, `Vset` 0…2.5 V ⇒ set-path gain
`Vnom/Vref` = 1000/2.5 = 400 V/V.** Session 1 computed this table as the *worst* case across an unfrozen
family; **it is now the only case, and no number needed rescaling.** All rows `[verified-run]`.

> **Which rows are still real.** Every "ESP32 LEDC PWM" and "classic-ESP32 internal DAC" row and the
> MCP4725 rows are **3.3 V-rail-referenced** and are therefore **disqualified on the safety ground of
> §1.1**, not merely on resolution — at full code they command **1320 V**, not 1000 V. **Only the
> "+ external 2.5 V reference" rows are live.** Of those, the **16-bit** row is the recommendation and
> the **12-bit** row is the adequate fallback (§1.7).

**Column key (post-G0):** ⛔ = **disqualified on SAFETY**, not on resolution — the source is
**3.3 V-rail-referenced**, so its top codes command **1320 V** on a 2.5 V-Vref module (§1.1).
✅ = live. **The only live rows are the "+ external 2.5 V reference" rows.**

| | Set-point source | Bits | LSB at VSET | **LSB at HV output** | ppm of FS |
|:-:|---|---:|---:|---:|---:|
| ⛔ | ESP32 LEDC PWM, 8-bit | 8 | 9804 µV | **3.92 V** | 3922 |
| ⛔ | ESP32 LEDC PWM, 10-bit | 10 | 2444 µV | **0.978 V** | 978 |
| ⛔ | ESP32 LEDC PWM, 12-bit | 12 | 610.5 µV | **0.244 V** | 244 |
| ⛔ | ESP32 LEDC PWM, 14-bit | 14 | 152.6 µV | **0.0610 V** | 61 |
| ⛔ | classic-ESP32 internal DAC | 8 | 9804 µV | **3.92 V** | 3922 |
| ⛔ | MCP4725, 12-bit, 3.3 V span attenuated to 2.5 V | 12 | 610.5 µV | **0.244 V** | 244 |
| ⛔ | MCP4725, 12-bit, using only 0…2.5 V of a 3.3 V span | 12 | 805.9 µV | **0.322 V** | 322 |
| ✅ | 12-bit DAC + external 2.5 V reference — **adequate fallback** | 12 | 610.5 µV | **0.244 V** | 244 |
| ✅ | **16-bit DAC + external 2.5 V reference — THE RECOMMENDATION** | 16 | 38.15 µV | **0.0153 V** | 15.3 |
| ✅ | 18-bit DAC + external 2.5 V reference — unnecessary | 18 | 9.54 µV | **0.0038 V** | 3.8 |

⚠ **Note the ⛔ rows are not "worse options" — they are UNSAFE options**, and two of them (12-bit PWM,
12-bit MCP4725-attenuated) have **numerically identical LSBs to the live 12-bit row**. A reader
comparing only the resolution columns would pick a disqualified part. **That is exactly the mistake
this key exists to prevent.**

Note the MCP4725 row split. **The MCP4725's reference is its own VDD** `[recalled]` — it is a
ratiometric DAC, not a precision one. Running it from 3.3 V and using only the bottom 76 % of codes
wastes 24 % of the range *and* inherits the rail's tolerance. Attenuating 3.3 V → 2.5 V recovers the
codes but not the accuracy.

> **Correction to the task premise:** the brief groups "MCP4726/DAC8551/AD5541" as 16-bit options.
> **The MCP4726 is a 12-bit part** (single channel, I²C, EEPROM, selectable VDD *or* external VREF,
> 2.7–5.5 V, 6 µs settling) `[web-verified, Microchip product description]`. It is a good *12-bit*
> external-reference DAC and belongs in the 12-bit row, not the 16-bit row.

### 1.3 Resolution vs. the module's own accuracy — what resolution actually buys

The module specifies **adjustment accuracy ±1 %** and **voltage monitor accuracy 1 %·Vnom**
(Table 1, p.7) `[verified-artifact]`. At 1 kV both are **±10 V** — **and G0-A2 confirms 1 kV, so
"±10 V" is now the number, not an example** (`DECISIONS.md` PART-34).

| Source | LSB at output | Codes inside the module's ±1 % accuracy band |
|---|---:|---:|
| 8-bit PWM | 3.92 V | **5.1** |
| 12-bit | 0.244 V | **81.9** |
| 16-bit | 0.0153 V | **1310.7** |

`[verified-run]`

**The honest reading.** Resolution beyond ±1 % buys **settability and repeatability, not accuracy** —
and that is genuinely worth something:

- **Repeatability.** The module's ±1 % is a *fixed, systematic* transfer-function error (dominated by
  its internal Vref tolerance, ±1 %, Table 1). It does not wander code-to-code. Once characterised,
  it is a calibration constant. Fine resolution lets you *return to the same output* reliably.
- **It is the resolution of the closed loop.** §2 gives us an independent monitor. A control loop can
  only correct to within one DAC LSB. So the DAC LSB, not the module's open-loop accuracy, sets the
  achievable *calibrated* accuracy.
- **Ramp smoothness.** A 3.92 V step (8-bit) into a capacitive HV load is a real `i = C dV/dt` event.

**But note the ceiling.** Because `Vout/Vnom = Vset/Vref` and *their* Vref is ±1 %, **no open-loop
accuracy better than 1 % is physically obtainable** no matter how good our DAC is. The only route to
sub-1 % absolute accuracy is closing the loop on our own monitor. That reframes §2: the independent
monitor is not merely a safety requirement, **it is the only path to accuracy**, and it converts every
static analog error in the set path (source-impedance offset, DAC gain error, attenuator ratio) from an
accuracy problem into a one-time calibration constant. This theme recurs; it is the study's central result.

### 1.4 The source-impedance trap — a first-order error most designs miss

> **◀ POST-G0: this table is pinned, not parameterised.** `Vref` = **2.5 V** and `Vnom` = **1000 V**
> (G0-A2), which are exactly the values the table was computed with. **The "open ⇒ 1000 V (full scale)"
> bottom row is now a statement about the specific modules sitting on the bench**, and it composes with
> §1.1: an open `VSET` gives 1000 V, while a `VSET` **shorted to the 3.3 V rail** gives **1320 V**.
> Both are one fault away, and neither is limited by the module.

From §0.3: VSET has a 10 kΩ pull-up to REF. Driving it from a source with output resistance `Rs`:

```
V_pin = V_drive + (Vref − V_drive) · Rs / (Rs + 10 kΩ)
```

Worst case at `V_drive = 0` (commanding zero output). All `[verified-run]`:

| Rs | Offset at VSET | % of FS | **Error at 1 kV output** |
|---:|---:|---:|---:|
| 0.1 Ω | 0.025 mV | 0.001 % | 0.010 V |
| 1 Ω | 0.250 mV | 0.010 % | 0.100 V |
| 10 Ω | 2.498 mV | 0.100 % | 0.999 V |
| 22 Ω | 5.488 mV | 0.220 % | 2.195 V |
| **100 Ω** | 24.75 mV | **0.990 %** | **9.90 V** |
| 470 Ω | 112.2 mV | 4.489 % | 44.9 V |
| 1 kΩ | 227.3 mV | 9.091 % | 90.9 V |
| 10 kΩ | 1250 mV | 50.0 % | 500 V |
| **open** | **= Vref** | **100 %** | **1000 V (full scale)** |

**Consequences, all load-bearing:**

1. A "harmless" 100 Ω series resistor in the set path — the kind you add for glitch filtering or
   short-circuit protection — costs **a full 1 % of full scale**, exactly as large as the module's own
   accuracy spec. **Keep the total series resistance from the driver to the VSET pin ≤ 10 Ω.**
2. **You cannot put the RC filter directly on VSET.** A PWM filter needs kΩ-scale resistance; that is
   a 9–50 % error. The filter must be followed by a low-impedance buffer. *This is precisely why the
   PHYS 439 board used PWM → RC → op-amp* — that architecture is correct, not incidental.
3. An **open VSET commands full scale**. Any disabled/unselected module must have its VSET
   **actively held at 0 V by hardware**, not by firmware convention. See §3.6.
4. Because we close the loop (§1.3), a *known* offset of a few volts is calibrated away. The trap is
   only fatal if it is large enough to eat the range, or unknown.

### 1.5 The RC penalty for PWM — computed, and smaller than folklore claims

ESP32 LEDC is clocked from the 80 MHz APB, so resolution and frequency trade directly:
`f_max = 80 MHz / 2^N` `[recalled — confirm against the ESP-IDF LEDC docs at G0]`.

Ripple model: square wave at VSET scale (2.5 V), D = 0.5, fundamental p-p = (4/π)·V; each pole
attenuates by `1/√(1+(2πfτ)²)`. **The module's own τ = 100 ms pole is always present** (§0.3).
Output ripple = 400 × VSET ripple. Module ripple spec: **< 30 mV p-p max**. All `[verified-run]`:

| Bits | f_PWM | External filter | Ripple at VSET | **Ripple at HV out** | vs 30 mV spec |
|---:|---:|---|---:|---:|---|
| 8 | 312.5 kHz | none | 16.2 µV | 6.48 mV | PASS |
| 10 | 78.1 kHz | none | 64.8 µV | 25.9 mV | PASS (marginal) |
| **12** | **19.5 kHz** | **none** | **259 µV** | **103.8 mV** | **FAIL — 3.5× over** |
| 12 | 19.5 kHz | τ = 1 ms | 2.11 µV | 0.845 mV | PASS |
| 12 | 19.5 kHz | τ = 10 ms | 0.211 µV | 0.085 mV | PASS |
| 14 | 4.88 kHz | none | 1038 µV | **415 mV** | **FAIL — 14× over** |
| 14 | 4.88 kHz | τ = 1 ms | 33.8 µV | 13.5 mV | PASS |
| 14 | 4.88 kHz | τ = 10 ms | 3.38 µV | 1.35 mV | PASS |

**The PWM squeeze, stated precisely:** high-frequency PWM has low ripple but useless resolution
(8-bit at 312 kHz: 6.5 mV ripple, 3.92 V per LSB); high-resolution PWM has good resolution but fails
the ripple spec unfiltered (12-bit at 19.5 kHz: 0.244 V per LSB, 104 mV ripple). You cannot have both
without an external filter, because `f · 2^N = 80 MHz` is fixed.

**Settling penalty — the surprise.** Time to settle to 1 LSB after a full-scale step,
`t = τ_total · ln(2^N)` with `τ_total = τ_ext + 100 ms` `[verified-run]`:

| Bits | τ_ext = none | τ_ext = 1 ms | τ_ext = 10 ms |
|---:|---:|---:|---:|
| 8 | 0.555 s | 0.560 s | 0.610 s |
| 12 | 0.832 s | 0.840 s | 0.915 s |
| 16 | 1.109 s | 1.120 s | 1.220 s |

A DAC with no filter at all still takes **1.109 s** to settle, because the module's 100 ms pole owns
the response. **The PWM filter penalty at τ_ext = 10 ms is +10 % on settling time.**

> **So the case against PWM is not speed.** It is (a) that the ripple/resolution squeeze forces the
> external filter anyway, which forces the buffer op-amp anyway (§1.4), so PWM saves no parts; and
> (b) **accuracy**, below.

### 1.6 The decisive argument: what sets the full-scale reference

| Set-point source | Full-scale reference | Accuracy of that reference |
|---|---|---|
| ESP32 LEDC PWM | the 3.3 V rail | LDO initial tolerance, typically ±1–3 %, plus load and temperature `[recalled]` |
| classic-ESP32 DAC | the 3.3 V rail | same |
| MCP4725 | its VDD | same |
| **DAC + REF5025** | **an external 2.5 V reference** | **±0.05 % initial, 3 ppm/°C max** `[web-verified, ti.com]` |

A PWM DAC's full scale *is* the rail. At 1 kV, a ±2 % rail is **±20 V** of full-scale gain error — worse
than the module's own ±1 %, and it moves with WiFi TX current bursts, USB load, and temperature.
A 0.05 % reference is **40× better** and, crucially, **stable**, which is what makes calibration hold.

**This, not resolution and not speed, is why PWM loses.**

### 1.7 Recommendation — set-point path

> **Use an external SPI DAC with an external precision reference. Drive VSET directly. No PWM, no RC filter, no buffer op-amp.**
>
> - **DAC8552** — dual 16-bit, SPI, **external reference input**, 2.7–5.5 V, 10 µs settling to
>   ±0.003 % FSR, on-chip rail-to-rail output buffer, lifecycle **ACTIVE**
>   `[web-verified, ti.com]` `[unverified-MPN — availability]`
> - **REF5025** — 2.500 V, ±0.05 % initial, 3 ppm/°C max, ±10 mA source/sink, **ACTIVE**
>   `[web-verified, ti.com]` `[unverified-MPN — availability]`
>
> **Dual is the right count** — two modules, two VSET pins, and the unselected VSET must be commanded
> to zero, not left open (§1.4 pt. 3).
>
> **Why no buffer op-amp:** the DAC8552 has an on-chip rail-to-rail output buffer, so its DC output
> impedance is ~Ω-class and it must sink the 250 µA the internal 10 kΩ pull-up delivers — well inside
> its drive capability `[recalled — confirm the output-impedance and sink-current numbers in the
> DAC8552 datasheet at G0; this is the one place where dropping the buffer could be wrong]`.
> Budget ≤ 10 Ω total series resistance to VSET (§1.4) — that is a short trace and nothing else.
>
> ⬛ **PRIMARY SAFETY ELEMENT — not "free protection by construction".** *(Session 1's heading was
> "Free overvoltage protection by construction"; **G0-A2 promotes it.** With Vref confirmed at 2.5 V
> against a 3.3 V MCU, and G0-A3 putting the set-point on a network-writable path, **this rail IS the
> barrier between a one-fault condition and ≈1320 V.** It gets its own verification — `SCOPE.md` S-8,
> `DECISIONS.md` PART-33 / ARCH-06.)*
>
> The DAC8552's output spans 0…VREF and *cannot* exceed VREF. Tying VREF to the 2.500 V reference makes
> `Vset > Vref` **structurally impossible**, which is a direct hardware answer to the manual's
> *"Attention! Output voltage is internally not limited! At Vset > 2.5 V ➜ Vout > Vnom is possible!"*
> `[verified-artifact, Table 1 p.7]`.
> Additionally clamp the firmware's maximum code to **98 % of full scale**: with our reference 0.05 %
> high and theirs 1 % low, `2.45 / 2.475 = 0.990` — guaranteed ≤ Vnom in the worst-case tolerance
> stack, at the cost of 2 % of range that calibration recovers anyway.
>
> **Three properties this must have, and they are now requirements rather than preferences:**
> 1. **Nothing in the set path may be powered from 3.3 V.** The DAC's VREF, its output stage, and any
>    buffer between it and `VSET` are all powered from the 2.500 V reference (or from a rail that
>    cannot exceed it). A rail-to-rail stage cannot exceed its own rail; that is the entire mechanism.
> 2. **The buffer/RRO stage may NOT be dropped as a BOM saving.** `DECISIONS.md` ARCH-32 previously
>    left this as "the one place where dropping the buffer could be wrong". **It is now resolved and
>    frozen: keep it. Dropping it is a safety regression, not a cost saving.**
> 3. **The 98 % firmware code clamp is the SECOND layer, not the first.** It is firmware, and
>    `CLAUDE.md` says firmware agreement is not sufficient. The hardware rail is the first layer.
>
> **What this does NOT protect against, stated plainly:** a fault *downstream* of the clamp — a short
> from `VSET` to the 3.3 V rail at the module pin, a broken `VSET` track (open ⇒ full scale via the
> internal 10 kΩ pull-up), or a lifted pull-down. Those are covered by ARCH-05 (pull-down **at the
> module pin**), ARCH-18 (**duplicate** every safe-state pull element), and §3.6 (the `/ON`-driven shunt
> FET) — **and by nothing else.** Layout must keep the 3.3 V domain physically away from `VSET`.
>
> **Is 16-bit necessary?** Honestly, **no.** 12-bit gives 0.244 V/LSB, already ~6× finer than the
> ±1.58 V accuracy of the monitor that closes the loop (§2.5) `[verified-run]`. 16-bit is *cheap
> insurance and smoother ramps*, not a requirement. If BOM cost or SPI channel count forces the issue,
> **MCP4726** (12-bit, external VREF, I²C) is fully adequate — but it is single-channel, so two are needed.
>
> **Fallback if an external DAC is refused:** 12-bit LEDC at 19.5 kHz → 2-pole RC (τ = 1 ms each) →
> rail-to-rail buffer op-amp → VSET. Ripple 6.9 µV at output `[verified-run]`, settling +1 %. It works.
> It is the PHYS 439 architecture and it is sound. It just costs an op-amp and a precision attenuator
> to save a $5 DAC, and it still has the 3.3 V rail as its reference.

---

## 2. Readback path

Two independent measurement chains. The brief requires the second one.

### 2.1 Per-module VMON — and the 20 kΩ that Figure 2 revealed

VMON is `0…Vref` tracking `|Vout|` 0…Vnom, accuracy `1 %·Vnom` (Tables 1 & 4) `[verified-artifact]`.

**Figure 2 shows VMON leaves through a 20 kΩ series resistor** `[verified-artifact]`. It is an
unbuffered, high-impedance output. Consequences:

- **Do not connect VMON directly to a switched-capacitor ADC input.** The ADS1115's sampling
  capacitor draws charge from a 20 kΩ source; the resulting settling error is a gain error `[recalled
  — the ADS1115 input impedance is PGA-dependent; confirm the value for the chosen FSR at G0]`.
- **Do not connect VMON directly to an ESP32 ADC pin** — same problem, worse ADC.
- **Mitigation:** a 10–100 nF capacitor at the ADC pin gives the sampling cap a local charge
  reservoir, and/or a unity-gain buffer. A buffer is cleaner and we already need op-amps (§2.4).
- The 20 kΩ also forms a convenient anti-alias pole with that capacitor: 20 kΩ · 100 nF = 2 ms.
- **VMON is per-module and one-quadrant** — it reports `|Vout|`, with no sign. Polarity must come from
  which module is enabled, i.e. from the interlock state, or from the independent monitor's sign.

### 2.2 The independent output monitor — divider design

**Requirement (brief):** output voltage monitored independently of the module readbacks.

Design target: bipolar ±1 kV → an ADC input, on a single supply, from one output node.

**Topology — a three-resistor summing divider, read differentially.** A plain divider to ground
produces a *negative* tap for negative HV, which no single-supply ADC can accept
(ADS1115 absolute input limit is GND − 0.3 V). So inject an offset:

```
   HV_OUT ──[ R1 = 200 MΩ ]──┬── TAP ──> buffer ──> ADC IN+
                             │
                     R2 = 402 kΩ ──> GND
                             │
                     R3 = 402 kΩ ──> +2.500 V (REF5025)

   ADC IN− <── buffer <── the same +2.500 V through a matched 402k/402k divider
                          (= the TAP potential at HV = 0)
```

The differential reading is then `HV × ratio` directly — bipolar, sign-correct, with a common mode
sitting comfortably mid-rail. Values `[verified-run]`:

| Quantity | Value |
|---|---|
| Divider ratio | 1.00399 × 10⁻³ = **1 : 996** |
| Tap common mode at HV = 0 | **1.2487 V** |
| Tap swing for ±1000 V | **±1.0040 V** |
| ADS1115 FSR to use | **±2.048 V** → **2.04× headroom** |
| Overvoltage measurable before ADC clips | **±2040 V** |
| Source impedance at tap | **200.8 kΩ** → **buffer mandatory** |

The 2× headroom is not slack — it is what lets the monitor **see** the "output voltage is internally
not limited" overvoltage condition instead of railing and reporting a plausible full-scale number.

### 2.3 Resistor selection — voltage rating is binding, and the obvious parts fail

I extracted the **Yageo RC-series datasheet** and read the table `[verified-artifact]`:

| | 0201 | 0402 | 0603 | 0805 | 1206 | 1210 | 2010 | 2512 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Power @ 70 °C | 1/20 W | 1/16 W | 1/10 W | 1/8 W | 1/4 W | 1/3 W | 3/4 W | 1 W |
| **Max working voltage** | 25 V | 50 V | **50 V** | 150 V | 200 V | 200 V | **200 V** | **200 V** |
| Max overload voltage | 50 V | 100 V | 100 V | 300 V | 400 V | 400 V | 400 V | 400 V |

**Two corrections to widely-repeated folklore:**

1. **0603 is 50 V in this series, not 75 V.**
2. **2010 and 2512 are 200 V — the same as 1206.** Going to a larger chip buys **power, not volts.**
   Since our dissipation is milliwatts (below), *upsizing the package is entirely wasted.*

Minimum series count from working voltage alone, and at 2× derating `[verified-run]`:

| Full scale | 0805 (150 V) min / 2× derate | 1206 (200 V) min / 2× derate |
|---:|---:|---:|
| 200 V | 2 / 3 | 1 / 2 |
| 400 V | 3 / 6 | 2 / 4 |
| 600 V | 4 / 8 | 3 / 6 |
| 800 V | 6 / 11 | 4 / 8 |
| **1000 V** | **7 / 14** | **5 / 10** |

**But the RC series cannot be used at all**, for two independent reasons `[verified-artifact]`:

- **Resistance range.** RC's E96 ±1 % range tops out at **2.2 MΩ**. A 200 MΩ top leg would need
  **≥ 91 resistors in series** `[verified-run]`. Not a design.
- **Stability.** RC's own environmental table: life 1000 h at RCWV → **±(1 % + 0.05 Ω)**; moisture
  1000 h → **±0.5 %**. A thick-film RC string drifts **~1 %** — exactly as badly as the module's own
  1 %·Vnom monitor. It would fail to be an *independent, better* check, which is the entire point.

**Use a purpose-built HV resistor.** The string count then collapses:

> **Top leg: 2 × Vishay CRHV1206, 100 MΩ, ±1 %, 100 ppm/°C, 3000 V, 0.3 W**
> `[web-verified — CRHV is 1206…2512, up to 3000 V, up to 50 GΩ, ±1 %, ±100 ppm/°C, stability < 0.5 %]`
> `[unverified-MPN — availability]`
>
> - 500 V per element at 1 kV FS → **6× voltage margin** `[verified-run]`
> - 2.5 mW per element vs 300 mW rating → **120× power margin** `[verified-run]`
>
> **Voltage rating was always the binding constraint. Buying the rating in a part is far cheaper
> than buying it in series.** 2 parts instead of 14.

**The precision alternative, and why it usually loses here.** The *right-looking* part is the
**Caddock USVD** ultra-precision divider network: 100:1 or 1000:1 ratio, 450–2000 V, ratio tolerance
**±0.01 %**, ratio TCR **±2 ppm/°C**, VCR **0.02 ppm/V** `[web-verified, caddock.com]`
`[unverified-MPN]`. Its 1000:1 ratio is exactly what §2.2 independently derived. **But its total
resistance is 1–20 MΩ** `[web-verified]`, and that is disqualifying at high voltage — see §2.4.

### 2.4 Loading — a monitor that eats the supply is a design error

Criterion adopted: **the monitor may draw ≤ 1 % of the module's Inom.** All `[verified-run]`:

> ### ⬛ POST-G0: ONE ROW OF THIS TABLE IS REAL, AND IT IS THE WORST ONE
>
> **G0-A2 selects `AP010504x05` — the bolded row.** Everything above and below it is retained as the
> derivation. Note what that means:
>
> - **The 200 MΩ CRHV divider draws exactly 1.00 % of Inom — precisely at the adopted budget, with
>   ZERO margin.** Session 1 flagged this as the reason 1 kV / 0.5 mA was the deliberate worst case.
>   **It is now the actual case.** The remedy session 1 offered (*"if that module is selected, raise R1
>   to 300–400 MΩ and accept the leakage penalty of §2.6"*) is **no longer a contingency — it is a live
>   design decision that must be made at G1**, and its cost is real: §2.6 shows a 10 GΩ surface path
>   already gives **20 V of error at 1 kV** on an uncoated board, and raising R1 makes that worse.
> - **The Caddock USVD is now definitively OUT.** At the selected part it draws **10.00 % of Inom**.
>   Its disqualification was previously conditional on the class; **the condition is met.**
> - **The 1 W / 12 V half of this table is DEAD, not merely un-chosen** — there is no 12 V family on
>   this board (`DECISIONS.md` PART-30). Do not read those rows as alternatives.
> - ⬛ **G0-A4 DOUBLES THIS BUDGET LINE.** Dual-unipolar mode needs **two** independent monitor strings,
>   one per output — each loading **its own** module by that same **1.00 %**. The budget is per module,
>   so it does not stack on one module — **but there is now no slack anywhere to absorb a second load
>   on either output**, and every subsequent draw (the COLD-permissive divider of C-2, the per-branch
>   monitor dividers, the bleed) competes for the remaining 99 %.

**Row key (post-G0):** ✅ = **the part we own.** ⬜ = a 0.5 W part we do not own (derivation only).
⛔ = **a 12 V / 1 W part that DOES NOT EXIST ON THIS BOARD** (PART-30) — **not an alternative.**

| | Module | Family | Vnom | Inom | USVD @ 20 MΩ | % Inom | | CRHV @ 200 MΩ | % Inom | |
|:-:|---|---|---:|---:|---:|---:|:-:|---:|---:|:-:|
| ⬜ | AP002255x05 | 0.5 W | 200 V | 2.50 mA | 10.00 µA | 0.40 % | OK | 0.999 µA | 0.04 % | OK |
| ⬜ | AP004125x05 | 0.5 W | 400 V | 1.20 mA | 20.00 µA | 1.67 % | **NO** | 1.998 µA | 0.17 % | OK |
| ⬜ | AP006804x05 | 0.5 W | 600 V | 0.80 mA | 30.00 µA | 3.75 % | **NO** | 2.997 µA | 0.37 % | OK |
| ⬜ | AP008604x05 | 0.5 W | 800 V | 0.60 mA | 40.00 µA | 6.67 % | **NO** | 3.996 µA | 0.67 % | OK |
| ✅ | **AP010504x05 — OWNED** | 0.5 W | 1000 V | 0.50 mA | **50.00 µA** | **10.00 %** | **NO** | 4.995 µA | **1.00 %** | **AT LIMIT** |
| ⛔ | ~~AP002505x12~~ | 1 W | 200 V | 5.00 mA | 10.00 µA | 0.20 % | OK | 0.999 µA | 0.02 % | OK |
| ⛔ | ~~AP004255x12~~ | 1 W | 400 V | 2.50 mA | 20.00 µA | 0.80 % | OK | 1.998 µA | 0.08 % | OK |
| ⛔ | ~~AP006165x12~~ | 1 W | 600 V | 1.60 mA | 30.00 µA | 1.88 % | **NO** | 2.997 µA | 0.19 % | OK |
| ⛔ | ~~AP008125x12~~ | 1 W | 800 V | 1.20 mA | 40.00 µA | 3.33 % | **NO** | 3.996 µA | 0.33 % | OK |
| ⛔ | ~~AP010105x12~~ | 1 W | 1000 V | 1.00 mA | 50.00 µA | 5.00 % | **NO** | 4.995 µA | 0.50 % | OK |

**Result:** the ultra-precision network is only usable at **200 V (both families)** and
**400 V (1 W family)**. Everywhere else it steals 2–10 % of the available output current — a
real, load-dependent error and a real reduction in deliverable current, i.e. a design error by the
brief's own standard. **The 200 MΩ CRHV divider is the general answer; the USVD is a
low-voltage/high-current special case.** Note the 0.5 W 1 kV part sits exactly at the 1.00 % limit —
if that module is selected, raise R1 to 300–400 MΩ and accept the leakage penalty of §2.6.

Total dissipation at 1 kV: **4.99 mW** `[verified-run]`. Power is a non-issue by two orders of magnitude.

### 2.5 Accuracy budget

Bottom leg: R2 = R3 = **402 kΩ, 0.1 %, thin film, 25 ppm/°C** `[unverified-MPN]`.
Buffer: **OPA192** — Ib ±5 pA typ / 20 pA max, Vos ±5 µV typ / 25 µV max, RRIO, **ACTIVE**
`[web-verified, ti.com]` `[unverified-MPN]`.

> ⚠ **OPA192 minimum supply is 4.5 V** `[web-verified, ti.com]`. It **cannot** run on 3.3 V.
> Power it from the +5 V rail. The tap swings 0.245…2.253 V, comfortably inside a 5 V RRIO range.
> If a 3.3 V-only rail is mandated, substitute a 1.8–5.5 V CMOS precision amp (e.g. **OPA333**,
> Vos 10 µV, Ib 200 pA `[recalled]` `[unverified-MPN]`) and re-run the Ib term.

All terms `[verified-run]`:

| Term | Contribution |
|---|---:|
| CRHV TCR 100 ppm/K vs bottom 25 ppm/K, ΔT = 20 K | 0.1500 % |
| CRHV voltage coefficient, assumed 1 ppm/V @ 500 V/element `[recalled — confirm]` | 0.0500 % |
| R2/R3 thin-film ratio 0.1 % | 0.1000 % |
| OPA192 Vos 25 µV max / 1.004 V FS | 0.0025 % |
| OPA192 Ib 20 pA max × 201 kΩ / 1.004 V | 0.0004 % |
| ADS1115 gain error 0.15 % max `[recalled — confirm in datasheet]` | 0.1500 % |
| ADS1115 INL 1 LSB (62.5 µV) / 1.004 V | 0.0062 % |
| REF5025 initial 0.05 % (offset leg) | 0.0500 % |
| **Worst-case sum** | **0.509 % = 5.09 V at 1 kV** |
| **RSS** | **0.245 % = 2.45 V at 1 kV** |
| **RSS after 2-point calibration (drift terms only)** | **0.158 % = 1.58 V at 1 kV** |
| CRHV long-term stability, added over life | +0.5 % = 5.0 V |

**Compare: the module's own VMON accuracy is 1 %·Vnom = 10.00 V.**

- Calibrated, the independent monitor is **6.3× tighter** than the readback it exists to check.
- Even at end-of-life CRHV drift (0.5 %) it remains **2× tighter**. Requirement met.
- **Therefore: schedule periodic recalibration.** CRHV's 0.5 % stability, not any instantaneous
  term, is the dominant long-term error. This belongs in the instrument's documented maintenance.

### 2.6 The error term nobody budgets: surface leakage

At 200 MΩ this is a **>100 MΩ-class measurement** and PCB surface resistance is a circuit element.
Leakage in parallel with R1 `[verified-run]`:

| Leakage across R1 | R1 effective | Ratio error | **Error at 1 kV** |
|---|---:|---:|---:|
| 1 TΩ (clean, conformal-coated) | 199.96 MΩ | 0.020 % | 0.20 V |
| 100 GΩ | 199.60 MΩ | 0.200 % | 2.00 V |
| 10 GΩ (humid, uncoated) | 196.08 MΩ | 2.000 % | **20.0 V** |
| 1 GΩ (contaminated) | 166.67 MΩ | 20.00 % | **200 V** |

A 10 GΩ surface path — entirely achievable on an uncoated board on a humid day — produces **20 V of
error at 1 kV, worse than the module readback we are trying to check.** Mandatory mitigations:

- **Guard ring** around the TAP node, driven from the **buffer output** (i.e. at the tap potential),
  so surface leakage terminates on the guard and sees no potential difference to the tap.
- **Conformal coating** over the HV divider region, applied after cleaning.
- **No-mask slots / routed isolation** under the HV string; soldermask alone is not a creepage barrier.
- This interacts with the HV DRC netclass work (`CLAUDE.md` non-negotiables) — the divider region
  needs its own clearance rule, and the guard ring needs its own net.

### 2.7 ADC selection

| Candidate | Verdict |
|---|---|
| **ESP32 internal ADC** | **Reject.** 12-bit but with well-documented INL/DNL nonlinearity and non-monotonic regions; even after eFuse two-point calibration, accuracy is roughly ±1–3 % `[recalled]`. That is **no better than the module's own 1 % monitor**, so it fails to be an *independent, better* check — the requirement is unmet by construction. On classic ESP32, **ADC2 is additionally unusable while WiFi is active** `[recalled]`. Rejecting it is not a close call. |
| **MCP3421** | 18-bit, but single-channel `[recalled]`. We need ≥ 4 channels (HV monitor differential pair, VMON_P, VMON_N, rail/reference health). Multiple parts or an analog mux; no advantage over ADS1115. |
| **ADS131M04** | 24-bit, 4-channel simultaneous-sampling SPI `[recalled]`. Genuinely better, and simultaneous sampling matters for AC measurement — which we are not doing. Overkill and more expensive for a DC instrument. Reconsider only if HV ripple measurement becomes a requirement. |
| **ADS1115** ✅ | **16-bit ΔΣ, 4 single-ended or 2 differential, I²C with 4 selectable addresses, 2.0–5.5 V supply, internal low-drift reference, PGA ±0.256 V to ±6.144 V, 860 SPS max, on-chip comparator for over/under-voltage detection** `[web-verified, ti.com]` `[unverified-MPN — availability]` |

**Why the ADS1115 fits this problem specifically:**

- **True differential input** is what makes the bipolar level-shifted divider work at all.
- **±2.048 V FSR** matches the ±1.004 V signal with 2× headroom for overvoltage visibility.
- **4 channels** covers exactly what we need (see §2.8 channel map).
- **The on-chip comparator** provides an *interrupt-driven* overvoltage flag without polling — useful,
  though it is **not** the hardware OVP (§3.4), because it is I²C-configured and therefore trusts firmware.
- **860 SPS is ample.** The module's own 100 ms pole (§0.3) means the output cannot change faster than
  ~1.6 Hz. Oversampling and averaging 16 samples gives ~54 Hz effective, 4 bits of noise averaging,
  and still 30× faster than the plant.
- **Accuracy justification:** the required tolerance is "better than the module's 1 %·Vnom, and enough
  to arbitrate a disagreement." At 0.158 % calibrated (§2.5), the ADC's 0.15 % gain error is one of
  the two co-dominant terms — and it **calibrates out entirely** in a 2-point calibration against a DMM.
  Nothing cheaper reaches this; nothing more expensive is needed.

### 2.8 Channel map — ⬛ **NO LONGER FITS. G0-A4 OVERFLOWS IT.**

**Session 1's map** (one output, one HV monitor):

| ADS1115 input | Signal | Notes |
|---|---|---|
| AIN0 / AIN1 (differential) | HV monitor tap vs. matched offset reference | ±1.004 V for ±1 kV, FSR ±2.048 V |
| AIN2 (single-ended) | VMON_POS via buffer | remember the module's 20 kΩ source (§2.1) |
| AIN3 (single-ended) | VMON_NEG via buffer | |

The +5 V and +2.500 V rail health should also be monitored; ~~if a 4th measurement channel is needed,~~
use a second ADS1115 at a different I²C address rather than multiplexing.

> **◀ POST-G0.** One ADS1115 gives **2 differential OR 4 single-ended** inputs, and session 1's map
> already consumed all of them (one differential pair + two single-ended). **G0-A4 adds a second
> independent HV monitor** — i.e. a **second differential pair** — for output B (`DECISIONS.md`
> MODE-07, invariant (c) applied to two outputs). **Two differential HV pairs alone fill one part
> completely, leaving nowhere for VMON_P, VMON_N, or rail health.**
>
> ⇒ **A second ADS1115 at a different I²C address is now REQUIRED, not "if a 4th channel is needed".**
> Proposed split, to be confirmed at G1:
>
> | Part | Channels |
> |---|---|
> | **ADC-A** | AIN0/AIN1 diff = **independent HV monitor, OUTPUT A**; AIN2/AIN3 diff = **independent HV monitor, OUTPUT B** |
> | **ADC-B** | AIN0 = VMON_POS (buffered) · AIN1 = VMON_NEG (buffered) · AIN2 = +2.500 V reference health · AIN3 = +5 V rail health |
>
> **Two consequences that must not be lost:**
> 1. **Put the two safety-critical HV monitors on the SAME part and the diagnostics on the other**, so
>    a single ADC failure takes out both independent monitors *together* and visibly, rather than one
>    silently. (Argue the opposite case at G1 if preferred — but argue it, do not default into it.)
> 2. **The C-2 correction (`COMBINER_STUDY.md` §5.2) demands a SEPARATE divider string for the COLD
>    permissive**, physically distinct from the invariant-(c) string, **plus per-branch monitor
>    dividers.** Those are additional channels and additional loading that this map still does not
>    show. **The channel budget must be re-derived end-to-end at G1, not patched.**

### 2.9 Is the divider a sufficient bleed path? — No.

Passive bleed resistance = R1 + (R2‖R3) = **200.2 MΩ**. All `[verified-run]`:

| C_out | τ | 1 kV → 50 V (3τ) | 1 kV → 10 V (4.6τ) | 1 kV → 1 V (6.9τ) |
|---|---:|---:|---:|---:|
| 100 pF | 0.020 s | 0.060 s | 0.092 s | 0.138 s |
| 470 pF | 0.094 s | 0.282 s | 0.433 s | 0.650 s |
| 1 nF | 0.200 s | 0.601 s | 0.922 s | 1.383 s |
| 10 nF | 2.002 s | 6.006 s | 9.220 s | 13.829 s |
| 100 nF | 20.02 s | 60.06 s | 92.20 s | **138.3 s** |

**Verdict — the divider alone does NOT satisfy the brief's discharge requirement**, for three
independent reasons:

1. **C_out is not ours to control.** With a bare 100 pF output node it is excellent (92 ms to 10 V).
   With a cable and a detector at 100 nF it is **92 seconds** — an unacceptable dwell before a
   polarity changeover, and an unacceptable time for the output to remain live after "OFF".
2. **It is on the wrong side of the combiner.** A divider on the output node bleeds the output node
   and the cable. Once the combiner opens, **the module's own output node is not bled at all** and
   retains charge behind an open contact.
3. **It is not fail-safe against its own failure.** A cracked CRHV chip or a lifted pad silently
   removes the only bleed path *and* the monitor simultaneously — a single point of failure for two
   safety functions. (Mitigation: the monitor reading "0 V" while the module reports Vnom is exactly
   the disagreement trip of §5.6, so this failure is at least *detectable*.)

### 2.10 Dedicated bleed — sizing

Requirement: **1 kV → 10 V in ≤ 1.0 s with C_out up to 100 nF** ⇒ τ ≤ 217 ms ⇒ **R ≤ 2.17 MΩ**
`[verified-run]`:

| R | τ (100 nF) | t: 1 kV → 10 V | I @ 1 kV | % of a 0.5 mA Inom | P peak |
|---:|---:|---:|---:|---:|---:|
| 1.0 MΩ | 0.100 s | 0.461 s | 1000 µA | **200 %** | 1.000 W |
| **2.2 MΩ** | 0.220 s | **1.013 s** | 454.5 µA | **90.9 %** | 0.455 W |
| 3.3 MΩ | 0.330 s | 1.520 s | 303.0 µA | 60.6 % | 0.303 W |
| 4.7 MΩ | 0.470 s | 2.164 s | 212.8 µA | 42.6 % | 0.213 W |
| 10 MΩ | 1.000 s | 4.605 s | 100.0 µA | 20.0 % | 0.100 W |

Energy dumped from 100 nF at 1 kV: **50 mJ** `[verified-run]`.

> **Therefore the dedicated bleed must be SWITCHED, never permanent** — at 2.2 MΩ it would consume
> 91 % of a 0.5 mA module's entire output capability.
>
> **Make it default-connected.** The right implementation is to use the combiner changeover relay's
> own **idle / neutral position** to connect the output to the bleed resistor. Then:
> - power off → relay de-energised → **bleed connected** ✓
> - ESP32 dead → relay de-energised → **bleed connected** ✓
> - between polarities → relay in transit/neutral → **bleed connected** ✓
> - only an actively-energised, actively-selected state disconnects the bleed
>
> This is fail-safe by mechanical default and costs one resistor. It also means **the bleed and the
> break-before-make interlock are the same physical mechanism.**
>
> Bleed resistor: **3.3 MΩ** as 2–3 series HV-rated elements (1.52 s to 10 V at 100 nF, 61 % of Inom
> transiently, 0.3 W peak, well within a CRHV-class part's 0.3 W and 3 kV) `[verified-run]`.
> Combiner topology itself is out of scope here — it is the separate Phase-1 combiner study.

> ### ⬛ POST-G0: the bleed must be re-derived for TWO output nodes and for the MODE element (G0-A4)
>
> The elegant result above — *"the bleed and the break-before-make interlock are the same physical
> mechanism"* — was derived for **one** output node and **one** relay's neutral position. **G0-A4 gives
> invariant (b) two output nodes and a second HV routing element**, so it must be re-derived rather than
> assumed to generalise. Specifically:
>
> - **Each output node needs its own defined bleed path**, engaged on disable **and on mode change**
>   (`DECISIONS.md` MODE-10). In mode 2 both outputs may be live at once, so "the neutral position of
>   the polarity relay" no longer covers both nodes.
> - **The mode routing element needs its own de-energised-is-safe position**, and that position must
>   leave **both** output nodes bled (`COMBINER_STUDY.md` C-5).
> - **NUM-09 applies to each:** two parallel strings, never one series chain — an open bleed is
>   **silently undetectable**, and there are now two of them to go silently open.
> - **The loading arithmetic must be re-summed.** The 61 %-of-Inom transient figure was computed against
>   a single 0.5 mA module; with two monitor strings (each 1.00 %), a COLD-permissive string (C-2),
>   per-branch monitor dividers (C-2), and two bleeds, **nobody has summed the total standing and
>   transient load per module since G0.** Do it before G1. `COMBINER_STUDY.md` F-11 is the precedent
>   for what happens when a load budget is never actually summed.

### 2.11 Output current measurement — a documentation discrepancy, flagged not resolved

**Table 1 (p.7) specifies "Current monitor accuracy 1 %·Inom." Table 4 (p.9) lists no current-monitor
pin, and Figure 2 shows no such node.** `[verified-artifact — both]`

**I am not resolving this.** It is a genuine inconsistency in iseg's v2.5 document and the resolution
is a question for the vendor, not an inference. Possibilities: the spec line is inherited boilerplate
from a larger iseg family; or a current monitor exists on a customised variant (the item code has a
`k` customisation digit); or it is an error. **Do not design a board that expects a current-monitor pin
on a 7-pin APS.**

If output current readback is required (the brief does not currently require it), note that the
obvious approaches fail: **pins 3 and 7 are both GND and the case is bonded to GND**
`[verified-artifact, Table 4 note]`, so the HV return is the common ground and cannot be broken for a
low-side sense without also unbonding the case. The workable approach is to bring the **load's return
conductor back separately** and sense it against GND at low potential. That is a system/connector
decision, not a board decision. **Raise at G0.**

---

## 3. Interlock logic

### 3.1 The hazard, stated precisely

`/ON` LOW **or floating** → HV ON (§0.1). Therefore:

- A GPIO configured as an input (the state of every ESP32 GPIO during reset and early boot) **is a
  request for HV ON.**
- An unpowered logic gate whose outputs float **is a request for HV ON.**
- A broken wire **is a request for HV ON.**

**Never drive `/ON` from a GPIO.** The interlock must invert this default at every level.

### 3.2 ESP32 boot-time hazards — specific pins to avoid

Strapping pins are sampled at reset and are driven or pulled by the boot ROM; several also emit boot
messages or brief transients. `[recalled — verify against the ESP32-S3 datasheet's strapping-pin table
and "GPIO states during reset" table at G0. This list is a starting point, not a clearance.]`

| Variant | Strapping / hazardous pins |
|---|---|
| ESP32 (classic) | GPIO0, GPIO2, GPIO5, GPIO12 (MTDI), GPIO15 (MTDO); GPIO1 = U0TXD emits the boot log |
| ESP32-S3 | GPIO0, GPIO3, GPIO45, GPIO46 |
| ESP32-C3 | GPIO2, GPIO8, GPIO9 |

**Rule: no interlock signal, no DAC chip-select, and no relay drive on any strapping pin.** On
ESP32-S3, use the GPIO4–GPIO18 band. This is a schematic-review checklist item, and it should become
an executable check in the generator (see Pipeline note in the session report).

### 3.3 The gate — mutual exclusion by construction

Inputs:

| Signal | Source | Sense |
|---|---|---|
| `EN_HB` | heartbeat charge pump fed from a GPIO square wave (§3.7) | 1 = firmware alive **and** asserting enable |
| `INTLK` | external interlock loop (door switch / key / enclosure lid), **closed = 1** | 1 = safe to run |
| `nOVP` | hardware overvoltage comparator latch (§3.4) | 1 = not tripped |
| `SETTLE` | changeover monostable (§3.5) | 1 = SEL has been stable for T_dwell |
| `SEL` | polarity select GPIO, 10 kΩ pull-**down** | 0 = POS module, 1 = NEG module |

Logic:

```
  ARM   = EN_HB AND INTLK AND nOVP AND SETTLE          (74HC/HCT 3-input AND + 2-input AND)
  nSEL  = NOT SEL                                       (74HC14 Schmitt inverter)

  /ON_P = NOT ( ARM AND nSEL )     -- open-drain, 10 kΩ pull-up to the module's +VIN
  /ON_N = NOT ( ARM AND  SEL )     -- open-drain, 10 kΩ pull-up to the module's +VIN
```

**`/ON_P` and `/ON_N` derive from a single `SEL` signal and its inverse.** There is no input
combination that drives both low. Both-enabled is **not a state the logic can express** — it is not a
state firmware is trusted to avoid.

---

### 3.3a ⬛ POST-G0: **THIS GATE IS CORRECT FOR MODE 1 AND FORBIDS MODE 2. IT MUST BE RE-DERIVED.**

**The gate above is not wrong — it is the exactly-right implementation of the OLD invariant.** Deriving
`/ON_P` and `/ON_N` from `SEL` and `¬SEL` makes both-enabled unexpressible, which is precisely what
`CLAUDE.md` demanded and what session 1 was asked to build.

**G0-A4 changes what must be unexpressible.**

| | Old invariant (a) | **Restated invariant (a) — G0-A4** |
|---|---|---|
| Statement | "both modules enabled into the output simultaneously must be unreachable" | **"both modules connected to the SAME OUTPUT NODE simultaneously must be unreachable"** |
| Mode 1 | forbids both-enabled | **forbids both-enabled — identical behaviour** |
| Mode 2 | forbids it too — **which forbids the feature** | **satisfied structurally**: the modules are on physically different nodes |

⇒ **`SEL`/`¬SEL` exclusivity must become MODE-CONDITIONAL**, and that makes **the mode a safety input.**

#### The failure mode that defines the design

> Firmware, a stuck GPIO, or **a network command** (G0-A3 grants the network **full write authority**)
> asserts *"mode 2 — both modules permitted"* while the HV routing element is **physically still in the
> mode-1 position.** Both modules are then enabled onto **one node.** **That is the forbidden state,
> reached through exactly the firmware-promise path `CLAUDE.md` forbids.**

#### The rule that follows, and it is not negotiable

> ⬛ **The mode permissive fed into this gate MUST be `MODE_POS` — a low-voltage readback of the HV
> routing element's ACTUAL PHYSICAL POSITION** — **NEVER a commanded mode bit `MODE_CMD` from the MCU.**
>
> This is the direct transfer of `COMBINER_STUDY.md` **F-7**'s lesson onto a new element: *proving
> exclusivity of the **drive** is not proving exclusivity of the **switch**.* F-7 killed T2's
> anti-parallel LED interlock for exactly this reason.

> ### ⬛ G0-A5: `MODE_POS` COMES FROM A **PHYSICAL SWITCH AUX POLE**, AND `MODE_CMD` DOES NOT EXIST
>
> **The rule above is unchanged. Its implementation got simpler and strictly safer.**
>
> | | A4 pass (relay + sense contact) | **G0-A5 (physical switch)** |
> |---|---|---|
> | Source of `MODE_POS` | aux/sense contact on a **mode relay** | **auxiliary LV pole of the panel MODE SWITCH** |
> | Can `MODE_POS` disagree with the HV routing? | **Yes** — a sense contact mis-wired to the **coil command** rather than the armature is invisible in normal operation and fatal in the fault | **No — by construction.** The aux poles and the HV poles are **the same armature**. There is no wiring error that makes them report different things, because there is nothing separate to wire |
> | Does `MODE_CMD` exist? | Yes, and it is **network-writable** (G0-A3) | ⬛ **NO. There is no mode command on any interface** (`DECISIONS.md` MODE-12). The mode is not software-reachable at all |
> | Sense-path failure analysis required? | **Yes** — open line, shorted line, power-loss behaviour, coil-vs-armature wiring | **Not applicable — the sense path does not exist.** What replaces it: **lead-break timing** (MODE-15) and **intermediate-position decode** (MODE-18) |
>
> **⇒ The algebra below is CORRECT AS WRITTEN and needs no change.** Read `MODE_POS` as *"an aux pole of
> the mode switch"*. Read `MODE_CMD` as *a variable that no longer exists* — it is retained in the truth
> table **only to show that it appears nowhere in the algebra**, which is now doubly true.
>
> **Requirements that DO carry over onto the switch:** `MODE_POS` must **fail to 0** (pseudo-bipolar),
> its pull element is **duplicated** per ARCH-18, and the interlock must read it **combinationally —
> never latched, never cached in firmware** (MODE-14).

#### Revised logic — mode-aware

```
  ARM      = EN_HB AND INTLK AND nOVP AND SETTLE          (unchanged)

  MODE_POS = 1  iff the MODE SWITCH is physically in the UNIPOLAR / DUAL-OUTPUT position
                (from an AUXILIARY LV POLE of that switch — G0-A5.
                 NOT from MODE_CMD, which does not exist)
  MODE_POS = 0  = PSEUDO-BIPOLAR position.  UNDRIVEN / INTERMEDIATE MUST MAP TO 0.

  PERMIT_P = ARM AND ( MODE_POS OR ¬SEL )      -- in mode 2, POS is permitted regardless of SEL
  PERMIT_N = ARM AND ( MODE_POS OR  SEL )      -- in mode 2, NEG is permitted regardless of SEL

  /ON_P    = NOT PERMIT_P      -- open-drain, 10 kΩ pull-up to that module's +VIN
  /ON_N    = NOT PERMIT_N      -- open-drain, 10 kΩ pull-up to that module's +VIN
```

**Read the safety property off the algebra:** `PERMIT_P ∧ PERMIT_N` requires `MODE_POS = 1`, i.e. it
requires the **armature to be physically in the dual-unipolar position** — which is the position in
which the two modules are on **different nodes**. **When `MODE_POS = 0` the expression reduces exactly
to session 1's `SEL`/`¬SEL` gate**, so mode 1 is unchanged, bit for bit. **There is no input combination
in which both modules are enabled onto one node**, because "both enabled" is gated by the physical fact
that makes it safe.

#### Mode-aware truth table (the safety-relevant rows)

| `ARM` | `MODE_POS` (physical) | `MODE_CMD` (software) | `SEL` | `/ON_P` | `/ON_N` | POS | NEG | Nodes | Verdict |
|:-:|:-:|:-:|:-:|:-:|:-:|---|---|---|---|
| 0 | X | X | X | **1** | **1** | OFF | OFF | — | safe (any `ARM` input low) |
| 1 | 0 | 0 | 0 | **0** | 1 | **ON** | OFF | one node | mode 1, POS selected ✓ |
| 1 | 0 | 0 | 1 | 1 | **0** | OFF | **ON** | one node | mode 1, NEG selected ✓ |
| 1 | 1 | 1 | X | **0** | **0** | **ON** | **ON** | **two nodes** | **mode 2 — permitted, and SAFE because the armature is physically split** ✓ |
| 1 | **0** | **1** | X | **0** | 1 (SEL=0) | ON | OFF | one node | ⬛ **THE ATTACK ROW.** Software says mode 2; the armature says mode 1. **`MODE_POS = 0` wins**, the gate collapses to mode-1 exclusivity, and **the forbidden state is not reached.** `MODE_CMD` appears nowhere in the algebra — it is shown only to prove it is ignored. **◀ G0-A5: THIS ROW IS NOW UNREACHABLE, NOT MERELY SAFE** — there is no `MODE_CMD` to assert (MODE-12). It is retained because *the gate must still be built so that this row would be safe if such a bit ever returned.* |
| 1 | **1** | **0** | X | **0** | **0** | ON | ON | two nodes | armature is split, software thinks it is not. **Permissive and safe** — the modules really are on different nodes. Firmware should flag the disagreement and trip, but the *hardware* is not relying on it. **◀ G0-A5: also unreachable for the same reason.** |

**Both disagreement rows are safe, and they are safe for different reasons.** That asymmetry is the
design: **`MODE_POS` is trusted because it is a physical fact; `MODE_CMD` is trusted for nothing.**

> ⬛ **G0-A5 promotes that from a design principle to a structural fact.** The two disagreement rows
> exist only because the A4 pass assumed a software-settable mode. **With the mode on a physical switch
> there is no `MODE_CMD` column at all**, so the safety property is not *"the gate ignores the untrusted
> input"* but *"the untrusted input was never wired in."* **Keep the algebra as specified anyway** — it
> costs nothing, and it means a future session that adds any form of mode telemetry or diagnostic bit
> cannot accidentally make it authoritative. **What firmware must still do** is compare its own read of
> the aux poles against the previous read and **trip on any change while energised** (MODE-16) — that is
> a *runtime-change* detector, not a *disagreement* detector, and it is a different mechanism.

#### What is NOT yet designed, and must not be assumed done

| Gap | Why it matters |
|---|---|
| ~~**Which mechanism provides `MODE_POS`** — (a) physical human-set element, or (b) sensed relay armature~~ | ✅ **CLOSED BY G0-A5: (a), a PHYSICAL SWITCH.** Session 1's stated cost of (a) — *"loses the remote flexibility the human asked for"* — **was false**: mode change requires re-cabling the instrument anyway, so a remote mode command could never have completed the job. `DECISIONS.md` MODE-04. |
| ~~**The sense path's own failure modes** (mechanism (b))~~ | ✅ **NOT APPLICABLE (G0-A5).** *"a sense contact wired to report the coil command rather than the armature; an open sense line; a shorted sense line; loss of the sense path's supply while HV lives"* — **none of these exist, because there is no sense path.** The aux poles **are** the armature. ✅ **What DOES carry over:** `MODE_POS` must **fail to 0**, and its pull element is subject to **ARCH-18 (duplicate it)**. |
| **`SETTLE` must cover MODE transitions, not just `SEL`** | ✅ **STILL REQUIRED, and now for a different and simpler reason.** §3.5's monostable forces `ARM = 0` on any `SEL` edge; **it must do the same on any `MODE_POS` edge.** Under A5 a `MODE_POS` edge means **a human is turning the switch on a live instrument** — an off-procedure act (MODE-17) — so the correct hardware response is **immediate both-modules-off**, which is exactly what the monostable gives, and it works **without firmware** (which MODE-16's runtime trip does not). ⚠ **Do not size this dwell for a graceful mode change; there is no such thing.** It exists to be *fast*, not to be *long*. |
| ⛔ ~~**The mode element must join C-1's fail-safe coil rail.** De-energised must be the safe mode.~~ | **STRUCK (G0-A5): the mode element has NO COIL.** It cannot join a coil rail. It is safe by **absence of energy**, not by correct de-energised position. `COMBINER_STUDY.md` C-5 is rewritten accordingly. |
| **The power-up self-test must exercise it** | ⛔ ~~Command mode 2 with the element held in mode 1 and require refusal.~~ **UNPERFORMABLE (G0-A5) — there is no way to command a mode.** ✅ **Replaced by three performable tests** (`SCOPE.md` S-3): **(i)** the aux poles **break before** the HV poles make — scope the actual switch (MODE-15); **(ii)** switch parked **between detents** ⇒ both modules off, both outputs bled (MODE-18); **(iii)** switch moved **while energised** ⇒ HV off immediately (MODE-16). **Test (i) is now the single most important test on the board.** |
| ⬛ **NEW (G0-A5): the switch itself is unspecified and its part class is unsearched** | Rating **1 kV per HV pole**, **2 kV between poles** if the arrangement creates an opposite-polarity pair, **plus aux LV poles**, **plus a specified contact sequence**. Nobody in this project has searched HV rotary / ceramic wafer switches, and **the honest fallback — an HV link block or a re-plugged HV cable — may be the better engineering answer.** `DECISIONS.md` MODE-13, `SCOPE.md` R-14. |

### 3.4 Truth table *(mode-1 form — see §3.3a for the mode-aware form)*

| `EN_HB` | `INTLK` | `nOVP` | `SETTLE` | `ARM` | `SEL` | `/ON_P` | `/ON_N` | POS module | NEG module |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|---|
| 0 | X | X | X | 0 | X | **1** | **1** | OFF | OFF |
| X | 0 | X | X | 0 | X | **1** | **1** | OFF | OFF |
| X | X | 0 | X | 0 | X | **1** | **1** | OFF | OFF |
| X | X | X | 0 | 0 | X | **1** | **1** | OFF | OFF |
| 1 | 1 | 1 | 1 | 1 | **0** | **0** | 1 | **ON** | OFF |
| 1 | 1 | 1 | 1 | 1 | **1** | 1 | **0** | OFF | **ON** |
| — | — | — | — | — | — | **0** | **0** | \*\* | \*\* |

\*\* **Unreachable.** Requires `ARM ∧ nSEL` and `ARM ∧ SEL` simultaneously, i.e. `SEL ∧ ¬SEL`.

Fail-state coverage (the rows that actually matter):

| Condition | `/ON_P`, `/ON_N` | Result |
|---|---|---|
| ESP32 in reset — all GPIO high-Z | pull-down holds SEL = 0; **no heartbeat ⇒ EN_HB = 0** | **both OFF** ✓ |
| ESP32 boot ROM driving strapping pins | interlock signals are not on strapping pins (§3.2); no heartbeat | **both OFF** ✓ |
| Firmware crashed / hung with GPIO stuck high | heartbeat stops toggling ⇒ pump decays ⇒ EN_HB = 0 | **both OFF** ✓ |
| **Logic supply (3.3 V) lost** | **open-drain outputs release; 10 kΩ pull-ups to +VIN pull /ON HIGH** | **both OFF** ✓ |
| Broken track on `/ON_P` | pull-up at the module end holds it HIGH | **that module OFF** ✓ |
| Interlock loop opened (lid raised) | `INTLK = 0` ⇒ `ARM = 0`, **with no firmware involvement** | **both OFF** ✓ |
| Overvoltage detected | `nOVP = 0` latched ⇒ `ARM = 0`, **hardware path** | **both OFF** ✓ |

> **The open-drain choice is the load-bearing detail.** A totem-pole gate running at 3.3 V would, on
> loss of its own supply, present floating or low outputs — **which the module reads as ON**. Open-drain
> outputs with pull-ups to the module's own `+VIN` make *loss of the logic rail* a turn-off event.
> Use **74HC03 / 74LVC07** open-drain parts `[unverified-MPN]`, pull-ups 10 kΩ to +VIN.
> Sink current 0.5 mA at 5 V — trivial. `/ON` HIGH is then ≈ +VIN, satisfying the module's
> `5.5 V ≥ V/ON > 2.5 V` requirement `[verified-artifact, Table 1]`.
>
> **Hardware OVP** (`nOVP`): a comparator (**TLV3201** `[unverified-MPN]`) on the *buffered* divider
> node, threshold at 105 % of the configured full scale, **latched** (SR latch from two NAND gates),
> cleared only by an explicit `OUTP:PROT:CLE`. This is the direct hardware answer to *"Output voltage
> is internally not limited"* — it does not depend on the ADC, on I²C, or on firmware being alive.

### 3.5 The SEL-transition race, quantified — and eliminated

`/ON_P = NAND(ARM, nSEL)` and `/ON_N = NAND(ARM, SEL)`. On a `SEL` 0→1 edge, `/ON_N` goes low
immediately while `/ON_P` stays low until the inverter's `t_pd` (~10 ns) elapses. **For ~10 ns both
are low.**

Is that dangerous? Because of §0.3, the module's internal set node charges through 100 kΩ into 1 µF,
τ = 100 ms `[verified-run]`:

| Both `/ON` low for | Internal set node rises | At the HV output |
|---:|---:|---:|
| 10 ns | 0.250 µV | **0.100 mV** |
| 100 ns | 2.50 µV | 1.00 mV |
| 1 µs | 25.0 µV | 10.0 mV |
| 1 ms | 24.9 mV | **9.95 V** |

**A nanosecond-scale logic race is physically harmless** — the module's own input filter integrates it
away. But *"both enabled" must be unreachable* is a statement about states, not about volts, and a
millisecond-scale race is not harmless. **Eliminate it anyway:**

> **The changeover monostable.** Feed `SEL` through an edge detector into a retriggerable monostable
> (**74HC123** `[unverified-MPN]`) whose output is `SETTLE`. Any `SEL` edge forces `SETTLE = 0`,
> hence `ARM = 0`, hence **both modules off**, for `T_dwell`.
>
> This single component does three jobs at once:
> 1. Makes the both-low race **structurally impossible** (both are already off before SEL moves).
> 2. Provides the **hardware break-before-make** for the polarity changeover.
> 3. Enforces the **bleed dwell** of §2.10 in hardware, so firmware cannot skip it.
>
> Set `T_dwell` ≈ 1 s (RC on the '123). Firmware's own dwell (§5) must be **longer**, so that the
> hardware is a backstop rather than the normal path.

### 3.6 Grounding the unselected module's VSET — free, and required

From §1.4 pt. 3: an open VSET commands full scale. The unselected module must have VSET held at 0 V
in **hardware**.

**`/ON_P` is already exactly the right signal.** It is HIGH when the POS module is disabled. Drive a
small N-channel MOSFET gate (**2N7002** `[unverified-MPN]`) directly from `/ON_P`:

- `/ON_P` HIGH (module disabled) → FET on → **VSET_P shunted to GND** ✓
- `/ON_P` LOW (module enabled) → FET off → DAC drives VSET_P ✓

Zero additional logic, zero additional firmware, and "disabled ⇒ VSET grounded" becomes a hardware
invariant. Firmware should *also* write code 0 to the unselected DAC channel — belt and braces, and it
means the FET normally carries no current. Add ~100 Ω between the DAC and the FET drain node purely to
limit the fault current if firmware fails to zero the channel, but **place it on the DAC side of the
VSET tap** so it does not appear in series with the VSET pin (§1.4 — 100 Ω there would cost 1 % FS).

> **◀ POST-G0: this mechanism survives G0-A4 unchanged, and that is worth stating explicitly.** The
> shunt FET is driven by `/ON_P` / `/ON_N`, which under §3.3a's revised algebra are still exactly
> *"this module is disabled"*. **In mode 2 both modules are enabled, so both FETs are off and both DACs
> drive — which is correct.** In mode 1 the deselected module's `VSET` is still shunted. **No change is
> needed**, because the mechanism was keyed to *enablement*, not to *selection*. Session 1 got this
> right for a reason that outlived the requirement it was written for.
>
> **G0-A2 raises its importance**, though: an open `VSET` on a 2.5 V-Vref module commands **1000 V**,
> and a `VSET` pulled to the 3.3 V rail commands **≈1320 V** (§1.1, §1.4). The shunt FET, the pull-down
> at the pin (ARCH-05) and their **duplication** (ARCH-18) are the only things standing between a
> disabled module and full scale. **Treat them as safety parts, not as tidiness.**

### 3.7 The heartbeat pump — "a watchdog that leaves HV on is not a watchdog"

`EN_HB` is **not a static GPIO level**. Firmware must emit a continuous square wave (e.g. 1 kHz on a
LEDC channel) into a diode charge pump; the rectified DC is the enable.

```
  GPIO_HB ──[ 10 nF ]──┬──|<|── +node ──┬── R ──┬── GND      → Schmitt buffer → EN_HB
                       │                │       │
                      |<|              100 nF   │
                       │                │       │
                      GND              GND     GND
```

Decay from 3.3 V to a 1.5 V HC threshold `[verified-run]`:

| R | C | τ | Time to drop below threshold |
|---:|---:|---:|---:|
| 1 MΩ | 100 nF | 100 ms | **78.8 ms** |
| 1 MΩ | 220 nF | 220 ms | 173.5 ms |
| 470 kΩ | 220 nF | 103 ms | 81.5 ms |

**Choose 1 MΩ / 100 nF → HV drops within ~79 ms of firmware ceasing to toggle.** Note this is
*shorter* than the module's own 100 ms set-node time constant, so the hardware chop is faster than the
module could have ramped up anyway.

This one component covers what firmware cannot: a hung task, a stuck GPIO, a crashed core, a
brown-out that halts the CPU without resetting GPIOs. A GPIO held high by a crashed MCU is
indistinguishable from a deliberate enable; **a GPIO that has stopped toggling is not.**

---

## 4. Comms

### 4.1 The safety argument comes first

The HV return is GND, and **the module case is bonded to GND** `[verified-artifact, Table 4 note]`.
A fault brings HV onto local ground. If a non-isolated USB cable ties local ground to a lab PC's
chassis, **the fault current path runs through the lab PC and the person sitting at it.**

This dominates the comms discussion:

1. **Bond the chassis to protective earth** with a low-impedance conductor. Non-negotiable.
2. **Isolate the data link.** USB isolation (**ADuM3160 / ISOUSB211** `[unverified-MPN]`) or Ethernet,
   whose magnetics provide ~1.5 kV isolation as a side effect of the standard `[recalled]`.
3. Wired Ethernet gets isolation *for free* — a real and often-overlooked point in its favour for an
   HV instrument.

### 4.2 Serial vs. network

| Option | For | Against |
|---|---|---|
| **USB-UART bridge (CP2102N)** `[unverified-MPN]` | In-box drivers on Windows/macOS/Linux; **the port survives an MCU reset**, so you keep the connection and see boot messages — a real operational advantage when debugging an instrument that reboots on a fault. | Needs USB isolation. One more part. |
| CH340 | Cheapest. | macOS driver history is poor; counterfeit/clone variability `[recalled]`. Not for an instrument. |
| FT232R | Most robust software support. | Cost; a well-documented history of counterfeit parts being bricked by driver updates `[recalled]`. |
| **Native USB (S3 / C3)** | No bridge part, no bridge BOM cost. | **The USB device disappears when the MCU resets or crashes** — the host loses the port exactly when you most need to see what happened. For a lab instrument this is a genuine drawback, not a nitpick. |
| **Wired Ethernet, W5500 (SPI)** `[unverified-MPN]` | Isolation via magnetics; deterministic; works with any ESP32 including S3; hardware TCP/IP offload; rack/remote friendly. | SPI bandwidth-limited (irrelevant here); more parts. |
| Wired Ethernet, LAN8720 (RMII) | Cheaper PHY. | Requires an **EMAC**. **ESP32-S3 and ESP32-C3 have no Ethernet MAC** `[recalled — verify at G0]`. On classic ESP32 the 50 MHz RMII clock arrangement is a known source of layout grief. |
| **ESP32 WiFi** | Free (already in the SoC); remote monitoring is genuinely useful. | See below. |

### 4.3 "WiFi on an HV instrument" — the honest argument

**Against:**

1. **It removes the physical-presence gate.** A serial cable is an implicit authorisation token:
   to command HV, be in the room. WiFi lets anyone on the network energise a kilovolt supply.
   This is the strongest objection and it is not a technical one.
2. **Security surface.** No authentication by default; OTA firmware update on an HV instrument is a
   remote-code-execution path to a device that can kill someone. Any WiFi write path needs
   authentication, and that is *security engineering we would be committing to maintain*.
3. **Reliability.** Dropouts mid-ramp are routine, so the fail-safe path gets exercised constantly.
   That is survivable (§5.7 handles it) but it means the risky path becomes the common path.
4. **Electrical noise.** WiFi TX bursts draw ~200–300 mA peaks `[recalled]`. Rail droop modulates
   anything rail-referenced — which is precisely why §1.6 insists on an external reference — and the
   RF field couples into a 200 kΩ divider tap sitting 5 µA above the noise (§2.2). Physically real.
5. **Institutional.** Many university networks prohibit unmanaged APs/stations.

**For:** remote telemetry, logging, and status display are genuinely valuable, and **read-only
telemetry carries almost none of the risk above.**

> **~~Recommendation:~~ ⛔ SESSION-1 RECOMMENDATION — OVERTURNED AT G0. RETAINED AS THE RECORD OF WHAT
> IS BEING ACCEPTED.** **any interface may READ; only the interface selected by a physical switch may
> WRITE.** A DIP switch or key-switch position selects the write-authoritative transport; all others
> are demoted to read-only at the parser level and report `+105,"Interface not write-authorised"`.
> The physical switch restores the physical-presence property that WiFi removes, and it is a
> one-component, auditable rule rather than a policy in a config file.
>
> **~~Ship:~~** isolated USB-CDC via **CP2102N** as the default control path. **Populate but do not stuff**
> the W5500 footprint for rack deployment. ~~**WiFi read-only**, defaulting to off.~~

---

### 4.3a ⬛ THE ANSWER: **BOTH TRANSPORTS, FULL WRITE AUTHORITY ON BOTH (G0-A3)**

> **Session 1 recommended: serial with full write authority; network read-only telemetry, defaulting to
> OFF, with write authority behind a physical switch.**
> **G0 answered, 2026-07-23: "Both serial and network, with FULL WRITE AUTHORITY on both."**
> **⇒ Therefore: the physical write-authority switch is NOT built, the network is NOT demoted to
> read-only, and `+105,"Interface not write-authorised"` is not the mechanism it was designed to be.**
>
> **The human made this choice deliberately, over the recommended default, with the risk stated.
> Do not re-litigate it. Do not quietly downgrade the network to read-only in a later session.**

**The five objections in §4.3 are not withdrawn — they are ACCEPTED.** Objection 1 (*"it removes the
physical-presence gate… anyone on the network can energise a kilovolt supply"*) is the strongest and it
stands, unmitigated by the mechanism that was designed to mitigate it. That is what makes the rest of
this section mandatory rather than advisory.

**Where the safety burden moves.** With HV set-point **and** enable commands reachable over the network:

> ⬛ **The hardware interlock (§3, §3.3a), the hardware `VSET` clamp (§1.7), and the soft limits carry
> the ENTIRE safety case.**

Nothing in firmware is a barrier any more; firmware is the **attack surface**. Concretely, three
elements that §3–§5 already describe are **promoted from good design to load-bearing**, and two become
**requirements** rather than options:

| Element | Status after G0-A3 | Where |
|---|---|---|
| Hardware interlock gate, open-drain, pull-ups to `+VIN` | **load-bearing** — it is what a hostile message cannot reach | §3.3, §3.3a |
| Hardware `VSET` clamp = the 2.500 V rail | **load-bearing, PRIMARY SAFETY ELEMENT** — the barrier between a bad write and ≈1320 V | §1.7, `DECISIONS.md` PART-33 |
| Latched hardware OVP (`nOVP`) | **load-bearing** — it is I²C-independent and firmware-independent by construction | §3.4 |
| AC-coupled heartbeat pump | **load-bearing** — a crashed or compromised firmware cannot fake a toggling GPIO from a hung loop | §3.7 |
| **Explicit ARM / DISARM step** | ⬛ **REQUIRED** (was implicit in `OUTP ON`). "Energised" must never be one packet away from "idle". Disarm must be reachable from every state and safe to issue at any time | `DECISIONS.md` ARCH-35 |
| **Comms-loss watchdog that FAILS TO HV-OFF** | ⬛ **REQUIRED** (was "recommended"). §5.7 already specifies it: default 10 s, any command kicks it, expiry ⇒ **ramp down and disable**, **never "hold last value"**, and `SYST:WATCH 0` refused without a **local jumper** | `DECISIONS.md` ARCH-36 |
| **Soft limits that ERROR rather than clamp** | ⬛ **REQUIRED.** The reference board's silent `constrain()` (REF-05) is the anti-pattern | `DECISIONS.md` ARCH-37 |

**And the work that §4.3's recommendation existed to avoid is now IN SCOPE and must be resourced:**
authentication, session management, OTA security, and a **bounded** command parser that is **fuzzed** —
not the reference board's parser, whose `msg_buffer` overflow is reachable from the control port
(REF-07). `SCOPE.md` R-10 is escalated to **High** accordingly.

**Two things that do NOT change, and should not be traded away in the redesign:**

1. **§4.1's isolation argument is untouched and is now more important, not less.** The HV return is GND
   and the module case is bonded to GND; a non-isolated USB tie to a lab PC puts the fault path through
   the person at the PC. **Bond the chassis to protective earth; isolate the data link.** Ethernet's
   magnetics give ~1.5 kV of that for free — a real point in favour of the wired path now that the
   network is a *committed* control path rather than optional telemetry.
2. **Ship both transports for real.** The W5500 footprint can no longer be *"populate but do not
   stuff"*, and WiFi can no longer default to off. **Both are control paths and both must be built,
   tested and fuzzed.** `SCOPE.md` S-2 requires the bench sweep over **both**.

**⚠ Compounding factor from G0-A4:** ~~the **output mode** is also commandable over this same network
path. **A mode command asserted against a physically-unmoved routing element is the forbidden state**~~
⛔ **REMOVED BY G0-A5 — and this is the ONE place where a G0 answer made the network write path LESS
dangerous rather than more.** The mode is a **physical switch** (`DECISIONS.md` MODE-04) and there is
**no `MODE` setter on any interface** (MODE-12), so **the network cannot reach the mode at all.** The
worst item on the remote attack surface — *the ability to make the hardware's own safety input lie* —
**does not exist.** §3.3a still takes the permissive from the physical element rather than from a
message, and now there is no message to take it from. **Everything else in §4.3a is unchanged and still
binds: setpoint and enable remain network-writable, and the hardware carries the whole safety case.**

### 4.4 ESP32 variant recommendation

> **ESP32-S3.**
>
> - The absent DAC is irrelevant (§1.1) — we use an external DAC regardless.
> - The absent ADC quality is irrelevant — we use an external ADC regardless (§2.7).
> - Ample GPIO for SPI (DAC) + I²C (ADC) + interlock + relay + heartbeat while avoiding all
>   strapping pins (§3.2).
> - Dual core: pin the safety supervisor loop to one core and comms/WiFi to the other, so a blocked
>   network stack cannot delay a trip.
> - We are adding a CP2102N anyway (§4.2), so native USB is not a deciding factor.
> - Trade-off accepted: no EMAC, so W5500 (SPI) is the Ethernet path. That is the recommended PHY anyway.

### 4.5 Protocol — SCPI-like ASCII

Keep SCPI. Rationale: the reference board already speaks it (Vrekrer parser, with
`Vrekrer_scpi_parser.{h,cpp}` on disk) `[verified-artifact]`; it is human-typeable over a terminal for
bench work; it is trivially scriptable; and lab tooling expects it.

**What the old firmware lacked, and why it matters.** `alpha-shield.ino` registers only `*IDN?` and a
`*DEBUG?` `[verified-artifact]`. Its own header comment lists the gaps as TODOs: *"`*RST`, any other
general SCPI commands?"*, *"include soft limits"*, *"global off?"*. Two defects are safety-relevant:

- **No `*RST`.** There is no single command that puts the instrument in a known safe state.
- **No error queue.** A malformed or out-of-range command is silently clamped by `constrain()` and
  the host is never told. On an HV instrument, *"I asked for 900 V and got 200 V and nothing said so"*
  is a serious failure mode.
- **No measurement.** `GetBias()` returns `bias_settings[channel-1]` — **the stored set point, not a
  measurement** `[verified-artifact]`. The instrument cannot tell you what its output actually is.
  Fixing this is the whole of §2.

### 4.6 Proposed command set

**Mandatory IEEE-488.2 / SCPI-99 surface** (all absent from the reference firmware):

| Command | Behaviour |
|---|---|
| `*IDN?` | `Yale,HVCTL-BIP,<serial>,<fw-version>` |
| `*RST` | → `SAFE`: ramp aborted, `OUTP OFF`, setpoint 0, DAC codes 0, bleed engaged, error queue cleared, `SEL` to POS. **Must be safe to issue at any time, in any state.** |
| `*CLS` | Clear status registers and error queue (does **not** clear a protection latch) |
| `*OPC?` | Returns `1` when the pending ramp/changeover completes; the blocking form of a state transition |
| `*TST?` | Self-test: with output off, verify `MEAS:VOLT?` ≈ 0; verify interlock readable; verify DAC and ADC ACK; verify reference within tolerance. Returns 0 = pass |
| `SYSTem:ERRor[:NEXT]?` | `<code>,"<message>"`; `0,"No error"` when empty. **FIFO, depth ≥ 16.** |
| `SYSTem:VERSion?` | `1999.0` |

**Source (signed setpoint):**

```
[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] <NRf>    e.g.  VOLT -350.0
[SOURce:]VOLTage?                                          commanded setpoint, signed
[SOURce:]VOLTage:LIMit:HIGH <NRf>                          soft limit, persisted in NVS
[SOURce:]VOLTage:LIMit:LOW  <NRf>                          soft limit (negative), persisted
[SOURce:]VOLTage:SLEW <NRf>                                ramp rate, V/s
[SOURce:]VOLTage:POLarity?                                 POS | NEG | ZERO   (read-only, derived)
```

**Output and protection:**

```
OUTPut[:STATe] ON|OFF        /  OUTPut[:STATe]?
OUTPut:POLarity POS|NEG      /  OUTPut:POLarity?     -- rejected unless OFF and measured |V| < V_safe
OUTPut:PROTection:TRIPped?   /  OUTPut:PROTection:CLEar
```

**Measurement — note the deliberate naming asymmetry:**

```
MEASure:VOLTage[:DC]?              signed, from the INDEPENDENT monitor. This is "the output voltage".
MEASure:VOLTage:MODule? POS|NEG    the module's own VMON, unsigned. Diagnostic only.
FETCh:VOLTage?                     last reading without re-triggering
```

`MEASure:VOLTage?` returning the *independent* monitor is a protocol-level encoding of the brief's
requirement. A host that asks the obvious question gets the trustworthy answer; the module's own
readback is reachable only by explicitly asking for it by name.

**Status and safety:**

```
STATus:OPERation:CONDition?     bit0 RAMPING  bit1 SETTLING  bit2 CHANGEOVER  bit3 DISCHARGING
STATus:QUEStionable:CONDition?  bit0 OVERVOLT bit1 INTERLOCK bit2 MON_DISAGREE bit3 WDOG
SYSTem:INTerlock?               0 | 1
SYSTem:WATCHdog <seconds>       0 disables -- and disabling REQUIRES a local jumper, refused otherwise
SYSTem:WATCHdog:KICK            (any received command also kicks it)
```

**Error codes.** Standard SCPI negatives (`-100` command error, `-109` missing parameter, `-113`
undefined header, `-221` settings conflict, `-222` data out of range) plus device-specific positives:

| Code | Meaning |
|---|---|
| `+100` | Interlock open |
| `+101` | Watchdog timeout — output was ramped down |
| `+102` | Overvoltage trip (hardware OVP latched) |
| `+103` | Changeover timeout — discharge did not complete |
| `+104` | Monitor disagreement (module VMON vs independent monitor) |
| `+105` | Interface not write-authorised (§4.3) |
| `+106` | Ramp timeout — output did not track the setpoint |

### 4.7 Why a signed setpoint

**Recommend `VOLT -350.0`.** Arguments:

- ⛔ ~~**It matches the physical reality.** The brief specifies **one output terminal**, explicitly not
  two unipolar outputs. One terminal, one number. A magnitude-plus-polarity API models a machine we did
  not build.~~
  **◀ THIS ARGUMENT IS DEAD. G0-A4 amends the brief: the instrument now has TWO output terminals and a
  mode that selects between one combined output and two independent ones.** "One terminal, one number"
  describes **mode 1 only**. See §4.7a — the signed-setpoint recommendation **survives, but on the
  atomicity argument alone**, and it must be **scoped to an output** rather than to the instrument.
- **Atomicity.** `POLarity NEG` followed by `VOLT 350` is a **two-write, non-atomic** state change.
  A crash, timeout, or dropped packet between them leaves polarity and magnitude inconsistent — and
  the inconsistent state is *"negative polarity selected, magnitude still 900 from last time."*
  A signed scalar cannot be torn.
- **Sweeps become data.** `[-1000, -900, ..., 900, 1000]` is a list of numbers a host can emit
  without knowing the instrument's polarity state. This is exactly the brief's success criterion
  ("commanded bipolar sweep across the full range").
- **Convention.** Signed programming is what bipolar sources do.

**Handle these honestly:**

- **A sign change is not a small change.** It is a mechanical changeover taking seconds. `VOLT` is
  therefore **non-blocking**: it is accepted, the state machine executes it, and the host either polls
  `STAT:OPER:COND?` or blocks on `*OPC?`. A host that assumes `VOLT` completes on return will be wrong.
  Document this loudly.
- **Signed zero is not reliable in ASCII parsing.** `VOLT 0` means *go to zero*, staying in the
  current polarity. Do **not** overload `-0`. Provide `OUTPut:POLarity:PREFerence POS|NEG` for the
  at-zero case.
- **Range checking is signed.** `VOLT 500` with a POS module fitted and a NEG-only limit configured
  must raise `-222`, not silently clamp — the old firmware's `constrain()` behaviour is the bug.
  **G0-A3 promotes this from a nicety to a named safety element** (`DECISIONS.md` ARCH-37): soft limits
  are one of the three things carrying the whole safety case, and a limit that silently clamps is not a
  limit.

### 4.7a ⬛ POST-G0: the protocol FORKS by mode (G0-A4)

**What survives:** the **atomicity** argument. A signed scalar cannot be torn; `POL NEG` + `VOLT 350`
can, and its torn state is *"negative selected, magnitude still 900 from last time"*. That argument is
independent of terminal count and it still decides the shape of the setpoint command.

**What breaks:** *"one terminal, one number"* is a mode-1 statement. **In mode 2 there are two
independently-commandable outputs and a signed scalar addressed to "the output" is ambiguous.**

**Proposed shape, to be designed properly at G1 — this is a sketch of the problem, not a solution:**

| Mode | Setpoint surface |
|---|---|
| **Mode 1 — bipolar combined** | `VOLT <signed>` as designed. Polarity is implied by sign; a sign change runs the full changeover state machine of §5. |
| **Mode 2 — dual unipolar** | Outputs addressed separately, e.g. `VOLT (@A) <magnitude>` / `VOLT (@B) <magnitude>`, with **sign fixed by the module wired to that terminal** and range-checked against it. `VOLT (@B) 350` on the negative terminal means −350 V; **`VOLT (@B) -350` must be an error, not a courtesy**, because a protocol that accepts both spellings will eventually be handed the wrong one. |

**Three rules that must hold in both modes** — *rewritten at G0-A5; the mode surface is READ-ONLY:*

1. ⛔ ~~**A MODE command is REJECTED — not queued, not clamped — unless both outputs are OFF and both
   MEASURE below `V_safe`**, mirroring `OUTPut:POLarity` in §4.8.~~
   ⬛ **STRUCK BY G0-A5. THERE IS NO MODE COMMAND. The mode cannot be set over serial, over the network,
   or at all — it is a physical switch** (`DECISIONS.md` MODE-04, MODE-12). **This is a deletion, and a
   large one:** the refusal logic, its `-221` settings-conflict path, its new error code, and the
   torn-state analysis it inherited from ARCH-21 **all disappear.** An immutable value cannot be torn
   and needs no atomicity argument. **Do not re-introduce a `MODE` setter "for convenience".**
2. **`MODE?` reports the PHYSICAL position (`MODE_POS`) — which is now the only position there is.**
   A host asking "what mode am I in" gets the answer the interlock is using (§3.3a). ⛔ ~~A separate
   query may report the commanded bit for diagnostics; the disagreement between them is itself a fault
   to report.~~ **Struck: there is no commanded bit, so there is no disagreement to report.**
   ✅ **Replaced by a different check with a different meaning:** firmware compares successive reads of
   the aux poles and **trips on any CHANGE while energised** (`DECISIONS.md` MODE-16) — a
   *runtime-change* detector, not a *disagreement* detector.
3. **`*RST` must report a mode; it must never set one.** §4.6 specifies `*RST` → `SAFE` with `SEL` to
   POS. ⬛ **G0-A5 makes the correct behaviour trivially available, where the A4 pass had to legislate
   it:** the A4 note warned that *"`*RST` must not MOVE the routing element, because that is an HV
   transition and `*RST` must be safe to issue at any time"*. **It now cannot move it — there is nothing
   to move.** `*RST` disables everything, discharges, and **reports** the physical position.
4. ⬛ **NEW (G0-A5): a setpoint or `OUTP ON` addressed to a terminal that is not live in the
   physically-selected mode must RAISE AN ERROR, not be silently ignored.** In pseudo-bipolar mode there
   is one live terminal; a command aimed at the other must fail loudly. The REF-05 anti-pattern
   (silently `constrain()` and say nothing) applies here exactly as it does to soft limits (ARCH-37).

**Error codes:** the 100–106 block of §4.6 must be extended — ⛔ ~~for mode-change refusal and for
mode-position disagreement~~ **struck, neither exists** — ✅ **for (a) mode switch moved while energised
⇒ HV forced off (MODE-16), (b) illegal/intermediate mode-switch position (MODE-18), and (c) command
addressed to a terminal not live in the selected mode.** `DECISIONS.md` ARCH-33. **Note the direction:
G0-A5 SHRANK this block's growth rather than adding to it.**

### 4.8 Safety-relevant changeover command sequences

**Simple (recommended for hosts):**

```
VOLT -400            -- instrument runs the full state machine of §5
*OPC?                -- blocks; returns 1 on completion
SYST:ERR?            -- MUST be checked: 0 = clean, +103 = discharge timed out, etc.
MEAS:VOLT?           -- confirm against the independent monitor
```

**Explicit (for scripts that want each step observable):**

```
VOLT 0
*OPC?
OUTP OFF                  -- /ON de-asserted; relay to neutral; bleed engaged
MEAS:VOLT?                -- poll until |V| < V_safe. MEASURED, not assumed, not timed.
OUTP:POL NEG              -- REJECTED with -221 unless OUTP is OFF and |MEAS| < V_safe
OUTP ON
VOLT -400
*OPC?
```

`OUTPut:POLarity` being **rejected** rather than queued is the point. The protocol refuses to express
an unsafe transition, mirroring the hardware that refuses to perform one (§3.3).

---

## 5. Firmware state machine

### 5.1 States

| State | Electrical condition |
|---|---|
| **S0 SAFE** | heartbeat not asserted → `ARM = 0`; both `/ON` high; relay neutral → **bleed engaged**; both DAC codes 0 |
| **S1 ARMED** | polarity selected, relay switched to that module, `/ON` still high, DAC at 0 |
| **S2 RAMPING** | `/ON` low; DAC stepping toward target at the `SLEW` rate; measured output tracking |
| **S3 REGULATING** | at setpoint; `|MEAS − target|` inside the window; watchdog kicked |
| **S4 RAMP_DOWN** | target forced to 0; DAC stepping down |
| **S5 DISCHARGE** | `/ON` high; relay neutral; bleed engaged; **waiting on a measurement** |
| **S6 CHANGEOVER** | held in neutral for `T_dwell`, then relay switched |
| **S7 TRIP** | electrically identical to S0 but **latched**; requires `OUTP:PROT:CLE` |

**Power-on state is S0**, and S0 is reached passively — no firmware action is required to be in it
(§3.4). This is the property that makes the whole thing safe.

> ### ⬛ POST-G0: this state machine is INCOMPLETE. Three gaps, all created by G0.
>
> **Gap 1 — G0-A4: there is no MODE-CHANGE state, and it must be a first-class transition.**
> A mode change moves an **HV routing element**. Session 1's S6 CHANGEOVER exists for exactly the
> analogous operation on the polarity element, and its safety rule is `ARCH-24`: **a discharge timeout
> before a changeover must TRIP, never fall through**, because falling through hot-switches a contact
> at unknown high voltage. **The same rule applies unchanged to a mode change**, on a contact whose
> correct position is the *entire* mode-2 safety argument (§3.3a).
>
> **Required sequence — every step, in order** (`DECISIONS.md` MODE-08):
> `both outputs to zero` → `both modules disabled (/ON high, +VIN removed)` → **`dwell for bleed, on
> BOTH output nodes, waiting on a MEASUREMENT not a timer`** → `move the routing element COLD` →
> `re-read MODE_POS and confirm it matches the command` → `re-arm`.
> **On discharge timeout: TRIP, leave the element where it is, tell a human.** On a
> `MODE_POS`-does-not-match-command timeout: **TRIP** — the element did not move, and continuing would
> mean operating with the interlock and the operator holding different beliefs about which terminal is
> live.
>
> > ### ⛔ **GAP 1 IS CLOSED BY DELETION, NOT BY DESIGN — G0-A5.**
> >
> > **The mode is set by a PHYSICAL SWITCH.** Firmware has **nothing to move**, so:
> > - **There is no mode-change state**, no S6-analogue, no timeout, and **no TRIP rule** — `ARCH-24`
> >   loses the second instance the A4 pass gave it, and the *"re-read `MODE_POS` and confirm it matches
> >   the command"* step **has no command to match against** (§4.7a).
> > - **The sequence above is not deleted as PHYSICS — it is relocated as PROCEDURE.** The identical
> >   steps (both outputs to zero → both modules disabled → dwell for bleed → move the element cold) are
> >   what the **operator** does on a **powered-down, cables-off** instrument, enforced by a **guard over
> >   the switch** and a **panel legend** (`DECISIONS.md` MODE-17).
> > - **Two hardware backstops replace the state machine**, and both work without firmware:
> >   **(i)** the switch's **aux poles break before its HV poles make** (MODE-15), so the interlock has
> >   already dropped `ARM` before any HV re-routing — this is §3.5's monostable doing in hardware what
> >   the dwell did in firmware; **(ii)** an **intermediate position** decodes to both-modules-off,
> >   both-outputs-bled (MODE-18).
> > - **One firmware duty remains, and it is the opposite of graceful:** firmware reads the aux poles at
> >   boot **and continuously**, and **a change detected at runtime forces HV OFF IMMEDIATELY** —
> >   **never a graceful ramp** (MODE-16). A graceful ramp-down would keep HV alive during exactly the
> >   contact transit the lead-break timing is racing.
> >
> > **This is the rare case where a G0 answer removed a safety-critical state instead of hardening one.**
> > Record it as such, and **do not re-create the transition** in a later session.
>
> **Gap 2 — G0-A4: every state is now a state of TWO outputs.** S2 RAMPING, S3 REGULATING, S4
> RAMP_DOWN and S5 DISCHARGE are written for one output. **In mode 2 the two outputs are independent**,
> so either the machine is replicated per output with a supervisor holding the shared transitions
> (mode change, interlock, OVP, trip), or the states become vectors. **This is a design decision for
> G1; do not let it be made implicitly by whoever writes the firmware first.**
>
> **Gap 3 — G0-A3: the abort paths in §5.4 are written for faults, not for messages.** With full
> network write authority, `*RST`, `OUTP OFF` and disarm must be reachable **and correct** from a
> hostile or malformed command stream, and the **ARM/DISARM** step of `ARCH-35` must appear here as a
> state, not as a flag. **S0 SAFE and "armed but at zero" are not the same state and must not be
> conflated.**
>
> **What does NOT change, and is worth saying:** S0 is still reached **passively**, and every hardware
> path in §3.4's fail-state table still lands there without firmware. **G0 did not weaken that — it is
> the reason the design survives having its command surface opened up.**

### 5.2 Transitions, with entry/exit conditions and timeouts

| From → To | Entry condition | Timeout | On timeout |
|---|---|---|---|
| S0 → S1 | `OUTP ON` **and** `INTLK = 1` **and** `\|MEAS\| < V_safe` | — | — |
| S1 → S2 | relay settled (50 ms) + bounce (10 ms); optional aux-contact position confirmed | 200 ms | **→ S7** `+103` |
| S2 → S3 | `\|MEAS − target\| < max(0.5 % FS, 3σ_monitor)` **sustained 200 ms** | `\|Δtarget\|/slew + 3 s` | **→ S7** `+106` |
| S3 → S4 | `VOLT 0`, `OUTP OFF`, watchdog expiry, or soft fault | — | — |
| S4 → S5 | `\|MEAS\| < 2 %·Vnom` | 5 s | **→ S5 anyway** (disabling is always safe) |
| S5 → S1 / S6 | **`\|MEAS\| < V_safe` sustained 500 ms** *and* dwell ≥ `T_dwell` | **30 s** | **→ S7** `+103`, **relay NOT switched** |
| S6 → S1 | dwell elapsed; relay switched; `SETTLE` re-asserted | 2 s | **→ S7** |
| any → S7 | hard fault (see §5.5) | — | — |
| S7 → S0 | `OUTP:PROT:CLE` **and** fault cleared **and** `\|MEAS\| < V_safe` | — | — |

**Thresholds, derived not guessed:**

- **`V_safe` = 10 V.** Two criteria coincide: relay contacts should be cold-switched (tens of volts),
  and 10 V is well below any touch-safety limit. At 1 kV with 1 nF this is reached in 0.92 s
  `[verified-run]`. **G0-A2 pins the 1 kV; the 1 nF is still `[recalled]` and now bench-measurable
  (PART-24).** **G0-A4: `V_safe` must be satisfied on BOTH outputs before any mode change** —
  **and G0-A5 relocates who checks it: the OPERATOR, on a powered-down instrument (MODE-17), not the
  state machine.** Firmware's remaining duty is MODE-16 (a mode change seen at runtime ⇒ HV off
  **immediately**). `V_safe` is still the right threshold; it is simply no longer a transition guard.
- **S4 → S5 at 2 %·Vnom = 20 V** because the module's stability and ripple specs are only guaranteed for
  `2 %·Vnom < Vout ≤ Vnom` `[verified-artifact, Table 1 note 1]`. Below that the module's own
  regulation is **unspecified, not merely worse**, so continuing to *ramp* there is meaningless — just
  disable and bleed. **G0-A2 makes the number concrete: 20 V.** Note the two thresholds now sit only a
  factor of two apart (20 V → 10 V), and **the region between them is one in which the module's output
  is unspecified while we are still measuring it** — the independent monitor, not VMON, is what must be
  trusted there.
- **Ramp step rate ≥ 300 ms.** The module's set node has τ = 100 ms; stepping faster than ~3τ means
  the output never tracks the DAC and `|MEAS − target|` becomes meaningless as a health check
  `[verified-run]`. A full-scale ramp at 100 V/s takes 10 s.
- **`T_dwell` (firmware) > `T_dwell` (hardware monostable, ~1 s)**, so the hardware backstop of §3.5
  is never the thing that acts in normal operation. Use 2 s.

### 5.3 The one transition that must never fall through

**S5 → S6 on discharge timeout must TRIP, not proceed.** Every other timeout in the table can safely
degrade toward "off", because off is safe. This one cannot: proceeding means **hot-switching a relay
at unknown high voltage**, which welds contacts and can leave the output permanently connected to the
wrong module. If the output will not discharge in 30 s, something is wrong (bleed resistor open, relay
stuck, load injecting charge) and **the correct action is to stop and tell a human.**

### 5.4 Abort paths — every one of them

| Trigger | Hardware does | Firmware does | End state |
|---|---|---|---|
| `OUTP OFF` | — | S3 → S4 → S5 → S0, graceful ramp | S0 |
| `*RST` | — | abort ramp, → S4 → S5 → S0 | S0 |
| **Interlock opened** | `INTLK = 0` ⇒ `ARM = 0` ⇒ **both `/ON` high immediately**, no firmware involvement | observes, logs `+100`, → S7 | S7 |
| **Overvoltage** | latched OVP ⇒ `ARM = 0` ⇒ **both off** | observes, logs `+102`, → S7 | S7 |
| **Monitor disagreement** | — | → S4 → S5 → S7, logs `+104` | S7 |
| **Watchdog expiry** | *if firmware is alive:* nothing yet. *If firmware is dead:* heartbeat stops, HV off in ~79 ms | S3 → S4 (graceful ramp) → S5 → S0, logs `+101` | S0 |
| **Firmware crash / hang** | **heartbeat pump decays, `ARM = 0`, HV off in ~79 ms** | nothing — it cannot | off |
| **Logic supply lost** | **open-drain releases, pull-ups take `/ON` high** | nothing | off |
| **I²C/SPI fault (DAC or ADC NAK)** | — | setpoint or measurement untrustworthy ⇒ → S4 → S5 → S7 | S7 |
| **Ramp timeout** | — | → S7, logs `+106` | S7 |
| **Discharge timeout** | — | → S7, logs `+103`, **relay left in neutral** | S7 |

**Note the deliberate two-speed design.** On comms loss, firmware performs a *graceful* ramp-down —
kinder to a capacitive load, avoids a `dV/dt` transient into a detector. The hardware pump performs an
*ungraceful* chop. The graceful path is preferred; the ungraceful path is what happens when the
graceful path is not available. **Both exist. Neither depends on the other.**

### 5.5 Hard faults (latch to S7) vs soft faults (ramp down to S0)

- **Hard** (require human acknowledgement via `OUTP:PROT:CLE`): overvoltage, interlock open, monitor
  disagreement, discharge timeout, ramp timeout, DAC/ADC bus fault, reference out of tolerance.
- **Soft** (auto-recover to S0, log an error, allow `OUTP ON` again): watchdog expiry, host disconnect,
  commanded `OUTP OFF`.

A watchdog expiry is a *soft* fault deliberately: a flaky network should not require a physical visit
to the instrument. An overvoltage is a *hard* fault deliberately: it means something is broken.

### 5.6 Monitor disagreement — the check that justifies having two monitors

```
|MEAS:VOLT? − sign · MEAS:VOLT:MODule?|  >  threshold   ⇒  fault +104
```

Threshold derivation `[verified-run]`:

| Term | Value at 1 kV |
|---|---:|
| Module VMON accuracy, 1 %·Vnom | 10.00 V |
| Independent monitor, calibrated | 0.71–1.58 V |
| Quadrature sum (legitimate disagreement) | **10.03 V** |
| **Trip threshold, 2 %·Vnom** | **20.00 V** (≥ 1.7× the legitimate disagreement) |

This catches: a divider resistor gone open (monitor reads ~0 while VMON reads full scale), a stuck
relay, a module in current limit, an ADC reference collapse, and a partial HV breakdown — none of
which any single monitor detects on its own.

### 5.7 Watchdog semantics

- Any received command kicks it. `SYST:WATCH:KICK` is the explicit no-op kick.
- Default `T_wd` = **10 s**, settable via `SYST:WATCH <s>`.
- **`SYST:WATCH 0` (disable) is refused with `-221` unless a local jumper is fitted.** Disabling the
  watchdog on an HV instrument should require being in the room with a screwdriver.
- On expiry: **ramp down and disable.** Log `+101`. Never "hold last value" — that is precisely the
  watchdog that leaves HV on.
- The watchdog is a firmware timer. The **heartbeat pump (§3.7) is its hardware shadow** and covers
  the case where the firmware timer itself is not running.

---

## 6. Recommendation

### 6.1 Architecture

```
 ESP32-S3 ──SPI──> DAC8552 (dual 16-bit) ──≤10 Ω──> VSET_P / VSET_N
     │                  ▲ VREF
     │             REF5025 (2.500 V, 0.05 %, 3 ppm/K)  → also the ADC offset leg
     │
     ├──I²C──> ADS1115 ──< AIN0/1 diff : buffered HV divider tap (±1.004 V for ±1 kV)
     │                    < AIN2/3     : buffered VMON_P / VMON_N (remember their 20 kΩ)
     │
     ├──GPIO(non-strapping)──> heartbeat square wave ──> charge pump ──┐
     ├──GPIO(non-strapping)──> SEL (10 kΩ pull-DOWN) ──> Schmitt ──┐   │
     │                                    └──> edge det ──> 74HC123 ┤   │
     │                             INTLK loop ────────────────────┤   │
     │                       latched OVP comparator ──────────────┤   │
     │                                                        [ ARM ]
     │                                     ┌──────────────────────┴──────┐
     │                          /ON_P = NAND_OD(ARM, ¬SEL)   /ON_N = NAND_OD(ARM, SEL)
     │                                     │  10 kΩ ↑ +VIN        │  10 kΩ ↑ +VIN
     │                                     └─> also gates the VSET shunt FETs (§3.6)
     │
     └──USB──> CP2102N ──> USB isolator ──> host
     └──SPI──> W5500 ──> Ethernet (magnetics = ~1.5 kV isolation)   BOTH ARE CONTROL PATHS
     └──WiFi (on, and write-authoritative)                          WITH FULL WRITE AUTHORITY
        ⬛ G0-A3: the pre-G0 annotation here read "[W5500 optional; WiFi read-only]".
           That is OVERTURNED. The W5500 is NOT "populate but do not stuff", and WiFi does
           NOT default to off. Both must be built, tested and FUZZED (§4.3a).

 HV path:  module_P ─┐                    ┌─ 200 MΩ CRHV ─┬─ 402 k ─ GND
                     ├─ combiner relay ───┤               └─ 402 k ─ +2.500 V
           module_N ─┘   (neutral pos.    │                      └─> buffer ─> ADS1115
                          = 3.3 MΩ bleed) └──> OUTPUT
```

> ### ⬛ POST-G0: THE DIAGRAM ABOVE IS THE MODE-1 ARCHITECTURE. It is incomplete in four places.
>
> Retained as drawn because it is correct for mode 1 and is the base the dual-mode design extends.
> **What it does not show, all of it required:**
>
> ```
>  1. MODE SWITCH (PHYSICAL, PANEL-MOUNTED — G0-A5) + AUXILIARY LV POLES
>       module_P ─┬─ combiner relay ──┬──> OUTPUT A     [pseudo-bipolar: A is the only output]
>       module_N ─┘                   │
>                 └── MODE SWITCH ────┴──> OUTPUT B     [unipolar/dual: P→A, N→B, both live]
>                     (hand-operated,
>                      1 kV/pole, guarded)
>                          │
>                          └─ AUX LV POLES ──> MODE_POS ──> INTERLOCK   (§3.3a)
>                             ^^^^^^^^^^^^^ SAME ARMATURE AS THE HV POLES.
>                             There is NO mode relay, NO coil, and NO MODE_CMD bit.
>                             Aux poles must BREAK BEFORE the HV poles MAKE (MODE-15).
>                             Between detents ⇒ both modules off, both outputs bled (MODE-18).
>
>  2. SECOND MONITOR CHAIN  — 200 MΩ CRHV + 402k/402k + buffer + guard ring, on OUTPUT B
>                              (1.00 % of Inom each, at the budget limit — §2.4)
>
>  3. SECOND BLEED NETWORK  — on OUTPUT B, two parallel strings (§2.10 post-G0 note)
>
>  4. SECOND ADS1115        — two differential HV pairs fill one part completely (§2.8)
>
>  Plus, on the LV side:  ARM/DISARM state · comms-loss watchdog · enforced soft limits  (§4.3a)
>         and on the set path:  the 2.500 V rail IS the over-range clamp, and it is a
>                               PRIMARY SAFETY ELEMENT, not a free property of the DAC (§1.7)
> ```
>
> **Two HV output connectors, spaced for the full 2 kV differential** (MODE-05/06) — in mode 2 they
> carry **+1 kV and −1 kV simultaneously and permanently**, which is a **normal steady-state condition**,
> not a fault case.

### 6.2 The five decisions, with the reason in one line each — **and their status after G0**

1. **External SPI DAC + precision reference, not PWM.** ✅ **CONFIRMED, and the reason got stronger.**
   Session 1's argument was *accuracy*: a PWM DAC's full scale *is* the 3.3 V rail (±1–3 % and drifting)
   versus ±0.05 % and 3 ppm/°C. **G0-A2 adds a SAFETY argument that is independent of accuracy**: with
   Vref = 2.5 V, a 3.3 V-referenced source reaches **132 % of Vnom ≈ 1320 V within its normal code
   range** (§1.1). Not for speed (the module's own 100 ms pole dominates every path — the PWM settling
   penalty is +10 %) and not for resolution.
2. **200 MΩ CRHV divider + buffer + ADS1115, differential, level-shifted.** ✅ **CONFIRMED — and the
   conditional disqualification of the Caddock network is now UNCONDITIONAL.** At the selected
   `AP010504x05` the USVD draws **10.00 % of Inom**. The 200 MΩ version is 6× tighter than the module
   readback it exists to check, at **exactly 1.00 %** loading — **at the budget limit, no margin**
   (§2.4). ⬛ **G0-A4: there are now TWO of these chains, one per output, and one ADS1115 no longer
   holds the channel count (§2.8).**
3. **Interlock as a single gate output pair derived from one SEL signal and its inverse**, open-drain
   with pull-ups to the module's own +VIN, gated by a heartbeat charge pump, an external interlock
   loop, a latched hardware OVP, and a changeover monostable. Both-enabled is not expressible.
   ⬛ **MUST BE RE-DERIVED (G0-A4).** As written it implements the *old* invariant and therefore
   **forbids mode 2**. The permissive becomes **mode-conditional**, and the mode input must be the
   element's **physical position (`MODE_POS`), never a commanded bit** — **and G0-A5 supplies it from
   an AUXILIARY LV POLE of the physical MODE SWITCH, on the SAME ARMATURE as the HV poles**, so the
   permissive and the routing **cannot disagree by construction**. **`MODE_CMD` does not exist.** See
   **§3.3a**, whose algebra and truth table are **unchanged** — only the signal's origin moved, and it
   moved to something stronger than the sensed relay position A4 specified. Everything else (open
   drain, pull-ups to `+VIN`, heartbeat, INTLK, OVP, monostable) is unchanged and is now **load-bearing
   rather than defensive**, because G0-A3 removed firmware from the trust chain.
4. ⛔ ~~**Isolated USB-CDC as the control path; read/write authority selected by a physical switch.**
   Restores the physical-presence property that a network interface removes.~~
   **OVERTURNED BY G0-A3: both serial and network, FULL WRITE AUTHORITY on both.** The physical
   write-authority switch is not built. **Isolation (§4.1) is NOT overturned and matters more** — the
   HV return is GND and the case is bonded to it. See **§4.3a** for what now carries the safety case.
5. **Signed `VOLT` setpoint, non-blocking, with a mandatory error queue and `*RST`.** ◐ **CONFIRMED on
   the ATOMICITY argument; its "one terminal, one number" argument is DEAD (G0-A4).** The setpoint must
   be scoped to an **output** in mode 2, and the protocol **forks by mode** — see **§4.7a**. The error
   queue is unchanged and remains a safety defect to omit; **G0-A3 makes soft limits that error rather
   than clamp a named safety element** (ARCH-37).

### 6.2a ⬛ The decisions G0 ADDED that this study never made

| # | Decision | Source |
|---|---|---|
| 6 | **The `VSET` clamp rail is a PRIMARY SAFETY ELEMENT with its own verification** — not a free property of the DAC | G0-A2 · §1.7 · PART-33 · `SCOPE.md` S-8 |
| 7 | **Explicit ARM/DISARM, comms-loss watchdog failing to HV-OFF, and enforced soft limits are REQUIRED** | G0-A3 · §4.3a · ARCH-35/36/37 |
| 8 | **The mode permissive comes from the element's physical position, never from a commanded bit** — **and G0-A5 supplies it from an AUX POLE OF THE SAME ARMATURE that moves the HV poles**, so permissive and routing cannot disagree by construction | G0-A4 + **G0-A5** · §3.3a · MODE-03/14 |
| 9 | ⛔ ~~**A mode change is a first-class state transition; its discharge timeout TRIPS rather than falling through**~~ **— DELETED BY G0-A5.** There is no commanded mode change. **Replaced by:** a **powered-down operating procedure** with a guard and legend (MODE-17), the switch's **lead-break** aux poles (MODE-15), an **intermediate-position** decode (MODE-18), and a **runtime-change trip that forces HV OFF immediately, never gracefully** (MODE-16) | G0-A4, **deleted by G0-A5** · §5.1 note · MODE-08/15/16/17/18 |
| 10 | **Two of everything on the output side**: connector, bleed, monitor chain, guard ring, ADC channel pair | G0-A4 · §2.8 · MODE-05/07/10 |
| 11 | ⬛ **NEW (G0-A5): the mode surface is READ-ONLY.** No `MODE` setter on any interface; `MODE?` reports the physical position. **The network cannot reach the mode at all** — the one place a G0 answer made the remote attack surface *smaller* | G0-A5 · §4.7a · MODE-12 · `SCOPE.md` R-10 |
| 12 | ⬛ **NEW (G0-A5): the mode SWITCH is an unsourced part with a CONTACT-SEQUENCE requirement** — 1 kV/pole, possibly 2 kV between poles, aux LV poles, aux **breaks before** HV **makes**. **A link block or HV cable re-plug is a legitimate alternative if no switch is procurable** | G0-A5 · MODE-13/15 · `SCOPE.md` R-14 |

### 6.3 Parts shortlist

> **Every MPN below is `[unverified-MPN]` for availability. Specification tags are per-line.
> Checking live distributor stock is a G0 action item.**

| Function | Part | Key specs | Spec evidence |
|---|---|---|---|
| MCU | ESP32-S3 module (e.g. ESP32-S3-WROOM-1) | no DAC, no EMAC, dual core, native USB | `[web-verified]` (no DAC) / `[recalled]` (no EMAC) |
| Set-point DAC | **DAC8552** | dual 16-bit, SPI, **external VREF**, 2.7–5.5 V, 10 µs to ±0.003 % FSR, RRO buffer, **ACTIVE** | `[web-verified, ti.com]` |
| — 12-bit alt. | MCP4726 ×2 | **12-bit** (not 16 — see §1.2), I²C, ext. VREF, 2.7–5.5 V, 6 µs | `[web-verified, Microchip]` |
| Reference | **REF5025** | 2.500 V, ±0.05 % init, 3 ppm/°C max, ±10 mA, **ACTIVE** | `[web-verified, ti.com]` |
| ADC | **ADS1115** | 16-bit ΔΣ, 4 SE / 2 diff, I²C ×4 addr, 2.0–5.5 V, PGA ±0.256…±6.144 V, 860 SPS, int. ref + comparator | `[web-verified, ti.com]` |
| Monitor buffer | **OPA192** | Ib 20 pA max, Vos 25 µV max, RRIO, **ACTIVE**. ⚠ **min supply 4.5 V — run on +5 V** | `[web-verified, ti.com]` |
| — 3.3 V alt. | OPA333 | 1.8–5.5 V, Vos 10 µV, Ib 200 pA | `[recalled]` |
| HV divider top | **Vishay CRHV1206, 100 MΩ ±1 %** ×2 | 3000 V, 100 ppm/°C, 0.3 W, stability < 0.5 %; 1206–2512 sizes, to 50 GΩ | `[web-verified, vishay/tti]` |
| — precision alt. | Caddock USVD (1000:1) | ratio ±0.01 %, 2 ppm/°C, VCR 0.02 ppm/V, 450–2000 V — **but RT ≤ 20 MΩ; only for ≤ 400 V configs** | `[web-verified, caddock.com]` |
| Divider bottom | 402 kΩ 0.1 % 25 ppm/°C thin film ×2 | e.g. Vishay TNPW / MMA | `[recalled]` |
| **Do NOT use** | ~~Yageo RC string~~ | 0603 = 50 V; 2010/2512 = 200 V (**no better than 1206**); ±1 % range ends at 2.2 MΩ; ~1 % life drift | `[verified-artifact, datasheet]` |
| Bleed | 3.3 MΩ as 2–3 HV-rated elements | 1.52 s to 10 V @ 100 nF; 0.3 W peak; **switched by relay neutral position** | `[verified-run]` |
| Interlock logic | 74HC03 / 74LVC07 (open-drain NAND/buffer) | pull-ups 10 kΩ to +VIN | `[unverified-MPN]` |
| SEL conditioning | 74HC14 (Schmitt inverter) | with 10 kΩ pull-**down** on SEL | `[unverified-MPN]` |
| Changeover dwell | 74HC123 (retriggerable monostable) | `T_dwell` ≈ 1 s | `[unverified-MPN]` |
| Hardware OVP | TLV3201 + NAND SR latch | threshold 105 % FS, on the **buffered** divider node | `[unverified-MPN]` |
| VSET shunt | 2N7002 ×2 | gate driven directly from `/ON_P` and `/ON_N` | `[unverified-MPN]` |
| USB bridge | CP2102N | port survives MCU reset | `[unverified-MPN]` |
| USB isolation | ADuM3160 / ISOUSB211 | **safety-relevant — see §4.1** | `[unverified-MPN]` |
| Ethernet (opt.) | W5500 | SPI + hardware TCP/IP; **required because S3 has no EMAC** | `[unverified-MPN]` |
| Module blocking cap | 22 µF near each `+VIN` | **datasheet-recommended**, Table 1 note 2 | `[verified-artifact]` |

### 6.4 Design rules to carry into the schematic generator

1. Total series resistance from DAC output to the VSET **pin** ≤ **10 Ω** (§1.4).
2. No interlock, DAC-CS, or relay signal on any ESP32 strapping pin (§3.2) — **make this an
   executable check** in the netlist checker.
3. `/ON` nets: open-drain drive **plus** a 10 kΩ pull-up to that module's `+VIN` (§3.4).
4. `SEL` net: 10 kΩ pull-**down**. `EN_HB` net: no static pull-up anywhere.
5. Guard ring at tap potential around the HV divider tap, its own net, driven from the buffer output;
   conformal-coat the region; HV clearance in its own netclass (§2.6).
6. 22 µF within a few mm of each module's `+VIN` pin (Table 1 note 2) `[verified-artifact]`.
7. Soldering constraint for the module: **270 °C max, 10 s, at 1.5 mm from the case**; max case
   temperature **120 °C** `[verified-artifact, Table 1]` — a fab-note and a thermal-keepout rule.

**⬛ Rules ADDED by the G0 answers — all executable-checkable, all mandatory:**

8. **No node in the set path may be powered from, or reachable from, the 3.3 V rail.** DAC VREF, the
   DAC output stage / buffer, and everything up to the `VSET` pin run from the **2.500 V** reference.
   **This is the over-range clamp and it is a primary safety element** (§1.7, PART-33). Make it a
   netlist check: *no net that touches `VSET_*` may also touch `+3V3`*. (G0-A2)
9. **`MODE_POS` comes from an AUXILIARY LV POLE OF THE PHYSICAL MODE SWITCH, never from an MCU output**
   (G0-A5). Make it a netlist check: *the interlock's mode input net must originate at the mode
   switch's aux-pole pins and must not be driven by any MCU pin* (§3.3a). **`MODE_POS` must fail to 0**
   (**pseudo-bipolar**), with a **duplicated** pull element per ARCH-18.
   ⬛ **G0-A5 permits a strictly stronger, and strictly simpler, check than G0-A4 could:** *no MCU
   output may drive ANY mode-related net anywhere in the design* — **there is no `MODE_CMD` net to
   permit**, so the rule is an absence, which is far easier to assert than a provenance. The MCU may
   only **read** the aux poles, on a **separate** pole or through a buffer whose direction is fixed by
   construction — **never a net the MCU could also drive** (MODE-14). (G0-A4 + **G0-A5**)
10. **`MODE_POS`, `SEL`, `EN_HB`, DAC-CS and every relay drive stay off ESP32 strapping pins** — rule 2
    extended to the new signals. **G0-A5 removes one signal from this list before it was ever drawn:
    there is no mode-drive output** (no relay), only the `MODE_POS` **input**. (G0-A4 + G0-A5)
10b. ⬛ **NEW (G0-A5): the mode switch's aux poles must decode BOTH valid modes POSITIVELY** — neither
    mode may be encoded as *"the absence of the other"* — so that an **intermediate / between-detent**
    position is **distinguishable** from a valid mode and lands in both-modules-off, both-outputs-bled
    (MODE-18). This is the mode-switch analogue of NUM-09's *"an open bleed is silently undetectable"*,
    and it is checkable at the netlist level as *two independent aux nets, not one net and its inverse*.
11. **Two of everything on the output side:** connector, bleed network (two parallel strings each),
    monitor divider, buffer, guard ring net, ADC differential pair. **A generator invariant should
    assert the pair exists**, because a silently-missing second bleed is exactly the failure NUM-09
    warns about. (G0-A4)
12. **`HV_POS`↔`HV_NEG` clearance is a PERMANENT normal-condition rule, not a fault-case rule.** It must
    live in a custom `.kicad_dru` pairwise rule (NUM-03 — a netclass alone is silently 2× under-spaced),
    and all HV copper must be single-layer (NUM-04). **The two output connectors are subject to the same
    2 kV spacing as the copper.** (G0-A4) ⚠ **The constant itself is `[unverified-primary]`** — keep it
    conservative until a human reads a primary standard (NUM-01, `SCOPE.md` R-1).

---

## 7. Open questions ~~that genuinely need the human at G0~~ — **STATUS AFTER G0 (2026-07-23)**

1. ✅ **ANSWERED — "Which module configuration?"** Everything above is computed for the ~~worst case~~
   **actual case (1 kV, 0.5 mA, 0.5 W, Vref 2.5 V, 5 V in)**. **G0-A2: the modules are already owned —
   `AP010504P05` + `AP010504N05`.** Session 1 called this the only choice that makes monitor loading
   marginal (exactly 1.00 % of Inom) and discharge times long; **it is now the case, so no number needed
   rescaling.** ⛔ *"A 1 W or lower-voltage part relaxes several constraints at once and permits the
   ultra-precision Caddock divider at ≤ 400 V"* — **struck: there is no such part on this board, and the
   Caddock divider is unconditionally out.** ⬛ **And the choice went the way the study's own safety
   recommendation argued against** (Vref 2.5 V, not 5 V) — see §1.1 and §1.7.
2. ⬜ **STILL OPEN — "What is `C_out`?"** **Q3 was NOT answered at G0.** Discharge time is entirely set
   by the load capacitance, which is the user's cable and detector, not our board. 100 pF → 92 ms;
   100 nF → 92 s with the passive divider alone `[verified-run]`. The bleed sizing, the `T_dwell` and
   the S5 timeout all follow from this number — **and G0-A4 means there are now TWO of them, one per
   output.** We proceed on the declared interface limit `C_load ≤ 10 nF` **per output** (NUM-13).
3. ⬜ **STILL OPEN — "Is output current readback required?"** Not in the brief, and **G0 did not raise
   it.** If yes, it forces a system-level decision about bringing the load return back separately
   (§2.11), because the module's GND pins and case bonding preclude the obvious low-side sense.
   **G0-A4 doubles the connector implication** if it is ever wanted.
4. ✅ **ANSWERED — "Through-zero or set-and-hold?"** **G0-A1: set-and-hold with polarity changeover,
   ~1 s dead-band, output clamped to ground.** This study's assumption was correct. §3.5 and §5.2 stand.
   Smooth through-zero is **not required and is not being built**.
5. ✅ **ANSWERED, AGAINST THE RECOMMENDATION — "Is WiFi wanted at all?"** §4.3 recommended read-only.
   **G0-A3: both serial and network, FULL WRITE AUTHORITY on both** — chosen deliberately with the risk
   stated. ⇒ *"the authentication and OTA-security work must be scoped as real work, not assumed away"*
   — **that sentence is now an instruction, not a warning.** See §4.3a.
6. ⬜ **STILL OPEN — the current-monitor discrepancy (§2.11).** **Q7 was not answered; nobody has
   emailed iseg.** Still worth one email before the schematic is frozen (`DECISIONS.md` PART-20).

### 7.1 ⬛ NEW open questions, created BY the G0 answers

| # | The question, and why it is open |
|---|---|
| ~~**N-1**~~ | ~~**Which mechanism provides `MODE_POS`** — (a) physical human-set link/keyed switch, or (b) relay with an armature-position sense contact?~~ ✅ **ANSWERED SAME DAY — G0-A5: (a), a PHYSICAL SWITCH.** The premise of the question was wrong: **(a) does not cost the remote flexibility**, because *"we would need to physically change cables, anyways"*. **No mode relay, no sense path, no `MODE_CMD`.** §3.3a, MODE-04. |
| **N-7** ⬛ | **NEW (G0-A5): which physical part, and is it procurable?** 1 kV working per HV pole; **2 kV between poles** if the arrangement creates an opposite-polarity pair; **auxiliary LV poles**; **a specified contact sequence**. Candidates nobody has searched: **HV rotary switch · ceramic wafer switch · HV link block · HV cable re-plug.** **If no panel switch is procurable, the link block or re-plug is better engineering, not a concession — say so.** MODE-13, `SCOPE.md` R-14, `G0_QUESTIONS.md` O-10. |
| **N-8** ⬛ | **NEW (G0-A5): what lead-break MARGIN do the aux poles need?** The requirement is frozen (aux **break before** HV **make**, MODE-15); the **number** is not. It must exceed the interlock's propagation delay plus the `/ON`-to-HV-off response — and note the module's own 100 ms set-node pole (§0.3) means HV does **not** vanish the instant `/ON` goes high, so **the margin is a MODULE-decay question, not a logic-delay question.** **Bounded consequence if got wrong:** at ≈0.75 mA, a **current-limited polarity fight, not an energetic fault** — report it that way. `G0_QUESTIONS.md` O-11. |
| **N-2** | **Do we raise R1 above 200 MΩ?** At the confirmed 1 kV / 0.5 mA the 200 MΩ divider is at **exactly** the 1.00 % loading limit. §2.4's own remedy is 300–400 MΩ — but §2.6 shows surface leakage already costs **20 V at 1 kV** on an uncoated board at 10 GΩ, and raising R1 makes that worse. **A real trade with no free side.** |
| **N-3** | **Coating: yes or no?** §2.6 **mandates** conformal coating over the divider region for leakage; `DECISIONS.md` NUM-18 assumes **no** coating for clearance. **Both cannot be true, Q5 was not answered, and it is a process commitment that must precede layout.** |
| **N-4** | **How is the state machine replicated for two outputs?** Per-output machines with a shared supervisor, or vectorised states? **Do not let this be decided implicitly by whoever writes the firmware first.** §5.1 note, Gap 2. |
| **N-5** | **Relay coil rail voltage.** C-1 says *"the 12 V coil rail"*, written when a 12 V module supply was expected. **There is no 12 V module rail** — `+VIN` is 5 V. Either 5 V coils, or a dedicated generated 12 V rail that must be budgeted. `COMBINER_STUDY.md` §5.2 C-1. |
| **N-6** | **The four unmeasured module numbers — now measurable.** VSET step response, output capacitance, internal bleeder, turn-on time. **The modules are in hand (G0-A2), so this stops being a vendor dependency and becomes a task.** Everything in §2.9, §2.10, §3.5 and §5.2 is parametric in them. |

---

## Appendix A — reproducing the numbers

Two stdlib-only scripts produced every computed value in this document, run under
`C:/Program Files/KiCad/10.0/bin/python.exe` (any Python 3 works — no third-party imports):

- `docs/studies/control_arch_numbers.py` — §1 resolution / ripple / settling / source-impedance tables;
  §2 divider, loading, bleed; §3 glitch and heartbeat timing; §5 thresholds.
- `docs/studies/control_arch_divider.py` — corrected divider analysis after the Yageo RC /
  Caddock USVD / Vishay CRHV datasheet reads.

Both are zero-argument and deterministic; run them and diff the output against the tables above.

```
"C:/Program Files/KiCad/10.0/bin/python.exe" "docs/studies/control_arch_numbers.py"
"C:/Program Files/KiCad/10.0/bin/python.exe" "docs/studies/control_arch_divider.py"
```

**What the instruments cannot see** (per `CLAUDE.md` rule 4):

- The scripts are **arithmetic on datasheet values**. They verify no circuit. Exit code 0 means the
  algebra ran, not that the design works. Nothing here has been simulated, built, or measured.
- The ripple model is a **single-harmonic estimate**. It ignores harmonics above the fundamental
  (which are further attenuated, so the estimate is conservative) and it assumes the module's HV loop
  passes set-node ripple with the gain `Vnom/Vref`. **The module's HV control-loop bandwidth is not
  specified in the manual**; if the loop rolls off below the PWM frequency, actual ripple is lower
  than tabulated. This should be measured on the bench before the PWM fallback is ever trusted.
- The accuracy budgets use **datasheet maxima where available and stated assumptions where not**
  (CRHV voltage coefficient assumed 1 ppm/V; ADS1115 gain error 0.15 % `[recalled]`). Both are
  flagged inline and both need a datasheet read at G0.
- The leakage table (§2.6) uses **assumed** surface resistances. Real values depend on coating,
  cleanliness, and humidity, and can only be measured on the actual board.
- **Availability of every part is unverified.** One distributor deep-link consulted during this study
  returned a *completely unrelated product* (a 64-way ribbon cable in place of a DAC), which is
  precisely why no availability claim is made here.
