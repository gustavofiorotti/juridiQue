from app.models.usuario import Usuario


def test_cadastro_page_renders(client):
    """Valida se a página de cadastro renderiza com sucesso via GET."""
    response = client.get("/cadastro")
    assert response.status_code == 200
    assert b"Criar Conta" in response.data
    assert b"E-mail" in response.data
    assert b"Senha" in response.data
    assert b"Confirmar Senha" in response.data


def test_cadastro_validation_errors(client):
    """Valida que erros de validação no formulário são exibidos corretamente."""
    response = client.post(
        "/cadastro", data={"email": "invalido", "senha": "", "confirmar_senha": ""}
    )
    assert response.status_code == 200
    assert b"E-mail inv\xc3\xa1lido" in response.data  # E-mail inválido (encoded UTF-8)
    assert b"A senha \xc3\xa9 obrigat\xc3\xb3ria" in response.data


def test_cadastro_success(app, client):
    """Valida se o cadastro com dados válidos é persistido no banco."""
    # Envia dados de cadastro corretos
    response = client.post(
        "/cadastro",
        data={
            "nome": "Novo Usuário",
            "email": "novo_usuario@teste.com",
            "senha": "senhadeseguranca123",
            "confirmar_senha": "senhadeseguranca123",
        },
    )

    # Após cadastro, o sistema faz login automático e redireciona para o painel
    assert response.status_code == 302
    assert response.headers["Location"] == "/painel/"

    # Verifica se o usuário foi realmente inserido no banco de dados com senha hasheada
    with app.app_context():
        usuario = Usuario.query.filter_by(email="novo_usuario@teste.com").first()
        assert usuario is not None
        assert usuario.id is not None
        # Verifica se o hash de senha funciona
        assert usuario.verificar_senha("senhadeseguranca123") is True
        assert usuario.verificar_senha("senha_errada") is False


def test_cadastro_duplicate_email(app, client):
    """Valida que não é permitido cadastrar dois usuários com o mesmo e-mail."""
    # Registra o primeiro usuário
    client.post(
        "/cadastro",
        data={
            "nome": "Usuário Original",
            "email": "duplicado@teste.com",
            "senha": "senha12345678",
            "confirmar_senha": "senha12345678",
        },
    )

    # Logout para poder testar o cadastro duplicado sem estar autenticado
    client.get("/logout")

    # Tenta registrar o segundo com o mesmo e-mail
    response = client.post(
        "/cadastro",
        data={
            "nome": "Outro Usuário",
            "email": "duplicado@teste.com",
            "senha": "outrasenha12345",
            "confirmar_senha": "outrasenha12345",
        },
    )

    # Deve redirecionar de volta para a rota de cadastro (recarregar)
    assert response.status_code == 302
    assert response.headers["Location"] == "/cadastro"

    # Acessa a página após o redirect e valida se a mensagem flash foi exibida
    follow_up = client.get("/cadastro")
    assert b"E-mail j\xc3\xa1 cadastrado" in follow_up.data


def test_login_page_renders(client):
    """Valida se a página de login renderiza com sucesso via GET."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Entrar na sua Conta" in response.data


def test_login_validation_errors(client):
    """Valida erros de validação no formulário de login."""
    response = client.post("/login", data={"email": "invalido", "senha": ""})
    assert response.status_code == 200
    assert b"E-mail inv\xc3\xa1lido" in response.data
    assert b"A senha \xc3\xa9 obrigat\xc3\xb3ria" in response.data


def test_login_success(client):
    """Valida login com credenciais corretas."""
    # Primeiro cadastramos o usuário
    client.post(
        "/cadastro",
        data={
            "nome": "Login Sucesso",
            "email": "login_sucesso@teste.com",
            "senha": "senha_valida_123",
            "confirmar_senha": "senha_valida_123",
        },
    )

    # Logout para poder testar o login separadamente
    client.get("/logout")

    # Tenta fazer login
    response = client.post(
        "/login",
        data={
            "email": "login_sucesso@teste.com",
            "senha": "senha_valida_123",
        },
    )
    # Redireciona para a página do painel (/painel/)
    assert response.status_code == 302
    assert response.headers["Location"] == "/painel/"

    # Valida que o logout (protegido) pode ser acessado e desloga com sucesso
    logout_response = client.get("/logout")
    assert logout_response.status_code == 302
    assert logout_response.headers["Location"] == "/login"


def test_login_invalid_credentials(client):
    """Valida falha ao fazer login com credenciais incorretas."""
    # Cadastra o usuário
    client.post(
        "/cadastro",
        data={
            "nome": "Login Falha",
            "email": "login_falha@teste.com",
            "senha": "senha_valida_123",
            "confirmar_senha": "senha_valida_123",
        },
    )

    # Logout para poder testar login com credenciais inválidas
    client.get("/logout")

    # Login com senha incorreta
    response = client.post(
        "/login",
        data={
            "email": "login_falha@teste.com",
            "senha": "senha_incorreta",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    follow_up = client.get("/login")
    assert b"E-mail ou senha incorretos" in follow_up.data

    # Login com usuário inexistente
    response = client.post(
        "/login",
        data={
            "email": "inexistente@teste.com",
            "senha": "senha_valida_123",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    follow_up = client.get("/login")
    assert b"E-mail ou senha incorretos" in follow_up.data

