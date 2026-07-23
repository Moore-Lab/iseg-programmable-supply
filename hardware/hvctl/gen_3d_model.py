#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_3d_model.py -- generate the 3D model for the iseg APS series HV module.

Emits two files into  <HERE>/lib/iseg.3dshapes/ :

    iseg_APS_THT.step   ISO-10303-21 / AP214 (AUTOMOTIVE_DESIGN), an
                        ADVANCED_BREP_SHAPE_REPRESENTATION holding eight
                        MANIFOLD_SOLID_BREPs (1 case + 7 pins).  Every face is
                        a genuine ADVANCED_FACE on a PLANE bounded by
                        EDGE_CURVEs on LINEs -- a real B-rep solid, not a mesh
                        and not a FACETED_BREP.  (A box needs only planar
                        faces, so "B-rep" and "faceted" coincide *geometrically*
                        here; the distinction is that the entities emitted are
                        the ADVANCED_BREP ones an AP214 consumer expects.)
    iseg_APS_THT.wrl    VRML V2.0 utf8, same geometry as IndexedFaceSets, with
                        colour: dark grey steel case, gold pins.
                        NOTE: KiCad interprets VRML units as 0.1 inch, so the
                        numbers written are millimetres / 2.54.

GEOMETRY SOURCE OF TRUTH
    iseg APS series technical documentation v2.5, 2024-08-20
      - Figure 1 (manual page 8): dimensional drawing, vector art, no
        extractable text; read off the rendered drawing.
      - Table 4 (manual page 9): pin assignment.

    Body            39.6 (L) x 15.7 (W) x 11 (H) mm
    Pins            square, 0.64 mm across, 2.2 mm +/-0.4 below the case
    Pins 1..5       one column, 2.54 mm pitch, pin1->pin5 span 10.16 mm
    Pins 7, 6       far column, 34.8 mm from the 1..5 column;
                    pin 7 in line with pin 1, pin 6 in line with pin 5
    Case edges      1.8 mm beyond the 1..5 column, 3.0 mm beyond the 6/7 column,
                    3.0 mm beyond pin 5, 2.54 mm beyond pin 1
    => THE CASE IS NOT CENTRED ON THE PIN RECTANGLE.  It is offset 0.6 mm along
       the long axis and 0.23 mm along the short axis.  Third-party models that
       centre the case on the pins are wrong by exactly those amounts.

MODEL ORIGIN
    (0,0) is the CENTRE OF THE PIN BOUNDING RECTANGLE, z=0 is the underside of
    the case == the board top surface.  A footprint whose pad origin is the pin
    centroid therefore uses (offset (xyz 0 0 0)).  That is the entire reason
    this file exists instead of reusing a corner-origin third-party model.

    KiCad's 3D world negates the footprint Y axis (footprint Y is down-positive,
    the 3D world is Y-up).  Model +Y therefore corresponds to footprint -Y.
    MODEL_Y_SIGN below encodes that; it is what makes the 0.23 mm case offset
    land on the correct side.  See VERIFICATION at the bottom of this file.

STYLE RULES OBEYED (docs/playbook/EE_PROJECT_BOOTSTRAP.md, CLAUDE.md)
    stdlib only, runs on any Python 3 (no pcbnew, no numpy) - it writes text.
    zero-arg, headless, deterministic (fixed timestamp, no uuid4, no time.time).
    Carries its own acceptance check; exit 0 ok / 1 verification failed /
    2 structural failure / 3 legibility failure.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "lib", "iseg.3dshapes")
STEP_PATH = os.path.join(OUT_DIR, "iseg_APS_THT.step")
WRL_PATH = os.path.join(OUT_DIR, "iseg_APS_THT.wrl")

# Fixed so the output is byte-identical on every run (idempotence rule).
FIXED_TIMESTAMP = "2024-08-20T00:00:00"
DOC_CITE = "iseg APS series technical documentation v2.5, 2024-08-20"

# ---------------------------------------------------------------------------
# 1. Datasheet dimensions, in the datasheet's own bottom-view frame:
#    pin 1 at the origin, +x toward pin 7, +y toward pin 5.
# ---------------------------------------------------------------------------
BODY_L = 39.6         # long axis  (x)
BODY_W = 15.7         # short axis (y)
BODY_H = 11.0         # height     (z), case underside at z = 0
PIN_SQ = 0.64         # pin cross-section, square
PIN_LEN = 2.2         # pin length below the case
PIN_PITCH = 2.54
PIN_COL_SPAN = 34.8   # 1..5 column to 6/7 column
PIN_ROW_SPAN = 10.16  # pin 1 to pin 5

