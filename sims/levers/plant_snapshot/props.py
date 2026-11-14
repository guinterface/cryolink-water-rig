"""Property lookups for the CryoLink SIL.

Oxygen: saturated properties interpolated from lox_table.py (generated with
CoolProp, see tools/make_lox_table.py). Vapor is treated as an ideal gas with
constant cp/cv (ASSUMPTION, error a few % at 1-4 bar near saturation).
Metals: specific heat tables are rounded handbook-style values from general
knowledge (ASSUMPTION, not checked against NIST for this project).
"""
from bisect import bisect_left

from .lox_table import ROWS

_T = [r[0] for r in ROWS]
_P = [r[1] for r in ROWS]
_COLS = list(zip(*ROWS))

R_O2 = 8.314462618 / 0.0319988   # J/kg/K
R_HE = 8.314462618 / 0.0040026   # J/kg/K
CP_HE, CV_HE = 5193.0, 3116.0    # monatomic ideal gas
CV_O2_GAS = 2.5 * R_O2           # ASSUMPTION: diatomic ideal gas
CP_O2_GAS = 3.5 * R_O2
G0 = 9.80665


def _interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect_left(xs, x)
    x0, x1 = xs[i - 1], xs[i]
    w = (x - x0) / (x1 - x0)
    return ys[i - 1] * (1 - w) + ys[i] * w


def psat(T):
    return _interp(_T, _P, T)


def tsat(p):
    return _interp(_P, _T, p)


def rho_l(T):
    return _interp(_T, _COLS[2], T)


def rho_v(T):
    return _interp(_T, _COLS[3], T)


def h_l(T):
    return _interp(_T, _COLS[4], T)


def h_v(T):
    return _interp(_T, _COLS[5], T)


def cp_l(T):
    return _interp(_T, _COLS[6], T)


def sigma(T):
    return _interp(_T, _COLS[8], T)


def h_fg(T):
    return h_v(T) - h_l(T)


def t_from_h_liquid(h):
    """Temperature of (approximately saturated) liquid with enthalpy h."""
    return _interp(list(_COLS[4]), _T, h)


# ASSUMPTION: rounded specific heats [J/kg/K] vs T [K]
_SS_T = [20, 50, 100, 150, 200, 250, 300]
_SS_CP = [10, 100, 270, 360, 410, 445, 480]      # 304 stainless (approx.)
_AL_T = [20, 50, 100, 150, 200, 250, 300]
_AL_CP = [9, 140, 480, 680, 790, 860, 900]       # 6061 aluminium (approx.)


def cp_ss(T):
    return _interp(_SS_T, _SS_CP, T)


def cp_al(T):
    return _interp(_AL_T, _AL_CP, T)


def choked_mdot(cda, p, T, R, gamma):
    """Choked (sonic) ideal-gas mass flow through an orifice into vacuum."""
    if p <= 0 or cda <= 0:
        return 0.0
    c = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    return cda * p * (gamma / (R * T)) ** 0.5 * c
