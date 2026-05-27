import pdfplumber
from typing import BinaryIO

class PDFProcessor:
    """
    Classe utilitária para extração e processamento de arquivos PDF.
    """
    
    @staticmethod
    def extract_text_from_pdf(pdf_file: BinaryIO) -> str:
        """
        Extrai texto bruto de um arquivo binário em formato PDF.
        Retorna uma string contendo o texto extraído. Retorna string
        vazia se o arquivo for ilegível ou em caso de erro.
        """
        text_parts = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            return "\n".join(text_parts).strip()
        except Exception as e:
            # Em produção, um Logger seria ideal aqui.
            print(f"Erro ao processar o PDF: {e}")
            return ""
