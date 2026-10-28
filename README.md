# AI-Based Intelligent Network Design Assistant

An AI-powered tool that generates complete enterprise LAN designs from business requirements.

## Project Structure

```
Project/
├── backend/       # Python + FastAPI
└── frontend/      # React + Vite
```

---

## Backend Setup

**Requirements:** Python 3.11+

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set your GEMINI_API_KEY

# 4. Run the development server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Running Tests

```bash
cd backend
pytest tests/test_health.py -v
```

---

## Frontend Setup

**Requirements:** Node.js 18+, pnpm

```bash
cd frontend

# 1. Install dependencies
pnpm install

# 2. Start the dev server
pnpm dev
```

App available at: http://localhost:5173

> The Vite dev server proxies all `/api/*` requests to the FastAPI backend at port 8000.

---

## Environment Variables

| Variable              | Default              | Description                        |
|-----------------------|----------------------|------------------------------------|
| `GEMINI_API_KEY`      | *(required for LLM)* | Google Gemini API key              |
| `GEMINI_MODEL`        | `gemini-2.5-flash`   | Gemini model to use                |
| `LLM_TIMEOUT_SECONDS` | `15`                 | LLM request timeout                |
| `DATABASE_URL`        | `sqlite:///./netdesign.db` | SQLAlchemy database URL      |

---

## Development Phases

| Phase | Description                        | Status     |
|-------|------------------------------------|------------|
| 1     | Project skeleton (this commit)     | ✅ Done    |
| 2–6   | Core engine modules                | 🔜 Planned |
| 7     | Full wizard UI + persistence       | 🔜 Planned |
