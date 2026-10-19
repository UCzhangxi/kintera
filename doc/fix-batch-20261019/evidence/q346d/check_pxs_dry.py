"""Q346d: ThermoX "PXS->T" (src/thermo/thermo_x.cpp:287-318) on a DRY parcel (no vapour, so the
saturation adjustment does nothing and latent heat plays no role).

The input entropy S is volumetric (J m^-3 K^-1, "TPV->S" = sum_n c_n s_n with c_n from "TPX->V").
At fixed p and x, c_n ~ 1/T, so dS_vol/dT = (C_p - S_vol)/T, not C_p/T. The code's update
T <- T (1 + (S* - S)/C_p) then has the fixed-point slope S_vol/C_p = s/c_p (molar) at the root, which
depends on the arbitrary entropy constant s0_R. Oracle: T* is known; compare the returned T.
The same deck is run with the dry species' s0_R set to 0 (as in tests/jupiter.yaml) and to larger values.

Run from a scratch dir (kintera writes thermo_x_entropy_to_temp_<time>.pt there on max_iter).
"""
import os
import re
import tempfile
import warnings

from common import DECK, thermo_x, jupiter_x, torch, version_line

print(version_line())
P = 1.0e5
src = open(DECK).read()

print(" s0_R(dry)  T*[K]   s/cp(molar)  T returned (max-iter 10)   (max-iter 100)  warnings(10)")
for s0 in (0.0, 5.0, 15.7, 30.0):
    deck = src.replace("    composition: {H: 1.5, He: 0.15}\n    cv_R: 2.5\n",
                       f"    composition: {{H: 1.5, He: 0.15}}\n    cv_R: 2.5\n    s0_R: {s0}\n", 1)
    assert f"s0_R: {s0}" in deck
    fd, path = tempfile.mkstemp(suffix=".yaml", dir=".")
    os.write(fd, deck.encode()); os.close(fd)
    for Tstar in (150.0, 300.0, 600.0):
        op, th = thermo_x(deck=path, max_iter=10)
        _, x = jupiter_x(op, xh2o=0.0, xnh3=0.0, xh2s=0.0)
        t = torch.tensor([Tstar]); p = torch.tensor([P])
        conc = th.compute("TPX->V", [t, p, x])
        S = th.compute("TPV->S", [t, p, conc]).item()
        cp = th.compute("TV->cp", [t, conc]).item()
        res = []
        for mi in (10, 100):
            op2, th2 = thermo_x(deck=path, max_iter=mi)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                T = th2.compute("PXS->T", [p, x.clone(), torch.tensor([S])])
            res.append((T.item(), len(w)))
        print(f" {s0:9.1f}  {Tstar:5.0f}   {S / cp:10.3f}   {res[0][0]:22.6f}   {res[1][0]:14.6f}  {res[0][1]:3d}")
    os.remove(path)
