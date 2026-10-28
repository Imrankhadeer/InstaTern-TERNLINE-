import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any

from ..models import Post, Story, Comment, CreatePostRequest, CreateCommentRequest, User
from ..database import db
from ..telemetry import telemetry
from .auth import CURRENT_ACTIVE_USER

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/stories", response_model=List[Story])
async def get_stories():
    """Returns stories for the stories bar."""
    return db.stories


@router.get("/feed", response_model=List[Post])
async def get_feed(request: Request):
    """
    Returns the home post feed.
    Emits an 'http.request' telemetry event.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_feed_{uuid.uuid4().hex[:12]}"

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "GET",
            "endpoint": "/api/feed",
            "status_code": 200,
            "user": CURRENT_ACTIVE_USER,
            "client_ip": client_ip,
        },
        source_resource=f"ip:{client_ip}",
        target_resource="/api/feed",
        trace_id=trace_id,
        severity="info",
    )

    return db.get_feed()


@router.post("/posts", response_model=Post)
async def create_post(req: CreatePostRequest, request: Request):
    """Creates a new post in the feed and triggers thumbnail generation."""
    user = db.users.get(CURRENT_ACTIVE_USER)
    if not user:
        raise HTTPException(status_code=401, detail="Please login first")

    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_post_{uuid.uuid4().hex[:12]}"

    post = db.create_post(
        author=user,
        caption=req.caption,
        image_url=req.image_url,
        tags=req.tags,
    )

    # Telemetry: HTTP request for post creation
    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "POST",
            "endpoint": "/api/posts",
            "status_code": 201,
            "post_id": post.id,
            "user": user.username,
        },
        source_resource=f"user:{user.username}",
        target_resource=f"post:{post.id}",
        trace_id=trace_id,
        severity="info",
    )

    # Telemetry: Database insertion
    telemetry.emit(
        event_type="db.query",
        attributes={
            "table": "posts",
            "operation": "INSERT",
            "rows_affected": 1,
            "post_id": post.id,
        },
        target_resource="table:posts",
        trace_id=trace_id,
        severity="info",
    )

    return post


@router.post("/posts/{post_id}/like", response_model=Post)
async def toggle_like(post_id: str, request: Request):
    """Like or unlike a post."""
    post = db.toggle_like(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "POST",
            "endpoint": f"/api/posts/{post_id}/like",
            "is_liked": post.is_liked,
            "likes_count": post.likes_count,
            "user": CURRENT_ACTIVE_USER,
        },
        target_resource=f"post:{post_id}",
        severity="info",
    )
    return post


@router.post("/posts/{post_id}/comments", response_model=Comment)
async def add_comment(post_id: str, req: CreateCommentRequest, request: Request):
    """Add a comment to a post."""
    user = db.users.get(CURRENT_ACTIVE_USER) or list(db.users.values())[0]
    comment = db.add_comment(post_id, user, req.text)
    if not comment:
        raise HTTPException(status_code=404, detail="Post not found")

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "POST",
            "endpoint": f"/api/posts/{post_id}/comments",
            "post_id": post_id,
            "user": user.username,
        },
        target_resource=f"post:{post_id}",
        severity="info",
    )
    return comment


@router.get("/users/{username}")
async def get_user_profile(username: str):
    """Fetch user profile and posts."""
    user = db.users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_posts = [p for p in db.posts.values() if p.author.username == username]
    return {
        "user": user,
        "posts": user_posts,
        "posts_count": len(user_posts),
    }

