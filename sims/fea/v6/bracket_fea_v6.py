"""FEA v6 bolted-joint boundary study on the fix3 plate (v5 mesh/model; only the support boundary changes) (fix3 plate: rib height ramps 28->8 mm over 60 mm, R7 noses merge into bolt lands; based on v3; copy of v2 with no solver timeout, results read from .frd): pocketed plate + triangulated strut support (CAD v2 bracket.step) with CalculiX.
Structural solids only (screws/washers left out; joints bonded = ASSUMPTION).
Units: mm, N, tonne, MPa, s.
Bonded: all bracket solids fused by gmsh fragment (shared nodes).
Masses of parts carried by the bracket are smeared into the solids that hold them (ASSUMPTION).
Boundary: v6 compares four bolted-joint idealizations (see VARIANTS); v5 used plate bottom fixed within 10 mm of the bolt centers.
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
import json as _j
_G=_j.load(open(os.path.expanduser('~/Documents/zyxem/cryolink/cad/out/engineering_summary.json')))['groups']
CARRIED={'rails':_G['manifold'],       # whole manifold subassembly on its two rails (v2 summary)
         'ring':_G['A'],               # coupling A on the mount carrier + flexure
         'plate':_G['line']+_G['box']+_G['harness']}   # smeared into the plate (ASSUMPTION)
MAN=[m for m in _j.load(open(os.path.expanduser('~/Documents/zyxem/cryolink/cad/out/parts_manifest.json'))) if m['subassembly']=='bracket']
gmsh.initialize(); gmsh.option.setNumber('General.Terminal',0)
gmsh.model.occ.importShapes(STEP); gmsh.model.occ.synchronize()
vols=gmsh.model.getEntities(3)
NAMES={}
for d,tg in vols:
    v=gmsh.model.occ.getMass(d,tg); m=min(MAN,key=lambda m:abs(m['volume_mm3']-v)); NAMES[tg]=m['name']
drop=[(3,tg) for tg,n in NAMES.items() if 'ISO4762' in n or 'washer' in n]
gmsh.model.occ.remove(drop,recursive=True); gmsh.model.occ.synchronize()
vols=gmsh.model.getEntities(3); print('structural solids',len(vols))
info=[]
for d,t in vols:
    bb=gmsh.model.occ.getBoundingBox(d,t); m=gmsh.model.occ.getMass(d,t); info.append((t,bb,m))
out,omap=gmsh.model.occ.fragment(vols,[]); gmsh.model.occ.synchronize()
vols=gmsh.model.getEntities(3)
SS_GROUPS={'flexure'}
def group(t,bb):
    n=NAMES.get(t,'')
    if 'plate' in n: return 'plate'
    if 'rail' in n: return 'rails'
    if 'carrier' in n: return 'ring'
    if 'flexure' in n: return 'flexure'
    if 'restraint' in n: return 'lock'
    return 'struts'
groups={}
for d,t in vols:
    bb=gmsh.model.occ.getBoundingBox(d,t); groups.setdefault(group(t,bb),[]).append(t)
print({g:len(v) for g,v in groups.items()})
vol={g:sum(gmsh.model.occ.getMass(3,t) for t in ts) for g,ts in groups.items()}
for g,ts in groups.items(): gmsh.model.addPhysicalGroup(3,ts,name=g)
gmsh.option.setNumber('Mesh.MeshSizeMax',H); gmsh.option.setNumber('Mesh.MeshSizeMin',0.8); gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',12)
gmsh.option.setNumber('Mesh.ElementOrder',2); gmsh.option.setNumber('Mesh.HighOrderOptimize',0); gmsh.option.setNumber('Mesh.SecondOrderLinear',1)
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
# ---- v6: bolted-joint boundary variants (everything above identical to v5) ----
lines.append('*MATERIAL,NAME=AL'); lines.append('*ELASTIC'); lines.append(f'{E},{NU}')
for g in groups:
    rho0=7.9e-9 if g in SS_GROUPS else RHO; Eg,NUg=(193e3,0.29) if g in SS_GROUPS else (E,NU)
    extra=CARRIED.get(g,0.0)*1e-3; rho=rho0+extra/vol[g]
    lines.append(f'*MATERIAL,NAME=AL_{g}'); lines.append('*ELASTIC'); lines.append(f'{Eg},{NUg}')
    lines.append('*DENSITY'); lines.append(f'{rho:.6e}')
    lines.append(f'*SOLID SECTION,ELSET=E_{g},MATERIAL=AL_{g}')


NUM=re.compile(r'-?\d\.\d+E[+-]\d+')
def read_frd(fn):
    U={};S={};blk=None
    for ln in open(fn):
        if ln.startswith(' -4'):
            blk='U' if 'DISP' in ln else ('S' if 'STRESS' in ln else None); continue
        if ln.startswith(' -3'): blk=None; continue
        if blk and ln.startswith(' -1'):
            n=int(ln[3:13]); v=[float(x) for x in NUM.findall(ln[13:])]
            if blk=='U' and len(v)>=3: U[n]=float(np.linalg.norm(v[:3]))
            if blk=='S' and len(v)>=6:
                sx,sy,sz,sxy,syz,szx=v[:6]
                S[n]=float(np.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(sxy**2+syz**2+szx**2)))
    return U,S
# Joint geometry (ASSUMPTION/COMPUTED): M8 ISO 4762 + ISO 7089 washer (OD 16 mm) on the 8 mm bolt land, hole r 5 mm (params BOLT_D 10).
# Clamped contact on the far (bottom) face from the 30 deg pressure-cone rule: D = dw + 2 t tan30 = 16 + 2*8*0.577 = 25.2 mm -> r 12.6 mm.
R_HOLE,R_WASH,R_CONE=5.0,8.0,12.6
bolts=[(sx*225,sy*225) for sx in (-1,1) for sy in (-1,1)]
zmin=X[:,2].min()
rb=np.sqrt(np.min([(X[:,0]-bx)**2+(X[:,1]-by)**2 for bx,by in bolts],axis=0))
bot=np.abs(X[:,2]-zmin)<1e-3
K_HOST=float(os.environ.get('K_HOST','1e4'))   # N/mm per bolt, soft host sensitivity (ASSUMPTION)
VARIANTS={
 'v5_patch10': dict(r=(0,10.0),  spring=False),   # v5 baseline: all dof fixed r<=10 mm
 'cone':       dict(r=(R_HOLE-0.5,R_CONE),spring=False), # preloaded joint: contact cone fixed (friction + no separation)
 'washer':     dict(r=(R_HOLE-0.5,R_WASH),spring=False), # lower bound: only washer footprint fixed
 'cone_soft':  dict(r=(R_HOLE-0.5,R_CONE),spring=True),  # cone, x/y fixed, z on springs K_HOST per bolt
}
sel=os.environ.get('VARIANTS',','.join(VARIANTS)).split(',')
G=9810.0
base=lines[:]
procs=[]
for vname in sel:
    V=VARIANTS[vname]; d=os.path.join(HERE,vname); os.makedirs(d,exist_ok=True)
    m=bot&(rb>=V['r'][0])&(rb<=V['r'][1]); fix=nid[m].tolist()
    L=base+['*NSET,NSET=FIX']+[','.join(map(str,fix[i:i+12])) for i in range(0,len(fix),12)]
    if V['spring']:
        L+=['*BOUNDARY','FIX,1,2,0.']
        # one SPRING1 per node in z, K_HOST split evenly over the nodes of each bolt
        eidn=nel+1; per={}
        for i in np.where(m)[0]:
            b=int(np.argmin([(X[i,0]-bx)**2+(X[i,1]-by)**2 for bx,by in bolts])); per.setdefault(b,[]).append(int(nid[i]))
        for b,ns in per.items():
            L.append(f'*ELEMENT,TYPE=SPRING1,ELSET=SP{b}')
            for n in ns: L.append(f'{eidn},{n}'); eidn+=1
            L+=[f'*SPRING,ELSET=SP{b}','3',f'{K_HOST/len(ns):.6e}']
    else:
        L+=['*BOUNDARY','FIX,1,3,0.']
    open(os.path.join(d,'modal.inp'),'w').write('\n'.join(L+['*STEP','*FREQUENCY','8','*NODE FILE','U','*END STEP'])+'\n')
    st=['*NSET,NSET=Nall,GENERATE',f'1,{nid.max()},1','*ELSET,ELSET=Eall,GENERATE',f'1,{nel},1','*STEP','*STATIC','*DLOAD',f'Eall,GRAV,{10*G},0,0,-1','*NODE FILE','U','*EL FILE','S','*END STEP']
    open(os.path.join(d,'axial_10g.inp'),'w').write('\n'.join(L+st)+'\n')
    print(f'{vname}: fixed nodes {len(fix)}',flush=True)
gmsh.finalize()
np.save(os.path.join(HERE,'nodes.npy'),np.column_stack([nid,X]))
env=dict(os.environ,OMP_NUM_THREADS=os.environ.get('NT','12'))
for vname in sel:
    d=os.path.join(HERE,vname)
    procs.append((vname,subprocess.Popen(f'{CCX} -i modal > modal.log 2>&1 && {CCX} -i axial_10g > axial.log 2>&1',shell=True,cwd=d,env=env)))
for vname,p in procs: p.wait(); print(vname,'ccx exit',p.returncode,flush=True)
for vname in sel:
    d=os.path.join(HERE,vname); res={'h':H,'nodes':len(nid),'elements':nel,'variant':vname,'bc':VARIANTS[vname],'k_host_n_per_mm':K_HOST if VARIANTS[vname]['spring'] else None}
    dat=open(os.path.join(d,'modal.dat')).read()
    res['modes_hz']=[float(m.group(1)) for m in re.finditer(r'^\s+\d+\s+\S+\s+\S+\s+(\S+)\s+\S+\s*$',dat.split('E I G E N V A L U E   O U T P U T')[1].split('P A R T I C I P')[0],re.M)]
    U,S=read_frd(os.path.join(d,'axial_10g.frd'))
    ids=np.array(list(S)); sv=np.array([S[i] for i in ids]); idx={n:k for k,n in enumerate(nid)}
    rr=rb[[idx[i] for i in ids]]; zz=X[[idx[i] for i in ids],2]
    away=~((rr<=20.0)&(zz<zmin+3.0))     # exclude the clamp zone (bottom 3 mm within 20 mm of a bolt)
    k=int(np.argmax(sv)); ka=int(np.argmax(np.where(away,sv,-1)))
    loc=lambda j: [round(float(v),1) for v in X[idx[int(ids[j])]]]
    res['axial_10g']={'umax_mm':max(U.values()),'vm_max_mpa':float(sv[k]),'vm_max_at':loc(k),'vm_p999_mpa':float(np.percentile(sv,99.9)),
                      'vm_max_outside_clamp_mpa':float(sv[ka]),'vm_max_outside_clamp_at':loc(ka)}
    json.dump(res,open(os.path.join(d,'results_h6.json'),'w'),indent=1)
    a=res['axial_10g']; print(f"{vname}: f1 {res['modes_hz'][0]:.1f} Hz; 10 g peak {a['vm_max_mpa']:.1f} MPa at {a['vm_max_at']}; outside clamp {a['vm_max_outside_clamp_mpa']:.1f} at {a['vm_max_outside_clamp_at']}; umax {a['umax_mm']:.3f}",flush=True)
print('done')
