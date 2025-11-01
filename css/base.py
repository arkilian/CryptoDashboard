"""
Estilo global para aplicar o mesmo fundo em toda a aplicação
"""

APP_BASE_STYLE = """
<style>
/* ======================== GLOBAL BACKGROUND ======================== */
html, body {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
}

/* Contêiner principal da app */
[data-testid="stAppViewContainer"] {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
}

/* Área principal (conteúdo) */
[data-testid="stAppViewContainer"] .main {
  background: transparent !important;
}

/* Header (barra superior) transparente para deixar ver o fundo */
[data-testid="stHeader"] {
  background: transparent !important;
}

/* Contêiner dos blocks (onde ficam colunas, charts, etc.) */
[data-testid="block-container"] {
  background: transparent !important;
}

/* Rodapé/Toolbar (se presente) */
section[data-testid="stToolbar"] {
  background: transparent !important;
}
</style>
"""


def get_app_base_style():
    """Retorna o CSS global da aplicação."""
    return APP_BASE_STYLE
