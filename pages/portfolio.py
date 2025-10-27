import streamlit as st
import pandas as pd
from datetime import date
from database.portfolio import insert_snapshot_and_fees

def show_portfolio_page():
    # Usa a flag is_admin em vez de comparar user_id == 1
    if st.session_state.get("is_admin", True):  # admin
        st.title("📸 Snapshot Manual (Modo Portfólio)")

        snapshot_date = st.date_input("Data do snapshot", date.today())

        st.markdown("### Inserir Ativos do Portfólio")
        df_assets = st.data_editor(
            pd.DataFrame({
                "asset_symbol": ["ADA", "DJED"],
                "quantity": [0.0, 0.0],
                "price": [0.0, 0.0],
            }),
            num_rows="dynamic"
        )
        df_assets["valor_total"] = df_assets["quantity"] * df_assets["price"]
        st.dataframe(df_assets)

        total = df_assets['valor_total'].sum()
        st.markdown(f"### Total do Portfólio: `{total:.2f} €`")

        if st.button("Criar Snapshot e Aplicar Taxas"):
            # usa o user_id do admin em sessão para registar ação
            admin_id = st.session_state.get("user_id")
            insert_snapshot_and_fees(user_id=admin_id, snapshot_date=snapshot_date, df_assets=df_assets)
            st.success("Snapshot e taxas aplicadas com sucesso!")
