from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

ARQUIVO_VAGAS = "vagas_vistas.json"


# 🔹 Carregar vagas já vistas (com proteção)
def carregar_vagas_vistas():
    if os.path.exists(ARQUIVO_VAGAS):
        try:
            with open(ARQUIVO_VAGAS, "r") as f:
                return json.load(f)
        except:
            return []
    return []


# 🔹 Salvar vagas vistas (com proteção)
def salvar_vagas_vistas(vagas):
    try:
        with open(ARQUIVO_VAGAS, "w") as f:
            json.dump(vagas, f)
    except:
        pass


# 🔹 Buscar vagas (últimas 24h)
def buscar_vagas():
    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil&f_TPR=r43200"
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
        try:
            titulo = job.text.strip().lower() if job.text else ""
            link = job.get("href")

            # valida dados
            if not titulo or not link:
                continue

            # 🔎 FILTRO POR PALAVRA-CHAVE
            if any(k in titulo for k in KEYWORDS):

                # ⭐ SCORE (ranking)
                score = 0
                if "senior" in titulo:
                    score += 2
                if "agile" in titulo:
                    score += 1
                if "scrum" in titulo:
                    score += 1

                vaga_id = link

                vaga_formatada = {
                    "titulo": titulo.title() if titulo else "Sem título",
                    "link": link if link else "#",
                    "score": score
                }

                # Evita duplicadas
                if vaga_id not in vagas_vistas:
                    vagas_vistas.append(vaga_id)
                    vagas.append(vaga_formatada)

        except:
            continue  # ignora qualquer erro individual de parsing

    # 💾 Salva histórico
    salvar_vagas_vistas(vagas_vistas)

    # 🔽 Ordena por relevância
    vagas = sorted(vagas, key=lambda x: x.get("score", 0), reverse=True)

    print("Vagas encontradas:", len(vagas))  # debug

    return vagas


# 🔹 Rota principal
@app.route("/")
def home():
    try:
        vagas = buscar_vagas()
        return render_template("index.html", vagas=vagas)
    except Exception as e:
        return f"Erro interno: {str(e)}", 500


# 🔹 Rodar app (Render + local)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)