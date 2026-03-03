from __future__ import annotations

import os
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HostMetrics:
    cpu_percent: float
    memory_percent: float
    swap_percent: float
    disk_percent: float
    mem_total_gib: float
    mem_used_gib: float
    swap_total_gib: float
    swap_used_gib: float
    disk_total_gib: float
    disk_used_gib: float
    load_1m: float
    load_5m: float
    load_15m: float
    tcp_established: int
    net_rx_kib_s: float
    net_tx_kib_s: float


class _NetState:
    def __init__(self) -> None:
        self.last_rx = 0
        self.last_tx = 0
        self.last_ts = 0.0


NET_STATE = _NetState()


try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return proc.returncode, out or err


def local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def public_ip() -> str:
    code, out = _run(["curl", "-sS", "--max-time", "3", "https://checkip.amazonaws.com"])
    if code == 0 and out:
        return out.splitlines()[0].strip()
    return "-"


def _read_proc_net() -> tuple[int, int]:
    rx = 0
    tx = 0
    content = Path("/proc/net/dev").read_text(encoding="utf-8", errors="ignore")
    for line in content.splitlines()[2:]:
        if ":" not in line:
            continue
        iface, data = line.split(":", 1)
        iface = iface.strip()
        if iface == "lo":
            continue
        parts = data.split()
        if len(parts) < 16:
            continue
        rx += int(parts[0])
        tx += int(parts[8])
    return rx, tx


def _network_rate(now_ts: float) -> tuple[float, float]:
    rx_now, tx_now = _read_proc_net()
    if NET_STATE.last_ts <= 0:
        NET_STATE.last_rx, NET_STATE.last_tx, NET_STATE.last_ts = rx_now, tx_now, now_ts
        return 0.0, 0.0
    elapsed = max(0.001, now_ts - NET_STATE.last_ts)
    rx_rate = max(0, rx_now - NET_STATE.last_rx) / elapsed / 1024.0
    tx_rate = max(0, tx_now - NET_STATE.last_tx) / elapsed / 1024.0
    NET_STATE.last_rx, NET_STATE.last_tx, NET_STATE.last_ts = rx_now, tx_now, now_ts
    return rx_rate, tx_rate


def _tcp_established() -> int:
    code, out = _run(["ss", "-ant", "state", "established"])
    if code != 0:
        return 0
    lines = [line for line in out.splitlines() if line.strip()]
    return max(0, len(lines) - 1)


def _memory_swap_fallback() -> tuple[float, float, float, float]:
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore")
    values: dict[str, int] = {}
    for line in meminfo.splitlines():
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip()
        number = parts[1].strip().split()
        if not number:
            continue
        try:
            values[key] = int(number[0])  # KiB
        except ValueError:
            continue

    mem_total = values.get("MemTotal", 0)
    mem_available = values.get("MemAvailable", 0)
    swap_total = values.get("SwapTotal", 0)
    swap_free = values.get("SwapFree", 0)

    mem_pct = 0.0
    if mem_total > 0:
        mem_pct = ((mem_total - mem_available) / mem_total) * 100.0

    swap_pct = 0.0
    if swap_total > 0:
        swap_pct = ((swap_total - swap_free) / swap_total) * 100.0

    mem_total_gib = mem_total / (1024.0 * 1024.0)
    mem_used_gib = max(0.0, (mem_total - mem_available) / (1024.0 * 1024.0))
    swap_total_gib = swap_total / (1024.0 * 1024.0)
    swap_used_gib = max(0.0, (swap_total - swap_free) / (1024.0 * 1024.0))
    return mem_pct, swap_pct, mem_total_gib, mem_used_gib, swap_total_gib, swap_used_gib


def _disk_fallback() -> tuple[float, float, float]:
    stats = os.statvfs("/")
    total = float(stats.f_blocks * stats.f_frsize)
    free = float(stats.f_bavail * stats.f_frsize)
    if total <= 0:
        return 0.0, 0.0, 0.0
    used = total - free
    percent = (used / total) * 100.0
    return percent, total / (1024.0**3), used / (1024.0**3)


def collect_host_metrics(now_ts: float) -> HostMetrics:
    if psutil is not None:
        mem_info = psutil.virtual_memory()
        swap_info = psutil.swap_memory()
        disk_info = psutil.disk_usage("/")
        cpu = float(psutil.cpu_percent(interval=None))
        mem = float(mem_info.percent)
        swap = float(swap_info.percent)
        disk = float(disk_info.percent)
        mem_total_gib = float(mem_info.total / (1024.0**3))
        mem_used_gib = float(mem_info.used / (1024.0**3))
        swap_total_gib = float(swap_info.total / (1024.0**3))
        swap_used_gib = float(swap_info.used / (1024.0**3))
        disk_total_gib = float(disk_info.total / (1024.0**3))
        disk_used_gib = float(disk_info.used / (1024.0**3))
    else:
        load_scale = max(1, os.cpu_count() or 1)
        cpu = min(100.0, (os.getloadavg()[0] / load_scale) * 100.0)
        mem, swap, mem_total_gib, mem_used_gib, swap_total_gib, swap_used_gib = _memory_swap_fallback()
        disk, disk_total_gib, disk_used_gib = _disk_fallback()

    load_1m, load_5m, load_15m = os.getloadavg()
    rx_rate, tx_rate = _network_rate(now_ts)

    return HostMetrics(
        cpu_percent=cpu,
        memory_percent=mem,
        swap_percent=swap,
        disk_percent=disk,
        mem_total_gib=mem_total_gib,
        mem_used_gib=mem_used_gib,
        swap_total_gib=swap_total_gib,
        swap_used_gib=swap_used_gib,
        disk_total_gib=disk_total_gib,
        disk_used_gib=disk_used_gib,
        load_1m=load_1m,
        load_5m=load_5m,
        load_15m=load_15m,
        tcp_established=_tcp_established(),
        net_rx_kib_s=rx_rate,
        net_tx_kib_s=tx_rate,
    )
