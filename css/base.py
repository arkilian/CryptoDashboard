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
</style>
"""


def get_app_base_style():
    """Retorna o CSS global da aplicação."""
    return APP_BASE_STYLE
