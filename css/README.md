# CSS Module - CryptoDashboard

Módulo centralizado de estilos para o CryptoDashboard.

## Estrutura

```
css/
├── __init__.py      # Exporta todas as funções
├── sidebar.py       # Estilos da sidebar
├── tables.py        # Estilos de tabelas e dataframes
└── charts.py        # Tema e funções para gráficos Plotly
```

## Uso

### Sidebar e Tabelas (CSS)

No arquivo principal (`app.py`):

```python
from css import get_sidebar_style, get_tables_style

# Aplicar estilos
st.markdown(get_sidebar_style(), unsafe_allow_html=True)
st.markdown(get_tables_style(), unsafe_allow_html=True)
```

### Gráficos Plotly

#### Método 1: Aplicar tema a gráfico existente

```python
import plotly.graph_objects as go
from css import apply_theme

fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
fig = apply_theme(fig)  # Aplica o tema escuro
st.plotly_chart(fig)
```

#### Método 2: Usar funções helpers (recomendado)

```python
from css import create_line_chart, create_pie_chart, create_area_chart
import pandas as pd

# Gráfico de linha
df = pd.DataFrame({'data': dates, 'valor': values})
fig = create_line_chart(df, x='data', y='valor', title='Evolução do Portfólio')
st.plotly_chart(fig, use_container_width=True)

# Gráfico de pizza
df_holdings = pd.DataFrame({'ativo': ['BTC', 'ETH', 'ADA'], 'valor': [1000, 500, 300]})
fig = create_pie_chart(df_holdings, values='valor', names='ativo', title='Distribuição')
st.plotly_chart(fig, use_container_width=True)

# Gráfico de área (stacked)
fig = create_area_chart(df, x='data', y=['btc', 'eth', 'ada'], title='Composição')
st.plotly_chart(fig, use_container_width=True)
```

#### Método 3: Usar cores do tema

```python
from css import COLORS, COLOR_PALETTE

# Usar cores individuais
fig.add_trace(go.Scatter(
    marker=dict(color=COLORS['primary'])  # Azul
))

# Usar paleta completa
fig = px.bar(df, color_discrete_sequence=COLOR_PALETTE)
```

## Funções Disponíveis

### Gráficos

- `apply_theme(fig)` - Aplica tema a qualquer gráfico Plotly
- `create_line_chart(df, x, y, ...)` - Gráfico de linha estilizado
- `create_area_chart(df, x, y, ...)` - Gráfico de área estilizado
- `create_pie_chart(df, values, names, ...)` - Gráfico de pizza (donut)
- `create_bar_chart(df, x, y, ...)` - Gráfico de barras estilizado
- `create_scatter_chart(df, x, y, ...)` - Gráfico de dispersão estilizado

### Cores

- `COLORS` - Dict com cores do tema (primary, secondary, success, etc.)
- `COLOR_PALETTE` - Lista de 8 cores para gráficos de múltiplas séries

## Paleta de Cores

```python
COLORS = {
    'primary': '#3b82f6',      # Azul
    'secondary': '#a78bfa',    # Roxo
    'success': '#10b981',      # Verde
    'danger': '#ef4444',       # Vermelho
    'warning': '#f59e0b',      # Laranja
    'info': '#06b6d4',         # Ciano
    'background': '#0f172a',   # Fundo escuro
    'surface': '#1e293b',      # Surface escuro
    'text': '#e2e8f0',         # Texto claro
    'text_secondary': '#94a3b8' # Texto secundário
}
```

## Características dos Gráficos

- **Tema escuro** consistente com a aplicação
- **Fundo semi-transparente** que se integra com o layout
- **Grid sutil** para melhor legibilidade
- **Hover labels** estilizados
- **Legendas** com fundo escuro e borda
- **Margens otimizadas** para melhor uso do espaço
- **Cores vibrantes** mas profissionais
- **Gráficos de pizza** como donut com fatias levemente separadas
- **Linhas** com markers e espessura adequada
- **Barras** com bordas sutis
