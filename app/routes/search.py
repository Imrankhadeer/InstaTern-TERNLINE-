from fastapi import APIRouter, Query
from typing import Dict, Any
from ..database import db

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(q: str = Query("", description="Search term")):
    """Clean parameterized search across users and posts."""
    if not q.strip():
        return {"query": "", "results": {"users": [], "posts": []}}

    results = db.search(q.strip())
    return {
        "query": q,
        "results": results,
    }
