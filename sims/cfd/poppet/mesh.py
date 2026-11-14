import gmsh, sys
H=float(sys.argv[1]); out=sys.argv[2]
gmsh.initialize(); gmsh.option.setNumber('General.Terminal',1); gmsh.option.setNumber('General.Verbosity',8)
gmsh.option.setNumber('Geometry.OCCFixSmallFaces',1); gmsh.option.setNumber('Geometry.OCCFixSmallEdges',1)
gmsh.model.occ.importShapes("fluid_int.step"); print("pre",[len(gmsh.model.occ.getEntities(k)) for k in (2,3)]); gmsh.model.occ.synchronize()
vols=gmsh.model.getEntities(3); print('vols',len(vols))
inl=[];outl=[];wall=[]
for d,t in gmsh.model.getEntities(2):
    x,y,z=gmsh.model.occ.getCenterOfMass(d,t)
    if abs(z-189.2)<1e-3: inl.append(t)
    elif abs(z-420.0)<1e-3: outl.append(t)
    else: wall.append(t)
print('inlet',inl,'outlet',outl,'walls',len(wall))
gmsh.model.addPhysicalGroup(2,inl,name='inlet'); gmsh.model.addPhysicalGroup(2,outl,name='outlet')
gmsh.model.addPhysicalGroup(2,wall,name='wall'); gmsh.model.addPhysicalGroup(3,[v[1] for v in vols],name='fluid')
gmsh.option.setNumber('Mesh.MeshSizeMax',H); gmsh.option.setNumber('Mesh.MeshSizeMin',H/20)
gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',20)
gmsh.option.setNumber('Mesh.Algorithm',6); gmsh.option.setNumber('Mesh.Algorithm3D',1)
gmsh.option.setNumber('General.NumThreads',16)
# coarser in the straight stubs
f=gmsh.model.mesh.field; b=f.add('Box')
f.setNumber(b,'VIn',H); f.setNumber(b,'VOut',2.2*H)
for k,v in (('XMin',-50),('XMax',50),('YMin',-50),('YMax',50),('ZMin',245),('ZMax',365),('Thickness',15)): f.setNumber(b,k,v)
f.setAsBackgroundMesh(b); gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
try:
    gmsh.model.mesh.generate(3)
except Exception:
    print('FAILED ENTITIES',gmsh.model.mesh.getLastEntityError(),flush=True)
    tags=gmsh.model.mesh.getLastNodeError()
    print('FAILED NODES',[(int(n),gmsh.model.mesh.getNode(int(n))[0].tolist()) for n in tags],flush=True)
    gmsh.write(out+'.failed_surface.msh')
    raise
gmsh.model.mesh.optimize('Netgen')
gmsh.option.setNumber('Mesh.MshFileVersion',2.2); gmsh.write(out)
n=gmsh.model.mesh.getElementsByType(4)[0]; print('tets',len(n))
gmsh.finalize()
