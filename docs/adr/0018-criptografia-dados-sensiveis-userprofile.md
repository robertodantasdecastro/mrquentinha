# ADR-0018: Criptografia de dados sensiveis no UserProfile

## Status
Aceito

## Contexto
O ecossistema Mr Quentinha armazena dados pessoais sensiveis (documentos e endereco)
no `UserProfile`. A LGPD exige medidas tecnicas para protecao desses dados,
incluindo criptografia e controle de acesso. Era necessario garantir protecao
em repouso sem quebrar a capacidade de busca administrativa.

## Decisão
- Introduzir um `EncryptedTextField` para campos sensiveis do `UserProfile`.
- Persistir hashes de documentos e telefone para suportar busca sem expor o valor.
- Usar `FIELD_ENCRYPTION_KEY` e `FIELD_HASH_SALT` por ambiente.
- Manter fallback com `django.core.signing` quando `cryptography` nao estiver
  instalada, com opcao de bloqueio via `FIELD_ENCRYPTION_STRICT=true`.

## Consequências
- Dados sensiveis ficam criptografados no banco.
- Buscas administrativas por CPF/CNPJ/telefone passam a usar hashes.
- Ambientes precisam definir chaves de criptografia/ hash para operacao correta.
- Requer atencao adicional na rotacao de chaves e backup.

## Alternativas consideradas
- Criptografia no nivel do banco (pgcrypto) sem mudanca no ORM.
- Vault/KMS externo para envelope encryption com rotacao automatica.
