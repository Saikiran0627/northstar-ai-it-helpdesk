# Demo 1 Submission: Vibe Coding - Northstar AI IT Help Desk

## Project overview

This project is a local Python and Streamlit demonstration of an AI-powered IT Help Desk for the fictional company Northstar Technologies. The application is designed for the Demo 1 "Vibe Coding" assignment, where the project is built iteratively from a high-level prompt instead of starting with a formal specification phase.

The main user scenario is:

> My VPN keeps disconnecting. I am working remotely, and I have a client presentation in 30 minutes. Can you help?

The application responds by searching local support documents, checking simulated VPN service status, recommending troubleshooting steps, explaining what actions it took, and preparing a support ticket only after the user explicitly confirms ticket creation.

## Objectives

The objectives of the project are to:

- Provide an interactive help desk chat experience.
- Use local retrieval-augmented generation (RAG) over fictional IT policy documents.
- Demonstrate simple agent routing between clarification, retrieval, service-status tools, and ticket workflows.
- Store support tickets and trace/evaluation records in SQLite.
- Show execution traces without revealing private model reasoning.
- Include safety controls such as prompt-injection screening and confirmation before ticket creation.
- Provide a local evaluation dashboard and automated tests.
- Keep secrets out of source code and load optional Claude configuration from `.env`.

## Technologies and libraries used

The project dependencies are defined in `pyproject.toml` and `requirements.txt`.

| Area | Technology | Purpose |
| --- | --- | --- |
| Web UI | Streamlit | Interactive chat interface, trace panel, ticket table, and evaluation dashboard |
| Data display | pandas | Display trace, ticket, and evaluation tables in Streamlit |
| RAG retrieval | scikit-learn `TfidfVectorizer` and cosine similarity | Local TF-IDF document retrieval without a vector database |
| Configuration | python-dotenv | Load optional `.env` values for Claude and local database path |
| HTTP client | requests | Send optional Claude API requests when credentials are configured |
| Persistence | SQLite through Python `sqlite3` | Store support tickets, execution traces, and evaluation results |
| Testing | pytest | Automated tests for agent, retrieval, evaluation, and security behavior |
| Optional model package | anthropic | Listed as a dependency, but the current implementation uses `requests` for the configurable Claude endpoint |

## Project structure

```text
.
|-- README.md
|-- .env.example
|-- pyproject.toml
|-- requirements.txt
|-- streamlit_app.py
|-- data/
|   `-- knowledge/
|       |-- email-outlook.md
|       |-- mfa-identity-access.md
|       |-- remote-work-policy.md
|       |-- ticket-escalation-policy.md
|       `-- vpn-remote-access.md
|-- src/
|   `-- northstar_helpdesk/
|       |-- agent.py
|       |-- config.py
|       |-- evaluation.py
|       |-- knowledge_base.py
|       |-- llm.py
|       |-- models.py
|       |-- security.py
|       |-- ticket_store.py
|       `-- tools.py
`-- tests/
    |-- conftest.py
    |-- test_agent.py
    |-- test_evaluation.py
    `-- test_knowledge_base.py
```

## Application architecture and workflow

The application has five main layers:

1. **Streamlit UI (`streamlit_app.py`)**
   - Displays the chat interface.
   - Stores conversation messages in `st.session_state`.
   - Shows the latest execution trace.
   - Shows support tickets from SQLite.
   - Runs and displays evaluation results.

2. **Agent orchestration (`src/northstar_helpdesk/agent.py`)**
   - Screens user input for prompt-injection patterns.
   - Classifies the request as clarification, troubleshooting, or answer.
   - Retrieves documents from the knowledge base.
   - Calls simulated tools when service terms are detected.
   - Drafts tickets when appropriate and requires confirmation before creation.
   - Logs execution trace steps to SQLite.

3. **Retrieval layer (`src/northstar_helpdesk/knowledge_base.py`)**
   - Loads Markdown knowledge documents from `data/knowledge`.
   - Builds a local TF-IDF matrix.
   - Returns the most similar documents for a user query.

4. **Model adapter (`src/northstar_helpdesk/llm.py`)**
   - If Claude environment settings are missing, returns a deterministic local fallback answer.
   - If Claude settings are present, sends a Claude Messages-style request to the configured endpoint.
   - Real Azure Claude credentials were not provided or tested, so live Azure Claude integration should be described as configured but not verified.

5. **Persistence and tools**
   - `ticket_store.py` creates SQLite tables for tickets, execution steps, and evaluations.
   - `tools.py` provides simulated service-status checks and support-ticket creation.

## Implemented features

### 1. Interactive AI chat interface

Implemented in `streamlit_app.py`.

The UI uses:

