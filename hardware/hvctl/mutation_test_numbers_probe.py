#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutation test harness for numbers_probe.py. Zero-arg, headless, deterministic, stdlib-only.

An assertion that cannot fail is not evidence. This tool applies ONE textual perturbation to an
INPUT constant of the probe at a time, re-runs it, and reports the exit code and which assertions
flipped to FAIL. **A mutation that does not flip any assertion is a hole in the probe's coverage**
and this tool exits non-zero for it.

It writes a throwaway `_mutant_numbers_probe.py` BESIDE the real probe rather than in a scratch
directory, because the probe reads three sibling artifacts by RELATIVE path (KiCad's stock
footprint library, this project's module footprint, and phase0_env_proof/env_proof.kicad_pro) and
would silently fall back to hardcoded values if run from anywhere else. The mutant is removed in a
`finally`, so an interrupted run does not leave one behind.

Exit codes: 0 every mutation caught · 1 a mutation survived or an anchor is stale ·
2 the baseline probe does not pass.
"""
import os
import re
import subprocess
import sys

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "numbers_probe.py")

MUTATIONS = [
    ("M1  divider loading budget 1% -> 5% of Inom",
     "DIVIDER_FRACTION_OF_INOM = 0.01", "DIVIDER_FRACTION_OF_INOM = 0.05"),
    ("M2  bleed budget 10% -> 0.2% of Inom (R_bleed 20M -> 1G)",
     "BLEED_FRACTION_OF_INOM = 0.10", "BLEED_FRACTION_OF_INOM = 0.002"),
    ("M3  MCU logic rail 3.3 V -> 2.4 V (below module Vref)",
     "LOGIC_RAIL_V = 3.3", "LOGIC_RAIL_V = 2.4"),
    ("M4  clearance design margin 1.5x -> 0.8x",
     "DESIGN_MARGIN = 1.5", "DESIGN_MARGIN = 0.8"),
    ("M5  IEC printed-board column de-duplicated from MG I (the tripwire)",
     '"printed_board": [(250, 1.0), (500, 2.5), (1000, 5.0)]',
     '"printed_board": [(250, 1.0), (500, 2.0), (1000, 4.0)]'),
    ("M6  ESP32 peak 500 mA -> 150 mA",
     "ESP32_PEAK_MA = 500.0", "ESP32_PEAK_MA = 150.0"),
    ("M7  VSET fail-safe pull-down 1 kohm -> 100 kohm",
     "R_PD_OHM = 1000.0", "R_PD_OHM = 100000.0"),
    ("M8  divider top-leg element count 10 -> 1 (VCR term x10)",
     "N_TOP_ELEMENTS = 10", "N_TOP_ELEMENTS = 1"),
]


def checks_of(text):
    out = {}
    for m in re.finditer(r"^  \[(PASS|FAIL)\] (.*?)(?:  --  |$)", text, re.M):
        out[m.group(2)] = m.group(1)
    return out


def run(path):
    p = subprocess.run([PY, path], capture_output=True, text=True,
                       cwd=os.path.dirname(path))
    return p.returncode, p.stdout + p.stderr


def main():
    base = open(SRC, encoding="utf-8").read()
    tmp = os.path.join(HERE, "_mutant_numbers_probe.py")
    try:
        open(tmp, "w", encoding="utf-8").write(base)
        rc0, out0 = run(tmp)
        base_checks = checks_of(out0)
        print("BASELINE exit=%d  checks=%d  fails=%d"
              % (rc0, len(base_checks),
                 sum(1 for v in base_checks.values() if v == "FAIL")))
        if rc0 != 0:
            print("baseline is not clean; aborting")
            return 2
        print()

        bad = 0
        for label, old, new in MUTATIONS:
            if base.count(old) != 1:
                print("%-62s  !! anchor not unique (%d)" % (label, base.count(old)))
                bad += 1
                continue
            open(tmp, "w", encoding="utf-8").write(base.replace(old, new))
            rc, out = run(tmp)
            ch = checks_of(out)
            fired = sorted(k for k, v in ch.items() if v == "FAIL")
            missing = sorted(set(base_checks) - set(ch))
            print("%s" % label)
            print("    exit=%d   assertions that FIRED: %d" % (rc, len(fired)))
            for f in fired:
                print("      FAIL  %s" % f[:110])
            if missing:
                print("      (assertions absent from mutant output: %d)" % len(missing))
            if rc == 0:
                print("      !!! MUTATION SURVIVED -- exit 0, no assertion caught it")
                bad += 1
            print()
        return 1 if bad else 0
    finally:
        if os.path.isfile(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    sys.exit(main())
