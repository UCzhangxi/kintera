"""Repeated chapter measurements must retain their build-specific attribution."""
from pathlib import Path
import re

REPORT = Path(__file__).resolve().parents[2]
BOOK = REPORT / 'book/chapters'


def test_active_set_historical_residual_is_attributed():
    text = (BOOK / '04-phase-equilibrium/_active-set.qmd').read_text()
    paragraph = next(p for p in text.split('\n\n') if '6.95\\times10^{-8}' in p)
    assert 'historical' in paragraph.lower()
    assert '[^ch04-conditions-check]' in paragraph
    footnotes = (BOOK / '04-phase-equilibrium/_conditions.qmd').read_text()
    note = footnotes.split('[^ch04-conditions-check]:', 1)[1].split('\n\n', 1)[0]
    assert 'historical: 0d9f67f97d841147e23283d2dcdab302238d2c45' in note
    assert '6.95\\times10^{-8}' in note
    output = (REPORT / 'derivation-checks/check_ch4_tp.out').read_text()
    residuals = [abs(float(x)) for x in re.findall(r'res=([-+\de.]+)\s+tol \|res\|', output)]
    assert max(residuals) == 1.331e-7  # distinct current-build evidence must remain intact


def test_newton_singular_value_identifies_historical_build():
    text = (BOOK / '05-chemical-equilibrium/_newton.qmd').read_text()
    paragraph = next(p for p in text.split('\n\n') if '1.6\\times10^{-17}' in p)
    assert 'historical' in paragraph.lower()
    assert '@tbl-ch05-conditions-phase-rule' in paragraph
    assert '[^ch05-newton-check]' in paragraph
    assert 'at the start state on x86_64' not in paragraph
    output = (REPORT / 'derivation-checks/check_ch5_equilibrium.out').read_text()
    assert 'sigma_min(J)=1.2e-16' in output
