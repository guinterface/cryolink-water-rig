"""Physical accounting and radial-resistance checks, independent of transfer scoring."""
import math,json
from physics_v2 import Line,properties,teflon

def check():
 s=properties('Nitrogen',325000)
 # Force legacy film regime so added resistance has a known exact effect.
 q=[]
 for t in (0,50e-6):
  w=[293.]*5; m=Line('Nitrogen',.01168,.914,math.pi*.01168*.914,.14,1e-4,t,{'boiling_model':'legacy'})
  m.advance(w,.001,.1,s['hl'],s['p'],lambda T:450)
  q.append(m.wall_heat)
 assert 0<q[1]<q[0]
 # Conservative open-flow -> closed-inlet boil-off/drain sequence.
 w=[250.]*5; line=Line('Nitrogen',.01168,.914,math.pi*.01168*.914,.14,1e-4,0.)
 incoming=outgoing=0.
 for j in range(500):
  md=.05 if j<30 else 0.
  out,h=line.advance(w,.01,md,s['hl'],s['p'],lambda T:450)
  incoming+=md*.01;outgoing+=out*.01
 assert line.off_heat>0
 assert abs(incoming-outgoing-sum(line.mass))<1e-10
 assert line.energy_error<1e-8
 # No fluid -> no off-pulse wall cooling.
 w=[250.]*5; empty=Line('Nitrogen',.01168,.914,.03,.14,1e-4)
 empty.advance(w,.01,0,s['hl'],s['p'],lambda T:450)
 assert w==[250.]*5
 return dict(passed=True,conduction_bare_J=q[0],conduction_coated_J=q[1],
             off_heat_J=line.off_heat,mass_error_kg=incoming-outgoing-sum(line.mass),
             cell_energy_error_J=line.energy_error,teflon_k_100K=teflon(100))
if __name__=='__main__':print(json.dumps(check(),indent=2))
