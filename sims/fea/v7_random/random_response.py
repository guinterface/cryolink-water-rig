"""Full multi-mode random vibration response of the CryoLink support (FEA v5 mesh, 1.01M nodes, C3D10).
Replaces the one-mode Miles screen (v3/random_miles.py) for "full base-drive random response" (design doc 6.2, still open).

Method (modal superposition, base excitation, COMPUTED):
  CalculiX *FREQUENCY gives mass-normalized modes phi_i, frequencies w_i and participation factors G_i = phi_i^T M r_d
  for each base direction d (modal60.dat). Each mode's nodal stress tensor s_i (6 comps, modal60.frd) is linear in its
  modal coordinate. Relative modal response to base acceleration A(f): q_i = -G_i A / (w_i^2 - w^2 + 2j z w_i w).
  The stress component covariance at a node is  Sigma = Phi C Phi^T  with  C_ij = Re int H_i H_j* S_A df  (all modes coupled,
  so closely spaced modes add correctly, unlike SRSS). Von Mises RMS by Segalman et al. (SAND98-1279C, "An efficient method
  for calculating RMS von Mises stress in a random vibration environment"): vm_rms^2 = trace(Q Sigma). Peak = 3 x RMS.
Input spectrum (MEASURED, SpaceX Rideshare Payload User's Guide v11, Table 4-6 MPE, all axes): 20 Hz 0.01, 50-700 Hz 0.015,
  800-925 Hz 0.03, 2000 Hz 0.00644 g^2/Hz, log-log between points -> 5.57 grms (checks the table). Levels (Table 6-1):
  acceptance = MPE, protoflight = MPE + 3 dB, qualification = MPE + 6 dB.
ASSUMPTIONS: uniform modal damping Q = 10 and 20 (zeta = 1/2Q; to be measured by the tap test, doc 6.2); 60 modes, the
  mass not captured by them is reported and treated as rigid (no stress); bonded joints and the 10 mm bolt patches of v5.
Units: mm, N, tonne, s, MPa.
"""
import numpy as np, re, json, os, sys, time
W = '<scratch>/fea_v7_random'
OUT = os.path.dirname(os.path.abspath(__file__))
G = 9810.0
YIELD, FS = 276.0, 1.25

# ---------- modes, participation, effective mass from the .dat ----------
dat = open(f'{W}/modal60.dat').read()
blk = lambda tag, nxt: dat.split(tag)[1].split(nxt)[0]
num = r'(-?\d\.\d+E[+-]\d+)'
ev = re.findall(r'^\s+(\d+)\s+' + r'\s+'.join([num] * 4) + r'\s*$', blk('E I G E N V A L U E   O U T P U T', 'P A R T I C I P'), re.M)
freq = np.array([float(r[3]) for r in ev]); w = 2 * np.pi * freq; nm = len(freq)
par = re.findall(r'^\s+(\d+)\s+' + r'\s+'.join([num] * 6) + r'\s*$', blk('P A R T I C I P A T I O N   F A C T O R S', 'E F F E C T'), re.M)
GAM = np.array([[float(x) for x in r[1:4]] for r in par])           # (nm, 3) x y z
eff = re.findall(r'^\s+(\d+)\s+' + r'\s+'.join([num] * 6) + r'\s*$', blk('E F F E C T I V E   M O D A L   M A S S', 'T O T A L   E F F'), re.M)
MEFF = np.array([[float(x) for x in r[1:4]] for r in eff])
tot = re.search(r'T O T A L   E F F E C T I V E   M A S S.*?\n\s*\n.*?\n\s+' + r'\s+'.join([num] * 3), dat, re.S)
MTOT = np.array([float(x) for x in tot.groups()])
print(f'{nm} modes {freq[0]:.1f}-{freq[-1]:.1f} Hz; captured mass fraction x/y/z', np.round(MEFF.sum(0) / MTOT, 3), flush=True)

# ---------- mode shapes (stress tensors and displacement) from the .frd, fast fixed-width reader ----------
def read_frd(fn):
    S, U, ids = [], [], None
    with open(fn, 'rb') as f:
        while True:
            ln = f.readline()
            if not ln: break
            if ln.startswith(b' -4'):
                name = ln[5:13].strip(); ncomp = int(ln[13:18])
                while True:
                    pos = f.tell(); l2 = f.readline()
                    if not l2.startswith(b' -5'): f.seek(pos); break
                first = f.readline(); L = len(first)
                # data lines are fixed width: ' -1' + 10-char node id + 12-char fields
                if ids is None:
                    buf = [first]
                    while True:
                        l3 = f.readline()
                        if l3.startswith(b' -3'): break
                        buf.append(l3)
                    raw = b''.join(buf)
                    nn = len(buf)
                else:
                    nn = len(ids); raw = first + f.read((nn - 1) * L); assert f.readline().startswith(b' -3')
                a = np.frombuffer(raw, np.uint8).reshape(nn, L)
                nid = np.frombuffer(a[:, 3:13].tobytes(), 'S10').astype(int)
                if ids is None: ids = nid
                else: assert np.array_equal(ids, nid)
                nv = ncomp if name != b'DISP' else 3
                fld = np.concatenate([a[:, 13:13 + 12 * nv].reshape(nn, nv, 12), np.full((nn, nv, 1), 32, np.uint8)], 2)
                vals = np.array(fld.tobytes().split(), dtype=np.float64).reshape(nn, nv).astype(np.float32)
                if name == b'STRESS': S.append(vals[:, :6])
                elif name == b'DISP': U.append(vals[:, :3])
    return ids, np.stack(U, 1), np.stack(S, 1)                     # (N, nm, 3), (N, nm, 6)
