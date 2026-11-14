# Cold-fit check of the coupling seals and seats (2026-11-02)

`python3 -I cold_seal.py` -> `cold_seal.json`. Hand calculation, no FEA. Sources are in the script header.

Results at 90 K (COMPUTED from MEASURED contraction data):
- Shrink 293 -> 90 K: Al 6061 0.376%, SS304 0.270%, PTFE 1.886% (NIST fits); PCTFE 0.931%, silicone 2.11% (NBS Monograph 29 Table 2.4).
- PCTFE poppet seat (r 19.5 mm) in its Al pocket: a 0.108 mm radial gap opens (0.216 mm on diameter); 3 mm seat loses 0.017 mm of axial clamp. The seat needs an axial preload that survives this or a larger interference. How the CAD retains the seat is not yet specified.
- Warm radial seal running clearance 0.1 mm (A nose spigot in B sleeve, both Al): unchanged if both are at the same temperature. Mating a warm A to a chilled B (90 K) leaves 0.006 mm: jam and galling risk. Keep B above ~202 K at mate, or open the running clearance to ~0.15 mm (then the seal squeeze must be rechecked).
- Nose face seal AS568-026: squeeze 22% -> 20.6% cold, so contraction is fine. The material is not: elastomers are hard and brittle at LOX temperature and most are not LOX compatible (TRW for NASA MSC 1970, p. 10). Replace both AS568 seals with spring-energized PTFE-jacketed seals or metal seals. This needs a seal supplier and a Codex CAD change of the glands.

Assumptions: silicone stands in for the CAD "elastomer"; whole parts at uniform 90 K or 293 K (no gradients); NBS values interpolated linearly between 80 and 100 K.

## Seal replacement spec (2026-11-02, seal_spec.py -> seal_spec.json)
Input for the next Codex CAD run. Catalog glands from Palmetto (P) and the clearance limit from Chesterton (C); sources and page numbers are in the script header.
- Radial warm seal: Palmetto 230-032, virgin PTFE jacket, helical 17-7 PH or Elgiloy spring. Gland floor Ø 47.35 -> 47.625 mm. Bore Ø 50.13 -> 50.80 mm. Width 2.39-2.64 mm (CAD 2.40 already fits).
- Nose face seal: Palmetto 239-026, internal pressure. Gland ID 30.18, OD 34.93, width 2.38, depth 1.45-1.50 mm (CAD depth 1.39).
- Clearance option A: keep 0.10 mm radial and warm B to >= 203 K before mate. Worst gap 0.39 mm diametral, inside C's 0.43 mm (10 MPa row).
- Clearance option B: 0.15 mm with no heater. Never jams, but the worst gap is 0.49 mm diametral, over that row. Only OK if the supplier rates it at our lower pressure.
- Provisional choice (decided while the user was away; revisit): option A. It needs a B heater or a "B warm" mate rule in the sequencer.
- Hardness: HRC 30 minimum on the sliding bore (P p.4, C p.18). Al 6061-T6 is much softer, so it needs a hard surface or a stainless sleeve. The supplier must confirm which one and its LOX compatibility.
- Finish: dynamic 2-8 µin Ra, static 8-12 µin Ra (P p.4).
- Face seal cold: the PTFE ring shrinks 0.26 mm more in radius than its groove. The supplier must size the cold radial fit (K p.4).


## 2026-11-06 cold-fit revision

CAD now uses Palmetto230-032 radial and239-026 internal-pressure face PTFE U-jackets with separate helical energizer envelopes, supplier-pending. Original PCTFE sealing cones, seat dimensions and .10mm radial running clearance remain. Each seat has an outer load collar, Smalley SSR-0200-S17 wave spring and screwed hard-stop retainer. The catalog reference rate is126.614N/mm; constant-rate cold preload is149.59N (ASSUMPTION), hard-stop axial gap.01306mm and worst shifted-seat collar overlap.6605mm (COMPUTED). All four cold-fit checks pass.

B has a pressed17-4PH H1025 sleeve (HRC30 minimum acceptance), conical film heater and thermistor boss. Require B>=203K before mate. Worst diametral extrusion gap.3904mm <=.43mm. SS304 contraction is an ASSUMPTION proxy for17-4PH/spring stainless; the Al-constrained bore bound is also reported. PTFE cold fit, oxygen compatibility, actual spring load and sleeve thermal/press-fit stress remain supplier/analysis qualifications. See cold_seal.json, seal_spec.json and [dimension/source ledger](../../cad/COLDFIT_CHANGES.md). Earlier sections above are historical findings retained.
