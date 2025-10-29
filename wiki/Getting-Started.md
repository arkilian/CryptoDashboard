# Getting Started

Este guia descreve os passos mínimos para executar o Crypto Dashboard localmente.

Pré-requisitos

- Python 3.10+
- PostgreSQL
- Git

Passos

1. Clone o repositório (ou copie os ficheiros para o seu workspace):

```powershell
git clone <repo-url> CryptoDashboard
cd CryptoDashboard
```

2. Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # PowerShell
```

3. Instale dependências:

```powershell
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente copiando `.env.example` para `.env` e atualizando as credenciais do PostgreSQL.

5. Execute as migrações para criar tabelas necessárias:

```powershell
python .\database\run_migrations.py
```

(ou, para apenas criar o schema base):

```powershell
psql -U <user> -d <database> -f database/tables.sql
```

6. Inicie a aplicação Streamlit:

```powershell
streamlit run app.py
```

Testes

Execute os testes unitários:

```powershell
python -m unittest discover tests
```

Notas

- Se encontrar erros de `ModuleNotFoundError` para `plotly` ou outras libs, confirme que o ambiente virtual está activado e as dependências instaladas.
- Para publicar documentação no GitHub Wiki, clone o repositório wiki: `git clone https://github.com/<user>/<repo>.wiki.git` e copie estes ficheiros markdown para lá.