#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_lib_footprints.py -- emit hardware/hvctl/lib/iseg.pretty/iseg_APS_THT.kicad_mod

WHAT THIS IS
    A .kicad_mod file is s-expression TEXT. Emitting it needs no KiCad API, so this generator
    is deliberately STDLIB-ONLY and runs on any Python 3.8+. It must NOT grow a third-party
    dependency and it must NOT import pcbnew. (The acceptance check *invokes* the KiCad python
    as a SUBPROCESS -- see check_c_pcbnew_readback -- which keeps this file importable
    everywhere while still letting KiCad itself be the instrument of record.)

    The emitted file is a BUILD ARTIFACT. Never hand-edit it. Fix this generator and re-run.

SCHEMA PROVENANCE  -- nothing about the file format is invented
    (version 20260206) / (generator_version "10.0") / tab indentation / the exact spelling of
    (stroke (width..) (type..)), (fp_rect ... (fill no)), (pad ... (remove_unused_layers no)),
    (clearance N), layer name "Cmts.User", (embedded_fonts no) and (attr through_hole
    exclude_from_pos_files) were all read off files KiCad 10.0.3 itself wrote:
      * C:/Program Files/KiCad/10.0/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty/
            PinHeader_1x05_P2.54mm_Vertical.kicad_mod        [stock, KiCad-authored]
      * a throw-away footprint built in-memory with pcbnew and saved via
            PCB_IO_MGR.FindPlugin(KICAD_SEXP).FootprintSave()  [this session]
        -- that is where the per-pad `(clearance ...)` token and `Cmts.User` were confirmed.
    KiCad 10 writes `(footprint ...)`, NOT the legacy `(module ...)`. The reference board's
    ISEG_HV_MODULE.kicad_mod is legacy `(module ...)` (KiCad 5) and must not be copied.

================================================================================================
GEOMETRY DERIVATION -- every number below traces to the vendor drawing
================================================================================================
SOURCE
    iseg APS series technical documentation v2.5, 2024-08-20,
    Figure 1 "dimensional drawing APS", manual page 8 (PDF page index 7).
    Pin names: same document, Table 4, manual page 9 (PDF page index 8).
    Local copy: references/iseg_manual_APS_en.pdf
    Figure 1 is vector/raster ARTWORK with no extractable dimension text; the labels were read
    visually and independently re-measured in pixels (see docs/PART_iseg_APS.md section 5.4 and
    tools/verify_part_iseg_aps_drawing.py, which both pass this session).

PRIMITIVES read off Figure 1
    body L x W x H            39.60 x 15.70 x 11.00 mm   (spec table rounds these to 40/16/11 --
                                                          USE THE DRAWING, not the spec table)
    pin cross-section         0.64 mm SQUARE
    pin length below case     2.20 mm +/- 0.40
    pin pitch, pins 1..5      2.54 mm      (span pin1->pin5 = 10.16 mm = 4 x 2.54)
    column separation         34.80 mm     (pins 1..5 column  <->  pins 6/7 column)
    overhang, pins 1..5 end    1.80 mm     (labelled "1,8")
    overhang, pin 5 side       3.00 mm     (labelled "3")

TWO OVERHANGS ARE NOT DIMENSIONED -- they follow by subtraction
    along L:  39.60 = 1.80 + 34.80 + X   ->  X = 3.00 mm   (overhang at the pins 6/7 end)
    along W:  15.70 = Y + 10.16 + 3.00   ->  Y = 2.54 mm   (overhang above pin 1)

    So the four overhangs are  1.80 / 3.00  along L  and  2.54 / 3.00  along W.
    Mnemonic: PIN 1 SITS AT THE CORNER WHERE THE CASE OVERHANGS LEAST IN BOTH AXES
    (1.80 and 2.54). Pin 6 sits at the corner where it overhangs most in both (3.00 and 3.00).

THE BODY IS NOT CENTRED ON THE PIN RECTANGLE  -- and this is the defect we are fixing
    offset along L = (3.00 - 1.80) / 2 = +0.60 mm
    offset along W = (3.00 - 2.54) / 2 = +0.23 mm

    SIGN, stated explicitly, in the footprint frame used below
    (origin = pin-array centroid; +x runs from the pins 1..5 column toward the pins 6/7 column;
     +y runs from pin 1 toward pin 5 -- i.e. KiCad top view, y down on screen, which reproduces
     Figure 1's TOP view: pin1 top-left, pin5 bottom-left, pin7 top-right, pin6 bottom-right):

        body centre = (+0.60, +0.23)   NOT (0, 0)

    +x because the overhang is BIGGER (3.00) at the pins 6/7 end than at the pins 1..5 end
    (1.80), so the can sticks out further past pin 6/7 -- the body centre is pushed AWAY from
    the pins 1..5 column.
    +y because the overhang is BIGGER (3.00) past pin 5 than above pin 1 (2.54), so the body
    centre is pushed AWAY from pin 1's side, toward pin 5.
    An independent pixel measurement of the vendor artwork gives +0.623 mm and +0.241 mm
    (tools/verify_part_iseg_aps_drawing.py, run this session) -- the asymmetry is visible in
    the pixels, not merely in the arithmetic.

    The reference footprint we are replacing,
      references/Phys439-alpha-lab/circuit/alpha-shield-pcb/alpha-shield.pretty/
          ISEG_HV_MODULE.kicad_mod
    draws the body SYMMETRICALLY at +/-19.812 x +/-7.874 about the pin centroid. That is wrong
    by 0.612 mm at the pins 1..5 end, 0.588 mm at the pins 6/7 end, 0.254 mm at pin 1's side and
    0.206 mm at pin 5's side. (The same file's 3D model offset, (-19.2278, -7.62, 0), is the
    CORRECT asymmetric corner to 0.028 mm -- the STEP was placed from the datasheet, the 2D
    outline was not.) We reproduce the asymmetric outline.

PAD COORDINATES (frame as above; all mm)
    X15 = -COLUMN_SEP/2 = -17.40      X67 = +COLUMN_SEP/2 = +17.40
    Y1  = -(4*2.54)/2   =  -5.08      Y5  = +5.08
      pad 1 +VIN (-17.40, -5.08)   pad 2 VSET (-17.40, -2.54)   pad 3 GND (-17.40,  0.00)
      pad 4 /ON  (-17.40, +2.54)   pad 5 VMON (-17.40, +5.08)
      pad 6 HV   (+17.40, +5.08)   pad 7 GND  (+17.40, -5.08)
    (pin 7 aligns with pin 1, pin 6 aligns with pin 5 -- Figure 1 bottom view.)

BODY OUTLINE (asymmetric, as derived)
    x0 = X15 - 1.80 = -19.20      x1 = X67 + 3.00 = +20.40      (x1-x0 = 39.60 = L  OK)
    y0 = Y1  - 2.54 =  -7.62      y1 = Y5  + 3.00 =  +8.08      (y1-y0 = 15.70 = W  OK)
    centre = ((x0+x1)/2, (y0+y1)/2) = (+0.60, +0.23)            matches the offset above  OK

================================================================================================
LAND PATTERN -- ENGINEERING DECISIONS. The vendor specifies NO land pattern (see
docs/PART_iseg_APS.md 6.4 / 10.9): no hole size, no pad size, no keepout, no HV clearance.
================================================================================================
DRILL  = 1.30 mm  (finished hole)
    The pin is 0.64 mm SQUARE, so the controlling dimension is the DIAGONAL:
        0.64 * sqrt(2) = 0.90510 mm.  Any hole below that will not accept the pin at all.
    Diametral allowance chosen = 1.30 - 0.90510 = 0.39490 mm  ->  0.197 mm radial float.
    That allowance has to absorb THREE things, and the usual IPC number only covers the first:
      (1) IPC-2222 level-B style lead-to-hole allowance, max lead dimension + ~0.25 mm  -> 0.25
      (2) fabricator finished-hole tolerance (drill wander + plating thickness), typ +/-0.05 mm
      (3) the module's PIN-POSITION tolerance -- which the datasheet DOES NOT STATE. Seven
          rigid pins in a steel can spanning 34.80 mm must all enter simultaneously; the only
          toleranced dimension anywhere in Figure 1 is the pin LENGTH (2.2 +/- 0.4).
    Evaluating the reference board's 1.143 mm (0.045 in) drill on the same basis:
        1.143 - 0.90510 = 0.238 mm diametral = 0.119 mm radial.
    That is essentially all of (1) with nothing left for (2) or (3) -- one 0.05 mm plating
    excursion and a 0.07 mm pin bow and the part will not seat. It is not adopted. 1.30 mm is a
    stocked drill, keeps ~0.15 mm of budget for the undocumented (3), and costs 0.08 mm of
    annular ring versus a 1.15 mm "textbook" hole. On a hand-fit part that trade is correct.
    (Re-open this number the day a physical module is measured with calipers.)

