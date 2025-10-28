import streamlit as st
from auth.login import show_login_page
from auth.register import show_register_page
from pages.portfolio import show_portfolio_page
from pages.settings import show_settings_page
from pages.prices import show as show_prices_page
from pages.snapshots import show as show_snapshots_page
from pages.documents import show as show_documents_page

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

    # Menu comum para todos os usuários
    menu_options = [
        "📈 Portfólio",
        "💰 Cotações",
        "📸 Snapshots",
        "📄 Documentos",
    ]
    
    # Opções adicionais para admins
    if is_admin:
        menu_options.insert(-1, "⚙️ Configurações")
    
    menu_options.append("🚪 Sair")
    
    menu = st.sidebar.radio("Navegação", menu_options)

    if menu == "📈 Portfólio":
        show_portfolio_page()
    elif menu == "💰 Cotações":
        show_prices_page()
    elif menu == "📸 Snapshots":
        show_snapshots_page()
    elif menu == "📄 Documentos":
        show_documents_page()
    elif menu == "⚙️ Configurações" and is_admin:
        show_settings_page()
    elif menu == "🚪 Sair":
        st.session_state.clear()
        st.session_state["page"] = "login"
        st.rerun()

if __name__ == "__main__":
    main()
