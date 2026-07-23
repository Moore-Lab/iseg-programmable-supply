#!/usr/bin/env python3
"""netcmp: pin-exact comparison, BOTH directions, of the kicad-cli-exported netlist
against the golden netlist in board_spec.py.

Phase 0 environment proof. Stdlib only. The exported netlist is the independent source
of truth here: it is produced by KiCad's own connectivity engine from the drawn
geometry, not by the generator's model of it.

Blind spot, stated up front: this inherits everything `kicad-cli sch export netlist`
cannot see -- it is lenient about taps the GUI rejects, and it never reads .kicad_pro,
so a netclass that breaks eeschema connectivity is invisible to this check.

Acceptance: exported nets == golden nets as sets of (ref, pad), after normalising the
sheet-path prefix that KiCad prepends to LOCAL LABEL names ("/IN", not "IN").
  python check_netlist.py [path/to/netlist.net]
Exit codes: 0 ok / 1 verification failed / 2 structural failure
"""
import os
import sys

import board_spec as spec
from sexpr import find, findall, parse, unq

HERE = os.path.dirname(os.path.abspath(__file__))
NET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "outputs", "env_proof.net")


def norm(name):
    """KiCad prefixes a LOCAL LABEL's net name with its sheet path: root sheet gives
    '/IN'. Power-symbol nets (GND) carry no prefix because they are global."""
    return name.lstrip("/")


def read_netlist(path):
    with open(path, "r", encoding="utf-8") as fh:
        tree = parse(fh.read())
    nets = {}
    section = find(tree, "nets")
    if section is None:
        raise ValueError("no (nets) section in %s" % path)
    for net in findall(section, "net"):
        name = unq(find(net, "name")[1])
        pts = []
        for node in findall(net, "node"):
            pts.append((unq(find(node, "ref")[1]), unq(find(node, "pin")[1])))
        nets[norm(name)] = sorted(pts)
    comps = {}
    csec = find(tree, "components")
    if csec is not None:
        for comp in findall(csec, "comp"):
            ref = unq(find(comp, "ref")[1])
            fp = find(comp, "footprint")
            comps[ref] = unq(fp[1]) if fp else ""
    return nets, comps


def check(path):
    problems = []
    if not os.path.exists(path):
        return ["netlist missing: %s (run kicad-cli sch export netlist first)" % path], {}
    exported, comps = read_netlist(path)
    golden = spec.board_nets()      # power symbols contribute no pads

    for name, pts in sorted(golden.items()):
        if name not in exported:
            problems.append("golden net %r absent from exported netlist "
                            "(exported: %s)" % (name, sorted(exported)))
        elif exported[name] != pts:
            problems.append("net %r: exported %s != golden %s"
                            % (name, exported[name], pts))
    for name, pts in sorted(exported.items()):
        if name not in golden:
            problems.append("exported net %r (%s) is not in the golden netlist"
                            % (name, pts))

    board = spec.build_board()
    for ref, c in board.items():
        if not c["on_board"]:
            if ref in comps:
                problems.append("%s is not on_board but appears in the netlist" % ref)
            continue
        if ref not in comps:
            problems.append("%s missing from the exported netlist components" % ref)
        elif comps[ref] != c["fp"]:
            problems.append("%s footprint %r != golden %r" % (ref, comps[ref], c["fp"]))
    return problems, exported


def main():
    problems, exported = check(NET)
    if problems:
        print("FAIL (%d):" % len(problems))
        for p in problems[:40]:
            print("   " + p)
        return 1
    print("PASS - %d nets pin-exact both directions vs board_spec (%s)"
          % (len(exported), ", ".join(sorted(exported))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
