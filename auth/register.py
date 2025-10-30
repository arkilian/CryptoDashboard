import streamlit as st
from database.users import create_user, get_user_by_username

def show_register_page():
    st.title("📝 Criar Conta")

    username = st.text_input("👤 Escolhe um username")
    email = st.text_input("📧 Email")
    password = st.text_input("🔐 Escolhe uma password", type="password")
    confirm_password = st.text_input("🔐 Confirma a password", type="password")
    
    # Validação visual em tempo real
    if password or confirm_password:
        if not password:
            st.warning("⚠️ A password é obrigatória")
        elif len(password) < 6:
            st.warning("⚠️ A password deve ter pelo menos 6 caracteres")
        elif password != confirm_password:
            st.error("❌ As passwords não coincidem")
        else:
            st.success("✅ Passwords válidas")

    if st.button("Registar"):
        if not username or not email or not password or not confirm_password:
            st.error("⚠️ Todos os campos são obrigatórios")
        elif get_user_by_username(username):
            st.error("⚠️ Este username já existe")
        else:
            user_id = create_user(username, password, email)
            st.success("✅ Conta criada com sucesso! Redirecionar para login...")
            # Limpar qualquer sessão anterior e redirecionar para login
            st.session_state.clear()
            st.session_state["show_register"] = False
            st.rerun()
