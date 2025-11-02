"""
Estilo global para aplicar o mesmo fundo em toda a aplicação
"""

APP_BASE_STYLE = """
<style>
/* ======================== GLOBAL BACKGROUND ======================== */
html, body {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Contêiner principal da app */
[data-testid="stAppViewContainer"] {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
  padding-top: 0 !important;
}

/* Área principal (conteúdo) */
[data-testid="stAppViewContainer"] .main {
  background: transparent !important;
  padding-top: 0 !important;
}

/* Header (barra superior) – visível mas compacto */
[data-testid="stHeader"] {
  background: transparent !important;
  height: 2.75rem !important;
  min-height: 2.75rem !important;
  padding: 0 .5rem !important;
  display: flex !important;
  align-items: center !important;
}

/* Decoração/ribbon do topo – manter visível */
[data-testid="stDecoration"] {
  display: block !important;
  height: auto !important;
}

/* Contêiner dos blocks (onde ficam colunas, charts, etc.) */
[data-testid="block-container"] {
  background: transparent !important;
  /* Reduzir ainda mais o espaçamento superior padrão do Streamlit */
  padding-top: 0.2rem !important;
  padding-bottom: 1.0rem !important;
  margin-top: 0 !important;
}

/* Remover margem/padding do primeiro bloco e do primeiro heading */
[data-testid="block-container"] > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }
[data-testid="block-container"] h1:first-child,
[data-testid="block-container"] h2:first-child,
[data-testid="block-container"] h3:first-child { margin-top: 0.2rem !important; }

/* Garantir que todos os h1 não criam espaço extra no topo */
[data-testid="block-container"] h1 { margin-top: 0.3rem !important; }

/* Ajuste adicional para dispositivos móveis (menos espaço no topo) */
@media (max-width: 768px) {
  [data-testid="block-container"] {
    padding-top: 0.15rem !important;
  }
}

/* Rodapé/Toolbar (se presente) */
section[data-testid="stToolbar"] {
  background: transparent !important;
  height: 0 !important;
  min-height: 0 !important;
  visibility: hidden !important;
}

/* ========================================
   TABS (Sub Menus) - st.tabs()
   ======================================== */
/* Container dos tabs */
[data-testid="stTabs"] {
    background: transparent;
    padding: 0;
    margin: 1rem 0;
}

/* Lista de tabs (cabeçalhos) */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: rgba(15, 23, 42, 0.4);
    padding: 0.5rem;
    border-radius: 12px;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

/* Cada tab individual */
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.5) !important;
    color: #94a3b8 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}

/* Tab hover */
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background: rgba(59, 130, 246, 0.2) !important;
    color: #e2e8f0 !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3) !important;
}

/* Tab ativa */
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(147, 51, 234, 0.4)) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-bottom: 3px solid #3b82f6 !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5) !important;
}

/* Painel de conteúdo do tab */
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    background: rgba(30, 41, 59, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    border: 1px solid rgba(59, 130, 246, 0.15);
}

/* Indicador de tab ativa (linha embaixo) */
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #3b82f6 !important;
    height: 3px !important;
}
</style>
"""


def get_app_base_style():
    """Retorna o CSS global da aplicação."""
    return APP_BASE_STYLE
