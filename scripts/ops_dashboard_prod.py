#!/usr/bin/env python3
"""Launcher do Ops Center em modo producao."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    root_dir = Path(__file__).resolve().parents[1]
    target = root_dir / "scripts" / "ops_center_prod.py"
    if not target.exists():
        print(f"Arquivo nao encontrado: {target}")
        return 1

    args = [sys.executable, str(target), *sys.argv[1:]]
    os.execv(sys.executable, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
