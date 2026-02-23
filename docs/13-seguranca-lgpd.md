# Segurança e LGPD (mínimo necessário desde o início)

## Dados coletados
- cliente: nome, e-mail, telefone (opcional), histórico de pedidos e pagamentos
- interno: e-mail, perfis, ações (auditoria)
- financeiro: contas, despesas e receitas

## Boas práticas
- minimizar dados pessoais
- consentimento e finalidade clara (termos)
- logs sem vazar dados sensíveis
- senhas: se houver login local, usar hashing forte (Django já faz)

## Acesso
- RBAC obrigatório
- segregação de funções (financeiro não precisa editar cardápio, por exemplo)

## Retenção
- definir política de retenção de logs e dados (futuro)
- permitir exportação/remoção conforme necessário (fase 2)

## Checklist de segurança por release
- [ ] endpoints protegidos
- [ ] validação de input
- [ ] rate limiting (quando exposto)
- [ ] backups verificados
