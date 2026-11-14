"""plant_sim: replaces hw_interface in software-in-the-loop tests.

Contains three simulated things that are NOT flight-computer software:
  * the physical plant (supply tank, He bottle, transfer line, receiver tank,
    coupling, electronics thermal node),
  * the safety microcontroller (MCU): it alone moves valves, times chilldown
    pulses at 10 ms resolution, and runs the hard interlocks (overpressure,
    heartbeat watchdog, stuck-valve series isolation),
  * the host spacecraft (settling acceleration, attitude status).

It is also the clock source: it publishes /clock and every other node runs with
use_sim_time. Sim time advances `speedup` x faster than wall time.

Model summary (every made-up number is marked ASSUMPTION):
  supply  : saturated-liquid pool at fixed temperature + isothermal ullage of
            He pressurant (Dalton: p = p_He + psat(T_liq)).
  line    : N lumped stainless wall nodes, quasi-steady marching of the flow
            enthalpy through them (no fluid hold-up), boiling-curve heat
            transfer (film / nucleate / gas convection).
  receiver: two-node model (liquid pool + ideal-gas ullage of O2 and He),
            interface evaporation/condensation, aluminium wall node,
            spray-cooling during chill, choked vent and relief flow.
Liquid properties come from lox_table.py (CoolProp).
"""
import math
import random

import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String

from . import common as C
from . import props as P

VALVES = ('in_a', 'in_b', 'rx', 'vent_rx', 'line_vent', 'purge', 'press')


