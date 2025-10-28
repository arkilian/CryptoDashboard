import streamlit as st
import streamlit_authenticator as stauth
import psycopg2
import pandas as pd
import bcrypt
import datetime
import binascii
import requests
import time
import plotly.express as px
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import os
from pycoingecko import CoinGeckoAPI
import plotly.graph_objects as go
from datetime import datetime
import streamlit.components.v1 as components
import base64

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="primeira",
    user="postgres",
    password="WFUikk22!"
)
cursor = conn.cursor()
st.set_page_config(page_title="Fundo Comunitario", page_icon="💰")
#https://api.coingecko.com/api/v3/coins/list
# Lista de moedas CoinGecko
coin_ids = [
    "bitcoin",
    "sui",
    "solana",
    "cardano",
    "singularitynet",
    "minswap",
    "indigo-dao-governance-token",
    "liqwid-finance",
    "world-mobile-token",
    "fluidtokens",
    "palm-economy",
    "iagon",
    "optim-finance",
    "talos",
    "genius-yield",
    "dexhunter",
    "nuvola-digital",
    "charli3",
    "metera",
    "aada-finance",
    "djed",
    "iusd"
]

# Transforma a lista em string separada por vírgulas
coin_ids_str = ",".join(coin_ids)

# Exibe o widget da CoinGecko em todas as páginas
html_code = f'''
<script src="https://widgets.coingecko.com/gecko-coin-price-marquee-widget.js"></script>
<gecko-coin-price-marquee-widget 
    locale="en" 
    dark-mode="true" 
    outlined="true" 
    coin-ids="{coin_ids_str}" 
    initial-currency="usd">
</gecko-coin-price-marquee-widget>
'''
# Renderiza o widget
components.html(html_code, height=60)

st.sidebar.title("Menu")
menu = st.sidebar.radio("Escolha uma opção", ["👤 Utilizadores", "📈 Portofolio", "📊 Cotações","📸 Snapshot Manual", "💼 Documentos"])

