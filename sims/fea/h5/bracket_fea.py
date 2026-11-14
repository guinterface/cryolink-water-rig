"""FEA of mount plate G + supports (bracket.step) with CalculiX.
Units: mm, N, tonne, MPa, s.
Bonded: all bracket solids fused by gmsh fragment (shared nodes).
Masses of parts carried by the bracket are smeared into the solids that hold them (ASSUMPTION).
Boundary: plate bottom fixed within 10 mm of the four bolt centers at +/-225 mm (ASSUMPTION, host bolt pattern params.py).
Loads: 10 g axial, 17 g lateral X and Y, each separate -- bounding small-payload test factors,
SpaceX Rideshare Payload User's Guide v11 Table 6-4 (ASSUMPTION that they bound a component on a host).
"""
import gmsh, numpy as np, subprocess, re, sys, json, os
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
STEP=os.path.expanduser('~/Documents/zyxem/cryolink/cad/out/bracket.step')
CCX='<scratch>/sim_env/bin/ccx'
E,NU,RHO=68.9e3,0.33,2.70e-9          # Al 6061-T6 (MPa, -, t/mm3)
YIELD=276.0                            # MPa Al 6061-T6 typical yield
H=float(sys.argv[1]) if len(sys.argv)>1 else 6.0   # mesh size mm
# extra carried mass (kg) by solid index from bracket.step order
CARRIED={'rails':1.50+0.147,           # manifold body + relief valve (CHECKS.md)
         'ring':0.595,                 # coupling A
         'plate':0.39+0.12}            # avionics box + line (approx, on plate)
gmsh.initialize(); gmsh.option.setNumber('General.Terminal',0)
gmsh.model.occ.importShapes(STEP); gmsh.model.occ.synchronize()
vols=gmsh.model.getEntities(3)
info=[]
for d,t in vols:
    bb=gmsh.model.occ.getBoundingBox(d,t); m=gmsh.model.occ.getMass(d,t); info.append((t,bb,m))
out,omap=gmsh.model.occ.fragment(vols,[]); gmsh.model.occ.synchronize()
vols=gmsh.model.getEntities(3)
def group(t,bb):
    x0,y0,z0,x1,y1,z1=bb
    if z1<=8.5 and x1-x0>400: return 'plate'
    if z0>=255: return 'ring'
    if z1<=41 and z0>=7: return 'rails'
    if x1-x0<14 and y1-y0<14: return 'posts'
    return 'lock'
groups={}
for d,t in vols:
    bb=gmsh.model.occ.getBoundingBox(d,t); groups.setdefault(group(t,bb),[]).append(t)
vol={g:sum(gmsh.model.occ.getMass(3,t) for t in ts) for g,ts in groups.items()}
for g,ts in groups.items(): gmsh.model.addPhysicalGroup(3,ts,name=g)
gmsh.option.setNumber('Mesh.MeshSizeMax',H); gmsh.option.setNumber('Mesh.MeshSizeMin',H/4)
gmsh.option.setNumber('Mesh.ElementOrder',2); gmsh.option.setNumber('Mesh.HighOrderOptimize',1)
gmsh.model.mesh.generate(3)
ntags,coords,_=gmsh.model.mesh.getNodes(); X=coords.reshape(-1,3); nid=ntags.astype(int)
# elements per group
lines=['*NODE']+[f'{i},{x:.6f},{y:.6f},{z:.6f}' for i,(x,y,z) in zip(nid,X)]
eid=1; elsets={}
order=[0,1,2,3,4,5,6,7,9,8]   # gmsh tet10 -> ccx C3D10 node order
for g,ts in groups.items():
    lines.append(f'*ELEMENT,TYPE=C3D10,ELSET=E_{g}'); elsets[g]=0
    for t in ts:
        et,etags,enodes=gmsh.model.mesh.getElements(3,t)
        for k,ty in enumerate(et):
            if ty!=11: continue
            en=enodes[k].astype(int).reshape(-1,10)
            for row in en:
                lines.append(f'{eid},'+','.join(str(row[j]) for j in order)); eid+=1; elsets[g]+=1
