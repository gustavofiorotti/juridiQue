import uuid

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from app.ext.database import db


class Usuario(UserMixin, db.Model):
    """
    Modelo ORM que representa um usuário do sistema.
    Usa hashes criptográficos para senhas em conformidade com OWASP.
    """
    __tablename__ = "usuarios"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )
    senha_hash = db.Column(
        db.String(256),
        nullable=False
    )

    # Relacionamento 1:N com processos/documentos analisados
    processos = db.relationship(
        "ProcessoJudicial",
        backref="usuario",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def definir_senha(self, senha: str) -> None:
        """
        Gera o hash da senha e atribui ao campo senha_hash.
        """
        if not senha:
            raise ValueError("A senha não pode ser vazia.")
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        """
        Verifica a senha informada contra o hash gravado no banco de dados.
        """
        if not self.senha_hash or not senha:
            return False
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self) -> str:
        return f"<Usuario {self.email}>"
