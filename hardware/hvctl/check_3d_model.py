#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_3d_model.py -- prove the iseg APS 3D model is actually there, actually
the right size, and actually lands on the pads, INSIDE KiCad.

    MUST run under PY_KICAD:
      "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/check_3d_model.py

WHY THIS EXISTS
    3D model paths fail SILENTLY in KiCad.  A typo in the filename, a model in
    units KiCad does not expect, a model whose origin is a corner instead of
    the pin centroid -- none of these produce a warning anywhere.  The part is
    simply absent from the render, or silently 2.54x wrong, or silently 0.23 mm
    out of position.  gen_3d_model.py's own acceptance check reads the files it
    wrote; it cannot see any of that, because all of it is a property of KiCad,
    not of the file.

WHAT IT DOES
    1. Builds a throwaway board (pcbnew) carrying one 7-pin iseg footprint per
       candidate model: our generated .step, our generated .wrl, and -- if it is
       still present -- the third-party reference .step with the offset the
       Phys439 alpha-lab footprint used for it.
    2. `kicad-cli pcb render` -> PNGs.  LOOK AT THEM.  That render is the check.
    3. `kicad-cli pcb export vrml --units mm` -> one file in which every model,
       .step or .wrl, has been resolved to explicit world-space triangles.
       Measures each model against the pad grid of the footprint it belongs to.
       This is the numeric half; it is independent of the generator because the
       numbers come out of KiCad's own model loader.

EXIT CODES
    0 all candidates that were expected to pass, passed
    1 a model loaded but is dimensionally or positionally wrong
    2 structural failure (a model did not load at all / tooling missing)
    3 legibility failure (render produced no image to look at)
