# Tema (Mobile)

- Use `theme.ts` como base.
- Para alternar dark/light: usar preferências do sistema e aplicar nos componentes.
- Ícones/Logo: usar os PNG em `assets/brand/png/` (1024/512).
- Conteudo dinamico (portal/cardapio/fotos): usar `contentApi.ts`.
- Endpoint base do backend deve apontar para `/api/v1` e retornar `image_url` para pratos e insumos.
- Parametros de autenticacao social (Google/Apple) devem ser consumidos via `auth_providers` no payload de `/api/v1/portal/config/?channel=client&page=home` e administrados no Web Admin.
- Parametros publicos de pagamentos (roteamento/metodos/providers habilitados) devem ser consumidos via `payment_providers` no payload de `/api/v1/portal/config/?channel=client&page=home`.
