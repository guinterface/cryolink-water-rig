"""V2 local artifacts only; one report table."""
import json,math,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/".mplconfig"))

def report(d):
    d['validation']['fixture_heat_leak_sensitivity']=json.loads((ROOT/'validation_supplement_v2.json').read_text())
    d['numerical_checks']=json.loads((ROOT/'checks_v2.json').read_text())
    import hashlib
    expected=json.loads((ROOT/'v1_hashes_v2.json').read_text())
    d['v1_preserved']=all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in expected.items())
    d['implementation_sha256']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run_v2.py','physics_v2.py','validation_v2.py','report_v2.py']}
    assert d['v1_preserved']
    (ROOT/'results_v2.json').write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
    v=d['validation']; checks=json.loads((ROOT/'checks_v2.json').read_text())
    lines=['# CryoLink lever study v2','',
           '**COMPUTED — experimental validation FAILED.** These are assumption-dependent comparisons with the conventional C0 method. They do not demonstrate flight savings or establish an exclusive invention.','',
           'Validation was run before the CryoLink sizing search and lever simulations. The independent LN2 fixture uses the published 0.914 m long, 12.7 mm OD, 0.51 mm wall tube, a 60.48 µm four-layer coating, 0.05 g, and F2/F28 mass fluxes. F28 uses 3 s / 10% pulses. It uses the same line solver and heat-transfer functions as CryoLink; it does not use receiver physics or any imposed saving factor.']
    for a in v['experiments']:
        lines+=['',f"{a['case']}: predicted {a['time_s']:.2f} s versus {a['measured_time_s']:.2f} s measured ({a['time_error_percent']:+.1f}%), and {a['outlet_mass_kg']:.4f} kg discharged versus {a['measured_outlet_mass_kg']:.4f} kg ({a['mass_error_percent']:+.1f}%). The paper states 2.1% time and 2.5% mass uncertainty; this case {'passes' if a['within_experimental_error'] else 'fails'}. Off-pulse wall cooling is {a['off_pulse_heat_J']:.0f} J."]
    lines+=['',f"The predicted paired mass saving is {v['computed_mass_saving_percent']:.1f}%. The paper's table gives 68.6% from 0.872 kg and 0.274 kg; its narrative gives about 75–76%. Neither number was used to fit the model. The approximately 67% 1 g / 20% duty comparison comes from a different experiment and was not simulated here.",
            '', 'This is an attempted reproduction with incomplete boundary data: 293 K initial wall, 77 K inlet and a constant 325 kPa mean test-section pressure are ASSUMPTIONS. The F28 table footnote says its time-series mass-flow data are missing. Applying its listed final mass flux as valve-on flow is an ASSUMPTION, with 1/4/10× flow sensitivity retained. The outer-wall derivative end criterion is approximated by all wall nodes below local saturation +5 K and mean cooling slope below 0.5 K/s for 0.2 s. Pressure, starting temperature, residual inventory, drain time, inlet temperature, steel properties and end-criterion sensitivities are in validation_v2.json; fixture heat-leak bounds are in validation_supplement_v2.json and results_v2.json. A match obtained by selecting those free inputs would require a separate calibration and independent validation.',
            '', 'Before → after model: v1 has no residual-fluid state, a three-level assumed HTC curve, and coating represented by an 80 K rewet threshold. V2 carries liquid mass and enthalpy in each axial cell, vaporizes and drains residual inventory with the inlet shut, and routes that outflow to the receiver or dump. It computes radial coating resistance δ/k(T) with a separate fluid-facing surface temperature. Nominal thickness is CAD D_COATING_T = 50 µm; the paper thicknesses are swept. The layer uses a quasi-steady temperature gradient with no coating heat capacity; it is not a transient multilayer/contact-resistance reconstruction.',
            '', 'V2 uses the source-visible Darr–Hartwig film-boiling/rewet equations and linear transition heat-flux interpolation from N7, with Purdue/GRC reduced-gravity nucleate boiling equations (2024, Eqs. 19–29). The N7 slide leaves nucleate coefficients symbolic. The separate 2023 universal chilldown poster also leaves coefficients unspecified. V2 therefore uses a documented hybrid, with an assumed CHF-temperature anchor and bounded rewet extension, rather than claiming the complete validated correlation sets. Purdue DFFB Eq. 43 and the old assumed curve are explicit alternative sweeps. Saturated-property approximations, LH2-to-LN2/LOX use, oxygen extrapolation beyond the Purdue NB database, near-zero-flow extrapolation and the simple liquid-retention law remain unvalidated. Details and equation provenance are in SOURCES.md.',
            '', 'All cells below show **v1 → v2**. Loss, time and settling are nominal completed-transfer results; abort counts use the same paired 40 draws (or the requested subset). Failed attempts are retained raw in JSON and excluded from sizing minima. C0 is continuous bare-line transfer; L1 coating, L2 fixed pulses, L3 measured-temperature adaptive pulses, L4 receiver spray plus pressure control, L5 sizing, ALL combined. L4 retains the v1 assumed spray conductance enhancement; no resolved receiver-coating layer is claimed. L5/ALL also change from the v1 20 mm line to the v2 mass optimum, so this table compares complete studies rather than isolating physics alone. The ablations below separate the inventory, boiling-curve and pressure-control effects. The conventional study line remains the inherited 16 mm ID × 5 m / 4 kg metal model; the CAD bore and route are not substituted into that baseline.',
            '', '| Case | LOX lost kg / 1000 kg | Total min | Settling propellant kg | Aborted/failed MC |',
            '|---|---:|---:|---:|---:|']
    for c,a in d['nominal'].items():
        b=d['before_v1']['nominal'][c]; om=d['before_v1']['monte_carlo'][c]; nm=d['monte_carlo'][c]
        def fmt(a,k):return f"{a[k]:.2f}"+(' (partial failure)' if a['failed'] else '')
        lines.append(f"| {c} | {fmt(b,'lost_kg')} → {fmt(a,'lost_kg')} | {fmt(b,'total_minutes')} → {fmt(a,'total_minutes')} | {fmt(b,'settling_propellant_kg')} → {fmt(a,'settling_propellant_kg')} | {om['failed_or_aborted']}/{om['n']} → {nm['failed_or_aborted']}/{nm['n']} |")
    lines+=['','![COMPUTED v1 and v2 comparison](comparison_v2.png)']
    oldcurve=d['sensitivity']['boiling_model'][0]['result']
    nohold=d['sensitivity']['holdup_fraction'][0]['result']
    l2=d['nominal']['L2']
    lines+=['',f"Physics ablations, COMPUTED: with the v2 inventory solver but the legacy HTC curve, C0 loses {oldcurve['lost_kg']:.2f} kg and takes {oldcurve['total_minutes']:.2f} min (outcome {oldcurve['failed'] or 'success'}). L2 with zero liquid holdup loses {nohold['lost_kg']:.2f} kg and takes {nohold['total_minutes']:.2f} min (outcome {nohold['failed'] or 'success'}). Nominal L2 removes {l2['line_off_heat_J']:.0f} J between pulses, {100*l2['line_off_heat_J']/max(l2['line_heat_J'],1):.1f}% of its line-wall heat extraction over the complete transfer. These ablations distinguish the new mechanisms from the complete v1/v2 comparison."]
    for c in ('L4','ALL'):
        off=d['pressure_control_off'][c]['monte_carlo'];on=d['monte_carlo'][c]
        lines+=['',f"{c} controller ablation within v2: control off {off['failed_or_aborted']}/{off['n']} ({100*off['failure_rate']:.1f}%) failed/aborted, control on {on['failed_or_aborted']}/{on['n']} ({100*on['failure_rate']:.1f}%). Reasons off: {off['counts']}; on: {on['counts']}. This separates the controller change from changing line physics. The control opens/closes the receiver vent at 2.6/2.2 bar and pauses/resumes receiver spray at 2.9/2.4 bar. All four setpoints are ASSUMPTIONS with sweeps; the 3.8 bar abort is retained. Exact sensors and instantaneous valves limit what these counts establish. Each controller variant is commissioned with its own nominal fixed phase durations before applying the paired draws."]
    best=d['sizing']['best'];a=best['result']
    lines+=['',f"L5's bounded nominal minimum is {best['diameter_mm']:.1f} mm ID: {a['lost_kg']:.2f} kg lost LOX + {a['settling_propellant_kg']:.2f} kg settling propellant = {best['objective_kg']:.2f} kg. Search: 8–40 mm in 2 mm steps, then ±1.8 mm around the best coarse size in 0.2 mm steps. This is a sampled minimum in that domain, not a global optimum or a qualified line design. ALL uses the same selected size; ALL is not independently size-optimized. Diameter also scales line volume, wall area, metal mass and assumed hydraulic conductance ∝D^2.5. Alternative hydraulic exponents, host masses and Isp have separate coarse re-optimizations in JSON. An equal kilogram sum is the requested mass objective, not an economic valuation of two different propellants."]
    c=d['nominal']['C0'];a=d['nominal']['ALL']
    lines+=['',f"Under these assumptions ALL versus C0 changes LOX loss by {a['lost_kg']-c['lost_kg']:+.2f} kg, transfer time by {a['total_minutes']-c['total_minutes']:+.2f} min, and settling propellant by {a['settling_propellant_kg']-c['settling_propellant_kg']:+.2f} kg. Because LN2 validation failed, these values cannot support a quantitative product-performance pitch. The source experiment supports the coating/pulsing mechanism relative to conventional chilldown; this study has not established its LOX system benefit. Coating alone increases nominal loss relative to v2 C0, so resolving the conduction layer has not reproduced the published coating advantage.",
            '', 'The Monte Carlo is the exact v1 seed-261 draw array: independent initial-wall discrepancy at both line ends and receiver, Gaussian mapping of an assumed 22–28% mean absolute discrepancy, clipped to −45/+65%. Fixed phase durations are recommissioned once under v2 nominal physics and frozen for MC; L3/ALL respond to wall temperature. These are stress-test frequencies under that assumed distribution, not flight reliability. Valve on-times are quantized to the timestep; non-integral duty sweep settings and the adaptive schedule do not have exact continuous-time duties. Wilson intervals, successful-loss ranges, raw attempts and failure reasons are in results_v2.json. No attempts are silently discarded.',
            '', 'Bookkeeping: loss = tanker liquid withdrawn − final receiver liquid, including residual line liquid, dumps, vents and oxygen left in vapor. Initial receiver oxygen can condense, so small negative calculated loss is possible and is not creation of oxygen. Net delivery is 1000 kg; successful losses are normalized for timestep overshoot. Settling uses the inherited 1.05×10⁻⁴ g over all three phases, 10,000 kg host and 220 s Isp, with rocket-equation mass/Isp sensitivity. No docking or leak-check time is included.',
            '', f"Maximum oxygen mass-balance residual across nominal/MC attempts: {d['max_mass_balance_residual_kg']:.3g} kg. The local physics checks pass: residual liquid cools with inlet shut, empty cells do not cool, added coating resistance reduces film-regime flux, and cell mass/enthalpy accounting closes. These are numerical checks, not experimental validation."]
    for c,a in d['timestep_check'].items():
        n=d['nominal'][c];lines+=['',f"Half-step {c}: loss change {a['lost_kg']-n['lost_kg']:+.3f} kg, time change {a['total_minutes']-n['total_minutes']:+.3f} min; fine-step outcome {a['failed'] or 'success'}. This checks the selected nominal design; the diameter grid itself is not re-optimized at half-step."]
    lines+=['',f"Reproduce with `python check_v2.py > checks_v2.json` then `python run_v2.py --samples 40 --dt 0.1`. Requires Python, CoolProp and matplotlib already installed here. Main run CPU {d['cpu_seconds']/60:.2f} min (excludes earlier source inspection, diagnostic runs and the small fixture supplement); wall {d['wall_seconds']/60:.2f} min. No source downloads are needed to rerun. V1 run.py, results.json, README.md and images are preserved. V2 reads the v1 plant snapshots and CAD thickness without changing FSW or CAD.",
            '', 'Context checked: v1 README/SOURCES/run/results and plant snapshots; CAD params.py; FSW README and research MOAT_BEYOND_1104/TECH_EDGE_1103; published line/spray text, N7 slides, Purdue/GRC 2024 equations and NIST coating data; HANDOFF_ALL, memory index, matching earlier project transcripts and read-only Crab inbox CryoLink search. No project handoff file was found in cryolink.']
    (ROOT/'README_v2.md').write_text('\n'.join(lines)+'\n')
    plot(d)

