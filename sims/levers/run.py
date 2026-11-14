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
    # Snapshot the physics only, retaining every original ASSUMPTION comment.
    dest = ROOT / 'plant_snapshot'
    dest.mkdir(exist_ok=True)
    hashes = {}
    for name in ['plant_sim.py', 'props.py', 'lox_table.py', 'common.py', 'chilldown_controller.py']:
        raw = (FSW/name).read_text()
        hashes[name] = hashlib.sha256(raw.encode()).hexdigest()
        (dest/name).write_text(raw)
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
    env=dict(math=math, P=p, C=c); exec(src,env)
    return env['Plant'],p,hashes

Plant,P,HASHES=load_plant()
CASES={'C0':(), 'L1':('coat',), 'L2':('pulse',), 'L3':('adaptive',),
       'L4':('spray',), 'L5':('size',), 'ALL':('coat','pulse','adaptive','spray','size','gate')}
DEFAULT=dict(rewet=80., duty=.10, period=3., adaptive_low=.10, adaptive_high=.50, adaptive_span=100.,
             spray_period=1., spray_duty=.4, spray_hA=3000., spray_gain=1.5, diameter=.020, conductance_power=2.5,
             fixed_margin=5., hold=30., gate_margin=5., host_mass=10000., isp=220.)

def simulate(case, cfg=None, dt=.1, initial_error=(0.,0.,0.), stops=None, trace=False):
    k=DEFAULT.copy(); k.update(cfg or {}); flags=CASES[case]
    pl=Plant(random.Random(0),receiver_volume=1000/(P.rho_l(90)*.95))
    pl.rewet_superheat=k['rewet'] if 'coat' in flags else 40.
    pl.Tw=[250*(1+initial_error[0]+(initial_error[1]-initial_error[0])*i/4) for i in range(5)]
    pl.Tw_rx=150*(1+initial_error[2]); pl.T_g=pl.Tw_rx
    # Bulk jet has no direct spray-wall term. Pool and ullage exchange remain.
    pl.hA_spray=k['spray_hA']*k['spray_gain'] if 'spray' in flags else 0.
    diameter=k['diameter'] if 'size' in flags else .016
    r=diameter/.016
    pl.A_line*=r; pl.V_line*=r*r; pl.m_line_wall*=r
    pl.cda_liq*=r**k['conductance_power']
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
        pr=pl.p_rx(); vent = pr>3.0e5 if vent else pr>3.5e5
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
                gate_checks=gate_checks,trace=rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--samples',type=int,default=40); ap.add_argument('--dt',type=float,default=.1)
    args=ap.parse_args()
    if args.samples < 1 or args.dt <= 0: ap.error('samples and dt must be positive')
    start=time.time(); cpu_start=time.process_time(); nominal={}; stops={}
    for case in CASES:
        a=simulate(case,dt=args.dt,trace=True); nominal[case]=a
        stops[case]=a['phase_seconds']
        print(case,round(a['lost_kg'],2),round(a['total_minutes'],2),a['failed'],flush=True)
    rng=random.Random(261)
    draws=[]
    for _ in range(args.samples):
        # MAPE is NOT a probability distribution. Gaussian mapping is an assumption.
        scale=rng.uniform(.22,.28)*math.sqrt(math.pi/2)
        draws.append(tuple(max(-.45,min(.65,rng.gauss(0,scale))) for i in range(3)))
    mc={}
    for case in CASES:
        runs=[simulate(case,dt=args.dt,initial_error=e,stops=stops[case]) for e in draws]
        counts={}
        for a in runs:
            reason=a['failed'] or 'success'; counts[reason]=counts.get(reason,0)+1
        n=len(runs); f=n-counts.get('success',0)
        mc[case]=dict(n=n,failed_or_aborted=f,failure_rate=f/n if n else None,counts=counts,runs=runs)
        print('MC',case,counts,flush=True)
    sweeps={}
    ranges={'rewet':('L1',[40,60,80,100,120]), 'duty':('L2',[.07,.1,.2]),
            'period':('L2',[2.,3.]), 'adaptive_low':('L3',[.07,.1,.2]),
            'adaptive_high':('L3',[.3,.5,1.]), 'adaptive_span':('L3',[50.,100.,150.]),
            'spray_period':('L4',[.5,1.,2.]), 'spray_duty':('L4',[.4,.5,.7]), 'spray_hA':('L4',[1000.,3000.,6000.]),
            'spray_gain':('L4',[1.,1.5,2.13]), 'diameter':('L5',[.012,.016,.020,.024]),
            'conductance_power':('L5',[0.,2.,2.5]),'fixed_margin':('C0',[3.,5.,10.]),
            'hold':('C0',[10.,30.,60.]),'gate_margin':('ALL',[0.,3.,5.,10.])}
    for key,(case,values) in ranges.items():
        sweeps[key]=[dict(value=v,result=simulate(case,{key:v},dt=args.dt)) for v in values]
    # Gate is bundled in ALL: explicit ablation keeps attribution visible.
    old=CASES['ALL']; CASES['ALL']=tuple(x for x in old if x!='gate')
    gate_off=simulate('ALL',dt=args.dt); CASES['ALL']=old
    fine={c:simulate(c,dt=args.dt/2) for c in ('C0','ALL')}
    for c,a in nominal.items():
        a['saved_lox_kg_vs_C0']=nominal['C0']['lost_kg']-a['lost_kg']
        a['saved_minutes_vs_C0']=nominal['C0']['total_minutes']-a['total_minutes']
        a['saved_settling_propellant_kg_vs_C0']=nominal['C0']['settling_propellant_kg']-a['settling_propellant_kg']
    host_sensitivity=[dict(case=c,host_mass_kg=m,isp_s=isp,settling_propellant_kg=m*(-math.expm1(-1.05e-4*a['settling_seconds']/isp))) for c,a in nominal.items() for m in (5000.,10000.,20000.) for isp in (100.,220.,300.)]
    data=dict(host_sensitivity=host_sensitivity,label='ALL RESULTS COMPUTED; all cases rest on ASSUMPTION',config=DEFAULT,
              dt=args.dt,seed=261,source_sha256=HASHES,nominal=nominal,monte_carlo=mc,
              uncertainty_draws=draws,sensitivity=sweeps,gate_off=gate_off,timestep_check=fine,
              reference_user_nominal=dict(withdrawn_kg=1007.4,delivered_kg=995.4,lost_kg=12.,line_s=506,receiver_s=277,fill_s=3400),
              cpu_seconds=time.process_time()-cpu_start,wall_seconds=time.time()-start)
    (ROOT/'results.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    finalize(data)

def finalize(data):
    # Paired Monte Carlo summaries; aborted attempts are never normalized to 1000 kg.
    for c,m in data['monte_carlo'].items():
        n=m['n']; f=m['failed_or_aborted']; z=1.96
        ph=f/n; center=(ph+z*z/(2*n))/(1+z*z/n)
        radius=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/(1+z*z/n)
        m['failure_rate_wilson95']=[max(0.,center-radius),min(1.,center+radius)]
        good=[r['lost_kg'] for r in m['runs'] if not r['failed']]
        good.sort()
        m['successful_loss_range_kg']=[good[0],good[-1]] if good else None
    # Oxygen mass conservation: liquid withdrawal equals net receiver oxygen +
    # dumped oxygen + vented oxygen (no He enters receiver in this harness).
    residuals=[]
    runs=list(data['nominal'].values())+[r for m in data['monte_carlo'].values() for r in m['runs']]
    for a in runs:
        residuals.append(abs(a['withdrawn_kg']-a['delivered_liquid_kg']-a['receiver_vapor_change_kg']-a['dumped_kg']-a['vented_mixture_kg']))
    data['validation']=dict(max_oxygen_mass_balance_residual_kg=max(residuals),all_nominal_success=all(not a['failed'] for a in data['nominal'].values()))
    assert max(residuals)<1e-6, max(residuals)
    (ROOT/'results.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    plots(data); report(data)

def plots(d):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cs=list(CASES); fig,axs=plt.subplots(1,2,figsize=(11,4))
    axs[0].bar(cs,[d['nominal'][c]['lost_kg'] for c in cs]); axs[0].set_ylabel('LOX lost / 1000 kg net liquid (kg)')
    bottom=[0.]*len(cs)
    for phase in ('line','receiver','fill'):
        values=[d['nominal'][c]['phase_seconds'].get(phase,0)/60 for c in cs]
        axs[1].bar(cs,values,bottom=bottom,label=phase); bottom=[a+b for a,b in zip(bottom,values)]
    axs[1].set_ylabel('Minutes'); axs[1].legend(); fig.suptitle('COMPUTED — assumption-based plant comparison'); fig.tight_layout(); fig.savefig(ROOT/'comparison.png',dpi=160); plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for c in ('C0','L3','ALL'):
        rows=d['nominal'][c]['trace']; axs[0].plot([r[0]/60 for r in rows],[r[1] for r in rows],label=c)
    axs[0].set(xlabel='Minutes',ylabel='Maximum line wall temperature (K)'); axs[0].legend()
    vals=d['sensitivity']['diameter']; axs[1].plot([1000*x['value'] for x in vals],[x['result']['total_minutes'] for x in vals],'o-')
    axs[1].set(xlabel='Assumed line diameter (mm)',ylabel='Total minutes (L5)')
    fig.suptitle('COMPUTED — controller trace and sizing sensitivity'); fig.tight_layout(); fig.savefig(ROOT/'sensitivity.png',dpi=160); plt.close(fig)

def report(d):
    lines=['# CryoLink transfer lever study','', 'All results below are **COMPUTED (our model)** and rest on **ASSUMPTION**. Comparison is against C0 conventional transfer, with the same plant, initial conditions and net-liquid target. No competitor performance is inferred.','',
    '| Case | LOX lost kg / 1000 kg | Total min | Settling propellant kg | Failed / aborted fills | LOX saved vs C0 kg |',
    '|---|---:|---:|---:|---:|---:|']
    for c,a in d['nominal'].items():
        m=d['monte_carlo'][c]; lines.append(f"| {c} | {a['lost_kg']:.2f} | {a['total_minutes']:.2f} | {a['settling_propellant_kg']:.3f} | {m['failed_or_aborted']}/{m['n']} ({100*m['failure_rate']:.1f}%) | {a['saved_lox_kg_vs_C0']:.2f} |")
    a=d['nominal']['ALL']; c=d['nominal']['C0']
    lines += ['', f"Under nominal assumptions, ALL saves {a['saved_lox_kg_vs_C0']:.2f} kg LOX, {a['saved_minutes_vs_C0']:.2f} minutes and {a['saved_settling_propellant_kg_vs_C0']:.2f} kg host settling propellant per transfer. The larger line drives the time saving. L2 saves more LOX but takes longer; L3 trades some of that saving for a shorter chilldown. L4 aborts in {d['monte_carlo']['L4']['failed_or_aborted']}/{d['monte_carlo']['L4']['n']} trials and ALL in {d['monte_carlo']['ALL']['failed_or_aborted']}/{d['monte_carlo']['ALL']['n']}; the post-chill gate cannot prevent overpressure during chill. These findings support a design trade study, not a demonstrated flight performance claim.", '', 'Phase times (minutes), COMPUTED:', '']
    for c,a in d['nominal'].items():
        lines.append(f"- {c}: "+', '.join(f'{p} {t/60:.2f}' for p,t in a['phase_seconds'].items())+f"; settling {a['settling_seconds']/60:.2f}.")
    lines+=['','![Comparison](comparison.png)','','![Sensitivity](sensitivity.png)','','## Interpretation and scope','',
    'Positive savings mean less client LOX spent per 1000 kg net liquid retained. Negative values mean a penalty. Lever effects are one-at-a-time against C0; ALL includes interactions, so individual savings must not be added. No dollar saving is asserted without a client propellant price.',
    '','C0 is a bare line, continuous flow and fixed phase durations established by a nominal commissioning run; receiver cooling is bulk liquid/pool/ullage exchange without direct spray-wall heat transfer. Production C0/L1/L2/L4/L5 retain their commissioned durations under uncertainty. L3 uses measured maximum wall temperature, varies duty from 0.10 hot to 0.50 near rewet, and waits for wall readiness for 30 s. L4 uses receiver spray plus coating/pulsing; the line remains conventional. L5 increases line diameter and assumed hydraulic conductance; it does not impose a gain for crossing 700 kg/m²s. ALL combines these and an assumed wall-readiness gate.',
    '','The spray gain multiplies the spray heat-transfer conductance, not a measured total propellant-saving factor. Its LN2-to-LOX and coupon-to-tank mapping is an ASSUMPTION swept from 1 to 2.13. The coating is represented by an effective rewet-superheat threshold (40–120 K sweep), not a resolved coating conduction layer. Published LN2 mass savings are context, not direct multipliers applied to results.',
    '','Settling acceleration is the recorded plant value 1.05e-4 g. Host initial mass 10,000 kg and thruster Isp 220 s are ASSUMPTIONS. Settling is maintained throughout line chill, receiver chill and fill; propellant = M0 [1 − exp(−a t/(Isp g0))]. Mass sensitivity is linear; Isp sensitivity is provided by this equation (e.g. 100–300 s). Docking, leak check, top-off, purge and demating are excluded from every case.',
    '','Loss = tanker liquid withdrawn − final receiver liquid. This includes line dumps, vented oxygen and oxygen retained as receiver vapor; it is a client liquid-delivery cost, not solely oxygen ejected into space. Plant vent bookkeeping includes gas mixture mass and is not used as an oxygen loss meter. Net liquid target is 1000 kg; successful losses are scaled by 1000/actual delivery to remove timestep overshoot. Times and settling consumption refer to the simulated crossing (overshoot is recorded).',
    '','MC uses paired draws with seed 261. N7 reports LH2 wall-temperature MAPE, not a LOX probability distribution. We ASSUME independent initial-wall temperature discrepancies at the two line ends and receiver, interpolate axially, draw Gaussian errors with mean absolute fractional error uniformly 22–28%, and clip to −45%/+65%. This is an illustrative model-discrepancy stress test, not a validated reliability prediction. Sensors are exact here; model error is not sensor error. Failure means receiver pressure ≥3.8 bar, fill fraction >98% before 1000 kg, timeout at 16000 s, or a rejected gate. Wilson 95% binomial intervals and successful-run loss ranges are recorded in JSON; these describe sampling under the assumed distribution, not flight reliability. Counts combine aborted and unsuccessful attempts; the JSON records reasons and each run. A zero failure count does not establish zero risk.',
    '','The ALL gate is a conservative wall-readiness check, not NASA’s validated thermodynamic target-temperature model. It runs after receiver conditioning; it can be redundant. gate_off in results.json isolates its nominal effect. No extra saving is attributed to NASA’s reported 100% failure classification.',
    '','Reproduction: `python run.py --samples 40 --dt 0.1` (Python 3, matplotlib). Reads the original FSW files and saves exact snapshots plus SHA-256 hashes locally. Physics is extracted from the original Plant class without importing ROS or modifying fsw. Source downloads are not required to rerun. Default runtime is recorded in results.json. All assumptions and source quotations are in [SOURCES.md](SOURCES.md).',
    '','## Validation and baseline differences','',
    'This study reuses the Plant physics but uses a standalone sequencer. The user’s existing nominal run (1007.4 kg withdrawn, 995.4 kg delivered, 12 kg loss; 506/277/3400 s) uses pulsing and spray already, and is not C0. We do not calibrate C0 to those numbers or claim to reproduce ROS timing. The present target is net receiver liquid rather than the original delivered flow counter. Pressure control uses a simple common bang-bang supply regulator and common receiver vent hysteresis. The existing plant has no fluid holdup, two-phase hydraulic resistance or spatial receiver wall distribution. Off-pulse residual-fluid cooling is absent; this can penalize pulsing and prevents quantitative validation against the paper’s measured pulse advantage.',
    '']
    for c,a in d['timestep_check'].items():
        n=d['nominal'][c]; lines.append(f"Half-step check {c}: loss change {a['lost_kg']-n['lost_kg']:+.3f} kg; total time change {a['total_minutes']-n['total_minutes']:+.3f} min.")
    lines.append(f"Maximum oxygen mass-balance residual: {d['validation']['max_oxygen_mass_balance_residual_kg']:.2e} kg across nominal and Monte Carlo runs.")
    lines+=['','Sensitivity sweeps are saved in results.json for every unsourced lever parameter; failed sensitivity runs retain raw partial-attempt losses and must not be compared as completed 1000 kg transfers; they are scenario bounds, not confidence intervals. Host mass/Isp scaling is analytic. The nominal comparison cannot establish a flight-qualified saving.','',
    'Context checked: fsw/README.md, Plant/common/controller/property tables; research/MOAT_BEYOND_1104.md N1–N13, PEOPLE_RESEARCH_1104.md Q1–Q16, TECH_EDGE_1103.md; original line paper and spray paper, Kim thesis abstract, NASA N7 and RGCT slides. Work remained inside sims/levers.']
    (ROOT/'README.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__': main()
