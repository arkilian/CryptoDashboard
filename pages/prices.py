import streamlit as st
import streamlit.components.v1 as components
from services.coingecko import CoinGeckoService
from auth.session_manager import require_auth
from database.connection import get_engine
import pandas as pd
from css.charts import apply_theme

@require_auth
def show():
    st.title("📊 Cotações")
    
    # Buscar ativos da base de dados
    engine = get_engine()
    df_assets = pd.read_sql("""
        SELECT symbol, name, coingecko_id 
        FROM t_assets 
        WHERE coingecko_id IS NOT NULL AND coingecko_id != ''
        ORDER BY symbol
    """, engine)
    
    if df_assets.empty:
        st.warning("⚠️ Nenhum ativo configurado com CoinGecko ID. Adicione ativos na página de Configurações.")
        return
    
    # Extrair lista de CoinGecko IDs e símbolos
    watched_coins = df_assets['coingecko_id'].tolist()
    symbol_map = dict(zip(df_assets['coingecko_id'], df_assets['symbol']))
    
    coingecko = CoinGeckoService()
    
    # Widget CoinGecko no topo
    coin_ids_str = ",".join(watched_coins)
    html_code = f'''
    <div style="margin-bottom: 20px;">
        <script src="https://widgets.coingecko.com/gecko-coin-price-marquee-widget.js"></script>
        <gecko-coin-price-marquee-widget 
            locale="en" 
            dark-mode="true" 
            outlined="true" 
            coin-ids="{coin_ids_str}" 
            initial-currency="usd">
        </gecko-coin-price-marquee-widget>
    </div>
    '''
    components.html(html_code, height=60)

    # Criar duas colunas
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Lista detalhada de moedas
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
        components.html(html_code, height=800)

    with col2:
        # Tabs para diferentes visualizações
        tab1, tab2 = st.tabs(["💰 Preços", "📈 Gráficos"])
        
        with tab1:
            # Obter preços em EUR e USD
            prices = coingecko.get_prices(watched_coins, ['eur', 'usd'])
            if prices:
                st.success(f"✅ Preços atualizados para {len(prices)} ativos!")
                
                # Criar tabela formatada com símbolos
                price_data = []
                for coin_id, price_info in prices.items():
                    symbol = symbol_map.get(coin_id, coin_id.upper())
                    price_data.append({
                        "Símbolo": symbol,
                        "Nome": coin_id.replace('-', ' ').title(),
                        "EUR": f"€{price_info.get('eur', 0):,.4f}" if price_info.get('eur') else "N/A",
                        "USD": f"${price_info.get('usd', 0):,.4f}" if price_info.get('usd') else "N/A"
                    })
                
                df_prices = pd.DataFrame(price_data)
                st.dataframe(df_prices, use_container_width=True, hide_index=True)
            else:
                st.error("❌ Erro ao obter preços do CoinGecko")
        
        with tab2:
            # Seletor de moeda para gráfico
            coin_options = {f"{symbol_map.get(cid, cid.upper())} - {cid.replace('-', ' ').title()}": cid 
                          for cid in watched_coins}
            
            selected_display = st.selectbox(
                "Escolha uma moeda para ver o gráfico", 
                list(coin_options.keys())
            )
            selected_coin = coin_options[selected_display]
            
            # Seletor de período
            period = st.selectbox(
                "Período", 
                ["24h", "7d", "30d", "90d", "1y", "max"]
            )
            
            try:
                chart_data = coingecko.get_market_chart(selected_coin, period)
                if chart_data:
                    # Criar gráfico com os dados
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    
                    # Adicionar linha de preço
                    fig.add_trace(go.Scatter(
                        x=[x[0] for x in chart_data['prices']],
                        y=[x[1] for x in chart_data['prices']],
                        mode='lines+markers',
                        name='Preço',
                        line=dict(width=3, color='#3b82f6'),
                        marker=dict(size=4)
                    ))
                    
                    fig.update_layout(
                        title=f'Preço de {symbol_map.get(selected_coin, selected_coin.upper())} ({selected_coin})',
                        xaxis_title='Data',
                        yaxis_title='Preço (USD)'
                    )
                    
                    fig = apply_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar estatísticas
                    if len(chart_data['prices']) > 1:
                        prices = [x[1] for x in chart_data['prices']]
                        current_price = prices[-1]
                        start_price = prices[0]
                        change = ((current_price - start_price) / start_price) * 100
                        
                        st.metric(
                            "Variação no período",
                            f"{change:.2f}%",
                            delta=f"{change:.2f}%"
                        )
            except Exception as e:
                st.error(f"Erro ao carregar gráfico: {str(e)}")
    
    # Adicionar informações sobre as moedas
    with st.expander("ℹ️ Sobre as moedas listadas"):
        st.markdown(f"""
        Esta lista contém **{len(watched_coins)} ativos** configurados no sistema.
        
        Os ativos são geridos na página **⚙️ Configurações > 🪙 Ativos**.
        
        Para cada ativo é necessário:
        - **Símbolo**: Código curto (ex: BTC, ADA)
        - **Nome**: Nome completo do ativo
        - **CoinGecko ID**: ID usado pela API do CoinGecko para obter cotações
        
        Os preços são atualizados em tempo real via API do CoinGecko.
        """)
        
        # Mostrar tabela de ativos configurados
        st.dataframe(
            df_assets.rename(columns={
                "symbol": "Símbolo",
                "name": "Nome",
                "coingecko_id": "CoinGecko ID"
            }),
            use_container_width=True,
            hide_index=True
        )