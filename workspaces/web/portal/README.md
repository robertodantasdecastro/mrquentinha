# Portal Institucional - Mr Quentinha

Frontend institucional em Next.js (App Router) para `www.mrquentinha.com.br`.

## Escopo da Etapa 6.0
- Home institucional em `/`
- Consulta de cardapio em `/cardapio`
- Pagina do app com QR Code em `/app`
- Contato em `/contato`
- Links de navegacao para:
  - Gestao web (`admin.mrquentinha.com.br`)
  - Area do cliente (`app.mrquentinha.com.br`)

## Tecnologias
- Next.js + TypeScript
- Tailwind CSS
- `qrcode.react` para QR Code

## Rodando localmente
1. Instale dependencias:
```bash
npm install
```
2. Configure variaveis de ambiente:
```bash
cp .env.example .env.local
```
3. Inicie o servidor:
```bash
npm run dev
```
4. Acesse:
- [http://localhost:3000](http://localhost:3000)

## Variaveis de ambiente
- `NEXT_PUBLIC_API_BASE_URL`: base da API backend.

Exemplo para VM:
```env
NEXT_PUBLIC_API_BASE_URL=http://10.211.55.21:8000
```

## Build de producao
```bash
npm run build
npm run start
```

## Integracao de Cardapio (API)
A pagina `/cardapio` consulta:
- `GET {NEXT_PUBLIC_API_BASE_URL}/api/v1/catalog/menus/by-date/YYYY-MM-DD/`

Se nao existir cardapio para a data, a interface exibe fallback amigavel.

## Download do App (placeholders)
Arquivo:
- `src/components/QRDownloadCard.tsx`

Constantes para trocar quando os links oficiais estiverem publicados:
- `ANDROID_DOWNLOAD_URL`
- `IOS_DOWNLOAD_URL`
