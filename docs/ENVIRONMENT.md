# ENVIRONMENT — Phase 0 proof

**Date:** 2026-07-23 · **Machine:** Windows 11 Home 10.0.26200 · **Gate: MET.**

The bootstrap defines the Phase 0 gate as *"the throwaway board produces gerbers"*. It does.
`hardware/phase0_env_proof/` holds a two-resistor board driven end-to-end: schematic → ERC →
netlist → PCB → zone fill → DRC → PDF → SVG → 3D render → **gerbers + drill**.

> **Provenance note.** The Phase-0 agent in the session-1 workflow died mid-run on an API
> transport error, after writing the generators and getting as far as ERC/netlist. The
> remaining links (fill, DRC, gerbers, drill, render, and this file) were executed directly
> by the orchestrator. Every fact below carries the instrument that produced it. This file
> supersedes the "REFUTED #2 / Phase 0 gate not met" entry in `STATUS.md` §1.3, which was
> correct when written.

---

## 1. Verified stack

| Thing | Value | How verified |
|---|---|---|
| `kicad-cli` | **10.0.3** | `kicad-cli --version` `[verified-run]` |
| KiCad Python | **3.11.5** (MSC v.1944 64-bit), built 2026-01-23 | `python.exe -c "import sys;print(sys.version)"` `[verified-run]` |
| `pcbnew` module | **10.0.3** | `pcbnew.GetBuildVersion()` `[verified-run]` |
| Schematic schema | **`(version 20260306)`** | `kicad-cli sch upgrade --force` on a copied demo — see the correction note below `[verified-run]` |
| Board / footprint schema | **`(version 20260206)`** | what `pcbnew` and `fp upgrade` actually write `[verified-artifact]` |

> **⚠ Correction — this row was wrong when first written, and the way it was wrong is instructive.**
> It originally read `(version 20250610)`, sourced by reading three `.kicad_sch` files from
> `share/kicad/demos/`. Those files really are KiCad-written, so the instrument looked sound — but the
> **shipped demos are stale**, written by an older KiCad and never regenerated. Copying one to scratch
> and running `kicad-cli sch upgrade --force` rewrites it `20250610 → 20260306` `[verified-run]`,
> which is what the installed eeschema natively emits.
>
> The demo corpus is a **reference, not an oracle.** The upgrade round-trip is the oracle.
> This matters concretely: the bootstrap warns that an older schema triggers an on-load
> upgrade-and-cleanup pass that can dissolve generated geometry, so a generator emitting `20250610`
> would be quietly wrong in a way no headless check would catch.
>
> Our generators were **already correct** — `env_proof.kicad_sch` carries `20260306` and
> `iseg_APS_THT.kicad_mod` carries `20260206` `[verified-artifact]`. Only this document was wrong.
> Logged as `PIPELINE_LOG.md` PL-04, which also records that four agents hit this independently and
> **two nearly "fixed" a correct generator to match the stale demo.**
| FreeRouting | **2.2.4**, build-date 2026-05-13, at `C:/Users/darro/tools/freerouting-2.2.4.jar` | jar banner printed on launch `[verified-run]` |
| JRE for FreeRouting | **Temurin 25** — `C:/Users/darro/tools/jdk-25.0.3+9-jre/bin/java.exe` | see §4 `[verified-run]` |

**Paths — the interpreter fork.** Nothing KiCad is on `PATH`.

```
PY_KICAD = C:/Program Files/KiCad/10.0/bin/python.exe      # ONLY interpreter with pcbnew
CLI      = C:/Program Files/KiCad/10.0/bin/kicad-cli.exe
DEMOS    = C:/Program Files/KiCad/10.0/share/kicad/demos/  # file-format ground truth
SYMBOLS  = C:/Program Files/KiCad/10.0/share/kicad/symbols/
FOOTPRNT = C:/Program Files/KiCad/10.0/share/kicad/footprints/
```

Bundled third-party modules confirmed importable under `PY_KICAD`: `pcbnew`, `fitz` (PyMuPDF),
`PIL`, `numpy`, `requests`. **No `scipy`, no `matplotlib`** — the numbers probe must not import them.

---

## 2. The command surface, verbatim

Every line below was executed this session and exited 0 `[verified-run]`. Run from
`hardware/phase0_env_proof/`.

