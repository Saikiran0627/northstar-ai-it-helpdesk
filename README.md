# Northstar AI IT Help Desk

AI-powered IT Help Desk for the fictional company Northstar Technologies. The app is a local Python/Streamlit demo with:

- Interactive AI chat interface.
- Local RAG over fictional IT support documents using TF-IDF.
- Agent orchestration that can answer, retrieve documents, call simulated tools, and ask clarifying questions.
- Simulated service status checks and SQLite support ticket creation.
- Conversation memory in the Streamlit session.
- Explicit confirmation before any ticket is created.
- Prompt-injection screening and basic source sanitization.
- Agent execution traces without exposing private model reasoning.
- Evaluation dashboard for answer quality, latency, and tool execution success.

## What I found in this environment

- Python 3.12 is available.
- No Python dependencies or database were preinstalled for this project.
- The app keeps everything local except the optional Claude API call.
- `.env` is ignored by git and must not be committed.

## What you need to provide

Copy `.env.example` to `.env` and fill in your Azure-hosted Claude values:

```bash
cp .env.example .env
```

Required values:

- `CLAUDE_API_ENDPOINT`
- `CLAUDE_API_KEY`
- `CLAUDE_MODEL`
- `CLAUDE_API_VERSION` if required by your Azure endpoint

If these values are missing, the app still runs with deterministic local fallback responses so you can test the workflow without credentials.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the app

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Try:

> My VPN keeps disconnecting. I am working remotely, and I have a client presentation in 30 minutes. Can you help?

The assistant should retrieve VPN and remote work guidance, check simulated VPN service status, recommend troubleshooting steps, explain its actions, and draft a high-priority ticket only after asking for confirmation. Reply `confirm` to create the ticket.

## Run tests

```bash
source .venv/bin/activate
pytest
```

## Project structure

```text
data/knowledge/                 Fictional IT knowledge documents
src/northstar_helpdesk/         Agent, RAG, tools, SQLite, safety, and evaluation modules
tests/                          Unit tests
streamlit_app.py                Streamlit UI
.env.example                    Safe template for local secrets
```

## Notes on Azure Claude integration

Cloud providers expose Claude-compatible endpoints with slightly different response shapes. The app sends a Claude Messages-style request with both `api-key` and `x-api-key` headers and parses common Claude and OpenAI-compatible response formats. If your Azure endpoint uses a different route, set `CLAUDE_API_ENDPOINT` to the complete invocation URL expected by your deployment.
