# Water rig: wiring and ROS 2 bridge plan (2026-11-05)

Labels: MEASURED = read at source (LINK_CHECK.md, copies in <scratch>/verify_1105/bom); ESTIMATE = our design choice; UNVERIFIED = not confirmed.
Hardware layout comes from prototype/cad (ASSEMBLY.md steps 10-14). Software comes from cryolink/fsw (README.md node graph).

## 1. Idea
- The flight software runs unchanged on a laptop. Only `plant_sim` is swapped for a new `rig_bridge` node.
- `rig_bridge` talks to the ESP32 over USB serial. The ESP32 plays the safety MCU: it owns the servos and the interlocks.
- This keeps the flight rule: "No ROS node commands a coil" (fsw/README.md, "Separation from the safety MCU"). (ESTIMATE design, rule MEASURED in README)

## 2. Parts on the bus
| Part | Job | Interface | Price |
|---|---|---|---|
| Adafruit HUZZAH32 (3405) | safety MCU, serial link | USB | $19.95 MEASURED |
| Adafruit PCA9685 16-ch (815) | 4 servo PWM | I2C | $14.95 MEASURED |
| 4 x SG-5010 servo | carriage, latch, feed pinch, drain pinch | PWM from 815 | $48.00 MEASURED |
| 3 x Pololu 1402 switch | seat, latch, home | GPIO | $7.11 MEASURED |
| 2 x DS18B20 (381) | wall of the metal spool, inlet water | 1-Wire, one pin | $19.90 MEASURED |
| HX711 board (5974) + 5 kg load cell (4541) | receiver mass = fill | 2 GPIO | $9.95 + $3.95 MEASURED |
| MPRLS 0-25 psi absolute (3965) | line pressure for leak check | I2C, address 0x18 MEASURED | $29.95 MEASURED |

- New items vs CAD BOM: HX711 + load cell + MPRLS = $43.85 (MEASURED prices). They replace the borrowed scale and add the pressure the FSW leak check needs.
- MPRLS is a gas sensor port (Adafruit text mentions vacuum chambers and pressurized containers; no water rating found). Connect it through an air-filled tube from a tee above the manifold, never wetted. (ESTIMATE; water compatibility UNVERIFIED)
- 1 m of water head is 9.8 kPa (CHECKS.md, COMPUTED), so the leak check sees a small rise over ambient. Honeywell datasheet (MEASURED): TEB ±1.5 %FSS (±2.6 kPa), resolution 14.0 bits (~10.5 Pa COMPUTED). Use it for pressure change only, not absolute head.

## 3. Pin map (ESP32 HUZZAH32)
GPIO numbers below are confirmed as general GPIO on the Adafruit pinout page (MEASURED, learn.adafruit.com/adafruit-huzzah32-esp32-feather/pinouts). Avoided: GPIO 12 (built-in pull-down, page says so), GPIO 34/39 (input only, page says so).
| Signal | GPIO | Note |
|---|---|---|
| seat switch | 27 | internal pull-up, switch to GND, normally open: open wire reads "not seated" (ESTIMATE) |
| latch switch | 33 | same wiring |
| home switch | 14 | same wiring |
| DS18B20 bus | 32 | 4.7k pull-up to 3.3 V (in CAD BOM allowance) |
| HX711 DOUT | 21 | |
| HX711 SCK | 25 | |
| I2C SDA / SCL | 23 / 22 (Feather SDA/SCL pads) | MEASURED in arduino-esp32 feather_esp32 pins_arduino.h; firmware Calibration.h uses the same. 815 and MPRLS share the bus |
- ESP32 power loss (e.g. USB cable pulled when USB powers it) stops the watchdog; geared servos may hold the last position. Only the manual clamp makes this safe. Power the ESP32 from a supply that stays on when the laptop link is lost. (ESTIMATE, from Codex firmware note 11-05 and CHECKS.md)
- I2C pull-ups: the Feather has none (Adafruit pinout page, MEASURED). The 815 board has 10K pull-ups to its VCC pin (MEASURED). So wire 815 VCC to the Feather 3V pin, never to 5 V; servo 5 V goes only to the V+ terminal. No extra resistors needed (ESTIMATE; check SDA/SCL idle at ~3.3 V with a meter before powering servos).
- Power (supply options and capacitor checked 11-06, see ORDER_LIST): servo 5 V from a separate current-limited bench supply into the 815 V+ terminal; ESP32 on laptop USB; common ground. Stall current of SG-5010 is not published (CHECKS.md), so measure it first and set the supply limit from that. (MEASURED gap)

