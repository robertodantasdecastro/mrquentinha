from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from .validators import normalize_postal_code


class CepLookupNotFoundError(Exception):
    pass


class CepLookupUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class AddressLookupResult:
    postal_code: str
    street: str
    neighborhood: str
    city: str
    state: str
    source: str

    def to_payload(self) -> dict[str, str]:
        return {
            "postal_code": self.postal_code,
            "street": self.street,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "source": self.source,
        }


def lookup_address_by_cep(*, cep: str) -> dict[str, str]:
    postal_code = normalize_postal_code(cep)
    if len(postal_code) != 8:
        raise DjangoValidationError("CEP invalido. Informe 8 digitos.")

    if getattr(settings, "CORREIOS_CEP_ENABLED", True):
        try:
            correios_result = _lookup_with_correios(postal_code)
            if correios_result is not None:
                return correios_result.to_payload()
        except CepLookupNotFoundError:
            # Continua para fallback se habilitado.
            pass

    if getattr(settings, "CORREIOS_CEP_ALLOW_VIACEP_FALLBACK", True):
        fallback_result = _lookup_with_viacep(postal_code)
        if fallback_result is not None:
            return fallback_result.to_payload()

    raise CepLookupNotFoundError(
        "CEP nao encontrado. Confira o numero informado e tente novamente."
    )


def _lookup_with_correios(postal_code: str) -> AddressLookupResult | None:
    bearer_token = _resolve_correios_bearer_token()
    if not bearer_token:
        raise CepLookupUnavailableError(
            "Integracao com Correios indisponivel. "
            "Configure token/contrato para consulta de CEP."
        )

    api_base_url = str(
        getattr(settings, "CORREIOS_CEP_API_BASE_URL", "https://api.correios.com.br")
    ).strip()
    api_base_url = api_base_url.rstrip("/")

    endpoint_paths = getattr(settings, "CORREIOS_CEP_ENDPOINT_PATHS", None)
    if not endpoint_paths:
        endpoint_paths = [
            "/cp/v2/enderecos",
            "/cep/v2/enderecos",
        ]

    query = urllib_parse.urlencode({"cep": postal_code})
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
    }

    last_http_status = 0
    for endpoint_path in endpoint_paths:
        path = str(endpoint_path or "").strip()
        if not path:
            continue
        if not path.startswith("/"):
            path = "/" + path

        endpoint = f"{api_base_url}{path}?{query}"
        try:
            payload = _http_json_request(endpoint, headers=headers)
        except urllib_error.HTTPError as exc:
            last_http_status = int(exc.code)
            if exc.code == 404:
                continue
            if exc.code in {401, 403}:
                raise CepLookupUnavailableError(
                    "Credenciais dos Correios invalidas ou sem permissao "
                    "para consulta de CEP."
                ) from exc
            continue
        except urllib_error.URLError as exc:
            raise CepLookupUnavailableError(
                "Falha de conexao com API dos Correios para consulta de CEP."
            ) from exc

        result = _parse_correios_payload(payload=payload, postal_code=postal_code)
        if result is not None:
            return result

    if last_http_status == 404:
        raise CepLookupNotFoundError("CEP nao encontrado na base dos Correios.")

    return None


def _resolve_correios_bearer_token() -> str:
    static_token = str(getattr(settings, "CORREIOS_CEP_BEARER_TOKEN", "")).strip()
    if static_token:
        return static_token

    username = str(getattr(settings, "CORREIOS_TOKEN_USERNAME", "")).strip()
    password = str(getattr(settings, "CORREIOS_TOKEN_PASSWORD", "")).strip()
    contract_number = str(getattr(settings, "CORREIOS_TOKEN_CONTRACT", "")).strip()
    dr_code = str(getattr(settings, "CORREIOS_TOKEN_DR", "")).strip()
    if not username or not password or not contract_number:
        return ""

    token_endpoint = str(
        getattr(
            settings,
            "CORREIOS_TOKEN_ENDPOINT",
            "https://api.correios.com.br/token/v1/autentica/contrato",
        )
    ).strip()
    if not token_endpoint:
        return ""

    basic_auth = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")

    payload: dict[str, object] = {
        "numero": contract_number,
    }
    if dr_code:
        try:
            payload["dr"] = int(dr_code)
        except ValueError:
            payload["dr"] = dr_code

    response_payload = _http_json_request(
        token_endpoint,
        method="POST",
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        body=json.dumps(payload).encode("utf-8"),
    )

    for key in ("token", "access_token", "accessToken"):
        token = str(response_payload.get(key, "")).strip()
        if token:
            return token

    return ""


def _lookup_with_viacep(postal_code: str) -> AddressLookupResult | None:
    endpoint = f"https://viacep.com.br/ws/{postal_code}/json/"
    try:
        payload = _http_json_request(
            endpoint,
            headers={"Accept": "application/json"},
        )
    except (urllib_error.HTTPError, urllib_error.URLError, TimeoutError):
        return None

    if not isinstance(payload, dict):
        return None

    if bool(payload.get("erro", False)):
        return None

    return AddressLookupResult(
        postal_code=postal_code,
        street=str(payload.get("logradouro", "")).strip(),
        neighborhood=str(payload.get("bairro", "")).strip(),
        city=str(payload.get("localidade", "")).strip(),
        state=str(payload.get("uf", "")).strip().upper(),
        source="viacep_fallback",
    )


def _http_json_request(
    endpoint: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> dict | list:
    timeout_seconds = int(getattr(settings, "CORREIOS_CEP_REQUEST_TIMEOUT_SECONDS", 8))
    request = urllib_request.Request(
        url=endpoint,
        method=method,
        data=body,
        headers=headers or {},
    )

    with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
        content = response.read().decode("utf-8")

    if not content:
        return {}

    return json.loads(content)


def _parse_correios_payload(
    *,
    payload: dict | list,
    postal_code: str,
) -> AddressLookupResult | None:
    item: dict | None = None
    if isinstance(payload, dict):
        if isinstance(payload.get("itens"), list) and payload["itens"]:
            first = payload["itens"][0]
            if isinstance(first, dict):
                item = first
        elif isinstance(payload.get("items"), list) and payload["items"]:
            first = payload["items"][0]
            if isinstance(first, dict):
                item = first
        else:
            item = payload
    elif isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            item = first

    if not isinstance(item, dict):
        return None

    street = _pick_string(
        item,
        [
            "logradouro",
            "nomeLogradouro",
            "endereco",
            "logradouroDNEC",
            "nome",
        ],
    )
    if not street:
        tipo = _pick_string(item, ["tipoLogradouro", "tipo"])
        nome = _pick_string(item, ["nomeLogradouro", "descricao"])
        street = " ".join(part for part in [tipo, nome] if part).strip()

    neighborhood = _pick_string(
        item,
        [
            "bairro",
            "nomeBairro",
            "bairroDNEC",
            "distrito",
        ],
    )
    city = _pick_string(
        item,
        [
            "localidade",
            "cidade",
            "municipio",
            "nomeLocalidade",
        ],
    )
    state = _pick_string(item, ["uf", "siglaUf", "estado"]).upper()

    if not city and not state and not street and not neighborhood:
        return None

    return AddressLookupResult(
        postal_code=postal_code,
        street=street,
        neighborhood=neighborhood,
        city=city,
        state=state,
        source="correios",
    )


def _pick_string(payload: dict, keys: list[str]) -> str:
    for key in keys:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    return ""
