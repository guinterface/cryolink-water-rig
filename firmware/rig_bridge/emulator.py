"""Wall-time MCU emulator. Physics constants are ASSUMPTION, not validation."""
import argparse
import json
import os
import select
import time
from .protocol import Framer, decode, encode, newer


class MCU:
    def __init__(self):
        self.seq = self.hb = None
        self.last_sp = self.last_hb = None
        self.command = dict(carriage=36., latch='open', feed=0, drain=1, hb=0)
        self.carriage = 36.
        self.latch_cmd = self.feed = self.seat = self.latch = False
        self.home = self.drain = self.safe = True
        self.fault = 'WATCHDOG'
        self.mismatch_since = None
        self.block_seat = self.block_latch = False
        self.mass = 0.
        self.wall = 22.
        self.inlet = 4.
        self.pressure = 101.325
        self.last = time.monotonic()

    def accept(self, raw, now):
        try:
            seq, sp = decode(raw, 'SP')
        except (ValueError, UnicodeError, OverflowError):
            return False
        if not newer(seq, self.seq):
            return False
        self.seq, self.command, self.last_sp = seq, sp, now
        if newer(sp['hb'], self.hb):
            self.hb, self.last_hb = sp['hb'], now
        return True

    def tick(self, now):
        dt = min(max(now - self.last, 0), 0.1)
        self.last = now
        c = self.command
        self.safe = (self.last_sp is None or now - self.last_sp >= 1 or
                     self.last_hb is None or now - self.last_hb >= 1)
        self.fault = 'WATCHDOG' if self.safe else 'NONE'
        self.feed = bool(c['feed']) and not self.safe
        self.drain = bool(c['drain']) or self.safe
        if self.feed and not (self.seat and self.latch):
            self.feed = False
            self.fault = 'INTERLOCK'
        if not self.safe:
            if c['latch'] == 'open' and self.feed:
                self.fault = 'LATCH_FEED'
            else:
                self.latch_cmd = c['latch'] == 'closed'
            target = c['carriage']
            if target > self.carriage and (self.latch or self.latch_cmd):
                self.fault = 'RETRACT'
            else:
                self.carriage = target
        # ASSUMPTION ideal motion, switches can be blocked for fault tests.
        self.seat = self.carriage <= 0.5 and not self.block_seat
        self.home = self.carriage >= 35.5
        self.latch = self.latch_cmd and self.seat and not self.block_latch
        # Remove feed immediately on a disappearing switch, same as firmware.
        if self.feed and not (self.seat and self.latch):
            self.feed, self.fault = False, 'INTERLOCK'
        mismatch = (self.latch_cmd != self.latch or
                    (self.carriage <= .5 and not self.seat) or
                    (self.carriage >= 35.5 and not self.home))
        self.mismatch_since = (now if self.mismatch_since is None else self.mismatch_since) if mismatch else None
        if self.mismatch_since is not None and now - self.mismatch_since >= .2 and not self.safe:
            if self.fault == 'NONE':
                self.fault = 'STUCK'
            self.feed = False
            self.drain = True
        # Raised fill branch: conditioning drains to waste; receiver never drains.
        if self.feed and not self.drain:
            self.mass += 3.0 * dt
        if self.feed and self.drain:
            self.wall += (self.inlet - self.wall) * (1 - pow(2.718281828, -dt / 3.0))
        gauge = self.pressure - 101.325
        if self.drain:
            gauge *= pow(2.718281828, -dt / .2)
        elif self.feed:
            gauge += (9.80665 - gauge) * (1 - pow(2.718281828, -dt / .25))
        self.pressure = 101.325 + gauge

    def status(self, seq):
        return encode('ST', seq, seat=int(self.seat), latch=int(self.latch), home=int(self.home),
                      Twall=f'{self.wall:.3f}', Tin=f'{self.inlet:.3f}', m=f'{self.mass:.3f}',
                      p=f'{self.pressure:.4f}', feed=int(self.feed), drain=int(self.drain),
                      safe=int(self.safe), fault=self.fault)


def serve(fd, log_path, control=None):
    os.set_blocking(fd, False)
    mcu, framer, seq = MCU(), Framer(), 0
    next_status = time.monotonic()
    reset_mass_id = None
    with open(log_path, 'w', buffering=1) as log:
        while True:
            now = time.monotonic()
            if control and os.path.exists(control):
                try:
                    d = json.load(open(control))
                    mcu.block_seat = bool(d.get('block_seat', False))
                    mcu.block_latch = bool(d.get('block_latch', False))
                    if d.get('reset_mass_id') != reset_mass_id:
                        reset_mass_id = d.get('reset_mass_id')
                        mcu.mass = 0.
                except (ValueError, OSError):
                    pass
            if select.select([fd], [], [], .005)[0]:
                try:
                    data = os.read(fd, 4096)
                except OSError:
                    data = b''
                for line in framer.push(data):
                    accepted = mcu.accept(line, now)
                    log.write(json.dumps({'t': now, 'rx': line.decode('ascii', 'replace').strip(), 'accepted': accepted}) + '\n')
            mcu.tick(now)
            if now >= next_status:
                frame = mcu.status(seq)
                try:
                    os.write(fd, frame)
                except (BlockingIOError, OSError):
                    pass
                log.write(json.dumps({'t': now, 'tx': frame.decode().strip()}) + '\n')
                seq = (seq + 1) & 0xFFFFFFFF
                next_status = now + .1


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fd', type=int, required=True, help='inherited PTY master descriptor')
    p.add_argument('--log', default='logs/emulator.jsonl')
    p.add_argument('--control', help='optional JSON file with block_seat / block_latch booleans')
    a = p.parse_args()
    serve(a.fd, a.log, a.control)


if __name__ == '__main__':
    main()
