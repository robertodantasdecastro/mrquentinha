#!/usr/bin/env python3
"""Painel operacional estilo btop para o stack Mr Quentinha."""

from __future__ import annotations

import argparse
import csv
import curses
import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import time
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque

REQUEST_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|OPTIONS)\b")
SPARK_CHARS = "▁▂▃▄▅▆▇█"
HISTORY_SIZE = 60
EXPORT_EVENT_WINDOW = 20
LOG_TAIL_LINES = 3

KEY_HELP = [
    "Acoes rapidas: a start all | s stop all | r restart all | q sair",
    "Backend: 1 start | 2 stop | 3 restart",
    "Admin:   g start | h stop | j restart",
    "Portal:  4 start | 5 stop | 6 restart",
    "Client:  7 start | 8 stop | 9 restart",
    "UI:      ? ajuda | l logs | c compacto",
]

HAS_SS = shutil.which("ss") is not None
HAS_LSOF = shutil.which("lsof") is not None


@dataclass(frozen=True)
class ServiceSpec:
    key: str
    name: str
    script: str
    port: int


@dataclass
class ServiceSnapshot:
    spec: ServiceSpec
    state: str
    pid: int | None
    uptime_seconds: float | None
    rss_mb: float | None
    hits_per_sec: int
    last_request: str


SERVICES = (
    ServiceSpec("backend", "Backend Django", "scripts/start_backend_dev.sh", 8000),
    ServiceSpec("admin", "Admin Web", "scripts/start_admin_dev.sh", 3002),
    ServiceSpec("portal", "Portal Next", "scripts/start_portal_dev.sh", 3000),
    ServiceSpec("client", "Client Next", "scripts/start_client_dev.sh", 3001),
)


class LogCounter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.offset = 0
        self.last_request = "-"

    def reset_to_end(self) -> None:
        if self.path.exists():
            self.offset = self.path.stat().st_size
        else:
            self.offset = 0

    def consume(self) -> int:
        if not self.path.exists():
            self.offset = 0
            return 0

        size = self.path.stat().st_size
        if size < self.offset:
            self.offset = 0

        with self.path.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.offset)
            chunk = f.read()
            self.offset = f.tell()

        hits = 0
        for line in chunk.splitlines():
            if REQUEST_RE.search(line):
                hits += 1
                self.last_request = line.strip()[:120]
        return hits


