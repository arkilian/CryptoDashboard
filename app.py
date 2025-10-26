import streamlit as st
from auth.login import show_login_page
from auth.register import show_register_page
from pages.portfolio import show_portfolio_page
from pages.settings import show_settings_page

def main():
    st.set_page_config(page_title="Crypto Dashboard", page_icon="??", layout="wide")

    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if "user_id" not in st.session_state:
        if st.session_state["page"] == "login":
            show_login_page()
        elif st.session_state["page"] == "register":
            show_register_page()
        return

    st.sidebar.title(f"?? {st.session_state['username']}")
    is_admin = st.session_state.get("is_admin", False)

    if is_admin:
        menu = st.sidebar.radio("Navega��o", ["Portf�lio", "Configura��es de Taxas", "Sair"])
    else:
        menu = st.sidebar.radio("Navega��o", ["Portf�lio", "Hist�rico de Taxas", "Sair"])

    if menu == "Portf�lio":
        show_portfolio_page()
    elif menu in ["Configura��es de Taxas", "Hist�rico de Taxas"]:
        show_settings_page()
    elif menu == "Sair":
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
