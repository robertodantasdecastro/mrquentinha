# ADR 0021: Consolidacao visual do portal e centrais de suporte/wiki

- Data: 03/03/2026
- Status: Aceito

## Contexto
O plano `T6.2.1` exige consolidar a experiencia visual do portal e alinhar a integracao com o Web Cliente (`app.mrquentinha.com.br`), incluindo areas institucionais de contato, suporte e wiki.

Antes desta decisao:
- o portal tinha navegacao e layout heterogeneos entre paginas institucionais;
- nao havia rotas dedicadas de suporte/wiki no portal e no web cliente;
- `PortalSection.page` nao aceitava `suporte` e `wiki`, limitando evolucao de conteudo por template no CMS.

## Decisao
1. Padronizar paginas institucionais do portal com um shell comum (`PortalPageIntro`) e variacao visual por template (`classic` e `letsfit-clean`) via CSS.
2. Criar rotas publicas no portal:
   - `/suporte`
   - `/wiki`
3. Criar rotas correspondentes no web cliente:
   - `/suporte`
   - `/wiki`
4. Integrar explicitamente Portal -> Web Cliente com CTAs de vendas e suporte (bridge comercial).
5. Evoluir o backend `portal` para aceitar `PortalPage.SUPORTE` e `PortalPage.WIKI`, com fixtures iniciais por template para viabilizar gestao de conteudo pelo CMS.
6. Adicionar novos templates inspirados na referencia `jp.lightisgood.com.br`:
   - portal: `editorial-jp`
   - web cliente: `client-editorial-jp`
   mantendo a identidade oficial do projeto (`#FF6A00` como cor primaria).

## Consequencias
- UX mais consistente entre paginas institucionais e templates.
- Navegacao mais clara entre descoberta (portal), conversao (web cliente) e atendimento (suporte/wiki).
- CMS passa a ter base tecnica para evoluir conteudo dinamico de suporte/wiki por template.
- Requer migration nova em `portal` (`0011_alter_portalsection_page`).
