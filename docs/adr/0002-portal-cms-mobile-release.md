# ADR-0002: Publicacao de release mobile via Portal CMS

## Status
Aceito

## Contexto
O Portal CMS ja centraliza configuracao publica de portal/client, mas o fluxo de download do app
mobile ainda dependia de links estaticos e edicao manual no frontend. Isso aumenta risco de
inconsistencia entre versao publicada, endpoint de API e links distribuidos em QR/download.

## Decisao
- Criar modelo `MobileRelease` no backend (`apps.portal`) para registrar versao, build, status e
  metadados de publicacao.
- Expor endpoint publico `GET /api/v1/portal/mobile/releases/latest/` para fornecer a ultima
  release publicada com links de download resolvidos.
- Expor endpoints admin em `/api/v1/portal/admin/mobile/releases/` para ciclo inicial
  `create -> compile -> publish`.
- Manter snapshot de ambiente por release (`api_base_url_snapshot` e `host_publico_snapshot`) para
  rastreabilidade operacional.
- Integrar Admin Web (secao `Build mobile`) e Portal Web (`/app`) ao contrato publico da release.

## Consequencias
- Positivas:
  - centralizacao do fluxo de release em uma unica fonte de verdade (CMS).
  - rastreabilidade de versao/build e links distribuidos ao usuario final.
  - eliminacao de links hardcoded no frontend do portal.
- Trade-offs:
  - aumenta escopo do app `portal` no backend com nova entidade operacional.
  - pipeline de compilacao ainda e "modo inicial" (simulado/orquestrado por service), sem CI/CD
    nativo de build mobile nesta fase.

## Alternativas consideradas
- Manter links de APK/iOS em variaveis de ambiente dos frontends.
- Criar servico separado de release fora do app `portal`.