EDGE_BEYOND_15_COL = 1.8    # case edge past the pin 1..5 column
EDGE_BEYOND_PIN5 = 3.0      # case edge past pin 5
# derived, must be self-consistent with BODY_L / BODY_W:
EDGE_BEYOND_67_COL = BODY_L - EDGE_BEYOND_15_COL - PIN_COL_SPAN     # 3.0
EDGE_BEYOND_PIN1 = BODY_W - EDGE_BEYOND_PIN5 - PIN_ROW_SPAN         # 2.54

# pin 1..7 centres in the datasheet frame
PINS_DS = [
    (1, 0.0, 0.0),                       # +VIN
    (2, 0.0, 1 * PIN_PITCH),             # VSET
    (3, 0.0, 2 * PIN_PITCH),             # GND
    (4, 0.0, 3 * PIN_PITCH),             # /ON  (active-low enable)
    (5, 0.0, 4 * PIN_PITCH),             # VMON
    (6, PIN_COL_SPAN, PIN_ROW_SPAN),     # HV
    (7, PIN_COL_SPAN, 0.0),              # GND
]

# centre of the pin bounding rectangle, in the datasheet frame
PIN_CX = PIN_COL_SPAN / 2.0     # 17.4
PIN_CY = PIN_ROW_SPAN / 2.0     # 5.08

# KiCad 3D world is Y-up; footprint Y is down-positive.  Model +Y == footprint -Y.
MODEL_Y_SIGN = -1.0

# Colours (linear RGB 0..1)
COLOUR_CASE = (0.28, 0.29, 0.31)     # dark grey, steel case
COLOUR_PIN = (0.85, 0.68, 0.26)      # gold

VRML_UNITS_PER_MM = 1.0 / 2.54       # KiCad VRML unit == 0.1 inch


def _to_model(x_ds, y_ds):
    """Datasheet frame -> model frame (origin = pin bbox centre, KiCad Y-up)."""
    return (x_ds - PIN_CX, MODEL_Y_SIGN * (y_ds - PIN_CY))


def build_boxes():
    """Return [(name, colour, (x0,y0,z0), (x1,y1,z1)), ...] in the model frame."""
    boxes = []

    bx0_ds = -EDGE_BEYOND_15_COL
    bx1_ds = bx0_ds + BODY_L
    by0_ds = -EDGE_BEYOND_PIN1
    by1_ds = by0_ds + BODY_W
    (mx0, my0) = _to_model(bx0_ds, by0_ds)
    (mx1, my1) = _to_model(bx1_ds, by1_ds)
    boxes.append((
        "case",
        COLOUR_CASE,
        (min(mx0, mx1), min(my0, my1), 0.0),
        (max(mx0, mx1), max(my0, my1), BODY_H),
    ))

    h = PIN_SQ / 2.0
    for num, px_ds, py_ds in PINS_DS:
        cx, cy = _to_model(px_ds, py_ds)
        boxes.append((
            "pin%d" % num,
            COLOUR_PIN,
            (cx - h, cy - h, -PIN_LEN),
            (cx + h, cy + h, 0.0),
        ))
    return boxes


