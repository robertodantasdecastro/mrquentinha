# Instruções do Projeto (Codex)

> Este arquivo é lido automaticamente pelo Codex antes de qualquer trabalho.
> Ele define as **regras do projeto**, o **padrão de arquitetura** e o **Definition of Done**.

## 1) Objetivo do produto
Construir o ecossistema **Mr Quentinha** (www.mrquentinha.com.br) para pedidos de marmitas com:
- App mobile (cliente) para escolher cardápio por data, pagar e acompanhar pedidos
- Portal web (gestão) para administrar cardápios, estoque, compras (com OCR) e **gestão financeira completa**
- Backend único (API) com autenticação e autorização por perfis (RBAC)

## 2) Regras inegociáveis
1. **Sem Docker/containers** no desenvolvimento local e no deploy inicial.
2. Banco de dados: **PostgreSQL**.
3. Backend: **Django + Django REST Framework (DRF)**.
4. Código orientado a objetos e separação por camadas (domínio, aplicação, infra).
5. Tudo com **testes automatizados** (mínimo: unitário e API).
6. Comentários e documentação em **português**.
7. Nunca inserir segredos no repositório. Use `.env.example` e variáveis de ambiente.
8. Cada mudança deve ser pequena e revisável: **um PR/commit por tarefa**.

## 3) Padrão arquitetural (resumo)
- Organização por domínios (apps Django): `accounts`, `catalog`, `inventory`, `procurement`, `orders`, `finance`, `ocr_ai`.
- “Service layer” para regras de negócio (evitar lógica complexa em views/models).
- Repositórios/Query services (selectors) para leitura.
- DTOs / schemas para entradas e saídas (serializers + dataclasses quando útil).

## 4) Definition of Done (DoD)
Uma tarefa só é considerada “pronta” se:
- [ ] Compila/roda localmente
- [ ] Testes passam (`pytest` ou `python manage.py test`)
- [ ] Cobertura mínima do que foi criado/alterado
- [ ] Lint/format (ruff/black) sem erros
- [ ] Migrações criadas quando necessário
- [ ] Documentação atualizada (pelo menos `docs/memory/CHANGELOG.md` + ADR quando mudar arquitetura)
- [ ] Segurança básica revisada (permissões, validações, dados sensíveis)

## 5) Como responder em tarefas
Ao implementar algo, sempre:
- Diga **o que foi mudado** (lista de arquivos)
- Diga **como testar** (comandos)
- Se houver decisão arquitetural, crie/atualize um ADR em `docs/adr/`

## 6) Arquivos de referência obrigatória
- `docs/02-arquitetura.md`
- `docs/03-modelo-de-dados.md`
- `docs/05-auth-rbac.md`
- `docs/10-plano-mvp-cronograma.md`


## 7) Identidade visual (obrigatório em UI)
- Nome oficial: **Mr Quentinha**
- Domínio: **www.mrquentinha.com.br**
- Tokens e logo ficam em `assets/brand/`.
- Ao criar telas (web/mobile), use:
  - `assets/brand/tokens.css` (web)
  - `assets/brand/tokens.json` (mobile/web)
- Exigir suporte a **light/dark mode** e usar `#FF6A00` como cor primária.
