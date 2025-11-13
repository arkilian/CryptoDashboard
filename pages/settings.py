import streamlit as st
import pandas as pd
from services.fees import get_current_fee_settings, update_fee_settings, get_fee_history
from database.connection import get_engine
from sqlalchemy import text
from utils.tags import ensure_default_tags, get_all_tags

def show_settings_page():
    st.title("⚙️ Configurações do Fundo")

    # Verificar se é admin
    if not st.session_state.get("is_admin", False):
        st.error("⛔ Acesso negado. Esta página é exclusiva para administradores.")
        st.stop()

    # Sub-menus
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "💰 Taxas", "🪙 Ativos", "🏦 Exchanges", "🏦 Bancos", 
        "🔌 APIs Cardano", "🦎 APIs CoinGecko", "👛 Wallets", "📸 Snapshots", "🏷️ Tags"
    ])

    # ========================================
    # TAB 1: TAXAS
    # ========================================
    with tab1:
        fees = get_current_fee_settings()

        st.subheader("Taxas Atuais")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Taxa de Manutenção", f"{fees['maintenance_rate']*100:.2f}%")
            st.caption(f"Mínimo: €{fees['maintenance_min']:.2f}")
        with col2:
            st.metric("Taxa de Performance", f"{fees['performance_rate']*100:.2f}%")

        st.divider()

        # Histórico de Taxas
        st.subheader("📜 Histórico de Taxas")
        history = get_fee_history()
        if history:
            df = pd.DataFrame(history)
            df["maintenance_rate"] = (df["maintenance_rate"] * 100).map(lambda x: f"{x:.2f}%")
            df["performance_rate"] = (df["performance_rate"] * 100).map(lambda x: f"{x:.2f}%")
            df["valid_from"] = pd.to_datetime(df["valid_from"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df.rename(columns={
                "maintenance_rate": "Manutenção",
                "maintenance_min": "Min. Manutenção (€)",
                "performance_rate": "Performance",
                "valid_from": "Válido Desde"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não existem configurações de taxas registadas.")

        st.divider()

        # Alteração de taxas
        st.subheader("✏️ Alterar Taxas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_maintenance = st.number_input(
                "Taxa de Manutenção (%)", 
                value=fees['maintenance_rate']*100,
                min_value=0.0,
                max_value=100.0,
                step=0.01
            ) / 100
        
        with col2:
            new_minimum = st.number_input(
                "Mínimo da Taxa de Manutenção (€)", 
                value=fees['maintenance_min'],
                min_value=0.0,
                step=0.50
            )
        
        with col3:
            new_performance = st.number_input(
                "Taxa de Performance (%)", 
                value=fees['performance_rate']*100,
                min_value=0.0,
                max_value=100.0,
                step=0.5
            ) / 100

        if st.button("Atualizar Taxas", type="primary", use_container_width=True):
            update_fee_settings(new_maintenance, new_minimum, new_performance)
            st.success("✅ Nova configuração de taxas aplicada com sucesso!")
            st.rerun()

    # ========================================
    # TAB 2: ATIVOS
    # ========================================
    with tab2:
        engine = get_engine()
        
        st.subheader("🪙 Gestão de Ativos")
        
        # Listar ativos existentes
        df_assets = pd.read_sql("""
            SELECT asset_id, symbol, name, chain, coingecko_id, is_stablecoin
            FROM t_assets
            ORDER BY symbol
        """, engine)
        
        if not df_assets.empty:
            st.dataframe(
                df_assets.rename(columns={
                    "asset_id": "ID",
                    "symbol": "Símbolo",
                    "name": "Nome",
                    "chain": "Blockchain",
                    "coingecko_id": "CoinGecko ID",
                    "is_stablecoin": "Stablecoin"
                }).drop('ID', axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"📊 Total: {len(df_assets)} ativos")
        else:
            st.info("📭 Nenhum ativo registado ainda.")
        
        st.divider()
        
        # Adicionar novo ativo
        st.subheader("➕ Adicionar Novo Ativo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_symbol = st.text_input("Símbolo", placeholder="Ex: BTC, ETH, ADA").upper()
            new_name = st.text_input("Nome", placeholder="Ex: Bitcoin, Ethereum")
            new_coingecko_id = st.text_input(
                "CoinGecko ID", 
                placeholder="Ex: bitcoin, ethereum",
                help="ID do ativo no CoinGecko para cotações automáticas"
            )
        
        with col2:
            new_chain = st.text_input("Blockchain", placeholder="Ex: Bitcoin, Ethereum, Cardano")
            new_is_stablecoin = st.checkbox("É uma stablecoin?")
        
        if st.button("Adicionar Ativo", type="primary", use_container_width=True):
            if not new_symbol:
                st.error("❌ O símbolo é obrigatório!")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
                                VALUES (:symbol, :name, :chain, :coingecko_id, :is_stablecoin)
                            """),
                            {
                                "symbol": new_symbol,
                                "name": new_name or None,
                                "chain": new_chain or None,
                                "coingecko_id": new_coingecko_id or None,
                                "is_stablecoin": new_is_stablecoin
                            }
                        )
                    
                    st.success(f"✅ Ativo {new_symbol} adicionado com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                        st.error(f"❌ O ativo {new_symbol} já existe!")
                    else:
                        st.error(f"❌ Erro ao adicionar ativo: {str(e)}")

    # ========================================
    # TAB 3: EXCHANGES
    # ========================================
    with tab3:
        st.subheader("🏦 Gestão de Exchanges")
        
        # Listar exchanges existentes
        df_exchanges = pd.read_sql("""
            SELECT exchange_id, name, category
            FROM t_exchanges
            ORDER BY name
        """, engine)
        
        if not df_exchanges.empty:
            st.dataframe(
                df_exchanges.rename(columns={
                    "exchange_id": "ID",
                    "name": "Nome",
                    "category": "Categoria"
                }).drop('ID', axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"📊 Total: {len(df_exchanges)} exchanges")
        else:
            st.info("📭 Nenhuma exchange registada ainda.")
        
        st.divider()
        
    # Adicionar nova exchange
        st.subheader("➕ Adicionar Nova Exchange")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_exchange_name = st.text_input("Nome da Exchange", placeholder="Ex: Binance, Kraken")
        
        with col2:
            new_category = st.selectbox(
                "Categoria",
                ["CEX", "Wallet", "DeFi", "Outro"]
            )
        
        if st.button("Adicionar Exchange", type="primary", use_container_width=True):
            if not new_exchange_name:
                st.error("❌ O nome da exchange é obrigatório!")
            else:
                try:
                    with engine.connect() as conn:
                        conn.execute("""
                            INSERT INTO t_exchanges (name, category)
                            VALUES (%s, %s)
                        """, (new_exchange_name, new_category))
                        conn.commit()
                    
                    st.success(f"✅ Exchange {new_exchange_name} adicionada com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao adicionar exchange: {str(e)}")

        st.divider()
        st.subheader("🏷️ Contas por Exchange (categoria)")

        # Selecionar exchange para gerir contas
        if not df_exchanges.empty:
            exch_map = dict(zip(df_exchanges['name'], df_exchanges['exchange_id']))
            selected_exch_name = st.selectbox("Exchange", list(exch_map.keys()), key="acct_exch_sel")
            selected_exch_id = exch_map[selected_exch_name]

            df_accounts = pd.read_sql(
                """
                SELECT account_id, name, COALESCE(account_category,'') AS account_category
                FROM t_exchange_accounts
                WHERE exchange_id = %s
                ORDER BY name
                """,
                engine,
                params=(int(selected_exch_id),)
            )

            # Tabela editável de categorias
            if not df_accounts.empty:
                st.caption("Edite a categoria da conta e clique em Guardar alterações")
                category_choices = ["", "Spot", "Earn", "LP", "Futures", "Staking", "DeFi", "Wallet", "Outro"]
                edited = st.data_editor(
                    df_accounts.rename(columns={"name": "Conta", "account_category": "Categoria"}),
                    column_config={
                        "Categoria": st.column_config.SelectboxColumn(options=category_choices)
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="fixed",
                    key="acct_editor"
                )
                if st.button("Guardar alterações", key="save_acct_cats"):
                    try:
                        with engine.begin() as conn:
                            # Optimized: Use executemany for bulk updates instead of iterrows()
                            updates = [
                                {"cat": (row.get("Categoria") or None), "id": int(row["account_id"])}
                                for row in edited.to_dict('records')
                            ]
                            if updates:
                                conn.execute(
                                    text("UPDATE t_exchange_accounts SET account_category = :cat WHERE account_id = :id"),
                                    updates
                                )
                        st.success("✅ Categorias de contas atualizadas!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar: {e}")
            else:
                st.info("📭 Nenhuma conta nesta exchange.")

            st.markdown("### ➕ Adicionar Conta")
            col1, col2 = st.columns(2)
            with col1:
                new_acct_name = st.text_input("Nome da Conta", placeholder="Ex.: Spot, Earn 1, LP Pool A")
            with col2:
                new_acct_cat = st.selectbox("Categoria", ["", "Spot", "Earn", "LP", "Futures", "Staking", "DeFi", "Wallet", "Outro"], index=0)
            if st.button("Adicionar Conta", key="btn_add_account"):
                if not new_acct_name:
                    st.error("❌ O nome da conta é obrigatório")
                else:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("INSERT INTO t_exchange_accounts (exchange_id, user_id, name, account_category) VALUES (:ex, NULL, :nm, :cat)"),
                                {"ex": int(selected_exch_id), "nm": new_acct_name, "cat": (new_acct_cat or None)}
                            )
                        st.success("✅ Conta adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar conta: {e}")
        else:
            st.info("Adicione uma exchange para gerir contas.")

    # ========================================
    # TAB 4: BANCOS
    # ========================================
    with tab4:
        show_banks_settings()

    # ========================================
    # TAB 5: APIs CARDANO
    # ========================================
    with tab5:
        show_api_cardano_settings()

    # ========================================
    # TAB 6: APIs COINGECKO
    # ========================================
    with tab6:
        show_api_coingecko_settings()

    # ========================================
    # TAB 7: WALLETS
    # ========================================
    with tab7:
        show_wallets_settings()

    # ========================================
    # TAB 8: SNAPSHOTS DE PREÇOS
    # ========================================
    with tab8:
        from datetime import date, timedelta
        from services.snapshots import populate_snapshots_for_period, update_latest_prices
        
        st.subheader("📸 Gestão de Snapshots de Preços")
        
        st.markdown("""
        Os snapshots de preços históricos permitem:
        - Carregar gráficos de portfólio mais rapidamente
        - Evitar chamadas repetidas ao CoinGecko
        - Manter um histórico de preços local para análise
        """)
        
        # Estatísticas dos snapshots
        df_stats = pd.read_sql("""
            SELECT 
                COUNT(DISTINCT asset_id) as num_assets,
                COUNT(*) as num_snapshots,
                MIN(snapshot_date) as first_date,
                MAX(snapshot_date) as last_date
            FROM t_price_snapshots
        """, engine)
        
        if not df_stats.empty and df_stats.iloc[0]['num_snapshots'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Ativos", df_stats.iloc[0]['num_assets'])
            with col2:
                st.metric("Total Snapshots", df_stats.iloc[0]['num_snapshots'])
            with col3:
                first = df_stats.iloc[0]['first_date']
                st.metric("Primeira Data", first.strftime("%Y-%m-%d") if first else "—")
            with col4:
                last = df_stats.iloc[0]['last_date']
                st.metric("Última Data", last.strftime("%Y-%m-%d") if last else "—")
        else:
            st.info("📭 Ainda não há snapshots de preços guardados.")
        
        st.divider()
        
        # Atualizar preços de hoje
        st.subheader("🔄 Atualização Rápida")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("Atualiza os preços de **hoje** para todos os ativos configurados com CoinGecko ID.")
        with col2:
            if st.button("🔄 Atualizar Preços de Hoje", use_container_width=True, type="primary"):
                with st.spinner("Atualizando preços..."):
                    try:
                        update_latest_prices()
                        st.success("✅ Preços de hoje atualizados com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar preços: {e}")
        
        st.divider()
        
        # Preencher período histórico
        st.subheader("📅 Preencher Período Histórico")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date_snap = st.date_input(
                "Data Inicial",
                value=date.today() - timedelta(days=30),
                max_value=date.today(),
                key="snap_start"
            )
        with col2:
            end_date_snap = st.date_input(
                "Data Final",
                value=date.today(),
                min_value=start_date_snap,
                max_value=date.today(),
                key="snap_end"
            )
        
        days_diff = (end_date_snap - start_date_snap).days + 1
        st.caption(f"⏱️ Serão processados {days_diff} dias de dados históricos.")
        
        if st.button("📸 Preencher Snapshots", use_container_width=True, type="secondary"):
            if days_diff > 365:
                st.warning("⚠️ Períodos muito longos podem demorar bastante tempo.")
            
            with st.spinner(f"Preenchendo snapshots de {start_date_snap} a {end_date_snap}..."):
                try:
                    populate_snapshots_for_period(start_date_snap, end_date_snap)
                    st.success(f"✅ Snapshots preenchidos com sucesso para {days_diff} dias!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao preencher snapshots: {e}")
        
        st.divider()
        
        # Últimos snapshots
        st.subheader("📋 Últimos Snapshots Guardados")
        
        df_recent = pd.read_sql("""
            SELECT 
                a.symbol as "Ativo",
                ps.snapshot_date as "Data",
                ps.price_eur as "Preço (€)",
                ps.source as "Origem",
                ps.created_at as "Guardado em"
            FROM t_price_snapshots ps
            JOIN t_assets a ON ps.asset_id = a.asset_id
            ORDER BY ps.created_at DESC
            LIMIT 20
        """, engine)
        
        if not df_recent.empty:
            df_recent["Data"] = pd.to_datetime(df_recent["Data"]).dt.strftime("%Y-%m-%d")
            df_recent["Guardado em"] = pd.to_datetime(df_recent["Guardado em"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Ainda não há snapshots guardados.")

    # ========================================
    # TAB 8: GESTÃO DE TAGS
    # ========================================
    with tab9:
        st.subheader("🏷️ Gestão de Tags (Estratégia)")
        try:
            ensure_default_tags(engine)
        except Exception:
            pass

        df_tags = pd.read_sql("SELECT tag_id, tag_code, COALESCE(tag_label, tag_code) AS tag_label, active FROM t_tags ORDER BY tag_label", engine)
        if not df_tags.empty:
            st.dataframe(
                df_tags.rename(columns={"tag_code": "Código", "tag_label": "Etiqueta", "active": "Ativa"}).drop("tag_id", axis=1),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📭 Sem tags.")

        st.divider()
        st.markdown("### ➕ Adicionar Tag")
        col1, col2 = st.columns(2)
        with col1:
            new_tag_code = st.text_input("Código", placeholder="ex.: staking, defi").strip()
        with col2:
            new_tag_label = st.text_input("Etiqueta", placeholder="ex.: Staking, DeFi").strip()
        if st.button("Adicionar Tag", key="btn_add_tag", type="primary"):
            if not new_tag_code:
                st.error("❌ Código é obrigatório")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO t_tags (tag_code, tag_label, active) VALUES (:c, :l, TRUE)"), {"c": new_tag_code, "l": new_tag_label or new_tag_code})
                    st.success("✅ Tag adicionada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao adicionar: {e}")

        st.divider()
        st.markdown("### ✏️ Editar/Remover Tags")
        df_tags_edit = pd.read_sql("SELECT tag_id, tag_code, COALESCE(tag_label, tag_code) AS tag_label, active FROM t_tags ORDER BY tag_label", engine)
        if not df_tags_edit.empty:
            edited = st.data_editor(
                df_tags_edit.rename(columns={"tag_code": "Código", "tag_label": "Etiqueta", "active": "Ativa"}),
                column_config={"Ativa": st.column_config.CheckboxColumn()},
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key="tags_editor"
            )
            colA, colB = st.columns(2)
            with colA:
                if st.button("Guardar alterações", key="btn_save_tags"):
                    try:
                        with engine.begin() as conn:
                            # Optimized: Use executemany for bulk updates instead of iterrows()
                            updates = [
                                {"l": row.get("Etiqueta") or row.get("Código"), "a": bool(row.get("Ativa")), "id": int(row["tag_id"])}
                                for row in edited.to_dict('records')
                            ]
                            if updates:
                                conn.execute(
                                    text("UPDATE t_tags SET tag_label = :l, active = :a WHERE tag_id = :id"),
                                    updates
                                )
                        st.success("✅ Tags atualizadas!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar: {e}")
            with colB:
                # Remoção segura: apenas se não houver uso na tabela de relação
                # UI mais amigável: selecionar a tag por etiqueta/código
                # Optimized: Use to_dict() instead of iterrows()
                tag_options = [
                    (int(row["tag_id"]), f"{row['tag_id']} - {row['tag_label']} ({row['tag_code']})")
                    for row in df_tags_edit.to_dict('records')
                ]
                if tag_options:
                    option_labels = [lbl for _, lbl in tag_options]
                    selected_label = st.selectbox("Selecionar Tag para remover", option_labels, key="tag_del_select")
                    selected_id = next((tid for tid, lbl in tag_options if lbl == selected_label), None)
                    if st.button("Remover Tag", key="btn_delete_tag"):
                        try:
                            with engine.begin() as conn:
                                used = conn.execute(text("SELECT COUNT(*) FROM t_transaction_tags WHERE tag_id = :id"), {"id": int(selected_id)}).scalar()
                                if used and used > 0:
                                    st.warning("❌ Tag em uso, não pode ser removida. Desative-a em vez disso.")
                                else:
                                    conn.execute(text("DELETE FROM t_tags WHERE tag_id = :id"), {"id": int(selected_id)})
                                    st.success("✅ Tag removida!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao remover: {e}")
                else:
                    st.info("Sem tags para remover.")


def show_banks_settings():
    """Tab de configuração de contas bancárias."""
    from database.banks import (
        get_all_banks, create_bank, update_bank, delete_bank, 
        set_primary_bank, validate_iban
    )
    
    st.subheader("🏦 Gestão de Contas Bancárias")
    
    # Filtro por utilizador (apenas admin vê todos)
    user_id = st.session_state.get("user_id")
    is_admin = st.session_state.get("is_admin", False)
    
    if is_admin:
        # Admin pode ver todos ou filtrar por utilizador
        from database.users import get_all_users
        users = get_all_users()
        user_options = [("Todos", None)] + [(u['username'], u['user_id']) for u in users]
        selected_user = st.selectbox(
            "Filtrar por utilizador",
            options=user_options,
            format_func=lambda x: x[0],
            key="banks_filter_user"
        )
        filter_user_id = selected_user[1]
    else:
        filter_user_id = user_id
    
    # Listar bancos
    banks = get_all_banks(filter_user_id)
    
    if banks:
        df_banks = pd.DataFrame(banks)
        
        # Selecionar colunas para display
        display_cols = ['banco_id', 'username', 'bank_name', 'account_holder', 
                       'iban', 'currency', 'is_active', 'is_primary']
        display_df = df_banks[display_cols].copy()
        display_df['is_active'] = display_df['is_active'].map({True: '✅', False: '❌'})
        display_df['is_primary'] = display_df['is_primary'].map({True: '⭐', False: ''})
        
        display_df = display_df.rename(columns={
            'banco_id': 'ID',
            'username': 'Utilizador',
            'bank_name': 'Banco',
            'account_holder': 'Titular',
            'iban': 'IBAN',
            'currency': 'Moeda',
            'is_active': 'Ativo',
            'is_primary': 'Principal'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma conta bancária cadastrada")
    
    st.divider()
    
    # Formulário para adicionar/editar
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ➕ Adicionar Nova Conta")
        
        with st.form("add_bank_form"):
            # Se não admin, usar user_id da sessão
            if not is_admin:
                form_user_id = user_id
                st.info(f"Conta será criada para: {st.session_state.get('username')}")
            else:
                users = get_all_users()
                user_choice = st.selectbox(
                    "Utilizador",
                    options=[(u['username'], u['user_id']) for u in users],
                    format_func=lambda x: x[0],
                    key="banks_add_user"
                )
                form_user_id = user_choice[1]
            
            bank_name = st.text_input("Nome do Banco *", placeholder="Ex: Banco BPI")
            account_holder = st.text_input("Titular *", placeholder="Nome completo")
            iban = st.text_input("IBAN", placeholder="PT50...")
            swift_bic = st.text_input("SWIFT/BIC", placeholder="BBPIPTPL")
            account_number = st.text_input("Número de Conta", placeholder="Formato local")
            
            col_a, col_b = st.columns(2)
            with col_a:
                currency = st.selectbox("Moeda", ["EUR", "USD", "GBP", "CHF"], index=0)
            with col_b:
                account_type = st.selectbox(
                    "Tipo de Conta",
                    [None, "checking", "savings", "business", "investment"],
                    format_func=lambda x: {
                        None: "Não especificado",
                        "checking": "À ordem",
                        "savings": "Poupança",
                        "business": "Empresarial",
                        "investment": "Investimento"
                    }[x]
                )
            
            country = st.text_input("País", placeholder="Portugal")
            branch = st.text_input("Agência/Balcão", placeholder="Opcional")
            
            col_x, col_y = st.columns(2)
            with col_x:
                is_active = st.checkbox("Conta Ativa", value=True)
            with col_y:
                is_primary = st.checkbox("Conta Principal")
            
            notes = st.text_area("Notas", placeholder="Observações adicionais")
            
            submitted = st.form_submit_button("💾 Adicionar Conta", use_container_width=True)
            
            if submitted:
                if not bank_name or not account_holder:
                    st.error("Nome do banco e titular são obrigatórios")
                elif iban and not validate_iban(iban):
                    st.warning("⚠️ Formato de IBAN inválido (verificação básica)")
                else:
                    success, msg = create_bank(
                        user_id=form_user_id,
                        bank_name=bank_name,
                        account_holder=account_holder,
                        iban=iban,
                        swift_bic=swift_bic,
                        account_number=account_number,
                        currency=currency,
                        country=country,
                        branch=branch,
                        account_type=account_type,
                        is_active=is_active,
                        is_primary=is_primary,
                        notes=notes
                    )
                    
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    with col2:
        st.markdown("### ✏️ Editar/Remover Conta")
        
        if banks:
            bank_options = [(f"{b['banco_id']} - {b['bank_name']} ({b['username']})", b['banco_id']) 
                           for b in banks]
            selected_bank = st.selectbox(
                "Selecionar Conta",
                options=bank_options,
                format_func=lambda x: x[0],
                key="banks_select_edit"
            )
            banco_id = selected_bank[1]
            
            # Botões de ação
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("⭐ Definir Principal", key=f"btn_bank_primary_{banco_id}", use_container_width=True):
                    success, msg = set_primary_bank(banco_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_btn2:
                if st.button("✏️ Editar", key="btn_edit_bank", use_container_width=True):
                    st.session_state['editing_bank'] = banco_id
            
            with col_btn3:
                if st.button("🗑️ Remover", key=f"btn_bank_delete_{banco_id}", type="secondary", use_container_width=True):
                    if st.session_state.get('confirm_delete_bank') == banco_id:
                        success, msg = delete_bank(banco_id)
                        if success:
                            st.success(msg)
                            st.session_state.pop('confirm_delete_bank', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state['confirm_delete_bank'] = banco_id
                        st.warning("⚠️ Clique novamente para confirmar remoção")
            
            # Formulário de edição
            if st.session_state.get('editing_bank') == banco_id:
                bank_data = next((b for b in banks if b['banco_id'] == banco_id), None)
                
                with st.form("edit_bank_form"):
                    st.markdown("**Editar Conta**")
                    
                    edit_bank_name = st.text_input("Nome do Banco", value=bank_data['bank_name'])
                    edit_holder = st.text_input("Titular", value=bank_data['account_holder'])
                    edit_iban = st.text_input("IBAN", value=bank_data.get('iban') or '')
                    edit_swift = st.text_input("SWIFT/BIC", value=bank_data.get('swift_bic') or '')
                    edit_currency = st.selectbox(
                        "Moeda", 
                        ["EUR", "USD", "GBP", "CHF"],
                        index=["EUR", "USD", "GBP", "CHF"].index(bank_data.get('currency', 'EUR'))
                    )
                    edit_active = st.checkbox("Ativa", value=bank_data['is_active'])
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if save_btn:
                        success, msg = update_bank(
                            banco_id=banco_id,
                            bank_name=edit_bank_name,
                            account_holder=edit_holder,
                            iban=edit_iban if edit_iban else None,
                            swift_bic=edit_swift if edit_swift else None,
                            currency=edit_currency,
                            is_active=edit_active
                        )
                        
                        if success:
                            st.success(msg)
                            st.session_state.pop('editing_bank', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    if cancel_btn:
                        st.session_state.pop('editing_bank', None)
                        st.rerun()


def show_api_cardano_settings():
    """Tab de configuração de APIs Cardano."""
    from database.api_config import (
        get_all_apis, create_api, update_api, delete_api, toggle_api_status
    )
    
    st.subheader("🔌 Gestão de APIs Cardano")
    
    # Listar APIs
    apis = get_all_apis()
    
    if apis:
        df_apis = pd.DataFrame(apis)
        
        display_cols = ['api_id', 'api_name', 'base_url', 'is_active', 
                       'rate_limit', 'timeout', 'default_address']
        display_df = df_apis[display_cols].copy()
        display_df['is_active'] = display_df['is_active'].map({True: '✅', False: '❌'})
        display_df['default_address'] = display_df['default_address'].apply(
            lambda x: f"{x[:12]}...{x[-8:]}" if x and len(x) > 24 else x or ''
        )
        
        display_df = display_df.rename(columns={
            'api_id': 'ID',
            'api_name': 'API',
            'base_url': 'URL Base',
            'is_active': 'Ativo',
            'rate_limit': 'Rate Limit',
            'timeout': 'Timeout',
            'default_address': 'Endereço Padrão'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma API configurada")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ➕ Adicionar Nova API")
        
        with st.form("add_api_form"):
            api_name = st.text_input("Nome da API *", placeholder="Ex: CardanoScan")
            api_key = st.text_input("API Key *", type="password", placeholder="Sua chave de API")
            base_url = st.text_input("URL Base *", placeholder="https://api.cardanoscan.io/api/v1")
            default_address = st.text_input("Endereço Padrão", placeholder="addr1...")
            
            col_a, col_b = st.columns(2)
            with col_a:
                rate_limit = st.number_input("Rate Limit (req/min)", min_value=0, value=60)
            with col_b:
                timeout = st.number_input("Timeout (segundos)", min_value=1, value=10)
            
            is_active = st.checkbox("API Ativa", value=True)
            notes = st.text_area("Notas", placeholder="Observações sobre a API")
            
            submitted = st.form_submit_button("💾 Adicionar API", use_container_width=True)
            
            if submitted:
                if not api_name or not api_key or not base_url:
                    st.error("Nome, API Key e URL são obrigatórios")
                else:
                    success, msg = create_api(
                        api_name=api_name,
                        api_key=api_key,
                        base_url=base_url,
                        is_active=is_active,
                        default_address=default_address if default_address else None,
                        rate_limit=rate_limit if rate_limit > 0 else None,
                        timeout=timeout,
                        notes=notes if notes else None
                    )
                    
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    with col2:
        st.markdown("### ✏️ Editar/Remover API")
        
        if apis:
            api_options = [(f"{a['api_id']} - {a['api_name']}", a['api_id']) for a in apis]
            selected_api = st.selectbox(
                "Selecionar API",
                options=api_options,
                format_func=lambda x: x[0],
                key="apis_select_edit"
            )
            api_id = selected_api[1]
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("🔄 Ativar/Desativar", key=f"btn_api_toggle_{api_id}", use_container_width=True):
                    success, msg = toggle_api_status(api_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_btn2:
                if st.button("✏️ Editar", key="btn_edit_api", use_container_width=True):
                    st.session_state['editing_api'] = api_id
            
            with col_btn3:
                if st.button("🗑️ Remover", key=f"btn_api_delete_{api_id}", type="secondary", use_container_width=True):
                    if st.session_state.get('confirm_delete_api') == api_id:
                        success, msg = delete_api(api_id)
                        if success:
                            st.success(msg)
                            st.session_state.pop('confirm_delete_api', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state['confirm_delete_api'] = api_id
                        st.warning("⚠️ Clique novamente para confirmar remoção")
            
            # Formulário de edição
            if st.session_state.get('editing_api') == api_id:
                api_data = next((a for a in apis if a['api_id'] == api_id), None)
                
                with st.form("edit_api_form"):
                    st.markdown("**Editar API**")
                    
                    edit_name = st.text_input("Nome", value=api_data['api_name'])
                    edit_key = st.text_input("API Key", type="password", value=api_data['api_key'])
                    edit_url = st.text_input("URL", value=api_data['base_url'])
                    edit_default_addr = st.text_input("Endereço Padrão", 
                                                      value=api_data.get('default_address') or '')
                    edit_timeout = st.number_input("Timeout", min_value=1, 
                                                   value=api_data.get('timeout', 10))
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Cancelar", use_container_width=True)

                    if save_btn:
                        success, msg = update_api(
                            api_id=api_id,
                            api_name=edit_name,
                            api_key=edit_key,
                            base_url=edit_url,
                            default_address=edit_default_addr if edit_default_addr else None,
                            timeout=edit_timeout
                        )

                        if success:
                            st.success(msg)
                            st.session_state.pop('editing_api', None)
                            st.rerun()
                        else:
                            st.error(msg)

                    if cancel_btn:
                        st.session_state.pop('editing_api', None)
                        st.rerun()

    st.divider()
    st.markdown("### 🔁 Resync de Wallets Cardano")
    from sqlalchemy import text as _sql_text
    from database.wallets import get_active_wallets
    from services.cardano_sync import sync_all_cardano_wallets_for_user

    # Listar apenas wallets Cardano ativas
    wallets = [w for w in get_active_wallets(st.session_state.get("user_id")) if (w.get("blockchain") or "").lower() == "cardano"]
    if wallets:
        # Seleção de wallets
        options = {f"{w['wallet_id']} - {w['wallet_name']}": int(w['wallet_id']) for w in wallets}
        selected_labels = st.multiselect("Selecionar wallet(s) para resync", list(options.keys()), placeholder="Escolha uma ou mais wallets")
        selected_ids = [options[lbl] for lbl in selected_labels]

        col_a, col_b, col_c = st.columns([1,1,1])
        with col_a:
            max_pages = st.slider("Páginas a sincronizar", min_value=1, max_value=50, value=20, help="Quantas páginas recentes buscar por wallet")
        with col_b:
            wipe_first = st.checkbox("Apagar transações existentes antes do sync", value=False, help="Irá remover t_cardano_transactions e respetivos IO para as wallets selecionadas e reiniciar o estado de sync")
        with col_c:
            show_counts = st.checkbox("Mostrar contagens após sync", value=True)

        if st.button("🚀 Executar Resync", type="primary", use_container_width=True, disabled=(len(selected_ids) == 0)):
            if not selected_ids:
                st.warning("Selecione pelo menos uma wallet")
            else:
                try:
                    with get_engine().begin() as conn:
                        if wipe_first:
                            conn.execute(_sql_text("DELETE FROM t_cardano_transactions WHERE wallet_id = ANY(:w)"), {"w": selected_ids})
                            conn.execute(_sql_text("DELETE FROM t_cardano_sync_state WHERE wallet_id = ANY(:w)"), {"w": selected_ids})
                    
                    res = sync_all_cardano_wallets_for_user(wallet_ids=selected_ids, max_pages=int(max_pages))
                    st.success(f"✅ Resync concluído: {res}")

                    if show_counts:
                        with get_engine().connect() as conn:
                            rows = conn.execute(_sql_text(
                                """
                                SELECT wallet_id,
                                       COUNT(*) AS tx_rows,
                                       COUNT(DISTINCT tx_hash) AS tx_unique,
                                       (
                                         SELECT COUNT(*) FROM t_cardano_tx_io i WHERE i.wallet_id = t.wallet_id
                                       ) AS io_rows
                                FROM t_cardano_transactions t
                                WHERE wallet_id = ANY(:w)
                                GROUP BY wallet_id
                                ORDER BY wallet_id
                                """
                            ), {"w": selected_ids}).fetchall()
                        if rows:
                            df = pd.DataFrame(rows, columns=["Wallet ID", "TX Rows", "TX Únicas", "IO Rows"]) 
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.info("Sem transações após sync.")
                except Exception as e:
                    st.error(f"❌ Erro no resync: {e}")
    else:
        st.info("Não há wallets Cardano ativas para sincronizar.")


def show_api_coingecko_settings():
    """Tab de configuração de APIs CoinGecko."""
    from database.api_config import (
        get_all_coingecko_apis, create_coingecko_api, update_coingecko_api, 
        delete_coingecko_api, toggle_coingecko_api_status
    )
    # Invalidate runtime cache after changes so new DB values (e.g., rate_limit) apply immediately
    try:
        from services.coingecko import invalidate_coingecko_config_cache
    except Exception:
        invalidate_coingecko_config_cache = None
    
    st.subheader("🦎 Gestão de APIs CoinGecko")
    
    st.info("""
    💡 **CoinGecko API Key (opcional)**
    - Plano **Free**: 10-50 chamadas/minuto sem API key
    - Plano **Pro/Enterprise**: até 500 chamadas/minuto com API key
    
    Configure o `rate_limit` de acordo com o seu plano para evitar 429 errors.
    """)
    
    # Listar APIs
    apis = get_all_coingecko_apis()
    
    if apis:
        df_apis = pd.DataFrame(apis)
        
        display_cols = ['api_id', 'api_name', 'base_url', 'is_active', 'rate_limit', 'timeout']
        display_df = df_apis[display_cols].copy()
        display_df['is_active'] = display_df['is_active'].map({True: '✅', False: '❌'})
        display_df['api_key'] = df_apis['api_key'].apply(lambda x: '🔑 Sim' if x else '—')
        
        display_df = display_df.rename(columns={
            'api_id': 'ID',
            'api_name': 'API',
            'base_url': 'URL Base',
            'is_active': 'Ativo',
            'rate_limit': 'Rate Limit (req/min)',
            'timeout': 'Timeout (s)',
            'api_key': 'API Key'
        })
        
        # Reorder columns
        display_df = display_df[['ID', 'API', 'API Key', 'URL Base', 'Ativo', 'Rate Limit (req/min)', 'Timeout (s)']]
        
        st.dataframe(display_df.drop('ID', axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma API CoinGecko configurada")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ➕ Adicionar Nova API")
        
        with st.form("add_coingecko_api_form"):
            api_name = st.text_input("Nome da API *", placeholder="Ex: CoinGecko Pro")
            api_key = st.text_input(
                "API Key (opcional para plano Free)", 
                type="password", 
                placeholder="Deixe vazio para usar API pública",
                help="Necessária apenas para planos Pro/Enterprise"
            )
            base_url = st.text_input(
                "URL Base *", 
                value="https://api.coingecko.com/api/v3",
                placeholder="https://api.coingecko.com/api/v3"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                rate_limit = st.number_input(
                    "Rate Limit (req/min)", 
                    min_value=1, 
                    value=10,
                    help="Free: 10-50 | Pro: 500+"
                )
            with col_b:
                timeout = st.number_input("Timeout (segundos)", min_value=5, value=15)
            
            is_active = st.checkbox("API Ativa", value=True)
            notes = st.text_area("Notas", placeholder="Ex: Plano Free, Plano Pro, etc.")
            
            submitted = st.form_submit_button("💾 Adicionar API", use_container_width=True)
            
            if submitted:
                if not api_name or not base_url:
                    st.error("Nome e URL são obrigatórios")
                else:
                    success, msg = create_coingecko_api(
                        api_name=api_name,
                        api_key=api_key if api_key else None,
                        base_url=base_url,
                        is_active=is_active,
                        rate_limit=rate_limit,
                        timeout=timeout,
                        notes=notes if notes else None
                    )
                    
                    if success:
                        if invalidate_coingecko_config_cache:
                            invalidate_coingecko_config_cache()
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    with col2:
        st.markdown("### ✏️ Editar/Remover API")
        
        if apis:
            api_options = [(f"{a['api_id']} - {a['api_name']}", a['api_id']) for a in apis]
            selected_api = st.selectbox(
                "Selecionar API",
                options=api_options,
                format_func=lambda x: x[0],
                key="coingecko_apis_select_edit"
            )
            api_id = selected_api[1]
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("🔄 Ativar/Desativar", key=f"btn_coingecko_api_toggle_{api_id}", use_container_width=True):
                    success, msg = toggle_coingecko_api_status(api_id)
                    if success:
                        if invalidate_coingecko_config_cache:
                            invalidate_coingecko_config_cache()
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_btn2:
                if st.button("✏️ Editar", key="btn_edit_coingecko_api", use_container_width=True):
                    st.session_state['editing_coingecko_api'] = api_id
            
            with col_btn3:
                if st.button("🗑️ Remover", key=f"btn_coingecko_api_delete_{api_id}", type="secondary", use_container_width=True):
                    if st.session_state.get('confirm_delete_coingecko_api') == api_id:
                        success, msg = delete_coingecko_api(api_id)
                        if success:
                            if invalidate_coingecko_config_cache:
                                invalidate_coingecko_config_cache()
                            st.success(msg)
                            st.session_state.pop('confirm_delete_coingecko_api', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state['confirm_delete_coingecko_api'] = api_id
                        st.warning("⚠️ Clique novamente para confirmar remoção")
            
            # Formulário de edição
            if st.session_state.get('editing_coingecko_api') == api_id:
                api_data = next((a for a in apis if a['api_id'] == api_id), None)
                
                with st.form("edit_coingecko_api_form"):
                    st.markdown("**Editar API CoinGecko**")
                    
                    edit_name = st.text_input("Nome", value=api_data['api_name'])
                    edit_key = st.text_input(
                        "API Key (deixe vazio para manter atual)", 
                        type="password",
                        placeholder="••••••••",
                        help="Deixe vazio para não alterar a API key existente"
                    )
                    edit_url = st.text_input("URL", value=api_data['base_url'])
                    edit_rate_limit = st.number_input(
                        "Rate Limit (req/min)", 
                        min_value=1, 
                        value=api_data.get('rate_limit', 10)
                    )
                    edit_timeout = st.number_input(
                        "Timeout", 
                        min_value=5, 
                        value=api_data.get('timeout', 15)
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if save_btn:
                        success, msg = update_coingecko_api(
                            api_id=api_id,
                            api_name=edit_name,
                            api_key=edit_key if edit_key else None,
                            base_url=edit_url,
                            rate_limit=edit_rate_limit,
                            timeout=edit_timeout
                        )
                        
                        if success:
                            if invalidate_coingecko_config_cache:
                                invalidate_coingecko_config_cache()
                            st.success(msg)
                            st.session_state.pop('editing_coingecko_api', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    if cancel_btn:
                        st.session_state.pop('editing_coingecko_api', None)
                        st.rerun()

    # Controlo global de pedidos CoinGecko e tarefas em background
    st.divider()
    st.markdown("### ⏯️ Controlo de Pedidos CoinGecko")
    try:
        from services.coingecko import pause_coingecko_requests, resume_coingecko_requests
        from services.snapshots import cancel_background_snapshots
        colp, colr, colc = st.columns(3)
        with colp:
            if st.button("⏸️ Pausar Pedidos", use_container_width=True):
                pause_coingecko_requests()
                st.success("Pedidos CoinGecko pausados")
        with colr:
            if st.button("▶️ Retomar Pedidos", use_container_width=True):
                resume_coingecko_requests()
                st.success("Pedidos CoinGecko retomados")
        with colc:
            if st.button("⏹️ Parar Snapshots em Background", use_container_width=True):
                if cancel_background_snapshots():
                    st.info("Pedido de cancelamento enviado; tarefas em execução irão terminar o mais rápido possível.")
                else:
                    st.warning("Não foi possível sinalizar cancelamento.")
    except Exception:
        st.caption("ℹ️ Controles de pausa indisponíveis no momento.")


def show_wallets_settings():
    """Tab de configuração de wallets."""
    from database.wallets import (
        get_all_wallets, create_wallet, update_wallet, delete_wallet,
        set_primary_wallet, update_balance_sync
    )
    
    st.subheader("👛 Gestão de Wallets")
    
    # Filtro por utilizador
    user_id = st.session_state.get("user_id")
    is_admin = st.session_state.get("is_admin", False)
    
    if is_admin:
        from database.users import get_all_users
        users = get_all_users()
        user_options = [("Todos", None)] + [(u['username'], u['user_id']) for u in users]
        selected_user = st.selectbox(
            "Filtrar por utilizador",
            options=user_options,
            format_func=lambda x: x[0],
            key="wallets_filter_user"
        )
        filter_user_id = selected_user[1]
    else:
        filter_user_id = user_id
    
    # Listar wallets
    wallets = get_all_wallets(filter_user_id)
    
    if wallets:
        df_wallets = pd.DataFrame(wallets)
        
        display_cols = ['wallet_id', 'username', 'wallet_name', 'wallet_type', 
                       'blockchain', 'address', 'is_active', 'is_primary']
        display_df = df_wallets[display_cols].copy()
        display_df['is_active'] = display_df['is_active'].map({True: '✅', False: '❌'})
        display_df['is_primary'] = display_df['is_primary'].map({True: '⭐', False: ''})
        display_df['address'] = display_df['address'].apply(
            lambda x: f"{x[:12]}...{x[-8:]}" if len(x) > 24 else x
        )
        
        display_df = display_df.rename(columns={
            'wallet_id': 'ID',
            'username': 'Utilizador',
            'wallet_name': 'Nome',
            'wallet_type': 'Tipo',
            'blockchain': 'Blockchain',
            'address': 'Endereço',
            'is_active': 'Ativo',
            'is_primary': 'Principal'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma wallet cadastrada")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ➕ Adicionar Nova Wallet")
        
        with st.form("add_wallet_form"):
            if not is_admin:
                form_user_id = user_id
                st.info(f"Wallet será criada para: {st.session_state.get('username')}")
            else:
                users = get_all_users()
                user_choice = st.selectbox(
                    "Utilizador",
                    options=[(u['username'], u['user_id']) for u in users],
                    format_func=lambda x: x[0],
                    key="wallets_add_user"
                )
                form_user_id = user_choice[1]
            
            wallet_name = st.text_input("Nome da Wallet *", placeholder="Ex: Eternl Principal")
            
            col_a, col_b = st.columns(2)
            with col_a:
                wallet_type = st.selectbox(
                    "Tipo *",
                    ["hot", "cold", "hardware", "exchange", "defi"],
                    format_func=lambda x: {
                        "hot": "🔥 Hot (Online)",
                        "cold": "❄️ Cold (Offline)",
                        "hardware": "🔐 Hardware",
                        "exchange": "🏦 Exchange",
                        "defi": "🌐 DeFi"
                    }[x]
                )
            with col_b:
                blockchain = st.selectbox("Blockchain *", ["Cardano", "Ethereum", "Bitcoin", "Solana"])
            
            address = st.text_input("Endereço *", placeholder="addr1...")
            stake_address = st.text_input("Stake Address (Cardano)", placeholder="stake1...")
            
            col_x, col_y = st.columns(2)
            with col_x:
                is_active = st.checkbox("Wallet Ativa", value=True)
            with col_y:
                is_primary = st.checkbox("Wallet Principal")
            
            notes = st.text_area("Notas", placeholder="Observações adicionais")
            
            submitted = st.form_submit_button("💾 Adicionar Wallet", use_container_width=True)
            
            if submitted:
                if not wallet_name or not address or not blockchain:
                    st.error("Nome, endereço e blockchain são obrigatórios")
                else:
                    success, msg = create_wallet(
                        user_id=form_user_id,
                        wallet_name=wallet_name,
                        wallet_type=wallet_type,
                        blockchain=blockchain,
                        address=address,
                        stake_address=stake_address if stake_address else None,
                        is_active=is_active,
                        is_primary=is_primary,
                        notes=notes if notes else None
                    )
                    
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    with col2:
        st.markdown("### ✏️ Editar/Remover Wallet")
        
        if wallets:
            wallet_options = [(f"{w['wallet_id']} - {w['wallet_name']} ({w['username']})", w['wallet_id']) 
                             for w in wallets]
            selected_wallet = st.selectbox(
                "Selecionar Wallet",
                options=wallet_options,
                format_func=lambda x: x[0],
                key="wallets_select_edit"
            )
            wallet_id = selected_wallet[1]
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("⭐ Definir Principal", key=f"btn_wallet_primary_{wallet_id}", use_container_width=True):
                    success, msg = set_primary_wallet(wallet_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_btn2:
                if st.button("✏️ Editar", key="btn_edit_wallet", use_container_width=True):
                    st.session_state['editing_wallet'] = wallet_id
            
            with col_btn3:
                if st.button("🗑️ Remover", key=f"btn_wallet_delete_{wallet_id}", type="secondary", use_container_width=True):
                    if st.session_state.get('confirm_delete_wallet') == wallet_id:
                        success, msg = delete_wallet(wallet_id)
                        if success:
                            st.success(msg)
                            st.session_state.pop('confirm_delete_wallet', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state['confirm_delete_wallet'] = wallet_id
                        st.warning("⚠️ Clique novamente para confirmar remoção")
            
            # Formulário de edição
            if st.session_state.get('editing_wallet') == wallet_id:
                wallet_data = next((w for w in wallets if w['wallet_id'] == wallet_id), None)
                
                with st.form("edit_wallet_form"):
                    st.markdown("**Editar Wallet**")
                    
                    edit_name = st.text_input("Nome", value=wallet_data['wallet_name'])
                    edit_type = st.selectbox(
                        "Tipo",
                        ["hot", "cold", "hardware", "exchange", "defi"],
                        index=["hot", "cold", "hardware", "exchange", "defi"].index(wallet_data['wallet_type']),
                        format_func=lambda x: {
                            "hot": "🔥 Hot", "cold": "❄️ Cold", "hardware": "🔐 Hardware",
                            "exchange": "🏦 Exchange", "defi": "🌐 DeFi"
                        }[x]
                    )
                    edit_active = st.checkbox("Ativa", value=wallet_data['is_active'])
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with col_cancel:
                        cancel_btn = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if save_btn:
                        success, msg = update_wallet(
                            wallet_id=wallet_id,
                            wallet_name=edit_name,
                            wallet_type=edit_type,
                            is_active=edit_active
                        )
                        
                        if success:
                            st.success(msg)
                            st.session_state.pop('editing_wallet', None)
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    if cancel_btn:
                        st.session_state.pop('editing_wallet', None)
                        st.rerun()


if __name__ == "__main__":
    show_settings_page()
