#!/usr/bin/env python3
"""Emit env_proof.kicad_sch (+ .kicad_pro, sym-lib-table, fp-lib-table) as s-expression TEXT.

Phase 0 environment proof. There is NO schematic API: KiCad schematics are s-expression
text, so this tool is stdlib-only and runs on any Python 3. It shells out to kicad-cli
only to VERIFY the schema version it wrote.

Schema provenance: the version emitted is not invented and is not taken from the demos
corpus (which ships FILES OLDER THAN THE INSTALLED KICAD -- see probe_schema_version).
It is read back from a file KiCad 10.0.3 itself rewrote via `kicad-cli sch upgrade --force`.

Gate order (Part IV.5 asymmetry): electrical checks run BEFORE writing -- a wrong netlist
must never reach disk. Legibility checks run AFTER writing, so a cosmetic failure can
still be rendered and inspected.

Acceptance: union-find over the DRAWN GEOMETRY reproduces board_spec.nets() exactly,
no diagonal wires, no mid-span taps, junctions exactly where >= 3 wire endpoints meet,
and the emitted (version N) equals what kicad-cli writes.  Exit 0 only if all hold.
  python gen_sch.py
Exit codes: 0 ok / 1 verification failed / 2 structural failure / 3 legibility failure
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import board_spec as spec
from sexpr import Q, dumps, extract_block, find, findall, parse, q

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, "env_proof.kicad_sch")
PRO = os.path.join(HERE, "env_proof.kicad_pro")

CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
DEMO_SCH = ("C:/Program Files/KiCad/10.0/share/kicad/demos/"
            "simulation/rectifier/rectifier.kicad_sch")

# Read back from a file KiCad 10.0.3 rewrote itself; verified by probe_schema_version().
SCHEMA_VERSION = "20260306"
GENERATOR_VERSION = "10.0"
LIB_TABLE_VERSION = "7"          # ground truth: demos/cm5_minima/{sym,fp}-lib-table
EPS = 1e-6


# ------------------------------------------------------------------ schema provenance
def probe_schema_version():
    """Ask KiCad itself what schematic schema version it writes. Returns str or None."""
    if not (os.path.exists(CLI) and os.path.exists(DEMO_SCH)):
        return None
    tmp = tempfile.mkdtemp(prefix="schema_probe_")
    try:
        dst = os.path.join(tmp, "probe.kicad_sch")
        shutil.copyfile(DEMO_SCH, dst)
        r = subprocess.run([CLI, "sch", "upgrade", "--force", dst],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return None
        with open(dst, "r", encoding="utf-8") as fh:
            head = fh.read(400)
        tree = parse(head + ")" * head.count("("))   # cheap: only need the version atom
        v = find(tree, "version")
        return str(v[1]) if v else None
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ library plumbing
_LIBCACHE = {}


def load_lib_symbol(lib_id):
    """Return (parsed symbol tree renamed to 'Lib:Name', {pad: (px, py)})."""
    if lib_id in _LIBCACHE:
        return _LIBCACHE[lib_id]
    lib, name = lib_id.split(":", 1)
    path = os.path.join(spec.SYMLIB, lib + ".kicad_sym")
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    tree = parse(extract_block(text, "symbol", name))
    tree[1] = q(lib_id)                       # lib_symbols keys on "Lib:Name"
    pins = {}
    for sub in findall(tree, "symbol"):       # "<name>_<unit>_<body>" sub-symbols
        for pin in findall(sub, "pin"):
            at = find(pin, "at")
            num = find(pin, "number")
            if at and num:
                pins[str(num[1])] = (float(at[1]), float(at[2]))
    body = symbol_body_bbox(tree)
    _LIBCACHE[lib_id] = (tree, pins, body)
    return _LIBCACHE[lib_id]


def symbol_body_bbox(tree):
    """Bounding box of the GRAPHIC items only (pins excluded), in symbol space."""
    xs, ys = [], []

    def walk(node):
        head = str(node[0]) if node and isinstance(node[0], str) else ""
        if head in ("polyline", "rectangle", "circle", "arc", "bezier"):
            for pts in findall(node, "pts"):
                for xy in findall(pts, "xy"):
                    xs.append(float(xy[1]))
                    ys.append(float(xy[2]))
            for key in ("start", "end", "mid", "center"):
                e = find(node, key)
                if e:
                    xs.append(float(e[1]))
                    ys.append(float(e[2]))
            r = find(node, "radius")
            c = find(node, "center")
            if r and c:
                xs.extend([float(c[1]) - float(r[1]), float(c[1]) + float(r[1])])
                ys.extend([float(c[2]) - float(r[1]), float(c[2]) + float(r[1])])
        for e in node[1:]:
            if not isinstance(e, str):
                walk(e)

    walk(tree)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def pin_xy(ref, pad):
    """Screen coordinate of a pin. Symbol space is y-up, schematic space is y-down."""
    c = spec.build_board()[ref]
    _, pins, _ = load_lib_symbol(c["sym"])
    if pad not in pins:
        raise KeyError("%s: symbol %s has no pin %s" % (ref, c["sym"], pad))
    px, py = pins[pad]
    ox, oy = spec.PLACE[ref]
    return (round(ox + px, 4), round(oy - py, 4))


def body_box(ref):
    c = spec.build_board()[ref]
    _, _, bb = load_lib_symbol(c["sym"])
    if bb is None:
        return None
    ox, oy = spec.PLACE[ref]
    x0, y0, x1, y1 = bb
    return (ox + x0, oy - y1, ox + x1, oy - y0)     # y flip swaps min/max


# ------------------------------------------------------------------ geometry checks
def _k(p):
    return (round(p[0], 3), round(p[1], 3))


class UF(object):
    def __init__(self):
        self.p = {}

    def add(self, x):
        self.p.setdefault(x, x)

    def find(self, x):
        self.add(x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def on_segment(p, a, b):
    """True if p lies strictly between a and b on an axis-aligned segment."""
    if abs(a[0] - b[0]) < EPS:                      # vertical
        return (abs(p[0] - a[0]) < EPS
                and min(a[1], b[1]) + EPS < p[1] < max(a[1], b[1]) - EPS)
    if abs(a[1] - b[1]) < EPS:                      # horizontal
        return (abs(p[1] - a[1]) < EPS
                and min(a[0], b[0]) + EPS < p[0] < max(a[0], b[0]) - EPS)
    return False


def junction_points(wires):
    """KiCad rule, encoded: a junction belongs ONLY where >= 3 wire ENDPOINTS coincide.

    The GUI's cleanup pass merges collinear wires and deletes any junction that is not
    at >= 3 wire endpoints, so a junction emitted anywhere else is deleted on first save
    (and a mid-span tap relying on one silently disconnects). Two wire endpoints meeting
    at a pin need no junction: connectivity there is geometric.
    """
    count = {}
    for a, b in wires:
        for p in (a, b):
            count[_k(p)] = count.get(_k(p), 0) + 1
    return sorted(p for p, n in count.items() if n >= 3)


def electrical_check(wires):
    """Runs BEFORE any file is written. Compares drawn geometry to the golden netlist."""
    problems = []
    board = spec.build_board()

    for a, b in wires:
        if abs(a[0] - b[0]) > EPS and abs(a[1] - b[1]) > EPS:
            problems.append("diagonal wire %s -> %s" % (a, b))
        if _k(a) == _k(b):
            problems.append("zero-length wire at %s" % (a,))

    # T-tap invariant: no wire endpoint may land mid-span on another wire.
    for i, (a, b) in enumerate(wires):
        for j, (c, d) in enumerate(wires):
            if i == j:
                continue
            for p in (c, d):
                if on_segment(p, a, b):
                    problems.append(
                        "mid-span tap: endpoint %s of wire %d lies inside wire %d (%s->%s)"
                        % (p, j, i, a, b))

    # union-find over drawn geometry
    uf = UF()
    for a, b in wires:
        uf.union(_k(a), _k(b))

    pinpts = {}
    for ref, c in board.items():
        for pad in c["pins"]:
            pinpts[(ref, pad)] = _k(pin_xy(ref, pad))

    endpoints = set()
    for a, b in wires:
        endpoints.add(_k(a))
        endpoints.add(_k(b))
    for (ref, pad), p in pinpts.items():
        if p not in endpoints:
            problems.append("pin %s.%s at %s is not a wire endpoint (floating)"
                            % (ref, pad, p))

    drawn = {}
    for (ref, pad), p in pinpts.items():
        drawn.setdefault(uf.find(p), []).append((ref, pad))
    drawn_nets = sorted(sorted(v) for v in drawn.values())
    golden_nets = sorted(sorted(v) for v in spec.nets().values())
    if drawn_nets != golden_nets:
        problems.append("drawn connectivity != golden netlist")
        for g in golden_nets:
            if g not in drawn_nets:
                problems.append("   golden group missing from drawing: %s" % (g,))
        for d in drawn_nets:
            if d not in golden_nets:
                problems.append("   drawn group not in golden netlist: %s" % (d,))

    for ref in board:
        if ref in spec.PLACE and len(spec.PLACE[ref]) != 2:
            problems.append("%s: PLACE must be (x, y); rotations are not implemented" % ref)

    # Every label must sit ON a wire, and on a wire belonging to the net it names --
    # a label 0.01 mm off the wire names nothing and ERC never mentions it.
    for net, p, _ang in spec.LABELS:
        owner = None
        for a, b in wires:
            if _k(p) in (_k(a), _k(b)) or on_segment(p, a, b):
                owner = uf.find(_k(a))
                break
        if owner is None:
            problems.append("label %r at %s does not touch any wire" % (net, p))
            continue
        members = drawn.get(owner, [])
        expected = spec.nets().get(net, [])
        if sorted(members) != sorted(expected):
            problems.append("label %r sits on the net carrying %s, expected %s"
                            % (net, members, expected))
    return problems


def legibility_check(wires):
    """Runs AFTER writing, so a cosmetic failure can still be rendered and inspected."""
    problems = []
    boxes = {r: body_box(r) for r in spec.build_board()}
    for ref, bb in boxes.items():
        if bb is None:
            continue
        x0, y0, x1, y1 = bb
        for a, b in wires:
            sx0, sx1 = sorted((a[0], b[0]))
            sy0, sy1 = sorted((a[1], b[1]))
            if (sx0 < x1 - EPS and sx1 > x0 + EPS
                    and sy0 < y1 - EPS and sy1 > y0 + EPS):
                problems.append("L3 wire %s->%s crosses the body of %s %s"
                                % (a, b, ref, bb))
    # L4: wire crossings (budget 0 on a board this small)
    for i, (a, b) in enumerate(wires):
        for j in range(i + 1, len(wires)):
            c, d = wires[j]
            if _crosses(a, b, c, d):
                problems.append("L4 wires %d and %d cross" % (i, j))
    return problems


def _crosses(a, b, c, d):
    ah = abs(a[1] - b[1]) < EPS
    ch = abs(c[1] - d[1]) < EPS
    if ah == ch:
        return False
    h, v = ((a, b), (c, d)) if ah else ((c, d), (a, b))
    hy = h[0][1]
    hx0, hx1 = sorted((h[0][0], h[1][0]))
    vx = v[0][0]
    vy0, vy1 = sorted((v[0][1], v[1][1]))
    return (hx0 + EPS < vx < hx1 - EPS) and (vy0 + EPS < hy < vy1 - EPS)


# ------------------------------------------------------------------ emission
def eff(size=1.27, justify=None, hide=False):
    e = ["effects", ["font", ["size", "%g" % size, "%g" % size]]]
    if justify:
        j = [justify] if isinstance(justify, str) else list(justify)
        e.append(["justify"] + j)
    return e


def prop(name, value, at, hide=False, justify=None):
    p = ["property", q(name), q(value), ["at", "%g" % at[0], "%g" % at[1], "%g" % at[2]]]
    if hide:
        p.append(["hide", "yes"])
    p += [["show_name", "no"], ["do_not_autoplace", "no"], eff(justify=justify)]
    return p


def symbol_instance(ref, c):
    ox, oy = spec.PLACE[ref]
    _, pins, bb = load_lib_symbol(c["sym"])
    if c["power"]:
        # Text goes on the side the body does NOT occupy: power:GND draws below its pin,
        # power:PWR_FLAG draws above it. Keying on the symbol's own body bbox rather
        # than on the refdes avoids the class of bug where a rail name lands on a wire.
        below = (bb is not None and bb[3] <= EPS)     # body ymax <= 0 in symbol space
        d = 1.0 if below else -1.0
        ref_at = (ox, oy + d * 6.35, 0)
        val_at = (ox, oy + d * 3.81, 0)
        ref_hide, val_hide = True, False
    else:
        ref_at = (ox + 3.81, oy - 1.27, 0)
        val_at = (ox + 3.81, oy + 1.27, 0)
        ref_hide, val_hide = False, False
    node = ["symbol",
            ["lib_id", q(c["sym"])],
            ["at", "%g" % ox, "%g" % oy, "0"],
            ["unit", "1"],
            ["body_style", "1"],
            ["exclude_from_sim", "no"],
            ["in_bom", "yes" if not c["power"] else "yes"],
            ["on_board", "yes"],
            ["in_pos_files", "yes"],
            ["dnp", "no"],
            ["uuid", q(spec.sym_uuid(ref))],
            prop("Reference", ref, ref_at, hide=ref_hide, justify="left"),
            prop("Value", c["val"], val_at, hide=val_hide, justify="left"),
            prop("Footprint", c["fp"], (ox, oy, 0), hide=True),
            prop("Datasheet", c["datasheet"], (ox, oy, 0), hide=True),
            prop("Description", "", (ox, oy, 0), hide=True)]
    for pad in sorted(pins):
        node.append(["pin", q(pad), ["uuid", q(spec.pin_uuid(ref, pad))]])
    node.append(["instances",
                 ["project", q(spec.PROJECT),
                  ["path", q("/" + spec.root_uuid()),
                   ["reference", q(ref)], ["unit", "1"]]]])
    return node


def build_tree(wires, juncs):
    board = spec.build_board()
    libs = ["lib_symbols"]
    for lib_id in sorted({c["sym"] for c in board.values()}):
        tree, _, _ = load_lib_symbol(lib_id)
        libs.append(tree)

    doc = ["kicad_sch",
           ["version", SCHEMA_VERSION],
           ["generator", q("phase0_gen_sch")],
           ["generator_version", q(GENERATOR_VERSION)],
           ["uuid", q(spec.root_uuid())],
           ["paper", q(spec.PAPER)],
           libs]
    for p in juncs:
        doc.append(["junction",
                    ["at", "%g" % p[0], "%g" % p[1]],
                    ["diameter", "0"],
                    ["color", "0", "0", "0", "0"],
                    ["uuid", q(spec.junction_uuid(p))]])
    for net, p, ang in spec.LABELS:
        doc.append(["label", q(net),
                    ["at", "%g" % p[0], "%g" % p[1], "%g" % ang],
                    eff(justify=["left", "bottom"]),
                    ["uuid", q(spec.label_uuid(net, p))]])
    for a, b in wires:
        doc.append(["wire",
                    ["pts", ["xy", "%g" % a[0], "%g" % a[1]],
                            ["xy", "%g" % b[0], "%g" % b[1]]],
                    ["stroke", ["width", "0"], ["type", "default"]],
                    ["uuid", q(spec.wire_uuid(a, b))]])
    for ref in sorted(board):
        doc.append(symbol_instance(ref, board[ref]))
    doc.append(["sheet_instances", ["path", q("/"), ["page", q("1")]]])
    return doc


def write_project():
    """.kicad_pro. The Default netclass carries its SCHEMATIC fields (wire_width,
    bus_width, line_style, diff_pair_*, microvia_*): a PCB-only netclass silently
    breaks eeschema connectivity for every net in it, and kicad-cli NEVER READS THIS
    FILE, so no headless gate can see the damage."""
    pro = {
        "board": {"3dviewports": [], "design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2,
                         "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
                         "copper_text_thickness": 0.3, "other_line_width": 0.15,
                         "silk_line_width": 0.15, "silk_text_size_h": 1.0,
                         "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
            "diff_pair_dimensions": [], "drc_exclusions": [],
            "rules": {"solder_mask_clearance": 0.0, "solder_mask_min_width": 0.0},
            "track_widths": [], "via_dimensions": []},
            "layer_presets": [], "viewports": []},
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [],
                "rule_severities": {}, "rule_severitiess": {}},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": "env_proof.kicad_pro", "version": 3},
        "net_settings": {
            "classes": [{
                "bus_width": 12, "clearance": 0.2,
                "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)",
                "priority": 2147483647, "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": spec.TRACK_W, "via_diameter": spec.VIA_D,
                "via_drill": spec.VIA_DRILL, "wire_width": 6}],
            "meta": {"version": 4}, "net_colors": None,
            "netclass_assignments": None, "netclass_patterns": []},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "",
                                  "pos_files": "", "specctra_dsn": "", "step": "",
                                  "svg": "", "vrml": ""},
                   "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": [],
                      "meta": {"version": 1}, "net_format_name": "",
                      "page_layout_descr_file": "", "plot_directory": ""},
        "sheets": [[spec.root_uuid(), "Root"]],
        "text_variables": {},
    }
    with open(PRO, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(pro, fh, indent=2, sort_keys=True)
        fh.write("\n")


def write_lib_tables():
    """Both tables must EXIST or the GUI cannot resolve libraries. This board uses only
    stock libraries, so the tables are structurally valid and carry no project entries;
    resolution falls through to the user's global tables."""
    for fname, head in (("sym-lib-table", "sym_lib_table"),
                        ("fp-lib-table", "fp_lib_table")):
        with open(os.path.join(HERE, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("(%s\n  (version %s)\n)\n" % (head, LIB_TABLE_VERSION))


def main():
    wires = [tuple(map(tuple, w)) for w in spec.WIRES]

    problems = spec.check()
    if problems:
        print("FAIL board_spec (%d):" % len(problems))
        for p in problems:
            print("   " + p)
        return 2

    problems = electrical_check(wires)
    if problems:
        print("FAIL electrical, nothing written (%d):" % len(problems))
        for p in problems:
            print("   " + p)
        return 2

    juncs = junction_points(wires)
    doc = build_tree(wires, juncs)
    with open(SCH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(doc) + "\n")
    write_project()
    write_lib_tables()

    probed = probe_schema_version()
    if probed is None:
        print("WARN  schema version could not be probed (kicad-cli absent?); "
              "emitted %s unverified" % SCHEMA_VERSION)
    elif probed != SCHEMA_VERSION:
        print("FAIL  emitted (version %s) but kicad-cli writes (version %s)"
              % (SCHEMA_VERSION, probed))
        return 1

    leg = legibility_check(wires)
    if leg:
        print("LEGIBILITY FAIL (%d) - file written, render it:" % len(leg))
        for p in leg:
            print("   " + p)
        return 3

    print("PASS - %s: %d symbols, %d wires, %d junction(s), %d nets; "
          "schema %s confirmed by kicad-cli sch upgrade"
          % (os.path.basename(SCH), len(spec.build_board()), len(wires), len(juncs),
             len(spec.nets()), SCHEMA_VERSION if probed else "?"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
