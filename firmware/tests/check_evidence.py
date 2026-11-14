"""Verify saved serial/CSV evidence, without rerunning or accelerating hardware."""
import csv
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
logs=root/'logs'
result=json.loads((logs/'integration_result.json').read_text())
assert result['nominal'] and result['watchdog']
assert not result['faults']
assert result['watchdog_s']<=2
# ASSUMPTION test-only discretization bound of 1 mL, not a physical fill tolerance.
assert 50 <= result['final_fill']['volume_ml'] < 51
rows=list(csv.DictReader((logs/'rig.csv').open()))
condition=[]
for row in rows:
    if row['mode']=='LINE_CHILLDOWN':
        condition.append(row)
    elif condition and row['mode']=='RECEIVER_CHILL':
        break
assert condition
cold_since=None
initial_mass=json.loads(condition[0]['ST'])['m']
for row in condition:
    t=float(row['monotonic_s']);st=json.loads(row['ST'])
    assert abs(st['m']-initial_mass)<.001, 'receiver gained mass during conditioning'
    if st['Twall']<15:
        cold_since=t if cold_since is None else cold_since
    else:
        cold_since=None
cold_hold=float(condition[-1]['monotonic_s'])-cold_since
assert cold_hold>=5, cold_hold
for name in ['seat','latch']:
    fault=json.loads((logs/f'fault_{name}/integration_result.json').read_text())
    assert fault['interlock'] and fault['blocked']==name
    assert fault['status'][name]==0 and fault['status']['feed']==0
    assert fault['status']['fault']=='INTERLOCK'
summary=dict(nominal_wall_s=result['nominal_wall_s'], fill_ml=result['final_fill']['volume_ml'],
             watchdog_s=result['watchdog_s'], measured_wall_below_15_hold_s=cold_hold,
             conditioning_receiver_gain_g=0, seat_interlock=True, latch_interlock=True,
             test_only_fill_bound_ml=[50,51])
(logs/'evidence_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
