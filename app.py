from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def buscar_vagas():
    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    vagas = []

    KEYWORDS = ["product owner", "agile", "scrum", "product manager"]

    jobs = soup.find_all("a", class_="base-card__full-link")

    for job in jobs[:30]:
        titulo = job.text.strip().lower()
        link = job["href"]

        # FILTRO INTELIGENTE
        if any(k in titulo for k in KEYWORDS):

            # SCORE (ranking da vaga)
            score = 0
            if "senior" in titulo:
                score += 2
            if "agile" in titulo:
                score += 1
            if "scrum" in titulo:
                score += 1

            vagas.append({
                "titulo": titulo.title(),
                "link": link,
                "score": score
            })

    # Ordena pelas melhores vagas
    vagas = sorted(vagas, key=lambda x: x["score"], reverse=True)

    return vagas


@app.route("/")
def home():
    vagas = buscar_vagas()
    return render_template("index.html", vagas=vagas)


if __name__ == "__main__":
    import os

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
    
    