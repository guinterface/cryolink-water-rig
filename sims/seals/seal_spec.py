"""Spring-energized PTFE replacements for the two AS568 elastomer seals, sized from vendor standard glands, checked cold.
Historical catalog specification, with implemented 2026-11-06 revision checks appended below (cold_seal.py found the elastomers unusable in LOX). Units mm.
Sources (MEASURED = read at source 2026-11-02, copies in <scratch>/verify_1102/seal2/):
  P = Palmetto Precision Polymers, Spring Energized Seal Catalog (2023),
      https://palmettoprecisionpolymers.com/wp-content/uploads/2023/10/PALMETTO-SES-CATALOG-e51f6b2-1.pdf
      p.2 jacket 01 virgin PTFE -425/+450 F; p.4 spring gives the sealing force below ~100 psi, hardness HRC 30 for
      linear motion up to 100 SFPM at 0-150 psi, finish 'Light Gases, Cryogenics' dynamic 2-8 / static 8-12 uin Ra;
      p.5 helical springs 17-7 PH or Elgiloy; p.8 series 230 'Best for tight sealing at low temperatures ... cryogenic',
      239 'I.D. Face Seal - Tight sealing of internal pressure sources ... cryogenic';
      p.10 radial 000 series (1/16") gland width .094/.104 in; p.11 radial -032 gland ID 1.875 OD 2.000 in;
      p.21 internal face 000 series depth .057/.059 in, -026 gland ID 1.188 OD 1.375 in.
  C = Chesterton, Spring Energized Seal Guide (EN23216), https://f.hubspotusercontent30.net/hubfs/2535282/EN23216_24645_SES_Guide.pdf
      p.20 Table 1: PTFE compounds max diametral clearance 0.43 mm at 10 MPa (lowest pressure listed);
      p.18 hardness table: reciprocating up to 0.5 m/s, 0-1 MPa -> HRC 30 (same as P).
  K = K. Le (Saint-Gobain Seals), 'Spring energized seals in space applications', 32nd Space Symposium 2016, p.4:
      'Any application where operating temperature is under -60F, excludes the use of elastomeric seals'; cryogenic
      seals use 'heavy springs to resist the shrinkage of the outer seal lip'.
ASSUMPTIONS: shrink values from cold_seal.json (NIST / NBS Mono 29); mating stroke is a slow single stroke (<0.5 m/s);
  line pressure < 1 MPa during mate; Al 6061-T6 bore is softer than HRC 30 (needs a hard surface: supplier to confirm).
"""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
IN = 25.4
nist = lambda c, t: sum(k * t**i for i, k in enumerate(c)) * 1e-5
cs = json.load(open(os.path.join(H, 'cold_seal.json')))
AL = -cs['dL_L_pct']['Al6061'] / 100          # positive shrink fraction
PTFE = -cs['dL_L_pct']['PTFE'] / 100
old = json.load(open(os.path.join(H, 'cold_seal_before_1106.json')))['warm_seal']                            # current AS568-032 radial gland
MAXDIA = 0.43                                    # C p.20, at 10 MPa (our pressure is lower; table gives no lower row)

r = {'source_note': 'gland dims from Palmetto catalog dash tables (inches -> mm); checks COMPUTED'}
# ---- radial (piston-type gland on A spigot, sealing against B bore), Palmetto 230-032 ----
g_id, g_od = 1.875 * IN, 2.000 * IN
w_lo, w_hi = .094 * IN, .104 * IN
rad = dict(series='Palmetto 230 (helical, 17-7 PH or Elgiloy), dash -032, jacket 01 virgin PTFE',
           gland_floor_dia=round(g_id, 3), bore_dia=round(g_od, 3), gland_width=[round(w_lo, 2), round(w_hi, 2)],
           radial_depth=round((g_od - g_id) / 2, 3),
           change_vs_cad=dict(floor_dia=[round(2 * (old['female_ri'] - 1.78 * 0.78), 3), round(g_id, 3)],
                              bore_dia=[round(2 * old['female_ri'], 3), round(g_od, 3)]))
