"""Q346c: what does warm_start change in ThermoX.forward (equilibrate_tp)?
equilibrate_tp re-tests every reaction each outer iteration (first = 0 .. nreaction,
src/thermo/equilibrate_tp.h:139-207) and never reads the incoming *nactive, so a warm start
can only permute the reaction order. Check: prime the buffers on one state, then solve a
second state cold and warm; compare diag (iterations) and the result.
"""
from common import thermo_x, jupiter_x, torch, version_line

print(version_line())
TS = [130.0, 150.0, 175.0, 200.0, 250.0]
P = torch.full((len(TS),), 1.0e5)
op, th = thermo_x(max_iter=50)
sp, x = jupiter_x(op, n=len(TS))

# prime: equilibrate a different state (warmer by 20 K) so the buffers hold a non-trivial set
xp = x.clone(); th.forward(torch.tensor(TS) + 20.0, P, xp)

res = {}
for mode in ("cold", "warm"):
    xx = x.clone(); d = torch.zeros(len(TS), 1)
    if mode == "warm":
        xp = x.clone(); th.forward(torch.tensor(TS) + 20.0, P, xp)  # re-prime
    th.forward(torch.tensor(TS), P, xx, warm_start=(mode == "warm"), diag=d)
    res[mode] = (xx, d.flatten())
print(" T[K]  diag cold  diag warm  max|x_warm - x_cold|")
for k, T in enumerate(TS):
    print(f"{T:5.0f}  {res['cold'][1][k].item():9.0f}  {res['warm'][1][k].item():9.0f}  "
          f"{(res['warm'][0][k] - res['cold'][0][k]).abs().max().item():.2e}")
