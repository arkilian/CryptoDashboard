# 🚀 Setup e Deployment

## Requisitos do Sistema

### Software Necessário

**Essenciais**:
- Python 3.10 ou superior
- PostgreSQL 12 ou superior
- pip (gestor de pacotes Python)

**Opcionais mas Recomendados**:
- Git (para clonar o repositório)
- virtualenv ou venv (ambientes virtuais Python)
- pgAdmin ou DBeaver (gestão de BD visual)

### Requisitos de Hardware

**Mínimos**:
- CPU: 1 core
- RAM: 512 MB
- Disco: 1 GB livre
- Internet: Conexão estável (para CoinGecko API)

**Recomendados** (para fundos com >20 utilizadores):
- CPU: 2+ cores
- RAM: 2 GB
- Disco: 5 GB livre (para logs e backups)
- SSD (melhor performance de BD)

---

## Instalação Local (Desenvolvimento)

### 1. Clonar o Repositório

```bash
git clone https://github.com/your-repo/CryptoDashboard.git
cd CryptoDashboard
```

### 2. Configurar Ambiente Virtual

**Windows**:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais**:
```
streamlit>=1.30.0
pandas>=2.1.0
plotly>=5.18.0
psycopg2-binary>=2.9.9
SQLAlchemy>=2.0.0
bcrypt>=4.1.2
python-dateutil>=2.8.2
requests>=2.31.0
```

### 4. Configurar PostgreSQL

#### Opção A: PostgreSQL Local