Rb = g_od / 2
opts = {}
for name, c, note in [('A: clearance 0.10 + B heater (mate only with B >= T_min)', 0.10, 'heater/ conops'),
                      ('B: clearance 0.15, no heater', 0.15, 'geometry only')]:
    cold_B = c - Rb * AL                 # B at 90 K, A warm
    cold_A = c + Rb * AL                 # A at 90 K, B warm (largest gap)
    tmin = None                          # min B temperature for 0.05 mm with A warm, NIST Al 6061 fit (as cold_seal.py)
    if cold_B < 0.05:
        lo, hi = 90.0, 293.0
        for _ in range(60):
            mid = (lo + hi) / 2
            e = -nist((-4.1277E2, -3.0389E-1, 8.7696E-3, -9.9821E-6, 0), mid)
            (lo, hi) = (mid, hi) if c - Rb * e < 0.05 else (lo, mid)
        tmin = hi
    opts[name] = dict(radial_clearance_warm=c, B_cold_A_warm=round(cold_B, 3), A_cold_B_warm=round(cold_A, 3),
                      worst_diametral=round(2 * max(cold_A, c), 3), within_C_0p43=bool(2 * max(cold_A, c) <= MAXDIA),
                      jams_if_B_cold=bool(cold_B < 0.05), B_min_temp_K=None if tmin is None else round(tmin, 0))
rad['clearance_options'] = opts
r['radial'] = rad
# ---- nose face seal, internal pressure, Palmetto 239-026 ----
f_id, f_od = 1.188 * IN, 1.375 * IN
face = dict(series='Palmetto 239 internal face (helical), dash -026, jacket 01 virgin PTFE',
            gland_id=round(f_id, 3), gland_od=round(f_od, 3), gland_width=round((f_od - f_id) / 2, 3),
            gland_depth=[round(.057 * IN, 3), round(.059 * IN, 3)], seal_height_ref=round(.050 * IN, 3),
            note='cold, the PTFE ring shrinks about %.3f mm more in radius than the Al groove, so it moves off the OD wall '
                 'that internal pressure pushes it against; the axial spring load still seals the faces, but the cold '
                 'radial fit (seal OD vs gland OD) must be sized by the supplier for 90 K (K p.4: heavy springs).'
                 % ((PTFE - AL) * f_od / 2),
            cold_radial_shrink_mm=dict(seal_od=round(PTFE * f_od / 2, 3), groove_od=round(AL * f_od / 2, 3)))
r['face'] = face
r['surfaces'] = dict(hardness='HRC 30 min on the dynamic bore (P p.4, C p.18); Al 6061-T6 is far softer -> hard surface '
                              'or a stainless sleeve; choice and LOX compatibility to confirm with the seal supplier (ASSUMPTION)',
                     finish_uin_Ra=dict(dynamic='2-8', static='8-12'))
r['verdict'] = ('Both seals have catalog glands within ~0.7 mm of the current CAD. Option A (keep 0.10 mm, warm B before '
                'mate) stays inside the 0.43 mm diametral limit in every hot/cold case; option B (0.15 mm) never jams but its '
                'worst gap exceeds the 10 MPa limit, which is only acceptable if the supplier rates it at our lower pressure.')
r['implemented_revision_2026_11_06']=dict(choice='A',mate_min_B_K=203,sleeve=cs['sleeve'],clearance_cases=cs['warm_seal']['cases'],seat_retention=cs['seat'],checks=cs['checks'],note='Historical Al-only option comparison retained above; implemented stainless sleeve proxy and Al constraint bounds below')
json.dump(r, open(os.path.join(H, 'seal_spec.json'), 'w'), indent=1)
print(json.dumps(r, indent=1))
