import cadquery as cq, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
fig,ax=plt.subplots(figsize=(6,10))
pl=gp_Pln(gp_Pnt(0,0,0),gp_Dir(0,1,0))
for n,c in (('coupling_a','tab:blue'),('coupling_b','tab:orange')):
    s=cq.importers.importStep(f'../../../cad/out/{n}.step')
    for i,so in enumerate(s.solids().vals()):
        b=so.BoundingBox()
        if b.xmax<0 or b.xmin>45 or b.ymin>0.1 or b.ymax<-0.1: continue
        sec=BRepAlgoAPI_Section(so.wrapped,pl); sec.Build()
        for e in cq.Shape.cast(sec.Shape()).Edges():
            pts=[e.positionAt(t) for t in [k/30 for k in range(31)]]
            xs=[p.x for p in pts]
            if max(xs)<-0.01: continue
            ax.plot(xs,[p.z for p in pts],c,lw=.7)
        ax.text(max(0,b.xmin)+.3,(b.zmin+b.zmax)/2,f'{n[-1]}{i}',fontsize=5)
ax.set_aspect('equal');ax.set_xlim(0,45);ax.set_ylim(250,365);ax.grid(alpha=.3)
plt.savefig('profile.png',dpi=110)
