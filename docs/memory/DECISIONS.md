# Decisoes vivas do projeto

Use este arquivo para registrar decisoes "em andamento" (menos formais).
Quando uma decisao for definitiva e afetar arquitetura, crie um ADR em `docs/adr/`.

## Padroes definidos
- Backend: Django + DRF
- DB: PostgreSQL
- Sem Docker no MVP
- Mobile: React Native
- Web Gestao: React/Next

## Itens para decidir (aberto)
- Gateway de pagamento (Pix/Cartao/VR)
- OCR (servico externo vs interno)
- Distribuicao iOS (TestFlight/Enterprise)

## Marca
- Nome: Mr Quentinha
- Dominio: www.mrquentinha.com.br
- Cor primaria: #FF6A00
- Assets: assets/brand/

## Pendencias tecnicas (catalogo)
- RBAC do `catalog` ainda esta em modo MVP com `AllowAny` nas views.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Cozinha CRUD, Financeiro leitura e Cliente leitura de cardapio).

## Pendencias tecnicas (inventory/procurement)
- RBAC de `inventory` e `procurement` ainda esta temporario com `AllowAny` no MVP.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Compras/Estoque CRUD, Cozinha criacao de solicitacao e leitura, Financeiro leitura).

## Etapa 3.1 - Geracao de requisicao por cardapio
- Multiplicador de consumo no MVP:
  - se `MenuItem.available_qty` estiver preenchido, usar esse valor para multiplicar os ingredientes da receita.
  - se `available_qty` estiver vazio, considerar `1` lote por prato.
- Conversao de unidade:
  - nao implementar nesta etapa.
  - service valida compatibilidade entre `DishIngredient.unit` e unidade base do ingrediente/estoque.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) em etapa futura.

## Decisoes abertas para Etapas 6-8
- Stack do portal institucional (Etapa 6):
  - decidir entre Next.js (SSR/SSG) ou estrutura estatica mais simples.
  - definir nivel de integracao com autenticacao e acesso ao admin.
- Estrategia de web clientes/PWA (Etapa 7):
  - definir escopo minimo do PWA (instalacao, cache, offline parcial, push).
  - definir paridade funcional entre mobile nativo e canal web.
- Segregacao de dados pessoais (Etapa 8):
  - definir separacao logica/fisica entre dados operacionais da empresa e dados pessoais sensiveis.
  - definir politicas de retencao, mascaramento e trilha de auditoria aderentes a LGPD.
