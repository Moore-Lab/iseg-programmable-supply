# Project Brief — Bipolar HV Controller (iseg modules)

*Prepend `EE_PROJECT_BOOTSTRAP.md` (v1.0) to this brief in a fresh Claude Code session. This project is the first test of that bootstrap: `docs/PIPELINE_LOG.md` is mandatory from session one, and the harvest at fab commit feeds bootstrap v1.1.*

## Objective

A high-voltage controller built around **iseg HV modules**, producing **bipolar output voltage from two unipolar modules** (one positive-polarity, one negative-polarity) through a **single output combiner** — one output terminal usable with either module, explicitly *not* two independent unipolar outputs. The device is controlled by an **ESP32**, reachable over **serial and/or network**.

## Stated requirements

1. Two unipolar iseg modules, opposite polarities, one combined bipolar output.
2. Single output connector/channel; the combiner selects or merges which module drives it.
3. ESP32 as the controller: set-point control, readback, and status over serial or network.
4. Developed end-to-end under `EE_PROJECT_BOOTSTRAP.md` with its gates; this run doubles as the bootstrap's first field test.

## Open questions for Gate 0 (batch these; assume-and-log the rest)

- **Module selection.** Which iseg family/part numbers (voltage class, current class, positive + negative variants), and what control interface do those modules actually expose (analog set/monitor pins vs. a digital interface)? This decides most of the board.
- **Output spec.** Full-scale ±V and I; what load it drives; required ripple/stability; and — the key behavioral question — is smooth **through-zero** operation required, or set-and-hold with polarity changeover acceptable? The answer selects the combiner topology.
- **Combiner topology.** To be resolved by a Phase-1 study + numbers probe, not assumed. Candidates to evaluate: HV relay changeover; opposite-polarity diode-OR with blocking rated for full reverse voltage; series/stacked arrangement with a driven midpoint. Non-negotiable invariants regardless of topology: an interlock making it impossible to enable both modules into the output simultaneously (enforced in hardware, not only firmware), a defined discharge/bleed path on changeover and on disable, and monitored output voltage independent of the module readbacks.
- **Comms.** Serial (USB/UART), network (ESP32 WiFi vs. wired Ethernet), or both; protocol (simple SCPI-like ASCII is the default candidate); whether it integrates with SIMPLE or runs standalone.
- **Monitoring.** Per-module V/I readback, combined-output readback, interlock and fault status reporting.
- **Safety envelope.** HV creepage/clearance per the working standard **encoded as DRC netclass rules** (so the check is executable, per bootstrap V.3 — and note netclasses need their schematic fields); HV connector choice (e.g. SHV); enclosure and touch-safety; bench energization procedure for Phase 7. First energization is human-present, always.

## Success criteria (draft — tighten at G0)

Fab-ready outputs passing the full bootstrap gate set; bench: commanded bipolar sweep across the full range from the ESP32 over the chosen interface, correct polarity handoff at the combiner with no both-enabled state reachable, readback agreeing with a DMM within a tolerance frozen at G1, and safe discharge on disable verified.

## Deliverables

The board (schematic + layout + fab package) under the bootstrap's generated-artifact rules; ESP32 firmware + a minimal host-side control/readback script (firmware lane runs under the generic software rules); `docs/PIPELINE_LOG.md` harvested into proposed bootstrap v1.1 edits at the fab-commit gate.
