"""Render a CalculiX .frd result: von Mises stress on the outer surface (C3D10 tets).
usage: render_frd.py result.frd out.png "title" [vmax_MPa] [deform_scale] [view: elev,azim]"""
import sys, re, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fn, out, title = sys.argv[1:4]
vmax = float(sys.argv[4]) if len(sys.argv) > 4 else None
scale = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
elev, azim = (map(float, sys.argv[6].split(','))) if len(sys.argv) > 6 else (25, -60)
NUM = re.compile(r'-?\d\.\d+E[+-]\d+')
import os
FIRST = os.environ.get('MODE1')  # color by first DISP block (mode shape) and stop
xyz = {}; tets = []; U = {}; VM = {}; ndisp = 0
blk = None; mode = None; cur = []
with open(fn) as f:
    for ln in f:
        if ln.startswith('    2C'): mode = 'N'; continue
        if ln.startswith('    3C'): mode = 'E'; continue
        if ln.startswith(' -4'):
            blk = 'U' if 'DISP' in ln else ('S' if 'STRESS' in ln else None); mode = None
            if blk == 'U':
                ndisp += 1
                if FIRST and ndisp > 1: break
            continue
        if ln.startswith(' -3'): blk = None; mode = None; continue
        if mode == 'N' and ln.startswith(' -1'):
            nid = int(ln[3:13]); v = [float(x) for x in NUM.findall(ln[13:])]; xyz[nid] = v[:3]
        elif mode == 'E':
            if ln.startswith(' -1'): cur = []
            elif ln.startswith(' -2'):
                cur += [int(x) for x in ln[3:].split()]
                if len(cur) >= 4: tets.append(cur[:4]); cur = []
        elif blk and ln.startswith(' -1'):
            nid = int(ln[3:13]); v = [float(x) for x in NUM.findall(ln[13:])]
            if blk == 'U' and len(v) >= 3:
                U[nid] = v[:3]
                if FIRST: VM[nid] = float(np.linalg.norm(v[:3]))
            if blk == 'S' and len(v) >= 6:
                sx, sy, sz, sxy, syz, szx = v[:6]
                VM[nid] = np.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(sxy**2+syz**2+szx**2))
T = np.array(tets)
faces = np.concatenate([T[:, [0, 1, 2]], T[:, [0, 1, 3]], T[:, [0, 2, 3]], T[:, [1, 2, 3]]])
key = np.sort(faces, axis=1)
_, idx, cnt = np.unique(key, axis=0, return_index=True, return_counts=True)
surf = faces[idx[cnt == 1]]
ids = np.unique(surf); P = {i: np.array(xyz[i]) + scale*np.array(U.get(i, (0, 0, 0))) for i in ids}
tri = np.array([[P[a], P[b], P[c]] for a, b, c in surf])
val = np.array([(VM.get(a, 0)+VM.get(b, 0)+VM.get(c, 0))/3 for a, b, c in surf])
vm = vmax or np.percentile(val, 99.5)
if FIRST: val = val/val.max(); vm = 1.0
print(f'{len(T)} tets, {len(surf)} surface tris, max nodal vM {max(VM.values()):.1f} MPa, color max {vm:.1f}')
fig = plt.figure(figsize=(9, 7), dpi=130); ax = fig.add_subplot(111, projection='3d')
cmap = plt.get_cmap('turbo'); norm = plt.Normalize(0, vm)
pc = Poly3DCollection(tri, facecolors=cmap(norm(val)), edgecolors='none', linewidths=0)
ax.add_collection3d(pc)
allp = tri.reshape(-1, 3); c = (allp.max(0)+allp.min(0))/2; r = (allp.max(0)-allp.min(0)).max()/2
ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
ax.view_init(elev, azim); ax.set_axis_off()
sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
cb.set_label('relative displacement (mode shape)' if FIRST else 'von Mises stress [MPa]')
ax.set_title(title, fontsize=11)
plt.tight_layout(); plt.savefig(out, facecolor='white'); print('wrote', out)
