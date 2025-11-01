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

    # Tabs para organizar a interface
    tab1, tab2 = st.tabs(["📝 Registar Transação", "📊 Histórico"])

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
                            "transaction_date": datetime.combine(transaction_date, datetime.min.time()),
                            "executed_by": int(st.session_state['user_id']),
                            "notes": notes or None,
                        }

                        # Usar transação explícita e SQL com parâmetros nomeados
                        with engine.begin() as conn:
                            result = conn.execute(
                                text(
                                    """
                                    INSERT INTO t_transactions 
                                    (transaction_type, asset_id, quantity, price_eur, total_eur, 
                                     fee_eur, exchange_id, transaction_date, executed_by, notes)
                                    VALUES (:transaction_type, :asset_id, :quantity, :price_eur, :total_eur, 
                                            :fee_eur, :exchange_id, :transaction_date, :executed_by, :notes)
                                    RETURNING transaction_id
                                    """
                                ),
                                params,
                            )

                            transaction_id = result.scalar_one()
                            
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
            df_assets_filter = pd.read_sql("SELECT DISTINCT symbol FROM t_assets ORDER BY symbol", engine)
            assets_list = ["Todos"] + df_assets_filter['symbol'].tolist()
            filter_asset = st.selectbox("Filtrar por ativo", assets_list, key="filter_asset")
        
        with col3:
            limit = st.number_input("Mostrar últimas", min_value=10, max_value=1000, value=50, step=10)
        
        # Construir query com filtros
        where_clauses = []
        if filter_type == "Compras":
            where_clauses.append("t.transaction_type = 'buy'")
        elif filter_type == "Vendas":
            where_clauses.append("t.transaction_type = 'sell'")
        
        if filter_asset != "Todos":
            where_clauses.append(f"a.symbol = '{filter_asset}'")
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Buscar transações
        df_transactions = pd.read_sql(f"""
            SELECT 
                t.transaction_id,
                t.transaction_date::date as "Data",
                CASE 
                    WHEN t.transaction_type = 'buy' THEN '🟢 Compra'
                    ELSE '🔴 Venda'
                END as "Tipo",
                a.symbol as "Ativo",
                t.quantity as "Quantidade",
                t.price_eur as "Preço (€)",
                t.total_eur as "Total (€)",
                t.fee_eur as "Taxa (€)",
                e.name as "Exchange",
                u.username as "Executado por",
                t.notes as "Notas"
            FROM t_transactions t
            JOIN t_assets a ON t.asset_id = a.asset_id
            LEFT JOIN t_exchanges e ON t.exchange_id = e.exchange_id
            LEFT JOIN t_users u ON t.executed_by = u.user_id
            {where_sql}
            ORDER BY t.transaction_date DESC, t.transaction_id DESC
            LIMIT {limit}
        """, engine)
        
        if df_transactions.empty:
            st.info("📭 Nenhuma transação registada ainda.")
        else:
            # Estatísticas rápidas
            total_buy = df_transactions[df_transactions['Tipo'] == '🟢 Compra']['Total (€)'].sum()
            total_sell = df_transactions[df_transactions['Tipo'] == '🔴 Venda']['Total (€)'].sum()
            total_fees = df_transactions['Taxa (€)'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Transações", len(df_transactions))
            with col2:
                st.metric("🟢 Total Compras", f"€{total_buy:,.2f}")
            with col3:
                st.metric("🔴 Total Vendas", f"€{total_sell:,.2f}")
            with col4:
                st.metric("💸 Total Taxas", f"€{total_fees:,.2f}")
            
            # Tabela de transações
            st.dataframe(
                df_transactions.drop('transaction_id', axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # Holdings atuais (calculados a partir das transações)
            st.divider()
            st.subheader("📦 Holdings Atuais (calculados)")
            
            df_holdings = pd.read_sql("""
                SELECT 
                    a.symbol as "Ativo",
                    a.name as "Nome",
                    SUM(CASE 
                        WHEN t.transaction_type = 'buy' THEN t.quantity
                        WHEN t.transaction_type = 'sell' THEN -t.quantity
                        ELSE 0
                    END) as "Quantidade Total",
                    SUM(CASE 
                        WHEN t.transaction_type = 'buy' THEN t.total_eur + t.fee_eur
                        WHEN t.transaction_type = 'sell' THEN -(t.total_eur - t.fee_eur)
                        ELSE 0
                    END) as "Custo Total (€)"
                FROM t_transactions t
                JOIN t_assets a ON t.asset_id = a.asset_id
                GROUP BY a.asset_id, a.symbol, a.name
                HAVING SUM(CASE 
                    WHEN t.transaction_type = 'buy' THEN t.quantity
                    WHEN t.transaction_type = 'sell' THEN -t.quantity
                    ELSE 0
                END) > 0.00000001
                ORDER BY a.symbol
            """, engine)
            
            if df_holdings.empty:
                st.info("📭 Nenhum holding atual (todas as posições foram vendidas ou não há transações).")
            else:
                # Calcular preço médio
                df_holdings['Preço Médio (€)'] = df_holdings['Custo Total (€)'] / df_holdings['Quantidade Total']
                
                st.dataframe(
                    df_holdings,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Quantidade Total": st.column_config.NumberColumn(format="%.8f"),
                        "Custo Total (€)": st.column_config.NumberColumn(format="€%.2f"),
                        "Preço Médio (€)": st.column_config.NumberColumn(format="€%.6f")
                    }
                )

    st.divider()
    st.caption("💡 **Dica**: Todas as transações aqui registadas afetam a carteira global do fundo e são usadas para calcular a performance e as comissões.")

if __name__ == "__main__":
    show()
