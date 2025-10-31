import streamlit as st
import pandas as pd
from services.fees import get_current_fee_settings, update_fee_settings, get_fee_history
from database.connection import get_engine

def show_settings_page():
    st.title("⚙️ Configurações do Fundo")

    # Verificar se é admin
    if not st.session_state.get("is_admin", False):
        st.error("⛔ Acesso negado. Esta página é exclusiva para administradores.")
        st.stop()

    # Sub-menus
    tab1, tab2, tab3 = st.tabs(["💰 Taxas", "🪙 Ativos", "🏦 Exchanges"])

    # ========================================
    # TAB 1: TAXAS
    # ========================================
    with tab1:
        fees = get_current_fee_settings()

        st.subheader("Taxas Atuais")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Taxa de Manutenção", f"{fees['maintenance_rate']*100:.2f}%")
            st.caption(f"Mínimo: €{fees['maintenance_min']:.2f}")
        with col2:
            st.metric("Taxa de Performance", f"{fees['performance_rate']*100:.2f}%")

        st.divider()

        # Histórico de Taxas
        st.subheader("📜 Histórico de Taxas")
        history = get_fee_history()
        if history:
            df = pd.DataFrame(history)
            df["maintenance_rate"] = (df["maintenance_rate"] * 100).map(lambda x: f"{x:.2f}%")
            df["performance_rate"] = (df["performance_rate"] * 100).map(lambda x: f"{x:.2f}%")
            df["valid_from"] = pd.to_datetime(df["valid_from"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df.rename(columns={
                "maintenance_rate": "Manutenção",
                "maintenance_min": "Min. Manutenção (€)",
                "performance_rate": "Performance",
                "valid_from": "Válido Desde"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não existem configurações de taxas registadas.")

        st.divider()

        # Alteração de taxas
        st.subheader("✏️ Alterar Taxas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_maintenance = st.number_input(
                "Taxa de Manutenção (%)", 
                value=fees['maintenance_rate']*100,
                min_value=0.0,
                max_value=100.0,
                step=0.01
            ) / 100
        
        with col2:
            new_minimum = st.number_input(
                "Mínimo da Taxa de Manutenção (€)", 
                value=fees['maintenance_min'],
                min_value=0.0,
                step=0.50
            )
        
        with col3:
            new_performance = st.number_input(
                "Taxa de Performance (%)", 
                value=fees['performance_rate']*100,
                min_value=0.0,
                max_value=100.0,
                step=0.5
            ) / 100

        if st.button("💾 Atualizar Taxas", type="primary", use_container_width=True):
            update_fee_settings(new_maintenance, new_minimum, new_performance)
            st.success("✅ Nova configuração de taxas aplicada com sucesso!")
            st.rerun()

    # ========================================
    # TAB 2: ATIVOS
    # ========================================
    with tab2:
        engine = get_engine()
        
        st.subheader("🪙 Gestão de Ativos")
        
        # Listar ativos existentes
        df_assets = pd.read_sql("""
            SELECT asset_id, symbol, name, chain, coingecko_id, is_stablecoin
            FROM t_assets
            ORDER BY symbol
        """, engine)
        
        if not df_assets.empty:
            st.dataframe(
                df_assets.rename(columns={
                    "asset_id": "ID",
                    "symbol": "Símbolo",
                    "name": "Nome",
                    "chain": "Blockchain",
                    "coingecko_id": "CoinGecko ID",
                    "is_stablecoin": "Stablecoin"
                }).drop('ID', axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"📊 Total: {len(df_assets)} ativos")
        else:
            st.info("📭 Nenhum ativo registado ainda.")
        
        st.divider()
        
        # Adicionar novo ativo
        st.subheader("➕ Adicionar Novo Ativo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_symbol = st.text_input("Símbolo", placeholder="Ex: BTC, ETH, ADA").upper()
            new_name = st.text_input("Nome", placeholder="Ex: Bitcoin, Ethereum")
            new_coingecko_id = st.text_input(
                "CoinGecko ID", 
                placeholder="Ex: bitcoin, ethereum",
                help="ID do ativo no CoinGecko para cotações automáticas"
            )
        
        with col2:
            new_chain = st.text_input("Blockchain", placeholder="Ex: Bitcoin, Ethereum, Cardano")
            new_is_stablecoin = st.checkbox("É uma stablecoin?")
        
        if st.button("💾 Adicionar Ativo", type="primary", use_container_width=True):
            if not new_symbol:
                st.error("❌ O símbolo é obrigatório!")
            else:
                try:
                    with engine.connect() as conn:
                        conn.execute("""
                            INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (new_symbol, new_name or None, new_chain or None, new_coingecko_id or None, new_is_stablecoin))
                        conn.commit()
                    
                    st.success(f"✅ Ativo {new_symbol} adicionado com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                        st.error(f"❌ O ativo {new_symbol} já existe!")
                    else:
                        st.error(f"❌ Erro ao adicionar ativo: {str(e)}")

    # ========================================
    # TAB 3: EXCHANGES
    # ========================================
    with tab3:
        st.subheader("🏦 Gestão de Exchanges")
        
        # Listar exchanges existentes
        df_exchanges = pd.read_sql("""
            SELECT exchange_id, name, category
            FROM t_exchanges
            ORDER BY name
        """, engine)
        
        if not df_exchanges.empty:
            st.dataframe(
                df_exchanges.rename(columns={
                    "exchange_id": "ID",
                    "name": "Nome",
                    "category": "Categoria"
                }).drop('ID', axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"📊 Total: {len(df_exchanges)} exchanges")
        else:
            st.info("📭 Nenhuma exchange registada ainda.")
        
        st.divider()
        
        # Adicionar nova exchange
        st.subheader("➕ Adicionar Nova Exchange")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_exchange_name = st.text_input("Nome da Exchange", placeholder="Ex: Binance, Kraken")
        
        with col2:
            new_category = st.selectbox(
                "Categoria",
                ["CEX", "Wallet", "DeFi", "Outro"]
            )
        
        if st.button("💾 Adicionar Exchange", type="primary", use_container_width=True):
            if not new_exchange_name:
                st.error("❌ O nome da exchange é obrigatório!")
            else:
                try:
                    with engine.connect() as conn:
                        conn.execute("""
                            INSERT INTO t_exchanges (name, category)
                            VALUES (%s, %s)
                        """, (new_exchange_name, new_category))
                        conn.commit()
                    
                    st.success(f"✅ Exchange {new_exchange_name} adicionada com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao adicionar exchange: {str(e)}")
