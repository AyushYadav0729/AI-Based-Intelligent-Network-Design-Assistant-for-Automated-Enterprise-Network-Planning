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

## Development Phases & Status

| Phase | Description | Status |
|-------|-------------|--------|
| **1** | Project Setup, Schemas & Device Catalog | ✅ Complete |
| **2** | Core Algorithmic Engine (VLSM Subnetting & Addressing) | ✅ Complete |
| **3** | Topology Selection & Graph Generation (Star, Collapsed Core, 3-Tier) | ✅ Complete |
| **4** | Hardware BOM, Device Selection & Cost Estimation | ✅ Complete |
| **5** | Design Rule Validator Engine (18 deterministic checks) | ✅ Complete |
| **6** | Variant Generator (Balanced, Budget, Performance) & Pipeline | ✅ Complete |
| **7** | Interactive Frontend Wizard (React Flow, IP tables, BOM, ACLs, Projects) | ✅ Complete |
| **8** | Exporters (Cisco IOS CLI configs, ReportLab PDF reports, NetworkX PNGs) | ✅ Complete |
| **9** | Testing, Verification & End-to-End Validation (97/97 tests passing) | ✅ Complete |

---

## Running Tests

Run the complete test suite across all 9 phases:

```bash
cd backend
pytest -v
```

All 97 unit and integration tests validate:
- VLSM address calculations, prefix alignment, and gateway allocation
- Topology threshold transitions (Star vs Collapsed-Core vs 3-Tier)
- All 18 rule engine error/warning validators
- Multi-variant synthesis and comparison engine
- LLM prompt engineering, response parsing, and deterministic fallback
- CLI configuration generation and ZIP packaging
- ReportLab multi-section PDF generation and diagram rendering

