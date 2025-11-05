"""Processador de PDFs usando PyMuPDF."""
import fitz  # PyMuPDF


class PDFProcessor:
    """Processador de PDFs para extrair texto."""
    
    def extract_text(self, file_content: bytes) -> str:
        """
        Extrai texto de um arquivo PDF.
        
        Args:
            file_content: Conteúdo binário do PDF
        
        Returns:
            Texto extraído do PDF
        """
        try:
            # Abre o PDF a partir do conteúdo em bytes
            doc = fitz.open(stream=file_content, filetype="pdf")
            
            # Extrai texto de todas as páginas
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)
            
            doc.close()
            
            # Junta todo o texto
            full_text = "\n\n".join(text_parts)
            
            return full_text.strip()
        except Exception as e:
            raise ValueError(f"Erro ao processar PDF: {str(e)}")

