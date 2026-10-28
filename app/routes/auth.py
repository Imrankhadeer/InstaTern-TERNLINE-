import uuid
from fastapi import APIRouter, HTTPException, Request, Response
from typing import List, Dict, Any

from ..models import User, LoginRequest, RegisterRequest
from ..database import db
from ..telemetry import telemetry

router = APIRouter(prefix="/api/auth", tags=["auth"])

CURRENT_ACTIVE_USER = "alice_cyber"


@router.get("/users", response_model=List[User])
async def list_available_users():
    """List demo users to easily test different personas in the web UI."""
    return list(db.users.values())


@router.get("/me", response_model=User)
async def get_current_user():
    """Returns the currently active session user."""
    global CURRENT_ACTIVE_USER
    user = db.users.get(CURRENT_ACTIVE_USER)
    if not user:
        user = list(db.users.values())[0]
        CURRENT_ACTIVE_USER = user.username
    return user


@router.post("/switch-user/{username}")
async def switch_user(username: str):
    """Switch active user profile in the UI."""
    global CURRENT_ACTIVE_USER
    if username not in db.users:
        raise HTTPException(status_code=404, detail="User not found")
    CURRENT_ACTIVE_USER = username
    return {"status": "switched", "user": db.users[username]}


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    """
    Simulates user login.
    Emits telemetry:
    - 'auth.login_success' on valid credentials
    - 'auth.login_failed' on invalid credentials (enables Cyber Engine BruteForceLoginDetector)
    """
    global CURRENT_ACTIVE_USER
    client_ip = request.client.host if request.client else "127.0.0.1"
    trace_id = f"trc_auth_{uuid.uuid4().hex[:12]}"

    expected_pwd = db.passwords.get(req.username)

    if expected_pwd is None or expected_pwd != req.password:
        # Failed login attempt -> Emit auth.login_failed
        telemetry.emit(
            event_type="auth.login_failed",
            attributes={
                "username": req.username,
                "ip": client_ip,
                "reason": "invalid_credentials" if expected_pwd else "user_not_found",
                "attempt_time": int(uuid.uuid1().time),
                "client_user_agent": request.headers.get("user-agent", "Unknown"),
            },
            source_resource=f"ip:{client_ip}",
            target_resource=f"user:{req.username}",
            trace_id=trace_id,
            severity="warning",
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Success login -> Emit auth.login_success
    CURRENT_ACTIVE_USER = req.username
    user = db.users[req.username]

    telemetry.emit(
        event_type="auth.login_success",
        attributes={
            "username": req.username,
            "user_id": user.id,
            "ip": client_ip,
        },
        source_resource=f"ip:{client_ip}",
        target_resource=f"user:{req.username}",
        trace_id=trace_id,
        severity="info",
    )

    return {
        "status": "authenticated",
        "token": f"jwt_mock_{uuid.uuid4().hex}",
        "user": user,
    }


@router.post("/register")
async def register(req: RegisterRequest):
    """Registers a new user account."""
    if req.username in db.users:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        username=req.username,
        full_name=req.full_name,
        avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face",
        bio=req.bio or "Hey there! I'm using InstaTern.",
        followers_count=0,
        following_count=0,
    )
    db.users[req.username] = new_user
    db.passwords[req.username] = req.password

    telemetry.emit(
        event_type="user.registered",
        attributes={"username": req.username, "user_id": new_user.id},
        severity="info",
    )

    return {"status": "created", "user": new_user}

