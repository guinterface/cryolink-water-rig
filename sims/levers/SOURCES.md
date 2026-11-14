# Source audit and assumption register

Sources opened and read 2026-11-04. Every simulation output is COMPUTED (our model). Experimental LN2 results below are not LOX module predictions. XML copies and extracted text are retained under sources/. Original FSW files and their hashes are retained by run.py in plant_snapshot/ and results.json.

## L1: coating and earlier film-to-transition boiling

Before: bare stainless tube with continuous flow, documented prior literature through 2018 and the matched baseline in the 2022 paper. New: Hartwig et al. (2022), *Nitrogen flow boiling and chilldown experiments in microgravity using pulse flow and low-thermally conductive coatings*, doi:10.1038/s41526-022-00220-9.

URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9363417/

Read full text through https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9363417/fullTextXML (the PMC web endpoint presented a captcha). Local line.txt includes full text and table contents.

Exact numeric excerpts, Results, “Effect of Teflon coating thickness”, Fig. 2 discussion: “68 and 46% propellant mass savings”; Methods, test sections: “average thickness per layer was ~15.12 µm”; Fig. 4 discussion: “76% reduction in propellant consumption”.

Mechanism read: the coating permits the fluid-facing surface to reach the Leidenfrost point before cooling all the metal, shortening film boiling. Authors explicitly report that inner wall temperature could not be reconstructed because coating contact resistances were unknown. Consequently no measured LOX effective rewet-superheat shift was available for this plant.

ASSUMPTION implemented: effective boiling-curve transition threshold 80 K wall superheat instead of the original Plant 40 K. Sweep 40, 60, 80, 100, 120 K. This represents early rewetting qualitatively; it is not a fitted Leidenfrost correlation, a measured temperature, or a resolved 60.48 µm coating. Coating thermal mass and pressure-drop changes are neglected. The quoted 68%, 46% and 76% are NOT imposed as savings.

## L2: fixed pulsed line chilldown

Before: continuous-flow baseline in the above 2022 paper (earlier studies reviewed through 2018). New: matched microgravity pulsing and coating/pulsing tests published 2022; pulsing itself also existed earlier (references 37–38 of that paper).

Same URL, Results, Fig. 3 discussion, exact numeric excerpt: “period of 2 s and duty cycle 10%”; also “period 3 s and duty cycle 10%”. Exact reported saving: “29–32% mass savings”. Fig. 4 uses coated flow at 3 s / 10%.

Implemented nominal period 3 s, duty 0.10. Period sweep 2–3 s is source-based; duty sensitivity 0.07, 0.10, 0.20 is an ASSUMPTION exploration (not a matched paper optimum). Plant has no residual fluid inventory or blowdown cooling during off time. We apply actual on/off flow and do not force the published saving.

## L3: adaptive measured-wall-temperature pulse schedule

Before: fixed period and duty as above (2022); the existing FSW controller uses 3 s / 10% and temperature-based stop, common.py and chilldown_controller.py. New: CryoLink study controller (2026 proposal), continuously changes duty as a function of measured maximum wall superheat. This study does not establish patent novelty.

ASSUMPTIONS: period 3 s; duty ramps linearly from 0.10 at 100 K above the effective rewet threshold to 0.50 at/below that threshold, clipped to that interval. Use a 5 K stop margin above receiver-pressure oxygen saturation and 30 s confirmation. The original 5 K/30 s rule is inherited from FSW, not claimed as new. Sensitivities: low duty 0.07/0.10/0.20; high duty 0.30/0.50/1.00; ramp span 50/100/150 K (ASSUMPTION). Sensor noise/lag are omitted; wall measurement is exact. This isolates scheduling under plant initial-temperature discrepancy rather than sensor robustness.

## L4: receiver spray with coating and pulse flow

Before: bulk injection/pool/ullage cooling; thin-film coating and spray pulsing compared with bare continuous spray in Chung et al. (2022). The present C0 bulk jet is a study baseline, not the experimental spray baseline.

