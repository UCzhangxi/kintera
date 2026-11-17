#pragma once
// V3 lane K skeleton: declarations only, in no build. Rev 1.
// Generalises eval_const_cv_pressure_delta (src/thermo/eval_uhs.hpp:41-56).
#include "tables.hpp"

namespace kintera {

//! pressure change of a perturbation about a reference state, in the
//! caller's dtype. Constant cv: today's formula. T-dependent cv: the change
//! in T from the fixed-mode solve about the reference; refused in FP32
//! until its eager gate passes (snapy/src/eos/ideal_moist.cpp:87).
torch::Tensor eval_pressure_delta(torch::Tensor const& thermal0,
                                  torch::Tensor const& gas0,
                                  torch::Tensor const& cv0,
                                  torch::Tensor const& dthermal,
                                  torch::Tensor const& dgas,
                                  torch::Tensor const& dcv,
                                  ThermoTables const& tables);

}  // namespace kintera
