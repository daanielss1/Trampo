from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

ARQUIVO_VAGAS = "vagas_vistas.json"


# 🔹 CONFIG EMAIL (ALTERAR AQUI)
EMAIL_REMETENTE = "dsilveiralima@gmail.com"
EMAIL_SENHA = "tpqr ucfl nhkz dyzl"
EMAIL_DESTINO = "dsilveiralima@gmail.com"


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


# 🔹 Enviar email
def enviar_email(novas_vagas):
    if not novas_vagas:
        return

    corpo = "🚀 Novas vagas nas últimas 24h:\n\n"

    for vaga in novas_vagas:
        corpo += f"- {vaga['titulo']}\n{vaga['link']}\n\n"

    msg = MIMEText(corpo)
    msg["Subject"] = f"🚀 {len(novas_vagas)} novas vagas encontradas"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINO

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.send_message(msg)
            print("📩 Email enviado com sucesso!")
    except Exception as e:
        print("❌ Erro ao enviar email:", e)


# 🔹 Buscar vagas
def buscar_vagas():
    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil&f_TPR=r432000"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    vagas = []
    vagas_vistas = carregar_vagas_vistas()
    novas_vagas = []

    KEYWORDS = ["product owner", "coordenador de TI", "product manager"]

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

            vaga_id = link

            vaga_formatada = {
                "titulo": titulo.title(),
                "link": link,
                "score": score
            }

            # Detecta novas vagas
            if vaga_id not in vagas_vistas:
                novas_vagas.append(vaga_formatada)
                vagas_vistas.append(vaga_id)

            vagas.append(vaga_formatada)

    # Salva histórico
    salvar_vagas_vistas(vagas_vistas)

    # Ordena por score
    vagas = sorted(vagas, key=lambda x: x["score"], reverse=True)

    return vagas, novas_vagas


# 🔹 Rota principal
@app.route("/")
def home():
    vagas, novas_vagas = buscar_vagas()

    # 🔔 Envia email se houver novas vagas
    if novas_vagas:
        enviar_email(novas_vagas)

    return render_template("index.html", vagas=vagas, novas_vagas=novas_vagas)


# 🔹 Rodar app (Render + local)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)