"""Coupling proof-pressure check: separation load on the latch path and the client half (B_turned_receptacle) flange.
Hand calcs + CalculiX C3D10 of B alone. Units mm, N, MPa.
Pressures (ASSUMPTION): relief set 4.0 bar (params C_RELIEF_SET_BAR), MEOP = 4.4 bar gauge (set + 10% full-flow overpressure, ASSUMPTION),
proof 1.5 x MEOP, burst 2.5 x MEOP (factors ASSUMPTION, common practice for lines and fittings; standard not read).
Sealed diameters COMPUTED conservatively from revised catalog gland ODs: face34.93 mm (primary),
radial50.80 mm (secondary). Supplier effective pressure diameters pending. Worst case = primary leaks, pressure acts to the radial seal.
Load path: coupling A sits on a spring-centered compliant mount, so the three hooks carry the whole separation load into B's flange.
FEA: B_turned_receptacle (Al 6061-T6), top (client side, z 352-354 planes) fixed; hook loads as uniform -z traction on the
flange far face (z 333) over the hook toe footprint (width 6 mm = params latch_width, radial land 44.5-48.5 mm); hook angles from A.step."""
import gmsh, numpy as np, subprocess, re, json, os, math, hashlib
HERE=os.path.dirname(os.path.abspath(__file__))
os.chdir(os.environ.get('COUPLING_PROOF_OUT',HERE))
CAD=os.path.expanduser('~/Documents/zyxem/cryolink/cad/out'); CCX='<scratch>/sim_env/bin/ccx'
MEOP=0.44; P={'MEOP':MEOP,'proof':1.5*MEOP,'burst':2.5*MEOP}
D_FACE,D_RAD=34.93,50.80 # COMPUTED conservative gland OD sealed-area bounds for new PTFE seals
A_FACE,A_RAD=math.pi/4*D_FACE**2,math.pi/4*D_RAD**2
res={'revision':'2026-11-06 cold-fit; B housing only, sleeve press-fit/thermal stress excluded','pressures_mpa':P,'sealed_area_mm2':{'face_seal':round(A_FACE,1),'radial_seal':round(A_RAD,1)}}
# hook angles from A.step (hook solids volume ~2639 mm3)
gmsh.initialize(); gmsh.option.setNumber('General.Terminal',0)
gmsh.model.occ.importShapes(f'{CAD}/A.step'); gmsh.model.occ.synchronize()
ang=[]
for d,t in gmsh.model.getEntities(3):
    if abs(gmsh.model.occ.getMass(d,t)-2639.33)<1.0:
        x,y,z=gmsh.model.occ.getCenterOfMass(d,t); ang.append(math.degrees(math.atan2(y,x)))
ang=sorted(a%360 for a in ang); print('hook angles',[round(a,1) for a in ang]); res['hook_angles_deg']=[round(a,1) for a in ang]
gmsh.clear()
# hand calcs
pin_d=5.0; A_pin=2*math.pi/4*pin_d**2       # double shear, params latch_pin_r 2.5
hand={}
for k,p in P.items():
    F=p*A_RAD; Fh=F/len(ang); hand[k]=dict(F_sep_N=round(F),F_per_hook_N=round(Fh),pin_tau_mpa=round(Fh/A_pin,1),F_sep_face_seal_N=round(p*A_FACE))
res['hand']=hand; print(hand)
# FEA of B
gmsh.model.occ.importShapes(f'{CAD}/B_pressure_housing_coldfit.step'); gmsh.model.occ.synchronize()
vs=gmsh.model.getEntities(3); assert len(vs)==1, f'Expected one housing solid, found {len(vs)}'
keep=vs[0]
gmsh.model.occ.remove([v for v in vs if v!=keep],recursive=True); gmsh.model.occ.synchronize()
gmsh.model.addPhysicalGroup(3,[keep[1]],name='B')
H=float(os.environ.get('H','1.5'))
gmsh.option.setNumber('Mesh.MeshSizeMax',H); gmsh.option.setNumber('Mesh.MeshSizeMin',0.3); gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',16)
gmsh.option.setNumber('Mesh.ElementOrder',2); gmsh.option.setNumber('Mesh.HighOrderOptimize',0); gmsh.option.setNumber('Mesh.SecondOrderLinear',1)
gmsh.model.mesh.generate(3)
ntags,coords,_=gmsh.model.mesh.getNodes(); X=coords.reshape(-1,3); nid=ntags.astype(int); idx={n:i for i,n in enumerate(nid)}
et,etags,enodes=gmsh.model.mesh.getElements(3,keep[1]); k=list(et).index(11); EN=enodes[k].astype(int).reshape(-1,10)
order=[0,1,2,3,4,5,6,7,9,8]
def face_tris(z0,rmin,rmax):
    """second-order surface triangles on plane z=z0 with r in [rmin,rmax]"""
    out=[]
    for d,t in gmsh.model.getBoundary([keep],oriented=False):
        bb=gmsh.model.occ.getBoundingBox(d,t)
        if gmsh.model.getType(d,t)=='Plane' and abs(bb[2]-z0)<1e-3 and abs(bb[5]-z0)<1e-3:
            ft,ftag,fn=gmsh.model.mesh.getElements(2,t)
            for j,ty in enumerate(ft):
                if ty==9: out+= [r for r in fn[j].astype(int).reshape(-1,6)]
    return out
