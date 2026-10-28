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


def test_story_creation():
    res = client.post(
        "/api/stories",
        json={"media_url": "https://images.unsplash.com/photo-test-story"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["author"]["username"] == "alice_cyber"


def test_post_creation_like_and_comments():
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

    # Add comment
    res_comm = client.post(
        f"/api/posts/{post_id}/comments",
        json={"text": "Awesome shot!"},
    )
    assert res_comm.status_code == 200
    comm = res_comm.json()
    assert comm["text"] == "Awesome shot!"


def test_direct_messages_and_bola_idor():
    # 1. List conversations
    res = client.get("/api/messages")
    assert res.status_code == 200
    convs = res.json()
    assert len(convs) >= 1

    # 2. Access unauthorized executive conversation (charlie and bob) as alice -> 403 Forbidden
    res_denied = client.get("/api/messages/conv_charlie_bob")
    assert res_denied.status_code == 403

    # 3. Exploit BOLA / IDOR vulnerability with exploit_bola=True -> 200 OK with leaked secrets
    res_bola = client.get("/api/messages/conv_charlie_bob?exploit_bola=true")
    assert res_bola.status_code == 200
    stolen = res_bola.json()
    assert len(stolen["messages"]) >= 2
    assert any("postgresql://" in m["text"] for m in stolen["messages"])

    # 4. Send legitimate message
    res_send = client.post(
        "/api/messages",
        json={"recipient": "bob_cloud", "text": "Deploying the security probe now."},
    )
    assert res_send.status_code == 200
    assert res_send.json()["recipient"] == "bob_cloud"


def test_admin_metrics_and_privilege_escalation():
    # 1. Admin metrics
    res_metrics = client.get("/api/admin/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert metrics["total_users"] >= 4

    # 2. Unauthorized user attempt to dump credentials -> 403 Forbidden
    res_denied = client.get("/api/admin/dump-users")
    assert res_denied.status_code == 403

    # 3. Simulated privilege escalation bypass -> 200 OK with user hashes
    res_dump = client.get("/api/admin/dump-users?bypass_role_check=true")
    assert res_dump.status_code == 200
    dump = res_dump.json()
    assert dump["records_count"] >= 4
    assert "password_hash" in dump["data"][0]


def test_follow_and_unfollow():
    res_follow = client.post("/api/users/bob_cloud/follow")
    assert res_follow.status_code == 200
    assert res_follow.json()["status"] == "following"

    res_unfollow = client.post("/api/users/bob_cloud/unfollow")
    assert res_unfollow.status_code == 200
    assert res_unfollow.json()["status"] == "unfollowed"


def test_search_normal_and_sqli():
    res_norm = client.get("/api/search?q=alice")
    assert res_norm.status_code == 200

    res_sqli = client.get("/api/search?q=' OR 1=1--")
    assert res_sqli.status_code == 200
    assert res_sqli.json()["attack_detected_by_app"] is True
    assert res_sqli.json()["results"]["leaked_user_rows"] == 850


def test_attack_suite_scenarios():
    # Scenario 1: Brute force
    res_bf = client.post("/api/attacks/brute-force", json={"target_username": "charlie_vip", "attempts": 3})
    assert res_bf.status_code == 200
    assert res_bf.json()["attempts_fired"] == 3

    # Scenario 2: APT exfiltration
    res_apt = client.post("/api/attacks/cross-service-exfil", json={"target_table": "users", "rows_affected": 500})
    assert res_apt.status_code == 200
    assert len(res_apt.json()["stages"]) == 3

    # Scenario 3: BOLA theft
    res_bola = client.post("/api/attacks/bola-dm-theft")
    assert res_bola.status_code == 200
    assert len(res_bola.json()["leaked_messages"]) >= 2

    # Scenario 4: Search SQLi
    res_sqli = client.post("/api/attacks/search-sqli")
    assert res_sqli.status_code == 200

    # Scenario 5: Scraper bot
    res_scrape = client.post("/api/attacks/api-scraping")
    assert res_scrape.status_code == 200
    assert res_scrape.json()["requests_burst"] >= 10

    # Scenario 6: Privilege escalation
    res_priv = client.post("/api/attacks/privilege-escalation")
    assert res_priv.status_code == 200
    assert res_priv.json()["dumped_users"] >= 4

    # Scenario 7: Benign traffic
    res_benign = client.post("/api/attacks/benign-traffic")
    assert res_benign.status_code == 200
    assert res_benign.json()["events_fired"] == 3
