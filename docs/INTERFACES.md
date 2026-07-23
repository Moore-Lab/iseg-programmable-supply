# INTERFACES — contract surfaces

The boundaries between parts of this project that must not drift. Each section is owned by one file
and consumed by several; changing a contract after its gate requires a gate.

| # | Contract | Owner | Consumers | Frozen at |
|---|---|---|---|---|
| 1 | `board_spec.py` data shape | this file | schematic gen, netlist check, PCB gen, parity check, BOM/CPL | now (shape) / G1 (content) |
| 2 | Net names + netclasses | this file | `board_spec.py`, `.kicad_pro`, `.kicad_dru`, DRC | now (convention) / G1 (list) |
| 3 | ESP32 command protocol | this file | firmware, host script | G1 |
| 4 | Host script CLI | this file | the human, CI | G1 |
| 5 | Electrical/mechanical interface to the outside world | this file | the user, the enclosure, the cable | now |

---

## 1. `board_spec.py` — the golden netlist as code

**The single structural idea the bootstrap transmits (§V.1).** Authored **before any CAD file
exists**; every downstream artefact is a function of it and acceptance everywhere is a pin-exact diff
against it.

Location: `hardware/hvctl/board_spec.py`. Stdlib-only, no `pcbnew` import, runs on any Python 3.

### 1.1 Shape

```python
def build_board() -> dict:
    """The ONE source of truth for what connects to what.
    No CAD file, no coordinate, no layer. Pure connectivity + identity."""
    return {
        "meta": {
            "board":   "hvctl",
            "rev":     "A",
            "spec_version": 1,          # bump on any change after G1; a gate
        },
        "components": [ Component, ... ],
        "netclasses": { "<CLASSNAME>": NetClass, ... },
        "net_notes":  { "<NETNAME>": "why this net is special", ... },
    }
```

A **Component** is exactly this dict — no extra keys, no missing keys:

```python
{
  "ref":    "U1",                      # refdes, unique. Prefix by role: see 1.2
  "sym":    "iseg:APS_HV_MODULE_P",    # "<lib_nickname>:<symbol_name>"
  "val":    "AP010504P05",             # BOM value string; the human-readable identity
  "fp":     "iseg:iseg_APS_THT",       # "<lib_nickname>:<footprint_name>"
  "pins":   {"1": "+5V_HV", "2": "VSET_P", "3": "GND",
             "4": "nON_P",  "5": "VMON_P", "6": "HV_POS", "7": "GND"},
  "dnp":    False,                     # Do Not Populate: in schematic + BOM, not on the board
  "nc":     [],                        # pad numbers deliberately unconnected -> ERC no-connect flag
  "fields": {                          # extra BOM/traceability fields; free-form keys
      "MPN":       "AP010504P05",
      "MPN_STATUS":"unverified-MPN",   # MANDATORY until Phase 6 verifies it live
      "Mfr":       "iseg Spezialelektronik GmbH",
      "Datasheet": "iseg APS series technical documentation v2.5, 2024-08-20",
      "Assembly":  "hand",             # "hand" | "smt"  -> drives BOM/CPL split
      "Notes":     "polarity is FACTORY-FIXED by the P/N letter; not a build option",
  },
}
```

**Invariants asserted by `check_netlist.py` on every run:**

| # | Invariant |
|---|---|
| I-1 | `pins` keys are exactly the pad numbers of `fp`, and exactly the pin numbers of `sym`. Set equality, both directions. |
| I-2 | `ref` unique. Every net has **≥2 pins** unless listed in `nc` or explicitly declared single-ended (test points, mounting holes). |
| I-3 | `nc` pads appear in `pins` with net `None`, never omitted — omission is indistinguishable from a mistake. |
| I-4 | Every component has `fields["MPN_STATUS"]`. Phase 6 flips `unverified-MPN` → `verified-<distributor>-<date>`. A fab BOM containing any `unverified-MPN` is a **build failure**, not a warning. |
| I-5 | Every net matches exactly one netclass pattern (§2). Zero matches or two matches is a failure. |
| I-6 | Domain safety assertions (§1.3) all hold. |

### 1.2 Refdes prefixes

`U` active devices incl. HV modules · `K` relays · `R` `C` `L` `D` passives · `J` connectors ·
`TP` test points · `SW` switches · `F` fuses/polyfuses · `MH` mounting holes · `Q` transistors ·
`Y` crystals.

### 1.3 Domain safety assertions — promoted from review to build failure

The R-5 pattern (bootstrap §IV): a safety property that a reviewer would otherwise check by eye
becomes a function that fails the build. These run inside `check_netlist.py` against
`build_board()`, before any CAD file is written.

```python
def safety_assertions(board) -> list[str]:
    """Return specific problems; [] means pass. Each entry names ref, pin, net."""
```

