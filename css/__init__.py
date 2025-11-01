"""
Módulo CSS para estilos customizados do CryptoDashboard
"""

from .sidebar import get_sidebar_style
from .tables import get_tables_style
from .charts import (
    apply_theme, 
    create_line_chart, 
    create_area_chart, 
    create_pie_chart,
    create_bar_chart,
    create_scatter_chart,
    COLORS,
    COLOR_PALETTE
)

__all__ = [
    'get_sidebar_style', 
    'get_tables_style',
    'apply_theme',
    'create_line_chart',
    'create_area_chart',
    'create_pie_chart',
    'create_bar_chart',
    'create_scatter_chart',
    'COLORS',
    'COLOR_PALETTE'
]