- `st.chat_message` to render user and assistant messages.
- `st.chat_input` for employee questions.
- `st.session_state.messages` to keep the visible chat history for the current browser session.

The app starts with an assistant welcome message explaining that it can search support documents, check simulated service status, and ask before creating tickets.

### 2. RAG with local TF-IDF retrieval

Implemented in `knowledge_base.py`.

The app loads Markdown documents from `data/knowledge`, sanitizes them, and indexes them with:

- `TfidfVectorizer(stop_words="english", ngram_range=(1, 2))`
- `cosine_similarity`

When a user asks a question, the agent calls `KnowledgeBase.search(...)` and retrieves up to three relevant documents. These documents are passed to the answer generator and displayed as citations in the Streamlit UI.

### 3. Agent routing between answers, retrieval, and tools

Implemented in `agent.py`.

The agent uses deterministic routing rules:

- Very short or unclear requests trigger a clarifying question.
- Requests containing terms such as `ticket`, `issue`, `broken`, `disconnect`, `error`, or `help` are treated as troubleshooting requests.
- Service terms such as `vpn`, `email`, `mfa`, `login`, `okta`, `wifi`, and related keywords trigger simulated service-status checks.

This is a practical local agent design. It does not use an autonomous unbounded loop. The routing is controlled and predictable.

### 4. Python tools for simulated service status and ticket creation

Implemented in `tools.py`.

The simulated service-status tool is:

- `check_service_status(service_name)`

It returns local fixed data for:

- VPN
- Email
- Identity
- Wi-Fi

The support-ticket tool is:

- `create_support_ticket(ticket, store)`

It writes ticket data to SQLite using `TicketStore.create_ticket(...)`. The agent only calls this tool after the user confirms a pending ticket.

### 5. Conversation memory

Implemented in `streamlit_app.py`.

The Streamlit session stores:

- `conversation_id`
- `messages`
- `pending_ticket`
- `last_trace`

The previous messages are passed into `agent.respond(...)` as `history`. The model adapter receives this history. In fallback mode, the generated response is deterministic and does not deeply reason over multi-turn history, but the UI does preserve and display the conversation context during the session.

### 6. Agent execution trace without private reasoning

Implemented in `agent.py`, `models.py`, `ticket_store.py`, and `streamlit_app.py`.

Trace steps include safe operational stages such as:

- `input_screening`
- `intent_classification`
- `clarification`
- `retrieval`
- `tool_call`
- `ticket_confirmation`
- `generation`

The trace records:

- Stage
- Action
- Observation
- Metadata such as document titles or tool results
- Timestamp

The trace does not expose hidden chain-of-thought or private model reasoning. It shows what the agent did, not internal private reasoning.

Trace rows are displayed in the Streamlit side panel and are also logged to the `execution_steps` SQLite table.

### 7. Prompt-injection protection and ticket confirmation

Implemented in `security.py` and `agent.py`.

Prompt-injection protection:

- The app checks user input for patterns such as:
  - "ignore previous instructions"
  - "reveal the system prompt"
  - "print API key"
  - "exfiltrate"
- Unsafe requests are blocked with a safe response.
- Knowledge documents are also sanitized for instruction-like unsafe lines.

Ticket confirmation:

- The agent can draft a pending ticket.
- The user must explicitly reply with confirmation words such as `confirm`, `yes`, or `approve`.
- Ticket creation is not executed during the initial troubleshooting response.
- If the user declines, the agent says no ticket was created.

### 8. Evaluation dashboard

Implemented in `evaluation.py`, `ticket_store.py`, and `streamlit_app.py`.

The dashboard includes a button to run a local evaluation suite. The current suite has three cases:

- Urgent VPN disconnect
- MFA login help
- Prompt-injection block

Each evaluation records:

- Whether the test passed
- Latency in milliseconds
- Tool success rate
- Answer score
- Details such as expected terms, tool names, and citations

The Streamlit dashboard displays:

- Pass rate
- Average latency
- Tool success percentage
- Evaluation result table

### 9. SQLite ticket storage

Implemented in `ticket_store.py`.

SQLite tables are created automatically:

- `tickets`
- `execution_steps`
- `evaluations`

The default database path is:

```text
data/helpdesk.db
```

This can be changed with:

```text
HELPDESK_DB_PATH
```

The `.gitignore` excludes local database files, so demo data is not committed.

### 10. Fictional IT knowledge documents

Implemented in `data/knowledge`.

The project includes five fictional Northstar documents:

- `vpn-remote-access.md`
- `remote-work-policy.md`
- `ticket-escalation-policy.md`
- `mfa-identity-access.md`
- `email-outlook.md`

These documents provide the content used by the local RAG system.

### 11. Local setup and instructions

Documented in `README.md` and summarized below.

Setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run:

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Run tests:

