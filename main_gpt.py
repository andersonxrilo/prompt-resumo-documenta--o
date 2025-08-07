import json
import os

import requests
from openai import OpenAI
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

# JIRA SETTINGS
JIRA_BASE_URL = f"https://{os.getenv('JIRA_DOMAIN')}.atlassian.net"
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_TOKEN")
NEW_VERSION_STATUS = ["HM", "NOVA VERSÃO"]
PROJECT = os.getenv("JIRA_PROJECT")
SPRINT = os.getenv("JIRA_SPRINT")

# OPENAI SETTINGS
# openai.api_key = os.getenv("GPT_KEY")  # Your OpenAI API Key
MODEL = "gpt-4.1"  # or gpt-3.5-turbo
# Build list of status with quotes
status_str = ", ".join(f'"{s}"' for s in NEW_VERSION_STATUS)
# JQL ASSEMBLY
JQL = f"project = {PROJECT} AND sprint = {SPRINT} AND status in ({status_str})"
HEADERS = {"Accept": "application/json"}


def fetch_issues(jql: str):
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql, "maxResults": 100}

    response = requests.get(
        url, headers=HEADERS, params=params, auth=HTTPBasicAuth(EMAIL, API_TOKEN)
    )
    response.raise_for_status()
    return response.json()["issues"]


def prepare_tasks_for_llm(issues):
    tasks = []
    for issue in issues:
        fields = issue["fields"]
        task = {
            "key": issue["key"],
            "type": fields["issuetype"]["name"],
            "summary": fields["summary"],
            "status": fields["status"]["name"]
        }
        tasks.append(task)
    return tasks


def generate_summary_with_ai(tasks):
    json_content = json.dumps(tasks, indent=2, ensure_ascii=False)

    prompt = f"""
    Você é um assistente de produto. Receberá a resposta crua de uma API do Jira que contém tarefas de uma sprint.

    Seu objetivo é ler o JSON e escrever um resumo claro e objetivo do que está sendo lançado nesta versão. Explique agrupando por tipo (bugs, histórias, tarefas técnicas, etc) e escreva em português.

    JSON da API Jira:
    {json_content}
        """

    client = OpenAI(api_key=os.getenv("GPT_KEY"))  # your key here

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    issues = fetch_issues(JQL)
    tasks = prepare_tasks_for_llm(issues)
    summary = generate_summary_with_ai(tasks)
    print("\n📦 EXPLICAÇÃO DA NOVA VERSÃO:\n")
    print(summary)
