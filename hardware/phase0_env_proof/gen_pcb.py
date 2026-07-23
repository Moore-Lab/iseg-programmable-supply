#!/usr/bin/env python3
"""Build env_proof.kicad_pcb: footprints, Edge.Cuts, GND zones, hand-placed tracks.

Phase 0 environment proof. This tool manipulates board GEOMETRY, so it imports pcbnew
and is locked to KiCad's bundled interpreter:
  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py

It DOES NOT fill zones. ZONE_FILLER.Fill() runs in a separate process on the saved file
(fill_zones.py) -- see that tool's docstring for what was actually observed here.

Net NAMES come from the kicad-cli-exported netlist, not from board_spec: KiCad prefixes
a local label's net name with the sheet path ("/IN"), and inventing "IN" here would make
every downstream parity check compare the wrong string.

Acceptance: every pad's net, read back off the built BOARD, equals the exported netlist
(the independent source of truth) -- checked BEFORE the file is saved.
Exit codes: 0 ok / 1 verification failed / 2 structural failure
"""
import os
import sys

import pcbnew

import board_spec as spec
from check_netlist import read_netlist

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "env_proof.kicad_pcb")
NET = os.path.join(HERE, "outputs", "env_proof.net")

LAYER = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}


def mm(v):
    """mm -> integer nanometres. pcbnew internal units are nm; never a bare literal."""
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def raw_net_names(path):
    """The net names exactly as KiCad wrote them, keyed by the golden name."""
    from sexpr import find, findall, parse, unq
    with open(path, "r", encoding="utf-8") as fh:
        tree = parse(fh.read())
    out = {}
    for net in findall(find(tree, "nets"), "net"):
        raw = unq(find(net, "name")[1])
        out[raw.lstrip("/")] = raw
    return out


def build():
    exported, _comps = read_netlist(NET)
    raw = raw_net_names(NET)
    golden = spec.board_nets()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)

    for name in sorted(golden):
        board.Add(pcbnew.NETINFO_ITEM(board, raw[name]))

    # ---- footprints
    fps = {}
    for ref, c in sorted(spec.build_board().items()):
        if not c["on_board"]:
            continue
        lib, fpname = c["fp"].split(":", 1)
        fp = pcbnew.FootprintLoad(os.path.join(spec.FPLIB, lib + ".pretty"), fpname)
        if fp is None:
            raise RuntimeError("footprint not found: %s" % c["fp"])
        # TRAP: pcbnew.FootprintLoad() returns a footprint whose FPID carries only the
        # bare name -- the library nickname is dropped. Left alone, the board records
        # "R_0805_2012Metric" instead of "Resistor_SMD:R_0805_2012Metric", which breaks
        # library linkage and footprint parity. Restore it explicitly.
        fp.SetFPID(pcbnew.LIB_ID(lib, fpname))
        (x, y), rot = spec.FP_PLACE[ref]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        fp.SetReference(ref)
        fp.SetValue(c["val"])
        # sheetpath tstamps + component tstamp. Flat board -> sheetpath is "/".
        fp.SetPath(pcbnew.KIID_PATH("/" + spec.sym_uuid(ref)))
        board.Add(fp)
        fps[ref] = fp

    # ---- pad nets
    for ref, c in spec.build_board().items():
        if not c["on_board"]:
            continue
        for pad in fps[ref].Pads():
            num = pad.GetNumber()
            if num not in c["pins"]:
                raise RuntimeError("%s: footprint pad %r is not in the golden netlist"
                                   % (ref, num))
            n = board.FindNet(raw[c["pins"][num]])
            if n is None:
                raise RuntimeError("net %r missing from board" % c["pins"][num])
            pad.SetNet(n)

    # ---- Edge.Cuts
    x0, y0, x1, y1 = spec.BOARD_RECT
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pt(*a))
        seg.SetEnd(pt(*b))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        board.Add(seg)

    # ---- tracks
    ntracks = 0
    for net, layer, (ra, pa), (rb, pb) in spec.TRACKS:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(fps[ra].FindPadByNumber(pa).GetPosition())
        t.SetEnd(fps[rb].FindPadByNumber(pb).GetPosition())
        t.SetWidth(mm(spec.TRACK_W))
        t.SetLayer(LAYER[layer])
        t.SetNet(board.FindNet(raw[net]))
        board.Add(t)
        ntracks += 1

    # ---- GND stitching via (bonds the F.Cu and B.Cu zones after fill)
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pt(*spec.GND_VIA))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetWidth(mm(spec.VIA_D))
    via.SetDrill(mm(spec.VIA_DRILL))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(board.FindNet(raw["GND"]))
    board.Add(via)

    # ---- GND zones (NOT filled here)
    d = spec.ZONE_INSET
    corners = [(x0 + d, y0 + d), (x1 - d, y0 + d), (x1 - d, y1 - d), (x0 + d, y1 - d)]
    nzones = 0
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(board.FindNet(raw["GND"]))
        z.SetAssignedPriority(0)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetMinThickness(mm(0.2))
        z.SetLocalClearance(mm(0.3))
        z.SetIsFilled(False)
        z.SetNeedRefill(True)
        outline = z.Outline()
        outline.NewOutline()
        for cx, cy in corners:
            outline.Append(mm(cx), mm(cy))
        board.Add(z)
        nzones += 1

    return board, ntracks, nzones, raw


def check(board, raw):
    """Independent source of truth: the kicad-cli-exported netlist. Compare EVERY pad's
    net as the built BOARD reports it -- `pcb drc --schematic-parity` does NOT do this."""
    problems = []
    exported, comps = read_netlist(NET)
    seen = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            seen.setdefault(pad.GetNetname().lstrip("/"), []).append(
                (ref, pad.GetNumber()))
    seen = {k: sorted(v) for k, v in seen.items()}
    for name, pts in sorted(exported.items()):
        if name not in seen:
            problems.append("net %r has no pads on the board" % name)
        elif seen[name] != pts:
            problems.append("net %r: board pads %s != netlist %s"
                            % (name, seen[name], pts))
    for name, pts in sorted(seen.items()):
        if name not in exported:
            problems.append("board net %r (%s) is not in the netlist" % (name, pts))
    for ref, fpname in sorted(comps.items()):
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            problems.append("%s in netlist but not on the board" % ref)
            continue
        got = str(fp.GetFPID().GetUniStringLibId())
        if got != fpname:
            problems.append("%s footprint %r != netlist %r" % (ref, got, fpname))
        path = str(fp.GetPath().AsString())
        want = "/" + spec.sym_uuid(ref)
        if path != want:
            problems.append("%s path %r != %r (footprint<->symbol bijection)"
                            % (ref, path, want))
    return problems


def main():
    if not os.path.exists(NET):
        print("FAIL structural: %s missing. Run "
              "`kicad-cli sch export netlist` first." % NET)
        return 2
    board, ntracks, nzones, raw = build()
    problems = check(board, raw)
    if problems:
        print("FAIL (%d), board NOT saved:" % len(problems))
        for p in problems[:40]:
            print("   " + p)
        return 1
    nfp = len(list(board.GetFootprints()))
    pcbnew.SaveBoard(PCB, board)
    print("PASS - %s: %d footprints, %d tracks, 1 via, %d unfilled GND zones, "
          "%d nets (%s)"
          % (os.path.basename(PCB), nfp, ntracks, nzones, len(raw),
             ", ".join(sorted(raw.values()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
