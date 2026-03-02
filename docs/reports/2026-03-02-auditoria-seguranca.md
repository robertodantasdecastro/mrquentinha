# Auditoria de Seguranca - Mr Quentinha
Data: 02/03/2026
Escopo: `workspaces/backend`, `workspaces/web`, `scripts`, `installdev.sh`, configuracoes de deploy.
Metodo: revisao estatica de codigo + verificacoes locais de configuracao.

## Resumo Executivo
- Nivel geral de risco atual: **ALTO**.
- Pontos mais criticos:
  1. **Exposicao publica de midias sensiveis** (`/media/*`) contendo documentos/biometria.
  2. **Hardening incompleto de producao** (HTTPS/HSTS/redirect/cabecalhos).
  3. **Segredo de aplicacao de producao fraco** (check de seguranca do Django acusa `security.W009`).

---

## Achados por severidade

### CRITICO

#### SEC-001 - Exposicao de arquivos sensiveis em `/media/*` sem controle de acesso
- Evidencias:
  - `workspaces/backend/src/config/urls.py:67`
  - `workspaces/backend/src/config/urls.py:69`
  - `workspaces/backend/src/config/urls.py:71`
  - campos com potencial LGPD sensivel em:
    - `workspaces/backend/src/apps/accounts/models.py:213`
    - `workspaces/backend/src/apps/accounts/models.py:218`
    - `workspaces/backend/src/apps/accounts/models.py:223`
    - `workspaces/backend/src/apps/accounts/models.py:228`
- Impacto:
  - acesso direto a selfie de documento e biometria por URL, sem politica de autorizacao por proprietario/papel.
  - risco LGPD alto (dados pessoais sensiveis).
- Recomendacao (alto nivel):
  - remover `serve` direto de `media` em runtime de producao;
  - implementar endpoint protegido para download (owner/admin) + URLs assinadas expiraveis;
  - separar `media_public` e `media_private`.

### ALTO

#### SEC-002 - Hardening HTTPS incompleto (Django + Nginx)
- Evidencias:
  - `workspaces/backend/src/config/settings/prod.py:6` (somente `SECURE_PROXY_SSL_HEADER`)
  - ausentes no `prod.py`: `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`.
  - `scripts/setup_nginx_prod.sh:37` (blocos HTTP 80 ativos sem redirect forcado para 443)
  - `scripts/setup_nginx_prod.sh:105` (blocos 443 sem headers de seguranca adicionais)
- Impacto:
  - superficie ampliada para downgrade/uso de HTTP;
  - ausencia de HSTS aumenta risco em clientes que acessam por HTTP inicialmente.
- Recomendacao (alto nivel):
  - forcar redirect 80 -> 443;
  - habilitar HSTS gradualmente;
  - aplicar headers de seguranca no reverse proxy e no app.

#### SEC-003 - `SECRET_KEY` de producao fraca
- Evidencias:
  - `python manage.py check --deploy` apontou `security.W009`.
  - validacao local (sem exibir segredo): tamanho atual **16** caracteres.
  - referencia de configuracao: `workspaces/backend/src/config/settings/base.py:12`.
- Impacto:
  - enfraquece mecanismos de assinatura, tokens e protecoes dependentes da chave.
- Recomendacao (alto nivel):
  - rotacionar `SECRET_KEY` para valor forte (>=50 chars, alta entropia) em cofre local seguro;
  - revisar componentes afetados por assinatura de payload/token apos rotacao.

#### SEC-004 - Falha de selecao de settings em comandos de gestao (risco operacional e de seguranca)
- Evidencias:
  - `workspaces/backend/manage.py:16` default fixo para `config.settings.dev` quando variavel ambiente nao exportada.
  - `installdev.sh` grava `DJANGO_SETTINGS_MODULE` no `.env` (`installdev.sh:484`), mas isso e lido tarde demais para o `setdefault` do `manage.py`.
  - efeito observado: `check --deploy` sem export explicito cai em comportamento inesperado e erro de app duplicado via `dev.py`.
- Impacto:
  - comandos criticos podem executar sob settings incorretas.
  - chance de migracao/check/seed rodar com configuracao de dev.
- Recomendacao (alto nivel):
  - tornar selecao de settings explicita e deterministica em todos scripts de operacao.

### MEDIO

#### SEC-005 - CORS/CSRF em producao com origens HTTP e hosts amplos
- Evidencias:
  - geracao de origens inclui `http://` para dominios/hosts: `installdev.sh:436`, `installdev.sh:437`, `installdev.sh:449`, `installdev.sh:450`.
  - `CORS_ALLOW_CREDENTIALS=True` em base: `workspaces/backend/src/config/settings/base.py:183`.
- Impacto:
  - politica mais permissiva do que necessario no modo producao.
- Recomendacao (alto nivel):
  - separar construcao de origens por ambiente (prod somente HTTPS oficial).

#### SEC-006 - Armazenamento de JWT em `localStorage`
- Evidencias:
  - `workspaces/web/admin/src/lib/storage.ts:24`
  - `workspaces/web/client/src/lib/storage.ts:63`
- Impacto:
  - em caso de XSS, tokens podem ser exfiltrados.
- Recomendacao (alto nivel):
  - avaliar migracao para cookie `HttpOnly`/`Secure`/`SameSite` + estrategia anti-CSRF.

#### SEC-007 - Execucao SSH com senha via `sshpass -p` em linha de comando
- Evidencias:
  - construcao com senha no argv: `workspaces/backend/src/apps/portal/services.py:3425`
  - execucao em background de wrapper shell: `workspaces/backend/src/apps/portal/services.py:4780`
- Impacto:
  - senha pode aparecer para processos locais com permissao de leitura de proc/argv.
- Recomendacao (alto nivel):
  - priorizar auth por chave;
  - se senha for inevitavel, usar abordagem com menor exposicao de segredo em argv.

#### SEC-008 - Fallback de "criptografia" sem Fernet nao e criptografia forte
- Evidencias:
  - fallback para `signing.dumps` quando sem chave/dependencia: `workspaces/backend/src/apps/accounts/fields.py:37`.
- Impacto:
  - pode haver falsa percepcao de criptografia real em cenarios mal configurados.
- Recomendacao (alto nivel):
  - em producao, exigir sempre criptografia forte (`FIELD_ENCRYPTION_STRICT=true` + chave valida).

### BAIXO

#### SEC-009 - Sem throttling global configurado no DRF
- Evidencias:
  - `workspaces/backend/src/config/settings/base.py:162` (nao ha `DEFAULT_THROTTLE_CLASSES`/`DEFAULT_THROTTLE_RATES`).
- Impacto:
  - maior superficie para abuso de endpoints publicos.
- Recomendacao (alto nivel):
  - definir throttling para login, registro, reenvio e webhooks.

#### SEC-010 - Comparacao de token de webhook sem `compare_digest`
- Evidencias:
  - `workspaces/backend/src/apps/orders/views.py:81`.
- Impacto:
  - risco teorico de timing side-channel.
- Recomendacao (alto nivel):
  - usar comparacao constante para segredos.

---

## Observacoes importantes
- Nao foram encontrados segredos reais hardcoded no repositorio rastreado.
- `pip_audit` e `bandit` nao estao instalados no ambiente local atual, entao a analise SAST/dependencias Python ficou parcial.

