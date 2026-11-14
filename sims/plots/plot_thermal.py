import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
BG='#030406'; FG='#E9EDF1'; MU='#7C8794'; AC='#4F8EF7'; HT='#D6A15E'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'axes.edgecolor':MU,'axes.labelcolor':FG,'xtick.color':MU,'ytick.color':MU,'text.color':FG,'font.size':10,'axes.grid':True,'grid.color':'#1b222c','grid.linewidth':.6})
r=json.load(open('../thermal/nvf_results.json'))['runs']
fig,ax=plt.subplots(figsize=(7,3.6))
cols={'100':AC,'150':'#8fb6ff','200':HT,'293':'#e26d5a'}
for k,v in r.items():
    t=np.array(v['t'])/60; ax.plot(t,v['p'],color=cols[k],lw=1.6,label=f'tank wall starts at {k} K')
ax.axhline(4.0,color=MU,ls='--',lw=1); ax.text(0.5,4.08,'4.0 bar supply / relief set',color=MU,fontsize=8)
ax.set_xlabel('time (min)'); ax.set_ylabel('client tank pressure (bar)'); ax.set_xlim(0,62); ax.set_ylim(0,4.6)
ax.legend(frameon=False,fontsize=8,loc='center right'); ax.set_title('No-vent fill, 1,000 kg LOX in 1 h (equilibrium model)',fontsize=10,loc='left')
fig.tight_layout(); fig.savefig('nvf_pressure.png',dpi=160)
c=json.load(open('../thermal/chilldown_results.json'))
fig,ax=plt.subplots(figsize=(7,3.6))
for key,col in [('rewet +60 K | full flow, continuous',HT),('rewet +60 K | full flow, pulsed 3 s/10%',AC),('rewet +60 K | 10% flow, continuous','#8fb6ff')]:
    h=np.array(c[key]['hist']); ax.plot(h[:,0],h[:,1],color=col,lw=1.6,label=key.split('| ')[1]+f" ({c[key]['used']:.1f} kg through line)")
ax.axhline(105.7+5,color=MU,ls='--',lw=1); ax.text(0.2,113,'saturation + 5 K',color=MU,fontsize=8)
ax.set_xlabel('time (s)'); ax.set_ylabel('hottest line wall (K)'); ax.set_xscale('symlog',linthresh=10); ax.set_ylim(90,300)
ax.legend(frameon=False,fontsize=8,loc='upper right'); ax.set_title('Line chilldown, 3 m of 1 in 304 stainless',fontsize=10,loc='left')
fig.tight_layout(); fig.savefig('chilldown_wall.png',dpi=160); print('ok')
