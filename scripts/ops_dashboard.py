#!/usr/bin/env python3
"""Launcher do Ops Center com foco em uso diario."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    root_dir = Path(__file__).resolve().parents[1]
    target = root_dir / "scripts" / "ops_center.py"
    if not target.exists():
        print(f"Arquivo nao encontrado: {target}")
        return 1

    extra_args = []
    if os.environ.get("MRQ_OPS_AUTO_START") == "1":
        if "--auto-start" not in sys.argv and "--once" not in sys.argv:
            extra_args.append("--auto-start")

    args = [sys.executable, str(target), *extra_args, *sys.argv[1:]]
    os.execv(sys.executable, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
