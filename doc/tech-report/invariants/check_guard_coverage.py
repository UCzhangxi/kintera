"""Fail closed: classification and a PASS label are never effect evidence."""
import hashlib
import json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def coverage(directory, effects=None):
    registry=json.loads((directory/'guard-classification.json').read_text())
    rows=registry['rows']; ids=[r['id'] for r in rows]
    assert len(ids)==len(set(ids)), 'Duplicate inventory row'
    old=json.loads((directory/'guard-inventory.json').read_text())
    assert {r['path']+':'+str(r['line']) for r in old['rows']}<=set(ids), 'Original candidate omitted'
    proven={}
    if effects is not None:
        data=json.loads(effects.read_text())
        assert data['source']==registry['source']==old['source']
        assert data['registry_sha256']==sha(directory/'guard-classification.json')
        assert data['probe_sha256']==sha(directory/'probe_guard_operations.py')
        source_hash={f['path']:f['sha256'] for f in old['files']}
        classified={r['id']:r for r in rows}
        for result in data['rows']:
            key=result['id']; assert key not in proven, 'Duplicate effect row'
            r=classified[key]
            assert r.get('policy')=='native_clamp', 'Unsupported evidence route'
            assert result['native_call']==r['native_call']
            assert result['source_file_sha256']==source_hash[r['path']]
            assert result['absolute_tolerance']==result['relative_tolerance']==0
            assert result['inputs'] and result['observed']==result['expected'] and result['pass_'], 'Numerical effect failed'
            assert len(result['inputs'])==len(result['observed'])
            proven[key]=result
    missing=[r['id'] for r in rows if 'policy' in r and r['id'] not in proven]
    return dict(candidates=len(rows),applicable=sum('policy'in r for r in rows),proven=len(proven),unresolved=len(missing),missing=missing,passed=not missing)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--effects',type=Path);a=p.parse_args()
    result=coverage(Path(__file__).parent,a.effects);print(json.dumps(result,indent=2));raise SystemExit(not result['passed'])
