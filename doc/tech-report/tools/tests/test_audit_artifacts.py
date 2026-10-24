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
