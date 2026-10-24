"""Conservative source inventory: retain false positives, never infer test coverage."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

PIN = 'e357792d50639d68e9090b542edf038d2b029aa2'
PATTERN = r'1[eE]-300|clamp|clip|\b(?:fmax|fmin|maximum|minimum)\s*\(|(?:std|torch)::(?:max|min)|\.(?:max|min)\(|gas_floor|numeric_limits.*(?:min|lowest)|torch::where|\b(?:conc\w*|xfrac\w*|vapor|total|theta|lambda|lam|slack|demand)\b.*(?:[<>]=?|\?)'
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--out', type=Path, default=Path(__file__).with_name('guard-inventory.json'))
p.add_argument('--check', action='store_true')
p.add_argument('--require-effects', action='store_true', help='Fail until per-occurrence physical effect/non-reachability evidence is complete')
p.add_argument('--effects', type=Path, help='Fresh numerical effect evidence; omitted evidence is not coverage')
p.add_argument('--source-effects',type=Path,help='Source-fragment/function effect evidence')
a = p.parse_args()
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.source, text=True).strip()
assert sha == PIN, (sha, PIN)
rows = []
files = []
for f in sorted((a.source / 'src').rglob('*')):
    if not f.is_file() or f.suffix not in ('.h', '.hpp', '.cpp', '.cu', '.cuh', '.c'): continue
    rel = str(f.relative_to(a.source)); text = f.read_text()
    files.append(dict(path=rel, sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    for n, line in enumerate(text.splitlines(), 1):
        if not re.search(PATTERN, line): continue
        # Keep comments and metadata candidates so reviewers can audit exclusions.
        code = line.strip()
        if code.startswith('//') or code.startswith('*'):
            effect = 'Comment, not an executable guard.'
        elif 'clamp_min' in code:
            effect = 'Raises values below the displayed lower bound (in-place only with trailing underscore); inspect context for the guarded quantity.'
        elif 'clamp_max' in code:
            effect = 'Lowers values above the displayed upper bound; inspect context for the guarded quantity.'
        elif 'clamp(' in code or 'torch::clamp' in code:
            effect = 'Bounds the displayed argument; concentration, coefficient and index bounds are distinct.'
        elif 'torch::where' in code:
            effect = 'Selects the displayed branches elementwise; continuation lines in context give the full condition and replacements.'
        elif 'fmax' in code or '::max' in code:
            effect = 'Selects the greater argument; some hits bound work sizes rather than concentrations.'
        elif 'fmin' in code or '::min' in code:
            effect = 'Selects the lesser argument; some hits bound dimensions rather than concentrations.'
        else:
            effect = 'Conditional/bound candidate; full surrounding statement retained for semantic review.'
        if any(x in rel for x in ['/photochem/', 'falloff', '/evaporation', '/three_body', '/interpolation', 'equilibrate_tp.h', 'extrapolate_ad.cpp']):
            evidence = 'Not dispatched by the two committed invariant decks (arrhenius A=>B and partition UV nucleation); NOT a claim of non-reachability across the full report.'
        elif rel.endswith('thermo_x.cpp') and n == 332:
            evidence = 'check_guard_effects.py: absent gas maps to 1e-20 mol/m3 while absent cloud remains zero; native runtime effect measured.'
        elif rel.endswith('kinetics.cpp') and n in (327,578):
            evidence = 'Actual-source floor mutation and unchanged reaction check exercise this guard family; zero/negative effect measured in results.'
        else:
            evidence = 'Per-occurrence native effect or full-report non-reachability remains unverified; do not treat successful budgets as branch coverage.'
        rows.append(dict(path=rel,line=n,code=code,effect=effect,evidence=evidence,
                         context='\n'.join(text.splitlines()[max(0,n-3):n+3]),
                         citation=f'https://github.com/chengcli/kintera/blob/{sha}/{rel}#L{n}'))
result=dict(source=sha,pattern=PATTERN,files=files,rows=rows,
            gaps=['Lexical search is not an AST proof: macros, helper calls and algebraic guards may require manual expansion.',
                  'Selected-deck non-dispatch does not establish non-reachability on every report case.',
                  'Per-occurrence native effect coverage is incomplete and explicitly marked.'])
if a.check:
    assert json.loads(a.out.read_text()) == result, 'Source inventory changed: review guards and evidence before updating'
else:
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Source guard inventory', '',f'Source: `{sha}`. {len(files)} source files searched; {len(rows)} candidate lines. False positives and comments are retained.', '',
           'This is a conservative search ledger, **not completed per-occurrence effect coverage**. Each row carries its evidence limitation. Full surrounding statements are in the JSON. Equivalent conditional guards are searched, but macro/AST review remains a gap.', '',
           '`'+PATTERN+'`', '', '| Source | Expression / change | Evidence |','|---|---|---|']
    for r in rows:
        lines.append('| ['+r['path']+':'+str(r['line'])+']('+r['citation']+') | `'+r['code'].replace('|','\\|')+'` — '+r['effect']+' | '+r['evidence']+' |')
    a.out.with_suffix('.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(files=len(files),candidates=len(rows),source=sha)))

if a.require_effects:
    from check_guard_coverage import coverage
    result=coverage(Path(__file__).parent,a.effects,a.source_effects)
    print(json.dumps(result))
    raise SystemExit(not result['passed'])