New: Chung et al., *Cryogenic spray quenching of simulated propellant tank wall using coating and flow pulsing in microgravity*, npj Microgravity (2022), doi:10.1038/s41526-022-00192-w.

URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC8975813/

Full text also saved from https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8975813/fullTextXML.

Exact numeric excerpts, Table 2, row 2: duty “40”, period “1” (percent and seconds). Combined-effects paragraph: “113%” improvement (80 psig case), and “84%” (90 psig case). These are efficiency improvements, not mass-saving percentages. Corresponding efficiency ratios are 2.13 and 1.84; 113% does not mean efficiency exceeds unity.

Implemented 1 s / 0.40 receiver spray pulses. Sensitivity periods 0.5/1/2 s are ASSUMPTION; duties 0.4/0.5/0.7 are source test values but used here as a LOX sensitivity, not matched flight cases. Original Plant assumed spray conductance 3000 W/K is multiplied by assumed 1.5 effective enhancement (sweep 1, 1.5, 2.13). This mapping from measured efficiency to thermal conductance is NOT given by the paper and is explicitly an ASSUMPTION; a gain of 2.13 is merely an exploratory bound. Base conductance sweep 1000/3000/6000 W/K. Liquid enthalpy limits cap spray heat extraction, so a conductance multiplier need not yield the same efficiency multiplier. No separate receiver coating conduction model is claimed. C0 has spray conductance zero; its bulk wall exchange remains unchanged.

## L5: sizing / high mass velocity

Before: original Plant 16 mm ID, 5 m line, specified 0.24 L/s at 1 bar. New design motivation: Kim thesis (2025), *Cryogenic Flow Boiling Physics in Terrestrial, Partial, and Microgravity Conditions*, abstract, fifth part.

URL: https://hammer.purdue.edu/articles/thesis/_b_CRYOGENIC_FLOW_BOILING_PHYSICS_IN_TERRESTRIAL_PARTIAL_AND_MICROGRAVITY_CONDITIONS_b_/29429012

Exact quoted threshold: “700 kg/m²s”. Context: LN2 steady-state heated tube CHF gravity effect is mitigated above that mass velocity. It is not a fill-time formula and is not proof of gravity independence of LOX transient chilldown. The nominal original line already has roughly 1360 kg/m²s at 0.274 kg/s full flow. Duty-averaged flux and pulse-on flux are different.

ASSUMPTION sizing: nominal 20 mm ID, sweep 12/16/20/24 mm; length fixed. Heat-transfer area and metal mass scale with diameter; volume scales with diameter squared. Hydraulic CdA scales as diameter^2.5, an exploratory turbulent-resistance approximation; exponent sweep 0/2/2.5 includes no hydraulic gain. No pump/valve redesign cost is included. Larger diameter does not imply faster filling if a valve fixes flow, illustrated by exponent zero. Source supplies threshold only; time changes are calculated by our Plant under assumed hydraulic scaling. Settling acceleration is unchanged; sizing can shorten thrust duration rather than remove its need.

## N7 uncertainty

LeClair et al., *Nodal Modeling of Cryogenic Chilldown of a Liquid Hydrogen Transfer Line*, May 2025, slides 16–17 (PDF pages 16–17; slide 15 is chilldown TIME error, not wall-temperature error).

URL: https://ntrs.nasa.gov/api/citations/20250004455/downloads/LeClair_GFSSP_LH2Chilldown_SCW2025.pdf

Exact numeric excerpts, slide 16 MEAN row LH2-only: “22%” upstream, “28%” downstream. Slide 17 states mean wall-temperature errors with these values. These errors are LH2 MAPE, not distributions, LOX uncertainty intervals or failure rates.

