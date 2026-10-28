"""
main.py — FastAPI application entry-point for the Network Design Assistant.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.db.session import engine, Base
from app.api.routes_design import router as design_router
from app.api.routes_projects import router as projects_router
from app.api.routes_llm import router as llm_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Network Design Assistant",
    description="Generates complete enterprise LAN designs from business requirements.",
    version="0.1.0",
)

# Allow the Vite dev server to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API route modules
app.include_router(design_router)
app.include_router(projects_router)
app.include_router(llm_router)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    """Returns the service health and LLM availability flag."""
    llm_available = bool(settings.gemini_api_key)
    return {
        "status": "ok",
        "version": "0.1.0",
        "llm_available": llm_available,
        "llm_model": settings.gemini_model if llm_available else None,
    }
