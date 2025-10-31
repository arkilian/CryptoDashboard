import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
from database.connection import get_connection, return_connection, get_engine
from auth.session_manager import require_auth


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
            df_users = pd.read_sql(
                "SELECT tu.user_id, tu.username, tup.email FROM t_users tu LEFT JOIN t_user_profile tup ON tu.user_id = tup.user_id ORDER BY tu.user_id",
                engine
            )
            
            # Adicionar opção "Todos (Fundo Comunitário)" no início
            opcoes = ["💰 Todos (Fundo Comunitário)"]
            opcoes += [f"{row['username']} ({row['email'] or 'sem email'})" for _, row in df_users.iterrows()]
            
            # Selectbox com pesquisa
            selecionado = st.selectbox("🔍 Escolhe uma vista", opcoes)
            
            # Determinar se é vista agregada ou utilizador específico
            if selecionado == "💰 Todos (Fundo Comunitário)":
                user_id = None  # None = todos os utilizadores
                user_name = "Fundo Comunitário"
            else:
                # Encontrar ID do utilizador selecionado
                user_id = None
                user_name = None
                for idx, row in df_users.iterrows():
                    if selecionado == f"{row['username']} ({row['email'] or 'sem email'})":
                        user_id = row['user_id']
                        user_name = row['username']
                        break
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
                # Gráfico de evolução do saldo
                fig_balance = px.line(
                    df_filtered,
                    x="date",
                    y="balance",
                    title="📈 Evolução do Saldo",
                    labels={"date": "Data", "balance": "Saldo (€)"}
                )
                fig_balance.update_traces(line_color='#00cc96')
                st.plotly_chart(fig_balance, use_container_width=True)
                
                # Métricas resumo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Saldo Atual", f"{df_filtered['balance'].iloc[-1]:.2f} €")
                with col2:
                    total_credits = df_filtered[df_filtered['net_movement'] > 0]['net_movement'].sum()
                    st.metric("📈 Total Depositado", f"{total_credits:.2f} €")
                with col3:
                    total_debits = abs(df_filtered[df_filtered['net_movement'] < 0]['net_movement'].sum())
                    st.metric("📉 Total Levantado", f"{total_debits:.2f} €")
                
                st.markdown("---")
                
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

                        # Calcular Saldo Atual evolutivo (caixa + valor de mercado das posições ao longo do tempo)
                        try:
                            from services.snapshots import get_historical_prices_bulk
                            
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
                            
                            # Criar array de datas para calcular evolução
                            all_dates = sorted(set(df_cap["date"].tolist()))
                            if not all_dates:
                                raise ValueError("Sem datas para calcular evolução")
                            
                            saldo_evolution = []
                            
                            # Calcular saldo para cada data
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
                                
                                # Posições até esta data
                                holdings_value = 0.0
                                if not tx_until.empty:
                                    holdings = {}
                                    for _, row in tx_until.iterrows():
                                        asset_id = int(row["asset_id"])
                                        qty = row["quantity"]
                                        if row["transaction_type"] == "buy":
                                            holdings[asset_id] = holdings.get(asset_id, 0.0) + qty
                                        else:
                                            holdings[asset_id] = holdings.get(asset_id, 0.0) - qty
                                    
                                    # Buscar preços históricos para esta data
                                    assets_held = [aid for aid, q in holdings.items() if q > 0]
                                    if assets_held:
                                        prices_dict = get_historical_prices_bulk(assets_held, calc_date)
                                        for aid, qty in holdings.items():
                                            if qty > 0 and aid in prices_dict:
                                                holdings_value += qty * prices_dict[aid]
                                
                                saldo_evolution.append(cash + holdings_value)
                            
                            df_cap["saldo_atual"] = saldo_evolution
                            saldo_atual_fundo = saldo_evolution[-1] if saldo_evolution else 0.0
                            
                            # Totais para métricas
                            total_credit = df_all_cap["credit"].sum()
                            total_debit = df_all_cap["debit"].sum()
                            
                        except Exception as e:
                            st.warning(f"⚠️ Não foi possível calcular evolução do saldo: {e}")
                            df_cap["saldo_atual"] = 0.0
                            saldo_atual_fundo = None
                            total_credit = 0.0
                            total_debit = 0.0

                        fig_portfolio = go.Figure()
                        fig_portfolio.add_trace(go.Scatter(
                            x=df_cap["date"],
                            y=df_cap["depositado_acum"],
                            mode='lines+markers',
                            name='Total Depositado',
                            line=dict(color='blue')
                        ))
                        fig_portfolio.add_trace(go.Scatter(
                            x=df_cap["date"],
                            y=df_cap["levantado_acum"],
                            mode='lines+markers',
                            name='Total Levantado',
                            line=dict(color='red')
                        ))
                        # Linha do Saldo Atual (evolutiva)
                        if "saldo_atual" in df_cap.columns and len(df_cap) > 0:
                            fig_portfolio.add_trace(go.Scatter(
                                x=df_cap["date"],
                                y=df_cap["saldo_atual"],
                                mode='lines+markers',
                                name='Saldo Atual',
                                line=dict(color='green', width=3)
                            ))

                        fig_portfolio.update_layout(
                            title='Evolução do Portfólio',
                            xaxis_title='Data',
                            yaxis_title='EUR',
                            legend=dict(x=0, y=1),
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig_portfolio, use_container_width=True)

                # Mostrar métricas resumo com valores calculados
                try:
                    if 'saldo_atual_fundo' in locals() and saldo_atual_fundo is not None:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💰 Saldo Atual (Fundo)", f"{saldo_atual_fundo:,.2f} €")
                        with col2:
                            st.metric("📈 Total Depositado", f"{total_credit:,.2f} €")
                        with col3:
                            st.metric("📉 Total Levantado", f"{total_debit:,.2f} €")
                except Exception as e:
                    st.warning(f"Não foi possível apresentar métricas: {e}")
        
        # Seção de Top Holders (sempre visível para admin, independente da vista)
        if is_admin:
            st.markdown("---")
            st.markdown("### 🏆 Top Holders da Comunidade")
            
            # Buscar top holders reais
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
                # Adiciona medalhas (ajusta para o número real de linhas)
                num_rows = len(df_top)
                medals = ["🥇", "🥈", "🥉"][:num_rows] + [""] * max(0, num_rows - 3)
                df_top.insert(0, "🏅", medals)
                
                # Mostra tabela
                st.dataframe(df_top, use_container_width=True)
                
                # Gráfico de pizza
                if len(df_top) > 1:
                    fig_pie = px.pie(
                        df_top,
                        names='Utilizador',
                        values='Saldo Total (€)',
                        title='Distribuição de Capital por Utilizador'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("ℹ️ Ainda não há dados suficientes para o ranking.")
        
    finally:
        if conn:
            return_connection(conn)
