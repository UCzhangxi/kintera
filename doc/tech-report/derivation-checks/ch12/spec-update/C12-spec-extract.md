
### C12-a Index rule of the host and device function tables

- **Question.** Why does a name at position id of the name list call the same function on both devices?
- **Start.** Host table and names: `src/func_table.cpp:10-16`, `src/func_table.cpp:18-26`. Device table with a
  leading `nullptr`: `src/func_table.cu:9-33`; its address in constant memory: `src/func_table.cu:35`.
  Function type `double (*)(double)` on both devices: `src/utils/user_funcs.hpp:18`.
- **End.** Host index `id` (`src/utils/user_funcs.hpp:28-31`); device index `id + 1`, or 0 for an empty or
  `null` name (`src/utils/user_funcs.cu:26-32`).
- **Steps.** (1) Both lookups search the one host list `func1_names`. (2) Slot 0 of the device table is null,
  so slot `id + 1` holds entry `id` of the host table exactly when the device table equals `[nullptr] + host table`.
  (3) That equality is a source fact, not enforced by the code; it holds at the pin.
- **Check.** `check_ch12_twins.py`:
  `(a) func1: 22 names, 22 host, 23 device slots; host==names True, device==[nullptr]+names True  PASS`;
  `(b) func2/func3: host []/[], device ['nullptr']/['nullptr']  PASS` (exact string match).
- **Home and status.** `12-gpu/_device-functions.qmd:40-54`. PRESENT; the Limits at `:125-134` already state that
  nothing enforces step 3. Suggest the Tests layer quote line (a) as the missing length-and-order check (`:116`).

### C12-b Twin drivers run the same per-cell arithmetic

- **Question.** Why should a CPU call and a CUDA call give the same numbers, up to round-off?
- **Start.** Each stub has a CPU registration in the `.cpp` and a CUDA registration in the `.cu`
  (e.g. `src/kinetics/evolve_implicit_dispatch.cpp:80-83`, `src/kinetics/evolve_implicit_dispatch.cu:44-45`).
  Both drivers call the same `DISPATCH_MACRO` template (`src/add_arg.h:4`), e.g. `equilibrate_tp` from
  `src/thermo/thermo_dispatch.cpp:62-65` and `src/thermo/thermo_dispatch.cu:57-62`. Named functions take and return
  `double` whatever the tensor dtype (`src/utils/user_funcs.hpp:18`), on both devices. CUDA flags carry no
  fast-math option (`cmake/compilers.cmake:6-7`).
- **End.** Same per-cell call, same argument order, same sentinel swap of inline curve names
  (`src/thermo/thermo_dispatch.cpp:36-38`, `src/thermo/thermo_dispatch.cu:29-31`).
- **Steps.** (1) Dispatch picks a driver by device type only (`src/kinetics/evolve_implicit_dispatch.cpp:45`).
  (2) Each driver unpacks the iterator pointers in the same `data[i]` order. (3) The per-cell function is one
  source, so the two drivers execute the same operations in the same order per cell; no atomics and no cross-cell
  reductions exist in any kintera kernel (no `atomicAdd` under `src/`). (4) Differences can then come only from
  floating-point contraction (nvcc fuses `a*b+c` into one FMA by default; host builds may not) and from library
  `log`/`exp`, both at round-off. (5) On the CPU the TP, UV and equilibrium drivers pass no workspace, so scratch
  comes from the heap (`src/utils/alloc.h:63`); on CUDA it comes from shared memory. This changes where arrays live,
  not the arithmetic.
- **Check.** `check_ch12_twins.py`: `(c) 8 stubs, each with a CPU and a CUDA registration; missing []  PASS`;
  `(d) 8 driver twins unpack the same pointers in the same data[] order; mismatches []  PASS`;
  `(e) sentinel name swap: cpp 2, cu 2 (expected 2 and 2)  PASS`. Exact text comparison.
  Unverified: needs a CUDA run of the same calls on CPU and CUDA tensors, bitwise or to 1e-15 relative (see C12-e).
