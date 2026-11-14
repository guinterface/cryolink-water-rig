# CryoLink: summary of everything so far (as of 13 Nov 2026)

## 1. The company

- **What we sell:**
  - the **CryoLink Transfer Assembly (CTA)**, about $5M, on depots and tankers;
  - a **receiver kit**, about $1M, on each client vehicle;
  - about **$50/kg** transfer fees at partner depots from 2033.
- **Long term:** our own propellant depot.
- **The core hardware:** a two-half cryogenic coupling. Half A (capture cone and spring poppet) is on the CTA. Half B (capture nose and spring poppet) is on the client.
- **Website:** cryolinkspace.com. The vehicle and mission scenes show our CryoLink tanker carrying the CTA, refuelling a real satellite (NASA's public Landsat 8 model) fitted with our receiver kit.

## 2. Part I: data package (team)

- The financial model, market sizing and orbital and thermal simulations were done by teammates.
- Canvas assignment: "Seed Pitch Data Package and Prototype", due 13 Nov, 11:59 pm.

## 3. Part II: simulations

| # | Simulation | Tool | Result |
|---|---|---|---|
| 1 | Capture and seat | MuJoCo 3.17 | Simplified cone: 60/60 seat up to 7 mm, 1°, 10.7 N. **Real flight CAD jams** (0.1 mm clearance, flat 1 mm ledge, no chamfer; 22.3 kN peak). Fix: lead-in chamfer |
| 2 | Line chilldown | Transient wall model | Continuous 43 s / 12.0 kg; pulsed 165 s / 4.4 kg (−63%). **Failed validation** vs NASA/UF LN2 data (5.28 s vs 14.60 s measured) |
| 3 | Transfer levers | Monte Carlo, 40 runs per case | Coating, pulsing, spray, line size compared; same validation caveat. Receiver pressure control prevents 10/40 overpressure aborts |
| 4 | Flow through the coupling | OpenFOAM 2412 | 1.8 kPa loss at 1,000 kg/h LOX (< 0.5% of supply); 134 g LOX trapped in a stagnant pocket |
| 5 | No-vent fill | CoolProp | Fills under 4 bar relief if the client tank wall starts ≤ 200 K (3.0 bar peak) |
| 6 | Launch loads | CalculiX 2.23 | First mode 82 Hz; static margins ≥ +2.05; proof +3.13, burst +1.78; qualification random vibration **−0.22** at a bolt edge |
| 7 | Seals at 90 K | Cold-fit calculation | PTFE seals replace rubber O-rings; B held ≥ 203 K before mating; worst cold gap 0.39 mm |

## 4. Part II: the water transfer rig

- Designed 5–8 Nov in CadQuery, using the coupling's own 22 mm bore and capture geometry.
- **Robot:** servo carriage, over-centre latch, two servo pinch valves, switches, temperature probes, a load cell and a pressure sensor, all run by an ESP32 tied to our ROS 2 flight software.
- **Size:** 355 parts in the CAD assembly. About 48 printer-hours, 29 machined parts, and $318.57 of components to order. Nothing has been ordered yet.
- **Tests:** T1 to T8 (see README section 2).
- **Documentation:** the build book (`book/`), and a 30% scale display model on 3 print plates (`cad/scale_model_30pct/`).
- **Set aside:** on 13 Nov we printed a simplified PLA alignment piece. It did not represent our coupling, so we dropped it.

## 5. Teaching-team feedback (13 Nov)

- **Questions an investor will ask:**
  - Which buyers will pay us when SpaceX and Blue Origin build transfer in-house for HLS?
  - How does a startup compete with hardware-heavy incumbents?
  - How much of the $1.2B market do we keep?
  - Who on the team has cryogenic hardware or oxygen-safety experience?
- **Suggested next steps:**
  - Why now: lead with HLS and undemonstrated in-orbit cryo transfer, not falling launch costs.
  - Consider narrowing to a qualified, reusable cryo coupling plus its test data.
  - Moat: cycle-test data and a common cryo port standard.
  - Add a cryogenic thermofluids advisor.
  - Prototype: a tabletop LN2 test, cycling the coupling 50–100 times and measuring leak rate, chilldown time and boil-off against our model.

## 6. NASA Glenn: Dr. Jason Hartwig

- **Who:** a NASA Glenn cryogenic fluid management researcher. He wrote the book on liquid acquisition devices, and his group ran the chilldown ground tests our model uses (npj Microgravity 2021).
- **Timeline:**
  - 3 Nov: first email.
  - 9 Nov: follow-up.
  - 12 Nov: he replied and offered a time.
  - 13 Nov: call held on Teams at 1:00 pm PT.
- **How it went:** the call went well. His feedback was that our questions were too broad, and he asked us to send specific technical questions in advance.
- **Follow-up:** he offered a second call on **Wed 18 Nov or Thu 19 Nov, 12:00–2:30 pm PT**. The team is choosing the time.
- **Questions prepared:** call-prep doc. The top five were:
  1. LN2 cycle-test setup and instruments.
  2. Which programs buy rather than build.
  3. A common cryo port standard.
  4. What qualification data builds trust.
  5. An advisor suggestion.
- **His technical answers:** _not written down yet. Add the call notes here._
- **For the next call:** specific questions on why our chilldown model misses the F2/F28 data, LN2 cycle-test instrumentation, seal leak criteria, and liquid acquisition devices.

## 7. Open items

1. Lead-in chamfer on the flight coupling CAD, then rerun the 60-case capture sweep.
2. Fix the chilldown model against the NASA/UF LN2 data.
3. Close the −0.22 vibration margin: stiffen the bracket near the bolts, or run a tap test.
4. Order rig parts, then print, machine and build. Run T1–T8, then the LN2 cycle test.
5. Pick the Hartwig follow-up time and send the specific questions in advance.