# ---------------------------------------------------------------------------
# 2. Box topology.  Loops are ordered counter-clockwise seen from OUTSIDE, i.e.
#    the right-hand-rule normal of the traversal equals the outward normal.
#    Corner key is (i, j, k) selecting lo/hi on x, y, z.
# ---------------------------------------------------------------------------
FACES = [
    # (outward normal, axis-x ref dir, loop of corner keys)
    ((-1, 0, 0), (0, 0, 1), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
    ((1, 0, 0), (0, 1, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
    ((0, -1, 0), (1, 0, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    ((0, 1, 0), (0, 0, 1), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    ((0, 0, -1), (0, 1, 0), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]),
    ((0, 0, 1), (1, 0, 0), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
]


def _corner(lo, hi, key):
    return (lo[0] if key[0] == 0 else hi[0],
            lo[1] if key[1] == 0 else hi[1],
            lo[2] if key[2] == 0 else hi[2])


# ---------------------------------------------------------------------------
# 3. STEP writer
# ---------------------------------------------------------------------------
def _r(v):
    """STEP real literal: must contain a '.'."""
    s = "%.6f" % (v + 0.0)
    if "." in s:
        s = s.rstrip("0")
        if s.endswith("."):
            pass
    if s in ("-0.", "-0"):
        s = "0."
    return s


class StepFile(object):
    def __init__(self):
        self._next = 1
        self._lines = {}
        self._pt = {}
        self._dir = {}

    def new(self):
        i = self._next
        self._next += 1
        return i

    def put(self, i, text):
        self._lines[i] = text
        return i

    def add(self, text):
        return self.put(self.new(), text)

    def point(self, xyz):
        key = tuple(round(v, 7) for v in xyz)
        if key not in self._pt:
            self._pt[key] = self.add("CARTESIAN_POINT('',(%s,%s,%s))"
                                     % (_r(key[0]), _r(key[1]), _r(key[2])))
        return self._pt[key]

    def direction(self, xyz):
        key = tuple(round(float(v), 7) for v in xyz)
        if key not in self._dir:
            self._dir[key] = self.add("DIRECTION('',(%s,%s,%s))"
                                      % (_r(key[0]), _r(key[1]), _r(key[2])))
        return self._dir[key]

    def axis2(self, origin, axis, refdir):
        return self.add("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)"
                        % (self.point(origin), self.direction(axis),
                           self.direction(refdir)))

    def render(self, header_lines):
        out = ["ISO-10303-21;", "HEADER;"]
        out.extend(header_lines)
        out.append("ENDSEC;")
        out.append("DATA;")
        for i in sorted(self._lines):
            out.append("#%d = %s;" % (i, self._lines[i]))
        out.append("ENDSEC;")
        out.append("END-ISO-10303-21;")
        return "\n".join(out) + "\n"


def _solid_brep(sf, lo, hi, name):
    """Emit one MANIFOLD_SOLID_BREP box, return its entity id."""
    verts = {}
    for key in [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)]:
        p = _corner(lo, hi, key)
        verts[key] = sf.add("VERTEX_POINT('',#%d)" % sf.point(p))

    edges = {}

    def edge(ka, kb):
        """EDGE_CURVE from corner ka to kb; returns (id, sense) for traversal."""
        if (ka, kb) in edges:
            return edges[(ka, kb)], ".T."
        if (kb, ka) in edges:
            return edges[(kb, ka)], ".F."
        pa = _corner(lo, hi, ka)
        pb = _corner(lo, hi, kb)
        d = [pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]]
        ln = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5
        if ln <= 0.0:
            raise ValueError("degenerate edge in %s" % name)
        u = [c / ln for c in d]
        vec = sf.add("VECTOR('',#%d,%s)" % (sf.direction(u), _r(ln)))
        line = sf.add("LINE('',#%d,#%d)" % (sf.point(pa), vec))
        eid = sf.add("EDGE_CURVE('',#%d,#%d,#%d,.T.)"
                     % (verts[ka], verts[kb], line))
        edges[(ka, kb)] = eid
        return eid, ".T."

    face_ids = []
    for normal, refdir, loop in FACES:
        oriented = []
        for n in range(4):
            ka = loop[n]
            kb = loop[(n + 1) % 4]
            eid, sense = edge(ka, kb)
            oriented.append(sf.add("ORIENTED_EDGE('',*,*,#%d,%s)" % (eid, sense)))
        el = sf.add("EDGE_LOOP('',(%s))"
                    % ",".join("#%d" % o for o in oriented))
        fb = sf.add("FACE_OUTER_BOUND('',#%d,.T.)" % el)
        plane_org = _corner(lo, hi, loop[0])
        ax = sf.axis2(plane_org, normal, refdir)
        pl = sf.add("PLANE('',#%d)" % ax)
        face_ids.append(sf.add("ADVANCED_FACE('',(#%d),#%d,.T.)" % (fb, pl)))

    shell = sf.add("CLOSED_SHELL('',(%s))"
                   % ",".join("#%d" % f for f in face_ids))
    return sf.add("MANIFOLD_SOLID_BREP('%s',#%d)" % (name, shell))


def write_step(boxes, path):
    sf = StepFile()
    # fixed low ids for the product/definition chain
    for _ in range(11):
        sf.new()
    sf.put(1, "APPLICATION_PROTOCOL_DEFINITION('international standard',"
              "'automotive_design',2000,#2)")
    sf.put(2, "APPLICATION_CONTEXT('core data for automotive mechanical "
              "design processes')")
    sf.put(3, "SHAPE_DEFINITION_REPRESENTATION(#4,#10)")
    sf.put(4, "PRODUCT_DEFINITION_SHAPE('','',#5)")
    sf.put(5, "PRODUCT_DEFINITION('design','',#6,#9)")
    sf.put(6, "PRODUCT_DEFINITION_FORMATION('','',#7)")
    sf.put(7, "PRODUCT('iseg_APS_THT','iseg_APS_THT','',(#8))")
    sf.put(8, "PRODUCT_CONTEXT('',#2,'mechanical')")
    sf.put(9, "PRODUCT_DEFINITION_CONTEXT('part definition',#2,'design')")
    sf.put(11, "AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)"
               % (sf.point((0.0, 0.0, 0.0)),
                  sf.direction((0.0, 0.0, 1.0)),
                  sf.direction((1.0, 0.0, 0.0))))

    solids = []
    for name, _colour, lo, hi in boxes:
        solids.append(_solid_brep(sf, lo, hi, name))

    ctx = sf.new()
    sf.put(10, "ADVANCED_BREP_SHAPE_REPRESENTATION('iseg_APS_THT',(#11,%s),#%d)"
               % (",".join("#%d" % s for s in solids), ctx))

    u_len = sf.add("( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )")
    u_ang = sf.add("( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) )")
    u_sol = sf.add("( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() )")
    unc = sf.add("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-007),#%d,"
                 "'distance_accuracy_value','confusion accuracy')" % u_len)
    sf.put(ctx, "( GEOMETRIC_REPRESENTATION_CONTEXT(3) "
                "GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#%d)) "
                "GLOBAL_UNIT_ASSIGNED_CONTEXT((#%d,#%d,#%d)) "
                "REPRESENTATION_CONTEXT('Context #1',"
                "'3D Context with UNIT and UNCERTAINTY') )"
                % (unc, u_len, u_ang, u_sol))
    sf.add("PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#7))")

    # ---- colour: one STYLED_ITEM per solid ----
    styled = []
    colour_cache = {}
    for (name, colour, _lo, _hi), sid in zip(boxes, solids):
        key = tuple(round(c, 6) for c in colour)
        if key not in colour_cache:
            col = sf.add("COLOUR_RGB('',%s,%s,%s)"
                         % (_r(key[0]), _r(key[1]), _r(key[2])))
            fac = sf.add("FILL_AREA_STYLE_COLOUR('',#%d)" % col)
            fas = sf.add("FILL_AREA_STYLE('',(#%d))" % fac)
            ssf = sf.add("SURFACE_STYLE_FILL_AREA(#%d)" % fas)
            sss = sf.add("SURFACE_SIDE_STYLE('',(#%d))" % ssf)
            ssu = sf.add("SURFACE_STYLE_USAGE(.BOTH.,#%d)" % sss)
            psa = sf.add("PRESENTATION_STYLE_ASSIGNMENT((#%d))" % ssu)
            colour_cache[key] = psa
        styled.append(sf.add("STYLED_ITEM('color',(#%d),#%d)"
                             % (colour_cache[key], sid)))
    sf.add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(%s),#%d)"
           % (",".join("#%d" % s for s in styled), ctx))

    header = [
        "FILE_DESCRIPTION(('iseg APS series programmable HV module, 7-pin THT; "
        "case %g x %g x %g mm; origin at the pin-array centre'),'2;1');"
        % (BODY_L, BODY_W, BODY_H),
        "FILE_NAME('iseg_APS_THT.step','%s',"
        "('iseg-programmable-supply hardware/hvctl/gen_3d_model.py'),"
        "('Yale University'),"
        "'gen_3d_model.py (stdlib Python 3)','gen_3d_model.py',"
        "'geometry from %s');" % (FIXED_TIMESTAMP, DOC_CITE),
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));",
    ]
    text = sf.render(header)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text


# ---------------------------------------------------------------------------
# 4. VRML2 writer.  KiCad reads VRML in units of 0.1 inch.
# ---------------------------------------------------------------------------
def write_wrl(boxes, path):
    s = VRML_UNITS_PER_MM
    out = ["#VRML V2.0 utf8",
           "# iseg APS series programmable HV module, 7-pin THT",
           "# geometry from %s" % DOC_CITE,
           "# generated by hardware/hvctl/gen_3d_model.py -- do not hand-edit",
           "# units: 0.1 inch (KiCad VRML convention); millimetres / 2.54",
           ""]
    for name, colour, lo, hi in boxes:
        pts = []
        keys = []
        for key in [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)]:
            keys.append(key)
            p = _corner(lo, hi, key)
            pts.append((p[0] * s, p[1] * s, p[2] * s))
        kidx = dict((k, n) for n, k in enumerate(keys))
        idx = []
        for _normal, _refdir, loop in FACES:
            idx.append(",".join(str(kidx[k]) for k in loop) + ",-1")
        out.append("Shape {")
        out.append("  # %s" % name)
        out.append("  appearance Appearance { material Material {")
        out.append("    diffuseColor %.4f %.4f %.4f" % colour)
        out.append("    specularColor %.4f %.4f %.4f"
                   % tuple(min(1.0, c * 1.6 + 0.10) for c in colour))
        out.append("    emissiveColor 0.0 0.0 0.0")
        out.append("    ambientIntensity 0.30")
        out.append("    shininess 0.45")
        out.append("    transparency 0.0")
        out.append("  } }")
        out.append("  geometry IndexedFaceSet {")
        out.append("    solid TRUE")
        out.append("    creaseAngle 0.0")
        out.append("    coord Coordinate { point [")
        out.append("      " + ", ".join("%.6f %.6f %.6f" % p for p in pts))
        out.append("    ] }")
        out.append("    coordIndex [ " + ", ".join(idx) + " ]")
        out.append("  }")
        out.append("}")
        out.append("")
    text = "\n".join(out) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text


