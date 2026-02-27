# ADR 0007 - Templates do Web Admin gerenciados pelo CMS

- Status: Aceita
- Data: 26/02/2026

## Contexto
O Web Admin precisava suportar multiplos templates visuais/estruturais para evolucao de UX sem fork de aplicacao.
A selecao do template deveria ser centralizada no Portal CMS, mantendo consistencia operacional entre ambientes.

## Decisao
1. `PortalConfig` passa a versionar tambem o canal admin, com:
   - `admin_active_template`
   - `admin_available_templates`
2. A API publica de configuracao aceita `channel=admin` e retorna:
   - `active_template` resolvido para o admin
   - `admin_active_template`
   - `admin_available_templates`
3. O Web Admin consome o template ativo em runtime no layout raiz e aplica variacao estrutural por provider/context.
4. Primeiro template entregue: `admin-adminkit` (layout sidebar/topbar, navegacao operacional e paleta de graficos dedicada), preservando identidade da marca Mr Quentinha.

## Consequencias
- Beneficios:
  - Troca de template do Admin sem deploy de codigo.
  - Evolucao de UX/IX por canal com governanca central no CMS.
  - Reaproveitamento de padrao existente de templates (portal/client).
- Trade-offs:
  - Maior acoplamento do Web Admin ao contrato de configuracao do Portal CMS.
  - Necessidade de validar compatibilidade de layout para cada novo template.

## Implementacao
- Backend: campos novos em `PortalConfig`, validacoes e serializacao publica/admin.
- Web Admin: provider de template, shell com layouts por template e seletor no modulo Portal CMS.
- UX: modulo de fluxo operacional guiado com navegacao anterior/proxima etapa.
