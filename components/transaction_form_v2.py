"""
UI Component: Formulário de registo de transações V2.
Suporta todos os tipos de transação do modelo V2.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.transaction_types import (
    TRANSACTION_TYPES,
    get_transaction_types_by_category,
    needs_from_asset,
    needs_to_asset,
    needs_from_account,
    needs_to_account,
    needs_fee_asset,
    build_transaction_params
)


def render_transaction_form(engine):
    """Renderiza o formulário de registo de transações V2."""
    
    st.subheader("Registar Nova Transação")
    
    # Buscar EUR asset_id (necessário para muitas operações)
    eur_asset = pd.read_sql("SELECT asset_id FROM t_assets WHERE symbol = 'EUR' LIMIT 1", engine)
    eur_asset_id = int(eur_asset.iloc[0]['asset_id']) if not eur_asset.empty else None
    
    if not eur_asset_id:
        st.error("⚠️ Asset EUR não encontrado. Execute a migration V2.")
        return
    
    # Seleção de tipo de transação (agrupado por categoria)
    st.markdown("### 1️⃣ Tipo de Operação")
    
    categories = get_transaction_types_by_category()
    
    # Criar tabs por categoria
    category_tabs = st.tabs(list(categories.keys()))
    
    selected_type = None
    for idx, (category, types) in enumerate(categories.items()):
        with category_tabs[idx]:
            for tx_type, label in types:
                desc = TRANSACTION_TYPES[tx_type]['description']
                if st.button(label, key=f"btn_type_{tx_type}", use_container_width=True):
                    st.session_state['tx_selected_type'] = tx_type
                    st.rerun()
                st.caption(desc)
    
    # Recuperar tipo selecionado
    selected_type = st.session_state.get('tx_selected_type')
    
    if not selected_type:
        st.info("👆 Escolha um tipo de operação acima")
        return
    
    st.success(f"✅ Tipo selecionado: **{TRANSACTION_TYPES[selected_type]['label']}**")
    
    # Botão para mudar tipo
    if st.button("🔄 Mudar tipo", key="btn_change_type"):
        st.session_state.pop('tx_selected_type', None)
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 2️⃣ Detalhes da Transação")
    
    # Data da transação
    transaction_date = st.date_input(
        "📅 Data da Transação",
        value=datetime.now().date(),
        key="tx_v2_date"
    )
    
    # Formulário dinâmico baseado no tipo
    form_data = {
        'transaction_date': datetime.combine(transaction_date, datetime.min.time()),
        'executed_by': st.session_state['user_id'],
        'eur_asset_id': eur_asset_id,
    }
    
    # Buscar dados auxiliares
    df_assets = pd.read_sql("SELECT asset_id, symbol, name FROM t_assets WHERE symbol != 'EUR' ORDER BY symbol", engine)
    df_accounts = pd.read_sql(
        """
        SELECT ea.account_id, ea.name AS account_name, e.name AS exchange_name, 
               COALESCE(ea.account_category, '') AS category
        FROM t_exchange_accounts ea
        JOIN t_exchanges e ON ea.exchange_id = e.exchange_id
        ORDER BY e.name, ea.name
        """,
        engine
    )
    df_exchanges = pd.read_sql("SELECT exchange_id, name FROM t_exchanges ORDER BY name", engine)
    
    # Assets map - Optimized: Use pandas to_dict() instead of iterrows()
    df_assets['label'] = df_assets['symbol'] + ' - ' + df_assets['name']
    asset_options = dict(zip(df_assets['label'], df_assets['asset_id'].astype(int)))
    
    # Accounts map - Optimized: Use pandas to_dict() instead of iterrows()
    df_accounts['label'] = df_accounts['exchange_name'] + ' → ' + df_accounts['account_name'] + ' (' + df_accounts['category'].fillna('—') + ')'
    account_options = dict(zip(df_accounts['label'], df_accounts['account_id'].astype(int)))
    
    # Render campos conforme tipo
    if selected_type in ['deposit', 'withdrawal']:
        _render_fiat_movement_fields(selected_type, form_data, account_options)
        
    elif selected_type in ['buy', 'sell']:
        _render_buy_sell_fields(selected_type, form_data, asset_options, account_options, df_exchanges, engine)
        
    elif selected_type == 'swap':
        _render_swap_fields(form_data, asset_options, account_options, df_exchanges, engine)
        
    elif selected_type == 'transfer':
        _render_transfer_fields(form_data, asset_options, account_options, engine)
        
    elif selected_type in ['stake', 'unstake']:
        _render_stake_fields(selected_type, form_data, asset_options, account_options)
        
    elif selected_type == 'reward':
        _render_reward_fields(form_data, asset_options, account_options)
        
    elif selected_type in ['lend', 'borrow', 'repay']:
        _render_defi_fields(selected_type, form_data, asset_options, account_options)
        
    elif selected_type == 'liquidate':
        _render_liquidate_fields(form_data, asset_options, account_options)
    
    # Notas
    st.markdown("---")
    notes = st.text_area("📝 Notas/Observações", key="tx_v2_notes")
    form_data['notes'] = notes or None
    
    # Botão de submit
    st.markdown("---")
    if st.button("✅ Registar Transação", type="primary", use_container_width=True, key="btn_submit_tx"):
        try:
            # Validações por conta (per-account)
            if selected_type == 'buy':
                qty = form_data.get('quantity', 0)
                price = form_data.get('price_eur', 0)
                fee = form_data.get('fee_eur', 0)
                total_needed = (qty * price) + fee
                account_id = form_data.get('account_id')
                eur_id = form_data.get('eur_asset_id')
                if account_id:
                    available_eur_acc = _get_account_asset_balance(engine, account_id, eur_id)
                    if total_needed > available_eur_acc + 1e-9:
                        st.error(f"❌ Saldo insuficiente nesta conta. Disponível: €{available_eur_acc:,.2f} | Necessário: €{total_needed:,.2f}")
                        return
                # Se não houver conta selecionada, não aplicamos validação por conta

            elif selected_type == 'swap':
                from_asset_id = form_data.get('from_asset_id')
                to_asset_id = form_data.get('to_asset_id')
                from_qty = float(form_data.get('from_quantity') or 0)
                fee_asset_id = form_data.get('fee_asset_id')
                fee_qty = float(form_data.get('fee_quantity') or 0)
                account_id = form_data.get('account_id')
                if account_id and from_asset_id:
                    available_from = _get_account_asset_balance(engine, account_id, int(from_asset_id))
                    # Se a taxa é no mesmo asset, somar ao débito total
                    total_debit_from = from_qty + (fee_qty if fee_asset_id == from_asset_id else 0.0)
                    if total_debit_from > available_from + 1e-9:
                        st.error(
                            f"❌ Saldo insuficiente do ativo de origem nesta conta. Disponível: {available_from:.8f} | Necessário: {total_debit_from:.8f}"
                        )
                        return
                    # Se a taxa for noutro asset, validar também
                    if fee_asset_id and fee_asset_id != from_asset_id:
                        available_fee = _get_account_asset_balance(engine, account_id, int(fee_asset_id))
                        if fee_qty > available_fee + 1e-9:
                            st.error(
                                f"❌ Saldo insuficiente para a taxa ({fee_qty:.8f} requeridos, {available_fee:.8f} disponíveis)."
                            )
                            return

            elif selected_type == 'transfer':
                asset_id = form_data.get('asset_id')
                qty = float(form_data.get('quantity') or 0)
                fee_qty = float(form_data.get('fee_quantity') or 0)
                from_account_id = form_data.get('from_account_id')
                if from_account_id and asset_id:
                    available_from = _get_account_asset_balance(engine, int(from_account_id), int(asset_id))
                    total_debit = qty + fee_qty
                    if total_debit > available_from + 1e-9:
                        st.error(
                            f"❌ Saldo insuficiente na conta de origem. Disponível: {available_from:.8f} | Necessário: {total_debit:.8f}"
                        )
                        return
            
            params = build_transaction_params(selected_type, form_data)
            _save_transaction(engine, params)
            st.success(f"✅ Transação registada com sucesso!")
            st.balloons()
            # Reset
            st.session_state.pop('tx_selected_type', None)
            st.session_state.pop('tx_v2_price_value', None)
            st.session_state.pop('tx_v2_market_price', None)
            st.session_state.pop('tx_v2_market_price_date', None)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao registar: {e}")
            import traceback
            st.code(traceback.format_exc())


def _render_fiat_movement_fields(tx_type, form_data, account_options):
    """Renderiza campos para deposit/withdrawal."""
    st.markdown("#### 💶 Movimento de EUR")
    
    col1, col2 = st.columns(2)
    
    with col1:
        amount_eur = st.number_input("Valor (EUR)", min_value=0.0, step=10.0, format="%.2f", key="tx_v2_amount")
        form_data['amount_eur'] = amount_eur
    
    with col2:
        fee_eur = st.number_input("Taxa (EUR)", min_value=0.0, step=0.1, format="%.2f", key="tx_v2_fee_eur")
        form_data['fee_eur'] = fee_eur
    
    st.markdown("#### 🔄 De / Para")
    col1, col2 = st.columns(2)
    
    with col1:
        from_label = "Conta de origem" if tx_type == 'withdrawal' else "Banco"
        if tx_type == 'deposit':
            st.info("EUR sai do banco")
            form_data['from_account_id'] = None  # Banco não tem account_id (ou criar especial)
        else:
            from_acc = st.selectbox(from_label, list(account_options.keys()), key="tx_v2_from_acc")
            form_data['from_account_id'] = account_options[from_acc]
    
    with col2:
        to_label = "Conta de destino" if tx_type == 'deposit' else "Banco"
        if tx_type == 'withdrawal':
            st.info("EUR vai para o banco")
            form_data['to_account_id'] = None
        else:
            to_acc = st.selectbox(to_label, list(account_options.keys()), key="tx_v2_to_acc")
            form_data['to_account_id'] = account_options[to_acc]
    
    st.metric("💵 Total", f"€{amount_eur:,.2f}")


def _render_buy_sell_fields(tx_type, form_data, asset_options, account_options, df_exchanges, engine):
    """Renderiza campos para buy/sell."""
    st.markdown(f"#### {'🟢 Compra' if tx_type == 'buy' else '🔴 Venda'}")
    
    # Calcular saldo disponível EUR
    df_cap = pd.read_sql(
        """
        SELECT 
            COALESCE(SUM(COALESCE(tucm.credit,0)),0) AS total_credit,
            COALESCE(SUM(COALESCE(tucm.debit,0)),0)  AS total_debit
        FROM t_user_capital_movements tucm
        JOIN t_users tu ON tucm.user_id = tu.user_id
        WHERE tu.is_admin = FALSE
        """,
        engine,
    )
    df_tx = pd.read_sql(
        """
        SELECT 
            COALESCE(SUM(CASE WHEN transaction_type = 'buy'  THEN total_eur + fee_eur ELSE 0 END),0) AS spent,
            COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN total_eur - fee_eur ELSE 0 END),0) AS received
        FROM t_transactions
        """,
        engine,
    )
    total_credit = float(df_cap.iloc[0]["total_credit"]) if not df_cap.empty else 0.0
    total_debit = float(df_cap.iloc[0]["total_debit"]) if not df_cap.empty else 0.0
    spent = float(df_tx.iloc[0]["spent"]) if not df_tx.empty else 0.0
    received = float(df_tx.iloc[0]["received"]) if not df_tx.empty else 0.0
    available_cash = total_credit - total_debit - spent + received
    
    st.metric("💶 Saldo disponível (EUR)", f"€{available_cash:,.2f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        asset = st.selectbox("Ativo", list(asset_options.keys()), key="tx_v2_asset")
        form_data['asset_id'] = asset_options[asset]
        
        # Guardar símbolo selecionado para usar no botão de preço
        selected_symbol = asset.split(' - ')[0]
        
        quantity = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_qty")
        form_data['quantity'] = quantity
    
    with col2:
        # Campo de preço com valor do session_state (para manter após usar preço de mercado)
        price_eur = st.number_input(
            "Preço Unitário (EUR)", 
            min_value=0.0, 
            step=0.000001, 
            format="%.6f", 
            value=float(st.session_state.get("tx_v2_price_value", 0.0)),
            key="tx_v2_price"
        )
        st.session_state["tx_v2_price_value"] = price_eur
        form_data['price_eur'] = price_eur
        
        # Botão e último preço lado a lado
        col_btn, col_info = st.columns([1, 1])
        
        with col_btn:
            if st.button("🔄 Usar preço de mercado", use_container_width=True, key="btn_market_price_v2"):
                # Buscar preço histórico para a data selecionada
                target_date = form_data.get('transaction_date', datetime.now()).date()
                
                try:
                    from services.snapshots import get_historical_price
                    
                    # Buscar preço histórico da data selecionada
                    price = get_historical_price(int(form_data['asset_id']), target_date)
                    
                    if price and price > 0:
                        st.session_state["tx_v2_price_value"] = round(price, 6)
                        st.session_state["tx_v2_market_price"] = price
                        st.session_state["tx_v2_market_price_date"] = target_date
                        st.success(f"✅ Preço aplicado: €{price:,.6f} ({target_date})")
                        st.rerun()
                    else:
                        st.warning(f"Preço de mercado não disponível para {target_date}.")
                except Exception as e:
                    st.error(f"❌ Erro ao obter preço: {e}")
        
        with col_info:
            # Mostrar último preço de mercado (se disponível)
            market_price = st.session_state.get("tx_v2_market_price")
            market_date = st.session_state.get("tx_v2_market_price_date")
            if market_price:
                date_str = f" ({market_date})" if market_date else ""
                st.markdown(f"**💡 Último:**  \n€{market_price:,.6f}{date_str}")
            else:
                st.markdown("**💡 Último:**  \n—")
        
        fee_eur = st.number_input("Taxa (EUR)", min_value=0.0, step=0.01, format="%.2f", key="tx_v2_fee")
        form_data['fee_eur'] = fee_eur
    
    total = quantity * price_eur
    st.metric("💵 Total", f"€{total:,.2f}")
    if fee_eur > 0:
        if tx_type == 'buy':
            st.caption(f"Custo total (com taxa): €{total + fee_eur:,.2f}")
        else:
            st.caption(f"Recebido (após taxa): €{total - fee_eur:,.2f}")
    
    st.markdown("#### 📍 Onde?")
    col1, col2 = st.columns(2)
    
    with col1:
        # Optimized: Use pandas to_dict() instead of iterrows()
        exchange_opts = dict(zip(df_exchanges['name'], df_exchanges['exchange_id'].astype(int)))
        exchange_opts["Não especificar"] = None
        exchange = st.selectbox("Exchange", list(exchange_opts.keys()), key="tx_v2_exch")
        form_data['exchange_id'] = exchange_opts[exchange]
    
    with col2:
        if form_data['exchange_id']:
            acc = st.selectbox("Conta", list(account_options.keys()), key="tx_v2_acc")
            form_data['account_id'] = account_options[acc]
        else:
            form_data['account_id'] = None

    # Saldo por conta (EUR)
    if form_data.get('account_id'):
        eur_id = form_data.get('eur_asset_id')
        acc_eur_available = _get_account_asset_balance(engine, int(form_data['account_id']), int(eur_id))
        st.caption(f"🧾 Disponível nesta conta (EUR): **€{acc_eur_available:,.2f}**")


def _render_swap_fields(form_data, asset_options, account_options, df_exchanges, engine):
    """Renderiza campos para swap."""
    st.markdown("#### 🔄 Swap (Cripto ↔ Cripto)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Dás (From)**")
        from_asset = st.selectbox("Ativo origem", list(asset_options.keys()), key="tx_v2_from_asset")
        form_data['from_asset_id'] = asset_options[from_asset]
        
        from_qty = st.number_input("Quantidade origem", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_from_qty")
        form_data['from_quantity'] = from_qty
    
    with col2:
        st.markdown("**Recebes (To)**")
        to_asset = st.selectbox("Ativo destino", list(asset_options.keys()), key="tx_v2_to_asset")
        form_data['to_asset_id'] = asset_options[to_asset]
        
        to_qty = st.number_input("Quantidade destino", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_to_qty")
        form_data['to_quantity'] = to_qty
    
    st.markdown("#### 💸 Taxa (Fee)")
    col1, col2 = st.columns(2)
    
    with col1:
        fee_asset = st.selectbox("Asset da taxa", list(asset_options.keys()), key="tx_v2_fee_asset")
        form_data['fee_asset_id'] = asset_options[fee_asset]
    
    with col2:
        fee_qty = st.number_input("Quantidade de taxa", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_fee_qty")
        form_data['fee_quantity'] = fee_qty
    
    st.markdown("#### 📍 Onde?")
    acc = st.selectbox("Conta/DEX", list(account_options.keys()), key="tx_v2_swap_acc")
    form_data['account_id'] = account_options[acc]

    # Mostrar saldo disponível do ativo de origem (e eventualmente do asset da taxa se diferente)
    try:
        from_asset_id = form_data.get('from_asset_id')
        if from_asset_id and form_data.get('account_id'):
            available_from = _get_account_asset_balance(engine, int(form_data['account_id']), int(from_asset_id))
            # Mostrar
            st.caption(f"🧾 Disponível nesta conta ({list(asset_options.keys())[list(asset_options.values()).index(from_asset_id)]}): **{available_from:.8f}**")
        fee_asset_id = form_data.get('fee_asset_id')
        if fee_asset_id and fee_asset_id != from_asset_id and form_data.get('account_id'):
            available_fee = _get_account_asset_balance(engine, int(form_data['account_id']), int(fee_asset_id))
            st.caption(f"🧾 Disponível para taxa ({list(asset_options.keys())[list(asset_options.values()).index(fee_asset_id)]}): **{available_fee:.8f}**")
    except Exception:
        pass


def _render_transfer_fields(form_data, asset_options, account_options, engine):
    """Renderiza campos para transfer."""
    st.markdown("#### ➡️ Transferência entre Contas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        asset = st.selectbox("Ativo", list(asset_options.keys()), key="tx_v2_transfer_asset")
        form_data['asset_id'] = asset_options[asset]
        
        quantity = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_transfer_qty")
        form_data['quantity'] = quantity
    
    with col2:
        fee_qty = st.number_input("Taxa de rede (mesmo asset)", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_transfer_fee")
        form_data['fee_quantity'] = fee_qty
        form_data['fee_asset_id'] = form_data.get('asset_id')
    
    st.markdown("#### 🔄 De / Para")
    col1, col2 = st.columns(2)
    
    with col1:
        from_acc = st.selectbox("De (Origem)", list(account_options.keys()), key="tx_v2_transfer_from")
        form_data['from_account_id'] = account_options[from_acc]
    
    with col2:
        to_acc = st.selectbox("Para (Destino)", list(account_options.keys()), key="tx_v2_transfer_to")
        form_data['to_account_id'] = account_options[to_acc]
    
    # Mostrar saldo disponível do ativo na conta de origem
    try:
        if form_data.get('from_account_id') and form_data.get('asset_id'):
            available_from = _get_account_asset_balance(engine, int(form_data['from_account_id']), int(form_data['asset_id']))
            st.caption(f"🧾 Disponível na conta de origem ({asset.split(' - ')[0]}): **{available_from:.8f}**")
    except Exception:
        pass

    st.metric("📦 Quantidade recebida", f"{quantity - fee_qty:.8f}")


def _render_stake_fields(tx_type, form_data, asset_options, account_options):
    """Renderiza campos para stake/unstake."""
    label = "🔒 Stake" if tx_type == 'stake' else "🔓 Unstake"
    st.markdown(f"#### {label}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        asset = st.selectbox("Ativo", list(asset_options.keys()), key=f"tx_v2_{tx_type}_asset")
        form_data['asset_id'] = asset_options[asset]
    
    with col2:
        quantity = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key=f"tx_v2_{tx_type}_qty")
        form_data['quantity'] = quantity
    
    st.markdown("#### 🔄 De / Para")
    col1, col2 = st.columns(2)
    
    with col1:
        from_acc = st.selectbox("De (Origem)", list(account_options.keys()), key=f"tx_v2_{tx_type}_from")
        form_data['from_account_id'] = account_options[from_acc]
    
    with col2:
        to_acc = st.selectbox("Para (Destino - Staking Pool)", list(account_options.keys()), key=f"tx_v2_{tx_type}_to")
        form_data['to_account_id'] = account_options[to_acc]


def _render_reward_fields(form_data, asset_options, account_options):
    """Renderiza campos para reward."""
    st.markdown("#### 🎁 Recompensa Recebida")
    
    col1, col2 = st.columns(2)
    
    with col1:
        asset = st.selectbox("Ativo", list(asset_options.keys()), key="tx_v2_reward_asset")
        form_data['asset_id'] = asset_options[asset]
    
    with col2:
        quantity = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_reward_qty")
        form_data['quantity'] = quantity
    
    st.markdown("#### 📍 Onde foi recebida?")
    to_acc = st.selectbox("Conta de destino", list(account_options.keys()), key="tx_v2_reward_to")
    form_data['to_account_id'] = account_options[to_acc]


def _render_defi_fields(tx_type, form_data, asset_options, account_options):
    """Renderiza campos para lend/borrow/repay."""
    labels = {'lend': '🏦 Lend', 'borrow': '🏦 Borrow', 'repay': '💳 Repay'}
    st.markdown(f"#### {labels[tx_type]}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        asset = st.selectbox("Ativo", list(asset_options.keys()), key=f"tx_v2_{tx_type}_asset")
        form_data['asset_id'] = asset_options[asset]
    
    with col2:
        quantity = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key=f"tx_v2_{tx_type}_qty")
        form_data['quantity'] = quantity
    
    if tx_type in ['lend', 'repay']:
        st.markdown("#### 🔄 De / Para")
        col1, col2 = st.columns(2)
        with col1:
            from_acc = st.selectbox("De (Origem)", list(account_options.keys()), key=f"tx_v2_{tx_type}_from")
            form_data['from_account_id'] = account_options[from_acc]
        if tx_type == 'lend':
            with col2:
                to_acc = st.selectbox("Para (Protocolo DeFi)", list(account_options.keys()), key=f"tx_v2_{tx_type}_to")
                form_data['to_account_id'] = account_options[to_acc]
    else:  # borrow
        to_acc = st.selectbox("Para (Recebido em)", list(account_options.keys()), key=f"tx_v2_{tx_type}_to")
        form_data['to_account_id'] = account_options[to_acc]
    
    # Fee (gas)
    st.markdown("#### 💸 Taxa (Gas)")
    col1, col2 = st.columns(2)
    with col1:
        fee_asset = st.selectbox("Asset da taxa", list(asset_options.keys()), key=f"tx_v2_{tx_type}_fee_asset")
        form_data['fee_asset_id'] = asset_options[fee_asset]
    with col2:
        fee_qty = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key=f"tx_v2_{tx_type}_fee_qty")
        form_data['fee_quantity'] = fee_qty


def _render_liquidate_fields(form_data, asset_options, account_options):
    """Renderiza campos para liquidate."""
    st.markdown("#### ⚠️ Liquidação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        asset = st.selectbox("Ativo perdido", list(asset_options.keys()), key="tx_v2_liq_asset")
        form_data['asset_id'] = asset_options[asset]
    
    with col2:
        quantity = st.number_input("Quantidade", min_value=0.0, step=0.00000001, format="%.8f", key="tx_v2_liq_qty")
        form_data['quantity'] = quantity
    
    st.markdown("#### 📍 De onde?")
    from_acc = st.selectbox("Conta/Protocolo", list(account_options.keys()), key="tx_v2_liq_from")
    form_data['from_account_id'] = account_options[from_acc]


def _save_transaction(engine, params):
    """Salva a transação na BD."""
    # Construir SQL dinamicamente baseado nas chaves presentes
    columns = []
    values_placeholders = []
    
    for key in params.keys():
        if params[key] is not None:
            columns.append(key)
            values_placeholders.append(f":{key}")
    
    sql_insert = f"""
        INSERT INTO t_transactions ({', '.join(columns)})
        VALUES ({', '.join(values_placeholders)})
        RETURNING transaction_id
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(sql_insert), params)
        tx_id = result.scalar_one()
        return tx_id


