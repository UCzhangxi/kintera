"""Execution metadata must never overwrite a command's numerical evidence."""
import ast
import json
from pathlib import Path
import signal
import subprocess
import time
import os


def test_command_evidence_survives_metadata(tmp_path):
    source = Path(__file__).resolve().parents[2] / 'environment' / 'audit.py'
    tree = ast.parse(source.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    namespace = dict(D=tmp_path, E=tmp_path, seen={}, json=json, time=time,
                     subprocess=subprocess, signal=signal, os=os)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
    command = "python -c 'import json; from pathlib import Path; Path(\"measurement.json\").write_text(json.dumps({\"source\": \"native\", \"values\": [0.0, 1.0]}))'"
    result = namespace['run']('measurement', command)
    assert result['exit'] == 0
    assert json.loads((tmp_path / 'measurement.json').read_text()) == {
        'source': 'native', 'values': [0.0, 1.0]}
    assert json.loads((tmp_path / 'measurement.execution.json').read_text()) == result


def test_inventory_recipe_resolves_its_json_input_from_scratch(tmp_path):
    import hashlib
    import re
    import shlex
    import sys
    report = tmp_path / 'report'
    folder = report / 'src/kintera_report/ch13/runs'
    folder.mkdir(parents=True)
    (folder / 'inventory.json').write_text('{"total": 43}')
    (folder / 'probe.py').write_text(
        'import json, sys\nfrom pathlib import Path\n'
        'assert json.loads(Path(sys.argv[2]).read_text())["total"] == 43\n')
    source = Path(__file__).resolve().parents[2] / 'environment/audit.py'
    tree = ast.parse(source.read_text())
    block = next(n for n in tree.body if isinstance(n, ast.For) and
                 isinstance(n.target, ast.Tuple) and any(isinstance(t, ast.Name) and t.id == 'item' for t in n.target.elts))
    helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'report_command']
    def run(name, command, cwd, timeout):
        cwd.mkdir(parents=True, exist_ok=True)
        p = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return {'exit': p.returncode, 'output': p.stdout + p.stderr}
    namespace = dict(D=report, E=tmp_path/'logs', P=tmp_path/'source',
                     rows=[dict(command=shlex.quote(sys.executable)+' src/kintera_report/ch13/runs/probe.py --check src/kintera_report/ch13/runs/inventory.json',
                                kind='provenance', chapter='ch13')], results=[],
                     gpu_only=lambda command: False, run=run, re=re, shlex=shlex, hashlib=hashlib)
    exec(compile(ast.Module(body=helpers+[block], type_ignores=[]), str(source), 'exec'), namespace)
    result = namespace['results'][0]['execution']
    assert result['exit'] == 0, result['output']
