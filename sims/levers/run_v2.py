#!/usr/bin/env python3
"""CryoLink matched-plant study. All results COMPUTED; see SOURCES.md.
No ROS, network, or writes outside this directory. Python 3 + matplotlib.
"""
import argparse, ast, hashlib, json, math, os, random, time, types
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mplconfig"))
from pathlib import Path
ROOT = Path(__file__).resolve().parent
FSW = ROOT / '../../fsw/src/cryolink_fsw/cryolink_fsw'

def load_plant():
    # Read-only v1 snapshots; no writes to fsw or v1 artifacts.
    dest = ROOT / 'plant_snapshot'
    hashes = {name: hashlib.sha256((dest/name).read_bytes()).hexdigest()
              for name in ['plant_sim.py','props.py','lox_table.py','common.py','chilldown_controller.py']}
    table = {}; exec((dest/'lox_table.py').read_text(), table)
    p = types.SimpleNamespace(); ns = p.__dict__
    # exec with a single globals dictionary is needed by property functions.
    ns['ROWS'] = table['ROWS']
    exec((dest/'props.py').read_text().replace('from .lox_table import ROWS', ''), ns)
    c = types.SimpleNamespace(BAR=1e5, RELIEF_RX_PA=4e5, RELIEF_LINE_PA=5.5e5)
    raw=(dest/'plant_sim.py').read_text()
    tree=ast.parse(raw); node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Plant')
    src='\n'.join(raw.splitlines()[node.lineno-1:node.end_lineno])
    # Explicit study extensions. No published LOX rewet shift is available.
    src=src.replace('dTw > 40', 'dTw > self.rewet_superheat')
    src=src.replace("        # -------- purge He --------", "        mdot = self.out_mdot\n        # -------- purge He --------")
    env=dict(math=math, P=p, C=c); exec(src,env)
    base=env['Plant']
    def march(self,dt,mdot,gas,p_s,p_down):
        if gas: raise ValueError('gas ingestion outside v2 study scope')
        if max(self.Tw)<self.T_sl+1 and sum(self.line.mass)==0:
            self.out_mdot=mdot; return ('o2',p.h_l(self.T_sl))
        # CoolProp has an absolute enthalpy datum different from inherited LOX table.
        from physics_v2 import properties
        sp=properties('Oxygen',max((p_s+p_down)/2,p.psat(self.T_sl)))
        hin=sp['hl']+p.h_l(self.T_sl)-p.h_l(sp['T'])
        mout,hout=self.line.advance(self.Tw,dt,mdot,hin,sp['p'],p.cp_ss,self.q_env_line)
        self.out_mdot=mout
        self.T_out=sp['T']+max(0,hout-sp['hv'])/sp['cpg']
        return ('o2',p.h_l(sp['T'])+hout-sp['hl']) if mout else None
    base._line_march=march
    return env['Plant'],p,hashes

from physics_v2 import Line
Plant,P,HASHES=load_plant()
CASES={'C0':(), 'L1':('coat',), 'L2':('pulse',), 'L3':('adaptive',),
       'L4':('spray',), 'L5':('size',), 'ALL':('coat','pulse','adaptive','spray','size','gate')}
DEFAULT=dict(rewet=80., duty=.10, period=3., adaptive_low=.10, adaptive_high=.50, adaptive_span=100.,
             spray_period=1., spray_duty=.4, spray_hA=3000., spray_gain=1.5, diameter=.020, conductance_power=2.5,
             fixed_margin=5., hold=30., gate_margin=5., host_mass=10000., isp=220.)

