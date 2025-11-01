"""Página de registo de transações (compra/venda de ativos).

Esta página permite ao administrador registar todas as operações de trading
realizadas na carteira do fundo (compras e vendas de criptomoedas).
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import get_engine
from sqlalchemy import text
import requests
from utils.tags import ensure_default_tags, get_all_tags, build_tags_where_clause, set_transaction_tags
from components.transaction_form_v2 import render_transaction_form

def show():
    """Exibe a página de transações."""
    # Verificar autenticação
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.warning("🔐 Por favor inicie sessão para aceder a esta página.")
        st.session_state['page'] = 'login'
        st.rerun()
        return

    st.title("💰 Transações de Ativos")

    # Verificar se o utilizador é admin
    if not st.session_state.get('is_admin', False):
        st.error("⛔ Acesso negado. Esta página é exclusiva para administradores.")
        st.stop()

    engine = get_engine()

    # Ensure tags tables and defaults exist
    try:
        ensure_default_tags(engine)
    except Exception:
        pass

    # Tabs para organizar a interface
    tab1, tab2, tab3 = st.tabs(["📝 Registar Transação (Legacy)", "📊 Histórico", "🆕 Novo UI (V2)"])


    with tab1:
        st.subheader("Registar Nova Transação")
        
        # Calcular saldo disponível em EUR (depósitos - levantamentos - compras + vendas)
        df_cap = pd.read_sql(
            """
            SELECT 
                COALESCE(SUM(COALESCE(tucm.credit,0)),0) AS total_credit,
                COALESCE(SUM(COALESCE(tucm.debit,0)),0)  AS total_debit
            FROM t_user_capital_movements tucm
            JOIN t_users tu ON tucm.user_id = tu.user_id
            WHERE tu.is_admin = FALSE
            """,
            engine,
        )
        df_tx = pd.read_sql(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'buy'  THEN total_eur + fee_eur ELSE 0 END),0) AS spent,
                COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN total_eur - fee_eur ELSE 0 END),0) AS received
            FROM t_transactions
            """,
            engine,
        )
        total_credit = float(df_cap.iloc[0]["total_credit"]) if not df_cap.empty else 0.0
        total_debit = float(df_cap.iloc[0]["total_debit"]) if not df_cap.empty else 0.0
        spent = float(df_tx.iloc[0]["spent"]) if not df_tx.empty else 0.0
        received = float(df_tx.iloc[0]["received"]) if not df_tx.empty else 0.0
        available_cash = total_credit - total_debit - spent + received

        st.metric("💶 Saldo disponível (EUR)", f"€{available_cash:,.2f}")

        # Buscar ativos disponíveis (inclui coingecko_id para preço de mercado)
        df_assets = pd.read_sql("SELECT asset_id, symbol, name, coingecko_id FROM t_assets ORDER BY symbol", engine)
        
        if df_assets.empty:
            st.warning("⚠️ Nenhum ativo encontrado. Adicione ativos primeiro na página de configurações.")
        else:
            # Buscar exchanges disponíveis
            df_exchanges = pd.read_sql("SELECT exchange_id, name FROM t_exchanges ORDER BY name", engine)
            
            # Data da transação (antes de tudo para estar disponível no botão)
            transaction_date = st.date_input("Data da Transação", value=datetime.now().date(), key="tx_date_input")
            
            # Guardar data selecionada em session_state
            prev_date = st.session_state.get("tx_target_date")
            if transaction_date != prev_date:
                st.session_state["tx_target_date"] = transaction_date
                # Reset preço quando muda a data
                st.session_state["tx_price"] = 0.0
                st.session_state.pop("tx_market_price", None)
                st.session_state.pop("tx_market_price_date", None)
            
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_type = st.selectbox(
                    "Tipo de Transação",
                    ["buy", "sell"],
                    format_func=lambda x: "🟢 Compra" if x == "buy" else "🔴 Venda"
                )
                
                # Dropdown de ativos - optimized using pandas operations
                asset_options = dict(zip(
                    df_assets.apply(lambda row: f"{row['symbol']} - {row['name']}", axis=1),
                    zip(df_assets['asset_id'], df_assets.get('coingecko_id', [None] * len(df_assets)))
                ))
                selected_asset = st.selectbox("Ativo", list(asset_options.keys()), key="tx_asset_select")
                asset_id, asset_cg_id = asset_options[selected_asset]

                # Reset preço quando muda o ativo selecionado
                prev_asset = st.session_state.get("tx_prev_asset")
                if prev_asset != asset_id:
                    st.session_state.pop("tx_price", None)
                    st.session_state.pop("tx_market_price", None)
                    st.session_state.pop("tx_market_price_date", None)
                    st.session_state["tx_prev_asset"] = asset_id
                
                quantity = st.number_input(
                    "Quantidade",
                    min_value=0.0,
                    value=0.0,
                    step=0.00000001,
                    format="%.8f"
                )
            
            with col2:
                # Campo de preço
                price_eur = st.number_input(
                    "Preço Unitário (€)",
                    min_value=0.0,
                    value=float(st.session_state.get("tx_price", 0.0)),
                    step=0.000001,
                    format="%.6f",
                    key="tx_price_input",
                )
                # manter sincronizado com session_state
                st.session_state["tx_price"] = price_eur
                
                # Botão e último preço lado a lado
                col_btn, col_info = st.columns([1, 1])
                
                with col_btn:
                    if st.button("🔄 Usar preço de mercado", use_container_width=True, key="btn_market_price"):
                        if asset_cg_id:
                            # Buscar data da transação para obter preço histórico
                            target_date = st.session_state.get("tx_target_date", datetime.now().date())
                            
                            try:
                                from services.snapshots import get_historical_price
                                
                                # Buscar preço histórico da data selecionada
                                price = get_historical_price(int(asset_id), target_date)
                                
                                if price and price > 0:
                                    st.session_state["tx_price"] = round(price, 6)
                                    st.session_state["tx_market_price"] = price
                                    st.session_state["tx_market_price_date"] = target_date
                                    st.success(f"✅ Preço aplicado: €{price:,.6f} ({target_date})")
                                    st.rerun()
                                else:
                                    st.warning(f"Preço de mercado não disponível para {target_date}.")
                            except Exception as e:
                                st.error(f"❌ Erro ao obter preço: {e}")
                        else:
                            st.info("Configure o CoinGecko ID do ativo em ⚙️ Configurações > 🪙 Ativos.")
                
                with col_info:
                    # Mostrar último preço de mercado (se disponível)
                    market_price = st.session_state.get("tx_market_price")
                    market_date = st.session_state.get("tx_market_price_date")
                    if market_price:
                        date_str = f" ({market_date})" if market_date else ""
                        st.markdown(f"**💡 Último:**  \n€{market_price:,.6f}{date_str}")
                    else:
                        st.markdown("**💡 Último:**  \n—")
                
                if not df_exchanges.empty:
                    # Optimized using pandas to_dict
                    exchange_options = dict(zip(df_exchanges['name'], df_exchanges['exchange_id']))
                    exchange_options["Não especificar"] = None
                    selected_exchange = st.selectbox("Exchange", list(exchange_options.keys()))
                    exchange_id = exchange_options[selected_exchange]
                else:
                    st.info("💡 Nenhuma exchange cadastrada")
                    exchange_id = None
                
                fee_eur = st.number_input(
                    "Taxa da Exchange (€)",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f"
                )

            
            # Cálculo automático do total
            total_eur = quantity * price_eur
            st.metric("💵 Total da Transação", f"€{total_eur:,.2f}")
            
            if fee_eur > 0:
                if transaction_type == "buy":
                    st.caption(f"Custo total (com taxa): €{total_eur + fee_eur:,.2f}")
                else:
                    st.caption(f"Valor recebido (após taxa): €{total_eur - fee_eur:,.2f}")
            
            notes = st.text_area("Notas/Observações", placeholder="Ex: Rebalanceamento mensal, aproveitamento de dip, etc.")

            # Seleção de Conta (se houver exchange selecionada)
            account_id = None
            if exchange_id:
                df_accounts = pd.read_sql(
                    "SELECT account_id, name, COALESCE(account_category,'') AS account_category FROM t_exchange_accounts WHERE exchange_id = %s ORDER BY name",
                    engine,
                    params=(int(exchange_id),)
                )
                if not df_accounts.empty:
                    acc_map = {f"{row['name']} ({row['account_category'] or '—'})": int(row['account_id']) for _, row in df_accounts.iterrows()}
                    acc_map["Não especificar"] = None
                    selected_acc = st.selectbox("Conta", list(acc_map.keys()))
                    account_id = acc_map[selected_acc]

            # Tags de estratégia (multi)
            tag_options = get_all_tags(engine)
            tag_labels = {t["label"]: t["code"] for t in tag_options}
            selected_tag_labels = st.multiselect(
                "Tags (estratégia)",
                options=list(tag_labels.keys()),
                help="Classifique a transação com tags como Staking, DeFi, etc. Pode gerir tags em Configurações futuramente.",
            )
            selected_tag_codes = [tag_labels[lbl] for lbl in selected_tag_labels]
            
            if st.button("Registar Transação", type="primary", use_container_width=True):
                if quantity <= 0:
                    st.error("❌ A quantidade deve ser maior que zero!")
                elif price_eur <= 0:
                    st.error("❌ O preço deve ser maior que zero!")
                elif transaction_type == "buy" and (total_eur + fee_eur) > available_cash + 1e-9:
                    st.error(f"❌ Saldo insuficiente. Disponível: €{available_cash:,.2f} | Necessário: €{(total_eur + fee_eur):,.2f}")
                else:
                    try:
                        # Preparar parâmetros nomeados e tipos apropriados
                        params = {
                            "transaction_type": transaction_type,
                            "asset_id": int(asset_id),
                            "quantity": float(quantity),
                            "price_eur": float(price_eur),
                            "total_eur": float(total_eur),
                            "fee_eur": float(fee_eur),
                            "exchange_id": exchange_id,
                            "account_id": account_id,
                            "transaction_date": datetime.combine(transaction_date, datetime.min.time()),
                            "executed_by": int(st.session_state['user_id']),
                            "notes": notes or None,
                        }

                        # Usar transação explícita e SQL com parâmetros nomeados
                        with engine.begin() as conn:
                            sql = text(
                                """
                                INSERT INTO t_transactions 
                                (transaction_type, asset_id, quantity, price_eur, total_eur, 
                                 fee_eur, exchange_id, account_id, transaction_date, executed_by, notes)
                                VALUES (:transaction_type, :asset_id, :quantity, :price_eur, :total_eur, 
                                        :fee_eur, :exchange_id, :account_id, :transaction_date, :executed_by, :notes)
                                RETURNING transaction_id
                                """
                            )

                            result = conn.execute(sql, params)

                            transaction_id = result.scalar_one()
                            # Guardar tags N:N
                            try:
                                set_transaction_tags(engine, transaction_id, selected_tag_codes)
                            except Exception:
                                pass
                            
                            st.success(f"✅ Transação #{transaction_id} registada com sucesso!")
                            st.balloons()
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao registar transação: {str(e)}")

    with tab2:
        st.subheader("Histórico de Transações")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filtrar por tipo",
                ["Todas", "Compras", "Vendas"],
                key="filter_type"
            )
        
        with col2:
            # Buscar símbolos e IDs para filtrar por ativo em todas as colunas relevantes (V2)
            df_assets_filter = pd.read_sql("SELECT asset_id, symbol FROM t_assets ORDER BY symbol", engine)
            assets_list = ["Todos"] + df_assets_filter['symbol'].tolist()
            symbol_to_id = dict(zip(df_assets_filter['symbol'], df_assets_filter['asset_id']))
            filter_asset = st.selectbox("Filtrar por ativo", assets_list, key="filter_asset")
        
        with col3:
            limit = st.number_input("Mostrar últimas", min_value=10, max_value=1000, value=50, step=10)

        # Linha 2 de filtros: filtros por Conta e Categoria de Conta
        st.markdown("")
        colc1, colc2, colc3 = st.columns([2, 2, 1])
        # Contas disponíveis
        df_all_accounts = pd.read_sql(
            "SELECT ea.account_id, e.name AS exchange, ea.name AS account, COALESCE(ea.account_category,'') AS category FROM t_exchange_accounts ea JOIN t_exchanges e ON ea.exchange_id = e.exchange_id ORDER BY e.name, ea.name",
            engine
        )
        with colc1:
            account_filter_options = [f"{row['exchange']} - {row['account']}" for _, row in df_all_accounts.iterrows()]
            selected_accounts_labels = st.multiselect("Contas", options=account_filter_options, key="tx_accounts_filter")
            selected_account_ids = set()
            if selected_accounts_labels:
                label_to_id = {f"{row['exchange']} - {row['account']}": int(row['account_id']) for _, row in df_all_accounts.iterrows()}
                selected_account_ids = {label_to_id[l] for l in selected_accounts_labels}
        with colc2:
            categories = sorted(list(set(df_all_accounts['category'].dropna().tolist() + [""])) )
            selected_account_cats = st.multiselect("Categoria de Conta", options=[c for c in categories if c], key="tx_account_cat_filter")
        with colc3:
            include_no_account = st.checkbox("Incluir sem conta", value=True)

        # Construir query com filtros
        where_clauses = []
        if filter_type == "Compras":
            where_clauses.append("t.transaction_type = 'buy'")
        elif filter_type == "Vendas":
            where_clauses.append("t.transaction_type = 'sell'")
        
        if filter_asset != "Todos":
            # Mapear símbolo para asset_id e aplicar aos campos V2 (from/to/fee) e legado (asset_id)
            asset_id_filter = symbol_to_id.get(filter_asset)
            if asset_id_filter is not None:
                where_clauses.append(
                    f"(t.asset_id = {int(asset_id_filter)} OR t.from_asset_id = {int(asset_id_filter)} OR t.to_asset_id = {int(asset_id_filter)} OR t.fee_asset_id = {int(asset_id_filter)})"
                )

        # Filtros por conta/categoria de conta (V2)
        selected_ids_full = set(selected_account_ids)
        if selected_account_cats:
            cat_ids = set(df_all_accounts[df_all_accounts['category'].isin(selected_account_cats)]['account_id'].astype(int).tolist())
            selected_ids_full |= cat_ids
        if selected_ids_full:
            ids_list = ",".join(str(i) for i in sorted(selected_ids_full))
            where_clauses.append(
                f"(t.account_id IN ({ids_list}) OR t.from_account_id IN ({ids_list}) OR t.to_account_id IN ({ids_list}))"
            )
        if not include_no_account:
            where_clauses.append("(t.account_id IS NOT NULL OR t.from_account_id IS NOT NULL OR t.to_account_id IS NOT NULL)")

        # Linha 3 de filtros: Tags de estratégia
        st.markdown("")
        tag_options = get_all_tags(engine)
        tag_labels = {t["label"]: t["code"] for t in tag_options}
        selected_tag_labels_filter = st.multiselect(
            "Tags (estratégia)",
            options=list(tag_labels.keys()),
            key="tx_tags_filter",
            help="Filtra por tags como Staking, DeFi, etc.",
        )
        selected_tag_codes_filter = [tag_labels[lbl] for lbl in selected_tag_labels_filter]
        tags_clause = build_tags_where_clause(selected_tag_codes_filter, tx_alias="t")
        if tags_clause:
            where_clauses.append(tags_clause)
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Buscar transações (modelo V2)
        df_transactions = pd.read_sql(f"""
            SELECT 
                t.transaction_id,
                t.transaction_date::date AS "Data",
                t.transaction_type AS "Tipo (código)",
                COALESCE(
                    CASE t.transaction_type 
                        WHEN 'buy' THEN '🟢 Compra'
                        WHEN 'sell' THEN '🔴 Venda'
                        WHEN 'deposit' THEN '💶 Depósito'
                        WHEN 'withdrawal' THEN '💶 Levantamento'
                        WHEN 'swap' THEN '🔄 Swap'
                        WHEN 'transfer' THEN '➡️ Transferência'
                        WHEN 'stake' THEN '🔒 Stake'
                        WHEN 'unstake' THEN '🔓 Unstake'
                        WHEN 'reward' THEN '🎁 Recompensa'
                        WHEN 'lend' THEN '🏦 Lend'
                        WHEN 'borrow' THEN '🏦 Borrow'
                        WHEN 'repay' THEN '💳 Repay'
                        WHEN 'liquidate' THEN '⚠️ Liquidação'
                        ELSE t.transaction_type
                    END,
                    t.transaction_type
                ) AS "Tipo",
                af.symbol AS "De Ativo",
                t.from_quantity AS "Qtd De",
                at.symbol AS "Para Ativo",
                t.to_quantity AS "Qtd Para",
                efrom.name AS "De Exchange",
                afrom.name AS "De Conta",
                eto.name AS "Para Exchange",
                ato.name AS "Para Conta",
                e.name AS "Exchange (principal)",
                a.name AS "Conta (principal)",
                faf.symbol AS "Taxa Asset",
                t.fee_quantity AS "Taxa Qtd",
                t.fee_eur AS "Taxa (€)",
                (
                    SELECT string_agg(tg.tag_code, ', ' ORDER BY tg.tag_code)
                    FROM t_transaction_tags tt
                    JOIN t_tags tg ON tt.tag_id = tg.tag_id
                    WHERE tt.transaction_id = t.transaction_id
                ) AS "Tags",
                u.username AS "Executado por",
                t.notes AS "Notas"
            FROM t_transactions t
            LEFT JOIN t_assets af ON t.from_asset_id = af.asset_id
            LEFT JOIN t_assets at ON t.to_asset_id = at.asset_id
            LEFT JOIN t_assets faf ON t.fee_asset_id = faf.asset_id
            LEFT JOIN t_exchange_accounts a ON t.account_id = a.account_id
            LEFT JOIN t_exchanges e ON a.exchange_id = e.exchange_id
            LEFT JOIN t_exchange_accounts afrom ON t.from_account_id = afrom.account_id
            LEFT JOIN t_exchanges efrom ON afrom.exchange_id = efrom.exchange_id
            LEFT JOIN t_exchange_accounts ato ON t.to_account_id = ato.account_id
            LEFT JOIN t_exchanges eto ON ato.exchange_id = eto.exchange_id
            LEFT JOIN t_users u ON t.executed_by = u.user_id
            {where_sql}
            ORDER BY t.transaction_date DESC, t.transaction_id DESC
            LIMIT {limit}
        """, engine)
        
        if df_transactions.empty:
            st.info("📭 Nenhuma transação registada ainda.")
        else:
            # Estatísticas rápidas (V2)
            try:
                buy_mask = df_transactions.get('Tipo (código)', pd.Series(dtype=str)) == 'buy'
                sell_mask = df_transactions.get('Tipo (código)', pd.Series(dtype=str)) == 'sell'
                total_buy = df_transactions.loc[buy_mask, 'Qtd De'].fillna(0).sum()
                total_sell = df_transactions.loc[sell_mask, 'Qtd Para'].fillna(0).sum()
            except Exception:
                total_buy = 0.0
                total_sell = 0.0
            total_fees = df_transactions.get('Taxa (€)', pd.Series(dtype=float)).fillna(0).sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Transações", len(df_transactions))
            with col2:
                st.metric("🟢 Total Compras (EUR gasto)", f"€{total_buy:,.2f}")
            with col3:
                st.metric("🔴 Total Vendas (EUR recebido)", f"€{total_sell:,.2f}")
            with col4:
                st.metric("💸 Total Taxas", f"€{total_fees:,.2f}")
            
            # Tabela de transações (V2)
            display_df = df_transactions.drop(columns=['transaction_id', 'Tipo (código)'], errors='ignore')
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Secção de holdings movida para � Portfólio

    # Novo UI (V2)
    with tab3:
        try:
            render_transaction_form(engine)
        except Exception as e:
            st.error(f"❌ Erro ao carregar o formulário V2: {e}")

    st.divider()
    st.caption("💡 **Dica**: Todas as transações aqui registadas afetam a carteira global do fundo e são usadas para calcular a performance e as comissões.")

if __name__ == "__main__":
    show()
