#!/usr/bin/env python3
"""Acceptance check for the geometry arithmetic in docs/PART_iseg_APS.md.

Re-derives every coordinate in PART_iseg_APS.md section 6 from the FIVE primitives
read off manual v2.5 Figure 1 (L, W, column separation, pin pitch, and the single
dimensioned end overhang), then asserts that the re-derived numbers are the ones
literally printed in the document.  The independent source of truth is the
arithmetic itself: if someone edits a coordinate in the document by hand without
editing the primitives, this fails.

Also re-derives the item-code Inom decoder against the catalogue currents in
Table 2, the Figure 2 set-node RC, and the VMON loading errors.

Citation: iseg APS series technical documentation v2.5, 2024-08-20
          (Figure 1 page 8, Table 2 page 8, Figure 2 page 9).

stdlib only; runs on any Python 3.  Zero arguments.
Exit 0 = all checks pass / 1 = a check failed / 2 = structural failure.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOC = os.path.join(REPO, "docs", "PART_iseg_APS.md")

# --- the only inputs: primitives read off manual v2.5 Figure 1 -----------------
BODY_L_MM = 39.6      # dimensioned "39,6" on the top view
BODY_W_MM = 15.7      # dimensioned "15,7" on the top view
COLUMN_SEP_MM = 34.8  # dimensioned "34,8" on the bottom view
PIN_PITCH_MM = 2.54   # dimensioned "2,54" on the bottom view
OVERHANG_PIN15_END = 1.8   # dimensioned "1,8" on the bottom view

# catalogue Inom, manual v2.5 Table 2 page 8: item-code field -> mA
INOM_CATALOGUE = {"255": 2.5, "125": 1.2, "804": 0.8, "604": 0.6, "504": 0.5,
                  "505": 5.0, "165": 1.6, "105": 1.0}

# reference footprint under references/ (read-only third-party material)
REF_FP_BODY_HALF_L = 19.812   # its fp_line half-extent, pin-centroid frame
REF_FP_BODY_HALF_W = 7.874
REF_FP_STEP_OFFSET = (-19.2278, -7.62)   # its (offset (xyz ...)) for the 3D model


class Checker(object):
    def __init__(self):
        self.failures = []

    def eq(self, name, got, want, tol=1e-9):
        ok = abs(got - want) <= tol
        if not ok:
            self.failures.append("%s: got %.6f, expected %.6f" % (name, got, want))
        print("  %-42s %10.4f  expect %10.4f   %s"
              % (name, got, want, "ok" if ok else "FAIL"))

    def same(self, name, got, want):
        ok = got == want
        if not ok:
            self.failures.append("%s: got %r, expected %r" % (name, got, want))
        print("  %-42s %-22r %s" % (name, got, "ok" if ok else "FAIL -> %r" % (want,)))

    def present(self, text, needle):
        ok = needle in text
        if not ok:
            self.failures.append("document text missing: %r" % (needle,))
        print("  %-64s %s" % (repr(needle)[:64], "present" if ok else "MISSING"))


def main():
    if not os.path.isfile(DOC):
        sys.stderr.write("structural: document not found: %s\n" % DOC)
        return 2
    try:
        with open(DOC, encoding="utf-8") as fh:
            txt = fh.read()
    except OSError as exc:
        sys.stderr.write("structural: cannot read document: %s\n" % exc)
        return 2

    c = Checker()

    print("derived overhangs (only two of four are dimensioned in Figure 1)")
    span = 4 * PIN_PITCH_MM
    ov_67 = BODY_L_MM - OVERHANG_PIN15_END - COLUMN_SEP_MM
    ov_p1 = BODY_W_MM - span - ov_67
    ov_p5 = ov_67
    c.eq("pin1..pin5 span", span, 10.16)
    c.eq("overhang, pins 6/7 end (derived)", ov_67, 3.0)
    c.eq("overhang, pin 1 side (derived)", ov_p1, 2.54)

    print("\nFrame T (KiCad F.Cu): origin pin 1, +x -> pin 7, +y -> pin 5")
    T = {1: (0.0, 0.0), 2: (0.0, PIN_PITCH_MM), 3: (0.0, 2 * PIN_PITCH_MM),
         4: (0.0, 3 * PIN_PITCH_MM), 5: (0.0, 4 * PIN_PITCH_MM),
         6: (COLUMN_SEP_MM, 4 * PIN_PITCH_MM), 7: (COLUMN_SEP_MM, 0.0)}
    bx0, by0 = -OVERHANG_PIN15_END, -ov_p1
    bx1, by1 = bx0 + BODY_L_MM, by0 + BODY_W_MM
    c.eq("body x0", bx0, -1.80)
    c.eq("body y0", by0, -2.54)
    c.eq("body x1", bx1, 37.80)
    c.eq("body y1", by1, 13.16)
    c.eq("gap pin6 -> far end edge", bx1 - T[6][0], 3.00)
    c.eq("gap pin5 -> near long edge", by1 - T[5][1], 3.00)

    cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
    px, py = COLUMN_SEP_MM / 2.0, span / 2.0
    print("\nthe asymmetry (body is NOT centred on the pin array)")
    c.eq("body centre x", cx, 18.00)
    c.eq("body centre y", cy, 5.31)
    c.eq("pin centroid x", px, 17.40)
    c.eq("pin centroid y", py, 5.08)
    c.eq("offset along L", cx - px, 0.60)
    c.eq("offset along W", cy - py, 0.23)
    c.eq("offset along L, alt formula", (ov_67 - OVERHANG_PIN15_END) / 2.0, 0.60)
    c.eq("offset along W, alt formula", (ov_p5 - ov_p1) / 2.0, 0.23)

    print("\nFrame T, pins relative to body centre")
    expect_relC = {1: (-18.00, -5.31), 2: (-18.00, -2.77), 3: (-18.00, -0.23),
                   4: (-18.00, 2.31), 5: (-18.00, 4.85),
                   6: (16.80, 4.85), 7: (16.80, -5.31)}
    for k in sorted(T):
        got = (round(T[k][0] - cx, 2), round(T[k][1] - cy, 2))
        c.same("pin %d rel. body centre" % k, got,
               (round(expect_relC[k][0], 2), round(expect_relC[k][1], 2)))

    print("\nFrame B is the pure mirror of Frame T about the pins 1..5 column")
    c.eq("pin 6 x", -T[6][0], -34.80)
    c.eq("body x0", -bx1, -37.80)
    c.eq("body x1", -bx0, 1.80)
    c.eq("body centre x", -cx, -18.00)

    print("\nFrame C (pin-array centroid) and the reference-footprint defect")
    cbx0, cbx1 = bx0 - px, bx1 - px
    cby0, cby1 = by0 - py, by1 - py
    c.eq("body x0", cbx0, -19.20)
    c.eq("body x1", cbx1, 20.40)
    c.eq("body y0", cby0, -7.62)
    c.eq("body y1", cby1, 8.08)
    c.eq("ref-fp error, pins 1-5 end", abs(-REF_FP_BODY_HALF_L - cbx0), 0.612, 5e-4)
    c.eq("ref-fp error, pins 6/7 end", abs(REF_FP_BODY_HALF_L - cbx1), 0.588, 5e-4)
    c.eq("ref-fp error, pin 1 side", abs(-REF_FP_BODY_HALF_W - cby0), 0.254, 5e-4)
    c.eq("ref-fp error, pin 5 side", abs(REF_FP_BODY_HALF_W - cby1), 0.206, 5e-4)
    # the reference file's own STEP offset agrees with the DATASHEET, not with its
    # own outline -- that internal contradiction is the citable evidence
    c.eq("ref-fp STEP offset x vs correct x0",
         abs(REF_FP_STEP_OFFSET[0] - cbx0), 0.0278, 5e-5)
    c.eq("ref-fp STEP offset y vs correct y0",
         abs(REF_FP_STEP_OFFSET[1] - cby0), 0.0, 5e-5)

    print("\nitem-code Inom decoder: two significant digits + count of trailing zeros, nA")
    for field, mA in sorted(INOM_CATALOGUE.items()):
        c.eq("  %s -> mA" % field, (int(field[:2]) * 10 ** int(field[2])) / 1e6, mA)

    print("\nFigure 2 internal set-node RC (100 k x 1 uF)")
    tau = 100e3 * 1e-6
    c.eq("tau, VSET stiffly driven (s)", tau, 0.10, 1e-12)
    c.eq("tau, VSET open (110 k) (s)", 110e3 * 1e-6, 0.11, 1e-12)
    c.eq("10-90 % of a step (s)", 2.2 * tau, 0.22, 1e-12)
    c.eq("settle to 1 % (s)", round(4.6 * tau, 2), 0.46)

    print("\nVMON loading error from the internal 20 k series resistor")
    for RL, pct in ((1e6, 1.96), (100e3, 16.67), (10e3, 66.67)):
        c.eq("  external load %9.0f ohm, %% low" % RL,
             100.0 * 20e3 / (20e3 + RL), pct, 5e-3)

    print("\nthe re-derived numbers must be the ones printed in the document")
    for needle in (
        "(  0.00, 10.16)   (-18.00,   4.85)",
        "( 34.80, 10.16)   ( 16.80,   4.85)",
        "x from  -1.80 to  37.80",
        "y from  -2.54 to  13.16",
        "( 18.00,  5.31)",
        "( 17.40,  5.08)",
        "x from -19.20 to  20.40 ,  y from -7.62 to  8.08",
        "BODY_MM = (-1.80, -2.54, 37.80, 13.16)",
        "COLUMN_SEP_MM       = 34.80",
        "v2.5, Table 4, page 9",
    ):
        c.present(txt, needle)

    if c.failures:
        print("\n%d FAILURE(S):" % len(c.failures))
        for f in c.failures:
            print("  " + f)
        return 1
    print("\nALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
