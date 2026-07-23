#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate docs/PIN_MAPS.md from board_spec.py.  Stdlib-only, zero-arg.

PIN_MAPS.md is a BUILD ARTIFACT.  Never hand-edit it -- fix this generator.
Its only job is to be easy for a human to check against a datasheet, line by
line, at the G1 gate.  So:

  * TIER-C parts (borrowed pinouts) come FIRST, in their own section, because
    they are the claims most likely to be wrong.
  * Every pin map prints the symbol's OWN pin NAME next to our net, so a
    reviewer can see "pin 6 = HV" and "pin 6 -> HV_POS" on the same line
    without opening KiCad.
  * Pin names come from the .kicad_sym on disk, so this document cannot drift
    from the library the schematic will actually be built against.
  * Deliberately-unconnected pads are printed as (nc), never omitted, because
    an omission is indistinguishable from a mistake.

    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/gen_pin_maps.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import board_spec as BS                                            # noqa: E402
from board_spec_parts import PARTS, derate_of                      # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "PIN_MAPS.md"))


def symbol_pin_names(symref):
    """{number: name} read from the .kicad_sym on disk. Follows `extends`."""
    nickname, name = symref.split(":", 1)
    path = BS._lib_path(nickname)
    with io.open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = BS._top_level_symbol_blocks(text)
    seen = set()
    while name in blocks and name not in seen:
        seen.add(name)
        body = blocks[name]
        pairs = re.findall(
            r'\(name "([^"]*)"\s*\n\s*\(effects[\s\S]{0,200}?\)\s*\n\s*\)\s*\n'
            r'\s*\(number "([^"]*)"', body)
        if pairs:
            return {n: nm for nm, n in pairs}
        ext = re.search(r'\(extends "([^"]+)"\)', body)
        if not ext:
            break
        name = ext.group(1)
    return {}


def _pad_key(p):
    m = re.match(r"^(\D*)(\d*)$", p)
    return (m.group(1), int(m.group(2)) if m.group(2) else 0)


def pin_table(c, names):
    rows = ["| pad | symbol pin name | net | |",
            "|---|---|---|---|"]
    for pad in sorted(c["pins"], key=_pad_key):
        net = c["pins"][pad]
        nm = names.get(pad, "")
        if net is None:
            rows.append("| `%s` | `%s` | *(nc)* | deliberately unconnected |" % (pad, nm))
        else:
            flag = ""
            if BS.is_hv_net(net):
                flag = "**HV**"
            rows.append("| `%s` | `%s` | `%s` | %s |" % (pad, nm, net, flag))
    return "\n".join(rows)


def emit_component(c, board):
    p = PARTS[c["fields"]["PartClass"]]
    names = symbol_pin_names(c["sym"])
    out = []
    out.append("#### `%s` &mdash; %s" % (c["ref"], c["val"]))
    out.append("")
    out.append("| | |")
    out.append("|---|---|")
    out.append("| symbol | `%s` |" % c["sym"])
    out.append("| footprint | %s |" % ("`%s`" % c["fp"] if c["fp"] else
                                       "*(none &mdash; panel / off-board part)*"))
    out.append("| part class | `%s` &nbsp; **TIER %s** |"
               % (c["fields"]["PartClass"], c["fields"]["Tier"]))
    out.append("| manufacturer | %s |" % c["fields"]["Mfr"])
    out.append("| MPN status | `%s` |" % c["fields"]["MPN_STATUS"])
    out.append("| voltage rating | %s V working, derated to %.0f V by this design |"
               % (c["fields"]["V_RATING"],
                  p["vmax"] * derate_of(c["fields"]["PartClass"])))
    out.append("| DNP | %s |" % ("**YES**" if c["dnp"] else "no"))
    out.append("")
    out.append("> **CITATION.** %s" % p["cite"].replace("\n", " "))
    out.append("")
    if c["fields"].get("Notes"):
        out.append("> **DESIGN NOTE.** %s" % c["fields"]["Notes"])
        out.append("")
    out.append(pin_table(c, names))
    out.append("")
    return "\n".join(out)


