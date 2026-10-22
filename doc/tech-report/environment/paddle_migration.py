"""Pinned Paddle migration: execute new driver and retain explicit old/new evidence.

The card comes from public Paddle a4cac94451ab5fc800735edb00180e98859a20c2,
 tests/test_evolve_kinetics_zero_condensate.py. EOS supplies its fixed 120 K;
ThermoX, ThermoY, Kinetics and the implicit solver are the real native objects.
The optional old API adapter only maps removed Snapy index names; it is NOT an
unmodified old-runtime reproduction and does not change kinetics calculations.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import types

import torch
import kintera as kt
import snapy

D = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location('migration_driver', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(candidate, legacy, out):
    torch.set_default_dtype(torch.float64)
    card = str(Path(__file__).with_name('paddle-card.yaml'))
    tx = kt.ThermoX(kt.ThermoOptions.from_yaml(card))
    ty = kt.ThermoY(kt.ThermoOptions.from_yaml(card))
    kinetics = kt.Kinetics(kt.KineticsOptions.from_yaml(card))
    class EOS:
        def compute(self, key, args):
            assert key == 'W->T'
            return torch.full((1, 1, 2), 120.)
    class Hydro:
        def get_eos(self):
            return EOS()
    class Block:
        hydro = Hydro()
        def module(self, name):
            assert name == 'hydro.eos.thermo'
            return ty
    old = load(legacy)
    rows = []
    for solid, dt in [(0., 1.), (1e-5, 0.), (1e-5, 1.), (1e-5, 10.)]:
        w = torch.zeros((snapy.kICY+2, 1, 1, 2))
        w[snapy.kIDN] = .1; w[snapy.kIPR] = 1e4
        w[snapy.kICY] = 1e-3; w[snapy.kICY+1] = solid
        row = {'solid_mass_fraction': solid, 'dt_s': dt}
        for kind in ['original', 'api_adapter', 'migrated']:
            try:
                if kind == 'migrated':
                    value = candidate(w.clone(), EOS(), tx, ty, kinetics, dt)
                else:
                    old.snapy = snapy if kind == 'original' else types.SimpleNamespace(
                        index=types.SimpleNamespace(ipr=snapy.kIPR, icy=snapy.kICY))
                    value = old.evolve_kinetics(w.clone(), Block(), kinetics, tx, dt)
                row[kind] = {'values_kg_m3': value.tolist()}
                if kind == 'migrated':
                    assert value.shape == (2, 1, 1, 2)
                    assert torch.isfinite(value).all()
                    if dt == 0. or solid == 0.:
                        assert torch.equal(value, torch.zeros_like(value))
                    else:
                        assert (value[0] > 0).all() and (value[1] < 0).all()
                    # Same molecular species in gas/solid: mass increments cancel.
                    residual = value.sum(dim=0).abs().max().item()
                    tolerance = 32*torch.finfo(torch.float64).eps*value.abs().sum(dim=0).max().item()
                    assert residual <= tolerance
                    row['mass_residual_kg_m3'] = residual
                    row['mass_tolerance_kg_m3'] = tolerance
            except Exception as exc:
                row[kind] = {'error': type(exc).__name__+': '+str(exc)}
        a, b = row['api_adapter'], row['migrated']
        if 'values_kg_m3' in a and 'values_kg_m3' in b:
            row['max_absolute_change_kg_m3'] = (torch.tensor(a['values_kg_m3'])-torch.tensor(b['values_kg_m3'])).abs().max().item()
        rows.append(row)
    result = {'legacy_sha': '3f5a07cca25b2c75e39c1d5a4afb7a7ff63d40bf',
              'candidate_sha': json.loads((D/'tools/package-pins.json').read_text())['paddle'],
              'review_required': 'ch14 authors: new validation values and source-contract migration; approval not assumed',
              'legacy_adapter_is_not_original_reproduction': True, 'cases': rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+'\n')
    passed = sum('error' not in r['migrated'] for r in rows)
    print(f'Paddle migration: {passed}/{len(rows)} cases passed; values: {out}')
    return int(passed != len(rows))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', type=Path, help='regression probe only; default uses installed Paddle')
    ap.add_argument('--legacy', type=Path, default=D/'.reproduce/sources/paddle-legacy/src/paddle/evolve_kinetics.py')
    ap.add_argument('--out', type=Path, default=D/'.reproduce/logs/paddle-migration-values.json')
    args = ap.parse_args()
    if args.candidate:
        fn = load(args.candidate).evolve_kinetics
    else:
        from paddle import evolve_kinetics
        fn = evolve_kinetics
    raise SystemExit(run(fn, args.legacy, args.out))
