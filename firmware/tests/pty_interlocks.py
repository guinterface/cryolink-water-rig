"""Fault switch injection over actual serial PTY, no ROS dependency."""
import json
import os
from pathlib import Path
import pty
import subprocess
import sys
import time
import tty
import serial
from rig_bridge.protocol import encode, decode


def main():
    root=Path(__file__).resolve().parents[1]
    control=root/'logs/interlock_control.json'
    master,slave=pty.openpty();tty.setraw(master);tty.setraw(slave)
    p=subprocess.Popen([sys.executable,'-m','rig_bridge.emulator','--fd',str(master),
                        '--log',str(root/'logs/interlocks_serial.jsonl'),'--control',str(control)],pass_fds=(master,))
    port=serial.Serial(os.ttyname(slave),115200,timeout=.15)
    seq=0
    rows=[]
    try:
        for blocked in ('seat','latch'):
            control.write_text(json.dumps({'block_'+blocked:True}))
            deadline=time.monotonic()+1.
            rejected=0
            while time.monotonic()<deadline:
                seq+=1
                port.write(encode('SP',seq,carriage=0,latch='closed',feed=1,drain=0,hb=seq))
                raw=port.readline()
                if not raw:continue
                _,st=decode(raw,'ST')
                assert not st['feed'],st
                if st['fault']=='INTERLOCK':rejected+=1
                rows.append({'blocked':blocked,'status':st})
            assert rejected>=5,rows
        control.write_text('{}')
        deadline=time.monotonic()+1.
        while time.monotonic()<deadline:
            seq+=1;port.write(encode('SP',seq,carriage=0,latch='closed',feed=1,drain=0,hb=seq))
            raw=port.readline()
            if raw:
                _,st=decode(raw,'ST')
                if st['feed']:break
        else:raise AssertionError('feed did not recover with both switches true')
        print('PTY false seat and false latch: every feed-open rejected; healthy feed opens PASS')
        (root/'logs/interlocks_result.json').write_text(json.dumps({'passed':True,'samples':rows},indent=2)+'\n')
    finally:
        port.close();p.terminate();p.wait(timeout=5);os.close(master);os.close(slave)
        control.unlink(missing_ok=True)


if __name__=='__main__':main()
