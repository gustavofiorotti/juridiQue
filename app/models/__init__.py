"""
Pacote contendo os modelos de dados da aplicação.

Exporta Usuario e ProcessoJudicial como parte da API pública do pacote.
"""

from app.models.usuario import Usuario
from app.models.documento import ProcessoJudicial

__all__ = ["Usuario", "ProcessoJudicial"]
