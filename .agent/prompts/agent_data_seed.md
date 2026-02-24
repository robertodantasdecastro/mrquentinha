# Template - Agent Data Seed

Objetivo:
- Gerar dados DEMO consistentes para fluxo ponta a ponta (catalogo -> pedidos -> financeiro -> OCR).

Checklist:
1. Garantir idempotencia do seed (reexecucao segura).
2. Criar dados realistas para:
   - ingredientes e receitas
   - cardapios por data
   - compras/estoque/producao
   - pedidos/pagamentos/financeiro
3. Midia/OCR no MVP:
   - gerar imagens sinteticas localmente (sem internet)
   - criar jobs OCR e aplicar em alvos
4. Validar smoke e testes apos seed.
5. Documentar comandos no RUNBOOK/README.

Restricoes:
- Sem dados sensiveis reais.
- Sem dependencias externas obrigatorias para dados de demo.
