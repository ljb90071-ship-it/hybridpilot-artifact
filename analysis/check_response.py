"""Exact calculation of first rate crossover; no latency benchmark.

A selected VP lane completes N observations (gain,time)=(8,1), followed
by (1,1) observations. R remains runnable at rate 4. Each low observation
publishes its gain only on completion; yields occur at quarters of a unit.
At a tie VP retains service. Stop at the first decision selecting R.
"""
from fractions import Fraction as F
from pathlib import Path
import csv
import json

Q = F(3, 4)

def first_switch(n, kind):
    g, t = F(8), F(1)
    gain, time = F(24), F(3)
    for _ in range(n):
        g, t = Q*g + (1-Q)*8, Q*t + (1-Q)
        gain += 8
        time += 1
    prior_mass = F(n + 3)
    for m in range(5000):
        assert g == 1 + 7*Q**m and t == 1
        assert gain == 8*prior_mass + m and time == prior_mass + m
        for u in [F(1,4), F(1,2), F(3,4), F(1)]:
            a = F(1) if u == 1 else F(0)
            episode_rate = (3*g+a)/(3*t+u)
            cumulative_rate = (gain+a)/(time+u)
            rate = episode_rate if kind == 'episode' else cumulative_rate
            # At u=1 the gain commit and closure precede the comparison.
            if u == 1:
                assert episode_rate == (Q*g+(1-Q))/(Q*t+(1-Q))
                assert cumulative_rate == (gain+1)/(time+1)
            if rate < 4:
                elapsed = F(m) + u
                return {'old_high_episodes':n,'controller':kind,
                        'completed_low_episodes':m+int(u == 1),
                        'open_low_time':str(u if u < 1 else 0),
                        'selected_work_units':str(elapsed),
                        'selected_work_decimal':float(elapsed),
                        'rate_at_switch':str(rate),'rival_rate':4}
        g, t = Q*g + (1-Q), Q*t + (1-Q)
        gain += 1
        time += 1
    raise AssertionError('No crossover within finite diagnostic budget')

def main():
    rows=[first_switch(n,k) for n in [0,4,16,64,256]
          for k in ['episode','cumulative']]
    assert all(r['selected_work_units']=='11/4' for r in rows if r['controller']=='episode')
    assert [r['selected_work_units'] for r in rows if r['controller']=='cumulative']==['17/4','19/2','51/2','179/2','691/2']
    root=Path(__file__).resolve().parents[1]/'results'
    with (root/'response_computed.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={'scope':__doc__,'unit':'abstract selected-lane work units',
            'alpha':0.25,'yield_work_units':0.25,'rows':rows,
            'checks_passed':True}
    (root/'response_computed.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS: exact rate/closure formulas, quarter-yield crossings')
    for r in rows:print(r['old_high_episodes'],r['controller'],r['selected_work_units'])

if __name__=='__main__':main()
