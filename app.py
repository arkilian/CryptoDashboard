import streamlit as st
from auth.login import show_login_page
from auth.register import show_register_page
from pages.portfolio import show_portfolio_page
from pages.portfolio_analysis import show as show_portfolio_analysis_page
from pages.settings import show_settings_page
from pages.prices import show as show_prices_page
from pages.snapshots import show as show_snapshots_page
from pages.documents import show as show_documents_page
from pages.users import show as show_users_page
from pages.transactions import show as show_transactions_page
from css.sidebar import get_sidebar_style
from css.tables import get_tables_style
from css.base import get_app_base_style
from css.forms import get_forms_style

def main():
    st.set_page_config(page_title="Crypto Dashboard", page_icon="🔒", layout="wide")

    # Initialize commonly used session_state keys to avoid AttributeError in pages
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    # Ensure user-related keys exist (may be None)
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False
    if "portfolio_data" not in st.session_state:
        st.session_state["portfolio_data"] = None

    # Navegação de páginas de autenticação
    page = st.session_state["page"]

    # Aplicar estilos também nas páginas de login/registo
    if page in ["login", "register"]:
        st.markdown(get_app_base_style(), unsafe_allow_html=True)
        st.markdown(get_forms_style(), unsafe_allow_html=True)
    
    if page == "login":
        show_login_page()
        
        # Botão para criar conta centralizado
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Não tens conta? Criar nova conta", key="btn_to_register", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        return

    if page == "register":
        show_register_page()
        
        # Botão para voltar ao login centralizado
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Já tens conta? Fazer login", key="btn_to_login", use_container_width=True):
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
    
    # Aplicar CSS global (fundo consistente), sidebar e tabelas
    st.markdown(get_app_base_style(), unsafe_allow_html=True)
    st.markdown(get_sidebar_style(), unsafe_allow_html=True)
    st.markdown(get_tables_style(), unsafe_allow_html=True)
    st.markdown(get_forms_style(), unsafe_allow_html=True)
    
    # Username no topo da sidebar
    st.sidebar.markdown(f"""
    <div class="sidebar-username">
        <h3 style="margin: 0; color: white;">👤 {st.session_state['username']}</h3>
        <p style="margin: 0.3rem 0 0 0; color: rgba(255,255,255,0.7); font-size: 0.85rem;">
            {'🔑 Administrador' if st.session_state.get('is_admin', False) else '👥 Utilizador'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    is_admin = st.session_state.get("is_admin", False)
    
    # Inicializar menu_selection no session_state
    if "menu_selection" not in st.session_state:
        st.session_state["menu_selection"] = "📊 Análise de Portfólio"

    # Menu comum para todos os usuários
    menu_options = [
        "📊 Análise de Portfólio",
        "📈 Portfólio",
        "💰 Cotações",
        "📸 Snapshots",
        "📄 Documentos",
    ]
    
    # Opções adicionais para admins
    if is_admin:
        menu_options.insert(0, "👤 Utilizadores")  # Adiciona no topo
        menu_options.insert(1, "💰 Transações")  # Adiciona depois de Utilizadores
        menu_options.insert(-1, "⚙️ Configurações")
    
    # Criar botões estilizados para cada opção
    for option in menu_options:
        if st.sidebar.button(option, key=f"menu_{option}", use_container_width=True):
            st.session_state["menu_selection"] = option
            st.rerun()
    
    # Botão de sair separado
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", key="menu_logout", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.session_state["page"] = "login"
        st.rerun()
    
    menu = st.session_state["menu_selection"]

    if menu == "👤 Utilizadores" and is_admin:
        show_users_page()
    elif menu == "💰 Transações" and is_admin:
        show_transactions_page()
    elif menu == "📊 Análise de Portfólio":
        show_portfolio_analysis_page()
    elif menu == "📈 Portfólio":
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
