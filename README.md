# CryoLink water transfer rig

This repository holds everything needed to build the CryoLink water transfer rig, our AA 261 Part II prototype. The rig mates, latches, leak-checks, chills, fills and disconnects the CryoLink propellant coupling, with water in place of liquid oxygen.

Three documents describe it:

- [`book/CryoLink_Rig_Build_Guide.pdf`](book/CryoLink_Rig_Build_Guide.pdf) is the build guide. It has the parts, a 1:1 hardware sheet, the shopping list, 70 assembly steps, the wiring and the test sequence.
- [`docs/CryoLink_Prototype_Report.pdf`](docs/CryoLink_Prototype_Report.pdf) explains what we built and why, with the timeline, the limitations and the next steps.
- [`sims/CryoLink_Simulations.pdf`](sims/CryoLink_Simulations.pdf) reports on the simulations of the coupling and of the transfer.

## How the rig works

The rig uses the geometry of our two-half coupling: a 22 mm bore, a capture cone on half A, a nose on half B and a spring-closed poppet valve in each half. When the halves mate, pins push both valves open by 2 mm.

Water flows by gravity from a 250 mL beaker on a mast, at most 0.6 m above the base. It passes through:

1. a manual clamp, which is the emergency stop;
2. the feed pinch valve;
3. half B and half A;
4. a metal conditioning spool with a temperature probe on its wall;
5. the manifold.

From the manifold, the drain pinch valve sends water to a waste cup. A raised fill branch drops it into a receiver beaker that sits on a load cell.

Half B rides on a floating plate mounted on soft grommets, which gives the cone the play it needs to correct an offset. A servo crank drives the carriage under the plate through 36 mm of travel. A second servo turns a shaft with two hooks that catch the back of half B just past centre.

Three switches report when the halves are seated, latched and fully retracted. A pressure sensor on the manifold handles the leak check. An ESP32 drives the four servos through a PCA9685 board and talks to our ROS 2 flight software through `firmware/rig_bridge`. It keeps the feed shut unless the halves are both seated and latched, and it closes the feed within two seconds if the link to the flight software drops.

The build guide lists the tests in the order to run them, and `tests/TEST_PROCEDURES.md` gives the full procedures. The follow-on cryogenic test is drafted in `tests/LN2_TEST_PLAN.md`.

## Folders

- `cad/step/assembly.step` is the whole rig with its 355 parts in place. Every other file in `cad/step/` is a single part in its own manufacturing coordinates.
- `cad/stl/` has the printable parts.
- `cad/drawings/` has the machining sheets for the PRL.
- `cad/BOM.csv`, `cad/PRINTS.csv` and `cad/ORDER_LIST.md` hold the bill of materials, the print orientations and the orders.
- `cad/ASSEMBLY.md` has the fabrication notes. `cad/CHECKS.md` lists what the CAD cannot prove.
- `cad/SUBBASE_HOLES_REPORT.md` records the 24 anchor holes added to the wet subbase on 13 November.
- `cad/build.py` regenerates the CAD with CadQuery.
- `cad/scale_model_30pct/` has the rig at 30% scale on three print plates, as a display model.
- `firmware/` holds the ESP32 firmware and the ROS 2 bridge.
- `sims/` holds the simulation code, the results and the simulations report.
- `tests/` holds the test procedures, the liquid nitrogen plan and the wiring notes.

To open the CAD in Fusion 360, use File, then Open, then Open from my computer, and pick `cad/step/assembly.step`. Each part arrives as a named component. The repository has no native `.f3d` files.
