from fastapi import APIRouter, Query, Depends
from typing import Dict, Any, Optional
from ..database import db
from ..models import User
from .auth import get_current_user_optional

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(
    q: str = Query("", description="Search term for creators, hashtags or captions"),
    type: str = Query("all", description="Entity type: all, users, posts, tags"),
    sort: str = Query("recent", description="Sort order: recent or popular"),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Advanced multi-facet search endpoint.
    Supports filtering by users, posts, or hashtags (#design), with sorting by recent or popular.
    """
    clean_q = q.strip()
    curr = current_user.username if current_user else None

    if not clean_q:
        # Return popular hashtags when query is empty
        tags_discovery = db.advanced_search(query="", entity_type="tags", limit=10, current_username=curr)
        return {
            "query": "",
            "results": {
                "users": [],
                "posts": [],
                "tags": tags_discovery.get("tags", []),
            },
            "total_matches": len(tags_discovery.get("tags", [])),
        }

    search_data = db.advanced_search(
        query=clean_q,
        entity_type=type,
        sort_by=sort,
        limit=limit,
        current_username=curr
    )

    return {
        "query": clean_q,
        "type": type,
        "sort": sort,
        "results": {
            "users": search_data["users"],
            "posts": search_data["posts"],
            "tags": search_data["tags"],
        },
        "total_matches": search_data["total_matches"],
    }
