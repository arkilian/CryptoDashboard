import streamlit as st
import pandas as pd
from datetime import date
import datetime
from database.connection import get_connection, return_connection, get_engine
from auth.session_manager import require_auth
from utils.security import hash_password
from config import USERS_CACHE_DURATION, GENDER_CACHE_DURATION


def _get_users_list_cached():
    """Get users list with caching to avoid redundant database queries."""
    cache_key = "users_list_cache"
    cache_time_key = "users_list_cache_time"
    
    import time
    current_time = time.time()
    
    # Check if cache is valid
    if (cache_key in st.session_state and 
        cache_time_key in st.session_state and
        current_time - st.session_state[cache_time_key] < USERS_CACHE_DURATION):
        return st.session_state[cache_key]
    
    # Fetch from database
    engine = get_engine()
    df_users = pd.read_sql("""
        SELECT tu.user_id, tu.username, tup.email
        FROM t_users tu
        LEFT JOIN t_user_profile tup ON tup.user_id = tu.user_id
        ORDER BY tu.user_id
    """, engine)
    
    # Cache the result
    st.session_state[cache_key] = df_users
    st.session_state[cache_time_key] = current_time
    
    return df_users


def _get_gender_list_cached():
    """Get gender list with caching to avoid redundant database queries."""
    cache_key = "gender_list_cache"
    
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # Fetch from database
    engine = get_engine()
    df_gender = pd.read_sql("SELECT gender_id, gender_name FROM t_gender ORDER BY gender_name", engine)
    
    # Cache the result (gender list is static)
    st.session_state[cache_key] = df_gender
    
    return df_gender


def _create_user_selector(df_users, label="🔍 Escolhe um utilizador"):
    """Create a user selector with efficient lookup.
    
    Returns: (selected_option, user_id)
    """
    # Create efficient lookup dict
    user_lookup = {}
    opcoes = []
    for _, row in df_users.iterrows():
        option = f"{row['username']} ({row['email'] or 'sem email'})"
        opcoes.append(option)
        user_lookup[option] = row['user_id']
    
    # Selectbox
    selecionado = st.selectbox(label, opcoes)
    user_id = user_lookup.get(selecionado)
    
    return selecionado, user_id


@require_auth
def show():
    """
    Página de gestão de utilizadores (admin only).
    Adaptado do ficheiro 2000.py - menu "👤 Utilizadores"
    """
    # Verificar se é admin
    if not st.session_state.get("is_admin", False):
        st.error("⛔ Acesso negado. Esta página é apenas para administradores.")
        return

    st.title("👤 Gestão de Utilizadores")
    
    conn = None
    cursor = None
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Inicializar submenu no session_state se não existir
        if "users_submenu" not in st.session_state:
            st.session_state["users_submenu"] = "📋 Ver Utilizadores"
        
        # Submenu com valor do session_state
        submenu = st.sidebar.radio(
            "Ações de Utilizador",
            ["📋 Ver Utilizadores", "✏️ Modificar Utilizador", "➕ Adicionar Utilizador", "💰 Dados Financeiros"],
            index=["📋 Ver Utilizadores", "✏️ Modificar Utilizador", "➕ Adicionar Utilizador", "💰 Dados Financeiros"].index(st.session_state["users_submenu"])
        )
        
        # Atualizar session_state com a seleção atual
        st.session_state["users_submenu"] = submenu

        if submenu == "📋 Ver Utilizadores":
            _show_users_list(conn)
        elif submenu == "✏️ Modificar Utilizador":
            _modify_user(conn, cursor)
        elif submenu == "➕ Adicionar Utilizador":
            _add_user(conn, cursor)
        elif submenu == "💰 Dados Financeiros":
            _financial_data(conn, cursor)
    finally:
        if cursor:
            cursor.close()
        if conn:
            # Devolve a ligação ao pool em vez de a fechar
            return_connection(conn)


def _show_users_list(conn):
    """Exibir lista de utilizadores"""
    st.subheader("📋 Lista de Utilizadores")
    
    engine = get_engine()
    df = pd.read_sql("""
        SELECT tu.username, tup.email, tup.first_name, tup.last_name
        FROM t_users tu 
        LEFT JOIN t_user_profile tup ON tup.user_id = tu.user_id
        ORDER BY tu.user_id
    """, engine)
    
    st.dataframe(df, use_container_width=True)


