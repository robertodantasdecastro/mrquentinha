from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .config import EVENTS_LOG, METRICS_LOG, RUNTIME_DIR


def ensure_runtime_dirs() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def append_event(level: str, message: str) -> None:
    ensure_runtime_dirs()
    timestamp = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with EVENTS_LOG.open("a", encoding="utf-8") as fp:
        fp.write(f"{timestamp} [{level}] {message}\n")


def append_metric(payload: dict) -> None:
    ensure_runtime_dirs()
    timestamp = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    line = {"ts": timestamp, **payload}
    with METRICS_LOG.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(line, ensure_ascii=True) + "\n")


def tail_events(limit: int = 12) -> list[str]:
    ensure_runtime_dirs()
    if not EVENTS_LOG.exists():
        return []
    lines = EVENTS_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-limit:]


def path_status() -> dict[str, str]:
    ensure_runtime_dirs()
    return {
        "events_log": str(Path(EVENTS_LOG).resolve()),
        "metrics_log": str(Path(METRICS_LOG).resolve()),
    }
