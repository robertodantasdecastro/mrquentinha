#!/usr/bin/env python
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _read_settings_module_from_dotenv() -> str:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return ""

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() != "DJANGO_SETTINGS_MODULE":
                continue
            return value.strip().strip('"').strip("'")
    except OSError:
        return ""

    return ""


def main() -> None:
    settings_module = (
        os.getenv("DJANGO_SETTINGS_MODULE")
        or _read_settings_module_from_dotenv()
        or "config.settings.dev"
    )
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        settings_module,
    )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
