"""chilldown_controller (1 Hz setpoints): pulse-flow period/duty for the line
and receiver chill; the MCU times the pulses. Publishes /setpoint/pulse and
(addition) /state/chill with the chill-done flags the sequencer needs.
Spec 3.2: period 3 s, duty 10 % (0.3 s open); done when outlet within 5 K of
saturation for 30 s. ASSUMPTIONS: "saturation" = Tsat at receiver pressure
(the outlet pressure once liquid is routed to the receiver); the receiver chill
reuses the same 5 K / 30 s rule on the receiver wall temperature; duty is held
at the starting value (no adaptation is specified or tuned yet).
"""
from std_msgs.msg import String

from . import common as C
from . import props as P
from .base import FswNode, run
from .common import LINE_CHILLDOWN, RECEIVER_CHILL


class ChilldownController(FswNode):
    def __init__(self):
        super().__init__('chilldown_controller')
        self.cache('/sensors/pressure', C.QOS_SENSOR, 'p')
        self.cache('/sensors/temperature', C.QOS_SENSOR, 'T', cb=self.on_T)
        self.watch_mode(self.on_mode)
        self.pub = self.create_publisher(String, '/setpoint/pulse', C.QOS_RELIABLE)
        self.pub_state = self.create_publisher(String, '/state/chill', C.QOS_STATE)
        self.ok_since = {'line': None, 'rx': None}
        self.done = {'line': False, 'rx': False}
        self.margin = {'line': None, 'rx': None}
        self.create_timer(1.0, self.tick)

    def on_mode(self, old, new):
        if new == LINE_CHILLDOWN and old != 'HOLD':
            self.done['line'], self.ok_since['line'] = False, None
        if new == RECEIVER_CHILL and old != 'HOLD':
            self.done['rx'], self.ok_since['rx'] = False, None

    def pulsing(self):
        return self.mode in (LINE_CHILLDOWN, RECEIVER_CHILL) and self.step.get('step') == 'FLOW'

    def on_T(self, T):
        p = self.last.get('p')
        if not p or not self.pulsing():
            return
        t = self.now()
        ts = P.tsat(0.5 * (p['p_rx_a'] + p['p_rx_b']))
        key = 'line' if self.mode == LINE_CHILLDOWN else 'rx'
        temp = 0.5 * (T['T_out_a'] + T['T_out_b']) if key == 'line' else T['T_rx_wall']
        self.margin[key] = temp - ts
        if temp - ts <= C.CHILL_MARGIN_K:
            if self.ok_since[key] is None:
                self.ok_since[key] = t
            if t - self.ok_since[key] >= C.CHILL_HOLD_S:
                if not self.done[key]:
                    self.get_logger().info(f'{key} chill done at t={t:.1f}')
                self.done[key] = True
        else:
            self.ok_since[key] = None

    def tick(self):
        self.pub.publish(C.jmsg({'enable': self.pulsing(), 'period': C.PULSE_PERIOD_S,
                                 'duty': C.PULSE_DUTY}))
        self.pub_state.publish(C.jmsg({'line_done': self.done['line'], 'rx_done': self.done['rx'],
                                       'line_margin_K': self.margin['line'],
                                       'rx_margin_K': self.margin['rx']}))


def main(args=None):
    run(ChilldownController, args)
