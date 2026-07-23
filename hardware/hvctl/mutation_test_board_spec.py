#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MUTATION TEST for board_spec.py's self-check.

A check that has not been mutation-tested has not been shown to check anything.
Each mutation below is a single textual edit that makes the design WRONG in one
specific way; the harness asserts that `board_spec.py` then exits NON-ZERO and
that the SPECIFIC assertion it targets fires.  A mutation that survives means
the corresponding assertion is decorative.

Zero-arg, stdlib-only. **NEVER writes to the real source tree.**

    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/hvctl/mutation_test_board_spec.py

Exit 0 = every mutation caught by the assertion it was aimed at.

WHY THIS COPIES THE TREE (do not "simplify" this away -- PIPELINE_LOG PL-38):
An earlier version mutated `board_spec.py` IN PLACE and wrote the original back
inside a `try/finally`. That is not sufficient, for two reasons, and it bit us:
  * `finally` does not run if the process is killed; and
  * it is NOT CONCURRENCY-SAFE. When several verifier agents ran in parallel
    against the one shared file, one read an already-mutated file as its
    "baseline" and later wrote that corrupted baseline back. The `sa6` mutation
    (FB1 -> VIN_P_UNUSED) was left permanently in the committed source, where it
    broke the positive module's interlock supply path.
It survived only because assertion SA-6 caught it. A mutation the assertions do
NOT cover would have corrupted the golden netlist silently -- a verification tool
whose failure mode is undetectable corruption of the artifact it certifies.
So: copy to a private temp dir, mutate THERE, delete it. The real tree is opened
read-only by this tool and never written under any circumstances.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "board_spec.py")
PARTS = os.path.join(HERE, "board_spec_parts.py")
PY = sys.executable

