# PART REFERENCE — iseg APS series HV print module

**This file is the authoritative part reference for the iseg APS module family in this
project. Downstream generators (symbol, footprint, netlist, firmware scaling constants)
cite *this file*, and this file cites the vendor documents.**

---

## 0. Source documents and citation

| role | document | version | date | path |
|---|---|---|---|---|
| **primary / authoritative** | iseg APS series technical documentation | **2.5** | **2024-08-20** | `references/iseg_manual_APS_en.pdf` |
| secondary / superseded, kept for cross-check | iseg APS series technical documentation | **2.1** | **2019-06-03** | `references/Phys439-alpha-lab/circuit/parts/iseg_datasheet_APS_en_2.1.pdf` |

Cite in text as: **iseg APS series technical documentation v2.5, 2024-08-20**
(older copy: **v2.1, 2019-06-03**).

> **The pin map in §1 is transcribed from iseg APS series technical documentation
> v2.5, Table 4, page 9 (PDF page index 8), dated 2024-08-20.**

Where v2.1 and v2.5 disagree, **v2.5 wins**; every difference is listed in §9.

PDF internal metadata confirms the primary document's creation date as
`D:20240820142451+02'00'`, matching its stated "Last changed on: 2024-08-20".
[verified-run — `fitz` metadata read this session]

### 0.1 How this file was produced (instruments, and what each is blind to)

| what | instrument | blind to |
|---|---|---|
| all body text and Tables 1–4 | `page.get_text()` under `PY_KICAD` + bundled `fitz` (PyMuPDF 1.28.0) | table *cell spans* — merged vs split columns are invisible in the text stream, so every merged row in §2 was re-confirmed by rasterising the table |
| merged/split cells in Table 1 and Table 4 | page rasterised at 4× and read visually | nothing relevant; this is the ground truth for §1–§2 |
| Figure 1 (dimensional drawing) | **raster image, xref 881, 2000×400 px, placed at (56.8, 605.9)–(530.2, 700.6) pt on page index 7.** Rasterised via `page.get_pixmap(matrix=Matrix(12,12), clip=…)` and read visually. Direct `Pixmap(doc, xref)` extraction yields an all-black image because the image carries an SMask — **you must render the page, not extract the xref.** | dimension *text* is outlined artwork, not extractable text; nothing in the PDF text stream contains "39,6", "34,8", "1,8" etc. |
| Figure 1 numbers, **independent check** | pixel measurement of the rendered bottom view at 24×, scaled by the 2.54 mm pin pitch measured in the same image — see §5.4 | absolute accuracy ≈ ±0.5 mm on body-referenced dimensions, because the case outline is a thick stroke; it can confirm a transcription, not refine it |
| Figure 2 (control principle) | **raster image, xref 1011, 4960×3072 px, placed at (58.1, 373.3)–(320.9, 518.2) pt on page index 8.** Rendered at 8–16× and read visually. | component *tolerances* — the figure gives nominal values only |
| cross-version check | the same two figures in v2.1 (Fig 1 = xref 17 on page index 2; Fig 2 = xref 21 on page index 3) rendered at 10× | — |

[verified-run] every row above was executed this session.

### 0.2 Re-running the checks

This file's geometry claims are not assertions, they are re-derivable. Two zero-argument
acceptance checks live in `tools/`; run them after any edit to §5 or §6.

```
# section 6 arithmetic, and that the re-derived numbers are the ones printed here.
# stdlib only, runs on ANY Python 3.  Independent truth = the arithmetic.
# (plain `python` is not on PATH in this environment -- use an absolute path;
#  PY_KICAD will do, it is just a Python 3.)
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/verify_part_iseg_aps_math.py

# section 5 mechanical transcription against the vendor's ARTWORK, in pixels.
# needs fitz + numpy, so PY_KICAD is REQUIRED here, not merely convenient.
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/verify_part_iseg_aps_drawing.py
```

Exit 0 = pass, 1 = a check failed, 2 = structural failure (file missing, wrong
interpreter, figure not parsed). Both returned **0** this session [verified-run].

---

## 1. Pin assignment

**Transcribed from iseg APS series technical documentation v2.5, Table 4, page 9,
dated 2024-08-20.** Seven pins. In v2.5 the VALUE column is split into a `Vin = 5V`
sub-column and a `Vin = 12V` sub-column; the `/ON` row spans both.

| PIN | NAME | DESCRIPTION | VALUE (Vin = 5 V) | VALUE (Vin = 12 V) |
|:--:|:--|:--|:--|:--|
| 1 | `+VIN` | Vin supply voltage | +5 V | +12 V |
| 2 | `VSET` | Vset set voltage | 0 … 2.5 V | 0 … 5 V |
| 3 | `GND` | Ground | — | — |
| 4 | `/ON` | Signal ON | TTL-level: **LOW or n.c. → HV ON**; **HIGH → HV OFF** *(spans both columns)* | ← |
| 5 | `VMON` | Vmon monitor voltage | 0 … 2.5 V | 0 … 5 V |
| 6 | `HV` | Vout high voltage output | — | — |
| 7 | `GND` | Ground | — | — |

Notes carried from the table:

- Pins **3 and 7 are one row in the source table** (`3/7  GND  Ground`) — two physically
  separate pins, one net.
- **"Case is connected to GND."** The moulded steel can is the ground net.
- There is **no separate HV-return pin.** The HV output is referenced to GND (pins 3/7).
- The table's caption in v2.5 reads *"Table 4: Technical data: options and order
  information"* — a copy-paste error in the vendor document; it is the pin assignment
  table. Recorded here so nobody "corrects" this file to match the wrong caption.

Machine-readable form for downstream generators (pin number → name, electrical type):

```
1  +VIN   power_in
2  VSET   input
3  GND    power_in
4  /ON    input          # active LOW; LOW or open = HV ON
5  VMON   output         # >= 20 kOhm source impedance, see 6.1
6  HV     output         # high voltage
7  GND    power_in       # same net as pin 3; case is on this net
```

---

## 2. Specifications (Table 1, v2.5, page 7)

Complete transcription. "**both**" means the source cell spans the 0.5 W and 1 W
columns (re-confirmed by rasterising the table, not inferred from the text stream).