class Plant:
    """Physics only. SI units throughout."""

    def __init__(self, rng, receiver_volume=0.922):
        self.rng = rng
        # ---------------- supply tank (tanker side) ----------------
        self.T_sl = 90.0          # ASSUMPTION: supply liquid temperature [K]
        self.M_sl = 2000.0        # ASSUMPTION: supply liquid loaded [kg]
        self.V_s = self.M_sl / P.rho_l(self.T_sl) + 0.5   # ASSUMPTION 0.5 m3 ullage
        self.R_s = 0.5            # spec 3.1: 0.5 m tank radius (for Bond number)
        p_s0 = 2.2 * C.BAR        # ASSUMPTION: initial supply pressure
        self.m_he_s = (p_s0 - P.psat(self.T_sl)) * self.v_ull_s() / (P.R_HE * self.T_sl)
        # ---------------- He bottle (pressurant + purge) ----------------
        self.V_b = 0.15           # ASSUMPTION [m3]
        self.T_b = 280.0          # ASSUMPTION [K]
        self.m_b = 200.0 * C.BAR * self.V_b / (P.R_HE * self.T_b)  # ASSUMPTION 200 bar
        self.cda_press = 4.0e-7   # ASSUMPTION pressurant orifice [m2]
        self.cda_purge = 1.0e-8   # ASSUMPTION purge orifice [m2]
        # ---------------- transfer line ----------------
        # spec 3.2: flow 0.24 L/s at 1 bar dP -> CdA = Q / sqrt(2 dP / rho)
        self.cda_liq = 0.24e-3 / math.sqrt(2 * C.BAR / P.rho_l(self.T_sl))
        self.n_line = 5                        # ASSUMPTION wall nodes
        self.V_line = 1.0e-3                   # spec 3.2 leak-check example: 1 L
        self.A_line = math.pi * 0.016 * 5.0    # ASSUMPTION 16 mm ID x 5 m
        self.m_line_wall = 4.0                 # ASSUMPTION stainless incl. fittings [kg]
        self.q_env_line = 10.0                 # ASSUMPTION parasitic heat leak [W]
        self.Tw = [250.0] * self.n_line        # ASSUMPTION initial line wall [K]
        self.m_lg = 0.0                        # He gas trapped in an isolated line [kg]
        self.cda_leak = 0.0                    # injected leak orifice [m2]
        self.T_out = 250.0                     # outlet fluid sensor truth [K]
        # ---------------- receiver (client tank) ----------------
        self.V_rx = receiver_volume            # spec 3.2: 0.92 m3 (1000 kg at 95 %)
        self.A_rx = 4 * math.pi * (3 * self.V_rx / (4 * math.pi)) ** (2 / 3)
        self.m_rx_wall = self.A_rx * 0.003 * 2700.0   # ASSUMPTION 3 mm Al sphere
        self.Tw_rx = 150.0                     # ASSUMPTION pre-cooled client tank [K]
        self.m_l = 0.0
        self.T_l = 90.0
        self.T_g = 150.0                       # ASSUMPTION initial ullage gas [K]
        self.m_v = 1.2 * C.BAR * self.V_rx / (P.R_O2 * self.T_g)  # ASSUMPTION 1.2 bar O2
        self.m_he_rx = 0.0
        self.cda_vent = 4.0e-5                 # ASSUMPTION receiver vent [m2]
        self.cda_relief = 4.0e-5               # ASSUMPTION relief valve [m2]
        self.relief_open = False
        self.q_env_rx = 20.0                   # ASSUMPTION heat leak [W]
        self.q_inject_rx = 0.0                 # injected heater runaway [W]
        self.hA_spray = 3000.0                 # ASSUMPTION spray-to-wall [W/K] at nominal flow
        self.A_interface = 1.0                 # ASSUMPTION liquid/gas interface [m2]
        # ---------------- electronics thermal node ----------------
        self.T_elec = 280.0                    # ASSUMPTION
        self.T_cpl = 250.0                     # coupling body [K], ASSUMPTION
        # ---------------- bookkeeping ----------------
        self.mdot_line = 0.0
        self.mdot_rx_in = 0.0
        self.mdot_vent = 0.0
        self.gas_ingestion = False
        self.p_line = 0.0
        self.dumped_overboard = 0.0
        self.vented = 0.0
        self.delivered = 0.0

    # ----- derived -----
    def v_ull_s(self):
        return self.V_s - self.M_sl / P.rho_l(self.T_sl)

    def p_supply(self):
        return self.m_he_s * P.R_HE * self.T_sl / self.v_ull_s() + P.psat(self.T_sl)

    def p_bottle(self):
        return self.m_b * P.R_HE * self.T_b / self.V_b

    def v_gas_rx(self):
        return max(self.V_rx - self.m_l / P.rho_l(self.T_l), 1e-4)

    def p_rx_parts(self):
        vg = self.v_gas_rx()
        return (self.m_v * P.R_O2 * self.T_g / vg, self.m_he_rx * P.R_HE * self.T_g / vg)

    def p_rx(self):
        a, b = self.p_rx_parts()
        return a + b

    def fill_fraction(self):
        return self.m_l / (P.rho_l(self.T_l) * self.V_rx)

    # ----- one substep -----
    def step(self, dt, pos, accel_g, ingest_inject, unsettled_for):
        p_s = self.p_supply()
        p_rx = self.p_rx()
        # Bond number (spec 3.1). ASSUMPTION: liquid unsettles if Bo < 2 for 5 s.
        bo = P.rho_l(self.T_sl) * accel_g * P.G0 * self.R_s ** 2 / P.sigma(self.T_sl)
        self.gas_ingestion = ingest_inject or unsettled_for > 5.0
        # -------- pressurant into supply ullage --------
        if pos['press'] and self.p_bottle() > p_s:
            md = P.choked_mdot(self.cda_press, self.p_bottle(), self.T_b, P.R_HE, 5 / 3)
            md = min(md, self.m_b / dt * 0.01)
            self.m_b -= md * dt
            self.m_he_s += md * dt
        # -------- line flow --------
        inlet_open = pos['in_a'] and pos['in_b']
        if pos['line_vent']:
            dest, p_down = 'vac', 0.0
        elif pos['rx']:
            dest, p_down = 'rx', p_rx
        else:
            dest, p_down = None, None
        mdot, gas = 0.0, False
        if inlet_open and dest is not None:
            if self.gas_ingestion:
                gas = True
                T_gas_in = 120.0   # ASSUMPTION: warm ullage gas reaching the outlet
                rho_g = p_s / (P.R_HE * T_gas_in)
                dp = max(p_s - p_down, 0.0)
                mdot = min(self.cda_liq * math.sqrt(2 * rho_g * dp),
                           P.choked_mdot(self.cda_liq, p_s, T_gas_in, P.R_HE, 5 / 3))
                mdot = min(mdot, self.m_he_s / dt * 0.01)
                self.m_he_s -= mdot * dt
            else:
                # ASSUMPTION: flashing liquid cannot see a downstream pressure
                # below its own saturation pressure (choked two-phase limit).
                dp = p_s - max(p_down, P.psat(self.T_sl))
                if dp > 0:
                    mdot = self.cda_liq * math.sqrt(2 * P.rho_l(self.T_sl) * dp)
                    self.M_sl -= mdot * dt
        self.mdot_line = mdot
        self.p_line_flowing = 0.5 * (p_s + p_down) if mdot > 0 else None
        # -------- march the flow through the line wall nodes --------
        out = self._line_march(dt, mdot, gas, p_s, p_down if p_down is not None else 0.0)
        # -------- purge He --------
        md_purge = 0.0
        if pos['purge'] and self.p_bottle() > 2 * max(p_rx, self.p_line):
            md_purge = P.choked_mdot(self.cda_purge, self.p_bottle(), self.T_b, P.R_HE, 5 / 3)
            self.m_b -= md_purge * dt
        # -------- line gas inventory / pressure --------
        Twm = sum(self.Tw) / self.n_line
        if mdot > 0:
            self.m_lg = 0.0
            self.p_line = self.p_line_flowing
        elif pos['line_vent']:
            self.m_lg += md_purge * dt
            self.m_lg *= math.exp(-dt / 0.3)        # ASSUMPTION vent time constant
            self.p_line = self.m_lg * P.R_HE * Twm / self.V_line
        elif pos['rx']:
            self.m_he_rx += self.m_lg + md_purge * dt   # line open to the receiver
            self.m_lg = 0.0
            self.p_line = p_rx
        else:
            self.m_lg += md_purge * dt
            pl = self.m_lg * P.R_HE * Twm / self.V_line
            leak = P.choked_mdot(self.cda_leak, pl, Twm, P.R_HE, 5 / 3)
            if pl > C.RELIEF_LINE_PA:
                leak += P.choked_mdot(1e-6, pl, Twm, P.R_HE, 5 / 3)  # ASSUMPTION line relief
            self.m_lg = max(self.m_lg - leak * dt, 0.0)
            self.p_line = self.m_lg * P.R_HE * Twm / self.V_line
        # -------- receiver --------
        if dest == 'rx' and mdot > 0:
            self._receiver(dt, out, mdot, pos)
            self.delivered += mdot * dt
            self.mdot_rx_in = mdot
        else:
            self._receiver(dt, None, 0.0, pos)
            self.mdot_rx_in = 0.0
            if dest == 'vac':
                self.dumped_overboard += mdot * dt
        return bo

    def _line_march(self, dt, mdot, gas, p_s, p_down):
        n = self.n_line
        A = self.A_line / n
        mw = self.m_line_wall / n
        q_env = self.q_env_line / n
        Q = [0.0] * n
        if mdot <= 0:
            for i in range(n):
                self.Tw[i] += q_env * dt / (mw * P.cp_ss(self.Tw[i]))
            # stagnant outlet sensor relaxes to the last wall node (tau 5 s, ASSUMPTION)
            self.T_out += (self.Tw[-1] - self.T_out) * min(dt / 5.0, 1.0)
            return None
        p_loc = 0.5 * (p_s + p_down)
        Ts = P.tsat(max(p_loc, P.psat(self.T_sl)))
        hls, hvs = P.h_l(Ts), P.h_v(Ts)
        if gas:
            Tg = 120.0
            for i in range(n):
                hc = 80.0                                   # ASSUMPTION gas convection
                eff = 1 - math.exp(-hc * A / (mdot * P.CP_HE))
                Q[i] = mdot * P.CP_HE * (self.Tw[i] - Tg) * eff
                Tg += Q[i] / (mdot * P.CP_HE)
            Tf_out = Tg
            out = ('he', Tg)
        else:
            h = P.h_l(self.T_sl)
            for i in range(n):
                Tw = self.Tw[i]
                if h < hls:
                    Tf, x = P.t_from_h_liquid(h), 0.0
                elif h < hvs:
                    Tf, x = Ts, (h - hls) / (hvs - hls)
                else:
                    Tf, x = Ts + (h - hvs) / P.CP_O2_GAS, 1.0
                if x >= 0.95:
                    hc = 80.0                               # ASSUMPTION vapor convection
                    eff = 1 - math.exp(-hc * A / (mdot * P.CP_O2_GAS))
                    q = mdot * P.CP_O2_GAS * (Tw - Tf) * eff
                else:
                    dTw = Tw - Ts
                    # ASSUMPTION boiling curve: film above 40 K superheat,
                    # nucleate 3..40 K, forced liquid convection below.
                    hc = 200.0 if dTw > 40 else (3000.0 if dTw > 3 else 1000.0)
                    q = hc * A * (Tw - Tf)
                    if q > 0:
                        q = min(q, mdot * (hvs - h) + mdot * P.CP_O2_GAS * max(Tw - Ts, 0))
                # do not overshoot the wall in one step
                cap = 0.5 * mw * P.cp_ss(Tw) * abs(Tw - Tf) / dt
                q = max(-cap, min(cap, q))
                Q[i] = q
                h += q / mdot
            if h < hls:
                Tf_out = P.t_from_h_liquid(h)
            elif h < hvs:
                Tf_out = Ts
            else:
                Tf_out = Ts + (h - hvs) / P.CP_O2_GAS
            out = ('o2', h)
        for i in range(n):
            self.Tw[i] += (q_env - Q[i]) * dt / (mw * P.cp_ss(self.Tw[i]))
        # flowing outlet sensor: tau 0.5 s (ASSUMPTION)
        self.T_out += (Tf_out - self.T_out) * min(dt / 0.5, 1.0)
        return out

    def _receiver(self, dt, inflow, mdot, pos):
        pO2, pHe = self.p_rx_parts()
        p = pO2 + pHe
        Ts = P.tsat(max(pO2, 800.0))
        hls, hvs = P.h_l(Ts), P.h_v(Ts)
        hfg = hvs - hls
        Vg = self.v_gas_rx()
        m_g = self.m_v + self.m_he_rx
        cv_g = (self.m_v * P.CV_O2_GAS + self.m_he_rx * P.CV_HE) / m_g
        R_g = (self.m_v * P.R_O2 + self.m_he_rx * P.R_HE) / m_g
        cp_g = cv_g + R_g
        gam = cp_g / cv_g
        E_g = 0.0          # energy into gas node [W], excluding p dV
        dm_v = 0.0
        dm_he = 0.0
        dm_l = 0.0
        E_l = 0.0          # sensible energy into liquid node [W]
        Q_sp = 0.0
        m_lin, T_lin = 0.0, Ts
        # ---- inflow from the line ----
        if inflow is not None and mdot > 0:
            kind, val = inflow
            if kind == 'he':
                dm_he += mdot
                E_g += mdot * (P.CP_HE * val - P.CV_HE * self.T_g)
            else:
                h = val
                if self.Tw_rx > Ts:
                    Q_sp = self.hA_spray * (mdot / 0.27) * (self.Tw_rx - Ts)
                    Q_sp = min(Q_sp, mdot * max(hvs - h, 0.0))
                    h += Q_sp / mdot
                if h <= hls:
                    m_lin, T_lin = mdot, P.t_from_h_liquid(h)
                elif h < hvs:
                    x = (h - hls) / hfg
                    m_lin, T_lin = mdot * (1 - x), Ts
                    dm_v += mdot * x
                    E_g += mdot * x * (P.CP_O2_GAS * Ts - P.CV_O2_GAS * self.T_g)
                else:
                    Tv = Ts + (h - hvs) / P.CP_O2_GAS
                    dm_v += mdot
                    E_g += mdot * (P.CP_O2_GAS * Tv - P.CV_O2_GAS * self.T_g)
        # ---- wall exchange ----
        f_wet = min(self.m_l / P.rho_l(self.T_l) / self.V_rx, 1.0)
        Q_wl = 300.0 * self.A_rx * f_wet * (self.Tw_rx - self.T_l)      # ASSUMPTION h
        Q_wg = 10.0 * self.A_rx * (1 - f_wet) * (self.Tw_rx - self.T_g)  # ASSUMPTION h
        if self.m_l < 0.05:
            Q_wl = 0.0
        E_g += Q_wg
        # ---- interface ----
        mdot_ev = 0.0
        if self.m_l > 0.05:
            q_l = 100.0 * self.A_interface * (self.T_l - Ts)   # ASSUMPTION h
            q_g = 20.0 * self.A_interface * (self.T_g - Ts)    # ASSUMPTION h
            mdot_ev = (q_l + q_g) / hfg
            if mdot_ev < 0:
                mdot_ev = max(mdot_ev, -0.2 * self.m_v / dt)
            else:
                mdot_ev = min(mdot_ev, 0.2 * self.m_l / dt)
            E_l -= q_l
            E_g -= q_g
            if mdot_ev > 0:
                E_g += mdot_ev * (P.CP_O2_GAS * Ts - P.CV_O2_GAS * self.T_g)
            else:
                E_g += mdot_ev * P.R_O2 * self.T_g
            dm_v += mdot_ev
            dm_l -= mdot_ev
        # ---- vent and relief (choked to space) ----
        if self.relief_open:
            self.relief_open = p > C.RELIEF_RX_PA - 0.1 * C.BAR   # ASSUMPTION reseat
        else:
            self.relief_open = p > C.RELIEF_RX_PA
        cda = (self.cda_vent if pos['vent_rx'] else 0.0) + (self.cda_relief if self.relief_open else 0.0)
        md_vent = P.choked_mdot(cda, p, self.T_g, R_g, gam)
        md_vent = min(md_vent, 0.2 * m_g / dt)
        self.mdot_vent = md_vent
        self.vented += md_vent * dt
        dm_v -= md_vent * self.m_v / m_g
        dm_he -= md_vent * self.m_he_rx / m_g
        E_g -= md_vent * R_g * self.T_g
        # ---- liquid node ----
        dm_l += m_lin
        m_l_new = max(self.m_l + dm_l * dt, 0.0)
        if m_l_new > 0.05:
            cpl = P.cp_l(self.T_l)
            H = self.m_l * cpl * self.T_l
            H += (m_lin * cpl * T_lin + E_l + Q_wl) * dt
            if mdot_ev > 0:
                H -= mdot_ev * cpl * self.T_l * dt     # evaporated mass leaves
            else:
                H += -mdot_ev * cpl * Ts * dt          # condensate joins at Tsat
            self.T_l = H / (m_l_new * cpl)
        elif m_lin > 0:
            self.T_l = T_lin
        dV_l = (m_l_new - self.m_l) / P.rho_l(self.T_l)
        self.m_l = m_l_new
        # ---- gas node ----
        E_g += p * dV_l / dt     # -p dV_gas: work done on the gas as the liquid grows
        m_v_new = max(self.m_v + dm_v * dt, 1e-6)
        m_he_new = max(self.m_he_rx + dm_he * dt, 0.0)
        m_g_new = m_v_new + m_he_new
        cv_new = (m_v_new * P.CV_O2_GAS + m_he_new * P.CV_HE) / m_g_new
        U = m_g * cv_g * self.T_g + (E_g + (dm_v * P.CV_O2_GAS + dm_he * P.CV_HE) * self.T_g) * dt
        self.T_g = max(U / (m_g_new * cv_new), 55.0)
        self.m_v, self.m_he_rx = m_v_new, m_he_new
        # ---- bulk boiling if the pool is superheated ----
        pO2, _ = self.p_rx_parts()
        Ts2 = P.tsat(max(pO2, 800.0))
        if self.m_l > 0.05 and self.T_l > Ts2:
            m_boil = self.m_l * P.cp_l(self.T_l) * (self.T_l - Ts2) / P.h_fg(Ts2)
            m_boil = min(m_boil, 0.5 * self.m_l)
            Ug = (self.m_v * P.CV_O2_GAS + self.m_he_rx * P.CV_HE) * self.T_g
            Ug += m_boil * P.CV_O2_GAS * Ts2
            self.m_l -= m_boil
            self.m_v += m_boil
            self.T_g = Ug / (self.m_v * P.CV_O2_GAS + self.m_he_rx * P.CV_HE)
            self.T_l = Ts2
        # ---- wall ----
        self.Tw_rx += (self.q_env_rx + self.q_inject_rx - Q_wl - Q_wg - Q_sp) * dt / (
            self.m_rx_wall * P.cp_al(self.Tw_rx))


