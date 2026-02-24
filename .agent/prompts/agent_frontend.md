# Template - Agent Frontend

Objetivo:
- Implementar/ajustar telas no portal/client com Design System compartilhado.

Checklist de implementacao:
1. Reutilizar componentes de `workspaces/web/ui`.
2. Manter layout clean, responsivo e sem hardcode de conteudo operacional.
3. Integrar dados via `NEXT_PUBLIC_API_BASE_URL`.
4. Tratar estados de loading, vazio e erro de API.
5. Validar com:
   - `npm run lint`
   - `npm run build`
6. Atualizar README e memoria do projeto quando houver mudanca operacional.

Restricoes:
- Nao expor segredos no frontend.
- Nao quebrar temas light/dark.
