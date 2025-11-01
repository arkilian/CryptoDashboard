"""
Tema e configuração para gráficos Plotly no CryptoDashboard
Design moderno e elegante consistente com o tema da aplicação
"""

import plotly.graph_objects as go
import plotly.express as px

# Cores do tema (consistente com o design da aplicação)
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
    'text_secondary': '#94a3b8', # Texto secundário
    'grid': 'rgba(148, 163, 184, 0.1)',  # Grid sutil
    'border': 'rgba(59, 130, 246, 0.3)',  # Bordas
}

# Paleta de cores para gráficos de múltiplas séries
COLOR_PALETTE = [
    '#3b82f6',  # Azul
    '#a78bfa',  # Roxo
    '#10b981',  # Verde
    '#f59e0b',  # Laranja
    '#06b6d4',  # Ciano
    '#ec4899',  # Rosa
    '#8b5cf6',  # Violeta
    '#14b8a6',  # Teal
]

# Layout padrão para todos os gráficos
DEFAULT_LAYOUT = {
    'template': 'plotly_dark',
    'paper_bgcolor': 'rgba(15, 23, 42, 0.6)',
    'plot_bgcolor': 'rgba(30, 41, 59, 0.6)',
    'font': {
        'family': 'system-ui, -apple-system, sans-serif',
        'size': 13,
        'color': COLORS['text']
    },
    'title': {
        'font': {
            'size': 18,
            'color': COLORS['text'],
            'family': 'system-ui, -apple-system, sans-serif'
        },
        'x': 0.5,
        'xanchor': 'center'
    },
    'xaxis': {
        'gridcolor': COLORS['grid'],
        'linecolor': COLORS['border'],
        'color': COLORS['text_secondary'],
        'showgrid': True,
        'zeroline': False
    },
    'yaxis': {
        'gridcolor': COLORS['grid'],
        'linecolor': COLORS['border'],
        'color': COLORS['text_secondary'],
        'showgrid': True,
        'zeroline': False
    },
    'legend': {
        'bgcolor': 'rgba(30, 41, 59, 0.8)',
        'bordercolor': COLORS['border'],
        'borderwidth': 1,
        'font': {
            'color': COLORS['text']
        }
    },
    'hoverlabel': {
        'bgcolor': 'rgba(30, 41, 59, 0.95)',
        'bordercolor': COLORS['border'],
        'font': {
            'color': COLORS['text'],
            'family': 'system-ui, -apple-system, sans-serif'
        }
    },
    'margin': {
        't': 60,
        'b': 60,
        'l': 60,
        'r': 40
    }
}


def apply_theme(fig):
    """
    Aplica o tema escuro elegante a um gráfico Plotly
    
    Args:
        fig: Figura Plotly (go.Figure ou resultado de px)
        
    Returns:
        Figura com tema aplicado
        
    Usage:
        import plotly.graph_objects as go
        from css.charts import apply_theme
        
        fig = go.Figure()
        fig.add_trace(...)
        fig = apply_theme(fig)
        st.plotly_chart(fig)
    """
    fig.update_layout(**DEFAULT_LAYOUT)
    
    # Atualizar cores das traces se ainda não estiverem definidas
    # Nota: Pular esta etapa para gráficos de pizza que já têm cores definidas
    try:
        for i, trace in enumerate(fig.data):
            # Verificar se a trace tem marker e se precisa de cor
            if hasattr(trace, 'marker') and trace.marker:
                # Para gráficos de pizza (Pie), as cores são definidas via marker.colors (plural)
                if hasattr(trace.marker, 'colors') and trace.marker.colors:
                    continue  # Já tem cores definidas
                # Para outros gráficos, usar marker.color (singular)
                if hasattr(trace.marker, 'color') and trace.marker.color:
                    continue  # Já tem cor definida
                
                # Se não tem cor definida, aplicar da paleta
                color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
                fig.update_traces(
                    marker=dict(color=color, line=dict(width=0)),
                    selector=dict(uid=trace.uid)
                )
    except Exception:
        # Se houver qualquer erro na atribuição de cores, ignorar
        # O gráfico já deve ter suas cores padrão
        pass
    
    return fig


def create_line_chart(df, x, y, title=None, labels=None, color=None):
    """
    Cria um gráfico de linha estilizado
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna(s) para eixo Y
        title: Título do gráfico
        labels: Dict com labels customizados
        color: Coluna para colorir linhas
        
    Returns:
        Figura Plotly estilizada
    """
    fig = px.line(df, x=x, y=y, title=title, labels=labels, color=color,
                  color_discrete_sequence=COLOR_PALETTE)
    
    # Estilizar linhas
    fig.update_traces(
        line=dict(width=3),
        mode='lines+markers',
        marker=dict(size=6, line=dict(width=1, color='white'))
    )
    
    return apply_theme(fig)


def create_area_chart(df, x, y, title=None, labels=None, color=None):
    """
    Cria um gráfico de área estilizado
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna(s) para eixo Y
        title: Título do gráfico
        labels: Dict com labels customizados
        color: Coluna para colorir áreas
        
    Returns:
        Figura Plotly estilizada
    """
    fig = px.area(df, x=x, y=y, title=title, labels=labels, color=color,
                  color_discrete_sequence=COLOR_PALETTE)
    
    # Estilizar áreas com transparência
    fig.update_traces(
        line=dict(width=2),
        fillcolor=None,  # Usar cor padrão com opacidade
    )
    
    return apply_theme(fig)


def create_pie_chart(df, values, names, title=None):
    """
    Cria um gráfico de pizza estilizado
    
    Args:
        df: DataFrame com os dados
        values: Coluna com valores
        names: Coluna com nomes
        title: Título do gráfico
        
    Returns:
        Figura Plotly estilizada
    """
    fig = px.pie(df, values=values, names=names, title=title,
                 color_discrete_sequence=COLOR_PALETTE)
    
    # Estilizar pizza
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=12, color='white'),
        marker=dict(line=dict(color='rgba(0, 0, 0, 0.5)', width=2)),
        pull=[0.05] * len(df),  # Separar levemente as fatias
        hole=0.3  # Donut chart
    )
    
    return apply_theme(fig)


def create_bar_chart(df, x, y, title=None, labels=None, color=None, orientation='v'):
    """
    Cria um gráfico de barras estilizado
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        title: Título do gráfico
        labels: Dict com labels customizados
        color: Coluna para colorir barras
        orientation: 'v' (vertical) ou 'h' (horizontal)
        
    Returns:
        Figura Plotly estilizada
    """
    fig = px.bar(df, x=x, y=y, title=title, labels=labels, color=color,
                 orientation=orientation, color_discrete_sequence=COLOR_PALETTE)
    
    # Estilizar barras
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='rgba(255, 255, 255, 0.2)'),
            pattern=dict(shape='')
        ),
        textposition='outside'
    )
    
    return apply_theme(fig)


def create_scatter_chart(df, x, y, title=None, labels=None, color=None, size=None):
    """
    Cria um gráfico de dispersão estilizado
    
    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        title: Título do gráfico
        labels: Dict com labels customizados
        color: Coluna para colorir pontos
        size: Coluna para tamanho dos pontos
        
    Returns:
        Figura Plotly estilizada
    """
    fig = px.scatter(df, x=x, y=y, title=title, labels=labels, 
                     color=color, size=size, color_discrete_sequence=COLOR_PALETTE)
    
    # Estilizar pontos
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='white'),
            opacity=0.8
        )
    )
    
    return apply_theme(fig)


# Configuração global para Plotly Express
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = COLOR_PALETTE
