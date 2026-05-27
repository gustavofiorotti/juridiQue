from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_app(app: Flask) -> None:
    """Inicializa a extensão do banco de dados (SQLAlchemy) e Migrações (Flask-Migrate)."""
    # Em ambiente de testes, forçamos o SQLite em memória
    if app.config.get("TESTING"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
            
    db.init_app(app)
    migrate.init_app(app, db)
