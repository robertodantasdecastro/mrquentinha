# Identidade visual — Mr Quentinha

Domínio: **www.mrquentinha.com.br**

## Ativos oficiais
Os arquivos oficiais estão em `assets/brand/`:

- `logo_wordmark.svg` — logo principal (nome + símbolo)
- `icon_symbol.svg` — símbolo (uso em favicon, marca d’água, etc.)
- `icon_app.svg` — ícone do app com fundo laranja
- `icon_app_transparent.svg` — ícone do app sem fundo (transparente)
- `png/` — exports em PNG (com transparência quando aplicável)

> **Recomendação prática:** para web, use SVG; para mobile e ícones, use PNG 1024/512.

## Cores (padrão)
- Primária (laranja): `#FF6A00`
- Secundária (grafite): `#1F1F1F`
- Acento (laranja claro): `#FF8A33`

### Light theme
- Background: `#FFFFFF`
- Surface: `#F6F6F6`
- Texto: `#141414`

### Dark theme
- Background: `#0F0F12`
- Surface: `#17171C`
- Texto: `#F4F4F5`

Tokens prontos:
- `assets/brand/tokens.css`
- `assets/brand/tokens.json`

## Tipografia (sugestão)
- Primária: **Poppins**
- Alternativa: Montserrat

## Regras rápidas de uso da marca
1. **Não distorcer** o símbolo (manter proporção).
2. Preferir a logo principal em fundo claro e a variante ícone em fundos sólidos.
3. Manter “área de respiro”: pelo menos 16px ao redor do símbolo em interfaces.
4. Em dark mode, usar o símbolo com grafite e laranja (evitar preto puro).

## Como incorporar no frontend (web)
- Importar `assets/brand/tokens.css` (ou copiar para o projeto web).
- Definir atributo `data-theme="dark"` no `html` ou `body` quando em dark mode.
- Usar variáveis CSS:
  - `var(--mrq-primary)` etc.

## Como incorporar no mobile (React Native)
- Usar `assets/brand/tokens.json` como fonte de verdade
- Criar um módulo `theme.ts` com `colors` para light/dark
- Carregar os ícones em:
  - Android: `mipmap-...`
  - iOS: `Assets.xcassets`



## Ativos já copiados para os workspaces (facilitar integração)
- Web: `workspaces/web/public/brand/`
- Backend (static): `workspaces/backend/static/brand/`
- Mobile: `workspaces/mobile/assets/brand/`
