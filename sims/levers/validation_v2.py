"""Published geometry and LN2 experiment attempted before CryoLink lever results."""
import math
from physics_v2 import Line,properties

def experiment(coated=False,dt=.01, **cfg):
    D=.0127-2*.00051; L=.914; A=math.pi*D*L
    mass=math.pi/4*(.0127**2-D**2)*L*cfg.get('density',8000) # ASSUMPTION steel density
    p=cfg.pop('p',325000.); s=properties('Nitrogen',p)
    t0=cfg.pop('T0',293.); tw=[t0]*5
    line=Line('Nitrogen',D,L,A,mass,math.pi/4*D*D*L,60.48e-6 if coated else 0.,cfg,g=.05*9.80665)
    G=500.43 if coated else 533.22
    onflow=G*math.pi*D*D/4*cfg.get('onflow_scale',1.)
    # Inlet subcooling not tabulated for F2/F28; assumed 77 K.
    inlet=cfg.get('inlet_K',77.)
    hin=s['hl']+s['cp']*(inlet-s['T'])
    t=0.; used=0.; output=0.; last=sum(tw)/5; steady=0.
    while t<300:
        opn=(t%3<.3-1e-8) if coated else True
        md=onflow if opn else 0.
        mout,h=line.advance(tw,dt,md,hin,p,lambda T: cfg.get('cp_scale',1.)*max(200.,450.*T/293),qenv=cfg.get('qenv',0.))
        used+=md*dt; output+=mout*dt; t+=dt
        mean=sum(tw)/5; slope=abs(mean-last)/dt; last=mean
        # Approximation to published outer-wall derivative criterion.
        steady=steady+dt if max(tw)<s['T']+cfg.get('stop_margin',5.) and slope<cfg.get('stop_slope',.5) else 0.
        if steady>=cfg.get('stop_hold',.2): break
    observed_t=7.25 if coated else 14.6; observed_m=.274 if coated else .872
    return dict(case='F28 coated pulsed' if coated else 'F2 bare continuous',time_s=t,
                inlet_mass_kg=used,outlet_mass_kg=output,inventory_kg=sum(line.mass),
                measured_time_s=observed_t,measured_outlet_mass_kg=observed_m,
                time_error_percent=100*(t/observed_t-1),mass_error_percent=100*(output/observed_m-1),
                within_experimental_error=abs(t/observed_t-1)<=.021 and abs(output/observed_m-1)<=.025,
                off_pulse_heat_J=line.off_heat,total_heat_J=line.wall_heat,
                mass_residual_kg=used-output-sum(line.mass),
                max_cell_mass_residual_kg=line.mass_error,max_cell_energy_residual_J=line.energy_error,
                boundary_assumptions=dict(mean_pressure_Pa=p,initial_wall_K=t0,onflow_kg_s=onflow,inlet_K=inlet),config=cfg)

def validate():
    a=experiment(); b=experiment(True)
    return dict(label='COMPUTED; validation attempt, not a calibration',experiments=[a,b],
                passed=a['within_experimental_error'] and b['within_experimental_error'],
                computed_mass_saving_percent=100*(1-b['outlet_mass_kg']/a['outlet_mass_kg']),
                tabulated_mass_saving_percent=100*(1-.274/.872),text_claim_mass_saving_percent=[75,76],
                sensitivities={key:[dict(value=v,result=experiment(True,**{key:v})) for v in values]
                 for key,values in {'p':[150000.,325000.,550000.],'T0':[280.,293.,300.],
                                  'onflow_scale':[1.,4.,10.],'holdup_fraction':[.05,.25,.75],
                                  'drain_tau':[.3,3.,30.],'inlet_K':[75.,77.,80.],
                                  'density':[7600.,8000.,8400.],'cp_scale':[.8,1.,1.2],
                                  'stop_margin':[2.,5.,10.],'stop_slope':[.2,.5,1.],
                                  'stop_hold':[.1,.2,.5]}.items()})
if __name__=='__main__':
 import json
 print(json.dumps(validate(),indent=2))
