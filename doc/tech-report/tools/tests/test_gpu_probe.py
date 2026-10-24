"""The report's CUDA comparison must not accept nonfinite or broadcast outputs."""
import importlib.util
import os
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("kintera")
PATH = Path(os.environ.get("GPU_PROBE_PATH", Path(__file__).resolve().parents[2] /
    "src/kintera_report/ch13/runs/gpu_probe.py"))
spec = importlib.util.spec_from_file_location("report_gpu_probe", PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def measured(monkeypatch, a, b):
    class Options:
        def species(self):
            return []
    class Kinetics:
        def to(self, device):
            return self
    monkeypatch.setattr(probe, "load", lambda card: (Options(), Kinetics()))
    monkeypatch.setattr(probe.kt, "Kinetics", lambda op: Kinetics())
    monkeypatch.setattr(torch.Tensor, "cuda", lambda self: self)
    monkeypatch.setattr(torch.cuda, "synchronize", lambda: None)
    outputs = iter([{"value": a}, {"value": b}])
    monkeypatch.setattr(probe, "evaluate", lambda *args: next(outputs))
    return probe.compare("controlled", "", lambda names: (torch.ones(1),) * 3, 10.)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("side", ["cpu", "gpu", "both"])
def test_nonfinite_is_failure(monkeypatch, bad, side):
    a = torch.tensor([bad if side in ("cpu", "both") else 1.], dtype=torch.float64)
    b = torch.tensor([bad if side in ("gpu", "both") else 1.], dtype=torch.float64)
    assert measured(monkeypatch, a, b) > 1e-13


def test_shape_mismatch_is_failure(monkeypatch):
    assert measured(monkeypatch, torch.ones(1), torch.ones(2)) > 1e-13


@pytest.mark.parametrize("a,b,expected", [([0., 0.], [0., 0.], 0.),
    ([0., 0.], [0., 2e-14], 2e-14), ([2., 4.], [2., 4.000000000004], 1.000088900582341e-12)])
def test_finite_formula_preserved(monkeypatch, a, b, expected):
    actual = measured(monkeypatch, torch.tensor(a, dtype=torch.float64), torch.tensor(b, dtype=torch.float64))
    assert actual == expected