HEADER = """# PIN_MAPS &mdash; every part's pin map, for a human to check line by line

> **GENERATED FILE.** Produced by `hardware/hvctl/gen_pin_maps.py` from
> `hardware/hvctl/board_spec.py` and the symbol libraries on disk.
> **Never hand-edit it.** Fix the generator and regenerate.
>
> Regenerate with:
> ```
> "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/gen_pin_maps.py
> ```

## What this document is for

Pin maps are the **highest-consequence, lowest-feedback work in the project**.
Every other check in this repo &mdash; ERC, DRC, the netlist parity check, the
golden-netlist domain assertions &mdash; is *blind* to a wrong pin map, because
a wrong pin map produces a netlist that is perfectly self-consistent and a board
that is perfectly, self-consistently wrong.

**This document is the only gate that can catch that, and the only instrument
is a human with a datasheet.** It is laid out for exactly that job.

## How to review it, in order

1. **Section 1 first.** Those are the parts whose pinout is a *claim* that two
   different part numbers share a package pinout. Nobody has checked those
   claims against a datasheet. They are the most likely place a defect is
   hiding, and several of them are safety elements.
2. **Section 2 next.** One part, two symbols, and it is the 1 kV source. If
   `U1`/`U2` are wrong, everything downstream is wrong.
3. **Section 3 last**, and it can be sampled rather than read exhaustively:
   these pin maps were transcribed from a KiCad stock symbol that is itself a
   transcription of a datasheet. Second-hand, but *checkable* &mdash; the file
   is on disk and `board_spec.py` re-reads it on every run.

## The three tiers

| Tier | What it means | How much to trust it |
|---|---|---|
| **A** | Project symbol generated in this repo from a **dated datasheet read**. | Highest available. Still transcription. |
| **B** | KiCad 10.0.3 **stock symbol**, read off disk this session. | Second-hand: the KiCad library team transcribed the datasheet, not us. |
| **C** | **Borrowed** symbol &mdash; a pin-compatible sibling used for a part the stock library does not have. | **A CLAIM, NOT A READ.** Check every one. |

## The mechanical check that already runs

`board_spec.py` re-parses each `.kicad_sym` on disk on every run and asserts
**set equality both ways** between the pin numbers in the hand-authored map and
the pin numbers the symbol actually has: no invented pin, no forgotten pin, and
every deliberately-unconnected pad explicitly declared.

**That check cannot see whether the symbol matches the physical part.**
That is what you are here to do.

## The one pin fact that would have been got wrong by assumption

`Switch:SW_SPDT` &mdash; **the common is pin 2**, not pin 1. Pins 1 and 3 are
the throws. Established from pin *geometry* in `Switch.kicad_sym` (pin 2 sits
alone on the opposite side of the symbol). Assuming "pin 1 is the common" would
have swapped a throw with the common on every HV pole of the mode switch.

---
"""


def _dup_note(dup):
    """Say WHICH refs were suppressed. 'de-duplicated' with no list is how a
    reviewer ends up believing a part was shown when it was not."""
    if not dup:
        return ""
    out = ["", "**Identical pin maps suppressed** (same part class, same pad "
           "set as the entry above &mdash; the refdes list is given so nothing "
           "is silently missing from this document):", ""]
    for key, refs in sorted(dup.items()):
        out.append("* `%s` pads `%s` &mdash; also %s"
                   % (key[0], ",".join(key[1]), ", ".join("`%s`" % r for r in refs)))
    out.append("")
    return "\n".join(out)