def plot(d):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cs=list(d['nominal']);xs=list(range(len(cs)));fig,axs=plt.subplots(2,2,figsize=(12,8))
    for i,(key,label) in enumerate([('lost_kg','LOX loss / 1000 kg (kg)'),('total_minutes','Transfer duration (min)')]):
        ax=axs[0,i]
        for shift,source,color,title in [(-.18,d['before_v1']['nominal'],'#89939b','v1'),(.18,d['nominal'],'#176c91','v2')]:
            ax.bar([x+shift for x in xs],[source[c][key] for c in cs],width=.36,label=title,color=color)
        ax.set_xticks(xs,cs);ax.set_ylabel(label);ax.legend();ax.grid(axis='y',alpha=.2)
    sizes=sorted(d['sizing']['search'],key=lambda a:a['diameter_mm']);good=[a for a in sizes if not a['result']['failed']]
    ax=axs[1,0];ax.plot([a['diameter_mm'] for a in good],[a['objective_kg'] for a in good],'.-',label='LOX + settling')
    b=d['sizing']['best'];ax.scatter([b['diameter_mm']],[b['objective_kg']],color='red',label=f"sampled minimum {b['diameter_mm']:.1f} mm")
    ax.set(xlabel='Line ID (mm)',ylabel='Total propellant mass cost (kg)');ax.legend();ax.grid(alpha=.2)
    ax=axs[1,1];ax.axis('off');v=d['validation']
    txt='LN2 VALIDATION: FAILED\n\n'
    for a in v['experiments']:
        txt+=f"{a['case']}\nTime error {a['time_error_percent']:+.1f}% (allowed ±2.1%)\nMass error {a['mass_error_percent']:+.1f}% (allowed ±2.5%)\n\n"
    txt+='CryoLink outputs are unvalidated estimates.'
    ax.text(.03,.97,txt,va='top',fontsize=11)
    fig.suptitle('COMPUTED — conventional-method comparison; experimental validation failed',fontsize=13)
    fig.tight_layout();fig.savefig(ROOT/'comparison_v2.png',dpi=170);plt.close(fig)
if __name__=='__main__':report(json.loads((ROOT/'results_v2.json').read_text()))
