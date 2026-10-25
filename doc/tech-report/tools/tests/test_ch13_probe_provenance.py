"""The probe's integration step is an input, not a measured runtime."""
import ast
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import check_provenance as cp

REPORT = Path(__file__).resolve().parents[2]
SECTION = 'chapters/13-verification/_device-coverage.qmd'


def test_probe_tag_passes_provenance_without_fabricated_timing():
    tags = [t for t in cp.tags(REPORT / 'book') if t['file'] == SECTION]
    probe = next(t for t in tags if 'gpu_probe.py' in t['text'])
    assert cp.problems(probe, lambda sha: None) == []
    assert 'scope' not in probe['fields'] and 'reps' not in probe['fields']
    tree = ast.parse((REPORT / 'src/kintera_report/ch13/runs/gpu_probe.py').read_text())
    default = next(k.value.value for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == '--dt'
                   for k in n.keywords if k.arg == 'default')
    assert f'default `--dt` ({default:g})' in probe['text']


def test_device_coverage_header_uses_verified_inventory_pin():
    text = (REPORT / 'book' / SECTION).read_text()
    assert f'pin: kintera@{cp.read_pin(REPORT)} (main)' in text


def test_device_coverage_has_no_math_span_errors():
    import check_math_spans as maths
    assert list(maths.bad_spans((REPORT / 'book' / SECTION).read_text())) == []


def test_invariant_section_has_no_history_or_missing_incoming_reference():
    import ratchet_gate as rg
    counts = rg.count(REPORT)['ch13']
    assert counts['history'] == 0
    assert counts['xref'] == 0


def test_math_checker_skips_code_but_keeps_adjacent_broken_math():
    import check_math_spans as maths
    for code in ['`echo "$HOME"`', '``literal ` and $HOME``', '`echo\n"$HOME"`']:
        assert list(maths.bad_spans(code + '\nGood $x$.')) == []
        errors = list(maths.bad_spans(code + '\nBad $ x$.'))
        assert len(errors) == 1 and errors[0][2] == 'whitespace after the opening $'