"""

import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "outputs", "model3d")
KICAD_CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

GEN_STEP = os.path.join(HERE, "lib", "iseg.3dshapes", "iseg_APS_THT.step")
GEN_WRL = os.path.join(HERE, "lib", "iseg.3dshapes", "iseg_APS_THT.wrl")
REF_STEP = os.path.join(REPO, "references", "Phys439-alpha-lab", "circuit",
                        "alpha-shield-pcb", "alpha-shield.3dshapes",
                        "ISEG_HV_MODULE.step")

# the real project footprint, if the footprint generator has produced it yet
PROJECT_FP = (os.path.join(HERE, "lib", "iseg.pretty"), "iseg_APS_THT")

BOARD_PCB = os.path.join(OUT, "model3d_check.kicad_pcb")
BOARD_W, BOARD_H = 70.0, 140.0

# ---- datasheet, iseg APS series technical documentation v2.5, 2024-08-20 ----
BODY_L, BODY_W, BODY_H = 39.6, 15.7, 11.0
PIN_PITCH, COL_SPAN, ROW_SPAN = 2.54, 34.8, 10.16
EDGE_PAST_15_COL = 1.8      # case edge past the pin 1..5 column
EDGE_PAST_67_COL = 3.0      # case edge past the pin 6/7 column
EDGE_PAST_PIN1 = 2.54       # case edge past pin 1
EDGE_PAST_PIN5 = 3.0        # case edge past pin 5

# ref, y on the board, model path, KiCad 3D offset, expect-pass
CANDIDATES = [
    ("U1", 20.0, GEN_STEP, (0.0, 0.0, 0.0), True,
     "generated STEP, origin = pin centroid"),
    ("U2", 45.0, GEN_WRL, (0.0, 0.0, 0.0), True,
     "generated VRML, origin = pin centroid"),
    ("U3", 70.0, REF_STEP, (-19.2278, -7.62, 0.0), False,
     "third-party STEP + the offset the Phys439 footprint used"),
    ("U4", 95.0, REF_STEP, (-19.2, -7.85, 0.0), False,
     "third-party STEP + the BEST POSSIBLE offset (its own pin centroid): "
     "shows the residual error is intrinsic to the model, not the offset"),
    ("U5", 120.0, GEN_STEP, (0.0, 0.0, 0.0), True,
     "generated STEP on the REAL project footprint lib/iseg.pretty",
     PROJECT_FP),
]

TOL_DIM = 0.02      # mm, on a dimension
TOL_POS = 0.05      # mm, pin vs pad concentricity


class Fail(Exception):
    def __init__(self, msg, code=2):
        Exception.__init__(self, msg)
        self.code = code


# ---------------------------------------------------------------------------
# board construction
# ---------------------------------------------------------------------------
def _mm(v):
    return pcbnew.FromMM(v)


def _v2(x, y):
    return pcbnew.VECTOR2I(_mm(x), _mm(y))


def pad_grid(cx, cy):
    """Pad centres for a footprint whose origin is the pin-array centre.
    Footprint +Y is down; pin 1 is at -Y, pin 5 at +Y."""
    x0 = cx - COL_SPAN / 2.0
    x1 = cx + COL_SPAN / 2.0
    y0 = cy - ROW_SPAN / 2.0
    return {1: (x0, y0), 2: (x0, y0 + PIN_PITCH), 3: (x0, y0 + 2 * PIN_PITCH),
            4: (x0, y0 + 3 * PIN_PITCH), 5: (x0, y0 + 4 * PIN_PITCH),
            6: (x1, y0 + 4 * PIN_PITCH), 7: (x1, y0)}


def build_board(candidates):
    board = pcbnew.BOARD()
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(_v2(*corners[i]))
        seg.SetEnd(_v2(*corners[(i + 1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(_mm(0.1))
        board.Add(seg)

    for cand in candidates:
        ref, y, path, off = cand[0], cand[1], cand[2], cand[3]
        libfp = cand[6] if len(cand) > 6 else None
        if libfp is not None:
            fp = pcbnew.FootprintLoad(libfp[0], libfp[1])
            if fp is None:
                raise Fail("could not load %s from %s" % (libfp[1], libfp[0]), 2)
            fp.SetReference(ref)
            fp.SetPosition(_v2(BOARD_W / 2.0, y))
            fp.Models().clear()
        else:
            fp = pcbnew.FOOTPRINT(board)
            fp.SetFPID(pcbnew.LIB_ID("model3d_check", "ISEG_APS_" + ref))
            fp.SetPosition(_v2(BOARD_W / 2.0, y))
            fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
            fp.SetReference(ref)
            fp.SetValue("ISEG_APS")
            fp.Reference().SetLayer(pcbnew.F_SilkS)
            fp.Value().SetLayer(pcbnew.F_Fab)
            for num, (px, py) in sorted(pad_grid(BOARD_W / 2.0, y).items()):
                pad = pcbnew.PAD(fp)
                pad.SetNumber(str(num))
                pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
                pad.SetShape(pcbnew.PAD_SHAPE_RECT if num == 1
                             else pcbnew.PAD_SHAPE_CIRCLE)
                pad.SetSize(_v2(1.7, 1.7))
                pad.SetDrillSize(_v2(1.1, 1.1))
                pad.SetLayerSet(pad.PTHMask())
                fp.Add(pad)
                pad.SetPosition(_v2(px, py))
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = path.replace("\\", "/")
        m.m_Offset = pcbnew.VECTOR3D(off[0], off[1], off[2])
        m.m_Scale = pcbnew.VECTOR3D(1.0, 1.0, 1.0)
        m.m_Rotation = pcbnew.VECTOR3D(0.0, 0.0, 0.0)
        m.m_Opacity = 1.0
        m.m_Show = True
        fp.Models().push_back(m)
        board.Add(fp)

    board.BuildListOfNets()
    pcbnew.SaveBoard(BOARD_PCB, board)
    thickness = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    return thickness


# ---------------------------------------------------------------------------
# kicad-cli
# ---------------------------------------------------------------------------
def cli(args, what):
    if not os.path.isfile(KICAD_CLI):
        raise Fail("kicad-cli not at %s" % KICAD_CLI, 2)
    p = subprocess.run([KICAD_CLI] + args, capture_output=True, text=True)
    if p.returncode != 0:
        raise Fail("%s failed (rc=%d):\n%s\n%s"
                   % (what, p.returncode, p.stdout[-800:], p.stderr[-800:]), 2)
    return p.stdout


# ---------------------------------------------------------------------------
# VRML world-space reader.  Walks Transform{translation,scale} and collects the
# points of every IndexedFaceSet, resolved into world coordinates.
# ---------------------------------------------------------------------------
def vrml_world_points(path):
    """-> [[(x,y,z), ...], ...] one list per IndexedFaceSet, world space.

    Handles DEF/USE: KiCad emits each distinct 3D model once and instances the
    repeats with `USE`.  A reader that ignores USE silently sees zero geometry
    for the second and later instances -- which looks exactly like a model that
    failed to load.  That bit us once; do not remove it."""
    txt = re.sub(r"#[^\n]*", "", open(path, encoding="utf-8",
                                      errors="replace").read())
    tok = re.findall(r"[\{\}\[\]]|[A-Za-z_][A-Za-z0-9_]*"
                     r"|-?\d+\.?\d*(?:[eE][-+]?\d+)?", txt)
    n = len(tok)
    defs = {}

    def xf(groups, t, s):
        return [[(t[0] + p[0] * s[0], t[1] + p[1] * s[1], t[2] + p[2] * s[2])
                 for p in g] for g in groups]

    def parse_body(i):
        """Parse tokens up to the matching '}'.  Returns
        (index_after, groups_in_this_node_frame, translation, scale)."""
        groups = []
        t = [0.0, 0.0, 0.0]
        s = [1.0, 1.0, 1.0]
        while i < n:
            k = tok[i]
            if k == "}":
                return i + 1, groups, tuple(t), tuple(s)
            if k == "rotation":
                if abs(float(tok[i + 4])) > 1e-9:
                    raise Fail("VRML export contains a rotated Transform; this "
                               "reader handles translation+scale only", 2)
                i += 5
                continue
            if k == "translation":
                t = [float(tok[i + q]) for q in (1, 2, 3)]
                i += 4
                continue
            if k == "scale":
                s = [float(tok[i + q]) for q in (1, 2, 3)]
                i += 4
                continue
            if k == "point":
                j = i + 2
                vals = []
                while tok[j] != "]":
                    vals.append(float(tok[j]))
                    j += 1
                groups.append([(vals[q], vals[q + 1], vals[q + 2])
                               for q in range(0, len(vals) - 2, 3)])
                i = j + 1
                continue
            if k == "coordIndex":
                j = i + 2
                while j < n and tok[j] != "]":
                    j += 1
                i = j + 1
                continue
            if k == "USE":
                groups.extend([list(g) for g in defs.get(tok[i + 1], [])])
                i += 2
                continue
            if k == "DEF":
                name = tok[i + 1]
                # skip the node type token(s) up to '{'
                j = i + 2
                while j < n and tok[j] != "{":
                    j += 1
                j, sub, st, ss = parse_body(j + 1)
                placed = xf(sub, st, ss)
                defs[name] = placed
                groups.extend(placed)
                i = j
                continue
            if k == "{":
                j, sub, st, ss = parse_body(i + 1)
                groups.extend(xf(sub, st, ss))
                i = j
                continue
            i += 1
        return i, groups, tuple(t), tuple(s)

    _, g, t, s = parse_body(0)
    return xf(g, t, s)


def bbox(pts):
    return (min(p[0] for p in pts), max(p[0] for p in pts),
            min(p[1] for p in pts), max(p[1] for p in pts),
            min(p[2] for p in pts), max(p[2] for p in pts))


def cluster_xy(pts, radius):
    """Greedy spatial clustering in XY. -> [(cx, cy, npts)]"""
    out = []
    for p in pts:
        for c in out:
            if abs(p[0] - c[0][0]) <= radius and abs(p[1] - c[0][1]) <= radius:
                c[1].append(p)
                break
        else:
            out.append([p, [p]])
    res = []
    for _seed, members in out:
        b = bbox(members)
        res.append(((b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0, len(members)))
    return res


# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)

    cands = []
    for c in CANDIDATES:
        libfp = c[6] if len(c) > 6 else None
        if not os.path.isfile(c[2]):
            print("SKIP %s: no such model %s" % (c[0], c[2]))
            continue
        if libfp is not None and not os.path.isfile(
                os.path.join(libfp[0], libfp[1] + ".kicad_mod")):
            print("SKIP %s: the project footprint %s/%s.kicad_mod does not "
                  "exist yet" % (c[0], libfp[0], libfp[1]))
            continue
        cands.append(c)
    if not cands:
        raise Fail("no candidate models exist", 2)

    thickness = build_board(cands)
    board_top = thickness / 2.0
    print("board: %.1f x %.1f mm, thickness %.3f mm -> models sit at z=%.3f"
          % (BOARD_W, BOARD_H, thickness, board_top))
    print("wrote %s" % BOARD_PCB)

    # ---- 1. RENDER.  Look at these. ----
    renders = []
    for side, extra, name in (("top", [], "render_top.png"),
                              ("bottom", [], "render_bottom.png"),
                              ("top", ["--perspective", "--rotate", "-40,0,25"],
                               "render_iso.png")):
        dst = os.path.join(OUT, name)
        cli(["pcb", "render", "-o", dst, "--side", side, "--width", "1600",
             "--height", "1600", "--quality", "high", "--background", "opaque"]
            + extra + [BOARD_PCB], "render " + name)
        if not os.path.isfile(dst) or os.path.getsize(dst) < 2000:
            raise Fail("render produced no usable image: %s" % dst, 3)
        renders.append(dst)
        print("rendered %s (%d bytes)" % (dst, os.path.getsize(dst)))

    # ---- 2. VRML export: every model resolved to world-space triangles ----
    wrl = os.path.join(OUT, "board_resolved.wrl")
    cli(["pcb", "export", "vrml", "-f", "--units", "mm",
         "--user-origin", "0x0mm", "-o", wrl, BOARD_PCB], "export vrml")
    groups = vrml_world_points(wrl)
    if not groups:
        raise Fail("VRML export contains no geometry", 2)

    # Self-calibrate the export frame from the board outline itself: the board
    # is pcbnew (0,0)..(W,H), so whichever sign the outline comes back with is
    # the sign KiCad uses.  No assumption about the Y convention is baked in.
    allp = [p for g in groups for p in g]
    b = bbox(allp)
    ysign = -1.0 if b[3] <= 1e-6 else 1.0
    if abs(abs(b[3] - b[2]) - BOARD_H) > 1.0 or abs((b[1] - b[0]) - BOARD_W) > 1.0:
        raise Fail("VRML export bbox %.2f x %.2f does not match the %.1f x %.1f "
                   "board; frame calibration failed"
                   % (b[1] - b[0], b[3] - b[2], BOARD_W, BOARD_H), 2)
    print("VRML frame: x_pcb = x_vrml,  y_pcb = %s * y_vrml,  z=0 at board mid"
          % ("-1" if ysign < 0 else "+1"))

    def to_pcb(p):
        return (p[0], ysign * p[1], p[2])

    # Work per IndexedFaceSet, not per point: board-wide layers (copper, mask,
    # silk) are single groups spanning the whole board and are rejected by
    # their extent, so they cannot contaminate a footprint's measurement.
    pcb_groups = [[to_pcb(p) for p in g] for g in groups]

    failures = []
    for cand in cands:
        ref, fy, path, off, expect_pass, why = cand[:6]
        fx = BOARD_W / 2.0
        pads = pad_grid(fx, fy)
        print("")
        print("--- %s  %s" % (ref, why))
        print("    %s" % path)
        print("    KiCad 3D offset %s" % (off,))

        mine = []
        for g in pcb_groups:
            gb = bbox(g)
            if (gb[0] >= fx - 24.0 and gb[1] <= fx + 24.0
                    and gb[2] >= fy - 10.5 and gb[3] <= fy + 10.5):
                mine.append(g)
        # the case: any group reaching well above the board surface
        case_groups = [g for g in mine if max(p[2] for p in g) > board_top + 1.0]
        # the pins: anything poking out below the board underside; nothing else
        # in the world lives there, so this cannot pick up copper or mask
        below = [p for g in mine for p in g if p[2] < -board_top - 0.05]

        if not case_groups:
            if expect_pass:
                failures.append("%s: NOTHING above the board -- the model did "
                                "not load at all (silent path failure)" % ref)
            print("    *** NO GEOMETRY.  Model absent from the board. ***")
            continue

        cb = bbox([p for g in case_groups for p in g])
        L, W, H = cb[1] - cb[0], cb[3] - cb[2], cb[5] - cb[4]
        print("    case  %.3f x %.3f x %.3f mm   [datasheet %.1f x %.1f x %.1f]"
              % (L, W, H, BODY_L, BODY_W, BODY_H))
        bad = []
        for got, want, lab in ((L, BODY_L, "length"), (W, BODY_W, "width"),
                               (H, BODY_H, "height")):
            if abs(got - want) > TOL_DIM:
                bad.append("case %s %.3f mm vs %.2f" % (lab, got, want))
        if abs(cb[4] - board_top) > TOL_DIM:
            bad.append("case underside at z=%.3f, board top is %.3f"
                       % (cb[4], board_top))

        # case edges relative to the pad grid -- the asymmetry that matters
        x15 = pads[1][0]
        x67 = pads[6][0]
        y1 = pads[1][1]
        y5 = pads[5][1]
        edges = ((x15 - cb[0], EDGE_PAST_15_COL, "case past pin1-5 column"),
                 (cb[1] - x67, EDGE_PAST_67_COL, "case past pin6/7 column"),
                 (y1 - cb[2], EDGE_PAST_PIN1, "case past pin 1"),
                 (cb[3] - y5, EDGE_PAST_PIN5, "case past pin 5"))
        for got, want, lab in edges:
            flag = "ok " if abs(got - want) <= TOL_DIM else "BAD"
            print("    %s  %-26s %6.3f mm  [datasheet %.2f]"
                  % (flag, lab, got, want))
            if abs(got - want) > TOL_DIM:
                bad.append("%s %.3f mm vs %.2f (off by %+.3f)"
                           % (lab, got, want, got - want))

        if below:
            cl = cluster_xy(below, 1.0)
            print("    pins  %d cluster(s) protruding below the board underside"
                  % len(cl))
            if len(cl) != 7:
                bad.append("%d pin clusters, expected 7" % len(cl))
            worst = 0.0
            for cx, cy, _n in cl:
                d = min(((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
                        for px, py in pads.values())
                worst = max(worst, d)
            flag = "ok " if worst <= TOL_POS else "BAD"
            print("    %s  worst pin-to-pad centre error   %6.3f mm" % (flag, worst))
            if worst > TOL_POS:
                bad.append("pin/pad concentricity off by %.3f mm" % worst)
        else:
            bad.append("no pin geometry below the board top")

        if bad:
            print("    VERDICT: WRONG -- " + "; ".join(bad))
            if expect_pass:
                failures.append("%s: %s" % (ref, "; ".join(bad)))
            else:
                print("    (expected to be wrong; kept as the side-by-side "
                      "control, not counted as a failure)")
        else:
            print("    VERDICT: correct")
            if not expect_pass:
                print("    (this one was expected to be WRONG and is not -- "
                      "re-check the expectation)")

    print("")
    print("LOOK AT THESE -- the render is the check:")
    for r in renders:
        print("   " + r)
    print("")
    if failures:
        for f in failures:
            print("FAIL: " + f)
        return 1
    print("ACCEPTANCE: PASS (every model expected to be correct, is)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fail as e:
        print("FAIL: %s" % e, file=sys.stderr)
        sys.exit(e.code)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("FAIL (structural): %s" % e, file=sys.stderr)
        sys.exit(2)
