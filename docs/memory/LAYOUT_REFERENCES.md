# Referências de Layout & UX (Sessão Antigravity)

Este documento registra as fontes de inspiração visual para o novo design system e template `letsfit-clean` do portal institucional do Mr Quentinha, assim como as imagens livres que serão incorporadas. Todo o material visual foi reinterpretado para a identidade do Mr Quentinha (Dark/Light mode + Cor primária Laranja).

## Fontes de Inspiração (Páginas Referenciais)
*Apenas estruturação, CTA arrays, micro-interações e heurísticas de venda foram extraídas; Nenhum texto ou HTML/CSS literal.*

- [LetsFit SP](https://letsfitsp.com.br/) - Base para a Hero com 2 CTAs, barra flutuante de benefícios e clean design.
- [Liv Up](https://www.livup.com.br/) - Base para demonstração de "Como Funciona" e grid arredondado para categorias.
- [Frutifica](https://www.frutifica.com.br/) - Referência de cardápios (display de tags como "Low Carb", "Sem Glúten").
- [FitDelivery](https://fitdeliveryonline.com/) - Arquitetura de "Monte seu Kit" rápido (simulador de compra/escolha).
- [NFit](https://nfit.com.br/) / [GymChef](https://gymchef.com.br/) - Prova social com foco em performance e praticidade.

## Seções Escolhidas e Adaptação ("letsfit-clean")
1. **Hero Header**: CTA "Ver cardápio de hoje" + "Como funciona". Texto com foco em rápido e prático.
2. **Benefits Bar**: Ícones pequenos ou micro-textos ("Pronto em 5 min", "Entrega Agendada", "VR/VA").
3. **Categorias (Cards)**: Grid com opções como "Dia a dia", "Low Carb", "Performance", etc.
4. **Cardápio Interativo ("Simulador/Vitrine")**: Consumindo dados via GET API.
5. **Preparo e Conservação ("Como Aquecer")**: Step-by-step visual para microondas.
6. **Social Proof (FAQ/Depoimentos)**: Layout com sanfona/accordion.

## Imagens e Ativos (Unsplash / Pexels)
*(Banco de imagens gratuitas e link direto / hotlink utilizado antes de persistir no bucket definitivo se necessário)*

| Imagem/Seção | Preview | Fonte Original | Descrição / Uso |
|--------------|---------|----------------|-----------------|
| Hero Background | `https://images.unsplash.com/photo-1546069901-ba9599a7e63c` | Unsplash - @lqazi | Bowl saudável na Hero |
| Categoria "Performance" | `https://images.unsplash.com/photo-1603569283847-aa295f0d016a` | Unsplash - @lucasmourao | Refeição fit focada em proteína |
| Categoria "Vegetariano" | `https://images.unsplash.com/photo-1512621776951-a57141f2eefd` | Unsplash - @brookelark | Salada e vegetais |
| "Como Funciona" / Praticidade | `https://images.unsplash.com/photo-1579113800032-c38bd7635818` | Unsplash - @sashamaries | Pessoa comendo de marmita/recipiente em casa/trabalho |

> **Nota de Implementação**: As imagens são tratadas via `<Image>` component do NextJS consumindo Unsplash diretamente ou placeholders padronizados para não sobrecarregar o repositório no `public/`.
