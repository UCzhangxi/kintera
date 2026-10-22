# Paddle compatibility boundary

The main environment deliberately reports this unresolved dependency and exits
nonzero. Building Paddle's wheel does not establish a working Paddle runtime.
No required experiment is removed to obtain a passing audit.

## Public refs inspected

On 2026-10-22, `git ls-remote https://github.com/chengcli/paddle.git`, a public
clone, and `git fetch origin '+refs/pull/*/head:refs/remotes/pull/*'` exposed the
following branch, tag and pull-request tips. Each tip's `pyproject.toml` declares
`torch>=2.7.0,<=2.7.1`, `kintera>=1.0.1`, and `snapy>=0.7.0`.

| Ref | Immutable commit |
|---|---|
| `refs/remotes/origin/cli/add_lint` | [bd6ba6ca8461010a03fb98502514e172e62b9be1](https://github.com/chengcli/paddle/blob/bd6ba6ca8461010a03fb98502514e172e62b9be1/pyproject.toml#L33) |
| `refs/remotes/origin/cli/fix_cd` | [5587fc430464e6ebfdfb59221ecb85c9fcb9483b](https://github.com/chengcli/paddle/blob/5587fc430464e6ebfdfb59221ecb85c9fcb9483b/pyproject.toml#L33) |
| `refs/remotes/origin/main` | [3f5a07cca25b2c75e39c1d5a4afb7a7ff63d40bf](https://github.com/chengcli/paddle/blob/3f5a07cca25b2c75e39c1d5a4afb7a7ff63d40bf/pyproject.toml#L33) |
| `refs/remotes/pull/1` | [7899db54dc7970bf6b848b86caad930503648584](https://github.com/chengcli/paddle/blob/7899db54dc7970bf6b848b86caad930503648584/pyproject.toml#L33) |
| `refs/remotes/pull/2` | [5bb2c2b75ac0dd22b5004d3eb805fda0e24914da](https://github.com/chengcli/paddle/blob/5bb2c2b75ac0dd22b5004d3eb805fda0e24914da/pyproject.toml#L33) |
| `refs/remotes/pull/3` | [de9fbf1950c2b8c37b60bbf73ee6e967883d8b49](https://github.com/chengcli/paddle/blob/de9fbf1950c2b8c37b60bbf73ee6e967883d8b49/pyproject.toml#L33) |
| `refs/remotes/pull/4` | [bd6ba6ca8461010a03fb98502514e172e62b9be1](https://github.com/chengcli/paddle/blob/bd6ba6ca8461010a03fb98502514e172e62b9be1/pyproject.toml#L33) |
| `refs/remotes/pull/5` | [5587fc430464e6ebfdfb59221ecb85c9fcb9483b](https://github.com/chengcli/paddle/blob/5587fc430464e6ebfdfb59221ecb85c9fcb9483b/pyproject.toml#L33) |
| `refs/remotes/pull/6` | [ea126dddaaa94b870ecacfdbdcccf07a8f529a10](https://github.com/chengcli/paddle/blob/ea126dddaaa94b870ecacfdbdcccf07a8f529a10/pyproject.toml#L33) |
| `refs/remotes/pull/7` | [534d18e2d5e641b1d7595392f3c7043084c8456a](https://github.com/chengcli/paddle/blob/534d18e2d5e641b1d7595392f3c7043084c8456a/pyproject.toml#L33) |
| `refs/tags/v1.1.2` | [3362e509f670aad6a0f00b1c0126b38c777525c4](https://github.com/chengcli/paddle/blob/3362e509f670aad6a0f00b1c0126b38c777525c4/pyproject.toml#L33) |
| `refs/tags/v1.1.3` | [bc79c1ca00e23fe01003947369aea022ae18e62b](https://github.com/chengcli/paddle/blob/bc79c1ca00e23fe01003947369aea022ae18e62b/pyproject.toml#L33) |
| `refs/tags/v1.1.4` | [28147875a38b67c7b3b12275f3f984f30367f630](https://github.com/chengcli/paddle/blob/28147875a38b67c7b3b12275f3f984f30367f630/pyproject.toml#L33) |
| `refs/tags/v1.1.5` | [3f5a07cca25b2c75e39c1d5a4afb7a7ff63d40bf](https://github.com/chengcli/paddle/blob/3f5a07cca25b2c75e39c1d5a4afb7a7ff63d40bf/pyproject.toml#L33) |

`git log --all --format=%H -- pyproject.toml` identifies 13 metadata revisions:
12 retain the same Torch range. The initial
[`17c226c440d9b70fbe4e5cd6bb24a600011348b2`](https://github.com/chengcli/paddle/tree/17c226c440d9b70fbe4e5cd6bb24a600011348b2)
has no dependencies, but its entire tree is five files and lacks
`src/paddle/evolve_kinetics.py`; it cannot reproduce chapter 14's driver.
This search establishes no compatible candidate among these public refs and
history, not a claim about every possible fork or future commit.

## Why isolation alone does not reproduce the pinned driver

The report pins kintera
[`0d9f67f97d841147e23283d2dcdab302238d2c45`](https://github.com/chengcli/kintera/blob/0d9f67f97d841147e23283d2dcdab302238d2c45/pyproject.toml#L8),
whose build requirements specify `torch==2.10.0`. Paddle's range excludes that
version. Kintera's Python runtime metadata does not repeat this Torch constraint,
so `pip check` alone cannot prove binary compatibility after a downgrade.
A separate process can isolate two Torch installations, but Paddle's driver
imports kintera and snapy and passes their objects to each other in one Python
process. It has no documented interprocess adapter.

A local isolation probe used a separate Python 3.11 venv with public
`torch==2.7.1+cpu` and attempted `ctypes.CDLL` of the previously source-built
pinned kintera library, with the pyharp library directory supplied. It failed
while loading the native dependency chain:
`libdisort_release.so: undefined symbol: _ZNK3c1010TensorImpl15incref_pyobjectEv`.
The same library load under Torch 2.10.0 succeeded. This demonstrates that
switching only the Torch runtime does not work for the validated native stack;
it does not prove that every possible historical rebuild is impossible.

Chapter 14 explicitly limits the driver description to source reading and
identifies both the dependency conflict and a three-argument `crm` call to a
five-argument `evolve_kinetics` function. Installing older kintera/snapy releases
would change the report's public source targets; it would not validate its
current pins, its newer kinetics options, or that call. No such substitution or
scientific-content change is included here.

## Required owner decision

Choose either:

1. Obtain a public Paddle revision that supports and validates Torch 2.10.0 with
   the report's existing kintera/snapy pins, then authorize the corresponding
   Paddle pin and chapter source-citation update; or
2. Commission a separately specified historical reproduction target, naming its
   kintera/snapy pins, input and expected behavior, with chapter-owner review of
   the differences. An isolated legacy runtime can then implement that target.

Until one is available, retain the explicit conflict, missing driver findings,
and nonzero overall audit result. A widened requirement without actual driver
validation, a no-dependencies install, or an older native pin is not evidence
that the report's coupling behavior works.
