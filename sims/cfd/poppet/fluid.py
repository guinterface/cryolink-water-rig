import cadquery as cq, json, sys, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"cad"))
import params as cadp
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.TopTools import TopTools_ListOfShape
Z0,Z1,ZT,ZIN=255.2,353.9,420.0,189.2
sol=[]
for n in ('coupling_a','coupling_b'):
    s=cq.importers.importStep(f'../../../cad/out/{n}.step')
    for so in s.solids().vals():
        b=so.BoundingBox()
        spring=abs(b.xmax-7.7)<0.1 and abs(b.xmin+7.7)<0.1
        if spring: print('skip spring',round(b.zmin,1),round(b.zmax,1)); continue
        if b.xmin<45 and b.xmax>-45 and b.ymin<45 and b.ymax>-45 and b.zmax>Z0 and b.zmin<Z1: sol.append(so)
# ASSUMPTION: mated seals are leak-tight -> solid annulus over the seal/interface gap
plug=cq.Solid.makeCylinder(30,10,cq.Vector(0,0,293))-cq.Solid.makeCylinder(18.3,10,cq.Vector(0,0,293))
sol.append(plug)
# ASSUMPTION: nominal seat-retention glands are sealed from the main flow.
# Cap their annular envelopes outside the original r18 chamber to avoid zero-thickness
# spring/contact ties in the fluid boundary. Actual CAD hardware is unchanged;
# separate coldfit_capacity.py records possible cold-filled gland hold-up.
F=cadp.COLDFIT
stack=F['collar_t']+F['wave_height']+F['retainer_t']
for back,side in [(290.,'A'),(326.,'B')]:
    zz=back if side=='A' else back-stack
    sol.append(cq.Solid.makeCylinder(F['retainer_ro'],stack,cq.Vector(0,0,zz)).cut(
        cq.Solid.makeCylinder(cadp.E2['chamber_r'],stack,cq.Vector(0,0,zz))))
# ASSUMPTION: 22 mm ID line tube butts into the r20 A socket (z 255-259) -> socket annulus r11..20 is tube wall
sol.append(cq.Solid.makeCylinder(20,4.2,cq.Vector(0,0,255.0))-cq.Solid.makeCylinder(11,4.2,cq.Vector(0,0,255.0)))
cyl=cq.Solid.makeCylinder(40,Z1-Z0,cq.Vector(0,0,Z0)).fuse(cq.Solid.makeCylinder(11,ZT-Z1+0.01,cq.Vector(0,0,Z1-0.01))).fuse(cq.Solid.makeCylinder(11,Z0-ZIN+0.01,cq.Vector(0,0,ZIN)))
a=TopTools_ListOfShape(); a.Append(cyl.wrapped); t=TopTools_ListOfShape()
for so in sol: t.Append(so.wrapped)
op=BRepAlgoAPI_Cut(); op.SetArguments(a); op.SetTools(t); op.SetFuzzyValue(1e-4); op.Build()
comps=cq.Shape.cast(op.Shape()).Solids()
info=[]
for i,c in enumerate(comps):
    caps=[(round(f.Center().z,1),round(f.Area(),1),round(max(abs(f.BoundingBox().xmax),abs(f.BoundingBox().xmin)),1)) for f in c.Faces() if abs(f.Center().z-ZIN)<1e-3 or abs(f.Center().z-ZT)<1e-3]
    if c.Volume()>50: print(i,round(c.Volume()),caps)
    info.append((c,caps))
best=[c for c,caps in info if any(abs(z-ZIN)<.1 and r<=11.1 for z,a,r in caps) and any(abs(z-ZT)<.1 and r<=20.1 for z,a,r in caps)]
print('interior components',len(best),[round(c.Volume()) for c in best])
assert len(best)==1, f'Need one connected inlet-outlet fluid component, got {len(best)}'
fluid=best[0].clean()
assert abs(fluid.Volume()-best[0].Volume())<best[0].Volume()*1e-6, 'BREP cleanup changed fluid volume'
assert fluid.isValid()
cq.exporters.export(cq.Workplane().add(fluid),'fluid_int.step')
case=Path('h1c');case.mkdir(exist_ok=True)
cq.exporters.export(cq.Workplane().add(fluid),str(case/'fluid_int.step'))
region=cq.Solid.makeCylinder(50,Z1-Z0,cq.Vector(0,0,Z0))
outer=cq.Solid.makeCylinder(50,Z1-302,cq.Vector(0,0,302)).cut(cq.Solid.makeCylinder(19,Z1-302,cq.Vector(0,0,302)))
vol=lambda s:sum(v.Volume() for v in s.Solids())/1000
metrics=dict(raw_boolean_volume_mm3=best[0].Volume(),cleanup_volume_delta_mm3=fluid.Volume()-best[0].Volume(),raw_faces=len(best[0].Faces()),cleaned_faces=len(fluid.Faces()),evidence='COMPUTED main CFD volume: nominal retention glands capped outside r18 flow bore; cold gland capacities reported separately; original two helical valve springs omitted as before',
    full_domain_with_stubs_cm3=vol(fluid),coupling_wetted_cm3=vol(fluid.intersect(region)),
    B_outer_pocket_r_gt_19mm_cm3=vol(fluid.intersect(outer)),
    B_outer_pocket_LOX_g=vol(fluid.intersect(outer))*1.14183,
    coupling_bounds_z_mm=[Z0,Z1],pocket_bounds_z_mm=[302,Z1],
    cad_sha256={n:hashlib.sha256(Path('../../../cad/out/'+n+'.step').read_bytes()).hexdigest() for n in ('coupling_a','coupling_b')})
(case/'volumes.json').write_text(json.dumps(metrics,indent=2))
print(json.dumps(metrics,indent=2))