```bash
source .venv/bin/activate
pytest
```

Optional Claude configuration:

```bash
cp .env.example .env
```

Then fill in:

```text
CLAUDE_API_ENDPOINT
CLAUDE_API_KEY
CLAUDE_MODEL
CLAUDE_API_VERSION
```

Important: `.env` should never be committed.

### 12. Automated tests

Implemented in `tests`.

Current tests cover:

- VPN query retrieves the VPN support document.
- VPN troubleshooting checks service status and requires ticket confirmation.
- Ticket creation happens after confirmation.
- Prompt-injection attempt is blocked.
- Evaluation suite returns three results with latency and answer-score fields.

## How RAG works in this project

The RAG process is local and simple:

1. The app loads Markdown support documents from `data/knowledge`.
2. Each document title and body is stored as a `KnowledgeChunk`.
3. `TfidfVectorizer` converts the documents into a term-frequency matrix.
4. When the user asks a question, the query is vectorized.
5. Cosine similarity ranks the most relevant documents.
6. The top documents are passed into the response prompt or fallback response.
7. The UI shows cited document titles and paths.

No vector database is required.

## How the agent decides what to do

The agent uses deterministic rules rather than an uncontrolled autonomous loop.

Main decision points:

- **Safety first:** Every user message is screened for prompt-injection patterns.
- **Clarify when necessary:** Very short or underspecified messages can trigger a follow-up question.
- **Retrieve documents:** Most support requests search the knowledge base.
- **Call tools:** Service keywords trigger service-status checks.
- **Draft tickets:** Urgent or degraded-service situations create a pending ticket draft.
- **Require confirmation:** Ticket creation only occurs after explicit confirmation.

This approach keeps tool use predictable and prevents unauthorized ticket creation.

## Model behavior and Azure Claude status

The project includes a configurable Claude client in `llm.py`.

Current verified behavior:

- If Claude settings are missing, the app uses a deterministic local fallback response.
- The fallback response is enough to demonstrate the local workflow: RAG, tools, tickets, traces, and evaluations.
- Automated tests use this local fallback path because no real Azure Claude credentials are stored in the repository.

Configured but not live-tested:

- The app can read `CLAUDE_API_ENDPOINT`, `CLAUDE_API_KEY`, `CLAUDE_MODEL`, and `CLAUDE_API_VERSION` from `.env`.
- The app sends a Claude Messages-style request to the configured endpoint.
- Real Azure Claude connectivity has not been tested because real credentials were not provided.

Therefore, this submission should not claim that live Azure Claude integration has been successfully verified. It should say that the integration is configurable and that the local fallback was used for development/testing when credentials were unavailable.

## Security and confirmation controls

Security controls include:

- Prompt-injection pattern detection.
- Removal of unsafe instruction-like lines from source documents.
- No hardcoded API keys or secrets.
- `.env` ignored by git.
- Explicit user confirmation before ticket creation.

Ticket workflow example:

1. User reports urgent VPN issue.
2. Agent retrieves documents and checks VPN status.
3. Agent drafts a high-priority ticket.
4. Agent asks the user to reply `confirm`.
5. Only after confirmation does `create_support_ticket(...)` write to SQLite.

## Conversation memory and execution tracing

Conversation memory:

- Streamlit keeps messages in `st.session_state.messages`.
- The pending ticket draft is stored in `st.session_state.pending_ticket`.
- This allows the next user message, such as `confirm`, to complete the ticket workflow.

Execution tracing:

- Each agent response builds a list of `TraceStep` records.
- The latest trace is displayed in the Streamlit side panel.
- Trace steps are saved in SQLite through `TicketStore.log_trace(...)`.
- The trace shows operational stages and tool calls, not private chain-of-thought.

## Evaluation and testing results

I ran the test suite against the actual project source code.

Command:

```bash
pytest
```

Actual output:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /agent/repos/northstar-ai-it-helpdesk
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.16.0
collected 5 items

tests/test_agent.py ...                                                  [ 60%]
tests/test_evaluation.py .                                               [ 80%]
tests/test_knowledge_base.py .                                           [100%]

