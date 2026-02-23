# POO e padrões de código (para escalar sem reescrever)

## Objetivo
Garantir:
- reutilização de código
- regras de negócio claras
- mudanças seguras e com testes
- performance e legibilidade

## Regras práticas
1. Evite regras complexas dentro de `views` e `models`.
2. Crie **serviços** (classes ou funções) para casos de uso.
3. Padronize “entrada/saída”:
   - serializers para API
   - dataclasses/DTOs para serviços quando útil

## Camadas (modelo simples)
- **API (controllers)**: views/viewsets, validação, auth
- **Application (use cases)**: orquestra ações (ex.: “criar pedido”)
- **Domain**: regras (ex.: cálculo de custo, validações)
- **Infrastructure**: integrações (pagamento, OCR), repositórios, queries

## Padrões sugeridos no Django
- `services.py` → casos de uso do domínio
- `selectors.py` → consultas (somente leitura)
- `repositories.py` (opcional) → abstração de persistência
- `types.py` / `dtos.py` → dataclasses e tipos
- `permissions.py` → RBAC por módulo

## Exemplo de “caso de uso” (conceitual)
- `CreateOrderService`:
  - valida cardápio do dia
  - calcula total
  - cria pedido + itens
  - dispara criação de AR no financeiro

## Performance (boas práticas)
- usar `select_related` / `prefetch_related`
- indexar campos de filtros frequentes
- evitar N+1 em endpoints de listagem
