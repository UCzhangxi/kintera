"""Execute the report's inventory; exit zero is execution evidence, not numerical equivalence.

CPU only. Appendix A/B/C/F/G/H content is excluded; shared generators still run.
No historical outputs or external scratch scripts are used as inputs.
"""
import json
import hashlib
import os
from pathlib import Path
import re
import runpy
import shlex
import shutil
import signal
import subprocess
import time
from inventory_policy import gpu_only

D = Path(__file__).resolve().parents[1]
E = D / '.reproduce/logs'
P = D / '.reproduce/sources/kintera'
E.mkdir(parents=True, exist_ok=True)
runpy.run_path(str(D / 'environment/inventory.py'))
rows = json.loads((E / 'inventory-initial.json').read_text())
results = []
seen = {}

def run(name, command, cwd=D, timeout=600):
    key = (command, str(cwd))
    if key in seen:
        return seen[key]
    cwd.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    log = E / (name + '.log')
    with log.open('w') as out:
        proc = subprocess.Popen(command, shell=True, executable='/bin/bash', cwd=cwd,
                                stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            code = 124
    result = dict(name=name, command=command, cwd=str(cwd), exit=code,
                  seconds=round(time.monotonic()-start, 2), log=str(log))
    (E / (name+'.json')).write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
    seen[key] = result
    return result

for i, item in enumerate(rows):
    c = item['command']
    name = f'item-{i:03d}'
    reason = None
    # Retain classifications; do not silently execute GPU claims on a CPU build.
    if gpu_only(c):
        reason = 'GPU-only/paired-device claim: not validated by CPU setup'
    elif c.startswith(('ThermoX', '[NO')):
        reason = 'Missing public experiment driver/complete executable command'
    elif item['kind'] == 'shell-block':
        reason = 'Recipe covered by source build or provenance wrapper; see build log'
    elif c.startswith(('cmake', 'ctest')) and item['chapter'] == 'ch12':
        reason = 'GPU or uncommitted patched build: not reproduced by normal CPU build'
    elif c == 'python <script>':
        reason = 'Expanded into individual public examples below'
    elif c in ('pytest', 'ctest'):
        reason = 'Explanatory command reference; complete suite executed separately'
    if reason:
        results.append(dict(**item, disposition=reason))
        continue
    c = re.sub(r'^(?:CUDA_VISIBLE_DEVICES=""|KINTERA_WT=<build>|KINTERA_REPO=<kintera checkout>)\s+', '', c)
    c = c.replace('<out_dir>', str(E/'ch05-cpu')).replace('<out.json>', str(E/(name+'.json-output')))
    c = c.replace('<file>', str(E/'pytest.xml')).replace('<case>', 'thermox_cpu_half')
    c = c.replace('<names>', 'h2o_ideal h2o_ideal_ddT nh3_ideal na_h2s_visscher_ddT')
    c = c.replace('<venv>', str(D/'.reproduce'/name))
    c = c.replace('<fresh check_ch12_twins output>', str(E/'gpu-not-run.log'))
    cwd = D
    for token in re.findall(r'(?:doc/tech-report/)?(?:src/kintera_report/|derivation-checks/)[^\s]+\.(?:py|sh)', c):
        rel = token.removeprefix('doc/tech-report/')
        c = c.replace(token, shlex.quote(str(D/rel)))
        cwd = E/('scratch-'+hashlib.sha256(c.encode()).hexdigest()[:16])
    if c.startswith('python check_ch12_'):
        c = c.replace('python ', 'python '+str(D/'derivation-checks/ch12')+'/')
    if 'ch01/runs/snippet.py' in c:
        cwd = P  # the documented snippet opens examples/jupiter.yaml
    elif c.startswith('ctest'):
        cwd = P/'build/tests'
    elif c.startswith(('git ', 'grep ', 'pytest', 'python -m pytest')):
        cwd = P/'tests' if c.startswith('grep') else P
    if '<' in c or '>' in c:
        results.append(dict(**item, disposition='Unresolved recipe placeholder: '+c))
        continue
    result = run(name, c, cwd, 1800 if 'pip_install' in c or 'build_from_source' in c else 600)
    results.append(dict(**item, execution=result))

for p in sorted((D/'derivation-checks').rglob('*.py')):
    if not p.name.startswith(('check_', 'validate_')):
        run('helper-'+p.parent.name+'-'+p.stem, 'python '+shlex.quote(str(p)), E/('helper-'+p.stem))
for rel in ['ch04/checks/equilibrate_uv_check.py', 'ch05/checks/newton_check.py',
            'ch09/runs/atm2d_run.py', 'ch12/runs/time_dispatch.py']:
    run(Path(rel).stem, 'python -P '+str(D/'src/kintera_report'/rel), E/'extra-runs')
for n in [20,30]:
    run(f'uv-coldstart-{n}', f'python -P {D}/src/kintera_report/ch04/runs/uv_coldstart.py {n}', E/'extra-runs')
for case in ['nh3_160','nh3_120','h2o_300']:
    for flag in ['off','on']:
        run(f'uv-h2cp-{case}-{flag}', f'python -P {D}/src/kintera_report/ch04/runs/uv_h2cp.py {case} {flag}', E/'extra-runs')
run('quick-start-maxiter0', f'python -P {D}/src/kintera_report/ch01/runs/quick_start.py 0', E/'extra-runs')
ex = E/'examples'
shutil.copytree(P/'examples', ex, dirs_exist_ok=True)
for p in sorted(ex.glob('*.py')):
    run('example-'+p.stem, 'python '+shlex.quote(p.name), ex, 180)
run('paddle-migration', 'python environment/paddle_migration.py', D)
commands = {
 'guard-effects': ('python invariants/check_guard_effects.py', D),
 'invariants': ('python invariants/check_invariants.py --output '+str(E/'invariants.json'), D),
 'guard-coverage': ('python invariants/inventory_guards.py '+str(P)+' --check --require-effects', D),
 'guard-inventory': ('python invariants/inventory_guards.py '+str(P)+' --check', D),
 'figure-values': ('python tools/check_figure_values.py --out '+str(E/'figure-values'), D),
 'cpp-tests': ("ctest -V -R '\\.release'", P/'build/tests'),
 'ctest': ('ctest --output-on-failure --timeout 1800', P/'build/tests'),
 'report-tests': ('python -m pytest tools/tests -q', D),
 'anchors': ('python tools/code_anchors.py check', D),
 'citations': ('python tools/check_citations.py', D),
 'test-index': ('python tools/gen_test_index.py --check', D),
 'test-index-refresh': (f'python tools/gen_test_index.py --refresh {P}/build', D),
 'book-list': ('python tools/book_chapters.py', D),
 'math-spans': ("find book -name '*.qmd' | sort | xargs python tools/check_math_spans.py", D),
 'cells': ('python tools/check_table_cells.py book/', D),
 'glance': ('python tools/check_glance_boxes.py', D),
 'ratchet': ('python tools/ratchet_gate.py check', D),
 'figstyle': ('python tools/check_figstyle.py', D),
 'figures': ('python tools/render_figures.py', D),
 'figure-manifest': ('python tools/render_figures.py --check', D),
 'manifest-regenerate': ('python tools/render_figures.py --manifest', D),
}
for name, (cmd,cwd) in commands.items():
    run(name, cmd, cwd, 1800)
# A complete fresh render must not reuse the committed Quarto freeze.
freeze = D/'book/_freeze'
if freeze.exists():
    shutil.move(str(freeze), str(E/'original-freeze'))
run('render', 'quarto render book/ -M latex-auto-install:false', D, 3600)
run('render-gate', 'python tools/render_gate.py book/', D, 3600)
(E/'inventory-results.json').write_text(json.dumps(results, indent=2))
(E/'executions.json').write_text(json.dumps(list(seen.values()), indent=2))
failures = sum(r['exit'] != 0 for r in seen.values())
print(f'{len(seen)} executions; {failures} nonzero exits. Numerical comparisons require review.')
paddle_conflicts = json.loads((E/'paddle-conflicts.json').read_text())
print('Unresolved Paddle runtime constraints:', paddle_conflicts)
raise SystemExit(bool(failures or paddle_conflicts))
