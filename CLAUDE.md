# CLAUDE.md — iseg Bipolar HV Controller

**Read these four rules before touching anything.**

1. **Generated CAD files are build artifacts. Never hand-edit them.**
   `*.kicad_sch`, `*.kicad_pcb`, `*.kicad_sym`, `*.kicad_mod`, `*.net`, gerbers — all are
   outputs of a generator in `hardware/hvctl/`. Every defect (electrical *or* cosmetic) is
   fixed in the generator and regenerated. Commit generator + artifact together.
   The one exception is `references/` — read-only third-party material, never regenerated.

2. **Interpreters — the fork matters.**
   ```
   PY_KICAD = C:/Program Files/KiCad/10.0/bin/python.exe    # ONLY interpreter with pcbnew; also has fitz, PIL, numpy
   CLI      = C:/Program Files/KiCad/10.0/bin/kicad-cli.exe # nothing KiCad is on PATH
   ```
   A tool that manipulates **board geometry** imports `pcbnew` → must run under `PY_KICAD`.
   A tool that **emits or verifies text files** (`.kicad_sch`, `.kicad_sym`, `.kicad_mod` are
   s-expression text; there is no schematic API) needs no KiCad API → runs on any Python 3,
   **stdlib only**. Prefer that path. **Zero third-party dependencies is the design.**
   There is no `requirements.txt` because there is nothing to pin.

3. **Shell and path discipline.**
   Two shells, not interchangeable: PowerShell 5.1 (no `&&`, no `grep/head/tail`) and
   git-bash (POSIX tools, MSYS path translation). State the shell in every command block.
   **Write every path as `C:/...` with forward slashes** — both shells and Python accept
   those; `/c/Users/...` is accepted by bash utilities but *not* by `kicad-cli.exe` or
   Python's `open()`. Plain `python` is not on PATH: always use an absolute interpreter path.
   The repo path contains a space (`OneDrive - Yale University`) — quote it, always.

4. **Evidence tags are mandatory when claiming something works.**
   `[verified-run]` executed this session, behaved as stated · `[verified-artifact]` output
   exists on disk and was inspected · `[recalled]` from context, unverified.
   "Exit code 0" is not "verified" — name the instrument and say what it cannot see.

---

## Layout

```
docs/            SCOPE · DECISIONS · PLAN · STATUS · INTERFACES · PIPELINE_LOG · SESSION_LOG
docs/playbook/   EE_PROJECT_BOOTSTRAP.md (the standing process file) + debriefs
hardware/hvctl/  board_spec.py (golden netlist) · generators · checks · lib/ · outputs/
firmware/        ESP32 application (generic software rules, not the CAD gates)
host/            minimal control/readback script
references/      READ-ONLY: iseg datasheets, the Phys439 alpha-lab reference board
```

## Non-negotiables for this board (HV)

- Hardware interlock: both modules enabled into the output simultaneously must be
  **unreachable**, enforced in hardware — firmware agreement is not sufficient.
- Defined discharge/bleed path on changeover and on disable.
- Output voltage monitored **independently** of the module readbacks.
- HV creepage/clearance encoded as **DRC netclass rules**, so the check is executable.
  A netclass must carry its *schematic* fields or it silently breaks eeschema connectivity
  (see bootstrap §V.3 — this is the most expensive fact in the playbook).
- First energization is human-present. No session ever claims the Phase 7 gate.

## Pipeline log

`docs/PIPELINE_LOG.md` is append-only and **mandatory from session one**. When you hit a
problem the bootstrap did not cover, covered wrongly, or made harder — and you solve it —
log it the same session. Litmus test: *would this have helped on a completely different
board?* If yes → PIPELINE_LOG. If it is a fact about this circuit → `docs/DECISIONS.md`.
Never block engineering work on bootstrap philosophy: solve, log, keep moving.

## Session close ritual

Append to `docs/SESSION_LOG.md` (absolute dates) → commit → push. The remote is the handoff
medium. Sessions boot cold from files; nothing lives only in a conversation.
