#!/usr/bin/env python3
"""Painel operacional do modo producao (EC2)."""

from __future__ import annotations

import curses
import datetime as dt
import os
import re
import shutil
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceSpec:
    key: str
    name: str
    port: int
    start_cmd: str


@dataclass
class ServiceState:
    spec: ServiceSpec
    state: str
    pid: int | None
    uptime: str
    rss_mb: str


SERVICES: tuple[ServiceSpec, ...] = (
    ServiceSpec(
        "backend",
        "Backend Django",
        8000,
        "source '/home/ubuntu/mrquentinha/workspaces/backend/.venv/bin/activate' "
        "&& cd '/home/ubuntu/mrquentinha/workspaces/backend' "
        "&& DJANGO_SETTINGS_MODULE=config.settings.prod DEBUG=False python manage.py migrate --noinput "
        "&& gunicorn config.wsgi:application --chdir '/home/ubuntu/mrquentinha/workspaces/backend/src' "
        "--bind 0.0.0.0:8000 --workers 3 --timeout 120",
    ),
    ServiceSpec(
        "portal",
        "Portal Web",
        3000,
        "cd '/home/ubuntu/mrquentinha/workspaces/web/portal' "
        "&& NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8000' npm run start -- --hostname 0.0.0.0 --port 3000",
    ),
    ServiceSpec(
        "client",
        "Client Web",
        3001,
        "cd '/home/ubuntu/mrquentinha/workspaces/web/client' "
        "&& NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8000' npm run start -- --hostname 0.0.0.0 --port 3001",
    ),
    ServiceSpec(
        "admin",
        "Admin Web",
        3002,
        "cd '/home/ubuntu/mrquentinha/workspaces/web/admin' "
        "&& NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8000' npm run start -- --hostname 0.0.0.0 --port 3002",
    ),
)

DOMAINS = {
    "www": "www.mrquentinha.com.br",
    "app": "app.mrquentinha.com.br",
    "admin": "admin.mrquentinha.com.br",
    "api": "api.mrquentinha.com.br",
}

ROOT = Path("/home/ubuntu/mrquentinha")
PID_DIR = ROOT / ".runtime" / "prod" / "pids"
LOG_DIR = ROOT / ".runtime" / "prod" / "logs"
HAS_SS = shutil.which("ss") is not None


