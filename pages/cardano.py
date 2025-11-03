"""
Página Cardano - Visualização de endereços, saldos, tokens e transações.
"""
import streamlit as st
import pandas as pd
from services.cardano_api import CardanoScanAPI
from datetime import datetime

# Configuração da API (em produção, mover para variáveis de ambiente)
API_KEY = "771d0a8a-9978-40b4-b60b-3fa873e5209d"
DEFAULT_ADDRESS = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"


def show():
    """Página principal do Cardano."""
    
    # Cabeçalho
    st.markdown("""
        <div class="page-header">
            <h1>🔷 Cardano Blockchain Explorer</h1>
            <p>Consulte informações de endereços Cardano em tempo real</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Inicializar API
    api = CardanoScanAPI(API_KEY)
    
    # Input do endereço
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
    
    # Salvar endereço no session state
    if address:
        st.session_state["cardano_address"] = address
    
    # Validação básica
    if not address or not address.startswith("addr1"):
        st.warning("⚠️ Por favor, insira um endereço Cardano válido (deve começar com 'addr1')")
        return
    
    # Tabs para organizar informações
    tab1, tab2, tab3 = st.tabs(["💰 Saldo e Tokens", "📜 Transações", "ℹ️ Informações"])
    
    # TAB 1: SALDO E TOKENS
    with tab1:
        show_balance_tab(api, address)
    
    # TAB 2: TRANSAÇÕES
    with tab2:
        show_transactions_tab(api, address)
    
    # TAB 3: INFORMAÇÕES
    with tab3:
        show_info_tab(address)


def show_balance_tab(api: CardanoScanAPI, address: str):
    """Mostra saldo e tokens do endereço."""
    
    with st.spinner("🔍 A consultar saldo..."):
        balance_data, error = api.get_balance(address)
    
    if error:
        st.error(f"❌ Erro ao consultar saldo: {error}")
        return
    
    if not balance_data:
        st.info("ℹ️ Nenhum dado encontrado para este endereço")
        return
    
    # Saldo ADA
    st.markdown("### 💎 Saldo ADA")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Saldo em ADA",
            f"{balance_data['ada']:,.6f} ₳",
            help="1 ADA = 1.000.000 lovelace"
        )
    
    with col2:
        st.metric(
            "Saldo em Lovelace",
            f"{balance_data['lovelace']:,}",
            help="Menor unidade do ADA"
        )
    
    with col3:
        # Calcular valor aproximado em EUR (exemplo com cotação fixa)
        # Em produção, buscar cotação real
        ada_price_eur = 0.35  # Exemplo
        value_eur = balance_data['ada'] * ada_price_eur
        st.metric(
            "Valor Aprox. (EUR)",
            f"€{value_eur:,.2f}",
            help=f"Baseado em 1 ADA ≈ €{ada_price_eur}"
        )
    
    st.markdown("---")
    
    # Tokens Nativos
    tokens = balance_data.get('tokens', [])
    
    if not tokens:
        st.info("ℹ️ Este endereço não possui tokens nativos")
    else:
        st.markdown(f"### 🪙 Tokens Nativos ({len(tokens)})")
        
        # Criar DataFrame dos tokens
        token_list = []
        for token in tokens:
            token_name = api.get_token_name(token)
            quantity = int(token.get("quantity", token.get("amount", 0)))
            policy_id = token.get("policyId", token.get("policy", "N/A"))
            fingerprint = token.get("fingerprint", "N/A")
            
            token_list.append({
                "Token": token_name,
                "Quantidade": f"{quantity:,}",
                "Policy ID": policy_id[:16] + "..." if len(policy_id) > 16 else policy_id,
                "Fingerprint": fingerprint[:20] + "..." if len(fingerprint) > 20 else fingerprint
            })
        
        df_tokens = pd.DataFrame(token_list)
        
        # Mostrar tabela com estilo
        st.dataframe(
            df_tokens,
            use_container_width=True,
            hide_index=True,
            height=min(400, len(token_list) * 40 + 40)
        )
        
        # Permitir exportar
        csv = df_tokens.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exportar Tokens (CSV)",
            csv,
            "cardano_tokens.csv",
            "text/csv",
            key='download-tokens-csv'
        )


def show_transactions_tab(api: CardanoScanAPI, address: str):
    """Mostra histórico de transações."""
    
    st.markdown("### 📜 Histórico de Transações")
    
    # Opções de filtro
    col1, col2 = st.columns([2, 1])
    with col1:
        max_pages = st.slider(
            "Número de páginas a carregar",
            min_value=1,
            max_value=20,
            value=5,
            help="Cada página contém aproximadamente 20 transações"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_button = st.button("📥 Carregar Transações", use_container_width=True, type="primary")
    
    if load_button or "cardano_transactions" in st.session_state:
        with st.spinner(f"🔍 A carregar transações (até {max_pages} páginas)..."):
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
        
        # Estatísticas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Transações", len(transactions))
        
        with col2:
            total_fees = sum(tx['fees'] for tx in transactions)
            st.metric("Taxas Totais", f"{total_fees:.4f} ₳")
        
        with col3:
            confirmed = sum(1 for tx in transactions if "✅" in tx['status'])
            st.metric("Confirmadas", confirmed)
        
        with col4:
            if transactions:
                latest = api.format_timestamp(transactions[0]['timestamp'])
                st.metric("Última Transação", latest)
        
        st.markdown("---")
        
        # Lista de transações
        for i, tx in enumerate(transactions[:50]):  # Limitar a 50 para não sobrecarregar
            with st.expander(
                f"🔖 {tx['hash'][:16]}... | {api.format_timestamp(tx['timestamp'])} | {tx['status']}",
                expanded=(i < 3)  # Expandir as 3 primeiras
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Hash:** `{tx['hash']}`")
                    st.markdown(f"**Data:** {api.format_timestamp(tx['timestamp'])}")
                    st.markdown(f"**Taxa:** {tx['fees']:.6f} ₳")
                
                with col2:
                    st.markdown(f"**Bloco:** {tx['block_height']:,}")
                    st.markdown(f"**Status:** {tx['status']}")
                    
                    # Link para o explorador
                    st.markdown(f"[🔗 Ver no CardanoScan](https://cardanoscan.io/transaction/{tx['hash']})")
                
                # Inputs
                if tx['inputs']:
                    st.markdown("**📥 Inputs:**")
                    for inp in tx['inputs'][:3]:  # Mostrar apenas os primeiros 3
                        value_ada = int(inp.get('value', 0)) / 1_000_000
                        addr = inp.get('address', 'N/A')
                        st.markdown(f"- `{addr[:20]}...` → {value_ada:.6f} ₳")
                
                # Outputs
                if tx['outputs']:
                    st.markdown("**📤 Outputs:**")
                    for out in tx['outputs'][:3]:  # Mostrar apenas os primeiros 3
                        value_ada = int(out.get('value', 0)) / 1_000_000
                        addr = out.get('address', 'N/A')
                        st.markdown(f"- `{addr[:20]}...` ← {value_ada:.6f} ₳")
                
                # Metadata
                if tx['metadata']:
                    st.markdown("**📋 Metadata:**")
                    metadata = tx['metadata']
                    if isinstance(metadata, dict) and 'data' in metadata:
                        for item in metadata['data']:
                            st.markdown(f"- Label {item.get('label')}: {item.get('value', 'N/A')}")
        
        # Mostrar alerta se houver mais transações
        if len(transactions) > 50:
            st.info(f"ℹ️ Mostrando as primeiras 50 de {len(transactions)} transações. Aumente o número de páginas para ver mais.")
        
        # Exportar transações
        if transactions:
            # Criar DataFrame simplificado
            tx_list = []
            for tx in transactions:
                tx_list.append({
                    "Hash": tx['hash'],
                    "Data": api.format_timestamp(tx['timestamp']),
                    "Taxa (ADA)": f"{tx['fees']:.6f}",
                    "Bloco": tx['block_height'],
                    "Status": tx['status']
                })
            
            df_tx = pd.DataFrame(tx_list)
            csv = df_tx.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "📥 Exportar Transações (CSV)",
                csv,
                "cardano_transactions.csv",
                "text/csv",
                key='download-transactions-csv'
            )


def show_info_tab(address: str):
    """Mostra informações sobre o endereço e a API."""
    
    st.markdown("### ℹ️ Informações do Endereço")
    
    # Informações do endereço
    st.code(address, language="text")
    
    # QR Code seria interessante aqui (requer biblioteca qrcode)
    
    st.markdown("---")
    
    st.markdown("""
    ### 📚 Sobre a API CardanoScan
    
    Esta página utiliza a **CardanoScan API** para consultar informações da blockchain Cardano em tempo real.
    
    **Funcionalidades disponíveis:**
    - ✅ Consulta de saldo em ADA e Lovelace
    - ✅ Listagem de tokens nativos (NFTs e FTs)
    - ✅ Histórico completo de transações
    - ✅ Detalhes de cada transação (inputs, outputs, metadata)
    - ✅ Exportação de dados em CSV
    
    **Limitações:**
    - Taxa de requisições limitada pela API
    - Histórico de transações paginado (20 por página)
    - Endereços devem estar no formato bech32 (addr1...)
    
    **Links úteis:**
    - [CardanoScan Explorer](https://cardanoscan.io)
    - [Documentação da API](https://docs.cardanoscan.io)
    - [Cardano Official](https://cardano.org)
    """)
    
    # Informações técnicas
    st.markdown("---")
    st.markdown("### 🔧 Informações Técnicas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Formato do Endereço:**
        - Bech32 (addr1...)
        - Mainnet Cardano
        
        **Unidades:**
        - 1 ADA = 1.000.000 lovelace
        - 1 lovelace = 0.000001 ADA
        """)
    
    with col2:
        st.markdown("""
        **API Endpoint:**
        - Base URL: api.cardanoscan.io
        - Versão: v1
        - Protocolo: HTTPS
        
        **Status:** 🟢 Conectado
        """)
