"""COMPUTED finite liquid holdup / quasi-steady radial coating conduction.
Source equations and explicit approximation boundaries: SOURCES.md v2.
"""
import math
from functools import lru_cache
from CoolProp.CoolProp import PropsSI

@lru_cache(None)
def sat(fluid, pbin):
    p=pbin*10000.
    def f(k,q=0): return PropsSI(k,'P',p,'Q',q,fluid)
    return dict(p=p,T=f('T'),rl=f('D'),rv=f('D',1),hl=f('H'),hv=f('H',1),
                kl=f('L'),kv=f('L',1),ml=f('V'),mv=f('V',1),cp=f('C'),cpg=f('C',1),
                sig=f('surface_tension'),tc=PropsSI('Tcrit',fluid),pc=PropsSI('pcrit',fluid))

def properties(fluid,p): return sat(fluid,max(2,round(p/10000)))

@lru_cache(None)
def teflon(Tbin):
    z=math.log10(max(4,min(300,Tbin)))
    return 10**sum(a*z**i for i,a in enumerate((2.738,-30.677,89.430,-136.99,124.69,-69.556,23.320,-4.3135,.33829)))

def db(G,D,mu,k,cp):
    re=max(G*D/mu,1.)
    return max(3.66,.023*re**.8*(cp*mu/k)**.4)*k/D

def darr_film(s,G,D,L,T,x,g):
    # N7 slide 9: actual-quality blend and combined IAF/DF correlation.
    re=max(G*D/s['ml'],1.); K=5.26e-5*re+.1
    xe=max(1e-6,x)
    xa=(xe**(-K)+1)**(-1/K)
    rev=max(G*D/s['mv'],1.); prv=s['cpg']*s['mv']/s['kv']
    # HEM viscosity is an explicit approximation to the slide's Re_tp.
    mutp=1/((1-min(1,xe))/s['ml']+min(1,xe)/s['mv'])
    retp=max(G*D/mutp,1.)
    ndf=.015*retp**.8774*prv**.6112
    # Slide prints a dimensional natural-convection HTC term; convert to Nu.
    hn=.06*(s['rv']*(s['rl']-s['rv'])*g*(s['hv']-s['hl'])*s['kv']**3 /
             (L*s['mv']*max(T-s['T'],.1)))**.25
    niaf=.0151*(1-xa)**4*rev**.8*prv**.8+hn*D/s['kv']
    return (niaf**.75+ndf**.75)**(4/3)*s['kv']/D

@lru_cache(200000)
def nb_cached(fluid,pbin,Gbin,D,delta_bin,xbin,g):
    # Purdue/GRC 2024 eqs 19--29, reduced gravity formulation, implicit in q.
    s=sat(fluid,pbin); G=max(1.,Gbin); d=max(.1,delta_bin); x=max(.001,min(.95,xbin))
    hfg=s['hv']-s['hl']; pr=s['cp']*s['ml']/s['kl']; we=G*G*D/(s['rl']*s['sig'])
    hsp=db(G*(1-x),D,s['ml'],s['kl'],s['cp'])
    xtt=((1-x)/x)**.9*(s['rv']/s['rl'])**.5*(s['ml']/s['mv'])**.1
    hecb=7*hsp*(1/xtt)**.39*(s['rl']/s['rv'])**(-.34)
    dp=d*hfg/(s['T']*(1/s['rv']-1/s['rl']))
    rb=d/(hfg*s['rv'])*math.sqrt(2*math.pi*s['kl']*s['rl']*s['cp']*s['sig']/dp)* (s['rl']/dp)**.25
    ja=s['cp']*d/hfg; reb=math.pi/pr*(s['rl']/s['rv'])**2*ja**2
    hpb=.0015*reb**.62*pr**.33*s['kl']/max(rb,1e-12)
    fr=(G+800)**2/(s['rl']**2*max(9.80665-g,1e-8)*D)
    fac=(1.36 if s['p']/s['pc']<=.41 else 1.2)*math.tanh(9.80665/max(g,1e-9))*(1+1/fr)**7.48
    def rhs(q):
        bo=q/(G*hfg)
        suppression=(1/(1+1000*math.exp(min(700,bo*bo*we))))**.475 if s['p']/s['pc']<=.41 else 1
        return d*math.hypot(hpb*fac*suppression,hecb)
    lo,hi=0.,1e8
    for _ in range(26):
        q=(lo+hi)/2
        if q>rhs(q): hi=q
        else: lo=q
    return (lo+hi)/2/d

