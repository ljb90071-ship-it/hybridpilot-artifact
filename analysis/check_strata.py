"""Validate paired aggregate counts and weighted log ratios."""
from pathlib import Path
import csv, math
ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT/'results'/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))
rows=read('main_strata.csv')
lat={(x['family'],x['policy']):float(x['geomean_ms']) for x in read('latency.csv')}
simple={(x['family'],x['policy']):float(x['geomean_ms']) for x in read('simple_controls.csv')}
expected={'Catalog':(364,34,202),'Documents':(326,37,237),'Media':(381,32,187)}
assert len(rows)==18
for family in expected:
    for base in ['AutoCost','Cumulative']:
        group=[x for x in rows if x['family']==family and x['baseline']==base]
        assert {x['stratum'] for x in group}=={'Low','Middle','High'}
        assert sum(int(x['n']) for x in group)==600
        totals=tuple(sum(int(x[k]) for x in group) for k in ['hybrid_wins','ties','baseline_wins'])
        if base=='AutoCost': assert totals==expected[family]
        for x in group:
            assert sum(int(x[k]) for k in ['hybrid_wins','ties','baseline_wins'])==int(x['n'])
            assert math.isclose(float(x['log_ratio_sum']),int(x['n'])*math.log(float(x['baseline_over_hybrid_gm'])),abs_tol=1e-10)
        gm=math.exp(sum(float(x['log_ratio_sum']) for x in group)/600)
        target=(lat if base=='AutoCost' else simple)[family,base]/lat[family,'HybridPilot']
        assert math.isclose(gm,target,rel_tol=1e-12)
        print(f'{family} {base}/HybridPilot: {gm:.9f}; H/tie/B = {totals}')
print('PASS: paired counts, weighted log ratios, and published family aggregates.')
