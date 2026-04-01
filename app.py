from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

ARQUIVO_VAGAS = "vagas_vistas.json"


# 🔹 Carregar vagas já vistas
def carregar_vagas_vistas():
    if os.path.exists(ARQUIVO_VAGAS):
        with open(ARQUIVO_VAGAS, "r") as f:
            return json.load(f)
    return []


# 🔹 Salvar vagas vistas
def salvar_vagas_vistas(vagas):
    with open(ARQUIVO_VAGAS, "w") as f:
        json.dump(vagas, f)


# 🔹 Buscar vagas
def buscar_vagas():
    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil&f_TPR=r86400"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    vagas = []
    vagas_vistas = carregar_vagas_vistas()
    novas_vagas = []

    KEYWORDS = ["product owner", "agile", "scrum", "product manager"]

    jobs = soup.find_all("a", class_="base-card__full-link")

    for job in jobs[:30]:
        titulo = job.text.strip().lower()
        link = job["href"]

        # FILTRO INTELIGENTE
        if any(k in titulo for k in KEYWORDS):

            # SCORE (ranking)
            score = 0
            if "senior" in titulo:
                score += 2
            if "agile" in titulo:
                score += 1
            if "scrum" in titulo:
                score += 1

            vaga_id = link  # identificador único

            # Detecta novas vagas
            if vaga_id not in vagas_vistas:
                novas_vagas.append(titulo.title())
                vagas_vistas.append(vaga_id)

            vagas.append({
                "titulo": titulo.title(),
                "link": link,
                "score": score
            })

    # Salva histórico
    salvar_vagas_vistas(vagas_vistas)

    # Ordena por score
    vagas = sorted(vagas, key=lambda x: x["score"], reverse=True)

    return vagas, novas_vagas


# 🔹 Rota principal
@app.route("/")
def home():
    vagas, novas_vagas = buscar_vagas()
    return render_template("index.html", vagas=vagas, novas_vagas=novas_vagas)


# 🔹 Rodar app (Render + local)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)