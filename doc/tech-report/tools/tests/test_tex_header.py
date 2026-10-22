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


def test_theme_chapters_without_obsolete_koma_alias(tmp_path):
    """The CI TeX Live 2026 environment removes the deprecated lowercase ifstr."""
    latex = shutil.which('lualatex')
    if latex is None:
        pytest.skip('LuaLaTeX is supplied by the reproduction environment')
    theme = REPORT / 'book/_tex/theme.tex'
    document = '\n'.join([
        r'\documentclass{scrreprt}',
        r'\usepackage{booktabs,hyperref}',
        r'\input{' + theme.as_posix() + '}',
        # Model the removed alias even on the pinned older TeX distribution.
        r'\let\ifstr\undefined',
        r'\begin{document}',
        r'\chapter{Numbered chapter} Numbered body.',
        r'\chapter*{Unnumbered chapter} Unnumbered body.',
        r'\end{document}',
    ])
    (tmp_path / 'theme.tex').write_text(document)
    result = subprocess.run(
        [latex, '-interaction=nonstopmode', '-halt-on-error', 'theme.tex'],
        cwd=tmp_path, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout
    assert (tmp_path / 'theme.pdf').is_file()
