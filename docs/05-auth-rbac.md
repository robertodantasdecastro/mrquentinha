# Autenticacao e RBAC (Google/Apple + JWT)

## Objetivo
- Permitir login rapido no web client e app mobile via Google e Apple.
- Manter JWT como sessao oficial de API (`access` + `refresh`).
- Centralizar configuracoes OAuth no Web Admin (Portal CMS), sem segredo no frontend.

## Estado atual (27/02/2026)
- Login JWT nativo (usuario/senha) em producao de desenvolvimento: **concluido**.
- Parametros OAuth Google/Apple no Portal CMS (`PortalConfig.auth_providers`): **concluido**.
- Painel do Admin Web revisado com mapeamento correto de campos por provider (Google x Apple): **concluido**.
- UI do web client para iniciar OAuth + callbacks de retorno (`/conta/oauth/google/callback`, `/conta/oauth/apple/callback`): **concluido**.
- Perfil completo do usuario logado no Admin Web (dados adicionais, endereco, documentos, foto e biometria por foto): **concluido**.
- Troca do `code` OAuth no backend para emissao de JWT local: **pendente**.

## Contrato de configuracao OAuth (Portal CMS)
- Persistencia admin (privada): `PortalConfig.auth_providers`.
- Leitura publica segura: `GET /api/v1/portal/config/?channel=client&page=home`.
- Payload publico inclui somente campos seguros e flag `configured`.
- Campos sensiveis (`client_secret`, `private_key`) ficam somente no canal admin.

### Google (admin)
- `enabled`
- `web_client_id`
- `ios_client_id`
- `android_client_id`
- `client_secret` (privado)
- `auth_uri`
- `token_uri`
- `redirect_uri_web`
- `redirect_uri_mobile`
- `scope`
- Observacao de mapeamento: `ios_client_id` permanece no box do Google por ser credencial do Google Sign-In para app iOS.

### Apple (admin)
- `enabled`
- `service_id`
- `team_id`
- `key_id`
- `private_key` (privado)
- `auth_uri`
- `token_uri`
- `redirect_uri_web`
- `redirect_uri_mobile`
- `scope`
- Observacao de mapeamento: Apple usa `service_id` como client id do provider (nao usa `ios_client_id`).

## Fluxo alvo (social login completo)
1. Frontend recebe configuracao publica do CMS e monta URL de autorizacao do provider.
2. Usuario autentica no provider e retorna com `code` + `state` no callback web/mobile.
3. Backend valida `state`/nonce, troca `code` no provider e valida identidade.
4. Backend cria/atualiza usuario local e retorna JWT.
5. Frontend persiste tokens e segue jornada autenticada.

## RBAC (Role Based Access Control)
- Roles base: `ADMIN`, `FINANCEIRO`, `COZINHA`, `COMPRAS`, `CLIENTE`.
- Matriz operacional resumida:
  - `CLIENTE`: leitura de catalogo, criacao e acompanhamento de pedidos proprios.
  - `COZINHA`: manutencao de cardapio e insumos operacionais.
  - `COMPRAS`: requisicoes e compras, com impacto em estoque.
  - `FINANCEIRO`: contas AP/AR, caixa, conciliacao e relatorios.
  - `ADMIN`: acesso completo + governanca de usuarios/roles.

## Padroes tecnicos (Django/DRF)
- Autenticacao principal: JWT (SimpleJWT).
- RBAC via `Role`/`UserRole` com permission classes por modulo e acao.
- Ownership obrigatorio em dados de cliente/pessoal.
- Auditoria em endpoints sensiveis (especialmente financeiro e dados pessoais).

## Endpoint de perfil do usuario logado (Admin Web)
- Endpoint: `GET/PATCH /api/v1/accounts/me/profile/`
- Autenticacao: JWT obrigatorio.
- Atualizacao textual: payload JSON parcial (`PATCH`) com dados pessoais, endereco e documentos.
- Upload de arquivos: `PATCH multipart/form-data` para:
  - `profile_photo`
  - `document_front_image`
  - `document_back_image`
  - `document_selfie_image`
  - `biometric_photo`
- Regra de biometria: ao enviar `biometric_photo`, status vai para `PENDING_REVIEW` para validacao futura.

## Requisitos de seguranca
- Nunca expor segredos OAuth no payload publico.
- Validar `redirect_uri` permitidas por canal (`web` e `mobile`).
- Aplicar rate limit e monitorar tentativas de login.
- Registrar eventos de negacao de acesso para auditoria.

## Politica de senha (cadastro)
- Validacao de cadastro (`/api/v1/accounts/register/`) exige:
  - minimo de 8 caracteres;
  - ao menos 1 letra maiuscula;
  - ao menos 1 letra minuscula;
  - ao menos 1 numero.
- Frontends web aplicam validacao de senha no cliente antes do submit para reduzir erros de preenchimento.