ASSUMPTION MC conversion: per trial choose mean absolute fractional error uniformly 0.22–0.28, map to zero-mean Gaussian standard deviation using sqrt(pi/2), perturb initial line endpoint and receiver wall temperatures independently, interpolate line error, clip fractional discrepancies to [-0.45, +0.65]. Receiver use and initial-temperature-only proxy are additional assumptions. Fixed controllers retain nominal commissioned durations; adaptive controller responds to actual wall temperatures. Paired samples seed 261. Failure criteria are common pressure/volume/time limits, not an invented requirement that all fixed-schedule fills must fail if warm.

## No-vent-fill gate (bundled in ALL, nominal ablation recorded)

Before: ungated fill; new research evidence: Hartwig et al. RGCT (2023), slide 14 (PDF page 14), thermodynamic target-temperature model.

URL: https://ntrs.nasa.gov/api/citations/20230009068/downloads/Hartwig%20RGCT%202023%20SCW%20Presentation%20final.pdf

Exact numeric excerpts: “158 tests” and “100%” (failure classification). These do not establish the accuracy of our gate. The actual paper model needs tank/inlet energy-state and injection-efficiency treatment beyond a wall threshold.

ASSUMPTION implemented: require receiver wall <= oxygen saturation +5 K after conditioning, otherwise gate aborts. Sweep gate margin 0/3/5/10 K. Gate may be redundant with the conditioning stop rule. No savings from NASA’s classifier are imposed. gate_off result gives direct nominal ablation.

## Common inherited plant assumptions and study boundary

Read first: ../../fsw/README.md; ../../fsw/src/cryolink_fsw/cryolink_fsw/{plant_sim.py,common.py,chilldown_controller.py,lox_table.py,props.py}; ../../research/{MOAT_BEYOND_1104.md,PEOPLE_RESEARCH_1104.md,TECH_EDGE_1103.md}. These are local project context, not experimental validation. All original Plant ASSUMPTION comments are retained in plant_snapshot/.

Inherited examples: line initially 250 K, receiver 150 K, oxygen liquid 90 K, 4 kg line stainless, 3 mm aluminium sphere, 10/20 W line/receiver heat leaks, film/nucleate/liquid HTC 200/3000/1000 W/m²K, bulk wall/pool 300 W/m²K, gas wall 10 W/m²K, ideal gas ullage, assumed metal heat capacities, no two-phase resistance or fluid hold-up. Oxygen table header records CoolProp 8.0.0 (README says 7; code/table is used). No new property values were invented.

Study choices ASSUMPTION: volume sized at rho(90 K) to 1000 kg at 95% fill; target 1000 kg net liquid, all initial gas remains part of plant energy/mass accounting; all cases same 1 bar supply-receiver pressure target capped at 4.8 bar; vent hysteresis 3.5/3.0 bar; abort at 3.8 bar; 98% volume guard; 16000 s timeout; dt 0.1 s with C0/ALL half-step checks. Fixed schedules are commissioned by the same 5 K / 30 s wall rule, then frozen for MC. No tuning to user nominal results.

Settling: original PlantSim host response records common.SETTLING_G *1.05 = 1.05e-4 g (nominal spec 1e-4 g). Host initial mass 10000 kg and Isp 220 s are ASSUMPTIONS. No cited host/thruster was supplied. Rocket equation scaling is analytic: propellant scales linearly with host mass and approximately inversely with Isp at these small delta-v. Sensitivity may be evaluated at any mass/Isp directly; explicit 5000/10000/20000 kg and 100/220/300 s values are saved in results.json. This is extra host thruster propellant, separate from LOX loss. Settling covers the three simulated transfer phases; other mission operations are excluded uniformly.

# V2 source audit (2026-11-04–05; supersedes v1 implementation descriptions)

V1 above is retained as the audit trail for run.py/results.json. V2 files are run_v2.py, physics_v2.py, validation_v2.py, report_v2.py, README_v2.md and results_v2.json. All v2 outputs are **COMPUTED**. The experiment reproduction **fails**; none of the CryoLink results is experimentally validated. No published saving is inserted into a model coefficient. Only conventional-method comparisons are made.

## Resolved line-fluid inventory and off-pulse cooling

