"""
Serviço de integração com a API Gemini (Google Generative AI).

Segue o padrão Application Factory (PEP 3333): a classe não acessa
configurações no escopo global — tudo é lido dentro do Application Context
via ``flask.current_app.config``, garantindo compatibilidade com testes e
múltiplas instâncias de aplicação.

PEP 8 + PEP 484 (Type Hints).
"""

import json
from typing import Any, Optional

import google.generativeai as genai
from flask import Flask, current_app
from google.api_core.exceptions import ResourceExhausted

# ---------------------------------------------------------------------------
# Prompt do sistema — instruções permanentes para o modelo agir como
# assistente jurídico que retorna JSON estruturado.
# ---------------------------------------------------------------------------
_SYSTEM_INSTRUCTION: str = (
    "Você é um assistente jurídico especialista em traduzir e descomplicar "
    "documentos jurídicos (como processos judiciais, projetos de lei, despachos, etc) para linguagem simples, "
    "acessível a cidadãos comuns sem formação jurídica.\n\n"
    "REGRA ABSOLUTA: sua resposta DEVE ser exclusivamente um objeto JSON "
    "válido, sem nenhum texto antes ou depois, contendo EXATAMENTE as "
    "seguintes chaves:\n"
    "- \"resumo\": (string) Resumo claro e acessível sobre o que trata o documento.\n"
    "- \"termos\": (array) Lista de objetos, cada um com as chaves "
    "\"termo\" (o jargão jurídico) e \"significado\" (sua explicação simples)."
)

# ---------------------------------------------------------------------------
# Respostas de fallback padronizadas (evitam 500 na view).
# ---------------------------------------------------------------------------
def _erro_quota() -> dict[str, Any]:
    return {
        "resumo": (
            "O sistema está momentaneamente sobrecarregado e não conseguiu "
            "processar o documento (limite de quota atingido). "
            "Por favor, tente novamente mais tarde."
        ),
        "termos": [],
    }


def _erro_json() -> dict[str, Any]:
    return {
        "resumo": "Ocorreu um erro ao interpretar a resposta estruturada da IA.",
        "termos": [],
    }


def _erro_generico() -> dict[str, Any]:
    return {
        "resumo": "Ocorreu um erro ao gerar o resumo estruturado.",
        "termos": [],
    }


