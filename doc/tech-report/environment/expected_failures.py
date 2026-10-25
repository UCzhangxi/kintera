"""Classify audit executions while retaining their raw exit status."""
import re
import hashlib
import json
from pathlib import Path


def normalized_traceback(output):
    marker = 'Traceback (most recent call last):'
    if not isinstance(output, str) or output.count(marker) != 1:
        return None
    prefix = output[:output.index(marker)]
    if re.search(r'^\s*(?:[\w.]*Error:|[\w.]*Exception:|Fatal Python error:|Segmentation fault|Killed\b)',
                 prefix, re.M):
        return None
    trace = output[output.index(marker):].strip()
    return re.sub(r'(  File ")[^"\n]+/([^/"\n]+)(", line )', r'\1\2\3', trace)


def evaluate(record, output, rule, source_sha, script_sha256):
    if rule is None:
        return {'status': 'PASS' if record['exit'] == 0 and not record.get('execution_error') else 'FAIL'}
    result = {'status': 'FAIL', 'issue': rule['issue']}
    if record.get('execution_error'):
        return dict(result, reason='execution/setup failure: '+record['execution_error'])
    if record['command'] != rule['command']:
        return dict(result, reason='command differs from the verified recipe')
    if source_sha != rule['source_sha'] or script_sha256 != rule['script_sha256']:
        return dict(result, reason='source commit or executed script differs from verified evidence')
    if record['exit'] == 0:
        return dict(result, status='UNEXPECTED-PASS', reason='known defect no longer reproduces; update issue and evidence')
    if record['exit'] != rule['exit']:
        return dict(result, reason='exit status differs from the verified failure')
    if normalized_traceback(output) != rule['traceback']:
        return dict(result, reason='error signature differs from the verified failure')
    return dict(result, status='EXPECTED-FAIL', reason='exact verified failure; scientific defect remains open')


def load_policy(path):
    """Require recorded matching executions at both full scientific source commits."""
    path = Path(path)
    policy = json.loads(path.read_text())
    if policy.get('version') != 1 or not policy.get('rules'):
        raise ValueError('missing or unsupported expected-failure policy')
    baseline = policy['baseline_source']
    if not re.fullmatch('[0-9a-f]{40}', baseline):
        raise ValueError('expected-failure baseline needs a full commit')
    if policy['evidence'] != 'expected_failure_evidence.json':
        raise ValueError('unexpected evidence file')
    evidence = json.loads((path.parent / policy['evidence']).read_text())
    for name, rule in policy['rules'].items():
        script = rule['script']
        if (Path(script).name != script or not script.endswith('.py')
                or name != 'example-'+script[:-3] or rule['command'] != 'python '+script
                or rule['exit'] != 1 or not re.fullmatch('[0-9a-f]{40}', rule['source_sha'])
                or rule['source_sha'] == baseline
                or not re.fullmatch('[0-9a-f]{64}', rule['script_sha256'])
                or rule['issue'] != 'https://github.com/UCzhangxi/kintera/issues/103'
                or normalized_traceback(rule['traceback']) != rule['traceback']):
            raise ValueError('invalid expected-failure rule: '+name)
        for sha in (baseline, rule['source_sha']):
            rows = [r for r in evidence if r['source'] == sha and r['script'] == script]
            if len(rows) != 1 or any(rows[0][k] != rule[k] for k in ('exit', 'traceback', 'script_sha256')):
                raise ValueError('missing or conflicting verified source evidence: '+name+' '+sha)
    return policy


def classify_ledger(records, policy, source_sha):
    """Annotate raw results; missing recipes and unrecognized failures stay red."""
    names = [r['name'] for r in records]
    for record in records:
        rule = policy['rules'].get(record['name'])
        output, digest = '', ''
        if rule:
            try:
                output = Path(record['log']).read_text()
                digest = hashlib.sha256((Path(record['cwd']) / rule['script']).read_bytes()).hexdigest()
            except (OSError, UnicodeError) as exc:
                record['execution_error'] = str(exc)
            if names.count(record['name']) != 1:
                record['execution_error'] = 'duplicate expected execution'
        record.update(evaluate(record, output, rule, source_sha, digest))
    missing = sorted(set(policy['rules']) - set(names))
    return {'executions': len(records),
            'raw_nonzero': sum(r['exit'] != 0 for r in records),
            'expected_failures': sum(r['status'] == 'EXPECTED-FAIL' for r in records),
            'unexpected': sum(r['status'] not in {'PASS', 'EXPECTED-FAIL'} for r in records) + len(missing),
            'missing_expected': missing}
