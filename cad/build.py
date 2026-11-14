#!python
"""CryoLink WATER bench prototype, mm. All custom dimensions are design assumptions.
Run from this directory. CPU only. Sources and limitations: SOURCES.md, CHECKS.md.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/cryolink_mpl')
from pathlib import Path
import math,json,csv,itertools
import cadquery as cq
from cadquery import exporters
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
for d in ('step','stl','drawings','renders'):Path(d).mkdir(exist_ok=True)
parts={}; instances=[]
BLUE=(.13,.39,.65); ORANGE=(.96,.52,.15); METAL=(.65,.7,.73); BLACK=(.15,.17,.2); GREEN=(.16,.48,.33)
def box(a,b,c,x=0,y=0,z=0):return cq.Workplane('XY').box(a,b,c,centered=(True,True,False)).translate((x,y,z))
def cyl(r,h,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((0,0,z))
def ring(ro,ri,h,z=0):return cq.Workplane('XY').circle(ro).circle(ri).extrude(h).translate((0,0,z))
def holes(s,pts,d,z,h):
 for x,y in pts:s=s.cut(cyl(d/2,h,z).translate((x,y,0)))
 return s

def register(n,s,process='print',mat='PETG',color=BLUE,notes=''):
 s=s.val() if isinstance(s,cq.Workplane) else s
 assert s.isValid(),n
 parts[n]=dict(shape=s,process=process,material=mat,color=color,notes=notes)
 return n

def put(n,pos=(0,0,0),rot=None,label=None,group='rig'):
 s=parts[n]['shape']
 if rot:s=s.rotate((0,0,0),rot[0],rot[1])
 s=s.translate(pos)
 instances.append(dict(name=label or n+'_'+str(len(instances)),part=n,shape=s,group=group))
 return s

def axial(n,x,flip=False,label=None):
 # local z increases from rear to coupling face; A +X, B -X
 return put(n,(x,0,110),((0,1,0),-90 if flip else 90),label,'coupling')

def torus(R,r):return cq.Solid.makeTorus(R,r)
def spring(od,wire,length,turns=9):
 rad=(od-wire)/2; pitch=(length-wire)/turns
 hel=cq.Wire.makeHelix(pitch,length-wire,rad)
 return cq.Workplane('XZ').center(rad,0).circle(wire/2).sweep(cq.Workplane(obj=hel),isFrenet=True).translate((0,0,wire/2))

# Metal wet cartridges: rear cap retained by four M3 through bolts, replaceable seat.
bolt=[(25*math.cos(t*math.pi/2),25*math.sin(t*math.pi/2)) for t in range(4)]
insert=ring(20,16,48,6).union(ring(29,16,6,0))
# slip-seat pocket at face end; polymer cone is dry and separately fastened
insert=insert.cut(cyl(17.025,7,47))
insert=insert.union(ring(16,13.5,19,0))
insert=holes(insert,bolt,3.4,0,6)
register('wet_insert',insert,'PRL lathe','6061-T6',METAL)
cap=ring(29,1.0,6,-6)
cap=holes(cap,bolt,3.4,-6,6)
# cap face seal -026 on shoulder; rear threaded barb through center
cap=cap.cut(ring(17.515,14.875,1.32,-1.32))
cap=cap.cut(cyl(2.05,7,-6))
register('rear_cap',cap,'PRL lathe','6061-T6',METAL)
seat=ring(17,11,7,47)
# poppet seal is -022? use same -026 unsuitable at radius13: custom silicone disk on poppet.
# Seat chamfer rear 45deg down to bore, compliant silicone washer seals rear flat annulus.
seat=seat.cut(cq.Solid.makeCone(12,11,1,cq.Vector(0,0,47)))
seat=seat.cut(ring(17,15.70,2.64,49))
register('seat',seat,'PRL lathe','acetal',(.91,.88,.72))
# 6 mm face extension from seat to interface, separate face insert with O-ring gland.
face=ring(20,11,6,54)
face=face.cut(ring(17.515,14.875,1.32,58.68))
for ang in (0,120,240):face=face.cut(box(5,6,3,21.5,0,57).rotate((0,0,0),(0,0,1),ang))
register('face_insert_A',face,'PRL lathe','6061-T6',METAL)
bface=ring(20,11,6,54)
for ang in (0,120,240):bface=bface.cut(box(5,6,3,21.5,0,57).rotate((0,0,0),(0,0,1),ang))
register('face_insert_B',bface,'PRL lathe','6061-T6',METAL)
# Seat and face insert clamped by threaded dry retainer, simplified thread envelope.
ret=ring(25,20.15,12,48).union(ring(25,18.0,3,60))
ret=ret.cut(box(60,60,4,z=60)) # face remains accessible; flange screws retain inserts instead
# Instead axial retainer ring flush face; 3 tabs over insert outer land
ret=ring(25,20.15,12,48)
for ang in (0,120,240):
 tab=box(5,6,3,21.5,0,57).rotate((0,0,0),(0,0,1),ang)
 ret=ret.union(tab)
ret=holes(ret,[(22.5*math.cos(math.radians(a)),22.5*math.sin(math.radians(a))) for a in (0,120,240)],3.4,48,12)
# FIX4: side-loaded DIN920 narrow heads; windows remain behind unchanged tabs.
# Remove the old 0.65mm inner bore ligament as an intentional open shaft slot.
for a in (0,120,240):
 ret=ret.cut(box(7,5,2.4,21.5,0,50).rotate((0,0,0),(0,0,1),a))
 ret=ret.cut(box(4,3.4,9,20.5,0,48).rotate((0,0,0),(0,0,1),a))
register('insert_retainer',ret)
register('retainer_screw_M3x8_97710A114',cyl(1.5,8,42).union(cyl(2,1.9,50)),
 'buy','18-8 SS',METAL,'DIN920 narrow cheese head diameter4 height1.9; M3x8 fully threaded; conservative cylindrical head; drive slot omitted')
# Poppet open state: disc z40..43, silicone face z43..45; closed face z47.
pop=cyl(13,3,40).union(cyl(2,22,18)).union(cyl(2,17,43))
register('poppet',pop,'PRL lathe','acetal',ORANGE)
register('poppet_seal',ring(13,2.1,2,43),'buy','silicone sheet 2 mm',(.7,.18,.18),'Cut washer; adhesive retention assumption')
guide=ring(15.9,2.1,3,19)
for a in (0,120,240):guide=guide.cut(box(10,9,5,8,0,18).rotate((0,0,0),(0,0,1),a))
register('spring_guide',guide,'PRL mill','acetal',METAL)
register('poppet_spring_9435K37',spring(6.096,.5588,20.6502), 'buy','302 SS',METAL,'Installed length overridden by preload spacer')
# guide to head distance18; add 6.35 mm preload spacer -> actual spring11.65 at open.
register('preload_spacer',ring(3,2.05,6.35,22),'PRL lathe','acetal',METAL)
# recompute installed spring length 11.65, free20.65 ->9mm compression; closed compression7mm
# free spring exported; installed compressed geometry follows
register('oring_026',torus(16.625,.89),'buy','Buna-N 70A',BLACK)
# A capture cone inner r28->46 over30, wall4; B exterior .25 radial gap
cone=cq.Solid.makeCone(32,50,30).cut(cq.Solid.makeCone(28,46,30))
cone=cq.Workplane(obj=cone).translate((0,0,60)).union(ring(32,25.2,16,44))
register('capture_A',cone)
bcone=cq.Solid.makeCone(27.75,45.75,30).cut(cq.Solid.makeCylinder(25.2,30))
# B local reversed axial; build B cone from face backwards: face z60 r27.75 ->rear z30 r45.75
bcone=cq.Workplane(obj=bcone).rotate((0,0,0),(1,0,0),180).translate((0,0,60))
bcone=bcone.union(ring(49,25.2,5,25))
register('capture_B',bcone,color=ORANGE)
# dry sleeve fixes metal rear flange to pedestal
sleeve=ring(25,20.2,42,6).union(ring(34,20.2,6,6))
sleeve=holes(sleeve,bolt,3.4,6,6)
# FIX3: local washer/nut seating clearance; flange and wet geometry unchanged.
sleeve=holes(sleeve,bolt,8,12,3.5)
# Narrow continuation clears the protruding screw tips without extending the washer notch.
sleeve=holes(sleeve,bolt,3.4,15.5,1)
sleeve=holes(sleeve,[(22.5*math.cos(math.radians(a)),22.5*math.sin(math.radians(a))) for a in (0,120,240)],2.5,40,8)
register('housing_sleeve',sleeve)
# fixed stand with split saddle atop 110mm axis
stand=box(40,90,10,z=0).union(box(14,65,65,z=10)).union(ring(42,34.2,10).rotate((0,0,0),(0,1,0),90).translate((-5,0,75)))
# FIX5: exterior clamp lugs give complete flat washer seats at y=+/-18.
for sy in [-1,1]:
 stand=stand.union(cyl(5.5,8).rotate((0,0,0),(1,0,0),-90*sy).translate((0,10*sy,113)))
stand=holes(stand,[(-13,-35),(-13,35),(13,-35),(13,35)],4.5,0,10)
stand=stand.cut(cyl(34.2,42).rotate((0,0,0),(0,1,0),90).translate((-21,0,75)))
for sy in [-1,1]:
 stand=stand.cut(cyl(5.5,30).rotate((0,0,0),(1,0,0),-90*sy).translate((0,18*sy,113)))
stand=stand.cut(box(44,1.5,55,0,0,75)).cut(cyl(2.25,60).rotate((0,0,0),(1,0,0),90).translate((0,30,113)))
register('coupling_stand',stand)
# local cartridges mate at world x0; both same rear frame distance60
for side,x,flip in [('A',-60,False),('B',60,True)]:
 for n in ['wet_insert','rear_cap','seat','poppet','poppet_seal','spring_guide','preload_spacer','housing_sleeve','insert_retainer']:
  axial(n,x,flip,side+'_'+n)
 axial('face_insert_'+side,x,flip,side+'_face')
 for k,a in enumerate((0,120,240)):
  sh=parts['retainer_screw_M3x8_97710A114']['shape'].translate((22.5*math.cos(math.radians(a)),22.5*math.sin(math.radians(a)),0)).rotate((0,0,0),(0,1,0),-90 if flip else 90).translate((x,0,110))
  instances.append(dict(name=f'{side}_retainer_screw_{k}',part='retainer_screw_M3x8_97710A114',shape=sh,group='coupling'))
 # installed toroid compressed axial at mating/rear face, volume-preserving ellipse in source approximation
 for station in ((59.34,-.66) if side=='A' else (-.66,)):
  # Volume-conserving installed ellipse, outer radius held by glandOD35.03.
  ea=(17.515-math.sqrt(17.515**2-4*16.625*.89**2/.66))/2
  er=17.515-ea
  s=cq.Solid.revolve(cq.Workplane('XZ').ellipse(ea,.66).val().translate((er,0,station)),[],360,cq.Vector(0,0,0),cq.Vector(0,0,1))
  n='installed_ring_'+side+str(station)
  register(n,s,'buy','Buna-N',BLACK)
  axial(n,x,flip,n)
 # spring starts after spacer
 sp=spring(6.096,.5588,11.65).val().translate((0,0,28.35))
 n='installed_spring_'+side;register(n,sp,'buy','302 SS',METAL);axial(n,x,flip,n)
axial('capture_A',-60)
axial('capture_B',60,True)
put('coupling_stand',(-50,0,35))
# base, dry electronics zone and wet tray
base=box(600,400,12,z=0)
mounts=[(-63,-35),(-63,35),(-37,-35),(-37,35)]
base=holes(base,mounts,4.5,0,12)
# FIX7 dry-side anchor through-holes and underside washer/nut counterbores.
base=holes(base,[(8,163),(32,187)],4.5,0,12)
base=holes(base,[(8,163),(32,187)],12,0,6.5)
register('base_plate',base,'PRL mill','sealed plywood 12 mm',(.63,.49,.33))
put('base_plate')
tray=box(580,275,3,z=12).union(box(580,3,32,0,-136,15)).union(box(580,3,32,0,136,15)).union(box(3,275,32,-288,0,15)).union(box(3,275,32,288,0,15))
# bought tray footprint is a labeled assumption; not manufacturing stl
register('spill_tray_envelope',tray,'buy','polypropylene',(.68,.78,.81),'ASSUMPTION 580x275x35; buy watertight tray or bonded sheet, contains >4L')
put('spill_tray_envelope')
# pedestals above tray; penetrations avoided: independent subbase rests in tray
register('wet_subbase',holes(box(490,220,10,z=0),mounts,4.5,0,10),'PRL mill','HDPE',METAL)
put('wet_subbase',(0,0,25))
# guide rods on 4 supports, slide bushings integrated to plate with .25 radial clearance
register('guide_rod',cyl(4,190),'buy','8 mm ground SS shaft',METAL,'Cut length190 ASSUMPTION')
for y in [-55,55]:put('guide_rod',(35,y,46.9),((0,1,0),90))
end=box(18,140,24,z=0)
for y in (-55,55):end=end.cut(cyl(4.1,20).rotate((0,0,0),(0,1,0),90).translate((-10,y,12)))
end=holes(end,[(0,-40),(0,40)],4.5,0,24)
register('rail_end',end)
for x in [35,225]:put('rail_end',(x,0,35))
plate=box(110,150,6,z=0)
for y in (-55,55):
 plate=plate.union(box(80,18,18,0,y,-18))
 plate=plate.cut(cyl(4.25,112).rotate((0,0,0),(0,1,0),90).translate((-56,y,-9)))
plate=holes(plate,[(-30,-69),(-10,-69)],4.5,0,6)
plate=holes(plate,[(-22,-30),(-22,30),(35,-30),(35,30)],4.5,0,6)
register('carriage_plate',plate,'PRL mill','6061-T6',METAL)
put('carriage_plate',(110,0,56))
# floating B platform constrained by shoulder screws in oversize holes, soft grommets
floatplate=holes(box(130,90,6,-10,0),[(-22,-30),(-22,30),(35,-30),(35,30)],16,0,6)
register('floating_plate',floatplate,color=ORANGE)
put('floating_plate',(110,0,64.5))
# B support shifted up? stand axis75 abovebottom -> bottom35, needs at35. use shorter B stand axis34 above76
bstand=box(30,50,8).union(box(12,58,31.5,z=8)).union(ring(42,34.2,10).rotate((0,0,0),(0,1,0),90).translate((-5,0,39.5)))
for sy in [-1,1]:
 bstand=bstand.union(cyl(5.5,8).rotate((0,0,0),(1,0,0),-90*sy).translate((0,10*sy,77.5)))
bstand=bstand.cut(cyl(34.2,42).rotate((0,0,0),(0,1,0),90).translate((-21,0,39.5)))
bstand=bstand.cut(box(100,100,20.01,z=-20),clean=False)
for sy in [-1,1]:
 bstand=bstand.cut(cyl(5.5,30).rotate((0,0,0),(1,0,0),-90*sy).translate((0,18*sy,77.5)))
bstand=bstand.cut(box(44,1.5,55,0,0,39.5)).cut(cyl(2.25,60).rotate((0,0,0),(1,0,0),90).translate((0,30,77.5)))
register('B_stand',bstand,color=ORANGE);put('B_stand',(50,0,70.5))
# B stand on platform extension x60..110
register('B_platform_extension',box(70,80,6),'print','PETG',ORANGE)
# extension merged into enlarged floating plate; separate part not installed
# captive shoulder bolts and elastomer centering rings actual mechanism - float ±6, tilt via grommets
register('shoulder_bolt_M4',cyl(2,25).union(cyl(4,3,25)),'buy','SS',METAL)
register('compliance_grommet',torus(5.0,3.25),'buy','silicone',BLACK,'ASSUMPTION ID3.5 OD16.5; stiffness must be measured')
for x in [88,145]:
 for y in [-30,30]:
  put('shoulder_bolt_M4',(x,y,56));put('compliance_grommet',(x,y,67.5))
# Shims alter fixed rail datum; remove all locks before moving
for off in [0,5,-5]:
 sh=box(18,80,3)
 sh=holes(sh,[(off,-30),(off,30)],4.5,0,3)
 register('offset_shim_'+str(off).replace('-','minus'),sh,color=(.86,.75,.2))
# wedge across70 gives1degree
wedge=cq.Workplane('XZ').polyline([(-35,0),(35,0),(35,2.222),(-35,1)]).close().extrude(40,both=True)
register('tilt_shim_1deg',wedge,color=(.86,.75,.2))
# Real-form bought servo from published LWH; ears and hole locations ASSUMPTION; slots avoid exact drill.
servo=box(40.6,20.5,38).union(box(54,20.5,3,z=28)).union(cyl(6,3,38).translate((-10,0,0))).union(cyl(3,3,41).translate((-10,0,0)))
servo=holes(servo,[(-24,-5),(-24,5),(24,-5),(24,5)],4.2,28,3)
register('servo_SG5010',servo,'buy','POM gears / polymer',BLACK)
# cradle with slotted flange and central body opening
cradle=box(66,34,5,z=-5).cut(box(42,22,7,z=-6))
for x in [-25,25]:
 for y in [-5,5]:cradle=cradle.cut(cq.Workplane('XY').center(x,y).slot2D(9,4.5,0).extrude(7).translate((0,0,-6)))
cradle=cradle.union(box(5,34,23,-30.5,0,-28)).union(box(5,34,23,30.5,0,-28))
register('servo_cradle',cradle)
# crank yoke x +/-18 driven shaft at world150,-85 z79
crank=box(36,10,5).union(cyl(7,5)).cut(cyl(3.1,7,-1))
crank=crank.union(cyl(5,5).translate((-18,0,0))).union(cyl(5,5).translate((18,0,0)))
crank=holes(crank,[(18,0)],4.2,0,5)
crank=holes(crank,[(-18,0)],3.9,0,5)
register('carriage_crank',crank)
yoke=box(12,64,6).cut(cq.Workplane('XY').slot2D(52,4.5,90).extrude(8).translate((0,0,-1)))
yoke=yoke.union(box(12,36,10,0,43,-4))
# FIX6 rigid rear-edge foot, two M4 through bolts; local z=-23 is plate top.
yoke=yoke.union(box(32,12,8,0,48,-23)).union(box(12,12,23,0,48,-23))
yoke=holes(yoke,[(-10,48),(10,48)],4.5,-23,8)
register('carriage_yoke',yoke,color=ORANGE)
put('servo_SG5010',(118,-117,35));put('servo_cradle',(118,-117,63));put('carriage_crank',(108,-117,79));put('carriage_yoke',(90,-117,85))
register('drive_pin',cyl(2,12),'buy','52100 alloy steel',METAL,'FIX6 McMaster91595A155 UNVERIFIED: nominal 4mm x12 dowel; verify catalog. Press into crank Ø3.90 bore:0.10mm diametral interference,5mm engagement; no head. Coupon-test PETG fit.');put('drive_pin',(90,-117,79))
register('fix6_yoke_screw_M4x25',cyl(2,25).union(cyl(3.5,4,-4)),'buy','18-8 SS',METAL,'91292A122 UNVERIFIED M4x25 SHCS;14mm stack plus3.2mm nut;7.8mm protrusion')
register('fix6_yoke_nut_M4',cq.Workplane('XY').polygon(6,7/math.cos(math.pi/6)).extrude(3.2).cut(cyl(2,3.2)),'buy','SS',METAL)
for x in [80,100]:
 put('fix6_yoke_screw_M4x25',(x,-69,70),((1,0,0),180))
 put('fix6_yoke_nut_M4',(x,-69,52.8))
# Two rounded-nose over-center hooks: pivot behind B, outside fluid path.
# Closed=-1deg, stop prevents further negative rotation; open=+30deg.
# Pressure load line is only105*sin1deg from pivot, instead of a high-pivot lever.
PIVOT_X=142.984
hook=box(114,10,8,-47,0).union(cyl(3,8).translate((-105,0,0)))
hook=hook.union(cyl(8,8)).cut(cyl(2.1,10,-1))
hook=hook.cut(box(.8,8,10,0,6,-1)).cut(cyl(1.6,18).rotate((0,0,0),(0,1,0),90).translate((-9,4,4)))
register('latch_hook',hook,color=ORANGE)
posed=hook.val().rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(0,1,0),-1)
register('latched_hook_pose',posed,color=ORANGE)
for y in [-45,53]:put('latched_hook_pose',(PIVOT_X,y,110),label='hook_'+str(y))
register('latch_shaft',cyl(2,199),'buy','4mm SS shaft',METAL)
put('latch_shaft',(PIVOT_X,-97,110),((1,0,0),-90))
for y in [-90,90]:
 bearing=box(16,12,81,PIVOT_X,y,35)
 bore=cyl(2.1,14).rotate((0,0,0),(1,0,0),90).translate((PIVOT_X,y+7,110))
 bearing=bearing.cut(bore)
 # 6mm bridge bottom115.18 is the closed hook hard stop, attached to fixed bearing tower.
 bearing=bearing.union(box(8,50,6,PIVOT_X+13, y/abs(y)*67,115.18)).union(box(20,12,6,PIVOT_X+7,y,115.18))
 register('latch_bearing_'+str(y).replace('-','minus'),bearing);put('latch_bearing_'+str(y).replace('-','minus'))
put('servo_SG5010',(PIVOT_X+10,146,110),((1,0,0),90))
put('servo_cradle',(PIVOT_X+10,118,110),((1,0,0),90))
# Pololu 1402: vendor/pololu1402-dimensions.png; local body left=-10, bottom=0.
# READ holes x=5.25,14.75 from left, z=2.5; diameter2.4.
sw=box(20,6.4,10.2)
for x in [-4.75,4.75]:sw=sw.cut(cyl(1.2,8).rotate((0,0,0),(1,0,0),90).translate((x,4,2.5)))
# READ lever pivot x=20-16.7=3.3 from left; tip free z=2.5+12.
# READ lever width4; ASSUMPTION thickness0.35 and straight simplified contour.
lever=cq.Workplane('XZ').polyline([(-6.7,10.2),(10,14.15),(10,14.5),(-6.7,10.55)]).close().extrude(2,both=True)
sw=sw.union(lever)
# READ terminal centers from left1.9,10.7,18; tip6.4 below hole axis (3.9 below body), width in side view0.6.
for x in [-8.1,.7,8]:sw=sw.union(box(.6,3.2,3.9,x,0,-3.9))
register('switch_1402',sw,'buy','polymer / steel',BLACK,'READ vendor drawing; lever width/thickness and simplified terminal contours ASSUMPTION')
SWPOSES={'seat':(34,-100,112),'latch':(123,70,96),'home':(186,100,59)}
for name,pos in SWPOSES.items():put('switch_1402',pos,label='switch_'+name)
# Side cheek has 8mm vertical adjustment slots, 2.7 clearance for M2 hardware.
# Base leaves terminals clear; screw/nut lengths verified on received hardware.
swm=box(28,20,4,0,5,-4).cut(box(22,8,6,0,0,-5)).union(box(28,4,17,0,7,0))
for x in [-4.75,4.75]:
 slot=cq.Workplane('XZ').center(x,2.5).slot2D(8,2.7,90).extrude(6,both=True).translate((0,7,0))
 swm=swm.cut(slot)
register('switch_mount',swm,notes='ASSUMPTION 8mm travel slots; M2 screws through sourced 2.4mm body holes')
register('compact_switch_mount',swm.cut(box(3,3,5,13,15,-4)))
for tag,pos in SWPOSES.items():put('compact_switch_mount' if tag=='latch' else 'switch_mount',pos)
# pinch valves: vertical jaw, guide posts, spring pushes down; servo cam lifts jaw by pull loop.
pinch=box(65,48,6).union(box(8,36,28.225,-25,0,6)).union(box(8,36,28.225,25,0,6))
pinch=pinch.union(box(65,48,6,z=34.225))
# tube direction Y, saddle shallow groove in anvil top
pinch=pinch.cut(cyl(2.5,50).rotate((0,0,0),(1,0,0),90).translate((0,25,8.5)))
pinch=pinch.cut(cyl(4.2,12,30))
# FIX5: two base ears with four anchors, clear of posts and the unchanged roof.
for px in [-20,20]:
 pinch=pinch.union(box(14,24,6,px,32))
pinch=holes(pinch,[(px,py) for px in [-20,20] for py in [28,38]],4.5,0,6)
roof=pinch.intersect(box(80,60,6,z=34.225))
pinch=pinch.cut(box(80,60,8,z=34.225))
roof=holes(roof,[(-25,-12),(-25,12),(25,-12),(25,12)],3.4,34,8)
pinch=holes(pinch,[(-25,-12),(-25,12),(25,-12),(25,12)],2.5,22,14)
register('pinch_roof',roof)
register('pinch_frame',pinch)
jaw=box(28,20,8).union(cyl(4,22,8)).cut(cyl(2.2,30,-1))
# radius2 edge nose separate smooth dowel
jaw=jaw.cut(cyl(2.05,22).rotate((0,0,0),(1,0,0),90).translate((0,11,0)))
register('pinch_jaw',jaw,color=ORANGE)
register('pinch_nose',cyl(2,20),'buy','4mm smooth SS',METAL)
register('pinch_spring_9435K125',spring(15.24,1.143,16.225,7),'buy','302 SS',METAL)
# eccentric disk and horn hole: lift through cord, no passive return claim
cam=cyl(11,5).cut(cyl(3.1,7,-1).translate((3,0,0))).cut(cyl(1.5,7,-1).translate((-3,0,0)))
register('pinch_cam',cam,color=ORANGE)
for tag,x in [('feed',-190),('drain',-115)]:
 put('pinch_frame',(x,-60,35),label=tag+'_frame')
 put('pinch_roof',(x,-60,35),label=tag+'_roof')
 put('pinch_jaw',(x,-60,45),label=tag+'_jaw')
 put('pinch_nose',(x,-50,45.05),((1,0,0),90),label=tag+'_nose')
 put('pinch_spring_9435K125',(x,-60,53),label=tag+'_spring')
 put('servo_SG5010',(x,-105,35));put('servo_cradle',(x,-105,63));put('pinch_cam',(x-10,-117,79))
# manual screw clamp thumbwheel and jaw, straight tubing slot
manual=box(30,24,6).union(box(5,24,24,-12.5,0,6)).union(box(30,24,6,z=30)).cut(cyl(2.5,8,29))
manual=manual.cut(cq.Workplane('XY').polygon(6,8.3).extrude(4.1).translate((0,0,32)))

manual=manual.union(box(24,26,6,3,20,0))
manual=holes(manual,[(0,25),(10,25)],4.5,0,6)
register('manual_clamp_frame',manual,color=ORANGE);put('manual_clamp_frame',(-240,-60,35))
register('manual_clamp_screw',cyl(2.5,23).union(cyl(10,4,23)),'buy','M5 thumb screw',METAL);put('manual_clamp_screw',(-240,-60,48))
register('M5_clamp_nut',cq.Workplane('XY').polygon(6,8.0).extrude(4).cut(cyl(2.1,6,-1)),'buy','SS',METAL,'ASSUMPTION standard M5 nut envelope')
put('M5_clamp_nut',(-240,-60,67))
register('manual_clamp_jaw',box(15,18,5));put('manual_clamp_jaw',(-240,-60,43))
# manifold downstream fixed A: axial bore and two outlet10-32 ports, metal spool wall sensor
man=box(50,32,24)
man=man.cut(cyl(2,52).rotate((0,0,0),(0,1,0),90).translate((-26,0,12)))
for x in [-12,12]:man=man.cut(cyl(2.05,18).rotate((0,0,0),(1,0,0),90).translate((x,1,12)))
man=holes(man,[(-18,10),(18,10)],4.5,0,24)
man=holes(man,[(-18,10),(18,10)],8,8,16)
man=holes(man,[(-8,13),(8,13)],3.3,11,13)
register('manifold',man,'PRL mill','6061-T6',METAL);put('manifold',(-155,10,70))
register('conditioning_spool',ring(6,2,60),'PRL lathe','6061-T6',METAL)
put('conditioning_spool',(-185,0,110),((0,1,0),90))
probe=cyl(3,30).union(cyl(2,35,30))
register('DS18B20_381',probe,'buy','stainless / cable',BLACK)
put('DS18B20_381',(-180,9,110),((0,1,0),90),label='wall_probe')
# clamp two parallel bores: spool and wall probe; contact through thermal paste/shim bridge
# FIX8 two-piece horizontal split clamp with a common thermal saddle.
clamp=box(24,32,22,0,-1,0)
for yy,rr,edge,sy in [(-3,6.1,-17,-13),(6,3.1,15,12)]:
 clamp=clamp.cut(cyl(rr,26).rotate((0,0,0),(0,1,0),90).translate((-13,yy,11)))
 clamp=clamp.cut(box(26,abs(edge-yy),.8,0,(edge+yy)/2,10.6))
 clamp=holes(clamp,[(0,sy)],3.4,11.4,11)
 clamp=holes(clamp,[(0,sy)],2.5,5,5.6)
# Removable common cap, full horizontal split; two independently adjusted screws.
clamp=clamp.cut(box(26,34,.8,0,-1,10.6))
clamp=clamp.union(box(24,22,5,0,12,-5))
clamp=holes(clamp,[(-8,20),(8,20)],4.5,-5,5)
register('wall_probe_clamp',clamp,'PRL mill','6061-T6',METAL,'FIX8 two-piece split clamp with two M3x16 screws; base seats on manifold; thermal paste path retained');put('wall_probe_clamp',(-155,3,99))
# dimensioned barb form: only tube interface and10-32 sourced; remaining shape assumption
barb=cyl(2.413,5).union(cq.Workplane('XY').polygon(6,7).extrude(3).translate((0,0,5))).union(cyl(1.2,9,8))
for z in [10,13,16]:barb=barb.union(cq.Solid.makeCone(1.6,1.2,1.4,cq.Vector(0,0,z)))
barb=barb.cut(cyl(.85,20,-1))
register('barb_5121K321',barb,'buy','polypropylene',(.85,.84,.72),'10-32 thread and3/32 tube sourced; body dimensions ASSUMPTION')
for pos,ang in [((-61,0,110),-90),((61,0,110),90),((-175,10,82),-90),((-180,0,110),-90),((-130,0,110),90)]:put('barb_5121K321',pos,((0,1,0),ang),label='B_feed_barb' if pos[0]>0 else None)
register('manifold_end_plug',cyl(2.413,5).union(cq.Workplane('XY').polygon(6,7).extrude(2).translate((0,0,5))),'buy','brass',METAL,'10-32 simplified thread envelope')
# FIX2: spare axial port accepts male10-32 tee, upward barb; third port capped.
tee=box(16,10,10,-122,10,77).union(cyl(2.413,5).rotate((0,0,0),(0,1,0),90).translate((-135,10,82)))
tee=tee.cut(cyl(.85,30).rotate((0,0,0),(0,1,0),90).translate((-136,10,82))).cut(cyl(.85,12,82).translate((-122,10,0)))
tee=tee.cut(cyl(2.05,5,82).translate((-122,10,0))).cut(cyl(2.05,5).rotate((0,0,0),(0,1,0),90).translate((-119,10,82)))
register('pressure_tee_10_32',tee,'buy','brass',METAL,'ASSUMPTION unselected male10-32 / female10-32 tee, 16x10x10 body; verify seal and tool clearance')
put('pressure_tee_10_32');put('manifold_end_plug',(-119,10,82),((0,1,0),90))
put('barb_5121K321',(-122,10,82))
for x in [-167,-143]:put('barb_5121K321',(x,-1,82),((1,0,0),90))
# tubing routes polyline with hollow swept straight segments; smooth routing schematic in fluid diagram
register('tube_sample',ring(2.35,1.25,60),'buy','silicone',(.32,.73,.8))
# connections laid out by exact endpoint; bend fittings are hoses with generous slack, not elbows
routes=[('source_to_clamp', [(-210, -20, 408), (-210, -20, 421), (-200, -35, 445), (-210, -45, 536), (-210, -65, 536), (-240, -85, 43.5), (-240, -60, 43.5)]), ('feed_to_B', [(-240, -80, 43.5), (-220, -80, 43.5), (-190, -89.375, 43.5), (-190, -60, 43.5), (-190, -25, 43.5), (-80, -25, 168), (98, -25, 160), (98, 0, 130), (78, 0, 110)]), ('A_to_spool', [(-78, 0, 110), (-113, 0, 110)]), ('spool_to_manifold', [(-197, 0, 110), (-205, 20, 105), (-192, 10, 82)]), ('waste', [(-167, -23, 82), (-75, -79, 85), (-75, -79, 43.5), (-115, -89.375, 43.5), (-115, -60, 43.5), (-115, -25, 43.5), (-102, 0, 80), (-105, 60, 115), (-105, 95, 112)]), ('fill', [(-143, -23, 82), (-130, -30, 95), (-130, 40, 170), (-205, 70, 170), (-205, 83, 170)])]
def tube_segment(a,b):
 v=cq.Vector(*b)-cq.Vector(*a);L=v.Length
 outer=cq.Solid.makeCylinder(2.35,L,cq.Vector(*a),v.normalized());inner=cq.Solid.makeCylinder(1.25,L,cq.Vector(*a),v.normalized())
 return outer.cut(inner)
for name,pts in routes:
 s=cq.Compound.makeCompound([tube_segment(a,b) for a,b in zip(pts,pts[1:])]);register('hose_route_'+name,s,'buy','silicone',(.28,.68,.78),'schematic straight spans; cut to suit bends');put('hose_route_'+name)
# receiver, reservoir and scale are shaped measured-on-receipt envelopes, explicitly unselected.
register('receiver_envelope',cyl(33,2).union(ring(33,31,85,2)),'buy','PP',(.66,.84,.85),'ASSUMPTION 250mL vented graduated receiver')
# FIX2: beam long axis along Y; published M4 pairs 10mm apart, inner pair44mm.
cell=box(12.7,75,12.7)
cell=holes(cell,[(0,y) for y in [-32,-22,22,32]],3.3,0,12.7)
# Reduced central sensing section is schematic, not a stiffness model.
cell=cell.cut(box(14,20,4,0,0,4.35))
register('load_cell_4541',cell,'buy','aluminum',METAL,'75x12.7x12.7; fourM4 drawing. Internal relief ASSUMPTION; arrow down at loaded end; confirm ends from markings')
put('load_cell_4541',(-205,56,47))
lbase=box(100,120,4,0,60).union(box(20,22,8,0,29,4))
lbase=holes(lbase,[(0,24),(0,34)],4.5,0,12)
# Recessed screw heads inserted from underside; base anchors avoid tray penetration.
for y in [24,34]:lbase=lbase.cut(cyl(4,3).translate((0,y,0)))
lbase=holes(lbase,[(-40,10),(40,10),(-40,110),(40,110)],4.5,0,4)
for x in [-42,42]:
 for y in [48,118]:lbase=lbase.union(box(8,8,24.2,x,y,4))
register('load_cell_base_clamp',lbase,notes='ASSUMPTION bottom screw heads recessed; fixed-end pedestal; four overload posts at Z63.2; shim/trim after load calibration')
put('load_cell_base_clamp',(-205,0,35))
pan=box(100,90,4).union(ring(36,34,3,4)).union(box(20,22,4,0,0,-4))
pan=holes(pan,[(0,-5),(0,5)],4.5,-4,8)
for y in [-5,5]:pan=pan.cut(cyl(4,3,1).translate((0,y,0)))
register('receiver_pan',pan,notes='ASSUMPTION receiverOD66; loaded-end top screws recessed; 4mm gap above beam; 0.5mm nominal overload-post gap')
put('receiver_pan',(-205,83,63.7));put('receiver_envelope',(-205,83,67.7))
register('waste_envelope',cyl(30,2).union(ring(30,28,70,2)),'buy','PP',(.66,.84,.85),'ASSUMPTION ≥250mL waste');put('waste_envelope',(-105,95,35))
# reservoir cradle behind wet zone; open500mL bottle on short mast at600mm water surface max
# FIX7 broad loose foot, within tray, with reliefs around the existing subbase feet.
# Local foot center is +74,+5 relative to post; world edges X[-284,-88],Y[-125,95].
foot=box(196,220,10,74,5)
for fy in [-70,110]:foot=foot.cut(cyl(13,10).translate((30,fy,0)))
foot=foot.cut(cyl(2.75,10)).cut(cyl(4.5,5.5))
foot=foot.cut(cyl(1.5,4,6).translate((6,0,0)))
post=box(19.05,19.05,420,z=10).cut(cyl(2.1,16,10))
post=post.cut(cyl(1.5,6,10).translate((6,0,0)))
mast=foot.union(post)
register('reservoir_mast',mast,'PRL mill','6061-T6',METAL,'FIX7 9008K12 19.05 square x420; foot196x220x10; M5x16 end joint +3mm dowel; see FIX7 drawings');put('reservoir_mast',(-260,-20,15))
register('fix7_reservoir_end_screw_M5x16',cyl(4.25,5,.5).union(cyl(2.5,16,5.5)),'buy','18-8 SS',METAL,'M5x16 SHCS; head recessed0.5;11.5mm thread engagement')
put('fix7_reservoir_end_screw_M5x16',(-260,-20,15))
register('fix7_reservoir_key_pin',cyl(1.5,10,6),'buy','SS',METAL,'3x10 dowel;4mm foot /6mm post; ream foot press fit and post slip fit')
put('fix7_reservoir_key_pin',(-254,-20,15))
cradle=ring(44,40,20).union(box(90,20,8,0,0,0))
cradle=cradle.cut(box(22,22,24,-50,0,-1))
register('reservoir_cradle',cradle);put('reservoir_cradle',(-210,-20,400))
register('reservoir_envelope',cyl(39,2).union(ring(39,37,120,2)),'buy','PP',(.66,.84,.85),'ASSUMPTION open500mL reservoir; surface≤600mm abovebase');put('reservoir_envelope',(-210,-20,408))
put('DS18B20_381',(-210,-20,450),label='inlet_probe')
# electronics boards from Eagle geometry, mounting hole positions package-derived
import xml.etree.ElementTree as ET

def pcb_from_eagle(path):
 root=ET.parse(path)
 # Reconstruct outline directly from Eagle layer20 wires, including curved corners.
 edges=[]
 for w in root.findall('.//board/plain/wire'):
  if w.get('layer')!='20':continue
  x1,y1,x2,y2=[float(w.get(k)) for k in ['x1','y1','x2','y2']]
  seg=cq.Workplane('XY').moveTo(x1,y1)
  seg=seg.radiusArc((x2,y2),math.copysign(math.hypot(x2-x1,y2-y1)/math.sqrt(2),float(w.get('curve','0')))) if w.get('curve') in ['-90','90'] else seg.lineTo(x2,y2)
  edges.extend(seg.val().Edges())
 board=cq.Workplane(obj=cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))).extrude(1.6)
 hs=[]
 for h in root.findall('.//board/plain/hole'):hs.append((float(h.get('x')),float(h.get('y')),float(h.get('drill'))))
 for e in root.findall('.//board/elements/element'):
  if 'MOUNTINGHOLE' in e.get('package',''):hs.append((float(e.get('x')),float(e.get('y')),2.5))
 for x,y,d in hs:board=board.cut(cyl(d/2,3,-.5).translate((x,y,0)))
 # header pads exact coordinates from Eagle packages
 packages={p.get('name'):p for p in root.findall('.//packages/package')}
 for e in root.findall('.//board/elements/element'):
  pkg=packages.get(e.get('package'))
  if pkg is None:continue
  if not any(k in e.get('package','') for k in ['1X','2X']):continue
  ang=float(e.get('rot','R0').replace('MR','').replace('R',''));c=math.cos(math.radians(ang));s=math.sin(math.radians(ang))
  for pad in pkg.findall('pad'):
   x,y=float(pad.get('x')),float(pad.get('y'));x,y=float(e.get('x'))+c*x-s*y,float(e.get('y'))+s*x+c*y
   board=board.cut(cyl(float(pad.get('drill'))/2,3,-.5).translate((x,y,0)))
 return board,hs
boardholes={}
for code,pat,pos in [('3405','*HUZZAH*.brd',(85,155,32)),('815','815-*rev C.brd',(150,162,32)),('5974','5974-*.brd',(230,160,32)),('3965','3965-*.brd',(40,160,650))]:
 board,hs=pcb_from_eagle(next(Path('vendor').glob(pat)));boardholes[code]=(hs,pos)
 if code=='3405':board=board.union(box(18,16,3,37,11.43,1.6)).union(box(6,8,3,2,11.43,1.6))
 elif code=='815':
  # ASSUMPTION header body/pin height; pad centers read from Eagle.
  for x in [8.89,21.59,36.83,49.53]:board=board.union(box(10.16,7.62,9,x,-2.54,1.6))
  board=board.union(box(10,8,10,29,13,1.6))
 if code=='5974':board=board.union(box(22,7,9,12.7,11,1.6))
 if code=='3965':board=board.union(box(5,5,2.2,8.89,8.89,1.6)).union(ring(1.25,.5,3.7,3.8).translate((8.89,8.89,0)))
 register('board_'+code,board,'buy','FR4 / electronics',GREEN,'PCB outline/holes from Eagle; thickness1.6 and components/heights ASSUMPTION')
 put('board_'+code,pos)
elec=box(193,46,4,172,170)
for code,(hs,pos) in boardholes.items():
 if code=='3965':continue
 for x,y,d in hs:elec=elec.union(ring(3,1.5 if abs(d-2.5)<.001 else d/2,16,4).translate((x+pos[0],y+pos[1],0)))
# dry-side cable-tie slots; leave a service loop above wall then route outward to +Y.
for x in [95,125,160,195,210]:elec=elec.cut(box(6,2,6,x,188,-1))
register('electronics_mount',elec);put('electronics_mount',(0,0,12))
register('electronics_splash_wall',box(197,3,65),'print','PETG',BLUE);put('electronics_splash_wall',(172,143,12))
register('pressure_splash_wall_extension',box(60,3,65),'print','PETG',BLUE);put('pressure_splash_wall_extension',(43.5,143,12))
# MPRLS above maximum600mm reservoir surface, behind splash wall (Y>144.5).
# Nonprinted mast anchored to dry base; bracket uses exact two Eagle mounting holes.
foot2=holes(box(32,32,6,20,175),[(8,163),(32,187)],4.5,0,6)
foot2=foot2.cut(cyl(2.25,6).translate((20,175,0))).cut(cyl(3.75,4.5).translate((20,175,0)))
foot2=foot2.cut(cyl(.75,2,4).translate((23.2,178.2,0)))
post2=box(9.525,9.525,632,20,175,6).cut(cyl(1.65,14,6).translate((20,175,0)))
post2=post2.cut(cyl(.75,4,6).translate((23.2,178.2,0)))
mast2=foot2.union(post2)
register('pressure_sensor_mast',mast2,'PRL mill','aluminum',METAL,'FIX7 9008K78 9.525 square x632; M4x12 end joint +1.5mm dowel; two M4x25 anchors with7mm spacers; underside recessed nuts')
put('pressure_sensor_mast',(0,0,12))
register('fix7_pressure_end_screw_M4x12',cyl(3.5,4,.5).union(cyl(2,12,4.5)),'buy','18-8 SS',METAL,'91292A117 M4x12;10.5mm engagement; head recessed0.5')
put('fix7_pressure_end_screw_M4x12',(20,175,12))
register('fix7_pressure_key_pin',cyl(.75,6,4),'buy','SS',METAL,'1.5x6 dowel;2mm foot /4mm post; offset(+3.2,+3.2)mm')
put('fix7_pressure_key_pin',(23.2,178.2,12))
register('fix7_mast_anchor_M4x25',cyl(2,25,-25).union(cyl(3.5,4)),'buy','18-8 SS',METAL,'91292A122 already ordered; bearingZ25.8; tipZ0.8')
register('fix7_anchor_spacer',ring(5,2.25,7),'PRL lathe','6061-T6',METAL,'OD10 ID4.5 x7; two spacers above pressure foot')
register('fix7_anchor_washer',ring(4.5,2.15,.8),'buy','SS',METAL,'OD9 ID4.3 thickness0.8; four total')
register('fix7_anchor_nut_M4',cq.Workplane('XY').polygon(6,7/math.cos(math.pi/6)).extrude(3.2).cut(cyl(1.65,3.2)),'buy','18-8 SS',METAL,'94150A335 already ordered; AF7 x3.2; underside counterbore')
for ax,ay in [(8,163),(32,187)]:
 put('fix7_mast_anchor_M4x25',(ax,ay,25.8))
 put('fix7_anchor_spacer',(ax,ay,18))
 put('fix7_anchor_washer',(ax,ay,25))
 put('fix7_anchor_washer',(ax,ay,5.7))
 put('fix7_anchor_nut_M4',(ax,ay,2.5))
pm=box(44,25,4,36,172).cut(box(10.5,10.5,5,20,175,-.5))
# split-free mast socket + transfer-drilled radial clamp screw on receipt.
pm=pm.union(box(17,17,18,20,175,-18).cut(box(10.5,10.5,20,20,175,-19)))
for x,y,d in boardholes['3965'][0]:pm=pm.union(ring(3,1.5,6,4).translate((40+x,160+y,0)))
register('pressure_sensor_mount',pm,notes='ASSUMPTION 10.5mm mast socket; transfer-drill M3 clamp; board underside650')
put('pressure_sensor_mount',(0,0,640))
pressure_pts=[(-122,10,99),(-122,20,99),(-122,25,140),(-100,35,160),(70,168.89,630),(70,168.89,665),(48.89,168.89,665),(48.89,168.89,654)]
register('hose_route_pressure_air_leg',cq.Compound.makeCompound([tube_segment(a,b) for a,b in zip(pressure_pts,pressure_pts[1:])]),'buy','silicone',(.5,.78,.85),'ASSUMPTION ID2.5 route; first121mm vertical air leg; keep dry; secure gradual bends and replace with snug3/32ID tail at MPRLS')
put('hose_route_pressure_air_leg')
register('subbase_foot',ring(10,2.25,10),'print','PETG',BLUE)
for xx in [-230,230]:
 for yy in [-90,90]:put('subbase_foot',(xx,yy,15))
# Captive washers prevent floating plate dropping through the 16mm travel holes.
register('travel_washer',ring(12,2.15,1.5),'buy','SS',METAL,'ASSUMPTION OD24; measure washer thickness')
register('float_standoff',ring(4,2.15,6.5),'PRL lathe','aluminum',METAL)
for x in [88,145]:
 for y in [-30,30]:
  put('travel_washer',(x,y,62));put('travel_washer',(x,y,73));put('float_standoff',(x,y,74.5))
# Mechanical witness flags: B full-seat cam, hook contact itself, and carriage-home tab.
flag=box(10,65,4,55,-72,70.5).union(box(10,10,57.5,55,-100,74.5)).union(box(17,10,4,51.5,-100,128)).union(box(4,10,8,45,-100,124))
register('seat_witness_cam',flag,color=ORANGE);put('seat_witness_cam')
# Home nose reaches x196 at36mm retraction; stationary switch tip x196.
homeflag=box(4,35,4,161,87.5,76).union(box(4,10,18,161,70,62)).union(box(4,6,4,161,100,72))
register('home_witness_cam',homeflag);put('home_witness_cam')
for nm in ['seat','home']:
 x,y,z=SWPOSES[nm]
 tower=box(8,8,z-4-35,x,y+11,35).union(box(28,24,5,x,y+11,35))
 register(nm+'_switch_tower',tower);put(nm+'_switch_tower')
support=box(10,10,53,-60,80,35).union(box(192,6,4,31,80,88)).union(box(8,8,4,123,80,88))
register('latch_sensor_support',support);put('latch_sensor_support')
witness=ring(5,2.1,4).union(box(10,4,4,-5,0)).union(box(4,4,4,-10,0))
witness=witness.cut(cyl(2.1,6,-1))
register('latch_witness_flag',witness,color=ORANGE)
put('latch_witness_flag',(PIVOT_X,72,110),((1,0,0),90))
# Split clamp joining 4mm latch shaft to supplied servo horn/spline adapter.
coupler=ring(8,2.1,9).cut(cyl(3.1,3,6)).cut(box(.8,18,11,0,0,-1))
for yy in [-5,5]:coupler=coupler.cut(cyl(1.6,20).rotate((0,0,0),(0,1,0),90).translate((-10,yy,4.5)))
register('latch_coupler',coupler);put('latch_coupler',(PIVOT_X,96,110),((1,0,0),-90))
# Seat OD elastomer compressed radially; standard ring section model for assembly indication.
register('seat_oring_026',torus(16.625,.89),'buy','Buna-N70A',BLACK)
for side,x,flip in [('A',-60,False),('B',60,True)]:
 er=(17.025+15.70)/2;ea=(17.025-15.70)/2;eb=16.625*.89**2/(er*ea)
 sh=cq.Solid.revolve(cq.Workplane('XZ').ellipse(ea,eb).val().translate((er,0,50.32)),[],360,cq.Vector(0,0,0),cq.Vector(0,0,1))
 n='installed_seat_ring_'+side;register(n,sh,'buy','Buna-N70A',BLACK);axial(n,x,flip,n)
# Separate machined parts with local datums are illustrated in drawings.py.

# FIX3 purchased hardware: conservative external head envelopes; sockets/chamfers omitted.
register('tie_screw_M3x22_91292A801',cyl(1.5,22,-6).union(cyl(2.75,3,-9)), 'buy','18-8 SS',METAL,'M3x0.5 x22; head diameter5.5 height3; socket/chamfer omitted ASSUMPTION envelope')
register('tie_nut_M3',cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.4).translate((0,0,12.5)).cut(cyl(1.5,2.4,12.5)), 'buy','SS',METAL,'AF5.5 height2.4; thread represented by nominal bore ASSUMPTION')
register('tie_washer_M3',ring(3.5,1.6,.5,12), 'buy','SS',METAL,'OD7 thickness0.5; ID3.2 ASSUMPTION')
for side,x,flip in [('A',-60,False),('B',60,True)]:
 for k,(bx,by) in enumerate(bolt):
  for n in ['tie_screw_M3x22_91292A801','tie_nut_M3','tie_washer_M3']:
   sh=parts[n]['shape'].translate((bx,by,0)).rotate((0,0,0),(0,1,0),-90 if flip else 90).translate((x,0,110))
   instances.append(dict(name=f'{side}_{n}_{k}',part=n,shape=sh,group='coupling'))
register('load_screw_M4x16_92095A194',cyl(2,16).union(cyl(3.8,2.2,-2.2)), 'buy','18-8 SS',METAL,'ISO7380 button head diameter7.6 height2.2; conservative cylindrical head, socket/chamfer omitted ASSUMPTION')
for y in [24,34]:put('load_screw_M4x16_92095A194',(-205,y,38),label=f'load_fixed_screw_{y}')
for y in [78,88]:put('load_screw_M4x16_92095A194',(-205,y,64.7),((1,0,0),180),label=f'load_loaded_screw_{y}')

# FIX5 bought hardware; nominal thread envelopes, conservative unslotted heads.
register('anchor_screw_M4x16',cyl(2,16,-9.2).union(cyl(3.5,4,6.8)), 'buy','18-8 SS',METAL,'M4x0.7 x16 SHCS; head OD7 x4; 9.2mm engagement into transfer-tapped subbase')
register('fix5_washer_M4',ring(4.5,2.15,.8), 'buy','18-8 SS',METAL,'OD9 ID4.3 thickness0.8; ASSUMPTION ISO7089 envelope')
register('clamp_screw_M4x45_91292A133',cyl(2,45).union(cyl(3.5,4,-4)), 'buy','18-8 SS',METAL,'M4x0.7 x45 SHCS; head OD7 x4; nominal thread envelope')
register('clamp_nut_M4',cq.Workplane('XY').polygon(6,7/math.cos(math.pi/6)).extrude(3.2).cut(cyl(2,3.2)), 'buy','18-8 SS',METAL,'AF7 thickness3.2 nominal M4 bore; ASSUMPTION ISO4032 envelope')
for tag,x in [('feed',-190),('drain',-115)]:
 for k,(px,py) in enumerate(( (px,py) for px in [-20,20] for py in [28,38] )):
  put('anchor_screw_M4x16',(x+px,-60+py,35),label=f'{tag}_anchor_screw_{k}')
  put('fix5_washer_M4',(x+px,-60+py,41),label=f'{tag}_anchor_washer_{k}')
for tag,x in [('A',-50),('B',50)]:
 put('clamp_screw_M4x45_91292A133',(x,-18.8,148),((1,0,0),-90),label=tag+'_clamp_screw')
 put('fix5_washer_M4',(x,-18.8,148),((1,0,0),-90),label=tag+'_clamp_head_washer')
 put('fix5_washer_M4',(x,18,148),((1,0,0),-90),label=tag+'_clamp_nut_washer')
 put('clamp_nut_M4',(x,18.8,148),((1,0,0),-90),label=tag+'_clamp_nut')

# FIX8 support stack. All new instances appended to retain historic semantic indices.
riser=box(26,30,6,16,7,0).union(box(18,12,35,15,0,0)).union(box(48,12,10,0,0,25))
riser=holes(riser,[(10,16),(22,16)],4.5,0,6)
riser=holes(riser,[(-18,0),(18,0)],3.3,25,10)
register('fix8_manifold_riser',riser,'PRL mill','6061-T6',METAL,'FIX8 single35mm bridge riser; right foot avoids load-cell base; twoM4x16 top screws and twoM4x16 subbase anchors')
register('fix8_M4x16',cyl(2,16,-16).union(cyl(3.5,4)), 'buy','18-8 SS',METAL,'91292A118 ordered M4x16 SHCS; conservative OD7x4 head')
register('fix8_M3x16',cyl(1.5,16,-16).union(cyl(2.75,3)), 'buy','18-8 SS',METAL,'M3x16 SHCS OD5.5x3; length selection from M3 allowance; verify stock')
put('fix8_manifold_riser',(-155,20,35))
for xx in [-173,-137]:
 put('fix8_M4x16',(xx,20,78),label=f'fix8_manifold_top_{xx}')
for xx in [-145,-133]:
 put('fix8_M4x16',(xx,36,41.8),label=f'fix8_riser_anchor_{xx}')
 put('fix5_washer_M4',(xx,36,41),label=f'fix8_riser_washer_{xx}')
for xx in [-240,-230]:
 put('fix8_M4x16',(xx,-35,41.8),label=f'fix8_manual_anchor_{xx}')
 put('fix5_washer_M4',(xx,-35,41),label=f'fix8_manual_washer_{xx}')
for xx in [-163,-147]:put('fix8_M4x16',(xx,23,99),label=f'fix8_probe_base_{xx}')
for yy in [-10,15]:put('fix8_M3x16',(-155,yy,121),label=f'fix8_pinch_{yy}')

exec(Path('fix9_geometry.py').read_text(),globals())
exec(Path('fix9b_geometry.py').read_text(),globals())

def deformable(p):
 return p.startswith(('installed_ring_','installed_seat_ring_','hose_route_')) or 'spring' in p or p=='compliance_grommet'
old_excluded=[i['name'] for i in instances if any(t in i['part'] for t in ['ring_','spring','hose_route','grommet'])]
new_excluded=[i['name'] for i in instances if deformable(i['part'])]
print('FIX6 excluded BEFORE',old_excluded,flush=True)
print('FIX6 excluded AFTER',new_excluded,flush=True)
assert set(old_excluded)-set(new_excluded)=={i['name'] for i in instances if i['part'].startswith('latch_bearing_')}
Path('fix6_exclusions.json').write_text(json.dumps(dict(before=old_excluded,after=new_excluded),indent=2))
print('Geometry complete',flush=True)
# export distinct part CAD local coordinates; printed exports reoriented to lowestZ by bounding box.
for n,p in parts.items():
 exporters.export(p['shape'],str(Path('step')/(n+'.step')))
 if p['process']=='print':
  s=p['shape'];bb=s.BoundingBox();s=s.translate((-bb.xmin,-bb.ymin,-bb.zmin))
  exporters.export(s,str(Path('stl')/(n+'.stl')),tolerance=.15,angularTolerance=.18)
assy=cq.Assembly(name='CryoLink_WATER')
for i in instances:assy.add(i['shape'],name=i['name'],color=cq.Color(*parts[i['part']]['color']))
assy.export('step/assembly.step')
# compact metadata and check ledger
inventory=[]
for n,p in parts.items():
 b=p['shape'].BoundingBox();inventory.append(dict(part=n,qty=sum(i['part']==n for i in instances),process=p['process'],material=p['material'],size_mm=[round(b.xlen,3),round(b.ylen,3),round(b.zlen,3)],valid=p['shape'].isValid(),volume_mm3=round(p['shape'].Volume(),3),notes=p['notes']))
Path('inventory.json').write_text(json.dumps(inventory,indent=2))
print('Exports complete',flush=True)
# Pairwise intersections actual BRep; all positive intersections classified in CHECKS, no blanket pass.
pairs=[]
for a,b in itertools.combinations(instances,2):
 if os.environ.get('CRYOLINK_SKIP_PAIRS'):break
 if deformable(a['part']) or deformable(b['part']):continue
 ba,bb=a['shape'].BoundingBox(),b['shape'].BoundingBox()
 if ba.xmax<=bb.xmin+.01 or bb.xmax<=ba.xmin+.01 or ba.ymax<=bb.ymin+.01 or bb.ymax<=ba.ymin+.01 or ba.zmax<=bb.zmin+.01 or bb.zmax<=ba.zmin+.01:continue
 try:
  vol=a['shape'].intersect(b['shape']).Volume()
  if vol>.1:pairs.append(dict(a=a['name'],b=b['name'],volume_mm3=round(vol,3)))
 except Exception as e:pairs.append(dict(a=a['name'],b=b['name'],error=str(e)))
Path('check_scope.json').write_text(json.dumps({'rigid_pair_checks_skipped':bool(os.environ.get('CRYOLINK_SKIP_PAIRS')),'excluded_instances':new_excluded},indent=2))
Path('interferences.json').write_text(json.dumps(pairs,indent=2))
print('Pair checks complete',len(pairs),flush=True)
# Mesh CPU renderer, painter sorted orthographic triangles; no OpenGL /GPU.
import numpy as np
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
def render(filename,items,title,view=(1,-1,.8),size=(1600,1150)):
 forward=np.array(view,dtype=float);forward/=np.linalg.norm(forward)
 right=np.cross([0,0,1],forward);right/=np.linalg.norm(right);up=np.cross(forward,right)
 tri=[];bound=[]
 for s,col in items:
  verts,faces=s.tessellate(.8,.25);v=np.array([[p.x,p.y,p.z] for p in verts]);proj=np.array([v@right,v@up,v@forward]).T;bound.extend(proj[:,:2])
  for f in faces:
   q=proj[list(f)];w=v[list(f)];normal=np.cross(w[1]-w[0],w[2]-w[0]);ln=np.linalg.norm(normal)
   shade=.56+.40*abs(float(normal@np.array([.3,-.5,.8]))/(ln or 1))
   tri.append((q[:,2].mean(),q,tuple(int(min(255,c*255*shade)) for c in col)))
 bound=np.array(bound);lo=bound.min(0);hi=bound.max(0);W,H=size;scale=min((W-120)/(hi[0]-lo[0]),(H-170)/(hi[1]-lo[1]))
 pixels=np.full((H,W,3),(245,247,249),dtype=np.uint8);zbuf=np.full((H,W),-np.inf,dtype=np.float32)
 for _,q,c in tri:
  xy=(q[:,:2]-(lo+hi)/2)*scale
  xx=xy[:,0]+W/2;yy=H/2+35-xy[:,1]
  xmin=max(0,int(np.floor(xx.min())));xmax=min(W-1,int(np.ceil(xx.max())))
  ymin=max(0,int(np.floor(yy.min())));ymax=min(H-1,int(np.ceil(yy.max())))
  if xmin>xmax or ymin>ymax:continue
  den=(yy[1]-yy[2])*(xx[0]-xx[2])+(xx[2]-xx[1])*(yy[0]-yy[2])
  if abs(den)<1e-9:continue
  gx=np.arange(xmin,xmax+1)[None,:]+.5;gy=np.arange(ymin,ymax+1)[:,None]+.5
  w0=((yy[1]-yy[2])*(gx-xx[2])+(xx[2]-xx[1])*(gy-yy[2]))/den
  w1=((yy[2]-yy[0])*(gx-xx[2])+(xx[0]-xx[2])*(gy-yy[2]))/den;w2=1-w0-w1
  zz=w0*q[0,2]+w1*q[1,2]+w2*q[2,2]
  zb=zbuf[ymin:ymax+1,xmin:xmax+1];mask=(w0>=-1e-7)&(w1>=-1e-7)&(w2>=-1e-7)&(zz>zb)
  zb[mask]=zz[mask];pixels[ymin:ymax+1,xmin:xmax+1][mask]=c
 im=Image.fromarray(pixels);draw=ImageDraw.Draw(im)
 draw.text((32,22),title,fill=(24,43,61),font=font)
 draw.text((32,H-35),'CryoLink / AA 261 / WATER prototype / mm / design assumptions require bench checks',fill=(60,75,90),font=font)
 im.save(filename)
if not os.environ.get('CRYOLINK_SKIP_RENDER'):
 render('renders/assembly.png',[(i['shape'],parts[i['part']]['color']) for i in instances], 'WATER TRANSFER RIG — assembly',view=(1,-1,.65))
 coupling=[i for i in instances if i['group']=='coupling']
 expl=[]
 for i in coupling:
  s=i['shape'];cx=s.Center().x;shift=(-45 if cx<0 else 45)
  if 'seat' in i['name'] or 'face' in i['name']:shift*=.4
  if 'cap' in i['name']:shift*=1.7
  expl.append((s.translate((shift,0,0)),parts[i['part']]['color']))
 render('renders/exploded.png',expl,'COUPLING — exploded / rear caps, seats and poppets',view=(1,-1,.6))
 clip=box(300,150,300,0,75,0).val()
 sec=[]
 for i in coupling:
  s=i['shape'].intersect(clip)
  if s.Volume()>.001:sec.append((s,parts[i['part']]['color']))
 render('renders/section.png',sec,'COUPLING — axial half section / open mechanically opposed poppets',view=(0,-1,.08))
 render('renders/switch_station.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['name']=='switch_seat' or i['part'] in ['seat_switch_tower','seat_witness_cam'] or (i['part']=='switch_mount' and i['shape'].Center().x<100)],'SEAT SWITCH — Pololu1402 / slotted cheek / moving witness',view=(.4,-1,.35),size=(1200,1000))
 render('renders/load_cell.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['part'] in ['load_cell_4541','load_cell_base_clamp','receiver_pan','receiver_envelope','load_screw_M4x16_92095A194']], 'FIX2 — receiver pan / beam / overload stops',view=(1,-1,.5),size=(1200,1000))
 render('renders/pressure_electronics.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['part'] in ['manifold','pressure_tee_10_32','pressure_sensor_mast','pressure_sensor_mount','board_3965','board_5974','board_3405','board_815','electronics_mount','electronics_splash_wall','pressure_splash_wall_extension','hose_route_pressure_air_leg']], 'FIX2 — pressure air leg / dry electronics',view=(1,-1,.45))
 render('renders/fix4_retainer.png',[(parts['insert_retainer']['shape'],BLUE)]+[(parts['retainer_screw_M3x8_97710A114']['shape'].translate((22.5*math.cos(math.radians(a)),22.5*math.sin(math.radians(a)),0)),METAL) for a in (0,120,240)], 'FIX4 — retainer / side-loaded DIN920 narrow heads / unchanged tabs',view=(1,-2,.8),size=(1400,1100))
 render('renders/fix5_access.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['part'] in ['pinch_frame','pinch_roof','coupling_stand','B_stand','anchor_screw_M4x16','fix5_washer_M4','clamp_screw_M4x45_91292A133','clamp_nut_M4']], 'FIX5 — anchor ears and through-clamp washer seats',view=(1,2,1),size=(1600,1100))
 render('renders/fix6_drive.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['part'] in ['carriage_plate','carriage_yoke','carriage_crank','drive_pin','latch_bearing_minus90','fix6_yoke_screw_M4x25','fix6_yoke_nut_M4'] or (i['part'] in ['servo_SG5010','servo_cradle'] and i['shape'].Center().y<-110 and i['shape'].Center().x>80)],'FIX6 — rear drive / rigid yoke foot / fixed latch tower',view=(1,-2,1))
 render('renders/fix7_masts.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['part'] in ['base_plate','spill_tray_envelope','reservoir_mast','reservoir_cradle','reservoir_envelope','pressure_sensor_mast','pressure_sensor_mount','board_3965'] or i['part'].startswith('fix7_')], 'FIX7 — stable reservoir foot and anchored pressure mast',view=(1,-2,.7))
 render('renders/fix8_supports.png',[(i['shape'],parts[i['part']]['color']) for i in instances if i['part'] in ['manifold','conditioning_spool','wall_probe_clamp','manual_clamp_frame','manual_clamp_screw','manual_clamp_jaw'] or i['part'].startswith('fix8_') or i['name'].startswith(('fix8_','wall_probe'))], 'FIX8 — manifold bridge, two-screw probe clamp and manual anchors',view=(1,-2,1))
 print('Exported',len(parts),'part definitions,',len(instances),'instances;',len(pairs),'overlap candidates. See interferences.json')


import fix9_checks
fix9_checks.run(globals())

import fix9_release
fix9_release.run(globals())

import fix9_clashes,fix9_validate,fix9_travel
fix9_clashes.run(globals())
fix9_validate.run(globals())
travel9=fix9_travel.run(globals())
assert not travel9['failures'],travel9['failures']

import fix9_latch_check,fix9_document
assert not fix9_latch_check.run(globals())
fix9_document.run()
import fix9_render
fix9_render.run(globals())

import runpy
runpy.run_path('drawings.py',run_name='__main__')

import fix9_joint_checks
fix9_joint_checks.run(globals())

import fix9b_checks
fix9b_checks.run(globals())
