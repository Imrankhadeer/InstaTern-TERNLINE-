import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app

client = TestClient(app)


def get_auth_token(username: str = "sarah_dev", password: str = "password123") -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    return res.json()["access_token"]


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_auth_and_profile_flow():
    token = get_auth_token("sarah_dev")
    # /api/auth/me
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["username"] == "sarah_dev"

    # /api/auth/users/{username}
    res_profile = client.get("/api/auth/users/marcus_photo", headers={"Authorization": f"Bearer {token}"})
    assert res_profile.status_code == 200
    p = res_profile.json()
    assert p["username"] == "marcus_photo"
    assert "posts" in p
    assert p["posts_count"] >= 1


def test_social_graph_follow_flow():
    token = get_auth_token("alex_travels")

    # Follow chloe_cooks
    res_follow = client.post(
        "/api/auth/users/chloe_cooks/follow",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_follow.status_code == 200
    assert res_follow.json()["following"] is True

    # List followers of chloe_cooks
    res_followers = client.get("/api/auth/users/chloe_cooks/followers")
    assert res_followers.status_code == 200
    followers = [u["username"] for u in res_followers.json()]
    assert "alex_travels" in followers

    # Unfollow
    res_unfollow = client.post(
        "/api/auth/users/chloe_cooks/follow",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_unfollow.status_code == 200
    assert res_unfollow.json()["following"] is False


def test_creator_analytics():
    res = client.get("/api/auth/users/marcus_photo/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "engagement_rate" in data
    assert "total_likes_received" in data
    assert "top_tags" in data


def test_advanced_search():
    # Search by creator name
    res_creator = client.get("/api/search?q=marcus&type=users")
    assert res_creator.status_code == 200
    assert len(res_creator.json()["results"]["users"]) >= 1

    # Search by tag
    res_tag = client.get("/api/search?q=architecture&type=tags")
    assert res_tag.status_code == 200
    assert len(res_tag.json()["results"]["posts"]) >= 1

    # Search popular sorting
    res_pop = client.get("/api/search?q=clean&sort=popular")
    assert res_pop.status_code == 200
    assert "results" in res_pop.json()


def test_post_creation_save_and_like():
    token = get_auth_token("sarah_dev")

    # Create post
    new_post = client.post(
        "/api/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "caption": "Complex endpoint testing #dev #cloud",
            "image_url": "https://images.unsplash.com/photo-1510519138197-06b8f2a09616",
            "tags": ["dev", "cloud"]
        }
    )
    assert new_post.status_code == 200
    post_id = new_post.json()["id"]

    # Save / bookmark post
    res_save = client.post(f"/api/posts/{post_id}/save", headers={"Authorization": f"Bearer {token}"})
    assert res_save.status_code == 200
    assert res_save.json()["saved"] is True

    # Get saved posts
    res_saved_list = client.get("/api/posts/saved/me", headers={"Authorization": f"Bearer {token}"})
    assert res_saved_list.status_code == 200
    assert any(p["id"] == post_id for p in res_saved_list.json())


def test_notifications_flow():
    token = get_auth_token("alex_travels")

    # Send comment to trigger notification to post owner
    client.post(
        "/api/posts/post_seed_2/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Awesome workspace Sarah!"}
    )

    # Login as sarah_dev and verify notification
    token_sarah = get_auth_token("sarah_dev")
    res_notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_sarah}"})
    assert res_notifs.status_code == 200
    notifs = res_notifs.json()
    assert len(notifs) >= 1

    # Mark notifications read
    res_read = client.post("/api/notifications/read", headers={"Authorization": f"Bearer {token_sarah}"})
    assert res_read.status_code == 200


def test_social_router_endpoints():
    token = get_auth_token("sarah_dev")
    # Follow via /api/social/follow/{username}
    res_follow = client.post("/api/social/follow/marcus_photo", headers={"Authorization": f"Bearer {token}"})
    assert res_follow.status_code == 200
    assert res_follow.json()["following"] is True

    # Get followers list
    res_followers = client.get("/api/social/followers/marcus_photo", headers={"Authorization": f"Bearer {token}"})
    assert res_followers.status_code == 200
    assert any(u["username"] == "sarah_dev" for u in res_followers.json())

    # Get following list
    res_following = client.get("/api/social/following/sarah_dev", headers={"Authorization": f"Bearer {token}"})
    assert res_following.status_code == 200
    assert any(u["username"] == "marcus_photo" for u in res_following.json())

    # Get suggestions
    res_sugg = client.get("/api/social/suggestions", headers={"Authorization": f"Bearer {token}"})
    assert res_sugg.status_code == 200
    assert isinstance(res_sugg.json(), list)

    # Unfollow via /api/social/unfollow/{username}
    res_unfollow = client.post("/api/social/unfollow/marcus_photo", headers={"Authorization": f"Bearer {token}"})
    assert res_unfollow.status_code == 200
    assert res_unfollow.json()["following"] is False


def test_telemetry_sdk_integration():
    from app.telemetry import telemetry

    # Health check should return telemetry info
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "telemetry" in data
    assert "enabled" in data["telemetry"]

    # Making requests with custom trace ID propagates to telemetry
    custom_trace = f"trc_test_{uuid.uuid4().hex[:12]}"
    res_feed = client.get("/api/feed", headers={"x-trace-id": custom_trace})
    assert res_feed.status_code == 200

    # Verify telemetry has captured the recent event
    matching = [e for e in telemetry.recent_events if e.get("trace_id") == custom_trace]
    assert len(matching) >= 1
    assert matching[0]["event_type"] == "http.request"
    assert matching[0]["attributes"]["status_code"] == 200
