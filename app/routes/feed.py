from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from ..models import (
    Post, Story, Comment, CreatePostRequest, CreateCommentRequest,
    CreateStoryRequest, Notification, User
)
from ..database import db
from .auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/stories", response_model=List[Story])
async def get_stories():
    """Retrieve active user stories."""
    return db.get_stories()


@router.post("/stories", response_model=Story)
async def create_story(
    req: CreateStoryRequest,
    current_user: User = Depends(get_current_user)
):
    """Publish a new 24h story."""
    if not req.media_url.strip():
        raise HTTPException(status_code=400, detail="Media URL is required")
    story = db.create_story(current_user.username, req.media_url.strip())
    return story


@router.get("/feed", response_model=List[Post])
async def get_feed(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve chronologically ordered social feed with like/save statuses."""
    username = current_user.username if current_user else None
    return db.get_feed(current_username=username)


@router.get("/posts/{post_id}", response_model=Post)
async def get_single_post(
    post_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve a single post by ID with comments and author details."""
    username = current_user.username if current_user else None
    post = db.get_post_by_id(post_id, current_username=username)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/posts", response_model=Post)
async def create_post(
    req: CreatePostRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new post in the feed."""
    if not req.image_url.strip():
        raise HTTPException(status_code=400, detail="Image URL is required")

    post = db.create_post(
        username=current_user.username,
        caption=req.caption.strip(),
        image_url=req.image_url.strip(),
        tags=req.tags or []
    )
    return post


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a post owned by the logged in user."""
    success = db.delete_post(post_id, current_user.username)
    if not success:
        raise HTTPException(status_code=403, detail="Post not found or unauthorized to delete")
    return {"status": "success", "message": "Post deleted"}


@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle like on a post."""
    try:
        result = db.toggle_like(post_id, current_user.username)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/posts/{post_id}/save")
async def toggle_save(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Bookmark / save a post to collection."""
    result = db.toggle_save_post(post_id, current_user.username)
    return result


@router.get("/posts/saved/me", response_model=List[Post])
async def get_my_saved_posts(current_user: User = Depends(get_current_user)):
    """Retrieve all posts saved/bookmarked by current user."""
    return db.get_saved_posts(current_user.username)


@router.post("/posts/{post_id}/comments", response_model=Comment)
async def add_comment(
    post_id: str,
    req: CreateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a post."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Comment text cannot be empty")

    comment = db.add_comment(
        post_id=post_id,
        username=current_user.username,
        text=req.text.strip()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Post not found")
    return comment


# Notification endpoints
@router.get("/notifications", response_model=List[Notification])
async def list_notifications(current_user: User = Depends(get_current_user)):
    """List activity notifications for user."""
    return db.get_user_notifications(current_user.username)


@router.post("/notifications/read")
async def mark_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read."""
    db.mark_notifications_read(current_user.username)
    return {"status": "success"}