# (name, file, old, new, substring that MUST appear in the failure output)
MUTATIONS = [
    # ---- domain assertion (a): the gate array ----------------------------
    ("a1  PERMIT_P loses its mode term (gate input tied high)", SPEC,
     '"9": "ARM", "10": "MU_OR_nSEL", "8": "PERMIT_P"',
     '"9": "ARM", "10": "+5V_MOD", "8": "PERMIT_P"',
     "(a) VIOLATED in the GATE ARRAY"),
    # *** a2 IS A DOCUMENTED EQUIVALENT MUTANT, AND THAT IS A FINDING. ***
    # Two variants were tried -- MODE_UNI = MODE_B OR nMODE_A, and MODE_UNI =
    # MODE_B (nMODE_A ignored) -- and NEITHER creates the forbidden state,
    # because MODE_VALID = MODE_A XOR MODE_B already rejects the only aux state
    # in which they differ from the AND. So the `nMODE_A` term in MODE_UNI is
    # DEFENCE IN DEPTH, not the load-bearing term; the XOR is.
    # This is recorded rather than deleted because "the assertion did not fire"
    # and "the mutation was harmless" look identical in a log, and only one of
    # them means the check is decorative. The variant below is kept as a live
    # mutation only because it ALSO orphans a net, which the structural check
    # catches -- a side effect, not a safety detection, and labelled as such.
    ("a2  MODE_UNI ignores MODE_A  [EQUIVALENT MUTANT -- see comment]", SPEC,
     '"1": "MODE_B", "2": "nMODE_A", "3": "MODE_UNI",',
     '"1": "MODE_B", "2": "+5V_MOD", "3": "MODE_UNI",',
     "every net needs >= 2"),
    ("a3  MODE_VALID decoded with OR instead of XOR (MODE-18)", SPEC,
     '"U32a": ("XOR", ["1", "2"], "3"),',
     '"U32a": ("OR", ["1", "2"], "3"),',
     "MODE-18 VIOLATED"),
    ("a4  /ON_N loses its mode term", SPEC,
     '"4": "ARM_OUTEN", "5": "MU_OR_SEL", "6": "nON_N"',
     '"4": "ARM_OUTEN", "5": "+5V_MOD", "6": "nON_N"',
     "(a) VIOLATED in the GATE ARRAY"),
    # ---- domain assertion (a): where the mode comes from ------------------
    ("a5  an ESP32 GPIO is put on the mode net", SPEC,
     '"24": "nALERT_ADC", "25": "LED_NET"',
     '"24": "MODE_A", "25": "LED_NET"',
     "ESP32 pin"),
    ("a6  the aux pole no longer drives the mode net", SPEC,
     'C("SW1E", "SW_SPST_LV", "SW1 pole S5 (aux UNI)", {"1": "+3V3", "2": "MODE_B"}',
     'C("SW1E", "SW_SPST_LV", "SW1 pole S5 (aux UNI)", {"1": "+3V3", "2": "MODE_B_SPARE"}',
     "does not touch its aux pole"),
    ("a7  a firmware-driven net reaches MODE_VALID", SPEC,
     '"1": "MODE_A", "2": "MODE_B", "3": "MODE_VALID",',
     '"1": "MODE_A", "2": "ARM_EN", "3": "MODE_VALID",',
     "reach MODE_VALID"),
    # ---- domain assertion (a): the routing itself -------------------------
    ("a8  S1's unipolar throw lands on OUT_A instead of OUT_B", SPEC,
     '{"2": "HV_X", "1": "HV_M", "3": "HV_OUT_B"}',
     '{"2": "HV_X", "1": "HV_M", "3": "HV_OUT_A"}',
     "BOTH energised modules reach"),
    ("a9  S2 left closed in unipolar (mode switch contact table)", SPEC,
     '"SW1B": {"PB": [("1", "2")], "SAFE": [], "UNI": []},',
     '"SW1B": {"PB": [("1", "2")], "SAFE": [], "UNI": [("1", "2")]},',
     "FAIL"),   # caught by the HV-stress walk, not by (a): with S2 closed in
                # UNI the two modules still land on different nodes, but M1 and
                # OUT_A become an opposite-polarity pair across a 2 kV gap.
    # ---- domain assertion (b): discharge paths ----------------------------
    ("b1  the M-node stub bleed is deleted", SPEC,
     '"BLDM": dict(top="HV_M", bot="GND"',
     '"BLDM": dict(top="HV_M", bot="HV_M"',
     "(b) VIOLATED"),
    ("b2  the positive module's park bleed is deleted", SPEC,
     '"BLDP": dict(top="HV_POS_PARK", bot="GND"',
     '"BLDP": dict(top="HV_POS_PARK", bot="HV_POS_PARK"',
     "(b) VIOLATED"),
    ("b3  the idle output B loses its bleed", SPEC,
     '"BLDB": dict(top="HV_OUT_B", bot="GND"',
     '"BLDB": dict(top="HV_OUT_B", bot="HV_OUT_B"',
     "no BLEED path to GND"),
    ("b4  R_G no longer reaches ground", SPEC,
     'R("R_G", "10k", "HV_SW_G", "GND", pclass="R_HV_AXIAL"',
     'R("R_G", "10k", "HV_SW_G", "HV_OUT_B", pclass="R_HV_AXIAL"',
     "FAIL"),   # (b) still holds -- HV_SW_G reaches GND through OUT_B's bleed.
                # What fires is the HV-stress walk. Recorded so the log does not
                # imply (b) caught something it did not.
    # ---- domain assertion (c): monitor independence -----------------------
    ("c1  a module VMON is moved onto the monitors' own ADC", SPEC,
     '"4": "MON_TAP_A",\n       "5": "MON_REF_A", "6": "MON_TAP_B", "7": "MON_REF_B",',
     '"4": "MON_TAP_A",\n       "5": "MON_REF_A", "6": "MON_TAP_B", "7": "VMON_P_BUF",',
     "(c)"),
    ("c2  the COLD chain is given the monitor's bottom node", SPEC,
     'R("RCB_%s" % X, "5.62M 0.1%", node, "GND")',
     'R("RCB_%s" % X, "5.62M 0.1%", node, "HVDIV_TAP_A")',
     "(c)"),
    # ---- symbol cross-check ----------------------------------------------
    ("s1  a pin that the symbol does not have", SPEC,
     '"5": "VMON_P", "6": "HV_POS", "7": "GND"',
     '"5": "VMON_P", "6": "HV_POS", "7": "GND", "8": "GND"',
     "is NOT on the symbol"),
    ("s2  a symbol pin silently omitted", SPEC,
     '"1": "VIN_N", "2": "VSET_N", "3": "GND", "4": "nON_N",',
     '"1": "VIN_N", "2": "VSET_N", "4": "nON_N",',
     "is not in the pin map"),
    ("s3  the iseg HV pin moved to the wrong pad", SPEC,
     '"5": "VMON_P", "6": "HV_POS", "7": "GND"}',
     '"5": "HV_POS", "6": "VMON_P", "7": "GND"}',
     "symbol pin name"),
    # ---- netclass / glob trap --------------------------------------------
    ("n1  an HV pattern loses the '*/' sheet wildcard", SPEC,
     '_nc("HV_POS", C_HV, 0.5, ["*/HV_POS*"]',
     '_nc("HV_POS", C_HV, 0.5, ["HV_POS*"]',
     "fell through to Default"),
    ("n2  a netclass drops a SCHEMATIC field", SPEC,
     '        "wire_width": wire_width,\n',
     '',
     "missing field"),
    # ---- HV voltage ratings ----------------------------------------------
    ("v1  the monitor string is shortened to 2 elements", SPEC,
     '"MONA": dict(top="HV_OUT_A", bot="HVDIV_TAP_A", n_series=10',
     '"MONA": dict(top="HV_OUT_A", bot="HVDIV_TAP_A", n_series=2',
     "per element against a derated limit"),
    ("v2  an HV series limiter becomes an ordinary 0603", SPEC,
     'R("R_G", "10k", "HV_SW_G", "GND", pclass="R_HV_AXIAL"',
     'R("R_G", "10k", "HV_SW_G", "GND", pclass="R_LV"',
     "sits on an HV routing node but is not rated"),
    ("v3  a bleed string becomes a single series chain (NUM-09)", SPEC,
     '"BLDA": dict(top="HV_OUT_A", bot="GND", n_series=2, n_par=2',
     '"BLDA": dict(top="HV_OUT_A", bot="GND", n_series=4, n_par=1',
     "single series chain"),
    ("v4  the 2512 package rating is inflated to cover a bad design", PARTS,
     '"R_HV_1206": dict(tier="B", sym="Device:R", fp="Resistor_SMD:R_1206_3216Metric",\n'
     '               vmax=800.0',
     '"R_HV_1206": dict(tier="B", sym="Device:R", fp="Resistor_SMD:R_1206_3216Metric",\n'
     '               vmax=80.0',
     "per element against a derated limit"),
    # ---- basic structure --------------------------------------------------
    ("t1  a net left with a single connection", SPEC,
     'C("TP3", "TP", "AHCT_SPARE", {"1": "AHCT_SPARE"})',
     'C("TP3", "TP", "AHCT_SPARE", {"1": "TP3_ORPHAN"})',
     "connection(s); every net needs >= 2"),
    ("t2  an nc pad omitted instead of declared", SPEC,
     'nc=["4", "5"],\n      notes="Q_ARM (C-1)',
     'nc=[],\n      notes="Q_ARM (C-1)',
     "is not in the pin map"),
    # ---- INTERFACES.md SA-1 .. SA-13 --------------------------------------
    ("sa1  one of the two /ON pull-ups deleted (ARCH-18)", SPEC,
     'R("R56", "10k", "nON_P", "VIN_P", notes="pair 2/2")',
     'R("R56", "10k", "nON_P", "GND", notes="pair 2/2")',
     "SA-1"),
    ("sa2  /ON pulled up to a rail that can outlive the module", SPEC,
     'R("R57", "10k", "nON_N", "VIN_N", notes="pair 1/2")',
     'R("R57", "10k", "nON_N", "+3V3", notes="pair 1/2")',
     "SA-2"),
    ("sa3  a VSET pull-down deleted", SPEC,
     'R("RPD2_%s" % M, "1.00k 0.1%", "VSET_%s" % M, "GND", notes="ARCH-18 pair 2/2")',
     'R("RPD2_%s" % M, "1.00k 0.1%", "VSET_%s" % M, "VSET_%s" % M, notes="x")',
     "SA-3"),
    ("sa4  the VSET buffer is powered from a logic rail, not the clamp", SPEC,
     '"7": "VSET_N_FORCE", "8": "VCLAMP_STAR"}',
     '"7": "VSET_N_FORCE", "8": "+5V_A"}',
     "SA-4"),
    ("sa6  a module +VIN is fed straight off a regulator", SPEC,
     'R("FB1", "600R@100MHz", "VIN_P_SW", "VIN_P", pclass="FB")',
     'R("FB1", "600R@100MHz", "VIN_P_SW", "VIN_P_UNUSED", pclass="FB")',
     "SA-6"),
    ("sa7  the coil rail bypasses its fail-safe switch (F-1)", SPEC,
     '"21": "+5V_COIL", "24": "COIL_FEED_P", "22": "COIL_FEED_N"',
     '"21": "+5V_MOD", "24": "COIL_FEED_P", "22": "COIL_FEED_N"',
     "SA-7"),
    ("sa11 a module GND pin left off GND", SPEC,
     '"5": "VMON_N", "6": "HV_NEG", "7": "GND"}',
     '"5": "VMON_N", "6": "HV_NEG", "7": "AGND_SPARE"}',
     "SA-11"),
    # This one exists because ADDING the DNP contingency pull-downs silently
    # broke SA-3: an unfitted footprint was counting toward "two pull elements",
    # so the board passed ARCH-18 with ONE fitted pull element. The mutation
    # test found it; nothing else would have.
    #
    # NOTE ON HOW IT IS TESTED. Deleting the `not dnp` filter alone does NOT
    # fail, because the DNP contingency parts only ADD to a ">= 2" count. The
    # mutation that actually exercises the property is to mark a FITTED pull
    # element DNP: the fitted count then drops to one while four footprints
    # remain on the net, which is exactly the situation the filter exists for.
    ("dnp1 a fitted safety pull element is marked DNP", SPEC,
     'R("RPD1_%s" % M, "1.00k 0.1%", "VSET_%s" % M, "GND",\n'
     '          notes="ARCH-18 pair 1/2. Turns \'clamp fails open\' from 1000 V into "',
     'R("RPD1_%s" % M, "1.00k 0.1%", "VSET_%s" % M, "GND", dnp=True,\n'
     '          notes="ARCH-18 pair 1/2. Turns \'clamp fails open\' from 1000 V into "',
     "SA-3"),
    ("sa13 the mandated 22 uF at a module +VIN removed", SPEC,
     'CAP("C14", "22u/16V", "VIN_N", "GND", pclass="C_BULK", notes="PART-18")',
     'CAP("C14", "1u/16V", "VIN_N", "GND", pclass="C_BULK", notes="PART-18")',
     "SA-13"),
]


