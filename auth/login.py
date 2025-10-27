import streamlit as st
from database.users import authenticate_user

def show_login_page():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Entrar"):
        user = authenticate_user(username, password)
        if user:
            st.session_state["user_id"] = user["user_id"]
            st.session_state["username"] = user["username"]
            st.session_state["is_admin"] = user["is_admin"]
            st.success(f"Bem-vindo {user['username']}!")
            st.rerun()
        else:
            st.error("Username ou password incorretos")
