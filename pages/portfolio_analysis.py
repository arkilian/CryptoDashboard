import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
from database.connection import get_connection, return_connection, get_engine
from auth.session_manager import require_auth
from css.charts import apply_theme


def _calculate_holdings_vectorized(df_tx):
    """Calculate holdings using vectorized operations instead of iterrows.
    
    Args:
        df_tx: DataFrame with columns: symbol, quantity, transaction_type
        
    Returns:
        dict: {symbol: net_quantity}
    """
    if df_tx.empty:
        return {}
    
    # Create a copy to avoid modifying original
    df = df_tx.copy()
    
    # Use numpy.where for fully vectorized operation (faster than apply)
    import numpy as np
    df['signed_qty'] = np.where(
        df['transaction_type'] == 'buy',
        df['quantity'],
        -df['quantity']
    )
    
    # Group by symbol and sum quantities
    holdings = df.groupby('symbol')['signed_qty'].sum().to_dict()
    
    # Filter out zero or negative holdings
    return {sym: qty for sym, qty in holdings.items() if qty > 0}


@require_auth
def show():
    """
    Análise de Portfólio - mostra evolução do saldo e gráficos de performance.
    Adaptado do ficheiro 2000.py - menu "📈 Portofolio"
    """
    st.title("📈 Análise de Portfólio")
    
    conn = None
    
    try:
        conn = get_connection()
        engine = get_engine()
        
        # Verificar se é admin para mostrar seletor de utilizadores
        is_admin = st.session_state.get("is_admin", False)
        
        if is_admin:
            # Admin pode ver "Todos" (fundo comunitário) ou utilizador individual
            # Cache user list to avoid redundant queries
            cache_key = "portfolio_analysis_users"
            cache_time_key = "portfolio_analysis_users_time"
            
            import time
            current_time = time.time()
            
            # Check if cache is valid (30 seconds TTL)
            if (cache_key in st.session_state and 
                cache_time_key in st.session_state and
                current_time - st.session_state[cache_time_key] < 30):
                df_users = st.session_state[cache_key]
            else:
                df_users = pd.read_sql(
                    "SELECT tu.user_id, tu.username, tup.email FROM t_users tu LEFT JOIN t_user_profile tup ON tu.user_id = tup.user_id ORDER BY tu.user_id",
                    engine
                )
                st.session_state[cache_key] = df_users
                st.session_state[cache_time_key] = current_time
            
            # Adicionar opção "Todos (Fundo Comunitário)" no início
            opcoes = ["💰 Todos (Fundo Comunitário)"]
            # Use list comprehension with apply for better performance
            user_options = df_users.apply(
                lambda row: f"{row['username']} ({row['email'] or 'sem email'})", 
                axis=1
            ).tolist()
            opcoes += user_options
            
            # Selectbox com pesquisa
            selecionado = st.selectbox("🔍 Escolhe uma vista", opcoes)
            
            # Determinar se é vista agregada ou utilizador específico
            if selecionado == "💰 Todos (Fundo Comunitário)":
                user_id = None  # None = todos os utilizadores
                user_name = "Fundo Comunitário"
            else:
                # Create lookup dictionary for efficient user ID retrieval
                user_lookup = dict(zip(user_options, df_users['user_id']))
                user_name_lookup = dict(zip(user_options, df_users['username']))
                
                user_id = user_lookup.get(selecionado)
                user_name = user_name_lookup.get(selecionado)
        else:
            # Utilizador normal só vê o próprio portfólio
            user_id = st.session_state.get("user_id")
            user_name = st.session_state.get("username")
        
        # Obter movimentos reais da base de dados
        if user_id is None and is_admin:
            # Vista agregada - todos os utilizadores (exceto admins)
            df_mov = pd.read_sql("""
                SELECT tucm.movement_date::date AS date,
                       SUM(COALESCE(tucm.credit, 0) - COALESCE(tucm.debit, 0)) AS net_movement
                FROM t_user_capital_movements tucm
                JOIN t_users tu ON tucm.user_id = tu.user_id
                WHERE tu.is_admin = FALSE
                GROUP BY tucm.movement_date::date
                ORDER BY tucm.movement_date
            """, engine)
        elif user_id:
            # Vista de utilizador específico
            df_mov = pd.read_sql("""
                SELECT movement_date::date AS date,
                       COALESCE(credit, 0) - COALESCE(debit, 0) AS net_movement
                FROM t_user_capital_movements
                WHERE user_id = %s
                ORDER BY movement_date
            """, engine, params=(user_id,))
        else:
            df_mov = pd.DataFrame()  # Fallback
        
        # Se não houver movimentos, mostrar aviso
        if df_mov.empty:
            st.info("ℹ️ Ainda não há movimentos registados.")
        else:
            # Calcular saldo acumulado
            df_mov["balance"] = df_mov["net_movement"].cumsum()
            
            # Determinar limites de data
            min_date = df_mov["date"].min()
            max_date = max(df_mov["date"].max(), date.today())
            
            # Título dinâmico
            if user_id is None and is_admin:
                st.markdown("### 💼 Fundo Comunitário (Todos os Utilizadores)")
            elif user_id in [1, 2]:
                st.markdown("### 💼 Conta Administrativa")
            else:
                st.markdown(f"### 💼 Portfólio de {user_name}")
            
            # Filtros de data
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "📅 Data inicial",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date
                )
            with col2:
                end_date = st.date_input(
                    "📅 Data final",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Filtrar por data
            df_filtered = df_mov[
                (df_mov["date"] >= start_date) &
                (df_mov["date"] <= end_date)
            ]
            
            if df_filtered.empty:
                st.warning("⚠️ Não há dados para o período selecionado.")
            else:
                # Gráfico de evolução: Total Depositado vs Total Levantado (acumulado)
                st.markdown("### 📊 Evolução do Portfólio")
                
                # Buscar créditos e débitos por dia conforme o contexto (agregado ou utilizador específico)
                if user_id is None and is_admin:
                    df_cap = pd.read_sql(
                        """
                        SELECT tucm.movement_date::date AS date,
                               COALESCE(SUM(COALESCE(tucm.credit,0)),0) AS total_credit,
                               COALESCE(SUM(COALESCE(tucm.debit,0)),0)  AS total_debit
                        FROM t_user_capital_movements tucm
                        JOIN t_users tu ON tucm.user_id = tu.user_id
                        WHERE tu.is_admin = FALSE
                        GROUP BY tucm.movement_date::date
                        ORDER BY tucm.movement_date
                        """,
                        engine,
                    )
                elif user_id:
                    df_cap = pd.read_sql(
                        """
                        SELECT movement_date::date AS date,
                               COALESCE(credit,0) AS total_credit,
                               COALESCE(debit,0)  AS total_debit
                        FROM t_user_capital_movements
                        WHERE user_id = %s
                        ORDER BY movement_date
                        """,
                        engine,
                        params=(user_id,),
                    )
                else:
                    df_cap = pd.DataFrame(columns=["date","total_credit","total_debit"])

                if df_cap.empty:
                    st.info("ℹ️ Sem dados de depósitos/levantamentos para o período.")
                else:
                    # Filtra por intervalo selecionado
                    df_cap = df_cap[(df_cap["date"] >= start_date) & (df_cap["date"] <= end_date)].copy()
                    if df_cap.empty:
                        st.info("ℹ️ Sem dados de depósitos/levantamentos no intervalo selecionado.")
                    else:
                        df_cap.sort_values("date", inplace=True)
                        df_cap["depositado_acum"] = df_cap["total_credit"].cumsum()
                        df_cap["levantado_acum"] = df_cap["total_debit"].cumsum()

                        # Calcular Saldo Atual evolutivo usando SEMPRE preços de hoje para holdings
                        try:
                            from services.coingecko import get_price_by_symbol
                            from datetime import date as date_cls
                            
                            # Buscar todas as transações até o período
                            df_all_tx = pd.read_sql(
                                """
                                SELECT transaction_date::date AS date,
                                       transaction_type,
                                       t.asset_id,
                                       a.symbol,
                                       quantity,
                                       total_eur,
                                       fee_eur
                                FROM t_transactions t
                                JOIN t_assets a ON t.asset_id = a.asset_id
                                WHERE transaction_date::date <= %s
                                ORDER BY transaction_date
                                """,
                                engine,
                                params=(end_date,)
                            )
                            
                            # Buscar todos os movimentos de capital até o período
                            if user_id is None and is_admin:
                                df_all_cap = pd.read_sql(
                                    """
                                    SELECT movement_date::date AS date,
                                           COALESCE(SUM(COALESCE(credit,0)),0) AS credit,
                                           COALESCE(SUM(COALESCE(debit,0)),0) AS debit
                                    FROM t_user_capital_movements tucm
                                    JOIN t_users tu ON tucm.user_id = tu.user_id
                                    WHERE tu.is_admin = FALSE AND movement_date::date <= %s
                                    GROUP BY movement_date::date
                                    ORDER BY movement_date
                                    """,
                                    engine,
                                    params=(end_date,)
                                )
                            elif user_id:
                                df_all_cap = pd.read_sql(
                                    """
                                    SELECT movement_date::date AS date,
                                           COALESCE(credit,0) AS credit,
                                           COALESCE(debit,0) AS debit
                                    FROM t_user_capital_movements
                                    WHERE user_id = %s AND movement_date::date <= %s
                                    ORDER BY movement_date
                                    """,
                                    engine,
                                    params=(user_id, end_date)
                                )
                            else:
                                df_all_cap = pd.DataFrame(columns=["date","credit","debit"])
                            
                            # Buscar preços históricos dos snapshots para cada data de evento
                            unique_symbols = df_all_tx['symbol'].unique().tolist() if not df_all_tx.empty else []
                            
                            # Criar array de datas para calcular evolução
                            # Regra de marcadores: um ponto por cada evento (depósito/levantamento OU compra/venda)
                            # + dia 1 de cada mês no intervalo
                            event_dates = set(df_cap["date"].tolist())
                            if not df_all_tx.empty:
                                event_dates.update(df_all_tx["date"].tolist())
                            
                            # Adicionar dia 1 de cada mês entre start_date e end_date
                            from datetime import datetime as dt_datetime
                            from dateutil.relativedelta import relativedelta
                            
                            current_month = start_date.replace(day=1)
                            while current_month <= end_date:
                                # Adicionar dia 1 se estiver dentro do intervalo
                                if current_month >= start_date:
                                    event_dates.add(current_month)
                                # Próximo mês
                                current_month = current_month + relativedelta(months=1)
                            
                            all_dates = sorted(event_dates)
                            if not all_dates:
                                raise ValueError("Sem datas para calcular evolução")
                            
                            # PRÉ-FETCH: Buscar TODOS os preços históricos de UMA VEZ para evitar rate limit
                            from services.snapshots import get_historical_prices_by_symbol
                            
                            # Criar cache de preços: {date: {symbol: price}}
                            prices_cache = {}
                            if unique_symbols:
                                # Mostrar progresso
                                total_dates = len(all_dates)
                                progress_text = st.empty()
                                progress_bar = st.progress(0.0)
                                info_text = st.empty()
                                
                                # Batch process dates in groups to reduce UI updates
                                # Update UI ~20 times total for optimal responsiveness
                                # (More frequent = slower, less frequent = feels unresponsive)
                                batch_size = max(1, total_dates // 20)
                                
                                for idx, calc_date in enumerate(all_dates):
                                    # Only update UI every batch_size iterations
                                    if idx % batch_size == 0 or idx == total_dates - 1:
                                        progress_text.text(f"🔄 A carregar preços históricos... {idx+1}/{total_dates} datas")
                                        progress_bar.progress((idx + 1) / total_dates)
                                    
                                    prices = get_historical_prices_by_symbol(unique_symbols, calc_date)
                                    prices_cache[calc_date] = prices
                                    
                                    # Informar se buscou da BD ou API (less frequent updates)
                                    if idx % batch_size == 0 and prices:
                                        info_text.text(f"✅ {calc_date}: {len(prices)} preços carregados (BD local + CoinGecko se necessário)")
                                
                                # Limpar mensagens de progresso
                                progress_text.empty()
                                progress_bar.empty()
                                info_text.empty()
                            
                            saldo_evolution = []
                            
                            # Calcular saldo para cada data usando preços DESSA DATA (snapshots)
                            for calc_date in all_dates:
                                # Caixa até esta data
                                cap_until = df_all_cap[df_all_cap["date"] <= calc_date]
                                cash = cap_until["credit"].sum() - cap_until["debit"].sum()
                                
                                tx_until = df_all_tx[df_all_tx["date"] <= calc_date]
                                if not tx_until.empty:
                                    spent = tx_until[tx_until["transaction_type"] == "buy"].apply(
                                        lambda r: r["total_eur"] + r["fee_eur"], axis=1
                                    ).sum()
                                    received = tx_until[tx_until["transaction_type"] == "sell"].apply(
                                        lambda r: r["total_eur"] - r["fee_eur"], axis=1
                                    ).sum()
                                    cash = cash - spent + received
                                
                                # Posições até esta data valoradas com preços DESSA DATA (snapshots)
                                holdings_value = 0.0
                                if not tx_until.empty:
                                    # Use vectorized function to calculate holdings efficiently
                                    holdings = _calculate_holdings_vectorized(tx_until)
                                    
                                    # Usar preços do cache (já buscados)
                                    historical_prices = prices_cache.get(calc_date, {})
                                    
                                    # Valorizar com preços DA DATA calc_date
                                    for sym, qty in holdings.items():
                                        if sym in historical_prices and historical_prices[sym]:
                                            holdings_value += qty * float(historical_prices[sym])
                                
                                saldo_evolution.append(cash + holdings_value)
                            
                            # Alinhar séries acumuladas (depósitos/levantamentos) às datas de eventos (forward-fill)
                            df_dates = pd.DataFrame({"date": pd.to_datetime(all_dates)})
                            df_cap_cum = df_cap[["date","depositado_acum","levantado_acum"]].copy()
                            df_cap_cum["date"] = pd.to_datetime(df_cap_cum["date"])
                            df_cap_cum = df_cap_cum.sort_values("date")
                            df_dates = df_dates.sort_values("date")
                            
                            df_plot = pd.merge_asof(df_dates, df_cap_cum, on="date", direction="backward")
                            df_plot[["depositado_acum","levantado_acum"]] = df_plot[["depositado_acum","levantado_acum"]].fillna(0)
                            df_plot["saldo_atual"] = saldo_evolution

                            saldo_atual_fundo = saldo_evolution[-1] if saldo_evolution else 0.0
                            
                            # Totais para métricas
                            total_credit = df_all_cap["credit"].sum()
                            total_debit = df_all_cap["debit"].sum()
                            
                        except Exception as e:
                            st.warning(f"⚠️ Não foi possível calcular evolução do saldo: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                            # Criar df_plot vazio para evitar UnboundLocalError
                            df_plot = df_cap[["date"]].copy()
                            df_plot["depositado_acum"] = df_cap.get("depositado_acum", 0.0)
                            df_plot["levantado_acum"] = df_cap.get("levantado_acum", 0.0)
                            df_plot["saldo_atual"] = 0.0
                            saldo_atual_fundo = None
                            total_credit = 0.0
                            total_debit = 0.0

                        fig_portfolio = go.Figure()
                        fig_portfolio.add_trace(go.Scatter(
                            x=df_plot["date"],
                            y=df_plot["depositado_acum"],
                            mode='lines+markers',
                            name='Total Depositado',
                            line=dict(color='#3b82f6', width=3),
                            marker=dict(size=6)
                        ))
                        fig_portfolio.add_trace(go.Scatter(
                            x=df_plot["date"],
                            y=df_plot["levantado_acum"],
                            mode='lines+markers',
                            name='Total Levantado',
                            line=dict(color='#ef4444', width=3),
                            marker=dict(size=6)
                        ))
                        # Linha do Saldo Atual (evolutiva)
                        if len(df_plot) > 0:
                            fig_portfolio.add_trace(go.Scatter(
                                x=df_plot["date"],
                                y=df_plot["saldo_atual"],
                                mode='lines+markers',
                                name='Saldo Atual',
                                line=dict(color='#10b981', width=4),
                                marker=dict(size=8)
                            ))

                        fig_portfolio.update_layout(
                            title='Evolução do Portfólio',
                            xaxis_title='Data',
                            yaxis_title='EUR',
                            legend=dict(x=0, y=1),
                            hovermode='x unified'
                        )
                        fig_portfolio = apply_theme(fig_portfolio)
                        st.plotly_chart(fig_portfolio, use_container_width=True)

                # Calcular SALDO ATUAL com preços de HOJE (para as métricas)
                try:
                    if 'total_credit' in locals() and 'total_debit' in locals():
                        # Buscar preços de HOJE
                        unique_symbols_today = df_all_tx['symbol'].unique().tolist() if 'df_all_tx' in locals() and not df_all_tx.empty else []
                        today_prices = {}
                        if unique_symbols_today:
                            today_prices = get_price_by_symbol(unique_symbols_today, vs_currency='eur')
                        
                        # Calcular caixa disponível
                        cash_balance = total_credit - total_debit
                        if 'df_all_tx' in locals() and not df_all_tx.empty:
                            spent_total = df_all_tx[df_all_tx["transaction_type"] == "buy"].apply(
                                lambda r: r["total_eur"] + r["fee_eur"], axis=1
                            ).sum()
                            received_total = df_all_tx[df_all_tx["transaction_type"] == "sell"].apply(
                                lambda r: r["total_eur"] - r["fee_eur"], axis=1
                            ).sum()
                            cash_balance = cash_balance - spent_total + received_total
                        
                        # Calcular holdings com preços de HOJE
                        crypto_holdings = []
                        if 'df_all_tx' in locals() and not df_all_tx.empty:
                            # Use vectorized function to calculate holdings efficiently
                            holdings_by_symbol = _calculate_holdings_vectorized(df_all_tx)
                            
                            for sym, qty in holdings_by_symbol.items():
                                price_today = today_prices.get(sym, 0)
                                if price_today:
                                    value_eur = qty * float(price_today)
                                    crypto_holdings.append({
                                        "Ativo": sym,
                                        "Quantidade": qty,
                                        "Preço Atual (€)": float(price_today),
                                        "Valor Total (€)": value_eur
                                    })
                        
                        # SALDO ATUAL REAL = caixa + cripto a preços de HOJE
                        crypto_value_today = sum([h["Valor Total (€)"] for h in crypto_holdings])
                        saldo_atual_real = cash_balance + crypto_value_today
                        
                except Exception as e:
                    saldo_atual_real = None
                    cash_balance = 0
                    crypto_holdings = []
                    crypto_value_today = 0

                # Mostrar métricas resumo
                try:
                    if 'total_credit' in locals() and 'total_debit' in locals():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💰 Saldo Atual (Fundo)", f"{saldo_atual_real:,.2f} €" if saldo_atual_real is not None else "N/A")
                        with col2:
                            st.metric("📈 Total Depositado", f"{total_credit:,.2f} €")
                        with col3:
                            st.metric("📉 Total Levantado", f"{total_debit:,.2f} €")
                        
                        st.divider()
                        
                        # Holdings detalhados do fundo (já calculados acima)
                        st.markdown("### 💼 Composição do Portfólio")
                        
                        # Métricas de caixa e cripto
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("💶 Caixa (EUR)", f"€{cash_balance:,.2f}")
                        with col2:
                            st.metric("🪙 Valor em Cripto", f"€{crypto_value_today:,.2f}")
                        
                        # Tabela de holdings cripto
                        if crypto_holdings:
                            df_holdings = pd.DataFrame(crypto_holdings)
                            df_holdings["% do Portfólio"] = (df_holdings["Valor Total (€)"] / saldo_atual_real * 100).round(2)
                            
                            st.dataframe(
                                df_holdings,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Quantidade": st.column_config.NumberColumn(format="%.6f"),
                                    "Preço Atual (€)": st.column_config.NumberColumn(format="€%.4f"),
                                    "Valor Total (€)": st.column_config.NumberColumn(format="€%.2f"),
                                    "% do Portfólio": st.column_config.NumberColumn(format="%.2f%%")
                                }
                            )
                        else:
                            st.info("📭 Nenhum ativo em carteira no momento.")
                        
                except Exception as e:
                    st.warning(f"Não foi possível apresentar métricas: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Seção de Top Holders (sempre visível para admin, independente da vista)
        if is_admin:
            st.markdown("---")
            st.markdown("### 🏆 Top Holders da Comunidade")
            
            # Verificar se a tabela t_user_shares existe
            try:
                check_shares_table = pd.read_sql(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 't_user_shares'
                    );
                    """,
                    engine
                )
                shares_table_exists = check_shares_table.iloc[0, 0]
            except:
                shares_table_exists = False
            
            if shares_table_exists:
                # Usar sistema de shares (NAV-based ownership)
                from services.shares import get_all_users_ownership, calculate_nav_per_share, get_total_shares_in_circulation, calculate_fund_nav
                
                try:
                    ownership_data = get_all_users_ownership()
                    
                    if ownership_data:
                        # Criar dataframe com informação de ownership
                        df_top = pd.DataFrame(ownership_data)
                        df_top = df_top.rename(columns={
                            'username': 'Utilizador',
                            'shares': 'Shares',
                            'ownership_pct': 'Propriedade (%)',
                            'value_eur': 'Valor (€)'
                        })
                        
                        # Ordenar por percentagem de propriedade
                        df_top = df_top.sort_values('Propriedade (%)', ascending=False)
                        
                        # Adiciona medalhas
                        num_rows = len(df_top)
                        medals = ["🥇", "🥈", "🥉"][:num_rows] + [""] * max(0, num_rows - 3)
                        df_top.insert(0, "🏅", medals)
                        
                        # Mostra métricas do fundo
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nav_per_share = calculate_nav_per_share()
                            st.metric("📊 NAV por Share", f"€{nav_per_share:.4f}")
                        with col2:
                            total_shares = get_total_shares_in_circulation()
                            st.metric("🔢 Total Shares", f"{total_shares:.2f}")
                        with col3:
                            # Mostrar NAV total do fundo calculado diretamente (caixa + cripto)
                            fund_total = calculate_fund_nav()
                            st.metric("💰 NAV Total Fundo", f"€{fund_total:,.2f}")
                        
                        # Mostra tabela
                        st.dataframe(
                            df_top[['🏅', 'Utilizador', 'Shares', 'Propriedade (%)', 'Valor (€)']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'Shares': st.column_config.NumberColumn(format="%.2f"),
                                'Propriedade (%)': st.column_config.NumberColumn(format="%.2f%%"),
                                'Valor (€)': st.column_config.NumberColumn(format="€%.2f")
                            }
                        )
                        
                        # Gráfico de pizza com % de shares
                        if len(df_top) > 1:
                            fig_pie = px.pie(
                                df_top,
                                names='Utilizador',
                                values='Propriedade (%)',
                                title='Distribuição de Propriedade do Fundo (%)',
                                hover_data=['Valor (€)'],
                            )
                            fig_pie.update_traces(
                                textposition='inside',
                                textinfo='percent+label',
                                hovertemplate='<b>%{label}</b><br>Propriedade: %{value:.2f}%<br>Valor: €%{customdata[0]:,.2f}<extra></extra>',
                                marker=dict(line=dict(color='rgba(0, 0, 0, 0.5)', width=2)),
                                pull=[0.05] * len(df_top),
                                hole=0.3
                            )
                            fig_pie = apply_theme(fig_pie)
                            st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("ℹ️ Ainda não há utilizadores com shares no fundo.")
                        
                except Exception as e:
                    st.warning(f"⚠️ Erro ao obter dados de shares: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            else:
                # Fallback para sistema antigo (depósitos brutos)
                st.info("⚠️ Sistema de shares não está configurado. A mostrar depósitos brutos.")
                df_top = pd.read_sql("""
                    SELECT 
                        tu.username AS "Utilizador",
                        COALESCE(SUM(COALESCE(tucm.credit, 0) - COALESCE(tucm.debit, 0)), 0) AS "Saldo Total (€)"
                    FROM t_users tu
                    LEFT JOIN t_user_capital_movements tucm ON tu.user_id = tucm.user_id
                    WHERE tu.is_admin = FALSE
                    GROUP BY tu.user_id, tu.username
                    HAVING COALESCE(SUM(COALESCE(tucm.credit, 0) - COALESCE(tucm.debit, 0)), 0) > 0
                    ORDER BY "Saldo Total (€)" DESC
                    LIMIT 10
                """, engine)
                
                if not df_top.empty:
                    num_rows = len(df_top)
                    medals = ["🥇", "🥈", "🥉"][:num_rows] + [""] * max(0, num_rows - 3)
                    df_top.insert(0, "🏅", medals)
                    st.dataframe(df_top, use_container_width=True)
                    
                    if len(df_top) > 1:
                        fig_pie = px.pie(
                            df_top,
                            names='Utilizador',
                            values='Saldo Total (€)',
                            title='Distribuição de Capital por Utilizador'
                        )
                        fig_pie.update_traces(
                            textposition='inside',
                            textinfo='percent+label',
                            marker=dict(line=dict(color='rgba(0, 0, 0, 0.5)', width=2)),
                            pull=[0.05] * len(df_top),
                            hole=0.3
                        )
                        fig_pie = apply_theme(fig_pie)
                        st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("ℹ️ Ainda não há dados suficientes para o ranking.")
        
    finally:
        if conn:
            return_connection(conn)