def simulate(case, cfg=None, dt=.1, initial_error=(0.,0.,0.), stops=None, trace=False):
    k=DEFAULT.copy(); k.update(cfg or {}); flags=CASES[case]
    pl=Plant(random.Random(0),receiver_volume=1000/(P.rho_l(90)*.95))
    pl.rewet_superheat=40.
    pl.Tw=[250*(1+initial_error[0]+(initial_error[1]-initial_error[0])*i/4) for i in range(5)]
    pl.Tw_rx=150*(1+initial_error[2]); pl.T_g=pl.Tw_rx
    # Bulk jet has no direct spray-wall term. Pool and ullage exchange remain.
    pl.hA_spray=k['spray_hA']*k['spray_gain'] if 'spray' in flags else 0.
    diameter=k['diameter'] if 'size' in flags else .016
    r=diameter/.016
    pl.A_line*=r; pl.V_line*=r*r; pl.m_line_wall*=r
    pl.cda_liq*=r**k['conductance_power']
    from physics_v2 import Line
    pl.line=Line('Oxygen',diameter,5.,pl.A_line,pl.m_line_wall,pl.V_line,
                 k['coating_t'] if 'coat' in flags else 0.,k)
    throttle=False
    phase='line'; elapsed=0.; local=0.; hold=0.; phase_t={}; rows=[]
    failed=None; vent=False; gate_checks=0; mass0=pl.M_sl; gas0=pl.m_v
    max_pressure=0.; fill_flux=[]
    # Commissioning uses measured wall temperature to establish fixed durations;
    # production fixed controllers use those same times for every uncertainty draw.
    adaptive='adaptive' in flags
    while elapsed < 16000:
        ts=P.tsat(max(pl.p_rx_parts()[0],800))
        wall=max(pl.Tw) if phase=='line' else pl.Tw_rx
        ready=wall <= ts+k['fixed_margin']
        if phase in ('line','receiver'):
            hold=hold+dt if ready else 0.
            done=(local >= stops[phase]) if stops and not adaptive else hold>=k['hold']
            if done:
                phase_t[phase]=local
                if phase=='line': phase='receiver'
                else:
                    if 'gate' in flags:
                        gate_checks+=1
                        # ASSUMPTION conservative wall-temperature readiness gate,
                        # not the published validated NVF energy-balance model.
                        if pl.Tw_rx>ts+k['gate_margin']:
                            failed='gate_abort'; break
                    phase='fill'
                local=0.; hold=0.; continue
        elif pl.m_l>=1000:
            phase_t['fill']=local; break
        period=k['period']; duty=1.
        if phase=='line' and ('pulse' in flags or adaptive):
            duty=k['duty']
            if adaptive:
                # Increase duty as measured wall approaches rewet; no foreknowledge.
                u=min(1.,max(0.,(wall-ts-pl.rewet_superheat)/k['adaptive_span']))
                duty=k['adaptive_high']-(k['adaptive_high']-k['adaptive_low'])*u
        if phase=='receiver' and 'spray' in flags:
            period=k['spray_period']; duty=k['spray_duty']
        opn=local%period < duty*period-1e-8
        if phase=='fill': opn=True
        pr=pl.p_rx()
        controlled='spray' in flags and k['pressure_control']
        vent = pr>(k['vent_off'] if controlled else 3.0e5) if vent else pr>(k['vent_on'] if controlled else 3.5e5)
        if controlled and phase!='line':
            throttle = pr>k['spray_resume'] if throttle else pr>k['spray_pause']
            if throttle: opn=False
        # Same pressure controller in every case. No-vent fill is allowed naturally.
        pos=dict(in_a=opn,in_b=opn,rx=phase!='line',line_vent=phase=='line',
                 vent_rx=vent,purge=False,press=pl.p_supply()<min(pr+1e5,4.8e5))
        pl.step(dt,pos,1.05e-4,False,0.)
        elapsed+=dt; local+=dt; max_pressure=max(max_pressure,pl.p_rx())
        if phase=='fill' and opn: fill_flux.append(pl.mdot_line/(math.pi*diameter**2/4))
        if trace and int(elapsed/dt)%max(1,int(5/dt))==0:
            rows.append([elapsed, max(pl.Tw),pl.Tw_rx,pl.m_l,pl.p_rx(),duty])
        if pl.p_rx()>=3.8e5: failed='overpressure_abort'; break
        if pl.fill_fraction()>.98 and pl.m_l<1000: failed='volume_abort'; break
    else: failed='timeout'
    phase_t.setdefault(phase,local)
    # Net client liquid gain; includes any incoming LOX remaining as vapor as loss.
    liquid=pl.m_l; withdrawn=mass0-pl.M_sl
    loss=withdrawn-liquid
    # Exact target crossing error <= one timestep of flow; normalize successful runs.
    norm=1000/liquid if not failed else 1.
    settling=elapsed # recorded acceleration maintained through all three phases
    prop=k['host_mass']*(-math.expm1(-1.05e-4*P.G0*settling/(k['isp']*P.G0)))
    return dict(label='COMPUTED (our model); rests on ASSUMPTION',case=case,
                failed=failed,delivered_liquid_kg=liquid,withdrawn_kg=withdrawn,
                lost_kg=loss*norm,normalization_factor=norm,phase_seconds=phase_t,
                total_minutes=elapsed/60,settling_seconds=settling,settling_propellant_kg=prop,
                dumped_kg=pl.dumped_overboard,vented_mixture_kg=pl.vented,
                receiver_vapor_change_kg=pl.m_v-gas0,max_pressure_Pa=max_pressure,
                mean_fill_flux_kg_m2s=sum(fill_flux)/len(fill_flux) if fill_flux else None,
                gate_checks=gate_checks,trace=rows,
                line_inventory_kg=sum(pl.line.mass),line_off_heat_J=pl.line.off_heat,
                line_heat_J=pl.line.wall_heat,line_local_mass_error_kg=pl.line.mass_error,
                line_local_energy_error_J=pl.line.energy_error,
                mass_balance_residual_kg=withdrawn-liquid-(pl.m_v-gas0)-pl.dumped_overboard-pl.vented-sum(pl.line.mass))