Source: the original 2022 LN2 line experiment, https://pmc.ncbi.nlm.nih.gov/articles/PMC9363417/ , Results, continuous versus pulse flow. Original full XML/text is retained in sources/line.xml and line.txt. It identifies continuing blowdown cooling after valve closure. It does not prescribe a liquid-retention fraction or a drainage law for CryoLink.

**ASSUMPTION with sweep:** each of five existing axial wall cells retains liquid up to `holdup_fraction * rho_l * V_cell`, nominal 0.25, swept 0/0.05/0.25/0.75. Incoming enthalpy and wall heat first determine evaporation and available remaining liquid; excess liquid and all vapor leave downstream. With inlet shut, remaining liquid accepts wall heat, vaporizes and also drains exponentially with nominal time constant 3 s, swept 0.3/3/30 s. Residual heat transfer uses inventory/tau divided by bore area as a flow-equivalent mass flux; this is an extrapolation, not a measured off-pulse correlation. Thermal HTC uncertainty is also swept by 0.5/1/2. Empty cells have no fluid cooling. Outflow continues to receiver or dump even with zero tanker inflow; it is not counted as a second tanker withdrawal.

For one cell, with old liquid inventory m_s and specific enthalpy h_s, incoming mass m_i and h_i, and wall heat Q dt, the energy relative to saturated liquid is E = m_s(h_s-h_l) + m_i(h_i-h_l) + Q dt. If E>=0, remaining liquid is max(0,m_s+m_i-E/h_fg); retained liquid gets h_l and outlet enthalpy follows conservation. If E<0, mixed subcooled liquid has h_l+E/(m_s+m_i), including retained inventory. Both mass and retained enthalpy are carried to the next step. Cell residuals check `m_s h_s + m_i h_i + Q dt = m_new h_new + m_out h_out`. This includes changes in the saturated-liquid datum as prescribed line pressure changes. It does not solve vapor holdup, transient compressible momentum, flashing pressure waves, p dV work, detailed two-phase pressure loss or a contact-line/free-surface geometry. No claim is made that this reduced inventory law reproduces the paper's apparatus.

The mean supply/downstream pressure is prescribed as in v1 (minimum supply-liquid saturation pressure); CoolProp saturation properties are cached at 0.1 bar pressure resolution. This spatial-pressure approximation remains an **ASSUMPTION**; the LN2 fixture sweeps mean test-section pressure 1.5/3.25/5.5 bar. Inlet liquid enthalpy is converted between CoolProp and the inherited oxygen-table datum by matching saturated-liquid enthalpies at local pressure. A changing datum is not counted as line heat. Incoming subcooled enthalpy is mixed with inventory; the heat-transfer driving temperature uses the incoming subcooled temperature when flow is subcooled and local saturation during off-time. This mixing/temperature closure is approximate, with the HTC multiplier sweep providing a model sensitivity rather than an error guarantee.

Numerical controls: v1's five wall cells, dt=0.1 s and 0.05 s C0/ALL check. Per-step heat removal is limited to half the wall-to-fluid temperature difference and available incoming/stored fluid enthalpy capacity. The latter includes incoming vapor superheat to the wall. No spatial-convergence or compressible-flow validation is claimed. A 0.5 K wall-superheat / 25 kg m^-2 s^-1 mass-flux / 0.05 quality cache grid is used only for nucleate HTC; all inventories, wall states and flux balances remain unrounded. The pressure rounding, nucleate lookup resolution and limiter are numerical approximations, not empirical material parameters. `checks_v2.json` contains numerical accounting/resistance checks.

## Actual radial conduction through the low-conductivity layer

Thickness source: read-only ../../cad/params.py `D_COATING_T = .05`, in mm; thus CryoLink nominal delta = 50 micrometers. The CAD file explicitly marks that thickness **ASSUMPTION**. It is not silently replaced by the experimental coating thickness. The 2022 paper Methods gives 15.12 micrometers per layer, with 0.7 micrometer per-layer uncertainty. V2 thickness sweep is 15.12/50/60.48/105.84 micrometers, covering one/four/seven layers and the CAD nominal. LN2 F28 uses four layers, 60.48 micrometers.

