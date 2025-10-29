# Contributing

Boas-vindas! Eis como pode contribuir para o Crypto Dashboard.

1. Fork & Branch

- Fork o repositório e crie uma branch específica para a sua feature/bugfix:

```powershell
git checkout -b feat/sua-feature
```

2. Testes

- Adicione testes para novas funcionalidades e corra `python -m unittest discover tests`.

3. Migrações de BD

- Para mudanças no schema, crie um novo ficheiro na pasta `database/migrations/` com um prefixo sequencial (e.g. `004_add_xxx.sql`). O runner aplica as migrações e regista em `t_migrations`.

4. Pull Request

- Abra um PR com descrição clara, screenshots se for UI e um resumo dos testes realizados.

5. Review

- O maintainer fará review; esteja disponível para fazer alterações solicitadas.

Contacto

- Para questões urgentes, abra um issue descrevendo o problema e logs relevantes.
