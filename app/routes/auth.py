import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models import (
    User, UserProfile, LoginRequest, RegisterRequest, ProfileUpdateRequest,
    ActivityAnalytics
)
from ..database import db
from ..config import settings
from ..telemetry import telemetry

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72


def create_access_token(username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": username,
        "exp": expires,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


async def get_current_user_optional(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        return None

    username = decode_token(token)
    if not username:
        return None

    return db.get_user_by_username(username)


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register")
async def register(req: RegisterRequest, response: Response, request: Request):
    """User registration with secure credential hashing."""
    clean_username = req.username.strip().lower()
    existing = db.get_user_by_username(clean_username)
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken")

    if len(clean_username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = db.create_user(
        username=clean_username,
        password=req.password,
        full_name=req.full_name.strip(),
        bio=req.bio or "",
        website=req.website or ""
    )

    client_ip = request.client.host if request.client else "unknown"
    telemetry.emit(
        event_type="auth.register_success",
        severity="info",
        source_resource=client_ip,
        target_resource=f"user:{clean_username}",
        attributes={"username": clean_username, "full_name": user.full_name},
    )

    token = create_access_token(user.username)
    is_secure = settings.environment != "development"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        max_age=3600 * 24 * 3
    )

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login")
async def login(req: LoginRequest, response: Response, request: Request):
    """Real JWT authentication endpoint."""
    clean_username = req.username.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    user = db.verify_user_password(clean_username, req.password)
    if not user:
        telemetry.emit(
            event_type="auth.login_failed",
            severity="medium",
            source_resource=client_ip,
            target_resource=f"user:{clean_username}",
            attributes={"username": clean_username, "reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    telemetry.emit(
        event_type="auth.login_success",
        severity="info",
        source_resource=client_ip,
        target_resource=f"user:{user.username}",
        attributes={"username": user.username, "role": user.role},
    )

    token = create_access_token(user.username)
    is_secure = settings.environment != "development"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        max_age=3600 * 24 * 3
    )

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Invalidate session cookies."""
    response.delete_cookie(key="access_token")
    if current_user:
        telemetry.emit(
            event_type="auth.token_revoked",
            severity="low",
            source_resource=request.client.host if request.client else "unknown",
            target_resource=f"user:{current_user.username}",
            attributes={"action": "logout"},
        )
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Return profile for the currently authenticated user."""
    return user


@router.put("/profile", response_model=User)
async def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user)):
    """Update profile attributes."""
    updated = db.update_user_profile(
        username=user.username,
        full_name=req.full_name,
        bio=req.bio,
        website=req.website,
        avatar_url=req.avatar_url,
        is_private=req.is_private
    )
    return updated


# Complex User Profile & Social Graph Endpoints
@router.get("/users/{username}", response_model=UserProfile)
async def get_profile(
    username: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns complete user profile including their posts, follower state,
    and saved posts (if viewing own profile).
    """
    curr = current_user.username if current_user else None
    profile = db.get_full_user_profile(username.strip().lower(), current_username=curr)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.get("/users/{username}/analytics", response_model=ActivityAnalytics)
async def get_profile_analytics(username: str):
    """
    Computes activity analytics: total likes, comments, engagement rate,
    and trending hashtags used by the creator.
    """
    try:
        return db.get_user_analytics(username.strip().lower())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{username}/follow")
async def toggle_follow_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle follow/unfollow a user."""
    target = username.strip().lower()
    if target == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    try:
        result = db.toggle_follow(current_user.username, target)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{username}/followers", response_model=List[User])
async def list_followers(
    username: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List accounts following this user."""
    curr = current_user.username if current_user else None
    return db.get_followers(username.strip().lower(), current_username=curr)


@router.get("/users/{username}/following", response_model=List[User])
async def list_following(
    username: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List accounts this user follows."""
    curr = current_user.username if current_user else None
    return db.get_following(username.strip().lower(), current_username=curr)


@router.get("/suggestions", response_model=List[User])
async def get_suggested_creators(current_user: User = Depends(get_current_user)):
    """Personalized suggestions of creators not yet followed."""
    return db.get_suggested_users(current_user.username, limit=5)