- **Home and status.** `12-gpu/_dispatch.qmd:40-51`. PARTIAL: steps 2-5 are not written; the section says
  "no derivation" and "same per-cell arithmetic" without the argument.

### C12-c Per-thread scratch size and block size

- **Question.** How many bytes does one cell need, how many threads fit in a block, and when does a launch fail?
- **Start.** Bump allocator on CUDA, 8-byte rounding, no bounds check (`src/utils/alloc.h:50-64`); block size and
  error (`src/loops.cuh:105-109`, `src/loops.cuh:125-129`); limit `M` (`src/loops.cuh:18-51`).
  Size functions: `src/kinetics/evolve_implicit_impl.h:25-35`, `src/utils/alloc.h:94-107`, `:141-156`,
  `:158-162`, `:164-181`, `src/equilibrium/equilibrium_dispatch.cu:12-26`.
- **End.** `b = 32 ns^2 + 48 ns` bytes for the implicit step in double; `N_thr = min(32, max(1, floor(M/b)))`;
  error iff `b > M`.
- **Steps.** (1) Each size function must list the per-cell `pmalloc` calls in order, because the CUDA bump
  allocator has no bound and an undersized slice silently overwrites the neighbour thread's slice. (2) Nested calls
  (`psolve`, `leastsq_kkt`, `ludcmp`) rewind their pool on exit, so the peak is the outer arrays plus the largest
  nested need; the size functions add the nested need once. (3) The partition UV solver (`uv_solver == 2`) uses
  only its own three arrays (`src/thermo/equilibrate_uv.h:131-133`); `uv_solver == 1` may fall through to the full
  solver and so is sized with the full formula (`src/thermo/thermo_dispatch.cu:117-120`). (4) In `equilibrate_tp`
  and `equilibrate_uv` the KKT solve gets `n2 = nactive <= nreaction` (`src/thermo/equilibrate_tp.h:261-263`), so the
  size function's `nreaction` is an upper bound. (5) Arithmetic of the block size, as in the report.
- **Check.** `check_ch12_twins.py`: seven lines of the form `(f-evolve_implicit) 4 pmalloc calls vs 4 size-function terms, same sizes in order: True  PASS`
  (evolve_implicit, psolve, equilibrate_tp, equilibrate_uv, leastsq_kkt, kkt_feasible_origin, phase_equilibrate_tp) and
  `(f-uv_partition) pmalloc sizes ['nspecies*sizeof(T)', 'nspecies*sizeof(T)', 'nreaction*sizeof(T)']; size function 2*ns + nr  PASS`; `(g) implicit-step scratch from the size function equals 32 ns^2 + 48 ns for ns = 1..59  PASS`;
  `(h) M=49152: threads ns=6 32, ns=7 25; launch error ns=38 False, ns=39 True (report: 32 up to 6, error from 39)  PASS`.
  Exact. The TP/UV/equilibrium sizes are exercised only on CUDA (the CPU drivers use the heap), so (f) is their
  only check here. Unverified: needs a CUDA run of `ThermoX.forward` with a deck of more than 6 species to see the
  block shrink, and of the implicit step with 39 species to see the launch error message.
- **Home and status.** `12-gpu/_kernels.qmd:38-69`. PARTIAL: steps 1-4 and the TP/UV/equilibrium formulas are
  missing (TODO at `12-gpu/_kernels.qmd:137`).

### C12-d Per-cell implicit step and its singular fallback

- **Question.** What does each thread solve, and what does it return when the matrix is singular?
- **Start.** `A = I/dt - S J`, `sr = S r` (`src/kinetics/evolve_implicit_impl.h:66-71`); LU with partial pivoting,
  else the pseudo-inverse solve (`src/kinetics/evolve_implicit_impl.h:77-82`). The CPU driver runs the same template
  with a host bump pool of the same size (`src/kinetics/evolve_implicit_dispatch.cpp:59-69`).
- **End.** `delta = A^{-1} S r` for regular A; `delta = A^+ S r` (minimum-norm least squares) otherwise.
- **Steps.** (1) Linearised backward Euler (derived in C6-h). (2) For singular A, the minimum-norm solution of
  `min |A x - S r|` is `A^+ S r`; `psolve` builds it from the eigenpairs of `A^T A`. (3) The CPU and CUDA drivers
  differ only in the pool backend, so this CPU run is a run of the CUDA arithmetic up to C12-e.
