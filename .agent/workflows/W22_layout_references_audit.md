---
id: W22
title: Auditoria de Referencias de Layout
description: Pesquisar e registrar referencias de layout/negocio e padroes de copy/CTA sem baixar assets.
inputs:
  - escopo (portal|client|ambos)
outputs:
  - docs/memory/LAYOUT_REFERENCES.md
commands:
  - ler GEMINI.md e AGENTS.md
  - mapear padroes de layout, secoes e CTAs existentes
  - registrar referencias de mercado e estrategia de copy
  - atualizar docs/memory/LAYOUT_REFERENCES.md
quality_gate:
  - layout clean, modular e reutilizavel com ui/TemplateProvider
memory_updates:
  - docs/memory/LAYOUT_REFERENCES.md
---

# W22 - Auditoria de Referencias de Layout

## Entrega
Gerar `docs/memory/LAYOUT_REFERENCES.md` com:
1. referencias visuais/estruturais por tela;
2. padroes de textos e CTA por contexto;
3. diretrizes reutilizaveis para portal/client.
