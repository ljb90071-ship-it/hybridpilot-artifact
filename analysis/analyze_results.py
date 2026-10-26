"""Validate archived aggregates and render Markdown tables; no benchmark run."""
from pathlib import Path
import csv,json,argparse
ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT/'results'/name).open(newline='') as f:return list(csv.DictReader(f))
p=argparse.ArgumentParser();p.add_argument('--output',default='result-tables.md');a=p.parse_args()
files=['workloads.csv','latency.csv','regimes.csv','accounting.csv','slices.csv','simple_controls.csv','phase_order.csv']
data={n:read(n) for n in files}
assert [len(data[n]) for n in files]==[3,18,5,4,3,15,6]
l=data['latency.csv']; assert len({(r['family'],r['policy']) for r in l})==18
assert all(int(r['queries'])==600 and 0<float(r['geomean_ms'])<=float(r['p95_ms']) for r in l)
c=json.loads((ROOT/'results/calibration_and_cumulative.json').read_text())
for pair in c['calibration']['initial_pairs'].values():
    assert abs(pair['V'][0]+pair['P'][0]-pair['VP'][0])<1e-9
    assert abs(pair['V'][1]+pair['P'][1]-pair['VP'][1])<1e-9
assert len({(r['family'],r['policy']) for r in data['simple_controls.csv']})==15
ph={(r['policy'],r['ordering']):float(r['geomean_completion_ms']) for r in data['phase_order.csv']}
assert len(ph)==6
assert round(ph['Cumulative','early_then_late']/ph['HybridPilot','early_then_late'],2)==1.19
ratios=[]
for family in ['Catalog','Documents','Media']:
    row={r['policy']:float(r['geomean_ms']) for r in l if r['family']==family}
    ratios.append(row['AutoCost']/row['HybridPilot'])
assert [round(v,2) for v in ratios]==[1.12,1.10,1.15]
a_rows=data['accounting.csv']; cell={(r['grouping'],r['update']):int(r['geomean_ms']) for r in a_rows}
assert cell[('separate','physical')]-cell[('joint','physical')]==24
assert cell[('separate','logical')]-cell[('joint','logical')]==26
assert all(int(r['queries'])==120 for r in a_rows+data['slices.csv'])
assert [float(r['budget_ms']) for r in data['slices.csv']]==[.25,1,4]
d=json.loads((ROOT/'results/diagnostics.json').read_text()); phase=d['phase_arithmetic_means_ms']
for name in ['AutoCost','RankBenefit','HybridPilot']:assert phase['common_prefix']+phase[name+'_completion']==phase[name+'_total']
text=['# Archived result tables','', 'Generated from the supplied CSV files; times and aggregation are defined in results/README.md.','']
for name,rows in data.items():
    keys=list(rows[0]);text+=['## '+name,'','| '+' | '.join(keys)+' |','| '+' | '.join(['---']*len(keys))+' |']
    text+=['| '+' | '.join(r[k] for k in keys)+' |' for r in rows];text+=['']
text+=['AutoCost / HybridPilot geometric-mean ratios: '+', '.join(f'{v:.2f}' for v in ratios)+'.']
Path(a.output).write_text('\n'.join(text)+'\n');print('Validated seven CSV tables and phase arithmetic; rendered archived values.')
