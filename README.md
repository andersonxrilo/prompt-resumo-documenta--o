# Jira Sprint Summarizer

This project contains two small scripts for generating release notes from Jira issues using either Google Gemini or OpenAI models. Both scripts fetch issues from Jira based on a JQL query and then ask the language model to produce a human‑friendly summary in Portuguese.

## Requirements

- Python 3.10+
- Access to the required APIs (Jira, Google Gemini and/or OpenAI)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with the following variables:

- `JIRA_DOMAIN` – your Jira domain (without protocol)
- `JIRA_EMAIL` – Jira account email
- `JIRA_TOKEN` – Jira API token
- `JIRA_PROJECT` – project key
- `JIRA_SPRINT` – sprint identifier
- `GEMINI_KEY` – API key for Google Gemini (used in `main.py`)
- `GPT_KEY` – API key for OpenAI (used in `main_gpt.py`)

## Usage

Two entry points are provided:

```bash
python main.py      # uses Google Gemini
python main_gpt.py  # uses OpenAI
```

Both commands will print the summary of the new version to the console.