def main():
    board = BS.build_board()
    comps = board["components"]
    tiers = {"A": [], "B": [], "C": []}
    for c in comps:
        tiers[c["fields"]["Tier"]].append(c)

    # only one representative entry per (part class, distinct pin map) for the
    # bulk passives, or the document becomes unreviewable.
    def dedupe(cs):
        seen, keep, dup = {}, [], {}
        for c in cs:
            key = (c["fields"]["PartClass"], tuple(sorted(c["pins"].keys())))
            if c["fields"]["PartClass"] in ("R_LV", "C_LV", "R_HV_2512",
                                            "R_HV_1206", "TP", "LED", "C_BULK",
                                            "L_PWR", "FB", "D_SCH", "R_HV_AXIAL",
                                            "D_ZEN", "PFUSE", "Q_NMOS"):
                if key in seen:
                    dup.setdefault(key, []).append(c["ref"])
                    continue
                seen[key] = c["ref"]
            keep.append(c)
        return keep, dup

    body = [HEADER]
    body.append("\n# 1. TIER C &mdash; BORROWED PINOUTS. **CHECK THESE FIRST.**\n")
    body.append("Each of these is the claim *'part X shares part Y's package "
                "pinout'*. **No datasheet was opened to verify any of them.** "
                "The `symbol` row names the symbol whose numbering was used; "
                "the `%s` row names the part that will actually be soldered "
                "down.\n" % "manufacturer")
    kc, dupc = dedupe(sorted(tiers["C"], key=lambda c: c["ref"]))
    for c in kc:
        body.append(emit_component(c, board))
    body.append(_dup_note(dupc))

    body.append("\n# 2. TIER A &mdash; the iseg HV modules\n")
    body.append("These two are the 1 kV source. The pin map below must be "
                "checked against **iseg APS technical documentation v2.5, "
                "2024-08-20, Table 4, page 9** &mdash; the actual table, not "
                "`docs/PART_iseg_APS.md`, which is itself a transcription.\n")
    body.append("Three facts on this part make a pin-map error unusually "
                "dangerous, and all three are in `docs/PART_iseg_APS.md` "
                "carrying `[skeptic x3]`:\n\n"
                "* pin 4 `/ON` is **active low, and an OPEN PIN MEANS HV ON**;\n"
                "* pin 2 `VSET` has an **internal 10 k pull-up to Vref, so an "
                "open VSET node commands FULL SCALE**;\n"
                "* pin 6 `HV` is **not internally limited** &mdash; Vset above "
                "Vref drives the output above Vnom.\n\n"
                "A swapped pin 2 / pin 5, or a swapped pin 5 / pin 6, is "
                "therefore not a wiring inconvenience.\n")
    for c in sorted(tiers["A"], key=lambda c: c["ref"]):
        body.append(emit_component(c, board))

    body.append("\n# 3. TIER B &mdash; KiCad stock symbols\n")
    body.append("Read off `C:/Program Files/KiCad/10.0/share/kicad/symbols/` "
                "this session. Repeated pin maps (every 0603 resistor, every "
                "test point) are printed once.\n")
    kb, dupb = dedupe(sorted(tiers["B"], key=lambda c: c["ref"]))
    for c in kb:
        body.append(emit_component(c, board))
    body.append(_dup_note(dupb))

    # ---------------- summary tables the reviewer can tick through ----------
    body.append("\n# 4. Review checklist\n")
    body.append("| # | Part class | Tier | Symbol | Instances | Checked? |")
    body.append("|---|---|---|---|---|---|")
    counts = {}
    for c in comps:
        counts.setdefault(c["fields"]["PartClass"], []).append(c["ref"])
    for i, (pc, refs) in enumerate(sorted(counts.items(),
                                          key=lambda kv: (PARTS[kv[0]]["tier"] != "C",
                                                          PARTS[kv[0]]["tier"] != "A",
                                                          kv[0])), 1):
        body.append("| %d | `%s` | **%s** | `%s` | %d (%s) | &#9744; |"
                    % (i, pc, PARTS[pc]["tier"], PARTS[pc]["sym"], len(refs),
                       refs[0] + ("&hellip;" if len(refs) > 1 else "")))
    body.append("")

    body.append("\n# 5. What this document does NOT cover\n")
    body.append("Recorded rather than left to be discovered:\n")
    for k, why in BS.NOT_STRUCTURALLY_EXPRESSIBLE:
        body.append("* **%s** &mdash; %s" % (k, why))
    body.append("")
    body.append("")
    body.append("## Deviations and unresolved cross-document conflicts\n")
    body.append("Reproduced verbatim from `board_spec.py` section 3 so this "
                "document stands alone at the review gate:\n")
    doc = BS.__doc__ or ""
    if "D-1" in doc:
        seg = doc[doc.index("D-1"):]
        seg = seg[:seg.index("=====")] if "=====" in seg else seg
        body.append("```\n" + seg.rstrip() + "\n```")
    body.append("")
    body.append("Plus the deviations and unresolved cross-document conflicts "
                "recorded in `board_spec.py` section 3 (`D-1` &hellip; `D-6`). "
                "**`D-1` (bleed topology and value) and `D-4` (the ESP32 GPIO "
                "remap) both change the netlist and both need a G1 decision.**")
    body.append("")

    txt = "\n".join(body)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    print("wrote %s" % OUT)
    print("  %d components, %d tier-A, %d tier-B, %d tier-C"
          % (len(comps), len(tiers["A"]), len(tiers["B"]), len(tiers["C"])))
    print("  %d pin maps printed (%d de-duplicated bulk passives suppressed)"
          % (len(kc) + len(tiers["A"]) + len(kb),
             len(comps) - len(kc) - len(tiers["A"]) - len(kb)))
    print("  %d lines" % (txt.count("\n") + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
