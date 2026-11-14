"""Summarize only h1c; never rewrites h1/h07 or historical results.json."""
import json,re,statistics as st
from pathlib import Path
c=Path('h1c');rho=1141.83;dpsdT=10598.2

def rows(name):
 f=sorted((c/'postProcessing'/name).glob('*/*.dat'))[-1]
 return [l.split() for l in f.read_text().splitlines() if l.strip() and not l.startswith('#')]
a=rows('pIn');b=rows('pOut')
A={float(l[0]):float(l[1]) for l in a};B={float(l[0]):float(l[1]) for l in b}
end=max(A.keys() & B.keys());lo=2000 if end>=3000 else max(0,end*.5)
v=[(A[t]-B[t])*rho for t in sorted(A.keys() & B.keys()) if t>=lo]
m=st.mean(v);sd=st.pstdev(v)
f=sorted((c/'postProcessing/mm').glob('*/fieldMinMax.dat'))[-1]
line=[l for l in f.read_text().splitlines() if l.split()[1:2]==['p']][-1].split('\t')
pm=float(line[2])*rho;loc=line[3].strip()
log=(c/'log.checkMesh').read_text();cells=int(re.search(r'cells:\s*(\d+)',log).group(1))
old=json.loads((c/'baseline_results.json').read_text())
new=dict(cells=cells,dp_Pa=round(m,2),dp_sd_Pa=round(sd,2),window=[lo,end],samples=len(v),
 p_min_rel_outlet_Pa=round(pm,2),p_min_loc_m=loc,p_min_below_inlet_Pa=round(m-pm,2),
 p_min_absolute_at_inlet_4bar_Pa=round(400000+pm-m,2),subcooling_needed_K=round((m-pm)/dpsdT,4),
 pressure_margin_above_psat_at_inlet_4bar_Pa=round(400000+pm-m-101348.2,2),
 mesh_ok='Mesh OK' in log,volumes=json.loads((c/'volumes.json').read_text()),
 limitations='Steady RANS oscillation, not residual convergence; one revised 1mm mesh; original two valve coils omitted (~12 Pa historical hand estimate)')
flux={}
for d in sorted((c/'postProcessing').glob('z*q')):
 f=sorted(d.glob('*/*.dat'))[-1]
 l=[x for x in f.read_text().splitlines() if x.strip() and not x.startswith('#')][-1]
 vec=[float(x) for x in l.split('(')[-1].rstrip(')').split()]
 flux[d.name]=vec[2]*rho
new['plane_mass_flux_kg_s']=flux
new['max_plane_mass_flux_error_pct']=round(max(abs(v-.28)/.28*100 for v in flux.values()),3)
new['mass_flux_within_1p5pct']=new['max_plane_mass_flux_error_pct']<=1.5
pinfile=sorted((c/'postProcessing/pIn').glob('*/*.dat'))[-1]
area=float(re.search(r'# Area\s*:\s*([0-9.eE+-]+)',pinfile.read_text()).group(1))
qin=area*.6457;qout=float(rows('phiOut')[-1][1])
new['inlet_patch_mdot_kg_s']=qin*rho
new['outlet_patch_mdot_kg_s']=qout*rho
new['global_flux_imbalance_pct']=round(abs(qout/qin-1)*100,5)
new['mesh_quality_lines']=[l.strip() for l in log.splitlines() if any(k in l for k in ('Max aspect ratio','Mesh non-orthogonality','Max skewness','Mesh OK','Failed'))]
new['retention_capacity']=json.loads((c/'retention_capacity.json').read_text())
U=.28/rho/(3.141592653589793*.011**2)
new['K_line_head']=round(m/(.5*rho*U**2),4)
new['Cv_equiv']=round((.28/rho*15850.3)*((rho/999)/(m/6894.76))**.5,4)
out=dict(revision='2026-11-06 cold-fit',old_h1=old.get('h1_2000_4000'),old_h07=old.get('h07_1500_2167'),old_volumes_cm3=old['volumes_cm3'],new_h1c=new)
(c/'results.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
