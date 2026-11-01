from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from ..models import Post, Story, Comment, CreatePostRequest, CreateCommentRequest, CreateStoryRequest, User
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
    """Publish a new story."""
    if not req.media_url.strip():
        raise HTTPException(status_code=400, detail="Media URL is required")
    story = db.create_story(current_user.username, req.media_url.strip())
    return story


@router.get("/feed", response_model=List[Post])
async def get_feed(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve chronological post feed."""
    username = current_user.username if current_user else None
    return db.get_feed(current_username=username)


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


@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle like on a post."""
    result = db.toggle_like(post_id, current_user.username)
    return result


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
    return comment
