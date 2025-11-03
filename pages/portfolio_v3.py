import time
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from auth.session_manager import require_auth
from css.charts import apply_theme
from database.connection import get_engine
from database.wallets import get_active_wallets
from services.cardano_sync import sync_all_cardano_wallets_for_user
from database.api_config import get_active_apis
from services.snapshots import get_historical_prices_by_symbol
from services.coingecko import get_price_by_symbol


@require_auth
def show():
    """Portfólio v3 (DB-first, Cardano)

    - Lê deltas diários de ADA/tokens guardados em DB (t_cardano_tx_io)
    - Só depois permite sincronizar novas transações com botão
    - Integra depósitos/levantamentos (t_user_capital_movements) como caixa
    """
    st.title("📈 Portfólio v3 (Cardano · DB-first)")

    engine = get_engine()
    is_admin = st.session_state.get("is_admin", False)
    current_user_id = st.session_state.get("user_id")

    # Scope do utilizador
    if is_admin:
        st.caption("Vista admin: escolhe o utilizador a analisar")
        df_users = pd.read_sql(
            "SELECT user_id, username FROM t_users ORDER BY user_id",
            engine,
        )
        user_map = {f"{r.username} (id={r.user_id})": int(r.user_id) for _, r in df_users.iterrows()}
        selected_label = st.selectbox("Utilizador", options=list(user_map.keys()))
        user_id = user_map.get(selected_label)
    else:
        user_id = current_user_id

    # Wallets Cardano deste utilizador
    wallets = get_active_wallets(user_id)
    wallets = [w for w in wallets if (w.get("blockchain") or "").lower() == "cardano"]
    if not wallets:
        st.info("ℹ️ Não há wallets Cardano ativas para este utilizador.")
        return

    options = {f"{w['wallet_name']} · {w['address'][:8]}…": int(w["wallet_id"]) for w in wallets}
    selected_labels = st.multiselect("Wallets Cardano", list(options.keys()), default=list(options.keys()))
    selected_wallet_ids = [options[l] for l in selected_labels] if selected_labels else []

    # Botão de sincronização (API só após ler DB)
    col1, col2 = st.columns([1, 1])
    with col1:
        do_sync = st.button("🔄 Sincronizar Transações Cardano", type="primary")
    with col2:
        max_pages = st.slider("Páginas (recentes)", 1, 20, 3)

    # Pré-verificações: API ativa e schema v3 existente
    # Verificar API ativa
    api_ok = True
    try:
        apis = get_active_apis()
        if not apis:
            api_ok = False
    except Exception:
        api_ok = False

    if not api_ok:
        st.error("🚫 Nenhuma API Cardano ativa encontrada. Configure em Configurações → APIs Cardano (t_api_cardano).")

    # Verificar schema v3 (tabelas Cardano)
    schema_ok = True
    try:
        df_chk = pd.read_sql(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name IN (
                't_cardano_transactions','t_cardano_tx_io','t_cardano_assets','t_cardano_sync_state'
            )
            """,
            engine,
        )
        if df_chk.shape[0] < 4:
            schema_ok = False
    except Exception:
        schema_ok = False

    if not schema_ok:
        st.error("🚫 Esquema Cardano v3 em falta. Aplique a migration: database/migrations/20251103_cardano_tx_v3.sql")

    if do_sync and api_ok and schema_ok:
        with st.spinner("A sincronizar wallets (Cardano)…"):
            res = sync_all_cardano_wallets_for_user(user_id=user_id, max_pages=max_pages)
        st.success(f"Sync concluído: {res.get('synced', 0)}/{res.get('wallets', 0)} wallets, {res.get('io_rows', 0)} linhas IO no DB")
        errs = res.get('errors') or []
        for err in errs[:5]:
            st.warning(f"Wallet {err.get('wallet_id')} ({(err.get('address') or '')[:12]}…): {err.get('error')}")
        if len(errs) > 5:
            st.info(f"…e mais {len(errs)-5} erro(s)")

    st.markdown("---")
    st.subheader("Evolução do Portfólio (DB · Cardano)")

    # Delimitar datas a partir do que existe em DB
    df_dates = pd.read_sql(
        f"""
        SELECT DISTINCT t.tx_timestamp::date AS dt
        FROM t_cardano_transactions t
        WHERE t.wallet_id = ANY(%s)
        ORDER BY dt
        """,
        engine,
        params=(selected_wallet_ids,),
    )

    # Movimentos de capital (caixa)
    df_cap = pd.read_sql(
        """
        SELECT movement_date::date AS dt,
               COALESCE(credit,0) AS credit,
               COALESCE(debit,0)  AS debit
        FROM t_user_capital_movements
        WHERE user_id = %s
        ORDER BY movement_date
        """,
        engine,
        params=(user_id,),
    )

    if df_dates.empty and df_cap.empty:
        st.info("ℹ️ Sem dados no DB. Use o botão de sincronização para carregar transações Cardano.")
        return

    # Escolha de intervalo de datas
    min_dt = min(
        [df_dates["dt"].min()] + ([df_cap["dt"].min()] if not df_cap.empty else [date.today()])
    )
    max_dt = max(
        [df_dates["dt"].max()] + ([df_cap["dt"].max()] if not df_cap.empty else [date.today()])
    )

    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Data inicial", min_dt or date.today(), min_value=min_dt or date(2020,1,1), max_value=max_dt or date.today())
    with c2:
        end_date = st.date_input("Data final", max_dt or date.today(), min_value=min_dt or date(2020,1,1), max_value=max_dt or date.today())

    # Deltas por dia (ADA lovelace + tokens raw) apenas das wallets selecionadas
    df_deltas = pd.read_sql(
        """
        WITH base AS (
            SELECT t.tx_timestamp::date AS dt,
                   i.wallet_id,
                   i.lovelace,
                   i.policy_id,
                   i.asset_name_hex,
                   i.io_type,
                   i.token_value_raw
            FROM t_cardano_tx_io i
            JOIN t_cardano_transactions t ON t.tx_hash = i.tx_hash
            WHERE i.wallet_id = ANY(%s)
              AND t.tx_timestamp::date BETWEEN %s AND %s
        ),
        agg AS (
         SELECT b.dt AS dt,
             CASE WHEN b.policy_id IS NULL THEN 'ADA' ELSE COALESCE(a.display_name, 'UNKNOWN') END AS symbol,
             SUM(CASE WHEN b.io_type='output' THEN COALESCE(b.lovelace,0) ELSE -COALESCE(b.lovelace,0) END) AS net_lovelace,
             SUM(CASE WHEN b.io_type='output' THEN COALESCE(b.token_value_raw,0) ELSE -COALESCE(b.token_value_raw,0) END) AS net_token_raw,
                   MAX(a.decimals) AS decimals
            FROM base b
            LEFT JOIN t_cardano_assets a ON a.policy_id = b.policy_id AND a.asset_name_hex = b.asset_name_hex
         GROUP BY b.dt, symbol
        )
        SELECT dt, symbol, net_lovelace, net_token_raw, COALESCE(decimals, 0) AS decimals
        FROM agg
        ORDER BY dt
        """,
        engine,
        params=(selected_wallet_ids, start_date, end_date),
    )

    # Construir tabela de variações em unidades humanas por símbolo
    rows = []
    for _, r in df_deltas.iterrows():
        sym = r["symbol"]
        if sym == "ADA":
            qty = (r["net_lovelace"] or 0) / 1_000_000.0
        else:
            dec = int(r["decimals"]) if pd.notna(r["decimals"]) else 0
            qty = (r["net_token_raw"] or 0) / (10 ** dec) if dec > 0 else float(r["net_token_raw"] or 0)
        rows.append({"date": r["dt"], "symbol": sym, "delta_qty": float(qty)})
    df_qty = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["date","symbol","delta_qty"]) 

    # Caixa (depósitos/levantamentos) acumulada
    if not df_cap.empty:
        df_cap_period = df_cap[(df_cap["dt"] >= start_date) & (df_cap["dt"] <= end_date)].copy()
        df_cap_period.sort_values("dt", inplace=True)
        df_cap_period["depositado_acum"] = df_cap_period["credit"].cumsum()
        df_cap_period["levantado_acum"] = df_cap_period["debit"].cumsum()
    else:
        df_cap_period = pd.DataFrame({"dt": [], "depositado_acum": [], "levantado_acum": []})

    # Datas alvo
    event_dates = set(df_qty["date"].tolist()) if not df_qty.empty else set()
    event_dates.update(df_cap_period["dt"].tolist() if not df_cap_period.empty else [])
    if not event_dates:
        st.info("ℹ️ Sem eventos no intervalo selecionado.")
        return
    all_dates = sorted(event_dates)

    # Pivot e acumulado por símbolo
    if not df_qty.empty:
        pivot = (
            df_qty.pivot_table(index="date", columns="symbol", values="delta_qty", aggfunc="sum")
            .fillna(0.0)
            .sort_index()
        )
        cum_holdings = pivot.cumsum().reindex(all_dates).ffill().fillna(0.0)
    else:
        cum_holdings = pd.DataFrame(index=all_dates)

    # Preços históricos por data/símbolo (CoinGecko snapshots)
    symbols = [c for c in (list(cum_holdings.columns) if not cum_holdings.empty else []) if c != "EUR"]
    prices_cache = {}
    for d in all_dates:
        # Evitar chamadas excessivas à CoinGecko: só usa snapshots já existentes em BD
        prices_cache[d] = get_historical_prices_by_symbol(symbols, d, allow_api_fallback=False) if symbols else {}

    # Série de saldo (EUR) ao longo do tempo (caixa + valor cripto)
    df_dates = pd.DataFrame({"date": all_dates})
    df_plot = df_dates.copy()
    # Merge com fluxos de capital cumulativos (forward-fill)
    if not df_cap_period.empty:
        cap = df_cap_period[["dt","depositado_acum","levantado_acum"]].rename(columns={"dt":"date"})
        df_plot = pd.merge_asof(df_plot.sort_values("date"), cap.sort_values("date"), on="date", direction="backward")
    # Garantir colunas mesmo quando não há movimentos de capital
    if "depositado_acum" not in df_plot.columns:
        df_plot["depositado_acum"] = 0.0
    if "levantado_acum" not in df_plot.columns:
        df_plot["levantado_acum"] = 0.0
    df_plot[["depositado_acum","levantado_acum"]] = df_plot[["depositado_acum","levantado_acum"]].fillna(0)

    saldo_series = []
    for d in all_dates:
        # caixa líquida
        if not df_cap_period.empty:
            cap_until = df_cap_period[df_cap_period["dt"] <= d]
            cash_from_cap = float(cap_until["credit"].sum() - cap_until["debit"].sum())
        else:
            cash_from_cap = 0.0

        # valor cripto (ADA + tokens) nessa data
        holdings_value = 0.0
        if not cum_holdings.empty and d in cum_holdings.index:
            prices = prices_cache.get(d, {})
            row = cum_holdings.loc[d]
            for sym, qty in row.items():
                if sym == "EUR":
                    continue
                price = prices.get(sym)
                if price:
                    holdings_value += float(qty) * float(price)

        saldo_series.append(cash_from_cap + holdings_value)

    df_plot["saldo_atual"] = saldo_series

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_plot["date"], y=df_plot["depositado_acum"], mode='lines+markers', name='Total Depositado', line=dict(color='#3b82f6', width=3)))
    fig.add_trace(go.Scatter(x=df_plot["date"], y=df_plot["levantado_acum"], mode='lines+markers', name='Total Levantado', line=dict(color='#ef4444', width=3)))
    fig.add_trace(go.Scatter(x=df_plot["date"], y=df_plot["saldo_atual"], mode='lines+markers', name='Saldo Atual', line=dict(color='#10b981', width=4)))
    fig.update_layout(title='Evolução do Portfólio v3 (Cardano)', xaxis_title='Data', yaxis_title='EUR', hovermode='x unified')
    fig = apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Métricas (hoje)
    total_credit = float(df_cap["credit"].sum() if not df_cap.empty else 0)
    total_debit = float(df_cap["debit"].sum() if not df_cap.empty else 0)
    cash_balance = total_credit - total_debit

    # Holdings atuais (preço de hoje)
    today_prices = get_price_by_symbol(symbols, vs_currency='eur') if symbols else {}
    crypto_value_today = 0.0
    if not cum_holdings.empty and len(cum_holdings) > 0:
        last_row = cum_holdings.iloc[-1]
        for sym, qty in last_row.items():
            if sym == 'EUR':
                continue
            p = today_prices.get(sym)
            if p:
                crypto_value_today += float(qty) * float(p)
    saldo_total = cash_balance + crypto_value_today

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Saldo Atual", f"€{saldo_total:,.2f}")
    c2.metric("📈 Total Depositado", f"€{total_credit:,.2f}")
    c3.metric("📉 Total Levantado", f"€{total_debit:,.2f}")

    st.markdown("---")
    st.subheader("Composição Atual (Cardano)")
    if not cum_holdings.empty and len(cum_holdings) > 0:
        last_row = cum_holdings.iloc[-1]
        rows = []
        for sym, qty in last_row.items():
            if sym == 'EUR':
                continue
            price = today_prices.get(sym) or 0
            value = float(qty) * float(price) if price else 0.0
            rows.append({"Ativo": sym, "Quantidade": float(qty), "Preço Atual (€)": float(price or 0), "Valor Total (€)": value})
        if rows:
            df_hold = pd.DataFrame(rows)
            df_hold["% do Portfólio"] = (df_hold["Valor Total (€)"] / saldo_total * 100).round(2) if saldo_total else 0
            st.dataframe(
                df_hold,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Quantidade": st.column_config.NumberColumn(format="%.6f"),
                    "Preço Atual (€)": st.column_config.NumberColumn(format="€%.4f"),
                    "Valor Total (€)": st.column_config.NumberColumn(format="€%.2f"),
                    "% do Portfólio": st.column_config.NumberColumn(format="%.2f%%"),
                },
            )
        else:
            st.info("📭 Sem holdings em cripto registados.")
    else:
        st.info("📭 Sem dados de holdings para apresentar.")
