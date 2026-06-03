import json
from typing import Any

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.wrappers import Response as WerkzeugResponse

from app.blueprints.interpreter.forms import UploadProcessoForm
from app.ext.database import db
from app.ext.llm_service import JuridicoLLMService
from app.models.documento import ProcessoJudicial
from app.utils.pdf_processor import PDFProcessor

interpreter_bp: Blueprint = Blueprint('interpreter', __name__)


@interpreter_bp.route('/', methods=['GET', 'POST'])
@login_required
def index() -> str | WerkzeugResponse:
    """
    Rota principal da aplicação.

    - Em requisições GET: renderiza o formulário de upload.
    - Em requisições POST: faz a leitura em memória do PDF, tradução pelo LLM,
      persistência no banco e exibe os resultados.

    Segurança:
        O decorator ``@login_required`` do Flask-Login redireciona usuários
        não-autenticados automaticamente para ``auth.login``.
        O ID do usuário é obtido via ``current_user.id`` (proxy do
        Flask-Login), garantindo que o valor reflita a sessão autenticada.
    """
    # O @login_required já garante que current_user está autenticado.
    # Flask-Login armazena internamente o ID como '_user_id' na session,
    # portanto usamos current_user.id (e não session.get('user_id')).
    user_id: str = current_user.id

    # ------------------------------------------------------------------
    # 1. Validação do formulário
    # ------------------------------------------------------------------
    form: UploadProcessoForm = UploadProcessoForm()

    if form.validate_on_submit():
        arquivo_pdf = form.arquivo_pdf.data

        # ------------------------------------------------------------------
        # 2. Extração de texto do PDF (OCR / pdfplumber)
        # ------------------------------------------------------------------
        # FileStorage (do Werkzeug) atua como um file-like object spooled em
        # memória.  O PDFProcessor lerá da memória e o arquivo será descartado
        # pelo Garbage Collector ao final do request sem ser salvo em disco.
        texto_extraido: str = PDFProcessor.extract_text_from_pdf(arquivo_pdf)

        if not texto_extraido:
            flash(
                'Não foi possível extrair o texto. O PDF pode ser uma imagem '
                '(escaneado) ou estar corrompido.',
                'danger',
            )
            return redirect(url_for('interpreter.index'))

        # ------------------------------------------------------------------
        # 3. Tradução via LLM (Gemini)
        # ------------------------------------------------------------------
        # Recuperando o serviço via Application Context (injetado no
        # app.extensions pelo Application Factory).
        llm: JuridicoLLMService | None = current_app.extensions.get(
            'juridico_llm'
        )
        if not llm:
            flash(
                'Serviço de tradução (LLM) está indisponível no momento.',
                'danger',
            )
            return redirect(url_for('interpreter.index'))

        # Solicitando o resumo em linguagem simples — a lógica de chamada
        # de API e parse de JSON permanece encapsulada em JuridicoLLMService.
        dados_llm: dict[str, Any] = llm.traduzir_processo(texto_extraido)

        # ------------------------------------------------------------------
        # 4. Persistência no banco de dados
        # ------------------------------------------------------------------
        processo_bd: ProcessoJudicial = ProcessoJudicial(
            id_usuario=user_id,
            nome_arquivo=arquivo_pdf.filename,
            texto_original_extraido=texto_extraido,
            resumo_gerado_llm=json.dumps(dados_llm, ensure_ascii=False),
        )

        try:
            db.session.add(processo_bd)
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.error(
                '[DB] Falha ao persistir ProcessoJudicial '
                '(usuario=%s, arquivo=%s): %s',
                user_id,
                arquivo_pdf.filename,
                exc,
            )
            flash(
                'Ocorreu um erro ao salvar o documento no banco de dados. '
                'Por favor, tente novamente.',
                'danger',
            )
            return redirect(url_for('interpreter.index'))

        flash('Documento traduzido e salvo com sucesso!', 'success')

        # Repassando os dados do model e o dicionário json para a view de
        # resultado.  O template será construído posteriormente.
        return render_template(
            'interpreter/resultado.html',
            processo=processo_bd,
            dados_llm=dados_llm,
        )

    # ------------------------------------------------------------------
    # 5. Consulta ao histórico do usuário (exibido na página principal)
    # ------------------------------------------------------------------
    # filter_by(id_usuario=...) garante isolamento de dados entre usuários
    # (OWASP A01:2021 – Broken Access Control).
    documentos: list[ProcessoJudicial] = (
        ProcessoJudicial.query
        .filter_by(id_usuario=user_id)
        .order_by(ProcessoJudicial.data_submissao.desc())
        .limit(5)
        .all()
    )

    # Renderiza o index passando o form e o histórico para o Jinja no GET
    # ou em caso de falha de validação do formulário.
    return render_template('interpreter/upload.html', form=form, documentos=documentos)


