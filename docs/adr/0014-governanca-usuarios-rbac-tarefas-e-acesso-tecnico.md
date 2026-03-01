# ADR 0014 - Governanca de usuarios com RBAC, tarefas e bloqueio de areas tecnicas

Data: 01/03/2026  
Status: Aceita

## Contexto
O modulo `Usuarios e RBAC` estava limitado a listar usuarios e atribuir papeis.

Para o modelo operacional do Mr Quentinha, era necessario:
- administracao completa de contas (criar/editar usuarios);
- vinculacao de usuarios a categorias e tarefas operacionais;
- bloqueio explicito de areas tecnicas do Web Admin para perfis nao administrativos;
- manutencao da regra de que atribuicoes de privilegios administrativos so podem ser feitas por administradores.

## Decisao
1. Evoluir o backend `accounts` para incluir catalogo de tarefas operacionais:
   - `UserTaskCategory`
   - `UserTask`
   - `UserTaskAssignment`
2. Publicar endpoints administrativos para:
   - criar e editar usuarios do sistema;
   - listar categorias/tarefas;
   - atribuir tarefas por usuario.
3. Expandir payload de usuario/admin com:
   - `task_codes`
   - `task_category_codes`
   - `allowed_admin_module_slugs`
   - `can_access_technical_admin`
4. Aplicar bloqueio de acesso no Web Admin para modulos tecnicos sem papel `ADMIN`:
   - `Portal CMS`
   - `Administracao do servidor`
   - `Instalacao / Deploy`
   - `Usuarios e RBAC`
5. Atualizar o modulo `Usuarios e RBAC` para cobrir:
   - criacao de conta;
   - edicao de conta;
   - atribuicao de papeis;
   - atribuicao de tarefas por categoria.

## Consequencias
- A governanca de acesso ficou mais aderente ao modelo de negocio operacional.
- Usuarios de operacao deixam de ter acesso a areas tecnicas por padrao.
- O Web Admin passa a suportar administracao de usuarios de ponta a ponta sem depender do Django Admin.
- O vinculo usuario↔tarefa permite evolucoes futuras de compliance operacional e trilhas de responsabilidade.

## Impacto tecnico
- Backend:
  - `apps/accounts/models.py`
  - `apps/accounts/services.py`
  - `apps/accounts/serializers.py`
  - `apps/accounts/views.py`
  - `apps/accounts/urls.py`
  - `apps/accounts/selectors.py`
  - migration `0006_usertaskcategory_usertask_usertaskassignment.py`
- Frontend Admin:
  - `components/modules/UsersRbacPanel.tsx`
  - `lib/api.ts`
  - `types/api.ts`
  - `components/ModuleAccessGuard.tsx`
  - `lib/adminAccess.ts`
  - paginas de modulo tecnico com guard de acesso
