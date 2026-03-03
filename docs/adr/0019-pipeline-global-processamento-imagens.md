# ADR-0019: Pipeline global de processamento de imagens

## Status
Aceito

## Contexto
Uploads de imagem acontecem em diferentes pontos do ecossistema (catalogo,
perfil de usuario, compras e OCR), com fluxos manuais e automaticos.
Sem um pipeline unico, cada tela/processo podia gerar arquivos com proporcoes,
resolucao e enquadramento inconsistentes, impactando UX e desempenho.

## Decisao
- Introduzir pipeline global no backend para processar `ImageField` em todos os
  apps relevantes via sinal `pre_save`.
- Definir perfis por contexto:
  - `catalog.dish.image`: corte central `1200x900`.
  - `catalog.ingredient.image`: corte central `1000x1000`.
  - `accounts/procurement/ocr`: redimensionamento proporcional (`contain`) com
    limites maximos por tipo de imagem.
- Aplicar o processamento tanto para upload manual (`_committed=False`) quanto
  para fluxos automaticos (`field.save(..., save=False)` + `save(update_fields=[...])`).
- Complementar no Web Admin (modulo de cardapio) com preparacao client-side
  de corte central e resize antes do envio, para feedback imediato ao operador.

## Consequencias
- Consistencia visual das imagens do cardapio em `admin`, `portal` e `client`.
- Menor variacao de tamanho de arquivo e melhor previsibilidade de renderizacao.
- Fluxos automaticos passam a obedecer o mesmo padrao dos fluxos manuais.
- A aplicacao ganha acoplamento explicito ao Pillow no processamento de upload.

## Alternativas consideradas
- Processamento somente no frontend (insuficiente para fluxos automaticos).
- Processamento por endpoint/serializer (alto risco de divergencia entre modulos).
- Worker assíncrono para pos-processamento (complexidade operacional desnecessaria
  para o estagio atual do projeto).
