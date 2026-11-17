#pragma once
// V3 lane K skeleton: declarations only, in no build. Rev 2.
// Additions to ThermoYImpl (src/thermo/thermo.hpp:115-276) at kintera
// 3f5ff938. Precision and graph types are lane X's; none is redefined here.
#include <array>
#include <optional>
#include "tables.hpp"

namespace kintera {

//! chosen once in reset() from options only, never from data
enum class SolvePlan : uint8_t {
  exact,   // no intEng_R_extra, no nasa9, no h2: guess + one correction
  newton,  // T-dependent heat capacity (src/thermo/thermo_y.cpp:510-545)
};

//! how a newton plan iterates
enum class SolveMode : uint8_t {
  eager_exit,  // today: host read per pass (src/thermo/thermo_y.cpp:525)
  fixed,       // max_iter passes, 0-d device flag freezes converged state;
               // bitwise equal to eager_exit (gate K-G2)
};

//! rows of the failure counter
enum class Failure : uint8_t { saturation = 0, temp_solve = 1, pres_solve = 2 };
inline constexpr int kFailureRows = 3;

//! warm-start state of the KKT solve (src/thermo/thermo.hpp:142-143)
struct ActiveSet {
  torch::Tensor reaction_set;  // (..., nreaction) int32
  torch::Tensor nactive;       // (...) int32
};

// ---- declarations added to class ThermoYImpl ----
class ThermoYV3Api {
 public:
  //! outside capture: build or reuse the tables, allocate the counter and
  //! the active set for `shape`, warm the shared-memory query
  //! (src/loops.cuh:18-50). Throws if called while capturing.
  ThermoTablesPtr prepare(torch::Device device, torch::Dtype dtype,
                          torch::IntArrayRef shape);
  ThermoTablesPtr tables() const;  // null before prepare()
  SolvePlan temp_plan() const;     // VU->T
  SolvePlan pres_plan() const;     // PV->T (exact iff every czh is empty)
  void set_solve_mode(SolveMode mode);  // newton plans only
  SolveMode solve_mode() const;

  //! same conversions as compute(); writes into `out` with copy_, no set_
  //! (src/thermo/thermo_y.cpp:462, src/thermo/thermo_y.cpp:517)
  void compute_into(std::string const& ab,
                    std::vector<torch::Tensor> const& args,
                    torch::Tensor out);

  //! (3,) int64 device view, fixed after prepare(); never read here
  torch::Tensor const& failures() const;
  //! zero_() in place; capturable (step-reset list, replaces a host read)
  void reset_failures();
  //! row 0 only: out.copy_(failures()[0] > 0), then row 0 zero_(); rows 1-2
  //! kept for the step-end read; capturable; `out` is the saturation slot
  //! of the retry stack (snapy/src/mesh/meshblock.cpp:1559-1560)
  void consume_failures(torch::Tensor out);
  //! host read of row 0, then zero: step end or output only (kept)
  int64_t take_saturation_adjustment_failures();

  //! copy_ into fixed storage; restore after a retry or a graph warm-up
  void snapshot_active_set(ActiveSet& out) const;
  void restore_active_set(ActiveSet const& in);
  ActiveSet make_active_set_storage() const;  // shapes from prepare()

 private:
  ThermoTablesPtr tables_;
  torch::Tensor failures_;  // replaces public nfail_ after one release
  SolvePlan temp_plan_ = SolvePlan::newton, pres_plan_ = SolvePlan::newton;
  SolveMode mode_ = SolveMode::eager_exit;
};

}  // namespace kintera
