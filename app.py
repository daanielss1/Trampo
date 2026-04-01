from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

ARQUIVO_VAGAS = "vagas_vistas.json"


def carregar_vagas_vistas():
    if os.path.exists(ARQUIVO_VAGAS):
        with open(ARQUIVO_VAGAS, "r") as f:
            return json.load(f)
    return []


def salvar_vagas_vistas(vagas):
    with open(ARQUIVO_VAGAS, "w") as f:
        json.dump(vagas, f)


def buscar_vagas():
    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil&f_TPR=r86400"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    vagas = []
    vagas_vistas = carregar_vagas_vistas()

    KEYWORDS = ["product owner", "coordenador de ti", "product manager"]

    jobs = soup.find_all("a", class_="base-card__full-link")

    for job in jobs[:30]:
        titulo = job.text.strip().lower() if job.text else ""
        link = job.get("href")

        if not link:
            continue

        if any(k in titulo for k in KEYWORDS):

            score = 0
            if "senior" in titulo:
                score += 2
            if "agile" in titulo:
                score += 1
            if "scrum" in titulo:
                score += 1

            vaga_formatada = {
                "titulo": titulo.title() if titulo else "Sem título",
                "link": link,
                "score": score
            }

            if link not in vagas_vistas:
                vagas_vistas.append(link)

            vagas.append(vaga_formatada)

    salvar_vagas_vistas(vagas_vistas)

    vagas = sorted(vagas, key=lambda x: x["score"], reverse=True)

    return vagas


@app.route("/")
def home():
    vagas = buscar_vagas() or []
    return render_template("index.html", vagas=vagas)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)