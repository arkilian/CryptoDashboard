import base64
from pathlib import Path
from typing import Optional

class PDFViewer:
    @staticmethod
    def get_pdf_display_html(pdf_path: str, width: str = "100%", height: str = "800px") -> Optional[str]:
        """
        Creates an HTML string to display a PDF file using an iframe.
        
        Args:
            pdf_path (str): Path to the PDF file
            width (str): Width of the iframe (default: "100%")
            height (str): Height of the iframe (default: "800px")
            
        Returns:
            Optional[str]: HTML string to display the PDF, or None if file doesn't exist
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return None
            
            # Read PDF in binary mode and encode to base64
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
                base64_pdf = base64.b64encode(pdf_data).decode("utf-8")
            
            # Create iframe HTML
            return f'''
                <iframe 
                    src="data:application/pdf;base64,{base64_pdf}" 
                    width="{width}" 
                    height="{height}" 
                    type="application/pdf">
                </iframe>
            '''
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return None

    @staticmethod
    def get_pdf_download_link(pdf_path: str, link_text: str) -> Optional[str]:
        """
        Creates an HTML string for a download link to a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            link_text (str): Text to display for the download link
            
        Returns:
            Optional[str]: HTML string for the download link, or None if file doesn't exist
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return None
            
            # Read PDF and encode to base64
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
                b64_pdf = base64.b64encode(pdf_data).decode()
            
            # Create download link HTML
            return f'''
                <a href="data:application/pdf;base64,{b64_pdf}" 
                   download="{pdf_path.name}"
                   style="text-decoration:none;">
                    {link_text}
                </a>
            '''
        except Exception as e:
            print(f"Error creating download link: {str(e)}")
            return None