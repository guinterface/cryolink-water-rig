# Water rig test procedures, tied to our sims (2026-11-05)

Labels: MEASURED = from a file or source named; ESTIMATE = our choice; UNVERIFIED = not confirmed.
Pass limits come from prototype/cad/CHECKS.md "Bench acceptance" (proposed class tests, not achieved results).
Sim sources: sims/mechanics/capture_results.json (MuJoCo capture), simpage/sims/replay.json (ROS 2 nominal + 18 tests), <scratch>/fsw_build/replay/*_replay.json (fault replays).
Wiring and bridge: prototype/WIRING_BRIDGE.md.

## Before any test
- Rig inside its spill tray; tray must hold the full 500 mL source (CHECKS.md). Electronics behind the splash wall.
- Log every run: date, run id, offsets, firmware version, pass or fail, notes. One CSV per run from `rig_bridge` (ESTIMATE).
- Video every run from one fixed side view (ESTIMATE; needed for the data package).

## T0 Prime the source siphon (only if the team keeps the FIX7 over-rim siphon; 11-07)
- Why: FIX7 changed the source to an over-rim siphon (prototype/cad/README.md "FIX7"). Filling the reservoir alone does not prime it (Codex FIX7 note).
- Do: manual clamp closed. Fill the reservoir. At the clamp side, draw water through the source line with a syringe until no bubbles remain. Then close the clamp before removing the syringe (ESTIMATE method).
- Check: the pickup has a side opening or standoff so it cannot seal on the bottle floor (FIX7 BOM row; part UNVERIFIED).
- Check: the bottle is restrained at the rim, so the tube cannot pull it off the cradle (FIX7 BOM row "rim restraint").
- Re-prime: after any run where the level drops below the pickup, or bubbles show in the line. Log it in the run CSV.
- Pass: with the clamp opened for 10 s into the receiver, flow is continuous and the line shows no air gap (ESTIMATE).
- If the team goes back to the bottom bulkhead outlet 5058K116, skip T0.

## T1 Dry mate with offsets (no water)
- Setup: offset shims 0, +5 mm, -5 mm, and the 1 degree tilt shim (CAD parts offset_shim_*, tilt_shim_1deg).
- Do: 5 autonomous mates per condition; rotate the shim fixture 90 degrees for the other axis.
- Pass: at least 90% capture per condition (CHECKS.md); seat and latch switches both true; no hand help.
- Sim tie: MuJoCo captured 60 of 60 cases up to 7 mm lateral and 1 degree tilt (MEASURED, capture_results.json). Report rig rate vs sim rate per condition. The sim used k_lat 500 and mu 0.2 (MEASURED in file); rig compliance is the grommets, not measured (UNVERIFIED).

## T2 Interlocks (no water)
- Do: block one hook, then the other; command "latch closed"; then command feed open.
- Pass: latch switch stays false with either hook blocked; MCU rejects every feed-open and reports INTERLOCK (CHECKS.md, WIRING_BRIDGE.md).
- Sim tie: FSW test fault_latch passed (MEASURED, replay.json tests). Same expected outcome.

## T3 Poppet hold, disconnected (water)
- Do: fill each half to the 1 m head; wait to settle; collect drips 10 min.
- Head note (11-07): the rig reservoir surface is at most 600 mm above the base (CAD README FIX2/FIX7), not 1 m. A 1 m head needs a temporary raised column, or run T3 at 0.6 m and say so (ESTIMATE). CHECKS.md "Poppets and 1m head" is a design note, not a rig setting.
- Also: pull each wet barb joint by hand (~10 N, ESTIMATE) with water at head; no weep at any barb. The 5121K321 barb is rated for firm 75A-80A tube, not soft silicone (McMaster spec, 11-05).
- Pass: 1 mL/min or less per half (CHECKS.md).
- Sim tie: none (seal leakage is not simulated). Say so.

## T4 Mated leak check (water + MPRLS)
- Step 0: clamp closed, no leak, log MPRLS 60 s; drift = noise floor (MPRLS resolution ~10.5 Pa, TEB ±2.6 kPa, Honeywell datasheet).
- Do: mate, open feed with drain closed, close feed, record pressure 60 s.
- Pass: mated leakage 1 mL/min or less (CHECKS.md). Pressure decay limit = 3x the step-0 floor (ESTIMATE).
- Fault version: loosen one barb a quarter turn; the FSW leak check must fail and stop before conditioning.
- Sim tie: nominal replay LEAK_CHECK PRESSURIZE to AWAIT_GO took 133 s (54.1 to 187.1 s, MEASURED, replay.json steps). fault_leak_check replay ends without transfer (test passed, MEASURED). Compare mode sequence, not pressure values.

## T5 Conditioning step (chilled water)
- Before: put both DS18B20 probes in stirred ice water for 2 min. Each should read 0 ± 0.5 °C (datasheet accuracy, MEASURED). Record the offsets and subtract them in the log (ESTIMATE procedure).
- Do: source at ice-water temperature; open feed and drain; FSW holds until wall below 15 C for 5 s (CHECKS.md); receiver mass must not rise.
- Pass: gate trips on the wall probe, not on time; zero receiver gain while drain is open (CHECKS.md, needed for the two-valve scheme).
- Sim tie: nominal LINE_CHILLDOWN FLOW ran 506 s (197.1 to 703.1 s, MEASURED replay.json) on LOX. Compare shape only: wall temperature falls, the gate fires, then fill starts. Not the same physics (CHECKS.md).
- Prediction for this rig (prototype/sims/t5_conditioning.py, lumped model, COMPUTED from CAD volumes + labelled ASSUMPTIONS; t5_conditioning.json):
  - Flow on the conditioning path 0.95 / 1.52 / 2.76 mL/s (low / base / high; head 0.4 / 0.6 / 1.0 m, 4-8 barbs of 1.7 mm). The 1.7 mm barbs and 1.27 m of 2.5 mm tube set the flow, not the coupling.
  - Gate (probe < 15 C) + 5 s hold reached at 135 / 94 / 64 s from 22 C with 2 C source water.
  - Water used before fill: 129 / 143 / 176 mL of the 500 mL source.
  - About 305 g of wetted aluminium in the coupling (inserts, caps, faces) stays near 17-20 C, so it warms the water before the spool.
- Pass add-on: gate time within 30-200 s and water used below 250 mL (ESTIMATE band around the model). Log Q from the load cell on the waste side once, so the model can be corrected (ESTIMATE).
- Assumptions to replace with measurements: probe lag 8-40 s in the clamp, 2 W/K spool-clamp contact (thermal paste), barb bore 1.7 mm, coupling internal h.

## T6 Full autonomous cycle
- Do: operator "start, go" once; rig runs LATCHING, MATED, LEAK_CHECK, LINE_CHILLDOWN, FILL to 50 mL, DRAIN_AND_PURGE, DEMATE.
- Pass: completes with no hand help; fill within the target (tolerance ESTIMATE, set after T6 run 1); demate spill 5 mL or less (CHECKS.md).
- Sim tie: plot rig mode timeline against the nominal replay step list (MEASURED steps in replay.json). Fill estimate vs load-cell truth, like the sim's fill_flow vs truth at inlet cut (0.950 vs 0.950, MEASURED replay.json nominal notes).

## T7 Heartbeat loss
- Do: during FILL, stop the serial data while the ESP32 stays powered: kill the rig_bridge process (by PID), or power the ESP32 from its own supply and pull only the USB data link.
- Do NOT test by pulling a USB cable that also powers the ESP32: that removes MCU power, the watchdog cannot act, and geared servos may hold the feed open (CHECKS.md; Codex firmware note 11-05). For that case the manual reservoir clamp is the safe state; drill it as T7b.
- Pass: feed closed and drain open within 2 s (CHECKS.md); MCU reports safe.
- T7b, MCU power loss: cut ESP32 power during FILL; operator closes the manual clamp; time it. No autonomous safe state is claimed for this case.
- Sim tie: crash_sequencer: watchdog at +1.70 s, inlets closed at +1.70 s (MEASURED replay.json tests). Report rig time next to 1.70 s.

## T8 Endurance
- Do: 20 full cycles (T6).
- Water: each cycle uses ~180-230 mL (conditioning 129-176 mL + 50 mL fill, COMPUTED from T5 model). Refill the 500 mL source every 2 cycles with ice water; plan ~4-5 L of ice water and ~10 refills for 20 cycles (ESTIMATE). Empty the waste container before it reaches its limit.
- Pass: at least 18 complete (CHECKS.md); inspect pinch tubes after 20 cycles (CHECKS.md).
- Sim tie: none; report failures by mode.

## Data package outputs (ESTIMATE)
- Table: each test, runs, pass rate, limit, sim value.
- Plots: rig vs replay mode timeline; wall temperature with gate time; fill estimate vs load cell; T7 timing.
- Limits section: water not LOX; no two-phase flow; poppets opened mechanically; no microgravity.
