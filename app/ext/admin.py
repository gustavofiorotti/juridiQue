from flask import Flask, request, abort
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models.documento import ProcessoJudicial
from app.ext.database import db

class ProcessoJudicialAdminView(ModelView):
    """
    View administrativa restrita para a gestão de Processos Judiciais.
    Controla como os registros SQLAlchemy são exibidos no painel admin.
    """
    # Esconde o texto bruto da tabela para evitar poluição visual
    column_list = ('nome_arquivo', 'data_submissao', 'id_usuario')
    
    # Também permite buscar por nome do arquivo
    column_searchable_list = ('nome_arquivo',)
    
    def is_accessible(self) -> bool:
        """
        Validação de acesso ao painel admin: aceita requisições apenas
        quando o parâmetro ?token da URL coincide com a SECRET_KEY da
        aplicação. Em produção, substituir por Flask-Login com current_user.is_admin.
        """
        from flask import current_app
        secret = current_app.config.get("SECRET_KEY", "")
        return bool(secret and request.args.get("token") == secret)
        
    def inaccessible_callback(self, name, **kwargs):
        """Bloqueia o acesso negando permissão explicitamente se a validação falhar."""
        abort(403)

# Instanciando o painel de forma simplificada sem conflitos com template_mode
admin_panel = Admin(name='Backoffice Judicial')

def init_app(app: Flask) -> None:
    """
    Atrasa a inicialização do painel integrando no ciclo de vida da Application Factory.
    """
    admin_panel.init_app(app)
    
    # Evita duplicar a view se o app for recriado repetidas vezes (bateria de testes do PyTest)
    if not any(isinstance(v, ProcessoJudicialAdminView) for v in admin_panel._views):
        admin_panel.add_view(ProcessoJudicialAdminView(ProcessoJudicial, db))
