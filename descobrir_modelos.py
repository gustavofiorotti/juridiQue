"""
Script de Troubleshooting -- Descoberta de Modelos Gemini Disponiveis
=====================================================================
Lista todos os modelos acessiveis pela API key configurada no .env
que suportam o metodo 'generateContent'. Destaca a familia "flash".

Uso:
    .\\venv\\Scripts\\python.exe descobrir_modelos.py

Requisitos (ja instalados no venv):
    google-genai python-dotenv
"""

import os
from typing import Optional

from dotenv import load_dotenv

try:
    from google import genai
    SDK = "google.genai"
except ImportError:
    import google.generativeai as genai  # type: ignore[no-redef]
    SDK = "google.generativeai (legado)"


def descobrir_modelos() -> None:
    """Configura o SDK e imprime os modelos disponiveis para generateContent."""
    load_dotenv()

    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERRO] GEMINI_API_KEY nao encontrada no .env.")
        return

    print(f"\n[INFO] SDK em uso: {SDK}")
    print("=" * 55)
    print("  Modelos Gemini disponiveis para generateContent")
    print("=" * 55)

    modelos_flash: list[str] = []
    modelos_outros: list[str] = []

    try:
        # SDK novo: google.genai
        if SDK == "google.genai":
            client = genai.Client(api_key=api_key)
            modelos_iter = client.models.list()
        else:
            # SDK legado: google.generativeai
            genai.configure(api_key=api_key)
            modelos_iter = genai.list_models()

        for modelo in modelos_iter:
            # SDK novo usa .name; legado usa .name com prefixo "models/"
            nome: str = getattr(modelo, "name", str(modelo))

            # Verifica suporte a generateContent (SDK legado)
            metodos = getattr(modelo, "supported_generation_methods", None)
            if metodos is not None and "generateContent" not in metodos:
                continue

            nome_limpo: str = nome.removeprefix("models/")

            if "flash" in nome.lower():
                modelos_flash.append(nome_limpo)
                tag = "[FLASH ***]"
            else:
                modelos_outros.append(nome_limpo)
                tag = "[outro]    "

            print(f"  {tag}  {nome_limpo}")

    except Exception as exc:  # noqa: BLE001
        print(f"[ERRO] Falha ao listar modelos: {type(exc).__name__}: {exc}")
        return

    print("=" * 55)
    print(f"\nTotal compativel: {len(modelos_flash) + len(modelos_outros)}")
    print(f"  Familia Flash : {len(modelos_flash)} modelo(s)")
    print(f"  Outros        : {len(modelos_outros)} modelo(s)")

    if modelos_flash:
        print("\nModelos Flash -- sugeridos para GEMINI_MODEL_NAME:")
        for m in modelos_flash:
            print(f"  -> {m}")

    print()


if __name__ == "__main__":
    descobrir_modelos()
