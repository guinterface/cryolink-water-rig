"""Cold-fit check of the coupling seals and PCTFE seats at LOX temperature (90 K). Units mm.
Sources (MEASURED = read at source 2026-11-02, PDFs in <scratch>/verify_1102/):
  Al 6061-T6, SS304, PTFE: NIST cryogenic material properties, linear expansion fit (L-L293)/L293 x1e5,
    https://trc.nist.gov/cryogenics/materials/6061%20Aluminum/6061_T6Aluminum_rev.htm (and 304Stainless, Teflon).
  PCTFE (Kel-F / Fluorothene), silicone rubber (Silastic 160): NBS Monograph 29 (Corruccini and Gniewek 1961),
    Table 2.4, printed p. 14, https://nvlpubs.nist.gov/nistpubs/Legacy/MONO/nbsmonograph29.pdf
    (Teflon in the same table, 1.89% at 90 K, matches the NIST fit 1.886%: cross-check).
  Elastomers in LOX: TRW report 14771-6001-R0-00 for NASA MSC (1970), p. 10, NTRS 19710007102:
    "At low temperatures elastomers become hard and brittle, and most elastomers cannot withstand the strong
    oxidizing environment of liquid oxygen, particularly under impact conditions."
2026-11-06 geometry inputs come directly from cad/params.py COLDFIT/COUPLING_SEALS/E2.
Nose and B body remain Al6061; sliding sleeve and load collars/retainers are17-4PH H1025;
seals are virgin PTFE U-jackets with supplier-pending helical springs. SS304 is a contraction
proxy for17-4PH/spring material. Silicone contraction is retained only as historical reference.
"""
import json, os, math, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"cad"))
import params
F=params.COLDFIT; C=params.COUPLING_SEALS
H = os.path.dirname(os.path.abspath(__file__))
T = 90.0

def nist(c, t):   # NIST 4th-order polynomial, returns (L-L293)/L293
    return sum(k * t**i for i, k in enumerate(c)) * 1e-5
AL = nist((-4.1277E2, -3.0389E-1, 8.7696E-3, -9.9821E-6, 0), T)
SS = nist((-2.9554E2, -3.9811E-1, 9.2683E-3, -2.0261E-5, 1.7127E-8), T)
PTFE = nist((-2.125E3, -8.201E-1, 6.161E-2, -3.171E-4, 6.850E-7), T)
PCTFE = -(962 + 900) / 2 * 1e-5          # NBS Table 2.4, 80 K 962, 100 K 900 -> 90 K by linear interpolation
SILICONE = -(2161 + 2066) / 2 * 1e-5     # NBS Table 2.4, Silastic 160, same interpolation; stands in for the CAD 'elastomer' (ASSUMPTION)
r = {'T_K': T, 'dL_L_pct': {k: round(100 * v, 3) for k, v in
     dict(Al6061=AL, SS304=SS, PTFE=PTFE, PCTFE=PCTFE, silicone=SILICONE).items()}}

# COMPUTED from current CAD. No elastomer squeeze model applies to spring U-jackets.
seat_ro, seat_t = params.E2['seat_ro'], params.E2['seat_t']
floor=F['radial_floor_d']/2; female_ri=F['radial_bore_d']/2
spigot_ro=female_ri-C['running_clearance']
gap_rad=seat_ro*(AL-PCTFE);gap_ax=seat_t*(AL-PCTFE)
loss=(seat_t+F['collar_t']+F['wave_height'])*(1+AL)-seat_t*(1+PCTFE)-(F['wave_height']+F['collar_t'])*(1+SS)
preload=F['wave_load']-F['wave_rate']*loss
stop_overlap=seat_ro*(1+PCTFE)-gap_rad-F['collar_ri']*(1+SS)
r['seat']=dict(cold_hard_stop_radial_overlap_worst_shift_mm=round(stop_overlap,4),cold_hard_stop_axial_gap_mm=round(loss,5),radial_gap_opens_mm=round(gap_rad,3),diametral_mm=round(2*gap_rad,3),
    axial_clamp_lost_mm=round(gap_ax,4),retention='four M1.2 screws + axial hard-stop retainer + load collar, A and B',
    spring='Smalley SSR-0200-S17; material/90K qualification pending',spring_source='https://www.smalley.com/wave-spring/ssr-0200',
    spring_rate_N_mm=F['wave_rate'],preload_warm_N=F['wave_load'],
    cold_stack_relaxation_mm=round(loss,5),preload_90K_N=round(preload,2),
    retains_preload=preload>0,load_model='ASSUMPTION constant catalog rate at 90K; SS304 contraction proxy for spring; no creep/pressure qualification')
