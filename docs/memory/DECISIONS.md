# Decisões vivas do projeto

Use este arquivo para registrar decisões “em andamento” (menos formais).
Quando uma decisão for definitiva e afetar arquitetura, crie um ADR em `docs/adr/`.

## Padrões definidos
- Backend: Django + DRF
- DB: PostgreSQL
- Sem Docker no MVP
- Mobile: React Native
- Web Gestão: React/Next

## Itens para decidir (aberto)
- Gateway de pagamento (Pix/Cartão/VR)
- OCR (serviço externo vs interno)
- Distribuição iOS (TestFlight/Enterprise)

## Marca
- Nome: Mr Quentinha
- Domínio: www.mrquentinha.com.br
- Cor primária: #FF6A00
- Assets: assets/brand/

## Pendencias tecnicas (catalogo)
- RBAC do `catalog` ainda esta em modo MVP com `AllowAny` nas views.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Cozinha CRUD, Financeiro leitura e Cliente leitura de cardapio).

## Pendencias tecnicas (inventory/procurement)
- RBAC de `inventory` e `procurement` ainda esta temporario com `AllowAny` no MVP.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Compras/Estoque CRUD, Cozinha criacao de solicitacao e leitura, Financeiro leitura).
