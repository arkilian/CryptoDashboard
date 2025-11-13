# 📦 Sistema de Backup e Criação de Base de Dados

## ✅ Ficheiros Criados

Foram criados **5 ficheiros** para facilitar a criação de uma base de dados nova:

### 1. 📋 `schema.sql` (10 KB)
**Estrutura completa da base de dados**
- 30+ tabelas
- Índices otimizados
- Views
- Constraints e chaves estrangeiras
- **SEM dados** - apenas estrutura

### 2. 📊 `data_export.sql` (2.5 MB / ~24,000 linhas)
**Todos os dados atuais da base de dados**
- ~8,000 registos exportados
- 6,912 preços históricos
- 158 transações Cardano
- 742 I/O de transações
- 33 ativos
- 3 utilizadores
- Respeitando ordem de dependências

### 3. 🔧 `export_data.py`
**Script Python para re-exportar dados**
- Extrai dados da base atual
- Gera `data_export.sql` atualizado
- Respeita dependências automaticamente

### 4. 🖥️ `setup_database.bat` (Windows)
**Script automático para Windows**
- Cria base de dados
- Aplica schema
- Importa dados
- Verifica instalação

### 5. 🐧 `setup_database.sh` (Linux/Mac)
**Script automático para Linux/Mac**
- Mesmas funcionalidades que o .bat
- Requer permissão de execução

### 6. 📖 `README_DATABASE_SETUP.md`
**Documentação completa**
- Instruções passo-a-passo
- Troubleshooting
- Estatísticas da exportação

---

## 🚀 Como Usar

### Opção 1: Script Automático (Recomendado)

#### Windows:
```bash
cd c:\CryptoDashboard\database
setup_database.bat
```

#### Linux/Mac:
```bash
cd /path/to/CryptoDashboard/database
chmod +x setup_database.sh
./setup_database.sh
```

### Opção 2: Manual (Controlo Total)

```bash
# 1. Criar base de dados
psql -U postgres -c "CREATE DATABASE crypto_dashboard_novo;"

# 2. Aplicar schema
psql -U postgres -d crypto_dashboard_novo -f database/schema.sql

# 3. Importar dados
psql -U postgres -d crypto_dashboard_novo -f database/data_export.sql

# 4. Atualizar .env
# DB_NAME=crypto_dashboard_novo

# 5. Testar
python database/test_connection.py
streamlit run app.py
```

---

## 🔄 Atualizar Dados Exportados

Quando a base de dados atual tiver dados novos e quiser re-exportar:

```bash
cd c:\CryptoDashboard
python database/export_data.py
```

Isto irá:
- ✅ Conectar à base configurada no `.env`
- ✅ Exportar todos os dados atualizados
- ✅ Sobrescrever `data_export.sql`

---

## 📊 Estatísticas Atuais

**Base de dados:** `patch`  
**Exportado em:** 2025-11-13 12:58:54

| Categoria | Tabela | Registos |
|-----------|--------|----------|
| **Utilizadores** | t_users | 3 |
| | t_user_profile | 2 |
| | t_address | 3 |
| | t_gender | 4 |
| **Exchanges** | t_exchanges | 7 |
| | t_exchange_accounts | 2 |
| **Ativos** | t_assets | 33 |
| | t_cardano_assets | 21 |
| **Transações** | t_transactions | 1 |
| | t_cardano_transactions | 158 |
| | t_cardano_tx_io | 742 |
| **Preços** | t_price_snapshots | 6,912 |
| **Capital** | t_user_capital_movements | 2 |
| | t_user_shares | 2 |
| **Configuração** | t_fee_settings | 1 |
| | t_tags | 2 |
| | t_api_coingecko | 1 |
| | t_api_cardano | 1 |
| **Banco/Wallet** | t_wallet | 2 |
| | t_banco | 1 |
| **TOTAL** | | **~8,000** |

---

## ⚠️ Notas Importantes

### ✅ Vantagens deste Sistema

1. **Separação Clara:** Schema e dados em ficheiros separados
2. **Reutilizável:** Facilmente aplicável a novas instalações
3. **Versionável:** Pode commit no git (exceto dados sensíveis)
4. **Automatizado:** Scripts prontos para Windows e Linux
5. **Seguro:** Usa `ON CONFLICT DO NOTHING` para evitar duplicações

### ⚠️ Segurança

**ATENÇÃO:** O ficheiro `data_export.sql` contém:
- Passwords (hashed com bcrypt) ✅
- Chaves de API 🔒
- Dados pessoais dos utilizadores 🔒

**Recomendações:**
- ✅ Adicionar `data_export.sql` ao `.gitignore`
- ✅ Guardar em local seguro (não partilhar publicamente)
- ✅ Encriptar backups antes de enviar

### 🔄 Compatibilidade

- PostgreSQL 12+
- Python 3.10+
- Testado em Windows 11

---

## 📁 Estrutura de Ficheiros

```
database/
├── schema.sql                    # ✅ Estrutura (commit no git)
├── data_export.sql               # 🔒 Dados (NÃO commit!)
├── export_data.py                # ✅ Script de exportação
├── setup_database.bat            # ✅ Setup Windows
├── setup_database.sh             # ✅ Setup Linux/Mac
├── README_DATABASE_SETUP.md      # ✅ Documentação
│
├── tablesv2.sql                  # ⚠️ Obsoleto (schema antigo com dados)
├── tables.sql                    # ⚠️ Obsoleto (V1)
└── new_tables.sql                # ⚠️ Obsoleto (migrações)
```

---

## 🎯 Próximos Passos Sugeridos

1. **Testar o sistema:**
   ```bash
   setup_database.bat  # Criar base de dados de teste
   ```

2. **Adicionar ao .gitignore:**
   ```
   database/data_export.sql
   ```

3. **Criar backups regulares:**
   ```bash
   # Adicionar ao cron/task scheduler
   python database/export_data.py
   ```

4. **Documentar no README principal:**
   - Como criar base de dados nova
   - Como fazer backup/restore

---

## 🆘 Suporte

- 📖 Documentação completa: `README_DATABASE_SETUP.md`
- 🐛 Troubleshooting: Ver secção no README
- 📧 Issues: Verificar logs de erro do PostgreSQL

---

**Criado em:** 2025-11-13  
**Versão:** 1.0  
**Status:** ✅ Pronto para Produção