| SPECIFICATION | APS 0.5 W | APS 1 W |
|:--|:--|:--|
| Out voltage Vnom | *(cell empty in source — see Table 2, §3)* | *(empty)* |
| Polarity | **both:** Factory fixed, positive or negative | |
| Ripple and noise ⁽¹ | **both:** typ. < 10 mV p-p \| max. < 30 mV p-p [f > 10 Hz] \| < 5 mV p-p [f > 2 kHz] | |
| Stability [ΔVout vs ΔVin] ⁽¹ | **both:** < 1 · 10⁻³ · Vnom | |
| Stability [ΔVout vs ΔRload] ⁽¹ | **both:** < 2 · 10⁻³ · Vnom | |
| Temperature coefficient | **both:** < 50 ppm/K ⁽³ | |
| Supply voltage ⁽² Vin | 4.5 – 5.5 V | 11.5 – 15.5 V |
| Supply current Iin, at Vout = 0 | < 5 mA | < 5 mA |
| Supply current Iin, at Vout = Vnom / no load | < 25 mA | < 18 mA |
| Supply current Iin, at Vout = Vnom / with load | < 180 mA | < 150 mA |
| Set / Monitor voltage | 0 – 2.5 V | 0 – 5 V |
| Adjustment accuracy | **both:** ± 1 % ⁽³ | |
| Voltage monitor accuracy | **both:** 1 % · Vnom | |
| **Current monitor accuracy** | **both:** 1 % · Inom — **see §10.8; there is no current-monitor pin on this part** | |
| Signal /ON | **both:** `/ON = 0 (LOW or open) → VOUT according setting`; `5.5 V ≥ V/ON > 2.5 V (HIGH) → VOUT = 0 !` | |
| Reference voltage Vref (internal) | 2.5 V ± 1 % | 5 V ± 1 % |
| Control Vset — version 1 | **both:** with Rset between Vset and GND: `Rset = Vout · 10 kΩ / (Vnom − Vout)` | |
| Control Vset — version 2 | with Vset (Ri ≪ 10 kΩ): `0 ≤ Vset ≤ 2.5 V → 0 ≤ Vout ≤ Vnom ± 1.0 %` ⁽³ | with Vset (Ri ≪ 10 kΩ): `0 ≤ Vset ≤ 5 V → 0 ≤ Vout ≤ Vnom ± 1.0 %` ⁽³ |
| ″ | **both, bold in source:** **Attention! Output voltage is internally not limited!** | |
| ″ | At Vset > 2.5 V → Vout > Vnom is possible! **Do not use Vset > 2.5 V !** | At Vset > 5 V → Vout > Vnom is possible! **Do not use Vset > 5 V !** |
| Protection | **both:** Overload and short circuit protected | |
| HV connector | **both:** Pin | |
| Maximum soldering temperature | **both:** 1.5 mm from case for 10 sec, 270 °C | |
| Maximum case temperature | **both:** 120 °C | |
| Case | **both:** Metal box steel, moulded | |
| Dimensions – L/W/H | **both:** 40 / 16 / 11 mm  *(rounded — the drawing says 39.6 / 15.7 / 11, see §5)* | |
| Operating temperature | **both:** 0 – 40 °C | |
| Storage temperature | **both:** −20 – 60 °C | |
| Humidity | **both:** max. 70 %, not condensing | |

Source notes, verbatim in substance:

1. Specifications for **stability, ripple and noise are guaranteed only in the range
   `2 % · Vnom < Vout ≤ Vnom`**.
2. **Blocking circuit is recommended** for ripple rejection to the input line, **22 µF
   near pin +VIN**.
3. Temperature coefficient and accuracy are guaranteed in the temperature range 0 – 40 °C.

---

## 3. Configurations (Table 2, v2.5, page 8)

Ten catalogue configurations. `x` in the item code is the polarity letter **P** or **N**.
The trailing `rk` in the v2.5 printing are the *revision* and *customization* digits and
**are omitted when there is no revision or customization** — so the ordinary orderable
code is e.g. `AP002255P05`, eleven characters.

| Type | Vnom | Inom ⁽¹ | Ripple/Noise typ. (mVpp) | Ripple/Noise max. (mVpp) | Vin | Pnom | Item code |
|:--|--:|--:|--:|--:|:--|:--|:--|
| APx 02 255 | 200 V | 2.5 mA | < 10 | < 30 | 5 V | 0.5 W | `AP002255x05rk` |
| APx 04 125 | 400 V | 1.2 mA | < 10 | < 30 | 5 V | 0.5 W | `AP004125x05rk` |
| APx 06 804 | 600 V | 0.8 mA | < 10 | < 30 | 5 V | 0.5 W | `AP006804x05rk` |
| APx 08 604 | 800 V | 0.6 mA | < 10 | < 30 | 5 V | 0.5 W | `AP008604x05rk` |
| APx 10 504 | 1 kV  | 0.5 mA | < 10 | < 30 | 5 V | 0.5 W | `AP010504x05rk` |
| APx 02 505 | 200 V | 5 mA   | < 10 | < 30 | 12 V | 1 W | `AP002505x12rk` |
| APx 04 255 | 400 V | 2.5 mA | < 10 | < 30 | 12 V | 1 W | `AP004255x12rk` |
| APx 06 165 | 600 V | 1.6 mA | < 10 | < 30 | 12 V | 1 W | `AP006165x12rk` |
| APx 08 125 | 800 V | 1.2 mA | < 10 | < 30 | 12 V | 1 W | `AP008125x12rk` |
| APx 10 105 | 1 kV  | 1 mA   | < 10 | < 30 | 12 V | 1 W | `AP010105x12rk` |

1. **Iout is limited to approx. 1.5 · Inom.**

Observations that matter for module selection:

- Pnom is *not* Vnom · Inom. `AP010504` is 1 kV × 0.5 mA = 0.5 W exactly, but
  `AP002255` is 200 V × 2.5 mA = 0.5 W, and `AP006804` is 600 V × 0.8 mA = 0.48 W.
  The family is constant-power to within rounding.
- **A bipolar pair must be two separate item codes differing only in the polarity
  letter** — e.g. `AP004125P05` + `AP004125N05`. They are not the same part; nothing
  in the documentation implies they are matched or binned as a pair.

---

## 4. Item-code decoder (Table 3, v2.5, page 8)

```
        AP   002    255      P        05        r          k
        │     │      │       │        │         │          │
        │     │      │       │        │         │          └── customization, one digit
        │     │      │       │        │         └───────────── revision, one digit
        │     │      │       │        │                        0 = no revision, A = first
        │     │      │       │        │                        revision, B = second, …
        │     │      │       │        └─────────────────────── input voltage, two
        │     │      │       │                                 significant digits
        │     │      │       │                                 05 = 5 V, 12 = 12 V
        │     │      │       └──────────────────────────────── polarity
        │     │      │                                         P = positive, N = negative
        │     │      └──────────────────────────────────────── Inom, expressed in nA as
        │     │                                                two significant digits
        │     │                                                followed by the count of
        │     │                                                trailing zeros
        │     └─────────────────────────────────────────────── Vnom, three significant
        │                                                      digits × 100 V
        └───────────────────────────────────────────────────── product family: APS
```

**"Without revision or customization, these digits are omitted."**

Worked decodes — the Inom field is the one people get wrong, so all ten are checked:

| field `nnd` | reading | nA | mA | catalogue Inom | ✓ |
|:--|:--|--:|--:|--:|:--:|
| `255` | 25 followed by 5 zeros | 2 500 000 | 2.5 | 2.5 mA | ✓ |
| `125` | 12 followed by 5 zeros | 1 200 000 | 1.2 | 1.2 mA | ✓ |
| `804` | 80 followed by 4 zeros | 800 000 | 0.8 | 0.8 mA | ✓ |
| `604` | 60 followed by 4 zeros | 600 000 | 0.6 | 0.6 mA | ✓ |
| `504` | 50 followed by 4 zeros | 500 000 | 0.5 | 0.5 mA | ✓ |
| `505` | 50 followed by 5 zeros | 5 000 000 | 5.0 | 5 mA | ✓ |
| `165` | 16 followed by 5 zeros | 1 600 000 | 1.6 | 1.6 mA | ✓ |
| `105` | 10 followed by 5 zeros | 1 000 000 | 1.0 | 1 mA | ✓ |

Vnom field: `002` → 2 × 100 V = 200 V; `010` → 10 × 100 V = 1 kV. ✓

Example: **`AP004125N05`** = APS, 400 V, 1.2 mA, **negative**, 5 V input, no revision,
no customization → the 0.5 W 400 V negative module.
Its positive twin is **`AP004125P05`**.

> v2.1 prints the polarity letters in lower case (`p` / `n`) and has **no** revision or
> customization digits at all. Use the v2.5 upper-case, seven-field form.

---

## 5. Mechanical — Figure 1, v2.5, page 8

