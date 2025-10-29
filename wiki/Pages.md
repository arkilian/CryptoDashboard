# Pages (Streamlit)

Resumo das páginas existentes em `pages/` e o que fazem.

- `portfolio.py` — Página principal do portfólio. Permite inserir activos, obter preços via CoinGecko, criar snapshots e persistir através de `database/portfolio.py`.
- `prices.py` — Visualizações de preços e charts usando dados de `services/coingecko.py`.
- `snapshots.py` — Página para criar snapshots manuais e visualizar histórico por utilizador (usa `services/snapshot.py`).
- `settings.py` — Página de administração para configurar taxas e ver histórico (`services/fees.py`).
- `documents.py` — Visualizador de documentos/PDFs com utilitários em `utils/pdf_viewer.py`.

Dicas de UI

- `st.session_state` é usado para persistir o dataframe do portfólio entre reruns.
- O `data_editor` do Streamlit pode devolver colunas renomeadas/omitidas — o código tem handling defensivo para normalizar nomes.

Segurança

- Páginas protegidas verificam `st.session_state['user_id']` para garantir autenticação.

