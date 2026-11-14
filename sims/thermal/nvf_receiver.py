"""No-vent fill of the client (receiver) tank: homogeneous thermal-equilibrium model.

Fluid + tank wall share one temperature (equilibrium). This is the LOWEST-pressure
bound; a stratified ullage gives higher pressure (see NTRS 19900011979 tests). Labels:
ASSUMPTION = design input, COMPUTED = this script, SOURCE = cited data.
"""
import numpy as np, json, sys
from CoolProp.CoolProp import PropsSI as P
from scipy.optimize import brentq

F = 'Oxygen'
V_TANK = 0.92          # m3 ASSUMPTION: 1,000 kg at 95% fill (design doc baseline)
R = (3*V_TANK/(4*np.pi))**(1/3)
A_TANK = 4*np.pi*R**2
WALL_T = 0.002         # m ASSUMPTION: 2 mm aluminum sphere wall
RHO_AL = 2700          # kg/m3 ASSUMPTION (params.py density)
M_WALL = A_TANK*WALL_T*RHO_AL
MDOT = 1000/3600       # kg/s ASSUMPTION baseline 1,000 kg in 1 h
P_SUPPLY = 4.0e5       # Pa ASSUMPTION: supply drives 1 bar over 3 bar receiver target
T_IN = 90.19           # K inflow liquid temperature ASSUMPTION (saturated at 1 atm)
Q_LEAK = 0.50*A_TANK   # W  SOURCE NTRS 20110014015 tank-applied MLI 0.50 W/m2
P_RELIEF = 4.0e5       # Pa CRV-250B set point used in the design doc
FILL_STOP = 0.95

# NIST 6061-T6 specific heat, log10 polynomial, 4-300 K (trc.nist.gov cryogenics materials)
C = [46.6467,-314.292,866.662,-1298.3,1162.27,-637.795,210.351,-38.3094,2.96344]
def cp_al(T):
    x = np.log10(T); return 10**sum(c*x**i for i,c in enumerate(C))
_Tg = np.linspace(4, 300, 3000); _cp = cp_al(_Tg)
_E = np.concatenate([[0], np.cumsum(0.5*(_cp[1:]+_cp[:-1])*np.diff(_Tg))])
def e_wall(T): return np.interp(T, _Tg, _E)   # J/kg relative to 4 K

def u_fluid(T, rho):
    return P('U','T',T,'D',rho,F)

def solve_T(m, E):
    rho = m/V_TANK
    f = lambda T: m*u_fluid(T,rho) + M_WALL*e_wall(T) - E
    return brentq(f, 60.0, 299.0, xtol=1e-6)

def run(T0_wall, dt=5.0):
    T = T0_wall; p0 = 1.0e5                      # ASSUMPTION: receiver starts with 1 bar O2 gas at wall temperature
    rho0 = P('D','T',T,'P',p0,F); m = rho0*V_TANK
    E = m*u_fluid(T,rho0) + M_WALL*e_wall(T)
    h_in = P('H','T',T_IN,'P',P_SUPPLY,F)
    t = 0.0; out = []
    while True:
        T = solve_T(m, E); rho = m/V_TANK
        p = P('P','T',T,'D',rho,F)
        try: q = P('Q','T',T,'D',rho,F)
        except Exception: q = -1
        rho_l = P('D','T',T,'Q',0,F) if T < P('Tcrit',F) else rho
        vapor_q = q if 0 <= q <= 1 else (0.0 if rho > rho_l else 1.0)
        liq_frac = (1-vapor_q)*m/rho_l/V_TANK if 0 <= vapor_q <= 1 else 0
        out.append((t, p/1e5, T, m, liq_frac))
        if liq_frac >= FILL_STOP or t > 4*3600 or p > 60e5: break
        if p >= P_SUPPLY: break                   # flow stops: no drive pressure left
        m += MDOT*dt; E += (MDOT*h_in + Q_LEAK)*dt; t += dt
    return np.array(out)

if __name__ == '__main__':
    print(f'tank r={R:.3f} m, area {A_TANK:.2f} m2, wall mass {M_WALL:.1f} kg (ASSUMPTION geometry)')
    res = {}
    for T0 in [100, 150, 200, 293]:
        a = run(T0)
        t,p,T,m,lf = a[-1]; pk = a[:,1].max()
        stop = 'filled to 95%' if lf >= FILL_STOP else ('supply pressure reached, flow stalls' if p*1e5 >= P_SUPPLY else 'stopped')
        print(f'wall start {T0:>3} K: end t={t/60:6.1f} min, P={p:5.2f} bar (peak {pk:5.2f}), T={T:6.1f} K, mass in {m:7.1f} kg, liquid {lf*100:5.1f}% -> {stop}')
        res[T0] = dict(t=a[:,0].tolist(), p=a[:,1].tolist(), T=a[:,2].tolist(), m=a[:,3].tolist(), lf=a[:,4].tolist(), stop=stop)
    json.dump(dict(meta=dict(V=V_TANK, M_WALL=M_WALL, MDOT=MDOT, P_SUPPLY=P_SUPPLY), runs=res), open('nvf_results.json','w'))
