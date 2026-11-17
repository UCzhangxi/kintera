#pragma once
// V3 lane K skeleton: declarations only, in no build. Rev 2.1.
// Pin kintera 3f5ff938. Replaces the per-call lookups of
// src/utils/user_funcs.cu:14-133 and the per-call uploads of
// src/thermo/eval_uhs.cpp:155-156 and src/thermo/log_svp.cpp:36-38.
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include <torch/torch.h>

namespace kintera {

//! device (or host) function pointers, one per column; nullptr = no term.
//! An int64 tensor on the table's device, filled once by prepare().
struct FuncTable {
  torch::Tensor ptrs;  // (ncol,) int64, never rebound
  int arity = 1;       // 1: f(T); 2: f(T, C); 3: f(T, C, P)
};

//! fills one table from names; the only device-symbol read (outside capture)
FuncTable make_func_table(std::vector<std::string> const& names, int arity,
                          torch::Device device);

//! everything a kintera thermo op reads per call, built once per
//! (device, dtype, generation pair). Immutable after prepare().
struct ThermoTables {
  torch::Device device = torch::kCPU;
  torch::Dtype dtype = torch::kFloat64;  // compute dtype of eval_*
  uint64_t options_digest = 0;  // hash of the options content
  int64_t epoch = 0;  // bumped by every reset()/prepare() that reallocates

  // constants now uploaded per call (src/thermo/eval_uhs.cpp:264-265)
  torch::Tensor cref_R, uref_R, sref_R;  // (nspecies,), dtype
  torch::Tensor cv0, u0, inv_mu;         // copies of the module buffers, dtype
  torch::Tensor nasa9_low, nasa9_high, nasa9_Tmid;  // (nsp,9), (nsp,9), (nsp,)
  torch::Tensor h2_mask;                 // (nspecies,) bool

  // saturation spec, now built per forward (src/thermo/log_svp.cpp:13-40)
  torch::Tensor svp_kind;    // (nreaction,) int32
  torch::Tensor svp_params;  // (nreaction, k) FP64 always

  // function tables (src/thermo/thermo_dispatch.cu:84-102)
  FuncTable logsvp, logsvp_ddT;
  FuncTable intEng_extra, intEng_extra_ddT;
  FuncTable cp_R_extra, czh, czh_ddC, entropy_extra;
};

using ThermoTablesPtr = std::shared_ptr<ThermoTables const>;

//! tables of `op` for the device and dtype of `like`, used by the eval_*
//! bodies; built if missing outside capture, throws inside
ThermoTablesPtr tables_for(std::shared_ptr<struct SpeciesThermoImpl> const& op,
                           torch::Tensor const& like);

//! true while the current stream is capturing; a table build then throws
bool capture_active(torch::Device device);

}  // namespace kintera
