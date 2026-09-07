# 🤖 Self-Healing Text-to-SQL Agent

> Ask questions in plain English → Get answers from your database.  
> Powered by **Google Gemini** (free API) + **LangGraph** agentic AI with **self-healing SQL generation**.

---

## ✨ Features

- **Natural Language to SQL** — Type questions in English, get SQL results
- **Self-Healing Pipeline** — If SQL fails, the agent automatically fixes and retries (up to 3 attempts)
- **Agentic AI with LangGraph** — Stateful, graph-based agent with typed state management
- **Swagger UI** — Interactive API documentation at `/docs`
- **Read-Only Safety** — SQL validation blocks all destructive operations (DROP, DELETE, etc.)
- **Free LLM** — Uses Google Gemini 3.6 Flash (no credit card required)
- **Sample Database** — Pre-seeded e-commerce data (customers, products, orders)

## 🏗️ Architecture

```
User (Swagger UI)
  │
  ▼
FastAPI /api/v1/query
  │
  ▼
┌─────────────────────────────────────────────┐
│           LangGraph Agent Pipeline          │
│                                             │
│  1. Schema Loader → 2. SQL Generator (LLM) │
│       → 3. SQL Validator → 4. Executor      │
│                    │                        │
│              ┌─────┴─────┐                  │
│              │           │                  │
│          [Success]    [Error]               │
│              │           │                  │
│            END     5. Self-Healer           │
│                    (retry ≤ 3) ──→ Back to 2│
└─────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.10+**
- **Google Gemini API Key** (free) — Get it at [Google AI Studio](https://aistudio.google.com/)

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Rinub/text-to-sql-agent.git
cd text-to-sql-agent
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```
Edit `.env` and add your Gemini API key:
```env
GOOGLE_API_KEY=your-actual-api-key-here
```

### 5. Run the server
```bash
python run.py
```

### 6. Open Swagger UI
Navigate to **http://localhost:8000/docs** in your browser.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Submit a natural language question |
| `GET` | `/api/v1/schema` | View database schema |
| `GET` | `/api/v1/health` | Health check |

### Example Request
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top 5 customers by total spending?"}'
```

### Example Response
```json
{
  "question": "What are the top 5 customers by total spending?",
  "sql": "SELECT c.name, SUM(o.total_amount) AS total_spending FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY total_spending DESC LIMIT 5;",
  "result": [
    {"name": "Alice Johnson", "total_spending": 2459.93},
    {"name": "Bob Smith", "total_spending": 1899.95}
  ],
  "attempts": 1,
  "is_success": true,
  "error": null
}
```

## 🧪 Sample Questions to Try

- "How many customers are there?"
- "Show me all products under $50"
- "What are the top 5 customers by total spending?"
- "What is the total revenue by product category?"
- "List all orders from customers in the USA"
- "What is the average order value?"
- "Which products have never been ordered?"
- "Show me monthly sales for 2024"

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI |
| LLM | Google Gemini 3.6 Flash |
| Agent Framework | LangGraph (StateGraph) |
| Database | SQLite (default) / PostgreSQL |
| ORM | SQLAlchemy |
| Language | Python 3.10+ |

## 📁 Project Structure

```
text-to-sql-agent/
├── .env.example              # Environment template
├── .gitignore
├── README.md
├── requirements.txt
├── run.py                    # Entry point
├── app/
│   ├── main.py               # FastAPI app
│   ├── config.py             # Settings
│   ├── api/
│   │   └── routes.py         # API endpoints
│   ├── database/
│   │   ├── connection.py     # DB engine & queries
│   │   └── seed.py           # Sample data
│   ├── agent/
│   │   ├── state.py          # LangGraph state
│   │   ├── nodes.py          # Pipeline nodes
│   │   └── graph.py          # Graph wiring
│   └── prompts/
│       └── templates.py      # LLM prompts
├── data/                     # SQLite DB (auto-generated)
└── tests/
    └── test_query.py         # Tests
```

## 🔧 Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | Your Gemini API key |
| `DATABASE_URL` | `sqlite:///data/sample.db` | Database connection string |
| `LLM_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `MAX_RETRIES` | `3` | Max self-healing attempts |

### Using PostgreSQL
To switch to PostgreSQL, update `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/text_to_sql
```

## 📄 License

MIT License