| ID | Assertion | Source |
|---|---|---|
| SA-1 | Every `nON_*` net has **≥2 parallel pull-up resistors** to a rail whose nominal is ≤5.5 V. | ARCH-17, ARCH-18, PART-02, PART-03 |
| SA-2 | No `nON_*` pull-up ties to a rail that can be absent while that module's `+VIN` is present. | ARCH-17 |
| SA-3 | Every `VSET_*` net has ≥1 pull-down to GND, and **≥2** if it is the only fail-safe on that node. | ARCH-05, ARCH-18 |
| SA-4 | The op-amp driving each `VSET_*` has its positive supply pin on the **precision reference net**, not a logic rail. | ARCH-06 |
| SA-5 | **No resistor of any value** appears in series between a buffer/DAC output and a `VSET_*` pin. | ARCH-04 — 1 kΩ there is 91 V of uncommanded output |
| SA-6 | Each module's `+VIN` reaches it only through the interlock element; a direct rail-to-`+VIN` path is a failure. | ARCH-19 |
| SA-7 | The relay **coil rail** passes through the fail-safe switch (not only the module supply rail). | **COMBINER_STUDY F-1** |
| SA-8 | The COLD/permissive divider shares **no component** with the invariant-(c) monitor divider. | **F-3** |
| SA-9 | Every bleed and every HV divider top leg is **two parallel strings**, never one series chain. | NUM-09 |
| SA-10 | No net belongs to both an `HV_*` netclass and a non-HV netclass. | clearance evasion |
| SA-11 | Pins 3 and 7 of each module are on `GND` as **separate entries** (both physically present). | PART-16, LIB-02 |
| SA-12 | Every dump/crowbar resistor satisfies `1.5 · Inom · R < 60 V`. | NUM-08, PART-13 |
| SA-13 | Each module has a ≥22 µF capacitor whose other pin is `GND`, on its `+VIN` net. | PART-18 |

---

## 2. Net naming and netclasses

### 2.1 Naming convention

```
Rails            +5V  +12V  +3V3  +5V_HV  VREF  GND  AGND
HV nets          HV_POS   HV_NEG   HV_BUS   HV_OUT
HV sense         HVDIV_TAP_A   HVDIV_TAP_B   HVDIV_GUARD
Per-module       <SIGNAL>_P  /  <SIGNAL>_N       e.g. VSET_P, VMON_N, nON_P
Active-low       leading lowercase 'n'            nON_P, nRESET, nCS_DAC
Bleed / dump     BLEED_P  BLEED_N  DUMP
Interlock        ARM  ALIVE  SEL  COLD  PERMIT
Digital          I2C_SDA  I2C_SCL  SPI_SCK  SPI_MOSI  SPI_MISO  nCS_<dev>  UART_TX  UART_RX
```

Rules: **UPPER_SNAKE**; no spaces, no `/` (which reads as a hierarchical path); `_P`/`_N` suffix
means *positive/negative module*, never *differential pair*; a net that touches an HV module's pin 6
or any node that can exceed 60 V **must** carry an `HV_` prefix, because §2.2's patterns key on it.

### 2.2 Netclasses

**Every class carries all 17 KiCad-10 fields, including the SCHEMATIC ones** (`wire_width`,
`bus_width`, `line_style`, `diff_pair_*`, `microvia_*`). A PCB-only class **silently breaks eeschema
connectivity for every net in it**, and only when the project is loaded — while ERC, netlist export,
and every check built on them stay green, because **`kicad-cli` never reads `.kicad_pro`**
(bootstrap §V.3; `DECISIONS.md` NUM-05).

| Class | Pattern | Clearance | Track | Notes |
|---|---|---|---|---|
| `HV_POS` | `*/HV_POS*` | `<C_hv>` | 0.5 mm | positive module HV pin → changeover relay |
| `HV_NEG` | `*/HV_NEG*` | `<C_hv>` | 0.5 mm | negative module HV pin → changeover relay |
| `HV_OUT_A` | `*/HV_OUT_A*` | `<C_hv>` | 0.5 mm | output A: combined pseudo-bipolar (mode 1) **or** positive (mode 2) |
| `HV_OUT_B` | `*/HV_OUT_B*` | `<C_hv>` | 0.5 mm | output B: dead (mode 1) **or** negative (mode 2) |
| `HV_SENSE` | `*/HVDIV_*` | `<C_hv>` | 0.25 mm | divider taps; **driven** guard ring at tap potential (ARCH-14, and NUMBERS_PROBE §4.4 — mandatory, not a refinement) |
| `PWR` | `+5V*`, `+3V3*`, `VREF` | 0.25 mm | 0.6 mm | 5 V only — G0-A2 froze the 5 V-input family; there is no +12 V rail |
| `Default` | everything else | 0.2 mm | 0.25 mm | |