# ---------------------------------------------------------------------------
# 5. ACCEPTANCE CHECK
#
#    Deliberately re-reads the files from disk and re-derives everything with a
#    parser that shares no code with the writers, then compares against the
#    datasheet numbers spelled out again below (independent transcription from
#    the manual, not a reference to the constants above).
# ---------------------------------------------------------------------------

# Independent transcription -- iseg APS technical documentation v2.5, Fig. 1 & Table 4.
EXPECT = {
    "body_l": 39.6,
    "body_w": 15.7,
    "body_h": 11.0,
    "pin_sq": 0.64,
    "pin_len": 2.2,
    "pitch": 2.54,
    "col_span": 34.8,
    "row_span": 10.16,
    # case centre relative to the pin-rectangle centre, in the MODEL frame.
    # long axis: (3.0 - 1.8)/2 = +0.6 toward the 6/7 column
    # short axis: (3.0 - 2.54)/2 = 0.23 toward pin 5; pin 5 is at model -Y
    #             (MODEL_Y_SIGN = -1), so the case centre sits at -0.23.
    "case_dx": 0.6,
    "case_dy": -0.23,
    "n_solids": 8,
    "n_pins": 7,
}
TOL = 1e-4


class Fail(Exception):
    def __init__(self, msg, code=1):
        Exception.__init__(self, msg)
        self.code = code


