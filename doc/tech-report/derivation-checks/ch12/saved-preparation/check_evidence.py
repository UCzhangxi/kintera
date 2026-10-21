"""Check saved paired evidence; expected failure probes are classified explicitly."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parent
checks=0
for name in ['kinetics64','kinetics32','workspace64','workspace32-relaxed','equilibrium64','equilibrium32','functions64','functions32','sparse64','sparse32']:
    rows=[json.loads(l) for l in (root/(name+'.jsonl')).read_text().splitlines() if l.startswith('{')]
    assert rows,name
    comparisons=[r for r in rows if 'outside_tolerance' in r and r['count']]
    assert comparisons,name
    for r in comparisons:
        assert r['outside_tolerance']==0,(name,r)
        assert r['finite_mask_mismatch']==r['nan_mask_mismatch']==r['inf_sign_mismatch']==0,(name,r)
        checks+=1
    for r in rows:
        for k in ['success_mask_mismatch','cloud_mask_mismatch','status_mismatch','iteration_mismatch','zero_mask_mismatch','positive_fraction_mask_mismatch']:
            if k in r:assert r[k]==0,(name,r)
# Deliberately too-tight float32 test must retain its measured disagreement.
rows=[json.loads(l) for l in (root/'one-cell.jsonl').read_text().splitlines() if l.startswith('{')]
status=[r for r in rows if r['label']=='one_cell/status']
assert [r['diag'] for r in status[:2]]==[11.,-2050.]
assert all(r['diag']>=0 for r in status[2:])
print(f'PASS: {checks} nonempty paired comparisons meet stated tolerances and finite-mask equality; expected one-cell status disagreement retained. This checks agreement, not universal convergence or physical accuracy.')
