"""Exercise native NetCDF, installed source bindings, Ctags and LuaLaTeX."""
from pathlib import Path
import subprocess
import tempfile
import importlib.metadata

subprocess.run(['python', '-m', 'pip', 'check'], check=True)
for name in ('torch', 'kintera', 'pyharp', 'snapy', 'numpy', 'matplotlib'):
    __import__(name)
    print(name, importlib.metadata.version(name), flush=True)
from packaging.version import Version
assert Version(importlib.metadata.version('kintera')) >= Version('2.6.3')
subprocess.run(['nc-config', '--version'], check=True)
subprocess.run(['ctags', '--version'], check=True)
subprocess.run(['quarto', '--version'], check=True)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'netcdf.c').write_text('#include <netcdf.h>\nint main(void) { return nc_inq_libvers() == 0; }\n')
    subprocess.run(['cc', str(root / 'netcdf.c'), '-lnetcdf', '-o', str(root / 'netcdf')], check=True)
    subprocess.run([str(root / 'netcdf')], check=True)
    (root / 'smoke.tex').write_text(r'\documentclass{scrreprt}\usepackage{unicode-math}\begin{document}NetCDF and TeX smoke test: $x=1$.\end{document}')
    subprocess.run(['lualatex', '-interaction=nonstopmode', '-halt-on-error', 'smoke.tex'], cwd=root, check=True)
    assert (root / 'smoke.pdf').stat().st_size > 0
print('Environment smoke test passed', flush=True)
