import io

def logar_usuario(client):
    """Auxiliar para cadastrar e logar um usuário de teste."""
    client.post(
        "/cadastro",
        data={
            "email": "user_teste@teste.com",
            "senha": "senha_valida_123",
            "confirmar_senha": "senha_valida_123",
        },
    )
    client.post(
        "/login",
        data={
            "email": "user_teste@teste.com",
            "senha": "senha_valida_123",
        },
    )


def test_render_index_page(client):
    """
    Valida se a Factory renderizou corretamente o Request Context inicial
    e a rota GET padrão que monta o formulário.
    """
    # Usuário precisa estar logado para acessar o painel
    logar_usuario(client)
    
    response = client.get('/painel/')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    assert "Juridiquê" in html
    assert "Envie seu documento" in html


def test_upload_pdf_integration(client):
    """
    Valida a orquestração completa: Request POST -> Fake PDF ->
    Mock LLM Injection -> Persistência SQLite (in-memory) -> Flash Message HTML.
    """
    # Usuário precisa estar logado para acessar o painel
    logar_usuario(client)

    # Emulando um arquivo sendo carregado pelo WTForms/Werkzeug na memória
    fake_pdf = (io.BytesIO(b"conteudo do pdf irrelevante"), 'processo_mock.pdf')
    
    response = client.post('/painel/', data={
        'arquivo_pdf': fake_pdf
    }, follow_redirects=True)
    
    # 200 Sucesso ao renderizar a View resultado.html
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    
    # Validações dos dados injetados na view vindos dos mocks
    assert "Documento traduzido e salvo com sucesso!" in html
    assert "Este é um resumo estático gerado por unittest.mock" in html
    assert "Mock" in html
    assert "Simulação de objetos no PyTest" in html
