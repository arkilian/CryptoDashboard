"""
Estilos consistentes para botões, inputs e restantes widgets do Streamlit
"""

FORMS_STYLE = """
<style>
/* ===================== BOTÕES (globais, não só na sidebar) ===================== */
.stButton > button {
  background: linear-gradient(135deg, rgba(59,130,246,.25), rgba(147,51,234,.25));
  color: #e2e8f0;
  border: 1px solid rgba(59,130,246,.35);
  border-radius: 10px;
  padding: .6rem 1rem;
  font-weight: 600;
  transition: all .25s ease;
  box-shadow: 0 2px 6px rgba(0,0,0,.25);
}
.stButton > button:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, rgba(59,130,246,.35), rgba(147,51,234,.35));
  border-color: #3b82f6;
  box-shadow: 0 6px 14px rgba(59,130,246,.25);
}
.stButton > button:active {
  transform: translateY(0);
}

/* Tipos de botão (primary/secondary) - normalizar cor da borda */
button[kind="primary"],
button[kind="secondary"] { border-color: #60a5fa !important; }

/* ===================== CAMPOS DE TEXTO/NUMÉRICOS ===================== */
/* TextInput */
[data-testid="stTextInput"]  input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
  background: rgba(30,41,59,.75) !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(59,130,246,.35) !important;
  border-radius: 10px !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,.25);
}
[data-testid="stTextInput"]  input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  outline: none !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,.25) !important;
}

/* ===================== SELECTS & MULTI-SELECTS ===================== */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
  background: rgba(30,41,59,.75) !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(59,130,246,.35) !important;
  border-radius: 10px !important;
}
/* Popovers e Menus (dropdowns e overlays) */
[data-baseweb="popover"] {
  background: rgba(15,23,42,.98) !important;
  border: 1px solid rgba(59,130,246,.25) !important;
  border-radius: 12px !important;
  box-shadow: 0 10px 24px rgba(0,0,0,.45) !important;
}

[data-baseweb="popover"] > div {
  background: rgba(15,23,42,.98) !important;
}

/* Lista/Menu dropdown */
[data-baseweb="menu"],
[data-baseweb="popover"] [role="listbox"] {
  background: rgba(15,23,42,.98) !important;
  border: none !important;
}

/* Opções individuais */
[data-baseweb="option"],
[role="option"] { 
  color: #e2e8f0 !important; 
  background: transparent !important;
}

[data-baseweb="option"]:hover,
[role="option"]:hover { 
  background: rgba(59,130,246,.20) !important; 
}

[data-baseweb="option"][aria-selected="true"],
[role="option"][aria-selected="true"] {
  background: rgba(59,130,246,.30) !important;
  color: #fff !important;
}

/* Calendário (DatePicker overlay) */
[data-baseweb="calendar"] {
  background: rgba(15,23,42,.98) !important;
  border: 1px solid rgba(59,130,246,.25) !important;
  border-radius: 12px !important;
  box-shadow: 0 10px 24px rgba(0,0,0,.45) !important;
  color: #e2e8f0 !important;
}
[data-baseweb="calendar"] button {
  color: #e2e8f0 !important;
}
[data-baseweb="calendar"] button:hover {
  background: rgba(59,130,246,.20) !important;
  border-radius: 8px !important;
}
[data-baseweb="calendar"] [aria-selected="true"] {
  background: #3b82f6 !important;
  color: #fff !important;
  border-radius: 8px !important;
}
[data-baseweb="calendar"] [aria-disabled="true"] {
  color: #64748b !important;
}

/* ===================== DATE PICKER ===================== */
[data-testid="stDateInput"] input {
  background: rgba(30,41,59,.75) !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(59,130,246,.35) !important;
  border-radius: 10px !important;
}
[data-testid="stDateInput"] button { filter: hue-rotate(20deg) saturate(1.2); }

/* ===================== SLIDER ===================== */
[data-testid="stSlider"] > div { padding-top: .2rem; }
[data-testid="stSlider"] [role="slider"] {
  background: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,.25);
}
[data-testid="stSlider"] .stSlider > div > div { background: rgba(59,130,246,.35) !important; }

/* ===================== CHECKBOX / RADIO ===================== */
[data-testid="stCheckbox"] input:checked ~ div {
  border-color: #3b82f6 !important;
  background: rgba(59,130,246,.35) !important;
}
[data-testid="stRadio"] label:hover { background: rgba(59,130,246,.12); border-radius: 8px; }

/* ===================== FILE UPLOADER ===================== */
[data-testid="stFileUploader"] section {
  background: rgba(30,41,59,.55) !important;
  border: 1px dashed rgba(59,130,246,.35) !important;
  border-radius: 12px !important;
}

/* ===================== FORM BLOCS / EXPANDERS ===================== */
[data-testid="stForm"] { 
  background: linear-gradient(135deg, rgba(30,41,59,.45), rgba(15,23,42,.45));
  border: 1px solid rgba(59,130,246,.25);
  border-radius: 12px;
  padding: 1rem;
}
</style>
"""


def get_forms_style():
  """Retorna o CSS de widgets e formulários."""
  return FORMS_STYLE