def run(sandbox):
    """Run board_spec.py inside the SANDBOX copy. Never touches the real tree."""
    out = subprocess.run([PY, os.path.join(sandbox, "board_spec.py")],
                         cwd=sandbox, capture_output=True, text=True)
    return out.returncode, out.stdout + out.stderr


def main():
    # Read the real tree ONCE, read-only. Everything after this happens in a copy.
    base_spec = io.open(SPEC, encoding="utf-8").read()
    base_parts = io.open(PARTS, encoding="utf-8").read()

    sandbox = tempfile.mkdtemp(prefix="hvctl_mutation_")
    # Private per-invocation directory => concurrent runs cannot collide (PL-38).
    sb_spec = os.path.join(sandbox, "board_spec.py")
    sb_parts = os.path.join(sandbox, "board_spec_parts.py")
    try:
        for name in os.listdir(HERE):
            src = os.path.join(HERE, name)
            if os.path.isfile(src) and name.endswith(".py"):
                shutil.copy2(src, os.path.join(sandbox, name))
        for sub in ("lib",):
            s = os.path.join(HERE, sub)
            if os.path.isdir(s):
                shutil.copytree(s, os.path.join(sandbox, sub))

        rc, txt = run(sandbox)
        if rc != 0:
            print("BASELINE IS ALREADY FAILING -- fix that first:\n" + txt)
            return 2
        print("baseline: exit 0  (sandbox: %s)" % sandbox)
        caught, survived, misfired = 0, [], []
        return _mutate(sandbox, sb_spec, sb_parts, base_spec, base_parts,
                       caught, survived, misfired)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        # Belt and braces: prove we did not touch the real tree.
        if io.open(SPEC, encoding="utf-8").read() != base_spec:
            sys.stderr.write("FATAL: board_spec.py was modified by the mutation "
                             "test. That must never happen (PL-38).\n")
            os._exit(2)


