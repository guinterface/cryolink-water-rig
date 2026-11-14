import cadquery as cq, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
s=cq.importers.importStep('fluid_c0.step')
fig,axs=plt.subplots(1,2,figsize=(10,10))
for ax,c,col in zip(axs,s.solids().vals(),('tab:blue','tab:red')):
  for ang,dirv in ((0,(0,1,0)),):
    sec=BRepAlgoAPI_Section(c.wrapped,gp_Pln(gp_Pnt(0,0,0),gp_Dir(*dirv)));sec.Build()
    for e in cq.Shape.cast(sec.Shape()).Edges():
        p=[e.positionAt(t/30) for t in range(31)]; ax.plot([q.x for q in p],[q.z for q in p],col,lw=.7)
  ax.set_aspect('equal');ax.grid(alpha=.3);ax.set_title(str(round(c.Volume())))
  for f in c.Faces():
    cc=f.Center()
    if abs(cc.z-255.2)<1e-3 or abs(cc.z-354.2)<1e-3: print(round(c.Volume()),'cap face z',round(cc.z,1),'area',round(f.Area(),1), 'bbox r', round(f.BoundingBox().xmax,1))
plt.savefig('fluid_sec.png',dpi=100)