def safe_add(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    text = text[: max(0, w - x - 1)]
    if not text:
        return
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def run_cmd(cmd: list[str] | str, use_shell: bool = False) -> tuple[int, str]:
    proc = subprocess.run(  # noqa: S603
        cmd,
        shell=use_shell,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return proc.returncode, out or err


def run_sudo_systemctl(action: str, unit: str) -> str:
    cmd = ["systemctl", action, unit] if os.geteuid() == 0 else ["sudo", "-n", "systemctl", action, unit]
    code, out = run_cmd(cmd)
    return "ok" if code == 0 else (out or "falha")


def listener_pids(port: int) -> list[int]:
    if not HAS_SS:
        return []
    code, out = run_cmd(["ss", "-ltnp", f"sport = :{port}"])
    if code != 0:
        return []
    pids = sorted({int(match.group(1)) for match in re.finditer(r"pid=(\d+)", out)})
    return pids


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid(key: str) -> int | None:
    path = PID_DIR / f"{key}.pid"
    if not path.exists():
        return None
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None
    if is_running(pid):
        return pid
    try:
        path.unlink()
    except OSError:
        pass
    return None


def write_pid(key: str, pid: int) -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    PID_DIR.joinpath(f"{key}.pid").write_text(str(pid), encoding="utf-8")


def clear_pid(key: str) -> None:
    try:
        PID_DIR.joinpath(f"{key}.pid").unlink()
    except OSError:
        pass


def kill_pid(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    deadline = time.time() + 6
    while time.time() < deadline:
        if not is_running(pid):
            return True
        time.sleep(0.2)
    try:
        os.kill(pid, signal.SIGKILL)
        return True
    except OSError:
        return False


def process_uptime(pid: int | None) -> str:
    if not pid:
        return "-"
    try:
        raw = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8").split()
        start_ticks = int(raw[21])
        uptime_seconds = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
        hz = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        sec = max(0, int(uptime_seconds - (start_ticks / hz)))
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        return "-"


def process_rss(pid: int | None) -> str:
    if not pid:
        return "-"
    try:
        content = (Path("/proc") / str(pid) / "status").read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("VmRSS:"):
                kib = int(line.split()[1])
                return f"{kib / 1024.0:.1f}"
    except Exception:
        return "-"
    return "-"


def start_service(spec: ServiceSpec) -> str:
    managed = read_pid(spec.key)
    if managed:
        return f"{spec.name} ja estava rodando (pid {managed})."
    if listener_pids(spec.port):
        return f"{spec.name} ja possui listener na porta {spec.port}."
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logfile = LOG_DIR / f"{spec.key}.log"
    with logfile.open("ab") as logf:
        proc = subprocess.Popen(  # noqa: S603
            ["bash", "-lc", spec.start_cmd],
            cwd=ROOT,
            stdout=logf,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=os.environ.copy(),
        )
    write_pid(spec.key, proc.pid)
    return f"{spec.name} iniciado (pid {proc.pid})."


def stop_service(spec: ServiceSpec) -> str:
    managed = read_pid(spec.key)
    stopped = False
    if managed:
        stopped = kill_pid(managed) or stopped
        clear_pid(spec.key)
    for pid in listener_pids(spec.port):
        if managed and pid == managed:
            continue
        stopped = kill_pid(pid) or stopped
    return f"{spec.name} parado." if stopped else f"{spec.name} ja estava parado."


def restart_service(spec: ServiceSpec) -> str:
    stop_service(spec)
    time.sleep(0.3)
    return start_service(spec)


def stack_action(action: str) -> str:
    script = ROOT / "scripts" / ("start_vm_prod.sh" if action == "start" else "stop_vm_prod.sh")
    if action == "restart":
        code, out = run_cmd(["bash", str(ROOT / "scripts" / "stop_vm_prod.sh")])
        if code != 0:
            return out or "falha ao parar stack"
        code, out = run_cmd(["bash", str(ROOT / "scripts" / "start_vm_prod.sh")])
        return out or ("stack reiniciada" if code == 0 else "falha ao iniciar stack")
    code, out = run_cmd(["bash", str(script)])
    return out or (f"stack {action}" if code == 0 else f"falha stack {action}")


def service_states() -> list[ServiceState]:
    rows: list[ServiceState] = []
    for spec in SERVICES:
        managed = read_pid(spec.key)
        listeners = listener_pids(spec.port)
        if managed:
            pid = listeners[0] if listeners else managed
            state = "RUNNING"
        elif listeners:
            pid = listeners[0]
            state = "EXTERNAL"
        else:
            pid = None
            state = "STOPPED"
        rows.append(
            ServiceState(
                spec=spec,
                state=state,
                pid=pid,
                uptime=process_uptime(pid),
                rss_mb=process_rss(pid),
            )
        )
    return rows


def public_ip() -> str:
    env_ip = os.environ.get("MRQ_PUBLIC_IP", "").strip()
    if env_ip:
        return env_ip
    code, out = run_cmd(["curl", "-s", "--max-time", "3", "https://checkip.amazonaws.com"])
    if code == 0 and out:
        return out.splitlines()[0].strip()
    return "-"


def domain_status() -> list[tuple[str, str, str, str]]:
    current_public_ip = public_ip()
    rows: list[tuple[str, str, str, str]] = []
    for key, domain in DOMAINS.items():
        try:
            resolved = socket.gethostbyname(domain)
        except Exception:
            resolved = "-"
        code_http, out_http = run_cmd(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "5", f"http://{domain}"]
        )
        code_https, out_https = run_cmd(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "5", f"https://{domain}"]
        )
        http_code = out_http if code_http == 0 else "ERR"
        https_code = out_https if code_https == 0 else "ERR"
        ip_ok = "OK" if current_public_ip != "-" and resolved == current_public_ip else "MISMATCH"
        rows.append((f"{key}:{domain}", resolved, f"http:{http_code} https:{https_code}", ip_ok))
    return rows


def draw(stdscr: curses.window, events: list[str], domain_rows: list[tuple[str, str, str, str]]) -> None:
    stdscr.erase()
    now = dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    safe_add(stdscr, 0, 0, f"Mr Quentinha Ops Center PROD | {now} | q sair", curses.A_BOLD)
    safe_add(
        stdscr,
        1,
        0,
        "Stack: a start all | s stop all | r restart all | Backend 1/2/3 | Portal 4/5/6 | Client 7/8/9 | Admin g/h/j",
    )
    safe_add(stdscr, 2, 0, "Infra: n/m/, nginx start/stop/restart | p/o/i postgres start/stop/restart | d refresh dns")
    safe_add(stdscr, 4, 0, "Servicos", curses.A_BOLD)
    safe_add(stdscr, 5, 0, "Nome            Estado     PID       Porta   Uptime    RSS(MB)")

    y = 6
    for row in service_states():
        color = curses.color_pair(2) if row.state == "RUNNING" else curses.color_pair(3)
        if row.state == "STOPPED":
            color = curses.color_pair(1)
        safe_add(
            stdscr,
            y,
            0,
            f"{row.spec.name[:14]:14}  {row.state:9}  {str(row.pid or '-'):8}  {row.spec.port:5d}   {row.uptime:8}  {row.rss_mb:>7}",
            color,
        )
        y += 1

    y += 1
    safe_add(stdscr, y, 0, "DNS e Subdominios", curses.A_BOLD)
    y += 1
    safe_add(stdscr, y, 0, "Dominio                               Resolve           HTTP/HTTPS                IP")
    y += 1
    for domain, resolved, http_health, ip_ok in domain_rows:
        color = curses.color_pair(2 if ip_ok == "OK" else 3)
        safe_add(stdscr, y, 0, f"{domain[:35]:35}  {resolved[:15]:15}  {http_health[:24]:24}  {ip_ok}", color)
        y += 1

    y += 1
    safe_add(stdscr, y, 0, "Eventos", curses.A_BOLD)
    for event in events[-8:]:
        y += 1
        safe_add(stdscr, y, 0, f"- {event}")

    stdscr.refresh()


def setup_colors() -> None:
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
    except Exception:
        pass


def main_loop(stdscr: curses.window) -> int:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(900)
    setup_colors()

    events: list[str] = []
    domain_rows = domain_status()

    spec_map = {spec.key: spec for spec in SERVICES}
    key_map = {
        ord("1"): ("start", "backend"),
        ord("2"): ("stop", "backend"),
        ord("3"): ("restart", "backend"),
        ord("4"): ("start", "portal"),
        ord("5"): ("stop", "portal"),
        ord("6"): ("restart", "portal"),
        ord("7"): ("start", "client"),
        ord("8"): ("stop", "client"),
        ord("9"): ("restart", "client"),
        ord("g"): ("start", "admin"),
        ord("h"): ("stop", "admin"),
        ord("j"): ("restart", "admin"),
    }

    while True:
        draw(stdscr, events, domain_rows)
        key = stdscr.getch()
        if key == -1:
            continue
        if key in (ord("q"), 27):
            return 0

        if key == ord("d"):
            domain_rows = domain_status()
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} DNS refreshed")
            continue

        if key == ord("a"):
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} {stack_action('start')}")
            continue
        if key == ord("s"):
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} {stack_action('stop')}")
            continue
        if key == ord("r"):
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} {stack_action('restart')}")
            continue

        if key == ord("n"):
            msg = run_sudo_systemctl("start", "nginx.service")
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} nginx start: {msg}")
            continue
        if key == ord("m"):
            msg = run_sudo_systemctl("stop", "nginx.service")
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} nginx stop: {msg}")
            continue
        if key == ord(","):
            msg = run_sudo_systemctl("restart", "nginx.service")
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} nginx restart: {msg}")
            continue

        if key == ord("p"):
            msg = run_sudo_systemctl("start", "postgresql.service")
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} postgres start: {msg}")
            continue
        if key == ord("o"):
            msg = run_sudo_systemctl("stop", "postgresql.service")
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} postgres stop: {msg}")
            continue
        if key == ord("i"):
            msg = run_sudo_systemctl("restart", "postgresql.service")
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} postgres restart: {msg}")
            continue

        if key in key_map:
            action, service_key = key_map[key]
            spec = spec_map[service_key]
            if action == "start":
                msg = start_service(spec)
            elif action == "stop":
                msg = stop_service(spec)
            else:
                msg = restart_service(spec)
            events.append(f"{dt.datetime.now().strftime('%H:%M:%S')} {msg}")


def main() -> int:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    curses.wrapper(main_loop)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
