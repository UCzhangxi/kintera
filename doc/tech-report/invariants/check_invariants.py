"""2603 CPU binary64 checks. No concentration repairs and no tolerated negatives."""
import argparse
import json
from pathlib import Path
import torch
import kintera as kt

D = Path(__file__).resolve().parent
N = 1000
TOL = 1e-12
R = 8.31446
torch.set_default_dtype(torch.float64)
torch.set_num_threads(1)


def budget(values, scale):
    x = torch.stack(values)
    step = ((x[1:] - x[:-1]).abs() / scale).max().item()
    total = ((x - x[0]).abs() / scale).max().item()
    return dict(max_relative_step=step, max_relative_total=total,
                mean_signed_step=((x[-1] - x[0]) / scale / N).tolist(),
                pass_step=step <= TOL)


def reaction():
    op = kt.KineticsOptions.from_yaml(str(D / 'reaction.yaml'))
    kin = kt.Kinetics(op)
    a = op.species().index('A')
    b = op.species().index('B')
    c = torch.zeros(2, 2)
    c[0, b] = 1.  # A exactly absent, B is an inert product.
    c[1, a] = 1.  # nontrivial active conversion, same chapter deck.
    temp, pres = torch.full((2,), 300.), torch.full((2,), 1e5)
    amounts, energies = [c.sum(-1)], [R * 1.5 * 300 * c.sum(-1)]
    worst_rate, minimum = 0., c.min().item()
    for _ in range(N):
        rate, dc, _ = kin.forward(temp, pres, c)
        worst_rate = max(worst_rate, rate[0].abs().max().item())
        jac = kin.jacobian(temp, c, torch.full((2,), R * 1.5), rate, dc)
        c = c + kt.evolve_implicit(rate, kin.stoich, jac, .001)
        minimum = min(minimum, c.min().item())
        amounts.append(c.sum(-1))
        energies.append(R * 1.5 * 300 * c.sum(-1))
    atoms = budget(amounts, amounts[0].abs())
    energy = budget(energies, energies[0].abs())
    return dict(steps=N, dt_s=.001, absent_rate_max=worst_rate,
                minimum_amount=minimum, final=c.tolist(),
                exact_zero=worst_rate == 0., nonnegative=minimum >= 0.,
                atoms=atoms, energy=energy)


def condensation():
    th = kt.ThermoY(kt.ThermoOptions.from_yaml(str(D / 'condensation.yaml')))
    rho, y = torch.tensor([1.]), torch.tensor([[.02], [0.]])
    inv_mu = th.buffer('inv_mu')
    cv = torch.tensor([2.5, 2.5, 9.])
    u0 = torch.tensor([0., 0., -3430.])
    # H, He, O rows; dry pseudo-species retains its specified atom counts.
    A = torch.tensor([[1.5, 2., 2.], [.15, 0., 0.], [0., 1., 1.]])
    c = (th.compute('DY->V', [rho, y]) * inv_mu)[0]
    T = torch.tensor([280.])
    independent_u = lambda c, t: (R * c * (u0 + cv * (t - 300.))).sum()
    U = independent_u(c, T).reshape(1)
    scale = (R * c * (u0.abs() + cv * (T - 300.).abs())).sum()
    atoms, energies = [A @ c], [independent_u(c, T)]
    minimum, diag_min = c.min().item(), float('inf')
    for _ in range(N):
        diag = torch.zeros(1, 1)
        th.forward(rho, U, y, False, diag)
        V = th.compute('DY->V', [rho, y])
        c = (V * inv_mu)[0]
        T = th.compute('VU->T', [V, U])
        atoms.append(A @ c)
        energies.append(independent_u(c, T))
        minimum = min(minimum, c.min().item())
        diag_min = min(diag_min, diag.item())
    return dict(steps=N, kind='closed-volume equilibrium projections, not kinetic timesteps',
                final_T_K=T.item(), final=c.tolist(), minimum_amount=minimum,
                nonnegative=minimum >= 0., diag_min=diag_min, converged=diag_min >= 0.,
                atoms=budget(atoms, atoms[0].abs()), energy=budget(energies, scale))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['all', 'reaction', 'condensation'], default='all')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = dict(kintera=kt.__version__, torch=torch.__version__, dtype='float64',
                  per_step_relative_tolerance=TOL, cases={})
    for name, fn in [('reaction', reaction), ('condensation', condensation)]:
        if args.case in ('all', name):
            try:
                v = fn()
                v['pass'] = all(v.get(k, True) for k in ['exact_zero', 'nonnegative', 'converged']) and all(v[k]['pass_step'] for k in ['atoms', 'energy'])
            except Exception as exc:
                v = dict(error=repr(exc), **{'pass': False})
            result['cases'][name] = v
    result['pass'] = all(v['pass'] for v in result['cases'].values())
    text = json.dumps(result, indent=2, allow_nan=False)
    print(text)
    if args.output:
        args.output.write_text(text + '\n')
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
