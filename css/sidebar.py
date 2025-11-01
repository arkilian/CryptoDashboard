"""
Estilos CSS para a sidebar do CryptoDashboard
Design moderno e elegante com gradientes e animações
"""

SIDEBAR_STYLE = """
<style>
/* ========================================
   SIDEBAR - Background e estrutura base
   ======================================== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

/* ========================================
   CARD DE UTILIZADOR
   ======================================== */
.sidebar-username {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(147, 51, 234, 0.2));
    padding: 1.2rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 2rem;
    border: 1px solid rgba(147, 51, 234, 0.3);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.sidebar-username h3 {
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ========================================
   TÍTULO DO MENU
   ======================================== */
[data-testid="stSidebar"] h3 {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1rem !important;
    padding-left: 0.5rem;
}

/* ========================================
   BOTÕES DO MENU
   ======================================== */
[data-testid="stSidebar"] button {
    width: 100%;
    padding: 0.85rem 1rem !important;
    margin: 0.25rem 0 !important;
    border: none !important;
    border-radius: 10px !important;
    background: rgba(30, 41, 59, 0.5) !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    text-align: left !important;
    transition: all 0.3s ease !important;
    border-left: 3px solid transparent !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}

[data-testid="stSidebar"] button:hover {
    background: rgba(59, 130, 246, 0.3) !important;
    border-left: 3px solid #3b82f6 !important;
    transform: translateX(5px);
    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3) !important;
}

[data-testid="stSidebar"] button:focus {
    background: rgba(59, 130, 246, 0.4) !important;
    border-left: 3px solid #3b82f6 !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5) !important;
}

/* ========================================
   BOTÃO DE LOGOUT (estilo diferenciado)
   ======================================== */
[data-testid="stSidebar"] button[kind="secondary"] {
    background: rgba(239, 68, 68, 0.2) !important;
    border-left: 3px solid transparent !important;
    margin-top: 1rem !important;
}

[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: rgba(239, 68, 68, 0.4) !important;
    border-left: 3px solid #ef4444 !important;
    box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4) !important;
}

/* ========================================
   SEPARADOR
   ======================================== */
[data-testid="stSidebar"] hr {
    margin: 1.5rem 0 !important;
    border-color: rgba(148, 163, 184, 0.2) !important;
}

/* ========================================
   SCROLLBAR CUSTOMIZADA
   ======================================== */
[data-testid="stSidebar"] ::-webkit-scrollbar {
    width: 8px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.5);
    border-radius: 4px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.8);
}

/* ========================================
   WIDGETS NA SIDEBAR (Inputs, Selects, Date, etc.)
   Mantêm consistência com css/forms.py
   ======================================== */
/* Text / Number / TextArea */
[data-testid="stSidebar"] [data-testid="stTextInput"] input,
[data-testid="stSidebar"] [data-testid="stNumberInput"] input,
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea {
    background: rgba(30,41,59,.75) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(59,130,246,.35) !important;
    border-radius: 10px !important;
    box-shadow: inset 0 1px 2px rgba(0,0,0,.25);
}

[data-testid="stSidebar"] [data-testid="stTextInput"] input:focus,
[data-testid="stSidebar"] [data-testid="stNumberInput"] input:focus,
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea:focus {
    outline: none !important;
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.25) !important;
}

/* Selects e MultiSelect */
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background: rgba(30,41,59,.75) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(59,130,246,.35) !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] [data-baseweb="menu"] {
    background: rgba(15,23,42,.98) !important;
    border: 1px solid rgba(59,130,246,.25) !important;
}
[data-testid="stSidebar"] [data-baseweb="option"] { color: #e2e8f0 !important; }
[data-testid="stSidebar"] [data-baseweb="option"]:hover { background: rgba(59,130,246,.20) !important; }

/* Date Input */
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: rgba(30,41,59,.75) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(59,130,246,.35) !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] button { filter: hue-rotate(20deg) saturate(1.2); }

/* Slider */
[data-testid="stSidebar"] [data-testid="stSlider"] > div { padding-top: .2rem; }
[data-testid="stSidebar"] [role="slider"] {
    background: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.25);
}
[data-testid="stSidebar"] .stSlider > div > div { background: rgba(59,130,246,.35) !important; }

/* Checkbox / Radio */
[data-testid="stSidebar"] [data-testid="stCheckbox"] input:checked ~ div {
    border-color: #3b82f6 !important;
    background: rgba(59,130,246,.35) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(59,130,246,.12); border-radius: 8px; }

/* File Uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    background: rgba(30,41,59,.55) !important;
    border: 1px dashed rgba(59,130,246,.35) !important;
    border-radius: 12px !important;
}
</style>
"""


def get_sidebar_style():
    """
    Retorna o CSS da sidebar para ser injetado no Streamlit
    
    Usage:
        from css.sidebar import get_sidebar_style
        st.markdown(get_sidebar_style(), unsafe_allow_html=True)
    """
    return SIDEBAR_STYLE
