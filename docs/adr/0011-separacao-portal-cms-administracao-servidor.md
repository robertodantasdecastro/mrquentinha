# ADR 0011 - Separacao entre Portal CMS e Administracao do servidor

- Status: Aceita
- Data: 27/02/2026

## Contexto
O modulo `Portal CMS` concentrava responsabilidades de produto (template, conteudo, autenticacao social e pagamentos) junto com operacao de infraestrutura (SMTP, conectividade/dominio, assistente de instalacao e build/release).

Essa mistura dificultava a operacao e aumentava a carga cognitiva para equipes diferentes.

## Decisao
1. Criar o modulo dedicado `Administracao do servidor` no Web Admin.
2. Mover para o novo modulo os paineis:
   - gestao de e-mail;
   - conectividade e dominio (incluindo assistente de instalacao);
   - build e release mobile.
3. Manter o `Portal CMS` focado em recursos de produto:
   - template ativo;
   - autenticacao social;
   - pagamentos;
   - conteudo dinamico;
   - publicacao.
4. Evitar duplicacao de codigo: o mesmo componente `PortalSections` opera com dois modos (`portal` e `server-admin`) para reutilizar estado, validacoes e handlers.

## Consequencias
- Beneficios:
  - melhor organizacao de UX por responsabilidade (produto vs infraestrutura);
  - menor risco de manutencao duplicada;
  - mais clareza para testes manuais por trilha funcional.
- Trade-offs:
  - dependencia temporaria de um componente unico mais extenso (`PortalSections`) com renderizacao condicionada por modo.

## Implementacao
- Rotas:
  - `workspaces/web/admin/src/app/modulos/administracao-servidor/page.tsx`
  - `workspaces/web/admin/src/app/modulos/administracao-servidor/[service]/page.tsx`
- Refatoracao:
  - `workspaces/web/admin/src/app/modulos/portal/sections.tsx`
- Navegacao/catalogo:
  - `workspaces/web/admin/src/components/AdminShell.tsx`
  - `workspaces/web/admin/src/lib/adminModules.ts`

## Testes
- `cd workspaces/web/admin && npm run lint`
- `cd workspaces/web/admin && npm run build`
- `cd workspaces/backend && source .venv/bin/activate && python manage.py check`
