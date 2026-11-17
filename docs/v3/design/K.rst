Lane K: kintera thermodynamics and chemistry contracts
======================================================

Owner: Xi Zhang (backup owner). Round-2 reviewers: the owners of lanes EF and R.
Every ``file:line`` below is at the pins of section 1. A bare ``src/...``
path is kintera; a path starting ``snapy/`` is snapy. "Hypothesis" marks a
claim that only a run would settle; its gate is named next to it.

1. Scope and pins
-----------------

Pins: kintera ``3f5ff938181351a84cb129a9e6314fb89b669b71`` (tag v2.6.10),
snapy ``9e5de2d4ce497d0b2d4da3295fc1fe969fe7e410``.

kintera ``src/`` is 19,228 lines at the pin (the brief's command); thermo
4,801, kinetics 4,825, photochem 3,083, utils 1,970, math 1,691,
equilibrium 673. Host reads (``.item<``) 60 and hard FP64 dtype sites 80,
as the root post says; 40 of the reads are in
``src/thermo/extrapolate_ad.cpp`` (set-up, not on a step path).

This lane is the kintera side of lane X's provider contracts. It reuses
X's precision table (``PrecisionPolicy``, X.rst section 6) and graph rules
(``StageExecutor``, segments, ``GraphKey``, the step-reset list, X.rst
section 7) and defines no second set. Rule of the lane: kintera files a V3
change touches do not grow in net (section 9).

Order of the study plan: items 1 and 3 first (sections 3.1 and 3.2), since
lane EF waits on both.

2. Concepts and current sites
-----------------------------

.. csv-table::
   :header: "Concept", "Site at the pin"

   "kintera's G2 duties", "snapy/V3_ROADMAP.md:65, snapy/V3_ROADMAP.md:70-73, snapy/V3_ROADMAP.md:179-209"
   "U to T inversion (host read per iteration)", "src/thermo/thermo_y.cpp:510-545; read at src/thermo/thermo_y.cpp:525"
   "P to T inversion (same pattern)", "src/thermo/thermo_y.cpp:454-500; read at src/thermo/thermo_y.cpp:480"
   "output rebound, not written in place", "src/thermo/thermo_y.cpp:517, src/thermo/thermo_y.cpp:462, src/thermo/thermo.hpp:240"
   "tolerances", "max_iter 100, ftol 1e-6: src/thermo/thermo.hpp:80-81"
   "saturation adjustment", "src/thermo/thermo_y.cpp:277-398; kernel src/thermo/thermo_dispatch.cu:67-142"
   "solver tolerance passed as a float", "src/thermo/thermo_y.cpp:370, src/thermo/equilibrate_uv.h:299"
   "failure count", "member src/thermo/thermo.hpp:145-147; accumulate src/thermo/thermo_y.cpp:379-390; take src/thermo/thermo_y.cpp:400-405; cleared by reset src/thermo/thermo_y.cpp:172-173"
   "warm-start active set", "src/thermo/thermo.hpp:142-143; reuse test src/thermo/thermo_y.cpp:293-312; ThermoX ignores it, src/thermo/thermo.hpp:367"
   "function-pointer tables, CUDA", "src/utils/user_funcs.cu:14-133; callers src/utils/utils_dispatch.cu:42-65, src/thermo/thermo_dispatch.cu:84-102"
   "function-pointer tables, CPU", "src/utils/user_funcs.hpp:23; src/thermo/thermo_dispatch.cpp:89-109"
   "saturation-pressure spec", "built per forward: src/thermo/log_svp.cpp:13-40 from src/thermo/thermo_y.cpp:365-366; statics src/thermo/log_svp.cpp:45-47"
   "heat-capacity constants per call", "src/thermo/eval_uhs.cpp:155-156, src/thermo/eval_uhs.cpp:187-188, src/thermo/eval_uhs.cpp:264-265"
   "constant-cv pressure helper", "src/thermo/eval_uhs.hpp:41-56; snapy/src/eos/ideal_moist.cpp:154"
   "T-dependent cv refused in FP32", "snapy/src/eos/ideal_moist.cpp:87"
   "snapy: saturation adjustment", "snapy/src/mesh/meshblock.cpp:949-982 (warm start snapy/src/mesh/meshblock.cpp:969-970)"
   "snapy: failure drain at step start", "snapy/src/mesh/meshblock.cpp:736 via snapy/src/mesh/meshblock.cpp:1447-1454"
   "snapy: failure drain into the retry flags", "snapy/src/mesh/meshblock.cpp:1538-1547; the one read snapy/src/mesh/meshblock.cpp:1566"
   "snapy: chemistry step (example driver only)", "snapy/examples/run_hydro.cpp:171-198; Kinetics built but never called in snapy/src/scalar/scalar.cpp:55"
   "snapy: version floor", "snapy/CMakeLists.txt:97-105, snapy/pyproject.toml:7"

What blocks capture today, by reading (each "hypothesis" until the G2
capture test of section 5 runs):

- A host read per Newton iteration in both inversions, also for constant
  heat capacity, where the first guess
  (``src/thermo/thermo_y.cpp:517``) is already exact and the loop still
  runs once and reads once (``src/thermo/thermo_y.cpp:520-528``). The same
  holds for ``PV->T`` when every ``czh`` is empty
  (``src/thermo/thermo_y.cpp:462-483``).
- ``cudaMemcpyFromSymbol`` (a synchronous device read), a host-to-device
  index copy and a ``thrust::device_vector`` allocation on every call that
  resolves function names (``src/utils/user_funcs.cu:19``,
  ``src/utils/user_funcs.cu:38``, ``src/utils/user_funcs.cu:44``; the same
  in the two other copies at 59/78/84 and 99/118/124). A saturation
  adjustment resolves four tables per call
  (``src/thermo/thermo_dispatch.cu:84``, ``src/thermo/thermo_dispatch.cu:91``,
  ``src/thermo/thermo_dispatch.cu:95``, ``src/thermo/thermo_dispatch.cu:102``),
  and every ``eval_*`` call resolves one more
  (``src/thermo/eval_uhs.cpp:153``).
- Host vectors uploaded on every call: ``torch::tensor(op->cref_R(), ...)``
  and friends (``src/thermo/eval_uhs.cpp:155-156``,
  ``src/thermo/eval_uhs.cpp:187-188``, ``src/thermo/eval_uhs.cpp:264-265``,
  ``src/thermo/eval_uhs.cpp:327-329``, ``src/thermo/eval_uhs.cpp:388-390``,
  ``src/thermo/eval_uhs.cpp:467-468``), the NASA-9 coefficients
  (``src/thermo/eval_uhs.cpp:55-57`` through ``src/species.hpp:60``), the
  saturation spec (``src/thermo/log_svp.cpp:36-38``) and the static spec
  moved per call (``src/thermo/log_svp.cpp:100-101``,
  ``src/thermo/log_svp.cpp:111-112``, ``src/thermo/log_svp.cpp:127-128``).
- The failure count is rebound to a new tensor every call
  (``src/thermo/thermo_y.cpp:383``) and dropped by assignment in snapy
  (``snapy/src/mesh/meshblock.cpp:1546``). A captured graph would replay
  the sum against the tensor seen at capture, so counts would not
  accumulate across replays.
- Per-call temporaries from the caching allocator (``yfrac.clone()``
  ``src/thermo/thermo_y.cpp:284``, ``gain`` 291, ``diag`` 317) are legal
  inside a captured segment (graph-private pool); they are not a blocker.
  The kernel's workspace is shared memory, no global allocation
  (``src/thermo/thermo_dispatch.cu:116-119``, ``src/loops.cuh:86-166``); the
  per-device shared-memory query is cached in a static on first use
  (``src/loops.cuh:18-50``), a lazy initialisation that must happen before
  capture.

Other host reads on step paths, for G2's optional chemistry: kinetics
(``src/kinetics/kinetics.cpp:442``), evaporation extent
(``src/kinetics/evaporation_extent.cpp:19``, ``:83``, ``:98``, ``:113``),
ThermoX equilibrium (``src/thermo/thermo_x.cpp:301``,
``src/thermo/thermo_x.cpp:343``). The reads at
``src/kinetics/kinetics.cpp:289-298`` are set-up.

3. Target design
----------------

3.1 Capture-safe temperature solves (study item 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ThermoY`` chooses a ``SolvePlan`` once, in ``reset()``, from options only
(never from data):

- ``exact``: every ``intEng_R_extra`` empty, ``use_nasa9_cp`` and
  ``use_h2_cp`` off. ``VU->T`` is the first guess plus exactly one Newton
  correction, with no read. ``PV->T`` takes the plan when every ``czh`` is
  empty. Bitwise against the pin whenever the pin's loop stops after one
  pass, i.e. whenever one correction changes T by less than ``ftol``
  relative (hypothesis for any ``ftol`` above round-off; gate K-G1).
- ``newton`` with ``SolveMode``:

  - ``eager_exit`` (default, today's loop): a host read per iteration,
    early exit. Used only outside captured segments.
  - ``fixed``: ``max_iter`` passes, no read. A 0-d device flag ``run``
    starts true; each pass keeps ``T_prev = T``, sets
    ``T = where(run, T + dT, T)`` (today's update first,
    ``src/thermo/thermo_y.cpp:524``), then
    ``run &= !(max|1 - T_prev/T| < ftol)``, the negation of today's test
    (``src/thermo/thermo_y.cpp:525``) so a NaN keeps ``run`` true as it
    keeps today's loop going; ``>= ftol`` would stop on NaN and differ.
    The test is done in double, as today. After the converged pass the
    state is never changed again, so ``fixed`` equals ``eager_exit``
    bitwise (gate K-G2, which includes a NaN cell). Cost: ``max_iter`` passes always (100 by
    default); a T-dependent heat capacity inside a graph pays it.
    Cheaper forms (a per-cell kernel, a graph conditional node) stop cells
    at different passes and change results within ``ftol``:
    ``FOR CHENG`` K-F2.

- On non-convergence the pin warns (``src/thermo/thermo_y.cpp:531-532``).
  V3 adds one to the ``temp_solve`` (or ``pres_solve``) row of the failure
  counter on the device, and keeps the warning on the CPU path. It is not
  a retry cause (no behaviour change).
- Output written in place: ``compute_into(ab, args, out)`` writes with
  ``copy_`` into caller storage; ``compute()`` keeps its allocating form
  and calls it. ``set_`` (``src/thermo/thermo_y.cpp:462``, ``:517``) goes.
- Tolerances unchanged: ``ftol`` and ``max_iter`` from
  ``src/thermo/thermo.hpp:80-81``.

3.2 Failure counter (study item 3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One fixed device tensor per ``ThermoY``, int64, shape (3,), rows
``saturation``, ``temp_solve``, ``pres_solve``. Allocated by ``prepare()``
(3.3) and never rebound; ``reset()`` and ``clone()`` drop it, as
``src/thermo/thermo_y.cpp:172-173`` does today. ``nfail_`` becomes private.

.. csv-table::
   :header: "Call", "Effect", "Capturable", "Replaces"

   "``failures()``", "the (3,) device tensor, a view; never read here", "yes", "``nfail_`` (snapy/src/mesh/meshblock.cpp:1544)"
   "``reset_failures()``", "``zero_()`` in place", "yes", "snapy/src/mesh/meshblock.cpp:736 (a host read today)"
   "``consume_failures(out)``", "``out.copy_(failures() > 0)``, then ``zero_()``; device only", "yes", "snapy/src/mesh/meshblock.cpp:1544-1546"
   "``take_saturation_adjustment_failures()``", "host read of row 0, then zero; kept", "no: step end or output only", "itself (src/thermo/thermo_y.cpp:400-405)"

``forward`` adds ``(diag < 0).sum()`` into row 0 with ``add_``
(today ``src/thermo/thermo_y.cpp:379-383``). snapy's lifecycle: the step
reset list (X) calls ``reset_failures()``; the retry stack calls
``consume_failures(flags.narrow(0, 4, 1))`` so the saturation slot keeps
its place in the stack (``snapy/src/mesh/meshblock.cpp:1559-1560``); the
one host read stays at ``snapy/src/mesh/meshblock.cpp:1566``. Rows 1 and 2
are read only by diagnostics after the accept.

3.3 Persistent device tables (study item 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ThermoTables``, one per (device, compute dtype), built by
``ThermoY::prepare(device, dtype)`` outside capture: ``cref_R``,
``uref_R``, ``sref_R``, ``cv0``, ``u0`` as tensors in the compute dtype;
NASA-9 coefficients and ``Tmid``; the H2 mask; ``svp_kind`` (int32) and
``svp_params`` (FP64); and ``FuncTable`` entries for ``logsvp``,
``logsvp_ddT``, ``intEng_extra``, ``intEng_extra_ddT``, ``cp_R_extra``,
``czh``, ``czh_ddC`` and the entropy extras. A ``FuncTable`` is an int64
tensor of device function pointers, filled once from the symbol table; it
replaces the three ``get_device_func*`` copies and their
``thrust::device_vector`` results, and on the CPU it holds host pointers
(``get_host_func``, ``src/utils/user_funcs.hpp:23``).

- Key: device index, dtype, and an options generation bumped by
  ``reset()``. ``prepare`` also runs the lazy shared-memory query of
  ``src/loops.cuh:18-50``.
- Lifetime: ``std::shared_ptr<const ThermoTables>``. The module holds one;
  X's ``StageExecutor`` keeps a copy with every graph that replays a kintera
  op, so a table outlives every graph that references it. The table
  generation joins X's ``GraphKey``; a new generation invalidates the
  graph.
- Inside a captured segment a missing table throws (no lazy set-up during
  capture).
- ``eval_*`` take the tables: the per-call uploads of section 2 go.

3.4 Warm start (study item 5)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``reaction_set`` and ``nactive`` (``src/thermo/thermo.hpp:142-143``) are
written in place by the kernel and survive across steps. V3 adds
``ActiveSet snapshot_active_set(out)`` and ``restore_active_set(in)``,
both ``copy_`` between fixed buffers of the same shape. Snapy calls
snapshot at step start (with ``u0``/``s0``) and restore in X's reset list
on a retry and after a graph warm-up, so a retry repeats the first attempt
from the same active set. Today a retry starts from the failed attempt's
active set (``snapy/src/mesh/meshblock.cpp:969-970``; the rollback does not
touch kintera). Whether this changes results beyond round-off is a
hypothesis (gate K-G5). Shapes are fixed by X's ``StateStore``, so the
cold-start branch (``src/thermo/thermo_y.cpp:303-312``) runs only in
``prepare``.

3.5 Data flow of the last stage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  host, set-up: thermo.prepare(device, dtype) -> ThermoTables (shared_ptr)
  step start:   thermo.reset_failures(); thermo.snapshot_active_set(as0)
  last stage [segment, FP64 totals]:
     limiter (EF) -> totals -> thermo.forward(rho, ie, yfrac, warm, diag)
        VU->T (exact | fixed) -> equilibrate_uv kernel (tables)
        failures[0] += count(diag < 0)
        -> species rows written back; cell_amount("thermo.saturation", ...)
  chemistry [segment, FP64]: kinetics step -> cell_amount("chem.*", ...)
  step end:     thermo.consume_failures(flags[4]); X's one host read
  retry:        restore u0/s0 (X); thermo.restore_active_set(as0)

3.6 Chemistry step (study item 7)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At the pin the step after the RK stages exists only in an example driver
(``snapy/examples/run_hydro.cpp:171-198``): kinetics rates, a Jacobian, one
implicit step (``kintera::evolve_implicit``), and the species rows of
``hydro_u`` increase by ``del_rho`` (``snapy/examples/run_hydro.cpp:197``);
the increment does not touch the energy row, so heat of reaction appears
as a temperature change through the composition. The EOS call before it
(``snapy/examples/run_hydro.cpp:179``) may apply the conserved limiter,
which can write the density and energy rows; that is EF's limiter, not
the chemistry increment, and is posted by EF. V3
makes it a ``ChemistrySource`` op that snapy schedules after the last
stage in its own eager segment (host reads at
``src/kinetics/kinetics.cpp:442``), FP64. maxichem (an existing proposal,
not this lane's) fits the same op: species in, species increments out.
Its budget declarations are section 4.

3.7 Thermodynamic math snapy repeats (study item 6, with EF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table::
   :header: "snapy site", "Repeats", "Where it lives in V3"

   "snapy/src/eos/ideal_moist.cpp:33-55", "ratios and offsets from ThermoY buffers (src/thermo/thermo_y.cpp:57-58, src/thermo/thermo_y.cpp:100-103)", "``ThermoTables`` (``cv0``, ``u0``)"
   "snapy/src/eos/ideal_moist.cpp:233-259", "``PV->T`` then ``VT->U`` for constant cv", "kintera ``compute_into`` (exact plan)"
   "snapy/src/eos/ideal_moist.cpp:261-268", "``PV->T`` first guess (src/thermo/thermo_y.cpp:459-462)", "kintera, exact plan"
   "snapy/src/eos/ideal_moist.cpp:270-292", "per-species energy U (src/thermo/eval_uhs.cpp:245-281)", "kintera ``eval_intEng_R``"
   "snapy/src/eos/ideal_moist.cpp:294-315", "per-species enthalpy (src/thermo/eval_uhs.cpp:448-477)", "kintera ``eval_enthalpy_R``"
   "snapy/src/eos/ideal_moist.cpp:317-340", "``VT->U`` (src/thermo/thermo.hpp:235-241)", "kintera ``compute_into``"

All of these are EF's lines; EF decides whether each goes, and the count
is EF's (section 9, joint rows). The kintera entry points already exist,
so kintera does not grow. snapy's forms order the arithmetic differently
from kintera's, so the swap rounds differently (not bitwise; EF's
gate). The FP32 anomaly path (``snapy/src/eos/ideal_moist.cpp:78-158``)
stays in snapy: kintera holds totals, not perturbations.

4. Flux-register contract
-------------------------

Names are lane R's provisional header (``docs/v3/skeleton/R/flux_register.hpp``
at happysky19/snapy ``543ff84f``): ``FluxRegister::cell_amount(name,
vol_du)`` and ``RegisterMonitor``. Lane K posts no face flux.

- Posts. Both kintera ops are cell sources, posted with ``cell_amount``,
  FP64, in the segment that applies them:

  - ``thermo.saturation``: the change of each species row from the
    saturation adjustment (``snapy/src/mesh/meshblock.cpp:972``). Total
    mass and total energy are unchanged by construction (the row sum is
    conserved, energy is untouched): the monitor checks that, it is not
    posted as a source.
  - ``chem.species``: ``del_rho`` per species row
    (``snapy/examples/run_hydro.cpp:196-197``).
  - ``chem.elements``: the element totals of ``del_rho`` (stoichiometry
    times ``del_rho``), a monitor amount that must be zero to the solver's
    tolerance; non-zero is a named non-closure.
  - ``chem.energy``: zero today (the increment leaves the energy row unchanged); declared so a later
    chemistry step with heat release posts it.

- Reads. None from the register; kintera reads only cell state.
- Corrects. Nothing; kintera is not a fixer.
- Ordering. After the last stage's limiter (``snapy/src/mesh/meshblock.cpp:951``)
  and after ``end_stage`` of the last stage; before X's step-end read. The
  chemistry step follows the saturation adjustment, as
  ``snapy/examples/run_hydro.cpp:177-179`` requires.
- Failure counts are not register counters: they go into X's retry stack
  (3.2), as R's ``retry_flags()`` does.

Of the ten requirements, lane K answers 6 (no host read: posts are device
ops, the counter is consumed on the device), 7 (each source names its
amount per conserved row), 8 (amounts FP64, fixed storage from
``prepare``), 9 (no field copy: species rows only) and 10 (tables and
counters are rebuilt, never in a restart). 1 to 5 are not this lane's.

5. Invariants and gates
-----------------------

Specified, not written and not run.

.. csv-table::
   :header: "Gate", "Identity", "Case", "Comparison"

   "K-G1", "exact plan equals the pin's ``VU->T`` and ``PV->T``", "kintera test, constant cv, random states, FP64 and FP32 inputs, CPU and CUDA", "bitwise"
   "K-G2", "``fixed`` equals ``eager_exit``", "NASA-9 and H2 decks, states that converge in 1, 5 and never, and one NaN cell", "bitwise"
   "K-G3", "no host sync in a captured kintera op", "replay ``forward`` and ``compute_into`` under ``torch.cuda.set_sync_debug_mode('error')``", "exact"
   "K-G4", "failure counts survive replay", "inject a failing cell on replay N >= 2; ``consume_failures`` sets the flag; counts accumulate over replays", "exact"
   "K-G5", "retry repeats the first attempt", "change the active set during a step, force a retry; compare with a clean run of the same dt", "bitwise (hypothesis)"
   "K-G6", "tables equal the pin's per-call values", "every ``eval_*`` with tables against the pin's form", "bitwise"
   "K-G7", "saturation conserves mass and energy", "``thermo.saturation`` row sum and energy, condensing column", "round-off (FP64 sum)"
   "K-G8", "chemistry conserves elements", "``chem.elements`` on a closed box", "solver tolerance"
   "K-G9", "paired revisions", "snapy CI builds against the kintera candidate tag (section 8)", "exact"

6. FP32 contract
----------------

X's rows hold: "kintera totals, saturation", FP64 storage and compute
(X.rst section 6). Per kintera entry point:

.. csv-table::
   :header: "Entry point", "Accepts FP32", "Inside", "Why"

   "``eval_cv_R``, ``eval_cp_R``, ``eval_czh``, ``eval_intEng_R``", "yes", "input dtype", "elementwise; the dispatch covers float (src/utils/utils_dispatch.cu:49)"
   "``compute`` / ``compute_into`` conversions", "yes after K3", "FP64 buffers today", "``inv_mu``, ``cv0``, ``u0`` are FP64 (src/thermo/thermo_y.cpp:57-58, src/thermo/thermo_y.cpp:100-103): mixed arithmetic returns FP64 by type promotion; V3 casts the tables to the compute dtype"
   "``forward`` (saturation adjustment)", "no (policy)", "FP64", "the kernel reads the module buffers through ``data_ptr<scalar_t>`` (src/thermo/thermo_dispatch.cu:111-113), so input and buffer dtypes must match; the default buffers are FP64 (src/thermo/thermo_y.cpp:58, src/thermo/thermo_y.cpp:100-109), so an FP32 call against them throws. FP64 is kept by policy: phase equilibrium near saturation cancels"
   "``eval_const_cv_pressure_delta``", "yes", "caller's", "perturbation form (src/thermo/eval_uhs.hpp:41-56)"
   "Kinetics, chemistry step", "no", "FP64", "stiff implicit step"

``eval_const_cv_pressure_delta`` generalises to
``eval_pressure_delta(thermal0, gas0, cv0, dthermal, dgas, dcv, tables)``:
for constant cv it is today's formula; for a T-dependent cv the change in T
comes from the ``fixed`` Newton solve on the perturbation about the
reference state. Until its eager gate passes, NASA-9 and H2 heat
capacities stay refused in FP32, as today
(``snapy/src/eos/ideal_moist.cpp:87``). Explicitly unsupported in FP32:
NASA-9 and H2 heat capacities, saturation adjustment, kinetics.
Explicitly unsupported in graphs: ThermoX equilibrium and kinetics (host
reads above) and ``extrapolate_ad`` (set-up only). Neither falls back
silently to constant cv (``snapy/V3_ROADMAP.md:201-205``).

7. CUDA-graph contract
----------------------

.. csv-table::
   :header: "Site", "Kind", "Fate", "Gate"

   "src/thermo/thermo_y.cpp:525, src/thermo/thermo_y.cpp:480", "host read per iteration", "exact plan or ``fixed`` mode", "G2"
   "src/thermo/thermo_y.cpp:385", "host read, CPU only", "stays (no graphs on CPU)", "-"
   "src/thermo/thermo_y.cpp:402", "host read", "``take_*`` only at step end; ``consume_failures`` in segments", "G2"
   "src/thermo/thermo_y.cpp:383", "tensor rebound per call", "``add_`` into the fixed counter", "G2"
   "src/utils/user_funcs.cu:19, src/utils/user_funcs.cu:59, src/utils/user_funcs.cu:99", "device-symbol read", "``prepare``", "G2"
   "src/utils/user_funcs.cu:38-44, src/utils/user_funcs.cu:78-84, src/utils/user_funcs.cu:118-124", "upload + allocation", "``FuncTable``", "G2"
   "src/thermo/eval_uhs.cpp:155-156, src/thermo/eval_uhs.cpp:264-265", "host vector upload", "``ThermoTables``", "G2"
   "src/thermo/log_svp.cpp:36-38, src/thermo/log_svp.cpp:100-101", "upload, move", "``ThermoTables``", "G2"
   "src/loops.cuh:18-50", "lazy static", "run by ``prepare``", "G2"
   "src/thermo/thermo_y.cpp:303-312", "cold-start allocation", "``prepare`` only (fixed shapes)", "G2"
   "src/thermo/equilibrate_uv.h:634-636", "device printf on non-convergence", "stays (legal in a kernel); counted by row 0", "G2"
   "src/kinetics/kinetics.cpp:442", "host read", "chemistry stays eager", "G6"

Segments: lane K registers ops; X schedules them. The saturation
adjustment is one compute op in the last stage's segment once G2 passes,
an eager segment before (X.rst section 7). The chemistry step is an eager
segment after the last stage. Data-dependent branches inside kintera ops:
none on the host after K3; the active-set and Newton branches are in
kernels (``snapy/V3_ROADMAP.md:185-189``).

Mapping to G0-G7: G2 is this lane (K1 to K4); G3 uses ``compute_into``
in the vertical implicit correction; G6 inherits it on the cubed sphere;
G7 accepts it.

8. Cross-repository interface changes and merge order
-----------------------------------------------------

New in kintera (skeleton ``thermo_v3.hpp``): ``SolvePlan``,
``SolveMode``, ``ThermoTables``, ``FuncTable``, ``ThermoY::prepare``,
``compute_into``, ``failures``, ``reset_failures``,
``consume_failures``, ``snapshot_active_set``, ``restore_active_set``,
``eval_pressure_delta``. Kept for one minor release: public ``nfail_``
(snapy reads it, ``snapy/src/mesh/meshblock.cpp:1544``) and
``take_saturation_adjustment_failures``; ``nfail_`` goes private in the
release after snapy stops using it.

Version contract (study item 8): snapy states its floor in one place,
``find_package(Kintera X.Y.Z REQUIRED)`` with a comment per feature, as
today (``snapy/CMakeLists.txt:97-105``), mirrored in
``snapy/pyproject.toml:7``. A paired revision is tested before release:
kintera tags a release candidate; snapy's PR raises the floor and its CI
builds that tag (gate K-G9); kintera releases; snapy merges.

Merge order (provider first):

1. pyharp ``out=`` (X).
2. kintera K1 (tables), K2 (counter API, ``nfail_`` kept), K3 (solve
   plans, ``compute_into``), K4 (active-set snapshot). One release.
3. snapy, X1 to X7 (X), with EF's and K's snapy PRs: S-K1 (the counter in
   the reset list and retry stack), S-K2 (warm-start snapshot), S-K3
   (saturation adjustment inside the segment).
4. kintera K5 (``nfail_`` private; ``eval_pressure_delta``).

Decision: kintera merges first because every snapy change needs the API,
and K1 to K4 are bitwise against the pin for every caller (section 10).

9. Line budget
--------------

kintera: touched files do not grow in net. The thermo total is 4,801 at the
pin and 4,770 after (target, not a measurement). Counted with
``wc -l`` at the pin; "after" are targets.

.. csv-table:: kintera touched
   :header: "File", "Now", "After", "Change"

   "src/utils/user_funcs.cu", 134, 56, "k1"
   "src/utils/user_funcs.hpp", 57, 57, "k2"
   "src/utils/utils_dispatch.cu", 105, 99, "k3"
   "src/utils/utils_dispatch.cpp", 113, 107, "k4"
   "src/thermo/thermo_dispatch.cu", 185, 173, "k5"
   "src/thermo/thermo_dispatch.cpp", 192, 182, "k6"
   "src/thermo/thermo_y.cpp", 557, 548, "k7"
   "src/thermo/thermo.hpp", 454, 454, "k8"
   "src/thermo/eval_uhs.cpp", 477, 477, "k9"
   "src/thermo/log_svp.cpp", 160, 160, "k10"
   "total", 2434, 2313, "cut 121 (5.0%)"

Items (net lines per file):

k1. -78 (src/utils/user_funcs.cu): the three ``get_device_func*`` copies
(14-133) become one template filling a ``FuncTable`` once per
``prepare``.

k2. -0 (src/utils/user_funcs.hpp): ``FuncTable`` and ``ThermoTables``
declared (+20); the per-call name lookup declarations go (-20).

k3. -6 (src/utils/utils_dispatch.cu): ``call_func*`` take a ``FuncTable``
instead of names (42-65 and twins).

k4. -6 (src/utils/utils_dispatch.cpp): the same on the CPU (28, 50, 74).

k5. -12 (src/thermo/thermo_dispatch.cu): four name resolutions (81-102)
become table fields.

k6. -10 (src/thermo/thermo_dispatch.cpp): the same on the CPU (89-109).

k7. -9 (src/thermo/thermo_y.cpp): the dead dump blocks (489-498, 534-543)
and the warning blocks go (-26); ``fixed``/exact plan (+8); counter
``add_`` replaces 379-383 (-2); ``prepare`` and snapshot (+11).

k8. -0 (src/thermo/thermo.hpp): the failure and table declarations (+12)
replace ``nfail_`` and ``take_`` comments (145-147, 164-166) and the
duplicated per-member comments of 130-140 (-12).

k9. -0 (src/thermo/eval_uhs.cpp): uploads become table reads, line for
line.

k10. -0 (src/thermo/log_svp.cpp): the three moves (100-101, 111-112,
127-128) read the table (-6); ``make_svp_spec`` fills it (+6).

snapy rows, joint with other lanes, not counted here (the owner counts
them):

.. csv-table:: joint, not counted
   :header: "File", "Now", "After", "Owner"

   "snapy/src/eos/ideal_moist.cpp", 372, 268, "EF (3.7: up to 104 lines)"
   "snapy/src/mesh/meshblock.cpp", 1919, 1903, "X (1447-1454 and 1541-1547 become two calls)"

10. Migration
-------------

.. csv-table::
   :header: "PR", "Repo", "Content", "Against main"

   "K1", "kintera", "``ThermoTables``, ``FuncTable``, ``prepare``; ``eval_*`` read tables", "bitwise (same values, same kernels)"
   "K2", "kintera", "fixed failure counter; ``failures``, ``reset_failures``, ``consume_failures``", "bitwise (counts only)"
   "K3", "kintera", "``SolvePlan``, ``SolveMode``, ``compute_into``", "bitwise (K-G1, K-G2; hypothesis for ``ftol`` near round-off)"
   "K4", "kintera", "active-set snapshot and restore", "bitwise when unused"
   "S-K1", "snapy", "counter in X's reset list and retry stack", "bitwise"
   "S-K2", "snapy", "snapshot at step start, restore on retry", "changes retried steps (hypothesis, K-G5): ``FOR CHENG`` K-F1"
   "S-K3", "snapy", "saturation adjustment in the captured segment", "bitwise (graph equals eager)"
   "K5", "kintera", "``nfail_`` private; ``eval_pressure_delta``", "bitwise for constant cv"

Removed: per-call function-name resolution on both devices; the dead
dump blocks; snapy's direct use of ``nfail_``. No option is dropped and no
default changes.

``FOR CHENG``:

- K-F1: restoring the active set on a retry changes the solver's starting
  point for retried steps (results within ``ftol`` of today's, by
  hypothesis).
- K-F2: a cheaper graph form of the T-dependent inversion (per-cell stop)
  changes results within ``ftol``; rev 1 keeps the bitwise ``fixed`` form.

11. Open questions to other lanes
---------------------------------

EF (Zoey):

- Items 1 and 3 are 3.1 and 3.2: ``compute_into`` with the exact plan for
  constant cv, ``fixed`` for the rest; ``reset_failures`` and
  ``consume_failures``. Does EF need ``pres_solve`` and ``temp_solve`` as
  retry causes, or as diagnostics only (rev 1)?
- Which rows of 3.7 does EF delete, and does EF accept the rounding change?

X (Xi, this owner's other lane):

- Add the kintera table generation to ``GraphKey`` and hold the table
  ``shared_ptr`` with each graph (3.3).
- Add ``reset_failures`` and ``restore_active_set`` to the step-reset
  list; ``consume_failures`` writes slot 4 of the retry stack.

R (Linfeng):

- Are ``thermo.saturation``, ``chem.species``, ``chem.elements`` and
  ``chem.energy`` acceptable ``cell_amount`` names, and may an amount have
  rows that are elements rather than conserved variables?

A (Jiachen):

- K-1: awaited in the K thread; rev 2 answers it here.

O (Jiachen):

- The failure rows 1 and 2 as diagnostics read after the accept.

12. Skeleton index
------------------

``docs/v3/skeleton/K/``, declarations only, in no build:

- ``thermo_v3.hpp``: ``SolvePlan``, ``SolveMode``, the ``ThermoY``
  additions (``prepare``, ``compute_into``, failure counter, active set).
- ``tables.hpp``: ``FuncTable``, ``ThermoTables``.
- ``chemistry_source.hpp``: ``ChemistrySource`` and its budget names.
- ``pressure_delta.hpp``: ``eval_pressure_delta``.
