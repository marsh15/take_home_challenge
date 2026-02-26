# 📊 Financial Document Analyzer — Debug Challenge

An AI-powered financial document analysis system built with **CrewAI**, **FastAPI**, **Celery**, and **SQLAlchemy**. Upload a PDF financial report and receive a comprehensive analysis covering financial health, investment strategies, and risk assessment — all processed asynchronously via a background worker queue.

> **Note**: This is a debugged and upgraded version of the original project. All deterministic bugs and inefficient prompts have been fixed, and bonus features (queue worker model + database integration) have been implemented.

---

## Table of Contents

- [Bugs Found & Fixes](#-bugs-found--fixes)
  - [Deterministic Bugs](#1-deterministic-bugs-code-crashes)
  - [Inefficient Prompts](#2-inefficient--harmful-prompts)
- [Bonus: System Architecture Upgrades](#-bonus-system-architecture-upgrades)
- [Project Structure](#-project-structure)
- [Setup Instructions](#-setup-instructions)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)

---

## 🐛 Bugs Found & Fixes

### 1. Deterministic Bugs (Code Crashes)

| # | File | Bug Description | Fix Applied |
|---|------|----------------|-------------|
| 1 | `tools.py` | **`Pdf` class never imported.** `Pdf(file_path=path).load()` crashes with `NameError` since there is no `Pdf` class anywhere. | Replaced with `pypdf.PdfReader(path)` — a reliable PDF parsing library. Added `pypdf` to `requirements.txt`. |
| 2 | `tools.py` | **Tools defined as raw classes**, not registered with CrewAI. Agents could not discover or invoke them. | Refactored all tools to use the `@tool` decorator from `crewai.tools`. |
| 3 | `tools.py` | **`read_data_tool` was `async def`** but CrewAI tools must be synchronous functions. | Changed to synchronous `def`. |
| 4 | `tools.py` | **Wrong import path** for `SerperDevTool`. `from crewai_tools.tools.serper_dev_tool import SerperDevTool` fails. | Changed to the correct public API: `from crewai_tools import SerperDevTool`. |
| 5 | `agents.py` | **`llm = llm` — undefined variable assigned to itself.** Crashes with `NameError` on import. | Removed entirely. CrewAI uses its default LLM when none is specified, or we pass the model explicitly via `_get_model()`. |
| 6 | `agents.py` | **`tool=[...]` (singular)** — wrong parameter name. CrewAI expects `tools=[...]` (plural). | Fixed to `tools=[...]`. |
| 7 | `agents.py` | **Wrong import path.** `from crewai.agents import Agent` doesn't work in crewai 0.130.0. | Fixed to `from crewai import Agent`. |
| 8 | `agents.py` | **LLM model cached at import time.** `LLM_MODEL = os.getenv(...)` at module level means `.env` changes never propagate to running workers. | Replaced with a `_get_model()` helper function called inside each factory, so the env var is read fresh every time. |
| 9 | `task.py` | **All 4 tasks assigned to the same agent** (`financial_analyst`), regardless of purpose. Verifier, Investment Advisor, and Risk Assessor tasks were all wrongly routed. | Mapped each task to its correct specialized agent via factory functions. |
| 10 | `main.py` | **Missing `file_path` in `crew.kickoff()` inputs.** Only `{'query': query}` was passed, so `{file_path}` placeholders in task descriptions were never interpolated. | Changed to `kickoff(inputs={'query': query, 'file_path': file_path})`. |
| 11 | `main.py` | **Only 1 agent and 1 task in the `Crew`.** The other 3 agents and 3 tasks were defined but never used. | All 4 agents and 4 tasks are now included in the sequential pipeline. |
| 12 | `main.py` | **`uvicorn.run(app, ..., reload=True)`** fails because `reload=True` requires the app to be passed as an import string, not an object. | Changed to `uvicorn.run("main:app", ..., reload=True)`. |
| 13 | `requirements.txt` | **Multiple version conflicts.** `pydantic==1.10.13` conflicts with `crewai==0.130.0` (needs `>=2.4.2`). Similar conflicts with `opentelemetry`, `onnxruntime`, `openai`, `click`. | Relaxed all sub-dependency pins from `==` to `>=` while keeping `crewai==0.130.0` pinned. Pinned `crewai-tools==0.47.1` for compatibility. |
| 14 | `database.py` | **Deprecated import.** `from sqlalchemy.ext.declarative import declarative_base` is deprecated in SQLAlchemy 2.x. | Updated to `from sqlalchemy.orm import declarative_base`. |

### 2. Inefficient / Harmful Prompts

| # | File | Problem | Fix Applied |
|---|------|---------|-------------|
| 1 | `agents.py` | **Financial Analyst** told to *"Make up investment advice"*, *"predict market crashes"*, *"make up market facts"*. | Rewritten to provide **objective, data-driven analysis** based on actual document content. |
| 2 | `agents.py` | **Verifier** told to *"just say yes to everything"*, *"assume everything is a financial document"*. | Rewritten as a **meticulous compliance officer** who validates document structure and readability. |
| 3 | `agents.py` | **Investment Advisor** told to *"sell expensive products"*, *"recommend meme stocks"*, *"avoid SEC compliance"*. | Rewritten as a **certified financial planner** providing balanced, data-backed, pragmatic investment advice. |
| 4 | `agents.py` | **Risk Assessor** told *"everything is either extremely high risk or completely risk-free"*, *"YOLO through volatility"*. | Rewritten as a **cautious analyst** identifying real credit, market, and operational risks with actionable mitigations. |
| 5 | `task.py` | Tasks instructed agents to *"make up website URLs"*, *"contradict yourself"*, *"include scary predictions"*. | All task descriptions and expected outputs rewritten for **professional, structured Markdown reports**. |

---

## � Bonus: System Architecture Upgrades

### Queue Worker Model (Celery + Redis)

**Problem**: The original `POST /analyze` endpoint blocked the HTTP thread for the entire CrewAI processing time (2-3+ minutes per document), causing client timeouts and preventing concurrent requests.

**Solution**: Implemented a **Celery** background task queue with **Redis** as the message broker. The API now:
1. Saves the uploaded PDF to disk
2. Creates a job record in the database with status `PENDING`
3. Dispatches the analysis task to a Celery worker
4. Returns the `job_id` immediately (< 100ms response time)

The heavy AI processing runs in an isolated background worker process. Clients can poll `GET /jobs/{job_id}` to check progress.

**Files**: `worker.py` (new)

### Database Integration (SQLAlchemy + SQLite)

**Problem**: No persistence — analysis results were computed once, returned in the HTTP response, and lost forever. No way to track job history or status.

**Solution**: Added **SQLAlchemy ORM** with **SQLite** for persistent job tracking. Every analysis job is stored with:
- `status`: `PENDING` → `PROCESSING` → `COMPLETED` / `FAILED`
- `query`: The user's analysis question
- `file_path`: Location of the uploaded PDF
- `result_text`: Full AI analysis output
- `created_at` / `updated_at`: Timestamps

**Files**: `database.py` (new), `models.py` (new)

### State Isolation for Concurrent Jobs

**Problem**: CrewAI agents and tasks defined as module-level singletons would leak state between concurrent Celery jobs.

**Solution**: Refactored all agent and task definitions into **factory functions** (`get_verifier()`, `get_verification_task()`, etc.). Each Celery job instantiates completely fresh, isolated agents and tasks, preventing memory/context cross-contamination.

### Automatic PDF Generation

**Problem**: The AI returns massive 3,000+ word Markdown strings that are difficult to read and manage inside a raw JSON terminal response.

**Solution**: Added the `markdown-pdf` library. The moment a Celery worker completes the CrewAI pipeline, it instantly converts the generated Markdown report into a beautifully paginated, professional PDF document saved to the `outputs/` directory.

The API provides a dedicated `GET /jobs/{job_id}/pdf` endpoint for instant, formatted downloading.

---

## 📁 Project Structure

```
financial-document-analyzer-debug/
├── main.py            # FastAPI server — upload endpoint + PDF download endpoint
├── worker.py          # Celery worker — runs CrewAI and generates the PDF
├── agents.py          # AI agent definitions (dynamic LLM selection)
├── task.py            # CrewAI task definitions 
├── tools.py           # PDF reader tool + web search tool
├── database.py        # SQLAlchemy engine and session setup (SQLite)
├── models.py          # Database models (User, AnalysisJob)
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── .gitignore         # Git ignore rules
├── data/              # Temporary isolated upload directory
│   └── TSLA-Q2-2025-Update.pdf
└── outputs/           # Automatically generated PDF analysis reports
```

---

## 🚀 Setup Instructions

### Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.12.x (3.14 lacks binary wheels for `onnxruntime`) |
| **Redis** | Message broker for Celery |
| **uv** or **pip** | Package manager |
| **API Key** | Google Gemini (free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)) or OpenAI |

### Step 1: Clone & Navigate

```bash
git clone <your-repo-url>
cd financial-document-analyzer-debug
```

### Step 2: Create Virtual Environment

```bash
# Using uv (recommended)
uv venv --python 3.12
source .venv/bin/activate

# Or using standard venv
python3.12 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
uv pip install -r requirements.txt
# Or: pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
SERPER_API_KEY=your-serper-api-key
GEMINI_API_KEY=your-gemini-api-key
OPENAI_MODEL_NAME=gemini/gemini-2.5-flash
```

### Step 5: Install & Start Redis

```bash
# macOS
brew install redis
redis-server

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

### Step 6: Start the Services (3 terminal tabs)

| Terminal | Command |
|----------|---------|
| **Tab 1** — Redis | `redis-server` |
| **Tab 2** — Celery Worker | `source .venv/bin/activate && celery -A worker.celery_app worker --loglevel=info --pool=solo` |
| **Tab 3** — FastAPI Server | `source .venv/bin/activate && python main.py` |

> **Note**: The `--pool=solo` flag is required on macOS to prevent `SIGSEGV` crashes caused by the default `fork` pool conflicting with native libraries like `onnxruntime`.

---

## 🧪 Usage

### Submit a Document for Analysis

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@data/TSLA-Q2-2025-Update.pdf" \
  -F "query=What are the key financial metrics?"
```

**Response** (returns immediately):
```json
{
  "status": "success",
  "message": "Analysis job added to the queue.",
  "job_id": 1,
  "query": "What are the key financial metrics?",
  "file_processed": "TSLA-Q2-2025-Update.pdf"
}
```

### Poll for Results

```bash
curl -X GET "http://localhost:8000/jobs/1"
```

**While processing:**
```json
{"job_id": 1, "status": "PROCESSING", "query": "What are the key financial metrics?"}
```

**When completed:**
```json
{
  "job_id": 1,
  "status": "COMPLETED",
  "query": "What are the key financial metrics?",
  "message": "Analysis is ready! Download your PDF report.",
  "download_url": "http://localhost:8000/jobs/1/pdf"
}
```

### Download the PDF Report

Once the status is `COMPLETED`, you can download the sleek, fully-formatted PDF analysis:

```bash
curl -O http://localhost:8000/jobs/1/pdf
```
*(This saves the file directly to your computer as `Financial_Analysis_Job_1.pdf`)*

### Interactive API Docs

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser for a Swagger UI where you can test all endpoints interactively.

---

## 📡 API Documentation

### `GET /` — Health Check

Returns server status.

```json
{"message": "Financial Document Analyzer API with Celery Async Queue is running"}
```

---

### `POST /analyze` — Submit Document for Analysis

Upload a PDF financial document and enqueue it for background AI analysis.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File (multipart) | ✅ | — | The PDF financial document |
| `query` | string (form) | ❌ | `"Analyze this financial document for investment insights"` | The specific question to answer |

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"success"` |
| `message` | string | Confirmation message |
| `job_id` | integer | Unique tracking ID for polling |
| `query` | string | The submitted query |
| `file_processed` | string | Original filename |

---

### `GET /jobs/{job_id}` — Poll Job Status

Check the status of a submitted analysis job and retrieve results.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | ✅ | The job ID from `POST /analyze` |

**Job Status Values:**

| Status | Meaning | Extra Fields |
|--------|---------|-------------|
| `PENDING` | Job created, waiting in queue | — |
| `PROCESSING` | Celery worker is running the CrewAI pipeline | — |
| `COMPLETED` | Analysis finished successfully | `analysis` (full report) |
| `FAILED` | An error occurred during processing | `error` (error message) |

---

## ⚙️ Configuration Reference

| Variable | Location | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | `.env` | Google Gemini API key ([get one free](https://aistudio.google.com/apikey)) |
| `OPENAI_API_KEY` | `.env` | OpenAI API key (alternative to Gemini) |
| `SERPER_API_KEY` | `.env` | Serper API key for web search tool |
| `OPENAI_MODEL_NAME` | `.env` | LLM model identifier (e.g., `gemini/gemini-2.5-flash`, `gpt-4o-mini`) |
| Redis broker URL | `worker.py` | Default: `redis://localhost:6379/0` |
| Database URL | `database.py` | Default: `sqlite:///./financial_analyzer.db` |

---

## 🏗️ Architecture Diagram

```
┌──────────┐     POST /analyze      ┌──────────────┐
│  Client  │ ──────────────────────▶ │   FastAPI    │
│ (curl /  │                         │   (main.py)  │
│ browser) │ ◀────── job_id ──────── │              │
└──────────┘                         └──────┬───────┘
     │                                      │
     │ GET /jobs/{id}                       │ 1. Save PDF
     │                                      │ 2. Create DB record (PENDING)
     ▼                                      │ 3. Dispatch to Celery
┌──────────┐                         ┌──────▼───────┐
│  SQLite  │ ◀─── status/results ─── │    Redis     │
│  (DB)    │                         │   (broker)   │
└──────────┘                         └──────┬───────┘
                                            │
                                     ┌──────▼───────┐
                                     │   Celery     │
                                     │  (worker.py) │
                                     │              │
                                     │  ┌─────────┐ │
                                     │  │ CrewAI  │ │
                                     │  │ 4 Agents│ │
                                     │  │ Pipeline│ │
                                     │  └─────────┘ │
                                     └──────────────┘
```

---

## 📝 License

This project was created as part of a debug challenge assignment.
