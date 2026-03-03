#!/usr/bin/env python3
"""GestorServidor - monitoramento e gestao TUI para producao."""

from __future__ import annotations

import argparse
import curses
import json
import time
from dataclasses import dataclass, field
from typing import Callable

from .config import (
    ALERT_COOLDOWN_SECONDS,
    CONNECTION_ALERT_THRESHOLD,
    CPU_ALERT_THRESHOLD,
    DISK_ALERT_THRESHOLD,
    DOMAINS,
    LATENCY_ALERT_THRESHOLD_MS,
    MEMORY_ALERT_THRESHOLD,
    REFRESH_INTERVAL_SECONDS,
)
from .events import append_event, append_metric, path_status, tail_events
from .healthchecks import HealthSnapshot, collect_health_snapshot
from .metrics import HostMetrics, collect_host_metrics, local_ip, public_ip
from .services import ServiceStatus, list_service_status, service_action

SPARK_CHARS = "▁▂▃▄▅▆▇█"
HISTORY_SIZE = 60


@dataclass
class PendingAction:
    key: str
    action: str
    label: str


@dataclass
class ClickButton:
    y: int
    x1: int
    x2: int
    key: str
    action: str
    label: str


@dataclass
class UIState:
    host_metrics: HostMetrics | None = None
    health: HealthSnapshot | None = None
    services: list[ServiceStatus] = field(default_factory=list)
    local_ip: str = "-"
    public_ip: str = "-"
    last_metrics_ts: float = 0.0
    last_health_ts: float = 0.0
    last_services_ts: float = 0.0
    last_ip_refresh_ts: float = 0.0
    events_tail: list[str] = field(default_factory=list)
    pending_action: PendingAction | None = None
    info_message: str = ""
    buttons: list[ClickButton] = field(default_factory=list)
    cpu_hist: list[float] = field(default_factory=list)
    mem_hist: list[float] = field(default_factory=list)
    disk_hist: list[float] = field(default_factory=list)
    rx_hist: list[float] = field(default_factory=list)
    tx_hist: list[float] = field(default_factory=list)
    last_alert_ts: dict[str, float] = field(default_factory=dict)
    show_help: bool = False


