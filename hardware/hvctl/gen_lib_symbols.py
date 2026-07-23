#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_lib_symbols.py -- emit hardware/hvctl/lib/iseg.kicad_sym (+ sym-lib-table, fp-lib-table).

WHAT THIS IS
    A .kicad_sym file is s-expression TEXT. There is no schematic/symbol Python API in KiCad,
    so this generator is deliberately STDLIB-ONLY and runs on any Python 3.8+. It must NOT
    grow a third-party dependency, and it must NOT import pcbnew.

    The emitted file is a BUILD ARTIFACT. Never hand-edit hardware/hvctl/lib/iseg.kicad_sym.
    Fix this generator and re-run.

DETERMINISM
    "Regenerate and `git diff`" is the regression test, so the output must be byte-identical
    across runs and machines. Note for the reader who came here looking for uuid5: the
    .kicad_sym schema (version 20251024) carries NO uuid fields at all -- verified by grepping
    the KiCad 10.0 stock libraries, `(uuid` count == 0 in Device.kicad_sym. Determinism here
    therefore comes from (i) no timestamps, (ii) no dict/set iteration order dependence,
    (iii) fixed float formatting. `stable_uuid()` is provided anyway because the *schematic*
    generator downstream needs it and must never reach for uuid4; check_determinism() below
    proves the byte-identity property directly, which is the stronger statement.

SCHEMA PROVENANCE
    (version 20251024) / (generator "kicad_symbol_editor") / (generator_version "10.0")
    and the tab-indented layout were copied from a library KiCad 10.0 itself wrote:
        C:/Program Files/KiCad/10.0/share/kicad/symbols/Regulator_Linear.kicad_sym
    Nothing about the format is invented. The inverted-pin-name syntax `~{ON}` was likewise
    copied from KiCad's own 74xx.kicad_sym (e.g. `(name "~{OE}"`), not guessed.

EXIT CODES
    0  ok
    1  verification failed  (parsed content disagrees with PIN_MAP, or KiCad rejected the lib)
    2  structural failure   (cannot write, cannot parse own output, kicad-cli not found)
    3  legibility failure   (pin/text geometry would render illegibly)
