#!/usr/bin/env python3
"""Acceptance check for the MECHANICAL transcription in docs/PART_iseg_APS.md section 5.

Independent source of truth: the vendor's own artwork, measured in pixels.

Figure 1 of the manual is a raster image with NO extractable text -- the dimension
labels ("39,6", "34,8", "1,8" ...) are outlined artwork.  This tool never reads
them.  It rasterises the bottom view at 24x, finds the case-outline strokes and
the seven pin squares by pixel profile, and scales everything by the PIN PITCH
measured in the same image.  So the only thing it takes on faith is 2.54 mm.

The case outline is a thick stroke, so every body-referenced dimension is emitted
as a bracket [stroke centre-line .. stroke outer edge]; the transcribed label must
fall inside it.  Pin-to-pin dimensions carry no such ambiguity and are checked to
a tight tolerance.

This confirms a transcription; it cannot refine one, and it cannot see an error in
the vendor's drawing.  A physical module must still be measured with calipers
before fabrication.

Citation: iseg APS series technical documentation v2.5, 2024-08-20, Figure 1,
          manual page 8 = PDF page index 7.

Requires `fitz` (PyMuPDF) and `numpy` -> must run under PY_KICAD:
    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/verify_part_iseg_aps_drawing.py
Zero arguments.
Exit 0 = every label lands in its bracket / 1 = a label misses / 2 = structural failure.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PDF = os.path.join(REPO, "references", "iseg_manual_APS_en.pdf")

PAGE_INDEX = 7                       # manual page 8
ZOOM = 24.0
CLIP = (160.0, 600.0, 300.0, 706.0)  # pt; the bottom view only, on that page
PIN_PITCH_MM = 2.54                  # the ruler, and the only assumed number

# transcribed labels under test (docs/PART_iseg_APS.md section 5.1 / 5.2)
LABELS = {
    "pin1..pin5 span": 10.16,
    "column separation": 34.80,
    "body length L": 39.60,
    "body width W": 15.70,
    "gap: pins 1-5 column -> end edge": 1.80,
    "gap: pins 6/7 column -> end edge": 3.00,
    "gap: pin 5 -> near long edge": 3.00,
    "gap: pin 1 -> near long edge": 2.54,
}
TOL_PIN = 0.03      # mm, pin-to-pin dimensions: unambiguous
TOL_BODY = 0.10     # mm, slack added either side of the stroke bracket


def runs(mask, minlen):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= minlen:
                out.append((start, i - 1))
            start = None
    if start is not None and len(mask) - start >= minlen:
        out.append((start, len(mask) - 1))
    return out


def main():
    try:
        import fitz
        import numpy as np
    except ImportError as exc:
        sys.stderr.write("structural: %s -- run this under PY_KICAD\n" % exc)
        return 2
    if not os.path.isfile(PDF):
        sys.stderr.write("structural: manual not found: %s\n" % PDF)
        return 2

    doc = fitz.open(PDF)
    if doc.page_count <= PAGE_INDEX:
        sys.stderr.write("structural: PDF has %d pages, need index %d\n"
                         % (doc.page_count, PAGE_INDEX))
        return 2
    pm = doc[PAGE_INDEX].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM),
                                    clip=fitz.Rect(*CLIP))
    arr = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)
    dark = arr[:, :, :3].mean(axis=2) < 128

    # case outline: the two full-width horizontal strokes and two full-height verticals
    hz = runs(dark.sum(1) > 0.5 * dark.shape[1], 5)
    if len(hz) < 2:
        sys.stderr.write("structural: found %d horizontal case strokes, need 2\n" % len(hz))
        return 2
    TOPo, TOPi, BOTi, BOTo = hz[0][0], hz[0][1], hz[1][0], hz[1][1]
    band = dark[TOPo:BOTo + 1]
    vt = runs(band.sum(0) > 0.7 * band.shape[0], 5)
    if len(vt) < 2:
        sys.stderr.write("structural: found %d vertical case strokes, need 2\n" % len(vt))
        return 2
    LFTo, LFTi, RGTi, RGTo = vt[0][0], vt[0][1], vt[-1][0], vt[-1][1]

    def pin_rows(c0, c1):
        """rows of FILLED squares in a vertical strip; leader lines are ~15 px, pins ~100"""
        strip = dark[:, c0:c1]
        return np.array([(a + b) / 2.0
                         for a, b in runs(strip.sum(1) > 0.9 * (c1 - c0), 60)
                         if a > TOPi and b < BOTi])

    def col_centre(c0, c1, rows):
        xs = []
        for r in rows:
            sub = dark[int(r) - 30:int(r) + 30, c0:c1]
            w = sub.sum(0).astype(float)
            if w.sum():
                xs.append(c0 + (w * np.arange(len(w))).sum() / w.sum())
        return float(np.mean(xs))

    R15 = np.sort(pin_rows(RGTi - 125, RGTi - 35))    # pins 1..5, inside the near wall
    R67 = np.sort(pin_rows(LFTi + 125, LFTi + 205))   # pins 7 and 6, inside the far wall
    if len(R15) != 5 or len(R67) != 2:
        sys.stderr.write("structural: found %d + %d pin squares, need 5 + 2\n"
                         % (len(R15), len(R67)))
        return 2
    X15 = col_centre(RGTi - 140, RGTi - 20, R15)
    X67 = col_centre(LFTi + 115, LFTi + 220, R67)

    gaps = np.diff(R15)
    pitch = gaps.mean()
    S = PIN_PITCH_MM / pitch
    print("iseg APS Figure 1, bottom view, rasterised at %gx" % ZOOM)
    print("pin pitch = %.2f px over 4 gaps, max deviation %.2f px (%.4f mm)"
          % (pitch, np.abs(gaps - pitch).max(), np.abs(gaps - pitch).max() * S))
    print("ruler: %.6f mm/px  (nothing below reads a dimension label)\n" % S)

    P1, P5 = R15[0], R15[-1]
    LFTc, RGTc = (LFTo + LFTi) / 2.0, (RGTi + RGTo) / 2.0
    TOPc, BOTc = (TOPo + TOPi) / 2.0, (BOTi + BOTo) / 2.0

    print("pin 7 row vs pin 1 row: %+.4f mm    pin 6 row vs pin 5 row: %+.4f mm  (expect 0)"
          % ((R67[0] - P1) * S, (R67[-1] - P5) * S))

    rows = [
        ("pin1..pin5 span", P5 - P1, P5 - P1, TOL_PIN),
        ("column separation", X15 - X67, X15 - X67, TOL_PIN),
        ("body length L", RGTc - LFTc, RGTo - LFTo, TOL_BODY),
        ("body width W", BOTc - TOPc, BOTo - TOPo, TOL_BODY),
        ("gap: pins 1-5 column -> end edge", RGTc - X15, RGTo - X15, TOL_BODY),
        ("gap: pins 6/7 column -> end edge", X67 - LFTc, X67 - LFTo, TOL_BODY),
        ("gap: pin 5 -> near long edge", BOTc - P5, BOTo - P5, TOL_BODY),
        ("gap: pin 1 -> near long edge", P1 - TOPc, P1 - TOPo, TOL_BODY),
    ]
    hdr = "%-34s %10s %10s %8s  %s" % ("dimension", "centreline", "outer", "label", "verdict")
    print("\n" + hdr)
    print("-" * len(hdr))
    failures = []
    for name, c_px, o_px, tol in rows:
        lo, hi = sorted((c_px * S, o_px * S))
        label = LABELS[name]
        ok = lo - tol <= label <= hi + tol
        if not ok:
            failures.append("%s: label %.3f outside [%.3f .. %.3f]" % (name, label, lo, hi))
        print("%-34s %10.3f %10.3f %8.2f  %s"
              % (name, c_px * S, o_px * S, label, "IN BRACKET" if ok else "*** MISS ***"))

    off_L = ((X67 - LFTc) - (RGTc - X15)) * S / 2.0
    off_W = ((BOTc - P5) - (P1 - TOPc)) * S / 2.0
    print("\nasymmetry: body centre vs pin-array centroid")
    print("  measured from artwork : %+.3f mm along L , %+.3f mm along W" % (off_L, off_W))
    print("  derived in section 5.3: +0.600 mm along L , +0.230 mm along W")
    for nm, got, want in (("L", off_L, 0.600), ("W", off_W, 0.230)):
        if abs(got - want) > 0.10:
            failures.append("asymmetry along %s: measured %+.3f vs derived %+.3f" % (nm, got, want))
    print("  -> the body is NOT centred on the pin rectangle; a symmetric outline is wrong.")

    if failures:
        print("\n%d FAILURE(S):" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("\nALL LABELS CONFIRMED AGAINST THE ARTWORK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
