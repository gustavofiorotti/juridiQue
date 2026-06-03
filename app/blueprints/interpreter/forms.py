from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed, FileSize
from wtforms import StringField
from wtforms.validators import DataRequired

class UploadProcessoForm(FlaskForm):
    """
    Formulário seguro para upload de arquivos de processos judiciais.
    A proteção CSRF está habilitada implicitamente (padrão do FlaskForm).
    """
    arquivo_pdf = FileField(
        'Arquivo do documento (PDF)',
        validators=[
            FileRequired(message='O envio de um arquivo é obrigatório.'),
            FileAllowed(['pdf'], message='Apenas arquivos com extensão .pdf são permitidos.'),
            FileSize(max_size=15 * 1024 * 1024, message='O tamanho máximo permitido é de 15MB.')
        ]
    )

class ChatForm(FlaskForm):
    """
    Formulário seguro para envio de dúvidas no chat integrado.
    """
    duvida = StringField(
        'Sua dúvida',
        validators=[
            DataRequired(message='O campo de dúvida não pode estar vazio.')
        ]
    )