## 4. Serial protocol (ESTIMATE)
- 115200 baud, one line per message, ASCII, checksum at the end.
- Laptop to MCU, 10 Hz: `SP <seq> carriage=<mm> latch=<open|closed> feed=<0|1> drain=<0|1> hb=<n>*<crc>`.
- MCU to laptop, 10 Hz: `ST <seq> seat=<0|1> latch=<0|1> home=<0|1> Twall=<C> Tin=<C> m=<g> p=<kPa> feed=<0|1> drain=<0|1> safe=<0|1> fault=<code>*<crc>`.
- MCU rules, enforced in firmware, not in ROS:
  - feed opens only if seat AND latch are true; otherwise reject and report `fault=INTERLOCK`;
  - no valid `SP` for 1 s puts the line-up in SAFE: feed closed, drain open (heartbeat timeout 1 s from fsw/README.md "watchdog"; CHECKS.md acceptance is isolation in 2 s or less);
  - latch may open only with feed closed;
  - commanded vs switch mismatch over 0.2 s flags a stuck actuator (same 0.2 s ASSUMPTION as fsw/README.md).
- Geared servos may hold position without power (CHECKS.md), so loss of servo power is not a safe state. Keep the manual reservoir clamp in reach. (MEASURED limit from CHECKS.md)

## 5. Topic mapping in `rig_bridge` (ESTIMATE)
| FSW topic | Rig meaning |
|---|---|
| `/setpoint/coupling` | carriage position + latch command |
| `/setpoint/valves` in_a | feed pinch |
| `/setpoint/valves` line_vent | drain pinch (conditioning = chilldown analogue) |
| `/setpoint/valves` rx, others | no hardware; logged only |
| `/setpoint/heartbeat` | `hb` field; MCU watchdog |
| `/sensors/coupling` | seat, latch, home switches |
| `/sensors/temperature` | Twall (Tw_line), Tin |
| `/sensors/pressure` | MPRLS minus ambient as p_line; p_rx not measured |
| `/sensors/flow` | d(mass)/dt from the load cell |
| `/valves/state` | MCU-reported pinch states |
- `/clock`: the bridge runs on wall time; nodes run with `use_sim_time:=false`. (ESTIMATE)
- Parameter overrides needed for water: chilldown exit "wall < 15 C for 5 s" and fill target 50 mL from CHECKS.md, instead of the LOX thresholds. (MEASURED values in CHECKS.md)
- Pressure-control and receiver-chill steps have no rig hardware: run them as pass-through and say so in the data package. (ESTIMATE)

## 6. What ties to our sims
- Same mode sequence as the nominal replay: LATCHING, MATED, LEAK_CHECK, LINE_CHILLDOWN, FILL, DRAIN_AND_PURGE, DEMATE (fsw replay steps). Plot rig mode times next to replay mode times.
- Fault cases we can repeat on the rig: leak check fail (crack the manual clamp or a loose barb), heartbeat loss (unplug USB), false interlock (block one hook). These mirror fault_leak_check and the watchdog test. (ESTIMATE)
- Not comparable: flow rate, pressure drop, two-phase chilldown physics (CHECKS.md says so for the narrow tubing).

## 7. Open items
- Firmware and `rig_bridge` code not written (ESTIMATE ~1 day for Guilherme).
- MPRLS short-term drift not in the datasheet; measure it (T4 step 0).
- Load-cell mount under the receiver is not in the CAD yet.