### 5.1 Dimensions read off the drawing

Every number below is read from the rendered vector artwork of Figure 1 (there is no
extractable text in that figure) and is identical in v2.1 Figure 1.

| symbol | value | where it appears |
|:--|:--|:--|
| **L** | **39.6 mm** | top view, overall body length |
| **W** | **15.7 mm** | top view, overall body width |
| **H** | **11 mm** | side view, body height |
| pin cross-section | **□ 0.64 mm** (square) | side view, `□0,64` |
| pin length below case | **2.2 mm ± 0.4** | side view, `2,2 ±0,4` |
| pin pitch, pins 1–5 | **2.54 mm** | bottom view, `2,54` |
| pin 1 → pin 5 span | **10.16 mm** | bottom view, `10,16` (= 4 × 2.54) |
| column separation | **34.8 mm** | bottom view, `34,8` — pins 1–5 column to pins 6/7 column |
| end overhang at the pins 1–5 column | **1.8 mm** | bottom view, `1,8` |
| side overhang beyond pin 5 | **3 mm** | bottom view, `3` |

The datasheet spec table (§2) rounds L/W/H to **40 / 16 / 11 mm**. **Use the drawing
numbers, not the spec-table numbers,** for anything geometric.

### 5.2 Derivation of the two dimensions the drawing does not label

Only two of the four body overhangs are dimensioned. The other two follow:

```
along L (long axis, 39.6 mm):
    L = (overhang at pins 1..5 end) + (column separation) + (overhang at pins 6/7 end)
    39.6 = 1.8 + 34.8 + X          =>  X = 39.6 - 1.8 - 34.8 = 3.0 mm

along W (short axis, 15.7 mm):
    W = (overhang above pin 1) + (pin1..pin5 span) + (overhang below pin 5)
    15.7 = Y + 10.16 + 3.0         =>  Y = 15.7 - 10.16 - 3.0 = 2.54 mm
```

So the four overhangs are **1.8 / 3.0** along L and **2.54 / 3.0** along W.

### 5.3 The consequence: the body is NOT centred on the pin rectangle

```
body centre  vs  pin-array centroid, along L:  (3.0 - 1.8)  / 2 = 0.60 mm
body centre  vs  pin-array centroid, along W:  (3.0 - 2.54) / 2 = 0.23 mm
```

The body centre is displaced **0.60 mm away from the pins 1–5 column** and
**0.23 mm away from pin 1's side**. A footprint that draws the body symmetrically about
the pin array is wrong by that much. See §5.5.

**Mnemonic for orientation checking:** *pin 1 sits at the corner where the case overhangs
least in **both** axes* (1.8 mm and 2.54 mm). Pin 6 sits at the corner where it overhangs
most in both (3.0 mm and 3.0 mm).

### 5.4 Independent verification of §5.1–§5.3

The dimension labels were checked against the artwork itself, without reading them:
Figure 1's bottom view was rasterised at 24×, the case outline strokes and the seven pin
squares were located by pixel profile, and everything was scaled by the **pin pitch
measured in the same image** (182.00 px, uniform to 0.00 px across all four gaps). The
case outline is a thick stroke, so each body-referenced dimension is reported as a
bracket **[stroke centre-line … stroke outer edge]**; a correct transcription must land
inside the bracket.

```
pin pitch = 182.00 px  (5 rows, max deviation 0.00 px)  ->  ruler 0.013956 mm/px

dimension                        centreline      outer    label   verdict
-------------------------------------------------------------------------
pin1..pin5 span                      10.160     10.160    10.16   IN BRACKET
column separation                    34.796     34.796    34.8    IN BRACKET
body length L                        39.175     40.110    39.6    IN BRACKET
body width  W                        15.317     16.175    15.7    IN BRACKET
gap: pin1..5 col -> end edge          1.566      2.034     1.8    IN BRACKET
gap: pin6/7 col  -> end edge          2.812      3.280     3.0    IN BRACKET
gap: pin5 -> near long edge           2.819      3.245     3.0    IN BRACKET
gap: pin1 -> near long edge           2.338      2.770     2.54   IN BRACKET

pin 7 row vs pin 1 row: +0.042 mm      pin 6 row vs pin 5 row: +0.042 mm   (expect 0)

ASYMMETRY, measured from the artwork:
  end gaps  1.566 mm vs 2.812 mm  ->  body offset +0.623 mm along L
  side gaps 2.338 mm vs 2.819 mm  ->  body offset +0.241 mm along W
  datasheet-derived (§5.3):            0.600 mm along L,  0.230 mm along W
```

[verified-run] — `tools/verify_part_iseg_aps_drawing.py`, executed this session under
`PY_KICAD`, exit code 0. Re-run it after any edit to §5.

Two independent results worth keeping:
- **Column separation measures 34.796 mm against a label of 34.8 mm** — 4 µm. The pin
  geometry in the artwork is drawn to scale and the transcription is right.
- **The asymmetry is visible in the pixels, not just in the arithmetic**: 0.623 mm and
  0.241 mm measured, 0.600 mm and 0.230 mm derived. The body offset is real.

*What this instrument cannot see:* it measures the vendor's **drawing**, not a module.
It cannot detect an error in the vendor's artwork, cannot see tolerances (only the pin
length carries one, ±0.4 mm), and its ±0.5 mm bracket on body-referenced dimensions is
too coarse to refine any number — only to confirm one. **A physical module must be
measured with calipers before fabrication.**

### 5.5 Defect in the existing reference footprint — fix, do not copy

`references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.pretty/ISEG_HV_MODULE.kicad_mod`
[verified-artifact — read this session] places its pads correctly at
`(±17.399, ±5.08)` — 34.798 mm × 10.16 mm, the imperial rounding of 34.8 × 10.16 — but
draws the body on `F.Fab`, `F.SilkS` and `F.CrtYd` **centred on the pin array**:

```
fp_line ... (start -19.812 -7.874) (end 19.812 -7.874)   # and the other three sides
```

i.e. ±19.812 × ±7.874 about the pin centroid, which is 39.624 × 15.748 mm centred.
Against the correct placement (§6.3) the outline is wrong by:

| edge | reference footprint | correct | error |
|:--|--:|--:|--:|
| pins 1–5 end | −19.812 | −19.20 | **0.612 mm too far out** |
| pins 6/7 end | +19.812 | +20.40 | **0.588 mm too short** |
| pin 1 side | −7.874 | −7.62 | **0.254 mm too far out** |
| pin 5 side | +7.874 | +8.08 | **0.206 mm too short** |

**The same file contradicts itself.** Its 3D model is attached with
`(offset (xyz -19.2278 -7.62 0))` — and `(−19.2278, −7.62)` is, to 0.028 mm, exactly the
**correct** minimum body corner in the pin-centroid frame. The STEP placement follows the
datasheet; the fab/silk/courtyard outline does not. Our footprint generator must produce
the asymmetric outline and must not inherit the symmetric one.

---

## 6. Coordinate tables for the footprint generator

These are the numbers a downstream generator consumes. Nothing below is estimated;
everything is §5.1 plus the §5.2 derivation.

### 6.1 Frames

Two frames, plus a legacy one:

- **Frame T — KiCad F.Cu / top view.** Origin at **pin 1**. **+x toward pin 7**,
  **+y toward pin 5**. KiCad's y axis points *down* on screen, and in Figure 1's top view
  pin 5 is *below* pin 1, so this frame reproduces the manual's top view directly:
  pin 1 top-left, pin 5 bottom-left, pin 7 top-right, pin 6 bottom-right. **This is the
  frame the footprint is authored in.**
