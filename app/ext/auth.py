from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager()


def init_app(app: Flask) -> None:
    """Inicializa o LoginManager do Flask-Login."""
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models.usuario import Usuario
        from app.ext.database import db

        return db.session.get(Usuario, user_id)
