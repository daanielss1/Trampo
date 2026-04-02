from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

VAGAS_FILE = "vagas.json"
APLICADAS_FILE = "aplicadas.json"


# -----------------------------
# Helpers
# -----------------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------
# Simulador de vagas (substituir futuramente por API)
# -----------------------------
def get_vagas():
    vagas = load_json(VAGAS_FILE)
    aplicadas = load_json(APLICADAS_FILE)

    return vagas, aplicadas


# -----------------------------
# Filtragem de tempo
# -----------------------------
def filtrar_por_tempo(vagas, horas):
    limite = datetime.now() - timedelta(hours=horas)

    filtradas = []
    for v in vagas:
        data_vaga = datetime.fromisoformat(v["timestamp"])
        if data_vaga >= limite:
            filtradas.append(v)

    return sorted(filtradas, key=lambda x: x["timestamp"], reverse=True)


# -----------------------------
# Rotas
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/vagas")
def vagas():
    filtro = request.args.get("filtro", "24h")

    vagas, aplicadas = get_vagas()

    ids_aplicados = {v["id"] for v in aplicadas}

    if filtro == "12h":
        vagas_filtradas = filtrar_por_tempo(vagas, 12)
    else:
        vagas_filtradas = filtrar_por_tempo(vagas, 24)

    # remover aplicadas da lista principal
    vagas_filtradas = [v for v in vagas_filtradas if v["id"] not in ids_aplicados]

    return jsonify(vagas_filtradas)


@app.route("/api/aplicadas")
def aplicadas():
    return jsonify(load_json(APLICADAS_FILE))


@app.route("/api/marcar_aplicada", methods=["POST"])
def marcar_aplicada():
    data = request.json

    vagas = load_json(VAGAS_FILE)
    aplicadas = load_json(APLICADAS_FILE)

    vaga = next((v for v in vagas if v["id"] == data["id"]), None)

    if vaga and vaga not in aplicadas:
        aplicadas.append(vaga)
        save_json(APLICADAS_FILE, aplicadas)

    return jsonify({"status": "ok"})


# -----------------------------
# MOCK inicial (caso vazio)
# -----------------------------
@app.route("/api/seed")
def seed():
    if not os.path.exists(VAGAS_FILE):
        agora = datetime.now()

        vagas_mock = [
            {
                "id": "1",
                "titulo": "Analista de Sistemas",
                "empresa": "Tech Brasil",
                "timestamp": (agora - timedelta(hours=2)).isoformat()
            },
            {
                "id": "2",
                "titulo": "Engenheiro de Software",
                "empresa": "Startup X",
                "timestamp": (agora - timedelta(hours=10)).isoformat()
            },
            {
                "id": "3",
                "titulo": "Dev Backend Python",
                "empresa": "AI Solutions",
                "timestamp": (agora - timedelta(hours=30)).isoformat()
            }
        ]

        save_json(VAGAS_FILE, vagas_mock)

    return {"status": "seed ok"}


if __name__ == "__main__":
    app.run(debug=True)