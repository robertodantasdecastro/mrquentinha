# T9.2.6-A1 - Perfil Completo do Usuario Logado (Web Admin)

Data: 27/02/2026

## Objetivo
Entregar no Web Admin, em todos os templates, uma area de administracao do usuario logado para:
- editar dados adicionais completos;
- cadastrar/editar endereco;
- cadastrar dados de documentos;
- subir foto de perfil;
- digitalizar/subir documentos;
- registrar biometria por foto para autenticacao futura;
- executar logoff.

## Escopo implementado

### Backend (`accounts`)
- Novo modelo `UserProfile` com campos de:
  - dados pessoais;
  - endereco;
  - documentos;
  - fotos (perfil, documento frente/verso/selfie, biometria);
  - status de biometria.
- Nova migration:
  - `workspaces/backend/src/apps/accounts/migrations/0002_userprofile.py`
- Novo endpoint autenticado:
  - `GET /api/v1/accounts/me/profile/`
  - `PATCH /api/v1/accounts/me/profile/` (JSON e multipart)
- Regras:
  - cria perfil automaticamente no primeiro acesso;
  - normaliza CPF/CNPJ/CEP;
  - ao receber `biometric_photo`, marca `biometric_status=PENDING_REVIEW`.

### Frontend Admin (`workspaces/web/admin`)
- Nova pagina:
  - `src/app/perfil/page.tsx`
- Recursos de UI:
  - formulario completo de perfil/endereco/documentos;
  - upload de arquivos;
  - digitalizacao por camera (`capture="environment"` e `capture="user"`);
  - visualizacao de imagens atuais;
  - status de biometria;
  - botao de logoff.
- Navegacao global:
  - item `Meu perfil` adicionado nos templates:
    - `admin-classic`
    - `admin-adminkit`
    - `admin-admindek`

## Tipos e integracao API no Admin
- `src/types/api.ts`:
  - `UserProfileData`
  - `UserDocumentType`
  - `UserBiometricStatus`
  - `UpdateUserProfilePayload`
- `src/lib/api.ts`:
  - `fetchMyUserProfile()`
  - `updateMyUserProfile()`
  - `uploadMyUserProfileFiles()`

## Testes executados

### Backend
- `ruff check src/apps/accounts tests/test_accounts_api.py`
- `black --check src/apps/accounts tests/test_accounts_api.py`
- `pytest tests/test_accounts_api.py` -> `10 passed`
- `python manage.py check`

### Frontend Admin
- `npm run lint`
- `npm run build`

## Pendencias tecnicas conhecidas
- Captura de biometria por foto esta implementada no cadastro/coleta; a etapa de validacao biometrica automatica/servico externo ainda depende de decisao de provider e requisitos de compliance.