nel=eid-1
# fixed nodes: plate bottom near bolt centers
bolts=[(sx*225,sy*225) for sx in (-1,1) for sy in (-1,1)]
fix=[i for i,(x,y,z) in zip(nid,X) if z<1e-3 and min((x-bx)**2+(y-by)**2 for bx,by in bolts)<=10.0**2]
lines.append('*NSET,NSET=FIX'); lines+= [','.join(map(str,fix[i:i+12])) for i in range(0,len(fix),12)]
lines.append('*MATERIAL,NAME=AL'); lines.append('*ELASTIC'); lines.append(f'{E},{NU}')
for g in groups:
    extra=CARRIED.get(g,0.0)*1e-3; rho=RHO+extra/vol[g]
    lines.append(f'*MATERIAL,NAME=AL_{g}'); lines.append('*ELASTIC'); lines.append(f'{E},{NU}')
    lines.append('*DENSITY'); lines.append(f'{rho:.6e}')
    lines.append(f'*SOLID SECTION,ELSET=E_{g},MATERIAL=AL_{g}')
lines.append('*BOUNDARY'); lines.append('FIX,1,3,0.')
def write(name,step):
    open(name+'.inp','w').write('\n'.join(lines+step)+'\n')
    r=subprocess.run([CCX,'-i',name],capture_output=True,text=True,timeout=3000)
    if r.returncode!=0: print(r.stdout[-2000:]); raise SystemExit('ccx failed')
    return open(name+'.dat').read()
mass_total=sum((RHO*vol[g]+CARRIED.get(g,0)*1e-3) for g in groups)*1e3
print(f'mesh h={H} mm: {len(nid)} nodes, {nel} C3D10; fixed nodes {len(fix)}; total mass {mass_total:.2f} kg')
for g in groups: print(f'  {g}: {vol[g]*RHO*1e3:.3f} kg structure + {CARRIED.get(g,0):.3f} kg carried')
res={'h':H,'nodes':len(nid),'elements':nel,'mass_kg':mass_total}
dat=write('modal',['*STEP','*FREQUENCY','8','*NODE FILE','U','*END STEP'])
f=[float(m.group(1)) for m in re.finditer(r'^\s+\d+\s+\S+\s+\S+\s+(\S+)\s+\S+\s*$',dat.split('E I G E N V A L U E   O U T P U T')[1].split('P A R T I C I P')[0],re.M)]
print('modes (Hz):',' '.join(f'{x:.1f}' for x in f)); res['modes_hz']=f
G=9810.0
for name,vec in [('axial_10g',(0,0,-10)),('lat_x_17g',(17,0,0)),('lat_y_17g',(0,17,0))]:
    n=np.array(vec,float); mag=np.linalg.norm(n); d=n/mag
    step=['*STEP','*STATIC','*DLOAD',f'Eall,GRAV,{mag*G},{d[0]},{d[1]},{d[2]}','*NODE PRINT,NSET=Nall','U','*EL PRINT,ELSET=Eall','S','*END STEP']
    lines_bak=lines[:]; lines.insert(1,'') 
    lines[:]=lines_bak
    if '*NSET,NSET=Nall,GENERATE' not in lines: pass
    dat=write(name,['*NSET,NSET=Nall,GENERATE',f'1,{nid.max()},1','*ELSET,ELSET=Eall,GENERATE',f'1,{nel},1']+step)
    U=[]; S=[]; sec=None
    for ln in dat.splitlines():
        if 'displacements' in ln: sec='U'; continue
        if 'stresses' in ln: sec='S'; continue
        p=ln.split()
        if sec=='U' and len(p)==4: U.append(np.linalg.norm([float(v) for v in p[1:]]))
        if sec=='S' and len(p)==8:
            sx,sy,sz,sxy,sxz,syz=[float(v) for v in p[2:]]
            S.append(np.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(sxy**2+sxz**2+syz**2)))
    umax=max(U); smax=max(S); s99=float(np.percentile(S,99.9))
    print(f'{name}: max |u| {umax:.3f} mm, max von Mises (integration pt) {smax:.1f} MPa, 99.9th pct {s99:.1f} MPa, yield margin MS={YIELD/(1.25*smax)-1:+.2f} (FS 1.25)')
    res[name]={'umax_mm':umax,'vm_max_mpa':smax,'vm_p999_mpa':s99}
json.dump(res,open(f'results_h{H:g}.json','w'),indent=1)
gmsh.finalize()
