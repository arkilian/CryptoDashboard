import streamlit as st
from database.users import create_user, get_user_by_username

def show_register_page():
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
                📝 Criar Conta
            </h1>
            <p style='color: #94a3b8; font-size: 1.1rem;'>Junta-te ao fundo de investimento</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        username = st.text_input("👤 Username", placeholder="Escolhe um username único", key="register_username")
        email = st.text_input("📧 Email", placeholder="O teu melhor email", key="register_email")
        
        st.markdown("---")
        
        password = st.text_input("🔐 Password", type="password", placeholder="Mínimo 6 caracteres", key="register_password")
        confirm_password = st.text_input("🔐 Confirmar Password", type="password", placeholder="Repete a password", key="register_confirm_password")
        
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
        
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Criar Conta", type="primary", use_container_width=True, key="register_submit"):
            if not username or not email or not password or not confirm_password:
                st.error("❌ Todos os campos são obrigatórios")
            elif password != confirm_password:
                st.error("❌ As passwords não coincidem")
            elif len(password) < 6:
                st.error("❌ A password deve ter pelo menos 6 caracteres")
            elif get_user_by_username(username):
                st.error("❌ Este username já existe")
            else:
                user_id = create_user(username, password, email)
                st.success("✅ Conta criada com sucesso! Redirecionar para login...")
                # Limpar qualquer sessão anterior e redirecionar para login
                st.session_state.clear()
                st.session_state["show_register"] = False
                st.rerun()
