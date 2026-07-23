#!/usr/bin/env python3
"""Fill copper zones on the saved board, as a SEPARATE process. Phase 0 link 5 of 8.

Why it is its own tool: calling ZONE_FILLER.Fill() inside the process that BUILT the board
segfaults headlessly (bootstrap IV.8). The fill must run against the board as loaded from
disk, in a process that did nothing else first. Splitting it also means a fill failure has
exactly one owner.

Acceptance: every zone on the board reports a non-empty filled polygon afterwards, and the
total filled area is > 0. A zone that "filled" to nothing is the failure this catches --
DRC passes vacuously on an empty zone, so the zone-area assertion is the real gate, not DRC.
Exit 0 only if it holds.

  "C:/Program Files/KiCad/10.0/bin/python.exe" fill_zones.py      # pcbnew tool: KiCad's interpreter ONLY
"""
import os, sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "env_proof.kicad_pcb")


def build():
    """Load, fill, save. Idempotent: re-filling an already-filled board is a no-op."""
    board = pcbnew.LoadBoard(PCB)
    zones = list(board.Zones())
    if not zones:
        return board, 0, 0.0

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    total_mm2 = 0.0
    for z in zones:
        for layer in z.GetLayerSet().Seq():
            poly = z.GetFilledPolysList(layer)
            if poly:
                total_mm2 += poly.Area() / 1e12  # nm^2 -> mm^2
    pcbnew.SaveBoard(PCB, board)
    return board, len(zones), total_mm2


def check(board, nzones, total_mm2):
    """Executable acceptance. Truth = the geometry pcbnew reads back off the saved board,
    not the filler's return value (which is True even when it fills nothing)."""
    problems = []
    if nzones == 0:
        problems.append("no zones on the board -- the Phase 0 proof requires at least one "
                        "GND zone, so this is a generator defect, not a fill defect")
        return problems

    reread = pcbnew.LoadBoard(PCB)
    for z in reread.Zones():
        name = z.GetNetname() or "<no net>"
        area = 0.0
        for layer in z.GetLayerSet().Seq():
            poly = z.GetFilledPolysList(layer)
            if poly:
                area += poly.Area() / 1e12
        if area <= 0.0:
            problems.append("zone on net %r filled to ZERO area -- DRC will pass vacuously "
                            "on this" % name)
    if total_mm2 <= 0.0:
        problems.append("total filled area is 0 mm2 across %d zone(s)" % nzones)
    return problems


def main():
    if not os.path.exists(PCB):
        print("FAIL structural: %s missing. Run gen_pcb.py first." % PCB)
        return 2
    board, nzones, total_mm2 = build()
    problems = check(board, nzones, total_mm2)
    if problems:
        print("FAIL (%d):" % len(problems))
        for p in problems[:40]:
            print("   " + p)
        return 1
    print("PASS - filled %d zone(s), %.2f mm2 total copper, saved to %s"
          % (nzones, total_mm2, os.path.basename(PCB)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
