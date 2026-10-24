"""Inventory literal CUDA mentions in the pinned source's Python test files.

This is a static file inventory, not evidence of executing any CUDA assertion.
The filename glob and case-sensitive substring match reproduce the chapter's
`grep -l "cuda" test*.py` definition, including comments and skipped tests.
"""
import argparse
import json
import subprocess
from pathlib import Path


def inventory(source):
    source = Path(source).resolve()
    files = sorted((source / "tests").glob("test*.py"))
    if not files:
        raise ValueError("no tests/test*.py files found")
    sha = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    named = [p.name for p in files if "cuda" in p.read_text()]
    return {
        "source_sha": sha,
        "definition": 'case-sensitive literal "cuda" anywhere in tests/test*.py',
        "total": len(files),
        "cuda_named": named,
        "cuda_named_count": len(named),
        "no_cuda_named_count": len(files) - len(named),
        "runtime_cuda_validation": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", type=Path, help="compare with a committed JSON inventory")
    args = parser.parse_args()
    result = inventory(args.source)
    print(json.dumps(result, indent=2))
    if args.check and result != json.loads(args.check.read_text()):
        raise SystemExit("inventory differs from the committed source identity or file list")


if __name__ == "__main__":
    main()
