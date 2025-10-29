# Development

Como desenvolver e contribuir para o projeto localmente.

Fluxo recomendado

1. Crie uma branch por feature/bugfix:

```powershell
git checkout -b feat/descricao
```

2. Execute testes locais frequentemente:

```powershell
python -m unittest discover tests
```

3. Mantenha o `requirements.txt` actualizado ao adicionar dependências.

4. Para alterações na base de dados, adicionar um script SQL em `database/migrations/` com nome numérico sequencial (e.g. `004_add_foo.sql`). O runner aplica migrações automaticamente.

Style & Lint

- Siga PEP8; prefer usar `black` ou `ruff` no CI se quiser adicionar checks.

Debugging com Streamlit

- Use `st.write()` ou `st.sidebar` para diagnosticar `st.session_state`.
- Reinicie o Streamlit (`streamlit run app.py`) após mudanças de dependências.

Publicar Wiki

- Para publicar este wiki numa repo GitHub separada (o wiki do repo é um repo Git separado), clone o wiki remoto:

```powershell
git clone https://github.com/<user>/<repo>.wiki.git
# copiar ficheiros markdown do diretório wiki/ para o repositório .wiki e fazer push
```

