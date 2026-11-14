"""1-D chilldown of the 3 m transfer line (304 SS, 25.4 mm OD, 22 mm bore), continuous vs pulsed LOX flow.

Wall: N lumped segments, m*c(T) dT/dt = -q_conv + q_leak.
Fluid: quasi-steady march along the line each time step (fluid transit << wall time constant).
Heat transfer (ASSUMPTION, simplest defensible regimes):
  * wall superheat above T_REWET - Tsat: film boiling, Dittus-Boelter on vapor at film temperature
    with the mixture mass flux (a vapor-blanket lower bound; no gravity term, since microgravity);
  * below it: nucleate/transition, constant H_NUC;
  * single-phase liquid or vapor: Dittus-Boelter on local phase.
Valve closed: no flow, no convection (stagnant vapor neglected).
Sources: NIST 304 SS cp (trc.nist.gov cryogenics materials); CoolProp oxygen; pulse 3 s / 10% from design doc
(Hartwig et al. 2022). Chill complete when outlet fluid is within 5 K of saturation for 30 s (design doc 3.2).
"""
import numpy as np, json, sys
from CoolProp.CoolProp import PropsSI as P
F='Oxygen'; PL=4.0e5                      # line pressure ASSUMPTION (supply 4 bar)
L,DO,DI,N=3.0,0.0254,0.022,30             # m, design doc baseline
RHO_SS=8000.; MDOT=1000/3600              # kg/m3 SS304; kg/s baseline flow when open
T0=293.15; T_IN=90.19
TSAT=P('T','P',PL,'Q',0,F); HL=P('H','P',PL,'Q',0,F); HV=P('H','P',PL,'Q',1,F)
C=[22.0061,-127.5528,303.647,-381.0098,274.0328,-112.9212,24.7593,-2.239153,0]
def cp_ss(T): x=np.log10(np.clip(T,4,300)); return 10**sum(c*x**i for i,c in enumerate(C))
dx=L/N; Aw=np.pi*DI*dx; Ax=np.pi*DI**2/4
mw=RHO_SS*np.pi*(DO**2-DI**2)/4*dx
Q_LEAK=0.5*np.pi*DO*dx                    # W per segment, MLI 0.50 W/m2 (NTRS 20110014015)
# property tables vs temperature for vapor and liquid at PL
Tv=np.linspace(TSAT+0.5,300,300); Tl=np.linspace(70,TSAT-0.3,80)
def props(Tg,q):
    return [np.array([P(k,'T',T,'P',PL,F) for T in Tg]) for k in ('H','L','V','C')]
hv_,kv_,muv_,cpv_=props(Tv,1); hl_,kl_,mul_,cpl_=props(Tl,0)
def T_of_h(h):
    if h<=HL: return np.interp(h,hl_,Tl),0.0
    if h>=HV: return np.interp(h,hv_,Tv),1.0
    return TSAT,(h-HL)/(HV-HL)
def db(G,k,mu,cp):
    Re=G*DI/mu; Pr=mu*cp/k; return 0.023*Re**0.8*Pr**0.4*k/DI
def htc(Tw,Tf,x,G,T_rewet,h_nuc):
    """Regime from WALL superheat (a hot wall blankets even a subcooled liquid core with vapor)."""
    if G<=0: return 0.0
    Tfilm=min(300,max(TSAT+0.5,0.5*(Tw+TSAT)))
    hvap=db(G,np.interp(Tfilm,Tv,kv_),np.interp(Tfilm,Tv,muv_),np.interp(Tfilm,Tv,cpv_))
    if x>=1: return hvap                                   # all vapor: single-phase vapor convection
    if Tw>T_rewet: return hvap                             # film boiling
    if Tw>TSAT: return max(h_nuc,hvap)                     # transition / nucleate
    Tl_=min(Tf,TSAT-0.3); return db(G,np.interp(Tl_,Tl,kl_),np.interp(Tl_,Tl,mul_),np.interp(Tl_,Tl,cpl_))
def run(duty=1.0,period=3.0,T_rewet=TSAT+50,h_nuc=2000.,dt=0.02,tmax=3600,mdot=MDOT):
    Tw=np.full(N,T0); h_in=P('H','T',T_IN,'P',PL,F); t=0; used=0; ok=0; hist=[]; vap=0.0
    G=mdot/Ax
    while t<tmax:
        open_=(t%period)<duty*period-1e-9 if duty<1 else True
        hf=h_in; q=np.zeros(N); Tout=None
        if open_:
            for i in range(N):
                Tf,x=T_of_h(hf); hc=htc(Tw[i],Tf,x,G,T_rewet,h_nuc)
                q[i]=hc*Aw*(Tw[i]-Tf); q[i]=min(q[i],mw*cp_ss(Tw[i])*max(Tw[i]-Tf,0)/dt)   # cannot cool past the fluid in one step
                hf+=q[i]/mdot
            Tout,xo=T_of_h(hf); used+=mdot*dt; vap+=mdot*dt*min(max(xo,0),1)
        Tw+= (Q_LEAK-q)/(mw*cp_ss(Tw))*dt
        # criterion used here: every wall segment within 5 K of saturation (the doc's outlet-temperature test
        # passes immediately at full flow because the outlet stays subcooled liquid)
        if Tw.max()<=TSAT+5: ok+=dt
        else: ok=0
        if int(t/1.0)!=int((t-dt)/1.0) or t==0: hist.append((round(t,2),float(Tw.max()),float(Tw.mean()),float(Tout if Tout else np.nan),used))
        t+=dt
        if ok>=30: break
    return dict(t=t,used=used,vapor=vap,Twmax=float(Tw.max()),hist=hist)
if __name__=='__main__':
    E=sum(mw*np.trapezoid(cp_ss(np.linspace(TSAT,T0,200)),np.linspace(TSAT,T0,200)) for _ in range(N))
    print(f'Tsat at {PL/1e5:.0f} bar = {TSAT:.1f} K; wall mass {mw*N:.2f} kg; sensible energy 293K->Tsat {E/1e3:.0f} kJ')
    print(f'ideal minimum LOX (vapor leaves at wall start temp) {E/(P("H","T",T0,"P",PL,F)-P("H","T",T_IN,"P",PL,F)):.2f} kg; worst (vapor leaves saturated) {E/(HV-P("H","T",T_IN,"P",PL,F)):.2f} kg')
    out={}
    cases=[('full flow, continuous',1.0,MDOT),('full flow, pulsed 3 s/10%',0.1,MDOT),('10% flow, continuous',1.0,MDOT*0.1)]
    for Trw in [TSAT+30,TSAT+60,TSAT+100]:
        for name,duty,md in cases:
            r=run(duty=duty,T_rewet=Trw,mdot=md)
            key=f'rewet +{Trw-TSAT:.0f} K | {name}'; out[key]=r
            print(f'{key:42s}: wall cold at {r["t"]-30:7.1f} s, LOX through line {r["used"]:6.2f} kg, of which left as vapor {r["vapor"]:5.2f} kg')
    json.dump(out,open('chilldown_results.json','w'))
