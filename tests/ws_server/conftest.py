"""Load the root server.py module without conflicting with this test package."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("moneypenny_server", _ROOT / "server.py")
assert _spec and _spec.loader
_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_server)

create_app = _server.create_app