def _near(a, b, tol=TOL):
    return abs(a - b) <= tol


def parse_step_solids(text):
    """Independent parser: -> [(name, [8 corner points], V, E, F, volume)]"""
    ents = {}
    for m in re.finditer(r"#(\d+)\s*=\s*(.*?);\s*(?=#|ENDSEC)", text, re.S):
        ents[int(m.group(1))] = " ".join(m.group(2).split())

    def refs(s):
        return [int(x) for x in re.findall(r"#(\d+)", s)]

    pts = {}
    for i, s in ents.items():
        m = re.match(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)\s*\)$", s)
        if m:
            pts[i] = tuple(float(v) for v in m.group(1).split(","))

    vpt = {}
    for i, s in ents.items():
        m = re.match(r"VERTEX_POINT\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*\)$", s)
        if m:
            vpt[i] = pts[int(m.group(1))]

    ecur = {}
    for i, s in ents.items():
        m = re.match(r"EDGE_CURVE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*#(\d+)\s*,"
                     r"\s*#(\d+)\s*,\s*\.([TF])\.\s*\)$", s)
        if m:
            ecur[i] = (int(m.group(1)), int(m.group(2)), m.group(4))

    oedge = {}
    for i, s in ents.items():
        m = re.match(r"ORIENTED_EDGE\s*\(\s*'[^']*'\s*,\s*\*\s*,\s*\*\s*,"
                     r"\s*#(\d+)\s*,\s*\.([TF])\.\s*\)$", s)
        if m:
            oedge[i] = (int(m.group(1)), m.group(2))

    out = []
    for i, s in ents.items():
        m = re.match(r"MANIFOLD_SOLID_BREP\s*\(\s*'([^']*)'\s*,\s*#(\d+)\s*\)$", s)
        if not m:
            continue
        name = m.group(1)
        shell = ents[int(m.group(2))]
        if not shell.startswith("CLOSED_SHELL"):
            raise Fail("solid %s is not bounded by a CLOSED_SHELL" % name, 2)
        faces = refs(shell)
        verts = set()
        edges = set()
        loops = []
        for fid in faces:
            fs = ents[fid]
            if not fs.startswith("ADVANCED_FACE"):
                raise Fail("solid %s: face #%d is %s, expected ADVANCED_FACE"
                           % (name, fid, fs.split("(")[0]), 2)
            frefs = refs(fs)
            bound = ents[frefs[0]]
            surf = ents[frefs[1]]
            if not surf.startswith("PLANE"):
                raise Fail("solid %s: face geometry %s is not a PLANE"
                           % (name, surf.split("(")[0]), 2)
            if not bound.startswith("FACE_OUTER_BOUND"):
                raise Fail("solid %s: bound is %s" % (name, bound.split("(")[0]), 2)
            eloop = ents[refs(bound)[0]]
            poly = []
            for oid in refs(eloop):
                ecid, sense = oedge[oid]
                v1, v2, _ = ecur[ecid]
                edges.add(ecid)
                a, b = (v1, v2) if sense == "T" else (v2, v1)
                poly.append(vpt[a])
                verts.add(a)
                verts.add(b)
            loops.append(poly)
        vol = 0.0
        for poly in loops:
            p0 = poly[0]
            for n in range(1, len(poly) - 1):
                p1, p2 = poly[n], poly[n + 1]
                a = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                b = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
                cr = (a[1] * b[2] - a[2] * b[1],
                      a[2] * b[0] - a[0] * b[2],
                      a[0] * b[1] - a[1] * b[0])
                vol += (p0[0] * cr[0] + p0[1] * cr[1] + p0[2] * cr[2]) / 6.0
        corners = sorted(set(vpt[v] for v in verts))
        out.append((name, corners, len(verts), len(edges), len(faces), vol))
    return out


