# Mr Quentinha - Web Cliente

Aplicacao web para clientes em `workspaces/web/client`, separada do portal institucional.

Stack:
- Next.js (App Router) + TypeScript
- TailwindCSS
- Integracao com backend via `NEXT_PUBLIC_API_BASE_URL`

## Funcionalidades da etapa 7.1
- Consulta de cardapio por data
- Carrinho local com quantidade e total
- Criacao de pedido autenticada (`POST /api/v1/orders/orders/`)
- Historico de pedidos autenticado (`GET /api/v1/orders/orders/`)
- Confirmacao de recebimento pelo cliente (`POST /api/v1/orders/orders/{id}/confirm-receipt/`)
- Conta do cliente com:
  - cadastro (`POST /api/v1/accounts/register/`)
  - login JWT (`POST /api/v1/accounts/token/`)
  - refresh de token (`POST /api/v1/accounts/token/refresh/`)
  - perfil autenticado (`GET /api/v1/accounts/me/`)
- Tema light/dark com identidade da marca

## Requisitos
- Node.js 20+
- NPM 10+
- Backend Django online

## Variaveis de ambiente
Crie `.env.local` a partir do exemplo:

```bash
cp .env.example .env.local
```

Arquivo `.env.local`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://10.211.55.21:8000
```

Notas:
- `NEXT_PUBLIC_API_BASE_URL` deve apontar para a API Django acessivel da sua VM.
- O token JWT e armazenado no `localStorage` do navegador no client.

## Como rodar
```bash
cd workspaces/web/client
npm install
npm run dev
```

## Subida rapida por script (root)
No root do repositorio (`~/mrquentinha`):

```bash
./scripts/start_client_dev.sh
```

Comportamento do script:
- encerra processo antigo do `next dev` na porta `3001` (SIGINT e depois SIGTERM);
- remove lock stale em `workspaces/web/client/.next/dev/lock` quando nao houver processo ativo;
- define default de ambiente se nao estiver exportado:
  - `NEXT_PUBLIC_API_BASE_URL=http://<IP_PRIMARIO_DA_VM>:8000` (fallback `127.0.0.1:8000`)
- sobe o client em `http://0.0.0.0:3001`.

Se voce quiser validar especificamente em `localhost:3000` (sem portal na mesma porta):

```bash
CLIENT_PORT=3000 ./scripts/start_client_dev.sh
```

Smoke test automatizado:

```bash
./scripts/smoke_client_dev.sh
```

Esse smoke valida:
- `GET /` -> `200`
- `GET /pedidos` -> `200`
- `GET /cardapio` -> `200`

Acesse:
- `http://localhost:3001/`
- `http://localhost:3001/pedidos`
- `http://localhost:3001/conta`

Fluxo recomendado:
1. `http://localhost:3001/conta` -> login/cadastro.
2. `http://localhost:3001/cardapio` -> selecionar pratos e finalizar pedido.
3. `http://localhost:3001/pedidos` -> acompanhar entrega e confirmar recebimento.

## Qualidade
```bash
npm run lint
npm run build
```

## Security Notes
- Comando executado: `npm audit fix` (sem `--force`).
- Resultado atual: ainda restam vulnerabilidades `high` na cadeia de lint (`minimatch` via `eslint` e plugins do `eslint-config-next`).
- O `npm audit` indica que a correcao automatica exige `npm audit fix --force` com upgrade breaking de `eslint`.
- Plano MVP:
  - manter sem `--force` agora para nao quebrar toolchain;
  - revisar compatibilidade e atualizar stack de lint antes do deploy de producao;
  - reexecutar `npm audit` apos atualizar dependencias de lint.

## Marca
- Assets de marca em `public/brand` (espelhados do portal para manter independencia do app cliente).
