import streamlit as st
from auth.login import show_login_page
from auth.register import show_register_page
from pages.portfolio import show_portfolio_page
from pages.settings import show_settings_page

def main():
    st.set_page_config(page_title="Crypto Dashboard", page_icon="🔒", layout="wide")

    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    # Navegação de páginas de autenticação
    page = st.session_state["page"]

    if page == "login":
        show_login_page()
        if st.button("Não tens conta? Criar nova conta", key="btn_to_register"):
            st.session_state.page = "register"
            st.rerun()
        return

    if page == "register":
        show_register_page()
        if st.button("Já tens conta? Fazer login", key="btn_to_login"):
            st.session_state.page = "login"
            st.rerun()
        return

    # Paginas protegidas
    if "user_id" not in st.session_state or st.session_state["user_id"] is None:
        st.session_state["page"] = "login"
        st.rerun()
        return
    
    # Se está aqui, usuário autenticado
    #st.write(st.session_state)
    st.sidebar.title(f"👤 {st.session_state['username']}")
    is_admin = st.session_state.get("is_admin", False)

    if is_admin:
        menu = st.sidebar.radio("Navegação", ["Portfólio", "Configurações de Taxas", "Sair"])
    else:
        menu = st.sidebar.radio("Navegação", ["Portfólio", "Histórico de Taxas", "Sair"])

    if menu == "Portfólio":
        show_portfolio_page()
    elif menu in ["Configurações de Taxas", "Histórico de Taxas"]:
        show_settings_page()
    elif menu == "Sair":
        st.session_state.clear()
        st.session_state["page"] = "login"
        st.rerun()

if __name__ == "__main__":
    main()
