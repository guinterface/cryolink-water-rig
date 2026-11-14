# CryoLink WATER prototype — checks and limits

Engineering assumptions are distinguished from CAD checks and hardware tests. Run `build.py` with the specified CadQuery Python; it regenerates the machine-readable reports cited below. No physical test has been performed. This package does not qualify pressure-opened flight B, cryogenic materials or free-flight capture.

Final generated verification: **0 unresolved nominal rigid overlaps, 0 unresolved sampled-travel overlaps, no unintended disconnected print solids, and all print envelopes fit MK4-class capacity.** Assembly STEP reimport is valid; all42 exported STL files passed the two-incident-edge check. There are109 STEP files (including assembly),16 PRL plus2 FIX3 print drawing sets and6 renders. See export_checks.json for current sizes, below15MB. See `build.log`, `verification_summary.json` and `export_checks.json`. These results do not replace the hardware tests below.

## Geometry and interference

`inventory.json` records each BRep’s validity, volume and envelope. `interferences.json` contains positive-volume nominal rigid intersections after bounding-box rejection; `interference_review.json` classifies every reported pair. A male10-32thread cylinder intentionally intersects a tap-drill cylinder; those are simplified thread engagements, not verified thread fits. Seat and latch levers intentionally contact their witness cams in the actuated pose. Pololu specifies maximum operating force0.9N and a dashed lever position9.6±1.0mm above the mounting-hole axis; this is not a guaranteed differential travel or overtravel allowance. Set actual transitions on hardware.

Seal, spring, soft grommet and schematic hose geometry is excluded from rigid interference tests: those deform and cannot be treated as rigid-body clearance evidence. Standard O-ring STEP is undeformed; assembly O-rings show simplified installed elliptical sections. CAD cannot establish sealing, hose slack, bolt preload or elastic switch travel. Numerical values are retained in the reports rather than discarded as “zero interference.”

`travel_checks.json` tests actual B/carriage solids at6,18,36mm retraction with hooks rotated30° open. `verification_summary.json` reports unresolved overlaps. This is a sampled travel check, not a continuous swept-volume certificate. Flexible feed-loop motion is a manual dry check before wet operation. The latch shaft is behind B’s maximum retracted rear face, not across the fluid bore. Retraction must not occur with the hooks closed.

`capture_checks.json` samples cone contact ordering at four5mm lateral directions and±1° tilt. The B pose retains its initial error for this search; cone contact before metal-face contact shows available guidance travel, not successful self-centering. The carriage allows nominal±6mm hard lateral travel from16mm holes around4mm shoulder fasteners; soft centering grommets, large retaining washers and axial clearance accommodate tilt. The cone mouth radius46 clears an initial27.75mm tip plus5mm delivery error and30tan1°=0.524mm tilt allowance, leaving12.73mm initial radial margin. Final cone radial clearance0.25mm is a design assumption requiring a print coupon and actual capture trials. Offset fixtures are removable; they must not lock out compliance.

## FDM fabrication

`PRINTS.csv` lists quantity, size, bed orientation and support strategy for every printable part. `print_checks.json` compares each envelope, allowing axis permutation, with250×210×220mm MK4-class capacity. Large base/subbase/mast/carriage metal parts are not FDM parts. STLs use0.15mm chord and0.18rad angular export tolerances; slicer hole compensation is independent.

Use PETG,0.4mm nozzle,0.2mm layers,5perimeters,40% infill and6top/bottom layers as starting settings. Print the capture cone axis vertical, larger end down. Female cone wall is4mm radially (3.43mm normal to the cone); male nose minimum radial wall2.55mm. Housing sleeve wall4.8mm except the local FIX3 seating/tip clearances described below; retainer wall≥4.8mm, latch arm10×8mm, pinch roof6mm and side columns8mm exceed a nominal2.4mm structural wall target. Thin0.8mm clamp splits are intentional gaps, not walls. Deburr printed seal-adjacent openings without touching machined sealing lands.

The cone slope0.6radial/axial is about31° from the axis. Large end down makes the inner funnel printable; local annular shoulders can need organic support. Print stands on their sides so shaft bores are vertical. Print the pinch roofs separately instead of bridging the whole jaw bay. Lay the tall switch supports and witness brackets on a side; align layer paths along the latch arms. Split coupler halves may appear as two disconnected solids in one STL; arrange/clamp them as a pair. All support removal and shaft-hole reaming happen with hardware absent.

Printed strength is not inferred from filament marketing. At a conservative90N total retained axial load, each hook carries45N, about0.56MPa direct stress in an80mm² arm, before local concentration, layer or creep factors. Those factors and the clamp connections require a dry proof load and repeated inspection. Do not rely on a printed servo spline: fasten to the supplied horn. Several fixture holes are explicitly transfer-drilled after fitting real hardware; those operations are stated on the drawings and in ASSEMBLY.md.

## O-ring glands