def _modify_user(conn, cursor):
    """Modificar dados de utilizador"""
    st.subheader("✏️ Modificar Utilizador")
    
    # Use cached users list
    df_users = _get_users_list_cached()
    selecionado, user_id = _create_user_selector(df_users, "🔍 Escolhe um utilizador para editar")

    if user_id:
        cursor.execute("SELECT username FROM t_users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            st.error("Utilizador não encontrado.")
            return
        username_atual = result[0]

        cursor.execute("""
            SELECT up.email, up.first_name, up.last_name, up.birth_date, g.gender_name,
                a.street, a.city, a.postal_code, a.country
            FROM t_user_profile up
            LEFT JOIN t_gender g ON up.gender_id = g.gender_id
            LEFT JOIN t_address a ON up.address_id = a.address_id
            WHERE up.user_id = %s
        """, (user_id,))
        perfil = cursor.fetchone()
        email, first_name, last_name, birth_date, gender_name, street, city, postal_code, country = (
            perfil or (None, None, None, None, None, None, None, None, None)
        )

        st.markdown("---")
        st.subheader("📝 Editar dados do utilizador")
        novo_username = st.text_input("Username", value=username_atual)
        novo_email = st.text_input("Email", value=email or "")
        
        # Password (opcional - só atualiza se preenchida)
        st.markdown("**🔐 Password** (deixe em branco para manter a atual)")
        nova_password = st.text_input("Nova Password", type="password", key="mod_pass")
        confirma_password = st.text_input("Confirmar Nova Password", type="password", key="mod_pass_conf")
        
        # Validação visual em tempo real
        if nova_password or confirma_password:
            if len(nova_password) < 6:
                st.warning("⚠️ A password deve ter pelo menos 6 caracteres")
            elif nova_password != confirma_password:
                st.error("❌ As passwords não coincidem")
            else:
                st.success("✅ Passwords válidas")

        st.subheader("🧍 Editar perfil")
        novo_first_name = st.text_input("Primeiro nome", value=first_name or "")
        novo_last_name = st.text_input("Último nome", value=last_name or "")
        nova_birth_date = st.date_input(
            "📅 Data de nascimento",
            value=birth_date or datetime.date(2000, 1, 1),
            min_value=datetime.date(1950, 1, 1),
            max_value=datetime.date(date.today().year + 10, 12, 31)
        )

        # Use cached gender list
        df_gender = _get_gender_list_cached()
        genero_opcoes = df_gender["gender_name"].tolist()
        genero_selecionado = st.selectbox(
            "Género",
            genero_opcoes,
            index=genero_opcoes.index(gender_name) if gender_name in genero_opcoes else 0
        )

        st.subheader("🏠 Morada")
        novo_street = st.text_input("Rua", value=street or "")
        novo_city = st.text_input("Cidade", value=city or "")
        novo_postal = st.text_input("Código Postal", value=postal_code or "")
        novo_country = st.text_input("País", value=country or "")

        if st.button("💾 Salvar"):
            # Validar password se foi preenchida
            if nova_password or confirma_password:
                if nova_password != confirma_password:
                    st.error("❌ As passwords não coincidem!")
                    return
                if len(nova_password) < 6:
                    st.error("❌ A password deve ter pelo menos 6 caracteres!")
                    return
            
            try:
                # Atualiza username e password (se fornecida)
                if nova_password:
                    pwd_hash, salt = hash_password(nova_password)
                    cursor.execute(
                        "UPDATE t_users SET username = %s, password_hash = %s, salt = %s WHERE user_id = %s",
                        (novo_username, pwd_hash, salt, user_id)
                    )
                else:
                    # Atualiza apenas o username em t_users (email pertence ao perfil)
                    cursor.execute(
                        "UPDATE t_users SET username = %s WHERE user_id = %s",
                        (novo_username, user_id)
                    )

                # Novo endereço
                cursor.execute("""
                    INSERT INTO t_address (street, city, postal_code, country)
                    VALUES (%s, %s, %s, %s) RETURNING address_id
                """, (novo_street, novo_city, novo_postal, novo_country))
                address_id = cursor.fetchone()[0]

                # Gender
                cursor.execute(
                    "SELECT gender_id FROM t_gender WHERE gender_name = %s",
                    (genero_selecionado,)
                )
                gender_id = cursor.fetchone()[0]

                cursor.execute("""
                    UPDATE t_user_profile
                    SET first_name = %s, last_name = %s, birth_date = %s,
                        gender_id = %s, address_id = %s, email = %s
                    WHERE user_id = %s
                """, (novo_first_name, novo_last_name, nova_birth_date, gender_id, address_id, novo_email, user_id))

                conn.commit()
                st.success("✅ Utilizador atualizado com sucesso!")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Erro ao atualizar: {str(e)}")


def _add_user(conn, cursor):
    """Adicionar novo utilizador"""
    st.subheader("➕ Adicionar Novo Utilizador")

    novo_username = st.text_input("👤 Username")
    novo_email = st.text_input("📧 Email")
    
    # Password obrigatória para novo utilizador
    st.markdown("---")
    st.markdown("**🔐 Password** (obrigatória)")
    nova_password = st.text_input("Password", type="password", key="add_pass")
    confirma_password = st.text_input("Confirmar Password", type="password", key="add_pass_conf")
    
    # Validação visual em tempo real
    if nova_password or confirma_password:
        if not nova_password:
            st.warning("⚠️ A password é obrigatória")
        elif len(nova_password) < 6:
            st.warning("⚠️ A password deve ter pelo menos 6 caracteres")
        elif nova_password != confirma_password:
            st.error("❌ As passwords não coincidem")
        else:
            st.success("✅ Passwords válidas")

    st.markdown("---")
    st.subheader("🧍 Dados de Perfil")
    first_name = st.text_input("Primeiro Nome")
    last_name = st.text_input("Último Nome")
    birth_date = st.date_input(
        "Data de Nascimento",
        min_value=datetime.date(1950, 1, 1),
        max_value=datetime.date(date.today().year + 10, 12, 31)
    )

    # Use cached gender list
    df_gender = _get_gender_list_cached()
    genero_opcoes = df_gender["gender_name"].tolist()
    genero_selecionado = st.selectbox("Género", genero_opcoes)

    st.subheader("🏠 Morada")
    street = st.text_input("Rua")
    city = st.text_input("Cidade")
    postal_code = st.text_input("Código Postal")
    country = st.text_input("País")

    if st.button("➕ Adicionar"):
        # Validar campos obrigatórios
        if not novo_username or not novo_email or not nova_password:
            st.warning("⚠️ Preenche todos os campos obrigatórios (Username, Email e Password).")
            return
        
        # Validar password
        if nova_password != confirma_password:
            st.error("❌ As passwords não coincidem!")
            return
        
        if len(nova_password) < 6:
            st.error("❌ A password deve ter pelo menos 6 caracteres!")
            return
        
        try:
            # Verifica se já existe utilizador com mesmo username ou email
            cursor.execute(
                "SELECT COUNT(*) FROM t_users tu LEFT JOIN t_user_profile tup ON tu.user_id = tup.user_id WHERE tu.username = %s OR tup.email = %s",
                (novo_username, novo_email)
            )
            existe = cursor.fetchone()[0]

            if existe == 0:
                # Hash da password
                pwd_hash, salt = hash_password(nova_password)
                
                # Inserir utilizador com password
                cursor.execute(
                    "INSERT INTO t_users (username, password_hash, salt) VALUES (%s, %s, %s) RETURNING user_id",
                    (novo_username, pwd_hash, salt)
                )
                user_id = cursor.fetchone()[0]

                # Inserir endereço
                cursor.execute("""
                    INSERT INTO t_address (street, city, postal_code, country)
                    VALUES (%s, %s, %s, %s) RETURNING address_id
                """, (street, city, postal_code, country))
                address_id = cursor.fetchone()[0]

                # Obter gender_id
                cursor.execute(
                    "SELECT gender_id FROM t_gender WHERE gender_name = %s",
                    (genero_selecionado,)
                )
                gender_id = cursor.fetchone()[0]

                # Inserir perfil com email
                cursor.execute("""
                    INSERT INTO t_user_profile (user_id, email, first_name, last_name, birth_date, gender_id, address_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, novo_email, first_name, last_name, birth_date, gender_id, address_id))

                conn.commit()
                st.success("✅ Utilizador adicionado com sucesso!")
                # Redirecionar para Ver Utilizadores
                st.session_state["users_submenu"] = "📋 Ver Utilizadores"
                st.rerun()
            else:
                st.warning("⚠️ Já existe um utilizador com esse username ou email.")
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Erro ao adicionar: {str(e)}")


def _financial_data(conn, cursor):
    """Gestão de dados financeiros (movimentos de capital)"""
    st.subheader("💰 Dados Financeiros")

    # Use cached users list
    df_users = _get_users_list_cached()
    selecionado, user_id = _create_user_selector(df_users, "🔍 Escolhe um utilizador")

    # Verifica se o utilizador selecionado é admin (sem IDs hardcoded)
    is_selected_admin = False
    if user_id is not None:
        try:
            cursor.execute("SELECT is_admin FROM t_users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            is_selected_admin = bool(row[0]) if row else False
        except Exception:
            is_selected_admin = False

    if is_selected_admin:
        st.warning("⚠️ Este utilizador é um administrador. Não é permitido editar transações.")
        
        # Mostrar resumo de todos os utilizadores
        st.subheader("💰 Resumo do Fundo Comunitário")
        
        # Calcular totais agregados de todos os utilizadores (exceto admins)
        engine = get_engine()
        df_totals = pd.read_sql("""
            SELECT 
                COUNT(DISTINCT tu.user_id) as total_users,
                COALESCE(SUM(tucm.credit), 0) as total_credits,
                COALESCE(SUM(tucm.debit), 0) as total_debits,
                COALESCE(SUM(tucm.credit) - SUM(tucm.debit), 0) as balance
            FROM t_user_capital_movements tucm
            JOIN t_users tu ON tucm.user_id = tu.user_id
            WHERE tu.is_admin = FALSE
        """, engine)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Utilizadores", int(df_totals['total_users'].iloc[0]))
        with col2:
            st.metric("💰 Total Depósitos", f"{df_totals['total_credits'].iloc[0]:.2f} €")
        with col3:
            st.metric("💸 Total Levantamentos", f"{df_totals['total_debits'].iloc[0]:.2f} €")
        with col4:
            st.metric("📊 Saldo Total", f"{df_totals['balance'].iloc[0]:.2f} €")
        
        # --- Histórico de movimentos agregado ---
        st.subheader("📜 Histórico de Todos os Movimentos")
        engine = get_engine()
        df_mov = pd.read_sql("""
            SELECT tucm.movement_date, tucm.credit, tucm.debit, tucm.description, tu.username
            FROM t_user_capital_movements tucm
            JOIN t_users tu ON tu.user_id = tucm.user_id
            WHERE tu.is_admin = FALSE
            ORDER BY tucm.movement_date DESC
            LIMIT 100
        """, engine)

        st.dataframe(df_mov, use_container_width=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💰 Movimentos de Capital")
        with col2:
            movement_date = st.date_input(
                "📅 Data do movimento",
                value=date.today(),
                min_value=datetime.date(2000, 1, 1),
                max_value=datetime.date(date.today().year + 10, 12, 31)
            )

        # --- Formulário de Depósito ---
        with st.expander("💰 Novo Depósito"):
            valor_dep = st.number_input("Valor a depositar", min_value=0.0, step=0.01, key="dep_val")
            descricao_dep = st.text_input("Descrição do depósito", key="dep_desc")
            if st.button("Confirmar Depósito"):
                try:
                    # Inserir movimento para o user
                    cursor.execute("""
                        INSERT INTO t_user_capital_movements (user_id, credit, description, movement_date) 
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, valor_dep, descricao_dep, movement_date))

                    conn.commit()
                    st.success("✅ Depósito registado com sucesso!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Erro ao registar depósito: {str(e)}")

        # --- Formulário de Levantamento ---
        with st.expander("💸 Novo Levantamento"):
            valor_lev = st.number_input("Valor a levantar", min_value=0.0, step=0.01, key="lev_val")
            descricao_lev = st.text_input("Descrição do levantamento", key="lev_desc")
            if st.button("Confirmar Levantamento"):
                try:
                    # Inserir movimento para o user
                    cursor.execute("""
                        INSERT INTO t_user_capital_movements (user_id, debit, description, movement_date) 
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, valor_lev, descricao_lev, movement_date))

                    conn.commit()
                    st.success("✅ Levantamento registado com sucesso!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Erro ao registar levantamento: {str(e)}")

        # --- Histórico de movimentos ---
        st.subheader("📜 Histórico de Movimentos")
        engine = get_engine()
        df_mov = pd.read_sql("""
            SELECT movement_date, credit, debit, description
            FROM t_user_capital_movements
            WHERE user_id = %s
            ORDER BY movement_date DESC
        """, engine, params=(user_id,))

        st.dataframe(df_mov, use_container_width=True)


# Entry point (compatibilidade com imports)
if __name__ == "__main__":
    show()