```bash
# 1. schematic + project + lib tables  (stdlib-only Python, no KiCad API)
python gen_sch.py

# 2. ERC — errors only
"$CLI" sch erc --severity-error -o outputs/erc.rpt env_proof.kicad_sch

# 3. netlist (the independent source of truth downstream checks compare against)
"$CLI" sch export netlist -o outputs/env_proof.net env_proof.kicad_sch

# 4. board geometry — pcbnew, KiCad's interpreter ONLY
"$PY_KICAD" gen_pcb.py

# 5. zone fill — SEPARATE PROCESS, mandatory (see §3)
"$PY_KICAD" fill_zones.py

# 6. DRC
"$CLI" pcb drc --severity-error --exit-code-violations -o outputs/drc.rpt env_proof.kicad_pcb

# 7. review artifacts
"$CLI" sch export pdf -o outputs/env_proof_sch.pdf env_proof.kicad_sch
"$CLI" sch export svg --exclude-drawing-sheet -o outputs/ env_proof.kicad_sch
"$CLI" pcb render --side top -o outputs/render_top.png env_proof.kicad_pcb

# 8. fab package
"$CLI" pcb export gerbers -o outputs/gerbers/ env_proof.kicad_pcb
"$CLI" pcb export drill   -o outputs/gerbers/ env_proof.kicad_pcb
```

`kicad-cli pcb` subcommands are exactly `{drc, export, import, render, upgrade}` `[verified-run]`.

### Results

