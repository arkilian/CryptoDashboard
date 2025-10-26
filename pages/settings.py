import streamlit as st
import pandas as pd
from services.fees import get_current_fee_settings, update_fee_settings, get_fee_history

def show_settings_page():
    st.title("?? Configura��es do Fundo")

    fees = get_current_fee_settings()

    st.subheader("Taxas Atuais")
    st.write(f"**Manuten��o:** {fees['maintenance_rate']*100:.2f}% (m�nimo {fees['maintenance_min']}�)")
    st.write(f"**Performance:** {fees['performance_rate']*100:.2f}%")

    # --- Hist�rico de Taxas ---
    st.subheader("?? Hist�rico de Taxas")
    history = get_fee_history()
    if history:
        df = pd.DataFrame(history)
        df["maintenance_rate"] = (df["maintenance_rate"] * 100).map(lambda x: f"{x:.2f}%")
        df["performance_rate"] = (df["performance_rate"] * 100).map(lambda x: f"{x:.2f}%")
        df["valid_from"] = pd.to_datetime(df["valid_from"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(df.rename(columns={
            "maintenance_rate": "Manuten��o",
            "maintenance_min": "Min. Manuten��o (�)",
            "performance_rate": "Performance",
            "valid_from": "V�lido Desde"
        }))
    else:
        st.info("Ainda n�o existem configura��es de taxas registadas.")

    # --- Altera��o (apenas admin) ---
    if st.session_state.get("user_id") == 1:  # admin
        st.subheader("Alterar Taxas")
        new_maintenance = st.number_input("Taxa de Manuten��o (%)", value=fees['maintenance_rate']*100) / 100
        new_minimum = st.number_input("M�nimo da Taxa de Manuten��o (�)", value=fees['maintenance_min'])
        new_performance = st.number_input("Taxa de Performance (%)", value=fees['performance_rate']*100) / 100

        if st.button("?? Atualizar Taxas"):
            update_fee_settings(new_maintenance, new_minimum, new_performance)
            st.success("Nova configura��o de taxas aplicada com sucesso!")
            st.rerun()
    else:
        st.info("?? Apenas o administrador pode alterar as taxas.")
