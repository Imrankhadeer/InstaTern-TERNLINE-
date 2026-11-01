import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app
from app.database import db

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_auth_login_and_me():
    # Login with default seeded account
    res = client.post(
        "/api/auth/login",
        json={"username": "sarah_dev", "password": "password123"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    token = data["access_token"]

    # Access current user profile using bearer token
    res_me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_me.status_code == 200
    me = res_me.json()
    assert me["username"] == "sarah_dev"
    assert me["full_name"] == "Sarah Jenkins"


def test_register_new_user():
    username = f"test_user_{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "valid_secure_pass123",
            "full_name": "Test User",
            "bio": "Production tester account"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["username"] == username
    assert "access_token" in data


def test_feed_and_posts():
    # Fetch public feed
    res_feed = client.get("/api/feed")
    assert res_feed.status_code == 200
    feed = res_feed.json()
    assert isinstance(feed, list)
    assert len(feed) >= 1

    # Login to create post
    login_res = client.post(
        "/api/auth/login",
        json={"username": "sarah_dev", "password": "password123"}
    )
    token = login_res.json()["access_token"]

    # Create a post
    new_post = client.post(
        "/api/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "caption": "Real production test post",
            "image_url": "https://images.unsplash.com/photo-1510519138197-06b8f2a09616",
            "tags": ["tech", "launch"]
        }
    )
    assert new_post.status_code == 200
    post_data = new_post.json()
    assert post_data["caption"] == "Real production test post"

    # Like the post
    post_id = post_data["id"]
    like_res = client.post(
        f"/api/posts/{post_id}/like",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert like_res.status_code == 200
    assert like_res.json()["liked"] is True

    # Comment on the post
    comment_res = client.post(
        f"/api/posts/{post_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Awesome post!"}
    )
    assert comment_res.status_code == 200
    assert comment_res.json()["text"] == "Awesome post!"


def test_direct_messaging():
    # Login as sarah_dev
    login1 = client.post("/api/auth/login", json={"username": "sarah_dev", "password": "password123"})
    token1 = login1.json()["access_token"]

    # Send message to marcus_photo
    msg_res = client.post(
        "/api/messages",
        headers={"Authorization": f"Bearer {token1}"},
        json={"recipient": "marcus_photo", "text": "Hey Marcus, nice photos!"}
    )
    assert msg_res.status_code == 200
    msg = msg_res.json()
    assert msg["sender"] == "sarah_dev"
    assert msg["recipient"] == "marcus_photo"

    # List conversations
    convs_res = client.get("/api/messages", headers={"Authorization": f"Bearer {token1}"})
    assert convs_res.status_code == 200
    convs = convs_res.json()
    assert len(convs) >= 1


def test_search():
    res = client.get("/api/search?q=sarah")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]["users"]) >= 1
    assert data["results"]["users"][0]["username"] == "sarah_dev"
