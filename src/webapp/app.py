# src/webapp/app.py
import os
import sys
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

# Caminho para src/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

# Importa Orquestrador
from agent_orchestrator import TobyOrchestrator

# Carrega .env na pasta src/
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("GROQ_API_KEY não definida no .env!")

bot = TobyOrchestrator()

# app aponta para o diretório atual (webapp/)
WEBAPP_DIR = os.path.dirname(__file__)
app = Flask(__name__, static_folder=WEBAPP_DIR)


@app.route("/")
def index():
    return send_from_directory(WEBAPP_DIR, "index.html")


@app.route("/style.css")
def css():
    return send_from_directory(WEBAPP_DIR, "style.css")


@app.route("/chat.js")
def js():
    return send_from_directory(WEBAPP_DIR, "chat.js")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    try:
        resposta = bot.ask(message)
        return jsonify({"reply": resposta})
    except Exception as e:
        return jsonify({"error": f"Erro interno: {e}"}), 500


if __name__ == "__main__":
    print("Servidor iniciado em http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
