# ADR-0020: OCR multicaptura para itens de compra no Web Admin

## Status
Aceito

## Contexto
O fluxo de compras precisava capturar evidencias de OCR por tipo de imagem
(rotulo frente, rotulo verso, foto do produto e etiqueta de preco), com
processamento separado e preenchimento assistido dos campos de compra.
Tambem era necessario manter fallback manual quando o OCR nao atingir
confianca suficiente.

## Decisao
- Evoluir o modelo `PurchaseItem` com campos dedicados para imagens de OCR:
  - `product_image`
  - `price_tag_image`
- Manter `label_front_image` e `label_back_image`, formando quatro entradas
  independentes para OCR de item.
- Evoluir `OCRKind` com novos tipos:
  - `PRODUCT`
  - `PRICE_TAG`
- Enriquecer `parsed_json` dos jobs de OCR com `recognized_ingredient` por
  matching com ingredientes cadastrados (exato/fuzzy com confianca).
- Permitir upload de imagem por `image_type` no endpoint de item de compra:
  `front|back|product|price`.
- No Web Admin (modulo Compras), incluir captura por camera/upload para os
  quatro tipos, processamento OCR individual por item e sugestao de
  preenchimento de `ingrediente`, `quantidade/unidade` e `preco`.
- Preservar preenchimento manual completo no formulario como fallback
  obrigatorio para dados nao reconhecidos.

## Consequencias
- Melhor rastreabilidade por tipo de evidencia visual no processo de compra.
- OCR passa a contribuir com sugestoes de preenchimento sem bloquear a
  operacao manual.
- Mais consistencia para alimentar composicao de pratos e calculo nutricional
  com base em insumos corretamente identificados.
- Pequeno aumento de complexidade no painel de compras e no contrato de API.

## Alternativas consideradas
- Usar somente uma imagem por item para OCR (insuficiente para rotulos e preco).
- Fazer OCR apenas apos salvar compra sem pre-validacao no formulario
  (pior feedback para o operador).
- Processar OCR sem reconhecimento de ingrediente no backend
  (perde ganho operacional no autopreenchimento).
