# ADR 0013 - Auditoria do Web Admin e modo de URL DEV do Cloudflare

Data: 28/02/2026  
Status: Aceita

## Contexto
O ecossistema Mr Quentinha precisava de dois reforcos operacionais:
- rastreabilidade completa de uso do Web Admin (quem fez, o que fez, quando fez);
- estabilidade de enderecamento para homologacoes longas (incluindo build mobile) no modo DEV com Cloudflare.

O modo DEV com `trycloudflare` ja existia com dominios aleatorios, mas havia necessidade de opcao de padrao fixo editavel no painel.

## Decisao
1. Foi criado o app Django `admin_audit` com o modelo `AdminActivityLog` e middleware dedicado para trilha de auditoria de operacoes administrativas em `/api/v1/*`.
2. Foi publicado endpoint administrativo paginado para consulta dos logs:
   - `GET /api/v1/admin-audit/admin-activity/`
3. O Web Admin passou a ter secao propria `Auditoria de atividade` em `Administracao do servidor`, com filtros e paginacao.
4. O `cloudflare_settings` evoluiu com:
   - `dev_url_mode` (`random` | `manual`)
   - `dev_manual_urls` (`portal/client/admin/api`)
5. Quando `dev_url_mode=manual` e as URLs estao completas, o backend usa essas URLs como referencia ativa para roteamento/sincronizacao de API no modo DEV.

## Consequencias
- Ganho de governanca e compliance operacional no painel admin.
- Reducao de risco de drift no ambiente DEV durante homologacoes longas.
- Compatibilidade mantida com fluxo atual de dominios aleatorios (`random`) e com operacao local/hybrid.
- O endpoint de auditoria foi excluido da auto-auditoria para evitar ruido e crescimento artificial de logs.

## Impacto tecnico
- Backend:
  - `apps/admin_audit/*`
  - `config/settings/base.py` (app + middleware)
  - `config/urls.py` (rota `admin-audit`)
  - `apps/portal/services.py` (modo manual/random das URLs DEV)
- Web Admin:
  - `modulos/administracao-servidor/auditoria`
  - tipos e cliente API atualizados para novos campos de Cloudflare e auditoria.