# 17-4 PH contraction lacks a retrieved cryogenic fit: bracket free sleeve with SS304 and Al-constrained limits.
# Do not present SS304 data as a measured 17-4 property.
def strain(t,mat):
    if t is None:return 0.
    coeff=(-4.1277E2,-3.0389E-1,8.7696E-3,-9.9821E-6,0) if mat=='Al' else (-2.9554E2,-3.9811E-1,9.2683E-3,-2.0261E-5,1.7127E-8)
    return nist(coeff,t)
cases={}
for name,tA,tB in [('both 293 K',None,None),('both 90 K',90.,90.),('B cold 90 K, A warm 293 K (mate to a chilled client)',None,90.),('A cold 90 K, B warm 293 K',90.,None),('B 203 K, A warm 293 K',None,203.)]:
    eA=strain(tA,'Al');eB=strain(tB,'SS')
    c=female_ri*(1+eB)-spigot_ro*(1+eA)
    constrained=female_ri*(1+strain(tB,'Al'))-spigot_ro*(1+eA)
    cases[name]=dict(clearance_mm=round(c,4),Al_constrained_bound_mm=round(constrained,4),
        PTFE_jacket_radial_depth_mm=round(female_ri*(1+eB)-floor*(1+eA),4))
r['warm_seal']=dict(female_ri=female_ri,spigot_ro=spigot_ro,floor_radius=floor,cases=cases,
    seal='Palmetto 230-032 virgin PTFE + helical spring; supplier-pending',sleeve='17-4 PH H1025',
    sleeve_contraction_model='ASSUMPTION SS304 proxy, bounded by Al housing; coupled press-fit thermoelasticity not solved',
    min_B_temp_rule_K=203.,worst_diametral_gap_mm=round(2*(female_ri-spigot_ro*(1+AL)),4),
    extrusion_limit_mm=.43)
lo,hi=90.,293.
for _ in range(60):
    mid=(lo+hi)/2
    if female_ri*(1+strain(mid,'SS'))-spigot_ro<.05:lo=mid
    else:hi=mid
r['warm_seal']['min_B_temp_K_for_0p05mm_with_A_warm']=round(hi,1)
# sleeve free OD interference grows cold because Al contracts more. Installed common surface modeled in CAD.
r['sleeve']=dict(material='17-4 PH H1025',diametral_interference_293K_mm=F['sleeve_press_diametral'],
    free_diametral_interference_90K_mm=round(F['sleeve_press_diametral']+F['sleeve_od']*(SS-AL),4),
    note='ASSUMPTION 17-4 contraction represented by SS304; actual fit stress and bore distortion require thermal FEA')
ri,ro=F['face_id']/2,F['face_od']/2
r['face_seal']=dict(material='Palmetto 239-026 virgin PTFE + helical spring; supplier-pending',
    gland_id_mm=F['face_id'],gland_od_mm=F['face_od'],depth_mm=F['face_depth'],
    cold_radial_mismatch_mm=round(ro*(AL-PTFE),4),
    depth_90K_mm=round(F['face_depth']*(1+AL),4),
    verdict='U-jacket spring energized, no elastomer squeeze claim; supplier must confirm cold radial fit, spring load and oxygen compatibility')
r['checks']=dict(cold_hard_stop_retains_radial_overlap=stop_overlap>0,seat_preload_positive=preload>0,clearance_at_203K_bounds_above_0p05=all(cases['B 203 K, A warm 293 K'][k]>=.05 for k in ('clearance_mm','Al_constrained_bound_mm')),
    extrusion_gap_within_0p43=r['warm_seal']['worst_diametral_gap_mm']<=.43)
json.dump(r,open(os.path.join(H,'cold_seal.json'),'w'),indent=1)
print(json.dumps(r,indent=1))
