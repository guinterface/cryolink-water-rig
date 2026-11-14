"""ASSUMPTION: CRC-16/CCITT-FALSE, UTF-8 restricted to ASCII, 256-byte frames.
CRC covers bytes before '*'; four uppercase hex digits; newline terminates.
Sequences and heartbeat counters are unsigned 32-bit with modular ordering.
"""
import math
import re

MAX_FRAME = 256


def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xFFFF
    return crc


def encode(kind, seq, **fields):
    body = f'{kind} {seq}' + ''.join(f' {k}={v}' for k, v in fields.items())
    raw = body.encode('ascii')
    frame = raw + f'*{crc16(raw):04X}\n'.encode()
    if len(frame) > MAX_FRAME:
        raise ValueError('frame too long')
    return frame


def newer(a, b):
    return b is None or 0 < ((a - b) & 0xFFFFFFFF) < 0x80000000


def decode(raw, kind):
    if len(raw) > MAX_FRAME or not raw.endswith(b'\n'):
        raise ValueError('framing')
    body, checksum = raw[:-1].split(b'*')
    if not re.fullmatch(rb'[0-9A-Fa-f]{4}', checksum) or crc16(body) != int(checksum, 16):
        raise ValueError('crc')
    words = body.decode('ascii').split(' ')
    if words[0] != kind or not re.fullmatch(r'[0-9]+', words[1]):
        raise ValueError('header')
    seq = int(words[1])
    if not 0 <= seq <= 0xFFFFFFFF:
        raise ValueError('sequence')
    fields = {}
    for word in words[2:]:
        k, v = word.split('=')
        if k in fields:
            raise ValueError('duplicate')
        fields[k] = v
    required = ('carriage latch feed drain hb' if kind == 'SP' else
                'seat latch home Twall Tin m p feed drain safe fault').split()
    if set(fields) != set(required):
        raise ValueError('fields')
    for k in required:
        v = fields[k]
        if k == 'fault':
            if v not in ('NONE', 'WATCHDOG', 'INTERLOCK', 'LATCH_FEED', 'STUCK', 'RETRACT', 'SENSOR', 'CALIBRATION'):
                raise ValueError('fault')
        elif k == 'latch' and kind == 'SP':
            if v not in ('open', 'closed'):
                raise ValueError('latch')
        elif k in ('seat', 'latch', 'home', 'feed', 'drain', 'safe'):
            if v not in ('0', '1'):
                raise ValueError('boolean')
            fields[k] = int(v)
        elif k == 'hb':
            if not re.fullmatch(r'[0-9]+', v) or not 0 <= int(v) <= 0xFFFFFFFF:
                raise ValueError('heartbeat')
            fields[k] = int(v)
        else:
            fields[k] = float(v)
            if not math.isfinite(fields[k]):
                raise ValueError('finite')
    if kind == 'SP' and not 0 <= fields['carriage'] <= 36:
        raise ValueError('travel')
    return seq, fields


class Framer:
    """Bounded stream parser; discard an entire overlong line until newline."""
    def __init__(self):
        self.buf = bytearray()
        self.dropping = False

    def push(self, data):
        out = []
        for b in data:
            if b == 10:
                if not self.dropping:
                    out.append(bytes(self.buf) + b'\n')
                self.buf.clear()
                self.dropping = False
            elif not self.dropping:
                self.buf.append(b)
                if len(self.buf) >= MAX_FRAME:
                    self.buf.clear()
                    self.dropping = True
        return out
