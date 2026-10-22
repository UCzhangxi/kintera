"""Numerical figure evidence must survive export and detect input changes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_figures


def test_renderer_records_plotted_numbers(tmp_path):
    chapter = tmp_path / 'book/chapters/01-example.qmd'
    chapter.parent.mkdir(parents=True)
    chapter.write_text('''```{python}
#| label: fig-example
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([0., 1.], [1., 2.])
fig
```
''')
    index, _ = render_figures.render(tmp_path / 'out', report=tmp_path, formats=())
    assert index['fig-example']['values']['axes'][0]['lines'][0]['xy'] == [[0., 1.], [1., 2.]]


def test_numeric_changes_and_missing_data_fail():
    from figure_values import compare
    assert not all(x['pass'] for x in compare({'x': [1., 2.]}, {'x': [1., 2.01]}))
    assert not all(x['pass'] for x in compare({'x': [1.]}, {}))
    assert not all(x['pass'] for x in compare({'x': [1.]}, {'x': []}))
    assert not all(x['pass'] for x in compare({'status': 0}, {'status': 1}))


def test_roundoff_is_reported_and_bounded():
    import math
    from figure_values import compare
    changes = compare([1.], [math.nextafter(1., 2.)])
    assert len(changes) == 1 and changes[0]['pass']
    assert not all(x['pass'] for x in compare({'status': 1.}, {'status': math.nextafter(1., 2.)}))
    assert not compare([1., 'NaN'], [1., 'NaN'])
    assert not all(x['pass'] for x in compare(['NaN'], [1.]))


def test_every_figure_requires_inputs_and_baseline():
    from check_figure_values import check
    baseline = {'figures': {'fig-a': {'values': [1.], 'inputs': ['a.json'], 'kind': 'model'}},
                'data': {'a.json': {'x': [1.]}}}
    index = {'fig-a': {'values': [1.]}}
    assert not check(baseline, index, {})['fig-a']['pass']
    assert not check(baseline, {}, {'a.json': {'x': [1.]}})['fig-a']['pass']
    assert check(baseline, index, {'a.json': {'x': [1.]}})['fig-a']['pass']
    assert not check(baseline, index, {'a.json': {'x': [2.]}})['fig-a']['pass']
    assert not check(baseline, {**index, 'fig-new': {'values': [1.]}}, {})['fig-new']['pass']


def test_missing_regenerated_file_never_uses_committed_fallback(tmp_path):
    import pytest
    from check_figure_values import redirect
    committed = tmp_path / 'committed.json'
    committed.write_text('{"x": [1]}')
    with redirect({committed.resolve(): tmp_path / 'missing.json'}):
        with pytest.raises(FileNotFoundError):
            committed.read_text()
