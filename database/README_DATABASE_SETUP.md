# Criação de Base de Dados Nova

Este diretório contém os ficheiros necessários para criar uma base de dados PostgreSQL nova com todos os dados do Crypto Dashboard.

## Ficheiros

### 📋 `schema.sql`
**Estrutura completa da base de dados** (tabelas, índices, views)
- Define todas as tabelas e relações
- Cria índices para otimização de queries
- Define constraints e chaves estrangeiras
- **NÃO contém dados** - apenas estrutura

### 📊 `data_export.sql`
**Dados existentes da base de dados atual**
- Contém todos os INSERT statements
- Exportado automaticamente com `export_data.py`
- Respeita ordem de dependências (chaves estrangeiras)
- Usa `ON CONFLICT DO NOTHING` para evitar erros

### 🔧 `export_data.py`
**Script Python para exportar dados**
- Conecta à base de dados configurada no `.env`
- Exporta dados de todas as tabelas
- Gera o ficheiro `data_export.sql`

## 🚀 Como Criar uma Base de Dados Nova

### Passo 1: Criar a Base de Dados
```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar a base de dados
CREATE DATABASE crypto_dashboard_novo;

# Criar utilizador (opcional)
CREATE USER crypto_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE crypto_dashboard_novo TO crypto_user;

# Sair
\q
```

### Passo 2: Aplicar o Schema (Estrutura)
```bash
psql -U postgres -d crypto_dashboard_novo -f database/schema.sql
```

Ou com utilizador específico:
```bash
psql -U crypto_user -d crypto_dashboard_novo -f database/schema.sql
```

### Passo 3: Importar os Dados
```bash
psql -U postgres -d crypto_dashboard_novo -f database/data_export.sql
```

### Passo 4: Atualizar Configuração
Editar o ficheiro `.env` na raiz do projeto:
```env
DB_NAME=crypto_dashboard_novo
DB_USER=crypto_user
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

### Passo 5: Verificar
```bash
# Conectar à nova base de dados
psql -U postgres -d crypto_dashboard_novo

# Verificar tabelas
\dt

# Verificar dados (exemplo)
SELECT COUNT(*) FROM t_users;
SELECT COUNT(*) FROM t_transactions;
SELECT COUNT(*) FROM t_price_snapshots;

# Sair
\q
```

## 🔄 Atualizar o Ficheiro de Dados

Se precisar de exportar novamente os dados mais recentes:

```bash
cd c:\CryptoDashboard
python database/export_data.py
```

Isto irá:
1. Ler a base de dados configurada no `.env`
2. Exportar todos os dados
3. Criar/sobrescrever o ficheiro `data_export.sql`

## 📊 Estatísticas da Exportação Atual

Dados exportados da base de dados `patch`:

| Tabela | Registos |
|--------|----------|
| `t_gender` | 4 |
| `t_users` | 3 |
| `t_exchanges` | 7 |
| `t_assets` | 33 |
| `t_fee_settings` | 1 |
| `t_tags` | 2 |
| `t_address` | 3 |
| `t_user_profile` | 2 |
| `t_exchange_accounts` | 2 |
| `t_wallet` | 2 |
| `t_banco` | 1 |
| `t_api_coingecko` | 1 |
| `t_api_cardano` | 1 |
| `t_cardano_assets` | 21 |
| `t_user_capital_movements` | 2 |
| `t_transactions` | 1 |
| `t_price_snapshots` | 6912 |
| `t_user_shares` | 2 |
| `t_cardano_transactions` | 158 |
| `t_cardano_tx_io` | 742 |

**Total: ~8,000 registos**

## ⚠️ Notas Importantes

### Ordem de Importação
O script `export_data.py` respeita automaticamente a ordem de dependências das tabelas. Sempre use os ficheiros gerados na ordem:
1. `schema.sql` primeiro
2. `data_export.sql` depois

### Conflitos
O ficheiro de dados usa `ON CONFLICT DO NOTHING`, o que significa:
- Se executar múltiplas vezes, não haverá erros
- Dados duplicados serão ignorados (não sobrescritos)

### Triggers
Durante a importação, os triggers são temporariamente desabilitados para melhor performance:
```sql
SET session_replication_role = replica;
-- ... inserts ...
SET session_replication_role = DEFAULT;
```

### Backup
**Sempre faça backup antes de importar dados!**

```bash
# Backup da base de dados atual
pg_dump -U postgres -d crypto_dashboard > backup_$(date +%Y%m%d_%H%M%S).sql

# Ou backup completo
pg_dump -U postgres -d crypto_dashboard -F c -f backup_$(date +%Y%m%d_%H%M%S).dump
```

## 🔧 Troubleshooting

### Erro: "role does not exist"
```bash
# Criar o utilizador primeiro
psql -U postgres
CREATE USER crypto_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE crypto_dashboard_novo TO crypto_user;
```

### Erro: "permission denied"
```bash
# Dar permissões no schema public
psql -U postgres -d crypto_dashboard_novo
GRANT ALL ON SCHEMA public TO crypto_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO crypto_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO crypto_user;
```

### Erro ao executar export_data.py
```bash
# Instalar dependências
pip install psycopg2-binary python-dotenv

# Verificar ficheiro .env
cat .env
```

## 📝 Ficheiros Relacionados

- `tablesv2.sql` - Schema antigo (com dados iniciais incluídos)
- `tables.sql` - Schema V1 (obsoleto)
- `new_tables.sql` - Migrações anteriores (obsoleto)

**Use sempre `schema.sql` + `data_export.sql` para criar bases de dados novas!**