============================== 5 passed in 0.05s ===============================
```

The tests passed. They verify the main local behavior, but they do not test live Azure Claude calls with real credentials.

## Screenshots to include in the assignment submission

The professor requested a screenshot of the application and a description of how it was achieved. Recommended screenshots:

1. **Main app screen before chat**
   - Shows the Streamlit title, chat input, execution trace panel, support tickets section, and evaluation dashboard.
   - Demonstrates that the app opens locally.

2. **VPN troubleshooting response**
   - Use the prompt:
     ```text
     My VPN keeps disconnecting. I am working remotely, and I have a client presentation in 30 minutes. Can you help?
     ```
   - Demonstrates RAG, service-status checking, troubleshooting recommendations, citations, and ticket draft.

3. **Execution trace panel**
   - Shows stages such as input screening, retrieval, tool call, ticket confirmation, and generation.
   - Demonstrates that trace information is visible without private reasoning.

4. **Ticket confirmation**
   - Reply:
     ```text
     confirm
     ```
   - Shows that a support ticket is created only after explicit confirmation.

5. **Evaluation dashboard**
   - Click "Run local evaluation suite."
   - Shows pass rate, average latency, tool success, and evaluation rows.

6. **SQLite ticket table in the UI**
   - Shows the created support ticket in the support tickets table.
   - Demonstrates local ticket persistence.

If Azure Claude credentials are not configured, the screenshot may show the warning that fallback responses are being used. That is acceptable as long as the submission clearly states that live Claude credentials were not tested.

## Vibe Coding approach used

This project follows the Demo 1 Vibe Coding style because the application was built iteratively from a high-level natural-language request. The development process focused on:

- Inspecting the environment and available tools.
- Creating the Streamlit application structure.
- Adding local RAG and sample documents.
- Adding deterministic agent routing and simulated tools.
- Adding SQLite persistence.
- Adding safety controls and ticket confirmation.
- Adding an evaluation dashboard.
- Running tests and refining behavior based on test results.

Unlike the Spec-Driven Coding workflow, this approach did not begin by writing separate formal specification documents and waiting for approval before implementation. Instead, the application was developed in practical increments and verified with tests.

## Limitations and outstanding items

The current project is suitable for a local university demo, but it has limitations:

- Live Azure Claude integration is configurable but not verified with real credentials.
- Automated tests currently use the local fallback behavior and do not mock HTTP responses from Azure Claude.
- The agent routing is deterministic and simple; it is not a complex autonomous planner.
- The service-status tool uses fixed simulated data, not real IT monitoring systems.
- Ticket storage is local SQLite only.
- Evaluation is a small local test suite, not a full production-quality evaluation framework.
- Streamlit session memory is browser-session based and is not a long-term user memory system.
- API error handling is basic in the current source code.

## Requirement-to-implementation checklist

| # | Assignment requirement | Implementation / evidence | Status |
| --- | --- | --- | --- |
| 1 | Interactive AI chat interface | `streamlit_app.py` uses Streamlit chat messages and chat input. | Implemented |
| 2 | RAG using sample IT policy documents and local TF-IDF retrieval | `knowledge_base.py` indexes `data/knowledge/*.md` with `TfidfVectorizer` and cosine similarity. | Implemented |
| 3 | AI agent routing between direct answers, retrieval, and tool calls | `agent.py` classifies requests, retrieves documents, asks clarifying questions, and calls tools based on service keywords. | Implemented |
| 4 | Python tools for simulated service status and support ticket creation | `tools.py` implements `check_service_status` and `create_support_ticket`. | Implemented |
| 5 | Conversation memory | `streamlit_app.py` stores messages and pending ticket state in `st.session_state`. | Implemented for Streamlit session |
| 6 | Agent execution trace without private model reasoning | `agent.py` creates `TraceStep` records; `streamlit_app.py` displays them; `ticket_store.py` logs them. | Implemented |
| 7 | Prompt injection protection and explicit confirmation before ticket creation | `security.py` blocks injection patterns; `agent.py` requires confirmation words before creating tickets. | Implemented |
| 8 | Evaluation dashboard showing test results, latency, and tool execution success | `evaluation.py` runs local evaluation cases; `streamlit_app.py` displays metrics and table. | Implemented |
| 9 | SQLite ticket storage | `ticket_store.py` creates and uses the `tickets` table in `data/helpdesk.db`. | Implemented |
| 10 | Fictional IT knowledge documents | Five Markdown documents exist in `data/knowledge`. | Implemented |
| 11 | Local application setup and instructions | `README.md` documents virtual environment setup, `.env`, running Streamlit, and running tests. | Implemented |
| 12 | Automated tests | `tests/` contains pytest tests; actual run showed 5 passed. | Implemented |

## Submission description example

For the assignment text box or uploaded file, I can describe the project as:

> I built a local Streamlit AI IT Help Desk for the fictional company Northstar Technologies. The app includes an interactive chat interface, local TF-IDF RAG over fictional IT support documents, deterministic agent routing, simulated IT tools, SQLite ticket storage, execution tracing, prompt-injection protection, confirmation before ticket creation, and a local evaluation dashboard. The app keeps secrets out of source code and can be configured with Azure Claude credentials through `.env`; because real credentials were not provided or tested, the verified demo uses the deterministic local fallback response path. I verified the implementation with pytest, and the current test run reports 5 passing tests.