# D_COATING_T is in mm. Parse only the literal; never execute CAD.
cad_tree=ast.parse((ROOT/'../../cad/params.py').read_text())
CAD_T=next(ast.literal_eval(n.value) for n in cad_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='D_COATING_T' for t in n.targets))*.001
DEFAULT.update(coating_t=CAD_T,holdup_fraction=.25,drain_tau=3.,k_scale=1.,contact_R=0.,
               htc_scale=1.,wet_cap=100.,dnb_delta=15.,film_model='darr',pressure_control=True,
               vent_on=2.6e5,vent_off=2.2e5,spray_pause=2.9e5,spray_resume=2.4e5)

def summarize(runs):
    counts={}
    for a in runs:
        reason=a['failed'] or 'success'; counts[reason]=counts.get(reason,0)+1
    n=len(runs); f=n-counts.get('success',0); z=1.96; ph=f/n
    ce=(ph+z*z/(2*n))/(1+z*z/n); ra=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/(1+z*z/n)
    good=[a['lost_kg'] for a in runs if not a['failed']]
    return dict(n=n,failed_or_aborted=f,failure_rate=ph,counts=counts,
                wilson95=[max(0,ce-ra),min(1,ce+ra)],
                successful_loss_range_kg=[min(good),max(good)] if good else None,runs=runs)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--samples',type=int,default=40);ap.add_argument('--dt',type=float,default=.1)
    args=ap.parse_args(); started=time.time(); cpu=time.process_time()
    if args.samples<1 or args.dt<=0: ap.error('positive samples and dt required')
    # Literal v1 draws, not a new generator or changed discrepancy distribution.
    before=json.loads((ROOT/'results.json').read_text()); draws=before['uncertainty_draws'][:args.samples]
    if len(draws)!=args.samples: ap.error('samples exceed retained v1 paired draws')
    from validation_v2 import validate
    validation=validate(); (ROOT/'validation_v2.json').write_text(json.dumps(validation,indent=2))
    print('VALIDATION',validation['passed'],validation['computed_mass_saving_percent'],flush=True)
    sizes=[]
    # Search finite engineering domain, then refine locally; never claim global optimum.
    for mm in range(8,41,2):
        a=simulate('L5',{'diameter':mm/1000},dt=args.dt)
        sizes.append(dict(diameter_mm=mm,objective_kg=a['lost_kg']+a['settling_propellant_kg'],result=a))
    best=min((a for a in sizes if not a['result']['failed']),key=lambda a:a['objective_kg'])
    for j in range(-9,10):
        mm=best['diameter_mm']+j*.2
        if not 8<=mm<=40: continue
        a=simulate('L5',{'diameter':mm/1000},dt=args.dt)
        sizes.append(dict(diameter_mm=mm,objective_kg=a['lost_kg']+a['settling_propellant_kg'],result=a))
    best=min((a for a in sizes if not a['result']['failed']),key=lambda a:a['objective_kg'])
    DEFAULT['diameter']=best['diameter_mm']/1000
    print('SIZE',best['diameter_mm'],best['objective_kg'],flush=True)
    nominal={};stops={};mc={}
    for case in CASES:
        a=simulate(case,dt=args.dt,trace=True);nominal[case]=a;stops[case]=a['phase_seconds']
        print('nominal',case,a['lost_kg'],a['total_minutes'],a['failed'],flush=True)
    for case in CASES:
        runs=[simulate(case,dt=args.dt,initial_error=e,stops=stops[case]) for e in draws]
        mc[case]=summarize(runs);print('MC',case,mc[case]['counts'],flush=True)
        (ROOT/'checkpoint_v2.json').write_text(json.dumps(dict(nominal=nominal,monte_carlo=mc)))
    controls={}
    for case in ('L4','ALL'):
        a=simulate(case,{'pressure_control':False},dt=args.dt)
        controls[case]=dict(nominal=a,monte_carlo=summarize([simulate(case,{'pressure_control':False},dt=args.dt,initial_error=e,stops=a['phase_seconds']) for e in draws]))
        print('control before',case,controls[case]['monte_carlo']['counts'],flush=True)
    ranges={'coating_t':('L1',[15.12e-6,50e-6,60.48e-6,105.84e-6]),
            'k_scale':('L1',[.5,1.,2.]),'contact_R':('L1',[0.,1e-4,5e-4]),
            'holdup_fraction':('L2',[0.,.05,.25,.75]),'drain_tau':('L2',[.3,3.,30.]),
            'htc_scale':('C0',[.5,1.,2.]),'wet_cap':('L1',[60.,100.,140.]),
            'dnb_delta':('C0',[5.,15.,30.]),'boiling_model':('C0',['legacy']),
            'film_model':('C0',['darr','purdue']),
            'duty':('L2',[.07,.1,.2]),'period':('L2',[2.,3.]),
            'adaptive_low':('L3',[.07,.1,.2]),'adaptive_high':('L3',[.3,.5,1.]),
            'adaptive_span':('L3',[50.,100.,150.]),'spray_period':('L4',[.5,1.,2.]),
            'spray_duty':('L4',[.4,.5,.7]),'spray_hA':('L4',[1000.,3000.,6000.]),
            'spray_gain':('L4',[1.,1.5,2.13]),'conductance_power':('L5',[0.,2.,2.5]),
            'fixed_margin':('C0',[3.,5.,10.]),'hold':('C0',[10.,30.,60.]),
            'gate_margin':('ALL',[0.,3.,5.,10.]),
            'vent_on':('L4',[2.4e5,2.6e5,2.8e5]),'vent_off':('L4',[2e5,2.2e5,2.4e5]),
            'spray_pause':('L4',[2.7e5,2.9e5,3.1e5]),'spray_resume':('L4',[2.2e5,2.4e5,2.6e5])}
    sweeps={key:[dict(value=v,result=simulate(case,{key:v},dt=args.dt)) for v in vs] for key,(case,vs) in ranges.items()}
    # Re-optimize coarse diameter under alternative hydraulic laws and host assumptions.
    sizing_sensitivity=[]
    for key,vs in {'conductance_power':[0.,2.],'host_mass':[5000.,20000.],'isp':[100.,300.]}.items():
        for v in vs:
            curve=[]
            for mm in range(8,41,4):
                a=simulate('L5',{key:v,'diameter':mm/1000},dt=args.dt)
                curve.append(dict(diameter_mm=mm,objective_kg=a['lost_kg']+a['settling_propellant_kg'],failed=a['failed']))
            good=[x for x in curve if not x['failed']]
            sizing_sensitivity.append(dict(parameter=key,value=v,curve=curve,best=min(good,key=lambda x:x['objective_kg']) if good else None))
    fine={c:simulate(c,dt=args.dt/2) for c in ('C0','ALL')}
    allruns=list(nominal.values())+[r for m in mc.values() for r in m['runs']]
    residual=max(abs(a['mass_balance_residual_kg']) for a in allruns)
    assert residual<1e-6,residual
    import CoolProp
    data=dict(property_version=CoolProp.__version__,label='COMPUTED; NOT EXPERIMENTALLY VALIDATED',validation=validation,config=DEFAULT,
              dt=args.dt,seed=261,source_sha256=HASHES,nominal=nominal,monte_carlo=mc,
              uncertainty_draws=draws,before_v1={k:before[k] for k in ['nominal','monte_carlo','config']},
              pressure_control_off=controls,sensitivity=sweeps,sizing=dict(search=sizes,best=best,sensitivity=sizing_sensitivity,
              objective='lost LOX kg + settling propellant kg; nominal successful completed transfers; 8--40 mm bounded search'),
              timestep_check=fine,max_mass_balance_residual_kg=residual,
              cpu_seconds=time.process_time()-cpu,wall_seconds=time.time()-started)
    (ROOT/'results_v2.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    from report_v2 import report
    report(data)
    print('DONE CPU',data['cpu_seconds'],flush=True)
if __name__=='__main__': main()
