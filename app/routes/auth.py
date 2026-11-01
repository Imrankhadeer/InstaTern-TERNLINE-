import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models import User, LoginRequest, RegisterRequest, ProfileUpdateRequest
from ..database import db
from ..config import settings

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
async def register(req: RegisterRequest, response: Response):
    """Real user registration with hashed password."""
    existing = db.get_user_by_username(req.username.strip().lower())
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken")

    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = db.create_user(
        username=req.username.strip().lower(),
        password=req.password,
        full_name=req.full_name.strip(),
        bio=req.bio or ""
    )

    token = create_access_token(user.username)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600 * 24 * 3
    )

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    """Real authentication endpoint."""
    user = db.verify_user_password(req.username.strip().lower(), req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = create_access_token(user.username)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600 * 24 * 3
    )

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout")
async def logout(response: Response):
    """Logout current user and clear auth cookies."""
    response.delete_cookie(key="access_token")
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Return profile for the currently authenticated user."""
    return user


@router.put("/profile", response_model=User)
async def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user)):
    """Update profile information."""
    updated = db.update_user_profile(
        username=user.username,
        full_name=req.full_name,
        bio=req.bio,
        avatar_url=req.avatar_url
    )
    return updated


@router.get("/users/{username}", response_model=User)
async def get_user_profile(username: str):
    """Get public profile for any user."""
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
