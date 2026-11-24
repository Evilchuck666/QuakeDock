#!/usr/bin/env python3
"""Start QuakeDock, from source or from its single-file executable (scripts/QuakeDock.spec)."""

import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    # From a checkout the package lives in src/, whether or not it is installed.
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from quakedock.__main__ import run  # noqa: E402 - needs src/ on sys.path first.

if __name__ == "__main__":
    raise SystemExit(run())
