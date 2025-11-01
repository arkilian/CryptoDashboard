import streamlit as st
from database.users import authenticate_user

def show_login_page():
    # Centralizar conteúdo
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='background: linear-gradient(90deg, #60a5fa, #a78bfa);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       background-clip: text;
                       font-size: 3rem;
                       margin-bottom: 0.5rem;'>
                🔐 Crypto Dashboard
            </h1>
            <p style='color: #94a3b8; font-size: 1.1rem;'>Inicia sessão para aceder à tua carteira</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        username = st.text_input("👤 Username", placeholder="Insere o teu username", key="login_username")
        password = st.text_input("🔐 Password", type="password", placeholder="Insere a tua password", key="login_password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Entrar", type="primary", use_container_width=True, key="login_submit"):
            user = authenticate_user(username, password)
            if user:
                st.session_state["user_id"] = user["user_id"]
                st.session_state["username"] = user["username"]
                st.session_state["is_admin"] = user["is_admin"]
                st.session_state["page"] = "portfolio"
                st.success(f"✅ Bem-vindo {user['username']}!")
                st.rerun()
            else:
                st.error("❌ Username ou password incorretos")
