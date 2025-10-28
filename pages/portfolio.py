import streamlit as st
import pandas as pd
from datetime import date
from database.portfolio import insert_snapshot_and_fees
from services.coingecko import get_price_by_symbol

def show_portfolio_page():
    # Usa a flag is_admin em vez de comparar user_id == 1
    if st.session_state.get("is_admin", False):  # admin
        st.title("📸 Snapshot Manual (Modo Portfólio)")

        snapshot_date = st.date_input("Data do snapshot", date.today())

        st.markdown("### Inserir Ativos do Portfólio")
        # Mantém o dataframe no session_state para permitir atualizações entre reruns
        default_df = pd.DataFrame({
            "asset_symbol": ["ADA", "DJED"],
            "quantity": [0.0, 0.0],
            "price": [0.0, 0.0],
        })

        if "portfolio_data" not in st.session_state:
            st.session_state["portfolio_data"] = default_df

        # Data editor - passamos o valor explicitamente como `value` e
        # evitamos usar a mesma chave no session_state como `key` do widget
        # para não violar as regras de atribuição do Streamlit.
        df_assets = st.data_editor(
            value=st.session_state["portfolio_data"],
            num_rows="dynamic",
        )

        # Botão para preencher preços via CoinGecko
        if st.button("Obter preços (CoinGecko)"):
            symbols = [s for s in df_assets["asset_symbol"].astype(str).tolist() if s and str(s).strip()]
            if symbols:
                with st.spinner("A obter preços do CoinGecko..."):
                    try:
                        prices = get_price_by_symbol(symbols, vs_currency="eur")
                    except Exception as e:
                        st.error(f"Erro ao obter preços: {e}")
                        prices = {s: None for s in symbols}

                # Atualiza preços onde estiverem vazios ou zero
                for i, row in df_assets.iterrows():
                    sym = str(row.get("asset_symbol", "")).strip()
                    if not sym:
                        continue
                    price = prices.get(sym)
                    # Só substitui se preço obtido e valor atual for falsy
                    if price is not None and (not row.get("price") or float(row.get("price") or 0) == 0):
                        df_assets.at[i, "price"] = price

                # Guarda o dataframe atualizado na sessão e rerun para refletir na UI
                st.session_state["portfolio_data"] = df_assets
                st.experimental_rerun()

        # Calcula valores após edição/preenchimento
        df_assets["valor_total"] = df_assets["quantity"].astype(float) * df_assets["price"].astype(float)
        st.dataframe(df_assets)

        total = df_assets['valor_total'].sum()
        st.markdown(f"### Total do Portfólio: `{total:.2f} €`")

        if st.button("Criar Snapshot e Aplicar Taxas"):
            # usa o user_id do admin em sessão para registar ação
            admin_id = st.session_state.get("user_id")
            insert_snapshot_and_fees(user_id=admin_id, snapshot_date=snapshot_date, df_assets=df_assets)
            st.success("Snapshot e taxas aplicadas com sucesso!")
