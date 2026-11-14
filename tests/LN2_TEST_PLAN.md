# LN2 chilldown bench test: draft plan (Claude, 2026-11-09; not approved by the team)

Why: the user (11-09): "Isn't the thermal part more important than the pressure part?" Water proves mating and interlocks. It shows none of the cryogenic physics: vapor first while the line chills, seal shrink, frost. LN2 is the standard inert stand-in for LOX (77 K vs 90 K; general knowledge).
Labels: MEASURED = read at source; COMPUTED = our script; ESTIMATE = judgment; UNVERIFIED = not confirmed.
Status: needs a host. Ask Diego (SSI Rockets, liquid engine per user 11-09) first: Slack draft #113. Not part of the Nov 13 must-have.

## 1. What we test
- Pour LN2 from a vented dewar through a short metal line and our coupling (mated by hand) into an open receiver.
- Measure:
  - wall temperature at 3 points (inlet, coupling, outlet) vs time;
  - time until liquid (not vapor) leaves the outlet;
  - LN2 used (dewar on a scale);
  - leak at the coupling seal once cold (frost/vapor plume, soap-free: watch for a jet).
- Compare with the prediction in section 3. Sim vs test is the result we show.

## 2. Hardware (ESTIMATE; nothing ordered)
- Line: about 0.6 m of 3/8" OD 304 stainless tube, uninsulated.
- Coupling halves: metal (aluminum or stainless, PRL). Seals: PTFE, not printed parts. PETG and most printed plastics turn brittle at 77 K (general knowledge).
- Mating by hand or with the servo kept away from the cold parts. Autonomy stays on the water rig.
- Sensors: 3 thermocouples on the wall + amplifier boards on the ESP32. Checked 11-09 at adafruit.com (MEASURED):
  - DS18B20 (381, the rig's sensor): "Usable temperature range: -55 to 125°C", so it cannot read LN2 (-196 °C).
  - MAX31856 universal amp (3263): "-210°C to +1800°C", handles type T and K with linearization, $17.50, OUT OF STOCK.
  - MAX31855K amp (269): "-200°C to +1350°C", K only, $14.95, in stock. -196 °C is at the edge, and the chip assumes a linear K curve, so cold readings need a software correction with the NIST K table (general knowledge; UNVERIFIED size of error).
  - K bead probe (270): $9.95, OUT OF STOCK.
  - So: 3 x MAX31855K ($44.85) now, or MAX31856 + type T probes from another vendor (UNVERIFIED stock). Check readings in a LN2 bath (-196 °C) and ice water (0 °C) before the run.
- Scale under the dewar or receiver (the rig's load cell, if it is rated for the cold receiver: UNVERIFIED).
- Every section that could trap liquid between two closed valves gets a vent or relief valve. Simplest: no valves at all, open dewar to open receiver.

## 3. Prediction (COMPUTED, prototype/sims/ln2_bench_chilldown.py -> ln2_bench_chilldown.json)
- Case: 0.6 m line + 0.40 kg stainless coupling lump, 1.3 bar, saturated LN2 inlet, bare tube in still air.
- Energy bound (no model choice): 0.10-0.21 kg LN2 just to cool the metal (43 kJ).
- Full model (film boiling above a rewet point, assumed):

| Flow | Rewet +30 K | Rewet +60 K |
|---|---|---|
| 5 g/s | cold in 267 s, 1.49 kg LN2 | 185 s, 1.08 kg |
| 10 g/s | 149 s, 1.79 kg | 115 s, 1.45 kg |
| 20 g/s | 90 s, 2.41 kg | 77 s, 2.14 kg |

- The thin tube cools in seconds; the coupling mass is what takes minutes (COMPUTED). Air keeps adding about 51 W once cold.
- So: about 1-2.5 kg (1.3-3 L) LN2 per run, 1.5-4.5 min (ESTIMATE from the table). Bring a 10 L dewar for 2-3 runs plus boil-off.
- Limits: film boiling has no gravity term; frost, dewar boil-off and pour losses are ignored; the coupling is one lump. Expect real times to differ; the test is what tells us by how much.

## 4. Safety (MEASURED unless marked; Stanford cryogen SOP as summarized in PROTOTYPE_PLAN.md section 3)
- Trainings: EHS-4200, EHS-1900, EHS-2200, EHS-2480 (online) + the host's lab-specific training. The user has done the ES3 trainings (user 11-09); the four EHS courses are separate (UNVERIFIED which are done).
- PPE: goggles + face shield if splash is possible, insulated cryogenic gloves.
- Well-ventilated area only (oxygen-deficiency risk). Small volumes (under 10 L).
- No closed volume anywhere (ESTIMATE, the main hazard is pressure from trapped liquid boiling).
- Never LOX, methane or hydrogen.
- Two people present (ESTIMATE).

## 5. Getting LN2 and a place (open)
- Supply: Physics Stockroom (Varian 115) lists LN2; sign-out needs a PTA, so a faculty sponsor (MEASURED 11-06). Or the host team's own supply (ask Diego).
- Place: ES3 with SSI Rockets (ask), or a sponsor's lab. Lab64 and PRL are not good fits (PRL discourages pressurized systems; MEASURED).

## 6. Questions for Diego
1. What propellants do you use now, and do you cold-flow with LN2?
2. Could a class project run this small, open, vented LN2 test at ES3 with you?
3. Who signs off on a test at ES3?
4. Could you look at this plan for 20 minutes?
