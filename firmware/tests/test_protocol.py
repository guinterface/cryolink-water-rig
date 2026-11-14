import random
import subprocess
import unittest
from rig_bridge.protocol import crc16, encode, decode, Framer, newer
from rig_bridge.emulator import MCU


class ProtocolTests(unittest.TestCase):
    def test_crc_reference(self):
        self.assertEqual(crc16(b'123456789'), 0x29B1)

    def test_roundtrip_and_cpp_parser(self):
        rng = random.Random(21)
        corpus = []
        for seq in range(100):
            corpus.append(encode('SP', seq, carriage=f'{rng.uniform(0,36):.3f}',
                                 latch=rng.choice(['open','closed']), feed=rng.randrange(2),
                                 drain=rng.randrange(2), hb=seq))
        corpus += [encode('SP', 2, carriage=v, latch='open', feed=0, drain=1, hb=2)
                   for v in ['nan', 'inf', '-1', '37', '']]
        corpus += [b'SP 4 carriage=0 latch=closed feed=1 drain=0 hb=4*0000\n']
        corpus += [encode('SP', 2, carriage=0, latch='open', feed=v, drain=1, hb=2)
                   for v in ['2','-1','True']]
        corpus += [encode('SP', 2, carriage=0, latch='open', feed=0, drain=1, hb=v)
                   for v in ['4294967296', '-1', '1.2']]
        corpus += [encode('SP', 2, carriage=0, latch='open', feed=0, drain=1, hb=2, extra=0)]
        expected = []
        for frame in corpus:
            try:
                decode(frame, 'SP')
                expected.append('1')
            except ValueError:
                expected.append('0')
        cpp = subprocess.run(['tests/safety_native', 'parse'], input=b''.join(corpus), capture_output=True, check=True)
        self.assertEqual(cpp.stdout.decode().splitlines(), expected)

    def test_stream_overflow_recovers_only_at_newline(self):
        frame=encode('SP', 1, carriage=0, latch='closed', feed=0, drain=1, hb=1)
        f=Framer()
        self.assertEqual(f.push(b'x'*1000+frame), [])
        self.assertEqual(f.push(frame[:5]), [])
        self.assertEqual(f.push(frame[5:]), [frame])

    def test_watchdog_invalid_replay_and_frozen_hb(self):
        m=MCU(); t=m.last
        frame=lambda seq,hb: encode('SP',seq,carriage=0,latch='closed',feed=1,drain=0,hb=hb)
        self.assertTrue(m.accept(frame(1,1),t));m.tick(t)
        m.accept(frame(2,2),t+.01);m.tick(t+.01)
        self.assertTrue(m.feed)
        for i in range(3,13):
            m.accept(frame(i,2),t+(i-2)*.1)
            m.tick(t+(i-2)*.1)
        m.tick(t+1.02)
        self.assertTrue(m.safe);self.assertFalse(m.feed);self.assertTrue(m.drain)
        self.assertFalse(m.accept(frame(12,2),t+1.03))
        self.assertFalse(m.accept(b'garbage\n',t+1.03))

    def test_wrap(self):
        self.assertTrue(newer(0,0xFFFFFFFF))
        self.assertFalse(newer(1,1))
        self.assertFalse(newer(0,1))


if __name__=='__main__':
    unittest.main(verbosity=2)
