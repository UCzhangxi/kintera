#!/usr/bin/env python3
"""Regenerate model inputs and compare data plus plotted values for EVERY figure.

No SVG hashes participate. Missing data, missing/new figures, changed array shapes,
nonfinite classes and integers fail. Eight binary64 ULPs permit roundoff only;
every changed floating value is retained for owner review, even if accepted.
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys

import render_figures as rf
from figure_values import compare

D = Path(__file__).resolve().parents[1]
BASELINE = D/'environment/figure-values.json'


def data(path):
    obj = json.loads(path.read_text())  # missing or malformed input is a failure
    obj.pop('provenance', None)
    return obj


@contextmanager
def redirect(mapping):
    original = Path.open
    def redirected(path, *args, **kwargs):
        target = mapping.get(path.resolve(), path)
        return original(target, *args, **kwargs)
    Path.open = redirected
    try:
        yield
    finally:
        Path.open = original


def capture(out):
    index, rows = rf.render(out, formats=(), record=True)
    return index, rows


def check(baseline, index, regenerated):
    results = {}
    for name in sorted(baseline['figures'].keys() | index.keys()):
        expected = baseline['figures'].get(name)
        if expected is None or name not in index:
            results[name] = {'pass': False, 'error': 'missing/new figure without reviewed baseline'}
            continue
        try:
            if 'error' in index[name]:
                raise ValueError(index[name]['error'])
            changes = compare(expected['values'], index[name]['values'], '/plotted')
            for path in expected['inputs']:
                if path not in regenerated:
                    raise FileNotFoundError('missing regenerated input: '+path)
                changes += compare(baseline['data'][path], regenerated[path], '/input/'+path)
            results[name] = {'pass': all(c['pass'] for c in changes), 'changes': changes,
                             'kind': expected['kind'], 'inputs': expected['inputs']}
        except (KeyError, FileNotFoundError, ValueError) as exc:
            results[name] = {'pass': False, 'error': str(exc)}
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=D/'build/figure-values')
    ap.add_argument('--write-baseline', action='store_true', help='explicit maintenance only; never used by audit')
    args = ap.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    if args.write_baseline:
        index, rows = capture(out/'reference')
        if any('error' in row for row in index.values()):
            raise RuntimeError('cannot write baseline from failed figures')
        baseline = {'reference_report_sha': '1839c0dc5e51bbb4de5ee4c9ddd7340478ec7518',
                    'policy': '8 binary64 ULPs; integers, strings, structure and nonfinite classes exact',
                    'figures': {}, 'data': {}}
        for name, row in rows.items():
            inputs = row['data']
            for path in inputs:
                baseline['data'][path] = data(D/path)
            baseline['figures'][name] = {'values': index[name]['values'], 'inputs': inputs,
                                         'kind': 'model' if inputs else 'schematic'}
        BASELINE.write_text(json.dumps(baseline, indent=1, allow_nan=False)+'\n')
        print('Baseline written:', len(index), 'figures; explicit review required')
        return 0
    baseline = json.loads(BASELINE.read_text())
    for path in baseline['data']:
        fresh = out/(('ch05/' if '/ch05/' in path else '')+Path(path).name)
        fresh.unlink(missing_ok=True)
    runs = D/'src/kintera_report'
    commands = [
        [sys.executable, '-P', str(runs/'ch04/runs/fig_tp_sweep.py'), str(out/'tp_coldstart.json')],
        [sys.executable, '-P', str(runs/'ch04/runs/fig_partition.py'), str(out/'uv_partition_tref.json')],
        [sys.executable, '-P', str(runs/'ch05/runs/run_equilibrium.py'), str(out/'ch05')],
    ]
    failures = []
    for i, command in enumerate(commands):
        with (out/f'writer-{i}.log').open('w') as log:
            result = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            failures.append({'command': command, 'exit': result.returncode})
    regenerated, mapping = {}, {}
    for path in baseline['data']:
        fresh = out/(('ch05/' if '/ch05/' in path else '')+Path(path).name)
        try:
            # A failed writer must not be hidden by stale output from an older run.
            if failures:
                raise RuntimeError('model writer failed; numerical inputs invalid')
            regenerated[path] = data(fresh)
            mapping[(D/path).resolve()] = fresh
        except (OSError, ValueError, RuntimeError) as exc:
            failures.append({'input': path, 'error': str(exc)})
    # Redirect even missing inputs: never silently fall back to committed model data.
    for path in baseline['data']:
        mapping[(D/path).resolve()] = out/(('ch05/' if '/ch05/' in path else '')+Path(path).name)
    try:
        with redirect(mapping):
            index, _ = capture(out/'regenerated')
        results = check(baseline, index, regenerated)
    except Exception as exc:
        results = {}; failures.append({'error': str(exc)})
    passed = sum(r['pass'] for r in results.values())
    payload = {'policy': baseline['policy'], 'figures': results, 'failures': failures,
               'passed': passed, 'total': len(baseline['figures'])}
    (out/'comparison.json').write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n')
    print(f'Figure numerical data: {passed}/{len(baseline["figures"])} passed; {len(failures)} errors')
    return int(bool(failures) or any(not row['pass'] for row in results.values())
               or passed != len(baseline['figures']))


if __name__ == '__main__':
    raise SystemExit(main())