| Step | Result |
|---|---|
| ERC | **0 errors, 0 warnings.** `erc_exclusions` **absent** (i.e. empty) and `pin_not_connected` **absent** (i.e. KiCad's default `error`) in `.kicad_pro` — so this is an honest zero, not a suppressed one `[verified-artifact]` |
| Netlist | 6545 bytes `[verified-artifact]` |
| PCB | 4 footprints, 3 tracks, 1 via, 2 zones `[verified-run]` |
| Zone fill | 2 zones, **2178.23 mm²** filled copper, read back off the saved board `[verified-run]` |
| DRC | **0 violations, 0 unconnected pads** `[verified-artifact]` — `outputs/drc.rpt` |
| 3D render | 1568×872 RGBA PNG, **136 distinct colours** (a blank render is ~1 — this is the check that the render is not empty) `[verified-run]` |
| Gerbers | **24 layer files + `.gbrjob` + `.drl`**, all non-zero; `F_Cu.gtl` 11 425 B, `Edge_Cuts.gm1` 718 B, `env_proof.drl` 346 B `[verified-artifact]` |

**Gate met.**

---

## 3. Traps confirmed on this machine

### 3.1 In-process `ZONE_FILLER.Fill()` **does** segfault — but only on a real board

The bootstrap says fills must run in a separate process. **Confirmed, exit code 139
(SIGSEGV)** `[verified-run]`, reproduced against the real `gen_pcb.build()` path:

```
BUILT_OK                     <- 4 footprints, 3 tracks, 2 zones
<segfault, no further output>
REAL_EXIT_CODE=139
```

**The near-miss worth recording:** a *minimal* repro — `CreateEmptyBoard()` plus one bare
`ZONE` with a hand-appended outline — **survives** and returns `True`. Filling in-process only
dies once footprints have been loaded from a library in the same process. Had the minimal
repro been the only test, this session would have written "the bootstrap's segfault claim does
not reproduce on KiCad 10.0.3" into a document, and the next session would have deleted
`fill_zones.py`. See `PIPELINE_LOG.md` PL-E2.

`fill_zones.py` asserts each zone's **filled polygon area > 0** after reload, because DRC
passes vacuously on a zone that filled to nothing — "DRC 0 violations" cannot see an empty zone.

### 3.2 KiCad writes CRLF on Windows; our generators write LF

Independently checked on `lib/iseg.kicad_sym` `[verified-run]`: after
`kicad-cli sym upgrade --force`, the file is **11 609 bytes with 600 CRLF** where ours is **11 009
bytes with 600 LF**, and the two are **byte-identical once newlines are normalized**. So the
round-trip content gate genuinely passes — KiCad would have written exactly these bytes — and only
the line-ending convention differs.

Two independent mechanisms keep that from becoming a phantom whole-file `git diff` the first time a
human saves the library in the GUI (the failure PL-02 exists to prevent):

1. The generator's own gate reads the upgraded file with `open(..., "r", encoding="utf-8")` — Python
   text mode applies universal newlines, so its byte-compare is already normalized.
2. `.gitattributes` sets `* text=auto`, confirmed to apply to this path via
   `git check-attr text -- hardware/hvctl/lib/iseg.kicad_sym` → `text: auto` `[verified-run]`, so git
   normalizes CRLF → LF on commit.

Do not "fix" this by making the generators emit CRLF — that would make the files platform-specific
for no gain. But **do not remove `.gitattributes`**, and when writing a round-trip byte-compare on any
platform, normalize newlines explicitly rather than relying on text mode by accident.

### 3.3 `pcb drc` exit codes

`--exit-code-violations` is required to make violations non-zero-exit; without it the command
exits 0 whether or not it found anything. Quoting a bare exit code as "DRC clean" without that
flag is exactly the structurally-blind green check the bootstrap warns about.

### 3.4 Netclasses carry schematic fields

The `Default` netclass in `env_proof.kicad_pro` carries `bus_width`, `line_style`,
`diff_pair_*` and `microvia_*` alongside the PCB fields `[verified-artifact]`. A PCB-only
netclass silently breaks eeschema connectivity for every net in it, and **`kicad-cli` never
reads `.kicad_pro`**, so no headless check here would ever notice. This must hold for the
HV netclasses on the real board.

---

## 4. FreeRouting — usable, with two traps

Needed only at Phase 4, but proved now.

- **`java` on `PATH` is Java 8** (`1.8.0_491`, Oracle). FreeRouting 2.2.4 is compiled to
  **class file version 69 = Java 25** and dies on it with `UnsupportedClassVersionError`
  `[verified-run]`.
- **Temurin 21 also fails** (`jdk-21.0.11+10-jre`, class version ≤ 65) `[verified-run]`.
  Only **Temurin 25** runs it. Use the absolute path; never bare `java`.
- **The dead-proxy workaround works.** Pointing its phone-home at a non-routable proxy makes
  analytics fail fast rather than hang:
  ```
  -Dhttp.proxyHost=127.0.0.1  -Dhttp.proxyPort=9
  -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=9
  ```
  Observed: `ConnectException: Connection refused` at +0.13 s, then
  `Further failures will be aggregated and reported every 60 minutes` `[verified-run]`.
- **`--help` is not a valid argument.** It logs `Unknown command line argument: --help` and
  proceeds to launch anyway. Flag discovery must come from the project's docs, not `--help`.
  Working invocation shape for Phase 4: `-de <design>.dsn -do <out>.ses -mp <passes>` `[recalled]` —
  **not yet exercised on a real DSN; prove it before relying on it.**

---

## 5. What each gate cannot see

Before quoting any check as evidence, read the row.

| Gate | Structurally blind to |
|---|---|
| `kicad-cli sch erc` | **everything in `.kicad_pro`** (never reads it); GUI-strict connectivity; accepts a malformed hierarchy identically to a correct one |
| `kicad-cli sch export netlist` | same; lenient about mid-span taps the GUI dissolves; derives paths from each symbol's own `(instances)` without cross-checking the root |
| `kicad-cli pcb drc` | **pad-net comparison** even with `--schematic-parity` (footprint-level only); an empty zone (passes vacuously); exits 0 on violations unless `--exit-code-violations` |
| `fill_zones.py` | whether the fill is *correct* — only that it is non-empty |
| own netcmp/parity tools | whatever they inherit from the CLI-exported netlist; UUID linkage needs a separate bijection check |
| 3D render | wrong-but-present geometry; a missing 3D model fails **silently** (part simply absent) — count what you expect to see |
| all headless checks together | anything `.kicad_pro`-scoped · legibility · polarized-part rotation · mechanical sense · **golden-netlist-vs-intent** |
| the human in the KiCad GUI | nothing above — which is why the GUI gate is non-negotiable |

---

## 6. Deltas from the bootstrap's stated stack

| Bootstrap says | Reality here | Consequence |
|---|---|---|
| KiCad 10.0.3, `C:/Program Files/KiCad/10.0/` | ✅ exact match | none |
| bundled Python is the only `pcbnew` interpreter | ✅ confirmed, 3.11.5 | none |
| schema `(version 20250610)` | ❌ **STALE — eeschema writes `20260306`**; boards/footprints write `20260206`. The bootstrap's number matches only the shipped demos, which lag the installed tool | §1 correction note; PL-04. The bootstrap must stop naming a version and instead name the *procedure* (`upgrade --force` a demo copy) |
| "FreeRouting 2.2.4 + Temurin JRE" | ✅ present — but **Temurin 25 specifically**, and PATH `java` is 8 | §4; bootstrap should name the version |
| in-process fill segfaults | ✅ confirmed **139** — but *not* reproducible on a minimal board | §3.1; PL-E2 |
