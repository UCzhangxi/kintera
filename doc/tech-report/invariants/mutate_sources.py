"""Apply one explicit break to a disposable source checkout, never an installation."""
import argparse
from pathlib import Path
import subprocess

PIN = 'e357792d50639d68e9090b542edf038d2b029aa2'
MUTATIONS = {
 'floor': ('src/kinetics/kinetics.cpp',
           'auto conc_pos = conc.clamp_min(0.);',
           'auto conc_pos = conc.clamp_min(1e-300);'),
 'atoms': ('src/kinetics/evolve_implicit_impl.h',
           'delta[t] = x[t];',
           'delta[t] = t == nspecies - 1 ? T(0) : x[t];'),
 'energy': ('src/thermo/eval_uhs.cpp',
            'auto result = uref_R + temp.unsqueeze(-1) * cref_R + intEng_R_extra;',
            'auto result = uref_R * torch::arange(conc.size(-1), temp.options()).lt(2) + temp.unsqueeze(-1) * cref_R + intEng_R_extra;'),
}
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('mutation', choices=MUTATIONS)
a = p.parse_args()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.source, text=True).strip() == PIN
assert not subprocess.check_output(['git', 'diff', '--name-only'], cwd=a.source, text=True).strip(), 'Use a clean disposable checkout'
f, old, new = MUTATIONS[a.mutation]
s = (a.source / f).read_text()
expected = 2 if a.mutation == 'floor' else 1
assert s.count(old) == expected
(a.source / f).write_text(s.replace(old, new))
print(subprocess.check_output(['git', 'diff', '--', f], cwd=a.source, text=True))
