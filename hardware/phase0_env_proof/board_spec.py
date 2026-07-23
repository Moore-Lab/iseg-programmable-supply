#!/usr/bin/env python3
"""Golden netlist for the Phase 0 throwaway board -- the single source of truth.

THIS IS NOT A REAL DESIGN. Two resistors in series between two test points, plus a
ground zone. Its only purpose is to prove the toolchain end to end.

Every downstream artifact (schematic, PCB, checks) is a function of build_board().
Acceptance everywhere is a diff against this structure.

Acceptance: self-test in main() asserts the spec is internally consistent (every net
has >= 2 endpoints, refdes unique, every pin mapped).  Exit 0 only if it holds.
  python board_spec.py
"""
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = "env_proof"

# Fixed namespace -> deterministic identity. uuid5 over a semantic key, NEVER uuid4:
# "regenerate and git diff" is then a free regression test.
NS = uuid.UUID("6f1c0a2e-2b4b-5b3a-9c8d-0e1f2a3b4c5d")

# ---------------------------------------------------------------- schematic geometry
# mm. Schematic grid U = 1.27 mm; every coordinate below is an integer multiple of U.
U = 1.27

# Symbol origins (mm). Rotation is 0 for every symbol on this board -- gen_sch.py
# asserts that, because the pin-transform for other rotations is deliberately not
# implemented here (a Phase 0 board must not carry untested transforms).
PLACE = {
    "TP1":    (76.2, 63.5),
    "R1":     (76.2, 76.2),
    "R2":     (76.2, 88.9),
    "TP2":    (101.6, 92.71),
    "#PWR01": (88.9, 99.06),
    "#FLG01": (95.25, 86.36),
}

# Wire runs, pre-split at every attach point so that EVERY meeting of two wires is
# endpoint-to-endpoint. KiCad's GUI cleanup merges collinear wires and deletes
# junctions that are not at >= 3 wire ENDPOINTS; a mid-span tap survives the file,
# passes the CLI, and dissolves on the first GUI save.
WIRES = [
    ((76.2, 63.50), (76.2, 72.39)),      # IN  : TP1.1 -> R1.1
    ((76.2, 80.01), (76.2, 85.09)),      # MID : R1.2  -> R2.1
    ((76.2, 92.71), (88.9, 92.71)),      # GND : R2.2  -> node A
    ((88.9, 92.71), (95.25, 92.71)),     # GND : node A -> node B   (pre-split run)
    ((95.25, 92.71), (101.6, 92.71)),    # GND : node B -> TP2.1    (pre-split run)
    ((88.9, 92.71), (88.9, 99.06)),      # GND : node A -> #PWR01.1
    ((95.25, 92.71), (95.25, 86.36)),    # GND : node B -> #FLG01.1
]

# Local labels NAME the nets. Without them KiCad invents "Net-(R1-Pad1)" and every
# downstream pad-net parity check compares against a machine-chosen name that changes
# when the schematic is edited. Labels here are for NAMING only -- connectivity is
# carried by the wires above.  (net, anchor point, angle)
LABELS = [
    ("IN",  (76.2, 68.58), 0),
    ("MID", (76.2, 82.55), 0),
]

PAPER = "A4"

# ---------------------------------------------------------------- board geometry (mm)
BOARD_RECT = (100.0, 100.0, 150.0, 125.0)   # x0, y0, x1, y1 on Edge.Cuts
ZONE_INSET = 1.0                            # zone outline inset from the board edge
TRACK_W = 0.25
VIA_D, VIA_DRILL = 0.8, 0.4
GND_VIA = (135.0, 118.0)                    # stitches the F.Cu and B.Cu GND zones

FP_PLACE = {                                # footprint centre (mm), rotation (deg)
    "TP1": ((108.0, 112.0), 0.0),
    "R1":  ((118.0, 112.0), 0.0),
    "R2":  ((128.0, 112.0), 0.0),
    "TP2": ((140.0, 112.0), 0.0),
}

# Hand-placed track segments (net, layer, (x0,y0), (x1,y1)). Resolved to pad centres
# by gen_pcb.py; endpoints given here as (refdes, pad) so the geometry follows the
# footprints rather than duplicating their coordinates.
TRACKS = [
    ("IN",  "F.Cu", ("TP1", "1"), ("R1", "1")),
    ("MID", "F.Cu", ("R1", "2"),  ("R2", "1")),
    ("GND", "F.Cu", ("R2", "2"),  ("TP2", "1")),
]

FPLIB = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
SYMLIB = "C:/Program Files/KiCad/10.0/share/kicad/symbols"