PAD    = 2.10 mm  ->  annular ring = (2.10 - 1.30)/2 = 0.40 mm
    The reference board used 1.778 mm pads on a 1.143 mm drill = 0.3175 mm ring. Is 0.32 mm
    adequate for THIS part? By IPC-2221 class-2 minimum annular ring (0.05 mm external, after
    all tolerances) -- yes, trivially. Mechanically -- no, it is thin for what this is:
    an 11 mm tall metal can weighing ~20 g, standing 39.6 mm long on 7 pins, HAND soldered
    (270 C for 10 s max, 1.5 mm from the case; case max 120 C -- there is no reflow profile,
    so this part is soldered, inspected, and quite possibly REWORKED with an iron). The
    failure mode is pad lift / annular-ring tear-out from repeated thermal cycling and lever
    loads on a tall part, and pad peel strength scales with bonded copper area.
    0.40 mm ring is a ~26 % increase in ring width over the reference at a cost of only
    0.44 mm of pad-to-pad copper gap in the 2.54 mm column (2.54 - 2.10), which is far above
    any fabricator's minimum copper spacing. So: adopt 0.40 mm, not 0.32 mm.
    Pad 1 is RECTANGULAR (pin-1 marker); pads 2..7 circular. Layers *.Cu *.Mask for all.

COURTYARD = body outline + 0.75 mm on every side
    -> x [-19.95, +21.15], y [-8.37, +8.83]
    NOT the reference's 0.254 mm hairline. Reasons, in order:
      * the body outline itself is only as good as a drawing nobody has checked with calipers;
      * pin-position tolerance is undocumented, so the can may not sit exactly where we drew it;
      * the steel can is CONNECTED TO GND (Table 4 note) -- it is a grounded conductive surface
        39.6 x 15.7 mm sitting on the board, not an insulating body, and neighbouring parts
        that carry HV must be kept off it;
      * it is a hand-fitted part: fingers, tweezers and an iron tip need room.
    The courtyard also fully encloses every pad (checked, see check_d_legibility).

HIGH VOLTAGE -- CREEPAGE, and the per-pad clearance override on pad 6
    Pad 6 is the HV output. Worst case in this family is Vnom = 1 kV (AP010504x05 / AP010105x12,
    Table 2) and the module's output is NOT internally limited (Table 1, in bold), so the design
    number is 1 kV, not "whatever we plan to run at".

    IPC-2221B Table 6-1, column B2 (external conductors, uncoated, sea level to 3050 m):
        301-500 V row                       2.50 mm
        ">500 V" row, adder                 x mm per volt above 500 V
        creepage(1000 V) = 2.50 + x * 500
    [recalled] -- THE STANDARD IS NOT ON DISK IN THIS REPO. Two adders are in wide circulation
    for that row, 0.0025 mm/V and 0.005 mm/V, giving 3.75 mm and 5.00 mm respectively. We take
    the LARGER, because being wrong in the other direction is a flashover:
        CREEPAGE_1KV_MM = 5.00
    B2 (uncoated) is the applicable row rather than B4 (permanent polymer coating, ~2.33 mm)
    because a PAD is a mask opening: there is no soldermask credit at the exact place where the
    HV copper is closest to its neighbour. This is the same mistake the reference board made
    (REFERENCE_BOARD_AUDIT section 5.1: 0.200 mm from exposed 200 V pads to I2C SDA, DRC-clean
    against the wrong rule). Re-derive this number from the actual standard before it becomes a
    board-level DRC gate; here it is a footprint-local floor and a self-check.

    What the PART's own geometry gives us, and it is fixed -- we cannot design it:
        pad 6 (HV) to pad 7 (GND) centre distance = 10.16 mm  (same end of the module!)
        copper gap = 10.16 - (2.10/2 + 2.10/2) = 8.06 mm
        8.06 mm >= 5.00 mm  ->  PASSES at 1 kV with 3.06 mm to spare.
        Inverting the IPC expression, 8.06 mm supports 500 + (8.06-2.50)/0.005 = 1612 V, i.e.
        the land pattern is not the limit anywhere in this module family.
        Note this is only true because we did NOT enlarge pad 6: every 0.1 mm of extra pad
        diameter costs 0.1 mm of creepage here. Sizing pad 6 up "for HV" would be backwards.

    (clearance 5) on pad 6 -- a per-pad LOCAL CLEARANCE OVERRIDE, KiCad's `(clearance ...)`
    token, confirmed by round-tripping a pad through pcbnew this session. Effect: zone fills,
    tracks and pads of every other net are pushed 5 mm off pad 6 automatically, in the copper
    engine, REGARDLESS of what netclass the HV net ends up in or whether someone forgets to
    create one. It is an anti-pad and a DRC rule in one, and it travels with the footprint.
    It is deliberately set to the creepage number and not more: it must stay <= 8.06 mm or the
    footprint would violate its own rule against pad 7 and DRC would be unsatisfiable
    (check_b_creepage asserts exactly that, in both directions).

    Also carried, because the copper engine cannot see them:
      * F.SilkS: a heavy bar and "HV" at the pin-6 end, placed OUTSIDE the body outline so it
        is still readable after the can is fitted (silk under a 39.6 x 15.7 mm steel box is
        invisible, which is why the reference footprint's marking-free silk was harmless and
        also useless).
      * F.Fab: "HV" beside pad 6, plus ${REFERENCE} at the true BODY CENTRE (0.60, 0.23).
      * Cmts.User: the datasheet citation and date, the body-offset value, the creepage
        derivation, and the soldering limits; plus a 5.00 mm radius keepout ring around pad 6
        drawn to scale, so the required void is visible in the layout editor.

    (attr through_hole exclude_from_pos_files): the module cannot be reflowed or machine
    placed -- 270 C/10 s at 1.5 mm from the case, case max 120 C. It stays in the BOM; it must
    not appear in a pick-and-place file.

    NO (model ...) IS ATTACHED. The reference project's ISEG_HV_MODULE.step is placed at the
    correct asymmetric corner, but KiCad's 3D offset sign convention was not verified this
    session and the STEP has not been copied into this repo. Attaching a model whose axis
    convention is unverified would put a plausible-looking, wrong body in the mechanical check
    -- exactly the class of error this footprint exists to remove. Add it deliberately, later,
    with its own check.

