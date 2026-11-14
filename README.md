# CryoLink Water Transfer Rig

A bench-scale robot that mates, latches, leak-checks, chills, fills and disconnects the CryoLink propellant coupling, with water in place of liquid oxygen. It is our AA 261 Part II prototype.

| Document | What it is |
|---|---|
| [`book/CryoLink_Rig_Build_Guide.pdf`](book/CryoLink_Rig_Build_Guide.pdf) | **Build guide.** Parts with part numbers, hardware at 1:1 scale, shopping list, 45 assembly steps with section views, wiring, test order |
| [`docs/CryoLink_Prototype_Report.pdf`](docs/CryoLink_Prototype_Report.pdf) | What we built and why, timeline, limitations, next steps |
| [`sims/CryoLink_Simulations.pdf`](sims/CryoLink_Simulations.pdf) | Separate report on the coupling and transfer simulations |

## How the rig works

```
mate → latch → leak check → condition (chill) the line → fill → drain → unlatch → retract
```

- **The coupling.** Our two-half coupling: 22 mm bore, a capture cone on half A, a nose on half B, and spring-closed poppet valves in both halves. When the halves mate, both valves are pushed open by 2 mm.
- **Water path.** A 250 mL source beaker sits on a mast, at most 0.6 m up. The water runs through:
  1. a manual clamp (the emergency stop);
  2. the feed pinch valve;
  3. half B, then half A;
  4. a metal conditioning spool with a temperature probe on its wall;
  5. the manifold.

  From the manifold, the drain pinch valve sends water to a waste cup. A raised fill branch drops it into a receiver beaker that sits on a load cell.
- **Motion.** Half B sits on a floating plate on soft grommets, so the cone can correct an offset. The plate rides on a carriage, and a servo crank drives the carriage 36 mm.
- **Latch.** Two hooks on a servo-driven shaft catch the back of half B just past centre.
- **Sensors:**
  - seat, latch and home switches;
  - two DS18B20 temperature probes (spool wall, inlet water);
  - a 5 kg load cell (the fill);
  - an MPRLS pressure sensor (the leak check).
- **Control.** An ESP32 drives the 4 servos through a PCA9685 board and talks to our ROS 2 flight software through `firmware/rig_bridge`. It refuses flow unless seat and latch are both true, and a watchdog shuts the feed within 2 s if the link drops.

## Tests

| Test | Pass mark |
|---|---|
| T1 Mate from ±5 mm and 1° offset | ≥ 90% capture |
| T2 Interlocks | No flow unless seated and latched |
| T3 Valve hold, halves apart | ≤ 1 mL/min per half |
| T4 Mated leak check | ≤ 1 mL/min |
| T5 Line conditioning | Gate on wall temperature; receiver stays dry |
| T6 Full autonomous cycle | No hand help; spill ≤ 5 mL |
| T7 Lost data link | Feed shut within 2 s |
| T8 Endurance | ≥ 18 of 20 cycles |

Procedures are in `tests/TEST_PROCEDURES.md`. The liquid nitrogen follow-on is in `tests/LN2_TEST_PLAN.md`.

## Folder map

| Path | What |
|---|---|
| `cad/step/assembly.step` | The whole rig, 355 parts in place |
| `cad/step/*.step` | Each part on its own, in manufacturing coordinates |
| `cad/stl/` | Printable parts |
| `cad/drawings/` | Machining sheets for the PRL |
| `cad/BOM.csv`, `cad/PRINTS.csv`, `cad/ORDER_LIST.md` | Bill of materials, print orientations, what to buy |
| `cad/ASSEMBLY.md`, `cad/CHECKS.md` | Fabrication notes, and the checks CAD cannot prove |
| `cad/SUBBASE_HOLES_REPORT.md` | The 24 anchor holes added to the wet subbase (13 Nov) |
| `cad/build.py` | Regenerates the CAD (CadQuery) |
| `cad/scale_model_30pct/` | The whole rig at 30% scale on 3 print plates (display model) |
| `firmware/` | ESP32 firmware and ROS 2 bridge |
| `sims/` | Simulation code, results and report |
| `tests/` | Test procedures, LN2 plan, wiring and bridge notes |

## Opening the CAD in Fusion 360

File → Open → Open from my computer → `cad/step/assembly.step`. Every part comes in as a named component. Native `.f3d` files are not included.

## Building it

1. **Order** the components ($318.57 in four orders; see the build guide, pages 8–9).
2. **Print** the printed parts in PETG: 0.2 mm layers, 5 walls, 40% infill.
3. **Machine** the metal and HDPE parts at the PRL from `cad/drawings/`.
4. **Assemble** following the build guide.
5. **Wire** it, then run T1 to T8 in order: dry first, then with water.
