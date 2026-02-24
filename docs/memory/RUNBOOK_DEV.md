# Runbook DEV (stack completo)

## 1) Subir stack local
No root (`~/mrquentinha`), em terminais separados:

```bash
./scripts/start_backend_dev.sh
```

```bash
./scripts/start_portal_dev.sh
```

```bash
./scripts/start_client_dev.sh
```

Acessos:
- API: `http://127.0.0.1:8000`
- Portal: `http://127.0.0.1:3000`
- Web Cliente: `http://127.0.0.1:3001`

## 2) Rodar smoke
Validacao automatica ponta a ponta:

```bash
./scripts/smoke_stack_dev.sh
```

Validacao rapida so do client:

```bash
./scripts/smoke_client_dev.sh
```

## 3) Seed DEMO
Com backend pronto:

```bash
./scripts/seed_demo.sh
```

O seed e idempotente e pode ser reexecutado no ambiente de desenvolvimento.

## 4) Testar OCR (MVP simulado)
### 4.1 Criar OCR job (multipart)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/ocr/jobs/ \
  -F "kind=LABEL_FRONT" \
  -F "image=@/caminho/arquivo.png" \
  -F "raw_text=Produto: Arroz Tipo 1\nMarca: Demo\nPorcao: 50 g\nValor energetico 180 kcal\nCarboidratos 38 g\nProteinas 3.5 g\nGorduras totais 0.5 g\nGorduras saturadas 0.1 g\nFibra alimentar 1.0 g\nSodio 2 mg"
```

### 4.2 Aplicar OCR em ingrediente
```bash
curl -X POST http://127.0.0.1:8000/api/v1/ocr/jobs/<JOB_ID>/apply/ \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "INGREDIENT",
    "target_id": 1,
    "mode": "merge"
  }'
```

## 5) Fluxo operacional completo para testes
1. Catalogo:
- criar/ajustar ingredientes e pratos
- criar cardapio do dia (`MenuDay` + `MenuItem`)

2. Compras/Estoque:
- registrar `Purchase` com `PurchaseItem`
- conferir `StockMovement IN` e saldo de `StockItem`

3. Producao:
- criar `ProductionBatch` para data
- completar lote (`/complete/`) para gerar `StockMovement OUT`

4. Pedidos:
- criar `Order` com itens do cardapio da data
- validar total e `Payment PENDING`

5. Financeiro:
- confirmar geracao de AP por compra
- confirmar geracao de AR por pedido
- marcar pagamento como `PAID` e validar entrada de caixa + ledger
- consultar `cashflow`, `dre` e `kpis`

## 6) Troubleshooting
- DisallowedHost em DEV:
  - ajustar `ALLOWED_HOSTS` em `workspaces/backend/.env` para incluir IP/host de acesso.
  - ajustar `CSRF_TRUSTED_ORIGINS` para as origens usadas pelo portal/client.

- CORS bloqueando frontend:
  - revisar `CORS_ALLOWED_ORIGINS` no `.env` do backend.
  - garantir que a origem exata (`http://IP:porta`) esteja na lista.

- Lock do Next no client (`.next/dev/lock`):
  - encerrar processo legado da porta 3001.
  - remover apenas o lock stale:
    - `rm -f workspaces/web/client/.next/dev/lock`

- Porta ocupada em smoke:
  - checar listeners:
    - `ss -ltnp | grep -E ':8000|:3000|:3001'`
  - reexecutar smoke apos liberar as portas.

## 7) Qualidade antes de PR
Backend:

```bash
cd workspaces/backend
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
make lint
make test
```

Root:

```bash
make test
pytest
```

Portal:

```bash
cd workspaces/web/portal
npm run lint
npm run build
```

Client:

```bash
cd workspaces/web/client
npm run lint
npm run build
```