def build_board():
    """The golden netlist. {ref: {...}}. pins maps pad number -> net name."""
    return {
        "TP1": dict(
            sym="Connector:TestPoint", val="IN", ref_prefix="TP",
            fp="TestPoint:TestPoint_Pad_D1.5mm",
            datasheet="~", pins={"1": "IN"}, on_board=True, power=False),
        "R1": dict(
            sym="Device:R", val="10k", ref_prefix="R",
            fp="Resistor_SMD:R_0805_2012Metric",
            datasheet="~", pins={"1": "IN", "2": "MID"}, on_board=True, power=False),
        "R2": dict(
            sym="Device:R", val="10k", ref_prefix="R",
            fp="Resistor_SMD:R_0805_2012Metric",
            datasheet="~", pins={"1": "MID", "2": "GND"}, on_board=True, power=False),
        "TP2": dict(
            sym="Connector:TestPoint", val="GND", ref_prefix="TP",
            fp="TestPoint:TestPoint_Pad_D1.5mm",
            datasheet="~", pins={"1": "GND"}, on_board=True, power=False),
        "#PWR01": dict(
            sym="power:GND", val="GND", ref_prefix="#PWR",
            fp="", datasheet="", pins={"1": "GND"}, on_board=False, power=True),
        # Without a PWR_FLAG, ERC raises power_pin_not_driven on the GND power symbol:
        # nothing on this board is a power OUTPUT. Verified: ERC went 1 error -> 0.
        "#FLG01": dict(
            sym="power:PWR_FLAG", val="PWR_FLAG", ref_prefix="#FLG",
            fp="", datasheet="", pins={"1": "GND"}, on_board=False, power=True),
    }


def nets():
    """{net: sorted [(ref, pad), ...]} derived from build_board()."""
    out = {}
    for ref, c in build_board().items():
        for pad, net in c["pins"].items():
            out.setdefault(net, []).append((ref, pad))
    return {n: sorted(v) for n, v in out.items()}


def board_nets():
    """Nets as they appear on the PCB: power symbols carry no pads."""
    out = {}
    for ref, c in build_board().items():
        if not c["on_board"]:
            continue
        for pad, net in c["pins"].items():
            out.setdefault(net, []).append((ref, pad))
    return {n: sorted(v) for n, v in out.items()}


def sym_uuid(ref):
    """Deterministic schematic symbol UUID. gen_pcb.py uses the SAME function to set
    each footprint's (path ...), so schematic<->board linkage is reproducible."""
    return str(uuid.uuid5(NS, "%s/symbol/%s" % (PROJECT, ref)))


def pin_uuid(ref, pad):
    return str(uuid.uuid5(NS, "%s/pin/%s.%s" % (PROJECT, ref, pad)))


def wire_uuid(a, b):
    return str(uuid.uuid5(NS, "%s/wire/%.4f,%.4f-%.4f,%.4f" % ((PROJECT,) + a + b)))


def label_uuid(net, p):
    return str(uuid.uuid5(NS, "%s/label/%s@%.4f,%.4f" % ((PROJECT, net) + p)))


def junction_uuid(p):
    return str(uuid.uuid5(NS, "%s/junction/%.4f,%.4f" % ((PROJECT,) + p)))


def root_uuid():
    return str(uuid.uuid5(NS, "%s/root" % PROJECT))


def check():
    problems = []
    b = build_board()
    for ref, c in b.items():
        if not ref.startswith(c["ref_prefix"]):
            problems.append("%s: refdes does not match ref_prefix %r" % (ref, c["ref_prefix"]))
        if not c["pins"]:
            problems.append("%s: no pins" % ref)
        if c["on_board"] and not c["fp"]:
            problems.append("%s: on_board but no footprint" % ref)
    for net, pts in nets().items():
        if len(pts) < 2:
            problems.append("net %s has %d endpoint(s); every net needs >= 2" % (net, len(pts)))
    for ref in b:
        if ref not in PLACE:
            problems.append("%s has no schematic placement" % ref)
    for ref, c in b.items():
        if c["on_board"] and ref not in FP_PLACE:
            problems.append("%s has no footprint placement" % ref)
    for x, y in [p for pair in WIRES for p in pair]:
        for v, n in ((x, "x"), (y, "y")):
            if abs(round(v / U) * U - v) > 1e-6:
                problems.append("wire %s=%.4f is off the %.2f mm grid" % (n, v, U))
    return problems


def main():
    problems = check()
    if problems:
        print("FAIL (%d):" % len(problems))
        for p in problems:
            print("   " + p)
        return 1
    n = nets()
    print("PASS - %d components, %d nets (%s), %d wire runs"
          % (len(build_board()), len(n), ", ".join(sorted(n)), len(WIRES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