**G0-A4 split the single `HV_OUT` class into two.** In dual-unipolar mode the positive module drives
output A and the negative module drives output B **simultaneously**, so `HV_OUT_B` is a real,
permanently-classed HV net. Two outputs means two HV classes, two bleed paths, two monitor dividers
and two connectors — all of it doubled, none of it shared.

`<C_hv>` is **not frozen** — see `DECISIONS.md` NUM-01/NUM-02. Working value at the frozen part
(AP010504, Vnom = 1000 V) is **7.5 mm**, tagged **`[unverified-primary]`** pending a human reading a
primary copy of the standard. It is the *single-ended* value on purpose: a KiCad netclass clearance
is a minimum against **all** other copper, so putting 15.0 mm here would also push every HV net
15.0 mm from GND — twice what GND needs, and it would waste the board twice over.

**The pairwise rules cannot be netclasses.** KiCad's `clearance` is a per-class minimum against *all*
copper with no pairwise form. Both 2000 V pairs live in `hardware/hvctl/hvctl.kicad_dru`:

```
(version 1)
(rule "HV_POS to HV_NEG bipolar span"
  (constraint clearance (min 15.0mm))
  (condition "A.NetClass=='HV_POS' && B.NetClass=='HV_NEG'"))
(rule "HV_OUT_A to HV_OUT_B bipolar span"        ; mode 2, both live
  (constraint clearance (min 15.0mm))
  (condition "A.NetClass=='HV_OUT_A' && B.NetClass=='HV_OUT_B'"))
(rule "HV nets to board edge"
  (constraint edge_clearance (min 7.5mm))
  (condition "A.NetClass=='HV_POS' || A.NetClass=='HV_NEG' || A.NetClass=='HV_OUT_A' || A.NetClass=='HV_OUT_B'"))
```

**TWO pairwise rules now, not one** (NUMBERS_PROBE finding F-4). Ruling only the module pair leaves
every net *downstream of the changeover relay* silently spaced for 7.5 mm instead of 15.0 mm.

Three limits, all recorded: the 15.0 mm value inherits NUM-01 and is `[unverified-primary]`; a
`clearance` constraint is a **per-layer 2-D** distance, so it cannot express `HV_POS` on top vs
`HV_NEG` on bottom (≈1.6 mm of dielectric) — enforced instead by a generator invariant that **all HV
copper is single-layer** (NUM-04); and a **per-pad `(clearance …)` override REPLACES the netclass
value for that pad**, silently. NUMBERS_PROBE finding F-3 caught exactly that on pad 6 of the module
footprint (5.00 mm override against a 7.5 mm netclass) — the check must therefore read pad-level
overrides, not just class values.

**Never infer "the rule applied" from "DRC passed" — measure the copper.**

---

## 3. ESP32 command protocol

SCPI-like ASCII, `\n`-terminated, case-insensitive keywords, `?` suffix = query. Same grammar on
serial and network. **Frozen at G1**; G0-4 decides which transports are enabled and whether the
network transport may write.

### 3.1 Design rules (each traceable to a decision)

| Rule | Source |
|---|---|
| **Setpoint is a SIGNED scalar.** `VOLT -350.0`. There is no separate polarity command. | ARCH-21 — `POL NEG` + `VOLT 350` is a two-write non-atomic change whose torn state is "negative selected, magnitude still 900 from last time". A signed scalar cannot be torn. |
| `MEAS:VOLT?` returns the **independent** monitor. The module's own readback must be asked for by name (`MOD:VMON? P`). | ARCH-22, invariant (c) |
| **Every out-of-range command is an ERROR, never a silent clamp.** | REF-05 — "I asked for 900 V and got 200 V and nothing said so" must be unreachable |
| A real error queue, `SYST:ERR?`, `*RST`, `*CLS`, `*ESR?`. | REF-05 — the reference board had none, and no single command reached a known safe state |
| No query blocks the control loop. | REF-05 — the reference blocked 50 ms + 1000 `analogRead`s per query |
| Bounded parser. **Do not vendor the reference SCPI parser.** | REF-07 |
| Readback is calibrated **per polarity**. | COMBINER_STUDY F-20 |

### 3.2 Command surface

