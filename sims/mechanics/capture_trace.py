"""One capture run (k 2000 N/m, mu 0.5, 5 mm lateral offset, 1 deg tilt) recorded every 20 ms for the website replay."""
import json, numpy as np, mujoco, capture_mujoco as cm
m = mujoco.MjModel.from_xml_string(cm.model_xml(2000., 20., 0.5, 0.005, 1.0, 0.)); d = mujoco.MjData(m)
z0 = 0.040; v = 0.005; rows = []; nxt = 0
while d.time < 9.0:
    d.ctrl[0] = max(z0 - v*d.time, 0.0) - z0; mujoco.mj_step(m, d)
    if d.time >= nxt:
        f = 0
        for i in range(d.ncon):
            fr = np.zeros(6); mujoco.mj_contactForce(m, d, i, fr); f += fr[0]
        rows.append([round(d.time, 3), round((z0+d.qpos[4])*1e3, 3), round(d.qpos[0]*1e3, 3), round(d.qpos[1]*1e3, 3), round(np.degrees(d.qpos[2]), 3), round(np.degrees(d.qpos[3]), 3), round(f, 2)])
        nxt += 0.02
json.dump({'cols': ['t_s', 'B_gap_mm', 'A_x_mm', 'A_y_mm', 'A_rx_deg', 'A_ry_deg', 'contact_N'], 'case': 'k_lat 2000 N/m, mu 0.5, offset 5 mm, tilt 1 deg, 5 mm/s', 'rows': rows}, open('capture_trace.json', 'w'))
print(len(rows), rows[-1])
