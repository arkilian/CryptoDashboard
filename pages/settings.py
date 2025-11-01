import streamlit as st
import pandas as pd
from services.fees import get_current_fee_settings, update_fee_settings, get_fee_history
from database.connection import get_engine
from sqlalchemy import text
from utils.tags import ensure_default_tags, get_all_tags
from database.migrations import ensure_exchange_accounts_category_column

def show_settings_page():
    st.title("⚙️ Configurações do Fundo")

    # Verificar se é admin
    if not st.session_state.get("is_admin", False):
        st.error("⛔ Acesso negado. Esta página é exclusiva para administradores.")
        st.stop()

    # Sub-menus
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Taxas", "🪙 Ativos", "🏦 Exchanges", "📸 Snapshots", "🏷️ Tags"])

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
                    with engine.connect() as conn:
                        conn.execute("""
                            INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (new_symbol, new_name or None, new_chain or None, new_coingecko_id or None, new_is_stablecoin))
                        conn.commit()
                    
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
        # Garantir coluna account_category
        try:
            ensure_exchange_accounts_category_column()
        except Exception:
            pass

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
                            for _, row in edited.iterrows():
                                conn.execute(
                                    text("UPDATE t_exchange_accounts SET account_category = :cat WHERE account_id = :id"),
                                    {"cat": (row.get("Categoria") or None), "id": int(row["account_id"])}
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
    # TAB 4: SNAPSHOTS DE PREÇOS
    # ========================================
    with tab4:
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
    # TAB 5: TAGS (CRUD)
    # ========================================
    with tab5:
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
                            for _, row in edited.iterrows():
                                conn.execute(
                                    text("UPDATE t_tags SET tag_label = :l, active = :a WHERE tag_id = :id"),
                                    {"l": row.get("Etiqueta") or row.get("Código"), "a": bool(row.get("Ativa")), "id": int(row["tag_id"])},
                                )
                        st.success("✅ Tags atualizadas!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar: {e}")
            with colB:
                # Remoção segura: apenas se não houver uso na tabela de relação
                # UI mais amigável: selecionar a tag por etiqueta/código
                tag_options = [
                    (int(row["tag_id"]), f"{row['tag_id']} - {row['tag_label']} ({row['tag_code']})")
                    for _, row in df_tags_edit.iterrows()
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


if __name__ == "__main__":
    show_settings_page()
