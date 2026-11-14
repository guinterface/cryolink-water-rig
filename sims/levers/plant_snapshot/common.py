"""Shared names, QoS profiles, thresholds and message helpers.

Messages are std_msgs/String carrying JSON (SIL simplification: no custom
.msg package, so the workspace builds with ament_python only). /mode is a
plain mode name, /cmd/operator a plain command word.
"""
import json
import time

from rclpy.qos import (QoSProfile, ReliabilityPolicy, DurabilityPolicy,
                       HistoryPolicy)
from std_msgs.msg import String

# ---- QoS (spec section 2: commands/setpoints/fault reliable; sensors best
# effort keep-last; /mode transient local) ----
QOS_RELIABLE = QoSProfile(depth=20, reliability=ReliabilityPolicy.RELIABLE,
                          durability=DurabilityPolicy.VOLATILE,
                          history=HistoryPolicy.KEEP_LAST)
QOS_SENSOR = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                        durability=DurabilityPolicy.VOLATILE,
                        history=HistoryPolicy.KEEP_LAST)
QOS_MODE = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                      durability=DurabilityPolicy.TRANSIENT_LOCAL,
                      history=HistoryPolicy.KEEP_LAST)
# ASSUMPTION: /state/* topics are treated like setpoints (reliable, depth 10).
QOS_STATE = QOS_RELIABLE

# ---- Modes (spec 3.3) ----
SAFE = 'SAFE'
STANDBY = 'STANDBY'
MATED = 'MATED'
LEAK_CHECK = 'LEAK_CHECK'
LINE_CHILLDOWN = 'LINE_CHILLDOWN'
RECEIVER_CHILL = 'RECEIVER_CHILL'
FILL = 'FILL'
TOP_OFF = 'TOP_OFF'
DRAIN_AND_PURGE = 'DRAIN_AND_PURGE'
DEMATE = 'DEMATE'
HOLD = 'HOLD'
NOMINAL_SEQUENCE = [SAFE, STANDBY, MATED, LEAK_CHECK, LINE_CHILLDOWN,
                    RECEIVER_CHILL, FILL, TOP_OFF, DRAIN_AND_PURGE, DEMATE,
                    STANDBY]
LOX_MODES = (LINE_CHILLDOWN, RECEIVER_CHILL, FILL, TOP_OFF)

# ---- Fault table (spec 3.4): id -> mode after ----
FAULT_TABLE = {
    'OVERPRESSURE': SAFE,
    'LEAK_CHECK_FAIL': STANDBY,
    'SETTLING_LOST': HOLD,
    'VAPOR_AT_OUTLET': HOLD,
    'STUCK_VALVE': SAFE,
    'SENSOR_DISAGREE': HOLD,
    'HEARTBEAT_LOST': SAFE,
    'FILL_DISAGREE': HOLD,
    'LATCH_NOT_CONFIRMED': STANDBY,
    'NODE_LOST': SAFE,   # ASSUMPTION (added 2026-11-01 after the crash test): a dead flight node
}
# ASSUMPTION: these two HOLD faults resume automatically once clear
# ("wait for host", "resume when settled"); the other HOLD faults need an
# operator 'resume'.
AUTO_RESUME_FAULTS = ('SETTLING_LOST', 'VAPOR_AT_OUTLET')

# ---- Starting numbers (spec 3.2 unless marked ASSUMPTION) ----
BAR = 1.0e5
PULSE_PERIOD_S = 3.0             # spec
PULSE_DUTY = 0.10                # spec
CHILL_MARGIN_K = 5.0             # spec (line); reused for receiver = ASSUMPTION
CHILL_HOLD_S = 30.0              # spec
SUPPLY_DP_PA = 1.0 * BAR         # spec
SUPPLY_DEADBAND_PA = 0.05 * BAR  # spec
TOPOFF_DP_PA = 0.3 * BAR         # ASSUMPTION: reduced dP for TOP-OFF
SUPPLY_P_MAX_PA = 4.8 * BAR      # ASSUMPTION: supply setpoint cap
VENT_OPEN_PA = 3.5 * BAR         # spec
VENT_CLOSE_PA = 3.0 * BAR        # spec
RELIEF_RX_PA = 4.0 * BAR         # spec
MCU_RX_LIMIT_PA = 3.8 * BAR      # ASSUMPTION: MCU limit below the relief
MCU_LINE_LIMIT_PA = 5.0 * BAR    # ASSUMPTION: line rated above supply
RELIEF_LINE_PA = 5.5 * BAR       # ASSUMPTION
FILL_TOPOFF_START = 0.90         # ASSUMPTION: FILL -> TOP-OFF at 90 %
FILL_CUTOFF = 0.95               # spec: close inlet at 95 %
FILL_DISAGREE = 0.03             # spec: 3 % (read as % of tank capacity)
LEAK_P_PA = 2.0 * BAR            # spec
LEAK_HOLD_S = 120.0              # spec
LEAK_LIMIT_PA = 100.0            # spec
LEAK_SETTLE_S = 10.0             # ASSUMPTION: thermal settling before hold
HEARTBEAT_TIMEOUT_S = 1.0        # spec (ASSUMPTION in the doc)
HEARTBEAT_PERIOD_S = 0.1         # ASSUMPTION: FSW sends heartbeat at 10 Hz
DISAGREE_K = 2.0                 # spec
DISAGREE_PA = 0.1 * BAR          # spec
VAPOR_MARGIN_K = 2.0             # spec
SETTLING_G = 1.0e-4              # spec (ASSUMPTION in the doc)
SETTLING_OK_G = 0.8e-4           # ASSUMPTION: 20 % margin for accel noise
ATTITUDE_RATE_DPS = 0.1          # spec
LATCH_TIMEOUT_S = 10.0           # ASSUMPTION
FAULT_DEBOUNCE_S = 1.0           # ASSUMPTION
ALIVE_PERIOD_S = 0.5             # ASSUMPTION: every FSW node beats /fsw/alive at 2 Hz
NODE_TIMEOUT_S = 2.0             # ASSUMPTION: 4 missed beats -> NODE_LOST
SETPOINT_TIMEOUT_S = 1.0         # ASSUMPTION: MCU drops /setpoint/valves older than this
# Liveness ages (NODE_TIMEOUT_S, SETPOINT_TIMEOUT_S) are measured on the WALL clock, like the
# plant pacing barrier. In flight wall = sim time; in the 10x SIL a sim-time 2 s limit was only
# 0.2 s of real time and Python start-up jitter raised false NODE_LOST (regression 2026-11-01).


def wall_s():
    return time.monotonic()


def jmsg(d):
    m = String()
    m.data = json.dumps(d)
    return m


def jload(msg):
    try:
        return json.loads(msg.data)
    except (ValueError, TypeError):
        return {}


def now_s(node):
    return node.get_clock().now().nanoseconds * 1e-9
