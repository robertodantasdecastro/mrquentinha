# Mr Quentinha - Admin Web

Aplicacao web de gestao interna em `workspaces/web/admin`.

Escopo atual (T9.0.3 concluida):
- shell inicial do admin;
- autenticacao real com JWT (`token`, `refresh`, `me`);
- dashboard operacional expandido;
- modulos operacionais conectados ao backend:
  - Pedidos (fila + mudanca de status);
  - Financeiro (KPIs + movimentos nao conciliados);
  - Estoque (saldo + movimentos);
  - Cardapio (menus e pratos baseline);
  - Compras (requisicoes e compras baseline);
  - Producao (lotes baseline).

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
- `T9.1.1`: evoluir os modulos de gestao para fluxo completo (CRUD e acoes operacionais de cardapio/compras/producao e usuarios/RBAC).
