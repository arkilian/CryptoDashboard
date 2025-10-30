import streamlit as st
import streamlit.components.v1 as components
from services.coingecko import CoinGeckoService
from auth.session_manager import require_auth
from config import WATCHED_COINS

@require_auth
def show():
    st.title("📊 Cotações")
    
    coingecko = CoinGeckoService()
    
    # Widget CoinGecko no topo
    coin_ids_str = ",".join(WATCHED_COINS)
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
            prices = coingecko.get_prices(WATCHED_COINS, ['eur', 'usd'])
            if prices:
                st.success("✅ Preços atualizados com sucesso!")
                st.json(prices)
            else:
                st.error("❌ Erro ao obter preços do CoinGecko")
        
        with tab2:
            # Seletor de moeda para gráfico
            selected_coin = st.selectbox(
                "Escolha uma moeda para ver o gráfico", 
                WATCHED_COINS
            )
            
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
                        mode='lines',
                        name='Preço'
                    ))
                    
                    fig.update_layout(
                        title=f'Preço de {selected_coin.upper()}',
                        xaxis_title='Data',
                        yaxis_title='Preço (USD)'
                    )
                    
                    st.plotly_chart(fig)
                    
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
        st.markdown("""
        Esta lista inclui:
        - **Bitcoin (BTC)**: A primeira e mais conhecida criptomoeda
        - **Cardano (ADA)**: Plataforma blockchain proof-of-stake
        - **Solana (SOL)**: Blockchain de alta performance
        - **Sui (SUI)**: Nova plataforma blockchain
        - **Tokens DeFi**: Vários tokens do ecossistema Cardano
        
        Os preços são atualizados em tempo real via API do CoinGecko.
        """)