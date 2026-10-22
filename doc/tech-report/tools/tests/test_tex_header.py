"""The shared PDF header must compile under the pinned LuaLaTeX toolchain."""
from pathlib import Path
import shutil
import subprocess

import pytest

REPORT = Path(__file__).resolve().parents[2]


def test_inline_code_header_compiles(tmp_path):
    latex = shutil.which('lualatex')
    if latex is None:
        pytest.skip('LuaLaTeX is supplied by the reproduction environment')
    header = REPORT / 'book/_tex/inline-code-breaks.tex'
    document = (
        r'\documentclass{scrreprt}' + '\n'
        + r'\input{' + header.as_posix() + '}\n'
        + r'\begin{document}' + '\n'
        + r'\texttt{SomeClass::member\_name} abc0123456789abcdef0123456789 $x=1$.' + '\n'
        + r'\end{document}' + '\n'
    )
    (tmp_path / 'header.tex').write_text(document)
    result = subprocess.run(
        [latex, '-interaction=nonstopmode', '-halt-on-error', 'header.tex'],
        cwd=tmp_path, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout
    assert (tmp_path / 'header.pdf').is_file()
