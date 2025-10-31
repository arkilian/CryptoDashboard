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
                
                # Gráfico de evolução do portfólio (simulado - para implementar com dados reais)
                st.markdown("### 📊 Evolução do Portfólio")
                st.info("ℹ️ Gráfico simulado - implementar integração com snapshots reais")
                
                # Dados simulados baseados no saldo atual
                import numpy as np
                saldo_atual = df_filtered['balance'].iloc[-1]
                periods = min(6, len(df_filtered))
                
                if periods > 0:
                    dates_sim = pd.date_range(start=start_date, end=end_date, periods=periods)
                    valor_investido = np.linspace(0, saldo_atual, periods)
                    # Simular valorização de 5-15%
                    variacao = np.random.uniform(1.05, 1.15, periods)
                    valor_atual = valor_investido * np.cumprod(variacao) / np.cumprod(variacao)[0]
                    
                    df_portfolio = pd.DataFrame({
                        "data": dates_sim.to_numpy(),  # Converter para numpy array
                        "valor_investido": valor_investido,
                        "valor_atual": valor_atual
                    })
                    
                    # Gráfico com duas linhas
                    fig_portfolio = go.Figure()
                    
                    fig_portfolio.add_trace(go.Scatter(
                        x=df_portfolio["data"],
                        y=df_portfolio["valor_investido"],
                        mode='lines+markers',
                        name='Total Investido',
                        line=dict(color='blue')
                    ))
                    
                    fig_portfolio.add_trace(go.Scatter(
                        x=df_portfolio["data"],
                        y=df_portfolio["valor_atual"],
                        mode='lines+markers',
                        name='Valor Atual',
                        line=dict(color='green')
                    ))
                    
                    fig_portfolio.update_layout(
                        title='Evolução do Portfólio (Simulado)',
                        xaxis_title='Data',
                        yaxis_title='EUR',
                        legend=dict(x=0, y=1),
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_portfolio, use_container_width=True)
        
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
