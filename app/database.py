import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from .models import User, Post, Comment, Story


class MockDatabase:
    """
    In-memory stateful store with realistic Instagram-like content and profiles.
    Allows testing both benign social operations and security attack patterns.
    """

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.passwords: Dict[str, str] = {}
        self.posts: Dict[str, Post] = {}
        self.stories: List[Story] = []
        self.direct_messages: List[Dict] = []
        self._seed_data()

    def _seed_data(self):
        # 1. Seed Users
        u1 = User(
            id="usr_alice",
            username="alice_cyber",
            full_name="Alice Vance",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=face",
            bio="Security Researcher @ Cyber Engine 🛡️ | Distributed Systems & Telemetry",
            followers_count=1420,
            following_count=320,
            is_verified=True,
        )
        u2 = User(
            id="usr_bob",
            username="bob_cloud",
            full_name="Bob Martinez",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
            bio="Kubernetes & Cloud Run whisperer ☁️ | Deploying microservices 24/7",
            followers_count=890,
            following_count=410,
        )
        u3 = User(
            id="usr_charlie",
            username="charlie_vip",
            full_name="Charlie Prince",
            avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face",
            bio="Enterprise CISO 👔 | Zero Trust & Continuous Threat Detection",
            followers_count=5280,
            following_count=190,
            is_verified=True,
            is_private=True,
        )
        u4 = User(
            id="usr_elena",
            username="elena_ai",
            full_name="Elena Rostova",
            avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop&crop=face",
            bio="Deep Learning & Meta LLaMA hacker 🧠✨ | Cyber investigation graphs",
            followers_count=3450,
            following_count=520,
            is_verified=True,
        )

        for u in [u1, u2, u3, u4]:
            self.users[u.username] = u
            self.passwords[u.username] = "SuperSecretPass2026!"

        # 2. Seed Stories
        self.stories = [
            Story(
                id="story_1",
                author=u1,
                media_url="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop",
                created_at="15m ago",
            ),
            Story(
                id="story_2",
                author=u2,
                media_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=600&auto=format&fit=crop",
                created_at="1h ago",
            ),
            Story(
                id="story_3",
                author=u4,
                media_url="https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&auto=format&fit=crop",
                created_at="3h ago",
            ),
            Story(
                id="story_4",
                author=u3,
                media_url="https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop",
                created_at="5h ago",
            ),
        ]

        # 3. Seed Posts
        c1 = Comment(
            id="comm_1",
            post_id="post_1",
            author=u2,
            text="The multi-service correlation pipeline caught the anomaly immediately! 🔥",
            created_at="10m ago",
        )
        c2 = Comment(
            id="comm_2",
            post_id="post_1",
            author=u4,
            text="0 LLM latency on the Fast Track is game changing. Super clean architecture.",
            created_at="5m ago",
        )

        p1 = Post(
            id="post_1",
            author=u1,
            image_url="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=900&auto=format&fit=crop",
            caption="Monitoring our distributed cloud deployment with Cyber Engine! Deterministic fast path + deep LLM investigation gives total visibility across services. 🛡️💻 #cybersecurity #cloudrun #ternline",
            likes_count=128,
            comments_count=2,
            comments=[c1, c2],
            tags=["cybersecurity", "cloudrun", "ternline"],
            created_at="2 hours ago",
            is_liked=False,
        )

        p2 = Post(
            id="post_2",
            author=u2,
            image_url="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=900&auto=format&fit=crop",
            caption="Serverless batch image pipelines running at scale. Telemetry instrumentation in the worker microservice helps detect rogue batch queries instantly. 🚀🌐 #microservices #devsecops",
            likes_count=94,
            comments_count=1,
            comments=[
                Comment(
                    id="comm_3",
                    post_id="post_2",
                    author=u1,
                    text="Make sure the worker job timeouts are configured properly!",
                    created_at="45m ago",
                )
            ],
            tags=["microservices", "devsecops", "kubernetes"],
            created_at="4 hours ago",
            is_liked=True,
        )

        p3 = Post(
            id="post_3",
            author=u4,
            image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=900&auto=format&fit=crop",
            caption="Synthetic attack simulation completed. Gated rule promotion replay verified 100% true-positive detection with zero false alarms! 📊🎯 #meta #cyberengine #securitytesting",
            likes_count=312,
            comments_count=0,
            comments=[],
            tags=["meta", "cyberengine", "securitytesting"],
            created_at="1 day ago",
            is_liked=False,
        )

        for p in [p1, p2, p3]:
            self.posts[p.id] = p

        # 4. Seed Sensitive Direct Messages (for exfiltration simulation)
        self.direct_messages = [
            {
                "id": "dm_101",
                "sender": "charlie_vip",
                "recipient": "alice_cyber",
                "message": "Here is the internal staging API token: sec_tok_stage_994821",
                "sensitive": True,
            },
            {
                "id": "dm_102",
                "sender": "alice_cyber",
                "recipient": "charlie_vip",
                "message": "Thanks Charlie, verifying the zero-trust authorization filter now.",
                "sensitive": False,
            },
            {
                "id": "dm_103",
                "sender": "charlie_vip",
                "recipient": "bob_cloud",
                "message": "Production database connection string: postgresql://admin:rootSecret@db.prod.internal:5432/creds",
                "sensitive": True,
            },
        ]

    def get_feed(self) -> List[Post]:
        return list(self.posts.values())

    def get_post(self, post_id: str) -> Optional[Post]:
        return self.posts.get(post_id)

    def create_post(self, author: User, caption: str, image_url: str, tags: List[str] = None) -> Post:
        post_id = f"post_{uuid.uuid4().hex[:8]}"
        post = Post(
            id=post_id,
            author=author,
            image_url=image_url,
            caption=caption,
            likes_count=0,
            comments_count=0,
            comments=[],
            tags=tags or [],
            created_at="Just now",
            is_liked=False,
        )
        self.posts[post_id] = post
        return post

    def toggle_like(self, post_id: str) -> Optional[Post]:
        post = self.posts.get(post_id)
        if not post:
            return None
        if post.is_liked:
            post.likes_count = max(0, post.likes_count - 1)
            post.is_liked = False
        else:
            post.likes_count += 1
            post.is_liked = True
        return post

    def add_comment(self, post_id: str, author: User, text: str) -> Optional[Comment]:
        post = self.posts.get(post_id)
        if not post:
            return None
        comment_id = f"comm_{uuid.uuid4().hex[:8]}"
        comment = Comment(
            id=comment_id,
            post_id=post_id,
            author=author,
            text=text,
            created_at="Just now",
        )
        post.comments.append(comment)
        post.comments_count = len(post.comments)
        return comment

    def search(self, query: str) -> Dict[str, Any]:
        q = query.lower().strip()
        matched_users = [
            u for u in self.users.values()
            if q in u.username.lower() or q in u.full_name.lower() or q in u.bio.lower()
        ]
        matched_posts = [
            p for p in self.posts.values()
            if q in p.caption.lower() or any(q in t.lower() for t in p.tags)
        ]
        return {
            "users": matched_users,
            "posts": matched_posts,
        }


db = MockDatabase()
