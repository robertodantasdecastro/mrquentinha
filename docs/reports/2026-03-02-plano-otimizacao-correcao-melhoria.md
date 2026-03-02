# Plano de Otimizacao, Correcao e Melhorias
Data: 02/03/2026
Status: PROPOSTA (aguardando aprovacao)

## Objetivo
Reduzir riscos de seguranca e aumentar robustez operacional sem regressao funcional.

## Priorizacao
- `P0` = executar imediatamente (risco critico/alto).
- `P1` = curto prazo (hardening importante).
- `P2` = melhoria estrutural.

## Fase P0 (Seguranca e disponibilidade)
1. Proteger midias sensiveis (`accounts/documents/*`, `accounts/biometric/*`)
- Acoes:
  - remover exposicao direta de `/media/*` em producao;
  - criar fluxo de acesso autenticado/autorizado para arquivos privados;
  - manter apenas midia publica realmente publica.
- Criterio de aceite:
  - URL direta de documento/biometria retorna 401/403 para nao autorizados;
  - owner/admin continuam com acesso controlado.

2. Corrigir selecao de settings no backend CLI/scripts
- Acoes:
  - tornar `DJANGO_SETTINGS_MODULE` deterministico em todos fluxos;
  - ajustar scripts que dependem apenas de `.env`.
- Criterio de aceite:
  - `manage.py check --deploy`, `migrate`, `seed` funcionam com settings esperadas sem export manual.

3. Rotacionar `SECRET_KEY` de producao e normalizar segredos
- Acoes:
  - gerar chave forte;
  - aplicar sem vazar em Git;
  - validar impactos de assinatura/token.
- Criterio de aceite:
  - `check --deploy` sem `security.W009`.

## Fase P1 (Hardening de borda)
4. Forcar HTTPS total e cabecalhos de seguranca
- Acoes:
  - redirect 80->443 no Nginx;
  - habilitar HSTS com rollout seguro;
  - configurar headers de seguranca (nosniff, referrer-policy, frame policy conforme necessidade).
- Criterio de aceite:
  - `check --deploy` sem `W004/W008`;
  - validacao externa de headers por dominio.

5. Revisar CORS/CSRF por ambiente
- Acoes:
  - produzir lista estrita em prod (somente HTTPS oficiais);
  - manter flexibilidade apenas no dev.
- Criterio de aceite:
  - origens HTTP/privadas nao entram em `.env.prod`.

6. Endurecer webhooks
- Acoes:
  - usar `compare_digest` para tokens;
  - adicionar rate-limits e observabilidade de tentativas invalidas.
- Criterio de aceite:
  - validacao constante + metricas de rejeicao ativas.

## Fase P2 (Estrutural e manutencao)
7. Reduzir duplicacao frontend
- Acoes:
  - extrair logica comum de runtime API routes para modulo compartilhado;
  - reduzir duplicacao de `next.config` e storage JWT.
- Criterio de aceite:
  - fonte unica para logica de runtime/configuracao.

8. Fortalecer pipeline de seguranca
- Acoes:
  - incluir `pip-audit` e `bandit` no fluxo de quality gate;
  - manter `npm audit` automatizado.
- Criterio de aceite:
  - relatorios de seguranca gerados em toda entrega.

9. Revisar estrategia de sessao JWT no frontend
- Acoes:
  - avaliar migracao de token para cookie HttpOnly + CSRF token;
  - plano de transicao sem interromper app/client/admin.
- Criterio de aceite:
  - PoC validada em ambiente de homologacao.

## Ordem sugerida de execucao
1. P0.1 proteger midia sensivel
2. P0.2 corrigir settings deterministicas
3. P0.3 rotacionar `SECRET_KEY`
4. P1.4 HTTPS/hardening headers
5. P1.5 CORS/CSRF strict
6. P1.6 webhooks hardening
7. P2.x melhorias estruturais

## Estimativa de esforco (baixa granularidade)
- P0: 1 a 2 dias uteis
- P1: 1 a 2 dias uteis
- P2: 2 a 4 dias uteis (incremental)

