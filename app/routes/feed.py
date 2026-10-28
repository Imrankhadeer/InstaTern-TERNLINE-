import uuid
from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Dict, Any

from ..models import Post, Story, Comment, CreatePostRequest, CreateCommentRequest, CreateStoryRequest, User
from ..database import db
from ..telemetry import telemetry
from .auth import CURRENT_ACTIVE_USER

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/stories", response_model=List[Story])
async def get_stories():
    """Returns all active 24-hour stories."""
    return db.stories


@router.post("/stories", response_model=Story)
async def create_story(req: CreateStoryRequest, request: Request):
    """Publish a new 24-hour story."""
    user = db.users.get(CURRENT_ACTIVE_USER)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    story_id = f"story_{uuid.uuid4().hex[:8]}"
    story = Story(
        id=story_id,
        author=user,
        media_url=req.media_url,
        created_at="Just now",
    )
    db.stories.insert(0, story)

    telemetry.emit(
        event_type="http.request",
        attributes={
            "method": "POST",
            "endpoint": "/api/stories",
            "user": user.username,
            "story_id": story_id,
        },
        source_resource=f"user:{user.username}",
        target_resource=f"story:{story_id}",
        severity="info",
    )
    return story


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


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    request: Request,
    exploit_idor: bool = Query(False, description="Simulate IDOR post deletion vulnerability")
):
    """
    Deletes a post.
    Demonstrates BOLA/IDOR vulnerability:
    If exploit_idor is True, an unauthorized user can delete someone else's post!
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_post_del_{uuid.uuid4().hex[:10]}"

    try:
        success = db.delete_post(post_id, requester_username=CURRENT_ACTIVE_USER, bypass_owner_check=exploit_idor)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")

        telemetry.emit(
            event_type="http.request",
            attributes={
                "method": "DELETE",
                "endpoint": f"/api/posts/{post_id}",
                "requester": CURRENT_ACTIVE_USER,
                "is_unauthorized_idor": exploit_idor,
                "status_code": 200,
            },
            source_resource=f"user:{CURRENT_ACTIVE_USER}",
            target_resource=f"post:{post_id}",
            trace_id=trace_id,
            severity="warning" if exploit_idor else "info",
        )
        return {"status": "deleted", "post_id": post_id, "idor_exploit": exploit_idor}

    except PermissionError as pe:
        telemetry.emit(
            event_type="security.alert",
            attributes={
                "alert_type": "UNAUTHORIZED_DELETE_ATTEMPT",
                "post_id": post_id,
                "requester": CURRENT_ACTIVE_USER,
                "status_code": 403,
            },
            source_resource=f"user:{CURRENT_ACTIVE_USER}",
            target_resource=f"post:{post_id}",
            trace_id=trace_id,
            severity="warning",
        )
        raise HTTPException(status_code=403, detail=str(pe))


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
        "followers": list(db.followers.get(username, [])),
        "following": list(db.following.get(username, [])),
    }


@router.post("/users/{username}/follow")
async def follow_user(username: str, request: Request):
    """Follow a user profile."""
    success = db.follow_user(CURRENT_ACTIVE_USER, username)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot follow this user")

    telemetry.emit(
        event_type="user.followed",
        attributes={"follower": CURRENT_ACTIVE_USER, "target": username},
        severity="info",
    )
    return {"status": "following", "target": username}


@router.post("/users/{username}/unfollow")
async def unfollow_user(username: str, request: Request):
    """Unfollow a user profile."""
    success = db.unfollow_user(CURRENT_ACTIVE_USER, username)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot unfollow this user")

    telemetry.emit(
        event_type="user.unfollowed",
        attributes={"follower": CURRENT_ACTIVE_USER, "target": username},
        severity="info",
    )
    return {"status": "unfollowed", "target": username}
