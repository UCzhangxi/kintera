"""Build public source pins with the README configure/build/install sequence."""
import json
import os
from pathlib import Path
import subprocess
import sys

report = Path(__file__).resolve().parents[1]
state = report / '.reproduce'
sources = state / 'sources'
sources.mkdir(parents=True, exist_ok=True)
pins = json.loads((report / 'tools/package-pins.json').read_text())
pins['kintera'] = next(x.split(':', 1)[1].strip() for x in
                       (report / 'code_pin.yml').read_text().splitlines() if x.startswith('sha:'))

def run(args, cwd=None):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(args, cwd=cwd, check=True)

for name, sha in pins.items():
    source = sources / name
    if not source.exists():
        owner = 'elijah-mullens' if name == 'paddle' else 'chengcli'
        run(['git', 'clone', f'https://github.com/{owner}/{name}', str(source)])
    run(['git', 'checkout', '--detach', sha], source)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if actual != sha:
        raise RuntimeError(f'{name}: expected {sha}, got {actual}')

for name in ['pyharp', 'kintera', 'snapy']:
    source = sources / name
    opts = ['-DCMAKE_BUILD_TYPE=Release', '-DCUDA=OFF', '-DNETCDF=ON']
    if name == 'snapy':
        opts += ['-DUCX=OFF', '-DPNETCDF=OFF']
    run(['cmake', '-S', str(source), '-B', str(source / 'build'), *opts])
    run(['cmake', '--build', str(source / 'build'), '--parallel', os.environ.get('MAX_JOBS', '2')])
    run([sys.executable, '-m', 'pip', 'install', '--no-build-isolation', '--no-deps', str(source)])
run([sys.executable, '-m', 'pip', 'install', '--no-build-isolation', '--no-deps', '-e', str(report / 'src')])
run([sys.executable, '-m', 'pip', 'check'])

# Install the authorized public Paddle migration; pip check validates its runtime floors.
run([sys.executable, '-m', 'pip', 'install', '--no-build-isolation', '--no-deps', str(sources / 'paddle')])
run([sys.executable, '-m', 'pip', 'check'])
legacy = sources / 'paddle-legacy'
if not legacy.exists():
    run(['git', 'clone', 'https://github.com/chengcli/paddle', str(legacy)])
run(['git', 'checkout', '--detach', '3f5a07cca25b2c75e39c1d5a4afb7a7ff63d40bf'], legacy)
import tomllib
from packaging.requirements import Requirement
from importlib.metadata import version
metadata = tomllib.loads((sources / 'paddle/pyproject.toml').read_text())
conflicts = []
for text in metadata['project']['dependencies']:
    requirement = Requirement(text)
    if requirement.marker is None or requirement.marker.evaluate():
        actual = version(requirement.name)
        if actual not in requirement.specifier:
            conflicts.append({'requirement': text, 'installed': actual})
(state / 'logs/paddle-conflicts.json').write_text(json.dumps(conflicts, indent=2))
print('Paddle runtime conflicts:', conflicts, flush=True)
