# Deploy na AWS EC2 (sem Docker)

## Visao
- EC2 Ubuntu
- Nginx como proxy reverso
- Gunicorn para Django
- PostgreSQL (inicialmente na VM/EC2; recomendado migrar para RDS depois)
- HTTPS com Let's Encrypt (certbot)

## Passos (macro)
1. Criar EC2 + Security Group (80/443/22)
2. Instalar dependencias (python, nginx, postgres se local)
3. Configurar `.env` em `/etc/<app>/env`
4. Configurar Gunicorn + systemd service
5. Configurar Nginx (server block)
6. Rodar migracoes e coletar estaticos
7. Habilitar HTTPS (certbot)
8. Configurar backups e logs

## Observacoes
- Media/static: no MVP pode ficar no disco; depois mover para S3 + CloudFront
- Segredos: nunca no repo; apenas no `.env` do servidor

## Nota: estrutura de dominios (planejada)
Esta estrutura esta documentada para orientar DNS, SSL e roteamento, sem implementacao nesta etapa:
- `www.mrquentinha.com.br` -> portal institucional
- `admin.mrquentinha.com.br` -> gestao web
- `api.mrquentinha.com.br` -> backend/API
- `app.mrquentinha.com.br` -> pagina de download e QR

## Nota de deploy do portal (Etapa 6)
Sem implementar nesta etapa, o deploy do portal pode seguir dois caminhos:
- Nginx reverse proxy para um processo Node.js (`next start`) dedicado ao portal.
- Build estatico do portal quando aplicavel, servido diretamente por Nginx.

Em ambos os cenarios, manter `www.mrquentinha.com.br` apontando para o frontend do portal e `api.mrquentinha.com.br` para o backend Django.
