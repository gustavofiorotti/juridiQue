from datetime import datetime, timezone

from app.ext.database import db


class ProcessoJudicial(db.Model):
    """
    Modelo para armazenar os Processos Judiciais e seus resumos processados.
    
    Mapeado Database-First integrado ao relacionamento com usuários.
    """
    __tablename__ = "processos_judiciais"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # ID do usuário vinculado. Deve bater com o tipo String(36) da tabela 'usuarios'
    id_usuario = db.Column(
        db.String(36),
        db.ForeignKey("usuarios.id"),
        nullable=True
    )
    
    nome_arquivo = db.Column(db.String(255), nullable=False)
    
    # Textos longos armazenados como db.Text no SQL Server (mapeia para VARCHAR(MAX) ou similar)
    texto_original_extraido = db.Column(db.Text, nullable=False)
    resumo_gerado_llm = db.Column(db.Text, nullable=True)
    
    data_submissao = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<ProcessoJudicial {self.nome_arquivo} (ID: {self.id})>"
