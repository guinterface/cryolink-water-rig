import cadquery as cq, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
from matplotlib.patches import Polygon
fig,ax=plt.subplots(figsize=(7,9))
cols=plt.cm.tab20.colors
k=0
for n in ('coupling_a','coupling_b'):
  for i,so in enumerate(cq.importers.importStep(f'../../../cad/out/{n}.step').solids().vals()):
    b=so.BoundingBox()
    if b.xmax<0 or b.xmin>50 or b.ymin>0 or b.ymax<0: continue
    sec=BRepAlgoAPI_Section(so.wrapped,gp_Pln(gp_Pnt(0,0,0),gp_Dir(0,1,0)));sec.Build()
    w=cq.Shape.cast(sec.Shape())
    try:
      ws=cq.Wire.combine(w.Edges())
      for wi in ws:
        pts=[v for e in wi.Edges() for v in [e.positionAt(t/8) for t in range(9)]]
        pp=[(p.x,p.z) for p in pts if p.x>-0.01]
        if len(pp)>2: ax.add_patch(Polygon(pp,closed=True,fc=cols[k%20],alpha=.55,ec='k',lw=.3))
    except Exception as e: print(n,i,e)
    ax.text(max(b.xmin,0)+.5,b.zmin+.5,f'{n[-1]}{i}',fontsize=6); k+=1
ax.set_xlim(0,50);ax.set_ylim(250,365);ax.set_aspect('equal');ax.grid(alpha=.3)
plt.savefig('solids_sec.png',dpi=110)
