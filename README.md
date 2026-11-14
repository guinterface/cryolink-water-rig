# CryoLink Water Transfer Rig

A bench-scale robot that mates, latches, leak-checks, chills, fills and disconnects our real propellant coupling, using water in place of liquid oxygen. It is the AA 261 Part II prototype for CryoLink.

**Project summary (everything so far, incl. the NASA Glenn call):** `PROJECT_SUMMARY.md`.

**Start here:** `book/CryoLink_Rig_Assembly_Book.pdf`. It is a 41-page build book (LEGO / IKEA style) with every part, the shopping list, 21 assembly steps, wiring, the test plan and our simulations.

---

## 1. What CryoLink is

CryoLink sells two things:

- **the CryoLink Transfer Assembly (CTA)**, fitted to depots and tankers;
- **a receiver kit**, fitted to client spacecraft.

Together they let a tanker refuel a client in orbit with cryogenic propellant. Longer term, we run our own depot.

The heart of both products is a **two-half coupling**:

- **Half A** is on the CTA. It has a capture cone and a spring-closed poppet valve.
- **Half B** is on the client. It has a capture nose and its own spring-closed valve.

When the halves are pushed together, the cone pulls B into line. A latch then locks the halves and both valves open. When the halves separate, both valves snap shut.

## 2. What the rig proves

The rig runs the same sequence as our flight software, at bench scale:

```
mate → latch → leak check → condition (chill) the line → fill → drain → unlatch → retract
```

| Test | Pass mark | Claim it checks |
|---|---|---|
| T1 Mate from ±5 mm / 1° offset | ≥ 90% capture | The cone aligns the halves by itself |
| T2 Interlocks | No flow unless seated **and** latched | Safe by design |
| T3 Valve hold, apart | ≤ 1 mL/min per half | Each half seals itself |
| T4 Mated leak check | ≤ 1 mL/min | The joint seals; a loose fitting is caught |
| T5 Line conditioning | Gate trips on wall < 15 °C; receiver stays dry | Water version of chilldown |
| T6 Full autonomous cycle | No hand help; spill ≤ 5 mL | No operator needed |
| T7 Lost link | Feed shut, drain open within 2 s | Goes safe by itself |
| T8 Endurance | ≥ 18 of 20 cycles | Reusable coupling |

Full procedures are in `tests/TEST_PROCEDURES.md`. The cryogenic follow-on is in `tests/LN2_TEST_PLAN.md`.

## 3. How the rig works

- **Water path.** A 250 mL source beaker sits on a mast, at most 0.6 m up, so gravity gives about 6 kPa. The water runs through:
  1. a manual clamp, which is the emergency stop;
  2. the **feed pinch valve**;
  3. coupling half B, then half A;
  4. a metal **conditioning spool** with a temperature probe clamped to its wall;
  5. the **manifold**.
- **From the manifold**, the water goes one of two ways:
  - the **drain pinch valve** sends it to a waste cup;
  - a raised fill branch drops it into a receiver beaker that sits on a **load cell**.
- **Moving the client half.** Half B sits on a floating plate on soft grommets. That plate rides on a **carriage**, and a servo crank drives the carriage 36 mm toward half A. The float is what lets the cone correct an offset.
- **Latch.** Two hooks on a shaft, turned by a servo, catch the back of B just past centre (over-centre).
- **Sensors:**
  - seat, latch and home switches;
  - two DS18B20 temperature probes, on the spool wall and in the inlet water;
  - a load cell, which measures the fill;
  - an MPRLS pressure sensor, for the leak check.
- **Brain.** An ESP32 runs the safety logic and drives the 4 servos through a PCA9685 board. It refuses flow unless seat and latch are both true, and its watchdog shuts the feed if the link drops. It talks over USB to our ROS 2 flight software through the `rig_bridge` node.

## 4. Folder map

| Path | What |
|---|---|
| `book/` | The assembly book (PDF) |
| `cad/step/assembly.step` | The whole rig, every part in place |
| `cad/step/*.step` | Each part on its own, in manufacturing coordinates |
| `cad/stl/` | Printable parts |
| `cad/drawings/` | Machining sheets for the PRL (PDF / PNG / SVG) |
| `cad/BOM.csv`, `cad/PRINTS.csv` | Bill of materials, print orientations |
| `cad/ORDER_LIST.md` | What to buy, by vendor, with part numbers and prices |
| `cad/ASSEMBLY.md`, `cad/CHECKS.md` | Detailed fabrication notes and the checks CAD cannot prove |
| `cad/build.py` | Regenerates all CAD (CadQuery) |
| `cad/scale_model_30pct/` | The whole rig at 30% scale on 3 print plates (display model, about 2 h per plate) |
| `firmware/` | ESP32 firmware and the ROS 2 bridge |
| `sims/` | Simulation code and results (section 6) |
| `tests/` | Test procedures, LN2 plan, wiring and bridge |

## 5. Opening the CAD in Fusion 360

Fusion 360 reads STEP directly. Native `.f3d` files are not included.

1. In Fusion: **File → Open → Open from my computer**, then pick `cad/step/assembly.step`. Fusion uploads and converts it, which takes a minute.
2. Each part arrives as its own component with its name, such as `capture_A`, `B_poppet` or `servo_SG5010_52`.
3. To edit one part, open its own STEP from `cad/step/`.

## 6. Simulations

| Folder | Tool | What it answers | Result |
|---|---|---|---|
| `sims/mechanics` | MuJoCo 3.17 | Does the cone capture from an offset? | Simplified cone: 60/60 seat up to 7 mm, 1°. **Real flight CAD jams** (0.1 mm clearance, no lead-in chamfer, 22.3 kN peak): it needs a chamfer |
| `sims/thermal` | Transient wall model | Propellant lost chilling the line | 12.0 kg continuous vs 4.4 kg pulsed (−63%). **Failed validation** against NASA/UF LN2 data, so this is a direction only |
| `sims/levers` | Monte Carlo transfer study | Coating, pulsing, spray, line size | Trade study; same validation caveat |
| `sims/cfd/poppet` | OpenFOAM 2412 | Does the coupling choke the flow? | 1.8 kPa loss at 1,000 kg/h LOX (< 0.5% of supply) |
| `sims/thermal/nvf_receiver.py` | CoolProp | Can the client tank fill without venting? | Yes, if its wall starts ≤ 200 K (3.0 bar peak, under 4 bar relief) |
| `sims/fea` | CalculiX 2.23 | Launch loads | First mode 82 Hz; static margins ≥ +2.05; proof +3.13. Qualification random vibration **−0.22** at a bolt edge |
| `sims/seals` | Cold-fit calculation | Do seals fit at 90 K? | Yes, after switching to PTFE seals and holding B ≥ 203 K before mating |

Large solver outputs (meshes, `.frd` result files, OpenFOAM case folders) are left out to keep the repository small. Each script regenerates them.

## 7. Building it

- **Print** the 61 printed parts in PETG: 0.2 mm layers, 5 walls, 40% infill. About 48 printer-hours.
- **Machine** the 29 metal and plastic parts at the PRL, from `cad/drawings/`.
- **Buy** the components: $318.57 in four orders (Adafruit, Pololu, McMaster, ServoCity), before tax and shipping. Fasteners and stock come extra, or from PRL.
- **Assemble** following the book, steps 1–21, then wire and run the tests in order: T1 to T8.

## 8. What the rig does not prove

- Cryogenic sealing and real chilldown. That is the LN2 bench test that comes next.
- That the flight valve on half B opens by pressure. On the rig, both valves are pushed open mechanically.
- Flight capture with the corrected chamfer. The rig uses its own printed cones.
