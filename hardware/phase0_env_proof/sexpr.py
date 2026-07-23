#!/usr/bin/env python3
"""S-expression format layer for KiCad text files (.kicad_sch / .kicad_sym / .kicad_mod).

Phase 0 environment proof. Stdlib only, runs on any Python 3 -- there is NO schematic API,
so every schematic byte is produced through this module.

Round-trip contract: quoted strings are stored RAW (exactly the characters between the
delimiting quotes, escapes undecoded). Re-emitting a parsed tree therefore reproduces the
original quoting/escaping byte-for-byte; only whitespace is normalised. Use q() to build a
new quoted string from a Python value.

Acceptance: self-test in main() parses and re-serialises a KiCad-written demo file and
asserts token-stream equality.  Exit 0 only if it holds.
  python sexpr.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = ("C:/Program Files/KiCad/10.0/share/kicad/demos/"
        "simulation/rectifier/rectifier.kicad_sch")

_TOK = re.compile(r'\(|\)|"((?:[^"\\]|\\.)*)"|[^\s()"]+', re.S)


class Q(str):
    """A quoted string. The value carried is the RAW inner text (escapes undecoded)."""
    __slots__ = ()


def q(value):
    """Build a Q from a plain Python string, escaping as KiCad does."""
    s = str(value)
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return Q(s)


def unq(node):
    """Decode a Q (or plain atom) back to a plain Python string."""
    s = str(node)
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            out.append({"n": "\n", "t": "\t", "r": "\r"}.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def tokenize(text):
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == "(" or t == ")":
            yield t
        elif t[0] == '"':
            yield Q(m.group(1))
        else:
            yield t


def parse(text):
    """Parse the first complete s-expression in text. Returns nested lists."""
    stack, root = [], None
    for tok in tokenize(text):
        if tok == "(":
            new = []
            if stack:
                stack[-1].append(new)
            stack.append(new)
        elif tok == ")":
            root = stack.pop()
            if not stack:
                return root
        else:
            if not stack:
                raise ValueError("atom outside any list: %r" % (tok,))
            stack[-1].append(tok)
    if root is None:
        raise ValueError("no s-expression found")
    raise ValueError("unbalanced parentheses")


def _atom(x):
    return isinstance(x, str)


def dumps(node, indent=0):
    """Serialise in KiCad's house style: tab indent, all-atom lists kept on one line."""
    if _atom(node):
        return '"%s"' % node if isinstance(node, Q) else str(node)
    if not node:
        return "()"
    if all(_atom(e) for e in node):
        return "(" + " ".join(dumps(e) for e in node) + ")"
    pad = "\t" * (indent + 1)
    out = ["(" + dumps(node[0], indent)]
    for e in node[1:]:
        out.append("\n" + pad + dumps(e, indent + 1))
    out.append("\n" + "\t" * indent + ")")
    return "".join(out)


def find(node, head):
    """First direct child list whose head atom == head, else None."""
    for e in node[1:] if node else []:
        if not _atom(e) and e and _atom(e[0]) and str(e[0]) == head:
            return e
    return None


def findall(node, head):
    return [e for e in (node[1:] if node else [])
            if not _atom(e) and e and _atom(e[0]) and str(e[0]) == head]


def extract_block(text, head, name):
    """Slice the raw substring of the (head "name" ...) block out of a big library file.

    Avoids parsing an 8 MB library to read three symbols. Paren-balanced, quote-aware.
    """
    needle = '(%s "%s"' % (head, name)
    start = -1
    for m in re.finditer(re.escape(needle), text):
        j = m.end()
        # the next character must end the name token context (newline/space), and the
        # match must start a list -- guard against "R_Small" matching "R".
        if j < len(text) and text[j] in " \t\r\n)":
            start = m.start()
            break
    if start < 0:
        raise KeyError("no %s named %r" % (head, name))
    depth, i, in_str = 0, start, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise ValueError("unbalanced %s %r" % (head, name))


def _selftest():
    problems = []
    if not os.path.exists(DEMO):
        return ["reference corpus missing: %s" % DEMO]
    with open(DEMO, "r", encoding="utf-8") as fh:
        text = fh.read()
    tree = parse(text)
    again = dumps(tree)
    a = [str(t) for t in tokenize(text)]
    b = [str(t) for t in tokenize(again)]
    if a != b:
        for k, (x, y) in enumerate(zip(a, b)):
            if x != y:
                problems.append("token %d differs: %r != %r" % (k, x, y))
                break
        if len(a) != len(b):
            problems.append("token count %d != %d" % (len(a), len(b)))
    blk = extract_block(
        open("C:/Program Files/KiCad/10.0/share/kicad/symbols/Device.kicad_sym",
             "r", encoding="utf-8").read(), "symbol", "R")
    sym = parse(blk)
    if str(sym[1]) != "R":
        problems.append("extract_block picked the wrong symbol: %r" % (sym[1],))
    if find(sym, "pin_numbers") is None:
        problems.append("Device:R block lost its pin_numbers")
    rt = q('a "b" c\\d')
    if unq(rt) != 'a "b" c\\d':
        problems.append("q/unq round-trip broken: %r" % (unq(rt),))
    return problems


def main():
    problems = _selftest()
    if problems:
        print("FAIL (%d):" % len(problems))
        for p in problems:
            print("   " + p)
        return 1
    print("PASS - sexpr round-trips a KiCad-written file token-for-token")
    return 0


if __name__ == "__main__":
    sys.exit(main())
