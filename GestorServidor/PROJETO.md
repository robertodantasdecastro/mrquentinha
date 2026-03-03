# GestorServidor - Projeto (TUI de Producao)

## Status
- MVP implementado em `GestorServidor/app.py`.
- Fase 2 (auditoria integrada ao Web Admin) permanece pendente.

## Objetivo
Criar um aplicativo TUI (terminal) para monitorar e gerenciar o ambiente de producao da EC2, cobrindo todo o ecossistema Mr Quentinha. Deve funcionar via SSH ou console local, com foco em tempo real, baixa carga e operacao segura.

## Escopo
- Monitoramento em tempo real:
  - CPU, memoria, swap, disco, load average, processos criticos.
  - Rede: throughput, conexoes abertas, latencia externa, DNS, IP publico/local.
  - Servicos essenciais: Nginx, Postgres, SSH, e servicos do stack Mr Quentinha.
  - Saude dos apps: portal, web client, web admin, API local e publica, mobile.
- Gestao operacional:
  - start/stop/restart de servicos e stack.
  - logs recentes e eventos operacionais.
  - alertas de anomalia (ex.: latencia, erro HTTP, uso de recursos, falhas de DNS).
- Auditoria (fase 2):
  - persistir logs e metricas para integracao com Web Admin.

## Regras de seguranca
- Nunca gravar credenciais/tokens/chaves no repositorio.
- Qualquer segredo deve permanecer em:
  - `~/.codex/secure`
  - `~/.mrquentinha-secure`

## Identidade e UX (TUI)
- Visual inspirado no btop (cores, barras, graficos, spark lines).
- Interacao estilo mc (mouse habilitado, janelas e modais).
- Atalhos de teclado e clique para acoes rapidas.

## Recursos existentes a reaproveitar
### Scripts e apps atuais
- `scripts/ops_center.py` (TUI dev com graficos, logs e controle dos servicos dev).
- `scripts/ops_center_prod.py` (TUI prod com systemctl, checagens DNS e dominios).
- `scripts/ops_dashboard_prod.py` + `scripts/start_ops_dashboard_prod.sh` (launcher prod).
- `scripts/setup_nginx_prod.sh` (vhosts prod e dominios oficiais).
- `scripts/ops_ssl_cert.sh` (certbot para SSL).
- `scripts/start_vm_prod.sh` / `scripts/stop_vm_prod.sh` (stack prod systemd).
- `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh` (smokes dev).
- `scripts/sync_dev_then_prod.sh` (deploy em duas fases).

### O que vamos reaproveitar diretamente
- Bibliotecas e patterns TUI (curses) do `ops_center.py`.
- Healthchecks e DNS do `ops_center_prod.py`.
- Chamada de `systemctl` e comandos de stack.
- Smokes e checagens HTTP dos scripts existentes.

## Fluxo ao abrir o app
1. Detectar IP local e IP publico.
2. Resolver DNS de `mrquentinha.com.br` e subdominios (www/app/admin/api).
3. Comparar IP publico com o IP do DNS.
4. Reportar divergencias e alertas.

## Tela e modulos (proposta)
1. Dashboard principal
   - CPU, RAM, SWAP, Disk, Load.
   - Rede: RX/TX, conexoes abertas.
   - Servicos: status (systemctl) + PID/uptime.
2. Saude do ecossistema
   - HTTP status para:
     - `https://www.mrquentinha.com.br`
     - `https://app.mrquentinha.com.br`
     - `https://admin.mrquentinha.com.br`
     - `https://api.mrquentinha.com.br/api/v1/health`
     - `https://web.mrquentinha.com.br` (legado: 404 esperado)
   - API local: `http://127.0.0.1:8000/api/v1/health`
3. Controle de servicos
   - Nginx, Postgres, SSH, backend, portal, client, admin.
   - Acoes: start/stop/restart, com confirmacao modal.
4. Eventos e logs
   - Logs tail (por servico).
   - Eventos do gestor (acoes e alertas).
5. Diagnosticos
   - DNS mismatch, latencia alta, erro 5xx repetitivo, uso de disco alto.

## Mapa de dados/metricas (fase 1)
- `psutil` (CPU/mem/disk/net/process)
- `systemctl` (status servicos)
- `curl` (HTTP status + health)
- DNS: `dig`/`getent hosts`/`socket.gethostbyname`
- IP publico: `https://checkip.amazonaws.com`

## Persistencia de logs (fase 2)
- Diretorio sugerido: `.runtime/gestor-servidor/`
  - `events.log`
  - `metrics.jsonl`
- Integracao futura com Web Admin via API admin (somente leitura).

## Arquitetura proposta
- Linguagem: Python 3 (curses + psutil + subprocess)
- Estrutura:
  - `GestorServidor/app.py` (entrypoint TUI)
  - `GestorServidor/metrics.py`
  - `GestorServidor/healthchecks.py`
  - `GestorServidor/services.py`
  - `GestorServidor/ui/` (painels/modais/temas)
  - `GestorServidor/logging.py` (eventos + persistencia)

## Comandos previstos
- `~/mrquentinha/gestor_servidor.sh` (launcher)
- Flags futuras:
  - `--dev` / `--prod`
  - `--headless` (somente logs)
  - `--interval 2s`

## Fases
- **Fase 1 (MVP)**: dashboard + status + controles + smokes.
- **Fase 2 (Auditoria)**: persistencia e integracao com Web Admin.
- **Fase 3 (Anomalias)**: thresholds configuraveis e alertas automatizados.

## Dependencias
- `python3`, `psutil`, `curses` (stdlib)
- `curl`, `systemctl`, `ss`/`lsof` (quando disponivel)

## Riscos
- Carga excessiva em t3.micro: atualizar com baixa frequencia.
- Permissoes de `systemctl`: usar `sudo -n` e fallback read-only.

## Criterios de aceite
- Dashboard abre via terminal/ssh.
- Status em tempo real com servicos e dominios oficiais.
- Acoes start/stop/restart funcionam com confirmacao.
- Logs e eventos gravados localmente (fase 2).
