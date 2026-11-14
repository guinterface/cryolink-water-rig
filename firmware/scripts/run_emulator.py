#!/usr/bin/env python3
"""Keep a raw PTY pair open and run the water MCU on its master."""
import argparse
import os
import pty
import tty
from rig_bridge.emulator import serve

p=argparse.ArgumentParser()
p.add_argument('--log', default='logs/manual_emulator.jsonl')
p.add_argument('--control', help='optional test-only JSON switch injection file')
a=p.parse_args()
master,slave=pty.openpty()
tty.setraw(master)
tty.setraw(slave)
print('MCU emulator port: '+os.ttyname(slave),flush=True)
print('Keep this process running; pass the port to rig.launch.py.',flush=True)
try:
    serve(master,a.log,a.control)
except KeyboardInterrupt:
    pass
finally:
    os.close(master)
    os.close(slave)