class OpsManager:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.runtime_dir = root_dir / ".runtime" / "ops"
        self.pid_dir = self.runtime_dir / "pids"
        self.log_dir = self.runtime_dir / "logs"
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_counters = {spec.key: LogCounter(self.log_file(spec)) for spec in SERVICES}
        for counter in self.log_counters.values():
            counter.reset_to_end()

        self.hit_history: dict[str, Deque[int]] = {
            spec.key: deque([0] * HISTORY_SIZE, maxlen=HISTORY_SIZE) for spec in SERVICES
        }

    def pid_file(self, spec: ServiceSpec) -> Path:
        return self.pid_dir / f"{spec.key}.pid"

    def log_file(self, spec: ServiceSpec) -> Path:
        return self.log_dir / f"{spec.key}.log"

    def _read_pid(self, spec: ServiceSpec) -> int | None:
        pid_path = self.pid_file(spec)
        if not pid_path.exists():
            return None

        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

        if self._is_pid_running(pid):
            return pid

        try:
            pid_path.unlink()
        except OSError:
            pass
        return None

    def _write_pid(self, spec: ServiceSpec, pid: int) -> None:
        self.pid_file(spec).write_text(str(pid), encoding="utf-8")

    def _clear_pid(self, spec: ServiceSpec) -> None:
        try:
            self.pid_file(spec).unlink()
        except OSError:
            pass

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @staticmethod
    def _listener_pids(port: int) -> list[int]:
        if HAS_SS:
            try:
                proc = subprocess.run(
                    ["ss", "-ltnp", f"sport = :{port}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                pids = {int(m.group(1)) for m in re.finditer(r"pid=(\d+)", proc.stdout)}
                return sorted(pids)
            except Exception:
                return []

        if HAS_LSOF:
            try:
                proc = subprocess.run(
                    ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                pids = {int(line.strip()) for line in proc.stdout.splitlines() if line.strip().isdigit()}
                return sorted(pids)
            except Exception:
                return []

        return []

    def start_service(self, key: str) -> str:
        spec = self._spec(key)
        managed_pid = self._read_pid(spec)
        listener_pids = self._listener_pids(spec.port)

        if managed_pid:
            return f"{spec.name} ja esta em execucao (pid {managed_pid})."
        if listener_pids:
            return (
                f"{spec.name} ja possui listener na porta {spec.port} "
                f"(pids {', '.join(map(str, listener_pids))})."
            )

        script_path = self.root_dir / spec.script
        if not script_path.exists():
            return f"Script nao encontrado: {script_path}"

        log_path = self.log_file(spec)
        with log_path.open("ab") as logf:
            proc = subprocess.Popen(  # noqa: S603
                ["bash", str(script_path)],
                cwd=self.root_dir,
                stdout=logf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                env=os.environ.copy(),
            )

        self._write_pid(spec, proc.pid)
        self.log_counters[spec.key].reset_to_end()
        return f"{spec.name} iniciado (pid {proc.pid})."

    def stop_service(self, key: str) -> str:
        spec = self._spec(key)
        managed_pid = self._read_pid(spec)
        stopped = False

        if managed_pid:
            stopped = self._terminate_process_group(managed_pid)
            self._clear_pid(spec)

        listener_pids = self._listener_pids(spec.port)
        for pid in listener_pids:
            if managed_pid and pid == managed_pid:
                continue
            stopped = self._terminate_pid(pid) or stopped

        if stopped:
            return f"{spec.name} parado."

        self._clear_pid(spec)
        return f"{spec.name} ja estava parado."

    def restart_service(self, key: str) -> str:
        stop_msg = self.stop_service(key)
        time.sleep(0.3)
        start_msg = self.start_service(key)
        return f"{stop_msg} {start_msg}"

    def start_all(self) -> str:
        return " | ".join(self.start_service(spec.key) for spec in SERVICES)

    def stop_all(self) -> str:
        return " | ".join(self.stop_service(spec.key) for spec in SERVICES)

    def restart_all(self) -> str:
        return " | ".join(self.restart_service(spec.key) for spec in SERVICES)

    def collect_snapshots(self) -> list[ServiceSnapshot]:
        snapshots: list[ServiceSnapshot] = []
        for spec in SERVICES:
            managed_pid = self._read_pid(spec)
            listener_pids = self._listener_pids(spec.port)

            pid_for_metrics: int | None
            state: str
            if managed_pid:
                state = "RUNNING"
                pid_for_metrics = listener_pids[0] if listener_pids else managed_pid
            elif listener_pids:
                state = "EXTERNAL"
                pid_for_metrics = listener_pids[0]
            else:
                state = "STOPPED"
                pid_for_metrics = None

            hits = self.log_counters[spec.key].consume()
            self.hit_history[spec.key].append(hits)

            snapshots.append(
                ServiceSnapshot(
                    spec=spec,
                    state=state,
                    pid=pid_for_metrics,
                    uptime_seconds=process_uptime_seconds(pid_for_metrics),
                    rss_mb=process_rss_mb(pid_for_metrics),
                    hits_per_sec=hits,
                    last_request=self.log_counters[spec.key].last_request,
                )
            )

        return snapshots

    @staticmethod
    def _terminate_process_group(pid: int) -> bool:
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            return False

        deadline = time.time() + 6
        while time.time() < deadline:
            if not OpsManager._is_pid_running(pid):
                return True
            time.sleep(0.2)

        try:
            os.killpg(pid, signal.SIGKILL)
            return True
        except OSError:
            return False

    @staticmethod
    def _terminate_pid(pid: int) -> bool:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return False

        deadline = time.time() + 4
        while time.time() < deadline:
            if not OpsManager._is_pid_running(pid):
                return True
            time.sleep(0.2)

        try:
            os.kill(pid, signal.SIGKILL)
            return True
        except OSError:
            return False

    @staticmethod
    def _spec(key: str) -> ServiceSpec:
        for spec in SERVICES:
            if spec.key == key:
                return spec
        raise KeyError(f"Servico desconhecido: {key}")


class ExportWriter:
    def __init__(self, root_dir: Path, json_target: str | None, csv_target: str | None) -> None:
        self.root_dir = root_dir
        self.export_dir = root_dir / ".runtime" / "ops" / "exports"
        self.json_path = self._resolve_target(json_target, "jsonl")
        self.csv_path = self._resolve_target(csv_target, "csv")

        if self.json_path:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
        if self.csv_path:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            self._ensure_csv_header()

    @property
    def enabled(self) -> bool:
        return self.json_path is not None or self.csv_path is not None

    def status_text(self) -> str:
        if not self.enabled:
            return "export: desativado"

        parts = []
        if self.json_path:
            parts.append(f"json={self.json_path}")
        if self.csv_path:
            parts.append(f"csv={self.csv_path}")
        return "export: " + " | ".join(parts)

    def _resolve_target(self, target: str | None, extension: str) -> Path | None:
        if not target:
            return None

        if target == "auto":
            stamp = dt.date.today().strftime("%Y%m%d")
            return self.export_dir / f"ops_{stamp}.{extension}"

        path = Path(target).expanduser()
        if not path.is_absolute():
            path = (self.root_dir / path).resolve()
        if path.suffix == "":
            path = path.with_suffix(f".{extension}")
        return path

    def _ensure_csv_header(self) -> None:
        assert self.csv_path is not None
        if self.csv_path.exists() and self.csv_path.stat().st_size > 0:
            return

        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "service",
                    "state",
                    "pid",
                    "port",
                    "uptime_seconds",
                    "rss_mb",
                    "hits_per_sec",
                    "cpu_percent",
                    "mem_percent",
                    "mem_used_gb",
                    "mem_total_gb",
                    "rx_bytes_per_sec",
                    "tx_bytes_per_sec",
                    "frontend_sources",
                    "last_request",
                    "events",
                ]
            )

    def write_sample(
        self,
        timestamp: str,
        cpu_now: float,
        mem_now: tuple[float, float, float],
        rx_rate: float,
        tx_rate: float,
        snapshots: list[ServiceSnapshot],
        frontend_hits: Counter[str],
        events: list[str],
    ) -> None:
        frontend_compact = ";".join(f"{ip}:{count}" for ip, count in frontend_hits.most_common())

        if self.json_path:
            payload = {
                "timestamp": timestamp,
                "system": {
                    "cpu_percent": round(cpu_now, 2),
                    "mem_percent": round(mem_now[0], 2),
                    "mem_used_gb": round(mem_now[1], 4),
                    "mem_total_gb": round(mem_now[2], 4),
                    "rx_bytes_per_sec": round(rx_rate, 2),
                    "tx_bytes_per_sec": round(tx_rate, 2),
                },
                "frontend_sources": dict(frontend_hits),
                "events": events,
                "services": [
                    {
                        "service": snap.spec.key,
                        "state": snap.state,
                        "pid": snap.pid,
                        "port": snap.spec.port,
                        "uptime_seconds": None if snap.uptime_seconds is None else round(snap.uptime_seconds, 2),
                        "rss_mb": None if snap.rss_mb is None else round(snap.rss_mb, 2),
                        "hits_per_sec": snap.hits_per_sec,
                        "last_request": snap.last_request,
                    }
                    for snap in snapshots
                ],
            }
            with self.json_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        if self.csv_path:
            with self.csv_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for snap in snapshots:
                    writer.writerow(
                        [
                            timestamp,
                            snap.spec.key,
                            snap.state,
                            snap.pid or "",
                            snap.spec.port,
                            "" if snap.uptime_seconds is None else round(snap.uptime_seconds, 2),
                            "" if snap.rss_mb is None else round(snap.rss_mb, 2),
                            snap.hits_per_sec,
                            round(cpu_now, 2),
                            round(mem_now[0], 2),
                            round(mem_now[1], 4),
                            round(mem_now[2], 4),
                            round(rx_rate, 2),
                            round(tx_rate, 2),
                            frontend_compact,
                            snap.last_request,
                            " | ".join(events),
                        ]
                    )


# Helpers de sistema

def read_cpu_counters() -> tuple[int, int]:
    with open("/proc/stat", "r", encoding="utf-8") as f:
        first = f.readline().split()

    values = [int(v) for v in first[1:]]
    total = sum(values)
    idle = values[3] + values[4]
    return total, idle


def cpu_percent(prev: tuple[int, int], curr: tuple[int, int]) -> float:
    total_delta = curr[0] - prev[0]
    idle_delta = curr[1] - prev[1]
    if total_delta <= 0:
        return 0.0
    return max(0.0, min(100.0, 100.0 * (1.0 - idle_delta / total_delta)))


def read_memory() -> tuple[float, float, float]:
    values: dict[str, int] = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0])

    total_kib = values.get("MemTotal", 0)
    avail_kib = values.get("MemAvailable", 0)
    used_kib = max(total_kib - avail_kib, 0)

    if total_kib <= 0:
        return 0.0, 0.0, 0.0

    percent = (used_kib / total_kib) * 100.0
    return percent, used_kib / 1024 / 1024, total_kib / 1024 / 1024