def parse_wrl_boxes(text):
    """Independent parser: -> [(diffuse, [pts in mm], n_faces)]"""
    boxes = []
    for m in re.finditer(r"Shape\s*\{(.*?)\n\}", text, re.S):
        blk = m.group(1)
        dm = re.search(r"diffuseColor\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", blk)
        pm = re.search(r"point\s*\[(.*?)\]", blk, re.S)
        im = re.search(r"coordIndex\s*\[(.*?)\]", blk, re.S)
        if not (dm and pm and im):
            raise Fail("VRML Shape block is missing colour/point/coordIndex", 2)
        diffuse = tuple(float(dm.group(n)) for n in (1, 2, 3))
        raw = [float(v) for v in pm.group(1).replace(",", " ").split()]
        if len(raw) % 3:
            raise Fail("VRML point list is not a multiple of 3", 2)
        pts = [(raw[n] * 2.54, raw[n + 1] * 2.54, raw[n + 2] * 2.54)
               for n in range(0, len(raw), 3)]
        nf = im.group(1).count("-1")
        boxes.append((diffuse, pts, nf))
    return boxes


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def check(verbose=True):
    def say(msg):
        if verbose:
            print(msg)

    for p in (STEP_PATH, WRL_PATH):
        if not os.path.isfile(p):
            raise Fail("missing output %s" % p, 2)

    step_txt = open(STEP_PATH, encoding="utf-8").read()
    wrl_txt = open(WRL_PATH, encoding="utf-8").read()

    if not step_txt.startswith("ISO-10303-21;"):
        raise Fail("STEP does not start with ISO-10303-21;", 2)
    if "END-ISO-10303-21;" not in step_txt:
        raise Fail("STEP is not terminated", 2)
    if "AUTOMOTIVE_DESIGN { 1 0 10303 214" not in step_txt:
        raise Fail("STEP schema is not AP214 AUTOMOTIVE_DESIGN", 2)
    if "SI_UNIT(.MILLI.,.METRE.)" not in step_txt:
        raise Fail("STEP length unit is not millimetre", 1)
    if "FACETED_BREP" in step_txt:
        raise Fail("emitted FACETED_BREP but the file claims ADVANCED_BREP", 2)
    if not wrl_txt.startswith("#VRML V2.0 utf8"):
        raise Fail("WRL is not VRML2", 2)

    solids = parse_step_solids(step_txt)
    say("STEP: %d MANIFOLD_SOLID_BREPs parsed back out of the written file"
        % len(solids))
    if len(solids) != EXPECT["n_solids"]:
        raise Fail("expected %d solids, found %d"
                   % (EXPECT["n_solids"], len(solids)), 1)

    total_vol = 0.0
    case = None
    pins = []
    for name, corners, nv, ne, nf, vol in solids:
        if (nv, ne, nf) != (8, 12, 6):
            raise Fail("%s: V,E,F = %d,%d,%d, expected 8,12,6"
                       % (name, nv, ne, nf), 2)
        if nv - ne + nf != 2:
            raise Fail("%s: Euler characteristic != 2" % name, 2)
        if vol <= 0.0:
            raise Fail("%s: outward-normal volume is %.4f <= 0, the shell is "
                       "inside-out" % (name, vol), 2)
        total_vol += vol
        if name == "case":
            case = (corners, vol)
        elif name.startswith("pin"):
            pins.append((name, corners, vol))

    if case is None:
        raise Fail("no solid named 'case'", 2)
    if len(pins) != EXPECT["n_pins"]:
        raise Fail("expected %d pins, found %d" % (EXPECT["n_pins"], len(pins)), 1)

    # ---- case dimensions ----
    cx0, cx1, cy0, cy1, cz0, cz1 = bbox(case[0])
    for got, want, label in ((cx1 - cx0, EXPECT["body_l"], "case length"),
                             (cy1 - cy0, EXPECT["body_w"], "case width"),
                             (cz1 - cz0, EXPECT["body_h"], "case height")):
        if not _near(got, want):
            raise Fail("%s = %.4f mm, datasheet %.4f mm" % (label, got, want), 1)
    say("STEP: case %.3f x %.3f x %.3f mm  [datasheet 39.6 x 15.7 x 11]"
        % (cx1 - cx0, cy1 - cy0, cz1 - cz0))
    if not _near(cz0, 0.0):
        raise Fail("case underside at z=%.4f, must be 0 (board surface)" % cz0, 1)

    # ---- pin grid ----
    pin_c = []
    for name, corners, _v in pins:
        px0, px1, py0, py1, pz0, pz1 = bbox(corners)
        if not (_near(px1 - px0, EXPECT["pin_sq"]) and
                _near(py1 - py0, EXPECT["pin_sq"])):
            raise Fail("%s cross-section %.4f x %.4f, datasheet %.2f square"
                       % (name, px1 - px0, py1 - py0, EXPECT["pin_sq"]), 1)
        if not _near(pz1 - pz0, EXPECT["pin_len"]):
            raise Fail("%s length %.4f mm, datasheet %.2f"
                       % (name, pz1 - pz0, EXPECT["pin_len"]), 1)
        if not (_near(pz1, 0.0) and _near(pz0, -EXPECT["pin_len"])):
            raise Fail("%s spans z %.4f..%.4f, expected -%.2f..0"
                       % (name, pz0, pz1, EXPECT["pin_len"]), 1)
        pin_c.append(((px0 + px1) / 2.0, (py0 + py1) / 2.0))

    xs = sorted(set(round(c[0], 4) for c in pin_c))
    ys = sorted(set(round(c[1], 4) for c in pin_c))
    if len(xs) != 2:
        raise Fail("pins occupy %d distinct x columns, expected 2" % len(xs), 1)
    if not _near(xs[1] - xs[0], EXPECT["col_span"]):
        raise Fail("column separation %.4f mm, datasheet %.2f"
                   % (xs[1] - xs[0], EXPECT["col_span"]), 1)
    col_lo = [c for c in pin_c if _near(c[0], xs[0])]
    col_hi = [c for c in pin_c if _near(c[0], xs[1])]
    if len(col_lo) != 5 or len(col_hi) != 2:
        raise Fail("columns hold %d and %d pins, expected 5 and 2"
                   % (len(col_lo), len(col_hi)), 1)
    lo_y = sorted(c[1] for c in col_lo)
    for n in range(4):
        if not _near(lo_y[n + 1] - lo_y[n], EXPECT["pitch"]):
            raise Fail("pin pitch %.4f mm, datasheet %.2f"
                       % (lo_y[n + 1] - lo_y[n], EXPECT["pitch"]), 1)
    if not _near(lo_y[-1] - lo_y[0], EXPECT["row_span"]):
        raise Fail("pin1..pin5 span %.4f mm, datasheet %.2f"
                   % (lo_y[-1] - lo_y[0], EXPECT["row_span"]), 1)
    hi_y = sorted(c[1] for c in col_hi)
    if not (_near(hi_y[0], lo_y[0]) and _near(hi_y[-1], lo_y[-1])):
        raise Fail("pins 6/7 are not in line with pins 5/1", 1)
    say("STEP: 7 pins, 2 columns %.2f mm apart, 5 at %.2f mm pitch spanning "
        "%.2f mm" % (xs[1] - xs[0], EXPECT["pitch"], lo_y[-1] - lo_y[0]))

    # ---- ORIGIN: the whole point of this file ----
    ox = (xs[0] + xs[1]) / 2.0
    oy = (min(lo_y) + max(lo_y)) / 2.0
    if not (_near(ox, 0.0) and _near(oy, 0.0)):
        raise Fail("pin-array centre is at (%.4f, %.4f), must be (0,0) so the "
                   "footprint can use (offset 0 0 0)" % (ox, oy), 1)
    say("STEP: pin-array centre at (0.000, 0.000) -> footprint offset 0 0 0")

    # ---- the asymmetry that third-party models get wrong ----
    ccx = (cx0 + cx1) / 2.0
    ccy = (cy0 + cy1) / 2.0
    if not _near(ccx, EXPECT["case_dx"], 1e-3):
        raise Fail("case centre x offset %.4f mm, datasheet %.2f (case is NOT "
                   "centred on the pin rectangle)" % (ccx, EXPECT["case_dx"]), 1)
    if not _near(ccy, EXPECT["case_dy"], 1e-3):
        raise Fail("case centre y offset %.4f mm, datasheet %.2f"
                   % (ccy, EXPECT["case_dy"]), 1)
    say("STEP: case centre offset from pin centre = (%+.3f, %+.3f) mm "
        "[datasheet %+.2f, %+.2f -- the case is deliberately not centred]"
        % (ccx, ccy, EXPECT["case_dx"], EXPECT["case_dy"]))

    want_vol = (EXPECT["body_l"] * EXPECT["body_w"] * EXPECT["body_h"]
                + EXPECT["n_pins"] * EXPECT["pin_sq"] ** 2 * EXPECT["pin_len"])
    if not _near(total_vol, want_vol, 1e-3):
        raise Fail("summed outward-normal volume %.4f mm3, expected %.4f"
                   % (total_vol, want_vol), 2)
    say("STEP: closed-shell volume by divergence theorem = %.3f mm3 "
        "(expected %.3f) -> all 8 shells are closed and outward-facing"
        % (total_vol, want_vol))

    # ---- WRL must agree with the STEP, box for box ----
    wboxes = parse_wrl_boxes(wrl_txt)
    if len(wboxes) != EXPECT["n_solids"]:
        raise Fail("WRL has %d Shapes, STEP has %d solids"
                   % (len(wboxes), EXPECT["n_solids"]), 1)
    wall = []
    for diffuse, pts, nf in wboxes:
        if len(pts) != 8:
            raise Fail("WRL Shape has %d points, expected 8" % len(pts), 2)
        if nf != 6:
            raise Fail("WRL Shape has %d faces, expected 6" % nf, 2)
        wall.extend(pts)
    sall = []
    for _n, corners, _v, _e, _f, _vol in solids:
        sall.extend(corners)
    wb = bbox(wall)
    sb = bbox(sall)
    for n, label in enumerate(("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")):
        if not _near(wb[n], sb[n], 1e-3):
            raise Fail("WRL %s = %.4f mm, STEP %s = %.4f mm (unit scale wrong? "
                       "KiCad VRML unit is 0.1 inch)" % (label, wb[n], label, sb[n]), 1)
    say("WRL: bbox x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f mm "
        "(after x2.54) -- identical to the STEP" % wb)

    dcolours = set(tuple(round(c, 4) for c in d) for d, _p, _f in wboxes)
    if len(dcolours) != 2:
        raise Fail("WRL uses %d diffuse colours, expected 2 (case + pins)"
                   % len(dcolours), 3)
    say("WRL: 2 materials -- case %s, pins %s"
        % (COLOUR_CASE, COLOUR_PIN))

    say("")
    say("ACCEPTANCE: PASS")
    return 0


