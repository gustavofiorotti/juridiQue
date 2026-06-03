from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class CadastroForm(FlaskForm):
    """Formulário de cadastro de usuários com validação no backend."""

    nome = StringField(
        "Nome",
        validators=[DataRequired(message="O nome é obrigatório.")]
    )

    email: EmailField = EmailField(
        "E-mail",
        validators=[
            DataRequired(message="O e-mail é obrigatório."),
            Email(message="E-mail inválido"),
        ],
    )
    senha: PasswordField = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="A senha é obrigatória."),
            Length(min=8, message="A senha deve ter no mínimo 8 caracteres."),
        ],
    )
    confirmar_senha: PasswordField = PasswordField(
        "Confirmar Senha",
        validators=[
            DataRequired(message="A confirmação de senha é obrigatória."),
            EqualTo("senha", message="As senhas devem coincidir"),
        ],
    )
    submit: SubmitField = SubmitField("Cadastrar")


class LoginForm(FlaskForm):
    """Formulário de login de usuários com validação no backend."""

    email: EmailField = EmailField(
        "E-mail",
        validators=[
            DataRequired(message="O e-mail é obrigatório."),
            Email(message="E-mail inválido"),
        ],
    )
    senha: PasswordField = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="A senha é obrigatória."),
        ],
    )
    submit: SubmitField = SubmitField("Entrar")


class PerfilForm(FlaskForm):
    """Formulário de edição de perfil."""
    
    nome = StringField(
        "Nome",
        validators=[DataRequired(message="O nome é obrigatório.")]
    )
    senha_atual = PasswordField("Senha Atual")
    nova_senha = PasswordField(
        "Nova Senha (deixe em branco se não quiser alterar)",
        validators=[
            Length(min=8, message="A senha deve ter no mínimo 8 caracteres.")
        ]
    )
    confirmar_nova_senha = PasswordField(
        "Confirmar Nova Senha",
        validators=[
            EqualTo("nova_senha", message="As novas senhas devem coincidir")
        ]
    )
    submit = SubmitField("Salvar Alterações")