- **Frame B — bottom view, as printed in Figure 1.** Origin at pin 1, page-right is +x
  (so pin 7 is at *negative* x, because the bottom view mirrors the top view), page-down
  is +y. Given so the generator's output can be eyeballed against the printed bottom view.
  `x_B = −x_T`, `y_B = +y_T`.
- **Frame C — pin-array centroid.** Origin at the centre of the 34.8 × 10.16 mm pin
  rectangle, axes as Frame T. Only used to state the reference-footprint defect (§5.5).

### 6.2 Pin coordinates

```
FRAME T — KiCad F.Cu (top view), origin = PIN 1, +x -> pin 7, +y -> pin 5
=========================================================================
                                       relative to        relative to
  pin  name    net role                   PIN 1            BODY CENTRE
  ---  ------  ---------------------  ---------------   ------------------
   1   +VIN    supply in              (  0.00,  0.00)   (-18.00,  -5.31)
   2   VSET    analog in              (  0.00,  2.54)   (-18.00,  -2.77)
   3   GND     ground                 (  0.00,  5.08)   (-18.00,  -0.23)
   4   /ON     digital in, act. LOW   (  0.00,  7.62)   (-18.00,   2.31)
   5   VMON    analog out             (  0.00, 10.16)   (-18.00,   4.85)
   6   HV      high voltage out       ( 34.80, 10.16)   ( 16.80,   4.85)
   7   GND     ground                 ( 34.80,  0.00)   ( 16.80,  -5.31)

  body outline    x from  -1.80 to  37.80        x from -19.80 to  19.80
                  y from  -2.54 to  13.16        y from  -7.85 to   7.85
  body centre           ( 18.00,  5.31)                 (  0.00,   0.00)
  pin-array centroid    ( 17.40,  5.08)                 ( -0.60,  -0.23)


FRAME B — bottom view as printed in Fig 1, origin = PIN 1, page-right = +x
=========================================================================
  x_B = -x_T ,  y_B = +y_T          (pure mirror about the pin 1-5 column)

                                       relative to        relative to
  pin  name                              PIN 1            BODY CENTRE
  ---  ------                        ---------------   ------------------
   1   +VIN                          (  0.00,  0.00)   ( 18.00,  -5.31)
   2   VSET                          (  0.00,  2.54)   ( 18.00,  -2.77)
   3   GND                           (  0.00,  5.08)   ( 18.00,  -0.23)
   4   /ON                           (  0.00,  7.62)   ( 18.00,   2.31)
   5   VMON                          (  0.00, 10.16)   ( 18.00,   4.85)
   6   HV                            (-34.80, 10.16)   (-16.80,   4.85)
   7   GND                           (-34.80,  0.00)   (-16.80,  -5.31)

  body outline    x from -37.80 to   1.80        x from -19.80 to  19.80
                  y from  -2.54 to  13.16        y from  -7.85 to   7.85
  body centre           (-18.00,  5.31)


FRAME C — pin-array centroid (legacy; the reference footprint's frame)
=========================================================================
  pin 1 (-17.40, -5.08)   pin 2 (-17.40, -2.54)   pin 3 (-17.40,  0.00)
  pin 4 (-17.40,  2.54)   pin 5 (-17.40,  5.08)
  pin 6 ( 17.40,  5.08)   pin 7 ( 17.40, -5.08)

  body outline    x from -19.20 to  20.40 ,  y from -7.62 to  8.08
  (the reference footprint draws -19.812..19.812 / -7.874..7.874 — see 5.5)
```

Arithmetic check of Frame T, body-centre column, all four edges:

```
  body left   = pin1.x - 1.80  = -1.80    and  -19.80 - (-18.00) = -1.80   ok
  body right  = pin6.x + 3.00  = 37.80    and   19.80 -   16.80  =  3.00   ok
  body top    = pin1.y - 2.54  = -2.54    and  -7.85 - (-5.31)   = -2.54   ok
  body bottom = pin5.y + 3.00  = 13.16    and   7.85 -    4.85   =  3.00   ok
  L = 37.80 - (-1.80) = 39.60   ok        W = 13.16 - (-2.54) = 15.70   ok
```

Every number in §6.2 and §6.3 is re-derived from the five Figure 1 primitives and
compared against the text printed above by `tools/verify_part_iseg_aps_math.py`
[verified-run — executed this session, exit code 0]. *What that check cannot see:* it
verifies internal consistency, not correctness of the five primitives — those are
covered by §5.4, and neither instrument has touched a physical module.

### 6.3 Constants block for the generator

```python
# iseg APS series technical documentation v2.5, 2024-08-20, Figure 1 (page 8)
# and Table 4 (page 9).  See docs/PART_iseg_APS.md.
PIN_PITCH_MM        = 2.54
COLUMN_SEP_MM       = 34.80     # pins 1..5 column  <->  pins 6/7 column
PIN1_TO_PIN5_MM     = 10.16     # = 4 * PIN_PITCH_MM
BODY_L_MM           = 39.60
BODY_W_MM           = 15.70
BODY_H_MM           = 11.00
PIN_SQUARE_MM       = 0.64      # square cross-section
PIN_LEN_MM          = 2.20      # below the case, tolerance +/-0.40
OVERHANG_PIN15_END  = 1.80      # body edge beyond the pins 1..5 column
OVERHANG_PIN67_END  = 3.00      # derived: 39.60 - 1.80 - 34.80
OVERHANG_PIN1_SIDE  = 2.54      # derived: 15.70 - 10.16 - 3.00
OVERHANG_PIN5_SIDE  = 3.00

# Frame T (KiCad F.Cu, origin = pin 1, +x -> pin 7, +y -> pin 5)
PADS_MM = {1: (0.00, 0.00), 2: (0.00, 2.54), 3: (0.00, 5.08), 4: (0.00, 7.62),
           5: (0.00, 10.16), 6: (34.80, 10.16), 7: (34.80, 0.00)}
BODY_MM = (-1.80, -2.54, 37.80, 13.16)     # x0, y0, x1, y1  -- NOT centred on PADS_MM
```

### 6.4 Land pattern — engineering decision, NOT from the datasheet

**The documentation specifies no recommended PCB land pattern**: no hole diameter, no pad
diameter, no keepout, no clearance around the HV pin. See §10.9. What we can say:

- The pin is 0.64 mm square → **body diagonal 0.905 mm**. A finished hole below that will
  not accept the pin.
- IPC-2222 level-B style allowance (max lead dimension + ~0.25 mm) puts the finished hole
  around **1.15 mm**. The reference footprint used a 1.143 mm (0.045″) drill with a
  1.778 mm (0.070″) pad and was built and used [verified-artifact — the file exists and
  specifies those numbers; **this session has no evidence the assembled board worked**].
- Pad 1 should be rectangular, the rest round, per normal practice.
- **Clearance around pad 6 (HV) is a netclass/DRC decision at Phase 1, not a datasheet
  number.** On the module itself pad 6 is only 10.16 mm from pad 7 (GND) — the module's
  own internal spacing, which tells us nothing about what our board needs at 1 kV.
- Through-hole, hand or selective solder only: **270 °C for 10 s measured 1.5 mm from the
  case**. There is no reflow profile, and the case max is 120 °C. Treat the module as a
  hand-fit part in the BOM, not an assembler-placed part.

---

## 7. Control principle — Figure 2, v2.5, page 9

This figure is raster artwork with no extractable text. It was rendered at 8–16× and read
visually, and the **identical figure appears in v2.1 page 4**, so the two document
revisions agree. [verified-artifact — both renders inspected this session]

