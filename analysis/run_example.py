"""Execute a completion trace, writing a JSON result to a chosen location."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.completion import run
p=argparse.ArgumentParser();p.add_argument('--input',default='examples/query.json');p.add_argument('--output',default='example-trace.json');p.add_argument('--policy',choices=['hybrid','cumulative','mixed','vector','relational'],default='hybrid');a=p.parse_args()
result=run(17,a.policy,json.loads(Path(a.input).read_text()),detail=True)
Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(result['answer'],result['primitive_steps'])
