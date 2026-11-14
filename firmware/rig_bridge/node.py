"""Hardware transport plus explicitly labeled water state adapters; wall time only."""
import csv
import json
import math
import time

import rclpy
import serial
from rclpy.node import Node
from std_msgs.msg import String
from cryolink_fsw import common as C
from .protocol import Framer, decode, encode, newer


class RigBridge(Node):
    def __init__(self):
        super().__init__('rig_bridge')
        # ASSUMPTION: ambient, density, charge/settle/decay and freshness limits are
        # provisional bench settings; wall gate and 50 mL target come from CHECKS.
        defaults = dict(port='/dev/ttyUSB0', wall_threshold_c=15., wall_hold_s=5.,
                        fill_target_ml=50., water_density_g_ml=1., ambient_kpa=101.325,
                        leak_charge_kpa=8., leak_settle_s=2., leak_hold_s=60.,
                        leak_decay_limit_pa=100., log_path='logs/rig.csv')
        for k, v in defaults.items():
            self.declare_parameter(k, v)
        self.cfg = {k: self.get_parameter(k).value for k in defaults}
        for k in defaults:
            if isinstance(defaults[k], float) and (not math.isfinite(self.cfg[k]) or
                    (k != 'wall_threshold_c' and self.cfg[k] <= 0)):
                raise ValueError(f'invalid parameter {k}')
        if self.get_parameter('use_sim_time').value:
            raise ValueError('rig_bridge requires use_sim_time=false')
        self.ser = serial.Serial(self.cfg['port'], 115200, timeout=0, write_timeout=.02)
        self.framer = Framer()
        self.seq = int(time.monotonic() * 1000) & 0xFFFFFFFF
        self.st_seq = None
        self.st = None
        self.st_time = 0.
        self.mode, self.step = 'SAFE', {}
        self.inputs, self.ages = {}, {}
        self.chill_since = None
        self.line_done = False
        self.leak = {'status': 'idle', 'adapter': 'water'}
        self.leak_start = self.leak_p0 = None
        self.prev_mass = None
        self.prev_mass_t = None
        self.last_cmd = {}
        self.armed = False
        self.pub = {}
        for topic in ('/sensors/pressure', '/sensors/temperature', '/sensors/flow',
                      '/sensors/coupling', '/host/accel', '/host/attitude_status'):
            self.pub[topic] = self.create_publisher(String, topic, C.QOS_SENSOR)
        for topic in ('/valves/state', '/rig/status', '/state/chill', '/state/fill',
                      '/leakcheck/result', '/fsw/alive', '/fault', '/sim/truth'):
            self.pub[topic] = self.create_publisher(String, topic, C.QOS_RELIABLE)
        self.create_subscription(String, '/mode', self.on_mode, C.QOS_MODE)
        self.create_subscription(String, '/sequence/step', lambda m: setattr(self, 'step', C.jload(m)), C.QOS_MODE)
        for key in ('coupling', 'valves', 'pulse', 'thermal', 'heartbeat'):
            self.create_subscription(String, '/setpoint/' + key,
                                     lambda m, k=key: self.on_input(k, m), C.QOS_RELIABLE)
        self.create_subscription(String, '/host/request', lambda m: self.on_input('host', m), C.QOS_RELIABLE)
        self.log = open(self.cfg['log_path'], 'w', newline='', buffering=1)
        self.csv = csv.writer(self.log)
        self.csv.writerow(['wall_epoch_s', 'monotonic_s', 'mode', 'step', 'SP', 'ST', 'water_leak', 'unmapped_setpoints'])
        self.create_timer(.01, self.read_serial)
        self.create_timer(.1, self.tick)
        self.create_timer(.5, lambda: self.emit('/fsw/alive', {'node': 'rig_bridge', 't': time.time()}))

    def emit(self, topic, d):
        self.pub[topic].publish(C.jmsg(d))

    def on_input(self, key, msg):
        d = C.jload(msg)
        if not isinstance(d, dict):
            return
        if key == 'heartbeat' and (type(d.get('seq')) is not int or not 0 <= d['seq'] <= 0xFFFFFFFF):
            return
        self.inputs[key], self.ages[key] = d, time.monotonic()

    def on_mode(self, msg):
        if msg.data != self.mode:
            self.chill_since = None
            if msg.data == 'LINE_CHILLDOWN':
                self.line_done = False
            if msg.data == 'LEAK_CHECK':
                self.leak = {'status': 'running', 'phase': 'PRESSURIZE', 'adapter': 'water'}
                self.leak_start = time.monotonic()
                self.leak_p0 = None
            elif msg.data in ('SAFE', 'STANDBY'):
                self.leak = {'status': 'idle', 'adapter': 'water'}
            self.mode = msg.data

    def read_serial(self):
        try:
            data = self.ser.read(4096)
        except serial.SerialException as e:
            self.get_logger().error(str(e))
            return
        for raw in self.framer.push(data):
            try:
                seq, st = decode(raw, 'ST')
                if not newer(seq, self.st_seq):
                    continue
                if not (-55 <= st['Twall'] <= 125 and -55 <= st['Tin'] <= 125 and
                        0 <= st['p'] <= 200 and -10000 <= st['m'] <= 10000):
                    continue
                self.st_seq, self.st, self.st_time = seq, st, time.monotonic()
                if self.last_cmd and not st['safe']:
                    self.armed = True
            except (ValueError, UnicodeError, OverflowError):
                continue

    def fresh(self, now):
        return self.st is not None and now - self.st_time < .5 and all(
            now - self.ages.get(k, -1e9) < 1. for k in ('heartbeat', 'valves', 'coupling'))

    def water_commands(self, now):
        st = self.st
        c, v = self.inputs.get('coupling', {}), self.inputs.get('valves', {})
        want_latch = bool(c.get('latch', False))
        # Mate with hooks open; hold carriage preload until switch reports open.
        carriage = 0. if want_latch or st['latch'] else 36.
        latch = 'closed' if want_latch and st['seat'] else 'open'
        feed, drain = bool(v.get('in_a', False)), bool(v.get('line_vent', False))
        if self.mode == 'LEAK_CHECK':
            phase = self.leak.get('phase')
            gauge = (st['p'] - self.cfg['ambient_kpa']) * 1000
            feed, drain = phase == 'PRESSURIZE', False
            if phase == 'PRESSURIZE':
                if gauge >= self.cfg['leak_charge_kpa'] * 1000:
                    self.leak['phase'] = 'SETTLE'
                    self.leak_settle_start = now
                    feed = False
                elif now - self.leak_start > 15.:
                    self.leak.update(status='fail', phase='DONE', reason='charge timeout')
                    feed = False
            elif phase == 'SETTLE' and now - self.leak_settle_start >= self.cfg['leak_settle_s']:
                self.leak['phase'] = 'HOLD'
                self.leak_hold_start = now
                self.leak_p0, self.leak_T0 = st['p'] * 1000, st['Twall'] + 273.15
            elif phase == 'HOLD':
                decay = self.leak_p0 - st['p'] * 1000 * self.leak_T0 / (st['Twall'] + 273.15)
                self.leak.update(decay_pa=decay, hold_s=now - self.leak_hold_start)
                if now - self.leak_hold_start >= self.cfg['leak_hold_s']:
                    self.leak.update(status='pass' if decay <= self.cfg['leak_decay_limit_pa'] else 'fail', phase='DONE')
        elif self.mode == 'LINE_CHILLDOWN':
            # Water continuous conditioning; FSW pulse command gates FLOW, no oxygen pulse timings.
            feed = self.step.get('step') == 'FLOW' and bool(self.inputs.get('pulse', {}).get('enable'))
            drain = True
            if feed and st['Twall'] < self.cfg['wall_threshold_c']:
                self.chill_since = self.chill_since if self.chill_since is not None else now
                if now - self.chill_since >= self.cfg['wall_hold_s']:
                    self.line_done = True
            else:
                self.chill_since = None
        elif self.mode == 'RECEIVER_CHILL':
            feed, drain = False, True  # explicit no-hardware pass-through
        elif self.mode in ('FILL', 'TOP_OFF'):
            if st['m'] >= self.cfg['fill_target_ml'] * self.cfg['water_density_g_ml']:
                feed = False
        elif self.mode == 'DRAIN_AND_PURGE':
            feed, drain = False, True  # no gas purge on the water bench
        if self.mode in ('SAFE', 'HOLD', 'DEMATE'):
            feed, drain = False, True
        return dict(carriage=carriage, latch=latch, feed=int(feed), drain=int(drain),
                    hb=self.inputs['heartbeat']['seq'])

    def tick(self):
        now = time.monotonic()
        fresh = self.fresh(now)
        if fresh:
            cmd = self.water_commands(now)
            frame = encode('SP', self.seq, **cmd)
            try:
                self.ser.write(frame)
                self.seq = (self.seq + 1) & 0xFFFFFFFF
                self.last_cmd = cmd
            except (serial.SerialException, serial.SerialTimeoutException):
                fresh = False
        self.emit('/rig/status', {'t': time.time(), 'fresh': fresh, 'mode': self.mode,
                                  'st': self.st, 'command': self.last_cmd,
                                  'assumptions': ['water adapters enabled; see README']})
        if not fresh and self.last_cmd:
            self.emit('/fault', {'id': 'NODE_LOST', 'mode_after': 'SAFE',
                                 'detail': 'rig bridge: serial or setpoint stale; stopped SP', 't': time.time()})
        # Never republish stale measurements as fresh sensor data.
        if self.st is None or now - self.st_time >= .5:
            return
        self.publish_sensors(now, fresh)
        self.csv.writerow([time.time(), now, self.mode, self.step.get('step'),
                           json.dumps(self.last_cmd), json.dumps(self.st), json.dumps(self.leak), json.dumps(self.inputs)])

    def publish_sensors(self, now, fresh):
        s, t = self.st, time.time()
        gauge = (s['p'] - self.cfg['ambient_kpa']) * 1000
        p = dict(t=t, p_line_a=gauge, p_line_b=gauge, p_supply_a=0., p_supply_b=0.,
                 p_rx_a=0., p_rx_b=0., p_bottle=0.,
                 _stubs=['p_supply_a', 'p_supply_b', 'p_rx_a', 'p_rx_b', 'p_bottle'],
                 _duplicates={'p_line_b': 'p_line_a'}, _units='Pa gauge (water adapter)')
        self.emit('/sensors/pressure', p)
        wall, inlet = s['Twall'] + 273.15, s['Tin'] + 273.15
        self.emit('/sensors/temperature', dict(t=t, T_supply_liq=inlet, T_line_wall=[wall],
                  T_out_a=wall, T_out_b=wall, T_rx_wall=295.15, T_rx_liq=295.15,
                  T_rx_ull=295.15, T_bottle=295.15, T_elec=295.15, T_coupling=wall,
                  _stubs=['T_rx_wall', 'T_rx_liq', 'T_rx_ull', 'T_bottle', 'T_elec'],
                  _proxies={'T_out_a': 'wall probe', 'T_out_b': 'wall probe', 'T_coupling': 'wall probe'}, _units='K'))
        mdot = 0. if self.prev_mass is None else (s['m'] - self.prev_mass) / (now - self.prev_mass_t) / 1000
        self.prev_mass, self.prev_mass_t = s['m'], now
        self.emit('/sensors/flow', dict(t=t, mdot_rx_in=mdot, mdot_vent=0.,
                  _derived=['mdot_rx_in: load-cell difference'], _stubs=['mdot_vent'], _units='kg/s'))
        self.emit('/sensors/coupling', dict(t=t, contact=bool(s['seat']), latch_a=bool(s['latch']),
                  latch_b=bool(s['latch']), seal_ok=bool(s['seat'] and s['latch']), home=bool(s['home']),
                  _duplicates={'latch_b': 'latch_a'}, _proxies={'seal_ok': 'seat AND latch; not leak evidence'}))
        pos = dict(in_a=bool(s['feed']), in_b=False, rx=False, line_vent=bool(s['drain']),
                   vent_rx=False, purge=False, press=False)
        self.emit('/valves/state', dict(t=t, cmd=self.last_cmd, pos=pos,
                  mismatch={'coupling': s['fault'] == 'STUCK'},
                  interlock={'watchdog': self.armed and s['fault'] == 'WATCHDOG', 'setpoint_stale': self.armed and not fresh,
                             'overpressure': False}, relief_rx_open=False,
                  _stubs=['in_b', 'rx', 'vent_rx', 'purge', 'press', 'relief_rx_open', 'overpressure'],
                  _open_loop=['in_a', 'line_vent'], fault=s['fault']))
        self.emit('/host/accel', dict(t=t, accel_g=1., _stub=True, reason='stationary Earth bench; not spacecraft settling'))
        self.emit('/host/attitude_status', dict(t=t, rate_dps=0., hold=True, _stub=True))
        fill = max(s['m'], 0) / (self.cfg['water_density_g_ml'] * self.cfg['fill_target_ml']) * C.FILL_CUTOFF
        self.emit('/state/fill', dict(t=t, fill_flow=fill, fill_pvt=fill, m_l_flow=s['m']/1000,
                  m_l_pvt=s['m']/1000, diff=0., disagree=False, adapter='water load cell',
                  _stubs=['fill_pvt', 'm_l_pvt', 'diff', 'disagree'], independent_estimates=False,
                  target_ml=self.cfg['fill_target_ml'], volume_ml=s['m']/self.cfg['water_density_g_ml']))
        self.emit('/state/chill', dict(t=t, line_done=self.line_done, rx_done=self.mode == 'RECEIVER_CHILL',
                  line_margin_K=s['Twall']-self.cfg['wall_threshold_c'], rx_margin_K=None,
                  adapter='water wall gate', _stubs=['rx_done', 'rx_margin_K']))
        self.emit('/leakcheck/result', self.leak)
        if s['fault'] in ('INTERLOCK', 'LATCH_FEED', 'RETRACT', 'SENSOR', 'CALIBRATION'):
            self.emit('/fault', dict(id='STUCK_VALVE', mode_after='SAFE', t=t, detail='MCU '+s['fault']))
        # Compatibility diagnostic topic; explicitly no independent ground truth on hardware.
        self.emit('/sim/truth', dict(t=t, fill=fill, m_l=s['m']/1000, Tw_line=[wall],
                  p_line=gauge, pos=pos, watchdog=s['fault']=='WATCHDOG', _stub=True,
                  reason='rig measurements, not simulation truth', target_fraction_scale=C.FILL_CUTOFF))

    def destroy_node(self):
        self.ser.close()  # stopping SP lets independent MCU watchdog isolate
        self.log.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RigBridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