### 7.1 What the figure actually shows

A dashed box labelled **APS** is the module boundary. Four pin terminals are drawn on it:
`VMON` (top left), `+VIN` (top right), `VSET` (mid left), `/ON` (bottom left).
Outside the box, a single-pole changeover switch selects between the two documented
control methods: **"Version 2) VSET"** — a wire from an external voltage source — and
**"Version 1) RSET"** — a resistor labelled `RSET` from the VSET pin to GND. Exactly one
of the two is connected at a time.

Inside the box, in full:

```
       ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐
       ┊                                                          APS   ┊
VMON ──○────────[ 20k ]───────·                                         ┊
       ┊                                 ·                              ┊
       ┊                                 │                              ┊
       ┊                        ┌────────┴────────┐                     ┊
       ┊                        │                 │                     ┊
       ┊                     ┌──┴──┐           ┌──┴──┐                  ┊
       ┊                     │ 10k │           │ REF │                  ┊
       ┊                     └──┬──┘           └──┬──┘                  ┊
       ┊                        │                ─┴─                    ┊
       ┊                        │                GND                    ┊
VSET ──○────────────────────────┴────[ 100k ]─────┬─────────┬─────·     ┊
       ┊                                          │         │           ┊
       ┊                                          o       ┌─┴─┐         ┊
/ON  ──○───────────────────────────────────────▶   ╱      │1µ │         ┊
       ┊                                          o       └─┬─┘         ┊
       ┊                                          │         │           ┊
       ┊                                         ─┴─       ─┴─          ┊
       ┊                                         GND       GND          ┊
       └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘

+VIN ──○   (drawn as a bare terminal; the converter, the multiplier, the HV
           output and the GND pins do not appear in this figure at all)

  ┊    module boundary (dashed in the source)
  ·    wire continues into circuitry the figure does not draw
  o╱   switch, drawn OPEN, actuated by /ON (the ▶ points at the actuator,
       not at a circuit node) — per Table 1 it CLOSES on /ON HIGH
  REF  source symbol: a circle with battery plates inside, negative to GND
```

Component values printed in the figure: **20k**, **10k**, **100k**, **1µ**. No tolerances.

Node by node:

1. **VMON pin ← 20 kΩ in series ← internal monitor node.** The 20 kΩ resistor sits
   *between* the internal node and the pin. Whatever produces the monitor signal is not
   drawn; the wire past the resistor is a stub into undrawn circuitry.
2. **REF** is a source symbol (circle with battery plates), negative terminal to GND. Its
   positive node feeds the top of the **10 kΩ**, and also a stub upward into undrawn
   circuitry — i.e. the same reference is used internally. Table 1 gives it as
   2.5 V ± 1 % (0.5 W family) or 5 V ± 1 % (1 W family).
3. **The 10 kΩ is a pull-up from REF to the VSET pin node.** This is the resistor named
   in the `Rset` formula, and it is *directly on the pin*, upstream of everything else.
4. From the VSET pin node, a **100 kΩ in series** feeds an internal node.
5. That internal node carries **1 µF to GND** and a **switch to GND actuated by /ON**
   (drawn as an arrow from the /ON terminal into the switch), and continues right into the
   undrawn control loop.
6. **+VIN** is drawn as a bare terminal. The converter, the multiplier, the HV output and
   the GND pins are **not** in this figure at all.

### 7.2 What follows arithmetically from the figure

**(a) The Rset formula is confirmed, and its origin is now visible.**
With `Rset` from VSET to GND and the internal 10 kΩ to Vref, the pin sits at
`Vset = Vref · Rset/(10k + Rset)`. With the documented transfer `Vout = Vnom · Vset/Vref`:

```
  Vout = Vnom · Rset/(10k + Rset)        =>        Rset = Vout · 10k / (Vnom - Vout)
```

which is exactly Table 1's "Control Vset — version 1". The figure and the table agree;
the 10 kΩ in the formula is a real, physical, always-present pull-up.

**(b) An open VSET pin commands full scale.** With nothing on the pin, no current flows
in the 10 kΩ, so the pin sits at Vref → `Vset = Vref` → `Vout = Vnom`. §8.1.

**(c) The set-point node has a ~0.1 s time constant.**
`R·C = 100 kΩ × 1 µF = 0.1 s` when VSET is driven from a stiff source. Driven from an open
pin it is `(100k + 10k) × 1 µF = 0.11 s`.

```
  10-90 % of a VSET step      ~ 2.2 tau ~ 0.22 s
  settle to 1 % of final      ~ 4.6 tau ~ 0.46 s
  settle to 0.1 % of final    ~ 6.9 tau ~ 0.69 s
```

**This is the only quantitative handle anywhere in the documentation on how fast the
module responds to a set-point change**, and it is inferred from a schematic drawn
"in principle", not specified. It bounds the *command* path only; the HV loop and
multiplier add their own, unspecified, delay, and the *falling* direction additionally
depends on the load and on the unspecified internal bleed (§10.1, §10.4).

**(d) `/ON` HIGH commands zero — it does not disconnect anything.** The switch grounds the
set node *after* the 100 kΩ. So "HV OFF" is "set point forced to zero", executed inside
the regulation loop. Nothing in this figure opens the HV output path, and nothing in it
discharges the output. Consequences in §8.3 and §8.6.

**(e) Turn-off and turn-on are asymmetric.** Grounding the 1 µF through the switch is
fast (limited by the switch, not by the 100 kΩ). Releasing it recharges through the
100 kΩ → ~0.1 s. **Disable is fast; enable takes roughly half a second to settle.** That
is the timing budget for any break-before-make polarity changeover.

**(f) VMON is a resistive tap of at least 20 kΩ source impedance.** The figure shows
series resistance and nothing else between the internal node and the pin. §8.7.

---

## 8. Design consequences

Each item: the datasheet fact, what it forces on our board, and the countermeasure.

### 8.1 The internal 10 kΩ pull-up means an OPEN VSET COMMANDS FULL SCALE

*Fact.* Table 1 "Control Vset — version 1" and Figure 2: a 10 kΩ resistor from the
internal Vref to the VSET pin, permanently. `Vset(open) = Vref` → `Vout = Vnom`.

*Why it bites.* Every ordinary failure of the set-point path — a broken track, an
unpopulated resistor, a DAC that powers up tri-stated, a connector not mated, a driver
whose supply comes up late — leaves VSET open and therefore commands **full rated output**.
The safe-looking failure (nothing connected) is the dangerous one.

*Countermeasure.*
- **A hard pull-down on VSET, at the module pin, sized against the 10 kΩ.** A 1 kΩ to GND
  holds an undriven pin at `Vref · 1/11 ≈ 9 %` of full scale; 470 Ω holds it at ≈4.5 %.
  Choose the value at Phase 1 against the driver's output current, and put it physically
  at the pin, not at the DAC.