def read_net_bytes() -> tuple[int, int]:
    rx_total = 0
    tx_total = 0
    with open("/proc/net/dev", "r", encoding="utf-8") as f:
        for line in f.readlines()[2:]:
            iface, payload = line.split(":", 1)
            iface = iface.strip()
            if iface == "lo":
                continue
            fields = payload.split()
            if len(fields) < 16:
                continue
            rx_total += int(fields[0])
            tx_total += int(fields[8])

    return rx_total, tx_total


def decode_ipv4(hex_addr: str) -> str:
    raw = bytes.fromhex(hex_addr)
    return ".".join(str(b) for b in raw[::-1])


def frontend_sources() -> Counter[str]:
    sources: Counter[str] = Counter()
    target_ports = {3000, 3001, 3002}

    with open("/proc/net/tcp", "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            parts = line.split()
            if len(parts) < 4:
                continue

            local_addr, remote_addr, state = parts[1], parts[2], parts[3]
            if state != "01":
                continue

            _, local_port_hex = local_addr.split(":")
            remote_ip_hex, _ = remote_addr.split(":")
            local_port = int(local_port_hex, 16)
            if local_port not in target_ports:
                continue

            ip = decode_ipv4(remote_ip_hex)
            sources[ip] += 1

    return sources


def process_uptime_seconds(pid: int | None) -> float | None:
    if not pid:
        return None

    stat_path = Path("/proc") / str(pid) / "stat"
    if not stat_path.exists():
        return None

    try:
        content = stat_path.read_text(encoding="utf-8")
        start_ticks = int(content.split()[21])
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            uptime_seconds = float(f.read().split()[0])
        hertz = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        return max(0.0, uptime_seconds - (start_ticks / hertz))
    except Exception:
        return None


def process_rss_mb(pid: int | None) -> float | None:
    if not pid:
        return None

    status_path = Path("/proc") / str(pid) / "status"
    if not status_path.exists():
        return None

    try:
        for line in status_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                rss_kib = int(line.split()[1])
                return rss_kib / 1024.0
    except Exception:
        return None

    return None


def fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def fmt_rate(byte_per_sec: float) -> str:
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    value = float(max(byte_per_sec, 0.0))
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:6.1f} {unit}"
        value /= 1024.0
    return f"{value:6.1f} GB/s"