if menu == "👤 Utilizadores":
    submenu = st.sidebar.radio("Ações", ["📋 Ver Utilizadores", "✏️ Modificar Utilizador", "➕ Adicionar Utilizador", "💰 Dados Financeiros"])

    if submenu == "📋 Ver Utilizadores":
        df = pd.read_sql("""select tu.user_name, tu.email, tup.first_name, tup.last_name
                              from t_users tu 
                              join t_user_profile tup 
                                on tup.user_id = tu.user_id
                             order by tu.user_id""", conn)
        st.title("📋 Lista de Utilizadores")
        st.dataframe(df)
    elif submenu == "✏️ Modificar Utilizador":
        # Obter lista de utilizadores
        df_users = pd.read_sql("select tu.user_id, tu.user_name, tu.email from t_users tu order by tu.user_id", conn)
        opcoes = [f"{row['user_name']} ({row['email']})" for _, row in df_users.iterrows()]

        # Selectbox com pesquisa
        selecionado = st.selectbox("🔍 Escolhe um utilizador para editar", opcoes)

        # Encontrar ID do utilizador selecionado
        user_id = None
        for idx, row in df_users.iterrows():
            if selecionado == f"{row['user_name']} ({row['email']})":
                user_id = row['user_id']
                break

        if user_id:
            cursor.execute("SELECT user_name, email FROM t_users WHERE user_id = %s", (user_id,))
            user_name_atual, email_atual = cursor.fetchone()

            cursor.execute("""
                SELECT up.first_name, up.last_name, up.birth_date, g.gender_name,
                    a.street, a.city, a.postal_code, a.country
                FROM t_user_profile up
                LEFT JOIN t_gender g ON up.gender_id = g.gender_id
                LEFT JOIN t_address a ON up.address_id = a.address_id
                WHERE up.user_id = %s
            """, (user_id,))
            perfil = cursor.fetchone()
            first_name, last_name, birth_date, gender_name, street, city, postal_code, country = perfil or (None, None, None, None, None, None, None, None)

            st.subheader("📝 Editar dados do utilizador")
            novo_user_name = st.text_input("Username", value=user_name_atual)
            novo_email = st.text_input("Email", value=email_atual)

            st.subheader("🧍 Editar perfil")
            novo_first_name = st.text_input("Primeiro nome", value=first_name or "")
            novo_last_name = st.text_input("Último nome", value=last_name or "")
            nova_birth_date = st.date_input("Data de nascimento", value=birth_date or datetime.date(2000, 1, 1))

            df_gender = pd.read_sql("SELECT gender_id, gender_name FROM t_gender ORDER BY gender_name", conn)
            genero_opcoes = df_gender["gender_name"].tolist()
            genero_selecionado = st.selectbox("Género", genero_opcoes, index=genero_opcoes.index(gender_name) if gender_name in genero_opcoes else 0)

            st.subheader("🏠 Morada")
            novo_street = st.text_input("Rua", value=street or "")
            novo_city = st.text_input("Cidade", value=city or "")
            novo_postal = st.text_input("Código Postal", value=postal_code or "")
            novo_country = st.text_input("País", value=country or "")

            if st.button("💾 Salvar"):
                cursor.execute("UPDATE t_users SET user_name = %s, email = %s WHERE user_id = %s",
                            (novo_user_name, novo_email, user_id))

                # Novo endereço
                cursor.execute("""
                    INSERT INTO t_address (street, city, postal_code, country)
                    VALUES (%s, %s, %s, %s) RETURNING address_id
                """, (novo_street, novo_city, novo_postal, novo_country))
                address_id = cursor.fetchone()[0]

                # Gender
                cursor.execute("SELECT gender_id FROM t_gender WHERE gender_name = %s", (genero_selecionado,))
                gender_id = cursor.fetchone()[0]

                cursor.execute("""
                    UPDATE t_user_profile
                    SET first_name = %s, last_name = %s, birth_date = %s,
                        gender_id = %s, address_id = %s
                    WHERE user_id = %s
                """, (novo_first_name, novo_last_name, nova_birth_date, gender_id, address_id, user_id))

                conn.commit()
                st.success("✅ Utilizador atualizado com sucesso!")
                st.rerun()

    elif submenu == "➕ Adicionar Utilizador":
        st.title("➕ Adicionar Novo Utilizador")

        novo_user_name = st.text_input("👤 Username")
        novo_email = st.text_input("📧 Email")

        st.subheader("🧍 Dados de Perfil")
        first_name = st.text_input("Primeiro Nome")
        last_name = st.text_input("Último Nome")
        birth_date = st.date_input("Data de Nascimento")

        df_gender = pd.read_sql("SELECT gender_id, gender_name FROM t_gender ORDER BY gender_name", conn)
        genero_opcoes = df_gender["gender_name"].tolist()
        genero_selecionado = st.selectbox("Género", genero_opcoes)

        st.subheader("🏠 Morada")
        street = st.text_input("Rua")
        city = st.text_input("Cidade")
        postal_code = st.text_input("Código Postal")
        country = st.text_input("País")

        if st.button("➕ Adicionar"):
            if novo_user_name and novo_email:
                # Verifica se já existe utilizador com mesmo username ou email
                cursor.execute("SELECT COUNT(*) FROM t_users WHERE user_name = %s OR email = %s", (novo_user_name, novo_email))
                existe = cursor.fetchone()[0]

                if existe == 0:
                    cursor.execute(
                        "INSERT INTO t_users (user_name, email) VALUES (%s, %s) RETURNING user_id",
                        (novo_user_name, novo_email)
                    )
                    user_id = cursor.fetchone()[0]

                    # Inserir endereço
                    cursor.execute("""
                        INSERT INTO t_address (street, city, postal_code, country)
                        VALUES (%s, %s, %s, %s) RETURNING address_id
                    """, (street, city, postal_code, country))
                    address_id = cursor.fetchone()[0]

                    # Obter gender_id
                    cursor.execute("SELECT gender_id FROM t_gender WHERE gender_name = %s", (genero_selecionado,))
                    gender_id = cursor.fetchone()[0]

                    # Inserir perfil
                    cursor.execute("""
                        INSERT INTO t_user_profile (user_id, first_name, last_name, birth_date, gender_id, address_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user_id, first_name, last_name, birth_date, gender_id, address_id))

                    conn.commit()
                    st.success("✅ Utilizador adicionado com sucesso!")
                    st.rerun()
                else:
                    st.warning("⚠️ Já existe um utilizador com esse username ou email.")
            else:
                st.warning("⚠️ Preenche todos os campos.")
    elif submenu == "💰 Dados Financeiros":
        # Obter lista de utilizadores
        df_users = pd.read_sql("SELECT tu.user_id, tu.user_name, tu.email FROM t_users tu ORDER BY tu.user_id", conn)
        opcoes = [f"{row['user_name']} ({row['email']})" for _, row in df_users.iterrows()]

        # Selectbox com pesquisa
        selecionado = st.selectbox("🔍 Escolhe um utilizador para editar", opcoes)

        # Encontrar ID do utilizador selecionado
        user_id = None
        for idx, row in df_users.iterrows():
            if selecionado == f"{row['user_name']} ({row['email']})":
                user_id = row['user_id']
                break

        if user_id in [1, 2]:
            st.warning("⚠️ Este utilizador é um administrador. Não é permitido editar transações.")
            # --- Histórico de movimentos ---
            st.subheader("📜 Histórico de Movimentos")
            df_mov = pd.read_sql("""
                select tucm.movement_date, tucm.credit, tucm.debit, tucm.description, tu.user_name
                from t_user_capital_movements tucm
                join t_users tu on tu.user_id  = tucm.original_user_id
                where tucm.user_id  = %s
                ORDER BY tucm.movement_date DESC
            """, conn, params=(user_id,))

            st.dataframe(df_mov)
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("💰 Dados Financeiros")
            with col2:
                movement_date = st.date_input("📅 Data do movimento", date.today())
            
            # --- Formulário de Depósito ---
            with st.expander("💰 Novo Depósito"):
                valor_dep = st.number_input("Valor a depositar", min_value=0.0, step=0.01)
                descricao_dep = st.text_input("Descrição do depósito")
                if st.button("Confirmar Depósito"):
                    # Inserir movimento para o user
                    cursor.execute("""
                        INSERT INTO t_user_capital_movements (user_id, credit, description, movement_date) 
                        VALUES (%s, %s, %s, %s) RETURNING movement_id
                    """, (user_id, valor_dep, descricao_dep, movement_date))
                    movement_id = cursor.fetchone()[0]
                    # Inserir movimento espelho para admin (user_id = 1)
                    cursor.execute("""
                        INSERT INTO t_user_capital_movements (user_id, credit, description, movement_type, movement_date, original_movement_id, original_user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (1, valor_dep, f"Movimento espelho", "mirror", movement_date, movement_id, user_id))

                    conn.commit()
                    st.success("Depósito registado com sucesso!")
                    #st.rerun()

            # --- Formulário de Levantamento ---
            with st.expander("💸 Novo Levantamento"):
                valor_lev = st.number_input("Valor a levantar", min_value=0.0, step=0.01, key="lev")
                descricao_lev = st.text_input("Descrição do levantamento")
                if st.button("Confirmar Levantamento"):
                    # Inserir movimento para o user
                    cursor.execute("""
                        INSERT INTO t_user_capital_movements (user_id, debit, description, movement_date) 
                        VALUES (%s, %s, %s, %s) RETURNING movement_id
                    """, (user_id, valor_lev, descricao_lev, movement_date))
                    movement_id = cursor.fetchone()[0]
                    # Inserir movimento espelho para admin (user_id = 1)
                    cursor.execute("""
                        INSERT INTO t_user_capital_movements (user_id, debit, description, movement_type, movement_date, original_movement_id, original_user_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (1, valor_lev, f"Movimento espelho", "mirror", movement_date, movement_id, user_id))

                    conn.commit()
                    st.success("Levantamento registado com sucesso!")
                    #st.rerun()

            # --- Histórico de movimentos ---
            st.subheader("📜 Histórico de Movimentos")
            df_mov = pd.read_sql("""
                SELECT movement_date, credit, debit, description
                FROM t_user_capital_movements
                WHERE user_id = %s
                ORDER BY movement_date DESC
            """, conn, params=(user_id,))

            st.dataframe(df_mov)

elif menu == "📈 Portofolio":
    # Obter lista de utilizadores
    df_users = pd.read_sql("SELECT tu.user_id, tu.user_name, tu.email FROM t_users tu ORDER BY tu.user_id", conn)
    opcoes = [f"{row['user_name']} ({row['email']})" for _, row in df_users.iterrows()]

    # Selectbox com pesquisa
    selecionado = st.selectbox("🔍 Escolhe um utilizador para editar", opcoes)

    # Encontrar ID do utilizador selecionado
    user_id = None
    for idx, row in df_users.iterrows():
        if selecionado == f"{row['user_name']} ({row['email']})":
            user_id = row['user_id']
            user_name = row['user_name']
            break

    if user_id:
        # movimentos reais da base de dados
        df_mov = pd.read_sql("""
            SELECT movement_date::date AS date,
                   COALESCE(credit, 0) - COALESCE(debit, 0) AS net_movement
            FROM t_user_capital_movements
            WHERE user_id = %s
            ORDER BY movement_date
        """, conn, params=(user_id,))

        # Se não houver movimentos, mostrar aviso
        if df_mov.empty:
            st.info("ℹ️ Este utilizador ainda não tem movimentos registados.")
        else:
            # Calcular saldo acumulado
            df_mov["balance"] = df_mov["net_movement"].cumsum()

            # Determinar limites de data
            min_date = df_mov["date"].min()
            max_date = max(df_mov["date"].max(), date.today())

            # Título
            if user_id == 1:
                st.title("📈 Fundo Comunitário")
            else:
                st.title(f"📈 Portofolio de {user_name}")

            # Filtros de data
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("📅 Data inicial", value=min_date, min_value=min_date, max_value=max_date)
            with col2:
                end_date = st.date_input("📅 Data final", value=max_date, min_value=min_date, max_value=max_date)
            # Filtrar por data
            df_filtered = df_mov[(df_mov["date"] >= start_date) &
                                 (df_mov["date"] <= end_date)]

            # Gráfico de saldo
            fig = px.line(df_filtered, x="date", y="balance", title="Evolução do Saldo", labels={"date": "Data", "balance": "Saldo (€)"})
            st.plotly_chart(fig)


            # Exemplo de dados simulados
            df = pd.DataFrame({
                "data": pd.date_range(start="2024-01-01", periods=6, freq="M"),
                "valor_investido": [1000, 2000, 2500, 3000, 3200, 3400],
                "valor_atual":    [1100, 2100, 2600, 2900, 3100, 3600]
            })

            # Gráfico com duas linhas
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=df["data"], y=df["valor_investido"],
                                    mode='lines+markers', name='Total Investido', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df["data"], y=df["valor_atual"],
                                    mode='lines+markers', name='Valor Atual', line=dict(color='green')))

            fig.update_layout(title='Evolução do Portfólio',
                            xaxis_title='Data',
                            yaxis_title='USD',
                            legend=dict(x=0, y=1))

            st.plotly_chart(fig)


            # Exemplo fake
            top_users = pd.DataFrame({
                "Usuário": ["alice", "bob", "charlie"],
                "Valor Total (USD)": [15000, 12000, 9800]
            })

            st.title("Top Holders da Comunidade")

            # Adiciona medalhas
            medals = ["🥇", "🥈", "🥉"] + [""] * (len(top_users) - 3)
            top_users["🏅"] = medals

            # Mostra tabela
            st.dataframe(top_users[["🏅", "Usuário", "Valor Total (USD)"]])


            # Dados de exemplo
            df = pd.DataFrame({
                "Usuário": ["Alice", "Bob", "Carlos", "Diana"],
                "Valor Total (USD)": [15000, 12000, 8000, 5000]
            })

            # Gráfico de pizza
            fig = px.pie(df, names='Usuário', values='Valor Total (USD)', title='Top Holders (USD)')

            st.plotly_chart(fig)


elif menu == "📊 Cotações":
    cg = CoinGeckoAPI()
    st.title("📈 Crypto Prices com CoinGecko")

    # Cria duas colunas
    col1, col2 = st.columns([3, 2])
    with col1:
        html_code = f'''
        <div>
        <script src="https://widgets.coingecko.com/gecko-coin-list-widget.js"></script>
        <gecko-coin-list-widget 
            locale="en" 
            dark-mode="true" 
            outlined="true" 
            coin-ids="{coin_ids_str}"
            initial-currency="usd">
        </gecko-coin-list-widget>
        </div>
        '''
        components.html(html_code, height=5000)

    with col2:
        coins = cg.get_price(ids=[coin_ids_str], vs_currencies='eur, usd')

        st.write("💹 Preços em EUR/USD:")
        st.json(coins)

elif menu == "📸 Snapshot Manual":
    st.title("📸 Criar Snapshot Manual")
    modo_portofolio = st.toggle("Modo Portofolio", value=False)

    if modo_portofolio:
        st.warning("⚠️ Work in progress.")
    else:
        snapshot_date = st.date_input("📅 Data do snapshot", date.today())
        binance = st.number_input("💰 Capital na Binance", min_value=0.0, step=10.0)
        ledger = st.number_input("🔐 Capital na Ledger", min_value=0.0, step=10.0)
        defi = st.number_input("🌊 Capital em DeFi (Cardano)", min_value=0.0, step=10.0)
        outros = st.number_input("💼 Outros", min_value=0.0, step=10.0)
        
        total = binance + ledger + defi + outros
        st.markdown(f"### 💼 Total atual: `{total:.2f} €`")

        if st.button("✅ Criar Snapshot"):
            insert_snapshot(user_id, snapshot_date, binance, ledger, defi, outros, total)
            st.success("Snapshot criado com sucesso!")
        
    # Mostrar histórico
    st.subheader("📊 Histórico de Snapshots")
    df = pd.read_sql("SELECT * FROM t_user_capital_snapshots WHERE user_id = %s ORDER BY snapshot_date", engine, params=(user_id,))
    st.dataframe(df)

elif menu == "💼 Documentos":
    submenu = st.sidebar.radio("Documentos", ["📋 Termos e Condições", "📋 Estratégia e Gestão de Risco", "📋 Roadmap"])
    if submenu == "📋 Termos e Condições":
        st.title("📋 Termos e Condições")
        pdf_path = "regulamento.pdf"

        # Ler PDF em binário e codificar para base64
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode("utf-8")

        # Mostrar o PDF via iframe
        pdf_viewer = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
        st.markdown(pdf_viewer, unsafe_allow_html=True)
    elif submenu == "📋 Estratégia e Gestão de Risco":
        st.title("📋 Estratégia e Gestão de Risco")
        pdf_path = "estrategia.pdf"

        # Ler PDF em binário e codificar para base64
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode("utf-8")

        # Mostrar o PDF via iframe
        pdf_viewer = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
        st.markdown(pdf_viewer, unsafe_allow_html=True)
