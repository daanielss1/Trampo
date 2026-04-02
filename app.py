from flask import Flask, render_template, redirect
import requests
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
# JSON
# =========================
def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_json(arquivo, dados):
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Erro JSON:", e)

# =========================
# FONTES DE VAGAS (ESTÁVEIS)
# =========================

def fetch_greenhouse():
    """
    Exemplo API pública da Greenhouse (muitas empresas usam)
    """
    url = "https://boards-api.greenhouse.io/v1/boards/lyft/jobs?content=true"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        vagas = []
        for job in data.get("jobs", [])[:20]:
            vagas.append({
                "titulo": job.get("title"),
                "link": job.get("absolute_url"),
                "score": 1,
                "candidatado": False
            })
        return vagas
    except:
        return []

def fetch_lever():
    """
    API pública Lever (muito estável)
    """
    url = "https://api.lever.co/v0/postings/lever?mode=json"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        vagas = []
        for job in data[:20]:
            vagas.append({
                "titulo": job.get("text"),
                "link": job.get("hostedUrl"),
                "score": 1,
                "candidatado": False
            })
        return vagas
    except:
        return []

# =========================
# BUSCA UNIFICADA
# =========================
def buscar_vagas():
    global CACHE_VAGAS, ULTIMA_ATUALIZACAO

    if time.time() - ULTIMA_ATUALIZACAO < 600 and CACHE_VAGAS:
        print("⚡ Cache ativo")
        return CACHE_VAGAS

    print("🔄 Buscando vagas (APIs estáveis)...")

    candidatas = carregar_json(ARQUIVO_CANDIDATAS)

    vagas = []
    vagas += fetch_greenhouse()
    vagas += fetch_lever()

    # normaliza + marca candidatas
    for v in vagas:
        v["candidatado"] = v["link"] in candidatas

    if not vagas:
        vagas = [{
            "titulo": "Nenhuma vaga encontrada no momento",
            "link": "#",
            "score": 0,
            "candidatado": False
        }]

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
        print("ERRO:", repr(e))
        return f"Erro interno: {repr(e)}"


@app.route("/candidatar/<path:link>")
def candidatar(link):
    try:
        link = unquote(link)

        candidatas = carregar_json(ARQUIVO_CANDIDATAS)

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