r=np.hypot(X[:,0],X[:,1]); th=np.degrees(np.arctan2(X[:,1],X[:,0]))%360
top=[i for i in range(len(nid)) if X[i,2]>352-1e-3 and abs(X[i,2]-352)<1e-3 or abs(X[i,2]-354)<1e-3]
fixn=sorted(set(nid[i] for i in range(len(nid)) if (abs(X[i,2]-354)<1e-3 or abs(X[i,2]-352)<1e-3)))
# hook footprint on z=333 face: tangential half-width 3 mm at r ~46.5
tris=face_tris(333.0,44.0,49.0)
def in_fp(c):
    x,y=c[0],c[1]; rr=math.hypot(x,y); a=math.degrees(math.atan2(y,x))%360
    return 44.4<=rr<=48.6 and any(abs(((a-h+180)%360)-180)*math.pi/180*rr<=3.0 for h in ang)
sel=[t for t in tris if in_fp(X[[idx[n] for n in t[:3]]].mean(0))]
area=0.0; nodal={}
for t in sel:
    P3=X[[idx[n] for n in t[:3]]]; a=0.5*np.linalg.norm(np.cross(P3[1]-P3[0],P3[2]-P3[0])); area+=a
    for n in t[3:]: nodal[n]=nodal.get(n,0)+a/3      # quadratic tri: corner loads 0, mid-side a/3 (consistent load)
print('mesh',len(nid),'nodes',len(EN),'C3D10; fixed',len(fixn),'hook footprint area',round(area,1),'mm2 on',len(sel),'tris')
res.update(mesh_h=H,nodes=len(nid),elements=len(EN),footprint_mm2=round(area,1))
# Release native mesh memory and stream the larger revised model to disk.
gmsh.finalize()
F=P['proof']*A_RAD
selected_solver=os.environ.get('CCX_SOLVER','')
static_card='*STATIC'+(',SOLVER='+selected_solver if selected_solver else '')
res['linear_solver']=selected_solver or 'SPOOLES'
print('Writing CalculiX input; solver',res['linear_solver'],flush=True)
with open('b_proof.inp','w') as stream:
    stream.write('*NODE\n')
    for n,(x,y,z) in zip(nid,X):
        stream.write(f'{n},{x:.6f},{y:.6f},{z:.6f}\n')
    print('Nodes written',flush=True)
    stream.write('*ELEMENT,TYPE=C3D10,ELSET=EB\n')
    for i,e in enumerate(EN):
        stream.write(f'{i+1},'+','.join(str(e[j]) for j in order)+'\n')
    print('Elements written',flush=True)
    stream.write('*NSET,NSET=FIX\n')
    for i in range(0,len(fixn),12):stream.write(','.join(map(str,fixn[i:i+12]))+'\n')
    stream.write('*MATERIAL,NAME=AL\n*ELASTIC\n68900,0.33\n*SOLID SECTION,ELSET=EB,MATERIAL=AL\n*BOUNDARY\nFIX,1,3,0.\n*STEP\n'+static_card+'\n*CLOAD\n')
    for n,w in nodal.items():stream.write(f'{n},3,{-F*w/area:.6e}\n')
    stream.write('*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n')
print('CalculiX solve',flush=True)
env=dict(os.environ,OMP_NUM_THREADS=os.environ.get('CCX_THREADS','16'),GFORTRAN_UNBUFFERED_ALL='1')
with open('ccx.stdout.log','w') as stdout,open('ccx.stderr.log','w') as stderr:
    r_=subprocess.run([CCX,'-i','b_proof'],stdout=stdout,stderr=stderr,text=True,env=env)
solver_text=open('ccx.stdout.log').read()
res['solver_returncode']=r_.returncode
res['housing_sha256']=hashlib.sha256(open(f'{CAD}/B_pressure_housing_coldfit.step','rb').read()).hexdigest()
assert r_.returncode==0, solver_text[-1500:]
NUM=re.compile(r'-?\d\.\d+E[+-]\d+'); S={};U={};blk=None
for ln in open('b_proof.frd'):
    if ln.startswith(' -4'): blk='U' if 'DISP' in ln else ('S' if 'STRESS' in ln else None); continue
    if ln.startswith(' -3'): blk=None; continue
    if blk and ln.startswith(' -1'):
        n=int(ln[3:13]); v=[float(x) for x in NUM.findall(ln[13:])]
        if blk=='U': U[n]=float(np.linalg.norm(v[:3]))
        else:
            sx,sy,sz,sxy,syz,szx=v[:6]; S[n]=float(np.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(sxy**2+syz**2+szx**2)))
ids=np.array(list(S)); sv=np.array([S[i] for i in ids]); kmax=int(np.argmax(sv)); loc=X[idx[int(ids[kmax])]]
# exclude load-patch and fixed-face nodes for a 'away from BC' value
xi=X[[idx[i] for i in ids]]; away=~((np.abs(xi[:,2]-333)<0.6)|(xi[:,2]>351.5))
ka=int(np.argmax(np.where(away,sv,-1)))
fe=dict(F_sep_N=round(F),vm_max_mpa=round(float(sv[kmax]),1),vm_max_at=[round(float(c),1) for c in loc],
        vm_max_away_mpa=round(float(sv[ka]),1),vm_max_away_at=[round(float(c),1) for c in X[idx[int(ids[ka])]]],umax_mm=round(max(U.values()),4))
for lvl,fac in [('proof',1.0),('burst',2.5/1.5)]:
    fe[f'ms_{lvl}_peak']=round((276 if lvl=='proof' else 310)/(fac*fe['vm_max_mpa'])-1,2)
    fe[f'ms_{lvl}_away']=round((276 if lvl=='proof' else 310)/(fac*fe['vm_max_away_mpa'])-1,2)
res['fea_proof']=fe; print(fe)
json.dump(res,open('results.json','w'),indent=1); print('saved')
