"""Known scientific defects cannot waive new failures, setup errors or fixes."""
import json
from pathlib import Path
import runpy
import pytest

ENV = Path(__file__).resolve().parents[2] / 'environment'
POLICY = runpy.run_path(str(ENV / 'expected_failures.py'))
RULES = json.loads((ENV / 'expected_failures.json').read_text())['rules']


@pytest.fixture(params=RULES.values(), ids=list(RULES))
def case(request):
    rule = request.param
    return dict(record={'command': rule['command'], 'exit': rule['exit']},
                output='normal scientific stdout\n'+rule['traceback']+'\n', rule=rule,
                source_sha=rule['source_sha'], script_sha256=rule['script_sha256'])


def test_exact_recorded_failure_is_expected(case):
    result = POLICY['evaluate'](**case)
    assert result['status'] == 'EXPECTED-FAIL'
    assert result['issue'] == 'https://github.com/UCzhangxi/kintera/issues/103'
    assert case['record']['exit'] == 1  # raw evidence must not be changed to success


@pytest.mark.parametrize('boundary', ['success', 'signal', 'timeout', 'shell_failure', 'launch_error',
                                     'wrong_message', 'extra_error', 'prior_setup_error', 'second_traceback', 'missing_traceback',
                                     'wrong_command', 'wrong_source', 'changed_script'])
def test_any_deviation_is_red(case, boundary):
    if boundary == 'success': case['record']['exit'] = 0
    elif boundary == 'signal': case['record']['exit'] = 139
    elif boundary == 'timeout': case['record']['exit'] = 124
    elif boundary == 'shell_failure': case['record']['exit'] = 127
    elif boundary == 'launch_error': case['record']['execution_error'] = 'could not launch interpreter'
    elif boundary == 'wrong_message': case['output'] = case['output'].replace(case['rule']['traceback'].splitlines()[-1], 'ImportError: setup failed')
    elif boundary == 'extra_error': case['output'] += 'FileNotFoundError: missing input\n'
    elif boundary == 'prior_setup_error': case['output'] = 'FileNotFoundError: missing setup input\n'+case['output']
    elif boundary == 'second_traceback': case['output'] += case['rule']['traceback']
    elif boundary == 'missing_traceback': case['output'] = 'python: cannot open file\n'
    elif boundary == 'wrong_command': case['record']['command'] = 'python missing.py'
    elif boundary == 'wrong_source': case['source_sha'] = '0'*40
    elif boundary == 'changed_script': case['script_sha256'] = '0'*64
    result = POLICY['evaluate'](**case)
    assert result['status'] in {'FAIL', 'UNEXPECTED-PASS'}


def test_unregistered_nonzero_is_not_waived():
    result = POLICY['evaluate']({'command': 'python unknown.py', 'exit': 1}, 'failure', None, '', '')
    assert result['status'] == 'FAIL'


def ledger_case(tmp_path):
    import copy
    import hashlib
    policy = copy.deepcopy(json.loads((ENV / 'expected_failures.json').read_text()))
    records = []
    for name, rule in policy['rules'].items():
        script = tmp_path / rule['script']
        script.write_text('# isolated ledger fixture\n')
        rule['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        log = tmp_path / (name+'.log')
        log.write_text(rule['traceback']+'\n')
        records.append(dict(name=name, command=rule['command'], exit=1, cwd=str(tmp_path), log=str(log)))
    return records, policy, next(iter(policy['rules'].values()))['source_sha']


def test_ledger_counts_expected_without_changing_raw_exits(tmp_path):
    records, policy, sha = ledger_case(tmp_path)
    result = POLICY['classify_ledger'](records, policy, sha)
    assert result['raw_nonzero'] == 3
    assert result['expected_failures'] == 3
    assert result['unexpected'] == 0
    assert all(r['exit'] == 1 and r['status'] == 'EXPECTED-FAIL' for r in records)


def test_missing_expected_execution_is_red(tmp_path):
    records, policy, sha = ledger_case(tmp_path)
    assert POLICY['classify_ledger']([], policy, sha)['unexpected'] > 0


def test_ledger_keeps_an_unrelated_failure_red(tmp_path):
    records, policy, sha = ledger_case(tmp_path)
    records.append(dict(name='unrelated', command='python probe.py', exit=2, cwd=str(tmp_path), log=str(tmp_path/'missing.log')))
    result = POLICY['classify_ledger'](records, policy, sha)
    assert result['expected_failures'] == 3
    assert result['unexpected'] == 1


def test_missing_log_or_script_is_red(tmp_path):
    records, policy, sha = ledger_case(tmp_path)
    Path(records[0]['log']).unlink()
    (tmp_path / policy['rules'][records[1]['name']]['script']).unlink()
    result = POLICY['classify_ledger'](records, policy, sha)
    assert result['unexpected'] == 2
    assert result['expected_failures'] == 1


def test_policy_has_independent_matching_evidence_for_both_sources():
    policy = POLICY['load_policy'](ENV / 'expected_failures.json')
    assert policy['baseline_source'] == '53f3ffcc6fefd34513dc04214d506103b2d917ed'
    assert len(policy['rules']) == 3


def test_policy_rejects_changed_verification_record(tmp_path):
    import shutil
    shutil.copyfile(ENV/'expected_failures.json', tmp_path/'expected_failures.json')
    proof = json.loads((ENV/'expected_failure_evidence.json').read_text())
    proof[0]['exit'] = 0
    (tmp_path/'expected_failure_evidence.json').write_text(json.dumps(proof))
    with pytest.raises(ValueError, match='conflicting verified'):
        POLICY['load_policy'](tmp_path/'expected_failures.json')


@pytest.mark.parametrize('mutation,exit_code', [('none',0), ('success',1), ('different_error',1), ('unrelated',1)])
def test_actual_audit_exit_uses_strict_classification(tmp_path, mutation, exit_code):
    import ast
    from types import SimpleNamespace
    records, policy, sha = ledger_case(tmp_path)
    if mutation == 'success': records[0]['exit'] = 0
    elif mutation == 'different_error': Path(records[0]['log']).write_text('ImportError: setup failed\n')
    elif mutation == 'unrelated': records.append(dict(name='probe', command='python probe.py', exit=2))
    (tmp_path/'paddle-conflicts.json').write_text('[]')
    source = ENV/'audit.py'
    tree = ast.parse(source.read_text())
    start = next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id == 'policy' for t in n.targets))
    namespace = dict(D=tmp_path, E=tmp_path, P=tmp_path, seen={r['name']:r for r in records},
                     results=[], json=json, load_policy=lambda path: policy,
                     classify_ledger=POLICY['classify_ledger'],
                     subprocess=SimpleNamespace(check_output=lambda *a,**kw: sha+'\n'))
    with pytest.raises(SystemExit) as stop:
        exec(compile(ast.Module(body=tree.body[start:],type_ignores=[]),str(source),'exec'),namespace)
    assert stop.value.code == exit_code
    ledger = json.loads((tmp_path/'executions.json').read_text())
    assert ledger[0]['exit'] == records[0]['exit']
    summary = json.loads((tmp_path/'expected-failures.json').read_text())
    assert summary['unexpected'] == exit_code
