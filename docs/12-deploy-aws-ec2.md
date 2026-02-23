# Deploy na AWS EC2 (sem Docker)

## Visão
- EC2 Ubuntu
- Nginx como proxy reverso
- Gunicorn para Django
- PostgreSQL (inicialmente na VM/EC2; recomendado migrar para RDS depois)
- HTTPS com Let's Encrypt (certbot)

## Passos (macro)
1. Criar EC2 + Security Group (80/443/22)
2. Instalar dependências (python, nginx, postgres se local)
3. Configurar `.env` em `/etc/<app>/env`
4. Configurar Gunicorn + systemd service
5. Configurar Nginx (server block)
6. Rodar migrações e coletar estáticos
7. Habilitar HTTPS (certbot)
8. Configurar backups e logs

## Observações
- Media/static: no MVP pode ficar no disco; depois mover para S3 + CloudFront
- Segredos: nunca no repo; apenas no `.env` do servidor