def _safe_add(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    if not text:
        return
    text = text[: max(0, w - x - 1)]
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        return


def _init_colors() -> None:
    if not curses.has_colors():
        return
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
    curses.init_pair(7, curses.COLOR_RED, -1)


def _c(index: int) -> int:
    try:
        return curses.color_pair(index)
    except Exception:
        return 0


def _clip(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    return text[: max(0, width - 3)] + "..."


def _fmt_rate(kib_per_s: float) -> str:
    units = ["KiB/s", "MiB/s", "GiB/s"]
    value = max(0.0, float(kib_per_s))
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:6.1f} {unit}"
        value /= 1024.0
    return f"{value:6.1f} GiB/s"


def _percent_bar(value: float, width: int) -> str:
    width = max(4, width)
    pct = max(0.0, min(100.0, value))
    filled = int((pct / 100.0) * width)
    return "#" * filled + "." * (width - filled)


def _sparkline(values: list[float], width: int) -> str:
    if width <= 0:
        return ""
    data = list(values)[-width:]
    if not data:
        return " " * width
    while len(data) < width:
        data.insert(0, 0.0)
    peak = max(data)
    if peak <= 0:
        return "." * width
    out: list[str] = []
    for value in data:
        idx = int((value / peak) * (len(SPARK_CHARS) - 1))
        out.append(SPARK_CHARS[idx])
    return "".join(out)


def _draw_box(stdscr: curses.window, x0: int, y0: int, width: int, height: int, attr: int) -> None:
    if width < 4 or height < 3:
        return
    _safe_add(stdscr, y0, x0, "+" + "-" * (width - 2) + "+", attr)
    for yy in range(1, height - 1):
        _safe_add(stdscr, y0 + yy, x0, "|" + " " * (width - 2) + "|", attr)
    _safe_add(stdscr, y0 + height - 1, x0, "+" + "-" * (width - 2) + "+", attr)


def _register_button(
    stdscr: curses.window,
    state: UIState,
    y: int,
    x: int,
    label: str,
    key: str,
    action: str,
    attr: int,
) -> int:
    display = f"[{label}]"
    _safe_add(stdscr, y, x, display, attr)
    state.buttons.append(ClickButton(y=y, x1=x, x2=x + len(display) - 1, key=key, action=action, label=label))
    return x + len(display) + 1


def _service_state_attr(service_state: str) -> int:
    state = service_state.lower()
    if state == "active":
        return _c(2)
    if state in {"activating", "reloading"}:
        return _c(3)
    return _c(7)


def _refresh_ips(state: UIState) -> None:
    state.local_ip = local_ip()
    state.public_ip = public_ip()


def _execute_pending_action(state: UIState) -> None:
    pending = state.pending_action
    if pending is None:
        return
    ok, msg = service_action(pending.key, pending.action)
    level = "INFO" if ok else "ERROR"
    append_event(level, f"acao={pending.action} alvo={pending.key} resultado={msg}")
    state.info_message = f"{pending.action} {pending.key}: {msg}"
    state.pending_action = None
    state.last_services_ts = 0.0
    state.last_health_ts = 0.0


def _alert_once(state: UIState, now_ts: float, key: str, message: str) -> None:
    last = state.last_alert_ts.get(key, 0.0)
    if now_ts - last < ALERT_COOLDOWN_SECONDS:
        return
    state.last_alert_ts[key] = now_ts
    append_event("WARN", message)


def _evaluate_alerts(state: UIState, now_ts: float) -> None:
    if state.host_metrics is not None:
        m = state.host_metrics
        if m.cpu_percent >= CPU_ALERT_THRESHOLD:
            _alert_once(state, now_ts, "cpu", f"cpu alta: {m.cpu_percent:.1f}%")
        if m.memory_percent >= MEMORY_ALERT_THRESHOLD:
            _alert_once(state, now_ts, "mem", f"memoria alta: {m.memory_percent:.1f}%")
        if m.disk_percent >= DISK_ALERT_THRESHOLD:
            _alert_once(state, now_ts, "disk", f"disco alto: {m.disk_percent:.1f}%")
        if m.tcp_established >= CONNECTION_ALERT_THRESHOLD:
            _alert_once(state, now_ts, "tcp", f"conexoes elevadas: {m.tcp_established}")

    if state.health is not None:
        for endpoint in state.health.endpoints:
            if not endpoint.ok:
                _alert_once(
                    state,
                    now_ts,
                    f"ep-{endpoint.key}",
                    f"endpoint falhou: {endpoint.label} status={endpoint.status_code} detalhe={endpoint.detail}",
                )
            if endpoint.latency_ms >= LATENCY_ALERT_THRESHOLD_MS:
                _alert_once(
                    state,
                    now_ts,
                    f"lat-{endpoint.key}",
                    f"latencia alta: {endpoint.label} {endpoint.latency_ms:.0f}ms",
                )

        for dns_row in state.health.dns_rows:
            if not dns_row.matches_public_ip:
                _alert_once(
                    state,
                    now_ts,
                    f"dns-{dns_row.host}",
                    f"dns divergente: {dns_row.host} -> {dns_row.resolved_ip} (publico {state.public_ip})",
                )

    for svc in state.services:
        if svc.state != "active":
            _alert_once(state, now_ts, f"svc-{svc.key}", f"servico inativo: {svc.label} ({svc.state})")


def _poll_state(state: UIState, now_ts: float, health_interval: float, services_interval: float) -> None:
    if now_ts - state.last_ip_refresh_ts >= 60 or state.last_ip_refresh_ts <= 0:
        _refresh_ips(state)
        state.last_ip_refresh_ts = now_ts

    if now_ts - state.last_metrics_ts >= 1 or state.last_metrics_ts <= 0:
        state.host_metrics = collect_host_metrics(now_ts)
        state.last_metrics_ts = now_ts
        if state.host_metrics is not None:
            m = state.host_metrics
            state.cpu_hist.append(m.cpu_percent)
            state.mem_hist.append(m.memory_percent)
            state.disk_hist.append(m.disk_percent)
            state.rx_hist.append(m.net_rx_kib_s)
            state.tx_hist.append(m.net_tx_kib_s)

            state.cpu_hist = state.cpu_hist[-HISTORY_SIZE:]
            state.mem_hist = state.mem_hist[-HISTORY_SIZE:]
            state.disk_hist = state.disk_hist[-HISTORY_SIZE:]
            state.rx_hist = state.rx_hist[-HISTORY_SIZE:]
            state.tx_hist = state.tx_hist[-HISTORY_SIZE:]

    if now_ts - state.last_services_ts >= services_interval or state.last_services_ts <= 0:
        state.services = list_service_status()
        state.last_services_ts = now_ts

    if now_ts - state.last_health_ts >= health_interval or state.last_health_ts <= 0:
        state.health = collect_health_snapshot(state.local_ip, state.public_ip, DOMAINS)
        state.last_health_ts = now_ts
        state.events_tail = tail_events(12)

        if state.host_metrics is not None:
            payload = {
                "local_ip": state.local_ip,
                "public_ip": state.public_ip,
                "cpu": state.host_metrics.cpu_percent,
                "mem": state.host_metrics.memory_percent,
                "disk": state.host_metrics.disk_percent,
                "tcp_established": state.host_metrics.tcp_established,
                "rx_kib_s": state.host_metrics.net_rx_kib_s,
                "tx_kib_s": state.host_metrics.net_tx_kib_s,
                "services_active": sum(1 for svc in state.services if svc.state == "active"),
                "services_total": len(state.services),
                "endpoint_ok": sum(1 for ep in state.health.endpoints if ep.ok),
                "endpoint_total": len(state.health.endpoints),
            }
            append_metric(payload)

    _evaluate_alerts(state, now_ts)


def _draw_header(stdscr: curses.window, state: UIState, now_ts: float) -> None:
    h, w = stdscr.getmaxyx()
    title = (
        f"Mr Quentinha GestorServidor | {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(now_ts))} "
        "| q sair"
    )
    _safe_add(stdscr, 0, 0, _clip(title, w - 1), curses.A_BOLD | _c(4))

    action_line = (
        "Acoes: [z] start stack [x] stop stack [k] restart stack "
        "| [1..7] restart rapido | [r] refresh | [?] ajuda | mouse clique"
    )
    _safe_add(stdscr, 1, 0, _clip(action_line, w - 1), _c(6))

    host_line = f"Host local={state.local_ip} publico={state.public_ip}"
    _safe_add(stdscr, 2, 0, _clip(host_line, w - 1), _c(5))

    x = 0
    for svc in state.services:
        state_txt = "ACT" if svc.state == "active" else svc.state[:3].upper()
        label = f"[{svc.key}:{state_txt}] "
        _safe_add(stdscr, 3, x, label, _service_state_attr(svc.state))
        x += len(label)


def _draw_system_and_network(stdscr: curses.window, state: UIState, y: int) -> int:
    h, w = stdscr.getmaxyx()
    m = state.host_metrics
    if m is None:
        _safe_add(stdscr, y, 0, "Coletando metricas de host...", _c(3))
        return y + 2

    bar_w = max(10, min(34, w // 4))

    _safe_add(stdscr, y, 0, "Sistema", curses.A_BOLD | _c(4))
    y += 1

    cpu_color = _c(2) if m.cpu_percent < 70 else _c(3)
    mem_color = _c(2) if m.memory_percent < 80 else _c(3)
    dsk_color = _c(2) if m.disk_percent < 85 else _c(3)

    _safe_add(
        stdscr,
        y,
        0,
        _clip(
            f"CPU {m.cpu_percent:5.1f}% [{_percent_bar(m.cpu_percent, bar_w)}] hist {_sparkline(state.cpu_hist, min(28, w - 54))}",
            w - 1,
        ),
        cpu_color,
    )
    y += 1

    _safe_add(
        stdscr,
        y,
        0,
        _clip(
            f"MEM {m.memory_percent:5.1f}% [{_percent_bar(m.memory_percent, bar_w)}] {m.mem_used_gib:4.2f}/{m.mem_total_gib:4.2f} GiB hist {_sparkline(state.mem_hist, min(24, w - 66))}",
            w - 1,
        ),
        mem_color,
    )
    y += 1

    _safe_add(
        stdscr,
        y,
        0,
        _clip(
            f"DSK {m.disk_percent:5.1f}% [{_percent_bar(m.disk_percent, bar_w)}] {m.disk_used_gib:4.2f}/{m.disk_total_gib:4.2f} GiB hist {_sparkline(state.disk_hist, min(24, w - 66))}",
            w - 1,
        ),
        dsk_color,
    )
    y += 1

    _safe_add(stdscr, y, 0, _clip(f"Load {m.load_1m:.2f} {m.load_5m:.2f} {m.load_15m:.2f} | TCP EST {m.tcp_established}", w - 1), _c(6))
    y += 2

    _safe_add(stdscr, y, 0, "Rede", curses.A_BOLD | _c(4))
    y += 1

    _safe_add(
        stdscr,
        y,
        0,
        _clip(f"RX {_fmt_rate(m.net_rx_kib_s)} {_sparkline(state.rx_hist, min(36, w - 20))}", w - 1),
        _c(2),
    )
    y += 1

    _safe_add(
        stdscr,
        y,
        0,
        _clip(f"TX {_fmt_rate(m.net_tx_kib_s)} {_sparkline(state.tx_hist, min(36, w - 20))}", w - 1),
        _c(5),
    )
    y += 2

    return y


def _draw_services_box(stdscr: curses.window, state: UIState, x0: int, y0: int, width: int, height: int) -> int:
    _draw_box(stdscr, x0, y0, width, height, _c(4))
    _safe_add(stdscr, y0, x0 + 2, " Servicos ", curses.A_BOLD | _c(4))

    row = y0 + 1
    for svc in state.services:
        if row >= y0 + height - 2:
            break
        _safe_add(stdscr, row, x0 + 2, _clip(f"{svc.label[:12]:12} {svc.state[:10]:10}", width - 24), _service_state_attr(svc.state))

        bx = x0 + width - 21
        bx = _register_button(stdscr, state, row, bx, "Start", svc.key, "start", _c(2))
        bx = _register_button(stdscr, state, row, bx + 1, "Stop", svc.key, "stop", _c(3))
        _register_button(stdscr, state, row, bx + 1, "Rst", svc.key, "restart", _c(6))
        row += 1

    if row < y0 + height - 1:
        _safe_add(stdscr, row, x0 + 2, "Stack mrq-*", curses.A_BOLD | _c(4))
        bx = x0 + width - 21
        bx = _register_button(stdscr, state, row, bx, "Start", "stack", "start", _c(2))
        bx = _register_button(stdscr, state, row, bx + 1, "Stop", "stack", "stop", _c(3))
        _register_button(stdscr, state, row, bx + 1, "Rst", "stack", "restart", _c(6))
        row += 1

    return row


def _draw_health_box(stdscr: curses.window, state: UIState, x0: int, y0: int, width: int, height: int) -> None:
    _draw_box(stdscr, x0, y0, width, height, _c(4))
    _safe_add(stdscr, y0, x0 + 2, " Dominios / API ", curses.A_BOLD | _c(4))

    row = y0 + 1
    health = state.health
    if health is None:
        _safe_add(stdscr, row, x0 + 2, "Coletando healthchecks...", _c(3))
        return

    _safe_add(stdscr, row, x0 + 2, "Endpoints", curses.A_BOLD | _c(4))
    row += 1
    for endpoint in health.endpoints:
        if row >= y0 + height - 4:
            break
        status = str(endpoint.status_code) if endpoint.status_code else "ERR"
        text = f"{endpoint.key[:11]:11} {status:>3} {endpoint.latency_ms:>4.0f}ms"
        attr = _c(2) if endpoint.ok else _c(7)
        _safe_add(stdscr, row, x0 + 2, _clip(text, width - 4), attr)
        row += 1

    if row < y0 + height - 3:
        row += 1
        _safe_add(stdscr, row, x0 + 2, "DNS", curses.A_BOLD | _c(4))
        row += 1

    dns_errors = 0
    for dns_row in health.dns_rows:
        if row >= y0 + height - 1:
            break
        ok = dns_row.matches_public_ip
        if not ok:
            dns_errors += 1
        _safe_add(
            stdscr,
            row,
            x0 + 2,
            _clip(f"{dns_row.host[:14]:14} -> {dns_row.resolved_ip}", width - 4),
            _c(2) if ok else _c(7),
        )
        row += 1

    _safe_add(stdscr, y0 + height - 2, x0 + 2, f"dns mismatch: {dns_errors}", _c(2) if dns_errors == 0 else _c(7))


def _draw_events_footer(stdscr: curses.window, state: UIState) -> None:
    h, w = stdscr.getmaxyx()
    footer_y = h - 3
    _safe_add(stdscr, footer_y, 0, "Eventos recentes:", curses.A_BOLD | _c(4))
    line = " | ".join(state.events_tail[-4:]) if state.events_tail else "(sem eventos)"
    _safe_add(stdscr, footer_y + 1, 0, _clip(line, w - 1), _c(6))
    _safe_add(stdscr, footer_y + 2, 0, _clip(state.info_message, w - 1), curses.A_BOLD | _c(5))


def _draw_paths(stdscr: curses.window) -> None:
    h, w = stdscr.getmaxyx()
    paths = path_status()
    info = f"logs: {paths['events_log']} | metrics: {paths['metrics_log']}"
    _safe_add(stdscr, h - 5, 0, _clip(info, w - 1), _c(1))


def _draw_help_modal(stdscr: curses.window) -> None:
    h, w = stdscr.getmaxyx()
    lines = [
        "Ajuda de operacao",
        "q: sair",
        "r: refresh manual",
        "z/x/k: start/stop/restart da stack mrq-*",
        "1..7: restart rapido nginx,postgres,ssh,backend,portal,client,admin",
        "mouse: clique em [Start] [Stop] [Rst]",
        "?: abre/fecha esta ajuda",
    ]
    bw = min(max(len(line) for line in lines) + 4, w - 4)
    bh = min(len(lines) + 2, h - 4)
    by = max(2, (h - bh) // 2)
    bx = max(2, (w - bw) // 2)

    for yy in range(bh):
        _safe_add(stdscr, by + yy, bx, " " * bw, _c(4))
    _safe_add(stdscr, by, bx + 2, lines[0], curses.A_BOLD | _c(1))
    for idx, line in enumerate(lines[1 : bh - 1]):
        _safe_add(stdscr, by + 1 + idx, bx + 2, _clip(line, bw - 4), _c(6))


def _draw_confirm_modal(stdscr: curses.window, pending: PendingAction) -> None:
    h, w = stdscr.getmaxyx()
    mh = 7
    mw = min(72, max(40, w - 6))
    y = (h - mh) // 2
    x = (w - mw) // 2

    for row in range(y - 1, y + mh + 1):
        _safe_add(stdscr, row, x - 1, " " * (mw + 2), curses.A_REVERSE)

    _draw_box(stdscr, x, y, mw, mh, _c(4))
    _safe_add(stdscr, y, x + 2, " Confirmacao ", curses.A_BOLD | _c(1))
    _safe_add(stdscr, y + 2, x + 2, _clip(f"Executar '{pending.action}' em '{pending.key}'?", mw - 4), _c(1))
    _safe_add(stdscr, y + 4, x + 2, "y confirmar | n cancelar | ESC cancelar", curses.A_BOLD | _c(6))


def _find_button(state: UIState, y: int, x: int) -> ClickButton | None:
    for btn in state.buttons:
        if btn.y == y and btn.x1 <= x <= btn.x2:
            return btn
    return None


def _handle_keypress(state: UIState, key: int) -> bool:
    if state.pending_action is not None:
        if key in (ord("y"), ord("Y")):
            _execute_pending_action(state)
            return True
        if key in (ord("n"), ord("N"), 27):
            state.pending_action = None
            state.info_message = "acao cancelada"
            return True
        return True

    if key in (ord("q"), ord("Q")):
        return False
    if key in (ord("r"), ord("R")):
        state.last_health_ts = 0.0
        state.last_services_ts = 0.0
        state.last_metrics_ts = 0.0
        state.info_message = "refresh manual"
        return True
    if key == ord("?"):
        state.show_help = not state.show_help
        return True

    hotkeys: dict[int, tuple[str, str]] = {
        ord("z"): ("stack", "start"),
        ord("x"): ("stack", "stop"),
        ord("k"): ("stack", "restart"),
        ord("1"): ("nginx", "restart"),
        ord("2"): ("postgres", "restart"),
        ord("3"): ("ssh", "restart"),
        ord("4"): ("backend", "restart"),
        ord("5"): ("portal", "restart"),
        ord("6"): ("client", "restart"),
        ord("7"): ("admin", "restart"),
    }
    if key in hotkeys:
        target, action = hotkeys[key]
        state.pending_action = PendingAction(key=target, action=action, label=target)
        return True

    if key == curses.KEY_MOUSE:
        try:
            _, mx, my, _, _ = curses.getmouse()
        except curses.error:
            return True
        btn = _find_button(state, my, mx)
        if btn is not None:
            state.pending_action = PendingAction(key=btn.key, action=btn.action, label=btn.label)
        return True

    return True


def _render(stdscr: curses.window, state: UIState, now_ts: float) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if h < 32 or w < 120:
        _safe_add(stdscr, 1, 1, f"Terminal muito pequeno ({w}x{h}). Minimo recomendado: 120x32", curses.A_BOLD | _c(7))
        _safe_add(stdscr, 3, 1, "Aumente o terminal e pressione 'r'.", _c(1))
        _safe_add(stdscr, 4, 1, "Pressione 'q' para sair.", _c(1))
        stdscr.refresh()
        return

    state.buttons = []
    _draw_header(stdscr, state, now_ts)

    y = _draw_system_and_network(stdscr, state, 5)

    boxes_y = y
    boxes_h = max(10, h - boxes_y - 8)
    left_w = max(48, (w // 2) - 2)
    right_w = max(48, w - left_w - 3)

    _draw_services_box(stdscr, state, 0, boxes_y, left_w, boxes_h)
    _draw_health_box(stdscr, state, left_w + 1, boxes_y, right_w, boxes_h)

    _draw_paths(stdscr)
    _draw_events_footer(stdscr, state)

    if state.show_help:
        _draw_help_modal(stdscr)
    if state.pending_action is not None:
        _draw_confirm_modal(stdscr, state.pending_action)

    stdscr.refresh()


def _run_once() -> int:
    now_ts = time.time()
    ip_local = local_ip()
    ip_public = public_ip()
    host = collect_host_metrics(now_ts)
    services = list_service_status()
    health = collect_health_snapshot(ip_local, ip_public, DOMAINS)
    payload = {
        "local_ip": ip_local,
        "public_ip": ip_public,
        "host": host.__dict__,
        "services": [svc.__dict__ for svc in services],
        "health": {
            "endpoints": [row.__dict__ for row in health.endpoints],
            "dns_rows": [row.__dict__ for row in health.dns_rows],
        },
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def _run_tui(stdscr: curses.window, refresh_interval: float, health_interval: float, services_interval: float, mouse: bool) -> int:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.keypad(True)
    _init_colors()

    if mouse:
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS)
            curses.mouseinterval(0)
        except curses.error:
            pass

    state = UIState(info_message="inicializando...")
    append_event("INFO", "GestorServidor iniciado")

    running = True
    while running:
        now_ts = time.time()
        _poll_state(state, now_ts, health_interval, services_interval)
        _render(stdscr, state, now_ts)

        loop_deadline = time.time() + refresh_interval
        while time.time() < loop_deadline:
            key = stdscr.getch()
            if key != -1:
                running = _handle_keypress(state, key)
                if not running:
                    break
                _render(stdscr, state, time.time())
            time.sleep(0.05)

    append_event("INFO", "GestorServidor finalizado")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GestorServidor - monitoramento e gestao da producao")
    parser.add_argument("--once", action="store_true", help="executa coleta unica e sai (json)")
    parser.add_argument(
        "--refresh-interval",
        type=float,
        default=REFRESH_INTERVAL_SECONDS,
        help=f"intervalo de redraw da UI (padrao: {REFRESH_INTERVAL_SECONDS}s)",
    )
    parser.add_argument(
        "--health-interval",
        type=float,
        default=8.0,
        help="intervalo de healthchecks HTTP/DNS em segundos (padrao: 8)",
    )
    parser.add_argument(
        "--services-interval",
        type=float,
        default=4.0,
        help="intervalo de consulta systemctl em segundos (padrao: 4)",
    )
    parser.add_argument("--no-mouse", action="store_true", help="desabilita mouse na TUI")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.once:
        return _run_once()

    refresh_interval = max(0.2, float(args.refresh_interval))
    health_interval = max(3.0, float(args.health_interval))
    services_interval = max(2.0, float(args.services_interval))

    wrapper: Callable[..., int] = curses.wrapper
    return wrapper(
        _run_tui,
        refresh_interval,
        health_interval,
        services_interval,
        not args.no_mouse,
    )


if __name__ == "__main__":
    raise SystemExit(main())