class Line:
    def __init__(self,fluid,D,L,A,mwall,volume,thickness=0.,cfg=None,g=1.05e-4*9.80665):
        self.fluid=fluid; self.D=D; self.L=L; self.A=A; self.mwall=mwall; self.V=volume
        self.t=thickness; self.k=cfg or {}; self.g=g; self.mass=[0.]*5; self.hold_h=[0.]*5; self.wet=[False]*5
        self.off_heat=0.; self.wall_heat=0.; self.max_mass=0.; self.mass_error=0.; self.energy_error=0.
    def advance(self,Tw,dt,mdot,hin,p,cpwall,qenv=0.):
        s=properties(self.fluid,p); ts=s['T']; hfg=s['hv']-s['hl']; hl=s['hl']; hv=s['hv']
        m=mdot*dt; h=hin; G=mdot/(math.pi*self.D**2/4); oldmass=sum(self.mass)
        for i in range(5):
            stored=self.mass[i]; area=self.A/5; mw=self.mwall/5
            if m<=1e-14 and stored<=1e-14:
                Tw[i]+=qenv/5*dt/(mw*cpwall(Tw[i])); continue
            x=max(0.,min(1.,(h-hl)/hfg)) if m else 0.
            # Residual boiling has no inlet G: use inventory drain-equivalent flux.
            geff=max(G,stored/max(self.k.get('drain_tau',3.),.01)/(math.pi*self.D**2/4))
            tf=ts if h>=hl or not m else ts+(h-hl)/s['cp']
            wetT=.844*s['tc']*(1+.060*(max(geff,1)**2*self.D/(s['rl']*s['sig']))**.208)
            wetT=min(ts+self.k.get('wet_cap',100.),wetT) # ASSUMPTION extension LH2 -> O2/N2
            film=darr_film(s,max(geff,1.),self.D,self.L,Tw[i],x,self.g)
            if self.k.get('film_model','darr')=='purdue':
                # Purdue eq 43, Bo* local quality ratio, DFFB only.
                film=.52*db(max(geff*x,1),self.D,s['mv'],s['kv'],s['cpg'])*max(x,.01)**(-.32)
            R=self.t/teflon(round((Tw[i]+ts)/2))*self.k.get('k_scale',1.)**-1+self.k.get('contact_R',0.) if self.t else 0.
            surf=(Tw[i]+film*R*tf)/(1+film*R)
            if surf<=wetT: self.wet[i]=True
            if self.wet[i]:
                # NB at CHF anchor, Darr linear heat-flux interpolation for TB.
                dn=self.k.get('dnb_delta',15.)
                hnb=nb_cached(self.fluid,round(s['p']/10000),round(max(geff,1)/25)*25,self.D,round(min(max(surf-ts,.5),dn)*2)/2,round(x*20)/20,self.g)
                if surf>ts+dn:
                    hfb_wet=darr_film(s,max(geff,1.),self.D,self.L,wetT,x,self.g) if self.k.get('film_model','darr')=='darr' else film
                    qfb=hfb_wet*(wetT-ts); qnb=hnb*dn
                    flux=qfb+(qnb-qfb)*max(0,min(1,(wetT-surf)/max(wetT-ts-dn,1)))
                    hc=max(film,flux/max(surf-ts,.1))
                else: hc=hnb if surf>ts+2 else db(max(geff,1),self.D,s['ml'],s['kl'],s['cp'])
            else: hc=film
            if self.k.get('boiling_model')=='legacy':
                hc=200. if Tw[i]-ts>40 else (3000. if Tw[i]-ts>3 else 1000.)
            hc*=self.k.get('htc_scale',1.)
            q=area*(Tw[i]-tf)/(1/max(hc,1e-6)+R)
            q=max(0.,min(q,.5*mw*cpwall(Tw[i])*max(Tw[i]-tf,0)/dt))
            # Only stored liquid + incoming enthalpy can accept heat. Vapor can superheat.
            cap=(stored*hfg+m*max(hv-h,0)+m*s['cpg']*max(Tw[i]-ts,0))/dt
            q=min(q,cap)
            E=stored*(self.hold_h[i]-hl)+m*(h-hl)+q*dt
            pool=stored+m
            target=self.V/5*s['rl']*self.k.get('holdup_fraction',.25)
            if E<0: # mixed subcooled liquid: retain its sensible energy, too
                new=min(pool,target)
                if mdot<=0: new*=math.exp(-dt/self.k.get('drain_tau',3.))
                mout=max(0,pool-new); hout=hl+E/max(pool,1e-14); hstored=hout
            else:
                liquid=max(0,pool-E/hfg)
                new=min(liquid,target)
                # Inventory drains even when no new liquid arrives.
                if mdot<=0: new*=math.exp(-dt/self.k.get('drain_tau',3.))
                mout=max(0,pool-new)
                hout=hl+E/mout if mout>1e-14 else hl
                hstored=hl
            self.mass[i]=new
            self.energy_error=max(self.energy_error,abs(stored*self.hold_h[i]+m*h+q*dt-new*hstored-mout*hout))
            self.hold_h[i]=hstored
            Tw[i]+=(qenv/5-q)*dt/(mw*cpwall(Tw[i]))
            self.wall_heat+=q*dt
            if mdot<=0: self.off_heat+=q*dt
            m,h=mout,hout
        self.max_mass=max(self.max_mass,sum(self.mass))
        self.mass_error=max(self.mass_error,abs(oldmass+mdot*dt-sum(self.mass)-m))
        return m/dt,h
