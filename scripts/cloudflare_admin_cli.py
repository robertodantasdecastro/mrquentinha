#!/usr/bin/env python3
"""CLI de operacao do Cloudflare via Portal CMS (Web Admin API).

Este script usa os mesmos endpoints da tela do Web Admin para:
- ativar/desativar Cloudflare em DEV ou PRODUCAO;
- iniciar/parar/status do runtime;
- sincronizar URLs de API nos frontends web.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

FRONTEND_ENV_TARGETS: dict[str, list[str]] = {
    "workspaces/web/admin/.env.local": [
        "NEXT_PUBLIC_API_BASE_URL",
        "ADMIN_API_BASE_URL",
        "INTERNAL_API_BASE_URL",
    ],
    "workspaces/web/client/.env.local": [
        "NEXT_PUBLIC_API_BASE_URL",
        "CLIENT_API_BASE_URL",
        "INTERNAL_API_BASE_URL",
    ],
    "workspaces/web/portal/.env.local": [
        "NEXT_PUBLIC_API_BASE_URL",
        "PORTAL_API_BASE_URL",
        "INTERNAL_API_BASE_URL",
    ],
}


class CliError(RuntimeError):
    """Erro esperado da CLI com mensagem amigavel."""


def _normalize_url(value: str) -> str:
    return value.strip().rstrip("/")


def _bool_from_env(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _extract_payload_or_raise(raw: bytes, status_code: int) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text) if text else {}
    except json.JSONDecodeError:
        if 200 <= status_code < 300:
            return {}
        raise CliError(
            f"Resposta invalida da API (HTTP {status_code}): {text[:240]}"
        ) from None

    if 200 <= status_code < 300:
        if isinstance(payload, dict):
            return payload
        raise CliError("API retornou JSON invalido: objeto esperado.")

    detail = ""
    if isinstance(payload, dict):
        if isinstance(payload.get("detail"), str):
            detail = payload["detail"]
        elif isinstance(payload.get("non_field_errors"), list):
            detail = " | ".join(str(item) for item in payload["non_field_errors"])
        else:
            detail = json.dumps(payload, ensure_ascii=False)
    elif payload:
        detail = str(payload)

    raise CliError(f"Falha na API (HTTP {status_code}): {detail or 'sem detalhe'}")


class PortalAdminApiClient:
    """Cliente HTTP minimalista para endpoints admin do Portal CMS."""

    def __init__(
        self,
        *,
        api_base_url: str,
        access_token: str | None,
        admin_user: str | None,
        admin_password: str | None,
    ) -> None:
        self.api_base_url = _normalize_url(api_base_url)
        self.access_token = access_token.strip() if access_token else ""
        self.admin_user = admin_user.strip() if admin_user else ""
        self.admin_password = admin_password or ""

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.api_base_url}{path}"
        data_bytes: bytes | None = None

        headers = {
            "Accept": "application/json",
        }
        if payload is not None:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if auth:
            token = self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"

        request = urllib.request.Request(
            url=url,
            data=data_bytes,
            headers=headers,
            method=method.upper(),
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
                return _extract_payload_or_raise(raw, response.getcode())
        except urllib.error.HTTPError as exc:
            raw = exc.read() if exc.fp is not None else b""
            return _extract_payload_or_raise(raw, exc.code)
        except urllib.error.URLError as exc:
            raise CliError(f"Falha de conexao com API '{url}': {exc.reason}") from exc

    def _get_access_token(self) -> str:
        if self.access_token:
            return self.access_token

        if not self.admin_user or not self.admin_password:
            raise CliError(
                "Defina MQ_ADMIN_ACCESS_TOKEN ou (MQ_ADMIN_USER + MQ_ADMIN_PASSWORD)."
            )

        token_payload = self._request(
            method="POST",
            path="/api/v1/accounts/token/",
            payload={
                "username": self.admin_user,
                "password": self.admin_password,
            },
            auth=False,
        )
        access = str(token_payload.get("access", "")).strip()
        if not access:
            raise CliError("Login admin sem token 'access'.")
        self.access_token = access
        return access

    def get_admin_config(self) -> dict[str, Any]:
        payload = self._request(
            method="GET",
            path="/api/v1/portal/admin/config/",
            auth=True,
        )
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            results = payload["results"]
            if results:
                first = results[0]
                if isinstance(first, dict):
                    return first
        if isinstance(payload, list):
            if payload and isinstance(payload[0], dict):
                return payload[0]
        if isinstance(payload, dict) and payload:
            return payload
        raise CliError("Nenhuma configuracao de portal retornada pela API admin.")

    def cloudflare_toggle(
        self, *, enabled: bool, settings: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/api/v1/portal/admin/config/cloudflare-toggle/",
            payload={
                "enabled": enabled,
                "settings": settings,
            },
            auth=True,
        )

    def cloudflare_runtime(self, *, action: str) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/api/v1/portal/admin/config/cloudflare-runtime/",
            payload={
                "action": action,
            },
            auth=True,
        )

    def cloudflare_preview(self, *, settings: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/api/v1/portal/admin/config/cloudflare-preview/",
            payload={"settings": settings},
            auth=True,
        )

    def fetch_public_portal_config(self) -> dict[str, Any]:
        query = urllib.parse.urlencode(
            {
                "channel": "portal",
                "page": "home",
            }
        )
        return self._request(
            method="GET",
            path=f"/api/v1/portal/config/?{query}",
            auth=False,
        )


def _upsert_env_key(file_path: Path, *, key: str, value: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    if file_path.exists():
        lines = file_path.read_text(encoding="utf-8").splitlines()

    target_prefix = f"{key}="
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith(target_prefix):
            lines[index] = f"{key}={value}"
            replaced = True
            break

    if not replaced:
        lines.append(f"{key}={value}")

    file_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _resolve_cloudflare_api_url_from_public_config(
    public_config: dict[str, Any],
) -> str:
    cloudflare = public_config.get("cloudflare")
    if isinstance(cloudflare, dict):
        if cloudflare.get("enabled") and cloudflare.get("dev_mode"):
            dev_urls = cloudflare.get("dev_urls")
            if isinstance(dev_urls, dict):
                dev_api = str(dev_urls.get("api", "")).strip().rstrip("/")
                if dev_api:
                    return dev_api

    api_base_url = str(public_config.get("api_base_url", "")).strip().rstrip("/")
    return api_base_url


def sync_frontend_api_envs(
    *,
    public_config: dict[str, Any],
    forced_api_url: str | None = None,
) -> tuple[str, list[str]]:
    api_url = _normalize_url(forced_api_url) if forced_api_url else ""
    if not api_url:
        api_url = _resolve_cloudflare_api_url_from_public_config(public_config)

    if not api_url:
        raise CliError("Nao foi possivel resolver a URL base da API para sincronizacao.")

    changed_files: list[str] = []
    for relative_path, keys in FRONTEND_ENV_TARGETS.items():
        target_file = ROOT_DIR / relative_path
        for key in keys:
            _upsert_env_key(target_file, key=key, value=api_url)
        changed_files.append(str(target_file))

    runtime_env_file = ROOT_DIR / ".runtime" / "ops" / "frontend_api_base_url.env"
    runtime_env_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_env_file.write_text(
        (
            "# Arquivo gerado por scripts/cloudflare_admin_cli.py\n"
            f"NEXT_PUBLIC_API_BASE_URL={api_url}\n"
        ),
        encoding="utf-8",
    )
    changed_files.append(str(runtime_env_file))
    return api_url, changed_files


def _runtime_to_lines(runtime_payload: dict[str, Any]) -> list[str]:
    lines = [
        f"state={runtime_payload.get('state', '-')}",
        f"pid={runtime_payload.get('pid', '-')}",
        f"log={runtime_payload.get('log_file', '-')}",
    ]
    if runtime_payload.get("run_command"):
        lines.append(f"run_command={runtime_payload.get('run_command')}")

    if runtime_payload.get("dev_mode") and isinstance(
        runtime_payload.get("dev_urls"), dict
    ):
        dev_urls = runtime_payload["dev_urls"]
        lines.append(f"dev.portal={dev_urls.get('portal', '-')}")
        lines.append(f"dev.client={dev_urls.get('client', '-')}")
        lines.append(f"dev.admin={dev_urls.get('admin', '-')}")
        lines.append(f"dev.api={dev_urls.get('api', '-')}")
    return lines


def _cloudflare_settings_summary(config: dict[str, Any]) -> list[str]:
    settings = config.get("cloudflare_settings")
    if not isinstance(settings, dict):
        return ["cloudflare_settings: indisponivel"]

    return [
        f"enabled={settings.get('enabled')}",
        f"mode={settings.get('mode')}",
        f"dev_mode={settings.get('dev_mode')}",
        f"auto_apply_routes={settings.get('auto_apply_routes')}",
        f"api_base_url={config.get('api_base_url', '-')}",
    ]


def _build_dev_settings(mode: str, auto_apply_routes: bool) -> dict[str, Any]:
    return {
        "dev_mode": True,
        "mode": mode,
        "auto_apply_routes": auto_apply_routes,
    }


def _build_prod_settings(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "dev_mode": False,
        "mode": args.mode,
        "scheme": args.scheme,
        "root_domain": args.root_domain,
        "subdomains": {
            "portal": args.portal_subdomain,
            "client": args.client_subdomain,
            "admin": args.admin_subdomain,
            "api": args.api_subdomain,
        },
        "tunnel_name": args.tunnel_name,
        "tunnel_id": args.tunnel_id,
        "tunnel_token": args.tunnel_token,
        "account_id": args.account_id,
        "zone_id": args.zone_id,
        "api_token": args.api_token,
        "auto_apply_routes": args.auto_apply_routes,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Operacao Cloudflare (DEV/PROD) via API admin do Portal CMS."
    )
    parser.add_argument(
        "--api-base-url",
        default=os.environ.get("MQ_API_BASE_URL", "http://127.0.0.1:8000"),
        help="Base da API backend (padrao: %(default)s).",
    )
    parser.add_argument(
        "--admin-user",
        default=os.environ.get("MQ_ADMIN_USER", ""),
        help="Usuario admin para login JWT.",
    )
    parser.add_argument(
        "--admin-password",
        default=os.environ.get("MQ_ADMIN_PASSWORD", ""),
        help="Senha admin para login JWT.",
    )
    parser.add_argument(
        "--access-token",
        default=os.environ.get("MQ_ADMIN_ACCESS_TOKEN", ""),
        help="Token JWT de acesso (opcional).",
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Nao sincronizar .env.local dos frontends apos operacao.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Exibe status de configuracao e runtime.")
    subparsers.add_parser(
        "sync-frontends",
        help="Sincroniza .env.local dos frontends com a URL atual da API.",
    )

    dev_up = subparsers.add_parser(
        "dev-up",
        help="Ativa Cloudflare em modo DEV (trycloudflare) e inicia runtime.",
    )
    dev_up.add_argument(
        "--mode",
        default=os.environ.get("MQ_CF_DEV_MODE", "hybrid"),
        choices=["local_only", "hybrid", "cloudflare_only"],
        help="Modo de coexistencia para DEV.",
    )
    dev_up.add_argument(
        "--auto-apply-routes",
        action=argparse.BooleanOptionalAction,
        default=_bool_from_env("MQ_CF_AUTO_APPLY_ROUTES", default=True),
        help="Ativa auto atualizacao de URLs/CORS no backend.",
    )

    dev_refresh = subparsers.add_parser(
        "dev-refresh",
        help="Reinicia runtime DEV para gerar novas URLs trycloudflare.",
    )
    dev_refresh.add_argument(
        "--mode",
        default=os.environ.get("MQ_CF_DEV_MODE", "hybrid"),
        choices=["local_only", "hybrid", "cloudflare_only"],
    )
    dev_refresh.add_argument(
        "--auto-apply-routes",
        action=argparse.BooleanOptionalAction,
        default=_bool_from_env("MQ_CF_AUTO_APPLY_ROUTES", default=True),
    )

    subparsers.add_parser(
        "dev-down",
        help="Para runtime e desativa Cloudflare (volta para local).",
    )

    prod_up = subparsers.add_parser(
        "prod-up",
        help="Ativa Cloudflare em modo operacional (dominio oficial) e inicia runtime.",
    )
    prod_up.add_argument(
        "--mode",
        default=os.environ.get("MQ_CF_PROD_MODE", "cloudflare_only"),
        choices=["local_only", "hybrid", "cloudflare_only"],
        help="Modo de coexistencia em producao.",
    )
    prod_up.add_argument(
        "--scheme",
        default=os.environ.get("MQ_CF_SCHEME", "https"),
        choices=["http", "https"],
    )
    prod_up.add_argument(
        "--root-domain",
        default=os.environ.get("MQ_CF_ROOT_DOMAIN", "mrquentinha.com.br"),
    )
    prod_up.add_argument(
        "--portal-subdomain",
        default=os.environ.get("MQ_CF_PORTAL_SUBDOMAIN", "www"),
    )
    prod_up.add_argument(
        "--client-subdomain",
        default=os.environ.get("MQ_CF_CLIENT_SUBDOMAIN", "app"),
    )
    prod_up.add_argument(
        "--admin-subdomain",
        default=os.environ.get("MQ_CF_ADMIN_SUBDOMAIN", "admin"),
    )
    prod_up.add_argument(
        "--api-subdomain",
        default=os.environ.get("MQ_CF_API_SUBDOMAIN", "api"),
    )
    prod_up.add_argument(
        "--tunnel-name",
        default=os.environ.get("MQ_CF_TUNNEL_NAME", "mrquentinha"),
    )
    prod_up.add_argument(
        "--tunnel-id",
        default=os.environ.get("MQ_CF_TUNNEL_ID", ""),
    )
    prod_up.add_argument(
        "--tunnel-token",
        default=os.environ.get("MQ_CF_TUNNEL_TOKEN", ""),
    )
    prod_up.add_argument(
        "--account-id",
        default=os.environ.get("MQ_CF_ACCOUNT_ID", ""),
    )
    prod_up.add_argument(
        "--zone-id",
        default=os.environ.get("MQ_CF_ZONE_ID", ""),
    )
    prod_up.add_argument(
        "--api-token",
        default=os.environ.get("MQ_CF_API_TOKEN", ""),
    )
    prod_up.add_argument(
        "--auto-apply-routes",
        action=argparse.BooleanOptionalAction,
        default=_bool_from_env("MQ_CF_AUTO_APPLY_ROUTES", default=True),
    )
    prod_up.add_argument(
        "--skip-runtime-start",
        action="store_true",
        help="Nao iniciar runtime automaticamente apos ativar Cloudflare.",
    )

    subparsers.add_parser(
        "prod-refresh",
        help="Reinicia runtime do modo operacional.",
    )
    subparsers.add_parser(
        "prod-down",
        help="Para runtime e desativa Cloudflare (volta para local).",
    )

    preview_prod = subparsers.add_parser(
        "preview-prod",
        help="Mostra preview de rotas para dominio oficial sem ativar.",
    )
    preview_prod.add_argument(
        "--mode",
        default=os.environ.get("MQ_CF_PROD_MODE", "cloudflare_only"),
        choices=["local_only", "hybrid", "cloudflare_only"],
    )
    preview_prod.add_argument(
        "--scheme",
        default=os.environ.get("MQ_CF_SCHEME", "https"),
        choices=["http", "https"],
    )
    preview_prod.add_argument(
        "--root-domain",
        default=os.environ.get("MQ_CF_ROOT_DOMAIN", "mrquentinha.com.br"),
    )
    preview_prod.add_argument(
        "--portal-subdomain",
        default=os.environ.get("MQ_CF_PORTAL_SUBDOMAIN", "www"),
    )
    preview_prod.add_argument(
        "--client-subdomain",
        default=os.environ.get("MQ_CF_CLIENT_SUBDOMAIN", "app"),
    )
    preview_prod.add_argument(
        "--admin-subdomain",
        default=os.environ.get("MQ_CF_ADMIN_SUBDOMAIN", "admin"),
    )
    preview_prod.add_argument(
        "--api-subdomain",
        default=os.environ.get("MQ_CF_API_SUBDOMAIN", "api"),
    )
    preview_prod.add_argument(
        "--tunnel-name",
        default=os.environ.get("MQ_CF_TUNNEL_NAME", "mrquentinha"),
    )
    preview_prod.add_argument(
        "--tunnel-id",
        default=os.environ.get("MQ_CF_TUNNEL_ID", ""),
    )
    preview_prod.add_argument(
        "--tunnel-token",
        default=os.environ.get("MQ_CF_TUNNEL_TOKEN", ""),
    )
    preview_prod.add_argument(
        "--account-id",
        default=os.environ.get("MQ_CF_ACCOUNT_ID", ""),
    )
    preview_prod.add_argument(
        "--zone-id",
        default=os.environ.get("MQ_CF_ZONE_ID", ""),
    )
    preview_prod.add_argument(
        "--api-token",
        default=os.environ.get("MQ_CF_API_TOKEN", ""),
    )
    preview_prod.add_argument(
        "--auto-apply-routes",
        action=argparse.BooleanOptionalAction,
        default=_bool_from_env("MQ_CF_AUTO_APPLY_ROUTES", default=True),
    )

    return parser


def _print_sync_result(api_url: str, files: list[str]) -> None:
    print(f"[sync] NEXT_PUBLIC_API_BASE_URL={api_url}")
    for file_path in files:
        print(f"[sync] atualizado: {file_path}")
    print("[sync] Reinicie os frontends web para carregar as novas variaveis.")


def _sync_if_requested(
    *,
    args: argparse.Namespace,
    client: PortalAdminApiClient,
) -> None:
    if args.no_sync:
        return

    public_config = client.fetch_public_portal_config()
    api_url, files = sync_frontend_api_envs(public_config=public_config)
    _print_sync_result(api_url, files)


def _run() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    client = PortalAdminApiClient(
        api_base_url=args.api_base_url,
        access_token=args.access_token,
        admin_user=args.admin_user,
        admin_password=args.admin_password,
    )

    if args.command == "sync-frontends":
        public_config = client.fetch_public_portal_config()
        api_url, files = sync_frontend_api_envs(public_config=public_config)
        _print_sync_result(api_url, files)
        return 0

    if args.command == "status":
        config = client.get_admin_config()
        runtime = client.cloudflare_runtime(action="status")
        print("[status] configuracao:")
        for line in _cloudflare_settings_summary(config):
            print(f"  - {line}")
        print("[status] runtime:")
        runtime_payload = runtime.get("runtime", {})
        if isinstance(runtime_payload, dict):
            for line in _runtime_to_lines(runtime_payload):
                print(f"  - {line}")
        return 0

    if args.command == "dev-up":
        settings = _build_dev_settings(args.mode, args.auto_apply_routes)
        client.cloudflare_toggle(enabled=True, settings=settings)
        runtime = client.cloudflare_runtime(action="start")
        print("[dev-up] Cloudflare DEV ativo.")
        runtime_payload = runtime.get("runtime", {})
        if isinstance(runtime_payload, dict):
            for line in _runtime_to_lines(runtime_payload):
                print(f"  - {line}")
        _sync_if_requested(args=args, client=client)
        return 0

    if args.command == "dev-refresh":
        settings = _build_dev_settings(args.mode, args.auto_apply_routes)
        client.cloudflare_toggle(enabled=True, settings=settings)
        runtime = client.cloudflare_runtime(action="refresh")
        print("[dev-refresh] Runtime DEV reiniciado com novas URLs.")
        runtime_payload = runtime.get("runtime", {})
        if isinstance(runtime_payload, dict):
            for line in _runtime_to_lines(runtime_payload):
                print(f"  - {line}")
        _sync_if_requested(args=args, client=client)
        return 0

    if args.command == "dev-down":
        client.cloudflare_runtime(action="stop")
        client.cloudflare_toggle(enabled=False, settings={})
        print("[dev-down] Cloudflare DEV desativado.")
        _sync_if_requested(args=args, client=client)
        return 0

    if args.command == "prod-up":
        settings = _build_prod_settings(args)
        client.cloudflare_toggle(enabled=True, settings=settings)
        print("[prod-up] Cloudflare de producao ativado.")
        if not args.skip_runtime_start:
            runtime = client.cloudflare_runtime(action="start")
            runtime_payload = runtime.get("runtime", {})
            if isinstance(runtime_payload, dict):
                for line in _runtime_to_lines(runtime_payload):
                    print(f"  - {line}")
        _sync_if_requested(args=args, client=client)
        return 0

    if args.command == "preview-prod":
        settings = _build_prod_settings(args)
        preview = client.cloudflare_preview(settings=settings)
        urls = preview.get("urls", {})
        if isinstance(urls, dict):
            print("[preview-prod] rotas previstas:")
            print(f"  - portal: {urls.get('portal_base_url', '-')}")
            print(f"  - client: {urls.get('client_base_url', '-')}")
            print(f"  - admin: {urls.get('admin_base_url', '-')}")
            print(f"  - api: {urls.get('api_base_url', '-')}")
        tunnel = preview.get("tunnel", {})
        if isinstance(tunnel, dict):
            run_command = str(tunnel.get("run_command", "")).strip()
            if run_command:
                print(f"  - run_command: {run_command}")
        return 0

    if args.command == "prod-refresh":
        runtime = client.cloudflare_runtime(action="refresh")
        print("[prod-refresh] Runtime de producao reiniciado.")
        runtime_payload = runtime.get("runtime", {})
        if isinstance(runtime_payload, dict):
            for line in _runtime_to_lines(runtime_payload):
                print(f"  - {line}")
        _sync_if_requested(args=args, client=client)
        return 0

    if args.command == "prod-down":
        client.cloudflare_runtime(action="stop")
        client.cloudflare_toggle(enabled=False, settings={})
        print("[prod-down] Cloudflare de producao desativado.")
        _sync_if_requested(args=args, client=client)
        return 0

    raise CliError(f"Comando nao suportado: {args.command}")


def main() -> None:
    try:
        code = _run()
    except CliError as exc:
        print(f"[erro] {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("[cancelado] operacao interrompida pelo usuario.", file=sys.stderr)
        sys.exit(130)
    sys.exit(code)


if __name__ == "__main__":
    main()
