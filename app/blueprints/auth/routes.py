import uuid
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.ext.database import db
from app.models.usuario import Usuario
from app.forms.auth_forms import CadastroForm, LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Rota para cadastro de novos usuários."""
    form = CadastroForm()

    if form.validate_on_submit():
        # Consulta o banco para verificar se o e-mail já existe
        usuario_existente = Usuario.query.filter_by(email=form.email.data).first()
        if usuario_existente:
            flash("E-mail já cadastrado", "danger")
            return redirect(url_for("auth.cadastro"))

        # Gera um novo UUID v4 para o ID do usuário
        novo_id = str(uuid.uuid4())

        # Cria a instância de Usuario
        novo_usuario = Usuario(id=novo_id, email=form.email.data)
        novo_usuario.definir_senha(form.senha.data)

        # Salva no banco de dados
        db.session.add(novo_usuario)
        db.session.commit()

        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/cadastro.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Rota para login de usuários."""
    # Se o usuário já está autenticado, redireciona direto para o painel
    if current_user.is_authenticated:
        return redirect(url_for("interpreter.index"))

    form = LoginForm()

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.verificar_senha(form.senha.data):
            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            # Após login, redireciona para /painel (upload + histórico)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("interpreter.index"))

        flash("E-mail ou senha incorretos", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Rota para logout de usuários."""
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))

