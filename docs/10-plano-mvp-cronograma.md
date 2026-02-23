# Plano do MVP + cronograma sugerido

> Data de referencia: 23/02/2026

## Status atual do roadmap
- **Etapa 0**: concluida
- **Etapa 1**: concluida
- **Etapa 2**: concluida
- **Etapa 3 / 3.1**: concluida
- **Etapa 4 (Orders)**: concluida
- **Etapa 5 (Finance)**: em planejamento detalhado (subfases 5.0 a 5.5)

## Escopo do MVP operacional
O MVP operacional permanece limitado ate a **Etapa 5**:
- base da plataforma
- catalogo
- estoque/compras
- pedidos
- financeiro integrado (AP/AR/Caixa/relatorio minimo)

## Etapa 5 (plano por subfases)
| Subfase | Foco |
| --- | --- |
| 5.0 | Fundacao |
| 5.1 | AP (compras) |
| 5.2 | AR (pedidos) |
| 5.3 | Caixa |
| 5.4 | Producao |
| 5.5 | Custos/Relatorios |

## Detalhe resumido da Etapa 5
- **5.0 Fundacao**: entidades financeiras base, contas, categorias, referencia por origem e validacoes.
- **5.1 AP (compras)**: gerar e liquidar contas a pagar com origem em `Purchase`.
- **5.2 AR (pedidos)**: gerar e liquidar contas a receber com origem em `Order`.
- **5.3 Caixa**: movimentos de entrada/saida, conciliacao e saldo diario.
- **5.4 Producao**: consolidar rotinas operacionais e preparar modulo dedicado de producao.
- **5.5 Custos/Relatorios**: fechamento com visoes de resultado, custos e indicadores basicos.

## Pos-MVP
### Etapa 6 - Portal institucional + distribuicao digital
- Escopo: site institucional, links oficiais e pagina de distribuicao (QR + atalhos).
- Dependencias:
  - MVP operacional validado ate Etapa 5;
  - conteudo institucional e identidade visual aprovados;
  - estrutura de deploy e dominios definida.

### Etapa 7 - Canais web para clientes (web app/PWA)
- Escopo: experiencia web para consulta, pedido e acompanhamento.
- Dependencias:
  - API de pedidos/pagamentos estabilizada;
  - observabilidade e deploy com baseline estavel;
  - decisoes de UX para navegacao entre portal, app e web clientes.

### Etapa 8 - Governanca, seguranca e escala
- Escopo: consolidacao de arquitetura, compliance e capacidade operacional.
- Dependencias:
  - validacao em producao das etapas 6 e 7;
  - politica de dados pessoais e LGPD definida;
  - estrategia de crescimento e custos de infra formalizada.

## Regras do cronograma
- Cada entrega precisa ser testavel e usavel.
- Nao avancar para escopo pos-MVP antes do fechamento financeiro da Etapa 5.
- Etapas 6-8 nao alteram o criterio de fechamento do MVP operacional.
