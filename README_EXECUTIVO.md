# Mr Quentinha - Resumo Executivo

<p align="center">
  <img src="assets/brand/png/logo_wordmark_2000x.png" alt="Logo Mr Quentinha" width="420" />
</p>

## O que e
O **Mr Quentinha** e um ecossistema digital completo para operacao de marmitas, cobrindo ponta a ponta:
- venda ao cliente (web e mobile)
- operacao interna (producao, compras, estoque, financeiro)
- gestao de conteudo e canais (Portal CMS)
- pagamentos online multigateway
- monitoramento operacional em tempo real

## Problema que resolve
Negocios de alimentacao normalmente operam com sistemas fragmentados (pedidos em um lugar, estoque em outro, financeiro em planilhas).  
O Mr Quentinha unifica essa operacao em uma plataforma unica, com rastreabilidade e controle.

## Solucao entregue
- **Backend central** (Django + DRF + PostgreSQL) para regras de negocio e integracoes.
- **Web Admin** para operacao diaria dos modulos criticos.
- **Web Client** para jornada de compra e acompanhamento do pedido.
- **Portal institucional** com CMS e controle de templates.
- **Contrato mobile** integrado ao ecossistema.

## Diferenciais
- Arquitetura modular por dominio.
- Pagamentos com suporte a `Mercado Pago`, `Efi` e `Asaas`.
- Selecao de provider por canal (`web` e `mobile`).
- Webhooks idempotentes com reconciliacao financeira.
- Monitoramento realtime de servicos, pagamentos e lifecycle de pedidos.
- Governanca de autenticacao social (Google/Apple) via Admin.
- Publicacao online com Cloudflare em 1 clique no Admin, com:
  - modo DEV por URLs aleatorias (`trycloudflare`);
  - modo operacional por dominio oficial (deploy tipico);
  - automacao equivalente por terminal (`scripts/cloudflare_admin.sh`).
- Assistente de instalacao/deploy no Web Admin com wizard guiado, monitoramento de jobs e pre-requisitos de producao.
- Workflow continuo de atualizacao do instalador com guard rail dedicado (`scripts/check_installer_workflow.sh`).

## Estado atual (28/02/2026)
- MVP operacional fechado (catalogo, estoque, compras, producao, pedidos, financeiro).
- Trilha de pagamentos avancada implementada ate `T7.2.4-A3`.
- Cloudflare com operacao completa em DEV e PRODUCAO, incluindo sincronizacao de endpoints para os frontends.
- Validacao funcional Cloudflare DEV concluida em `27/02/2026`: frontends publicados em `trycloudflare` comunicando com a API com sucesso.
- Assistente de instalacao/deploy publicado no modulo independente `Instalacao / Deploy` (wizard + autosave + jobs).
- Proxima etapa: `T7.2.4-A4` (homologacao externa oficial dos gateways).
- Plano manual E2E institucionalizado em `T9.2.1`.

## Modelo tecnico
- Backend unico para todos os canais.
- Frontends desacoplados consumindo API versionada (`/api/v1/...`).
- Suporte a operacao em VM (modelo atual) e Docker (modelo novo opcional).
- Qualidade com lint, build, testes automatizados e smoke scripts.

## Valor de negocio
- Reducao de retrabalho operacional.
- Mais previsibilidade financeira e operacional.
- Escalabilidade para crescimento de canais.
- Base tecnica pronta para evolucao de produto.
