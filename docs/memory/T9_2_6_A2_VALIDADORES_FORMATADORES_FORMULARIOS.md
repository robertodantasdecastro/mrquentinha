# T9.2.6-A2 - Validadores e Formatadores Globais de Formularios

Data: 27/02/2026

## Objetivo
Padronizar formatacao e validacao de campos em todos os formularios dos frontends web do ecossistema Mr Quentinha:
- Web Admin
- Web Client
- Portal Web

## Estrategia implementada

### Camada global reutilizavel
- Criado componente `FormFieldGuard` no pacote compartilhado `@mrquentinha/ui`:
  - `workspaces/web/ui/src/components/FormFieldGuard.tsx`
- Componente aplicado nos layouts raiz:
  - `workspaces/web/admin/src/app/layout.tsx`
  - `workspaces/web/client/src/app/layout.tsx`
  - `workspaces/web/portal/src/app/layout.tsx`

### Regras de formatacao
- CPF: mascara `000.000.000-00`
- CNPJ: mascara `00.000.000/0000-00`
- CEP: mascara `00000-000`
- E-mail: normalizacao de tipo/input mode para email
- Datas: campos textuais identificados como data sao convertidos para `type="date"` quando aplicavel

### Regras de validacao
- CPF: validacao de digitos verificadores
- CNPJ: validacao de digitos verificadores
- CEP: 8 digitos
- E-mail: formato valido
- Senha atual: minimo de 8 caracteres
- Nova senha: minimo de 8 + maiuscula + minuscula + numero
- Data: valida formato selecionado

### UX mobile touch
- Datas com `type="date"` para usar seletor nativo (picker/rolagem) em dispositivos moveis.
- Campos numericos com `inputMode="numeric"` para teclado numérico no mobile.

## Reforcos de semantica em formularios criticos
- Login Admin: `name` em usuario/senha e `minLength` para senha.
- Conta Web Client (login/cadastro): `name`, `autocomplete` e `minLength` reforcados.
- Perfil Admin (`/perfil`): `name` explicito para dados pessoais, endereco, documentos e uploads.
- Portal CMS (pagamentos): `receiver_cpf/receiver_cnpj` e `receiver_email` com identificacao explicita.

## Reforco backend
- `accounts/register`: senha forte obrigatoria (8+, maiuscula, minuscula, numero).
- `portal config` (`payment_providers.receiver`):
  - documento validado por tipo de pessoa (CPF/CNPJ);
  - email do recebedor validado.

## Validacao executada
- Backend:
  - `ruff check`
  - `black --check`
  - `pytest tests/test_accounts_api.py tests/test_portal_api.py tests/test_portal_services.py`
- Frontends:
  - `npm run lint` (admin/client/portal)
  - `npm run build` (admin/client/portal)
