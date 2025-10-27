import streamlit as st
from database.users import create_user, get_user_by_username

def show_register_page():
    st.title("📝 Criar Conta")

    username = st.text_input("Escolhe um username")
    password = st.text_input("Escolhe uma password", type="password")
    confirm_password = st.text_input("Confirma a password", type="password")

    if st.button("Registar"):
        if password != confirm_password:
            st.error("As passwords não coincidem")
        elif get_user_by_username(username):
            st.error("Este username já existe")
        else:
            user_id = create_user(username, password)
            st.success("Conta criada com sucesso! Agora podes fazer login.")
            st.session_state["user_id"] = user_id
            st.session_state["username"] = username
            st.session_state["is_admin"] = False
            st.rerun()