Conductivity source: NIST Cryogenic Material Properties, Teflon, https://trc.nist.gov/cryogenics/materials/Teflon/Teflon_rev.htm . Local copy: sources/teflon.html. For 4–300 K, log10(k) = sum(a_i [log10(T)]^i), with a_i = [2.7380, -30.677, 89.430, -136.99, 124.69, -69.556, 23.320, -4.3135, 0.33829], k in W/(m K). NIST gives 5% fit error against its data. This is evaluated at rounded mean metal/fluid temperature, clamped to its documented temperature range. These coefficients are a property fit, not newly fitted chilldown coefficients. At 100 K the computed conductivity is about 0.243 W/(m K).

**ASSUMPTION with sweep:** NIST Teflon properties are a proxy for the paper's black FEP paint, Teflon 959G-203, and the conceptual CAD coating. No composition-specific conductivity measurement was recovered. Conductivity multiplier is swept 0.5/1/2. Additional area contact resistance is nominal zero, swept 0/1e-4/5e-4 m2 K/W; the paper says interlayer/contact resistances were unknown.

For each coated cell, R'' = delta/k(T) + R_contact. The fluid-facing surface temperature for a fixed HTC is `T_surface = (T_metal + h R'' T_fluid)/(1+h R'')`, and heat rate is `A (T_metal-T_fluid)/(1/h+R'')`. The surface, rather than metal temperature, determines the rewet latch. The film-state surface estimate triggers wetting, then the wet-regime HTC and resistance determine heat flow. A wetting latch prevents stepwise film/nucleate chattering; dryout/rewetting hysteresis is not reconstructed. This is a real quasi-steady conduction layer, not an imposed 80 K coating rewet threshold. Thin-layer curvature, coating heat capacity and internal layer transient storage are omitted. These are thin-layer modeling approximations; thickness, conductivity and contact-resistance sweeps explore their conduction uncertainty but are not a direct test of missing coating heat capacity. A full transient coating layer remains a model limit. No resolved receiver-coating layer has been added; L4 remains the assumed effective spray enhancement described in v1.

## New source-visible boiling equations and explicit gaps

Primary source N7: LeClair et al., *Nodal Modeling of Cryogenic Chilldown of a Liquid Hydrogen Transfer Line*, SCW 2025, slide 9, https://ntrs.nasa.gov/api/citations/20250004455/downloads/LeClair_GFSSP_LH2Chilldown_SCW2025.pdf . Retained sources/n7.pdf, n7.txt and n7_page9.png. It reproduces the 2020 Darr–Hartwig LH2 correlation forms. The cited original is Darr and Hartwig (2020), *Two-phase convection heat transfer correlations for liquid hydrogen pipe chilldown*, Cryogenics 105, 102999, https://doi.org/10.1016/j.cryogenics.2019.102999 (bibliographic details checked against N7 reference 7; equations here are transcribed from the NASA slide).

V2 uses the following visible forms:

- Actual quality x_a = (1/x_e^K + 1)^(-1/K), K = 5.26e-5 Re_l,in + 0.1.
- Nu_DF = 0.015 Re_tp^0.8774 Pr_v,f^0.6112.
- IAF contribution: turbulent term 0.0151 (1-x_a)^4 Re_v^0.8 Pr_v^0.8, plus the slide's natural-convection term 0.06 [rho_v (rho_l-rho_v) g h_fg k_v^3 / (L mu_v (T_w-T_sat))]^0.25. The slide labels the sum Nu even though the latter term has HTC units. V2 treats that natural-convection term as an HTC and converts it to Nu with D/k_v before combining. This dimensional interpretation is explicit, not a verified correction from the original authors.
- Nu_FB = (Nu_IAF^0.75 + Nu_DF^0.75)^(4/3), h_FB = Nu_FB k_v/D.
- T_wet = 0.844 T_critical [1+0.060 We_D^0.208].
- Transition: linear heat-flux interpolation between q_FB(T_wet) and q_NB(T_DNB).

