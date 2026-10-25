"""The delivered stand-in must not certify the unrecovered patched experiment."""
import ast
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2]


def test_missing_requested_formula_fails_even_with_a_valid_formula():
    tree = ast.parse((REPORT / 'probe.py').read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    check = next(n for n in main.body if isinstance(n, ast.If)
                 and isinstance(n.test, ast.Name) and n.test.id == 'missing')
    # Execute the actual missing-name branch, without importing the native extension.
    module = ast.Module(body=[ast.FunctionDef(name='check', args=ast.arguments(
        posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=check.body, decorator_list=[])], type_ignores=[])
    import sys
    scope = dict(missing=['absent'], wanted=['h2o_ideal', 'absent'], forms=['h2o_ideal'], sys=sys)
    exec(compile(ast.fix_missing_locations(module), '<probe missing-name check>', 'exec'), scope)
    assert scope['check']() == 2


def test_unrecovered_claim_is_deferred_with_original_evidence():
    chapter = (REPORT / 'book/chapters/12-gpu/_device-functions.qmd').read_text()
    assert '4.559 against 4.333' not in chapter
    assert 'stand-in' in chapter and 'not recovered' in chapter
    archive = (REPORT / 'reviews/ch12-next-repin.md').read_text()
    assert '4.559 against 4.333' in archive
    assert 'ch12-devfn-scratch' in archive
    assert 'c197d576a42f430444f9ffffe73ef282ebdace3d' in archive
