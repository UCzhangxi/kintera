"""Validate supplied-script output tags; original script does not fail its exit code on FAIL."""
import pathlib,re,sys
text=pathlib.Path(sys.argv[1]).read_text()
rows=[l for l in text.splitlines() if l.startswith('(')]
expected=['a','b','c','d','e','f-evolve_implicit','f-psolve','f-equilibrate_tp','f-equilibrate_uv','f-leastsq_kkt','f-kkt_feasible_origin','f-phase_equilibrate_tp','f-uv_partition','g','h','i','j','k']
tags=[l[1:l.index(')')] for l in rows]
assert tags==expected,('missing/reordered check lines',tags)
assert all(l.endswith('PASS') for l in rows[:-1]),'FAIL or unexpected verdict'
assert rows[-1].endswith('INFO'),'float32 is informational'
assert not re.search(r'\b(?:nan|inf)\b', '\n'.join(rows),re.I),'nonfinite printed metric'
print('PASS: 17 PASS, 1 INFO, 0 FAIL, 0 EXPECTED-FAIL; all expected labels present, no printed nonfinite metrics. Original exit code alone is insufficient.')
