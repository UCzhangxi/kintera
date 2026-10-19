"""Reader spellings from the frozen audit must have explicit glossary routes."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import glossary_registry as registry


def test_frozen_concept_routes_exist_and_resolve():
    report = registry.REPORT
    text = (report / 'book/chapters/apph-glossary.qmd').read_text()
    routes = {'reference-pressure': 'sec-ch03-reference-state',
              'Shomate': 'sec-ch02-nasa9',
              'third-body reaction': 'sec-ch06-falloff',
              'binary diffusion': 'sec-ch09-molecular',
              'ADD_ARG': 'sec-ch11-options',
              'batch dimension': 'sec-ch12-dispatch',
              'validation tolerance': 'sec-ch13-suite',
              'operator splitting': 'sec-ch14-kinetics'}
    labs = registry.labels(report / 'book')
    for term, target in routes.items():
        lines = [l for l in text.splitlines() if f'**{term}**' in l]
        assert len(lines) == 1, term
        assert '@' + target in lines[0], term
        assert target in labs and labs[target]['level'] > 1
    for alias in ['three-body reaction', 'batch axes', 'splitting order', 'binary-diffusion coefficient']:
        assert alias in text
    data = json.loads((report / registry.REGISTRY).read_text())
    identities = [(e['kind'], e['term']) for e in data['entries']]
    assert len(identities) == len(set(identities))
    concepts = {e['term']: e['section'] for e in data['entries'] if e['kind'] == 'concept'}
    assert concepts['ADD_ARG'] == routes['ADD_ARG']
    assert concepts['validation tolerance'] == routes['validation tolerance']
    assert registry.registry_problems(report, data) == []
