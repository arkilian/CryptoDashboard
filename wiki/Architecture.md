# Architecture

Resumo de alto-nível da arquitectura do projeto.

Componentes principais

- Streamlit frontend: `app.py` + `pages/` — páginas interactivas que compõem a UI.
- Serviços: `services/` — encapsula integrações externas e lógica de negócio (CoinGecko, fees, snapshots, minswap etc.).
- Database: `database/` — código de ligação (`connection.py`), helpers (`portfolio.py`, `users.py`) e scripts SQL (`tables.sql`, `migrations/`).
- Autenticação: `auth/` — páginas e helpers de login, registo e gestão da sessão.
- Utilities: `utils/` — helpers para formatação, PDF viewer e segurança.

Estrutura de ficheiros (resumida)

```
app.py
auth/
  login.py
  register.py
  session_manager.py
database/
  connection.py
  portfolio.py
  users.py
  tables.sql
  migrations/
pages/
  portfolio.py
  prices.py
  snapshots.py
  settings.py
services/
  coingecko.py
  fees.py
  snapshot.py
utils/
  formatters.py
  security.py
```

Fluxo de execução

- `app.py` inicializa o `streamlit` e `st.session_state`, mostra a página de login ou o menu principal.
- Páginas chamam serviços para obter dados (e.g. `services/coingecko.py` para preços) e `database/*` para persistência.
- `database/run_migrations.py` aplica migrações presentes em `database/migrations/`.

Design notes

- A separação entre `pages/` e `services/` facilita testes e reutilização da lógica de negócio.
- Migrações incrementais existem em `database/migrations/` — o runner cria uma tabela `t_migrations` para controlar execução.
- Sessões Streamlit são mantidas em `st.session_state`; existe código defensivo para evitar KeyError em reloads.
