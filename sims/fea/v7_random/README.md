# Full random vibration response (2026-11-02)

Replaces the one-mode Miles screen with a 60-mode base-drive random analysis of the v5 support.

- Modes: CalculiX `*FREQUENCY` 60 on the v5 h6 mesh (1,013,475 nodes), 82.2-1712.4 Hz. Run in <scratch>/fea_v7_random (`run.sh`, 1 h 06 min, 44 GB; frd 10 GB, cached as modes.npz). Captured effective mass x 0.878, y 0.901, z 0.961.
- Post: `random_response.py` -> `random_response.json`. Modal superposition with the full modal covariance; von Mises RMS by Segalman's quadratic form; 3-sigma peak. Spectrum: Rideshare v11 Table 4-6 MPE, log-log, 5.57 grms (checks the table). Q 10 and 20 (ASSUMPTION until the tap test).
- Result (3-sigma von Mises, MS on 276 MPa with FS 1.25):
  - z, protoflight: 140 MPa (Q 10, MS +0.57), 200 MPa (Q 20, MS +0.10). Mode 1 carries 99% of it. Miles gave 135 and 191 MPa, so the screen was 4-5% low.
  - z, qualification Q 20: 283 MPa, MS -0.22 at the bolt clamp edge (singular); away from the clamp 238 MPa, MS -0.07. Qual MS 0 needs Q below 12.4 (peak) or 17.5 (away). v6 said 11-16.
  - x and y (new, never checked before): protoflight Q 20 102 and 147 MPa (MS +1.17, +0.51); qualification Q 20 144 and 207 MPa (MS +0.54, +0.07). Peak near the coupling ring (-3.9, 42.6, 266.2), driven by modes at 748 Hz (y) and 1032 Hz (x).
- Not included: modes above 1712 Hz (12% x, 10% y, 4% z of the mass, treated as rigid); stress concentrations below the 6 mm mesh; joint slip.
