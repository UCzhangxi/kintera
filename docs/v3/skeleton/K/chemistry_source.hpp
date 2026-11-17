#pragma once
// V3 lane K skeleton: declarations only, in no build. Rev 2.
// A snapy type: kintera's API gains none. The step now in
// snapy/examples/run_hydro.cpp:171-198 as a registered source. FluxRegister
// is lane R's (docs/v3/skeleton/R/flux_register.hpp, happysky19/snapy 3490d7e1).
#include <string>
#include <vector>
#include <torch/torch.h>

namespace snap {

class FluxRegister;  // lane R

//! cell_amount names posted by lane K (FP64, volume-weighted, after_combine)
inline constexpr char kSatSpecies[] = "thermo.saturation";  // species rows
inline constexpr char kChemSpecies[] = "chem.species";      // del_rho rows
inline constexpr char kChemElements[] = "chem.elements";    // must be ~0
inline constexpr char kChemEnergy[] = "chem.energy";        // zero today

//! one chemistry step after the last stage, eager segment, FP64. Built on
//! kintera's Kinetics, evolve_implicit and stoich; any provider fills it.
class ChemistrySource {
 public:
  virtual ~ChemistrySource() = default;
  virtual std::string name() const = 0;
  //! species rows of the conserved state it changes
  virtual std::vector<int> rows() const = 0;
  //! element-by-species matrix for the chem.elements amount (FP64)
  virtual torch::Tensor element_matrix() const = 0;
  //! adds the increment to u in place; posts the four amounts as
  //! cell_amount(name, vol_du) in phase after_combine
  virtual void apply(torch::Tensor u, torch::Tensor const& temp,
                     torch::Tensor const& pres, double dt,
                     FluxRegister& reg) = 0;
  //! true if apply() holds no host read (none at the pin: kinetics.cpp)
  virtual bool capturable() const = 0;
};

}  // namespace snap
