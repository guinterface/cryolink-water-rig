import cadquery as cq, sys
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
for n in ('coupling_a','coupling_b'):
    s=cq.importers.importStep(f'../../../cad/out/{n}.step')
    sols=s.solids().vals()
    bb=s.val().BoundingBox()
    print(n,len(sols),'bbox z',round(bb.zmin,1),round(bb.zmax,1),'x',round(bb.xmin,1),round(bb.xmax,1),'y',round(bb.ymin,1),round(bb.ymax,1))
    for i,so in enumerate(sols):
        b=so.BoundingBox()
        if abs(b.xmin)<40 and abs(b.ymin)<40:
            print(' ',i,round(b.xmin,1),round(b.xmax,1),round(b.ymin,1),round(b.ymax,1),round(b.zmin,1),round(b.zmax,1),round(so.Volume()))
