"""
Estilos CSS para tabelas e dataframes do CryptoDashboard
Design moderno e elegante com melhor legibilidade
"""

TABLES_STYLE = """
<style>
/* ========================================
   TABELAS (st.dataframe e st.table) - Estilo geral
   ======================================== */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.6), rgba(30, 41, 59, 0.6));
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

/* Tabela base */
[data-testid="stDataFrame"] table,
[data-testid="stTable"] table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
}

/* ========================================
   CABEÇALHO DA TABELA
   ======================================== */
[data-testid="stDataFrame"] thead th,
[data-testid="stTable"] thead th {
    background: linear-gradient(135deg, #1e40af, #3b82f6) !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 1rem 0.75rem !important;
    border: none !important;
    text-align: left !important;
    position: sticky;
    top: 0;
    z-index: 2;
}

[data-testid="stDataFrame"] thead th:first-child,
[data-testid="stTable"] thead th:first-child {
    border-top-left-radius: 8px;
}

[data-testid="stDataFrame"] thead th:last-child,
[data-testid="stTable"] thead th:last-child {
    border-top-right-radius: 8px;
}

/* ========================================
   LINHAS DA TABELA
   ======================================== */
[data-testid="stDataFrame"] tbody tr {
    transition: all 0.2s ease;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

[data-testid="stDataFrame"] tbody tr:hover,
[data-testid="stTable"] tbody tr:hover {
    background: rgba(59, 130, 246, 0.15) !important;
    transform: scale(1.01);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

[data-testid="stDataFrame"] tbody tr:nth-child(even),
[data-testid="stTable"] tbody tr:nth-child(even) {
    background: rgba(30, 41, 59, 0.4) !important;
}

[data-testid="stDataFrame"] tbody tr:nth-child(odd),
[data-testid="stTable"] tbody tr:nth-child(odd) {
    background: rgba(30, 41, 59, 0.2) !important;
}

/* ========================================
   CÉLULAS DA TABELA
   ======================================== */
[data-testid="stDataFrame"] tbody td,
[data-testid="stTable"] tbody td {
    padding: 0.85rem 0.75rem !important;
    color: #e2e8f0 !important;
    font-size: 0.9rem !important;
    border: none !important;
    font-variant-numeric: tabular-nums;
}

/* Primeira coluna com destaque */
[data-testid="stDataFrame"] tbody td:first-child,
[data-testid="stTable"] tbody td:first-child {
    font-weight: 600;
    color: #60a5fa !important;
}

/* Borda inferior arredondada na última linha */
[data-testid="stDataFrame"] tbody tr:last-child td:first-child,
[data-testid="stTable"] tbody tr:last-child td:first-child { border-bottom-left-radius: 10px; }
[data-testid="stDataFrame"] tbody tr:last-child td:last-child,
[data-testid="stTable"] tbody tr:last-child td:last-child { border-bottom-right-radius: 10px; }

/* ========================================
   TABELAS EDITÁVEIS (data_editor)
   ======================================== */
[data-testid="stDataFrameContainer"] {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.6), rgba(30, 41, 59, 0.6));
    border-radius: 12px;
    padding: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

/* Células editáveis */
[data-testid="stDataFrameContainer"] input {
    background: rgba(30, 41, 59, 0.8) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
}

[data-testid="stDataFrameContainer"] input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    outline: none;
}

/* ========================================
   MÉTRICAS (st.metric)
   ======================================== */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.5));
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    border-left-color: #60a5fa;
}

[data-testid="stMetric"] [data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.9rem !important;
}

/* ========================================
   EXPANDERS
   ======================================== */
[data-testid="stExpander"] {
    background: rgba(30, 41, 59, 0.3);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 10px;
    margin-bottom: 1rem;
}

[data-testid="stExpander"] summary {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.2), rgba(147, 51, 234, 0.2));
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-weight: 600;
    color: #e2e8f0;
    transition: all 0.2s ease;
}

[data-testid="stExpander"] summary:hover {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.3), rgba(147, 51, 234, 0.3));
    transform: translateX(3px);
}

/* ========================================
   SCROLLBAR para tabelas
   ======================================== */
[data-testid="stDataFrame"] ::-webkit-scrollbar,
[data-testid="stDataFrameContainer"] ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

[data-testid="stDataFrame"] ::-webkit-scrollbar-track,
[data-testid="stDataFrameContainer"] ::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 4px;
}

[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb,
[data-testid="stDataFrameContainer"] ::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.5);
    border-radius: 4px;
}

[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover,
[data-testid="stDataFrameContainer"] ::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.8);
}
</style>
"""


def get_tables_style():
    """
    Retorna o CSS das tabelas para ser injetado no Streamlit
    
    Usage:
        from css.tables import get_tables_style
        st.markdown(get_tables_style(), unsafe_allow_html=True)
    """
    return TABLES_STYLE
