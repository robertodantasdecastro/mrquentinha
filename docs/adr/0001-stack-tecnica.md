# ADR-0001: Stack técnica do MVP

## Status
Aceito

## Contexto
Precisamos construir rapidamente um MVP com backend único, web de gestão e mobile,
priorizando escalabilidade, segurança e produtividade.

## Decisão
- Backend: Django + DRF
- Banco: PostgreSQL
- Mobile: React Native
- Web gestão: React/Next
- Sem Docker no MVP (VM Linux local + EC2 no deploy)

## Consequências
- Alta produtividade no backend e boa maturidade do ecossistema.
- Sem Docker aumenta esforço de replicabilidade, mas atende a restrição do projeto.