**Instalar PostgreSQL**:
- Windows: [PostgreSQL Installer](https://www.postgresql.org/download/windows/)
- Mac: `brew install postgresql`
- Linux: `sudo apt install postgresql postgresql-contrib`

**Criar Base de Dados**:
```bash
# Aceder ao PostgreSQL
psql -U postgres

# Criar base de dados
CREATE DATABASE crypto_dashboard;

# Criar utilizador
CREATE USER crypto_user WITH PASSWORD 'secure_password';

# Dar permissões
GRANT ALL PRIVILEGES ON DATABASE crypto_dashboard TO crypto_user;

# Sair
\q
```

#### Opção B: PostgreSQL Cloud

**Recomendações**:
- [Supabase](https://supabase.com) (grátis até 500 MB)
- [ElephantSQL](https://www.elephantsql.com) (grátis até 20 MB)
- [Neon](https://neon.tech) (grátis com scaling automático)

**Obter Connection String**:
```
postgresql://username:password@host:5432/database_name
```

### 5. Configurar Variáveis de Ambiente

Criar ficheiro `.env` na raiz do projeto:

```bash
# .env
DATABASE_URL=postgresql://crypto_user:secure_password@localhost:5432/crypto_dashboard
SECRET_KEY=your-random-secret-key-here
ENVIRONMENT=development

# Opcional: CoinGecko API key (para tier pago)
COINGECKO_API_KEY=your-api-key
```

**Gerar SECRET_KEY**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 6. Atualizar config.py

Editar `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/crypto_dashboard')

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')

# CoinGecko
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', None)
COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3'
```

### 7. Inicializar Base de Dados

**Executar Script de Setup**:
```bash
psql -U crypto_user -d crypto_dashboard -f database/tablesv2.sql
```

**Ou via Python**:
```python
from database.connection import get_connection
with open('database/tablesv2.sql', 'r') as f:
    sql = f.read()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
```

### 8. Esquema da Base de Dados

Nesta versão, não há migrações em runtime. Para iniciar ou atualizar o ambiente de desenvolvimento/teste, aplique o ficheiro `database/tablesv2.sql`, que contém o schema completo e seeds essenciais (EUR e a exchange especial Banco).

### 9. Criar Utilizador Admin Inicial

**Via Python**:
```python
from database.connection import get_connection
import bcrypt

conn = get_connection()
cur = conn.cursor()

# Hash password
password = "admin123"  # MUDAR EM PRODUÇÃO!
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Inserir admin
cur.execute("""
    INSERT INTO t_users (username, email, password_hash, is_admin)
    VALUES (%s, %s, %s, %s)
    RETURNING user_id;
""", ('admin', 'admin@example.com', password_hash, True))

user_id = cur.fetchone()[0]
conn.commit()

print(f"Admin criado! user_id={user_id}")
print(f"Username: admin")
print(f"Password: admin123")
print("⚠️  ALTERE A PASSWORD NO PRIMEIRO LOGIN!")
```

**Via SQL direto**:
```sql
-- Gerar hash no Python primeiro:
-- import bcrypt
-- print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())

INSERT INTO t_users (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@example.com', '$2b$12$XYZ...', TRUE);
```

### 10. Popular Ativos Iniciais

```sql
-- Inserir criptomoedas principais
INSERT INTO t_assets (symbol, name, coingecko_id, is_active) VALUES
('BTC', 'Bitcoin', 'bitcoin', TRUE),
('ETH', 'Ethereum', 'ethereum', TRUE),
('ADA', 'Cardano', 'cardano', TRUE),
('SOL', 'Solana', 'solana', TRUE),
('XRP', 'Ripple', 'ripple', TRUE),
('DOT', 'Polkadot', 'polkadot', TRUE),
('USDT', 'Tether', 'tether', TRUE),
('USDC', 'USD Coin', 'usd-coin', TRUE);
```

### 11. Lançar Aplicação

```bash
streamlit run app.py
```

**Ou com configurações personalizadas**:
```bash
streamlit run app.py --server.port 8501 --server.address localhost
```

**Acessar**:
```
http://localhost:8501
```

**Login inicial**:
- Username: `admin`
- Password: `admin123`
- ⚠️ **Alterar password imediatamente!**

---

## Deployment em Produção

### Opção 1: Streamlit Cloud (Mais Fácil)

**Pré-requisitos**:
- Repositório GitHub público ou privado
- Conta [Streamlit Cloud](https://streamlit.io/cloud)

**Passos**:

1. **Push código para GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/username/repo.git
   git push -u origin main
   ```

2. **Deploy no Streamlit Cloud**:
   - Aceder a [share.streamlit.io](https://share.streamlit.io)
   - Conectar GitHub
   - Selecionar repositório
   - Main file: `app.py`
   - Python version: 3.10

3. **Configurar Secrets**:
   - No dashboard Streamlit Cloud → Settings → Secrets
   - Adicionar:
     ```toml
     DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
     SECRET_KEY = "your-secret-key"
     ```

4. **Deploy**:
   - Clicar "Deploy"
   - Aguardar ~2-5 minutos
   - App disponível em: `https://your-app.streamlit.app`

**Limitações**:
- Máximo 1 GB RAM
- CPU compartilhada
- Sleep após 7 dias sem acesso
- Adequado para <50 utilizadores

### Opção 2: Heroku

**Pré-requisitos**:
- Conta [Heroku](https://heroku.com)
- Heroku CLI instalado

**Passos**:

1. **Criar Procfile**:
   ```
   web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

2. **Criar runtime.txt**:
   ```
   python-3.10.13
   ```

3. **Login e criar app**:
   ```bash
   heroku login
   heroku create crypto-dashboard-prod
   ```

4. **Adicionar PostgreSQL**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

5. **Configurar variáveis**:
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set ENVIRONMENT="production"
   ```

6. **Deploy**:
   ```bash
   git push heroku main
   ```

7. **Inicializar BD**:
   ```bash
   heroku run python -c "from setup_db import init_db; init_db()"
   ```

**Custo**: ~$7/mês (Hobby Dynos)

### Opção 3: VPS (DigitalOcean, Linode, AWS EC2)

**Recomendado para controlo total e performance**

#### Setup no Ubuntu 22.04

**1. Conectar ao servidor**:
```bash
ssh root@your-server-ip
```

**2. Atualizar sistema**:
```bash
apt update && apt upgrade -y
```

**3. Instalar dependências**:
```bash
# Python 3.10
apt install python3.10 python3.10-venv python3-pip -y

# PostgreSQL
apt install postgresql postgresql-contrib -y

# Nginx (reverse proxy)
apt install nginx -y

# Certificados SSL
apt install certbot python3-certbot-nginx -y
```

**4. Configurar PostgreSQL**:
```bash
sudo -u postgres psql

CREATE DATABASE crypto_dashboard;
CREATE USER crypto_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE crypto_dashboard TO crypto_user;
\q
```

**5. Clonar e configurar aplicação**:
```bash
cd /opt
git clone https://github.com/your-repo/CryptoDashboard.git
cd CryptoDashboard

python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**6. Criar .env**:
```bash
nano .env
```
```
DATABASE_URL=postgresql://crypto_user:password@localhost:5432/crypto_dashboard
SECRET_KEY=your-generated-secret
ENVIRONMENT=production
```

**7. Inicializar BD**:
```bash
source .venv/bin/activate
psql -U crypto_user -d crypto_dashboard -f database/tablesv2.sql
```

**8. Criar serviço systemd**:
```bash
nano /etc/systemd/system/crypto-dashboard.service
```

```ini
[Unit]
Description=Crypto Dashboard Streamlit App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/CryptoDashboard
Environment="PATH=/opt/CryptoDashboard/.venv/bin"
ExecStart=/opt/CryptoDashboard/.venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**9. Ativar serviço**:
```bash
systemctl daemon-reload
systemctl enable crypto-dashboard
systemctl start crypto-dashboard
systemctl status crypto-dashboard
```

**10. Configurar Nginx**:
```bash
nano /etc/nginx/sites-available/crypto-dashboard
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**11. Ativar site**:
```bash
ln -s /etc/nginx/sites-available/crypto-dashboard /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**12. SSL com Let's Encrypt**:
```bash
certbot --nginx -d your-domain.com
```

**Aceder**: `https://your-domain.com`

---

## Backup e Recuperação

### Backup Automatizado

**Script de Backup**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/crypto-dashboard"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="crypto_dashboard"
DB_USER="crypto_user"

# Criar diretório
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# Backup arquivos críticos
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" \
    /opt/CryptoDashboard/database/ \
    /opt/CryptoDashboard/services/ \
    /opt/CryptoDashboard/.env

# Manter apenas últimos 30 dias
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup concluído: $DATE"
```

**Agendar com Cron**:
```bash
crontab -e
```
```
# Backup diário às 2h da manhã
0 2 * * * /opt/scripts/backup.sh >> /var/log/crypto-dashboard-backup.log 2>&1
```

### Restaurar Backup

**Restaurar BD**:
```bash
# Parar aplicação
systemctl stop crypto-dashboard

# Restaurar
psql -U crypto_user -d crypto_dashboard < /backups/crypto-dashboard/db_20251031_020000.sql

# Reiniciar aplicação
systemctl start crypto-dashboard
```

**Restaurar Ficheiros**:
```bash
tar -xzf /backups/crypto-dashboard/files_20251031_020000.tar.gz -C /
```

---

## Monitorização e Logs

### Logs da Aplicação

**Ver logs em tempo real**:
```bash
# Streamlit logs
journalctl -u crypto-dashboard -f

# Últimos 100 linhas
journalctl -u crypto-dashboard -n 100

# Logs de erro apenas
journalctl -u crypto-dashboard -p err
```

### Logs PostgreSQL

**Localização**: `/var/log/postgresql/postgresql-14-main.log`

**Ver queries lentas**:
```sql
-- Ativar log de queries lentas (>100ms)
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();
```

### Métricas de Sistema

**CPU e Memória**:
```bash
# Top em tempo real
htop

# Uso de memória da app
ps aux | grep streamlit

# Uso do PostgreSQL
ps aux | grep postgres
```

**Disco**:
```bash
# Espaço livre
df -h

# Tamanho da BD
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('crypto_dashboard'));"

# Tamanho das tabelas
sudo -u postgres psql crypto_dashboard -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Alertas (Opcional)

**Setup com Uptimerobot**:
1. Criar conta em [uptimerobot.com](https://uptimerobot.com)
2. Adicionar monitor HTTP: `https://your-domain.com`
3. Configurar alertas por email/SMS

**Setup com Prometheus + Grafana** (avançado):
- Exportar métricas do PostgreSQL
- Exportar métricas do sistema (node_exporter)
- Dashboard Grafana personalizado

---

## Segurança

### SSL/TLS

**Let's Encrypt (Grátis)**:
```bash
certbot --nginx -d your-domain.com
certbot renew --dry-run  # Testar renovação automática
```

**Renovação automática**:
```bash
crontab -e
```
```
0 3 * * * certbot renew --quiet && systemctl reload nginx
```

### Firewall

```bash
# Instalar UFW
apt install ufw

# Permitir apenas necessário
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# Ativar
ufw enable
ufw status
```

### PostgreSQL Security

**1. Autenticação**:
```bash
nano /etc/postgresql/14/main/pg_hba.conf
```
```
# Permitir apenas local e conexões com password
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

**2. Configurações**:
```bash
nano /etc/postgresql/14/main/postgresql.conf
```
```
# Escutar apenas localhost
listen_addresses = 'localhost'

# Max conexões
max_connections = 20

# Log de conexões
log_connections = on
log_disconnections = on
```

**3. Restart**:
```bash
systemctl restart postgresql
```

### Aplicação Security

**1. Alterar SECRET_KEY**:
```python
import secrets
print(secrets.token_urlsafe(32))
# Copiar output para .env
```

**2. Rate Limiting** (futuro):
```python
# Em app.py
from streamlit_rate_limiter import rate_limiter

@rate_limiter(max_calls=100, period=60)
def login_attempt():
    # ...
```

**3. HTTPS Only**:
```nginx
# Em /etc/nginx/sites-available/crypto-dashboard
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Troubleshooting

### Problema: App não inicia

**Sintomas**: `systemctl status crypto-dashboard` mostra "failed"

**Diagnóstico**:
```bash
journalctl -u crypto-dashboard -n 50
```

**Causas comuns**:
- ❌ .env não existe ou mal configurado
- ❌ PostgreSQL não está a correr
- ❌ Dependências não instaladas
- ❌ Porta 8501 já em uso

**Soluções**:
```bash
# Verificar .env
cat /opt/CryptoDashboard/.env

# PostgreSQL
systemctl status postgresql
psql -U crypto_user -d crypto_dashboard -c "SELECT 1;"

# Reinstalar dependências
cd /opt/CryptoDashboard
source .venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Porta em uso
lsof -i :8501
kill -9 <PID>
```

### Problema: Erro 429 (Too Many Requests)

**Sintomas**: Análise de portfólio demora muito ou falha

**Causa**: Rate limit do CoinGecko

**Soluções**:
1. Usar snapshots (já implementado)
2. Aumentar delay em `services/snapshots.py`:
   ```python
   time.sleep(3)  # Era 2, aumentar para 3
   ```
3. Upgrade para CoinGecko API paga

### Problema: NAV Inconsistente

**Sintomas**: NAV Total ≠ Caixa + Cripto

**Diagnóstico**:
```sql
-- Calcular manualmente
WITH capital AS (
    SELECT SUM(credit) - SUM(debit) AS cash_movements
    FROM t_user_capital_movements
),
trades AS (
    SELECT 
        SUM(CASE WHEN transaction_type='buy' THEN total_eur+fee_eur ELSE 0 END) AS spent,
        SUM(CASE WHEN transaction_type='sell' THEN total_eur-fee_eur ELSE 0 END) AS received
    FROM t_transactions
)
SELECT cash_movements - spent + received AS calculated_cash
FROM capital, trades;

-- Comparar com holdings
SELECT symbol, SUM(CASE WHEN transaction_type='buy' THEN quantity ELSE -quantity END)
FROM t_transactions t
JOIN t_assets a ON a.asset_id = t.asset_id
GROUP BY symbol;
```

**Causa comum**: Transação com fee_eur NULL (assume 0)

**Solução**:
```sql
UPDATE t_transactions SET fee_eur = 0 WHERE fee_eur IS NULL;
```

### Problema: Shares Inconsistentes

**Sintomas**: Ownership não soma 100%

**Diagnóstico**:
```sql
SELECT 
    user_id,
    SUM(shares_amount) AS total_shares,
    (SELECT SUM(shares_amount) FROM t_user_shares) AS grand_total,
    SUM(shares_amount) / (SELECT SUM(shares_amount) FROM t_user_shares) * 100 AS pct
FROM t_user_shares
GROUP BY user_id;
```

**Causa**: Pode ter arredondamentos (normal se diferença < 0.01%)

**Se erro real**:
```bash
# Backup primeiro!
pg_dump -U crypto_user crypto_dashboard > /tmp/backup_before_fix.sql

# Contactar suporte ou verificar código de allocate_shares
```

---

## Performance Tuning

### PostgreSQL

**Configurações para otimizar**:
```sql
-- Em /etc/postgresql/14/main/postgresql.conf

# Memória
shared_buffers = 256MB          # 25% da RAM
effective_cache_size = 1GB      # 50-75% da RAM
work_mem = 16MB                 # Para queries complexas

# Checkpoint
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Planner
random_page_cost = 1.1          # Para SSD
effective_io_concurrency = 200   # Para SSD

# Conexões
max_connections = 50
```

**Aplicar**:
```bash
systemctl restart postgresql
```

### Índices Adicionais

**Se queries ficarem lentas**:
```sql
-- Índice para análise de portfólio por utilizador
CREATE INDEX idx_capital_movements_user_date 
ON t_user_capital_movements(user_id, movement_date);

CREATE INDEX idx_transactions_date 
ON t_transactions(transaction_date);

-- Índice para ownership
CREATE INDEX idx_user_shares_user_date 
ON t_user_shares(user_id, movement_date DESC);

-- Analisar tabelas
ANALYZE t_user_capital_movements;
ANALYZE t_user_shares;
ANALYZE t_transactions;
ANALYZE t_price_snapshots;
```

### Streamlit Caching

**Em app.py**:
```python
@st.cache_data(ttl=300)  # Cache 5 minutos
def load_portfolio_data(user_id):
    # ...
    return data

@st.cache_resource
def init_db_connection():
    # ...
    return connection
```

---

## Atualizações

### Atualizar Código

```bash
cd /opt/CryptoDashboard
git pull origin main

# Reinstalar dependências se requirements.txt mudou
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Reiniciar app
systemctl restart crypto-dashboard
```

### Atualizar o Esquema

Para desenvolvimento, a forma mais simples é recriar a base de dados aplicando novamente `database/tablesv2.sql`. Em produção, avalie cuidadosamente e crie scripts SQL de alteração explícitos conforme necessário.

---

## FAQ Deployment

**Q: Posso usar SQLite em vez de PostgreSQL?**  
A: Não recomendado. Sistema foi desenvolvido para PostgreSQL. SQLite não suporta algumas features (ex: `NUMERIC` com precisão).

**Q: Preciso de domínio próprio?**  
A: Não essencial, mas recomendado para produção (SSL, profissionalismo). Pode usar IP direto para desenvolvimento.

**Q: Quantos utilizadores o sistema aguenta?**  
A: Depende do servidor. Com VPS de $10/mês: ~100 utilizadores confortavelmente.

**Q: Como fazer upgrade de Streamlit Cloud para VPS?**  
A: 1) Backup BD; 2) Setup VPS como descrito; 3) Restaurar BD; 4) Testar; 5) Mudar DNS.

**Q: Sistema funciona offline?**  
A: Não. Precisa internet para CoinGecko API. Pode implementar modo offline com preços em cache apenas.

---

**Anterior**: [← Guias de Utilizador](05-guias-utilizador.md)  
**Voltar ao Início**: [📚 Wiki Home](README.md)
