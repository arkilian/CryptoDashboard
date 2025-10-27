Setup rápido
===============

1. Copia o ficheiro de exemplo de ambiente e preenche os valores:

   - Windows PowerShell:

     ```powershell
     Copy-Item .env.example .env
     # Edita .env com um editor (substitui os valores de DB_*)
     ```

2. Cria e ativa um virtualenv, instala dependências e corre a app:

   ```powershell
   python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; streamlit run app.py
   ```

3. Cria o esquema de base de dados (Postgres) executando `database/tables.sql` no teu servidor PostgreSQL.

Notas:
- O ficheiro `.env` não está incluído no repositório por segurança. Usa `.env.example` como base.
- Se não conseguires conectar, confirma as variáveis `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`.
