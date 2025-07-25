import os
import re
from typing import List, Dict
from dotenv import load_dotenv
import requests
import json
import google.generativeai as genai
from requests.auth import HTTPBasicAuth
load_dotenv(dotenv_path=".env")
# CONFIGURAÇÕES JIRA
JIRA_BASE_URL = "https://guardcenter.atlassian.net"
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_TOKEN")
STATUS_COLUNA_NOVA_VERSAO = ["HM", "NOVA VERSÃO"]
PROJETO = "GC"
SPRINT = "103"

# CONFIGURAÇÕES GEMINI
genai.configure(api_key=os.getenv("GEMINI_KEY"))
MODEL = "gemini-2.5-pro"

# Gera string da JQL corretamente
status_str = ", ".join(f'"{s}"' for s in STATUS_COLUNA_NOVA_VERSAO)
JQL = f'project = {PROJETO} AND sprint = {SPRINT} AND status in ({status_str})'
HEADERS = {"Accept": "application/json"}


def buscar_issues(jql):
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql, "maxResults": 100}
    response = requests.get(
        url, headers=HEADERS, params=params, auth=HTTPBasicAuth(EMAIL, API_TOKEN)
    )

    if response.status_code != 200:
        raise Exception(f"Erro: {response.status_code} - {response.text}")

    return response.json()["issues"]

def extrair_issues_com_comentarios(dados: List[Dict]) -> List[Dict[str, str]]:
    resultado = []

    for issue in dados:
        fields = issue.get("fields", {})
        comentarios = fields.get("comment", {}).get("comments", [])

        resultado.append({
            "id": issue.get("key", ""),
            "resumo": fields.get("summary", ""),
            "status": fields.get("status", {}).get("name", ""),
            "prioridade": fields.get("priority", {}).get("name", ""),
            "responsavel": fields.get("assignee", {}).get("displayName", ""),
            "data_criacao": fields.get("created", ""),
            "data_atualizacao": fields.get("updated", ""),
            "previsao_inicio": fields.get("customfield_10041", ""),  # ajuste conforme seu campo real
            "previsao_fim": fields.get("customfield_10042", ""),     # ajuste conforme seu campo real
            "comentarios": [
                {
                    "autor": c.get("author", {}).get("displayName", ""),
                    "data": c.get("created", ""),
                    "mensagem": c.get("body", "")
                }
                for c in comentarios
            ]
        })

    return resultado

def gerar_explicacao_com_gemini(dados_json):
    conteudo_json = json.dumps(dados_json, indent=2, ensure_ascii=False)

    prompt = f"""
Você é um assistente de produto. Receberá a resposta crua da API do Jira com tarefas da sprint.

Seu objetivo é:
- Ler o JSON completo abaixo.
- Explicar, em português, de forma executiva e clara, o que está sendo lançado nesta versão.
- Agrupar por tipo: bugs, histórias, melhorias, tarefas técnicas, etc.
- Preparar uma documentação pronta de toda atualização (incluindo imagens que estão dentro das tarefas).
- Não precisa incluir ou mencionar responsáveis por tarefas.
- a saída deve ser um um html estiloso(layout flat)

JSON da API Jira:
{conteudo_json}
    """

    model = genai.GenerativeModel(MODEL)
    resposta = model.generate_content(prompt)

    return resposta.text


if __name__ == "__main__":
    resultado = buscar_issues(JQL)
    tarefas = extrair_issues_com_comentarios(resultado)
    explicacao = gerar_explicacao_com_gemini(resultado)
    print("\n📦 EXPLICAÇÃO DA NOVA VERSÃO:\n")
    print(explicacao)
