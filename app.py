# app.py (Parte 1)
import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importando o que criamos no outro arquivo:
from config import GUN_SCHEMA, SYSTEM_INSTRUCTION

# Carrega as variáveis de ambiente e inicia o Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Garante que a chave existe antes de iniciar o cliente
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# Inicializa o Flask
app = Flask(__name__)
CORS(app)


# app.py (Parte 2)


def generate_weapon(descricao_input):
    # Verifica se o cliente global do Gemini foi devidamente inicializado
    if client is None:
        raise RuntimeError(
            "O cliente Gemini não foi inicializado. Verifique a chave de API."
        )

    # Tratamento seguro do input: aceita tanto lista (arrays) quanto string direta
    if isinstance(descricao_input, list):
        descricao_formatada = ", ".join(descricao_input)
    else:
        descricao_formatada = str(descricao_input)

    # Construção do prompt contextualizado com foco no perfil do cliente
    conteudo_prompt = (
        f"O cliente se descreveu da seguinte forma: {descricao_formatada}. "
        f"Com base nesse perfil psicológico e operacional, selecione a plataforma "
        f"de armamento ideal e os acessórios de marcas reais e renomadas no ramo tático."
    )

    # Chamada ao modelo utilizando a API estável e Structured Outputs
    response = client.models.generate_content(
        model="gemini-3-flash-preview",  # Versão estável de produção
        contents=conteudo_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GUN_SCHEMA,  # Alinhado com o nome do seu config.py
            temperature=0.65,
        ),
    )

    return response.text


# app.py (Parte 3)


@app.route("/")
def root():
    return (
        jsonify(
            {
                "status": "success",
                "message": "API Sommelier de Armas do Continental ativa!",
                "version": "1.0",
            }
        ),
        200,
    )


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()

    # Validação 1: O JSON foi enviado e contém a chave 'perfil'?
    if not data or "perfil" not in data:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Por favor, envie o perfil do usuário no formato JSON usando a chave 'perfil'.",
                }
            ),
            400,
        )

    perfil = data.get("perfil", [])

    # Validação 2: É uma lista e possui no mínimo 3 características/tags?
    if not isinstance(perfil, list) or len(perfil) < 3:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Você precisa fornecer no mínimo 3 características ou palavras-chave sobre o perfil.",
                }
            ),
            400,
        )

    try:
        # Pede para o Gemini gerar a arma customizada (retorna como string JSON)
        arma_json_string = generate_weapon(perfil)

        # Converte a string JSON em Dicionário Python para o Flask organizar a resposta
        arma_estruturada = json.loads(arma_json_string)

        return (
            jsonify(
                {
                    "status": "success",
                    "perfil_analisado": perfil,
                    "dados_arma": arma_estruturada,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Erro ao processar a recomendação do Sommelier: {str(e)}",
                }
            ),
            500,
        )


# Executa o servidor local
if __name__ == "__main__":
    app.run(debug=True)
