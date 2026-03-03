from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from .config import SERVICE_GROUP_UNITS, SERVICE_UNITS


@dataclass(frozen=True)
class ServiceStatus:
    key: str
    label: str
    unit: str
    state: str


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return proc.returncode, out or err


def _systemctl_cmd(action: str, unit: str) -> list[str]:
    if os.geteuid() == 0:
        return ["systemctl", action, unit]
    return ["sudo", "-n", "systemctl", action, unit]


def list_service_status() -> list[ServiceStatus]:
    rows: list[ServiceStatus] = []
    for spec in SERVICE_UNITS:
        code, out = _run(["systemctl", "is-active", spec.unit])
        state = out if code == 0 else (out or "unknown")
        rows.append(ServiceStatus(spec.key, spec.label, spec.unit, state))
    return rows


def service_action(key: str, action: str) -> tuple[bool, str]:
    allowed = {"start", "stop", "restart"}
    if action not in allowed:
        return False, f"acao invalida: {action}"

    if key == "stack":
        return stack_action(action)

    spec = next((item for item in SERVICE_UNITS if item.key == key), None)
    if spec is None:
        return False, f"servico invalido: {key}"

    code, out = _run(_systemctl_cmd(action, spec.unit))
    return code == 0, out or "ok"


def stack_action(action: str) -> tuple[bool, str]:
    if action not in {"start", "stop", "restart"}:
        return False, f"acao invalida: {action}"

    cmd = ["systemctl", action, *SERVICE_GROUP_UNITS] if os.geteuid() == 0 else ["sudo", "-n", "systemctl", action, *SERVICE_GROUP_UNITS]
    code, out = _run(cmd)
    return code == 0, out or "ok"