class PlantSim(Node):
    def __init__(self):
        super().__init__('plant_sim', parameter_overrides=[])
        self.declare_parameter('speedup', 10.0)
        self.declare_parameter('wall_tick_s', 0.01)
        self.declare_parameter('seed', 1)
        self.declare_parameter('receiver_volume', 0.922)
        self.speedup = float(self.get_parameter('speedup').value)
        self.wall_tick = float(self.get_parameter('wall_tick_s').value)
        self.rng = random.Random(int(self.get_parameter('seed').value))
        self.plant = Plant(self.rng, float(self.get_parameter('receiver_volume').value))
        self.dt = 0.01                       # spec: MCU pulse resolution 10 ms
        self.t = 0.0
        # ---- MCU state ----
        self.sp_valves = {v: False for v in VALVES}
        self.sp_press_duty = 0.0
        self.sp_valves_t = None              # WALL time of last /setpoint/valves
        self.setpoint_stale = False
        self.sp_pulse = {'enable': False, 'period': C.PULSE_PERIOD_S, 'duty': C.PULSE_DUTY}
        self.sp_latch = False
        self.sp_thermal = {'elec_heater_W': 0.0}
        self.hb_last = None                  # sim time of last heartbeat seen by MCU
        self.hb_stamp = None                 # sim stamp carried by last heartbeat (pacing)
        self.hb_wall = None
        self.watchdog = False
        self.overpressure = False
        self.cmd = {v: False for v in VALVES}
        self.pos = {v: False for v in VALVES}
        self.cmd_hist = []                   # (t, cmd) for 20 ms actuator delay
        self.mismatch = {v: False for v in VALVES}
        self.mismatch_t = {v: 0.0 for v in VALVES}
        # ---- coupling ----
        self.latch_sw = [False, False]
        self.latch_t = 0.0
        # ---- host ----
        self.host_req = False
        self.host_req_t = None
        self.accel_g = 0.0
        self.unsettled_for = 0.0
        # ---- injections ----
        self.inj = {}
        self.drift = {}
        self.flow_bias = 1.0
        self.last_pub = -1.0
        self.last_truth = -1.0
        self.max_hb_gap = 0.0

        self.pub_clock = self.create_publisher(Clock, '/clock', 10)
        self.pub_p = self.create_publisher(String, '/sensors/pressure', C.QOS_SENSOR)
        self.pub_T = self.create_publisher(String, '/sensors/temperature', C.QOS_SENSOR)
        self.pub_f = self.create_publisher(String, '/sensors/flow', C.QOS_SENSOR)
        self.pub_c = self.create_publisher(String, '/sensors/coupling', C.QOS_SENSOR)
        self.pub_v = self.create_publisher(String, '/valves/state', C.QOS_RELIABLE)
        self.pub_acc = self.create_publisher(String, '/host/accel', C.QOS_SENSOR)
        self.pub_att = self.create_publisher(String, '/host/attitude_status', C.QOS_SENSOR)
        self.pub_truth = self.create_publisher(String, '/sim/truth', C.QOS_RELIABLE)
        self.create_subscription(String, '/setpoint/valves', self.on_valves, C.QOS_RELIABLE)
        self.create_subscription(String, '/setpoint/pulse', self.on_pulse, C.QOS_RELIABLE)
        self.create_subscription(String, '/setpoint/coupling', self.on_latch, C.QOS_RELIABLE)
        self.create_subscription(String, '/setpoint/thermal', self.on_thermal, C.QOS_RELIABLE)
        self.create_subscription(String, '/setpoint/heartbeat', self.on_hb, C.QOS_RELIABLE)
        self.create_subscription(String, '/host/request', self.on_host, C.QOS_RELIABLE)
        self.create_subscription(String, '/sim/inject', self.on_inject, C.QOS_RELIABLE)
        self.timer = self.create_timer(self.wall_tick, self.tick)
        self.get_logger().info(f'plant_sim up, speedup {self.speedup}x')

    # ---------- inputs ----------
    def on_valves(self, msg):
        d = C.jload(msg)
        for v in VALVES:
            if v in d:
                self.sp_valves[v] = bool(d[v])
        self.sp_press_duty = float(d.get('press_duty', 0.0))
        self.sp_valves_t = C.wall_s()          # wall clock, see common.py

    def on_pulse(self, msg):
        self.sp_pulse.update(C.jload(msg))

    def on_latch(self, msg):
        self.sp_latch = bool(C.jload(msg).get('latch', False))

    def on_thermal(self, msg):
        self.sp_thermal.update(C.jload(msg))

    def on_hb(self, msg):
        d = C.jload(msg)
        self.hb_stamp = float(d.get('t', self.t))
        self.hb_wall = self.get_clock().now().nanoseconds * 1e-9
        if self.inj.get('heartbeat_loss'):
            return                      # injected: link to MCU drops heartbeats
        if self.hb_last is not None:
            self.max_hb_gap = max(self.max_hb_gap, self.t - self.hb_last)
        self.hb_last = self.t

    def on_host(self, msg):
        req = bool(C.jload(msg).get('settling', False))
        if req and not self.host_req:
            self.host_req_t = self.t
        self.host_req = req

    def on_inject(self, msg):
        d = C.jload(msg)
        f = d.get('fault')
        self.get_logger().warn(f'INJECT {d} at sim t={self.t:.1f}')
        if f == 'clear':
            self.inj, self.drift, self.flow_bias = {}, {}, 1.0
            self.plant.cda_leak = 0.0
            self.plant.q_inject_rx = 0.0
            return
        self.inj[f] = d
        if f == 'overpressure':
            self.plant.q_inject_rx = float(d.get('heat_W', 30000.0))
        elif f == 'leak':
            self.plant.cda_leak = float(d.get('cda', 5e-11))
        elif f == 'sensor_drift':
            self.drift[d.get('sensor', 'p_rx_a')] = [float(d.get('rate', 1000.0)),
                                                     float(d.get('max', 3e4)), 0.0]
        elif f == 'flowmeter_bias':
            self.flow_bias = float(d.get('scale', 1.25))

    # ---------- MCU ----------
    def mcu_step(self, sensors_p):
        t = self.t
        if self.hb_last is not None:
            self.watchdog = (t - self.hb_last) > C.HEARTBEAT_TIMEOUT_S
        cmd = dict(self.sp_valves)
        if self.sp_pulse.get('enable'):
            period = max(float(self.sp_pulse.get('period', C.PULSE_PERIOD_S)), 0.1)
            duty = min(max(float(self.sp_pulse.get('duty', C.PULSE_DUTY)), 0.0), 1.0)
            phase = math.fmod(t, period)
            opn = phase < duty * period - 1e-9
            cmd['in_a'] = cmd['in_b'] = opn
        # pressurant: MCU-timed duty inside a 100 ms window (ASSUMPTION)
        cmd['press'] = math.fmod(t, 0.1) < self.sp_press_duty * 0.1 - 1e-9
        # hard interlocks (ignore software)
        p_rx = max(sensors_p['p_rx_a'], sensors_p['p_rx_b'])
        p_ln = max(sensors_p['p_line_a'], sensors_p['p_line_b'])
        if p_rx >= C.MCU_RX_LIMIT_PA or p_ln >= C.MCU_LINE_LIMIT_PA:
            if not self.overpressure:
                self.get_logger().warn(f'MCU overpressure interlock p_rx={p_rx:.0f} p_line={p_ln:.0f}')
            self.overpressure = True            # latched until power cycle (ASSUMPTION)
        # setpoint freshness (ASSUMPTION, added 2026-11-01): stale valve setpoints = lost link
        if self.sp_valves_t is not None:
            self.setpoint_stale = (C.wall_s() - self.sp_valves_t) > C.SETPOINT_TIMEOUT_S
        if self.watchdog or self.setpoint_stale:
            cmd = {v: False for v in VALVES}
            cmd['line_vent'] = True             # ASSUMPTION safe state = SAFE-mode valves
            cmd['vent_rx'] = self.sp_valves.get('vent_rx', False) or p_rx > C.VENT_OPEN_PA
        if self.overpressure:
            cmd['in_a'] = cmd['in_b'] = cmd['press'] = False
            cmd['vent_rx'] = True
        if self.mismatch['in_b']:
            cmd['in_a'] = False                 # close the series valve upstream
        if self.mismatch['in_a']:
            cmd['in_b'] = False
        self.cmd = cmd
        # actuators: 20 ms transport delay (ASSUMPTION), stuck valves ignore command
        self.cmd_hist.append((t, dict(cmd)))
        while len(self.cmd_hist) > 1 and self.cmd_hist[1][0] <= t - 0.02 + 1e-9:
            self.cmd_hist.pop(0)
        delayed = self.cmd_hist[0][1]
        stuck = self.inj.get('stuck_valve')
        for v in VALVES:
            self.pos[v] = delayed[v]
            if stuck and stuck.get('valve') == v:
                self.pos[v] = bool(stuck.get('pos', True))
            # position switch vs command, debounce 0.2 s (ASSUMPTION)
            if self.pos[v] != cmd[v]:
                self.mismatch_t[v] += self.dt
                if self.mismatch_t[v] > 0.2 and not self.mismatch[v]:
                    self.mismatch[v] = True
                    self.get_logger().warn(f'MCU: valve {v} position mismatch')
            else:
                self.mismatch_t[v] = 0.0

    # ---------- sensors ----------
    def noisy(self, x, sd):
        return x + self.rng.gauss(0.0, sd)

    def read_pressures(self):
        pl = self.plant
        sd = 50.0                                   # ASSUMPTION transducer noise [Pa]
        ps, prx, pln = pl.p_supply(), pl.p_rx(), pl.p_line
        d = {'p_supply_a': self.noisy(ps, sd), 'p_supply_b': self.noisy(ps, sd),
             'p_line_a': self.noisy(pln, sd), 'p_line_b': self.noisy(pln, sd),
             'p_rx_a': self.noisy(prx, sd), 'p_rx_b': self.noisy(prx, sd),
             'p_bottle': self.noisy(pl.p_bottle(), 2000.0)}   # ASSUMPTION 0.02 bar
        for k, (rate, mx, acc) in self.drift.items():
            if k in d:
                d[k] += acc
        return d

    def tick(self):
        # pacing barrier: never run more than 0.5 s sim ahead of the FSW heartbeat
        # (only after the first heartbeat; released after 2 s wall of silence so a
        # dead FSW still lets the watchdog trip). See README.
        if self.hb_stamp is not None:
            wall = self.get_clock().now().nanoseconds * 1e-9
            if self.t - self.hb_stamp > 0.5 and wall - self.hb_wall < 2.0:
                return
        n = max(1, int(round(self.speedup * self.wall_tick / self.dt)))
        pl = self.plant
        for _ in range(n):
            self.t += self.dt
            for k in self.drift:
                rate, mx, acc = self.drift[k]
                self.drift[k][2] = min(acc + rate * self.dt, mx)
            sp = self.read_pressures()
            self.mcu_step(sp)
            # host settling: 5 s after the request, 1e-4 g (ASSUMPTION response)
            if self.host_req and self.host_req_t is not None and self.t - self.host_req_t > 5.0:
                self.accel_g = C.SETTLING_G * 1.05
            else:
                self.accel_g = 0.0
            if self.inj.get('settling_loss'):
                self.accel_g = 0.0
            bo = P.rho_l(pl.T_sl) * self.accel_g * P.G0 * pl.R_s ** 2 / P.sigma(pl.T_sl)
            self.unsettled_for = self.unsettled_for + self.dt if bo < 2.0 else 0.0
            pl.step(self.dt, self.pos, self.accel_g, bool(self.inj.get('vapor_ingestion')),
                    self.unsettled_for)
            # coupling latch: switches close 3 s after latch command and open 3 s after
            # unlatch command (ASSUMPTION: same actuator stroke both ways; was instant open)
            if self.sp_latch:
                self.unlatch_t = 0.0
                self.latch_t += self.dt
                if self.latch_t > 3.0:
                    self.latch_sw = [True, not bool(self.inj.get('latch_fail'))]
            else:
                self.latch_t = 0.0
                if any(self.latch_sw):
                    self.unlatch_t = getattr(self, 'unlatch_t', 0.0) + self.dt
                    if self.unlatch_t > 3.0:
                        self.latch_sw = [False, False]
            # electronics: C=2000 J/K, 15 W internal, G=1 W/K to 250 K sink (ASSUMPTION)
            q_h = min(max(float(self.sp_thermal.get('elec_heater_W', 0.0)), 0.0), 30.0)
            pl.T_elec += (15.0 + q_h - 1.0 * (pl.T_elec - 250.0)) * self.dt / 2000.0
        msg = Clock()
        msg.clock.sec = int(self.t)
        msg.clock.nanosec = int(round((self.t - int(self.t)) * 1e9)) % 1000000000
        self.pub_clock.publish(msg)
        if self.t - self.last_pub >= 0.02 - 1e-9:      # 50 Hz sim (hw_interface rate)
            self.last_pub = self.t
            self.publish_sensors()
        if self.t - self.last_truth >= 0.5:
            self.last_truth = self.t
            self.publish_truth()

    def mcu_flowing(self):
        return self.pos['in_a'] and self.pos['in_b']

    def publish_sensors(self):
        pl = self.plant
        t = self.t
        p = self.read_pressures()
        p['t'] = t
        self.pub_p.publish(C.jmsg(p))
        sdT = 0.1                                   # ASSUMPTION thermometer noise [K]
        T = {'t': t, 'T_supply_liq': self.noisy(pl.T_sl, sdT),
             'T_line_wall': [self.noisy(x, sdT) for x in pl.Tw],
             'T_out_a': self.noisy(pl.T_out, sdT), 'T_out_b': self.noisy(pl.T_out, sdT),
             'T_rx_wall': self.noisy(pl.Tw_rx, sdT), 'T_rx_liq': self.noisy(pl.T_l, sdT),
             'T_rx_ull': self.noisy(pl.T_g, sdT), 'T_bottle': self.noisy(pl.T_b, sdT),
             'T_elec': self.noisy(pl.T_elec, sdT), 'T_coupling': self.noisy(pl.T_cpl, sdT)}
        for k, (rate, mx, acc) in self.drift.items():
            if k in T:
                T[k] += acc
        self.pub_T.publish(C.jmsg(T))
        sdf = 0.005                                 # ASSUMPTION 0.5 % flow meter noise
        self.pub_f.publish(C.jmsg({
            't': t,
            'mdot_rx_in': pl.mdot_rx_in * self.flow_bias * (1 + self.rng.gauss(0, sdf)),
            'mdot_vent': pl.mdot_vent * (1 + self.rng.gauss(0, sdf))}))
        self.pub_c.publish(C.jmsg({'t': t, 'contact': True, 'latch_a': self.latch_sw[0],
                                   'latch_b': self.latch_sw[1],
                                   'seal_ok': all(self.latch_sw)}))
        self.pub_v.publish(C.jmsg({'t': t, 'cmd': self.cmd, 'pos': self.pos,
                                   'mismatch': self.mismatch,
                                   'interlock': {'overpressure': self.overpressure,
                                                 'watchdog': self.watchdog,
                                                 'setpoint_stale': self.setpoint_stale},
                                   'relief_rx_open': pl.relief_open}))
        self.pub_acc.publish(C.jmsg({'t': t, 'accel_g': self.noisy(self.accel_g, 2e-6)}))
        self.pub_att.publish(C.jmsg({'t': t, 'rate_dps': 0.02, 'hold': True}))  # ASSUMPTION

    def publish_truth(self):
        pl = self.plant
        self.pub_truth.publish(C.jmsg({
            't': self.t, 'fill': pl.fill_fraction(), 'm_l': pl.m_l, 'T_l': pl.T_l,
            'T_g': pl.T_g, 'p_rx': pl.p_rx(), 'p_supply': pl.p_supply(), 'p_line': pl.p_line,
            'Tw_line': pl.Tw, 'Tw_rx': pl.Tw_rx, 'T_out': pl.T_out, 'M_sl': pl.M_sl,
            'p_bottle': pl.p_bottle(), 'mdot_line': pl.mdot_line, 'mdot_vent': pl.mdot_vent,
            'dumped_overboard': pl.dumped_overboard, 'vented': pl.vented,
            'delivered': pl.delivered, 'gas_ingestion': pl.gas_ingestion,
            'pos': self.pos, 'watchdog': self.watchdog, 'overpressure': self.overpressure,
            'setpoint_stale': self.setpoint_stale,
            'mismatch': self.mismatch, 'relief_open': pl.relief_open,
            'max_hb_gap': self.max_hb_gap, 'accel_g': self.accel_g}))


def main(args=None):
    rclpy.init(args=args)
    node = PlantSim()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
