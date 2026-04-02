from flask import Flask, render_template, redirect
import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import unquote

app = Flask(__name__)

# =========================
# CACHE
# =========================
CACHE_VAGAS = []
ULTIMA_ATUALIZACAO = 0

ARQUIVO_CANDIDATAS = "vagas_candidatas.json"

# =========================
# JSON UTIL
# =========================
def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Erro lendo JSON:", e)
            return []
    return []

def salvar_json(arquivo, dados):
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Erro salvando JSON:", e)

# =========================
# SCRAPING VAGAS
# =========================
def buscar_vagas():
    global CACHE_VAGAS, ULTIMA_ATUALIZACAO

    # cache 10 min
    if time.time() - ULTIMA_ATUALIZACAO < 600 and CACHE_VAGAS:
        print("⚡ Cache ativo")
        return CACHE_VAGAS

    print("🔄 Buscando vagas...")

    url = "https://www.linkedin.com/jobs/search?keywords=product%20owner&location=Brazil&f_TPR=r86400"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }

    KEYWORDS = ["product owner", "product manager", "coordenador de ti"]

    vagas = []
    candidatas = carregar_json(ARQUIVO_CANDIDATAS) or []

    try:
        response = requests.get(url, headers=headers, timeout=10)

        print("Status:", response.status_code)
        print("HTML size:", len(response.text))

        # =========================
        # DETECÇÃO REAL DE BLOQUEIO
        # =========================
        if (
            response.status_code != 200
            or "signin" in response.text.lower()
            or len(response.text) < 8000
        ):
            print("⚠️ Possível bloqueio/login do LinkedIn")

            return CACHE_VAGAS or [{
                "titulo": "LinkedIn bloqueou ou exigiu login",
                "link": "#",
                "score": 0,
                "candidatado": False
            }]

        soup = BeautifulSoup(response.text, "html.parser")

        jobs = soup.find_all("a", class_="base-card__full-link")

        if not jobs:
            jobs = soup.find_all("a")

        for job in jobs[:30]:
            try:
                titulo = (job.text or "").strip().lower()
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

                    vagas.append({
                        "titulo": titulo.title() if titulo else "Sem título",
                        "link": link,
                        "score": score,
                        "candidatado": link in candidatas
                    })

            except Exception as e:
                print("Erro vaga:", e)

    except Exception as e:
        print("Erro scraping:", e)
        return CACHE_VAGAS or []

    if not vagas:
        return CACHE_VAGAS or [{
            "titulo": "Nenhuma vaga encontrada (possível bloqueio)",
            "link": "#",
            "score": 0,
            "candidatado": False
        }]

    vagas = sorted(vagas, key=lambda x: x["score"], reverse=True)

    CACHE_VAGAS = vagas
    ULTIMA_ATUALIZACAO = time.time()

    return vagas

# =========================
# ROTAS
# =========================

@app.route("/")
def home():
    try:
        vagas = buscar_vagas()
        return render_template("index.html", vagas=vagas)
    except Exception as e:
        print("ERRO COMPLETO:", repr(e))
        return f"Erro interno: {repr(e)}"


@app.route("/candidatar/<path:link>")
def candidatar(link):
    try:
        link = unquote(link)

        if not link.startswith("http"):
            return redirect("/")

        candidatas = carregar_json(ARQUIVO_CANDIDATAS) or []

        if link not in candidatas:
            candidatas.append(link)
            salvar_json(ARQUIVO_CANDIDATAS, candidatas)

        return redirect("/")

    except Exception as e:
        print("Erro candidatar:", e)
        return redirect("/")


@app.route("/health")
def health():
    return "ok"


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)