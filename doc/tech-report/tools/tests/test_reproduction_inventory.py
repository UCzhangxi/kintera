"""CPU commands mentioning CUDA must remain in the reproduction audit."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'environment'))
from inventory_policy import gpu_only  # noqa: E402


@pytest.mark.parametrize(('command', 'expected'), [
    ('CUDA_VISIBLE_DEVICES="" python -P src/kintera_report/ch01/runs/snippet.py', False),
    ('grep -l "cuda" test*.py', False),
    ('python check_ch12_spec_complement.py conditioning', False),
    ('python check_ch12_spec_complement.py sparse', True),
    ('python gpu_probe.py', True),
    ('cuobjdump --dump-sass libkintera.so', True),
])
def test_gpu_classification_preserves_cpu_and_static_commands(command, expected):
    assert gpu_only(command) is expected
