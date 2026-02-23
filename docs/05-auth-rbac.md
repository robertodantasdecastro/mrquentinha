# Autenticação e RBAC (Google + JWT)

## Objetivo
- Cliente (mobile) entra rápido via Google.
- Usuários internos (web) também podem entrar via Google.
- Depois, completam cadastro (telefone, perfil, etc.) conforme regras da empresa.

## Estratégia recomendada
1. **Google OAuth** para autenticar e obter identidade (`sub`, `email`, `name`).
2. Backend cria/atualiza usuário local e retorna **JWT** (access + refresh).
3. Toda requisição na API usa `Authorization: Bearer <access_token>`.

## RBAC (Role Based Access Control)
- Roles (ex.: ADMIN, FINANCEIRO, COZINHA, COMPRAS, CLIENTE).
- Permissões por endpoint e por ação.
- Matriz sugerida (resumo):
  - Cliente: `orders: create/read`, `catalog: read`
  - Cozinha: `catalog: write`, `procurement_request: create`
  - Compras: `procurement: write`, `inventory: write`
  - Financeiro: `finance: write/read`, `orders: read`
  - Admin: tudo

## Padrões técnicos (Django/DRF)
- Modelos: `Role`, `UserRole`
- DRF permissions:
  - permission classes por viewset (ex.: `IsFinanceRole`)
  - object-level permissions quando necessário
- Auditoria:
  - salvar `created_by`/`updated_by` em tabelas críticas

## Fluxo de onboarding de usuário interno
1. Login Google
2. Se “não possui perfil interno”, fica em estado `PENDING_PROFILE`
3. Admin/Financeiro aprova e atribui roles
4. Usuário acessa módulos conforme role

## Observações de segurança
- Bloquear endpoints de gestão para não-clientes.
- Rate limit em login (fase 2).
- Logs de tentativa de acesso negado.
