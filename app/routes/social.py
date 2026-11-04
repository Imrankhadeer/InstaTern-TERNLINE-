import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from ..models import User
from ..database import db
from .auth import get_current_user, get_current_user_optional
from ..telemetry import telemetry

router = APIRouter(prefix="/api/social", tags=["social"])


@router.post("/follow/{username}")
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """
    Explicitly follow a user.
    Emits security telemetry and social graph notification.
    """
    target = username.strip().lower()
    if target == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    try:
        # Check current follow status
        following_list = db.get_following(current_user.username)
        is_already_following = any(u.username == target for u in following_list)
        if not is_already_following:
            res = db.toggle_follow(current_user.username, target)
        else:
            profile = db.get_user_by_username(target)
            res = {
                "following": True,
                "target_username": target,
                "followers_count": profile.followers_count if profile else 0
            }

        telemetry.emit(
            event_type="social.follow_success",
            severity="info",
            source_resource=current_user.username,
            target_resource=f"user:{target}",
            attributes={"follower": current_user.username, "target": target}
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/unfollow/{username}")
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """
    Explicitly unfollow a user.
    """
    target = username.strip().lower()
    if target == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot unfollow yourself")

    try:
        following_list = db.get_following(current_user.username)
        is_following = any(u.username == target for u in following_list)
        if is_following:
            res = db.toggle_follow(current_user.username, target)
        else:
            profile = db.get_user_by_username(target)
            res = {
                "following": False,
                "target_username": target,
                "followers_count": profile.followers_count if profile else 0
            }

        telemetry.emit(
            event_type="social.unfollow_success",
            severity="info",
            source_resource=current_user.username,
            target_resource=f"user:{target}",
            attributes={"follower": current_user.username, "target": target}
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/followers/{username}", response_model=List[User])
async def get_followers_list(
    username: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List all accounts following this user."""
    curr = current_user.username if current_user else None
    return db.get_followers(username.strip().lower(), current_username=curr)


@router.get("/following/{username}", response_model=List[User])
async def get_following_list(
    username: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List all accounts this user is following."""
    curr = current_user.username if current_user else None
    return db.get_following(username.strip().lower(), current_username=curr)


@router.get("/suggestions", response_model=List[User])
async def get_recommended_users(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get personalized friend and creator recommendations."""
    return db.get_suggested_users(current_user.username, limit=limit)
