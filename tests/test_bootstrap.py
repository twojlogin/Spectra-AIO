from pathlib import Path
import subprocess
import sys


def test_bootstrap_check_only_runs():
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, "scripts/bootstrap.py", "--check-only"], cwd=root, capture_output=True, text=True)
    # returns 0 or 1 depending on warnings, but should run
    assert r.returncode in (0, 1)
    assert "System:" in (r.stdout + r.stderr)
