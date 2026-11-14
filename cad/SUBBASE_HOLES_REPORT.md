# Subbase anchor holes — 2026-11-13

Added 24 Ø3.3 mm through tap drills for M4x0.7 threads in HDPE. All 24 screws have Ø4 mm cylindrical shanks and Ø7 mm heads; no M5 anchors occur in the target list. Hole axes were extracted from the fastener cylinder surfaces in the original assembly STEP and confirmed against the regenerated STEP. All axes are parallel to Z. Assembly XY equals subbase local XY; plate spans assembly Z25–35 mm (local Z0–10).

`build.py` now defines `SUBBASE_ANCHOR_HOLES` and `make_wet_subbase()`, used by both the full build and a new targeted export mode. No full build was run. Exact export command:

```sh
PYTHONDONTWRITEBYTECODE=1 python build.py --subbase-only
```

This regenerated only `step/wet_subbase.step`, `step/assembly.step`, and `drawings/wet_subbase.{svg,png,pdf}`. The wet_subbase note in `drawings.py` now specifies the tap drills. Other assembly components were loaded from the existing STEP and retained; only `wet_subbase_36` was replaced. No BOM or inventory changes.

Verification used the same Python interpreter with an inline Python script: reimport both STEP exports; execute only the source subbase geometry definitions via AST; compare both directions of Boolean differences; run `OCP.BRepAlgoAPI.BRepAlgoAPI_Common` for each of the 24 target screws and for each full-thickness Ø3.3 core cylinder. Both STEP exports agree with source geometry within 0.00001 mm³; all solids are valid and the assembly retains its 355 component objects.

Acceptance: overlap ≤ π(2²−1.65²) × engaged length × 1.02. **24/24 pass. All full-thickness core overlaps are <0.000001 mm³.** Remaining overlap is intentional thread engagement. The original <0.05 mm³ screw-overlap criterion is superseded by the user's thread-annulus criterion.

All dimensions are mm; volumes are mm³. Annulus is the nominal volume before the +2% tolerance.

| Fastener | Drill Ø | Assembly X | Assembly Y | Engaged length | Common volume | Annulus | Core volume |
|---|---:|---:|---:|---:|---:|---:|---:|
| feed_anchor_screw_0 | 3.3 | -210.000 | -32.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| feed_anchor_screw_1 | 3.3 | -210.000 | -22.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| feed_anchor_screw_2 | 3.3 | -170.000 | -32.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| feed_anchor_screw_3 | 3.3 | -170.000 | -22.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| drain_anchor_screw_0 | 3.3 | -135.000 | -32.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| drain_anchor_screw_1 | 3.3 | -135.000 | -22.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| drain_anchor_screw_2 | 3.3 | -95.000 | -32.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| drain_anchor_screw_3 | 3.3 | -95.000 | -22.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix8_riser_anchor_-145 | 3.3 | -145.000 | 36.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix8_riser_anchor_-133 | 3.3 | -133.000 | 36.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix8_manual_anchor_-240 | 3.3 | -240.000 | -35.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix8_manual_anchor_-230 | 3.3 | -230.000 | -35.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_servo_base_0_-30.5 | 3.3 | 87.500 | -105.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_servo_base_0_30.5 | 3.3 | 148.500 | -105.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_servo_base_1_-30.5 | 3.3 | -220.500 | -93.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_servo_base_1_30.5 | 3.3 | -159.500 | -93.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_servo_base_2_-30.5 | 3.3 | -145.500 | -93.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_servo_base_2_30.5 | 3.3 | -84.500 | -93.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_latch_tower_anchor_-6 | 3.3 | 197.984 | 80.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9_latch_tower_anchor_6 | 3.3 | 215.984 | 80.000 | 9.2 | 36.923138 | 36.923138 | 0.000000 |
| fix9b_fill_anchor_0 | 3.3 | -238.000 | -10.000 | 10.0 | 40.133846 | 40.133846 | 0.000000 |
| fix9b_fill_anchor_1 | 3.3 | -222.000 | -10.000 | 10.0 | 40.133846 | 40.133846 | 0.000000 |
| fix9b_waste_anchor_0 | 3.3 | -53.000 | 96.000 | 10.0 | 40.133846 | 40.133846 | 0.000000 |
| fix9b_waste_anchor_1 | 3.3 | -37.000 | 96.000 | 10.0 | 40.133846 | 40.133846 | 0.000000 |

Context checked: overlap JSON, build.py, fix9_geometry.py, fix9b_geometry.py, drawings.py, inventory.json, and assembly/part STEP files, all within this CAD folder.