Selected seal: McMaster9452K113, AS568-026 NBR70A; supplier cross-reference gives ID31.47mm, section1.78mm, OD35.03mm. McMaster direct drawing/price was inaccessible; see [supplier cross-reference](https://www.globaloring.com/product/n70026/). This is water/chilled-water selection, not cryogenic qualification.

Axial interface and rear-cap glands: OD35.03mm, radial width2.64±0.03mm, depth1.32±0.02mm. Nominal squeeze=(1.78−1.32)/1.78=25.84%. Using Parker’s actual.070±.003in section and the stated depth tolerance gives21.26–29.89% worst-case squeeze. Nominal cross-section fill is π(1.78²)/4 /(2.64×1.32)=71.4%, leaving expansion room. Parker chart4-3 lists19–32% squeeze,1.270–1.372mm depth and2.565–2.718mm liquid groove width for this section. The chosen nominal gland lies inside that dimensional range. [Parker ORD5700, chart4-3 p4-18](https://www.parker.com/Literature/O-Ring%20Division%20Literature/ORD%205700.pdf)

The replaceable seat uses the same-026ring in a radial static gland: rootØ31.40±0.03, width2.64±0.03 and mating pocketØ34.05 +0.03/0. Nominal installed radial height1.325mm gives25.6% squeeze; worst-case section/diameter stack gives approximately20.4–29.3%. Root circumference compresses the free ring ID by0.22%, within Parker’s small circumferential-compression guidance; exact compound and tolerance approval remains a fit test. The axial chart is the basis for the face glands, not a claim that it specifies the radial seat geometry. [Parker static installation guidance](https://www.parker.com/content/dam/Parker-com/Literature/Praedifa/Catalogs/Catalog_O-Ring-Handbook_PTD5705-EN.pdf)

Finish sealing faces to≤0.8µm RMS and0.03mm flatness, and gland rootsR0.15–0.25. These are drawing requirements; no metrology was performed. The back face-insert joint uses a thin removable RTV film, cured before water. It is a prototype service joint and must be leak tested. Nominal poppet seal is a2mm silicone washer against a machined acetal seat; it is not assigned O-ring squeeze data.

## Poppets and1m head

Water pressureρgh=1000×9.80665×1=9806.65Pa. A22mm projected seat area is380.13mm², so conservative hydraulic opening force is3.728N per half. The stainless9435K37catalog spring is20.6502mm free, rate4.4lbf/in=0.77056N/mm. Closed length13.65mm gives5.394N preload, a1.45factor over the full1m hydraulic force. Open length11.65mm gives6.935N, below catalog1.7lbf=7.56N maximum load; length exceeds catalog10.5918mm compressed-length limit by1.058mm. This is a force budget, not demonstrated closure: guide friction, washer adhesion, temperature and spring tolerances can consume the1.67N closing surplus. [McMaster catalog rows9435K37 and9435K125](https://www.mcmaster.com/products/9657K236/)

The opposing pins retract each poppet2mm at full mate. The spring-closed mechanism therefore operates at gravity head without requiring pressure to crack B. Pin-to-pin contact begins about4mm before the hard face stop; feed must remain isolated until seat and latch are confirmed. The interface face seal compresses only in the last0.46mm, so this is not a dry-break sequencing qualification. Measure disconnected leakage and demate spill. Nominal seat bore remains22mm;2mm curtain area≈138mm² and poppet annulus reduce the coupling’s local flow section, while2.5mm tubing and the assumed1.7mm barb passage dominate this slow-flow rig.

## Servo margins

Adafruit publishes5.5kgf·cm at5V=0.5394Nm for SG-5010. Use50% of that,0.2697Nm, for the preliminary actuation budget; this is an assumed derating, not a continuous-duty torque rating. Stall current and actual angular range are not published on that page. Measure both and use a current-limited separate servo supply. [Adafruit#155](https://www.adafruit.com/product/155)

Carriage:18mm crank radius gives36mm travel, sufficient for30mm capture plus4mm poppet opposition and2mm approach clearance. At midstroke the half-stall force is15.0N. The larger mating load occurs close to the crank dead center, where effective moment arm is smaller. `mating_force_envelope.json` evaluates the last4mm using both spring loads,6N total friction allowance, and a linear0→60N face-seal compression over the final0.46mm. Feed is closed and the coupling drained while mating, so that envelope is unpressurized. The minimum sampled half-stall margin is about1.4. This advantage requires correct phasing: mated pin at shaftX−18, retracted atX+18. Set a physical face stop and command limits; never use sustained stall as the stop. If measured seal force exceeds60N or sliding resistance exceeds6N, this budget is invalid and the mechanism/preload must change.

Latch: the105mm nose lever closes1° past dead center against fixed stops. With a90N retained load, effective opening arm105sin1°=1.833mm, giving0.165Nm plus0.03Nm assumed bearing/clamp friction. Half-stall margin0.2697/0.195≈1.38; full published torque margin≈2.76. The stops carry the closed load. Opening to30° moves the nose clear for retraction. Maintain carriage preload while moving the latch; isolate/drain before opening. These margins depend on actual hard-stop position and hook keying. Block each hook separately and prove that the latch switch cannot assert with either blocked.

Pinch:9435K125free22.225mm, rate10lbf/in=1.7513N/mm. Closed installed16.225mm gives10.51N;6mm lift compresses to10.225mm and21.02N,1.157mm above catalog compressed-length limit9.0678mm. At a6mm cord-anchor radius, maximum moment≈0.126Nm, half-stall margin≈2.14. Closure margin is1.31 against an8N measured-tube-force acceptance limit. The8N value is an assumption to test on actual tubing, not a sourced silicone property. Adjust positive stops to close the2.5mm lumen without cutting the4.7mm-OD hose. Inspect after20cycles.

All geared servos may hold position without power. Spring-return jaws can remain held open by a taut cord and unpowered gearbox. Commanded-close/watchdog response and power-loss closure are different tests. Keep the manual reservoir clamp available; no passive power-loss safe-state claim is made.

## Plumbing, conditioning and bench acceptance

The two-valve layout uses a raised fill branch: manifold→150mm rise→free discharge above receiver; drain is a short downward branch to waste. A free discharge is necessary to prevent a primed siphon bypassing the raised crest. During conditioning, waste flow must hold manifold head below the150mm crest. This depends on actual upstream/downstream hose resistance and receiver/waste heights. Prove zero receiver mass gain while drain is open at the highest permitted source head. Otherwise shorten/lower the drain, adjust the crest within the available head or add a fill selector before claiming autonomous conditioning. CAD alone cannot prove the branch split.

Clamp the wall probe to the metal spool, not merely into the outlet water stream. Gate on wall<15°C for5s; test temperature lag and the installed thermal contact. Use a50mL initial fill target and the calibrated4541 platform; compare against an independent reference scale during acceptance. Container/tray envelopes remain assumptions pending measurement. Verify that the tray holds the entire500mL source with hardware displacement and that no electrical connector is in a spill path.

Bench acceptance from the existing project plan: disconnected and mated leakage≤1mL/min; demate spill≤5mL; five repeats per capture condition, ≥90% success;20cycles, ≥18complete; false seat or latch must suppress every feed-open command; physical watchdog isolation≤2s. These are proposed class tests, not achieved results. No flow-rate or pressure-drop comparison to the flight LOX CFD is claimed for the narrow tubing.

## FIX1 switch and electronics acceptance

COM/NO retains asserted-on-contact logic with a pull-down input: open or broken wire reads false. SPDT NC can optionally be read on a second input to reject equal NO/NC readings after debounce, but needs extra wiring/firmware and cannot prove either hook is clamped to the shaft. No firmware change is delivered. Test an unplugged wire, blocked hook, and partially seated coupling before feed is enabled.

Slots are8mm long ×2.7mm wide on9.5mm centers (ASSUMPTION M2 screws with washers); available screw-center adjustment is5.3mm. Set seat only in the last~1mm, home only near36mm retraction, latch only at−1° against stops. Lever is shown free and overlaps its cam elastically; do not use switch bottoming as a hard stop. All new witness dimensions and trip/overtravel settings are ASSUMPTION pending continuity measurements. Check transitions both directions, allowable overtravel, compliance offsets and twenty cycles; record measured trip/release points. Test each blocked hook separately.

HUZZAH32 and815 share a tray but have independent mounting-hole standoffs at PCB undersideZ32. The header tops are open for vertical servo plugs. ASSUMPTION component and plug envelopes require dry fitting. Route I2C, USB and servo power toward+Y through dry-side tie slots; pass servo leads above the wall with strain relief and a wet-side drip loop. Keep the separate current-limited servo V+ supply,3.3V logic VCC and common ground. Verify no connector lies in a spill path before wet testing.

FIX1 generated evidence: `switch_state_checks.json` checks full-seat contact and release at2/6/36mm, home clear at0/18mm and contacting at36mm, and latch contacting closed but clear at30° open. These free-lever contact checks verify geometry, not electrical trip thresholds. All four regenerated renders were visually inspected. `export_checks.json` is now regenerated by verify.py each build.

## FIX2 load-cell and pressure acceptance

CAD checks actual beam/base/pan solids, nominal0.5mm overload gap,4mm pan-to-beam clearance away from its loaded spacer, board mounting patterns and sensor elevation. `fix2_checks.json` records nominal and stop-contact geometry. Screw threads, engagement and stiffness are simplified; received hardware must be verified. The5kg rating does not establish that printed posts protect the beam at0.5mm travel. Measure full-load deflection and vendor safe overtravel before setting/shimming posts; keep posts clear at working load. Test gradual loads with a reference scale; a sudden set-down can overload the beam before a rigid stop catches it.

Load-cell creep, thermal drift, hysteresis, eccentric pan loading, printed-support creep and HX711 noise/resolution are not proven by CAD. Tare with the actual empty receiver and dry pan, calibrate using known weights spanning0–500g of added water, repeat at pan edges, and log drift during a sustained full load and after unloading. Choose a measured allowable mass error for the50mL target before closed-loop use;5kg full scale does not imply50g accuracy. Wires, receiver contact with a wall, and discharge hose forces can corrupt mass readings. The receiver remains vented; no hose rests on it.

The MPRLS measures absolute gas pressure; subtract a fresh ambient baseline to obtain gauge pressure. Air-leg compression moves the water/air interface upward, introduces a water-column offset relative to manifold pressure, and adds compliance and settling lag to leak transients. Thus sensor gauge pressure need not equal manifold gauge pressure, even without a leak. At9.81kPa gauge and101.3kPa initial absolute pressure, an isothermal trapped-air volume shrinks about8.8%; use measured tube length/volume and interface height to characterize the actual system. Tube elasticity, temperature, condensation, trapped droplets, leakage and transient jets add errors. CAD cannot establish water exclusion or a leak-detection threshold. Sensor is above the600mm static source surface and behind the splash wall; verify that limit physically, secure mast/tubing, inspect the dry tube and do not operate tipped or with a blocked/pressurized reservoir.

Bench-test with reference pressure at several heads, record steady offsets and step response, and repeat a known small leak. Re-prime with dry air after service, with feed isolated and manifold drained; do not blow water toward sensor. Confirm air fittings hold pressure and water never approaches port. The0–25psi range and24-bit ADC do not establish sufficient accuracy for this rig's~1.42psi maximum gauge rise. No creep, overload, pressure-accuracy or wet acceptance test has been performed.

FIX2 final generated evidence: build.log reports successful full build; zero unresolved nominal/travel pairs, all42 STL edge checks pass, valid STEP reimport, all prints fit MK4. Six regenerated CPU renders were opened and visually inspected. Largest export7,658,681bytes. These are CAD/export results, not hardware acceptance.

## FIX3 fastener seating and checks (2026-11-07)

Four Ø8 sleeve clearances at PCD50 span localz12..15.5, with Ø3.4 screw-tip continuations toz16.5. Washer OD7 has0.5mm radial clearance. Nut AF5.5 x2.4 sits on the0.5mm washer. Local inner ligament is0.8mm (3.5mm high), then3.1mm beside the1mm-high tip clearance; tube wall elsewhere4.8mm. The6mm flange seating pad remains intact, and the continuous tube above the relief carries sleeve loads. This short ligament is a local clearance feature below the nominal structural wall target; strength/preload capability remains ASSUMPTION to dry proof-test. Wet geometry, PCD and seals are unchanged. M3x22 SHCS91292A801 leaves1.1mm beyond nut, exceeding one0.5mm full thread.

The pan's two loaded-end Ø8 recesses are3mm deep, leaving5mm under the head through the plate/spacer. M4x16 ISO7380 92095A194 heads Ø7.6 x2.2 finish0.8mm below pan floor; fixed-end heads finish0.8mm above base underside inside its existing3mm recess. Four actual screw external envelopes are included. Simplified nominal M4 thread cylinders intersect the cell's3.3mm tap-drill bores: four intended engagements, not clearance passes. Actual thread depth/bottoming remains ASSUMPTION; measure received cell.

Full build/verify passes: unresolved nominal/travel0/0 before and after; raw nominal overlap pairs13→17, exactly four new thread engagements. Scope increases7626→11476 rigid pair combinations before bounding-box rejection. Added screws/nuts/washers are included in nominal and B sampled-travel checks. `fix3_checks.py` independently checks exported seating geometry and confirms only sleeve/pan volumes changed among existing parts; it also records original sleeve clashes with the same new hardware as a control. All42 STL edge checks pass, STEP reimport valid, all prints fit MK4; switch and FIX2 tests pass.109 STEPs,18 drawing sets,6 CPU renders; largest export8,253,527bytes. Changed-part sheets and coupling/load-cell renders visually inspected. See `fix3_checks.json`, `fix3_print_delta.json`, `build.log` and `export_checks.json`. Physical tests are not claimed.

Matched-profile PrusaSlicer estimates: sleeve43.92→43.48g and5844→5836s each (qty2); pan39.85→39.81g and3539→3549s (qty1). `print_times.json` updates those two entries; aggregate totals retain the prior rounded baseline plus these deltas.

## FIX4 (2026-11-07)

Only the existing `insert_retainer` changes; six purchased M3x8 screws are newly modeled. Three5mm-wide radial windows localz50..52.4 accept DIN920 narrow headsØ4 x1.9 (McMaster[97710A114](https://www.mcmaster.com/97710A114/), 18-8 SS, $5.24/10, MEASURED2026-11-07). Inner-open shaft slots localz48..57 permit loading from the bore before fitting the retainer to the sleeve. The tabs and completez57..60 region are compared against the backup; seals, wet parts, inserts, cones, sleeve pilots and mating travel remain unchanged. Ordinary socket/low/button heads are too wide for the5.2mm wet-body/cone annulus with0.5mm clearance on both sides; outer flanges would require more surrounding geometry changes. Rear windows with narrow heads avoid both problems.

Heads bear atz50, finish at51.9 and sit8.1mm behind the interface. Screw tips atz42 give6mm pilot engagement and2mm blind-bottom margin. Minimum retained wall0.8mm is the outer ligament at the unchangedØ3.4 shaft hole. The former0.65mm inner ligament is removed, rather than retained as a thin wall. Seat web2mm; window roof to tabs4.6mm. These are geometry dimensions, not PETG strength or creep ratings. A head must touch its intended bearing seat; quoted free clearances exclude that seat and the same screw's shank. They include all other assembly parts, conservative full-cylinder heads and other screws.

`fix4_checks.py` compares the legacyØ5.5 x3 heads with the supplied backup, tests the new heads at nominal mate and straight6/18/36mm retraction, and additionally tests all combinations of0/2/4/6/8/10/12/18/36mm retraction, four5mm lateral directions and±1° B tilt about the original capture-test pivot (76 poses total). This extends the existing sampled set through retained-error endpoints; it does not assert that uncorrected offset cartridges can physically reach every endpoint or certify a continuous sweep. Nominal and sampled minimum free head clearance is0.5mm; intended bearing contact remains0mm. Confirm actual fastener dimensions, printed windows,5mm bridges, pilot engagement and seating before wet tests. Use a slim slotted driver and hand-tighten; the vendor warns that this drive tolerates limited torque.

Same-profile slicer estimates:9.89→9.66g and25m20s→23m25s per retainer,−0.46g and−3m50s total for two. CAD volume7986.473→7806.951mm³ each. Existing print estimates remain unchanged. See `fix4_print_delta.json`; newly modeled screw-envelope mass is not a measured hardware mass delta.

BOM.csv was diffed against `<scratch>/rigcad_pre_fix4_1107/BOM.csv`: **zero existing rows changed, zero removed; only `retainer_screw_M3x8_97710A114` added (qty6)**. Every old URL/date/notes field is exact. `fix4_bom_diff.json` retains every changed/added row. The package generator preserves existing BOM rows on future builds.

FIX4 final verification: legacy heads overlapped each opposite retainer67.8657mm³ and face insert1.08768mm³; all six new heads have0mm³ interference and0.500mm minimum free clearance at nominal and across76 poses (bearing contact excluded). Full build, verify.py and fix3_checks.py passed; unresolved nominal/travel counts0/0. All42 STL edge checks pass, assembly STEP reimport valid, all prints fit MK4. Current exports:110 STEPs,19 drawing sets and7 renders; largest export8,659,652bytes. Changed-part sheet, close-up, section and exploded renders visually inspected. Reports: `fix4_checks.json`, `fix4_step_diff.json`, `fix4_loading_path.json`, `fix4_print_delta.json`, `fix4_bom_diff.json`; successful full build log `fix4_build_final.log`.

## FIX5 (2026-11-07)

Changed existing geometry is restricted to pinch_frame, coupling_stand and B_stand. `fix5_checks.py` compares all pre-existing part STEP DATA sections, ignoring the export timestamp, and computes symmetric differences for changed geometry. Separate checks protect the pinch structure above its6 mm base, each stand's complete original ring bore, split and foot. The jaw, groove, roof screws, cones and original stand footprints retain FIX4 geometry.

Pinch: four Ø4.5 anchor holes now atX±20,Y28/38 on two14×24×6 mm ears centeredX±20,Y32. Ear edges spanY20..44, retaining the original65 mm width and giving68 mm overall depth. Conservative Ø7×4 heads sit on OD9×0.8 washers at baseZ6. Straight head-insertion and3 mm AF key paths are checked against all other rigid assembly parts, including fittings and neighbouring fasteners. The key is additionally enlarged by0.5 mm radially. Its nearest roof-edge allowance is4−3/√3=2.268 mm. Washer seat probes use radius5 mm (0.5 beyond the washer), and head probes radius4 mm (0.5 beyond the head). Intentional bearing contact and the same fastener's shank are excluded. Flexible hose routing remains a physical assembly check.

Stand clamps: Ø4.5 through alongY atX0,Z113 /77.5 local. Seat lugs OD11 start atY±10, terminate at flat planesY±18, and have matching OD11 exterior reliefs beyond those planes. Recutting the original bore preserves it exactly. At each bearing plane an OD9 washer has1 mm outer seat margin. Head/nut/washer envelopes enlarged by0.5 mm and the insertion paths are free of rigid collisions; straight3 mm AF key access on−Y and a10 mm OD nut socket with0.5 mm radial allowance on+Y are checked. Complete flat bearing seats avoid trying to support a9 mm washer on the original ring's4 mm-high outer ligament above the screw axis. These geometry checks do not establish printed clamp strength or preload.

Clamp hardware: two M4×45 SHCS91292A133,18-8 SS, headØ7×4,3 mm key, minimum threaded length20 mm. Direct McMaster product page $13.14/50, MEASURED2026-11-07.36 mm seat span+1.6 mm washers+3.2 mm nut=40.8 mm;4.2 mm/six full pitches project beyond the nut, entirely on the threaded end. Eight M4×16 SHCS91292A118 ($11.63/100, same measured date) with one washer each anchor the pinch frames. Their9.2 mm nominal HDPE engagement leaves0.8 mm before the10 mm subbase underside. Transfer-drill Ø3.3/tap M4×0.7 off the tray; confirm real screw length and thread grip. The subbase CAD remains unchanged. Its eight raw screw intersections are retained as assembly transfer-tap engagements, not suppressed or called head clearances. No other new collision classification is added.

Same-profile print deltas: pinch_frame +3.20 g/+373 s each, qty2; coupling_stand +0.29 g/+99 s; B_stand +0.28 g/+105 s. Total+6.97 g/+950 s. Existing estimates for every other print remain unchanged. New bought-hardware envelope mass39.185 g uses assumed7.93 g/cm³; no physical mass or build test is claimed. `fix5_print_delta.json` records exact before/after slicer settings and CAD volumes. Production print orientations/support guidance remains in PRINTS.csv.

Report only: `fix5_other_holes.json` gives12 unusable PCB attachment bores,10 in electronics_mount and2 in pressure_sensor_mount. All are PCB-derived Ø2.5 clearance holes closed by4 mm of solid base, with no nut access/pocket. An M2 shank penetrating only0.5 mm past the bore bottom intersects1.571 mm³ of base; an AF4×1.6 M2 nut at the bore bottom intersects14.316 mm³. These are clearance copies from Eagle, not specified self-tap pilots. Intended housing/roof pilots, hose routes, sliding-pin/shaft bores, FIX3 screw-tip continuations and FIX4 side-loaded heads are excluded or reviewed separately. Slot arc extrema in the automatic screen do not identify actual switch screw centers. No part was changed for these findings.

The exact BOM diff is in `fix5_bom_diff.json`: no existing row or note may change, no row may be removed, and existing order is checked. Only four new hardware rows are appended. New washers/nuts retain unverified price/standard-envelope labels.

FIX5 final verification: full build, verify.py, fix3_checks.py, FIX4's76-pose regression and48 FIX5 access probes passed. Unresolved nominal/travel overlaps0/0 before and0/0 after. Raw nominal pairs23→31: eight new nominal M4 engagement cylinders in the assembly transfer-tapped subbase; new head/washer/nut seating overlaps0. Pinch control overlaps per hole: head104.583→0 mm³, washer30.735→0 mm³. Both clamp sides: head87.614→0 mm³, washer33.104→0 mm³; conservative nut-cylinder control96.652→0 mm³. At least0.5 mm free clearance is tested independently of intended bearing contacts. Both frames have50.5 mm minimum lateral tray margin. All42 STL edge checks pass, assembly STEP reimport valid, all prints fit MK4.114 STEPs,23 drawing sets,8 renders; changed sheets and FIX5 render visually inspected. BOM: zero existing rows changed or removed; four hardware rows added. Successful log: `fix5_build_complete.log`; scope/results: `fix5_checks.json`, `fix5_final_audit.json`; complete BOM row values: `fix5_bom_diff.json`.

## FIX6 — bearing coverage, drive and inserts

build.py and verify.py share an explicit deformable predicate: installed_ring_*, installed_seat_ring_*, *spring*, hose_route_* and exact compliance_grommet. fix6_exclusions.json records both instance lists; an assertion requires their difference to be exactly the two bearing towers. The corrected pair checker includes both towers. verify.py checks carriage displacement0..36mm every3mm. fix6_checks.py independently recreates before/after BReps, reproduces every supplied clash, reports every newly exposed bearing pair, checks24 crank poses at15deg with corresponding yoke motion, and checks head/key/nut-tool paths at every3mm travel. The headless dowel press interference remains quantified and explicitly classified; no collisions are silently zeroed.

Six changed existing geometries are audited against fix6_before/build.py; historical FIX3/FIX4/FIX5 scope checks defer only these named parts, keeping their seating, access and protected-region checks. FIX6 verifies all12 Ø3.0 board bores and their depths. See fix6_checks.json for volumes and sampled limits, interference_review.json for full nominal classifications, travel_checks.json for travel results and FIX6_REPORT.md for final results and open issues. Fit samples are not a continuous swept-volume, strength or physical retention test.

FIX6 final:0 unresolved nominal/travel clashes;24 crank poses at15deg and78 fastener-access probes pass. All twelve insert bores verified. No additional open clashes. Full results and all five supplied before/after volumes are in FIX6_REPORT.md and fix6_checks.json.

## FIX6B

Only `hose_route_feed_to_B` geometry changes. Nominal endpoints remain (-240,-80,43.5) and (78,0,110); OD4.7/ID2.5mm is unchanged. New waypoints: [[-240, -80, 43.5], [-220, -80, 43.5], [-190, -89.375, 43.5], [-190, -60, 43.5], [-190, -25, 43.5], [-190, -25, 170], [98, -25, 170], [98, 0, 130], [78, 0, 110]]. The approach to the feed pinch station clears the manual clamp corner and enters the channel at Y-89.375; the path exits along its channel toward Y-25, rises to Z170 and returns above the latch shaft. All held geometry (logo, cradle Ø117, receiver ring, mast sockets) and all printed parts remain unchanged; print mass/time delta is zero.

Nominal straight-span centerline length: **463.840 → 605.760mm**, delta **+141.920mm**. BOM/ASSEMBLY specify cut-to-suit hose, with no route-specific cut length, so BOM.csv is byte-identical and ASSEMBLY.md has no cut-number change. This length is the schematic polyline length, not a production cut length including barb insertion, bend smoothing or slack.

Smallest existing modeled corner radius is **0mm**: the existing routes are compounds of straight hollow cylinders with sharp, unfilleted corners. FIX6B retains that representation and the same 0mm minimum; no physical allowable bend radius was specified by the existing CAD. Assemble with gradual supported bends and cut to fit; zero is not a silicone-tube bend specification.

`fix6b_checks.py` records every hose-route/rigid-instance nominal gap, sampled stroke gaps and actual intersection volumes in `fix6b_checks.json`; `FIX6B_HOSE_AUDIT.md` lists every pair closer than1mm, including intended contacts and retained open findings. Spring guides are included as rigid despite the historical *spring* exclusion. Carriage stroke is +X, 0..36mm every3mm. The last three feed-route waypoints follow B by the stroke displacement; upstream waypoints remain fixed. Other schematic routes remain fixed. This is an explicit sampled slack-path model, not a flexible-hose simulation or continuous clearance proof. Its polyline length grows36mm over the stroke; provide at least that additional working slack when cutting to fit, while keeping the actual supported bends clear.

The supplied FIX6 baseline segment overlaps were17.76mm³ at carriage_yoke and51.41mm³ at the x100 yoke screw. The measured new nominal/stroke overlaps are tabulated below.

The feed route's minimum free clearance over all13 poses is **3.1320mm**, at `servo_SG5010_79`. The feed pinch frame/jaw/nose and B feed barb are intentional channel/squeeze/attachment contacts; these contacts are reported separately, without claiming3mm at an attachment. A literal3mm gap from every rigid part including the barb attachment is incompatible with the preserved endpoint.

|Rigid instance|Nominal gap(mm)|Stroke minimum(mm)|Maximum overlap(mm³)|
|---|---:|---:|---:|
|guide_rod_37|77.6441|77.6441|0.0000|
|guide_rod_38|77.6441|77.6441|0.0000|
|rail_end_39|60.8771|60.8771|0.0000|
|rail_end_40|135.4341|106.1228|0.0000|
|carriage_plate_41|46.3383|46.3383|0.0000|
|carriage_yoke_55|57.1185|57.1185|0.0000|
|fix6_yoke_screw_M4x25_57|72.5460|72.5460|0.0000|
|fix6_yoke_nut_M4_58|82.7933|82.7933|0.0000|
|fix6_yoke_screw_M4x25_59|75.4307|75.4307|0.0000|
|fix6_yoke_nut_M4_60|84.9527|84.9527|0.0000|
|latch_bearing_minus90_64|65.0117|41.7720|0.0000|
|feed_frame|0.0000|0.0000|0.0311|
|feed_jaw|0.1902|0.1902|0.0000|
|feed_nose|0.0000|0.0000|102.7120|
|B_feed_barb|0.0000|0.0000|0.7337|

Only feed_to_B is rerouted. All other hose findings are retained and enumerated in FIX6B_HOSE_AUDIT.md. Geometry face signatures verify every other part definition unchanged against fix6b_before/build.py; BOM bytes are checked against fix6b_before/BOM.csv. Historical FIX3/FIX4/FIX5/FIX6 scope assertions defer only this hose to the new audit. package.py includes the audit in build_manifest.json.

Independent nominal STEP reimport checks in `fix6b_step_check.json` confirm zero overlap and matching direct/segmented distances for the yoke, both screws, both nuts, bearing tower, manual clamp and feed servo. Reproduce with `python fix6b_step_check.py`.

Rebuilt STEP assembly and individual parts, printed STLs, shop drawings and all renders using build.py without skip flags. The full run, including verify.py travel, FIX2, FIX3, FIX4, FIX5, FIX6 and FIX6B, is recorded in fix6b_build_release.log. No git commits.

Context checked: in-folder FIX6/FIX6B instructions, FIX6_REPORT.md, README.md, CHECKS.md, ASSEMBLY.md, BOM.csv, build/package/drawings/verify scripts and historical check scripts; in-folder FIX6B source/BOM snapshot.

## FIX7 — mast stability, joints and hose routes

FIX7 starts from the in-folder FIX6B geometry saved in `fix7_before/`. No git commit was made. All printed definitions, including the existing reservoir cradle, receiver ring/pan, STEP-logo/capture geometry and both mast sockets, retain their complete FIX6B face signatures. The held Ø117 cradle change was not made. Neither mast moves; all hose endpoint coordinates, bottle position, water-surface limit and sensor elevation remain unchanged.

The reservoir mast now uses ordered 9008K12 **19.05 mm square ×420 mm** stock. Its separate 6061 foot is **196 ×220 ×10 mm**, offset under the bottle: world support edges X−284/−88, Y−125/+95, underside Z15. R13 reliefs clear the existing two subbase feet by3 mm. The plate fits within the existing tray walls, rests flat on the pan floor and makes no tray holes. Its top atZ25 touches the existing wet-subbase underside; install the foot before placing that subbase. Post top remainsZ445. The support corners remain intact after the foot reliefs.

Using actual machined CAD volume at2700 kg/m³, the mast/foot restoring mass is 1.5488 kg. Add600 g water,60 g bottle and30 g cradle at the specified50 or75 mm X offset. A2 N horizontal push at worldZ600 acts585 mm above the tray floor. For every direction, subtract Fh/W from each rectangular support-edge CG distance. The minimum with-push margins are **24.27 mm at50 mm offset** and **31.97 mm at75 mm offset**; both exceed15 mm. This is a static rigid-body tipping calculation. Minimum friction coefficient against sliding is 0.091; clean/dry the contact faces and verify against sliding before use.

Reservoir post-to-foot joint: one M5×16 SHCS from below, Ø5.5 through foot and underside Ø9 counterbore5.5 deep. Its Ø8.5×5 head sits0.5 mm above the floor. Remaining foot web4.5 mm gives **11.5 mm post thread engagement**. Tap M5×0.8 full14 mm, drill16 mm; screw bottom margin4.5 mm. A3×10 dowel at post-local(+6,0) engages4 mm in the foot and6 mm in the post to prevent rotation. Select a light press fit in the foot and slip fit in the post; screw preload holds the post against the foot.

The pressure mast uses ordered 9008K78 **9.525 mm square ×632 mm** stock on its existing32×32×6 foot. Its top remainsZ650. One **91292A117 M4×12** end screw seats in underside Ø7.5×4.5 counterbore, head recessed0.5 mm. Remaining foot web1.5 mm gives **10.5 mm engagement**; tap full12 mm/drill14 mm. A1.5×6 dowel at post-local(+3.2,+3.2), world(23.2,178.2), engages2 mm foot/4 mm post. The corner offset clears the screw head; minimum pin-to-head nominal gap is0.275 mm and post edge ligament0.8125 mm. Press only into the foot, with a slip fit in the post.

Pressure-foot anchors use **two already ordered91292A122 M4×25 screws and94150A335 nuts**, at(8,163),(32,187). From head to nut:0.8 top washer +7 spacer +6 foot +5.5 remaining plywood +0.8 bottom washer +3.2 nut =23.3 mm, leaving1.7 mm beyond the nut. Spacers are machined OD10/ID4.5×7. The12 mm plywood gets Ø4.5 through holes and **underside Ø12 counterbores6.5 deep**, wholly in the dry strip. Nuts sit atZ2.5–5.7, washersZ5.7–6.5 and screw tipsZ0.8, so the bench contact remains flat. The ordered25 mm screws are used without cutting or purchasing a different anchor length.

The unanchored pressure foot fails the2 N top-push case, so its anchors are mandatory. A50 g board/bracket/tail allowance is placed at(48.89,168.89,657.5). A360-direction anchor-load calculation gives worst required uplift **54.77 N**. Through-nut/washer bearing must sustain the specified100 N per-anchor verification load; this is an assembly acceptance load, not a catalog plywood strength rating. With only the plywood base at an assumed500 kg/m³, pressure mast and50 g load counted, the anchored system's worst tipping margin is **97.15 mm** under the2 N push. Other rig masses are omitted conservatively. Verify the finished base mass is at least1.439 kg; otherwise recalculate. The10.5 mm pressure_sensor_mount socket remains unchanged: radial clearance is0.4875 mm, and its M3 radial clamp needs0.2375 mm more reach than for the old10 mm post. No socket modification is required.

All FIX6B OPEN route/rigid pairs are mapped to current results in `fix7_checks.json`. Source, feed, waste, fill and pressure-air routes change. The feed route keeps its FIX6B clamp approach and replaces the long rectangular overhead detour with two sloping overhead spans; A-to-spool and spool-to-manifold remain geometrically unchanged. Every hose/rigid pair is checked at relevant0–36 mm carriage positions every3 mm. Conservative AABB lower bounds certify distant pairs; potential near pairs use exact BRep distances and actual intersection volumes. **Minimum free clearance is3.0240 mm**, after trimming only the explicitly listed bounded attachment/channel regions. Raw distances and overlaps are retained, including intentional tube squeeze/port contacts. `FIX7_HOSE_AUDIT.md` and the refreshed `FIX6B_HOSE_AUDIT.md` show the local contacts; `fix7_checks.json` contains every pair, mask and pose.

The source now leaves the vessel through its open top, clear of the unchanged cradle and inlet probe, then approaches the manual clamp along its Y channel. Prime and secure this over-rim siphon before gravity operation; filling the reservoir alone does not prime it. Keep its crest and vessel position at the modeled height. The first waypoint remains the original bottom outlet/intake interface at(−210,−20,408); its small overlap with the simplified vessel floor is explicitly retained as a terminal port/intake envelope, with zero cradle overlap. Use a pickup fitting with side openings/standoff so the tube cannot seal against the floor; this terminal interface is not a3 mm free span. The existing assumed bottom bulkhead on the BOM is not required for the over-rim supply; keep any actual bottom port sealed. Do not drill the pan or revise the cradle. The manual clamp's frame anvil proximity0.15 mm and screw-tip proximity2.15 mm occur only within the local tube/jaw channel; there is no crossing of the roof, nut or screw body. Outside the listed contact masks every rigid part has at least3 mm free clearance.

Waste enters its pinch channel from the right, traverses along Y, then rises clear of the tee into the open waste vessel. It no longer crosses a frame wall or servo cradle. Fill passes around the spool/probe clamp before entering the open receiver. The pressure line turns away from the wall probe before rising on the dry side, misses the mast and retains a high loop above the sensor port. Keep its rising air-filled leg dry. Contact masks include only the manual clamp local channel, feed/drain pinch entry lips/jaws/noses, existing barb ends, reservoir terminal pickup and MPRLS port; they are not whole-part exemptions. The exact masks and raw overlaps are reviewable in JSON.

|Route|Centerline mm|Barb allowance mm|Travel allowance mm|Minimum cut allocation mm|
|---|---:|---:|---:|---:|
|source_to_clamp|673.927|10|0|683.927|
|feed_to_B|527.454|10|36|573.454|
|A_to_spool|35.000|20|0|55.000|
|spool_to_manifold|50.362|20|0|70.362|
|waste|405.710|10|0|415.710|
|fill|216.041|10|0|226.041|
|pressure_air_leg|667.205|20|0|687.205|

Centerline total **2575.700 mm**, plus100 mm for ten barb ends and36 mm feed-stroke slack, gives **2711.700 mm**, below2800 mm by88.300 mm. Rounding each allocation upward to a whole millimetre uses2715 mm. Each route is under1 m; cut one route from each of the three1 m bought lengths according to the nesting below, not by summing unrelated nominal spans. Rounded bends can shorten these sharp schematic polylines, but they must stay within the checked corridors; no physical minimum bend radius is supplied by the tubing vendor here. Reserve the36 mm feed slack so the moving end cannot tug on the B barb. The free-distance audit uses the FIX6B sampled feed deformation and does not prove a continuous flexible-tube sweep.

Print delta: **0 changed printed parts,0 g and0 print time**. Complete printed-part face signatures and the print schedule remain unchanged, so no new slicing estimate is needed. PRL delta: replace the small reservoir foot with the196×220 plate; machine its reliefs/end-screw counterbore/dowel hole; cut the reservoir post to420 and drill/tap its end. Cut the pressure post to632 and drill/tap its end; add its foot counterbore/dowel hole. Drill/counterbore the two dry plywood anchors and turn two7 mm spacers. Wet-cartridge machining is unchanged. No machining-time or material-price quote is asserted.

BOM: only `base_plate`, `reservoir_mast` and `pressure_sensor_mast` existing rows are edited. Every other existing row is byte-identical, in the original order; dedicated new joint hardware/spacer rows are appended. New M4×25/nut rows allocate already ordered stock and do not request another purchase. The immutable FIX6B source/BOM/inventory snapshot is in `fix7_before/`.

Reproduce with `python build.py`. Rebuilt STEP assembly/parts, printed STLs, shop SVG/PDF sheets and renders include `renders/fix7_masts.png`. The full release run is `fix7_build.log`; the new audit is `fix7_checks.json`. `fix6b_checks.py` delegates to this stricter all-route audit in a FIX7 build. Historical FIX3/4/5/6 scope checks defer only the listed FIX7 geometry and BOM rows to the new face-signature and byte-preservation checks, while retaining their feature/access/functional assertions.

Context checked: in-folder FIX6/FIX6B/FIX7 briefs, README.md, CHECKS.md, ASSEMBLY.md, BOM.csv, FIX6_REPORT.md, FIX6B hose ledger, build/package/drawings/verify scripts, historical check scripts and the current FIX6B snapshot; no project context outside this folder was used.

Tubing cut nesting (whole-mm allocations, including barb/travel allowances):

- Bought1 m piece1: source_to_clamp 684 mm + A_to_spool 55 mm + spool_to_manifold 71 mm = 810 mm.
- Bought1 m piece2: feed_to_B 574 mm + waste 416 mm = 990 mm.
- Bought1 m piece3: fill 227 mm + pressure_air_leg 688 mm = 915 mm.

## FIX8 — manifold support and clamp anchors

Starts from the current FIX7 state saved in `fix8_before/`. Only the manifold, wall-probe clamp and manual frame definitions change. One 6061 bridge and dedicated hardware are added. Two rod and two nose instances receive seating corrections described below. All other existing part face signatures, the manifold pose, ports, every hose waypoint, STEP logo/capture parts, cradle (no Ø117 change), receiver ring/pan and both mast sockets remain unchanged. The FIX7 over-rim siphon decision remains in force. No git commit was made.

The manifold now seats at Z70 on a **35 mm 6061 bridge** bearing on the wet subbase at Z35. Its right-side foot avoids the load-cell base; the top bridge reaches both original mounting axes at world(-173,20),(-137,20). The original Ø4.5 mounting holes receive Ø8 counterbores16 deep from the top, leaving8 mm of web. Two already ordered **91292A118 M4×16** screws seat at Z78 and engage8 mm in the bridge. The left top pilot/tap passes through the10 mm bridge thickness; the right pilot is10 mm blind with8.5 mm full thread. Both give8 mm engagement and2 mm between the screw tip and the pilot exit/bottom. The counterbores stay clear of the axial gallery by at least3 mm of metal. Two base anchors at(-145,36),(-133,36) use the same ordered M4×16:6 mm foot +0.8 mm washer +9.2 mm engagement in assembly-transfer-tapped HDPE, with0.8 mm to the subbase underside. Do not penetrate the tray. The machined bridge is a single piece; no printed riser is required.

Exact bridge clearances: load_cell_base_clamp **3.000 mm**, receiver pan **12.000 mm**, receiver vessel **29.650 mm**. The bridge does not add a load path to the scale pan. All ten new screw heads have clear vertical tool paths with the jaw, thumb screw, spool, probe, and full plumbing geometry installed:80 mm straight reach, radius2.2 mm for M4 and1.6 mm for M3. M4 counterbore diameter8 clears the Ø7 heads by0.5 mm radially. Tool cylinders begin above each head and do not claim clearance through its intended bearing plane.

The wall-probe clamp has a5 mm integral base extension from Z94 to99, seated directly on the manifold top. Two M4×16 screws at(-163,23),(-147,23) pass through that5 mm base and engage11 mm in new blind manifold M4 taps. Drill13 mm, giving2 mm drill-bottom clearance; these holes are outside the wet galleries. The clamp is now a **two-piece saddle and removable cap**, with one full0.8 mm horizontal split centered on the bore axes at Z110. Two M3×16 screws at(-155,-10),(-155,15) bridge the split:10.6 mm upper cap +0.8 mm slit +4.6 mm engagement in the lower tapped half; blind pilot extends another1 mm. At0.20 mm cap closure, engagement becomes4.8 mm and drill-bottom margin0.8 mm. Bottoming-tap at least5.0 mm full thread in the5.6 mm pilot; check actual screw freedom before loading the probe. Heads are Ø5.5×3. These screws use the existing M3 allowance if stock is available; the exact M3×16 catalog item has not been verified.

Both bores retain their original nominal centers, diameters and object positions: Ø12.2 on Ø12 spool and Ø6.2 on Ø6 probe,9 mm center spacing. Under nominal vertical cap closure, **each needs0.20 mm to make opposed contact**, leaving0.60 mm of the0.8 split. Both objects settle0.10 mm toward the lower saddle within their original clearances as the cap closes; the closed-state BRep check verifies both upper and lower contacts. This is assembly seating motion, while exported nominal port/hose coordinates remain unchanged. Neither nominal bore stays loose when the other first grips, and the split does not bottom. Two screws permit cap tilt for actual diameter differences: with screw axes25 mm apart and bore axes9 mm apart, a0.10 mm closure difference between the bores requires about0.278 mm differential screw travel, within the0.60 mm nominal slit reserve. This is first-contact geometry, not a torque or flexural strength qualification. Tighten alternately and confirm retention of both actual parts before the split bottoms; do not crush the sealed probe.

The Ø12 spool and Ø6 probe remain nominally tangent at their original9 mm center spacing. Retain thermal paste at that interface and the aluminum saddles. The steel probe section overlaps the24 mm-wide clamp over17 mm; the remaining7 mm is its narrower cable envelope and is not claimed as Ø6 grip. The new full split changes the surrounding aluminum conduction area and adds a cap joint; it does not relocate or insert material between the probe and spool. Treat thermal time constant as unqualified and recheck response on the bench. Saw the0.8 mm split first, then fixture the two pieces with a0.8 mm shim and line-bore the matched bores; deburr without opening the bores.

The manual frame now has one integral24×26×6 mm ear, centered local(3,20), with two Ø4.5 holes at world(-240,-35),(-230,-35). Two M4×16 screws and0.8 mm washers give9.2 mm HDPE thread engagement and0.8 mm underside margin, following FIX5. Both screw heads and straight keys clear the installed thumb screw, roof, jaw and feed-pinch frame. The original jaw/anvil channel remains unchanged; source contact at that original channel remains intentional. Every new ear/hardware free span participates in the full hose audit.

All-hose audit: **3.0240 mm** minimum free clearance over the existing0–36 mm stroke sampled every3 mm; **0 failures**. Hoses and bounded contact masks are unchanged from FIX7. `fix7_checks.json` contains every pair, raw overlap and pose; the FIX8 release adds new support/hardware pairs to that same audit. `fix8_checks.json` checks exact joint-only thread overlaps, all new tool paths, unchanged FIX7 geometry and BOM bytes, and every rigid support path. Assembly STEP and individual STEP reimports are also checked. These are geometric/sampled checks, not continuous hose simulation or physical proof loading.

Matched-profile manual-frame print estimate: **14.54 g, 37m 32s**, versus FIX7 11.77 g, 31m 4s; delta **+2.77 g,+6m28s**. The only changed printed definition is the manual frame. Same existing PETG profile,5 perimeters,40% infill,6 top/bottom layers, without supports; original roof still needs production bridging/support judgment. `print_times.json` includes this delta; `PRINTS.csv` has the new envelope. No other print time/mass change is claimed.

PRL machining delta: one new single-piece6061 bridge (base, pillar, top bridge, two top M4 taps and two anchor clearances); manifold two mounting counterbores and two blind top M4 taps; clamp revised into two matched pieces with full split, two M3 pilots/taps, integral base and two clearances. Transfer-tap four M4 sites in HDPE during assembly, following FIX5 rather than adding a drilling pattern to the nominal subbase solid. No new lathe operations or tray holes. The bridge CAD volume is14182.1 mm³, about38.3 g at2700 kg/m³. Measured before/after machining volumes are in `fix8_checks.json`. No verified shop-time quote is available. BOM edits are limited to the three changed existing parts; every other original row is byte-identical and new rows are appended.

The no-floating audit uses exact contacts and explicit fastened joints to trace each rigid instance to the base plate. Hoses do not count as supports; actual springs and seals may transmit load. The two existing FIX5 M4x45 split clamps are explicit fastened edges:0.20 mm nominal radial sleeve clearance is removed by tightening their1.5 mm slots (nominal circumference take-up1.257 mm). These joints do not require a new FIX8 geometry change. It reports disconnected groups even when their members touch each other. Clear fit errors corrected: both guide rods sit0.10 mm lower on the existing rail-bore bottom walls; both pinch-nose dowels move20 mm along Y into the existing jaw bores and sit0.05 mm higher against their bore walls. Their original reversed-end placement left the dowels outside the jaw with only an end adjacent to its bore. Their part definitions and all port/hose geometry stay unchanged. Remaining findings follow; these are open issues rather than a blanket no-floating pass.

|Rigid instance|Nearest modeled part|Local gap mm|Gap to grounded assembly mm|Status|
|---|---|---:|---:|---|
|carriage_plate_41|carriage_yoke_55|0.0000|0.1500|Intentional sliding guide clearances;0.15mm to lower rod after seating rods. Nominal ports/poses retained; verify actual bearing seating.|
|carriage_crank_54|drive_pin_56|0.0000|0.1000|Existing supplied servo horn/retaining screw connection is specified but not modeled;0.10mm nominal gap.|
|carriage_yoke_55|carriage_plate_41|0.0000|10.8167|Bolted to carriage; shares guide/horn support conditions.|
|drive_pin_56|carriage_crank_54|0.0000|8.2759|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|fix6_yoke_screw_M4x25_57|fix6_yoke_nut_M4_58|0.0000|8.0000|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|fix6_yoke_nut_M4_58|carriage_plate_41|0.0000|8.0441|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|fix6_yoke_screw_M4x25_59|fix6_yoke_nut_M4_60|0.0000|8.0000|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|fix6_yoke_nut_M4_60|carriage_plate_41|0.0000|8.0441|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|switch_latch|latch_witness_flag_168|0.0000|0.8000|Existing switch screw/nut allocation is unmodeled; verify and install physical M2 joint. No rigid CAD path demonstrated.|
|switch_home|switch_mount_73|0.8000|0.8000|Existing switch screw/nut allocation is unmodeled; verify and install physical M2 joint. No rigid CAD path demonstrated.|
|reservoir_cradle_122|reservoir_envelope_123|0.0000|1.4750|Held22mm socket on19.05mm mast:1.475mm per side; no clamp fastening modeled. Socket unchanged by request.|
|reservoir_envelope_123|reservoir_cradle_122|0.0000|1.4750|Supported by cradle; shares the cradle socket support gap.|
|inlet_probe|reservoir_envelope_123|34.0000|37.8071|Existing inlet probe is suspended within reservoir; no rigid hanger modeled. Retained for an installation restraint design.|
|board_3965_128|pressure_sensor_mount_145|0.0000|15.2375|Board touches its mount; shares the unmodeled M3 mast-clamp joint.|
|pressure_sensor_mount_145|board_3965_128|0.0000|0.4875|Held10.5mm socket on9.525mm mast:0.4875mm per side. Existing transfer-drilled M3 clamp is required but hardware not modeled.|
|travel_washer_151|carriage_plate_41|0.0000|0.1500|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|travel_washer_154|carriage_plate_41|0.0000|0.1500|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|travel_washer_157|carriage_plate_41|0.0000|0.1500|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|travel_washer_160|carriage_plate_41|0.0000|0.1500|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|home_witness_cam_164|carriage_plate_41|0.0000|8.0160|Existing unmodeled joint/clearance; review the connected component in fix8_checks.json.|
|latch_witness_flag_168|switch_latch|0.0000|0.1000|ExistingØ4.2 witness bore onØ4 shaft leaves0.10mm radial gap; witness retention hardware not modeled.|

Disconnected group summary (each member and gap is listed above):

- board_3965_128, pressure_sensor_mount_145: nearest grounded gap 0.4875 mm at pressure_sensor_mount_145 to pressure_sensor_mast_132.
- carriage_crank_54, drive_pin_56: nearest grounded gap 0.1000 mm at carriage_crank_54 to servo_SG5010_52.
- carriage_plate_41, carriage_yoke_55, fix6_yoke_screw_M4x25_57, fix6_yoke_nut_M4_58, fix6_yoke_screw_M4x25_59, fix6_yoke_nut_M4_60, travel_washer_151, travel_washer_154, travel_washer_157, travel_washer_160, home_witness_cam_164: nearest grounded gap 0.1500 mm at travel_washer_157 to shoulder_bolt_M4_48.
- inlet_probe: nearest grounded gap 37.8071 mm at inlet_probe to reservoir_mast_119.
- switch_latch, latch_witness_flag_168: nearest grounded gap 0.1000 mm at latch_witness_flag_168 to latch_shaft_63.
- reservoir_cradle_122, reservoir_envelope_123: nearest grounded gap 1.4750 mm at reservoir_cradle_122 to reservoir_mast_119.
- switch_home: nearest grounded gap 0.8000 mm at switch_home to switch_mount_73.

Context checked: in-folder FIX5–FIX8 briefs, README.md, CHECKS.md, ASSEMBLY.md, BOM.csv, print schedules, historical reports, build/drawing/check scripts, FIX7 snapshot and current exports. No outside project context used.

## FIX9 — every rigid part physically held

Starts from FIX8 saved in `fix9_before/`. Final no-floating audit: **0 disconnected groups, 0 unsupported rigid instances**. Every rigid instance is listed with its exact contacts or modeled fastened joint in `fix9_checks.json`. Hoses do not supply support. FIX8's two pre-existing split-clamp joints and the FIX8 two-piece probe saddle retain their explicit closed-state joint treatment; the FIX9 closures use actual solids and fasteners. No git commit was made. This section supersedes earlier open retention findings and earlier socket/fastener notes.

|Closure|Modeled load path and retention|
|---|---|
|Reservoir cradle and bottle|19.55mm square socket on19.05 stock: **0.25mm per side ASSUMPTION, coupon-tune**. M4x40 cross bolt through the post at Z398 has its upper surface at the socket underside Z400, providing a positive stop. Second M4x40 at Z410 crosses socket and post, with a modeled M4 nut, preventing lift/rotation. Bottle bottom remains at Z408; removable rim capture at Z530, with two upright struts and two underside M3x22 screws, prevents escape. Source-side opening preserves hose clearance. Held ring diameter and bottle pose remain unchanged.|
|Pressure sensor|10.025mm square socket on9.525 stock: **0.25mm per side ASSUMPTION, coupon-tune**. M3x22 stop at Z620.5 supports sleeve underside Z622; second M3x22 at Z632 crosses socket/post, with M3 nut. Two M2x6 screws pass through PCB into modeled M2 brass inserts at Z647–650;3mm engagement and1.6mm screw-tip clearance to the floor.|
|Carriage and home cam|Existing Ø8.5 guide bores recentered up0.15mm; their lower surfaces now actually ride on the Ø8 rods at fixed carriage pose. Existing guide clearance remains above the loaded contact. Two modeled M3x12 screws attach the home cam's added foot to tapped carriage pilots.|
|Crank and servo output|Modeled supplied horn envelope, recessed central retaining screw/washer and two **M2x6** crank-to-horn screws; heads lie below Z84, clear of yoke underside Z85. The printed crank is the adapter to the supplied horn; no guessed printed spline is required.|
|Switches and witness flag|All three switches sit against their cheeks after +0.8mm Y seating. Each has two **M2x14 91292A835** screws and M2 nuts. Latch flag has an integral threaded radial boss and M3x12 screw bearing on the actual Ø4 shaft.|
|Inlet probe|Rim-mounted hanger reaches the original probe steel section at Z475–480. Its Ø6 bore and radial M3x12 screw retain the unchanged probe depth. Hanger bolts to bottle capture; capture bolts to cradle.|
|Other reaction/retention paths|All four servo ear sets have four M4x16 screws and M4 nuts each. Three horizontal cradles have integral mounting feet, six M4x16/washer anchors into HDPE. Latch cradle is bolted to a fixed reaction tower with pillar at X206.984, beyond home-cam maximum X199, and overhead arm above Z94 with two M3x16/nuts and two M4x16 HDPE anchors. Hooks and latch coupler have modeled shaft clamp screws. Both pinch cams have horn adapters, retaining screws and M2 through bolts/nuts. Seat witness cam is screwed to the floating plate with two M2x8 screws; upright shifts5mm toward +Y to clear crank, sensing tip unchanged.|

The cradle socket is locally relieved against the unchanged bottle envelope. Bottle-capture bolt heads install from underneath in open-sided counterbores: head bearing Z404, screw tip Z426, nominal6mm engagement in the printed strut pilot. Do not bury heads inside the upright. Cross-post bores are physical modeled holes, not assembly notes standing in for missing joints. Thread helices and sockets are omitted from screw envelopes; exact host/screw and screw/nut engagements are explicitly enumerated rather than globally exempting hardware.

Validation: **3.0254mm** minimum free hose clearance, ≥3mm over0–36mm stroke sampled every3mm; **0 hose failures**. Source/siphon waypoints remain identical. FIX9B adds barb insertion tails and discharge guides; its section below supersedes the original FIX9 hose endpoint and exclusion scope. `fix9_validation.json` reports **0 unexpected new nominal clashes**, exact original-part scope, all individual STEP reimports and assembly placed-solid bounds/volume agreement. `interferences.json` retains every positive nominal rigid overlap, including historical intended fits and explicit thread envelopes. `fix9_new_overlaps.json` reports every increase from FIX8; each has a specific joint classification. `fix9_travel.json` covers13 translation samples and24 drive poses at15° increments. Open hooks before carriage retraction. Home cam/lever contact above switch body Z69.2 is intentional compliant-lever actuation and is listed separately; no switch-body clash is accepted. `fix9_joint_contacts.json` independently checks actual guide contact at all13 travel positions, both positive stop shanks bearing under their sockets, all radial clamp tips touching their shafts/probe, and rim capture contact. These are sampled geometric checks, not continuous flexible-hose or strength certification.

Matched-profile print delta: **+74.37g, +4.981h** for installed quantities. Same existing PETG profile,5 perimeters,40% infill,6 top/bottom layers; support material enabled for both before/after comparisons. Supports are needed for the new overhangs; inspect slicer previews and accessible removal before production. `fix9_release.json` records each measured before/after estimate. Existing unrelated print estimates remain historical.

|Printed part|Qty|Before g each|After g each|Installed delta g|Installed delta minutes|
|---|---:|---:|---:|---:|---:|
|floating_plate|1|58.21|58.29|+0.08|+2.65|
|servo_cradle|4|22.85|21.41|-5.76|+32.53|
|carriage_crank|1|2.47|2.42|-0.05|+0.45|
|latched_hook_pose|2|9.55|11.41|+3.72|+18.07|
|latch_bearing_90|1|25.92|25.76|-0.16|+1.18|
|pinch_cam|2|2.03|1.99|-0.08|+0.27|
|reservoir_cradle|1|35.47|42.84|+7.37|+19.62|
|pressure_sensor_mount|1|12.83|13.10|+0.27|+1.12|
|seat_witness_cam|1|10.47|11.33|+0.86|+1.45|
|home_witness_cam|1|2.25|2.55|+0.30|+0.78|
|latch_witness_flag|1|0.52|0.76|+0.24|+0.40|
|latch_coupler|1|1.82|1.41|-0.41|-1.73|
|fix9_bottle_capture|1|0.00|38.82|+38.82|+118.77|
|fix9_probe_hanger|1|0.00|7.09|+7.09|+38.25|
|fix9_feed_horn_adapter|1|0.00|1.08|+1.08|+3.20|
|fix9_drain_horn_adapter|1|0.00|1.08|+1.08|+3.20|
|fix9_latch_reaction_tower|1|0.00|19.92|+19.92|+58.65|

PRL delta: reservoir mast two Ø4 cross bores at world Z398/410; pressure mast two Ø3 cross bores at Z620.5/632. Carriage guide bores move+0.15mm in Z, with two M3 tapped cam pilots; these changes require remachining/replacing that plate if already fabricated. Printed fixed +90 latch tower gains two axial head/tool bores and a Ø14.2×2mm-deep continuous screw-head rotation pocket at Y94–96. Latch shaft trims3mm to196mm so its end at Y99 clears the recessed horn retainer. Add eight M4 assembly-transfer taps in the HDPE for servo reaction anchors, using the existing FIX5 practice:6mm foot+0.8mm washer+9.2mm engagement,0.8mm to subbase underside. No tray holes. Other added reaction brackets and retainers are printed. No new lathe operation is required. Latch motion is additionally sampled through0–31° in `fix9_latch_motion.json`; both screw heads clear their modeled rotation pocket. No measured shop-time quote is claimed; before/after PRL solid volumes are in `fix9_release.json`.

Hardware rows are allocations against the existing ordered stock where identified; do not order duplicates of assortment allowances automatically. New insert candidate: **McMaster94180A307 UNVERIFIED**, M2 nominal OD3×3 heat-set envelope,2 pieces. Prices remain UNVERIFIED. Supplied horns/central retaining screws are now solids, not missing-hardware promises. TowerPro publishes the40.6×20.5×38 body and included Futaba-compatible arms/screws; its page does not dimension the supplied horn. The model uses an explicit assumed round-horn envelope OD14, hub ID6 and printed adapters with modeled screw attachment. Supplied central M3×6 retaining screw envelope and adapter transfer-hole pattern are ASSUMPTIONS; match the actual supplied horn/thread before fabrication. These assumptions qualify manufacturing fit, not the existence of a modeled retention path. Source: https://towerpro.com.tw/product/sg5010-4/ .

`BOM.csv` preserves every unaffected FIX8 row byte-for-byte and preserves original order. Only rows of changed parts receive FIX9 notes; added printed parts and dedicated hardware allocations are appended. `fix9_validation.json` independently checks this against `fix9_before/BOM.csv`. The logo, receiver ring/pan, held cradle ring diameter, bottle pose and source/siphon route stay in place.

Rebuild CAD and checks: `CRYOLINK_SKIP_RENDER=1 python build.py`. Omit the environment flag for the historical full render montage. FIX9 scripts replace revision-specific FIX3–FIX8 assertions that demanded old exact part signatures; those scripts/reports remain historical. Current release checks include original-protected signatures, all-pair nominal clashes, all-hose/stroke audit, base-connected contact graph, STEP reimports, BOM byte comparison, matched-profile print slicing and full drive travel samples.

Context checked: in-folder FIX8 report and snapshot, FIX5–FIX8 check/build scripts, README.md, CHECKS.md, ASSEMBLY.md, BOM.csv, print schedules and STEP/STL outputs. Work confined to this CAD folder; no outside project context used.

Review views: [reservoir and probe](renders/fix9_reservoir.png), [crank attachment](renders/fix9_drive.png), [latch reaction bracket](renders/fix9_latch_reaction.png). Updated fabrication sheets are in `drawings/`.

## FIX9B — hose ends held

All seven routes audited. All eight 5121K321 ends now have axial push-on sections covering local Z10–17.4: **7.4 mm per end** (three cone envelope). Source/manual clamp and pressure-sensor tail retain their existing held interfaces. The feed route begins at its overlapping continuation of source tubing at the manual-clamp approach; this is a schematic split of the same tube, not an open discharge. Fill and waste discharge guides are independent printed towers fastened to the fixed HDPE subbase with two ordered 91292A118 M4×16 screws each. Screw axes (world X,Y mm): fill (-238,-10), (-222,-10); waste (-53,96), (-37,96). The waste guide bore follows the existing 3/35 downward slope. Slide tubing through each closed Ø4.7 guide before installing the barb ends; check snug retention on the actual tubing. Transfer-drill Ø3.3 and tap M4×0.7 off the tray. Each 6 mm foot gives 10 mm screw engagement through the 10 mm HDPE; screw tips are flush with its underside. No tray penetration. Fill endpoint stays at Z170, **15.3 mm above receiver rim Z154.7**; waste endpoint stays at Z112, 5 mm above waste rim Z107. Preserve these air gaps. Guides do not load the receiver, scale or receiver ring.

|Route|Barb|Push-on mm|
|---|---|---:|
|feed_to_B|B_feed_barb|7.4|
|A_to_spool|barb_5121K321_98|7.4|
|A_to_spool|barb_5121K321_102|7.4|
|spool_to_manifold|barb_5121K321_101|7.4|
|spool_to_manifold|barb_5121K321_100|7.4|
|waste|barb_5121K321_106|7.4|
|fill|barb_5121K321_107|7.4|
|pressure_air_leg|barb_5121K321_105|7.4|

Full hose/stroke free-clearance audit: 3.0254 mm, zero failures. Independent exported STEP audit: 404 solids, **0 unreachable** at 0.02 mm or modeled joints; contact-only unreachable: 0. Hoses are included per solid, and every barb end has a positive checked cone overlap. See fix9b_checks.json. Existing FIX9 rigid support, clash, travel, latch, joint, STEP and print checks rerun.

|New print|Mass delta g|Time delta|
|---|---:|---|
|fix9b_fill_guide|+48.29|2h 5m 12s|
|fix9b_waste_guide|+22.04|1h 5m 22s|

Total print delta: +70.33 g, +3.176 h. Existing printed parts: zero delta.

Every existing BOM row remains byte-identical to FIX9; three dedicated rows appended. Logo, receiver ring, cradle and siphon decision unchanged. Context checked: in-folder FIX9 source, snapshots, BOM, README, CHECKS, ASSEMBLY and check/release scripts. No commits.
