import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add instagram_app directory to python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app
from app.telemetry import telemetry
from app.database import db

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "cyber_engine_connection" in data


def test_feed_and_stories():
    res_feed = client.get("/api/feed")
    assert res_feed.status_code == 200
    feed = res_feed.json()
    assert isinstance(feed, list)
    assert len(feed) >= 1

    res_stories = client.get("/api/stories")
    assert res_stories.status_code == 200
    stories = res_stories.json()
    assert isinstance(stories, list)
    assert len(stories) >= 1


def test_post_creation_and_like():
    post_payload = {
        "caption": "Testing automated post creation from test suite! #test",
        "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b",
        "tags": ["test", "automation"],
    }
    res_post = client.post("/api/posts", json=post_payload)
    assert res_post.status_code == 200
    post = res_post.json()
    assert post["caption"] == post_payload["caption"]
    post_id = post["id"]

    # Like the post
    res_like = client.post(f"/api/posts/{post_id}/like")
    assert res_like.status_code == 200
    liked_post = res_like.json()
    assert liked_post["is_liked"] is True
    assert liked_post["likes_count"] == 1

    # Add comment
    res_comm = client.post(
        f"/api/posts/{post_id}/comments",
        json={"text": "Awesome shot!"},
    )
    assert res_comm.status_code == 200
    comm = res_comm.json()
    assert comm["text"] == "Awesome shot!"


def test_search_normal_and_sqli():
    # Normal search
    res_norm = client.get("/api/search?q=alice")
    assert res_norm.status_code == 200
    norm_data = res_norm.json()
    assert "results" in norm_data

    # SQL Injection search simulation
    res_sqli = client.get("/api/search?q=' OR 1=1--")
    assert res_sqli.status_code == 200
    sqli_data = res_sqli.json()
    assert sqli_data["attack_detected_by_app"] is True
    assert sqli_data["results"]["leaked_user_rows"] == 850


def test_brute_force_attack_simulation():
    res = client.post(
        "/api/attacks/brute-force",
        json={"target_username": "charlie_vip", "attempts": 3},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["attack"] == "brute_force_login"
    assert data["attempts_fired"] == 3
    assert len(data["events"]) == 3
    assert data["detector_targeted"] == "BruteForceLoginDetector"


def test_cross_service_exfil_attack_simulation():
    res = client.post(
        "/api/attacks/cross-service-exfil",
        json={"target_table": "users", "rows_affected": 500},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["attack"] == "cross_service_exfiltration"
    assert len(data["events"]) == 3
    assert data["detector_targeted"] == "CrossServiceExfiltrationDetector"
    assert "correlated_trace_id" in data


def test_recent_telemetry_dock():
    res = client.get("/api/attacks/recent-telemetry")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    assert len(events) >= 1