EXIT CODES
    0  ok
    1  verification failed  (numbers disagree with the independent recomputation, or the
                             creepage assertion fails, or KiCad's readback disagrees)
    2  structural failure   (cannot write, cannot parse our own output, no KiCad interpreter)
    3  legibility failure   (KiCad cannot load/plot it, or silk/courtyard geometry is unreadable)
"""

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(HERE, "lib")
PRETTY_DIR = os.path.join(LIB_DIR, "iseg.pretty")
FP_NAME = "iseg_APS_THT"
OUT_MOD = os.path.join(PRETTY_DIR, FP_NAME + ".kicad_mod")

# Nothing KiCad is on PATH (CLAUDE.md rule 2). Absolute paths, with a short search list so the
# tool keeps working if KiCad moves or on another host.
PY_KICAD_CANDIDATES = [
    r"C:/Program Files/KiCad/10.0/bin/python.exe",
    r"C:/Program Files/KiCad/9.0/bin/python.exe",
    "/usr/lib/kicad/bin/python3",
    "/usr/bin/python3",
]
KICAD_CLI_CANDIDATES = [
    r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe",
    r"C:/Program Files/KiCad/9.0/bin/kicad-cli.exe",
    "/usr/bin/kicad-cli",
    "/usr/local/bin/kicad-cli",
]

# Fixed namespace for deterministic ids. NEVER uuid4 anywhere in this project.
NS_ISEG = uuid.UUID("6f3b6b4a-1f2c-5c8e-9a4d-0d1e2f3a4b5c")


def stable_uuid(semantic_key):
    """Deterministic id from a semantic key. Same key -> same id, forever, on every host."""
    return str(uuid.uuid5(NS_ISEG, "footprint/" + FP_NAME + "/" + semantic_key))


# ---------------------------------------------------------------------------------------
# GROUND TRUTH -- Figure 1 primitives only. Everything else is derived, below and in check().
# ---------------------------------------------------------------------------------------
DATASHEET_CITATION = "iseg APS series technical documentation v2.5, 2024-08-20"
DATASHEET_URI = "${KIPRJMOD}/../../references/iseg_manual_APS_en.pdf"

PIN_PITCH_MM = 2.54       # Figure 1, "2,54"
COLUMN_SEP_MM = 34.80     # Figure 1, "34,8"
BODY_L_MM = 39.60         # Figure 1, top view
BODY_W_MM = 15.70         # Figure 1, top view
BODY_H_MM = 11.00         # Figure 1, side view (documentation only; not drawn)
PIN_SQUARE_MM = 0.64      # Figure 1, side view, square cross-section
OVERHANG_PIN15_END = 1.80  # Figure 1, "1,8"
OVERHANG_PIN5_SIDE = 3.00  # Figure 1, "3"
# derived (see header):
OVERHANG_PIN67_END = BODY_L_MM - OVERHANG_PIN15_END - COLUMN_SEP_MM      # 3.00
OVERHANG_PIN1_SIDE = BODY_W_MM - 4 * PIN_PITCH_MM - OVERHANG_PIN5_SIDE   # 2.54

# Table 4, page 9. Names only; the footprint carries no nets, but the pad->function map is
# what makes "pad 6 is the HV one" checkable rather than remembered.
PAD_FUNCTION = {
    "1": "+VIN", "2": "VSET", "3": "GND", "4": "/ON", "5": "VMON", "6": "HV", "7": "GND",
}
HV_PAD = "6"

# --- land pattern (engineering decisions, see header) ---
PIN_DIAGONAL_MM = PIN_SQUARE_MM * math.sqrt(2.0)   # 0.905097...
DRILL_MM = 1.30
PAD_MM = 2.10
COURTYARD_MARGIN_MM = 0.75

# --- creepage (see header). [recalled] IPC-2221B Table 6-1 column B2. ---
IPC_B2_500V_MM = 2.50
IPC_B2_ADDER_MM_PER_V = 0.005     # conservative of the two circulating readings
DESIGN_VMAX_V = 1000.0            # largest Vnom in the APS family (Table 2)
CREEPAGE_MM = round(IPC_B2_500V_MM + IPC_B2_ADDER_MM_PER_V * (DESIGN_VMAX_V - 500.0), 3)  # 5.0
PAD6_CLEARANCE_MM = CREEPAGE_MM

# --- line widths, KiCad house style ---
W_SILK = 0.12
W_FAB = 0.10
W_CRTYD = 0.05
W_SILK_HV_BAR = 0.30
W_CMTS = 0.05

DESCR = (
    "iseg APS series programmable DC-HV converter module, 7-pin THT, "
    "body 39.6 x 15.7 x 11 mm. Body outline is ASYMMETRIC about the pin array "
    "(+0.60 mm long axis, +0.23 mm short axis) per Figure 1. Pad 6 = HV output, carries a "
    "5.00 mm local clearance override. Hand solder only (270 C / 10 s / 1.5 mm from case). "
    + DATASHEET_CITATION
)
TAGS = "iseg APS HV high-voltage module THT 7-pin hand-solder AP002255 AP010105"


# ---------------------------------------------------------------------------------------
# BUILD  (implementation #1: pin-centroid outward)
# ---------------------------------------------------------------------------------------

def build_geometry():
    """Everything the emitter draws, as plain numbers. Frame: pin-array centroid at (0,0),
    +x from the pins 1..5 column toward the pins 6/7 column, +y from pin 1 toward pin 5."""
    x15 = -COLUMN_SEP_MM / 2.0
    x67 = +COLUMN_SEP_MM / 2.0
    y1 = -(4 * PIN_PITCH_MM) / 2.0

    pads = {}
    for i in range(5):
        pads[str(i + 1)] = (x15, y1 + i * PIN_PITCH_MM)
    pads["6"] = (x67, y1 + 4 * PIN_PITCH_MM)
    pads["7"] = (x67, y1)

    body = (
        x15 - OVERHANG_PIN15_END,               # x0  = -19.20
        y1 - OVERHANG_PIN1_SIDE,                # y0  =  -7.62
        x67 + OVERHANG_PIN67_END,               # x1  = +20.40
        y1 + 4 * PIN_PITCH_MM + OVERHANG_PIN5_SIDE,   # y1 = +8.08
    )
    crtyd = (body[0] - COURTYARD_MARGIN_MM, body[1] - COURTYARD_MARGIN_MM,
             body[2] + COURTYARD_MARGIN_MM, body[3] + COURTYARD_MARGIN_MM)
    body_centre = ((body[0] + body[2]) / 2.0, (body[1] + body[3]) / 2.0)
    return {"pads": pads, "body": body, "crtyd": crtyd, "body_centre": body_centre}


G = build_geometry()


# ---------------------------------------------------------------------------------------
# EMITTER
# ---------------------------------------------------------------------------------------

def fmt(v):
    """KiCad-style number formatting: no trailing zeros, no '-0', deterministic."""
    s = "{:.6f}".format(float(v)).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


class Emit(object):
    def __init__(self):
        self.lines = []

    def add(self, depth, text):
        self.lines.append("\t" * depth + text)

    def text(self):
        return "\n".join(self.lines) + "\n"


def emit_effects(e, d, size, thickness, justify=None):
    e.add(d, "(effects")
    e.add(d + 1, "(font")
    e.add(d + 2, "(size %s %s)" % (fmt(size), fmt(size)))
    e.add(d + 2, "(thickness %s)" % fmt(thickness))
    e.add(d + 1, ")")
    if justify:
        e.add(d + 1, "(justify %s)" % justify)
    e.add(d, ")")


def emit_stroke(e, d, width):
    e.add(d, "(stroke")
    e.add(d + 1, "(width %s)" % fmt(width))
    e.add(d + 1, "(type solid)")
    e.add(d, ")")


def emit_property(e, d, name, value, at, layer, size, thickness, hide=False):
    e.add(d, "(property %s %s" % (q(name), q(value)))
    e.add(d + 1, "(at %s %s %s)" % (fmt(at[0]), fmt(at[1]), fmt(at[2])))
    e.add(d + 1, "(layer %s)" % q(layer))
    if hide:
        e.add(d + 1, "(hide yes)")
    e.add(d + 1, "(uuid %s)" % q(stable_uuid("property/" + name)))
    emit_effects(e, d + 1, size, thickness)
    e.add(d, ")")


def emit_line(e, d, p0, p1, width, layer, key):
    e.add(d, "(fp_line")
    e.add(d + 1, "(start %s %s)" % (fmt(p0[0]), fmt(p0[1])))
    e.add(d + 1, "(end %s %s)" % (fmt(p1[0]), fmt(p1[1])))
    emit_stroke(e, d + 1, width)
    e.add(d + 1, "(layer %s)" % q(layer))
    e.add(d + 1, "(uuid %s)" % q(stable_uuid(key)))
    e.add(d, ")")


def emit_rect(e, d, r, width, layer, key):
    e.add(d, "(fp_rect")
    e.add(d + 1, "(start %s %s)" % (fmt(r[0]), fmt(r[1])))
    e.add(d + 1, "(end %s %s)" % (fmt(r[2]), fmt(r[3])))
    emit_stroke(e, d + 1, width)
    e.add(d + 1, "(fill no)")
    e.add(d + 1, "(layer %s)" % q(layer))
    e.add(d + 1, "(uuid %s)" % q(stable_uuid(key)))
    e.add(d, ")")


def emit_circle(e, d, centre, radius, width, layer, key, filled):
    e.add(d, "(fp_circle")
    e.add(d + 1, "(center %s %s)" % (fmt(centre[0]), fmt(centre[1])))
    e.add(d + 1, "(end %s %s)" % (fmt(centre[0] + radius), fmt(centre[1])))
    emit_stroke(e, d + 1, width)
    e.add(d + 1, "(fill %s)" % ("yes" if filled else "no"))
    e.add(d + 1, "(layer %s)" % q(layer))
    e.add(d + 1, "(uuid %s)" % q(stable_uuid(key)))
    e.add(d, ")")


def emit_text(e, d, s, at, layer, size, thickness, key):
    e.add(d, "(fp_text user %s" % q(s))
    e.add(d + 1, "(at %s %s %s)" % (fmt(at[0]), fmt(at[1]), fmt(at[2])))
    e.add(d + 1, "(layer %s)" % q(layer))
    e.add(d + 1, "(uuid %s)" % q(stable_uuid(key)))
    emit_effects(e, d + 1, size, thickness)
    e.add(d, ")")


def emit_pad(e, d, number, centre, shape, clearance=None):
    e.add(d, "(pad %s thru_hole %s" % (q(number), shape))
    e.add(d + 1, "(at %s %s)" % (fmt(centre[0]), fmt(centre[1])))
    e.add(d + 1, "(size %s %s)" % (fmt(PAD_MM), fmt(PAD_MM)))
    e.add(d + 1, "(drill %s)" % fmt(DRILL_MM))
    e.add(d + 1, '(layers "*.Cu" "*.Mask")')
    e.add(d + 1, "(remove_unused_layers no)")
    if clearance is not None:
        e.add(d + 1, "(clearance %s)" % fmt(clearance))
    e.add(d + 1, "(uuid %s)" % q(stable_uuid("pad/" + number)))
    e.add(d, ")")


# text placement (all derived from the body rectangle so they follow if the geometry changes)
def text_layout():
    x0, y0, x1, y1 = G["body"]
    cx = G["body_centre"][0]
    hv_x = G["pads"][HV_PAD][0]
    return {
        "ref_silk": (cx, y0 - 1.98, 0),
        "value_fab": (cx, y0 - 3.58, 0),
        "ref_fab": (G["body_centre"][0], G["body_centre"][1], 0),
        "fab_hv": (hv_x, y1 - 0.98, 0),
        "silk_hv_bar": ((hv_x - 4.0, y1 + 0.47), (x1, y1 + 0.47)),
        "silk_hv": (hv_x - 0.5, y1 + 1.85, 0),
        "silk_pin1_dot": (x0 - 0.40, G["pads"]["1"][1]),
        "cmts": [(cx, y1 + 3.40 + i * 1.00) for i in range(4)],
    }


T = text_layout()

# Kept short on purpose: at 0.7 mm these lines are ~40 mm wide, i.e. they stay inside the
# footprint's own extent instead of sprawling across neighbouring parts' comment layer.
CMTS_SIZE = 0.7
CMTS_THICK = 0.10
_PAD6_PAD7_GAP = 10.16 - PAD_MM
CMTS_NOTES = [
    "iseg APS technical documentation v2.5, 2024-08-20 (Fig.1 p.8, Table 4 p.9)",
    "Body 39.60 x 15.70 x 11.00; centre offset +0.60 / +0.23 from pin centroid",
    "Pad 6 = HV. Keepout %.2f mm (IPC-2221B B2, 1 kV). Pad6-7 copper gap %.2f mm"
    % (CREEPAGE_MM, _PAD6_PAD7_GAP),
    "Hand solder only: 270 C / 10 s / 1.5 mm from case. Case max 120 C.",
]


def build_footprint_text():
    e = Emit()
    x0, y0, x1, y1 = G["body"]
    pads = G["pads"]

    e.add(0, "(footprint %s" % q(FP_NAME))
    e.add(1, "(version 20260206)")
    e.add(1, '(generator "gen_lib_footprints.py")')
    e.add(1, '(generator_version "10.0")')
    e.add(1, '(layer "F.Cu")')
    e.add(1, "(descr %s)" % q(DESCR))
    e.add(1, "(tags %s)" % q(TAGS))

    emit_property(e, 1, "Reference", "REF**", T["ref_silk"], "F.SilkS", 1.0, 0.15)
    emit_property(e, 1, "Value", FP_NAME, T["value_fab"], "F.Fab", 1.0, 0.15)
    emit_property(e, 1, "Datasheet", DATASHEET_URI, (0, 0, 0), "F.Fab", 1.0, 0.15, hide=True)
    emit_property(e, 1, "Description", DESCR, (0, 0, 0), "F.Fab", 1.0, 0.15, hide=True)

    e.add(1, "(attr through_hole exclude_from_pos_files)")
    e.add(1, "(duplicate_pad_numbers_are_jumpers no)")

    # ---- F.SilkS: true (asymmetric) body outline, pin-1 dot outside the can, HV marking ----
    emit_rect(e, 1, (x0, y0, x1, y1), W_SILK, "F.SilkS", "silk/body")
    emit_circle(e, 1, T["silk_pin1_dot"], 0.25, W_SILK, "F.SilkS", "silk/pin1", filled=True)
    bar0, bar1 = T["silk_hv_bar"]
    emit_line(e, 1, bar0, bar1, W_SILK_HV_BAR, "F.SilkS", "silk/hvbar")
    emit_text(e, 1, "HV", T["silk_hv"], "F.SilkS", 1.2, 0.25, "silk/hvtext")

    # ---- F.CrtYd ----
    emit_rect(e, 1, G["crtyd"], W_CRTYD, "F.CrtYd", "crtyd/body")

    # ---- F.Fab: same outline, chamfered at the pin-1 corner ----
    ch = 1.5
    fab_pts = [(x0, y0 + ch), (x0 + ch, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + ch)]
    for i in range(len(fab_pts) - 1):
        emit_line(e, 1, fab_pts[i], fab_pts[i + 1], W_FAB, "F.Fab", "fab/outline/%d" % i)
    emit_text(e, 1, "${REFERENCE}", T["ref_fab"], "F.Fab", 1.0, 0.15, "fab/reference")
    emit_text(e, 1, "HV", T["fab_hv"], "F.Fab", 1.0, 0.15, "fab/hv")

    # ---- Cmts.User: provenance, the derivation, and the keepout drawn to scale ----
    for i, note in enumerate(CMTS_NOTES):
        cx, cy = T["cmts"][i]
        emit_text(e, 1, note, (cx, cy, 0), "Cmts.User", CMTS_SIZE, CMTS_THICK,
                  "cmts/note/%d" % i)
    emit_circle(e, 1, pads[HV_PAD], CREEPAGE_MM, W_CMTS, "Cmts.User", "cmts/hvkeepout",
                filled=False)

    # ---- pads ----
    for n in ("1", "2", "3", "4", "5", "6", "7"):
        shape = "rect" if n == "1" else "circle"
        clr = PAD6_CLEARANCE_MM if n == HV_PAD else None
        emit_pad(e, 1, n, pads[n], shape, clearance=clr)

    e.add(1, "(embedded_fonts no)")
    e.add(0, ")")
    return e.text()


# ---------------------------------------------------------------------------------------
# MINIMAL S-EXPRESSION READER  (shares no code with the emitter, so a bug in one cannot
# cancel out in the other)
# ---------------------------------------------------------------------------------------

_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+')


def sexp_parse(text):
    stack = [[]]
    for m in _TOKEN.finditer(text):
        t = m.group(0)
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            if len(stack) == 1:
                raise ValueError("unbalanced ')' at offset %d" % m.start())
            stack.pop()
        elif t.startswith('"'):
            stack[-1].append(("str", t[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        else:
            stack[-1].append(("atom", t))
    if len(stack) != 1:
        raise ValueError("unbalanced '(' -- %d unclosed" % (len(stack) - 1))
    if len(stack[0]) != 1:
        raise ValueError("expected exactly one top-level form, got %d" % len(stack[0]))
    return stack[0][0]


def head(node):
    if isinstance(node, list) and node and isinstance(node[0], tuple):
        return node[0][1]
    return None


def val(node, i):
    x = node[i]
    return x[1] if isinstance(x, tuple) else None


def children(node, tag):
    return [c for c in node if isinstance(c, list) and head(c) == tag]


def child(node, tag):
    c = children(node, tag)
    return c[0] if c else None


def layer_of(node):
    c = child(node, "layer")
    return val(c, 1) if c else None


# ---------------------------------------------------------------------------------------
# ACCEPTANCE CHECKS
# ---------------------------------------------------------------------------------------

class Fail(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, msg)
        self.code = code


def find_first(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


# ---- (a) INDEPENDENT RECOMPUTATION -------------------------------------------------------
# Deliberately a SECOND IMPLEMENTATION, not a re-read of build_geometry()'s variables.
# build_geometry() works OUTWARD from the pin-array centroid. This one works INWARD from the
# body rectangle: it places the 39.60 x 15.70 body about its own (offset) centre and then finds
# the pins by stepping in from the body edges by the four overhangs. The two paths share only
# the five Figure-1 primitives, so a sign error or a transposed overhang in either one shows up
# as a disagreement rather than cancelling.

def independent_pad_centres():
    L = 39.60
    W = 15.70
    ov_pin15_end = 1.80          # Figure 1, labelled
    ov_pin5_side = 3.00          # Figure 1, labelled
    col_sep = 34.80              # Figure 1, labelled
    span_1_to_5 = 10.16          # Figure 1, labelled
    pitch = span_1_to_5 / 4.0

    ov_pin67_end = L - ov_pin15_end - col_sep        # 3.00
    ov_pin1_side = W - span_1_to_5 - ov_pin5_side    # 2.54

    # body centre relative to the pin-array centroid: half the difference of opposite overhangs.
    off_long = (ov_pin67_end - ov_pin15_end) / 2.0   # +0.60, toward the pins 6/7 end
    off_short = (ov_pin5_side - ov_pin1_side) / 2.0  # +0.23, toward pin 5

    bx0 = off_long - L / 2.0
    bx1 = off_long + L / 2.0
    by0 = off_short - W / 2.0
    by1 = off_short + W / 2.0

    col15_x = bx0 + ov_pin15_end     # step in from the pins 1..5 end
    col67_x = bx1 - ov_pin67_end     # step in from the pins 6/7 end
    pin1_y = by0 + ov_pin1_side      # step in from pin 1's long edge
    pin5_y = by1 - ov_pin5_side      # step in from pin 5's long edge

    out = {}
    for i in range(5):
        out[str(i + 1)] = (col15_x, pin1_y + i * pitch)
    out["6"] = (col67_x, pin5_y)
    out["7"] = (col67_x, pin1_y)
    return out, (bx0, by0, bx1, by1), (col67_x - col15_x, pin5_y - pin1_y)


def parse_emitted(path):
    if not os.path.exists(path):
        raise Fail(2, "emitted file does not exist: %s" % path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        root = sexp_parse(text)
    except ValueError as ex:
        raise Fail(2, "our own reader cannot parse the file we just wrote: %s" % ex)
    if head(root) != "footprint":
        raise Fail(2, "top-level form is %r; KiCad 10 requires (footprint ...), not the "
                      "legacy (module ...)" % head(root))
    return root, text


def check_a_pads_from_first_principles(root):
    want, want_body, (want_colsep, want_span) = independent_pad_centres()

    if abs(want_colsep - 34.80) > 1e-9 or abs(want_span - 10.16) > 1e-9:
        raise Fail(1, "independent recomputation is self-inconsistent: column sep %.6f, "
                      "pin1-pin5 span %.6f" % (want_colsep, want_span))

    got = {}
    shapes = {}
    clearances = {}
    for p in children(root, "pad"):
        num = val(p, 1)
        shapes[num] = val(p, 3)
        at = child(p, "at")
        got[num] = (float(val(at, 1)), float(val(at, 2)))
        c = child(p, "clearance")
        clearances[num] = float(val(c, 1)) if c else None
        sz = child(p, "size")
        if abs(float(val(sz, 1)) - PAD_MM) > 1e-9 or abs(float(val(sz, 2)) - PAD_MM) > 1e-9:
            raise Fail(1, "pad %s size %s x %s != %.3f" % (num, val(sz, 1), val(sz, 2), PAD_MM))
        dr = child(p, "drill")
        if abs(float(val(dr, 1)) - DRILL_MM) > 1e-9:
            raise Fail(1, "pad %s drill %s != %.3f" % (num, val(dr, 1), DRILL_MM))
        lays = [val(child(p, "layers"), i) for i in (1, 2)]
        if lays != ["*.Cu", "*.Mask"]:
            raise Fail(1, "pad %s layers %r != ['*.Cu', '*.Mask']" % (num, lays))

    problems = []
    if set(got) != set(want):
        problems.append("pad set %s != %s" % (sorted(got), sorted(want)))
    for n in sorted(want):
        if n not in got:
            continue
        dx = got[n][0] - want[n][0]
        dy = got[n][1] - want[n][1]
        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            problems.append("pad %s at (%.6f, %.6f); first-principles says (%.6f, %.6f), "
                            "delta (%.6f, %.6f)" % (n, got[n][0], got[n][1],
                                                    want[n][0], want[n][1], dx, dy))
    if shapes.get("1") != "rect":
        problems.append("pad 1 shape %r != 'rect' (pin-1 marker)" % shapes.get("1"))
    for n in ("2", "3", "4", "5", "6", "7"):
        if shapes.get(n) != "circle":
            problems.append("pad %s shape %r != 'circle'" % (n, shapes.get(n)))

    # drill must clear the SQUARE pin's diagonal, with the allowance we claimed
    allowance = DRILL_MM - PIN_DIAGONAL_MM
    if allowance <= 0:
        problems.append("drill %.3f does not clear the 0.64 mm square pin diagonal %.5f"
                        % (DRILL_MM, PIN_DIAGONAL_MM))
    elif allowance < 0.25:
        problems.append("drill allowance %.3f mm is below the IPC-2222 level-B style 0.25 mm "
                        "lead-to-hole allowance" % allowance)

    ring = (PAD_MM - DRILL_MM) / 2.0
    if ring < 0.35:
        problems.append("annular ring %.3f mm is thin for a hand-soldered 11 mm tall module"
                        % ring)

    # body outline on F.SilkS must be the asymmetric rectangle, not the centred one
    silk_rects = [r for r in children(root, "fp_rect") if layer_of(r) == "F.SilkS"]
    if len(silk_rects) != 1:
        problems.append("expected exactly 1 F.SilkS body rectangle, found %d" % len(silk_rects))
    else:
        s = silk_rects[0]
        gb = (float(val(child(s, "start"), 1)), float(val(child(s, "start"), 2)),
              float(val(child(s, "end"), 1)), float(val(child(s, "end"), 2)))
        for i, (g, w) in enumerate(zip(gb, want_body)):
            if abs(g - w) > 1e-6:
                problems.append("silk body edge %d = %.6f, first-principles %.6f" % (i, g, w))
        if abs((gb[2] - gb[0]) - 39.60) > 1e-6 or abs((gb[3] - gb[1]) - 15.70) > 1e-6:
            problems.append("silk body is %.4f x %.4f, must be 39.60 x 15.70"
                            % (gb[2] - gb[0], gb[3] - gb[1]))
        # THE defect being fixed: a symmetric outline about the pin centroid.
        bcx = (gb[0] + gb[2]) / 2.0
        bcy = (gb[1] + gb[3]) / 2.0
        if abs(bcx) < 1e-6 and abs(bcy) < 1e-6:
            problems.append("body outline is CENTRED on the pin array -- this is precisely the "
                            "reference footprint's defect (see header). Expected centre "
                            "(+0.60, +0.23).")
        if abs(bcx - 0.60) > 1e-6 or abs(bcy - 0.23) > 1e-6:
            problems.append("body centre (%.6f, %.6f) != (+0.60, +0.23)" % (bcx, bcy))

    if problems:
        raise Fail(1, "(a) pad/outline recomputation:\n  - " + "\n  - ".join(problems))
    return got, clearances


def pad_half_extent(num, ux, uy):
    """Half-extent of a pad along the unit vector (ux,uy). Pad 1 is a square, the rest circles."""
    if num == "1":
        # square of side PAD_MM: support function of a box
        return (PAD_MM / 2.0) * (abs(ux) + abs(uy))
    return PAD_MM / 2.0


# ---- (b) CREEPAGE ------------------------------------------------------------------------

def check_b_creepage(pads, clearances):
    report = []
    problems = []

    hv = pads[HV_PAD]
    gaps = {}
    for n, p in sorted(pads.items()):
        if n == HV_PAD:
            continue
        dx, dy = p[0] - hv[0], p[1] - hv[1]
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        gap = d - pad_half_extent(HV_PAD, ux, uy) - pad_half_extent(n, -ux, -uy)
        gaps[n] = (d, gap)

    d67, gap67 = gaps["7"]
    report.append("pad 6 (HV) -> pad 7 (GND): centre %.4f mm, copper gap %.4f mm" % (d67, gap67))
    if abs(d67 - 10.16) > 1e-6:
        problems.append("pad6-pad7 centre distance %.6f != 10.16 mm (part geometry, Figure 1)"
                        % d67)

    nearest = min(gaps.items(), key=lambda kv: kv[1][1])
    report.append("pad 6 (HV) -> nearest other pad = pad %s: centre %.4f mm, copper gap %.4f mm"
                  % (nearest[0], nearest[1][0], nearest[1][1]))
    report.append("required creepage at %d V (IPC-2221B B2, external uncoated, [recalled]): "
                  "%.4f mm = %.2f + %.4f x (%d - 500)"
                  % (DESIGN_VMAX_V, CREEPAGE_MM, IPC_B2_500V_MM, IPC_B2_ADDER_MM_PER_V,
                     DESIGN_VMAX_V))

    for n, (d, gap) in sorted(gaps.items()):
        if gap < CREEPAGE_MM:
            problems.append("pad 6 -> pad %s copper gap %.4f mm < required creepage %.4f mm at "
                            "%d V -- THIS FOOTPRINT CANNOT MEET CLEARANCE AT FULL SCALE"
                            % (n, gap, CREEPAGE_MM, DESIGN_VMAX_V))

    c6 = clearances.get(HV_PAD)
    if c6 is None:
        problems.append("pad 6 has no local (clearance ...) override; zone fills and foreign "
                        "copper would be governed only by whatever netclass exists")
    else:
        report.append("pad 6 local clearance override: %.4f mm" % c6)
        if c6 + 1e-9 < CREEPAGE_MM:
            problems.append("pad 6 local clearance %.4f mm < creepage %.4f mm" % (c6, CREEPAGE_MM))
        if c6 > nearest[1][1] + 1e-9:
            problems.append("pad 6 local clearance %.4f mm EXCEEDS its own gap to pad %s "
                            "(%.4f mm): the footprint would violate its own DRC rule and the "
                            "board could never pass" % (c6, nearest[0], nearest[1][1]))
    for n, c in sorted(clearances.items()):
        if n != HV_PAD and c is not None:
            problems.append("pad %s carries a local clearance %.4f; only pad 6 should" % (n, c))

    v_supported = 500.0 + (nearest[1][1] - IPC_B2_500V_MM) / IPC_B2_ADDER_MM_PER_V
    report.append("geometry supports up to %.0f V by the same expression (family max is %d V)"
                  % (v_supported, DESIGN_VMAX_V))

    if problems:
        raise Fail(1, "(b) creepage:\n  - " + "\n  - ".join(problems))
    return report


# ---- (c) KiCad READBACK ------------------------------------------------------------------

PCBNEW_PROBE = r'''
import json, os, sys
import pcbnew

libdir = sys.argv[1]
name = sys.argv[2]
io = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
fp = io.FootprintLoad(libdir, name)
if fp is None:
    print(json.dumps({"error": "FootprintLoad returned None"}))
    sys.exit(0)

def mm(v):
    return round(v / 1e6, 6)

org = fp.GetPosition()
pads = []
for p in fp.Pads():
    try:
        pos = p.GetFPRelativePosition()
    except AttributeError:
        pos = p.GetPosition() - org
    try:
        c = p.GetLocalClearance()
    except Exception:
        c = None
    if hasattr(c, "value"):
        c = c.value() if c.has_value() else None
    clr = None if c is None else mm(c)
    pads.append({
        "number": p.GetNumber(),
        "x": mm(pos.x), "y": mm(pos.y),
        "sx": mm(p.GetSizeX()), "sy": mm(p.GetSizeY()),
        "drill": mm(p.GetDrillSizeX()),
        "shape": int(p.GetShape()),
        "clearance": clr,
        "layers": p.GetLayerSet().FmtHex(),
    })
pads.sort(key=lambda d: d["number"])

layers = {}
for g in fp.GraphicalItems():
    ln = pcbnew.BOARD.GetStandardLayerName(g.GetLayer())
    layers[ln] = layers.get(ln, 0) + 1

fields = {}
try:
    for f in fp.GetFields():
        fields[f.GetName()] = pcbnew.BOARD.GetStandardLayerName(f.GetLayer())
except Exception:
    pass

print(json.dumps({
    "name": fp.GetFPIDAsString(),
    "attrs": int(fp.GetAttributes()),
    "pads": pads,
    "graphics_by_layer": layers,
    "fields": fields,
    "pad_count": fp.GetPadCount(),
}))
'''

# pcbnew's API reports the USER-FACING layer names ("F.Silkscreen", "User.Comments"); the file
# format uses the short forms ("F.SilkS", "Cmts.User"). Both name the same layer -- verified by
# loading this footprint and printing GetLayer() ids (5, 31, 35, 19) alongside both spellings.
LAYER_ALIASES = {
    "F.SilkS": ("F.SilkS", "F.Silkscreen"),
    "F.CrtYd": ("F.CrtYd", "F.Courtyard"),
    "F.Fab": ("F.Fab",),
    "Cmts.User": ("Cmts.User", "User.Comments"),
}


def check_c_pcbnew_readback():
    """Make KiCad itself read the file back. This is the strongest available instrument: it is
    KiCad's own parser and its own PAD object, not our reader agreeing with our writer."""
    py = find_first(PY_KICAD_CANDIDATES)
    if py is None:
        raise Fail(2, "no KiCad python found; cannot prove KiCad can load the footprint. "
                      "Tried: %s" % ", ".join(PY_KICAD_CANDIDATES))
    tmp = tempfile.mkdtemp(prefix="iseg_fpcheck_")
    probe = os.path.join(tmp, "probe.py")
    with open(probe, "w", encoding="utf-8", newline="\n") as f:
        f.write(PCBNEW_PROBE)
    r = subprocess.run([py, probe, PRETTY_DIR, FP_NAME],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = r.stdout.decode("utf-8", "replace").strip()
    err = r.stderr.decode("utf-8", "replace").strip()
    if r.returncode != 0 or not out:
        raise Fail(3, "pcbnew could not load the footprint (rc=%d)\nstdout: %s\nstderr: %s"
                   % (r.returncode, out, err))
    try:
        data = json.loads(out.splitlines()[-1])
    except ValueError:
        raise Fail(3, "pcbnew probe produced unparseable output:\n%s\n%s" % (out, err))
    if "error" in data:
        raise Fail(3, "pcbnew: %s" % data["error"])

    want, _, _ = independent_pad_centres()
    problems = []
    got = {}
    for p in data["pads"]:
        got[p["number"]] = p
    if set(got) != set(want):
        problems.append("pcbnew read pads %s, expected %s" % (sorted(got), sorted(want)))
    if data["pad_count"] != 7:
        problems.append("pcbnew reports pad count %d, expected 7" % data["pad_count"])
    for n in sorted(want):
        p = got.get(n)
        if p is None:
            continue
        if abs(p["x"] - want[n][0]) > 1e-4 or abs(p["y"] - want[n][1]) > 1e-4:
            problems.append("pcbnew read pad %s at (%.6f, %.6f); first principles (%.6f, %.6f)"
                            % (n, p["x"], p["y"], want[n][0], want[n][1]))
        if abs(p["drill"] - DRILL_MM) > 1e-4:
            problems.append("pcbnew read pad %s drill %.4f != %.4f" % (n, p["drill"], DRILL_MM))
        if abs(p["sx"] - PAD_MM) > 1e-4 or abs(p["sy"] - PAD_MM) > 1e-4:
            problems.append("pcbnew read pad %s size %.4f x %.4f != %.4f"
                            % (n, p["sx"], p["sy"], PAD_MM))
    c6 = got.get(HV_PAD, {}).get("clearance")
    if c6 is None or abs(c6 - PAD6_CLEARANCE_MM) > 1e-4:
        problems.append("pcbnew read pad 6 local clearance %r, expected %.4f -- the HV anti-pad "
                        "did not survive the round trip" % (c6, PAD6_CLEARANCE_MM))

    lay = data.get("graphics_by_layer", {})
    for need, aliases in sorted(LAYER_ALIASES.items()):
        if sum(lay.get(a, 0) for a in aliases) <= 0:
            problems.append("pcbnew sees no graphics on %s (looked for %s; it reported %s)"
                            % (need, "/".join(aliases), sorted(lay)))

    fields = data.get("fields", {})
    if fields:
        if fields.get("Reference") not in LAYER_ALIASES["F.SilkS"]:
            problems.append("pcbnew reads the Reference field on %r, expected F.SilkS"
                            % fields.get("Reference"))
        if fields.get("Value") not in LAYER_ALIASES["F.Fab"]:
            problems.append("pcbnew reads the Value field on %r, expected F.Fab"
                            % fields.get("Value"))

    if problems:
        raise Fail(1, "(c) pcbnew readback:\n  - " + "\n  - ".join(problems))
    return data


def check_c2_kicad_cli():
    """Secondary: kicad-cli must also accept the library, and must not rewrite our schema
    version (which would mean (version 20260206) was guessed wrong)."""
    cli = find_first(KICAD_CLI_CANDIDATES)
    if cli is None:
        return ["kicad-cli not found; skipped (pcbnew readback already passed)"]
    report = []
    tmp = tempfile.mkdtemp(prefix="iseg_fpcli_")
    up = os.path.join(tmp, "up")
    r = subprocess.run([cli, "fp", "upgrade", PRETTY_DIR, "-o", up, "--force"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise Fail(3, "kicad-cli fp upgrade rejected the library (rc=%d):\n%s" % (r.returncode, out))
    report.append("kicad-cli fp upgrade: rc=0 %s" % (("| " + out) if out else ""))
    upf = os.path.join(up, FP_NAME + ".kicad_mod")
    if os.path.exists(upf):
        with open(upf, "r", encoding="utf-8") as f:
            t = f.read()
        m = re.search(r"\(version (\d+)\)", t)
        if not m or m.group(1) != "20260206":
            raise Fail(1, "KiCad rewrote the schema version to %s; our (version 20260206) is "
                          "stale" % (m.group(1) if m else "?"))
        report.append("round-trip kept (version 20260206)")

    svg = os.path.join(tmp, "svg")
    os.makedirs(svg, exist_ok=True)
    r = subprocess.run([cli, "fp", "export", "svg", PRETTY_DIR, "-o", svg],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise Fail(3, "kicad-cli fp export svg failed (rc=%d):\n%s" % (r.returncode, out))
    svgs = sorted(n for n in os.listdir(svg) if n.lower().endswith(".svg"))
    report.append("kicad-cli fp export svg: rc=0, %d file(s) -> %s" % (len(svgs), svg))
    return report


# ---- (d) LEGIBILITY ----------------------------------------------------------------------

def _text_box(at, s, size, thickness):
    """Conservative bounding box of KiCad stroke text, centre-justified.
    KiCad's stroke font advances ~0.75 em per glyph; add the stroke thickness on every side."""
    w = len(s) * size * 0.75 + thickness
    h = size + thickness
    return (at[0] - w / 2.0, at[1] - h / 2.0, at[0] + w / 2.0, at[1] + h / 2.0)


def _pad_box(num, centre):
    h = PAD_MM / 2.0
    return (centre[0] - h, centre[1] - h, centre[0] + h, centre[1] + h)


def _box_gap(a, b):
    """Separation between two axis-aligned boxes; negative means overlap."""
    dx = max(a[0] - b[2], b[0] - a[2])
    dy = max(a[1] - b[3], b[1] - a[3])
    if dx >= 0 and dy >= 0:
        return math.hypot(dx, dy)
    return max(dx, dy)


def check_d_legibility(root, pads):
    problems = []
    pad_boxes = {n: _pad_box(n, p) for n, p in pads.items()}

    # courtyard must enclose the body AND every pad
    crt = [r for r in children(root, "fp_rect") if layer_of(r) == "F.CrtYd"]
    if len(crt) != 1:
        problems.append("expected exactly 1 F.CrtYd rectangle, found %d" % len(crt))
    else:
        c = crt[0]
        cb = (float(val(child(c, "start"), 1)), float(val(child(c, "start"), 2)),
              float(val(child(c, "end"), 1)), float(val(child(c, "end"), 2)))
        if abs((cb[2] - cb[0]) - (39.60 + 2 * COURTYARD_MARGIN_MM)) > 1e-6:
            problems.append("courtyard width %.4f != body 39.60 + 2 x %.2f"
                            % (cb[2] - cb[0], COURTYARD_MARGIN_MM))
        for n, b in sorted(pad_boxes.items()):
            if not (cb[0] <= b[0] and cb[1] <= b[1] and cb[2] >= b[2] and cb[3] >= b[3]):
                problems.append("pad %s is not inside the courtyard" % n)
        if COURTYARD_MARGIN_MM <= 0.254:
            problems.append("courtyard margin %.3f is a hairline; the reference footprint's "
                            "0.254 mm is what we are moving away from" % COURTYARD_MARGIN_MM)

    # silkscreen must not print on any pad
    for r in children(root, "fp_rect"):
        if layer_of(r) != "F.SilkS":
            continue
        rb = (float(val(child(r, "start"), 1)), float(val(child(r, "start"), 2)),
              float(val(child(r, "end"), 1)), float(val(child(r, "end"), 2)))
        for n, b in sorted(pad_boxes.items()):
            # rectangle OUTLINE, so only an edge crossing a pad matters
            for edge in ((rb[0], rb[1], rb[0], rb[3]), (rb[2], rb[1], rb[2], rb[3]),
                         (rb[0], rb[1], rb[2], rb[1]), (rb[0], rb[3], rb[2], rb[3])):
                ebox = (min(edge[0], edge[2]) - W_SILK / 2, min(edge[1], edge[3]) - W_SILK / 2,
                        max(edge[0], edge[2]) + W_SILK / 2, max(edge[1], edge[3]) + W_SILK / 2)
                if _box_gap(ebox, b) < 0.15:
                    problems.append("F.SilkS body edge is within 0.15 mm of pad %s "
                                    "(silk over a solderable pad)" % n)

    for c in children(root, "fp_circle"):
        if layer_of(c) != "F.SilkS":
            continue
        cx = float(val(child(c, "center"), 1))
        cy = float(val(child(c, "center"), 2))
        ex = float(val(child(c, "end"), 1))
        rad = abs(ex - cx) + W_SILK / 2
        cb = (cx - rad, cy - rad, cx + rad, cy + rad)
        for n, b in sorted(pad_boxes.items()):
            if _box_gap(cb, b) < 0.15:
                problems.append("F.SilkS pin-1 marker is within 0.15 mm of pad %s" % n)
        # the pin-1 marker must be OUTSIDE the can, or it is invisible after assembly
        if G["body"][0] <= cx <= G["body"][2] and G["body"][1] <= cy <= G["body"][3]:
            problems.append("pin-1 silk marker at (%.3f, %.3f) is under the module body; it "
                            "would be invisible once the can is fitted" % (cx, cy))

    for ln in children(root, "fp_line"):
        if layer_of(ln) != "F.SilkS":
            continue
        s0 = (float(val(child(ln, "start"), 1)), float(val(child(ln, "start"), 2)))
        s1 = (float(val(child(ln, "end"), 1)), float(val(child(ln, "end"), 2)))
        w = float(val(child(child(ln, "stroke"), "width"), 1))
        lb = (min(s0[0], s1[0]) - w / 2, min(s0[1], s1[1]) - w / 2,
              max(s0[0], s1[0]) + w / 2, max(s0[1], s1[1]) + w / 2)
        for n, b in sorted(pad_boxes.items()):
            if _box_gap(lb, b) < 0.15:
                problems.append("F.SilkS line is within 0.15 mm of pad %s" % n)

    # texts: none may sit on a pad; silk texts must be outside the can to stay readable
    texts = []
    for t in children(root, "fp_text"):
        s = val(t, 2)
        at = child(t, "at")
        pos = (float(val(at, 1)), float(val(at, 2)))
        eff = child(t, "effects")
        font = child(eff, "font")
        size = float(val(child(font, "size"), 1))
        thick = float(val(child(font, "thickness"), 1))
        texts.append((s, pos, size, thick, layer_of(t)))
    for s, pos, size, thick, lay in texts:
        box = _text_box(pos, s, size, thick)
        for n, b in sorted(pad_boxes.items()):
            if _box_gap(box, b) < 0.05:
                problems.append("text %r on %s overlaps pad %s" % (s[:24], lay, n))
        if lay == "F.SilkS":
            inside = (G["body"][0] < box[0] and box[2] < G["body"][2]
                      and G["body"][1] < box[1] and box[3] < G["body"][3])
            if inside:
                problems.append("silk text %r is entirely under the module can; unreadable "
                                "after assembly" % s[:24])
        # annotation must not sprawl across the neighbours: nothing wider than the courtyard
        crt_w = 39.60 + 2 * COURTYARD_MARGIN_MM
        if (box[2] - box[0]) > crt_w:
            problems.append("text %r on %s is %.1f mm wide, wider than the %.1f mm courtyard; "
                            "it will overprint neighbouring parts"
                            % (s[:32], lay, box[2] - box[0], crt_w))

    # the HV marking must actually exist, on silk and on fab
    silk_hv = [t for t in texts if t[4] == "F.SilkS" and "HV" in t[0]]
    fab_hv = [t for t in texts if t[4] == "F.Fab" and "HV" in t[0]]
    if not silk_hv:
        problems.append("no HV marking on F.SilkS")
    if not fab_hv:
        problems.append("no HV marking on F.Fab")
    # reference designator on BOTH silk (property) and fab (text)
    props = {val(p, 1): p for p in children(root, "property")}
    if "Reference" not in props or layer_of(props["Reference"]) != "F.SilkS":
        problems.append("Reference property missing or not on F.SilkS")
    if not [t for t in texts if t[0] == "${REFERENCE}" and t[4] == "F.Fab"]:
        problems.append("no ${REFERENCE} text on F.Fab")
    # provenance note naming the datasheet and its date
    cm = [t for t in texts if t[4] == "Cmts.User"]
    if not [t for t in cm if "2024-08-20" in t[0] and "iseg" in t[0]]:
        problems.append("no Cmts.User note naming the datasheet and its date")

    if problems:
        raise Fail(3, "(d) legibility:\n  - " + "\n  - ".join(problems))
    return len(texts)


# ---- determinism + project integration ---------------------------------------------------

def check_determinism(path):
    with open(path, "rb") as f:
        on_disk = f.read()
    again = build_footprint_text().encode("utf-8")
    if on_disk != again:
        raise Fail(1, "regenerating produced different bytes; output is not deterministic")
    if build_footprint_text() != build_footprint_text():
        raise Fail(1, "build_footprint_text() is not stable across calls")


def warn_project_integration():
    """NON-FATAL. Reports contract breaks with the sibling generators that this tool is not
    entitled to fix by itself."""
    warns = []
    fptab = os.path.join(LIB_DIR, "fp-lib-table")
    if not os.path.exists(fptab):
        warns.append("hardware/hvctl/lib/fp-lib-table does not exist; KiCad will not find "
                     "iseg.pretty")
    else:
        with open(fptab, "r", encoding="utf-8") as f:
            t = f.read()
        if "iseg.pretty" not in t:
            warns.append("fp-lib-table does not reference iseg.pretty")

    sym = os.path.join(HERE, "gen_lib_symbols.py")
    if os.path.exists(sym):
        with open(sym, "r", encoding="utf-8") as f:
            st = f.read()
        m = re.search(r'^FOOTPRINT\s*=\s*"([^"]+)"', st, re.M)
        if m:
            want = m.group(1)
            have = "iseg:" + FP_NAME
            if want != have:
                warns.append(
                    "FOOTPRINT NAME CONTRACT BROKEN. gen_lib_symbols.py puts %r in every "
                    "symbol's Footprint field, but this generator emits %r. The netlist will "
                    "not resolve and the board will come up with an unassigned footprint. "
                    "Fix ONE of the two -- this is a project-level naming decision, so it is "
                    "reported, not silently patched." % (want, have))
        mf = re.search(r'^FP_FILTERS\s*=\s*"([^"]+)"', st, re.M)
        if mf:
            pat = mf.group(1).replace("*", "")
            if not all(tok.lower() in FP_NAME.lower() for tok in pat.split() if tok):
                pass  # crude; the FOOTPRINT check above is the load-bearing one
            import fnmatch
            if not fnmatch.fnmatch(FP_NAME.lower(), mf.group(1).lower()):
                warns.append("gen_lib_symbols.py FP_FILTERS=%r does not match %r, so the "
                             "footprint chooser will hide this footprint from the symbol"
                             % (mf.group(1), FP_NAME))
    return warns


# ---------------------------------------------------------------------------------------

def main():
    try:
        os.makedirs(PRETTY_DIR, exist_ok=True)
        text = build_footprint_text()
        with open(OUT_MOD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s (%d bytes)" % (OUT_MOD, len(text.encode("utf-8"))))

        check_determinism(OUT_MOD)
        print("[ok] deterministic: regenerated bytes identical (uuid5, no timestamps)")

        root, _ = parse_emitted(OUT_MOD)
        print("[ok] top-level form is (footprint ...) -- KiCad 10, not legacy (module ...)")

        pads, clearances = check_a_pads_from_first_principles(root)
        print("[ok] (a) all 7 pad centres, the drill, the pad size and the ASYMMETRIC body "
              "outline agree with an independent recomputation")
        print("        drill %.3f mm clears the 0.64 mm square pin diagonal %.5f mm by "
              "%.3f mm; annular ring %.3f mm"
              % (DRILL_MM, PIN_DIAGONAL_MM, DRILL_MM - PIN_DIAGONAL_MM,
                 (PAD_MM - DRILL_MM) / 2.0))
        for n in sorted(pads, key=int):
            print("        pad %s %-5s emitted (%8.3f, %8.3f)"
                  % (n, PAD_FUNCTION[n], pads[n][0], pads[n][1]))

        for line in check_b_creepage(pads, clearances):
            print("[ok] (b) %s" % line)

        ntexts = check_d_legibility(root, pads)
        print("[ok] (d) legibility: courtyard encloses body+pads, no silk on pads, pin-1 "
              "marker outside the can, %d texts placed, HV marked on F.SilkS and F.Fab"
              % ntexts)

        data = check_c_pcbnew_readback()
        print("[ok] (c) pcbnew FootprintLoad() succeeded: %r, %d pads"
              % (data["name"], data["pad_count"]))
        for p in data["pads"]:
            print("        KiCad read pad %s at (%8.3f, %8.3f)  size %.3f  drill %.3f  "
                  "clearance %s" % (p["number"], p["x"], p["y"], p["sx"], p["drill"],
                                    ("%.3f" % p["clearance"]) if p["clearance"] is not None
                                    else "-"))
        print("        graphics by layer: %s"
              % ", ".join("%s=%d" % kv for kv in sorted(data["graphics_by_layer"].items())))

        for line in check_c2_kicad_cli():
            print("[ok] (c) %s" % line)

    except Fail as ex:
        sys.stderr.write("FAIL(%d): %s\n" % (ex.code, ex))
        return ex.code
    except Exception as ex:  # noqa: BLE001
        sys.stderr.write("FAIL(2): unexpected: %r\n" % (ex,))
        return 2

    warns = warn_project_integration()
    for w in warns:
        sys.stderr.write("WARNING: %s\n" % w)
    print("ALL CHECKS PASSED" + (" (with %d warning(s) above)" % len(warns) if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
