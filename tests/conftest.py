import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Safe defaults for tests
os.environ.setdefault("SPECTRA_PROXY_MODE", "direct")
os.environ.setdefault("SPECTRA_DB_PATH", str(ROOT / "backend" / "test_profiles.db"))

from backend.db import init_db  # noqa: E402

init_db()
