# CONTROLLER_AND_POWER — ESP32 selection, power tree, comms, arm/watchdog, connectors

**Project:** iseg bipolar HV controller · **Phase:** 2 detailed design · **Written:** 2026-07-23
**Written against the FROZEN G0 answers (A1–A5).** Nothing here re-opens a G0 decision.

> **This file is HAND-WRITTEN engineering judgement.** Where it quotes a number produced by
> `hardware/hvctl/numbers_probe.py` it says so and names the section. Where it *changes* an
> arrangement that a session-1/2 document assumed, it says so **explicitly and with the reasoning**,
> per the standing instruction not to contradict prior analysis silently. Section 0.3 is the list of
> every such change; read it before reading anything else.

---

## 0. Preamble

### 0.1 Evidence key (same as the rest of the repo)

| Tag | Meaning |
|---|---|
| `[verified-artifact]` | Read out of a file on disk in this session |
| `[verified-run]` | A computation executed and its output quoted (arithmetic in this document is shown inline so it can be re-derived by hand) |
| `[web-verified]` | Read this session from the manufacturer's own documentation page |
| `[recalled]` | Background knowledge. **Unverified.** Do not commit a BOM line or a safety claim to it |
| `[unverified-MPN]` | Part number not checked against any live distributor page. Availability unknown |
| `[unverified-primary]` | Derived from a clearance/creepage constant that no human has read in a primary standard (`STATUS.md` §1.2, `DECISIONS.md` NUM-01) |
| `MEASURABLE-NOW` | Depends on a module parameter that is unmeasured but the modules are in hand (G0-A2) |

**No MPN in this document has been checked against a live distributor page.** Every one is
`[unverified-MPN]` for availability even where the specification is `[web-verified]`. Phase 6
re-verifies. **A fab BOM containing any `unverified-MPN` is a build failure** (`INTERFACES.md` I-4).

### 0.2 Two places where the task brief I was given is stale against G0, and what I did

Recorded rather than silently reconciled.

| Task wording | Frozen G0 answer | What this document does |
|---|---|---|
| *"plus the relay coils (including the **mode relay**)"* | **G0-A5: there is NO mode relay.** The mode is a physical switch with no coil (`DECISIONS.md` MODE-04, `COMBINER_STUDY.md` C-5, NUM-21 struck) | **No mode coil is budgeted.** The coil budget is unchanged from the single-mode design. What *does* enter the GPIO budget is the mode switch's **auxiliary-pole readback** (`MODE_A_RB`, `MODE_B_RB`), which §2 treats as a first-class safety input. §3.4 states the coil budget explicitly so the omission is visible rather than accidental |
| *"the SCPI-like command set for a **BIPOLAR SINGLE-OUTPUT** instrument"* | **G0-A4: two selectable output modes**, and in mode 2 there are two independently-commandable outputs | §8 specifies the **full dual-mode surface**. The single-signed-setpoint form the task asks for is exactly the **pseudo-bipolar (mode 1)** surface and is specified as such; mode 2 forks to channel-addressed setpoints per `CONTROL_ARCHITECTURE.md` §4.7a |

### 0.3 Changes this document makes to prior analysis — the complete list

Every item here is a deliberate, argued change to something a session-1/2 document assumed. **None of
them changes a G0 answer.** Anyone who disagrees should argue with the reasoning, not re-derive it.