def main():
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        boxes = build_boxes()
        write_step(boxes, STEP_PATH)
        write_wrl(boxes, WRL_PATH)
        print("wrote %s (%d bytes)" % (STEP_PATH, os.path.getsize(STEP_PATH)))
        print("wrote %s (%d bytes)" % (WRL_PATH, os.path.getsize(WRL_PATH)))
        print("")
        return check()
    except Fail as e:
        print("FAIL: %s" % e, file=sys.stderr)
        return e.code
    except Exception as e:  # noqa: BLE001 - structural failure
        import traceback
        traceback.print_exc()
        print("FAIL (structural): %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------------
# VERIFICATION NOTE -- what the acceptance check above CANNOT see
#
#   It proves the two files contain the datasheet geometry, that every shell is
#   closed and outward-facing, and that the pin-array centre is the origin.
#   It does NOT prove KiCad can load them, and it does NOT prove MODEL_Y_SIGN
#   is right -- both of those are properties of KiCad, not of the file.
#   3D model paths fail SILENTLY in KiCad: a bad path or an unparsable file
#   just means the part is missing from the render, with no warning anywhere.
#   The only instruments that see that are:
#       kicad-cli pcb render      -> look at the PNG
#       kicad-cli pcb export step -> re-measure the placed model numerically
#   Run both against a board that places the footprint.  See the session notes.
# ---------------------------------------------------------------------------
