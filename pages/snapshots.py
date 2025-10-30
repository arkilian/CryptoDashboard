import streamlit as st
from datetime import date
import plotly.express as px
from services.snapshot import SnapshotService
from auth.session_manager import require_auth

@require_auth
def show():
    st.title("📸 Snapshot Manual")
    
    # Get current user from session (be defensive if not fully initialised)
    user = st.session_state.get('user')
    if not user:
        # Fallback to minimal user structure if only individual fields exist
        user = {
            'user_id': st.session_state.get('user_id'),
            'user_name': st.session_state.get('username'),
            'is_admin': st.session_state.get('is_admin', False),
        }
    snapshot_service = SnapshotService()

    # Toggle between portfolio mode (future) and manual mode
    modo_portfolio = st.toggle("Modo Portfolio", value=False)

    if modo_portfolio:
        st.warning("⚠️ Work in progress - Integração futura com portfolio.")
    else:
        # Form for new snapshot
        with st.form("novo_snapshot"):
            st.subheader("📝 Novo Snapshot")
            
            # Get latest snapshot for default values
            latest = snapshot_service.get_latest_snapshot(user['user_id'])
            
            col1, col2 = st.columns(2)
            with col1:
                snapshot_date = st.date_input(
                    "📅 Data do snapshot",
                    value=date.today(),
                    min_value=date(2000, 1, 1),
                    max_value=date(date.today().year + 10, 12, 31)
                )
            
            # Use latest values as defaults if available
            binance = st.number_input("💰 Capital na Binance", 
                                    min_value=0.0, 
                                    step=10.0,
                                    value=float(latest['binance_value']) if latest else 0.0)
            
            ledger = st.number_input("🔐 Capital na Ledger", 
                                   min_value=0.0, 
                                   step=10.0,
                                   value=float(latest['ledger_value']) if latest else 0.0)
            
            defi = st.number_input("🌊 Capital em DeFi (Cardano)", 
                                 min_value=0.0, 
                                 step=10.0,
                                 value=float(latest['defi_value']) if latest else 0.0)
            
            outros = st.number_input("💼 Outros", 
                                   min_value=0.0, 
                                   step=10.0,
                                   value=float(latest['other_value']) if latest else 0.0)
            
            total = binance + ledger + defi + outros
            st.markdown(f"### 💼 Total atual: `{total:.2f} €`")

            submitted = st.form_submit_button("✅ Criar Snapshot")
            
            if submitted:
                try:
                    snapshot_service.create_manual_snapshot(
                        user['user_id'],
                        snapshot_date,
                        binance,
                        ledger,
                        defi,
                        outros
                    )
                    st.success("✅ Snapshot criado com sucesso!")
                    st.rerun()  # Refresh page to show new data
                except Exception as e:
                    st.error(f"❌ Erro ao criar snapshot: {str(e)}")

        # Historical view
        st.subheader("📊 Histórico de Snapshots")
        
        # Date filters
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Data inicial",
                value=date(date.today().year, 1, 1),
                min_value=date(2000, 1, 1),
                max_value=date(date.today().year + 10, 12, 31)
            )
        with col2:
            end_date = st.date_input(
                "Data final",
                value=date.today(),
                min_value=date(2000, 1, 1),
                max_value=date(date.today().year + 10, 12, 31)
            )

        # Get snapshots
        snapshots = snapshot_service.get_user_snapshots(
            user['user_id'],
            start_date,
            end_date
        )
        
        if not snapshots:
            st.info("ℹ️ Nenhum snapshot encontrado para o período selecionado.")
        else:
            # Convert to DataFrame for visualization
            import pandas as pd
            df = pd.DataFrame(snapshots, columns=[
                'Data', 'Binance', 'Ledger', 'DeFi', 'Outros', 'Total'
            ])
            
            # Line chart
            fig = px.line(df, x='Data', y='Total',
                         title="Evolução do Capital Total")
            st.plotly_chart(fig)
            
            # Stacked area chart
            fig_stacked = px.area(df, x='Data',
                                y=['Binance', 'Ledger', 'DeFi', 'Outros'],
                                title="Distribuição do Capital")
            st.plotly_chart(fig_stacked)
            
            # Data table
            st.dataframe(df)