- **Check.** `check_ch12_twins.py`: `(i) evolve_implicit vs numpy solve, 64 cells ns=5 nr=4: max rel diff 1.78e-13  tol 1e-12  PASS`;
  `(j) singular cell, fallback vs numpy pinv: got [ 0.  -0.8  0. ], ref [ 0.  -0.8  0. ], max abs diff 0.0e+00  tol 1e-12  PASS`.
- **Home and status.** `12-gpu/_dispatch.qmd:42-51`. PARTIAL: step 2 (the fallback) is not derived in Chapter 12
  or Chapter 6.

### C12-e Expected size of CPU-CUDA differences

- **Question.** How close should CPU and CUDA results be, and what tolerance should a CPU-vs-CUDA test use?
- **Start.** C12-b: same operations, differences only from FMA contraction and library functions.
- **End.** Per cell, relative difference of order `kappa(A) * eps` for a linear solve (`eps` = 2.2e-16 in double,
  1.2e-7 in single), and of order `eps` for a direct formula (rates, saturation curves).
- **Steps.** (1) One FMA versus a multiply and an add differs by at most one rounding, `eps/2` relative.
  (2) Backward error of LU with pivoting is a small multiple of `eps`; forward error multiplies by `kappa(A)`.
  (3) Iterative solvers with a stopping tolerance (TP/UV saturation adjustment) can stop one iteration apart on the
  two devices; then the difference is bounded by the solver tolerance (`ftol`), not by `eps`.
- **Check.** `check_ch12_twins.py`: `(k) float32 evolve_implicit vs float64 numpy: max rel diff 5.35e-05 (INFO: sets the float32 CPU-vs-CUDA comparison scale, not a CUDA result)  INFO`
  sets the single-precision scale. Unverified: needs a CUDA run comparing `Kinetics.forward_with_rate_constants`,
  `Kinetics.jacobian`, `evolve_implicit` and `ThermoX.forward` on CPU and CUDA tensors, double and single, reporting
  max relative difference against `kappa(A) eps` and, for ThermoX, against `ftol`.
- **Home and status.** `12-gpu/_dispatch.qmd:184-192` reports measured values (8.6e-18 to 8.0e-16) and calls them
  "round-off" without steps 1-3. MISSING. The three test tolerances are TODO (`12-gpu/_dispatch.qmd:171-173`).

### C12-f CUDA sparse QR solve against the CPU sparse LU solve

- **Question.** Do the two atm2d sparse solves return the same solution, and when does each report a singular matrix?
- **Start.** CUDA: `cusolverSp{D,S}csrlsvqr` with `tol` and `reorder` (`src/math/sparse_solver.cu:136-161`), called
  with `tol = 0.0`, `reorder = 0` (`python/atm2d/solver.py:32-39`). CPU: cached SciPy factorisation
  (`python/atm2d/solver.py:41-43`).
- **End.** Both return `x = A^{-1} b` in exact arithmetic; QR and LU differ at `kappa(A) eps`.
- **Steps.** (1) Sparse QR: `A = Q R`, `x = R^{-1} Q^T b`. (2) Sparse LU with pivoting: `x = U^{-1} L^{-1} P b`.
  (3) Backward stability of both; forward error `kappa(A) eps`. (4) With `tol = 0`, cuSOLVER flags singularity only
  for an exactly zero diagonal of R, so a near-singular matrix passes silently on CUDA; the CPU LU stops only on an
  exactly zero pivot too. (5) `reorder = 0` turns off fill-reducing ordering: speed and memory, not the answer.
- **Check.** None possible without a GPU. Unverified: needs a CUDA run of `solve_sparse_system` on an assembled atm2d
  matrix against the CPU path, max relative difference against `kappa(A) eps` (estimate `kappa` with a dense
  condition number on a small grid).
- **Home and status.** `12-gpu/_sparse-solver.qmd:19-21`. MISSING (Derivation is TODO).


