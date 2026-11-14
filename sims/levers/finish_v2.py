"""Finalize first run while preserving unaffected computations.
run_v2.py reproduces the final controller directly; this file is an execution audit.
"""
import ast,json,time
from pathlib import Path
import run_v2 as r
from report_v2 import report
ROOT=Path(__file__).resolve().parent
start=time.process_time()
# The source equations and paired draws are unchanged; only receiver pressure protection changed.
log=(ROOT/'run_v2.log').read_text()
mm=float(next(s.split()[1] for s in log.splitlines() if s.startswith('SIZE ')))
r.DEFAULT['diameter']=mm/1000
draws=json.loads((ROOT/'results.json').read_text())['uncertainty_draws']
dt=.1
corrected={}
for c in ('L4','ALL'):
 a=r.simulate(c,dt=dt,trace=True)
 corrected[c]=dict(nominal=a,monte_carlo=r.summarize([r.simulate(c,dt=dt,initial_error=e,stops=a['phase_seconds']) for e in draws]))
 print('corrected',c,corrected[c]['monte_carlo']['counts'],flush=True)
 (ROOT/'controller_final_v2.json').write_text(json.dumps(corrected,indent=2))
# Read the exact nominal sensitivity requests from the reproducible driver.
tree=ast.parse((ROOT/'run_v2.py').read_text())
ranges=ast.literal_eval(next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ranges' for t in n.targets)))
sweeps={key:[dict(value=v,result=r.simulate(c,{key:v},dt=dt)) for v in values]
        for key,(c,values) in ranges.items() if c in ('L4','ALL')}
fine=r.simulate('ALL',dt=dt/2)
while not (ROOT/'results_v2.json').exists(): time.sleep(5)
d=json.loads((ROOT/'results_v2.json').read_text())
assert d['dt']==dt and d['uncertainty_draws']==draws
assert d['config']['diameter']==r.DEFAULT['diameter']
# Main writes the report after JSON; allow its short artifact write to finish.
time.sleep(5)
for c,pair in corrected.items():
 d['nominal'][c]=pair['nominal'];d['monte_carlo'][c]=pair['monte_carlo']
d['sensitivity'].update(sweeps);d['timestep_check']['ALL']=fine
allruns=list(d['nominal'].values())+[a for mc in d['monte_carlo'].values() for a in mc['runs']]
d['max_mass_balance_residual_kg']=max(abs(a['mass_balance_residual_kg']) for a in allruns)
assert d['max_mass_balance_residual_kg']<1e-6
d['controller_correction_cpu_seconds']=time.process_time()-start
d['cpu_seconds']+=d['controller_correction_cpu_seconds']
d['runtime_note']='CPU includes full first pass plus corrected L4/ALL MC, nominal sensitivities and ALL half-step. These independent runs overlapped in wall time. Earlier source checks/diagnostic attempts excluded.'
d['wall_seconds']+=max(0,time.time()-(ROOT/'results_v2.json').stat().st_mtime)
(ROOT/'results_v2.json').write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
report(d)
print('FINAL CPU min',d['cpu_seconds']/60,flush=True)