```
*IDN?                      -> "YALE,HVCTL,<serial>,<fw-version>"
*RST                       ARM off, setpoint 0, dump asserted, errors cleared. The one command
                           that reaches a known safe state from anywhere.
*CLS                       clear error queue and status
SYSTem:ERRor?              -> "<code>,\"<text>\""   0,"No error" when empty

# --- set path -------------------------------------------------------------
VOLTage <signed volts>     signed setpoint. Sign selects polarity. Out of range -> error.
VOLTage?                   -> commanded setpoint (NOT a measurement; named so)
OUTPut ON | OFF            ARM. OFF is always accepted and always safe.
OUTPut?                    -> ON | OFF | INTERLOCK | FAULT | CHANGEOVER | DISCHARGE

# --- measurement ----------------------------------------------------------
MEASure:VOLTage?           -> independent monitor, signed, volts. THE readback.
MEASure:VOLTage:RAW?       -> raw ADC counts + gain/offset in use (for calibration audit)
MODule:VMON? P|N           -> that module's own opinion, unsigned. Never used for safety.
MODule:STATus? P|N         -> ENABLED|DISABLED|POWERED|UNPOWERED
INTerlock?                 -> OK | TRIPPED,<reason>
STATus?                    -> one-line machine-parseable snapshot of the whole state machine

# --- diagnostics (refuse unless OUTPut is OFF) ----------------------------
TEST:BLEED?                commanded dump, measure tau, compare to expected  -> PASS|FAIL,<tau_ms>
TEST:INTerlock?            power-up weld/stuck-contact self-test             -> PASS|FAIL,<detail>
CALibration:...            per-polarity gain/offset, write-protected
```

### 3.3 State machine

```
   OFF ──ARM──▶ RAMP ──▶ HOLD ──setpoint sign change──▶ DISCHARGE ──▶ CHANGEOVER ──▶ RAMP
    ▲                      │                                │
    └──────── OUTP OFF ────┴──── any fault ──▶ FAULT ◀───────┘  (latched; needs *RST)
```

**`DISCHARGE → CHANGEOVER` is the one transition that must never fall through on timeout.** Every
other timeout may degrade toward OFF because OFF is safe; this one would hot-switch at unknown high
voltage and weld a contact. On discharge timeout: **TRIP, leave the switch in neutral, tell a human**
(ARCH-24).

Additional hard rules: `FAULT` is latched · monitor disagreement >2 %·Vnom trips (ARCH-23) ·
loss of the independent monitor (I²C hang, ADC fail) is a **fault**, and firmware must respond by
*stopping the heartbeat*, which drops HV in hardware (ARCH-20).

### 3.4 Transports

| | Serial (USB-CDC / UART) | Network |
|---|---|---|
| Enabled | yes (default) | **G0-4** |
| Write authority | yes | **default NO — read-only telemetry**; writes gated by a physical switch |
| Rationale | — | Remote control is an RCE path to a device that can kill (R-10). If write is required, authentication and OTA security must be scoped as real, maintained work. |

---

## 4. Host script

`host/hvctl.py` — stdlib-only, no third-party dependencies (matching the project's design), one file.

```
python hvctl.py --port COM7 idn
python hvctl.py --port COM7 set -350.0
python hvctl.py --port COM7 on
python hvctl.py --port COM7 read                 # -> signed volts from the INDEPENDENT monitor
python hvctl.py --port COM7 sweep --from -500 --to 500 --step 50 --dwell 2.0 --csv run.csv
python hvctl.py --port COM7 selftest             # TEST:BLEED? + TEST:INTerlock?
python hvctl.py --port COM7 off
python hvctl.py --host 192.168.1.50 read         # network transport, same verbs
```

Contract: exit `0` ok · `1` device reported an error (printed verbatim from `SYST:ERR?`) ·
`2` transport failure. `--csv` rows are
`iso8601,setpoint_v,meas_v,module_vmon_v,state,interlock`. The script **always** issues `OUTP OFF`
on `SIGINT` and on any unhandled exception before exiting.

---

## 5. External interface — the contract with the user and the enclosure

| Item | Value | Source |
|---|---|---|
| HV output connector | **SHV** panel jack, chassis-grounded shell | NUM-12 |
| **Maximum load capacitance** | **`C_load ≤ 10 nF`** — a hard limit, stated on the panel label and in the manual | NUM-13. It is simultaneously the discharge limit and the fault-energy limit. Max permissible is ~19.5 nF; 10 nF carries margin. Consider enforcing it physically with an in-line HV resistor in the cable. |
| Total output capacitance on the board | **< 50 nF ⇒ fit NO bulk HV filter capacitor** | NUM-06 — above this the board becomes a hazardous-stored-**energy** source, not merely a hazardous-voltage one |
| Output return | chassis / earth. Module GND is **not** floated | PART-26 |
| Supply input | 5 V / 1.7 A (0.5 W family) **or** 12 V / 1.1 A (1 W family) | NUM-11 — sized by the ESP32 WiFi burst, not by the HV modules |
| Enclosure | earthed metal chassis · tool-required access · **lid interlock that CLOSES to pull `/ON` HIGH** · ventilation for 4.2–6.4 W · HV-present indication · HV labelling | NUM-23. Note the interlock polarity: a switch that *opens* on lid removal is exactly backwards, because `/ON` open ⇒ HV ON (PART-02). |
| Bench cable | SHV–SHV, ≤2 m nominal, ~100 pF/m assumed | NUM-19 |
