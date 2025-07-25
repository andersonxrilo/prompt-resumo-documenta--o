import json
import os

import requests
from openai import OpenAI
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

# CONFIGURAÇÕES JIRA
JIRA_BASE_URL = "https://guardcenter.atlassian.net"
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_TOKEN")
STATUS_COLUNA_NOVA_VERSAO = ["HM", "NOVA VERSÃO"]
PROJETO = "GC"
SPRINT = "270225"

# CONFIGURAÇÕES OPENAI
# openai.api_key = os.getenv("GPT_KEY")  # Sua API Key da OpenAI
MODEL = "gpt-4.1"  # ou gpt-3.5-turbo
# Monte a lista de status com aspas
status_str = ", ".join(f'"{s}"' for s in STATUS_COLUNA_NOVA_VERSAO)
# MONTAGEM DA JQL
JQL = f'project = {PROJETO} AND status in ({status_str})'
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


def preparar_tarefas_para_llm(issues):
    tarefas = []
    for issue in issues:
        fields = issue["fields"]
        tarefa = {
            "chave": issue["key"],
            "tipo": fields["issuetype"]["name"],
            "resumo": fields["summary"],
            "status": fields["status"]["name"]
        }
        tarefas.append(tarefa)
    return tarefas


def gerar_explicacao_com_ia(tarefas):
    conteudo_json = json.dumps(tarefas, indent=2, ensure_ascii=False)

    prompt = f"""
    Você é um assistente de produto. Receberá a resposta crua de uma API do Jira que contém tarefas de uma sprint.

    Seu objetivo é ler o JSON e escrever um resumo claro e objetivo do que está sendo lançado nesta versão. Explique agrupando por tipo (bugs, histórias, tarefas técnicas, etc) e escreva em português.

    JSON da API Jira:
    {conteudo_json}
        """

    client = OpenAI(api_key=os.getenv("GPT_KEY"))  # sua chave aqui

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    issues = buscar_issues(JQL)
    tarefas = preparar_tarefas_para_llm(issues)
    # print(tarefas)
    explicacao = gerar_explicacao_com_ia(tarefas)
    print("\n📦 EXPLICAÇÃO DA NOVA VERSÃO:\n")
    print(explicacao)
