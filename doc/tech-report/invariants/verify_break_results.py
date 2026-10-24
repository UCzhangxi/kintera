"""Reject crashes/import errors masquerading as successful mutation detection."""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
d = {name: json.loads((root/(name+'.json')).read_text())
     for name in ['pre', 'clean', 'floor', 'atoms', 'energy']}
for name, record in d.items():
    assert all('error' not in x for x in record['cases'].values()), (name, record)
    assert all(x['steps'] == 1000 for x in record['cases'].values())
assert d['clean']['pass']
for name in ['pre','floor']:
    r = d[name]['cases']['reaction']
    assert not r['exact_zero'] and not r['nonnegative'], (name,r)
assert not d['atoms']['cases']['reaction']['atoms']['pass_step']
assert not d['energy']['cases']['condensation']['energy']['pass_step']
print('PASS: pre-floor RED, clean GREEN, actual floor/atom/energy mutations RED with quantitative results (not exceptions)')
