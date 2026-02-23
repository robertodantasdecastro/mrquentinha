# Prompt — Aplicar identidade visual (Web/Mobile)

Tarefa: incorporar a identidade visual do **Mr Quentinha** no frontend.

Referências:
- `assets/brand/` (logo e ícones)
- `assets/brand/tokens.css` e `assets/brand/tokens.json`
- `docs/14-identidade-visual.md`

Entregas (Web):
1) Importar tokens CSS (ou replicar como design tokens do projeto)
2) Implementar suporte a `light/dark mode` com `data-theme="dark"`
3) Aplicar `--mrq-primary` como cor primária em botões, links e elementos de destaque
4) Inserir a logo `logo_wordmark.svg` no header e `icon_symbol.svg` como favicon

Entregas (Mobile):
1) Criar `theme.ts` (se não existir) com base em `tokens.json`
2) Aplicar tema em componentes e navegação (light/dark)
3) Incorporar `icon_app_1024.png` ou `icon_app_transparent_1024.png` como ícone do app
4) Inserir logo em splash screen (quando houver)

DoD:
- build roda
- sem hardcode de cores (usar tokens/tema)
- documentação atualizada
