# Database

Este documento descreve o esquema da base de dados e como criá-lo.

Esquema base (`database/tables.sql`)

Tabelas definidas no ficheiro `database/tables.sql`:

- `t_users` — utilizadores (user_id, username, password_hash, salt, is_admin)
- `t_fee_settings` — configuração de taxas com histórico
- `t_portfolio_snapshots` — snapshots do fundo (snapshot_id, snapshot_date, total_value)
- `t_portfolio_holdings` — holdings por snapshot (holding_id, snapshot_id, asset_symbol, quantity, price, valor_total)
- `t_user_snapshots` — snapshots por utilizador (user_snapshot_id, user_id, snapshot_date, valor_antes, valor_depois)
- `t_user_high_water` — high water mark por utilizador
- `t_user_fees` — histórico de taxas aplicadas

Migrações adicionais

Há migrações em `database/migrations/` que criam tabelas adicionais:

- `003_add_manual_snapshots.sql` — cria `t_user_manual_snapshots` (snapshots manuais com colunas binance_value, ledger_value, defi_value, other_value, total_value)
- `004_add_user_profile_and_movements.sql` — cria:
  - `t_gender` — lookup de géneros
  - `t_address` — endereços
  - `t_user_profile` — perfis de utilizador (first_name, last_name, birth_date, gender_id, address_id)
  - `t_user_capital_movements` — movimentos de capital (depósitos, levantamentos). Os admins não têm movimentos próprios; a visualização agregada mostra a soma de todos os utilizadores não-admin.

O runner de migrações (`database/run_migrations.py`) cria uma tabela de controlo `t_migrations` e aplica os scripts SQL encontrados em `database/migrations/`.

Como criar as tabelas

1. Usando o schema base:

```powershell
psql -U <user> -d <database> -f database/tables.sql
```

2. Usando o runner de migrações (recomendado para aplicar migrações adicionais):

```powershell
python .\database\run_migrations.py
```

Notas sobre compatibilidade

- Alguns módulos do código referenciam `t_user_manual_snapshots`. Esse ficheiro NÃO está em `tables.sql` mas existe como migração; certifique-se de executar as migrações para evitar `relation does not exist`.
- `run_migrations.py` cria `t_migrations` automaticamente; não é necessário criar essa tabela manualmente.

Backup e restauração

- Use `pg_dump`/`pg_restore` para operações de backup/restore.

```powershell
pg_dump -U <user> -Fc -d <database> -f backup.dump
pg_restore -U <user> -d <database> backup.dump
```
