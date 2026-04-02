from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import json
import os
import time

app = Flask(__name__)

# 🔹 Cache (evita travamento no Render)
CACHE_VAGAS = []
ULTIMA_ATUALIZACAO = 0

ARQUIVO_CANDIDATAS = "vagas_candidatas.json"


# 🔹 Utilidades JSON
def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def salvar_json(arquivo, dados):
    try:
        with open(arquivo, "w") as f:
            json.dump(dados, f)
    except:
        pass


# 🔹 Buscar vagas (com proteção)
def buscar_vagas():
    global CACHE_VAGAS, ULTIMA_ATUALIZACAO

    # ⏱️ Cache de 10 minutos
    if time.time() - ULTIMA_ATUALIZACAO < 600 and CACHE_VAGAS:
        print("⚡ Usando cache...")
        return CACHE_VAGAS

    print("🔄 Buscando vagas no LinkedIn...")

    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil&f_TPR=r86400"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    }

    vagas = []
    candidatas = carregar_json(ARQUIVO_CANDIDATAS)

    KEYWORDS = ["product owner", "product manager", "coordenador de ti"]

    try:
        response = requests.get(url, headers=headers, timeout=8)

        print("Status:", response.status_code)
        print("Tamanho HTML:", len(response.text))

        # 🔴 Se bloqueado → usa cache antigo
        if response.status_code != 200 or len(response.text) < 10000:
            print("⚠️ Possível bloqueio do LinkedIn")
            return CACHE_VAGAS if CACHE_VAGAS else []

        soup = BeautifulSoup(response.text, "html.parser")

        jobs = soup.find_all("a", class_="base-card__full-link")

        # 🔄 fallback se estrutura mudou
        if not jobs:
            print("⚠️ Estrutura mudou, fallback geral")
            jobs = soup.find_all("a")

        for job in jobs[:30]:
            try:
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

                    vaga = {
                        "titulo": titulo.title() if titulo else "Sem título",
                        "link": link,
                        "score": score,
                        "candidatado": link in candidatas
                    }

                    vagas.append(vaga)

            except Exception as e:
                print("Erro ao processar vaga:", e)
                continue

    except Exception as e:
        print("❌ Erro geral scraping:", e)
        return CACHE_VAGAS if CACHE_VAGAS else []

    # 🔴 Se não achou nada → evita tela vazia
    if not vagas:
        print("⚠️ Nenhuma vaga encontrada")
        return CACHE_VAGAS if CACHE_VAGAS else [
            {
                "titulo": "Nenhuma vaga encontrada no momento (LinkedIn pode ter bloqueado)",
                "link": "#",
                "score": 0,
                "candidatado": False
            }
        ]

    # 🔽 Ordena por score
    vagas = sorted(vagas, key=lambda x: x["score"], reverse=True)

    # 💾 Atualiza cache
    CACHE_VAGAS = vagas
    ULTIMA_ATUALIZACAO = time.time()

    return vagas


# 🔹 Página principal
@app.route("/")
def home():
    try:
        vagas = buscar_vagas()
        return render_template("index.html", vagas=vagas)
    except Exception as e:
        print("❌ Erro na rota /:", e)
        return "Erro interno, tente novamente"


# 🔹 Health check (teste rápido)
@app.route("/health")
def health():
    return "ok"


# 🔹 Rodar local/Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)