def _mutate(sandbox, sb_spec, sb_parts, base_spec, base_parts,
            caught, survived, misfired):
    # MUTATIONS carries the REAL paths as its file key; map each to its sandbox
    # twin. Nothing below ever writes outside `sandbox`.
    twin = {SPEC: sb_spec, PARTS: sb_parts}
    baseline = {sb_spec: base_spec, sb_parts: base_parts}

    for name, real_path, old, new, want in MUTATIONS:
        path = twin[real_path]
        base = baseline[path]
        if base.count(old) != 1:
            misfired.append((name, "anchor appears %d times" % base.count(old)))
            continue
        io.open(path, "w", encoding="utf-8").write(base.replace(old, new, 1))
        rc, txt = run(sandbox)
        io.open(path, "w", encoding="utf-8").write(base)
        if rc == 0:
            survived.append((name, "exit 0 -- THE ASSERTION IS DECORATIVE"))
        elif want not in txt:
            survived.append((name, "failed, but not with %r" % want))
        else:
            caught += 1
            print("  CAUGHT  %s" % name)

    rc, txt = run(sandbox)
    print("\nrestored baseline (in sandbox): exit %d" % rc)
    print("%d/%d mutations caught" % (caught, len(MUTATIONS)))
    for n, why in survived:
        print("  SURVIVED  %-55s %s" % (n, why))
    for n, why in misfired:
        print("  MISFIRED  %-55s %s" % (n, why))
    return 0 if (not survived and not misfired and rc == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
