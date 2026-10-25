"""A failed pre-render check must not make log collection fail again."""
import os
from pathlib import Path
import subprocess
import textwrap


def test_failure_diagnostic_without_rendered_logs(tmp_path):
    repository = Path(__file__).resolve().parents[4]
    workflow = (repository / '.github/workflows/tech-report.yml').read_text()
    block = workflow.split('      - name: Show the failing log', 1)[1].split('        run: |', 1)[1]
    (tmp_path / 'book').mkdir()
    result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', textwrap.dedent(block)],
                            cwd=tmp_path, env=dict(os.environ, RUNNER_TEMP=str(tmp_path)),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
