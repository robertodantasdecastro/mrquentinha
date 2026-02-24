# Recovery Template (Read-Only)

## Objetivo
Registrar diagnostico de ambiente/projeto sem alterar arquivos de codigo ou configuracao.

## Contexto do incidente
- Data/hora:
- Sintoma principal:
- Ultima acao antes da falha:

## Checklist read-only
1. Estado git:
  - branch atual
  - `git status --porcelain`
  - ultimos commits/reflog
2. Estado de processos:
  - processos backend/frontend
  - portas 8000/3000/3001
3. Logs relevantes:
  - logs temporarios
  - erros recorrentes
4. Comparativo docs vs implementacao:
  - divergencias encontradas

## Diagnostico
- Causa provavel:
- Impacto:
- Risco de regressao:

## Plano de recuperacao
- Plano A (normal):
- Plano B (locks/processos):
- Plano C (deps/venv/node):

## Proximos passos
- Acao recomendada:
- Dono da acao:
- Prazo:
