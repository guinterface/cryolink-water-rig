# CryoLink AA 261 water-rig firmware

Arduino safety MCU, serial MCU emulator, ROS 2 Jazzy bridge, and a water adaptation
of the existing flight graph. All project changes are in this directory. `fsw/`
is read-only to this package. There is no `/clock` publisher; every node uses wall
time and `use_sim_time:=false`.

**Bench software; hardware operation has not been verified.** The sketch deliberately
ships with `RIG_CALIBRATED=false`: feed stays closed, drain is commanded open, and
`fault=CALIBRATION`. Complete dry calibration before changing that constant.
Geared servos do not establish a passive safe state when power disappears. Keep
the manual reservoir clamp within reach.

ASSUMPTION: heartbeat-loss acceptance requires the ESP32 and PCA logic to remain
powered. With the specified USB-only MCU supply, unplugging the USB cable also
removes MCU power, so it cannot execute its watchdog. Test serial-data loss with
logic power retained; test total power loss separately with the manual clamp.
The process-kill test here models data loss with power retained, not a physical
USB-power-loss qualification.

## Wiring and calibration

Follow `../WIRING_BRIDGE.md`, `../TEST_PROCEDURES.md` and `../cad/CHECKS.md` for the
mechanics, spill tray, preload and test limits. Resolve the contradictory final
CHECKS pull-down wording in favor of the explicit wiring requested here:

| Signal | ESP32 GPIO / PCA channel |
|---|---|
| Seat / latch / home NO | 27 / 33 / 14, `INPUT_PULLUP`; COM to ground |
| DS18B20 bus | 32, external 4.7 kΩ to 3.3 V; powered three-wire probes |
| HX711 DOUT / SCK | 21 / 25, 3.3 V compatible logic |
| SDA / SCL pads | 23 / 22, explicit `Wire.begin(23,22)` |
| PCA9685 / MPRLS | I2C 0x40 / 0x18, 3.3 V logic |
| Carriage / latch / feed / drain servo | PCA channels 0 / 1 / 2 / 3 |

