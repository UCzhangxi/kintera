"""K10: an Arrhenius rate constant with Ea_R omitted gets Ea_R = 1 K (src/kinetics/arrhenius.cpp:96), not 0."""
import math
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import version_line, kintera as kt, torch  # noqa: E402

TMP = tempfile.mkdtemp(prefix="k10_")
SPECIES = ("species:\n"
           "  - {name: O, composition: {O: 1}, cv_R: 2.5}\n"
           "  - {name: H, composition: {H: 1}, cv_R: 2.5}\n"
           "  - {name: OH, composition: {O: 1, H: 1}, cv_R: 2.5}\n")


def kf(rate_constant, T):
    path = os.path.join(TMP, f"k{abs(hash(rate_constant))}.yaml")
    with open(path, "w") as f:
        f.write("reference-state: {Tref: 300., Pref: 1.e5}\n" + SPECIES + "reactions:\n"
                f"  - equation: OH => O + H\n    type: arrhenius\n    rate-constant: {rate_constant}\n")
    op = kt.KineticsOptions.from_yaml(path)
    kin = kt.Kinetics(op)
    c = torch.tensor([[1e-3, 1e-3, 1e-3]])
    k = kin.forward_with_rate_constants(torch.tensor([T]), torch.tensor([1e5]), c)[3]
    return list(op.arrhenius().Ea_R())[0], k.reshape(-1)[0].item()


print(version_line())
print(" card                          T [K]  stored Ea_R   k / k(Ea_R: 0)   exp(-1/T)")
for T in (50., 300.):
    e_omit, k_omit = kf("{A: 3.0e-3, b: 0.}", T)
    e_zero, k_zero = kf("{A: 3.0e-3, b: 0., Ea_R: 0.}", T)
    print(f" Ea_R omitted               {T:8.1f}  {e_omit:11.4f}   {k_omit / k_zero:14.6f}   {math.exp(-1 / T):9.6f}")
    print(f" Ea_R: 0                    {T:8.1f}  {e_zero:11.4f}   {1.0:14.6f}")
ok = e_omit == 0.0
print(f"omitted Ea_R stored as {e_omit:g} K (expected 0): {'PASS' if ok else 'EXPECTED-FAIL'}")
