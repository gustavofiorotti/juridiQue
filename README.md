# juridiQue

Protótipo acadêmico de aplicação web que traduz documentos jurídicos em PDF para uma linguagem simples, acessível a quem não é da área.

> **Status:** protótipo desenvolvido em trabalho da faculdade, não é um produto pronto. As respostas são geradas por IA e não substituem a orientação de um profissional do direito.

## Funcionalidades

- Cadastro, login, edição de perfil e exclusão de conta
- Envio de um PDF e extração automática do texto
- Identificação de documentos que não são de natureza jurídica
- Resumo em linguagem simples e glossário dos termos jurídicos, gerados com o Google Gemini
- Histórico de análises, com consulta, nova análise e exclusão
- Painel administrativo

## Tecnologias

- **Backend:** Python, Flask, Flask-Login, Flask-WTF e Flask-Admin
- **Banco de dados:** SQL Server, SQLAlchemy e Flask-Migrate
- **IA:** Google Gemini
- **Processamento de PDF:** pdfplumber
- **Testes:** pytest

## Como rodar

### Pré-requisitos

- Python 3.10 ou superior
- SQL Server com um driver ODBC instalado
- Chave de API do Google Gemini

### Instalação

```bash
git clone https://github.com/gustavofiorotti/juridiQue.git
cd juridiQue
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Configuração

Copie o arquivo de exemplo e preencha as variáveis com os seus valores:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `FLASK_APP` | Aplicação Flask |
| `FLASK_ENV` | Ambiente de execução |
| `SECRET_KEY` | Chave secreta do Flask |
| `SQLALCHEMY_DATABASE_URI` | Conexão com o SQL Server |
| `GEMINI_API_KEY` | Chave da API do Gemini |
| `GEMINI_MODEL_NAME` | Modelo do Gemini a ser usado |

### Banco de dados e execução

```bash
flask --app app db upgrade
invoke run
```

A aplicação fica disponível em `http://127.0.0.1:5000`.

### Testes

```bash
invoke test
```

## Estrutura

```text
app/
├── blueprints/   # Rotas de autenticação e análise de documentos
├── ext/          # Configuração, banco, autenticação, admin e serviço de IA
├── forms/        # Formulários
├── models/       # Modelos de usuário e documento
├── static/       # Arquivos estáticos
├── templates/    # Páginas HTML
└── utils/        # Processamento de PDF
migrations/       # Migrações do banco
tests/            # Testes automatizados
```
