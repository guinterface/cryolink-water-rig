"""Coupling capture dynamics in MuJoCo: client half B (nose cone) driven into host half A (female cone)
with the specified misalignment, A riding on its spring-centered compliant mount.
Geometry from cad/params.py (cone root 28 mm, mouth 46 mm, height 30 mm, 2 mm radial clearance).
A's concave cone is built from 64 convex box facets on the analytic surface; B's nose is a convex frustum mesh.
ASSUMPTIONS (labeled): mate stroke speed, mount stiffness/damping, friction, contact softness.
"""
import mujoco, numpy as np, json, sys, itertools, os
sys.path.insert(0,os.path.expanduser('~/Documents/zyxem/cryolink/cad')); import params as p
mm=1e-3
R0,R1,HC=p.CONE_ROOT*mm,p.CONE_MOUTH*mm,p.CONE_HEIGHT*mm
slope=(R1-R0)/HC; half=np.arctan(slope)
rtip=(p.CONE_ROOT+ (p.CONE_MOUTH-p.CONE_ROOT)/p.CONE_HEIGHT*p.B_TIP - p.RADIAL_CLEARANCE)*mm
rtop=(p.CONE_MOUTH-p.RADIAL_CLEARANCE)*mm; ztip=p.B_TIP*mm
M_A=0.595; M_B=0.218                      # kg, CAD (CHECKS.md)
def model_xml(k_lat,k_rot,mu,lat,tilt_deg,az_deg,kp=2.0e6):
    NF=64; L=np.hypot(HC,R1-R0); facets=[]
    for i in range(NF):
        th=2*np.pi*i/NF; rm=(R0+R1)/2+0.0025*np.cos(half)   # box center 2.5 mm behind the surface
        zm=HC/2-0.0025*np.sin(half)
        cx,cy=rm*np.cos(th),rm*np.sin(th)
        # box axes: x along slant (in r-z plane), y tangential, z along surface normal
        w=2*np.pi*((R0+R1)/2)/NF*1.15
        # orientation: rotate about tangential axis by (90deg - half) then about z by th
        q1=[np.cos((np.pi/2-half)/2*-1+0),0,0,0]
        facets.append(f'<geom type="box" size="{L/2:.5f} {w/2:.5f} 0.0025" pos="{cx:.6f} {cy:.6f} {zm:.6f}" euler="{th:.6f} {-(np.pi/2-half):.6f} 0" friction="{mu} 0.005 0.0001" rgba=".3 .5 .9 1"/>')
    # B nose frustum vertices (local frame, tip at z=ztip)
    ang=np.linspace(0,2*np.pi,48,endpoint=False)
    V=[(rtip*np.cos(a),rtip*np.sin(a),ztip) for a in ang]+[(rtop*np.cos(a),rtop*np.sin(a),HC) for a in ang]
    vert=' '.join(f'{x:.6f} {y:.6f} {z:.6f}' for x,y,z in V)
    t=np.radians(tilt_deg); a=np.radians(az_deg)
    return f'''<mujoco><compiler angle="radian" eulerseq="zyx"/>
<option timestep="0.0002" gravity="0 0 0" cone="elliptic" impratio="5"/>
<default><geom solref="0.002 1" solimp="0.95 0.99 0.0005"/></default>
<asset><mesh name="nose" vertex="{vert}"/></asset>
<worldbody>
 <body name="A" pos="0 0 0">
  <joint name="ax" type="slide" axis="1 0 0" stiffness="{k_lat}" damping="{2*np.sqrt(k_lat*M_A)*0.3:.4f}"/>
  <joint name="ay" type="slide" axis="0 1 0" stiffness="{k_lat}" damping="{2*np.sqrt(k_lat*M_A)*0.3:.4f}"/>
  <joint name="rx" type="hinge" axis="1 0 0" stiffness="{k_rot}" damping="{2*np.sqrt(k_rot*2e-4)*0.3:.5f}"/>
  <joint name="ry" type="hinge" axis="0 1 0" stiffness="{k_rot}" damping="{2*np.sqrt(k_rot*2e-4)*0.3:.5f}"/>
  <inertial pos="0 0 -0.01" mass="{M_A}" diaginertia="2e-4 2e-4 3e-4"/>
  {''.join(facets)}
 </body>
 <body name="B" pos="{lat*np.cos(a):.6f} {lat*np.sin(a):.6f} 0.040" euler="{t*np.sin(a):.6f} {-t*np.cos(a):.6f} 0">
  <joint name="bz" type="slide" axis="0 0 1"/>
  <inertial pos="0 0 0.03" mass="50" diaginertia="1 1 1"/>
  <geom type="mesh" mesh="nose" friction="{mu} 0.005 0.0001" rgba=".8 .7 .9 1"/>
 </body>
</worldbody>
<actuator><position name="drive" joint="bz" kp="{kp}" kv="{2*np.sqrt(kp*50)}"/></actuator>
</mujoco>'''
def run(k_lat=2000.,k_rot=20.,mu=0.3,lat=0.005,tilt=1.0,az=0.,v=0.005,tend=12.0,kp=2.0e6):
    m=mujoco.MjModel.from_xml_string(model_xml(k_lat,k_rot,mu,lat,tilt,az,kp)); d=mujoco.MjData(m)
    z0=0.040; fmax=0; dmax=0; t=0
    while d.time<tend:
        tgt=max(z0-v*d.time,0.0)-z0          # joint coordinate (B starts at +40 mm)
        d.ctrl[0]=tgt; mujoco.mj_step(m,d)
        f=0
        for i in range(d.ncon):
            c=d.contact[i]; fr=np.zeros(6); mujoco.mj_contactForce(m,d,i,fr); f+=fr[0]
        fmax=max(fmax,f); dmax=max(dmax,np.hypot(d.qpos[0],d.qpos[1]))
    fseat=-float(d.actuator_force[0])          # axial force the mate drive must hold at the seat (N)
    gap=(z0+d.qpos[4])                         # B height above nominal seat (m)
    return dict(seat_force_N=fseat,seat_gap_mm=gap*1e3,peak_contact_N=fmax,max_A_shift_mm=dmax*1e3,final_A_shift_mm=np.hypot(d.qpos[0],d.qpos[1])*1e3)
if __name__=='__main__':
    print(f'cone half-angle {np.degrees(half):.1f} deg; B nose r {rtip*1e3:.1f}-{rtop*1e3:.1f} mm; radial clearance {p.RADIAL_CLEARANCE} mm')
    rows=[]
    for k_lat,mu,lat,tilt,az in itertools.product([500.,2000.,20000.],[0.2,0.5],[0.0,0.005,0.007],[0.0,1.0],[0.,45.]):
        if lat==0 and az: continue
        r=run(k_lat=k_lat,mu=mu,lat=lat,tilt=tilt,az=az); r.update(k_lat=k_lat,mu=mu,lat_mm=lat*1e3,tilt=tilt,az=az)
        ok=r['seat_gap_mm']<0.5; r['captured']=bool(ok); rows.append(r)
        print(f"k={k_lat:6.0f} N/m mu={mu} lat={lat*1e3:.0f} mm tilt={tilt} az={az:>2.0f}: gap {r['seat_gap_mm']:6.2f} mm, hold force {r['seat_force_N']:6.1f} N, peak F {r['peak_contact_N']:7.2f} N, A shift max {r['max_A_shift_mm']:.2f} mm -> {'CAPTURED' if ok else 'JAMMED'}")
    json.dump(rows,open('capture_results.json','w'),indent=1)
