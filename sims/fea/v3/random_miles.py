"""Random vibration screen (Miles' equation) for the CryoLink support, FEA v3.
Source: SpaceX Rideshare Payload User's Guide v11 (Aug 2026), Table 4-6 random MPE (flat 0.015 g^2/Hz, 50-700 Hz, 5.57 grms, all axes);
Table 6-1 test levels: acceptance = MPE, protoflight = MPE + 3 dB, qualification = MPE + 6 dB.
Section 4.1.2.2: the quasi-static load factors are net-CG payload loads and "shall not be utilized for individual internal
components", so for a component on a host the random response is checked here.
Mode 1 (78.8 Hz) is axial plate drumming carrying 89% of the Z effective mass (modal.dat), so Miles is applied axially.
Q = 10 is an ASSUMPTION (bolted aluminum, no test data); Q = 20 shown as sensitivity. 3-sigma load factor = 3 x grms.
Stress is scaled linearly from the 10 g axial static case (results_h6.json)."""
import json, math, sys, os
if len(sys.argv)>1: os.chdir(sys.argv[1])
R=json.load(open('results_h6.json')); f1=R['modes_hz'][0]; ax=R['axial_10g']
import re
_d=open('modal.dat').read().split('E F F E C T I V E   M O D A L   M A S S')[1]
_m1=[float(x) for x in re.search(r'^\s+1\s+(\S+)\s+(\S+)\s+(\S+)',_d,re.M).groups()]
_tot=float(re.search(r'T O T A L   E F F E C T I V E   M A S S.*?\n\s*\n.*?\n\s+(\S+)',open('modal.dat').read(),re.S).group(1))
mz=_m1[2]/_tot                                  # mode-1 Z effective-mass fraction (modal.dat)
psd_mpe=0.015                                   # g^2/Hz at f1 (50-700 Hz plateau)
out={'f1_hz':f1,'mode1_z_mass_fraction':mz,'cases':[]}
for lvl,db in [('acceptance (MPE)',0),('protoflight (MPE+3 dB)',3),('qualification (MPE+6 dB)',6)]:
    psd=psd_mpe*10**(db/10)
    for Q in (10,20):
        grms=math.sqrt(math.pi/2*f1*Q*psd); g3=3*grms; k=g3/10.0
        vm=ax['vm_max_mpa']*k; p999=ax['vm_p999_mpa']*k
        c=dict(level=lvl,Q=Q,psd=round(psd,4),grms=round(grms,2),g3sigma=round(g3,1),vm_peak_mpa=round(vm,0),
               ms_peak=round(276/(1.25*vm)-1,2),vm_p999_mpa=round(p999,0),ms_p999=round(276/(1.25*p999)-1,2),umax_mm=round(ax['umax_mm']*k,2))
        out['cases'].append(c); print(c)
json.dump(out,open('random_miles.json','w'),indent=1)