- The set-point driver must satisfy **Ri ≪ 10 kΩ** (Table 1's own wording) — an op-amp
  buffer, not a bare DAC output through a filter resistor. Any series R in that path also
  divides against the 10 kΩ and shifts the whole scale.
- **Treat the pull-down as safety hardware**: it goes in the netclass/DNP-forbidden list
  and appears in the pre-fab checklist, not as a generic passive.

### 8.2 The output is NOT internally limited above Vref

*Fact.* Table 1, in bold: **"Attention! Output voltage is internally not limited!"** —
`Vset > Vref → Vout > Vnom is possible`, with "Do not use Vset > 2.5 V / > 5 V".

*Why it bites.* The module will happily produce more than its rated voltage. A firmware
bug, a DAC reference collapse, a stuck DAC code, or an ESP32 GPIO glitching high can drive
VSET above Vref. Nothing in the module stops it, and the insulation margin we design for
is sized on Vnom.

*Countermeasure.*
- **A hardware clamp on VSET at or just below Vref.** This is a clamp requirement, not a
  firmware nicety. Candidates for Phase 1: a precision shunt reference plus a Schottky
  from VSET to it, or a rail-to-rail buffer powered from a rail that is itself ≤ Vref.
  A plain Zener is too loose at these voltages (Vref is 2.5 V ± 1 %).
- **The clamp rail must not be the same node the DAC uses as its reference** — a shared
  reference failure would raise the clamp and the command together.
- Firmware limits are additive, never a substitute. The clamp is the thing that has to be
  true when firmware is wrong.
- Note the clamp interacts with §8.1: the clamp must sink the 10 kΩ pull-up's current
  (`Vref/10k` = 250 µA / 500 µA) without lifting.

### 8.3 `/ON` is ACTIVE LOW — floating or undriven `/ON` turns HV ON

*Fact.* Table 4 and Table 1: `/ON = 0 (LOW **or open**) → HV ON`;
`5.5 V ≥ V/ON > 2.5 V (HIGH) → Vout = 0`.

*Why it bites.* The passive state of the module is **enabled**. ESP32 GPIOs are inputs
during reset and for the whole bootloader window; a pulled-out ribbon cable, a
not-yet-programmed MCU, or a brown-out all present "open" to `/ON`. On top of that,
`/ON` HIGH only *commands zero* (§7.2d) — it is not an output disconnect.

*Countermeasure.*
- **Default-OFF hardware: pull `/ON` HIGH with a resistor to a rail that is present
  whenever the module is powered, and have the MCU pull it LOW only to enable.** Then
  every open circuit, every reset, every unprogrammed board is OFF. The rail must be
  ≤ 5.5 V — see the next point.
- **`/ON` absolute maximum is 5.5 V for BOTH families.** The `/ON` row in Table 1 spans
  the 0.5 W and 1 W columns [verified-artifact — confirmed by rasterising the table; the
  merged cell is invisible in the extracted text]. So on a **12 V module, `/ON` must not
  be driven from the 12 V rail**; the pull-up rail and any driver must be ≤ 5.5 V. This is
  an easy and expensive mistake.
- ESP32 drives 3.3 V, which is above the 2.5 V HIGH threshold but with only 0.8 V of
  margin. Prefer an open-drain driver against a 5 V pull-up over a direct 3.3 V push-pull,
  and re-check the threshold on the bench.
- **The brief's "both modules must never be enabled simultaneously, in hardware"
  invariant lands here.** Because enable is a LOW, an interlock that physically cannot
  produce two LOWs is the right shape: a **single changeover contact that routes one
  ground to exactly one module while the other is pulled up**, so "both enabled" is not a
  state the wiring can represent. A logic gate is not equivalent — it can fail with both
  outputs low.
- **And `/ON` alone is not isolation.** Since HV OFF is a commanded zero, a true
  break in the HV path (relay or series switch) is still required for the combiner.
  Budget ~0.5 s of set-point settling on the enable side (§7.2e) into the changeover
  sequence.

### 8.4 Polarity is FACTORY FIXED

*Fact.* Table 1: "Factory fixed, positive or negative"; the polarity letter is baked into
the item code (§4).

*Why it bites.* One module = one sign, permanently. Bipolar output *requires* two modules
and a combiner — which is exactly the brief — and it means a wrongly-ordered module cannot
be re-configured, only replaced.

*Countermeasure.*
- **The two footprints on the board are not interchangeable.** Silkscreen must carry the
  full item code including the polarity letter (e.g. `AP004125P05` / `AP004125N05`), and
  the BOM must list two distinct line items. A generic "iseg APS" designator invites
  swapping them at build.
- Consider making the two module positions **mechanically or electrically keyed** so a
  swapped pair is detectable — at minimum, the independent output monitor (§8.7, and the
  brief's third invariant) must be able to report the *sign* of the output, so a swap is
  caught at first energization rather than by a scope.
- **VMON cannot distinguish the two.** VMON is a 0…Vref positive-going signal on both
  polarities; the independent monitor is the only thing that knows the sign.

### 8.5 Ripple and stability are guaranteed only above 2 % of Vnom

*Fact.* Table 1 note 1: stability, ripple and noise are specified for
`2 % · Vnom < Vout ≤ Vnom`. Below that — including at and near zero — **nothing is
specified**.

*Why it bites.* On a 1 kV module the specified floor is 20 V. Everything below 20 V is
undocumented territory, and that is precisely the region a bipolar controller crosses on
every polarity changeover, and the region a "through-zero" mode would have to live in.
The 1 %·Vnom monitor accuracy has the same problem: ±10 V of monitor uncertainty on a
1 kV module says nothing useful about whether the output is actually near zero.

*Countermeasure.*
- **Do not claim any output specification below 2 % of Vnom.** Write the usable range
  into `DECISIONS.md` as `[0.02·Vnom, Vnom]` per module and design the product spec
  around it.
- **Pick the module class so the required minimum output is above 2 % of Vnom** — this is
  a module-selection input, and it argues for the *lowest* Vnom that meets the maximum
  requirement rather than headroom for its own sake.
- **The independent output monitor must have absolute accuracy far better than 1 %·Vnom
  near zero**, because that is the measurement the changeover interlock and the
  discharge-verified condition depend on. A monitor scaled only for full range will not
  do; consider a dual-range or an amplified low-range path.
- Treat "output is at zero" as something to be **measured**, never inferred from a
  commanded set point or from VMON.

### 8.6 A defined discharge path is our job, not the module's

*Fact.* Nothing in Table 1, Table 4 or Figure 2 describes any output discharge, bleeder,
or self-discharge behaviour. Figure 2 shows the `/ON` switch acting only on the internal
set-point node. See §10.4.

*Why it bites.* The brief's second invariant is "a defined discharge/bleed path on
changeover and on disable". The module provides no documented one. Whatever the multiplier
stack's internal divider does is unspecified and must not be relied on.

*Countermeasure.*
- **An explicit bleeder on the combined output node**, sized at Phase 1 against the target
  discharge time and the unknown output capacitance (§10.3) — with the RC re-measured on
  the bench and the resistor's *voltage* rating, not just power rating, checked (HV
  resistors have a maximum working voltage; a single 1 GΩ part is usually not rated for
  1 kV and a series string is needed).
- **An active discharge (relay-shorted or FET-switched HV resistor) for changeover**, so
  the ~0.5 s enable settling (§7.2e) is not spent with residual charge of the wrong sign
  on the output.
- **The bleeder is always-connected safety hardware**, not switched by firmware; a
  switched-only discharge fails exactly when the controller is dead.
- Interlock ordering to encode: disable both → verify discharged **by the independent
  monitor** → change polarity selection → enable one.

### 8.7 The case is tied to GND, and VMON is a ≥ 20 kΩ resistive tap

*Fact.* Table 4 note: "Case is connected to GND." Figure 2: a 20 kΩ resistor in series
into the VMON pin, with nothing else drawn between it and the internal node.

*Why the case matters.* The moulded steel can is on the same net as pins 3 and 7. Two
consequences: (i) the module cannot be operated with its GND floated off the board ground
without floating the case too, which makes the can live — so **GND-referenced operation is
the only documented configuration** (§10.6); (ii) the can is a conductive object of
39.6 × 15.7 mm sitting on the board at GND, and it must be treated as a grounded surface
for creepage and clearance from the HV pin, the HV track and the combiner — not as an
insulator, and not as an unconnected mechanical body.

*Why VMON matters.* A 20 kΩ series resistance means **VMON is not a low-impedance output**.
Any load forms a divider with it:

```
  load 1 MΩ    -> reading low by 20k/1020k   = 1.96 %
  load 100 kΩ  -> reading low by 20k/120k    = 16.7 %
  load 10 kΩ   -> reading low by 20k/30k     = 66.7 %
```

Against a 1 %·Vnom accuracy spec, **even a 1 MΩ input divider destroys the specification**.
Whether there is a buffer *behind* the 20 kΩ is not shown (§10.7).

*Countermeasure.*
- **Buffer VMON with a unity-gain, low-bias-current (CMOS/FET-input) op-amp placed at the
  module pin**, before any divider, filter or ADC. Do not connect VMON to an ESP32 ADC
  input directly, and do not put an attenuator on it first.
- Input bias current matters: 20 kΩ × 1 nA = 20 µV, fine; 20 kΩ × 1 µA = 20 mV, not fine
  against a 2.5 V full scale.
- Any deliberate filter on VMON must be placed **after** the buffer, or its R must be
  included in the divider arithmetic above.
- Route the can's ground and the HV pin with the same care as any HV clearance: the can is
  grounded copper-adjacent metal 3.0 mm from the HV pin along the body (§5), and our
  board's clearance rules must not assume otherwise.
- **VMON is a module self-report and does not satisfy the brief's third invariant.** The
  independent output monitor must tap the combined output node through its own divider.

---

## 9. Differences between v2.1 (2019-06-03) and v2.5 (2024-08-20)

Recorded so nobody "corrects" this file from the older PDF, which is also in the repo.

| item | v2.1 | v2.5 | note |
|:--|:--|:--|:--|
| Voltage monitor accuracy | absent | **1 % · Vnom** | new spec |
| Current monitor accuracy | absent | **1 % · Inom** | new spec, and the discrepancy of §10.8 |
| Maximum soldering temperature | absent | **270 °C, 10 s, 1.5 mm from case** | new |
| Maximum case temperature | absent | **120 °C** | new |
| Humidity | absent | **max 70 %, not condensing** | new |
| Vin in the configurations table | folded into the Type column (`APx 02 255 5`) | its own column | cosmetic |
| Polarity letter case | lower case `p` / `n` | **upper case `P` / `N`** | use upper |
| Item-code revision / customization digits | absent entirely | `r`, `k`, omitted if unused | v2.4 added these |
| Rset formula | `Rset = Vout · 10kΩ / (\|Vnom\| − Vout)` | `Rset = Vout · 10kΩ / (Vnom − Vout)` | absolute-value bars dropped; the intent is unchanged |
| Figure 1 (dimensional drawing) | identical geometry and labels | identical | cross-checked by render |
| Figure 2 (control principle) | identical, same 20k/10k/100k/1µ values | identical | cross-checked by render |
| Warranty | 12 months + purchasable 5-year extension | 12 months, extension by enquiry | not engineering-relevant |

**Nothing mechanical or electrical that this project depends on changed between 2019 and
2024.** Two independently-typeset documents five years apart carry the same pin map, the
same dimensions and the same internal control schematic — which is the strongest evidence
available short of measuring a module.

---

## 10. What the datasheet does NOT say

Everything below is **absent** from both v2.1 and v2.5, in text and in both figures. Each
is a question for iseg or a bench measurement. They are ordered by how much they can
change the design.

### 10.1 Slew rate and settling time on a VSET step — *and therefore whether "through-zero" is even meaningful*

**Nothing** specifies how fast Vout follows Vset: no slew rate, no rise time, no settling
time, no small-signal bandwidth, no step response, in either revision. Figure 2 gives the
*command-side* RC as 100 kΩ × 1 µF ≈ 0.1 s (§7.2c), but the HV loop and the multiplier
stack contribute an unknown amount on top, and the **falling** direction is worse: a
supply that can only source charge falls only as fast as the load plus whatever internal
bleed exists (§10.4). A resonant multiplier's descent from Vnom into no load can be
seconds.

*Why it decides the design.* The brief leaves open "smooth through-zero versus
set-and-hold with polarity changeover". If the settling time is ~0.5 s and asymmetric,
a smooth through-zero sweep of the kind a sweep experiment wants is not achievable with
these modules and the answer collapses to set-and-hold. **Measure this before choosing
the combiner topology.**
Bench: step VSET 10 %→90 %→10 % of Vref with a defined load and with no load; capture Vout
through an HV probe; repeat with the `/ON` transition instead of a VSET step.

### 10.2 Reverse-voltage tolerance on the HV pin

**Nothing** specifies what the HV pin can survive when the module is off, or when the
opposite polarity is applied to it from outside. Since `/ON` HIGH is a commanded zero and
not a disconnect (§7.2d), an off module's HV pin **remains connected to its multiplier
output**, and in any shared-output combiner the *other* module's full voltage appears
across it with reversed polarity.

*Why it decides the design.* This single unknown selects the combiner topology. If reverse
voltage is not tolerated, an opposite-polarity diode-OR is illegal and an **HV relay
changeover with a true break** is mandatory. If it is tolerated, cheaper topologies open
up. The brief lists diode-OR as a candidate; it cannot be evaluated without this number.
Ask iseg: *"With the module powered and `/ON` HIGH, what reverse voltage may be applied to
the HV pin with respect to GND, continuously and transiently?"*

### 10.3 Output capacitance

**Nothing** gives the multiplier's output capacitance. It sets the stored energy
(`½CV²` — the touch-safety and spark-energy question), the discharge time constant against
any bleeder, and the settling behaviour of §10.1. Bench: measure the RC against a known
HV resistor.

### 10.4 Discharge behaviour when disabled — does it self-bleed?

**Nothing** says what Vout does after `/ON` goes HIGH or Vset goes to zero with **no load
attached**. It may bleed through an internal divider in seconds, or hold charge for
minutes. The brief's discharge invariant (§8.6) cannot be sized without it, and the "safe
discharge on disable" success criterion cannot be claimed without it.
Bench: charge to Vnom, disable, record Vout vs time with a ≥ 1 GΩ probe and with the probe
removed (the probe itself is a bleeder — this measurement is easy to get wrong).

### 10.5 Short-circuit and overload behaviour

Table 1 says only **"Overload and short circuit protected"**. Not stated: the current-limit
value, whether it is constant-current / foldback / hiccup, whether it latches, the recovery
time and whether recovery is automatic, how many events it tolerates, and whether repeated
HV arcing into a shorted output is a wear mechanism. `Iout ≈ 1.5 · Inom` (Table 2 note 1)
is a limit on *available* current, not a description of the protection.
Relevant because an HV controller's realistic failure mode is a flashover at the load.

### 10.6 Isolation, hipot, and behaviour with GND above earth

**Nothing** states an isolation voltage between input and output, nor any rating for
operating the module's GND at a potential above earth. Since the case is bonded to GND
(§8.7), floating GND floats the can. This forecloses stacking two modules in series to
double the output — a topology that would otherwise be attractive — until iseg confirms a
rating.
Ask iseg: *"What is the maximum potential difference permitted between the module's GND
pins/case and earth?"*

### 10.7 Whether VMON is buffered, and what its transfer function is

Figure 2 shows **only** a 20 kΩ series resistor into the pin. What is behind it — a
buffered amplifier, or a bare tap off the HV feedback divider — is not drawn. The pin's
source and sink capability, its short-circuit tolerance, and its behaviour if pulled
outside 0…Vref are all unstated.

Worse, **the VMON transfer function is never written down anywhere.** Table 4 gives a
range (0…2.5 V / 0…5 V) and Table 1 gives an accuracy (1 %·Vnom), but no equation. That
`Vmon = Vref · |Vout| / Vnom` is *implied* by the range and by symmetry with Vset — it is
not stated, and neither is the sign convention on a negative-polarity module (this file
assumes VMON is positive-going for both polarities; **that assumption is unverified**).
Zero-offset at Vout = 0 is also unspecified.
Bench: sweep Vout, measure VMON against an HV probe on both a P and an N module, with the
buffer of §8.7 in place.

### 10.8 The current-monitor accuracy spec that has no pin

v2.5 Table 1 adds **"Current monitor accuracy: 1 % · Inom"**, spanning both families.
**The 7-pin part in Table 4 has no current-monitor pin.** Pins 1–7 are +VIN, VSET, GND,
/ON, VMON, HV, GND — there is nowhere for a current monitor to appear.

*Do not silently resolve this.* Three readings are possible, and they are not equivalent:
(i) boilerplate copied from another iseg family into the APS table by mistake;
(ii) it describes a customized variant (Table 3 has a customization digit);
(iii) some current information is encoded on an existing pin in a way Table 4 does not
document. Reading (iii) would change what we can measure.
Ask iseg directly. **Until answered, the design must assume there is no current readback
from the module at all**, and any output-current measurement must be our own — which
interacts with the brief's independent-monitoring invariant.

### 10.9 No recommended land pattern

No hole diameter, no pad diameter, no keepout, no minimum clearance around the HV pin, no
recommended creepage on the board, no soldering profile beyond the 270 °C / 10 s / 1.5 mm
limit, and no statement about washing or conformal coating. §6.4 records what we chose
instead and on what basis. The absence of a vendor keepout means **our HV clearance rules
are entirely our own responsibility** and must come from the working HV standard, encoded
as DRC netclass rules per the bootstrap.

### 10.10 Load capacitance stability limit

**Nothing** states the maximum capacitive load, or whether the control loop is stable into
one. A detector, a cable, or our own filter capacitor is a capacitive load. A resonant
converter with an unstated loop can ring or oscillate into the wrong C.

### 10.11 Power-up and power-down behaviour

Not stated: what Vout does while Vin ramps (remember `/ON` open = ON, so a module can be
enabled before the controller exists); the start-up time from Vin valid to Vout valid;
whether there is any inrush limit on +VIN beyond the recommended 22 µF; what happens on a
Vin brown-out mid-output; and whether Vin sequencing relative to `/ON` matters.
Directly relevant to the first-energization procedure.

### 10.12 `/ON` input electrical characteristics

Not stated: input impedance, the value of whatever holds it low when open, its input
current when driven HIGH, its threshold hysteresis, and the minimum pulse width it
recognises. Only the level thresholds (>2.5 V HIGH, ≤5.5 V max) are given. The pull-up
resistor of §8.3 cannot be sized rigorously without the input impedance.

### 10.13 VSET input absolute maximum, and negative Vset

Table 1 says "do not use Vset > Vref" but gives **no absolute maximum** — the voltage at
which the pin is damaged rather than merely out of spec. Nor is anything said about
negative Vset, which our clamp design (§8.2) should defensively prevent anyway.

### 10.14 Tolerances on the internal components in Figure 2

The figure gives 20k, 10k, 100k, 1µ as bare nominals. **The 10 kΩ tolerance directly sets
the accuracy of Rset-mode control** (§7.2a) and the effectiveness of the VSET pull-down
(§8.1); the 100 kΩ × 1 µF tolerance sets the spread on the ~0.1 s time constant. The ±1 %
"adjustment accuracy" in Table 1 presumably absorbs the 10 kΩ in Vset mode, but says
nothing about Rset mode.

### 10.15 Switching frequency and ripple spectrum

"Patented resonance converter technology", ripple specified at f > 10 Hz and f > 2 kHz —
but **the switching frequency itself is never given**. Needed to design the VMON and
independent-monitor anti-alias filtering (a switching component aliasing into the ESP32
ADC will read as a slow drift), and to plan EMI.

### 10.16 Thermal and lifetime data

Case max 120 °C and ambient 0–40 °C are given, but there is **no thermal resistance, no
derating curve, and no statement of Pnom versus ambient**. Also absent: MTBF, expected
life, and whether on/off cycling is a wear mechanism — the last one matters because a
polarity-changeover controller cycles `/ON` constantly by design.

---

## 11. Assumptions this file makes (each is a candidate bench measurement)

1. **v2.5 supersedes v2.1** wherever they differ. §9 lists every difference found.
2. **The 3.0 mm overhangs are exactly 3.0 mm** — the drawing prints "3" with no decimal.
3. **The two undimensioned overhangs are 3.0 mm and 2.54 mm** by the subtraction in §5.2.
   The pixel measurement of §5.4 brackets both correctly but cannot refine them.
4. **`Vmon = Vref · |Vout| / Vnom`, positive-going on both polarities.** Implied by the
   range and by symmetry with Vset; **never stated** (§10.7).
5. **`/ON`'s 5.5 V maximum applies to both the 5 V and 12 V families**, because that
   table row spans both columns [verified-artifact — table rasterised and read].
6. **The ~0.1 s set-node RC bounds the command path only**, and is an order of magnitude,
   not a specification (§7.2c, §10.1).
7. **No current readback exists on the 7-pin part** (§10.8), pending iseg's answer.
8. **The module is operated with GND at board ground**, not floated or stacked (§10.6).

---

## 12. Questions to put to iseg

Ranked. The first three change the topology.

1. With the module powered and `/ON` HIGH, **what reverse voltage may be applied to the HV
   pin** with respect to GND — continuously and transiently? (§10.2)
2. **What is the step response of Vout to a VSET step**, rising and falling, into no load
   and into a resistive load? Equivalently: settling time to 1 % of final. (§10.1)
3. **What is the maximum potential difference permitted between the module GND/case and
   earth?** Can two modules be stacked in series? (§10.6)
4. **Table 1 v2.5 lists a current monitor accuracy of 1 %·Inom, but Table 4 shows no
   current-monitor pin. Which is correct?** (§10.8)
5. **What is the output capacitance**, and what does Vout do after disable with no load
   attached — is there an internal bleeder, and what is its value? (§10.3, §10.4)
6. **Is VMON buffered?** What is its source impedance, its output-current capability, and
   its exact transfer function including the sign convention on N-polarity modules?
   (§10.7)
7. **Describe the short-circuit protection**: limit value, characteristic, latching or
   auto-recovery, recovery time. (§10.5)
8. **What is the maximum capacitive load** the control loop is stable into? (§10.10)
9. **What is the converter switching frequency?** (§10.15)
10. **Is there a recommended PCB land pattern and HV keepout** for this module? (§10.9)

---

*Ground truth in this file: iseg APS series technical documentation v2.5, 2024-08-20
(primary) and v2.1, 2019-06-03 (cross-check). The pin map in §1 is transcribed from
v2.5 Table 4, page 9, dated 2024-08-20. Every geometric number in §5 and §6 is read from
v2.5 Figure 1, page 8, and independently bracketed by pixel measurement of the same
artwork. Every element of §7 is read from v2.5 Figure 2, page 9, and confirmed against the
identical figure in v2.1 page 4. Nothing in this file has been measured on a physical
module.*