"""

import os
import re
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(HERE, "lib")
OUT_SYM = os.path.join(LIB_DIR, "iseg.kicad_sym")
OUT_SYM_TABLE = os.path.join(LIB_DIR, "sym-lib-table")
OUT_FP_TABLE = os.path.join(LIB_DIR, "fp-lib-table")

# kicad-cli is not on PATH on this machine (see CLAUDE.md rule 2). Absolute path, with a
# short search list so the tool keeps working if KiCad moves or on another host.
KICAD_CLI_CANDIDATES = [
    r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe",
    r"C:/Program Files/KiCad/9.0/bin/kicad-cli.exe",
    "/usr/bin/kicad-cli",
    "/usr/local/bin/kicad-cli",
]

# Fixed namespace for deterministic ids. NEVER uuid4 anywhere in this project.
NS_ISEG = uuid.UUID("6f3b6b4a-1f2c-5c8e-9a4d-0d1e2f3a4b5c")


def stable_uuid(semantic_key):
    """Deterministic id from a semantic key. Same key -> same id, forever, on every host."""
    return str(uuid.uuid5(NS_ISEG, semantic_key))


# ---------------------------------------------------------------------------------------
# GROUND TRUTH
# ---------------------------------------------------------------------------------------
# Source of truth for the pinout, transcribed by hand and re-read from the PDF:
#   iseg APS technical documentation v2.5, 2024-08-20, Table 4, page 9
#   references/iseg_manual_APS_en.pdf  (page footer: "Last changed on: 2024-08-20", 9/10)
# Table 4 lists row "3/7  GND  Ground" -- pins 3 and 7 are BOTH ground, and the note
# "Case is connected to GND" is on the same page.
#
# Pin 4 /ON is ACTIVE LOW: "LOW or n.c. -> HV ON", "HIGH -> HV OFF". The leading slash in the
# manual's "/ON" is rendered in KiCad as an overbar via the name "~{ON}".
#
# Fields: number, name, electrical type, side ('L'/'R'), y position (mm).
PIN_MAP = [
    ("1", "+VIN",  "power_in", "L",  10.16),   # supply: +5 V (05 variants) / +12 V (12 variants)
    ("2", "VSET",  "input",    "L",   5.08),   # 0..2.5 V (5 V fam) / 0..5 V (12 V fam)
    ("4", "~{ON}", "input",    "L",   2.54),   # TTL, ACTIVE LOW enable. LOW or n.c. -> HV ON
    ("3", "GND",   "power_in", "L",  -5.08),   # Table 4 row "3/7 GND"
    ("7", "GND",   "power_in", "L",  -7.62),   # Table 4 row "3/7 GND" -- real pad, NOT stacked
    ("5", "VMON",  "output",   "R",  10.16),   # 0..2.5 V / 0..5 V, tracks |Vout| over 0..Vnom
    ("6", "HV",    "output",   "R", -10.16),   # high voltage output, polarity factory-fixed
]

# HV pin 6 sits alone on the bottom row, below both grounds, inside an L-shaped "fence"
# polyline that quarantines the bottom-right corner of the body. Nothing else may enter that
# region -- check_hv_isolation() enforces it, so the isolation is a gate and not a hope.
FENCE_Y = -8.89      # fence horizontal run
FENCE_X = 2.54       # fence vertical run

# The two GND pins are deliberately NOT stacked-and-hidden (the usual KiCad idiom for
# duplicated grounds). Both 3 and 7 are physical pads that must be soldered; a hidden pin
# disappears from the SVG/plot, is easy to leave unrouted, and defeats a schematic<->footprint
# pad-parity check. They are therefore two visible power_in pins at distinct y, same name.
# `duplicate_pin_numbers_are_jumpers` stays `no` -- the numbers differ, so nothing is duplicated.

DATASHEET_CITATION = "iseg APS technical documentation v2.5, 2024-08-20"

# Local, read-only copy of the manual. Relative to the eventual .kicad_pro (see the note at
# the bottom of this file about where the lib tables must end up).
DATASHEET_URI = "${KIPRJMOD}/../../references/iseg_manual_APS_en.pdf"

# CROSS-GENERATOR COUPLING -- read before changing.
# The footprint library/name this symbol expects. The footprint generator MUST emit exactly
# this name into hardware/hvctl/lib/iseg.pretty/ or every netlist import silently drops the
# part. The base name is taken from the sibling 3D generator (gen_3d_model.py writes
# lib/iseg.3dshapes/iseg_APS_THT.{step,wrl}); KiCad's convention is footprint name ==
# 3D model base name, so all three agree on "iseg_APS_THT".
FOOTPRINT = "iseg:iseg_APS_THT"
FP_FILTERS = "iseg*APS*"

# Body rectangle (mm). Pins sit 2.54 outside the left/right edges.
BODY_X = 10.16
BODY_Y = 12.7
PIN_LEN = 2.54
PIN_NAME_OFFSET = 0.508
FONT = 1.27

KEYWORDS = "iseg APS high voltage DC-DC HV module programmable power supply"

DESC_COMMON = (
    "iseg APS series programmable DC-HV converter module, 7-pin, 39.6 x 15.7 x 11 mm. "
    "Vset 0..Vref -> |Vout| 0..Vnom. /ON is active low (LOW or n.c. = HV ON). "
    "WARNING: output is NOT internally limited -- Vset above Vref drives |Vout| above Vnom; "
    "VSET has an internal 10k pull-up to Vref, so an OPEN VSET NODE COMMANDS FULL SCALE."
)

SYMBOLS = [
    {
        "name": "APS_HV_MODULE",
        "extends": None,
        "item_code": "AP______x__",
        "polarity": "TEMPLATE - factory fixed at order time; x = P (positive) or N (negative)",
        "vnom": "TEMPLATE - 200 / 400 / 600 / 800 / 1000 V",
        "vin": "TEMPLATE - 5 V (0.5 W family) or 12 V (1 W family)",
        "vref": "TEMPLATE - 2.5 V (5 V family) or 5 V (12 V family)",
        "description": "Generic (polarity unspecified). " + DESC_COMMON,
    },
    {
        "name": "APS_HV_MODULE_P",
        "extends": "APS_HV_MODULE",
        "item_code": "AP______P__",
        "polarity": "POSITIVE (item code letter P) - factory fixed, not switchable",
        "vnom": "TEMPLATE - 200 / 400 / 600 / 800 / 1000 V",
        "vin": "TEMPLATE - 5 V (0.5 W family) or 12 V (1 W family)",
        "vref": "TEMPLATE - 2.5 V (5 V family) or 5 V (12 V family)",
        "description": "POSITIVE polarity variant. " + DESC_COMMON,
    },
    {
        "name": "APS_HV_MODULE_N",
        "extends": "APS_HV_MODULE",
        "item_code": "AP______N__",
        "polarity": "NEGATIVE (item code letter N) - factory fixed, not switchable",
        "vnom": "TEMPLATE - 200 / 400 / 600 / 800 / 1000 V",
        "vin": "TEMPLATE - 5 V (0.5 W family) or 12 V (1 W family)",
        "vref": "TEMPLATE - 2.5 V (5 V family) or 5 V (12 V family)",
        "description": "NEGATIVE polarity variant. " + DESC_COMMON,
    },
]


# ---------------------------------------------------------------------------------------
# EMITTER
# ---------------------------------------------------------------------------------------

def fmt(v):
    """KiCad-style number formatting: no trailing zeros, no '-0', deterministic."""
    s = "{:.6f}".format(float(v)).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


class Emit(object):
    def __init__(self):
        self.lines = []

    def add(self, depth, text):
        self.lines.append("\t" * depth + text)

    def text(self):
        return "\n".join(self.lines) + "\n"


def emit_effects(e, d, italic=False):
    e.add(d, "(effects")
    e.add(d + 1, "(font")
    e.add(d + 2, "(size %s %s)" % (fmt(FONT), fmt(FONT)))
    if italic:
        e.add(d + 2, "(italic yes)")
    e.add(d + 1, ")")
    e.add(d, ")")


def emit_property(e, d, name, value, at, hide, italic=False):
    e.add(d, "(property %s %s" % (q(name), q(value)))
    e.add(d + 1, "(at %s %s %s)" % (fmt(at[0]), fmt(at[1]), fmt(at[2])))
    e.add(d + 1, "(show_name no)")
    e.add(d + 1, "(do_not_autoplace no)")
    if hide:
        e.add(d + 1, "(hide yes)")
    emit_effects(e, d + 1, italic=italic)
    e.add(d, ")")


def pin_sort_key(number):
    """Natural pin-number order (KiCad's storage order). Handles A1/2/10 style numbers too."""
    return (0, int(number), "") if number.isdigit() else (1, 0, number)


def emit_pin(e, d, number, name, etype, side, y):
    if side == "L":
        x, rot = -(BODY_X + PIN_LEN), 0
    else:
        x, rot = (BODY_X + PIN_LEN), 180
    e.add(d, "(pin %s line" % etype)
    e.add(d + 1, "(at %s %s %s)" % (fmt(x), fmt(y), fmt(rot)))
    e.add(d + 1, "(length %s)" % fmt(PIN_LEN))
    e.add(d + 1, "(name %s" % q(name))
    emit_effects(e, d + 2)
    e.add(d + 1, ")")
    e.add(d + 1, "(number %s" % q(number))
    emit_effects(e, d + 2)
    e.add(d + 1, ")")
    e.add(d, ")")


def emit_props_block(e, d, spec):
    """Property block shared by root and derived symbols (KiCad repeats them on derived)."""
    emit_property(e, d, "Reference", "U", (0, BODY_Y + 5.08, 0), hide=False)
    emit_property(e, d, "Value", spec["name"], (0, BODY_Y + 2.54, 0), hide=False)
    emit_property(e, d, "Footprint", FOOTPRINT, (0, -(BODY_Y + 2.54), 0), hide=True, italic=True)
    emit_property(e, d, "Datasheet", DATASHEET_URI, (0, -(BODY_Y + 5.08), 0), hide=True)
    emit_property(e, d, "Description", spec["description"], (0, 0, 0), hide=True)
    # CANONICAL ORDER (do not rearrange): KiCad 10.0's serializer writes the five mandatory
    # fields, then user fields in insertion order, then ki_* LAST. Verified by round-tripping
    # through `kicad-cli sym upgrade` and byte-comparing -- see check_kicad_writer_agrees.
    # Order-information template fields. Left as templates on the generic symbol so a
    # schematic instance is forced to fill them in rather than silently inheriting a lie.
    emit_property(e, d, "Item Code", spec["item_code"], (0, 0, 0), hide=True)
    emit_property(e, d, "Polarity", spec["polarity"], (0, 0, 0), hide=True)
    emit_property(e, d, "Vnom", spec["vnom"], (0, 0, 0), hide=True)
    emit_property(e, d, "Vin_nom", spec["vin"], (0, 0, 0), hide=True)
    emit_property(e, d, "Vref_fullscale", spec["vref"], (0, 0, 0), hide=True)
    emit_property(e, d, "Datasheet_Rev", DATASHEET_CITATION, (0, 0, 0), hide=True)
    emit_property(e, d, "ki_keywords", KEYWORDS, (0, 0, 0), hide=True)
    emit_property(e, d, "ki_fp_filters", FP_FILTERS, (0, 0, 0), hide=True)


def emit_root_symbol(e, d, spec):
    e.add(d, "(symbol %s" % q(spec["name"]))
    # NOTE: no (pin_names (offset ...)) block. PIN_NAME_OFFSET == 0.508 is KiCad's default and
    # KiCad's own writer OMITS the block when the value is default -- proven by
    # check_kicad_writer_agrees(), which round-trips through `kicad-cli sym upgrade` and
    # byte-compares. Emitting it produced a spurious diff on every GUI save.
    e.add(d + 1, "(exclude_from_sim no)")
    e.add(d + 1, "(in_bom yes)")
    e.add(d + 1, "(on_board yes)")
    e.add(d + 1, "(in_pos_files yes)")
    e.add(d + 1, "(duplicate_pin_numbers_are_jumpers no)")
    emit_props_block(e, d + 1, spec)

    # unit 1, body-only sub-symbol (KiCad convention: <name>_0_1 holds graphics)
    e.add(d + 1, "(symbol %s" % q(spec["name"] + "_0_1"))
    e.add(d + 2, "(rectangle")
    e.add(d + 3, "(start %s %s)" % (fmt(-BODY_X), fmt(BODY_Y)))
    e.add(d + 3, "(end %s %s)" % (fmt(BODY_X), fmt(-BODY_Y)))
    e.add(d + 3, "(stroke")
    e.add(d + 4, "(width 0.254)")
    e.add(d + 4, "(type default)")
    e.add(d + 3, ")")
    e.add(d + 3, "(fill")
    e.add(d + 4, "(type background)")
    e.add(d + 3, ")")
    e.add(d + 2, ")")
    # HV fence: an L-shaped polyline that visually quarantines the bottom-right corner where
    # pin 6 lives, so the HV pin does not read as just another low-voltage signal.
    e.add(d + 2, "(polyline")
    e.add(d + 3, "(pts")
    # KiCad's writer puts every (xy ..) of a pts list on ONE line. Matching it exactly.
    e.add(d + 4, " ".join("(xy %s %s)" % (fmt(x), fmt(y)) for x, y in
                          [(BODY_X, FENCE_Y), (FENCE_X, FENCE_Y), (FENCE_X, -BODY_Y)]))
    e.add(d + 3, ")")
    e.add(d + 3, "(stroke")
    e.add(d + 4, "(width 0.254)")
    e.add(d + 4, "(type default)")
    e.add(d + 3, ")")
    e.add(d + 3, "(fill")
    e.add(d + 4, "(type none)")
    e.add(d + 3, ")")
    e.add(d + 2, ")")
    # Deliberately NO free-standing "HV" text label here. The first render carried one and it
    # overprinted the pin-6 name, which already reads "HV" -- the fence plus the pin name is
    # unambiguous, and one glyph in that corner is better than two on top of each other.
    e.add(d + 1, ")")

    # unit 1, pins
    # KiCad stores pins sorted by pin number, not in the order you typed them. PIN_MAP is kept
    # in schematic-layout order because that is how a human checks it against Table 4; the sort
    # happens here so the file matches what the GUI would write.
    e.add(d + 1, "(symbol %s" % q(spec["name"] + "_1_1"))
    for number, name, etype, side, y in sorted(PIN_MAP, key=lambda p: pin_sort_key(p[0])):
        emit_pin(e, d + 2, number, name, etype, side, y)
    e.add(d + 1, ")")

    e.add(d + 1, "(embedded_fonts no)")
    e.add(d, ")")


def emit_derived_symbol(e, d, spec):
    e.add(d, "(symbol %s" % q(spec["name"]))
    e.add(d + 1, "(extends %s)" % q(spec["extends"]))
    emit_props_block(e, d + 1, spec)
    e.add(d + 1, "(embedded_fonts no)")
    e.add(d, ")")


def build_library_text():
    e = Emit()
    e.add(0, "(kicad_symbol_lib")
    e.add(1, "(version 20251024)")
    e.add(1, '(generator "kicad_symbol_editor")')
    e.add(1, '(generator_version "10.0")')
    # KiCad stores symbols sorted by name, so emit them sorted -- otherwise the first GUI save
    # reshuffles the file and produces a diff that has nothing to do with an engineering change.
    for spec in sorted(SYMBOLS, key=lambda s: s["name"]):
        if spec["extends"] is None:
            emit_root_symbol(e, 1, spec)
        else:
            emit_derived_symbol(e, 1, spec)
    e.add(0, ")")
    return e.text()


SYM_LIB_TABLE = """(sym_lib_table
\t(version 7)
\t(lib (name "iseg") (type "KiCad") (uri "${KIPRJMOD}/lib/iseg.kicad_sym") (options "") (descr "iseg APS programmable HV converter modules (project library)"))
)
"""

FP_LIB_TABLE = """(fp_lib_table
\t(version 7)
\t(lib (name "iseg") (type "KiCad") (uri "${KIPRJMOD}/lib/iseg.pretty") (options "") (descr "iseg APS HV module footprints (project library)"))
)
"""


# ---------------------------------------------------------------------------------------
# MINIMAL S-EXPRESSION READER  (independent of the emitter -- it does not share any code
# with build_library_text(), so a bug in one does not cancel out in the other)
# ---------------------------------------------------------------------------------------

_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+')


def sexp_parse(text):
    stack = [[]]
    for m in _TOKEN.finditer(text):
        t = m.group(0)
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            if len(stack) == 1:
                raise ValueError("unbalanced ')' at offset %d" % m.start())
            stack.pop()
        elif t.startswith('"'):
            stack[-1].append(("str", t[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        else:
            stack[-1].append(("atom", t))
    if len(stack) != 1:
        raise ValueError("unbalanced '(' -- %d unclosed" % (len(stack) - 1))
    if len(stack[0]) != 1:
        raise ValueError("expected exactly one top-level form, got %d" % len(stack[0]))
    return stack[0][0]


def head(node):
    if isinstance(node, list) and node and isinstance(node[0], tuple):
        return node[0][1]
    return None


def val(node, i):
    x = node[i]
    return x[1] if isinstance(x, tuple) else None


def children(node, tag):
    return [c for c in node if isinstance(c, list) and head(c) == tag]


# ---------------------------------------------------------------------------------------
# ACCEPTANCE CHECKS
# ---------------------------------------------------------------------------------------

class Fail(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, msg)
        self.code = code


def find_kicad_cli():
    for p in KICAD_CLI_CANDIDATES:
        if os.path.exists(p):
            return p
    from shutil import which
    w = which("kicad-cli") or which("kicad-cli.exe")
    if w:
        return w
    return None


def check_parses_and_matches_pinmap(path):
    """(a) Re-parse our own output and compare every pin against the literal PIN_MAP."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        root = sexp_parse(text)
    except ValueError as ex:
        raise Fail(2, "own s-expression reader could not parse the file we just wrote: %s" % ex)

    if head(root) != "kicad_symbol_lib":
        raise Fail(2, "top-level form is %r, expected kicad_symbol_lib" % head(root))

    ver = [c for c in root if head(c) == "version"]
    if not ver or val(ver[0], 1) != "20251024":
        raise Fail(1, "version is not 20251024 (must match what KiCad 10.0 writes)")

    syms = {}
    for c in children(root, "symbol"):
        syms[val(c, 1)] = c
    expected = set(s["name"] for s in SYMBOLS)
    if set(syms) != expected:
        raise Fail(1, "symbol set mismatch: got %s expected %s"
                   % (sorted(syms), sorted(expected)))

    root_sym = syms["APS_HV_MODULE"]

    # collect pins from the nested unit sub-symbols
    pins = []
    for sub in children(root_sym, "symbol"):
        for p in children(sub, "pin"):
            etype = val(p, 1)
            at = children(p, "at")[0]
            x, y = float(val(at, 1)), float(val(at, 2))
            rot = float(val(at, 3))
            name = val(children(p, "name")[0], 1)
            num = val(children(p, "number")[0], 1)
            hidden = bool(children(p, "hide"))
            pins.append(dict(num=num, name=name, etype=etype, x=x, y=y, rot=rot, hide=hidden))

    by_num = {}
    for p in pins:
        by_num.setdefault(p["num"], []).append(p)

    problems = []
    for number, name, etype, side, y in PIN_MAP:
        got = by_num.get(number, [])
        if len(got) != 1:
            problems.append("pin %s appears %d times, expected exactly 1" % (number, len(got)))
            continue
        g = got[0]
        if g["name"] != name:
            problems.append("pin %s name %r != %r (PIN_MAP / Table 4)" % (number, g["name"], name))
        if g["etype"] != etype:
            problems.append("pin %s type %r != %r" % (number, g["etype"], etype))
        if abs(g["y"] - y) > 1e-6:
            problems.append("pin %s y %.4f != %.4f" % (number, g["y"], y))
        want_x = -(BODY_X + PIN_LEN) if side == "L" else (BODY_X + PIN_LEN)
        if abs(g["x"] - want_x) > 1e-6:
            problems.append("pin %s x %.4f != %.4f (wrong side, or mirrored)" % (number, g["x"], want_x))
        want_rot = 0.0 if side == "L" else 180.0
        if abs(g["rot"] - want_rot) > 1e-6:
            problems.append("pin %s rotation %.1f != %.1f (pin would point into the body)"
                            % (number, g["rot"], want_rot))
        if g["hide"]:
            problems.append("pin %s is hidden; every APS pad is a real solder joint" % number)

    extra = set(by_num) - set(p[0] for p in PIN_MAP)
    if extra:
        problems.append("unexpected pin numbers in file: %s" % sorted(extra))

    # both GNDs must be present as separate, non-coincident pins
    gnd = [p for p in pins if p["name"] == "GND"]
    if len(gnd) != 2:
        problems.append("expected exactly 2 GND pins (Table 4 row '3/7 GND'), got %d" % len(gnd))
    elif abs(gnd[0]["y"] - gnd[1]["y"]) < 1e-6 and abs(gnd[0]["x"] - gnd[1]["x"]) < 1e-6:
        problems.append("GND pins 3 and 7 are stacked at the same point; both must be visible")

    # /ON must carry the KiCad overbar syntax
    on = [p for p in pins if p["num"] == "4"]
    if on and not (on[0]["name"].startswith("~{") and on[0]["name"].endswith("}")):
        problems.append("pin 4 name %r lacks the ~{...} overbar form KiCad uses for active low"
                        % on[0]["name"])

    # derived symbols must extend the root and must NOT redeclare pins
    for spec in SYMBOLS:
        if spec["extends"] is None:
            continue
        s = syms[spec["name"]]
        ext = children(s, "extends")
        if not ext or val(ext[0], 1) != spec["extends"]:
            problems.append("%s does not (extends %r)" % (spec["name"], spec["extends"]))
        if children(s, "symbol"):
            problems.append("%s redeclares geometry; derived symbols must inherit it"
                            % spec["name"])
        names = set(val(p, 1) for p in children(s, "property"))
        for req in ("Description", "Datasheet", "ki_keywords", "Value", "Reference"):
            if req not in names:
                problems.append("%s missing required field %r" % (spec["name"], req))

    if problems:
        raise Fail(1, "PIN_MAP / structure mismatch:\n  - " + "\n  - ".join(problems))
    return pins


def check_legibility(pins):
    """(c) Geometry sanity that a human would otherwise have to catch by eye."""
    problems = []
    # KiCad's stroke font advance is ~0.7 em for uppercase; overbar braces do not render.
    def textw(name):
        visible = name.replace("~{", "").replace("}", "")
        return len(visible) * FONT * 0.7

    for p in pins:
        if abs(round(p["x"] / 2.54) * 2.54 - p["x"]) > 1e-6 or \
           abs(round(p["y"] / 2.54) * 2.54 - p["y"]) > 1e-6:
            problems.append("pin %s not on the 2.54 mm grid (%.4f, %.4f)"
                            % (p["num"], p["x"], p["y"]))
        w = textw(p["name"]) + PIN_NAME_OFFSET
        if w > 2 * BODY_X:
            problems.append("pin %s name %r (%.2f mm) is wider than the body (%.2f mm)"
                            % (p["num"], p["name"], w, 2 * BODY_X))

    # opposing pin names on the same row must not collide inside the body
    rows = {}
    for p in pins:
        rows.setdefault(p["y"], []).append(p)
    for y, ps in sorted(rows.items()):
        left = [p for p in ps if p["x"] < 0]
        right = [p for p in ps if p["x"] > 0]
        if left and right:
            lmax = -BODY_X + PIN_NAME_OFFSET + max(textw(p["name"]) for p in left)
            rmin = BODY_X - PIN_NAME_OFFSET - max(textw(p["name"]) for p in right)
            if lmax >= rmin:
                problems.append("pin names collide at y=%.2f: left text ends at %.2f, "
                                "right text starts at %.2f" % (y, lmax, rmin))

    # pins must not land on top of each other
    seen = {}
    for p in pins:
        key = (round(p["x"], 4), round(p["y"], 4))
        if key in seen:
            problems.append("pins %s and %s occupy the same point %s" % (seen[key], p["num"], key))
        seen[key] = p["num"]

    if problems:
        raise Fail(3, "legibility:\n  - " + "\n  - ".join(problems))


def check_hv_isolation(pins):
    """The HV pin must be the ONLY thing inside the fenced bottom-right corner.

    This is the executable form of "put the HV pin visually separated from the low-voltage
    pins" -- without it, a later y-tweak silently drags a signal pin into the HV corner.
    """
    problems = []
    inside = []
    for p in pins:
        # the pin's body-side endpoint, i.e. where it meets the rectangle
        bx = p["x"] + PIN_LEN if p["x"] < 0 else p["x"] - PIN_LEN
        if bx > FENCE_X and p["y"] < FENCE_Y:
            inside.append(p["num"])
    if inside != ["6"]:
        problems.append("pins inside the HV fence = %s, expected exactly ['6']" % inside)
    hv = [p for p in pins if p["num"] == "6"]
    if hv and hv[0]["y"] >= FENCE_Y:
        problems.append("pin 6 (HV) at y=%.2f is not below the fence at y=%.2f"
                        % (hv[0]["y"], FENCE_Y))
    # no low-voltage pin may share a row with HV
    if hv:
        same_row = [p["num"] for p in pins if p["num"] != "6" and abs(p["y"] - hv[0]["y"]) < 1e-6]
        if same_row:
            problems.append("pins %s share the HV row y=%.2f; HV must stand alone"
                            % (same_row, hv[0]["y"]))
    if problems:
        raise Fail(3, "HV isolation:\n  - " + "\n  - ".join(problems))


def check_kicad_loads(path):
    """(b) The decisive check: make KiCad itself parse the library.

    A library our own reader accepts but KiCad rejects is exactly the failure mode this
    exists to catch, so the instrument here must be kicad-cli, not us.
    """
    cli = find_kicad_cli()
    if cli is None:
        raise Fail(2, "kicad-cli not found; cannot prove KiCad can load the library. "
                      "Tried: %s" % ", ".join(KICAD_CLI_CANDIDATES))
    report = []
    tmp = tempfile.mkdtemp(prefix="iseg_symcheck_")

    up = os.path.join(tmp, "upgraded.kicad_sym")
    r = subprocess.run([cli, "sym", "upgrade", path, "-o", up, "--force"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise Fail(1, "kicad-cli sym upgrade rejected the library (rc=%d):\n%s" % (r.returncode, out))
    report.append("kicad-cli sym upgrade: rc=0 %s" % (("| " + out) if out else ""))

    # `sym upgrade` on an already-current file must be a no-op in schema terms: if KiCad
    # rewrites the version, ours was wrong.
    with open(up, "r", encoding="utf-8") as f:
        up_text = f.read()
    m = re.search(r"\(version (\d+)\)", up_text)
    if not m or m.group(1) != "20251024":
        raise Fail(1, "KiCad rewrote the schema version to %s; our (version 20251024) is stale"
                   % (m.group(1) if m else "?"))
    report.append("kicad-cli round-trip kept (version 20251024)")

    # Stronger than "it loaded": KiCad's own serializer must reproduce our bytes exactly.
    # If it does not, opening the lib in the GUI and pressing Ctrl+S would produce a spurious
    # git diff -- and worse, it means we guessed a formatting convention instead of copying it.
    with open(path, "r", encoding="utf-8", newline="") as f:
        ours = f.read()
    if up_text.replace("\r\n", "\n") != ours.replace("\r\n", "\n"):
        ours_l = ours.replace("\r\n", "\n").split("\n")
        theirs_l = up_text.replace("\r\n", "\n").split("\n")
        diff = []
        import difflib
        for line in difflib.unified_diff(ours_l, theirs_l, "generated", "kicad-rewritten",
                                         n=1, lineterm=""):
            diff.append(line)
            if len(diff) > 40:
                diff.append("... (truncated)")
                break
        raise Fail(1, "KiCad's own writer does not reproduce our bytes; our formatting "
                      "deviates from the KiCad 10.0 convention:\n" + "\n".join(diff))
    report.append("KiCad's writer reproduces our bytes exactly (no GUI-save diff)")

    svgdir = os.path.join(tmp, "svg")
    os.makedirs(svgdir, exist_ok=True)
    r = subprocess.run([cli, "sym", "export", "svg", path, "-o", svgdir],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise Fail(1, "kicad-cli sym export svg failed (rc=%d):\n%s" % (r.returncode, out))
    svgs = sorted(n for n in os.listdir(svgdir) if n.lower().endswith(".svg"))
    if len(svgs) != len(SYMBOLS):
        raise Fail(1, "expected %d SVGs (one per symbol), kicad-cli produced %d: %s"
                   % (len(SYMBOLS), len(svgs), svgs))
    report.append("kicad-cli sym export svg: rc=0, %d SVGs -> %s" % (len(svgs), svgdir))
    return report, svgdir


def check_determinism(path):
    """Rebuild in memory and byte-compare. This is what makes `git diff` a regression test."""
    with open(path, "rb") as f:
        on_disk = f.read()
    again = build_library_text().encode("utf-8")
    if on_disk != again:
        raise Fail(1, "regenerating produced different bytes; output is not deterministic")
    if build_library_text() != build_library_text():
        raise Fail(1, "build_library_text() is not stable across calls")


# ---------------------------------------------------------------------------------------

def main():
    try:
        os.makedirs(LIB_DIR, exist_ok=True)
        text = build_library_text()
        with open(OUT_SYM, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        for p, t in ((OUT_SYM_TABLE, SYM_LIB_TABLE), (OUT_FP_TABLE, FP_LIB_TABLE)):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(t)
        print("wrote %s (%d bytes)" % (OUT_SYM, len(text.encode("utf-8"))))
        print("wrote %s" % OUT_SYM_TABLE)
        print("wrote %s" % OUT_FP_TABLE)

        check_determinism(OUT_SYM)
        print("[ok] deterministic: regenerated bytes identical")

        pins = check_parses_and_matches_pinmap(OUT_SYM)
        print("[ok] (a) re-parsed; %d pins match PIN_MAP (%s, Table 4, page 9)"
              % (len(pins), DATASHEET_CITATION))

        check_legibility(pins)
        print("[ok] (c) legibility: grid, name widths, no collisions")

        check_hv_isolation(pins)
        print("[ok] (c) HV isolation: pin 6 alone inside the fence, alone on its row")

        report, svgdir = check_kicad_loads(OUT_SYM)
        for line in report:
            print("[ok] (b) %s" % line)

    except Fail as ex:
        sys.stderr.write("FAIL(%d): %s\n" % (ex.code, ex))
        return ex.code
    except Exception as ex:  # noqa: BLE001
        sys.stderr.write("FAIL(2): unexpected: %r\n" % (ex,))
        return 2
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# NOTE FOR WHOEVER CREATES THE .kicad_pro
#   sym-lib-table and fp-lib-table are resolved by KiCad from the PROJECT DIRECTORY -- the
#   directory containing the .kicad_pro -- not from wherever the .kicad_sym happens to live.
#   ${KIPRJMOD} expands to that project directory. These two stubs are written into lib/ only
#   because that is this generator's output area; they must be MOVED (or merged, if the
#   project already has tables) next to the .kicad_pro, and the "lib/..." path segment in the
#   uri adjusted to match the real project->lib relationship at that time.
#   DATASHEET_URI above ("${KIPRJMOD}/../../references/...") assumes the .kicad_pro lands in
#   hardware/hvctl/. If it lands elsewhere, fix DATASHEET_URI here and regenerate.