SDA/SCL 23/22 are confirmed by the [Adafruit HUZZAH32 pinout](https://raw.githubusercontent.com/adafruit/Adafruit-HUZZAH32-ESP32-Feather-PCB/master/Adafruit%20HUZZAH32%20ESP32%20Feather%20Pinout.pdf).
Do not use generic ESP32 SDA=21: that would conflict with HX711.
Servo V+ comes from a separate, current-limited 5 V supply; common ground with USB
and logic. Measure actual servo stall current before selecting the supply limit.
Keep the MPRLS dry, via the air-filled pressure tee above the manifold. It reports
absolute pressure; set the bridge ambient offset with the line open to atmosphere.
An unplugged NO switch reads false. A short to ground cannot be detected with this
single-wire input arrangement; false also cannot distinguish released contact from
a broken wire. Retraction clearance still requires the mechanical/switch checks. Raw switch opening removes feed immediately; no
assertion debounce is assumed.

All actuator endpoint, PWM, load-cell, and ROM constants are in
[`Calibration.h`](esp32/cryolink_mcu/Calibration.h), marked `CALIBRATE`.

1. Clamp the source and disconnect servo horns/cords for initial electrical checks.
   Confirm 3.3 V logic, common ground, PCA address, and every switch's NO polarity.
   Unplug each switch; prove false. Block each hook separately and prove latch false.
2. Read and record each DS18B20's ROM with DallasTemperature's address example.
   Set `WALL_ROM` and `INLET_ROM`; clamp the wall probe to the metal spool. Compare
   both with an independent thermometer. Enumeration order is never used.
3. Measure receiver tare counts and counts per gram using known weights in both
   directions. Set signed `HX_COUNTS_PER_GRAM` and `HX_ZERO_COUNTS`. Tare includes
   the empty vessel, not water. Firmware never auto-tares on reboot.
4. Dry fit horns and positive stops. Set safe PWM endpoints, then carriage mated/home
   angles and latch open/closed angles. ASSUMPTION: crank travel follows
   `x=18*(1-cos(theta))` mm; endpoint phasing must be measured. Hold carriage preload
   during latch motion; retraction waits for latch switch false. Never use sustained
   stall as the stop. Verify switch trip/release/overtravel in both directions.
5. Set pinch endpoints to close the lumen without cutting the tube. Prove closure
   and zero receiver gain with drain open at maximum permitted source head. Pinch
   states are **commanded PWM states**, with no independent position sensors.
6. Set `RIG_CALIBRATED=true`, compile and flash with the source clamped. Verify
   watchdog isolation with water only after dry motion checks. Measure physical
   closure time separately; software status does not prove a sealed tube. The
   200 ms mismatch check is intentionally active during motion, so slow or badly
   phased actuators will flag STUCK and require mechanical investigation.
7. Set `ambient_kpa` from a settled atmospheric reading. Establish leak decay
   allowance using a known-good assembly and independent collected leakage; the
   shipped pressure limit is provisional. Check installed probe lag and a 50 mL
   fill against an independent scale before autonomous wet tests.

## Build and flash

Tool downloads and build products use `<scratch>/cryolink_arduino`.
No sudo is required. `scripts/build_firmware.sh` installs the pinned core/libraries
and compiles for `esp32:esp32:featheresp32` (original Adafruit HUZZAH32, product 3405).
Bootstrap Arduino CLI if it is absent:

```bash
mkdir -p <scratch>/cryolink_arduino/bin
curl -fL https://downloads.arduino.cc/arduino-cli/arduino-cli_1.3.1_Linux_64bit.tar.gz \
  -o <scratch>/cryolink_arduino/cli.tar.gz
tar -xzf <scratch>/cryolink_arduino/cli.tar.gz \
  -C <scratch>/cryolink_arduino/bin arduino-cli
./scripts/build_firmware.sh
<scratch>/cryolink_arduino/bin/arduino-cli upload \
  --config-file esp32/arduino-cli.yaml --fqbn esp32:esp32:featheresp32 \
  --port /dev/ttyUSB0 --input-dir <scratch>/cryolink_arduino/build \
  esp32/cryolink_mcu
```

Exact versions: Arduino CLI **1.3.1**, Espressif Arduino core **3.3.2**;
Adafruit PWM Servo Driver Library **3.0.2**, OneWire **2.3.8**,
DallasTemperature **4.0.5**, HX711 Arduino Library (bogde) **0.7.5**,
Adafruit MPRLS Library **1.2.2**; transitive Adafruit BusIO **1.17.4** and
Adafruit Unified Sensor **1.1.15**. Host pyserial **3.5**.
No networking/Wi-Fi is initialized by the sketch.

Sensors run on a separate FreeRTOS task; Dallas conversions are asynchronous,
HX711 reads require ready, and Wire has a 20 ms transaction timeout. This keeps
sensor waits out of the safety loop. The MPRLS library's own bounded polling is
on the sensor task. Arduino ESP32 Wire serializes bus transactions. Stale/failed
sensors, missing PCA, or any failed PWM write force the software SAFE line-up.
PWM write errors latch until MCU reboot; failed writes are retried. A broken bus
cannot guarantee physical actuator movement. Serial parsing is bounded per tick
so an input flood cannot suppress the watchdog. Startup commands feed closed and
drain open when the PCA becomes available. Carriage/latch PWM stays disabled until
the first valid calibrated command; initial seat/latch switches establish the
mechanical starting state. Contradictory latch-without-seat or seat-plus-home
readings force SENSOR SAFE. This avoids an automatic home stroke against closed
hooks on boot.

## Protocol

The exact SP/ST fields and units match WIRING_BRIDGE. Pressure `p` is **kPa
absolute**, mass `m` is receiver water **g** after fixed tare, temperatures are °C.
Carriage 0 mm is fully mated; 36 mm is home/retracted.

ASSUMPTION: the previously unspecified checksum is **CRC-16/CCITT-FALSE**, initial
0xFFFF, polynomial 0x1021, no reflection/final XOR, over ASCII bytes before `*`.
Append four uppercase hexadecimal digits and LF. `123456789` has CRC 29B1. Frames
are at most 256 bytes including LF. No trailing CR, duplicate/missing/unknown
fields, nonfinite numbers or out-of-range travel. Firmware ignores boot chatter;
the host accepts only valid ST frames. See `rig_bridge.protocol.encode/decode`.

ASSUMPTION: sequence and heartbeat counters are uint32 with modular forward
ordering; duplicates/replays do not refresh freshness. SP sequence and **advancing
hb** must each be newer within 1 s. Invalid CRC or fields never renew the watchdog.
This strengthens the SP timeout so a live bridge cannot mask a dead sequencer.
A fresh command/heartbeat clears watchdog SAFE; stuck faults are reported while
mismatch persists. Interlocks continuously suppress feed whenever seat or latch
is false, even between commands. Latch-open is rejected while feed is commanded
open. Carriage retraction is rejected until hooks report open. Missing sensor or
uncalibrated operation forces SAFE. Mismatch longer than 200 ms reports STUCK,
closes feed and opens drain. Only seat, latch and home can be checked against
switches; there are no feed/drain position switches.

ASSUMPTION: a host or MCU restart requires a deliberate session reset (MCU reset
with reservoir clamped), because heartbeat and telemetry sequences restart. Do
not reset an operating MCU to work around an interlock. ASSUMPTION: checksum and
counters protect framing/replay mistakes, not hostile access.

## ROS 2 setup and operation

Reuse the existing `fsw/env.sh` RoboStack Jazzy environment. This package does not
rebuild FSW. Run commands from **this firmware directory**. Domain 89 is used to
avoid the original SIL's domain 87. Set a different private domain consistently
if another local rig run uses 89.

```bash
<scratch>/ros_env/bin/python -m pip install \
  --target <scratch>/cryolink_python pyserial==3.5
source scripts/env.sh
colcon build --base-paths . --build-base build --install-base install --parallel-workers 1
source install/local_setup.bash
ros2 launch rig_bridge rig.launch.py port:=/dev/ttyUSB0 \
  wall_threshold_c:=15.0 wall_hold_s:=5.0 fill_target_ml:=50.0
```

In another shell, source the same environment and send `standby`, `start`, then
`go` **after** LEAK_CHECK reaches AWAIT_GO:

```bash
ros2 topic pub --once /ground/uplink std_msgs/msg/String 'data: standby'
ros2 topic pub --once /ground/uplink std_msgs/msg/String 'data: start'
ros2 topic pub --once /ground/uplink std_msgs/msg/String 'data: go'
```

`abort` requests SAFE. Stopping/killing the bridge stops SPs; the independent MCU
watchdog commands feed closed/drain open after 1 s. SIGINT also closes the serial
port; it does not assume a final USB command reaches the MCU. Stop the graph
before changing calibration or emptying/re-taring the receiver.

For a bridge alone: `python -m rig_bridge.node --ros-args -p port:=/dev/ttyUSB0`.
ASSUMPTION: it intentionally sends no SP until telemetry, heartbeat, coupling and valve
setpoints are fresh. It stops sending on > 0.5 s stale telemetry or > 1 s stale
heartbeat/coupling/valve input and raises NODE_LOST. It does not invent heartbeats. Boot-time MCU WATCHDOG is expected before the
first command: the flight HEARTBEAT_LOST flag arms only after a valid ST reports
SAFE cleared. Raw startup SAFE/WATCHDOG remains visible on `/rig/status`; sensor
and calibration faults are still reported immediately.

Parameters on `rig_bridge` (set in launch or with `--ros-args -p name:=value`):

| Parameter | Default | Meaning |
|---|---:|---|
| `port` | /dev/ttyUSB0 | 115200 baud serial |
| `wall_threshold_c`, `wall_hold_s` | 15, 5 | strictly below 15 °C continuously for 5 s while conditioning |
| `fill_target_ml`, `water_density_g_ml` | 50, 1 | measured fill cutoff; density is ASSUMPTION |
| `ambient_kpa` | 101.325 | ASSUMPTION until measured before run |
| `leak_charge_kpa` | 8 | ASSUMPTION gauge charge gate below 1 m water head |
| `leak_settle_s`, `leak_hold_s` | 2, 60 | settle is ASSUMPTION; hold follows T4 |
| `leak_decay_limit_pa` | 100 | ASSUMPTION provisional; calibrate on known-good rig |
| `log_path` | logs/rig.csv | CSV: epoch/monotonic time, mode, step, SP, ST, leak, all inputs |

Parameters are startup settings; restart safely to change them. CSV includes all
unmapped setpoints so no command is silently discarded from the record. Run ID,
offsets, firmware hash, notes and independent scale/video evidence belong in a
separate per-run record per TEST_PROCEDURES; the software cannot collect them.

### Water adaptations and stubs

The existing nodes hard-code LOX saturation, 2 bar He leak charging, and oxygen
PVT gauging. They expose no water-threshold ROS parameters. Publishing fake
cryogenic readings would invalidate a water run, so this package makes the
adaptation explicit without editing FSW:

- ASSUMPTION: the installed `/setpoint/coupling` contains only a latch boolean,
  so the bridge infers carriage 0 mm to mate and 36 mm to retract, staging latch
  closure after seat and retraction after latch release.
- `fsw_runner` runs the installed classes; the real lifecycle sequencer is configured
  and activated. Coupling, pressure, chilldown, fill estimator, thermal, host and
  telemetry classes are unchanged. The original LOX `/leakcheck/result`,
  `/state/chill`, `/state/fill` publishers are remapped to `/diagnostics/lox/*`.
  Their outputs are diagnostic only; their LOX calculations are invalid on water.
- The bridge publishes the water leak/chill/fill states consumed by the sequencer.
  Leak charging opens actual feed with drain closed, closes feed at the measured
  charge gate, settles and holds real measured absolute p/T. ASSUMPTION: the spool wall is a proxy for the trapped
  pressure-tee gas temperature. It fails after a
  15 s charge timeout. This overrides the original He purge command, which has
  no actuator. Pressure decay is **not** a measured mL/min leakage qualification.
- Line conditioning is continuous feed+drain during FLOW when the real chill
  controller requests enable. ASSUMPTION: continuous water flow replaces the LOX
  pulse duty cycle. The measured wall gate is the only line-chill exit. Receiver
  chill is an explicit pass-through, feed closed/drain open.
- FILL/TOP_OFF use `in_a` as feed, `line_vent` as drain. There is also a bridge-side
  mass cutoff at the target. ASSUMPTION: `fill_flow = measured_ml / target_ml *
  0.95`, so the existing sequencer's 95% threshold means exactly the water target;
  TOP_OFF starts at 90/95 of target. This is a compatibility normalization, not
  physical receiver volume fraction. `fill_pvt` duplicates the load-cell estimate,
  explicitly marked stub; no independent fill disagreement test is possible.
- Supply pressure control, receiver pressure and gas purge have no hardware.
  Purge drains the line with feed closed; the sequencer retains its real 20 s
  PUSH + 10 s VENT dwell. HOLD/SAFE/DEMATE close feed and open drain.
- The FDIR process uses the real FdirMonitor with a process-local water vapor
  reference: atmospheric water boiling point 373.15 K instead of oxygen Tsat.
  Its existing +2 K rule becomes an over-hot wall proxy, **not a vapor detector**.
  Other flight fault checks and node liveness remain active. ASSUMPTION: open
  receiver at Earth atmosphere. The water rig does not validate LOX vapor FDIR.

All sensor topics remain `std_msgs/String` JSON using the FSW QoS: sensors best
effort depth 1, setpoints/states reliable, mode/step transient local. Metadata
keys `_stubs`, `_duplicates`, `_proxies`, `_derived`, `_open_loop` identify limits:

| Topic | Measured/derived | Stub/proxy fields |
|---|---|---|
| `/sensors/coupling` | seat/contact, latch, home | latch_a/b duplicate one switch; seal_ok=seat AND latch, not a seal test |
| `/sensors/temperature` | Tin→T_supply_liq, Twall→T_line_wall; °C→K | T_out_a/b and T_coupling proxy wall; receiver, bottle, electronics fixed 295.15 K |
| `/sensors/pressure` | MPRLS minus ambient, kPa→Pa gauge | p_line_a/b duplicate one transducer; supply, receiver, bottle 0 gauge |
| `/sensors/flow` | signed d(receiver mass)/dt in kg/s | mdot_vent=0; no flow meter; noise/handling affect derivative |
| `/valves/state` | MCU-reported feed/drain PWM commands; faults | other valves false, relief false, overpressure false; no pinch position feedback |
| `/host/accel`, `/host/attitude_status` | none | 1 g bench, zero rate, hold=true; no host sensors/thrust |
| `/sim/truth` | compatibility copy of rig measurements | entire topic marked `_stub=true`; no independent truth |

No duplicate pair is an independent sensor vote. There is no water overpressure
qualification or independent mass estimate. SENSOR/CALIBRATION/INTERLOCK/
LATCH_FEED/RETRACT faults route to the existing STUCK_VALVE → SAFE category with
an explicit MCU detail; STUCK uses the mismatch map; watchdog and stale setpoints
use the existing HEARTBEAT_LOST/NODE_LOST paths.

## Emulator and tests

For a manual session, run `python scripts/run_emulator.py` after sourcing the
environment. Keep it running and pass the printed `/dev/pts/N` path to
`ros2 launch rig_bridge rig.launch.py port:=/dev/pts/N` in another terminal.
The same ground commands work; no hardware is required.

`python -m rig_bridge.emulator --fd N --log logs/emulator.jsonl` takes an inherited
PTY master descriptor. `tests/integration.py` creates a raw master/slave PTY pair,
passes the master to the emulator, and gives the slave path to **pyserial** in the
bridge. It launches all nine real installed FSW classes in separate processes,
including the explicit water FDIR adapter. No synthetic ROS clock or sped-up ROS
time is used. Only owned process PIDs are signaled for cleanup.

ASSUMPTION emulator physics: 4 °C inlet, 22 °C initial wall, 3 g/s receiver fill
with feed open/drain closed; feed+drain routes entirely to waste and wall approaches
inlet exponentially with 3 s time constant. Pressure approaches 9.80665 kPa gauge
with feed only, is held with both pinches closed, and vents with 0.2 s time constant.
Ideal instantaneous carriage/latch motion is assumed. No leak, noise, compliance,
seal mechanics, power loss, tube force or servo lag model is claimed. Optional
`--control FILE` reads test-only `block_seat`, `block_latch`, and a changed
`reset_mass_id` (empty the emulated receiver once). The MCU protocol itself has
no simulation injection fields.

```bash
source scripts/env.sh
./scripts/test_safety.sh > logs/safety_tests.log 2>&1
python tests/integration.py > logs/integration.log 2>&1
python tests/integration.py --fault seat > logs/fault_seat_test.log 2>&1
python tests/integration.py --fault latch > logs/fault_latch_test.log 2>&1
```

The nominal test uses the full 60 s pressure hold and checks the exact FSW nominal
mode sequence, no faults, and recorded water fill. It empties the **emulated**
receiver between cycles, then SIGKILLs the bridge during second-cycle FILL and
checks independent emulator serial records for SAFE/feed closed/drain open within
2 s. Seat/latch runs use an explicitly shortened **2 s test-only pressure hold**
to reach FILL, inject one false switch, and require INTERLOCK with feed closed.
Separate PTY tests repeatedly request feed while each switch is false. Native
C++ tests exercise the exact firmware Safety.h, including 200 ms mismatch, latch
opening, retraction, sensor failure and uint32 rollover; Python/C++ parser corpus
checks checksum, invalid fields, ranges and replay behavior.

Saved logs and JSON results are under `logs/`; see `logs/VALIDATION.md` for the
actual run results. `logs/first_nominal_run/` preserves the first completed nominal
cycle and the interrupted attempt to start a second cycle with an already-full
receiver. It is not the final watchdog test. Build evidence is in
`logs/firmware_compile.log` and `logs/ros_package_build.log`.

Not tested on physical hardware: flashing, probe ROMs, tare/calibration, servo
motion or timing, pinch isolation, hydraulic split, pressure resolution, leak
qualification, spill, capture, power loss, and 20-cycle endurance. T1–T8 require
the real rig, independent scale, side-view video and per-run metadata. The emulator
results do not establish those acceptance limits or cryogenic performance.

Context used: WIRING_BRIDGE.md, TEST_PROCEDURES.md, cad/CHECKS.md, zyxem/HANDOFF.md,
Documents/HANDOFF_ALL.md, fsw/README.md, env.sh, plant_sim.py, the flight node sources
and SIL harness. No inbox search was needed for the specified firmware interfaces.