t0 = time.time()
cache = f'{W}/modes.npz'
if os.path.exists(cache):
    z = np.load(cache); ids, U, S = z['ids'], z['U'], z['S']
else:
    ids, U, S = read_frd(f'{W}/modal60.frd'); np.savez(cache, ids=ids, U=U, S=S)
assert U.shape[1] == nm and S.shape[1] == nm, (U.shape, S.shape, nm)
print(f'read {len(ids)} nodes x {nm} modes in {time.time() - t0:.0f} s', flush=True)
X = None
inp = open(f'{W}/modal60.inp').read().split('*NODE\n')[1].split('*')[0]
xyz = np.loadtxt(inp.splitlines(), delimiter=',')
pos = dict(zip(xyz[:, 0].astype(int), xyz[:, 1:]))
X = np.array([pos[i] for i in ids])

# ---------- spectrum ----------
fp = np.array([20, 50, 700, 800, 925, 2000.]); pp = np.array([0.01, 0.015, 0.015, 0.03, 0.03, 0.00644])
F = np.unique(np.concatenate([np.logspace(np.log10(20), np.log10(2000), 6000),
                              np.concatenate([fi * (1 + np.linspace(-0.2, 0.2, 801)) for fi in freq if fi < 2400])]))
F = F[(F >= 20) & (F <= 2000)]
PSD = 10 ** np.interp(np.log10(F), np.log10(fp), np.log10(pp))
grms = np.sqrt(np.trapezoid(PSD, F)); print(f'MPE {grms:.2f} grms', flush=True)

Qm = np.array([[1, -.5, -.5, 0, 0, 0], [-.5, 1, -.5, 0, 0, 0], [-.5, -.5, 1, 0, 0, 0],
               [0, 0, 0, 3, 0, 0], [0, 0, 0, 0, 3, 0], [0, 0, 0, 0, 0, 3]], np.float64)  # vm^2 = s^T Q s (tensor shear order irrelevant: diag)
_e, _V = np.linalg.eigh(Qm); Lq = _V * np.sqrt(np.clip(_e, 0, None))   # Q is PSD (hydrostatic null), so eigen not Cholesky
def run(d, Q, dB):
    z = 1 / (2 * Q); Om = 2 * np.pi * F
    H = -GAM[:, d][:, None] / (w[:, None] ** 2 - Om[None] ** 2 + 2j * z * w[:, None] * Om[None])   # (nm, nf) per (mm/s^2)
    SA = PSD * 10 ** (dB / 10) * G ** 2
    wt = np.zeros_like(F); dF = np.diff(F); wt[:-1] += dF / 2; wt[1:] += dF / 2            # trapezoid weights
    C = np.real((H * (wt * SA)) @ np.conj(H).T)                                          # C_ij = Re int H_i H_j* S_A df
    ev_, V = np.linalg.eigh(C); ev_ = np.clip(ev_, 0, None); Lc = V * np.sqrt(ev_)          # C = Lc Lc^T
    vm = np.zeros(len(ids)); um = np.zeros(len(ids))
    for a in range(0, len(ids), 200000):
        Sb = S[a:a + 200000].astype(np.float64)                                              # (n, nm, 6)
        Y = np.einsum('nmc,mk->nck', Sb, Lc)                                                 # (n, 6, nm)
        Z = np.einsum('dc,nck->ndk', Lq.T, Y)                                                # Q = Lq Lq^T
        vm[a:a + 200000] = np.sqrt((Z ** 2).sum((1, 2)))
        Yu = np.einsum('nmc,mk->nck', U[a:a + 200000].astype(np.float64), Lc)
        um[a:a + 200000] = np.sqrt((Yu ** 2).sum((1, 2)))
    k = int(np.argmax(vm))
    # per-mode share of the variance at the peak node (diagonal terms only, for explanation)
    Sk = S[k].astype(np.float64); share = np.array([(Lq.T @ Sk[i]) @ (Lq.T @ Sk[i]) * C[i, i] for i in range(nm)])
    top = np.argsort(share)[::-1][:3]
    return dict(axis='xyz'[d], Q=Q, dB=dB, vm_rms_max=round(float(vm[k]), 2), vm_3sig_max=round(3 * float(vm[k]), 1),
                ms_3sig=round(YIELD / (FS * 3 * vm[k]) - 1, 2), at_xyz=[round(float(v), 1) for v in X[k]],
                vm_3sig_p999=round(3 * float(np.percentile(vm, 99.9)), 1), ms_3sig_p999=round(YIELD / (FS * 3 * np.percentile(vm, 99.9)) - 1, 2),
                u_3sig_max_mm=round(3 * float(um.max()), 3),
                top_modes=[dict(mode=int(i + 1), f_hz=round(float(freq[i]), 1), share=round(float(share[i] / share.sum()), 3)) for i in top]), vm
res = dict(modes=nm, f_hz=[round(float(x), 1) for x in freq], captured_mass_fraction=dict(zip('xyz', np.round(MEFF.sum(0) / MTOT, 3).tolist())),
           mpe_grms=round(float(grms), 2), cases=[])
best = {}
for d in (0, 1, 2):
    for Q in (10, 20):
        for lvl, dB in [('acceptance', 0), ('protoflight', 3), ('qualification', 6)]:
            r, vm = run(d, Q, dB); r['level'] = lvl; res['cases'].append(r); print(r, flush=True)
            if lvl == 'protoflight' and Q == 10: np.save(f'{W}/vm_rms_{"xyz"[d]}_Q10_pf.npy', vm.astype(np.float32))
json.dump(res, open(os.path.join(OUT, 'random_response.json'), 'w'), indent=1)
np.save(f'{W}/ids.npy', ids); print('saved', flush=True)
