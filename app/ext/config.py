import logging
import os
from flask import Flask
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def init_app(app: Flask) -> None:
    """Inicializa e carrega as configurações da aplicação a partir do .env."""
    load_dotenv()

    # Para garantir que todas as sessões anteriores no navegador sejam invalidadas
    # a cada reinício do servidor (conforme solicitado pelo usuário), adicionamos
    # um componente dinâmico/aleatório à SECRET_KEY em tempo de execução.
    base_secret = os.environ.get("SECRET_KEY", "dev-secret-key-insegura")
    app.config["SECRET_KEY"] = f"{base_secret}-{os.urandom(16).hex()}"

    # --- Configuração de sessão -------------------------------------------
    # SESSION_PERMANENT = False  →  cookie expira ao fechar o navegador.
    # SESSION_COOKIE_HTTPONLY    →  impede acesso via JavaScript (XSS).
    # SESSION_COOKIE_SAMESITE   →  proteção básica contra CSRF em cookies.
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY")
    app.config["GEMINI_MODEL_NAME"] = os.environ.get(
        "GEMINI_MODEL_NAME", "gemini-2.5-flash"
    )

