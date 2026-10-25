# Chapter 12 next-repin task: device-table mutation

The original claim below is preserved as historical evidence, but withdrawn from the chapter's
validated claims. The original scratch probe was not recovered. Delivery
[c197d576a42f430444f9ffffe73ef282ebdace3d](https://github.com/happysky19/kintera/commit/c197d576a42f430444f9ffffe73ef282ebdace3d)
supplies a stand-in, not that producer. Only its unmodified-deck CPU measurements are validated here.
The historical patched-CUDA 4.559 result is NOT reproduced by the stand-in.

Next repin: recover or replace the complete mutation experiment in a disposable source build;
validate all requested formula names and paired CPU/CUDA outputs, restoration and source attribution.
The supplied mutation helper was not integrated or executed: it references absent func_table_probe.py,
redefines installed_lib_dir with an in-process native import after a subprocess-safe definition,
and would swap installed libraries. Its delivery remains available at the immutable link above.

This retirement removes exactly ch12-devfn-scratch from the active historical registry (104 to 103).
All other witnesses and strict source-label checks remain unchanged. Original record at
[dfe26fc9829252f162cb05d88908cbd5b51dc233](https://github.com/UCzhangxi/kintera/blob/dfe26fc9829252f162cb05d88908cbd5b51dc233/doc/tech-report/book/chapters/12-gpu/_device-functions.qmd#L133):

```qmd
::: {.callout-warning title="Limits"}
- **A function missing from the device table gives wrong values on CUDA, not an error.** Two cases were measured with
  a scratch build in which a test function returning $\ln K = 7$ (and its derivative) was added to `func1_table_cpu`
  and `func1_names` only. Appended at the end, it evaluated to 7 on the CPU and to 0 on CUDA: its device index
  $\mathrm{id}+1$ points past the end of the device table, and the slot read there was null, so the kernel added
  nothing. Inserted at the front, it shifted every later name by two device slots. On CUDA, `h2o_ideal` then returned
  the values of `h2o_bryan` ($\ln K$ = 4.559 against 4.333 at 250 K), the test function returned those of
  `h2o_ideal`, and the last registered name returned 0. In every case no error was raised.[^ch12-devfn-scratch]
  Reading past the end of a device array is undefined; that it reads a null pointer on other builds is a hypothesis.
:::

- The device table is a fixed array compiled into the CUDA library; adding a function needs a rebuild of both
  libraries.

[^ch12-devfn-scratch]: [sha: kintera@0d9f67f97d841147e23283d2dcdab302238d2c45 with `src/func_table.cpp` patched in a
scratch copy only, not committed; deck: names `h2o_ideal`, `h2o_ideal_ddT`, `nh3_ideal`, `na_h2s_visscher_ddT` and
the test function; run: `cmake --build . --target kintera_release` in the `build` directory of a `-DCUDA=ON` Release
build, so that only the CPU library and its tables change, then `python -P probe.py <names>`, a scratch script that
evaluates $\ln K$ at 250 K and 300 K through `relative_humidity` on CPU and CUDA tensors; source restored and the
library rebuilt bit-identical afterwards; GeForce GTX 1080 Ti, CUDA 12.6.85, GCC 11.5.0, torch 2.10.0+cu126,
Python 3.11.13.; historical: 0d9f67f97d841147e23283d2dcdab302238d2c45]

```

## Integration validation

Two regression tests failed before correction and pass afterward: partial missing-name requests must
return 2, and the unsupported mutation claim must be deferred with its original evidence preserved.
The new exact recipe `python -P probe.py h2o_ideal nh3_ideal` returned 0 using the existing source-built
kintera 2.6.7 at e357792d50639d68e9090b542edf038d2b029aa2, Python 3.11 / Torch 2.10 environment,
with CUDA hidden. At 250/300 K, respectively, h2o_ideal prints 4.333445/8.171729 and nh3_ideal
11.710101/13.301208. The former four-name recipe returns 2 because both derivative names are absent
from the deck's nucleation formulas. No patched CUDA measurement was made. Native source and
committed scientific outputs were not modified.