class JuridicoLLMService:
    """
    Extensão Flask que encapsula toda a comunicação com a API Gemini.

    Nenhuma chamada de rede é feita fora do método ``traduzir_processo``.
    """

    def __init__(self, app: Optional[Flask] = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Registra a extensão no Application Context do Flask.

        Valida, em tempo de inicialização, se as configurações obrigatórias
        estão presentes, emitindo avisos no log sem travar o servidor.
        """
        if not hasattr(app, "extensions"):
            app.extensions = {}

        app.extensions["juridico_llm"] = self

        # Validação antecipada — evita que erros apareçam só na primeira requisição.
        api_key: Optional[str] = app.config.get("GEMINI_API_KEY")
        model_name: str = app.config.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

        if not api_key:
            app.logger.warning(
                "[LLM] GEMINI_API_KEY não configurada. "
                "O serviço LLM estará inoperante até que a chave seja definida no .env."
            )
        else:
            app.logger.info(
                f"[LLM] Serviço Gemini inicializado. Modelo configurado: '{model_name}'"
            )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _limpar_markdown(texto: str) -> str:
        """
        Remove delimitadores de bloco Markdown (```json ... ```) que o
        modelo eventualmente inclui mesmo com response_mime_type=application/json.
        """
        limpo: str = texto.strip()
        if limpo.startswith("```"):
            linhas = limpo.splitlines()
            limpo = "\n".join(linhas[1:-1]).strip()
        return limpo

    def _criar_modelo(
        self, api_key: str, model_name: str
    ) -> Optional[genai.GenerativeModel]:
        """
        Instancia o ``GenerativeModel`` com as configurações de geração.

        Retorna ``None`` e loga o erro em caso de falha na inicialização,
        evitando que a aplicação trave silenciosamente.
        """
        try:
            genai.configure(api_key=api_key)
            modelo = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=_SYSTEM_INSTRUCTION,
                generation_config={
                    "response_mime_type": "application/json",
                    # Temperatura baixa → maior previsibilidade na extração de dados
                    "temperature": 0.1,
                },
            )
            current_app.logger.info(
                f"[LLM] GenerativeModel instanciado com sucesso: '{model_name}'"
            )
            return modelo
        except Exception as exc:  # noqa: BLE001
            current_app.logger.error(
                f"[LLM] Falha crítica ao instanciar GenerativeModel "
                f"({type(exc).__name__}): {exc}"
            )
            return None

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def traduzir_processo(self, texto: str) -> dict[str, Any]:
        """
        Envia o texto do documento para o Gemini e retorna um dicionário
        estruturado com 'resumo' e 'termos'.

        Toda a lógica de rede está encapsulada aqui — blueprints e views
        nunca devem chamar a API diretamente.

        Args:
            texto: Texto extraído do documento judicial (PDF, etc.).

        Returns:
            Dicionário com as chaves 'resumo' (str) e 'termos' (list).
            Em caso de erro, retorna um dicionário de fallback descritivo.
        """
        # --- 1. Lê configurações via Application Context ---
        api_key: Optional[str] = current_app.config.get("GEMINI_API_KEY")
        model_name: str = current_app.config.get(
            "GEMINI_MODEL_NAME", "gemini-2.5-flash"
        )

        if not api_key:
            current_app.logger.error(
                "[LLM] GEMINI_API_KEY ausente na config. Abortando tradução."
            )
            return {
                "resumo": "⚠️ Erro de Configuração: A chave da API do Google Gemini (GEMINI_API_KEY) não foi encontrada. Para que o Juridiquê consiga analisar e traduzir o documento conectando-se à IA, você precisa colar a sua chave da API no arquivo .env que está aberto no seu editor.",
                "termos": []
            }

        # --- 2. Instancia o modelo ---
        modelo: Optional[genai.GenerativeModel] = self._criar_modelo(
            api_key, model_name
        )
        if modelo is None:
            return _erro_generico()

        # --- 3. Gera conteúdo ---
        resposta_texto: str = ""
        try:
            current_app.logger.info(
                f"[LLM] Enviando requisição para '{model_name}' "
                f"({len(texto)} caracteres de entrada)."
            )
            response = modelo.generate_content(
                f"Por favor, traduza o seguinte documento jurídico:\n\n{texto}"
            )
            resposta_texto = response.text
            current_app.logger.info("[LLM] Resposta recebida com sucesso.")

        except ResourceExhausted as exc:
            current_app.logger.error(f"[LLM] Quota da API excedida: {exc}")
            return _erro_quota()

        except Exception as exc:  # noqa: BLE001
            current_app.logger.error(
                f"[LLM] Erro ao chamar generate_content "
                f"({type(exc).__name__}): {exc}"
            )
            return _erro_generico()

        # --- 4. Faz parse do JSON retornado ---
        try:
            resposta_limpa: str = self._limpar_markdown(resposta_texto)
            resultado: dict[str, Any] = json.loads(resposta_limpa)
            current_app.logger.info("[LLM] JSON da resposta interpretado com sucesso.")
            return resultado

        except json.JSONDecodeError as exc:
            current_app.logger.error(
                f"[LLM] JSONDecodeError ao interpretar resposta: {exc}\n"
                f"[LLM] Resposta bruta: {resposta_texto!r}"
            )
            return _erro_json()


# ---------------------------------------------------------------------------
# Instância padrão — exportada para uso pelo Application Factory em __init__.py
# ---------------------------------------------------------------------------
llm_service = JuridicoLLMService()
