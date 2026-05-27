import os
import pytest
from unittest.mock import patch

@pytest.fixture
def app():
    """
    Valida a Application Factory. 
    Intercepta as variáveis de ambiente antes da inicialização.
    """
    with patch.dict('os.environ', {
        'GEMINI_API_KEY': 'mock-api-key'
    }):
        from app import create_app
        from app.ext.database import db
        
        app = create_app(test_config={
            "TESTING": True,
            "WTF_CSRF_ENABLED": False 
        })
        
        # Cria as tabelas do banco de dados relacional em memória
        with app.app_context():
            db.create_all()
        
        yield app


@pytest.fixture
def client(app):
    """Fornece o cliente HTTP do Flask."""
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_llm_service():
    """
    Mock obrigatório e automático. Intercepta todas as requisições ao serviço LLM 
    durante qualquer teste para não disparar chamadas reais e gerar cobranças.
    """
    with patch('app.ext.llm_service.JuridicoLLMService.traduzir_processo') as mock_llm:
        mock_llm.return_value = {
            "resumo": "Este é um resumo estático gerado por unittest.mock.",
            "termos": [
                {"termo": "Mock", "significado": "Simulação de objetos no PyTest"}
            ]
        }
        yield mock_llm

@pytest.fixture(autouse=True)
def mock_pdf_processor():
    """
    Opcional, porém prático. Pula a extração de binários do PDFplumber,
    permitindo que enviemos apenas bytestreams simples simulados.
    """
    with patch('app.utils.pdf_processor.PDFProcessor.extract_text_from_pdf') as mock_pdf:
        mock_pdf.return_value = "Texto legível, extraído simuladamente do PDF em memória."
        yield mock_pdf
