import streamlit as st
from utils.pdf_viewer import PDFViewer
from auth.session_manager import require_auth
from pathlib import Path

# Configuração dos documentos
DOCUMENTS = {
    "terms": {
        "title": "📋 Termos e Condições",
        "file": "docs/terms.pdf",
        "description": """
        Este documento contém os termos e condições gerais do serviço, 
        incluindo direitos e responsabilidades dos utilizadores.
        """
    },
    "risk": {
        "title": "📋 Estratégia e Gestão de Risco",
        "file": "docs/risk_management.pdf",
        "description": """
        Detalhamento da estratégia de investimento e metodologia 
        de gestão de risco aplicada ao fundo.
        """
    },
    "roadmap": {
        "title": "📋 Roadmap",
        "file": "docs/roadmap.pdf",
        "description": """
        Plano de desenvolvimento e evolução do projeto, incluindo 
        funcionalidades futuras e melhorias planejadas.
        """
    }
}

@require_auth
def show():
    st.title("💼 Documentos")
    
    # Criar menu lateral para navegação entre documentos
    doc_selection = st.sidebar.radio(
        "Escolha um documento",
        list(DOCUMENTS.keys()),
        format_func=lambda x: DOCUMENTS[x]["title"]
    )
    
    # Obter informações do documento selecionado
    doc = DOCUMENTS[doc_selection]
    
    # Exibir título e descrição
    st.header(doc["title"])
    st.markdown(doc["description"])
    
    # Tentar carregar e exibir o PDF
    pdf_viewer = PDFViewer()
    pdf_html = pdf_viewer.get_pdf_display_html(doc["file"])
    
    if pdf_html:
        st.markdown(pdf_html, unsafe_allow_html=True)

        # Adicionar botão de download
        download_link = pdf_viewer.get_pdf_download_link(
            doc["file"],
            "⬇️ Download PDF"
        )
        if download_link:
            st.markdown(download_link, unsafe_allow_html=True)
    else:
        st.error(f"❌ Erro ao carregar o documento. Por favor, contacte o administrador.")

        # Se for admin, mostrar caminho do arquivo (acesso defensivo)
        user = st.session_state.get('user')
        is_admin = False
        if user and isinstance(user, dict):
            is_admin = user.get('is_admin', False)
        else:
            is_admin = st.session_state.get('is_admin', False)

        if is_admin:
            st.warning(f"Caminho do arquivo: {Path(doc['file']).absolute()}")

    # Adicionar seção de metadata para admins
    # Admin-only metadata (access defensively)
    user = st.session_state.get('user')
    is_admin = False
    if user and isinstance(user, dict):
        is_admin = user.get('is_admin', False)
    else:
        is_admin = st.session_state.get('is_admin', False)

    if is_admin:
        with st.expander("🔧 Informações do Documento (Admin)"):
            st.json({
                "path": str(Path(doc["file"]).absolute()),
                "exists": Path(doc["file"]).exists(),
                "size": Path(doc["file"]).stat().st_size if Path(doc["file"]).exists() else None,
                "modified": Path(doc["file"]).stat().st_mtime if Path(doc["file"]).exists() else None
            })