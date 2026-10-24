"""Fail closed: classification and a PASS label are never effect evidence."""
import hashlib
import json
import math
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def coverage(directory, effects=None, source_effects=None):
    registry=json.loads((directory/'guard-classification.json').read_text())
    rows=registry['rows']; ids=[r['id'] for r in rows]
    assert len(ids)==len(set(ids)), 'Duplicate inventory row'
    old=json.loads((directory/'guard-inventory.json').read_text())
    assert {r['path']+':'+str(r['line']) for r in old['rows']}<=set(ids), 'Original candidate omitted'
    proven={}
    classified={r["id"]:r for r in rows}
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
    if source_effects is not None:
        manifest_path=directory/'guard-source-fixtures.json'
        manifest=json.loads(manifest_path.read_text())
        data=json.loads(source_effects.read_text())
        assert data['source']==registry['source']==manifest['source']
        assert data['registry_sha256']==sha(directory/'guard-classification.json')
        assert data['manifest_sha256']==sha(manifest_path)
        assert data['probe_sha256']==sha(directory/'probe_source_effects.py')
        specifications={f['name']:f for f in manifest['fixtures']}
        assert len(specifications)==len(manifest['fixtures'])
        assert len(data['results'])==len(specifications), 'Missing source fixture'
        manifest_rows=[key for f in manifest['fixtures'] for key in f['rows']]
        assert len(manifest_rows)==len(set(manifest_rows))
        assert set(manifest_rows)=={r['id'] for r in rows if r.get('policy') and r['policy']!='native_clamp'}, 'Source manifest coverage mismatch'
        seen=set()
        for result in data['results']:
            name=result['name']; assert name not in seen; seen.add(name)
            spec=specifications[name]
            assert result['rows']==spec['rows'] and result['inputs']==spec['inputs']
            assert result['expected']==spec['expected'], 'Expected value mismatch'
            assert result['relative_tolerance']==spec['relative_tolerance']
            assert result['absolute_tolerance']==spec['absolute_tolerance']==0
            assert len(result['observed'])==len(spec['expected'])
            assert all(math.isfinite(x) and abs(x-y)<=spec['relative_tolerance']*abs(y) for x,y in zip(result['observed'],spec['expected'])), 'Source effect numerical mismatch'
            assert result['passed'] and data['passed'], 'Source effect failed'
            assert len(result['fragments'])==len(spec['fragments'])
            for actual,want in zip(result['fragments'],spec['fragments']):
                assert all(actual[k]==v for k,v in want.items()), 'Fragment identity mismatch'
                assert actual['sha256']==hashlib.sha256(actual['extracted'].encode()).hexdigest()
            for key in spec['rows']:
                assert key in classified and 'policy' in classified[key]
                assert key not in proven, 'Duplicate effect row'
                file,line=key.rsplit(':',1)
                assert any(f['path']==file and f['start']<=int(line)<=f['end'] for f in spec['fragments']), 'Row not compiled'
                proven[key]=result
        assert seen==set(specifications)
    missing=[r['id'] for r in rows if 'policy' in r and r['id'] not in proven]
    return dict(candidates=len(rows),applicable=sum('policy'in r for r in rows),proven=len(proven),unresolved=len(missing),missing=missing,passed=not missing)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--effects',type=Path);p.add_argument('--source-effects',type=Path);a=p.parse_args()
    result=coverage(Path(__file__).parent,a.effects,a.source_effects);print(json.dumps(result,indent=2));raise SystemExit(not result['passed'])
