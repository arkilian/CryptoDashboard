import streamlit as st
import pandas as pd
from services.cardano_api import CardanoScanAPI
from datetime import datetime

API_KEY = "771d0a8a-9978-40b4-b60b-3fa873e5209d"
DEFAULT_ADDRESS = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"

def show():
    """Pagina principal do Cardano."""
    
    st.title("🔷 Cardano Blockchain Explorer")
    st.markdown("Consulte informações de endereços Cardano em tempo real")
    
    api = CardanoScanAPI(API_KEY)
    col1, col2 = st.columns([3, 1])
    with col1:
        address = st.text_input(
            "📍 Endereço Cardano (formato bech32)",
            value=st.session_state.get("cardano_address", DEFAULT_ADDRESS),
            help="Insira um endereço Cardano válido começando com 'addr1'"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Atualizar", use_container_width=True, type="primary")
    if address:
        st.session_state["cardano_address"] = address
    if not address or not address.startswith("addr1"):
        st.warning("⚠️ Por favor, insira um endereço Cardano válido (deve começar com 'addr1')")
        return
    tab1, tab2, tab3 = st.tabs(["💰 Saldo e Tokens", "📜 Transações", "ℹ️ Informações"])
    with tab1:
        show_balance_tab(api, address)
    with tab2:
        show_transactions_tab(api, address)
    with tab3:
        show_info_tab(address)

def show_balance_tab(api, address):
    with st.spinner("🔍 A consultar saldo..."):
        balance_data, error = api.get_balance(address)
    if error:
        st.error(f"❌ Erro ao consultar saldo: {error}")
        return
    if not balance_data:
        st.info("ℹ️ Nenhum dado encontrado para este endereço")
        return
    st.markdown("### 💎 Saldo ADA")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Saldo em ADA", f"{balance_data['ada']:,.6f} ₳", help="1 ADA = 1.000.000 lovelace")
    with col2:
        st.metric("Saldo em Lovelace", f"{balance_data['lovelace']:,}", help="Menor unidade do ADA")
    with col3:
        ada_price = 0.35
        value_eur = balance_data['ada'] * ada_price
        st.metric("Valor Aprox. (EUR)", f"€{value_eur:,.2f}", help=f"Baseado em 1 ADA ≈ €{ada_price}")
    st.markdown("---")
    tokens = balance_data.get('tokens', [])
    if not tokens:
        st.info("ℹ️ Este endereço não possui tokens nativos")
    else:
        st.markdown(f"### 🪙 Tokens Nativos ({len(tokens)})")
        token_list = []
        for token in tokens:
            token_name = api.get_token_name(token)
            quantity = int(token.get("quantity", token.get("amount", 0)))
            policy_id = token.get("policyId", token.get("policy", "N/A"))
            token_list.append({"Token": token_name, "Quantidade": f"{quantity:,}", "Policy ID": policy_id[:16] + "..." if len(policy_id) > 16 else policy_id})
        df_tokens = pd.DataFrame(token_list)
        st.dataframe(df_tokens, use_container_width=True, hide_index=True)
        csv = df_tokens.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar Tokens (CSV)", csv, "cardano_tokens.csv", "text/csv", key='download-tokens')

def show_transactions_tab(api, address):
    st.markdown("### 📜 Atividade")
    col1, col2 = st.columns([2, 1])
    with col1:
        max_pages = st.slider("📄 Número de páginas a carregar", 1, 20, 5, help="Cada página contém ~20 transações")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_button = st.button("📥 Carregar Transações", use_container_width=True, type="primary")
    
    if load_button or "cardano_transactions" in st.session_state:
        with st.spinner("Carregando..."):
            if load_button:
                transactions, error = api.get_transactions(address, max_pages)
                st.session_state["cardano_transactions"] = transactions
                st.session_state["cardano_transactions_error"] = error
            else:
                transactions = st.session_state.get("cardano_transactions")
                error = st.session_state.get("cardano_transactions_error")
        
        if error:
            st.error(f"❌ Erro ao carregar transações: {error}")
            return
        if not transactions:
            st.info("ℹ️ Nenhuma transação encontrada")
            return
        
        # Agrupar por data
        from collections import defaultdict
        grouped = defaultdict(list)
        for tx in transactions[:50]:
            ts = tx['timestamp']
            if isinstance(ts, str):
                # Se for ISO format (2025-03-10T07:56:49.000Z)
                if 'T' in ts:
                    timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                else:
                    ts = int(ts)
                    timestamp = datetime.fromtimestamp(ts)
            else:
                timestamp = datetime.fromtimestamp(ts)
            date_key = timestamp.strftime("%b %d, %Y")
            grouped[date_key].append(tx)
        
        # Mostrar agrupado por data (ordem inversa - mais recentes primeiro)
        for date_str in sorted(grouped.keys(), reverse=True, key=lambda x: datetime.strptime(x, "%b %d, %Y")):
            txs = grouped[date_str]
            st.markdown(f"<div style='color: #6b7280; font-size: 0.9rem; margin: 1.5rem 0 0.75rem 0; font-weight: 500;'>{date_str}</div>", unsafe_allow_html=True)
            
            # Inverter ordem das transações dentro do dia (mais recentes primeiro)
            for tx in reversed(txs):
                analysis = api.analyze_transaction(tx, address)
                
                # Definir icone e cor
                if analysis['type'] == 'sent':
                    icon = "↗"
                    color = "#ef4444"
                    amount_color = "#ef4444"
                    amount_str = f"-{abs(analysis['net_change_ada']):.1f}"
                elif analysis['type'] == 'received':
                    icon = "↙"
                    color = "#10b981"
                    amount_color = "#10b981"
                    amount_str = f"{analysis['net_change_ada']:.1f}"
                else:
                    icon = "↔"
                    color = "#06b6d4"
                    amount_color = "#94a3b8"
                    amount_str = f"{analysis['net_change_ada']:.1f}"
                
                # Linha de tipo (Enviado/Recebido/Contrato)
                tipo_display = analysis['description'] if analysis['type'] == 'contract' else ("Enviado" if analysis['type'] == 'sent' else "Recebido")
                subtipo = ""
                if analysis['type'] == 'contract':
                    subtipo = f"<div style='color: #9ca3af; font-size: 0.85rem;'>{tipo_display}</div>"
                
                # Hash da transação (primeiros 8 caracteres)
                tx_hash = tx.get('hash', '')
                hash_short = f"{tx_hash[:8]}...{tx_hash[-8:]}" if len(tx_hash) > 16 else tx_hash
                
                # Links para explorers
                cardanoscan_link = f"https://cardanoscan.io/transaction/{tx_hash}"
                
                # Mostrar tokens se houver
                token_html = ""
                if analysis['net_tokens']:
                    for token_name, qty in list(analysis['net_tokens'].items())[:1]:
                        if qty != 0:
                            token_sign = "+" if qty > 0 else ""
                            token_color = "#10b981" if qty > 0 else "#ef4444"
                            token_html = f"<div style='color: {token_color}; font-size: 0.85rem; margin-top: 0.15rem;'>{token_sign}{qty:.1f} {token_name}</div>"
                            break
                
                # Card com mais informações - construir em partes
                fees_display = f"{analysis['fees_ada']:.4f}"
                
                card_html = f'<div style="background: rgba(30, 41, 59, 0.4); border-radius: 0.75rem; padding: 1rem; margin-bottom: 0.5rem;"><div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;"><div style="width: 40px; height: 40px; border-radius: 50%; background: rgba(55, 65, 81, 0.8); display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;">{icon}</div><div style="flex: 1; min-width: 0;"><div style="font-size: 1rem; font-weight: 600; color: #f3f4f6; margin-bottom: 0.15rem;">{tipo_display}</div>{subtipo}<div style="color: #9ca3af; font-size: 0.8rem;">Taxa: {fees_display} ₳</div>{token_html}</div><div style="text-align: right; flex-shrink: 0;"><div style="font-size: 1.1rem; font-weight: 700; color: {amount_color};">{amount_str} ₳</div></div></div><div style="border-top: 1px solid rgba(75, 85, 99, 0.3); padding-top: 0.5rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;"><div style="color: #6b7280;"><span style="font-family: monospace;">{hash_short}</span></div><div><a href="{cardanoscan_link}" target="_blank" style="color: #3b82f6; text-decoration: none; margin-left: 1rem;">🔍 CardanoScan</a></div></div></div>'
                
                st.markdown(card_html, unsafe_allow_html=True)
        
        if len(transactions) > 50:
            st.info(f"ℹ️ Mostrando as primeiras 50 de {len(transactions)} transações. Aumente o número de páginas para ver mais.")

def show_info_tab(address):
    st.markdown("### ℹ️ Informações do Endereço")
    st.code(address, language="text")
    
    # Link para o explorer
    st.markdown(f"🔗 [Ver no CardanoScan](https://cardanoscan.io/address/{address})")
    
    st.markdown("---")
    
    st.markdown("""
    ### 📚 Sobre a API CardanoScan
    
    Esta página utiliza a **CardanoScan API** para consultar informações da blockchain Cardano em tempo real.
    
    **Funcionalidades disponíveis:**
    - ✅ Consulta de saldo em ADA e Lovelace
    - ✅ Listagem de tokens nativos (NFTs e FTs)
    - ✅ Histórico completo de transações
    - ✅ Análise automática (enviado/recebido)
    - ✅ Exportação de dados em CSV
    - ✅ Links diretos para explorers
    
    **Limitações:**
    - ⚠️ Taxa de requisições limitada pela API
    - ⚠️ Histórico de transações paginado (20 por página)
    - ⚠️ Endereços devem estar no formato bech32 (addr1...)
    
    **Links úteis:**
    - 🌐 [CardanoScan Explorer](https://cardanoscan.io)
    - 📖 [Documentação da API](https://docs.cardanoscan.io)
    - 🔷 [Cardano Official](https://cardano.org)
    """)
    
    st.markdown("---")
    st.markdown("### 🔧 Informações Técnicas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Formato do Endereço:**
        - 🔑 Bech32 (addr1...)
        - 🌐 Mainnet Cardano
        
        **Unidades:**
        - 💰 1 ADA = 1.000.000 lovelace
        - 🪙 1 lovelace = 0.000001 ADA
        """)
    
    with col2:
        st.markdown("""
        **API Endpoint:**
        - 🔗 Base URL: api.cardanoscan.io
        - 📌 Versão: v1
        - 🔒 Protocolo: HTTPS
        
        **Status:** 🟢 Conectado
        """)