@interpreter_bp.route('/historico', methods=['GET'])
@login_required
def historico() -> str | WerkzeugResponse:
    """
    Exibe o histórico de documentos processados pelo usuário autenticado.

    Segurança (OWASP A01:2021 — Broken Access Control):
        A query filtra **exclusivamente** pelo ``current_user.id``,
        garantindo isolamento total entre usuários.  Nenhum parâmetro da
        URL é utilizado para determinar o proprietário dos documentos,
        eliminando vetores de IDOR (Insecure Direct Object Reference).
    """
    # O @login_required já garante que current_user está autenticado.
    user_id: str = current_user.id

    # ------------------------------------------------------------------
    # 1. Consulta ao banco — histórico do usuário corrente
    # ------------------------------------------------------------------
    # filter_by(id_usuario=...) aplica uma cláusula WHERE que restringe os
    # resultados ao usuário logado, impedindo vazamento de dados de outros
    # usuários (OWASP A01:2021 – Broken Access Control).
    #
    # order_by(data_submissao.desc()) garante que o documento mais recente
    # apareça primeiro na listagem, proporcionando melhor UX.
    documentos: list[ProcessoJudicial] = (
        ProcessoJudicial.query
        .filter_by(id_usuario=user_id)
        .order_by(ProcessoJudicial.data_submissao.desc())
        .all()
    )

    # ------------------------------------------------------------------
    # 2. Renderização do template
    # ------------------------------------------------------------------
    # A variável 'documentos' é passada ao Jinja2 para iteração no HTML.
    return render_template(
        'interpreter/historico.html',
        documentos=documentos,
    )


@interpreter_bp.route('/historico/<int:id>/apagar', methods=['POST'])
@login_required
def apagar_historico(id: int) -> WerkzeugResponse:
    """
    Apaga um documento do histórico do usuário.
    """
    user_id: str = current_user.id
    documento = ProcessoJudicial.query.filter_by(id=id, id_usuario=user_id).first()
    
    if documento:
        db.session.delete(documento)
        db.session.commit()
        flash('Documento apagado com sucesso.', 'success')
    else:
        flash('Documento não encontrado ou sem permissão para apagar.', 'danger')
        
    return redirect(url_for('interpreter.historico'))


@interpreter_bp.route('/historico/<int:id>', methods=['GET'])
@login_required
def ver_analise(id: int) -> str | WerkzeugResponse:
    """
    Exibe a análise completa de um documento previamente salvo no histórico.
    """
    user_id: str = current_user.id
    processo = ProcessoJudicial.query.filter_by(id=id, id_usuario=user_id).first()
    
    if not processo:
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('interpreter.historico'))
        
    try:
        dados_llm = json.loads(processo.resumo_gerado_llm) if processo.resumo_gerado_llm else {}
    except json.JSONDecodeError:
        dados_llm = {"resumo": "Erro ao ler o resumo do banco de dados.", "termos": []}
        
    return render_template(
        'interpreter/resultado.html',
        processo=processo,
        dados_llm=dados_llm,
    )


@interpreter_bp.route('/historico/<int:id>/reanalisar', methods=['POST'])
@login_required
def reanalisar(id: int) -> WerkzeugResponse:
    """
    Refaz a análise de um documento usando o texto original já extraído.
    """
    user_id: str = current_user.id
    processo = ProcessoJudicial.query.filter_by(id=id, id_usuario=user_id).first()
    
    if not processo:
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('interpreter.historico'))
        
    llm: JuridicoLLMService | None = current_app.extensions.get('juridico_llm')
    if not llm:
        flash('Serviço de tradução (LLM) está indisponível no momento.', 'danger')
        return redirect(url_for('interpreter.historico'))
        
    dados_llm = llm.traduzir_processo(processo.texto_original_extraido)
    
    novo_processo = ProcessoJudicial(
        id_usuario=user_id,
        nome_arquivo=processo.nome_arquivo,
        texto_original_extraido=processo.texto_original_extraido,
        resumo_gerado_llm=json.dumps(dados_llm, ensure_ascii=False)
    )
    
    try:
        db.session.add(novo_processo)
        db.session.commit()
        flash('Documento reanalisado com sucesso! Um novo registro foi criado.', 'success')
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error('[DB] Falha ao reanalisar ProcessoJudicial: %s', exc)
        flash('Ocorreu um erro ao salvar a reanálise.', 'danger')
        
    return redirect(url_for('interpreter.ver_analise', id=novo_processo.id if novo_processo.id else processo.id))