| # | Prior position | This document | Why |
|---|---|---|---|
| **Δ1** | `NUMBERS_PROBE.md` §6.2: **single 5 V / 1.8 A input**, modules taken directly from the brick, ESP32 fed by a 5→3.3 V buck reflecting **388 mA onto the 5 V module rail** | **Single 12 V / 2.0 A input.** 5 V, 3.3 V and the analog rail are each generated on-board **from 12 V, in parallel** | Two independent reasons. **(a)** `OPA192`'s minimum supply is **4.5 V** (`CONTROL_ARCHITECTURE.md` §2.5, `[web-verified]`) — you cannot make a *quiet* 5 V analog rail from a 5 V input, because there is no LDO headroom. A 5 V input forces the µV-class monitor buffers onto the same rail that carries the HV converters' switching current. **(b)** It takes the WiFi TX burst **off the module rail entirely**. §3.2 shows the burst falls from 388 mA-on-5 V to 213 mA-on-12 V and no longer shares a node with `+VIN`. **Cost, stated: one extra conversion stage and ≈1.3 W of conversion loss** (7.14 W drawn at 12 V for 5.81 W delivered, 81 %; §3.2). The probe's arithmetic is not wrong; its *architecture* was a 5 V-input architecture |
| **Δ2** | `CONTROL_ARCHITECTURE.md` §1.7 headline: *"Drive VSET directly. **No** buffer op-amp."* Its own post-G0 note then says the buffer *"may NOT be dropped… keep it"* | **Fit the buffer.** Its supply rail is a **shunt-regulated 2.500 V rail**, which is the structural over-range clamp | The §1.7 headline and its post-G0 note **contradict each other inside one section**. The note is the later and safety-driven one, so it wins. §5 works out what "powered from the 2.500 V reference" actually requires, which nobody had costed: the reference has to **source up to 9.8 mA** into the two duplicated `VSET` pull-downs, and **REF5025 is rated ±10 mA** — i.e. the naïve implementation sits at 100 % of the reference's drive |
| **Δ3** | Implicit: the 2.500 V clamp rail is "the reference" | The clamp rail is **shunt-regulated by two paralleled LM4040-2.5**, separate from the REF5025 that sets DAC gain | A **series** reference (REF5025) fails to *its input rail* on a pass-element short — 5 V on the clamp rail is **2000 V** at the output, from one fault. A **shunt** reference cannot do that: raising the rail is what it sinks. Duplicating it per ARCH-18 covers the open-circuit failure, which is the one failure a shunt device has that matters here |
| **Δ4** | `CONTROL_ARCHITECTURE.md` §6.2/§6.4: full scale = Vnom = 1000 V, with a **firmware** 98 % code clamp | **Declared full scale is ±980 V**, and 98 % is now a **hardware headroom requirement**, not only a firmware convention | §5.4's headroom arithmetic: the buffer's rail (2.4975 V worst case) must exceed the commanded output (2.4512 V at 98 % code) by more than the op-amp's output-swing dropout at 4.9 mA. The 2 % was already being given away; this states what it buys and makes it a spec |
| **Δ5** | `CONTROL_ARCHITECTURE.md` §3.3/§3.3a: `ARM = EN_HB · INTLK · nOVP · SETTLE` (4 terms) | `ARM = EN_HB · ARM_EN · INTLK · nOVP · SETTLE · RAIL_OK · MODE_VALID` (7 terms) | Three additions, each closing a named single fault. **`ARM_EN`** gives ARCH-35 its explicit, revocable arm bit with a sub-microsecond disarm (the heartbeat's decay is 61.5–164.5 ms). **`RAIL_OK`** closes "a buck's pass FET shorts and puts 12 V on the 4.5–5.5 V module rail" (§10, F-13). **`MODE_VALID`** implements MODE-18's intermediate-position decode as an ARM term rather than as a special case |
| **Δ6** | `CONTROL_ARCHITECTURE.md` §3.7: heartbeat pump drops HV in **~79 ms**, computed against a 3.3 V source and a 1.5 V threshold | **62 ms (worst-case-late) to 165 ms**, computed against real 74HCT Schmitt thresholds and a two-series-cap AC coupling | Session 1 used a single nominal threshold. C-3 requires **two series coupling caps**, which changes the pump capacitance, and the HCT hysteresis band is 0.5–2.0 V, not a point. **The result is worse than 79 ms and must not be quoted as 79 ms** |
| **Δ7** | `CONTROL_ARCHITECTURE.md` §4.4 / §6.1: ESP32-S3 with **CP2102N + W5500 + WiFi**, all three, without ranking the two network media | Same three parts. **W5500 is the primary network transport; WiFi is secondary and is treated as the noisiest, least trustworthy path** | §1.3. This is a statement about *medium*, not about *authority* — **both remain fully write-authoritative, exactly as G0-A3 requires.** G0-A3 is not re-litigated and is not downgraded |
| **Δ8** | Not previously stated | The ESP32 module must be the **`-1U` (external-antenna) variant** | The enclosure is a *fully enclosed earthed metal chassis* (`HV_SAFETY_ENVELOPE.md` §2.1). A PCB-antenna module inside a Faraday cage does not communicate. This is a hard dependency between two documents that neither had noticed |
| **Δ9** | `HV_SAFETY_ENVELOPE.md` §2 G0-A5 note: the aux poles must break before the HV poles make, margin **open** (N-8) | **The lead-break requirement is satisfied primarily by a guard-cover microswitch in series with the interlock loop**, with the switch's own contact sequence as a second layer | §7.4. A rotary switch's inter-deck contact timing is not a catalogue parameter and nobody publishes it. A guard that must be opened to reach the selector, wired into `INTLK`, gives a lead-break margin measured in **hundreds of milliseconds of hand travel** rather than in unspecified milliseconds of contact geometry. **This does not retire MODE-15**; it makes MODE-15 satisfiable with a procurable part |
| **Δ10** | `CONTROL_ARCHITECTURE.md` §6.1: one SPI bus implied | **Two SPI buses: the DAC on its own host, the W5500 on the other** | §2.3. The setpoint path must not share a bus with the network interface. A babbling W5500 or a stuck `nCS` is then structurally unable to corrupt a DAC write |
| **Δ11** | Not previously stated | **Panel `HV PRESENT` and `FAULT` lamps are driven from the hardware interlock signals, never from a GPIO** | A firmware-driven HV lamp lies in exactly the fault where you need it. §11 |
| **Δ12** | `CONTROL_ARCHITECTURE.md` §5.7: watchdog kicked by *"any received command"* | Kicked only by commands from the **session that holds control** (`SYSTem:LOCK`) | §7.3. With **two** write-authoritative transports (G0-A3), a chatty telemetry poller on one transport would otherwise hold HV alive while the operator's control link on the other transport is dead. That is a watchdog that does not watch |

### 0.4 Reconciliation with the three sibling documents written in parallel

`docs/design/SETPOINT_PATH.md`, `docs/design/MONITOR_AND_BLEED.md` and
`docs/design/COMBINER_DESIGN.md` were written **concurrently with this one, by other agents, from
the same frozen G0 answers.** They were read after this document's first draft. Where they overlap,
this section says **which document governs** and what changed here as a result. Nothing is left to
be discovered by a reader noticing two numbers.

| Overlap | Governing document | What happened |
|---|---|---|
| **The `VSET` clamp** — §5 of this document vs `SETPOINT_PATH.md` §§2–4 | **`SETPOINT_PATH.md` GOVERNS** | Both arrived independently at *"a rail-to-rail buffer whose supply is the 2.500 V rail IS the clamp, and it is mandatory"* — which is worth recording, because that conclusion contradicts `CONTROL_ARCHITECTURE.md` §1.7's headline and two agents reached it separately. **Three differences, and `SETPOINT_PATH.md` is right on all three:** see below |
| **Relay coil current** — §3.2/§3.4 here | **`COMBINER_DESIGN.md` §4.2 GOVERNS** | It selected a real part and read its coil resistance. **The number moved from 80 mA to 286 mA and it changed this document's conclusions.** See below |
| **ADC channel map, analog rail loads** — §3.2 here | **`MONITOR_AND_BLEED.md` GOVERNS** | Consistent: two ADS1115 at 0x48/0x49, ADC-A carrying both differential HV monitors, OPA192 on a ≥4.5 V rail. **No change needed to the analog-rail budget** |
| **5 V relay coils rather than a generated 12 V rail** | independently agreed | This document (§3.4) and `COMBINER_DESIGN.md` §4.2 closed open question N-5 / TOPO-08 **the same way, separately.** Two independent derivations agreeing is the only reason to have any confidence in it |

#### 0.4.1 Where `SETPOINT_PATH.md` supersedes §5 of this document

| # | This document's §5 | `SETPOINT_PATH.md` | Verdict |
|---|---|---|---|
| 1 | Clamp rail = `+5V_A` through `R_sh` = 180 Ω, **shunt-regulated by 2 × LM4040-2.5** | Clamp rail = **REF5025 followed by a unity-gain rail-force amplifier `U3`**, with Kelvin feedback taken at the star point | **`SETPOINT_PATH.md` wins, on a load number I got wrong.** I enumerated **9.83 mA** of clamp-rail load; it enumerates **12.06 mA**, because it also counts the DAC's reference input current (~1 mA), the buffers' quiescent (~1 mA) and the comparator sense divider (0.062 mA). **Under 12.06 mA my shunt arrangement leaves each LM4040 only 0.92 mA at nominal and 0.22 mA at the `+5V_A` low corner** — above the ~60 µA floor, but with the rail 87 % consumed. That is not a rail, it is a coincidence. It also has a cross-coupling term I never looked for: `SETPOINT_PATH.md` §3.1.2 shows 20 mΩ of shared copper puts **80 mV of error on each output that depends on the other output's setting**, which only exists because G0-A4 made both channels live at once |
| 2 | Over-range comparator threshold = **2.625 V from a 0.1 % divider off `+5V_A`** | Threshold from a **dedicated `LM4040-2.048`, deliberately a different device from a different family than REF5025** | **`SETPOINT_PATH.md` wins.** My threshold moves with the `+5V_A` rail (±1 %), so a rail excursion is indistinguishable from a set-point fault. A dedicated reference does not. My §5.5 got the *principle* right — *"not the reference that feeds the DAC"* — and then derived the threshold from something almost as bad |
| 3 | Declared full scale **±980 V** | **±950 V guaranteed, ~980 V typical**; guaranteed deliverable magnitude **960.1 V** | **`SETPOINT_PATH.md` wins.** I stacked only *our* tolerances (clamp rail low, REF5025 high). It also folds in **the module's own Vref tolerance (±1 %, 2.475–2.525 V) and its ±1 % adjustment accuracy.** ±980 V is a *typical*, not a *guarantee*, and declaring a typical as a spec is the REF-05 anti-pattern this project keeps citing |

> **§5 of this document is retained rather than deleted**, for one reason: it is an *independent*
> derivation that reached the same architectural conclusion (buffer mandatory, clamp is the buffer's
> rail, DAC rail may be 3.3 V because the buffer makes it irrelevant). **Read §5 for the argument;
> take the component values from `SETPOINT_PATH.md`.** Its numbers are marked in place.
>
> **What does NOT change is this document's job:** the analog rail must supply the clamp-rail
> arrangement whichever one is built. My `+5V_A` budget of 60 mA covers `SETPOINT_PATH.md`'s
> `U3` (12.06 mA delivered, ≥18.1 mA capability required) with the same margin it covered my
> 13.9 mA shunt feed. **The power tree is indifferent to which clamp arrangement wins**, which is
> the property you want a power tree to have.

#### 0.4.2 The relay coil finding — this one changed numbers here

`COMBINER_DESIGN.md` §4.2 selected **Pickering `67-1-C-5/5D`** `[unverified-MPN]` and read its coil
resistance: **40 Ω at 5 V = 125 mA, 0.625 W per relay.** With two Form-C coils energised
simultaneously — **which is normal operation in unipolar mode, not an overlap allowance** — plus
≈36 mA for the `K_S` interlock relay, the coil rail is **286 mA, not the 80 mA `NUMBERS_PROBE.md`
§6.2 budgets.**

That is a 206 mA error in a prior frozen document, found by picking a real part. **This document's
§3.2 has been re-run against 286 mA.** The consequences are in §3.2 and §3.6, and one of them is
that the enclosure's ventilation figure no longer holds.

---

## 1. ESP32 variant selection

### 1.1 What actually discriminates, and what does not

Three things that are usually decisive here **do not discriminate at all in this design**, and saying
so prevents a later session re-opening them:

- **Internal DAC presence is irrelevant.** `CONTROL_ARCHITECTURE.md` §1.1 disqualified every ESP32
  internal DAC twice over: on resolution (8 bit = **3.92 V per LSB** at 1 kV) and, after G0-A2, on
  **safety** — a 3.3 V-rail-referenced source commands `3.3/2.5 × 1000 =` **1320 V** inside its normal
  code range, on an input the datasheet says is *"internally not limited"* `[verified-artifact]`. An
  external DAC is mandatory for every variant, so "the S3 has no DAC" costs nothing.
- **Internal ADC quality is irrelevant.** ARCH-15 disqualified it (±1–3 % even calibrated is *no
  better* than the module's own 1 %·Vnom monitor, so it fails to be an *independent, better* check by
  construction). An external ADC is mandatory for every variant.
- **Native USB is not decisive.** §1.4 keeps the CP2102N bridge for a reason that is independent of
  the SoC.

**What does discriminate: the Ethernet MAC, the core count, and the strapping pins.**

### 1.2 The variant table

| | ESP32 (classic) | **ESP32-S3** | ESP32-C3 | ESP32-C6 |
|---|---|---|---|---|
| Cores | 2 × LX6 | **2 × LX7** | 1 × RISC-V | 1 × RISC-V (+LP) |
| Ethernet MAC (RMII) | **yes** | no `[recalled]` | no `[recalled]` | no `[recalled]` |
| Strapping pins | GPIO0, 2, 5, **12 (MTDI)**, 15 `[recalled]` | **GPIO0, 3, 45, 46** `[web-verified, Espressif]` | GPIO2, 8, 9 `[recalled]` | GPIO8, 9, 15 `[recalled]` |
| USB | none (bridge required) | native OTG + USB-Serial-JTAG on GPIO19/20 `[web-verified, Espressif]` | USB-Serial-JTAG | USB-Serial-JTAG |
| Internal DAC | 2 × 8-bit (unusable, §1.1) | none | none | none |
| GPIO available on a WROOM-class module | ~26 | ~36 | ~15 | ~22 |

> **The ESP32-S3 strapping-pin set — GPIO0, GPIO3, GPIO45, GPIO46 — is `[web-verified]` this session**
> against Espressif's *ESP Hardware Design Guidelines → ESP32-S3 → Schematic Checklist*, which states
> them by name and gives the GPIO0/GPIO46 boot-mode combinations and a 3 ms strap hold time.
> Session 1 recorded the same four pins as `[recalled]` (`CONTROL_ARCHITECTURE.md` §3.2). **Two
> independent statements now agree and one of them is primary.** This matters because §2's entire
> safety argument is "no HV-relevant control line sits on a strapping pin", and that argument is only
> as good as the list.
>
> **The EMAC-absence claim is weaker evidence and is tagged accordingly.** Espressif's S3 schematic
> checklist and peripheral list contain no EMAC entry, which is *absence of mention*, not a positive
> denial. `[recalled — confirm against the ESP32-S3 datasheet feature list at Phase 6]`. **The
> decision below does not depend on it**: §1.3 rejects the RMII path on a second, independent ground.

### 1.3 Network medium — WiFi vs W5500 vs LAN8720, decided on the safety-critical criterion

G0-A3 froze **both serial and network with full write authority on both**. It did **not** name a
network medium. That is the open question this section closes.

| Criterion | ESP32 WiFi | **W5500 (SPI)** | LAN8720 (RMII) |
|---|---|---|---|
| Galvanic isolation from the host | **none** | ~1.5 kV via magnetics `[recalled]` | ~1.5 kV via magnetics `[recalled]` |
| Needs an EMAC | no | **no** | **yes** ⇒ forces the classic ESP32 |
| Where the TCP/IP stack runs | lwIP, **on the CPU that runs the supervisor** | **inside the W5500** (hardware TCP/IP) | lwIP, on the CPU |
| Current reflected onto the supply | **500 mA peak TX bursts** (`NUMBERS_PROBE.md` §6.3) | ~132 mA steady on 3V3 `[recalled — datasheet check at Phase 6]` | ~60 mA + PHY |
| RF field beside a 200 kΩ / 5 µA divider tap | **yes** | no | no |
| Physical-presence property | **none** | a cable | a cable |
| Pin cost | 0 | 6 | 9 **plus a 50 MHz REF_CLK, conventionally on GPIO0 — a strapping pin** |
| Institutional policy risk | real (many university networks prohibit unmanaged stations) | none | none |

**Decision: the W5500 is the primary network transport.** Reasons in order of weight:

1. **Isolation is a safety property here, not an EMC nicety.** The HV return is GND and the module
   case is bonded to GND (`[verified-artifact]`, iseg Table 4). A fault brings HV onto local ground.
   Ethernet's magnetics break that tie for free. `CONTROL_ARCHITECTURE.md` §4.3a already says
   isolation *"matters more, not less"* after G0-A3; this is the transport that has it by construction.
2. **The network stack is off the safety CPU.** With full network write authority, the network stack
   *is* the attack surface. A hardware-TCP/IP part bounds what a malformed or flooding peer can
   consume: the socket state machine is in the W5500's silicon, not in a task competing with the
   supervisor loop. This is the single strongest argument and it is specific to the safety case
   G0-A3 created.
3. **It removes the design's largest current from the analog neighbourhood.** `NUMBERS_PROBE.md`
   §6.3's finding — *"the WiFi TX burst is a LARGER 5 V load than both HV modules combined"* — is a
   statement about a rail that also feeds a µV-class reference and a 5 µA divider tap.

**WiFi is also built, is also fully write-authoritative, and is not downgraded** (G0-A3; not
re-litigated, per the standing instruction). It is *ranked second* as a medium, and the design treats
it as the noisiest and least trustworthy path: §3 puts it on its own regulator, §7 gives it the same
watchdog and the same control-ownership rules as every other transport, and §9 gives it an external
antenna so it is not fighting an earthed steel box.

**LAN8720 / RMII is rejected on two independent grounds**, either of which is sufficient:
- It requires an EMAC, which forces the classic ESP32 — whose strapping-pin set includes **GPIO12
  (MTDI)**, the flash-voltage strap. A pull-up there makes the part boot with 1.8 V on a 3.3 V flash.
  On a board carrying dozens of deliberate pull-ups, that is a live foot-gun `[recalled]`.
- The 50 MHz RMII reference clock is conventionally fed into **GPIO0**, which is the boot-mode strap
  and the auto-reset target. Putting a 50 MHz clock on the pin that decides whether the chip boots is
  exactly the class of arrangement §2 exists to forbid `[recalled]`.

### 1.4 Serial transport

Keep the **CP2102N USB-UART bridge**, behind a **USB isolator**, on UART0 (GPIO43/44).
`CONTROL_ARCHITECTURE.md` §4.2's argument stands and is worth restating because it is easy to
dismiss: **the bridge stays enumerated across an MCU reset.** On an instrument that reboots when it
trips, the debug port disappearing at the moment of the trip is a real operational defect.

The S3's **native USB-Serial-JTAG (GPIO19/20)** `[web-verified]` is retained but is brought out only
to an **internal header inside the chassis**, never to the panel — see §9.4 for why (it is an
un-isolated ground tie, and the whole point of §4.1's isolation argument is that there must not be one).

### 1.5 Recommendation

> **ESP32-S3-WROOM-1U-N8R2** `[unverified-MPN]` — external-antenna (U.FL) variant, 8 MB flash,
> **2 MB *quad* PSRAM**.
>
> - **`-1U` (external antenna) is a requirement, not a preference** (Δ8). The chassis is earthed
>   metal (`HV_SAFETY_ENVELOPE.md` §2.1); a PCB antenna inside it does not work. U.FL pigtail to a
>   panel bulkhead RP-SMA. It also deletes the antenna keep-out from the layout, which on a board
>   already dominated by HV keep-outs (`SCOPE.md` R-12) is a real saving.
> - **Quad PSRAM (`R2`), not octal (`R8`), is a requirement.** Espressif: *"In cases where 1.8 V or
>   3.3 V, octal, in-package or off-package SPI flash/PSRAM is used, **GPIO33 ~ GPIO37 are occupied
>   and cannot be used** for other functions"* `[web-verified, ESP32-S3 Hardware Design Guidelines]`.
>   §2.3's pin map uses GPIO33–37 for the safety-status inputs precisely so that GPIO39–42 stay free
>   for JTAG. **Fitting an `R8` module silently removes five pins**, and the failure would present as
>   "the mode readback doesn't work" long after layout. Make it a netlist-check note.
> - 8 MB flash is the minimum for dual-OTA partitions + NVS + a TLS certificate store + a coredump
>   partition (§7.5). 2 MB PSRAM is more than enough; the application has no large buffers.
> - Dual core is used as `CONTROL_ARCHITECTURE.md` §4.4 intends: **the safety supervisor is pinned to
>   core 1, all comms and WiFi to core 0**, so a blocked network stack cannot delay a trip and cannot
>   delay the heartbeat toggle.

---

## 2. Boot-time GPIO and strapping-pin analysis

### 2.1 Why this is a real hazard on this board and not a checklist item

Three documented module behaviours compose into one sentence
(`HV_SAFETY_ENVELOPE.md` §2, `[verified-artifact]`):

- `/ON` is **active low, and "LOW *or open*" means HV ON**.
- An open `VSET` node commands **full scale**, via an internal 10 kΩ pull-up to Vref.
- The output is *"internally not limited"* above Vref.

> **⇒ The module's un-driven default state is ENERGISED AT OVER-RANGE.**

Therefore, on this board specifically:

- A GPIO configured as an input — **the state of every ESP32 GPIO during reset and early boot** — is,
  if it reaches `/ON`, a request for HV ON.
- The boot ROM **drives** strapping pins and emits a boot log on U0TXD.
- The CP2102N's DTR/RTS auto-reset circuit **drives GPIO0 and EN** whenever a host opens the port.

The mitigation is structural and has three parts, all of which must hold:

1. **No HV-relevant signal on a strapping pin** (§2.2).
2. **`/ON` is never driven by a GPIO at all.** It is the output of an open-drain interlock gate
   (`CONTROL_ARCHITECTURE.md` §3.3a) pulled up to the module's own `+VIN`. A GPIO is one *term* of
   that gate and can never be sufficient.
3. **Every ESP32 output that enters the interlock has a duplicated external pull to its safe state,
   in the 5 V logic domain** — i.e. at the 74HCT input, not at the ESP32 pin. This is the part that
   is easy to get wrong: a pull-down at the ESP32 pin does nothing if the wire between the ESP32 and
   the logic breaks. **Pull where the receiver is.** (ARCH-18 duplication; `INTERFACES.md` SA-3.)

### 2.2 The strapping pins, and the demonstration that nothing HV-relevant is on one

ESP32-S3 strapping pins `[web-verified, Espressif ESP32-S3 Schematic Checklist]`:

| Pin | Function | Required state | This design |
|---|---|---|---|
| **GPIO0** | Boot mode. `1` ⇒ SPI boot (normal); `0` with GPIO46 `0` ⇒ download boot | HIGH at reset (internal pull-up) | **BOOT button to GND + auto-reset jumper only.** No net. Not routed anywhere else |
| **GPIO3** | JTAG source select | don't-care; leave floating | **Unconnected.** Test point only |
| **GPIO45** | `VDD_SPI` voltage select | LOW (3.3 V flash) | **Unconnected**, with a 10 kΩ pull-**down** fitted as insurance |
| **GPIO46** | ROM message printing / boot mode | LOW at reset (internal pull-down) | **Unconnected**, 10 kΩ pull-**down** fitted |

Also reserved and not used for board signals:
GPIO26–32 (in-package SPI flash), GPIO19/20 (USB D−/D+, internal header only `[web-verified]`),
GPIO43/44 (U0TXD/U0RXD — **the boot log comes out of GPIO43 at 115200 baud, which is exactly why no
HV-relevant signal may share it**), GPIO39–42 (JTAG, deliberately left free).

**Result: the four strapping pins carry no net in this design.** The claim is checkable, and §12
makes it an executable netlist assertion rather than a review item (`CONTROL_ARCHITECTURE.md` §6.4
rule 2 already asks for this; here is the pin list it needs).

**The vivid version of why, for the record.** If `SEL` were on GPIO0: opening a serial terminal
asserts DTR, the auto-reset circuit pulls GPIO0 low, and the *polarity of a kilovolt supply changes
because someone started a terminal program*. If `ARM_EN` were on GPIO46, the ROM's boot-mode sampling
would drive it. Neither is hypothetical; both are the normal behaviour of the parts.

### 2.3 Full GPIO map

Module: **ESP32-S3-WROOM-1U-N8R2** (quad PSRAM ⇒ GPIO33–37 available `[web-verified]`).

| GPIO | Net | Dir | State while ESP32 is in reset **or unpowered** | External pull (where) | HV-relevant | Consequence of a **broken wire** |
|---:|---|:-:|---|---|:-:|---|
| 4 | `HB_OUT` | O | hi-Z, **not toggling** | AC-coupled (2 × 47 nF series); 100 kΩ to GND at the ESP32 pin | **YES** | pump decays ⇒ `EN_HB=0` ⇒ **ARM=0** ⇒ both modules OFF |
| 5 | `ARM_EN` | O | hi-Z | **2 × 10 kΩ to GND at the 74HCT30 input** | **YES** | `ARM_EN=0` ⇒ **ARM=0** |
| 6 | `OUT_EN` | O | hi-Z | **2 × 10 kΩ to GND at the 74HCT input** | **YES** | `/ON` stays HIGH ⇒ both modules OFF (modules may be powered; that is the ARMED state) |
| 7 | `SEL` | O | hi-Z | **2 × 10 kΩ to GND** | **YES** | defaults to POS. Harmless: `ARM` is independently required, and `SETTLE` fires on the edge |
| 8 | `nSYNC_DAC` | O | hi-Z | 10 kΩ to `+3V3_A` | indirect | DAC deselected, holds last code. Caught by monitor disagreement (+104) |
| 9 | `SPI_A_SCK` | O | hi-Z | 10 kΩ to GND | indirect | as above |
| 10 | `SPI_A_MOSI` | O | hi-Z | — | indirect | as above |
| 11 | `SPI_A_MISO` (74LVC165 `QH`) | I | hi-Z | 10 kΩ to GND | no | status word reads all-zero ⇒ pattern-bit check fails ⇒ firmware trips (§2.4) |
| 12 | `nLOAD_165` | O | hi-Z | 10 kΩ to `+3V3` | no | as above |
| 13 | `SPI_B_SCK` | O | hi-Z | — | no | Ethernet down. Watchdog expires ⇒ ramp down + disarm |
| 14 | `SPI_B_MOSI` | O | hi-Z | — | no | as above |
| 15 | `SPI_B_MISO` | I | hi-Z | — | no | as above |
| 16 | `nCS_W5500` | O | hi-Z | 10 kΩ to `+3V3` | no | as above |
| 17 | `nRST_W5500` | O | hi-Z | 10 kΩ to `+3V3` | no | W5500 held out of reset; benign |
| 18 | `nINT_W5500` | I | hi-Z | 10 kΩ to `+3V3` | no | polled fallback |
| 21 | `I2C_SDA` | I/O-OD | hi-Z | 4.7 kΩ to `+3V3_A` | **indirect** | **both ADS1115 unreachable ⇒ the independent monitor is lost ⇒ hard fault ⇒ firmware STOPS the heartbeat** (ARCH-20) |
| 2 | `I2C_SCL` | I/O-OD | hi-Z | 4.7 kΩ to `+3V3_A` | **indirect** | as above |
| 33 | `MODE_A_RB` (pseudo-bipolar aux, buffered) | I | hi-Z | 74LVC14A output; aux pole has **2 × 10 kΩ to GND** in the 5 V domain | **read-only** | reads 0. With `MODE_B_RB` also 0 ⇒ `MODE_VALID=0` **in hardware** ⇒ ARM=0. Firmware reports `INVALID` |
| 34 | `MODE_B_RB` (unipolar aux, buffered) | I | hi-Z | as above | **read-only** | as above |
| 35 | `OVP_RB` (hardware OVP latch state) | I | hi-Z | 74LVC14A output | **read-only** | reads "tripped"; firmware refuses to arm. Fail-safe direction |
| 36 | `nOVP_CLR` | O | hi-Z | **AC-coupled (100 nF) + 10 kΩ to the inactive level** | **YES** | latch cannot be cleared ⇒ instrument will not arm. Fail-safe direction. **The AC coupling is the point: a stuck-HIGH GPIO cannot hold the OVP latch cleared** |
| 37 | `nALERT_ADC` | I | hi-Z | 10 kΩ to `+3V3_A` | no | polled fallback |
| 1 | `LED_NET` (firmware/network status only) | O | hi-Z | — | no | cosmetic. **The HV-PRESENT and FAULT lamps are NOT here** — §11 |
| 43 | `U0TXD` → CP2102N | O | **boot log, 115200** | — | no | serial console lost |
| 44 | `U0RXD` ← CP2102N | I | hi-Z | — | no | serial control lost ⇒ watchdog |
| 38, 47, 48 | **spare** | — | — | — | — | — |
| 39–42 | reserved for JTAG (MTCK/MTDO/MTDI/MTMS) | — | — | — | — | — |
| 0, 3, 45, 46 | **strapping — no net** | — | — | 10 kΩ pull-downs on 45, 46 | **none** | — |

**Count: 25 signals assigned (including UART0), 3 spare (GPIO38, 47, 48), JTAG preserved
(GPIO39–42), four strapping pins carrying no net.**

*(This count was wrong at first writing — it said 23 — and was caught by
`docs/studies/controller_power_numbers.py`, which enumerates the map independently and compares the
total against this line. That is what the script is for.)*

### 2.4 Why the status readback goes through a shift register, and how it is made honest

Eight-plus status bits read as direct GPIOs would consume every remaining pin and leave no spares.
They are read instead through **two cascaded 74LVC165A** `[unverified-MPN]` on the DAC's SPI bus
(`nSYNC_DAC` high ⇒ the DAC8552 ignores the clock, so the bus is shared safely).

**74LVC**, not 74HC: LVC inputs are 5 V-tolerant when `VCC = 3.3 V` `[recalled — confirm at Phase 6]`,
which is what lets a 3.3 V-powered register read the 5 V interlock domain without a translator.

The 16-bit word:

| bit | signal | note |
|---:|---|---|
| 0 | `MODE_A` | **redundant copy** of GPIO33 — a disagreement means the register or the direct line is dead |
| 1 | `MODE_B` | **redundant copy** of GPIO34 |
| 2 | `K1_AUX` | positive-relay armature position |
| 3 | `K2_AUX` | negative-relay armature position |
| 4 | `INTLK` | interlock loop (key + lid + guard) |
| 5 | `RAILOK_5V_MOD` | TPS3701 window comparator |
| 6 | `RAILOK_2V5_CLAMP` | TPS3701 window comparator |
| 7 | `RAILOK_5V_A` | TPS3701 window comparator |
| 8 | `WDOG_JMP` | local jumper permitting `SYST:WATCH 0` |
| 9 | `OVP_LATCH` | **redundant copy** of GPIO35 |
| 10 | `nON_P_RB` | **the actual level at the module's pin 4**, level-shifted — not the command |
| 11 | `nON_N_RB` | as above |
| 12 | `VSET_OVR_P` | VSET over-range comparator (§5.5) |
| 13 | `VSET_OVR_N` | as above |
| 14 | tied **HIGH** | pattern bit |
| 15 | tied **LOW** | pattern bit |

Two properties this buys that direct GPIOs would not:

- **A dead register is detectable.** Bits 14/15 must read `1,0`. Any other value ⇒ the readback path
  is untrustworthy ⇒ hard fault ⇒ firmware stops the heartbeat.
- **Bits 10/11 read the real `/ON` pin, not the commanded state.** This catches a stuck open-drain
  output, a missing or lifted pull-up, and a shorted `/ON` net — none of which any command-side
  check can see. It is the cheapest observability improvement on the board.

**Limitation, stated:** the shift register is a firmware-visible diagnostic only. **Nothing in the
interlock reads it.** The interlock reads the aux poles and the comparators combinationally
(MODE-14). If the register dies, the interlock is unaffected; only firmware's *knowledge* degrades,
and the correct response to degraded knowledge is to stop the heartbeat.

---

## 3. Power tree

### 3.1 Topology

```
                 ┌── F1 2 A(T) ──── Q1 P-FET ──── D1 TVS ──── C_bulk ────┐
  J1  12 V DC ───┤   reverse-block, soft-start   SMBJ15A      470 µF     │  +12V
  (2.1 mm        └── GND ───────────────────────────────────────────────┘
   locking)                                    (§4 input protection)
                                                       │
        ┌──────────────────────────────┬───────────────┴──────────────┐
        │                              │                              │
  ┌─────▼──────┐               ┌───────▼───────┐            ┌─────────▼─────────┐
  │ U10  BUCK  │               │  U11   BUCK   │            │  U12   LDO        │
  │ 12 → 5.00 V│               │ 12 → 3.30 V   │            │ 12 → 5.00 V       │
  │ 1.5 A      │               │ 1.0 A         │            │ LT3045, 60 mA     │
  └─────┬──────┘               └───────┬───────┘            └────────┬──────────┘
        │ +5V_MOD                      │ +3V3                        │ +5V_A
        │                              │                             │  (µV-class,
        │                              ├── ESP32-S3                  │   no switcher
        ├── 74HCT interlock logic      ├── W5500 + magnetics         │   current)
        ├── TPS3701 × 3 (RAIL_OK)      ├── CP2102N                   ├── REF5025 → +2V500_REF
        │                              ├── 74LVC14A / 74LVC165A      ├── OPA192 × 2 (monitor bufs)
        ├── [SW1] coil load switch     └── LP5907 ──► +3V3_A         ├── OPA192 × 2 (guard drivers)
        │      gated by ARM (C-1)            │  ADS1115 × 2          ├── TLV3202 × 3 (comparators)
        │      └─► +5V_COIL ──► K1…K4        │  DAC8552 VDD          │
        │                                    └  I²C pull-ups         └── R_sh 180 Ω ──► +2V5_CLAMP
        │                                                                 ║ 2 × LM4040-2.5 (shunt)
        ├── [SW2] +VIN_P load switch, gated by PERMIT_P (ARCH-19/SA-6)     ║   └─► OPA2320 × 2 supply
        │      └─► FB1 ferrite ─► 22 µF ─► U1 pin 1                        (the over-range CLAMP)
        │
        └── [SW3] +VIN_N load switch, gated by PERMIT_N
               └─► FB2 ferrite ─► 22 µF ─► U2 pin 1
```

### 3.2 Load budget, rail by rail

All arithmetic shown so it can be checked by hand. Module currents are **iseg Table 1 maxima**, not
typicals `[verified-artifact via NUMBERS_PROBE.md §6]`.

**`+5V_MOD` (buck from 12 V)**

| Load | mA | W |
|---|---:|---:|
| U1 `+VIN_P`, loaded at Vnom | 180 | 0.900 |
| U2 `+VIN_N`, loaded at Vnom **(simultaneous — G0-A4/NUM-22; the "only one is ever enabled" argument is DEAD)** | 180 | 0.900 |
| 74HCT interlock logic (7 packages, CMOS static + 1 kHz dynamic) | 5 | 0.025 |
| 3 × TPS3701 rail supervisors | 1 | 0.005 |
| `+5V_COIL` — **2 × Pickering `67-1-C-5/5D` at 125 mA + `K_S` at 36 mA** (`COMBINER_DESIGN.md` §4.2) | 286 | 1.430 |
| **Total** | **652** | **3.260** |

> ⚠ **This line moved by 206 mA after the sibling combiner document selected a real relay.**
> `NUMBERS_PROBE.md` §6.2 budgets *"4 relay coils at 20 mA = 80 mA"*, which is a plausible figure for
> a small signal relay and **not** the figure for a 5 kV-standoff reed relay: the Pickering part's
> coil is **40 Ω**, i.e. **125 mA at 5 V**. Both coils are energised at once in unipolar mode — that
> is the mode, not a transient. **See §0.4.2. `NUM-11` and `NUM-21` must be re-run in the probe;
> neither this document nor the combiner document edits the probe** (`CLAUDE.md` rule 1).

**`+3V3` (buck from 12 V)**

| Load | mA | W |
|---|---:|---:|
| ESP32-S3, WiFi TX peak `[recalled, NUM-21]` | 500 | 1.650 |
| W5500 + magnetics, 100 Mbps link `[recalled — Phase 6]` | 132 | 0.436 |
| CP2102N | 20 | 0.066 |
| 74LVC14A, 74LVC165A ×2, LP5907, LED | 30 | 0.099 |
| **Total (worst-case simultaneous)** | **682** | **2.251** |

Regulator sized at **1.0 A** (1.47× the simultaneous peak). `NUMBERS_PROBE.md` §6.3 already
established that ride-through capacitance is the wrong answer to the WiFi burst — a full 2 ms
802.11b frame at 100 mV droop needs 10 000 µF. **Size the regulator, fit 22 µF bulk + 100 nF local,
and stop.**

**`+5V_A` (LDO from 12 V)**

| Load | mA |
|---|---:|
| `R_sh` = 180 Ω shunt-rail feed (standing, no VSET load) | 13.9 |
| REF5025 (Iq + DAC VREF + 4 × 402 kΩ offset legs ≈ 25 µA) | 2 |
| OPA192 × 4 (2 monitor buffers + 2 guard drivers) | 4 |
| TLV3202 × 3 | 2 |
| LP5907 → `+3V3_A` (2 × ADS1115 @ 150 µA + I²C pull-ups) | 3 |
| **Total** | **≈ 25** |

Budget **60 mA** (the `NUMBERS_PROBE.md` §6.2 analog line, retained unchanged). ⇒ 0.30 W out.

**12 V input**

| Branch | W out | η | W in | mA @ 12 V |
|---|---:|---:|---:|---:|
| `+5V_MOD` buck | 3.260 | 0.90 | 3.622 | 302 |
| `+3V3` buck | 2.251 | 0.88 | 2.558 | 213 |
| `+5V_A` LDO | 0.300 | 0.42 | 0.720 | 60 |
| input protection, indicators, quiescent | — | — | 0.240 | 20 |
| **TOTAL** | **5.811** | **0.81** | **7.140** | **595** |

> **Recommended supply: 12 V DC, ≥ 2.0 A (24 W), IEC 62368-1 listed** `[unverified-MPN]`.
> 2.0 A is **3.36×** the computed 595 mA — down from 4.00× before the coil correction, and still
> above the **3.0× floor** this document sets. **2.5 A (30 W) restores 4.2× and costs nothing**; take
> it if the brick is being ordered anyway. The floor is 3.0× rather than the probe's 2.0× convention
> because §4.4's inrush and the unmeasured module turn-on surge (MEASURABLE-NOW, M-7) are not in the
> steady-state number.

> ### ⚠ CONSISTENCY CHECK AGAINST THE ENCLOSURE — **IT FAILS, AND THIS IS A REPORTED FINDING**
>
> Worst-case dissipation inside the chassis is the full **7.14 W** (essentially all input power
> becomes heat). `HV_SAFETY_ENVELOPE.md` §2 item 5 specifies **ventilation for 4.2–6.4 W**.
>
> **7.14 W is ABOVE that band by 0.74 W (12 %). The enclosure ventilation figure must be re-opened.**
>
> The cause is entirely §0.4.2's coil correction: 286 mA of coil current at 5 V is **1.43 W**, and
> **1.25 W of that is pure resistive heating in two relay coils** that the 4.2–6.4 W figure was never
> computed against. Three responses, in preference order:
>
> 1. **Re-run the enclosure thermal figure at 7.2 W** (`NUM-23` already flags the ventilation number
>    as needing a re-run for dual-mode). This is bookkeeping and is the honest answer.
> 2. **Accept it as a corner, not an operating point.** Both coils at 125 mA *and* both modules at
>    their datasheet-maximum 180 mA *and* a WiFi TX burst is a simultaneity that lasts milliseconds.
>    **But the two coils really are continuously energised in unipolar mode**, so 1.43 W of the
>    excess is steady-state, not a corner. Do not use this argument for the coil term.
> 3. **A coil economiser** (series resistor bypassed by a capacitor, dropping hold current after
>    pull-in) recovers ~60 % of the coil power. `COMBINER_DESIGN.md` §4.2 evaluated and **rejected**
>    it for the first build — the Pickering part's must-release voltage is 0.5 V, so an economiser
>    that overshoots drops the armature and **the failure is silent.** Do not revive it here to fix a
>    thermal number; fix the thermal number.
>
> **Recorded, not absorbed.** It is a cross-document inconsistency created by one document doing its
> job properly, and the correct outcome is that a third document gets updated.

### 3.3 Regulator selection

| Ref | Function | Part | Key specs | Notes |
|---|---|---|---|---|
| U10 | 12 → 5.00 V, **≥1.5 A** | **TPS54331DR** `[unverified-MPN]` | 3.5–28 V in, 3 A, 570 kHz, internal soft-start | Same part as U11 — one MPN, two uses. **652 mA steady-state after §0.4.2's coil correction**, so a 1.5 A rating is 2.3× and the 3 A part is comfortable. Post-filter with a 1 µH + 22 µF LC into the module branch. **Coil switching now moves 250 mA in ~4 ms steps — put the coil rail on its own local 100 µF so the step does not land on the module branch** |
| U11 | 12 → 3.30 V, 1.0 A | **TPS54331DR** `[unverified-MPN]` | as above | Feeds the ESP32 burst. **This is the rail that carries the WiFi TX current, and it is not the module rail** (Δ1) |
| U12 | 12 → 5.00 V analog, 60 mA | **LT3045EDD** `[unverified-MPN]` | 4.2–20 V in, 500 mA, 0.8 µVRMS (10 Hz–100 kHz), PSRR 76 dB @ 1 MHz, dropout 260 mV `[recalled — datasheet read at Phase 6]` | **7.0 V of headroom.** Dissipation `(12 − 5) × 60 mA = 0.42 W`; at ~45 °C/W on 2 oz copper that is +19 K. Alternative **TPS7A4901** (36 V, 150 mA) if 60 mA is confirmed |
| U13 | 5.0 → 3.30 V analog, 5 mA | **LP5907MFX-3.3** `[unverified-MPN]` | ultra-low-noise, 250 mA | Powers the two ADS1115 and the I²C pull-ups. **This is why the ADCs are not on the ESP32's rail** |
| — | `+2V500_REF` | **REF5025** `[web-verified, ti.com]` `[unverified-MPN]` | 2.500 V, ±0.05 % initial, 3 ppm/°C max, ±10 mA | **Sets DAC gain and the monitor offset leg. It is NOT the clamp** — see §5.3 |
| — | `+2V5_CLAMP` | **2 × LM4040DIZ-2.5 (grade A, ±0.1 %)** in parallel `[unverified-MPN]` | shunt reference | **This is the clamp.** §5.3 |

**Why 12 V rather than the probe's 5 V input — the two-sentence version.** You cannot LDO 5 V down to
a *quiet* 5 V, and `OPA192`'s minimum supply is 4.5 V, so a 5 V input puts the µV-class monitor
buffers on the same node as two HV converters and a WiFi radio. It also lets the ESP32's 500 mA burst
be taken from 12 V (213 mA) instead of from the module rail (388 mA).

### 3.4 Relay coil rail — closing open question N-5

`CONTROL_ARCHITECTURE.md` §7.1 N-5 and `COMBINER_STUDY.md` C-1: *"C-1 says 'the 12 V coil rail',
written when a 12 V module supply was expected. There is no 12 V module rail. Either 5 V coils, or a
dedicated generated 12 V rail that must be budgeted."*

> **Decision: 5 V coils, fed from `+5V_COIL`, which is `+5V_MOD` through a load switch gated by ARM.**

Reasoning:

1. **A 12 V coil rail now exists for free** (the input *is* 12 V), so the old objection — "you'd have
   to boost" — has evaporated. But taking the coils from the *raw input* would put relay coil switching
   transients upstream of every regulator's input filter, and would mean the coil rail survives a
   failure of the module rail. **Coils must die with the modules**, so the coil rail is derived from
   `+5V_MOD`, not from 12 V.
2. C-1 requires a **fail-safe-open switch in the coil rail**, gated by the same ARM element as the
   module supply. A high-side load switch at 5 V with a duplicated pull-down on its enable is the
   simplest correct implementation of that. **`ARM = 0` ⇒ coil rail dead ⇒ every relay to its
   de-energised position ⇒ per-module bleed engaged** (`CONTROL_ARCHITECTURE.md` §2.10).
3. Cost: a 5 V coil draws ~2× the current of a 12 V coil at the same *power*. ⚠ **On the selected
   part it is not that simple, and the honest answer is better rather than worse.**
   `COMBINER_DESIGN.md` §4.2 read the Pickering `67-1-C-5/5D` datasheet: the **5 V coil is
   simultaneously the lowest-power option** (0.625 W, versus 0.960 W for both the 12 V and 24 V
   variants) **and the only one needing no extra rail.** The usual "5 V coils cost you current"
   intuition does not hold here. What *did* move is the absolute number — 125 mA per coil, not the
   20 mA `NUM-21` assumed — and that is a part-selection fact, not a rail-voltage consequence.
   **See §0.4.2 and the finding in §3.2.**

**Coil count — and the explicit absence of a mode coil.**

| Element | Coils | Current at 5 V | Certainty |
|---|---:|---:|---|
| K1 — positive-module Form C changeover (HV routing + module bleed) | 1 | **125 mA** | **certain**, part selected: Pickering `67-1-C-5/5D`, 40 Ω coil (`COMBINER_DESIGN.md` §4.2) |
| K2 — negative-module Form C changeover | 1 | **125 mA** | **certain**, same part |
| `K_S` — LV interlock armature routing `+VIN` and coil power | 1 | **36 mA** | Panasonic `TQ2SA-5V` (`COMBINER_DESIGN.md` §6.3) |
| K3 / K4 — per-output-node bleed/dump elements | 0–2 | not yet budgeted | **provisional** — see the note below |
| **Mode selector** | **0** | **0 mA** | ⬛ **G0-A5: it is a physical switch with NO COIL.** `NUM-21`'s dual-mode coil uplift is struck |
| **BUDGETED** | **3** | **286 mA** | **supersedes `NUMBERS_PROBE.md` §6.2's 80 mA — see §0.4.2** |

⚠ **If K3/K4 are fitted as separate relays, the coil rail grows again.** At Pickering-class coil
currents that would be another ~250 mA and would take the 12 V input to roughly **8.4 W**, well
outside the enclosure band. **This is a reason to prefer an output-node bleed arrangement that uses
spare contacts on K1/K2 or on `K_S` rather than new coils** — but the arrangement is
`COMBINER_DESIGN.md`'s decision, not this document's, and the finding is passed to it rather than
resolved here.

> **Note on K3/K4, and a finding handed to the combiner owner.** `CONTROL_ARCHITECTURE.md` §2.10's
> elegant result — *"the bleed and the break-before-make interlock are the same physical mechanism"* —
> was derived for **one** output node. It does **not** generalise to two, and the reason is specific:
> in pseudo-bipolar mode both K1 and K2 feed `HV_OUT_A`, so an output-node bleed hung on K1's NC
> contact would **short the negative module's output through the bleed whenever K2 is selected**. The
> output-node bleed must therefore be a function of *both* relays, and a series NC-contact chain is
> the wrong answer (a single failed-open contact removes the bleed silently — NUM-09's exact failure).
> **Two dedicated bleed elements, one per output node, is the arrangement this document budgets for.**
> Deciding it is `COMBINER_STUDY.md`'s job at G1, not this document's; **the budget is sized so that
> the answer cannot be constrained by the power tree.**

**Coil drive.** Low-side N-FET per coil, gate from the 5 V logic domain with **2 × 100 kΩ gate
pull-downs** (duplicated, ARCH-18) so an open drive line ⇒ coil de-energised ⇒ bleed engaged.

> ⚠ **Cross-document finding, passed to `COMBINER_DESIGN.md` §6.3.** That document specifies
> **2N7002** for `Q_K1`/`Q_K2`. **A 2N7002's continuous drain current is ~115 mA `[recalled — confirm
> at Phase 6]`, and the selected Pickering coil draws 125 mA.** The driver would be operated above
> its continuous rating from the first energisation. **Specify a ≥300 mA part** — e.g. `DMN2075U`,
> `2N7002K`, or `BSS138` at 200 mA (still only 1.6×, so prefer the 300 mA class)
> `[unverified-MPN]`. **Flagged, not silently corrected in someone else's document.**

Freewheel: the `67-1-C-5/**5D**` suffix means the relay has an **internal** flyback diode, so the
coil polarity is **not optional and must be observed** (`COMBINER_DESIGN.md` §4.2,
`[verified-artifact]`). **Do not add an external series-Zener release accelerator across a coil that
already has an internal diode** — it cannot work, because the internal diode clamps first. If faster
release is ever needed, it must come from a part **without** the `D` suffix plus an external
diode + 15 V Zener; that is a part-selection change, not an addition.

### 3.5 Module `+VIN` load switches — ARCH-19 / SA-6 implemented

`INTERFACES.md` **SA-6**: *"Each module's `+VIN` reaches it only through the interlock element; a
direct rail-to-`+VIN` path is a failure."* ARCH-19: *"`+VIN` removal is the PRIMARY disable; `/ON` is
secondary."*

Per module: **TPS22918DBVT** `[unverified-MPN]` (5.5 V, 2 A, adjustable slew via `CT`), enable driven
from `PERMIT_P` / `PERMIT_N`, with **2 × 100 kΩ pull-downs on `EN`**. Slew set to ≈ 1 ms by `CT` so
the two module converters do not present a step load to U10 (§4.4).

Then, per module and within 5 mm of pin 1: **ferrite bead** (e.g. BLM31PG601SN1, 600 Ω @ 100 MHz,
3 A `[unverified-MPN]`) → **22 µF** (iseg Table 1 note 2, `[verified-artifact]`; `INTERFACES.md`
SA-13) → **100 nF** → pin 1.

**Single-fault note.** A load switch failing *short* leaves the module permanently powered. That is a
single fault, and it is covered because `/ON` is an **independent** disable driven by the same
`PERMIT` term through a different physical path (open-drain gate + pull-up to `+VIN`). Two mechanisms,
no shared element except the logic signal itself. The load switch failing *open* is fail-safe.

---

## 4. Input protection

Order matters and is stated as a chain, because getting the order wrong is the usual defect.

```
J1 ─► F1 ─► Q1 (P-FET, reverse block + soft start) ─► D1 (TVS) ─► C_bulk ─► π ─► regulators
```

### 4.1 Elements

| Ref | Part | Value / rating | Purpose and reasoning |
|---|---|---|---|
| **F1** | **Littelfuse 0453002.MR Nano2, 2 A time-lag** `[unverified-MPN]` | 2 A, 125 V | **A real fuse, not a polyfuse.** A polyfuse's hold current swings widely with ambient, its resistance rises permanently after every trip, and its failure mode is a *sagging rail* — on an instrument whose module rail must stay inside 4.5–5.5 V, a sagging rail is worse than a stopped instrument. Time-lag because §4.4's inrush is real |
| **Q1** | P-channel MOSFET, e.g. **SI7135DP** `[unverified-MPN]` | −30 V, R_DS(on) ≈ 20 mΩ | Reverse-polarity block. At 500 mA: `0.5² × 0.02 = 5 mW`. Source to input, drain to load, gate through R_g to GND, **Zener BZX84C12 gate clamp** so V_GS never exceeds 12 V |
| **R_g / C_gs** | 100 kΩ / 100 nF | τ = 10 ms | **Soft-start.** Q1 turns on over ≈10 ms, limiting inrush into C_bulk to roughly `C·dV/dt = 470 µF × 12 V / 10 ms ≈ 0.56 A` — comfortably under F1 |
| **D1** | **SMBJ15A** `[unverified-MPN]` | 15 V standoff, 24.4 V clamp @ 26 A | Transient/overvoltage. Placed **after** Q1: reverse polarity is then simply *blocked* and does not blow F1. A sustained overvoltage clamps and F1 opens |
| **C_bulk** | 470 µF / 25 V low-ESR aluminium + 100 nF X7R | | |
| **CM choke + π** | e.g. **744232222** `[unverified-MPN]` | 2 × 2.2 mH | Conducted-emissions filter. Not a safety element; sized at Phase 4 |

### 4.2 Earth and the input's relationship to it

The chassis must be bonded to protective earth (`HV_SAFETY_ENVELOPE.md` §2.1: the module cases,
board GND and chassis are **one node**, and it must be earthed, not floating).

> **Do not rely on the DC brick for protective earth.** A 2-wire (Class II) brick has none, and a
> 3-wire brick's DC-side earth continuity is not a specified parameter. Fit a **dedicated M4 earth
> stud** on the chassis with a green/yellow bonding lead, and bond board GND to that stud at **one
> point**, adjacent to the HV modules' GND pins. Chassis-to-earth-pin resistance **< 0.1 Ω** is
> already a Phase-7 acceptance item (`HV_SAFETY_ENVELOPE.md` §4, item 1.5).
>
> Consequence: board 0 V is earthed. A Class I brick that also earths its output 0 V creates a
> parallel earth path (a ground loop, not a hazard). A Class II brick's floating output is bonded by
> us. **Either is acceptable; neither is the safety earth.**

### 4.3 What input protection deliberately does *not* do

It does not protect the modules against a regulator failing with its pass element shorted — 12 V would
reach a 4.5–5.5 V input. That is **not** an input-protection problem and is not solved here; it is
solved by the `RAIL_OK` window supervisors in §6.3 (finding F-13).

### 4.4 Inrush — and why it mostly closes itself

`NUMBERS_PROBE.md` §6 lists inrush as an explicit blind spot: *"both module converters and the buck
start together; this model is steady-state only."*

**In this architecture they do not start together**, and that is structural rather than lucky:

1. At power-on, `ARM = 0` (no heartbeat, `ARM_EN` pulled down, OVP latch powers up **set**, §6.4).
2. `ARM = 0` ⇒ `PERMIT_P = PERMIT_N = 0` ⇒ **both module `+VIN` load switches are OFF**. The HV
   modules draw nothing at power-on. Their converters start only when a human has closed the
   interlock, firmware is alive and toggling, and an explicit `SYST:ARM ON` has been accepted.
3. `ARM = 0` ⇒ the coil rail load switch is OFF ⇒ no coil inrush at power-on.
4. So the only power-on inrush is C_bulk plus three regulator soft-starts, and Q1's 10 ms gate
   ramp bounds it at ≈0.56 A.
5. The *module* inrush happens later, at ARM, into a rail that is already up and regulating, through
   a load switch with a 1 ms controlled slew (§3.5).

**MEASURABLE-NOW — new register entry M-7: module `+VIN` inrush and turn-on profile.** Nobody has
measured what an APS module's converter draws in the first milliseconds after `+VIN` is applied, and
iseg does not publish it. It sizes U10's transient response and the TPS22918's `CT`.
**If it comes back at the pessimistic end** (say a 1.5 A, 1 ms surge per module): raise `CT` to slew
over 5 ms, add 100 µF of local bulk on `+5V_MOD` downstream of U10, and **stagger the two ARM-time
load switches by 20 ms in firmware** — none of which changes the topology, which is why this
measurement is not on the critical path.

---

## 5. The set-point path and the over-range clamp

> **This is the primary safety element of the design** (G0-A2 CONSEQUENCE 1; `DECISIONS.md` PART-33;
> `SCOPE.md` S-8). It gets its own verification (§12).
>
> ### ⬛ GOVERNANCE: `docs/design/SETPOINT_PATH.md` SUPERSEDES THIS SECTION'S COMPONENT VALUES
>
> That document is the dedicated treatment of the set-point path and it was written in parallel with
> this one. **Read this section for the argument; take the component values from `SETPOINT_PATH.md`.**
> The two agree that the buffer is mandatory and that its supply rail *is* the clamp — a conclusion
> both reached independently, and one that contradicts `CONTROL_ARCHITECTURE.md` §1.7's headline.
> They differ in three places and `SETPOINT_PATH.md` is right in all three: the **clamp-rail
> topology** (a buffered reference, not my shunt — my clamp-rail load figure was 2.2 mA short), the
> **comparator threshold reference** (a dedicated LM4040-2.048, not my rail-derived divider), and the
> **declared range** (**±950 V guaranteed / ~980 V typical**, which folds in the module's own Vref
> tolerance that I did not). **Full reconciliation in §0.4.1.**
>
> **What this section still owns** is the *power-tree* consequence: §3.2's 60 mA analog budget covers
> either arrangement, which is the property a power tree should have.

### 5.1 The chain

```
ESP32 ──SPI-A──► DAC8552 ──► OPA2320 buffer ──► ≤10 Ω ──► VSET_x pin ──► module
                 VDD  = +3V3_A          V+ = +2V5_CLAMP        │
                 VREF = +2V500_REF          (2.500 V, SHUNT)   ├─ 2 × 1 kΩ to GND (= 500 Ω)
                        (REF5025)                              ├─ 2N7002 shunt FET, gate = /ON_x
                                                               └─ 1 kΩ ──► TLV3202 over-range comp
```

### 5.2 Why the buffer is mandatory, resolving a contradiction inside §1.7 (Δ2)

`CONTROL_ARCHITECTURE.md` §1.7's heading says *"Drive VSET directly. No PWM, no RC filter, **no buffer
op-amp**"*, and its own post-G0 note thirty lines later says *"The buffer/RRO stage may **NOT** be
dropped as a BOM saving… It is now resolved and frozen: **keep it**."* **These cannot both be
followed.** The note is the later statement and it is the safety-driven one, so it governs.

The buffer is what makes the clamp *structural*:

- **DAC8552's minimum VDD is 2.7 V** `[web-verified, ti.com]`. You therefore **cannot** power the DAC
  from a 2.500 V rail, so "the DAC output cannot exceed 2.5 V" is a statement about its *transfer
  function*, not about its *silicon*. A DAC output-stage fault reaches VDD.
- Running the DAC from `+3V3_A` (its logic then matches the ESP32's 3.3 V levels, which a 5 V VDD
  would not — `V_IH = 0.7 × VDD = 3.5 V > 3.3 V`) means a DAC output fault reaches **3.3 V = 1320 V**
  at the output. **Exactly the G0-A2 hazard.**
- A **rail-to-rail-output op-amp cannot exceed its own supply.** Its supply is `+2V5_CLAMP`.
  Therefore `VSET ≤ 2.500 V` **structurally**, regardless of what the DAC does.

> **⇒ The DAC's rail is deliberately allowed to be 3.3 V, because the buffer makes it irrelevant.**
> That is the whole mechanism, and it is the reason `CONTROL_ARCHITECTURE.md` §6.4 rule 8 (*"no net
> that touches `VSET_*` may also touch `+3V3`"*) is still satisfied: the 3.3 V domain stops at the
> buffer's input pin, which is not a `VSET_*` net.

### 5.3 Why the clamp rail is a SHUNT reference and why there are two of them (Δ3)

A **series** reference (REF5025) fed from `+5V_A` fails to *its input* on a pass-element short. Five
volts on the clamp rail is **2000 V** at the output, from one component fault, on the element the
whole safety case rests on.

A **shunt** reference cannot fail that way: raising the rail is the thing it exists to sink. Its one
relevant failure is **open circuit**, which would let the rail rise to `+5V_A` through `R_sh`.
ARCH-18's rule — *duplicate every safe-state pull element* — applies directly:

> **`+2V5_CLAMP` = `+5V_A` through `R_sh` = 180 Ω 1 % 1206, shunt-regulated by TWO paralleled
> LM4040DIZ-2.5 (grade A, ±0.1 %)** `[unverified-MPN]`.
>
> - Available current: `(5.00 − 2.50) / 180 = 13.9 mA`
> - Worst-case load: two buffers at 98 % code into their 500 Ω pull-downs = `2 × 2.4512/500 = 9.80 mA`,
>   plus 2 × 17 µA of op-amp quiescent
> - Remaining shunt current, split between two devices: `(13.9 − 9.84)/2 = 2.02 mA each` — well above
>   the LM4040's ~60 µA minimum operating current `[recalled — datasheet at Phase 6]`
> - At the `+5V_A` low corner (4.75 V): `(4.75 − 2.50)/180 = 12.50 mA`, remaining `1.35 mA` each ✓
> - Dissipation: `R_sh` at no load `2.5²/180 = 34.7 mW`; each LM4040 ≤ 17 mW ✓
>
> **One reference open ⇒ the other holds the rail.** **One reference shorted ⇒ the rail collapses to
> 0 V ⇒ `VSET` = 0 ⇒ output off.** *Both single-fault outcomes are safe, in opposite directions.*
> That is what duplication is supposed to buy and it is worth checking that it actually does.

`REF5025` keeps its jobs — DAC `VREF`, and the four 402 kΩ monitor offset legs — but **is no longer
load-bearing for over-range**. Its ±0.05 % / 3 ppm accuracy is what those jobs need; the clamp needs
current capability and a fail-direction, which is what a shunt gives.

### 5.4 The headroom arithmetic, and where the ±980 V comes from (Δ4)

The buffer must swing to the commanded voltage while sitting on a 2.500 V rail. Worst case:

| Quantity | Value |
|---|---:|
| `+2V5_CLAMP` worst-case low (LM4040 grade A, −0.1 %; with two in parallel the *lower* device sets the rail) | **2.4975 V** |
| `REF5025` worst-case high (+0.05 %) | 2.50125 V |
| DAC code clamp, 98 % of full scale ⇒ commanded `VSET` | **2.4512 V** |
| Headroom available to the buffer | **46.3 mV** |
| Buffer load at that point (into 2 × 1 kΩ = 500 Ω) | **4.90 mA** |
| OPA2320 output swing from rail at ≈5 mA `[recalled — read the swing-vs-load curve at Phase 6]` | ≈30 mV |
| **Margin** | **≈1.5×** |

> **Declared full scale is therefore ±980 V by this section's arithmetic** — but see the governance
> banner above: **`SETPOINT_PATH.md` §10 is the governing figure and it is `±950 V guaranteed,
> ~980 V typical`**, because it additionally stacks the module's own Vref tolerance (±1 %,
> 2.475–2.525 V) and its ±1 % adjustment accuracy. **±980 V is a typical, not a guarantee, and
> declaring a typical as a spec is the REF-05 anti-pattern.** What both agree on: it is a deliberate
> specification, not a shortfall. Two things make it cost nothing: the module's own **adjustment accuracy is ±1 %
> (±10 V)** `[verified-artifact, PART-34]`, so "1000 V" was never a deliverable number; and the
> instrument closes the loop on its own monitor (`CONTROL_ARCHITECTURE.md` §1.3), which turns the
> 2 % into a calibration constant over the range that *is* declared.
>
> **If the Phase-6 datasheet read shows OPA2320 cannot make 30 mV at 4.9 mA**, the fallbacks in
> preference order are: (i) drop the code clamp to 96 % ⇒ **±960 V**; (ii) raise the `VSET`
> pull-downs to 2 × 1.5 kΩ (= 750 Ω), which halves the buffer load but degrades the
> buffer-dead default from **4.8 %** to **7.0 %** of Vnom (48 V → 70 V) — both are far below any
> hazard threshold and both are inside or just above the module's unspecified <20 V band;
> (iii) a different RRO op-amp. **Do not solve it by raising the clamp rail.**

**Buffer part.** **OPA2320AIDGKR** (dual) `[unverified-MPN]`: RRIO, 1.8–5.5 V, V_os 150 µV max,
±40 mA output. One package covers both channels. *Not* OPA333 — its output stage is too weak at
5 mA for the headroom above (`[recalled]`; this is the specific reason).

**Commanded zero is not electrical zero.** At DAC code 0 the buffer's output cannot go below its own
sink saturation, ≈12 mV at 250 µA ⇒ ≈5 V at the HV output. That is inside the module's
**unspecified** band (`Vout ≤ 2 %·Vnom = 20 V`), so it is not a defect — **but firmware's "zero" must
mean *disable + shunt*, not *DAC code 0*.** The 2N7002 shunt FET, gated directly from `/ON_x`
(`CONTROL_ARCHITECTURE.md` §3.6), is what produces a real zero.

### 5.5 The `VSET` over-range comparator — a second layer for what the rail cannot see

`CONTROL_ARCHITECTURE.md` §1.7 is explicit that the rail clamp does **not** cover a fault *downstream*
of it: a short from `VSET` to the 3.3 V rail at the module pin, a broken `VSET` track (open ⇒ full
scale), or a lifted pull-down. Those are covered by ARCH-05/ARCH-18/§3.6 *"and by nothing else."*

Add one thing else, for two comparators:

> **TLV3202 (dual)** `[unverified-MPN]`, one comparator per channel, input tapped **at the module pin**
> through 1 kΩ, threshold **2.625 V (= 105 % of Vref)**.
>
> - Threshold source: a 0.1 % divider from **`+5V_A`** — `R_top = 9.53 kΩ`, `R_bot = 10.5 kΩ` ⇒
>   `5.000 × 10.5/20.03 = 2.621 V`. **Deliberately not derived from REF5025**, per the Phase-7 check
>   *"confirm its threshold reference is not the reference that feeds the DAC — a comparator on that
>   node fails in the same event it exists to catch"* (`HV_SAFETY_ENVELOPE.md` §4, item 2.5).
> - Outputs wire-OR into the OVP latch (§6.4) ⇒ `nOVP = 0` ⇒ `ARM = 0` ⇒ both modules off, **in
>   hardware, with no firmware involvement**. Also readable as `VSET_OVR_P/N` in the status word.
> - **The 1 kΩ series resistor does not violate the ≤10 Ω rule** (`CONTROL_ARCHITECTURE.md` §1.4,
>   ARCH-04). That rule bounds the **drive** path's source impedance, because the module's internal
>   10 kΩ pull-up turns series resistance into a first-order offset. A **sense** tap into a 1 pA
>   comparator input carries no current and produces no offset. The resistor is there to stop the
>   comparator's ESD diodes conducting into a dead `+5V_A` rail. **State this distinction in the
>   schematic note, because it is exactly the kind of thing a reviewer will flag as a violation.**

---

## 6. The interlock gate, extended — arm/disarm and the ARM chain

### 6.1 The algebra (extends `CONTROL_ARCHITECTURE.md` §3.3a; Δ5)

```
  MODE_VALID = MODE_A  XOR  MODE_B                 -- positive decode of BOTH modes (MODE-18)
  MODE_UNI   = MODE_B  AND  NOT MODE_A             -- "unipolar / dual-output" permissive

  ARM        = EN_HB · ARM_EN · INTLK · nOVP · SETTLE · RAIL_OK · MODE_VALID     (7 terms)

  /ON_P      = NOT ( ARM · OUT_EN · ( MODE_UNI + NOT SEL ) )   -- open drain, 10 kΩ ↑ +VIN_P
  /ON_N      = NOT ( ARM · OUT_EN · ( MODE_UNI +     SEL ) )   -- open drain, 10 kΩ ↑ +VIN_N

  PERMIT_P   = ARM · ( MODE_UNI + NOT SEL )        -- gates +VIN_P load switch AND K1 coil
  PERMIT_N   = ARM · ( MODE_UNI +     SEL )        -- gates +VIN_N load switch AND K2 coil
```

**Read the safety property off it, unchanged from §3.3a:** `PERMIT_P ∧ PERMIT_N` requires
`MODE_UNI = 1`, i.e. it requires the **armature to be physically in the dual-unipolar position** —
which is the position in which the two modules are on **different nodes**. When `MODE_UNI = 0` the
expression collapses exactly to session 1's `SEL`/`¬SEL` gate. **There is no input combination in
which both modules are enabled onto one node.** `MODE_CMD` does not exist (G0-A5, MODE-12), so the
attack row is unreachable rather than merely defeated.

**The three new ARM terms, each closing a named fault:**

| Term | Source | What it closes |
|---|---|---|
| `ARM_EN` | ESP32 GPIO5, **2 × 10 kΩ to GND at the 74HCT30 input** | ARCH-35's explicit, revocable arm bit. Disarm is **sub-microsecond**, versus the heartbeat pump's 61.5–164.5 ms decay. "Energised" is never one packet away from "idle" |
| `RAIL_OK` | wire-AND of 3 × TPS3701 open-drain outputs | A regulator failing with its pass element shorted puts 12 V on a 4.5–5.5 V module input (§10, F-13). Also catches an LDO short putting 12 V on `+5V_A` |
| `MODE_VALID` | `MODE_A ⊕ MODE_B` | MODE-18's intermediate/illegal position, as an **ARM term** rather than a special case. Between detents, or with a broken aux lead, or with the two aux nets shorted ⇒ `MODE_VALID = 0` ⇒ both modules off, both outputs bled |

**`OUT_EN` is deliberately NOT an ARM term.** It sits only in the `/ON` path, so that
`ARM ∧ ¬OUT_EN` is a real, distinct state: **modules powered, relays positioned and settled, HV off
by `/ON`.** That is session 1's S1 ARMED, and it is what `CONTROL_ARCHITECTURE.md` §5.1 Gap 3 means by
*"S0 SAFE and 'armed but at zero' are not the same state and must not be conflated."*

> **Is a GPIO in the `/ON` path a violation of §3.1's "never drive `/ON` from a GPIO"?** No, and the
> distinction is load-bearing. `OUT_EN` is **one term of an AND whose other terms are hardware**. A
> stuck-high `OUT_EN` — the worst case — cannot enable anything, because `ARM` is independently
> required and `ARM` requires a physically-closed key/lid/guard loop, a live toggling heartbeat, a
> valid mode decode, three healthy rails and an un-tripped OVP latch. What §3.1 forbids is a GPIO
> being **sufficient**. This one is not even close to sufficient.

### 6.2 Gate implementation — exact packages

All in **74HCT** (TTL input thresholds, `V_IH = 2.0 V`) on **`+5V_MOD`**.

> **HCT, not HC, on every input reachable from the ESP32.** 74HC at `VCC = 5 V` has
> `V_IH = 0.7 × VCC = 3.5 V`; a 3.3 V ESP32 output **does not meet it**. This is the single most
> likely silent defect in this whole section — an HC part will *appear* to work at room temperature
> and fail at a corner.

| Ref | Part | Gates used | Function |
|---|---|---|---|
| U20 | **74HCT30** (8-input NAND) `[unverified-MPN]` | 1 | `¬ARM` from all 7 terms (8th input tied HIGH) |
| U21 | **74HCT14** (hex Schmitt inverter) | 6 | `ARM` (invert U20); `¬MODE_A`; `¬SEL`; heartbeat-pump conditioning; OVP-clear edge squaring; 1 spare |
| U22 | **74HCT86** (quad XOR) | 1 + 3 | `MODE_VALID = MODE_A ⊕ MODE_B`; three edge detectors (`SEL`, `MODE_A`, `MODE_B`) for `SETTLE` |
| U23 | **74HCT08** (quad AND) | 4 | `MODE_UNI`; `PERMIT_P`; `PERMIT_N`; `ARM·OUT_EN` |
| U24 | **74HCT32** (quad OR) | 3 | `MODE_UNI + ¬SEL`; `MODE_UNI + SEL`; OR of the three edge pulses into U25 |
| U25 | **74HCT123** (dual retriggerable monostable) | 1 | `SETTLE`. `R_ext = 1 MΩ`, `C_ext = 2.2 µF film` ⇒ `t_w ≈ 0.45·R·C = 0.99 s` `[recalled — the 74HCT123 pulse-width formula and its R_ext range must be read at Phase 6]` |
| U26 | **74HCT03** (quad 2-in open-drain NAND) | 2 | `/ON_P`, `/ON_N`. **Pull-ups 10 kΩ to each module's OWN `+VIN`, within 5 mm of pin 4** (ARCH-17) |
| U27 | **74HCT00** (quad NAND) | 2 + 2 | OVP SR latch + power-on-set network |

Propagation: 74HCT `t_pd` ≈ 25 ns max per gate at 5 V `[recalled]`; the deepest `/ON` path is four
gates ⇒ **≤ 100 ns**. The module's internal set node has **τ = 100 ms** (`[verified-artifact]`,
manual Figure 2), i.e. **10⁶× margin**. Logic timing is not a constraint anywhere in this design and
should not be treated as one.

**`SETTLE` and mode edges.** `CONTROL_ARCHITECTURE.md` §3.3a requires `SETTLE` to cover `MODE_POS`
edges as well as `SEL` edges. Two independent mechanisms now do:

1. **Require the aux poles to be NON-SHORTING (break-before-make between detents).** Then any mode
   movement necessarily passes through "neither aux closed" ⇒ `MODE_VALID = 0` ⇒ `ARM = 0`
   **combinationally**, with no timing element at all. **Add "non-shorting aux contacts" to the switch
   specification (§7.4)** — it is what makes MODE-18 a decode rather than a hope.
2. The three XOR edge detectors into U25 give the same result through a second path, and hold it for
   `T_dwell ≈ 1 s`.

### 6.3 `RAIL_OK` — window supervision

Three **TPS3701** `[unverified-MPN]` (dual-channel OV+UV window comparator, 3–36 V, open-drain),
powered from **`+5V_MOD`** with their outputs wire-ANDed and pulled up to `+5V_MOD`.

| Rail | UV trip | OV trip | Why those numbers |
|---|---:|---:|---|
| `+5V_MOD` | **4.62 V** | **5.38 V** | Module `Vin` range is **4.5–5.5 V** `[verified-artifact, PART-30]`. With the supervisor's own ±1 % the trips land at 4.57–4.67 and 5.33–5.43 — **both inside the module's window with margin** |
| `+2V5_CLAMP` | **2.40 V** | **2.60 V** | OV at 2.60 V = 104 % of Vref ⇒ trips **before** the 2.625 V `VSET` comparator, so the rail fault is diagnosed as a rail fault |
| `+5V_A` | **4.60 V** | **5.40 V** | OPA192 minimum supply is 4.5 V `[web-verified]`; below that the monitor buffers are out of spec and the monitor cannot be trusted |

**Powering the supervisors from `+5V_MOD` is the fail-safe choice**: if that rail dies, the modules
die with it and the whole question is moot. If any *other* rail dies, its supervisor is still alive to
say so.

### 6.4 The OVP latch, and the one detail that makes it real

SR latch from two 74HCT00 gates. **Set** inputs (wire-OR): the four HV-monitor window comparators
(±105 % on each output's buffered tap) and the two `VSET` over-range comparators.

Two properties that are easy to omit and fatal to omit:

1. **The clear path is AC-coupled.** `nOVP_CLR` (GPIO36) reaches the latch through **100 nF in series
   with a 10 kΩ pull to the inactive level**, squared by a 74HCT14. **Only an edge clears the latch.**
   A stuck-high or stuck-low GPIO — or a firmware bug that leaves the line asserted — **cannot hold
   the protection defeated.** Without this, the OVP is one stuck GPIO away from being decorative.
2. **The latch powers up SET (tripped).** An RC into the Set input asserts a trip at power-on. Every
   power-up therefore begins latched-off and requires an explicit clear before arming. A brownout that
   glitches the logic rail lands in the same place.

*Operational consequence, stated so it is not a surprise:* `SYSTem:ARM ON` implicitly issues one clear
pulse **if and only if** no comparator is currently asserting. A latch set by a genuine over-range
while running requires the explicit `OUTPut:PROTection:CLEar` and a human.

**Threshold references for the HV window comparators** come from `+2V5_CLAMP`, not from REF5025. That
is deliberate and it has a cost worth naming: REF5025 also drives the divider's 402 kΩ offset leg, so
a REF5025 drift moves the *tap* without moving the *threshold*. **That is the correct direction** — a
collapsing REF5025 moves the tap to a wrong place, and the OVP should notice, which it cannot if both
sides move together.

### 6.5 Arm / disarm — the complete mechanism

Seven independent conditions, of which **three are physical, three are hardware-electrical, and one is
firmware intent**. HV exists only when all seven hold.

| Layer | Condition | Nature | Revoked by |
|---|---|---|---|
| L0 | `INTLK` loop closed: **key switch ∧ lid switch ∧ mode-guard microswitch**, in series | **physical** | turning the key, lifting the lid, opening the mode guard |
| L1 | `MODE_VALID` — exactly one aux pole closed | **physical** | the selector between detents, or a broken aux lead |
| L2 | `RAIL_OK` — three rails inside their windows | hardware | a regulator fault |
| L3 | `nOVP` — latch not set | hardware | any of six comparators |
| L4 | `SETTLE` — no `SEL` or mode edge within `T_dwell` | hardware | moving anything |
| L5 | `EN_HB` — heartbeat pump charged | hardware, **proves firmware liveness** | firmware stopping the toggle (61.5–164.5 ms) |
| L6 | `ARM_EN` — firmware intent | firmware | `SYSTem:ARM OFF`, any hard fault, watchdog expiry (sub-µs) |
| L7 | `OUT_EN` — output enable (`/ON` path only, not an ARM term) | firmware | `OUTPut OFF` |

**Arming sequence** (each step is a precondition for the next; any failure aborts to SAFE):

1. `INTLK` closed and `MODE_VALID` asserted and `RAIL_OK` asserted — all read back and *reported*, none
   assumed.
2. Both DAC codes written to 0; both `VSET` measured (through the status word's `VSET_OVR` bits and
   the ADC rail-health channels) as not over-range.
3. `MEAS:VOLT?` on **every output that is live in the physically-selected mode** reads `|V| < V_safe`
   (10 V). **Measured, not timed, not assumed.**
4. One `nOVP_CLR` pulse if no comparator is asserting.
5. `ARM_EN` asserted; heartbeat already running.
6. ⇒ `PERMIT_x` asserted ⇒ module `+VIN` load switch closes, relay coil energises. Wait for
   **relay settle (50 ms) + bounce (10 ms)** *and* for the module's own turn-on
   (**MEASURABLE-NOW, M-4**), then confirm `K1_AUX`/`K2_AUX` in the status word.
7. `OUT_EN` asserted ⇒ `/ON_x` goes LOW ⇒ HV enabled at DAC code 0.
8. Ramp.

**Disarm** is `ARM_EN` low. It is reachable from every state, is always accepted, is never queued
behind anything, and is the response to every hard fault. **`*RST` disarms.** A parser error disarms
nothing (an error is not a fault), but a *malformed* command that cannot be parsed at all still leaves
the watchdog un-kicked, which disarms on expiry.

---

## 7. Comms, watchdog and control ownership

### 7.1 Transports, all three write-authoritative (G0-A3, not re-litigated)

| Transport | Physical | Isolation | Rank |
|---|---|---|---|
| **USB-CDC** via CP2102N | panel USB-C | **ISOUSB211 / ADuM3160** `[unverified-MPN]` | default control path |
| **Ethernet/TCP** via W5500 | panel RJ45 with integrated magnetics | **magnetics, ~1.5 kV** `[recalled]` | **primary network path** (§1.3) |
| **WiFi/TCP** | external antenna, RP-SMA bulkhead | none | secondary network path |
| USB-Serial-JTAG (native) | **internal header only** | none | programming/recovery, chassis open, HV supply disconnected |

Same SCPI grammar on all of them (`INTERFACES.md` §3).

### 7.2 Control ownership — required because there are now *two* write-authoritative networks (Δ12)

With one write-authoritative transport, "any received command kicks the watchdog" is correct. With
three, it is a hole: **a telemetry poller on WiFi keeps HV alive while the operator's serial link is
dead.** A watchdog that is kicked by someone other than the person in control is not a watchdog.

```
SYSTem:LOCK:REQuest?     -> 1 (granted, this session now owns write) | 0 (denied, someone else owns it)
SYSTem:LOCK:RELease
SYSTem:LOCK:OWNer?       -> NONE | SERIAL | ETH,<ip> | WIFI,<ip>
SYSTem:LOCK:FORCe <key>  -> steal control; requires the local jumper (WDOG_JMP) AND logs +107
```

Rules:

- **Any transport may READ at any time.** Queries are never gated. (This is telemetry, and denying it
  buys nothing.)
- **Only the owner may WRITE.** A write from a non-owner returns **`+105,"Interface not
  write-authorised"`** — the error code session 1 reserved for this. *Its meaning has changed*: it is
  no longer the physical-write-switch mechanism (G0-A3 deleted that), it is the ownership mechanism.
  Same code, different and honest reason.
- **Only the owner's commands kick the watchdog.**
- Ownership is released explicitly, by TCP close, or by watchdog expiry.
- **This is not a re-litigation of G0-A3.** Every transport can *become* the owner; none is
  permanently demoted. What is prevented is two hosts fighting over a kilovolt supply and a stranger's
  poller masking a dead control link.

### 7.3 The comms-loss watchdog (ARCH-36 — REQUIRED, not optional)

| Property | Value | Reasoning |
|---|---|---|
| Default period | **10 s** | `CONTROL_ARCHITECTURE.md` §5.7 |
| Settable range | 1 s … **300 s** | Above 300 s it is not a watchdog. `-222` outside the range |
| Kicked by | any **valid** command from the **owning** session, or `SYST:WATCH:KICK` | Δ12 |
| **NOT kicked by** | TCP keepalive, ARP, ICMP, a link-up state, a malformed command, a query from a non-owner | **A TCP connection can stay open with a dead application. Link state is not liveness.** State this in the manual |
| On expiry | **ramp down at `SLEW`, then `OUT_EN` low, then `ARM_EN` low.** Log `+101`. **Soft** fault | A flaky network should not require a physical visit. Never "hold last value" — that is precisely the watchdog that leaves HV on |
| `SYST:WATCH 0` | **refused with `-221` unless `WDOG_JMP` is fitted** | Disabling the watchdog on an HV instrument should require being in the room with a screwdriver |
| Hardware shadow | the heartbeat pump (§7.4) | Covers the case where the firmware timer itself is not running |

**The two-speed design is deliberate and both halves are needed.** The firmware watchdog performs a
*graceful* ramp — kinder to a capacitive load, no `dV/dt` transient into a detector. The hardware pump
performs an *ungraceful* chop in 61.5–164.5 ms. **Neither depends on the other.**

### 7.4 The heartbeat pump — recomputed (Δ6)

```
  GPIO4 ──[47 nF]──┬──[47 nF]──┬──|◄|── EN_HB_NODE ──┬── 1 MΩ ──┬── GND   ──► 74HCT14 ──► EN_HB
                   │           │                     │          │
                 10 MΩ        |◄|                  100 nF       │
                   │           │                     │          │
                  GND         GND                   GND        GND
```

- **Frequency 1 kHz**, generated by a hardware-timer ISR that toggles the pin **only if a
  main-loop-serviced counter has changed since the previous tick** (C-3: *"generate the heartbeat from
  a main-loop-serviced toggle"*). **A free-running LEDC peripheral is forbidden** — it keeps toggling
  after the CPU hangs, which is the exact failure the pump exists to catch.
- **Two 47 nF caps in series** (C-3) ⇒ `C_p = 23.5 nF`. **A single shorted coupling cap would turn
  the AC path into a DC path, letting a stuck-high GPIO hold the pump charged.** With two, one short
  leaves the coupling intact. One *open* kills the pump ⇒ HV off. Both single-fault outcomes safe.
  The 10 MΩ from the midpoint to GND stops that node drifting.
- Diodes **BAT54S** dual Schottky, `V_f ≈ 0.3 V` at these currents `[recalled]`.

**Equilibrium.** `f·C_p·(V_drive − 2V_f − V) = V/R` ⇒ `23.5 µA/V × (3.3 − 0.6 − V) = V/1 MΩ`
⇒ `23.5(2.7 − V) = V` ⇒ **`V = 2.590 V`**.
74HCT14 `V_T+` max ≈ 2.0 V at `VCC = 4.5–5.5 V` `[recalled — datasheet at Phase 6]` ⇒ **margin
0.59 V**.

**Decay when the toggle stops.** `τ = 1 MΩ × 100 nF = 100 ms`.

| To threshold | Time |
|---|---:|
| `V_T−` **max** 1.4 V (worst case, latest turn-off) | `100·ln(2.590/1.4) =` **61.5 ms** |
| `V_T−` **min** 0.5 V | `100·ln(2.590/0.5) =` **164.5 ms** |

> **⇒ HV drops between 61.5 ms and 164.5 ms after firmware stops toggling.** Session 1's §3.7 quoted a
> single **79 ms** figure computed against a 3.3 V source and a nominal 1.5 V threshold. **That number
> should not be quoted any more.** The change is a consequence of C-3's two-series-cap requirement and
> of using the HCT hysteresis *band* rather than a point. It is still comfortably shorter than the
> module's own 100 ms set-node time constant, so the hardware chop remains faster than the module
> could have ramped.

### 7.5 Network security work that G0-A3 put in scope

`CONTROL_ARCHITECTURE.md` §4.3a: *"the work that §4.3's recommendation existed to avoid is now IN
SCOPE and must be resourced."* The minimum:

- **TLS on both network transports**, device certificate in NVS, no anonymous write. The W5500 does
  not offload TLS; budget the CPU (mbedTLS on core 0, never core 1).
- **A bounded parser.** `INTERFACES.md`: *"Do not vendor the reference SCPI parser."* The reference's
  `msg_buffer[64]` overflow is reachable from the control port (`REFERENCE_BOARD_AUDIT.md` §6.3
  items 9–10, `[verified-artifact]`). Fixed-size line buffer, hard length cap, **dispatch by string
  compare and not by 32-bit hash** (audit item 12: a hash collision dispatches the wrong handler with
  no diagnostic). **Fuzz it** — this is a named deliverable, not a wish.
- **OTA is refused unless the instrument is DISARMED and the `WDOG_JMP` jumper is fitted.** Signed
  images, A/B partitions, rollback on failed self-test. An unsigned OTA path on a device that can kill
  is the remote-code-execution hazard §4.3 named and G0-A3 accepted.
- **Rate-limit and cap concurrent connections** in the W5500's socket allocation, so a connection
  flood cannot starve the owner's session.

---

## 8. Command set

Extends `CONTROL_ARCHITECTURE.md` §4.6/§4.7a and `INTERFACES.md` §3. **SCPI-like ASCII,
`\n`-terminated, case-insensitive, `?` = query, `;` separates compound commands.** Same grammar on
every transport.

### 8.1 The mandatory IEEE-488.2 / SCPI-99 surface the reference firmware lacked

`REFERENCE_BOARD_AUDIT.md` §6.3 `[verified-artifact]`: the reference registers only `*IDN?` and
`*DEBUG?`; it has **no `*RST`**, **no error queue**, **no `SYSTem:ERRor?`**, and an unknown command
produces **no response at all**, so a host cannot distinguish "not supported" from "device hung".

```
*IDN?            -> "Yale,HVCTL-BIP,<serial>,<fw-semver>+<git-short>"
*RST             -> SAFE. Aborts any ramp, OUT_EN low, ARM_EN low, both DAC codes 0, both shunt FETs on,
                    relays de-energised (bleeds engaged), soft limits RETAINED, error queue cleared.
                    Does NOT clear the OVP latch. Does NOT release SYST:LOCK.
                    MUST be safe to issue at any time, in any state, from any transport.
*CLS             -> clear status registers and the error queue. Does NOT clear a protection latch.
*OPC?            -> 1 when the pending ramp / changeover / discharge completes. The blocking form.
*OPC             -> set the OPC bit in ESR on completion (non-blocking form).
*TST?            -> 0 = pass. Self-test, refused unless disarmed: DAC and both ADCs ACK; 74LVC165
                    pattern bits read 1,0; REF5025 and both rails inside tolerance; MEAS ~ 0 on all
                    outputs; MODE_VALID asserted; direct MODE_A/B agree with the shift-register copies.
*ESR? / *ESE / *SRE / *STB?   -> standard status model. Present because SCPI-99 requires them and
                                 because a host framework will ask for them.
SYSTem:ERRor[:NEXT]?   -> <code>,"<message>";  0,"No error" when empty.  FIFO, depth 32.
SYSTem:VERSion?        -> 1999.0
```

### 8.2 Mode — read-only, always (G0-A5, MODE-12)

```
SYSTem:MODE?   -> PSEUDOBIPOLAR | UNIPOLAR | INVALID
```

> **There is no `MODE` setter, on any transport.** Not a guarded one, not an admin one, not a
> "diagnostic" one. `SYSTem:MODE?` reports the **aux poles' physical state** — the same signal the
> interlock is using. `INVALID` means the selector is between detents or an aux lead is broken, and in
> that state the hardware already has both modules off and both outputs bled.
> **Do not re-introduce a `MODE` setter "for convenience" in a later session.**

### 8.3 Setpoint — the protocol forks by mode

**Pseudo-bipolar (mode 1) — one terminal, one signed number.** This is the surface the task brief
asks for, and it is exactly right for this mode.

```
[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] <NRf>     e.g.   VOLT -350.0
[SOURce:]VOLTage?                                          commanded setpoint, signed. NOT a measurement
[SOURce:]VOLTage:SLEW <NRf>                                V/s, default 100
[SOURce:]VOLTage:POLarity?                                 POS | NEG | ZERO  (derived, read-only)
```

**Unipolar / dual-output (mode 2) — channel-addressed magnitudes.**

```
VOLTage (@A) <NRf>      output A, positive module.  Range 0 … +980. A NEGATIVE argument is an ERROR.
VOLTage (@B) <NRf>      output B, negative module.  Argument is a MAGNITUDE, 0 … 980; the terminal is
                        negative by construction.  `VOLT (@B) -350` -> -222.  NOT a courtesy.
VOLTage? (@A)           / VOLTage? (@B)
```

Four rules, each with a reason that is not stylistic:

1. **Signed scalar in mode 1, on the atomicity argument** (ARCH-21). `POL NEG` then `VOLT 350` is a
   two-write, non-atomic change whose torn state is *"negative selected, magnitude still 900 from last
   time."* A signed scalar cannot be torn. *(The "one terminal, one number" argument is dead —
   G0-A4 — and is not used.)*
2. **`VOLT (@B) -350` is an error, not a courtesy.** A protocol that accepts two spellings of the
   same thing will eventually be handed the wrong one, on a terminal whose sign the operator cannot
   see from the panel.
3. **A command addressed to a terminal that is not live in the physically-selected mode raises
   `+108`, and is not silently ignored** (MODE-12 / `CONTROL_ARCHITECTURE.md` §4.7a rule 4). In
   pseudo-bipolar, `VOLT (@B) 350` fails loudly.
4. **`VOLT` is non-blocking.** A sign change is a mechanical changeover taking seconds. The host polls
   `STAT:OPER:COND?` or blocks on `*OPC?`. **A host that assumes `VOLT` has completed on return is
   wrong — document this loudly.**

**Signed zero.** `VOLT 0` means *go to zero, staying in the current polarity.* `-0` is **not**
overloaded. `OUTPut:POLarity:PREFerence POS|NEG` covers the at-zero case.

### 8.4 Arm, output and protection

```
SYSTem:ARM ON|OFF        explicit arm/disarm (ARCH-35). OFF is accepted from any state, always, and is
                         never queued. ON is refused with -221 unless: interlock closed, MODE_VALID,
                         RAIL_OK, no latched fault, all live outputs measure |V| < V_safe, and this
                         session owns SYST:LOCK.
SYSTem:ARM?              -> ON | OFF | REFUSED,<reason>

OUTPut[:STATe] ON|OFF                 OUT_EN.  OFF always accepted, always safe.
OUTPut[:STATe]?          -> OFF | ARMED | RAMPING | REGULATING | DISCHARGE | CHANGEOVER | INTERLOCK | FAULT
OUTPut:POLarity POS|NEG               mode 1 only. REJECTED with -221 unless OUTP is OFF and
                                      |MEAS| < V_safe.  Rejected, not queued: the protocol refuses to
                                      express a transition the hardware refuses to perform.
OUTPut:PROTection:TRIPped?   -> 0 | 1,<source>     source in {HV_OVP_A, HV_OVP_B, VSET_P, VSET_N}
OUTPut:PROTection:CLEar               one edge on nOVP_CLR. Fails if a comparator is still asserting.
```

### 8.5 Soft limits — a named safety element (ARCH-37)

```
[SOURce:]VOLTage:LIMit:HIGH <NRf>     persisted in NVS with a CRC
[SOURce:]VOLTage:LIMit:LOW  <NRf>     (negative)
[SOURce:]VOLTage:LIMit:HIGH? / :LOW?
```

- Enforced on the **signed** setpoint, **before any DAC write**.
- **Violation raises `-222,"Data out of range"` and the setpoint does not change.** It is **never**
  clamped. The reference board's `constrain()`-and-say-nothing behaviour is the anti-pattern
  (`REFERENCE_BOARD_AUDIT.md` REF-05, `[verified-artifact]`): *"I asked for 900 V and got 200 V and
  nothing said so"* must be unreachable.
- **A hard ceiling of ±980 V (§5.4) sits above the soft limits and cannot be raised by any command.**
  It is enforced as a DAC code clamp *and* by the 2.500 V rail in hardware.
- **At boot, the NVS limits are CRC-checked. On failure both limits default to 0 V and the instrument
  refuses to arm until they are re-entered.** A corrupted limit that silently defaults to full scale
  is a limit that is worse than none.

### 8.6 Measurement — the deliberate naming asymmetry

```
MEASure:VOLTage[:DC]? [(@A|@B)]      SIGNED, from the INDEPENDENT monitor. THIS is "the output voltage".
MEASure:VOLTage:RAW? [(@A|@B)]       raw ADC counts + the gain/offset pair in use (calibration audit)
MEASure:VOLTage:MODule? POS|NEG      that module's own VMON, UNSIGNED. Diagnostic only, never safety.
FETCh:VOLTage? [(@A|@B)]             last reading, no re-trigger
```

A host that asks the obvious question gets the trustworthy answer. The module's own readback is
reachable **only by asking for it by name.** That is a protocol-level encoding of the brief's
invariant (c).

### 8.7 Status, interlock, watchdog, calibration

```
STATus:OPERation:CONDition?     bit0 RAMPING  bit1 SETTLING  bit2 CHANGEOVER  bit3 DISCHARGING
                                bit4 ARMED    bit5 OUT_EN
STATus:QUEStionable:CONDition?  bit0 OVERVOLT bit1 INTERLOCK bit2 MON_DISAGREE bit3 WDOG
                                bit4 MODE_INVALID  bit5 RAIL_FAULT  bit6 READBACK_PATH_FAULT
SYSTem:INTerlock?               -> OK | OPEN
SYSTem:RAILs?                   -> "<5v_mod>,<3v3>,<5v_a>,<2v5_clamp>,<2v500_ref>" volts, measured
SYSTem:WATCHdog <s> / ?         1..300; 0 refused with -221 unless WDOG_JMP fitted
SYSTem:WATCHdog:KICK
SYSTem:WATCHdog:REMaining?      seconds
SYSTem:LOCK:REQuest? / :RELease / :OWNer? / :FORCe <key>
STATus?                         one-line machine-parseable snapshot of the entire state machine
TEST:BLEED?                     commanded dump, measure tau, compare to expected -> PASS|FAIL,<tau_ms>
TEST:INTerlock?                 power-up weld / stuck-contact self-test -> PASS|FAIL,<detail>
CALibration:...                 PER-OUTPUT gain/offset (COMBINER_STUDY F-20 as amended by G0-A4:
                                in mode 2 the two polarities are two physically different chains),
                                write-protected behind WDOG_JMP
```

**Diagnostics refuse to run unless `OUTPut` is OFF.** `TEST:BLEED?` additionally requires ARM, because
it must charge a node to measure its decay.

### 8.8 The explicit polarity-changeover sequence

**Simple form, recommended for hosts:**

```
VOLT -400
*OPC?                -- blocks; returns 1 on completion
SYST:ERR?            -- MUST be checked. 0 = clean; +103 = discharge timed out; +106 = ramp timeout
MEAS:VOLT?           -- confirm against the INDEPENDENT monitor
```

**Explicit form, for scripts that want every step observable:**

```
VOLT 0                      -- ramp to zero at SLEW
*OPC?
OUTP OFF                    -- OUT_EN low; /ON high; VSET shunt FETs on
                            -- >>> hardware: SETTLE has NOT fired yet; the relay has NOT moved <<<
MEAS:VOLT?                  -- poll until |V| < V_safe (10 V). MEASURED. Not timed. Not assumed.
OUTP:POL NEG                -- -221 unless OUTP is OFF and |MEAS| < V_safe.
                            -- SEL toggles -> 74HCT86 edge detector -> 74HCT123 -> SETTLE = 0
                            -- -> ARM = 0 -> BOTH modules off and BOTH relays de-energised for
                            --    T_dwell ~ 1 s, IN HARDWARE, whatever firmware believes.
                            -- Bleed is engaged the whole time (relay NC).
*OPC?                       -- returns when SETTLE has re-asserted and the new relay has settled
OUTP ON
VOLT -400
*OPC?
SYST:ERR?
```

**The one transition that must never fall through** (ARCH-24, `CONTROL_ARCHITECTURE.md` §5.3):
`DISCHARGE → CHANGEOVER` on **discharge timeout must TRIP**, leave the switch in neutral, and tell a
human. Every other timeout may degrade toward OFF because OFF is safe. This one cannot: proceeding
means hot-switching a relay at unknown high voltage.
*Honest bound, per PART-13 / MODE-15:* at ≈0.75 mA the modules **cannot sustain an arc** (three orders
below the ~1 A a tungsten arc needs), so the physical consequence of getting it wrong is a
**current-limited fight, not an energetic fault**. **That bounds the consequence; it does not remove
the requirement**, because a welded contact leaves the output permanently connected to the wrong
module and that is not self-announcing.

### 8.9 Error codes

Standard SCPI negatives (`-100` command error, `-109` missing parameter, `-113` undefined header,
`-221` settings conflict, `-222` data out of range) plus device-specific positives:

| Code | Meaning |
|---|---|
| `+100` | Interlock open (key, lid, or mode guard) |
| `+101` | Watchdog timeout — output was ramped down and disarmed |
| `+102` | Overvoltage trip (hardware OVP latched) — `OUTP:PROT:TRIP?` names the source |
| `+103` | Changeover timeout — discharge did not complete. **Relay left in neutral** |
| `+104` | Monitor disagreement (module VMON vs the independent monitor) |
| `+105` | Interface does not hold `SYST:LOCK` (§7.2) |
| `+106` | Ramp timeout — the output did not track the setpoint |
| `+107` | ⬛ Control ownership was forcibly taken |
| `+108` | ⬛ Command addressed to a terminal that is not live in the physically-selected mode |
| `+109` | ⬛ Mode selector moved while energised — **HV was forced off immediately** (MODE-16) |
| `+110` | ⬛ Mode selector in an illegal / intermediate position (MODE-18) |
| `+111` | ⬛ Rail out of window (`RAIL_OK` de-asserted) — the message names the rail |
| `+112` | ⬛ Status-readback path fault (74LVC165 pattern bits wrong, or the redundant `MODE_A/B` copies disagree with the direct GPIOs) |

**`+109` is not a graceful transition and must never become one.** MODE-16: a mode change seen at
runtime means the specified powered-down procedure was not followed, i.e. a human is turning a switch
on a live instrument. **A graceful ramp-down would keep HV alive during exactly the contact transit
the lead-break timing is racing.**

---

## 9. Connectors

### 9.1 HV output — SHV, and why not MHV or LEMO at 1 kV

`HV_SAFETY_ENVELOPE.md` §1 settles this; the reasoning is not repeated in full, only sharpened for the
frozen 1 kV / dual-output case.

| | **SHV** | MHV | LEMO (HV series) |
|---|---|---|---|
| DC rating | 5 kV typical `[verified-web]` | up to 5 kV `[verified-web]` | to ~20 kV `[recalled]` |
| **Margin at our 980 V declared FS** | **5.1×** | 5.1× | ≫ |
| Mates into a BNC? | **No** — reversed gender + protruding insulator | **Yes, mechanically** — *this is the problem* | No |
| Live pin touchable when unmated | **No** | **Yes** | No |
| Break order on disconnect | HV breaks **before** ground | unspecified | varies |
| Shell | **grounded** | grounded | varies |
| Detector-physics default | **yes** | legacy | no |

**SHV, unconditionally.** Three reasons in order of weight, and the first is not a rating:

1. **It cannot be forced onto a BNC.** MHV shares BNC's bayonet geometry closely enough that an MHV
   plug can be pushed onto a BNC jack, putting kilovolts on a signal cable someone will later pick up.
   This is a *design-for-error* property and it is why SHV exists. **Do not use MHV.** A legacy MHV
   instrument in the lab is a reason for a clearly-labelled adapter *cable*, not for fitting MHV here.
2. **The live conductor is untouchable when unmated, and HV breaks before ground.** Both matter on a
   bench where a cable gets pulled with the supply live by someone who assumed it was off. At 980 V
   into a 0.75 mA current limit, contact is survivable and still far above the let-go threshold —
   the connector geometry is the control, not the current limit.
3. **It is what the building already speaks.** Anything else guarantees an adapter, and the adapter is
   the thing that ends up unmated and live.

**LEMO** is rejected on ecosystem and availability, not capability. It is the fallback if enclosure
volume ever becomes binding, and would need a live-distributor check.

**Two connectors, not one** (MODE-05), and three specifics for this design:

- **Grounded shells are the guard ring, for free.** iseg Table 4: *"Case is connected to GND"*
  `[verified-artifact]`, so both shells sit at chassis potential. **Shell-to-shell is 0 V, and each
  centre conductor sees 980 V to its own shell.** Panel spacing is therefore the **single-ended**
  requirement (7.5 mm class), **not** the 15.0 mm span — both `[unverified-primary]`, per NUM-01.
  (IPC-2221 does not rate panel air gaps at all; it is a PCB standard.)
- **The board-side wiring to each bulkhead DOES carry the full 2 kV differential** and stays inside
  the 15.0 mm corridor rule `[unverified-primary]` like any other HV copper. **Two separate HV leads,
  routed apart, never in one bundle and never in one sleeve.**
- **Panel-mount bulkhead, not board-mount** (`HV_SAFETY_ENVELOPE.md`): a board-mount connector puts
  the mechanical load of cable insertion into the PCB and drags the HV keep-out through the board edge.

| Function | Candidate | Note |
|---|---|---|
| SHV panel bulkhead jack ×2 | **Amphenol RF SHV series** (e.g. 000-79340-0002) `[unverified-MPN]` | grounded shell, solder cup |
| — alternative family | **Radiall SHV**, **Fairview Microwave SHV** `[unverified-MPN]` | price/lead-time hedge |
| HV lead, board → bulkhead | 20 kV-rated silicone HV wire, 22 AWG `[unverified-MPN]` | one per output, routed apart |

### 9.2 The mode selector — the honest answer to MODE-13

> # ⛔ SUPERSEDED — DO NOT PROCURE FROM THIS SECTION. Banner added 2026-07-23 (session 2 verification).
>
> **This section specifies a 2-position, 4-pole switch. The design that is actually built specifies a
> 3-position, 7-pole switch, and the two are incompatible.**
>
> `COMBINER_DESIGN.md` §3.5 (SW-R1, SW-R3) requires **3 positions — `PB · SAFE · UNI` — and ≥3 HV +
> ≥4 LV poles**; `hardware/hvctl/board_spec.py` builds **`SW1A…SW1G` = 7 poles, 3 positions**, and
> the `MODE_MID` series-HV arrangement drawn below **does not exist in the netlist**. §0.4's
> reconciliation table omits the mode selector entirely, which is how the divergence survived.
>
> **A purchaser who buys from the table below buys a part with NO SAFE detent — which deletes the
> single mechanism `COMBINER_DESIGN.md` §3.5 relies on to meet MODE-15's lead-break requirement, and
> which `COMBINER_DESIGN.md` §3.7 explicitly warns against ("Do not adopt a two-position switch").**
> Three independent skeptics flagged this; it is a **STOP-THE-LINE** item for procurement.
>
> **Governing text is `COMBINER_DESIGN.md` §3.5–§3.8 plus its own correction banner** (which itself
> refutes §3.6's part claims and downgrades the SAFE-detent timing argument). Strike or rewrite this
> section before G1 procurement. The *engineering argument* below — that two series 1 kV HV poles
> beat one 2 kV pole — is retained and is the same argument `COMBINER_DESIGN.md` §3.2 makes with the
> `M` node; only the **part specification table** is wrong.

Requirement (MODE-13/14/15/18): a **physical** element the operator moves; **1 kV working per HV
pole**; **auxiliary LV poles on the same armature**; **aux breaks before HV makes**; **non-shorting**
so an intermediate position decodes as neither mode; guarded.

**A finding first, because it changes the part class.** MODE-13 asks that we *"attempt an arrangement
in which no two poles carry opposite polarities."* One does exist, and it is better than "no two poles"
— it puts **no more than 1 kV across any single contact gap**:

```
   K2_NO ──► [HV-1] ──┬── BIP ──► MODE_MID ──► [HV-2] ──┬── BIP ──► HV_BUS_A   (pseudo-bipolar)
                      └── UNI ──► HV_BUS_B              └── UNI ──► bleed (0 V)  (unipolar)
```

- In **UNI**: `HV-1` common is at −980 V and its open BIP throw goes to `MODE_MID`, which `HV-2` has
  tied to **bleed (0 V)**. `HV-1`'s gap sees **980 V**, not 1960 V.
  `HV-2`'s common is at 0 V and its open BIP throw goes to `HV_BUS_A` at +980 V ⇒ **980 V**.
- In **BIP**: `HV-2` connects `MODE_MID` to `HV_BUS_A`; `HV-1`'s open UNI throw goes to `HV_BUS_B`,
  which is dead in this mode.

> **Two HV poles in series, each rated 1 kV, replace one pole rated 2 kV.** The naïve
> single-pole arrangement puts +980 V and −980 V across one open contact — a **1960 V** gap and a much
> harder part to buy. This is the arrangement MODE-13 asked us to look for; it exists; use it.

**Selector specification** (all `[unverified-MPN]`; **this part class is unsearched in this project**
and remains `SCOPE.md` R-14 / O-10):

| Requirement | Value |
|---|---|
| Poles | **4 total**: 2 HV (above) + 2 LV aux |
| Positions | 2, detented |
| HV pole rating | **≥ 1 kV DC working**, ≥ 2 kV standoff, at ≥ 1 mA |
| Aux poles | **NON-SHORTING** (break-before-make between detents) — this is what makes MODE-18 a decode rather than a hope |
| Aux decode | **positive for both modes**: `MODE_A` closes only in pseudo-bipolar, `MODE_B` closes only in unipolar. **Neither mode may be encoded as "the absence of the other"** (`CONTROL_ARCHITECTURE.md` §6.4 rule 10b) |
| Aux vs HV timing | aux **breaks before** HV **makes** (MODE-15) — see §9.3 for how this requirement is actually met |
| Guard | opaque cover, captive screw, with a **microswitch in the `INTLK` loop** |

Candidate classes, honestly ranked:

1. **Ceramic wafer rotary switch, 4-pole 2-position** — e.g. **Elma type 04 ceramic**, **Grayhill 71
   series ceramic** `[unverified-MPN]`. Best fit *if* a 1 kV wafer rating can be confirmed on a live
   datasheet. Its inter-deck contact timing is **not a catalogue parameter**, which is the problem
   §9.3 solves.
2. **HV link block / re-plugged HV cable** — the fallback MODE-13 explicitly blesses (*"if a link
   block or connector re-plug is better engineering, SAY SO"*). Implementable today with a third SHV
   bulkhead and a short SHV–SHV jumper. **Its cost is real and must be recorded, not absorbed:** a
   re-plugged cable has **no armature**, so the by-construction agreement between the HV routing and
   the interlock permissive — the entire reason G0-A5 is stronger than G0-A4 — **is lost**, and the
   design falls back to the guard interlock plus MODE-16's runtime trip. **If this fallback is taken,
   record it as a weakening in `DECISIONS.md`.**
3. **Vacuum / HV rotary (Ross, Kilovac)** `[unverified-MPN]` — capable, and priced like it. Only if 1
   and 2 both fail.

### 9.3 How the lead-break requirement is actually met (Δ9, closing N-8)

N-8 asks for the *margin* the aux poles need. The honest position is that **no stock rotary switch
specifies its inter-deck contact timing**, so a design that depends on that number is a design that
depends on an unobtainable spec.

> **Primary mechanism: a microswitch on the mode selector's guard cover, wired in series with the
> `INTLK` loop.**
>
> The operator cannot reach the selector without opening the guard. Opening the guard opens `INTLK`
> ⇒ `ARM = 0` ⇒ **both modules off, both relays de-energised, both bleeds engaged** — combinationally,
> in hardware, before a hand has moved. **The lead-break margin is then hundreds of milliseconds of
> hand travel**, not an unspecified few milliseconds of contact geometry.
>
> **Secondary mechanism, retained:** the switch's own aux poles are non-shorting, so any movement
> passes through `MODE_VALID = 0`. **Tertiary:** the 74HCT123 monostable holds `ARM = 0` for
> `T_dwell ≈ 1 s` on any aux edge.
>
> **This does not retire MODE-15.** MODE-15 remains a switch-selection requirement and Phase-7 bench
> item 1.6 (scope the actual contact order) remains mandatory. What it does is make MODE-15
> **satisfiable with a procurable part**, and it means that a switch which *fails* the timing test
> degrades the design by one layer instead of invalidating it.
>
> **Residual hazard, stated neither hidden nor overstated** (MODE-15, PART-13): if all of this is got
> wrong and both modules are routed onto one node while energised, the modules are short-circuit
> protected and limited to **≈0.75 mA**, so the outcome is a **current-limited polarity fight, not an
> energetic fault**, and the contacts cannot sustain an arc. **That bounds the consequence. It does
> not remove the requirement**, because a welded contact is silent and permanent.

### 9.4 LV connectors

| Function | Part class | Specifics |
|---|---|---|
| **DC input** | **2.1 × 5.5 mm locking DC jack**, e.g. **Switchcraft S-761K** `[unverified-MPN]` | Locking. Losing input power is *safe* (everything de-energises) but is a nuisance mid-sweep |
| **USB (serial control)** | **USB-C receptacle, USB 2.0**, 5.1 kΩ CC pull-downs `[unverified-MPN]` | Behind the isolator. **Shell bonded to chassis through 1 MΩ ∥ 10 nF**, not directly: keeps the RF bond, blocks a DC ground loop, preserves §4.1's isolation argument |
| **Ethernet** | **RJ45 with integrated magnetics**, e.g. **Pulse JXD0-0001NL** / **Halo HFJ11-2450E** `[unverified-MPN]` | Bob Smith termination: 4 × 75 Ω to a common node, then **1 nF / 2 kV** to chassis. Shielded jack, shell **directly** to chassis (the magnetics already provide the isolation) |
| **WiFi antenna** | **RP-SMA bulkhead + U.FL pigtail** `[unverified-MPN]` | Required by Δ8: the chassis is an earthed steel box |
| **External interlock** | **3-pin 3.5 mm pluggable screw terminal**, e.g. **Phoenix MC 1,5/3-G-3,5** `[unverified-MPN]` | Pins: `INTLK_A`, `INTLK_B`, `GND`. **Ship a fitted shorting plug** and say so on the panel. Deliberately *not* a connector that resembles anything else on the instrument |
| **HV-enable key switch** | panel keyswitch, e.g. **Lorlin / NKK CKS** `[unverified-MPN]` | **In series in the `INTLK` loop**, with the lid switch and the mode guard microswitch. This is the brief's own *"external interlock loop (door switch / key / enclosure lid)"* and it is **not** a change to G0-A3: the network keeps full write authority; the key simply gates whether HV can exist at all |
| **Programming / recovery** | 1 × 6, 0.1 in header, **internal** | `3V3 / GND / U0TXD / U0RXD / EN / IO0`, plus the native USB-Serial-JTAG on GPIO19/20 to an internal micro-USB. **Never on the panel** — it is an un-isolated ground tie, which is exactly what §4.1 forbids |

> **The control interface must never look like the HV interface** (`HV_SAFETY_ENVELOPE.md` §1). Every
> LV connector above is visually and mechanically distinct from SHV. Nobody can plug the HV lead into
> the interlock terminal or vice versa.

### 9.5 The CP2102N auto-reset circuit — a specific operational finding

The standard CP2102N/ESP32 auto-reset circuit drives `EN` and `GPIO0` from DTR/RTS. **Any host program
that opens the serial port therefore resets the ESP32.** During that reset every GPIO is hi-Z, so
`ARM_EN` is pulled down, the heartbeat stops, and **HV drops within 61.5–164.5 ms.**

That behaviour is *correct* — it is the design working — but it means **opening a terminal drops HV**,
which will look like a fault the first time it happens.

> **Fit the two-transistor auto-reset circuit, but with a removable jumper (`JP_AUTORST`), and ship the
> jumper REMOVED.** Programming is then done either by fitting the jumper or via the internal
> USB-Serial-JTAG. Document the behaviour in the manual under "why did my HV turn off when I opened a
> terminal", because the answer is "because it is supposed to".

---

## 10. Single-fault analysis

Every row is one fault, with nothing else broken. **`✓ safe` means the module ends up OFF or the fault
is bounded and announced.** Faults that are only *detectable* rather than *prevented* are marked ⚠ and
are named as such.

### 10.1 The case the task names explicitly: ESP32 in reset or unpowered while HV rails are up

| # | Fault | Hardware behaviour | Result |
|---|---|---|---|
| F-1 | **ESP32 held in reset** (BOOT button, auto-reset, brownout detector, WDT reset) | All GPIO hi-Z. `ARM_EN` pulled down by 2 × 10 kΩ **at the 74HCT30 input**. `OUT_EN` pulled down. `SEL` pulled down (POS). Heartbeat stops ⇒ pump decays in 61.5–164.5 ms ⇒ `EN_HB = 0` | **ARM = 0 by two independent terms.** Both `+VIN` load switches open, both coils de-energise, both `/ON` pulled to their own `+VIN` by the 10 kΩ pull-ups, both `VSET` shunt FETs turn on, both bleeds engage. **✓ safe** |
| F-2 | **`+3V3` rail lost entirely, `+5V_MOD` and `+12V` still up** | As F-1, plus: the 74LVC14A/74LVC165A readback buffers go hi-Z, so no 5 V logic is driven into an unpowered ESP32 pin. The 74HCT interlock is on `+5V_MOD` and is fully alive to hold `ARM = 0` | **✓ safe**, and note `RAIL_OK` does *not* monitor `+3V3` — it does not need to, because `EN_HB` and `ARM_EN` both fail safe without it |
| F-3 | **ESP32 boot ROM driving strapping pins** | GPIO0/3/45/46 carry no net (§2.2). U0TXD emits a boot log on GPIO43, which reaches only the CP2102N | **✓ safe** |
| F-4 | **Firmware crashed / hung with every GPIO stuck at its last level** | `ARM_EN` may be stuck high — but the heartbeat is a **main-loop-serviced toggle**, not a free-running peripheral (§7.4). A hung loop stops toggling. Pump decays | **✓ safe in 61.5–164.5 ms.** *This is the fault the pump exists for, and the "main-loop-serviced" requirement is what makes it work* |
| F-5 | **ESP32 alive but compromised** (the G0-A3 threat model) | It can command any legal setpoint and can arm. It **cannot** exceed 2.500 V on `VSET` (§5.3), cannot reach the mode (§8.2), cannot both-enable onto one node (§6.1), cannot hold the OVP latch cleared (§6.4), cannot defeat the key/lid/guard loop, and cannot raise the ±980 V hard ceiling | **Bounded by hardware.** *This is exactly where G0-A3 moved the safety burden, and this row is the answer to it* |

### 10.2 Broken wire, one line at a time

| # | Line | Result |
|---|---|---|
| F-6 | `HB_OUT` | pump decays ⇒ ARM = 0 ⇒ **✓ both OFF** |
| F-7 | `ARM_EN` | duplicated pull-downs at the HCT input hold it low ⇒ **✓ both OFF** |
| F-8 | `OUT_EN` | duplicated pull-downs ⇒ `/ON` stays HIGH ⇒ **✓ both OFF** (modules may remain powered — that is ARMED, and it is a defined state) |
| F-9 | `SEL` | pull-downs default to POS. `ARM` independently required; the break itself is an edge, which fires `SETTLE` ⇒ **✓ safe** |
| F-10 | `/ON_P` or `/ON_N` (the net itself) | the 10 kΩ pull-up **at the module end**, within 5 mm of pin 4, holds it HIGH ⇒ **✓ that module OFF.** *This is why ARCH-17 places the pull-up at the module, not at the gate* |
| F-11 | a `MODE_A` or `MODE_B` aux lead | duplicated pull-downs ⇒ that aux reads 0 ⇒ `MODE_VALID = 0` ⇒ **✓ ARM = 0, both outputs bled.** Firmware reports `INVALID` and `+110` |
| F-12 | `INTLK` loop | opens ⇒ `ARM = 0` **with no firmware involvement** ⇒ **✓ both OFF** |
| F-13 | `VSET_P` / `VSET_N` track open | **module commands FULL SCALE** via its internal 10 kΩ pull-up. Mitigated by the **2 × 1 kΩ pull-downs at the module pin** (4.8 % of Vnom = 48 V; **9.2 % = 92 V if one of the pair is also open**) and by the `/ON`-driven shunt FET. ⚠ **Detectable but not prevented if the break is between the pull-downs and the pin.** *This is the single worst break on the board and it is the reason ARCH-05 puts the pull-downs at the pin and ARCH-18 duplicates them.* ⚠ **Numeric discrepancy flagged, not resolved:** `HV_SAFETY_ENVELOPE.md` §2 and `NUMBERS_PROBE.md` §5.1 both print **9.2 %** for the one-pull-down-open case, but the plain divider `1000/(1000+10000) = 9.09 %` gives **9.09 % (91 V)**. The repo's published figure is quoted above; **the 0.11-point gap is unexplained and someone should find out which formula the probe used before either number is relied on.** Both are safe; neither is worth guessing about |
| F-14 | relay coil drive | duplicated gate pull-downs ⇒ coil de-energised ⇒ **✓ neutral ⇒ bleed engaged** |
| F-15 | `+VIN` load-switch `EN` | duplicated pull-downs ⇒ switch open ⇒ **✓ that module unpowered** |
| F-16 | `nOVP_CLR` | latch cannot be cleared ⇒ instrument will not arm ⇒ **✓ fail-safe direction** |
| F-17 | I²C `SDA` or `SCL` | both ADS1115 unreachable ⇒ the **independent monitor is lost** ⇒ hard fault ⇒ firmware **stops the heartbeat**, which drops HV in hardware (ARCH-20) ⇒ **✓ safe** |
| F-18 | shift-register `MISO` or `nLOAD` | status word reads all-zero ⇒ pattern bits `14,15` fail ⇒ `+112` ⇒ hard fault ⇒ heartbeat stops ⇒ **✓ safe** |

### 10.3 Shorted nets and component failures

| # | Fault | Result |
|---|---|---|
| F-19 | **`VSET` shorted to `+3V3`** downstream of the buffer | ≈**1320 V** commanded. The 2.500 V rail **cannot** stop this (§5.5 admits it). Caught by the **`VSET` over-range comparator at 2.625 V** ⇒ OVP latch ⇒ `ARM = 0` in hardware, and by the HV window comparator at 105 %. ⚠ **Detected and tripped, not prevented.** *Layout must keep the 3.3 V domain physically away from `VSET`* |
| F-20 | **DAC output-stage fault to its 3.3 V VDD** | the buffer's rail-to-rail output stage cannot exceed `+2V5_CLAMP` ⇒ **✓ structurally blocked.** *This is the entire reason the buffer is mandatory (Δ2)* |
| F-21 | **One LM4040 open** | the other holds `+2V5_CLAMP` ⇒ **✓ safe.** Un-duplicated, this would raise the rail to `+5V_A` ⇒ 2000 V |
| F-22 | **One LM4040 shorted** | rail collapses to ~0 V ⇒ `VSET` = 0 ⇒ **✓ output off.** `RAIL_OK` UV trip at 2.40 V announces it as `+111` |
| F-23 | **REF5025 fails to its input rail (5 V)** | DAC full scale rises, **but the buffer still clamps at 2.500 V** ⇒ **✓ bounded.** The monitor's 402 kΩ offset leg also moves, which the HV window comparators see ⇒ trip. *This is why the OVP thresholds are referenced to `+2V5_CLAMP`, not to REF5025 (§6.4)* |
| F-24 | **U10 or U11 buck pass FET shorted** ⇒ 12 V on a 4.5–5.5 V module rail | **`RAIL_OK` OV trip at 5.38 V ⇒ `ARM = 0` ⇒ both `+VIN` load switches open within the supervisor's ~20 µs** ⇒ **✓ modules disconnected.** ⚠ The 12 V still reaches the load switches' inputs and the 74HCT logic (abs max 7 V) — **the logic may be destroyed, but it fails with `/ON` released to its pull-ups, i.e. HIGH, i.e. OFF**, and the modules are already disconnected. *Δ5's `RAIL_OK` term exists for this row* |
| F-25 | **`+VIN` load switch fails short** | that module is permanently powered. `/ON` is an **independent** disable through a different physical path ⇒ **✓ that module still OFF.** ⚠ Latent — detectable only by `*TST?` reading `nON_x_RB` and the module's VMON |
| F-26 | **Relay contact welded** | ⚠ **Detection only** — `SCOPE.md` Q6 was never answered and this design proceeds on detection plus a mandatory power-up self-test (`TEST:INTerlock?`). **The aux contact reads the armature, not the contact**, so a weld that also holds the armature is visible and a weld on a moved armature is not. **State this limit; do not claim prevention** |
| F-27 | **W5500 babbling / stuck `nCS`** | the DAC is on a **separate SPI host** (Δ10) ⇒ **✓ setpoint writes cannot be corrupted.** Network dies ⇒ watchdog ⇒ ramp down + disarm |
| F-28 | **Network flood / TLS CPU exhaustion** | comms is pinned to core 0, the supervisor and the heartbeat to core 1 ⇒ **✓ the trip path is not starved.** If the whole SoC stalls, the heartbeat stops ⇒ HV off |
| F-29 | **Fuse F1 opens** | every rail down ⇒ relays de-energise ⇒ **✓ bleeds engaged, both `/ON` released** (their pull-ups are to `+VIN`, which is also gone — the modules are simply unpowered) |
| F-30 | **Reverse-polarity FET Q1 fails short** | normal operation unaffected; reverse protection silently gone. ⚠ **Latent.** Only a production test finds it |
| F-31 | **A mode aux pole shorted to the other** | both read 1 ⇒ `MODE_VALID = MODE_A ⊕ MODE_B = 0` ⇒ **✓ ARM = 0.** *This is why the decode is XOR and not "B means unipolar, otherwise bipolar"* |
| F-32 | **Mode selector moved while energised** | guard microswitch opens `INTLK` first (§9.3) ⇒ hardware `ARM = 0`; then non-shorting aux poles give `MODE_VALID = 0`; then the monostable holds it. Firmware sees the change and logs `+109`. **✓ three layers, the first of which is mechanical** |
| F-33 | **Both ADS1115 report plausible but wrong values** (shared I²C, shared rail) | ⚠ **Not covered by redundancy** — the two ADCs are not independent of each other. It *is* covered by the **monitor disagreement check** against each module's own VMON, threshold 2 %·Vnom = 20 V (`CONTROL_ARCHITECTURE.md` §5.6). Legitimate quadrature disagreement is 10.03 V, so the trip has only **2×** margin — **do not treat a 12 V spread as nothing** |
| F-34 | **Guard microswitch defeated (taped closed)** | ⚠ Procedural, not preventable. The aux poles and the monostable remain. Recorded because pretending otherwise would be dishonest |

---

## 11. Panel, indication and UX

`DECISIONS.md` NUM-23 (eight enclosure requirements), MODE-09, and G0-A4 consequence 6: **which
terminal is live differs between modes, and a wrong assumption at 1 kV is a shock hazard, not a
usability complaint.**

### 11.1 Indicators — and why two of them are not on a GPIO (Δ11)

| Indicator | Driven from | Why |
|---|---|---|
| **`HV PRESENT` (red, one per output)** | **hardware**: a neon or a high-value-resistor-fed LED across **each output node**, inside the chassis and visible through a window (`HV_SAFETY_ENVELOPE.md` §2 item 6) | **It must not depend on firmware being alive.** It is the only pre-touch indication that survives a crashed MCU |
| **`ARMED` (amber)** | **hardware**: buffered from the `ARM` node of U21 | An "armed" lamp driven by a GPIO tells you what firmware *believes*. This one tells you what the interlock *is doing* |
| **`FAULT` (red)** | **hardware**: buffered from the OVP latch `Q` | Same argument. A latched protection trip must be visible even if the MCU is the thing that failed |
| **`NET` (green/blue)** | GPIO1 | Firmware/network status only. Cosmetic. It may lie without consequence |

> **A firmware-driven "HV ON" lamp lies in exactly the fault where you need it.** All three
> safety-relevant lamps are driven from hardware nodes. This costs three transistors.

### 11.2 Mode indication

**The switch's own position is the indication and it cannot lie** (MODE-09 as satisfied by G0-A5 —
there is no commanded bit for an indicator to be driven from wrongly). Add:

- An **engraved legend at the selector**, under the guard:
  `MODE: [PSEUDO-BIPOLAR — OUT_A ONLY] / [UNIPOLAR — OUT_A = +, OUT_B = −]`
  and `CHANGE ONLY WITH POWER OFF AND CABLES REMOVED`.
- An **engraved legend at `OUT_B`**:
  `LIVE IN UNIPOLAR MODE ONLY — DEAD IN PSEUDO-BIPOLAR MODE. VERIFY WITH A METER.`
- **Two LEDs echoing the aux poles** — driven from the **aux contacts themselves** through the 5 V
  domain, **never from firmware state** (MODE-14). Both lit or both dark ⇒ the selector is between
  detents, which is also exactly the state in which the hardware has both modules off.
- Rear panel: `12 V / 2.0 A` and an earth-bond symbol (§3.2, §4.2 — note this **supersedes**
  `HV_SAFETY_ENVELOPE.md` §3's `5 V / 1.8 A` rear-panel legend, which was written against the
  probe's 5 V-input architecture; Δ1).

### 11.3 The guard

Opaque, captive-screw, covering **only** the mode selector, with a microswitch in the `INTLK` loop
(§9.3). It is simultaneously the enforcement of MODE-17's *"powered-down, cables-off"* procedure and
the primary lead-break mechanism. **One part, two jobs, both of them safety.**

---

## 12. What is open, what must be verified, and what to measure

### 12.1 Executable checks this design owes the netlist checker

To be added to `hardware/hvctl/check_netlist.py` as domain safety assertions
(`INTERFACES.md` §1.3 pattern — a property a reviewer would check by eye becomes a build failure):

| ID | Assertion |
|---|---|
| SA-14 | **No net is attached to ESP32 GPIO0, GPIO3, GPIO45 or GPIO46** other than the BOOT button, the auto-reset jumper, and pull-downs. Strapping list is `[web-verified]` (§2.2) |
| SA-15 | No net that touches `VSET_*` touches `+3V3` **or `+3V3_A`** (extends `CONTROL_ARCHITECTURE.md` rule 8 to the DAC's actual rail) |
| SA-16 | `ARM_EN`, `OUT_EN`, `SEL` each have **≥ 2 pull-downs**, and those pull-downs' other terminal is at the **74HCT input**, not at the ESP32 pin |
| SA-17 | `+2V5_CLAMP` has **≥ 2 shunt reference devices** and exactly one series feed resistor |
| SA-18 | `MODE_A` and `MODE_B` are **two independent nets** originating at the mode switch's aux-pole pins; **no MCU pin drives either**, directly or through any bidirectional element (§6.4 rule 9/10b) |
| SA-19 | The DAC's SPI host and the W5500's SPI host share **no** net (Δ10) |
| SA-20 | Every ESP32 module footprint used is a **`-1U` variant with a U.FL net**, and the PSRAM variant field is **quad** (so GPIO33–37 are legal) |
| SA-21 | `nOVP_CLR` reaches the latch **only through a series capacitor** (no DC path) |

### 12.2 MEASURABLE-NOW — additions to the register (the modules are in hand, G0-A2)

| ID | Quantity | What it sets here | If it comes back pessimistic |
|---|---|---|---|
| **M-7** ⬛ NEW | **Module `+VIN` inrush and turn-on surge** | U10's transient response; TPS22918 `CT` | Raise `CT` to 5 ms, add 100 µF local bulk, stagger the two ARM-time load switches by 20 ms in firmware. **No topology change** |
| **M-8** ⬛ NEW | **Actual `Iin` at Vout = 0 / Vnom no-load / Vnom loaded** | the entire 5 V budget (§3.2 uses iseg *maxima*) | Nothing — the design is sized on maxima. **A favourable measurement must NOT be used to size the supply down**, because the maxima are what the datasheet guarantees |
| **M-4** (existing) | **Turn-on time from `+VIN`** | how long ARM must wait before asserting `OUT_EN` (§6.5 step 6) | The changeover dwell (1 s hardware / 2 s firmware) and the guard's hundreds of ms already exceed any plausible value ⇒ **the design is insensitive**. Only the arming *latency* changes |
| **M-3** (existing) | **VSET step response** | ramp step rate (currently ≥300 ms from the 100 ms internal pole) | Slow the ramp step; `|MEAS − target|` health checking still works |
| **M-1 / M-2** (existing) | **Output capacitance / internal bleeder** | bleed sizing, `T_dwell`, the S5 timeout | Not in this document's scope; both are **unpowered** measurements and should be done first |

### 12.3 Open questions this document does NOT close

| # | Question | Why it stays open |
|---|---|---|
| **O-A** | **Is a 4-pole, 2-position, 1 kV-rated switch with non-shorting aux poles procurable?** | §9.2 gives the requirement, the series-pole arrangement that reduces it from 2 kV to 1 kV, and three candidate classes. **Nobody in this project has searched this part class.** `SCOPE.md` R-14, `G0_QUESTIONS.md` O-10. **If the answer is no, the link-block fallback is legitimate engineering — and its cost (loss of the same-armature guarantee) must be RECORDED, not absorbed** |
| **O-B** | **`RAIL_OK` on `+3V3`?** | Deliberately omitted: `EN_HB` and `ARM_EN` both fail safe without it (F-2), and adding it would put an ARM term on a rail the interlock does not need. **Argue it at G1 if you disagree — but argue it** |
| **O-C** | **Does `OPA2320` make 30 mV of output swing at 4.9 mA on a 2.5 V rail?** | The ±980 V declaration depends on it (§5.4). Phase-6 datasheet read; fallbacks are stated and none of them is a topology change |
| **O-D** | **The clearance constants** | Every clearance figure quoted here — 7.5 mm single-ended, 15.0 mm pairwise, panel spacing — is **`[unverified-primary]`** and inherits NUM-01. A human must read a primary copy of IPC-2221B Table 6-1 and IEC 60664-1/62368-1 **before layout**, because `NUMBERS_PROBE.md` §1.6 shows the two candidate readings put the board on **different fab tiers** |
| **O-E** | **How is the firmware state machine replicated for two outputs?** | `CONTROL_ARCHITECTURE.md` §5.1 Gap 2 / N-4. §8's command surface is written to accommodate either answer (channel-addressed setpoints work with per-output machines or with vectorised states). **Do not let this be decided implicitly by whoever writes the firmware first** |
| **O-F** | **The exact output-node bleed arrangement (K3/K4)** | §3.4 budgets for it and states the finding that kills the naïve arrangement. Deciding it is `COMBINER_STUDY.md`'s job at G1 |
| **O-G** | **Welded-contact prevention vs detection** | `SCOPE.md` Q6 unanswered. This design proceeds on **detection**. If prevention is ever required, the combiner study reopens (TOPO-10) |
| **O-H** ⬛ NEW | **The `VSET` one-pull-down-open figure: 9.2 % (repo) or 9.09 % (plain divider)?** | Both `HV_SAFETY_ENVELOPE.md` §2 and `NUMBERS_PROBE.md` §5.1 print 9.2 %; `1000/(1000+10000)` gives 9.09 %. **Small, safe either way, and unexplained — which is exactly the kind of thing that should not be silently rounded away.** Read the probe's formula |

### 12.5 Reproducing the numbers

```
"C:/Program Files/KiCad/10.0/bin/python.exe" "docs/studies/controller_power_numbers.py"
```

Zero-argument, deterministic, stdlib-only (runs on any Python 3 — it does **not** import `pcbnew`).
It recomputes §3, §5, §6.2, §6.3, §7.4 and the §2.3 GPIO map from first principles.

**The check is deliberately two-sided.** Every expected string is **assembled from the script's own
computed values** and then searched for in this document. Change a component value in the script and
the assembled string stops matching the prose; change a number in the prose and the prose stops
matching the assembled string. Either way, exit 1. The acceptance source of truth is independent of
the computation: the prose was typed by a human, the arithmetic is done by the script.

| | |
|---|---|
| Assertions | **43, all pass, exit 0** `[verified-run]` |
| Determinism | **byte-identical across two independent invocations** `[verified-run]` |
| Mutation test | **22/22 caught with exit 1**, spanning 7 document edits, 7 component-value edits, and 8 mutations aimed at the safety assertions (a signal moved onto a strapping pin, a rail window pushed outside the module's `Vin` range, a code clamp that eats the buffer headroom, a firmware dwell shorter than the hardware backstop, an ESP32 current that blows the enclosure thermal band) `[verified-run]` |

**One assertion is deliberately not a pass/fail on the number.** The enclosure-ventilation check
asks *"if the dissipation is outside `HV_SAFETY_ENVELOPE.md`'s 4.2–6.4 W band, does this document
**say so**?"* — because after §0.4.2's coil correction it **is** outside, by 0.74 W. An exceedance
that is reported is a finding; an exceedance that is silent is a defect. The script enforces the
difference.

> **It has already earned its keep five times, and two of those are worth naming.** It caught
> (i) the **GPIO count** in §2.3, which said 23 and is 25; (ii) the 5 V buck's 12 V input current,
> which said 207 mA and is **206 mA**; (iii) a shunt-current line that said `2.03 mA` and is
> **2.02 mA**; (iv) **a defect in the check itself**; and (v) it **re-derived the entire power budget
> in one edit** when `COMBINER_DESIGN.md`'s real relay moved the coil rail from 80 mA to 286 mA
> (§0.4.2) — including surfacing that the result now **exceeds the enclosure's ventilation band**,
> which nobody would have noticed by hand.
>
> The first version of `check()` took a computed value and a hand-typed document string, and only
> ever grepped for the string — **the computed value was never used.** Mutation testing showed a
> changed script constant produced no failure at all. **That version was worthless as an acceptance
> check while passing 42 assertions and printing the right numbers**, which is exactly the failure
> mode `STATUS.md` §1.2 documents for the clearance study's "algebraic tautology". The docstring in
> the script records the mistake so it is not repeated. **A check that has not been mutation-tested
> has not been shown to check anything.**

**What it cannot see:** it is arithmetic over datasheet values. It verifies no circuit, simulates
nothing, and checks no part number. See §12.4.

### 12.4 What the instruments in this document cannot see

Per `CLAUDE.md` rule 4, stated plainly:

- **Every number here is arithmetic over datasheet values or over prior documents' arithmetic.**
  Nothing has been simulated, built, powered, or measured. There is no SPICE deck. Exit code 0 does
  not exist for this file.
- **Two facts are `[web-verified]` this session** — the ESP32-S3 strapping-pin set and the octal-PSRAM
  GPIO33–37 restriction, both from Espressif's own hardware-design guidelines. **Everything else about
  the ESP32-S3 in §1 is `[recalled]`**, including the EMAC-absence claim, which rests on *absence of
  mention* rather than on a positive denial. §1.3 was written so that the decision does not depend on it.
- **No MPN has been checked against a live distributor page.** Prior sessions found a distributor
  deep-link returning a confident, complete spec report for **an entirely different product**; a
  recalled MPN that does not exist from the named manufacturer; and a best-documented candidate
  stamped *Not For New Designs*. Treat every table row above as a *specification requirement with a
  plausible part attached*, not as a BOM.
- **Regulator efficiencies (0.90 / 0.88), the W5500's link current, the 74HCT123 pulse-width formula,
  the 74HCT14 threshold band, the LM4040 minimum operating current, and the OPA2320 output-swing
  curve are all `[recalled]`.** Six numbers, each of which changes a margin in this document, none of
  which has been read from a datasheet in this session. They are the highest-value Phase-6 reads.
- **The thermal analysis is a single number (7.14 W) and the observation that it does NOT fit the
  enclosure's existing 4.2–6.4 W band.** There is no airflow model, no junction-temperature
  calculation beyond the LDO's, and no measurement. The 12 % exceedance is reported (§3.2) rather
  than resolved, because resolving it belongs to whoever owns the enclosure.
