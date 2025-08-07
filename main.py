import os
from typing import List, Dict
from dotenv import load_dotenv
import requests
import json
import google.generativeai as genai
from requests.auth import HTTPBasicAuth

load_dotenv(dotenv_path=".env")

# JIRA SETTINGS
JIRA_BASE_URL = f"https://{os.getenv('JIRA_DOMAIN')}.atlassian.net"
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_TOKEN")
NEW_VERSION_STATUS = ["HM", "NOVA VERSÃO"]
PROJECT = os.getenv("JIRA_PROJECT")
SPRINT = os.getenv("JIRA_SPRINT")

# GEMINI SETTINGS
genai.configure(api_key=os.getenv("GEMINI_KEY"))
MODEL = "gemini-2.5-pro"

# Build JQL query string
status_str = ", ".join(f'"{s}"' for s in NEW_VERSION_STATUS)
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

def extract_issues_with_comments(data: List[Dict]) -> List[Dict[str, str]]:
    result = []

    for issue in data:
        fields = issue.get("fields", {})
        comments = fields.get("comment", {}).get("comments", [])

        result.append({
            "id": issue.get("key", ""),
            "summary": fields.get("summary", ""),
            "status": fields.get("status", {}).get("name", ""),
            "priority": fields.get("priority", {}).get("name", ""),
            "assignee": fields.get("assignee", {}).get("displayName", ""),
            "created_at": fields.get("created", ""),
            "updated_at": fields.get("updated", ""),
            "planned_start": fields.get("customfield_10041", ""),  # adjust for your field
            "planned_end": fields.get("customfield_10042", ""),    # adjust for your field
            "comments": [
                {
                    "author": c.get("author", {}).get("displayName", ""),
                    "date": c.get("created", ""),
                    "message": c.get("body", "")
                }
                for c in comments
            ]
        })

    return result

def generate_summary_with_gemini(data_json: List[Dict]):
    json_content = json.dumps(data_json, indent=2, ensure_ascii=False)

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
{json_content}
    """

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)

    return response.text


if __name__ == "__main__":
    issues = fetch_issues(JQL)
    tasks = extract_issues_with_comments(issues)
    summary = generate_summary_with_gemini(tasks)
    print("\n📦 EXPLICAÇÃO DA NOVA VERSÃO:\n")
    print(summary)
