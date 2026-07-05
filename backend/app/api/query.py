"""
Natural Language Query endpoint — RAG-powered query interface for the PM.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.ai.query_engine import RAGQueryEngine

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class EvidenceItem(BaseModel):
    text: str
    source: str
    date: Optional[str] = None
    rating: Optional[int] = None
    sentiment: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    evidence: List[EvidenceItem]
    confidence: str  # High / Medium / Low
    confidence_reason: str
    follow_up_questions: List[str]
    result_count: int
    query_time_ms: int


@router.post("/query")
async def natural_language_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Natural language query over the review intelligence database.
    Uses RAG: embed query → vector search → AI synthesis.
    """
    engine = RAGQueryEngine(db)
    result = await engine.query(request.query)
    return result

