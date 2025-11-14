# Implementação no Azure App Service (Streamlit + PostgreSQL)

Este guia prepara o projeto para correr no Azure App Service com base de dados Azure Database for PostgreSQL Flexible Server. Inclui pré‑requisitos, configs de aplicação, schema da BD, CI/CD e troubleshooting.

## 1) Pré‑requisitos
- App Service Plan + Web App (Linux, stack Python >= 3.12)
- Azure Database for PostgreSQL Flexible Server (servidor e base criados)
- Integração GitHub já configurada (workflows em `.github/workflows/`)

## 2) Arranque da aplicação (Streamlit)
O App Service não deteta Streamlit automaticamente. Para isso, adicionámos:
- `startup.sh` (na raiz) – arranca o Streamlit na porta correta
- `Procfile` – instrui o Oryx/App Service a usar o script acima

Se necessário, no Web App > Configuration > General Settings:
- Python version: 3.12 (ou a versão LTS disponível mais recente)
- Startup Command (opcional, apenas se quiser forçar): `sh startup.sh`

O Oryx usa automaticamente o `Procfile` se existir, pelo que o Startup Command não é obrigatório.

## 3) Variáveis de ambiente (App Settings)
No Web App > Configuration > Application settings, adicione as seguintes chaves (não commit ao `.env` em produção):
- `DB_HOST` = host do PostgreSQL (ex: `myserver.postgres.database.azure.com`)
- `DB_PORT` = `5432`
- `DB_NAME` = nome da base de dados (ex: `crypto_dashboard`)
- `DB_USER` = utilizador (ex: `app_user@myserver`)
- `DB_PASSWORD` = palavra‑passe

Opcional (usados por alguns stacks):
- `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true` (normalmente já vem configurado via Portal)

O código lê estas variáveis via `os.getenv()` em `database/connection.py` (o `load_dotenv()` não impacta produção se não houver `.env`).

## 4) Esquema da Base de Dados
Não existem migrações em runtime. Aplique o schema manualmente antes do primeiro deploy:

Utilize `psql` a partir da sua máquina:
```powershell
$env:PGPASSWORD = "<DB_PASSWORD>"
psql -h <DB_HOST> -p 5432 -U <DB_USER> -d <DB_NAME> -f database/tablesv2.sql
```

Validação rápida da ligação (opcional):
```powershell
python database/test_connection.py
```

## 5) CI/CD com GitHub Actions
O repositório já contém workflows:
- `.github/workflows/main_cryptodashboard.yml` (federated credentials)
- `.github/workflows/main_arkilian-webapp.yml` (publish profile)

Cada push na branch `main` faz o build e deploy através da ação `azure/webapps-deploy`. Não é necessário alterar os workflows.

## 6) Comportamento em execução
O script `startup.sh` arranca o Streamlit com:
- `--server.address 0.0.0.0`
- `--server.port` igual a `PORT`/`WEBSITES_PORT` (definido pelo App Service)
- CORS e XSRF desligados (necessário para reverse proxies do Azure)

## 7) Troubleshooting
- Página não abre / porta errada:
  - Verifique o Log Stream do Web App
  - Confirme que o `Procfile` está na raiz e contém `web: sh startup.sh`
  - Se necessário, defina `Startup Command = sh startup.sh`
- Erros de ligação ao PostgreSQL:
  - Confirme `DB_*` nas App Settings e permissões do utilizador
  - Reaplique `database/tablesv2.sql` se necessário
- Dependências Python:
  - O Oryx instala a partir de `requirements.txt`
  - Confirme versão Python do Web App compatível com as versões dos pacotes

## 8) Execução local (referência)
```powershell
# Ativar venv e executar localmente
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## 9) Notas finais
- Manter textos/labels em PT conforme convenção do projeto
- Evitar usar `.env` em produção – preferir App Settings no Azure
- Em caso de problemas de build, consultar Kudu/Log Stream e o histórico do GitHub Actions
