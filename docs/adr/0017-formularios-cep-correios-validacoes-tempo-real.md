# ADR 0017 - Formularios com CEP Correios e validacoes em tempo real

- Data: 01/03/2026
- Status: Aceita

## Contexto
O ecossistema Mr Quentinha passou a exigir padrao unico para formularios com dados sensiveis de cadastro:
- CEP com autopreenchimento de endereco;
- telefone com mascara/validacao e marcador opcional de WhatsApp;
- CPF/CNPJ com validacao de digito verificador (DV);
- e-mail com validacao imediata no frontend e reforco no backend.

Sem padrao central, cada formulario evoluia de forma isolada, com risco de inconsistencia entre Admin, Client e Portal, alem de maior retrabalho no ciclo Codex + Antigravity.

## Decisao
1. Centralizar regras de formulario no `FormFieldGuard` do pacote `@mrquentinha/ui`, aplicado globalmente nos layouts de `admin`, `client` e `portal`.
2. Adotar endpoint backend dedicado para lookup de CEP:
   - `GET /api/v1/accounts/lookup-cep/?cep=...`
   - consulta principal na API dos Correios;
   - fallback opcional para ViaCEP em ambiente de desenvolvimento/controlado.
3. Reforcar validacoes servidor-side em `accounts` e `portal`:
   - CPF/CNPJ obrigatoriamente validados por DV quando informados;
   - telefone normalizado (DDD + numero) e validado com 10 ou 11 digitos;
   - e-mail validado no backend para campos de recebedor/configuracao.
4. Persistir o indicador de WhatsApp no perfil (`UserProfile.phone_is_whatsapp`) para uso operacional no Web Admin.

## Consequencias
- Melhor experiencia de preenchimento (menos erro manual) em todos os templates do Web Admin e nos demais frontends web.
- Maior seguranca de dados ao manter validacao no cliente e no servidor.
- Padrao unico para novos formularios: qualquer campo `CEP/telefone/CPF/CNPJ/email` deve reutilizar o guard global e os validadores backend.
- Dependencia operacional explicita de configuracao Correios quando o fallback estiver desabilitado.

## Referencias
- `workspaces/web/ui/src/components/FormFieldGuard.tsx`
- `workspaces/backend/src/apps/accounts/address_lookup.py`
- `workspaces/backend/src/apps/accounts/validators.py`
- `docs/memory/T9_2_6_A2_VALIDADORES_FORMATADORES_FORMULARIOS.md`
