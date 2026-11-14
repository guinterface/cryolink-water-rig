"""Actual installed FSW processes, pyserial bridge and MCU over a PTY pair.
Run from firmware after source scripts/env.sh. No time acceleration or /clock.
"""
import argparse
import json
import os
from pathlib import Path
import pty
import signal
import subprocess
import sys
import time
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from cryolink_fsw import common as C
from rig_bridge.protocol import decode

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / 'logs'


def main():
    global LOG
    parser = argparse.ArgumentParser()
    parser.add_argument('--fault', choices=['heartbeat', 'seat', 'latch'], default='heartbeat')
    a = parser.parse_args()
    if a.fault != 'heartbeat':
        LOG = LOG / ('fault_' + a.fault)
    LOG.mkdir(exist_ok=True)
    control = LOG/'control.json'
    control.write_text('{}')
    procs, handles = [], []
    master, slave = pty.openpty()
    tty.setraw(master)
    tty.setraw(slave)
    port = os.ttyname(slave)

    def start(name, args, pass_fds=()):
        handle = open(LOG / (name + '.log'), 'w')
        handles.append(handle)
        p = subprocess.Popen([sys.executable] + args, cwd=ROOT, stdout=handle,
                             stderr=subprocess.STDOUT, pass_fds=pass_fds)
        procs.append(p)
        return p

    emulator = start('emulator_process', ['-m', 'rig_bridge.emulator', '--fd', str(master),
                      '--log', str(LOG/'emulator.jsonl'), '--control', str(control)], (master,))
    bridge = start('bridge', ['-m', 'rig_bridge.node', '--ros-args', '-p', f'port:={port}',
                             '-p', 'use_sim_time:=false', '-p', f'log_path:={LOG / "rig.csv"}',
                             '-p', f'leak_hold_s:={60. if a.fault == "heartbeat" else 2.}'])
    remaps = {'coupling_manager': ('/leakcheck/result', '/diagnostics/lox/leakcheck'),
              'chilldown_controller': ('/state/chill', '/diagnostics/lox/chill'),
              'fill_estimator': ('/state/fill', '/diagnostics/lox/fill')}
    for name in ['transfer_sequencer', 'coupling_manager', 'chilldown_controller',
                 'pressure_controller', 'fill_estimator', 'thermal_controller',
                 'fdir_monitor', 'host_bridge', 'tm_gateway']:
        args = ['-m', 'rig_bridge.fsw_runner', name, '--ros-args', '-p', 'use_sim_time:=false']
        if name in remaps:
            args += ['-r', ':='.join(remaps[name])]
        start(name, args)
    rclpy.init()
    node = Node('rig_integration_harness')
    t0 = time.monotonic()
    events = open(LOG/'events.jsonl', 'w', buffering=1)
    state = {'mode': None, 'step': {}, 'rig': {}, 'faults': [], 'modes': [], 'fill': {}}

    def event(topic, msg):
        d = msg.data if topic == '/mode' else json.loads(msg.data)
        events.write(json.dumps({'elapsed_s': time.monotonic()-t0, 'topic': topic, 'data': d})+'\n')
        if topic == '/mode':
            state['mode'] = d
            if not state['modes'] or state['modes'][-1] != d:
                state['modes'].append(d)
                print(f'{time.monotonic()-t0:.2f}s MODE {d}', flush=True)
        elif topic == '/sequence/step':
            state['step'] = d
        elif topic == '/rig/status':
            state['rig'] = d
        elif topic == '/state/fill':
            state['fill'] = d
        elif topic == '/fault':
            if d['id'] not in [f['id'] for f in state['faults']]:
                state['faults'].append(d)
                print('FAULT', d, flush=True)
    for topic in ('/mode', '/sequence/step', '/rig/status', '/fault', '/state/fill'):
        node.create_subscription(String, topic, lambda m, t=topic: event(t, m),
                                 C.QOS_MODE if topic in ('/mode', '/sequence/step') else C.QOS_RELIABLE)
    uplink = node.create_publisher(String, '/ground/uplink', C.QOS_RELIABLE)
    sent = set()
    result = {'nominal': False, 'watchdog': False, 'modes': [], 'faults': []}
    last_nudge = 0.
    killed_at = None
    second = False
    try:
        while time.monotonic() - t0 < 260:
            rclpy.spin_once(node, timeout_sec=.05)
            now = time.monotonic()
            dead = [p.pid for p in procs if p.poll() is not None and p is not bridge]
            assert not dead, f'process exited: {dead}'
            if killed_at is None and now - last_nudge > 1.:
                last_nudge = now
                cmd = None
                if state['mode'] == 'SAFE' and now-t0>6 and not state['faults']:
                    cmd = 'standby'
                elif state['mode']=='STANDBY' and state['step'].get('step')=='IDLE':
                    if not result['nominal']:
                        cmd = 'start'
                    elif not second:
                        second = True
                        cmd = 'start'
                elif state['mode']=='LEAK_CHECK' and state['step'].get('step')=='AWAIT_GO':
                    cmd = 'go'
                if cmd:
                    uplink.publish(String(data=cmd))
            if a.fault != 'heartbeat' and state['mode'] == 'FILL':
                st = state['rig'].get('st') or {}
                if st.get('feed') and not st.get('safe'):
                    control.write_text(json.dumps({'block_'+a.fault: True}))
                    inject_at = time.monotonic()
                    while time.monotonic()-inject_at < 2.:
                        rclpy.spin_once(node, timeout_sec=.05)
                        st = state['rig'].get('st') or {}
                        if not st.get(a.fault) and not st.get('feed') and st.get('fault') == 'INTERLOCK':
                            result.update(interlock=True, blocked=a.fault, interlock_s=time.monotonic()-inject_at, status=st)
                            print('ROS+PTY INTERLOCK PASS', a.fault, st, flush=True)
                            return
                    raise AssertionError('no INTERLOCK status after switch block')
            assert not state['faults'], f'fault before deliberate injection: {state["faults"]}'
            if 'DEMATE' in state['modes'] and state['mode']=='STANDBY' and not result['nominal']:
                assert state['modes'] == C.NOMINAL_SEQUENCE, state['modes']
                # ASSUMPTION test-only 1 mL sampling/transport bound, not bench acceptance.
                assert 50 <= state['fill']['volume_ml'] < 51, state['fill']
                result.update(nominal=True, modes=list(state['modes']),
                              final_fill=state['fill'], nominal_wall_s=now-t0)
                print('NOMINAL PASS', result, flush=True)
                control.write_text(json.dumps({'reset_mass_id': 1}))
                # ASSUMPTION test-only receiver emptied between cycles.
                # Second cycle tests kill while feed is reported open.
            if result['nominal'] and second and state['mode']=='FILL' and killed_at is None:
                st = state['rig'].get('st') or {}
                if st.get('feed') and not st.get('safe'):
                    bridge.kill()
                    bridge.wait(timeout=5)
                    killed_at = time.monotonic()
                    print('SIGKILL bridge at', killed_at-t0, flush=True)
            if killed_at is not None:
                # Read the independent MCU trace after bridge death, not stale ROS cache.
                for line in reversed((LOG/'emulator.jsonl').read_text().splitlines()[-30:]):
                    row = json.loads(line)
                    if 'tx' in row and row['t'] >= killed_at:
                        _, st = decode((row['tx']+'\n').encode(), 'ST')
                        if st['safe'] and not st['feed'] and st['drain']:
                            latency = row['t']-killed_at
                            assert latency <= 2., latency
                            result.update(watchdog=True, watchdog_s=latency, safe_status=st)
                            print('WATCHDOG PASS', latency, flush=True)
                            return
                assert now-killed_at<2.2, 'no independent SAFE status within 2s'
        raise AssertionError('integration timeout')
    finally:
        result['faults'] = state['faults']
        (LOG/'integration_result.json').write_text(json.dumps(result, indent=2)+'\n')
        control.unlink(missing_ok=True)
        events.close()
        node.destroy_node()
        rclpy.try_shutdown()
        for p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGINT)
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=5)
        for h in handles:
            h.close()
        os.close(master)
        os.close(slave)


if __name__ == '__main__':
    main()