**ASSUMPTIONS with sweeps:** N7 is an LH2 vertical-upward-flow correlation; applying its functional forms to LN2 and LOX, especially residual liquid without forced inflow, is unvalidated. Saturated vapor rather than vapor-film properties are used. The HEM dynamic-viscosity approximation used in Re_tp is 1/[(1-x)/mu_l+x/mu_v]. The IAF/DF quality and flow inputs are local approximations, not the complete original non-equilibrium bulk-vapor solution. Rewet is capped at T_sat +100 K, swept +60/+100/+140 K. T_DNB = T_sat+15 K, swept +5/+15/+30 K. The Darr film HTC is reevaluated at T_wet for the transition endpoint. The alternate Purdue DFFB endpoint keeps its local-quality HTC. Property and low-flow approximations are explored with the 0.5/1/2 HTC sensitivity. Single-phase fallback uses max(3.66, 0.023 Re^0.8 Pr^0.4) k/D; 3.66 is the fully developed laminar constant-wall-temperature limit and the turbulent form is the Dittus–Boelter form reproduced in the Purdue/GRC paper. It is an approximate low-Re transition, not a validated correlation in every orientation. NB quality is bounded 0.001–0.95 for singularity avoidance; g is the simulated acceleration. Above the rewet point, each cell starts on the film branch and remains wetted after crossing its fluid-side threshold. The old v1 three-level curve (200/3000/1000 W m^-2 K^-1, 40/3 K thresholds) remains selectable as `boiling_model='legacy'` in a v2 same-inventory comparison, in addition to the unchanged full v1 files.

Important source distinction: N6 in the project research notes is Purdue/GRC **heated-tube** universal flow boiling; it is not the same correlation as the Darr et al. 2023 universal **chilldown** poster. The latter is retained as sources/universal_poster.pdf, https://ntrs.nasa.gov/api/citations/20230009910/downloads/SCW%202023%20Poster%20rev2.pdf . Its Eqs. 5–14 contain unspecified fitted coefficients and its conclusion says final fitting remains future work. Those coefficients have not been invented or presented as a deployable complete correlation.

The source supplying numerical nucleate coefficients is Hartwig et al. (2024), *A Continuous Flow Boiling Curve in the Heating Configuration Based on New Cryogenic Universal Correlations*, Applied Thermal Engineering 248, 123235. Author-hosted primary PDF: https://engineering.purdue.edu/mudawar/files/articles-all/2024/2024-07.pdf . Retained sources/purdue_curve.pdf/.txt and page8 image. The paper explicitly distinguishes heating and quenching configurations. Its NB database covers LHe, LH2, neon, argon, LN2 and methane, not LOX. Using its reduced-gravity saturated NB equations for oxygen and in transient quenching is an **ASSUMPTION**, explored with the HTC multiplier and DNB anchor sweeps. The full heating-configuration CHF/film assembly has not been substituted for a validated chilldown regime map.

Implemented equations (19)–(29), with SI units, at the local fluid-side superheat dT:

