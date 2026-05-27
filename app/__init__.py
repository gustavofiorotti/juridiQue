from flask import Flask, redirect, url_for

from app.ext import config
from app.ext import database
from app.ext.llm_service import llm_service
from app.ext import admin
from app.ext import auth

def create_app(test_config=None) -> Flask:
    """Application Factory: Cria e configura uma instância do Flask."""
    app = Flask(__name__)
    
    # 1. Configurações
    config.init_app(app)
    if test_config:
        app.config.update(test_config)
    
    # 2. Extensões
    database.init_app(app)
    llm_service.init_app(app)
    admin.init_app(app)
    auth.init_app(app)
    
    # 3. Blueprints
    from app.blueprints.interpreter.routes import interpreter_bp
    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(interpreter_bp, url_prefix="/painel")
    
    # 4. Rota raiz — redireciona para login como página de entrada padrão
    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))
    
    return app

