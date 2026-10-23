"""Behavioral checks for the executable reference; standard library only."""
import sys,json,argparse
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.completion import run,boundary_tests
from src.dependency import run as dependency
from src.survival import remaining
p=argparse.ArgumentParser();p.add_argument('--output',default='core-checks.json');a=p.parse_args()
bad={'distances':[1],'eligible':['false'],'witness_advances':[1]}
try:run(17,'hybrid',bad)
except ValueError:pass
else:raise AssertionError('Non-Boolean eligibility accepted')
rows=[run(seed,mode) for seed in range(500) for mode in ['mixed','vector','relational','hybrid','cumulative']]
assert remaining({1:9,10:1},2)==8
try:remaining({1:9,10:1},10)
except ValueError:pass
else:raise AssertionError('Exhausted continuation accepted')
two={'distances':[5,1],'eligible':[False,True],'witness_advances':[1,1]}
assert run(17,'vector',two,True)['threshold_fraction']==0.5
assert run(17,'relational',two,True)['threshold_fraction']==0.0
split=dependency('split');pooled=dependency('pooled')
assert split['time_units']==18 and pooled['time_units']==2
result={'cases':len(rows),'primitive_steps':sum(x[0] for x in rows),'max_steps':max(x[0] for x in rows),'R_resolved_pending':sum(x[1] for x in rows),'boundaries':boundary_tests(),'dependency':{'split':split,'pooled':pooled}}
Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print('Checked',len(rows),'finite executions')