def _get_account_asset_balance(engine, account_id: int, asset_id: int) -> float:
    """Calcula o saldo atual de um asset numa conta específica (per-account).
    Baseado nos deltas do modelo V2: inflows - outflows - fees.
    """
    if not account_id or not asset_id:
        return 0.0
    sql = text(
        """
        WITH inflows AS (
            SELECT COALESCE(t.to_account_id, t.account_id, -1) AS account_id, t.to_asset_id AS asset_id, SUM(t.to_quantity) AS qty
            FROM t_transactions t
            WHERE t.to_asset_id = :asset_id AND COALESCE(t.to_account_id, t.account_id, -1) = :account_id
            GROUP BY 1,2
        ), outflows AS (
            SELECT COALESCE(t.from_account_id, t.account_id, -1) AS account_id, t.from_asset_id AS asset_id, SUM(t.from_quantity) AS qty
            FROM t_transactions t
            WHERE t.from_asset_id = :asset_id AND COALESCE(t.from_account_id, t.account_id, -1) = :account_id
            GROUP BY 1,2
        ), fees AS (
            SELECT COALESCE(t.from_account_id, t.account_id, -1) AS account_id, t.fee_asset_id AS asset_id, SUM(t.fee_quantity) AS qty
            FROM t_transactions t
            WHERE t.fee_asset_id = :asset_id AND t.fee_quantity > 0 AND COALESCE(t.from_account_id, t.account_id, -1) = :account_id
            GROUP BY 1,2
        )
        SELECT 
            COALESCE((SELECT SUM(qty) FROM inflows),0) 
          - COALESCE((SELECT SUM(qty) FROM outflows),0)
          - COALESCE((SELECT SUM(qty) FROM fees),0) AS balance
        """
    )
    with engine.begin() as conn:
        row = conn.execute(sql, {"account_id": int(account_id), "asset_id": int(asset_id)}).first()
        return float(row[0]) if row and row[0] is not None else 0.0
