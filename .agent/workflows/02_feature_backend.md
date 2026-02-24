---
description: Entrega de feature backend Django/DRF com service layer, testes e memoria atualizada.
---

# Workflow 02 - Feature Backend

1. Criar branch (`codex/<escopo-curto>`).
2. Implementar no padrao: `services`, `selectors`, `serializers`, `views`, `urls`, `tests`.
3. Gerar e aplicar migracoes quando necessario.
4. Validar com:
   - `python manage.py check`
   - `make lint`
   - `make test`
5. Atualizar memoria (`PROJECT_STATE`, `CHANGELOG`, `DECISIONS`) e README relacionado.
6. Commitar e fazer push.
