# Template - Agent Backend

Objetivo:
- Implementar/ajustar funcionalidade backend no padrao Django + DRF.

Checklist de implementacao:
1. Definir impacto em dominio/apps.
2. Implementar em camadas:
   - `services.py` (regra de negocio)
   - `selectors.py` (consultas)
   - `serializers.py` (entrada/saida/validacao)
   - `views.py` + `urls.py` (API)
   - `tests/` (service + API + regressao)
3. Rodar validacao:
   - `python manage.py check`
   - `make lint`
   - `make test`
4. Atualizar docs de memoria e README quando necessario.

Restricoes:
- Sem segredos em codigo/docs.
- Evitar logica de negocio em views/models alem do minimo.