def percent_bar(value: float, width: int) -> str:
    width = max(width, 4)
    pct = max(0.0, min(100.0, value))
    filled = int((pct / 100.0) * width)
    return "█" * filled + "░" * (width - filled)


def sparkline(values: Deque[int] | list[int], width: int) -> str:
    if width <= 0:
        return ""

    data = list(values)[-width:]
    if not data:
        return " " * width

    while len(data) < width:
        data.insert(0, 0)

    max_val = max(data)
    if max_val <= 0:
        return "·" * width

    out = []
    for value in data:
        idx = int((value / max_val) * (len(SPARK_CHARS) - 1))
        out.append(SPARK_CHARS[idx])
    return "".join(out)


def color_pair_safe(index: int) -> int:
    try:
        return curses.color_pair(index)
    except Exception:
        return 0


def safe_add(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    if not text:
        return
    trimmed = text[: max(0, w - x - 1)]
    try:
        stdscr.addstr(y, x, trimmed, attr)
    except curses.error:
        pass


def host_hint() -> str:
    return os.environ.get("MRQ_HOST_IP", os.environ.get("OPS_HOST_IP", "127.0.0.1"))


def tail_log_lines(path: Path, lines: int = LOG_TAIL_LINES) -> list[str]:
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return content[-lines:]
    except Exception:
        return []


def draw_dashboard(
    stdscr: curses.window,
    manager: OpsManager,
    snapshots: list[ServiceSnapshot],
    cpu_hist: Deque[int],
    mem_hist: Deque[int],
    rx_hist: Deque[int],
    tx_hist: Deque[int],
    cpu_now: float,
    mem_now: tuple[float, float, float],
    rx_rate: float,
    tx_rate: float,
    events: Deque[str],
    frontend_hits: Counter[str],
    export_status: str,
    show_help: bool,
    show_logs: bool,
    compact: bool,
) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    title_attr = curses.A_BOLD | color_pair_safe(7)
    safe_add(
        stdscr,
        0,
        0,
        f"Mr Quentinha Ops Center  |  {dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  |  q sair",
        title_attr,
    )
    safe_add(
        stdscr,
        1,
        0,
        "Acoes rapidas: [a] start all  [s] stop all  [r] restart all  |  Servicos: [1/2/3] Backend  [g/h/j] Admin  [4/5/6] Portal  [7/8/9] Client",
        color_pair_safe(6),
    )
    safe_add(stdscr, 2, 0, export_status, color_pair_safe(5))

    status_parts = []
    for snap in snapshots:
        state = snap.state
        if state == "RUNNING":
            color = color_pair_safe(2)
        elif state == "EXTERNAL":
            color = color_pair_safe(3)
        else:
            color = color_pair_safe(1)
        status_parts.append((f"[{snap.spec.key}:{state[:3]}]", color))

    y = 3
    x = 0
    for label, color in status_parts:
        safe_add(stdscr, y, x, label + " ", color)
        x += len(label) + 1

    y = 5
    bar_width = max(10, min(32, w // 4))
    mem_percent, used_gb, total_gb = mem_now

    safe_add(stdscr, y, 0, "Sistema", curses.A_BOLD | color_pair_safe(4))
    y += 1
    safe_add(
        stdscr,
        y,
        0,
        f"CPU {cpu_now:5.1f}% [{percent_bar(cpu_now, bar_width)}]  hist {sparkline(cpu_hist, min(28, w - 50))}",
        color_pair_safe(2 if cpu_now < 70 else 3),
    )
    y += 1
    safe_add(
        stdscr,
        y,
        0,
        f"MEM {mem_percent:5.1f}% [{percent_bar(mem_percent, bar_width)}]  {used_gb:4.2f} GB / {total_gb:4.2f} GB  hist {sparkline(mem_hist, min(28, w - 58))}",
        color_pair_safe(2 if mem_percent < 80 else 3),
    )
    y += 2

    safe_add(stdscr, y, 0, "Rede (trafego total host)", curses.A_BOLD | color_pair_safe(4))
    y += 1
    safe_add(
        stdscr,
        y,
        0,
        f"RX {fmt_rate(rx_rate)}  {sparkline(rx_hist, min(36, w - 20))}",
        color_pair_safe(2),
    )
    y += 1
    safe_add(
        stdscr,
        y,
        0,
        f"TX {fmt_rate(tx_rate)}  {sparkline(tx_hist, min(36, w - 20))}",
        color_pair_safe(5),
    )
    y += 2

    safe_add(stdscr, y, 0, "Servicos", curses.A_BOLD | color_pair_safe(4))
    y += 1
    if not compact:
        safe_add(
            stdscr,
            y,
            0,
            "Nome           Estado     PID      Porta   Uptime    RSS(MB)  Hits/s   Grafico de acessos",
            curses.A_UNDERLINE,
        )
    y += 1

    service_rows_left = max(1, min(len(snapshots), h - y - 12))
    graph_space = max(8, w - 76)
    host = host_hint()

    for snap in snapshots[:service_rows_left]:
        if snap.state == "RUNNING":
            state_attr = color_pair_safe(2)
        elif snap.state == "EXTERNAL":
            state_attr = color_pair_safe(3)
        else:
            state_attr = color_pair_safe(1)

        hist = manager.hit_history[snap.spec.key]
        if compact:
            row = (
                f"{snap.spec.name[:14]:14} "
                f"{snap.state:9} "
                f"pid {str(snap.pid or '-'):>6} "
                f"port {snap.spec.port:<5d} "
                f"hits {snap.hits_per_sec:>3d}/s "
                f"{sparkline(hist, max(6, w - 64))}"
            )
            safe_add(stdscr, y, 0, row, state_attr)
            y += 1
            continue

        row = (
            f"{snap.spec.name[:14]:14} "
            f"{snap.state:9} "
            f"{str(snap.pid or '-'):8} "
            f"{snap.spec.port:5d}  "
            f"{fmt_duration(snap.uptime_seconds):8}  "
            f"{(f'{snap.rss_mb:7.1f}' if snap.rss_mb is not None else '-'):>7}  "
            f"{snap.hits_per_sec:6d}   "
            f"{sparkline(hist, graph_space)}"
        )
        safe_add(stdscr, y, 0, row, state_attr)
        y += 1
        if y < h - 1:
            key_hint = {
                "backend": "1/2/3",
                "admin": "g/h/j",
                "portal": "4/5/6",
                "client": "7/8/9",
            }.get(snap.spec.key, "-")
            safe_add(
                stdscr,
                y,
                2,
                f"acoes {key_hint}  url http://{host}:{snap.spec.port}",
                color_pair_safe(6),
            )
        y += 1

    y += 1
    safe_add(
        stdscr,
        y,
        0,
        "Fontes de acesso nos web apps (conexoes TCP ESTABLISHED em 3000/3001/3002)",
        curses.A_BOLD | color_pair_safe(4),
    )
    y += 1
    if frontend_hits:
        for ip, count in frontend_hits.most_common(4):
            safe_add(stdscr, y, 0, f"- {ip:<21} {count:2d} conexoes", color_pair_safe(5))
            y += 1
            if y >= h - 4:
                break
    else:
        safe_add(stdscr, y, 0, "- sem conexoes ativas no momento", color_pair_safe(1))
        y += 1

    if y < h - 4 and not compact:
        y += 1
        safe_add(stdscr, y, 0, "Ultimas atividades HTTP por servico", curses.A_BOLD | color_pair_safe(4))
        y += 1
        for snap in snapshots:
            safe_add(stdscr, y, 0, f"{snap.spec.key:7}: {snap.last_request}", color_pair_safe(6))
            y += 1
            if y >= h - 3:
                break

    if show_logs and y < h - 4:
        y += 1
        safe_add(stdscr, y, 0, "Ultimas linhas de log", curses.A_BOLD | color_pair_safe(4))
        y += 1
        for snap in snapshots:
            lines = tail_log_lines(manager.log_file(snap.spec))
            if not lines:
                safe_add(stdscr, y, 0, f"{snap.spec.key:7}: (sem log)", color_pair_safe(1))
                y += 1
                continue
            for line in lines[-LOG_TAIL_LINES:]:
                safe_add(stdscr, y, 0, f"{snap.spec.key:7}: {line[: max(0, w - 12)]}", color_pair_safe(6))
                y += 1
                if y >= h - 3:
                    break
            if y >= h - 3:
                break

    footer_y = h - 2
    safe_add(stdscr, footer_y, 0, "Eventos recentes:", curses.A_BOLD | color_pair_safe(4))
    safe_add(stdscr, footer_y + 1, 0, " | ".join(events)[-max(0, w - 2) :], color_pair_safe(6))

    if show_help:
        box_lines = KEY_HELP
        box_width = min(w - 4, max(len(line) for line in box_lines) + 4)
        box_height = min(h - 4, len(box_lines) + 2)
        box_y = max(2, (h - box_height) // 2)
        box_x = max(2, (w - box_width) // 2)
        for i in range(box_height):
            safe_add(stdscr, box_y + i, box_x, " " * box_width, color_pair_safe(4))
        safe_add(stdscr, box_y, box_x + 2, "Ajuda", curses.A_BOLD | color_pair_safe(7))
        for idx, line in enumerate(box_lines[: box_height - 2]):
            safe_add(stdscr, box_y + 1 + idx, box_x + 2, line, color_pair_safe(6))

    stdscr.refresh()


def handle_key(manager: OpsManager, key: str) -> str | None:
    mapping = {
        "1": lambda: manager.start_service("backend"),
        "2": lambda: manager.stop_service("backend"),
        "3": lambda: manager.restart_service("backend"),
        "g": lambda: manager.start_service("admin"),
        "h": lambda: manager.stop_service("admin"),
        "j": lambda: manager.restart_service("admin"),
        "4": lambda: manager.start_service("portal"),
        "5": lambda: manager.stop_service("portal"),
        "6": lambda: manager.restart_service("portal"),
        "7": lambda: manager.start_service("client"),
        "8": lambda: manager.stop_service("client"),
        "9": lambda: manager.restart_service("client"),
        "a": manager.start_all,
        "s": manager.stop_all,
        "r": manager.restart_all,
    }

    action = mapping.get(key)
    if not action:
        return None

    try:
        return action()
    except Exception as exc:  # pragma: no cover
        return f"Erro: {exc}"


def sample_bundle(
    manager: OpsManager,
    cpu_prev: tuple[int, int],
    net_prev: tuple[int, int],
    elapsed: float,
) -> tuple[tuple[int, int], tuple[int, int], float, tuple[float, float, float], float, float, list[ServiceSnapshot], Counter[str]]:
    curr_cpu = read_cpu_counters()
    curr_net = read_net_bytes()

    cpu_now = cpu_percent(cpu_prev, curr_cpu)
    mem_now = read_memory()
    rx_rate = (curr_net[0] - net_prev[0]) / max(elapsed, 0.001)
    tx_rate = (curr_net[1] - net_prev[1]) / max(elapsed, 0.001)
    snapshots = manager.collect_snapshots()
    front = frontend_sources()

    return curr_cpu, curr_net, cpu_now, mem_now, rx_rate, tx_rate, snapshots, front


def run_dashboard(
    stdscr: curses.window,
    manager: OpsManager,
    auto_start: bool,
    exporter: ExportWriter,
    export_interval: float,
) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    try:
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
            curses.init_pair(1, curses.COLOR_WHITE, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_CYAN, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_BLUE, -1)
            curses.init_pair(7, curses.COLOR_YELLOW, -1)
    except Exception:
        pass

    stdscr.nodelay(True)
    stdscr.timeout(100)

    events: Deque[str] = deque(maxlen=4)
    event_history: Deque[str] = deque(maxlen=300)

    if auto_start:
        boot_msg = manager.start_all()
        events.append(boot_msg)
        event_history.append(boot_msg)
    else:
        events.append("Painel iniciado.")
        event_history.append("Painel iniciado.")

    cpu_prev = read_cpu_counters()
    net_prev = read_net_bytes()
    last_sample = time.monotonic()
    last_export = 0.0

    cpu_hist: Deque[int] = deque([0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)
    mem_hist: Deque[int] = deque([0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)
    rx_hist: Deque[int] = deque([0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)
    tx_hist: Deque[int] = deque([0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)

    snapshots: list[ServiceSnapshot] = manager.collect_snapshots()
    mem_now = read_memory()
    cpu_now = 0.0
    rx_rate = 0.0
    tx_rate = 0.0
    front = frontend_sources()
    show_help = False
    show_logs = False
    compact = False

    while True:
        ch = stdscr.getch()
        if ch != -1:
            key = chr(ch).lower() if 0 <= ch <= 255 else ""
            if key == "q":
                msg = "Encerrando painel."
                events.append(msg)
                event_history.append(msg)
                break
            if key == "?":
                show_help = not show_help
            if key == "l":
                show_logs = not show_logs
            if key == "c":
                compact = not compact

            action_msg = handle_key(manager, key)
            if action_msg:
                events.append(action_msg)
                event_history.append(action_msg)

        now = time.monotonic()
        if now - last_sample >= 1.0:
            (
                cpu_prev,
                net_prev,
                cpu_now,
                mem_now,
                rx_rate,
                tx_rate,
                snapshots,
                front,
            ) = sample_bundle(manager, cpu_prev, net_prev, now - last_sample)

            cpu_hist.append(int(cpu_now))
            mem_hist.append(int(mem_now[0]))
            rx_hist.append(int(max(rx_rate / 1024, 0)))
            tx_hist.append(int(max(tx_rate / 1024, 0)))

            if exporter.enabled and (now - last_export >= max(export_interval, 0.5)):
                ts = dt.datetime.now().isoformat(timespec="seconds")
                try:
                    exporter.write_sample(
                        timestamp=ts,
                        cpu_now=cpu_now,
                        mem_now=mem_now,
                        rx_rate=rx_rate,
                        tx_rate=tx_rate,
                        snapshots=snapshots,
                        frontend_hits=front,
                        events=list(event_history)[-EXPORT_EVENT_WINDOW:],
                    )
                except Exception as exc:  # pragma: no cover
                    msg = f"Falha no export: {exc}"
                    events.append(msg)
                    event_history.append(msg)
                last_export = now

            last_sample = now

        draw_dashboard(
            stdscr,
            manager,
            snapshots,
            cpu_hist,
            mem_hist,
            rx_hist,
            tx_hist,
            cpu_now,
            mem_now,
            rx_rate,
            tx_rate,
            events,
            front,
            exporter.status_text(),
            show_help,
            show_logs,
            compact,
        )

        time.sleep(0.05)


def snapshot_once(manager: OpsManager, exporter: ExportWriter) -> int:
    cpu_prev = read_cpu_counters()
    net_prev = read_net_bytes()
    time.sleep(0.2)

    (
        _cpu_curr,
        _net_curr,
        cpu_now,
        mem_now,
        rx_rate,
        tx_rate,
        snapshots,
        front,
    ) = sample_bundle(manager, cpu_prev, net_prev, 0.2)

    timestamp = dt.datetime.now().isoformat(timespec="seconds")

    print(f"timestamp={timestamp}")
    print(f"cpu={cpu_now:.1f}% mem={mem_now[0]:.1f}% ({mem_now[1]:.2f}/{mem_now[2]:.2f} GB)")
    print(f"rx={fmt_rate(rx_rate)} tx={fmt_rate(tx_rate)}")
    for snap in snapshots:
        print(
            f"service={snap.spec.key} state={snap.state} pid={snap.pid or '-'} port={snap.spec.port} "
            f"hits_per_sec={snap.hits_per_sec} uptime={fmt_duration(snap.uptime_seconds)}"
        )
    if front:
        print("frontend_sources=" + ", ".join(f"{ip}:{count}" for ip, count in front.most_common(5)))
    else:
        print("frontend_sources=none")

    if exporter.enabled:
        exporter.write_sample(
            timestamp=timestamp,
            cpu_now=cpu_now,
            mem_now=mem_now,
            rx_rate=rx_rate,
            tx_rate=tx_rate,
            snapshots=snapshots,
            frontend_hits=front,
            events=["snapshot_once"],
        )
        print(exporter.status_text())

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ops Center TUI para gerenciamento e monitoramento do stack")
    parser.add_argument("--once", action="store_true", help="Executa uma coleta unica e sai")
    parser.add_argument("--auto-start", action="store_true", help="Inicia backend/portal/client ao abrir o painel")
    parser.add_argument(
        "--export-json",
        nargs="?",
        const="auto",
        default=None,
        metavar="PATH",
        help="Exporta amostras em JSONL (PATH opcional; sem PATH usa arquivo diario automatico)",
    )
    parser.add_argument(
        "--export-csv",
        nargs="?",
        const="auto",
        default=None,
        metavar="PATH",
        help="Exporta amostras em CSV (PATH opcional; sem PATH usa arquivo diario automatico)",
    )
    parser.add_argument(
        "--export-interval",
        type=float,
        default=5.0,
        help="Intervalo em segundos para export no modo painel (padrao: 5)",
    )
    return parser.parse_args()


def main() -> int:
    root_dir = Path(__file__).resolve().parents[1]
    manager = OpsManager(root_dir)
    args = parse_args()
    exporter = ExportWriter(root_dir, args.export_json, args.export_csv)

    if args.once:
        return snapshot_once(manager, exporter)

    try:
        curses.wrapper(run_dashboard, manager, args.auto_start, exporter, args.export_interval)
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
