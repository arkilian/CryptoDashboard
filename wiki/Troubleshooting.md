# Troubleshooting

Erros comuns e correções rápidas.

1) TypeError: DataEditorMixin.data_editor() got an unexpected keyword argument 'value'

Causa: versão do Streamlit instalada usa `data` como nome do parâmetro em vez de `value`.
Correção: alterar chamadas `st.data_editor(value=...)` para `st.data_editor(data=...)`.

2) psycopg2.errors.UndefinedTable: relation "t_user_manual_snapshots" does not exist

Causa: a tabela `t_user_manual_snapshots` é criada por uma migração (`database/migrations/003_add_manual_snapshots.sql`) e não está presente no `database/tables.sql`.
Correção: execute `python .\database\run_migrations.py` ou executar a migração manualmente com `psql -f database/migrations/003_add_manual_snapshots.sql`.

3) KeyError: 'quantity' ao computar colunas

Causa: o utilizador removeu/renomeou colunas no `st.data_editor` e o código assume colunas `quantity` e `price` existirem.
Correção: atualizar o código para lidar defensivamente com nomes alternativos e preencher defaults (o código já faz isso em `pages/portfolio.py`).

4) ModuleNotFoundError: plotly

Causa: dependência não instalada no venv.
Correção: active o venv e corra `pip install -r requirements.txt`.

5) Erros do CoinGecko (rate limit / timeout)

Causa: CoinGecko pode limitar pedidos públicos.
Correção: implementar retry/backoff (existe em `services/coingecko.py`) e cache local dos ids/preços.

Se não conseguir resolver, cole o traceback e eu ajudo a diagnosticar.