"""Processador de PDFs - TEMPORARIAMENTE DESABILITADO.

PyMuPDF foi removido temporariamente porque excede o limite de 250MB
da Vercel para Serverless Functions.

Para usar PDFs novamente:
1. Deploy o backend em Railway/Render/Fly.io
2. Ou reabilite pymupdf no requirements.txt quando mudar de plataforma
"""


class PDFProcessor:
    """Processador de PDFs para extrair texto."""
    
    def extract_text(self, file_content: bytes) -> str:
        """
        TEMPORARIAMENTE DESABILITADO - pymupdf removido por tamanho.
        
        Args:
            file_content: Conteúdo binário do PDF
        
        Returns:
            Texto extraído do PDF
            
        Raises:
            NotImplementedError: Funcionalidade temporariamente desabilitada
        """
        raise NotImplementedError(
            "Processamento de PDF temporariamente desabilitado. "
            "PyMuPDF foi removido para reduzir o tamanho da função serverless. "
            "Use apenas artefatos de TEXTO por enquanto, ou faça deploy do backend "
            "em Railway/Render para reabilitar PDFs."
        )

