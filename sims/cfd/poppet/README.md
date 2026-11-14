# Coupling CFD: LOX through the mated, open coupling (2026-11-01)

3D steady RANS (OpenFOAM 2412 simpleFoam, k-omega SST, wall functions) of the full wetted path
through coupling A + B as built by Codex (cad/out/coupling_a.step, coupling_b.step), both poppets open.

## Inputs
- LOX 90.19 K, 4 bar: rho 1141.83 kg/m3, nu 1.71e-7 m2/s, psat 101.35 kPa, dpsat/dT 10.6 kPa/K (COMPUTED, CoolProp).
- Mass flow 0.28 kg/s (ASSUMPTION, same as the line CFD in ../bend, ../straight). Line 22 mm ID, U 0.645 m/s, q 237.6 Pa.
- 66 mm straight stubs (22 mm ID) at inlet and outlet; their friction (~30 Pa) is inside the reported dp.

## Assumptions in the fluid domain (fluid.py)
- Mated seals are leak-tight: solid annulus r 18.3-30 mm, z 293-303 (undeformed O-rings in CAD leave slivers).
- The 22 mm line tube butts into the r 20 mm A socket (z 255-259.2 filled).
- Both coil springs removed (ground ends 0.28 mm from faces break the mesher). Hand estimate: 0.65 mm wire, ~220 mm per spring, ~0.25 m/s, Cd 1.2 -> ~6 Pa each, 12 Pa total.
- Guide spiders, poppets, stems, seats, plenum and side port are kept exactly as in CAD.

## Results (results.json)
| Mesh | cells | dp (Pa), iters 1500-2167 | min p below inlet (Pa) | subcooling to avoid flashing |
|---|---|---|---|---|
| h1 (1.0 mm) | 1.04 M | 1802 +/- 42 | 4425 | 0.42 K |
| h07 (0.7 mm) | 2.92 M | 1598 +/- 40 | 3563 | 0.34 K |
- h1 run to 4000 iters: 1780 +/- 50 Pa (iters 2000-4000). Steady RANS settles to a small oscillation (+/- 3%), not a residual-converged state.
- Mesh study: 12.8% difference; Richardson estimate 1.1-1.4 kPa (order 1-2). Report dp ~1.6 kPa, upper bound 1.8 kPa.
- K on line head ~6.7-7.6; equivalent Cv ~8.2-8.6.
- Lowest pressure at B's outlet guide spider (z 352.6); highest velocity ~2 m/s at A's inlet step / spider.
- Mass flux on every cutting plane within 1.5% of 0.28 kg/s.
- Wetted volume 202 cm3; B outer pocket (r > 19 mm) 117 cm3 is nearly stagnant (< 0.1 m/s in section plot) = ~134 g LOX hold-up.

## Meaning
- dp is < 0.5% of a 4 bar supply: not a design driver.
- Flashing needs only ~0.4 K subcooling; at 4 bar / 90 K there is ~3 bar margin. Saturated LOX delivered at tank pressure would flash at the B spider.
- The B pocket is the finding: chilldown mass, vapor trap, and LOX vented at every demate. Candidate fix (via Codex): fill/turn down the B receptacle interior to r ~19 mm.

## Rerun
python -I fluid.py (cq_env) -> python -I mesh.py 1.0 h1/mesh.msh (sim_env) -> NP=16 ./mkcase.sh h1 -> ./run.sh h1 -> ./post.sh h1 -> python3 -I summarize.py.
run.sh preloads lib/mpich-3.3/libPstream.so (conda OpenFOAM RPATH points to the dummy Pstream).


## 2026-11-06 cold-fit revision

New h1c case: OpenFOAM2412 simpleFoam, same LOX/flow inputs,1.0mm global mesh,576413 cells. Mesh check PASS; solver completed4000 iterations. dp=2292.03 +/-51.19Pa versus old h1=1780 +/-50Pa; minimum pressure5820.34Pa below inlet; subcooling requirement0.5492K. Statistics use iterations2000-4000.

Nominal main wetted volume85.197cm3 versus202.3; connected B outer pocket r>19mm is0 versus117.1cm3. New retention-gland capacities are1.841cm3 each; if both admit LOX cold, nominal capacity total is88.880cm3 (ESTIMATE, not resolved gap flow). B gland capacity beyond r19 is1.710cm3 (~1.95g LOX allowance).

**Sampled-plane mass-flux check FAIL:3.45% maximum at z340 versus1.5% criterion.** Global inlet/outlet flux imbalance is0.08774%. Local interpolation/mesh convergence remains open. This is one revised mesh; the old12.8% mesh sensitivity remains relevant.

CFD-only assumptions: retention glands capped outside original r18 chamber to remove zero-thickness spring-contact ties; original two valve coils omitted as before (~12Pa hand estimate). BREP same-domain cleanup,0.05mm local minimum and curvature20; global H=1.0mm retained. Gmsh4.15.2/OpenFOAM2412 preserved video runtimes replace missing sim_env files. PurgeWrite disabled and forced decomposition removed to preserve outputs. h1/h07 retained. Rerun from this folder: ./h1c/run_revision.sh. Details: [h1c/results.json](h1c/results.json), [gland capacities](h1c/retention_capacity.json). Prior sections are historical.
