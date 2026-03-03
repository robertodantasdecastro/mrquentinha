# GestorServidor

TUI de monitoramento e gestao do ambiente de producao do ecossistema Mr Quentinha.
Layout visual alinhado ao padrao do modo dev (`scripts/ops_dashboard.py` -> `scripts/ops_center.py`):
- cabecalho de acoes rapidas
- linhas de sistema/rede com `percent_bar + sparkline`
- boxes operacionais de servicos e saude de dominios/API
- eventos recentes no rodape

## Executar

No diretorio raiz do repositorio:

```bash
bash gestor_servidor.sh
```

Recomendado: terminal minimo `120x32`.

Modo coleta unica (json):

```bash
bash gestor_servidor.sh --once
```

## Atalhos

- `q`: sair
- `r`: refresh imediato
- `z`: start stack `mrq-*`
- `x`: stop stack `mrq-*`
- `k`: restart stack `mrq-*`
- `1..7`: restart rapido (`nginx`, `postgres`, `ssh`, `backend`, `portal`, `client`, `admin`)
- Mouse: clique em `[start] [stop] [restart]` nos blocos de servico

## Arquitetura

- `GestorServidor/app.py`: TUI principal (`curses`)
- `GestorServidor/metrics.py`: metricas de host/rede
- `GestorServidor/healthchecks.py`: healthchecks HTTP + DNS
- `GestorServidor/services.py`: status e acao em servicos (`systemctl`)
- `GestorServidor/events.py`: logs locais de eventos/metricas

## Logs

Persistidos em:

- `.runtime/gestor-servidor/events.log`
- `.runtime/gestor-servidor/metrics.jsonl`