- h_NB = sqrt(h_SNB^2+h_ECB^2), Eq.19.
- For P/P_critical <=0.41: h_SNB = h_PB [1.36 tanh(g_e/g)] (1+1/Fr*)^7.48 [1/(1+1000 exp(Bo^2 We_fo))]^0.475. Above 0.41 use 1.2 instead of 1.36 and omit the final Bo/We factor, Eq.20. The multiplier is 10^3 = 1000 (verified visually in the PDF).
- We_fo = G^2 D/(rho_l sigma); Fr* = (G+800)^2/[rho_l^2 (g_e-g) D], Eqs.21–22. At 1 g the limiting denominator is floored numerically; the LN2 validation uses 0.05 g and CryoLink uses 1.05e-4 g.
- h_PB = 0.0015 Re_b^0.62 Pr_l^0.33 k_l/R_b, Eq.23.
- Re_b = pi/Pr_l [(rho_l/rho_v) Ja]^2, Eq.24.
- R_b = dT/(h_fg rho_v) sqrt(2 pi k_l rho_l cp_l sigma / dP_sat) (rho_l/dP_sat)^0.25, Eq.25.
- Ja = cp_l dT/h_fg, dP_sat = dT h_fg/[T_sat (v_v-v_l)], Eqs.26–28.
- h_ECB = 7 h_sp,l (1/X_tt)^0.39 (rho_l/rho_v)^(-0.34), Eq.29; X_tt = [(1-x)/x]^0.9 (rho_v/rho_l)^0.5 (mu_l/mu_v)^0.1. The paper permits the Dittus–Boelter base instead of Gnielinski at Re>3000; v2 also extends that base below this range using the laminar floor, an **ASSUMPTION** covered by HTC sensitivity.

Bo = q''/(G h_fg), so q'' = h_NB(q'') dT is solved implicitly by bracketed bisection (26 iterations over 0–1e8 W/m2). Numerical guards limit exponential overflow. In the exercised states these are convergence controls, not fitted enhancement factors. The alternative film sensitivity uses Purdue Eq.43 h_FB = 0.52 h_sp,v (Bo*)^-0.32 with local quality as a simplified Bo* (assuming near-zero inlet quality), lower bound 0.01. This is only the saturated DFFB branch, not a full Purdue film-regime implementation. Default film is the Darr hybrid above; the JSON marks the alternative explicitly.

LN2/O2 properties: installed CoolProp (version stored in results_v2 metadata at final verification), https://coolprop.org/fluid_properties/fluids/Nitrogen.html and https://coolprop.org/fluid_properties/fluids/Oxygen.html . No new property library was installed. CryoLink receiver continues using the inherited LOX table. CoolProp provides saturated densities, enthalpies, viscosity, conductivity, surface tension, heat capacities and critical properties for the line. The property package is not experimental validation of the transient solver.

## Experiment reproduction, input gaps and acceptance

Source is the same 2022 line paper, Table 1 and Methods. F2: 0.05 g, 550 kPa inlet, bare continuous, 14.6 s, 0.872 kg, listed final mass flux 533.22 kg/m2 s. F28: 0.05 g, 550 kPa inlet, four coating layers, 3 s/10% pulse, 7.25 s, 0.274 kg, listed final mass flux 500.43 kg/m2 s. Geometry: length 0.914 m, OD 12.7 mm, metal thickness 0.51 mm (therefore bare ID 11.68 mm). The coating is thin relative to the bore and its bore-volume reduction is neglected in the validation fixture. Methods state 2.1% chilldown-time and 2.5% consumed-mass uncertainty. Model acceptance requires **both** errors within those bounds, separately for each case. Neither a relative-saving match alone nor the much larger NASA wall-temperature MAPE qualifies as a pass.

The table's direct paired saving is 1-0.274/0.872 = 68.6%, whereas the text around Fig.4 says 76% and the abstract says up to75%. This discrepancy is retained, not resolved by selecting the number that favors our result. F28's footnote says time-series mass-flow data are missing. Listed steady/final mass flux and a valve duty do not uniquely reconstruct the integrated transient inlet/outlet flow; the model's fixed valve-on flux assumption is therefore weak. Its 1/4/10× sensitivity is deliberately exposed; it is not fitted to the measured total mass. The approximately67% in1g at20% duty is a cross-reference to another experiment, not a second boundary-complete dataset modeled here.

