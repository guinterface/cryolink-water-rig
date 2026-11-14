"""Damping (Q) of the plate's first mode from a tap-test free decay.
Input: CSV with columns t_s, a_z (one accelerometer channel, e.g. ADXL343 over SPI at 3200 Hz).
Method: band-pass around the FE mode (default 60-110 Hz, FE predicts 69-85 Hz, sims/fea/v6),
then (1) log decrement of successive peaks and (2) half-power bandwidth of the spectrum (zero-padded FFT).
zeta = d/sqrt(4 pi^2 + d^2), Q = 1/(2 zeta); half-power Q = fn/(f2-f1).  (general knowledge, standard vibration texts)
Run with --selftest to check the method on synthetic decays with known Q and noise."""
import numpy as np, sys, json
from scipy.signal import butter, sosfiltfilt, find_peaks
def q_estimate(t,a,band=(60,110)):
    fs=1/np.median(np.diff(t)); sos=butter(4,band,btype='band',fs=fs,output='sos'); y=sosfiltfilt(sos,a-a.mean())
    i0=int(np.argmax(np.abs(y))); y=y[i0:]; tt=t[i0:]-t[i0]
    pk,_=find_peaks(y); pk=pk[y[pk]>0]
    amp=y[pk]; keep=amp>0.1*amp[0]; pk,amp=pk[keep],amp[keep]          # use peaks above 10% of the first (noise floor)
    n=np.arange(len(amp)); d=-np.polyfit(n,np.log(amp),1)[0]            # mean log decrement per cycle
    fn=(len(pk)-1)/(tt[pk[-1]]-tt[pk[0]]) if len(pk)>2 else np.nan
    zeta=d/np.sqrt(4*np.pi**2+d**2); q_ld=1/(2*zeta)
    N=1<<18; F=np.abs(np.fft.rfft(y*np.ones_like(y),N)); f=np.fft.rfftfreq(N,1/fs)
    m=(f>band[0])&(f<band[1]); k=np.argmax(F*m); half=F[k]/np.sqrt(2)
    lo=k; hi=k
    while lo>0 and F[lo]>half: lo-=1
    while hi<len(F)-1 and F[hi]>half: hi+=1
    q_hp=f[k]/(f[hi]-f[lo])
    return dict(fs_hz=round(fs,1),fn_hz=round(float(f[k]),2),fn_peaks_hz=round(float(fn),2),cycles_used=int(len(pk)),Q_logdec=round(float(q_ld),2),Q_halfpower=round(float(q_hp),2))
def synth(Q,fn=82.0,fs=3200.0,T=1.5,noise=0.02,seed=0,f2=118.0):
    rng=np.random.default_rng(seed); t=np.arange(0,T,1/fs); z=1/(2*Q); wn=2*np.pi*fn; wd=wn*np.sqrt(1-z*z)
    a=np.exp(-z*wn*t)*np.sin(wd*t)+0.3*np.exp(-0.02*2*np.pi*f2*t)*np.sin(2*np.pi*f2*t)   # mode 1 + a second mode at 118 Hz (FE m2)
    a=np.concatenate([np.zeros(200),a])+noise*rng.standard_normal(len(a)+200)
    return np.arange(len(a))/fs,a
if __name__=='__main__':
    if '--selftest' in sys.argv:
        out=[]
        for Q in (5,10,15,20,30):
            for s in range(3):
                r=q_estimate(*synth(Q,seed=s)); r['Q_true']=Q; out.append(r); print(r)
        json.dump(out,open('selftest.json','w'),indent=1)
    else:
        d=np.genfromtxt(sys.argv[1],delimiter=',',names=True); print(q_estimate(d['t_s'],d['a_z']))
