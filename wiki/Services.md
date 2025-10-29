# Services

Descrição dos serviços e integrações em `services/`.

Principais serviços

- `coingecko.py` — Integra com a API pública CoinGecko para mapear símbolo -> id e obter preços. Implementa caching simples e retry/backoff para lidar com limites de taxa.
- `fees.py` — Lógica para obter configurações de taxas, calcular e persistir fees em `t_user_fees` e atualizar `t_user_high_water`.
- `snapshot.py` — API para criar snapshots manuais, obter histórico e recuperar o snapshot mais recente. Nota: código referencia `t_user_manual_snapshots` (migração).
- `minswap.py` — Integração com minswap (se aplicável ao projecto).

Boas práticas

- Serviços não devem manipular `st.session_state` diretamente; devem receber dados e retornar resultados.
- Cobrir chamadas externas com retries e timeouts para evitar travamentos na UI.

