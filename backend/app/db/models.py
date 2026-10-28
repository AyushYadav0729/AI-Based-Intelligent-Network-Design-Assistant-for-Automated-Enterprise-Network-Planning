"""
models.py — SQLAlchemy database models.
Spec Section 11.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.session import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    org_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    requirements_json = Column(Text, nullable=False)
    results_json = Column(Text, nullable=False)
    explanation_source = Column(String(50), default="template")

