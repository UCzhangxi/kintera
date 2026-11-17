#pragma once
// V3 lane K skeleton: declarations only, in no build. Rev 2.1.
// A snapy type: kintera's API gains none. The step now in
// snapy/examples/run_hydro.cpp:171-198 as a registered source. FluxRegister
// is lane R's (docs/v3/skeleton/R/flux_register.hpp, happysky19/snapy 4c59162a).
#include <string>
#include <vector>
#include <torch/torch.h>

namespace snap {

class FluxRegister;  // lane R

//! names posted by lane K (FP64, volume-weighted, last after_combine only)
inline constexpr char kSatSpecies[] = "thermo.saturation";  // cell_source
inline constexpr char kChemSpecies[] = "chem.species";      // cell_source
inline constexpr char kChemElements[] = "chem.elements";    // diagnostic, element/<name>
inline constexpr char kChemEnergy[] = "chem.energy";        // cell_source, 0

//! one chemistry step after the last stage, eager segment, FP64. Built on
//! kintera's Kinetics and evolve_implicit; any provider fills it.
class ChemistrySource {
 public:
  virtual ~ChemistrySource() = default;
  virtual std::string name() const = 0;
  //! species rows of the conserved state it changes
  virtual std::vector<int> rows() const = 0;
  //! element-by-species matrix E from species composition (FP64);
  //! chem.elements = E del_conc
  virtual torch::Tensor element_matrix() const = 0;
  //! row names of element_matrix(), posted as "element/<name>"
  virtual std::vector<std::string> element_names() const = 0;
  //! adds the increment to u in place; posts cell_amount(name, vol_du,
  //! 1.0, kind) and derived_amount for chem.elements
  virtual void apply(torch::Tensor u, torch::Tensor const& temp,
                     torch::Tensor const& pres, double dt,
                     FluxRegister& reg) = 0;
  //! true if apply() holds no host read (none at the pin: kinetics.cpp)
  virtual bool capturable() const = 0;
};

}  // namespace snap
