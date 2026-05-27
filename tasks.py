from invoke import task

@task
def install(c):
    """Instala as dependências do projeto, incluindo as de desenvolvimento."""
    c.run("pip install -e .[dev]")

@task
def run(c):
    """Roda o servidor de desenvolvimento do Flask."""
    c.run("flask --app app run --debug")

@task
def test(c):
    """Roda a suíte de testes usando o pytest."""
    c.run("pytest")