**ASSUMPTIONS with sensitivity:** initial wall293 K (280/293/300 K); mean line pressure325 kPa (150/325/550 kPa); inlet77 K; wall density8000 kg/m3; wall heat capacity max(200,450 T/293) J/(kg K); no parasitic heat in the fixture; five wall cells. The validation supplement sweeps inlet75/77/80 K, density7600/8000/8400 kg/m3, heat-capacity multiplier0.8/1/1.2, endpoint margin2/5/10 K, cooling-slope threshold0.2/0.5/1 K/s and confirmation0.1/0.2/0.5 s. Its nominal parasitic heat is zero (vacuum-jacketed short test section); this is swept below as a fixture boundary sensitivity. Starting wall temperature and pressure are not tabulated as complete time histories. The source uses an outer-wall cooling-slope criterion; v2 approximates this as all nodes below saturation+5 K and mean cooling slope<0.5 K/s for0.2 s, with no claim of equivalent thermocouple processing. The exact experimental slope threshold was not reported. Endpoint/properties are never adjusted to force agreement. `validation_v2.json` records the actual errors and failure.

## Receiver pressure controller and L5 objective

Controller **ASSUMPTIONS with sweeps** in L4/ALL: vent open2.6/close2.2bar (open2.4/2.6/2.8bar; close2.0/2.2/2.4bar); pause receiver spray at2.9bar and resume below2.4bar (pause2.7/2.9/3.1bar; resume2.2/2.4/2.6bar). Hysteresis state persists each timestep. Pressure pause applies whenever flow is connected to the receiver, including the initial fill interval while a warm receiver can still boil incoming spray. The earlier vent thresholds remain active throughout transfer in spray cases. This avoids dropping pressure protection merely because a nominal fixed conditioning timer has expired. The pressure supply regulator, 3.8bar abort and vent hardware are inherited. Compare controller enabled versus disabled **under v2 physics with identical MC draws**; retain separate v1→v2 counts so changed line physics cannot be credited to the controller. Sensor/valve delay and noise are omitted as in v1; this is a simple control feasibility study, not certified overpressure protection.

L5 minimizes nominal successful-completion `lost LOX kg + settling propellant kg`, over8–40mm ID, coarse2mm grid plus0.2mm refinement within±1.8mm of the coarse winner. Domain and resolution are **ASSUMPTION design-search choices**, not a manufacturing constraint or proof of global optimality. Failures have no completed-delivery objective and cannot win. Wall area/mass scale with diameter, volume with diameter squared, and hydraulic conductance with D^2.5, as in v1. V2 re-optimizes a coarse grid for hydraulic exponents0/2, host mass5000/20000kg and Isp100/300s. The nominal exponent2.5, host10000kg and Isp220s case has the finer search. This objective sums different propellants by mass at the user's request and makes no price or financial claim. It does not include dry line mass, valve/pump cost or fatigue.

All other inherited assumptions and sensitivities are listed in the v1 register above. V2 repeats duty/period, adaptive schedule, spray conductance/enhancement, stop/hold/gate, hydraulic and host-mass/Isp sensitivities rather than silently retaining v1 results. Initial temperatures use the identical v1 MC draw array. Fixed durations are freshly commissioned under nominal v2 physics; an uncorrected v1 timing schedule would confound model changes with an obsolete controller. The full v1 model and its original outputs remain the before case. No parameter was tuned to match an experimental mass-saving target or a user's earlier nominal FSW run.

Fixture parasitic-heat ASSUMPTION supplement: 0/1/5 W, both bare-continuous and coated-pulsed cases, in validation_supplement_v2.json and embedded in results_v2.json. Nominal results remain zero heat leak. The unused v1 `rewet` entry retained in DEFAULT is compatibility metadata; v2 coating does not apply it. Adaptive scheduling retains the inherited 40 K wall-superheat anchor; the complete legacy v1 case continues to use its original implementation.

Pulse scheduling uses the inherited timestep Boolean valve command. Non-integral on-times are quantized: a commanded 7% of 3 s is 0.21 s and may occupy 0.3 s at dt=0.1 s. Nominal fixed 3 s/10% and receiver 1 s/40% on-times are integral timestep multiples; adaptive on-times are quantized. These duty sweeps are discrete-controller sensitivities, not exact reproductions of every paper duty. The half-step C0/ALL comparison probes timestep dependence but does not establish convergence for every sensitivity case.
