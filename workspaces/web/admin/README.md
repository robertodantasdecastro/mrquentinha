# Mr Quentinha - Admin Web

Aplicacao web de gestao interna em `workspaces/web/admin`.

Escopo da subetapa `T9.0.1`:
- shell inicial do admin;
- autenticacao real com JWT (`token`, `refresh`, `me`);
- dashboard inicial de operacao;
- modulos exibidos como trilha de execucao para `T9.0.2`.

## Stack
- Next.js (App Router) + TypeScript
- TailwindCSS
- UI compartilhada via `@mrquentinha/ui`

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

## Como rodar
```bash
cd workspaces/web/admin
npm install
npm run dev -- --hostname 0.0.0.0 --port 3002
```

Acesse:
- `http://localhost:3002/`

## Qualidade
```bash
npm run lint
npm run build
```

## Proximas etapas
- `T9.0.2`: modulos operacionais reais (Pedidos, Financeiro, Estoque) integrados ao backend.
