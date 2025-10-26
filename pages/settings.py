import streamlit as st
import pandas as pd
from services.fees import get_current_fee_settings, update_fee_settings, get_fee_history

def show_settings_page():
    st.title("⚙️ Configurações do Fundo")

    fees = get_current_fee_settings()

    st.subheader("Taxas Atuais")
    st.write(f"**Manutenção:** {fees['maintenance_rate']*100:.2f}% (mínimo {fees['maintenance_min']}€)")
    st.write(f"**Performance:** {fees['performance_rate']*100:.2f}%")

    # --- Hist�rico de Taxas ---
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
        }))
    else:
        st.info("Ainda não existem configurações de taxas registadas.")

    # --- Alteração (apenas admin) ---
    if st.session_state.get("user_id") == 1:  # admin
        st.subheader("Alterar Taxas")
        new_maintenance = st.number_input("Taxa de Manutenção (%)", value=fees['maintenance_rate']*100) / 100
        new_minimum = st.number_input("Mínimo da Taxa de Manutenção (€)", value=fees['maintenance_min'])
        new_performance = st.number_input("Taxa de Performance (%)", value=fees['performance_rate']*100) / 100

        if st.button("Atualizar Taxas"):
            update_fee_settings(new_maintenance, new_minimum, new_performance)
            st.success("Nova configuração de taxas aplicada com sucesso!")
            st.rerun()
    else:
        st.info("Apenas o administrador pode alterar as taxas.")
