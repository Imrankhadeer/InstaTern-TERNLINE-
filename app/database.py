import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from .models import User, Post, Comment, Story, DirectMessage, Conversation


class MockDatabase:
    """
    In-memory stateful store with realistic Instagram-like content, social graphs,
    and direct messaging threads designed for realistic application behavior
    and comprehensive security vulnerability testing.
    """

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.passwords: Dict[str, str] = {}
        self.posts: Dict[str, Post] = {}
        self.stories: List[Story] = []
        self.conversations: Dict[str, Conversation] = {}
        self.followers: Dict[str, Set[str]] = {}
        self.following: Dict[str, Set[str]] = {}
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
            role="user",
        )
        u2 = User(
            id="usr_bob",
            username="bob_cloud",
            full_name="Bob Martinez",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
            bio="Kubernetes & Cloud Run whisperer ☁️ | Deploying microservices 24/7",
            followers_count=890,
            following_count=410,
            role="user",
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
            role="admin",
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
            role="user",
        )
        u5 = User(
            id="usr_hacker",
            username="hacker_zero",
            full_name="Null Pointer",
            avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face",
            bio="Red Team Penetration Tester 🕶️ | Breaking distributed auth & APIs",
            followers_count=666,
            following_count=13,
            is_verified=False,
            role="user",
        )

        for u in [u1, u2, u3, u4, u5]:
            self.users[u.username] = u
            self.passwords[u.username] = "SuperSecretPass2026!"
            self.followers[u.username] = set()
            self.following[u.username] = set()

        # Follower graph
        self.following["alice_cyber"].update(["bob_cloud", "elena_ai", "charlie_vip"])
        self.followers["bob_cloud"].add("alice_cyber")
        self.followers["elena_ai"].add("alice_cyber")
        self.followers["charlie_vip"].add("alice_cyber")

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

        # 4. Seed Direct Messaging (DMs) with sensitive conversation (Target for BOLA/IDOR)
        conv1_id = "conv_charlie_bob"
        dm1 = DirectMessage(
            id="dm_101",
            conversation_id=conv1_id,
            sender="charlie_vip",
            recipient="bob_cloud",
            text="Bob, here is the secret internal staging API token: sec_tok_stage_994821. Please do not commit this.",
            timestamp="10:30 AM",
            is_sensitive=True,
        )
        dm2 = DirectMessage(
            id="dm_102",
            conversation_id=conv1_id,
            sender="bob_cloud",
            recipient="charlie_vip",
            text="Understood Charlie, storing it directly in Google Secret Manager.",
            timestamp="10:32 AM",
            is_sensitive=False,
        )
        dm3 = DirectMessage(
            id="dm_103",
            conversation_id=conv1_id,
            sender="charlie_vip",
            recipient="bob_cloud",
            text="Production database connection string: postgresql://admin:RootCluster991@db.prod.internal:5432/user_vault",
            timestamp="10:35 AM",
            is_sensitive=True,
        )

        self.conversations[conv1_id] = Conversation(
            id=conv1_id,
            participants=["charlie_vip", "bob_cloud"],
            last_message="Production database connection string: postgresql://admin:...",
            last_updated="10:35 AM",
            messages=[dm1, dm2, dm3],
        )

        conv2_id = "conv_alice_elena"
        self.conversations[conv2_id] = Conversation(
            id=conv2_id,
            participants=["alice_cyber", "elena_ai"],
            last_message="The model weights look solid for the Deep Track investigation loop.",
            last_updated="11:15 AM",
            messages=[
                DirectMessage(
                    id="dm_201",
                    conversation_id=conv2_id,
                    sender="alice_cyber",
                    recipient="elena_ai",
                    text="Hey Elena, did you review the candidate detection rules from the Meta AI investigation?",
                    timestamp="11:10 AM",
                ),
                DirectMessage(
                    id="dm_202",
                    conversation_id=conv2_id,
                    sender="elena_ai",
                    recipient="alice_cyber",
                    text="The model weights look solid for the Deep Track investigation loop.",
                    timestamp="11:15 AM",
                ),
            ],
        )

    # --- Posts & Feed ---
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

    def delete_post(self, post_id: str, requester_username: str, bypass_owner_check: bool = False) -> bool:
        """Deletes a post. If bypass_owner_check is True, demonstrates BOLA/IDOR vulnerability."""
        post = self.posts.get(post_id)
        if not post:
            return False
        if not bypass_owner_check and post.author.username != requester_username:
            raise PermissionError("Forbidden: You cannot delete another user's post")
        del self.posts[post_id]
        return True

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

    # --- Direct Messaging & BOLA Target ---
    def get_user_conversations(self, username: str) -> List[Conversation]:
        """Returns all conversations where the user is a participant."""
        return [
            c for c in self.conversations.values()
            if username in c.participants
        ]

    def get_conversation(self, conv_id: str, requester_username: str, bypass_auth: bool = False) -> Optional[Conversation]:
        """
        Fetches conversation messages.
        If bypass_auth is True, simulates a BOLA / IDOR vulnerability exposing private messages.
        """
        conv = self.conversations.get(conv_id)
        if not conv:
            return None
        if not bypass_auth and requester_username not in conv.participants:
            raise PermissionError(f"Access Denied: User '{requester_username}' is not a participant of this conversation")
        return conv

    def send_direct_message(self, sender: str, recipient: str, text: str) -> DirectMessage:
        # Find or create conversation
        conv = None
        for c in self.conversations.values():
            if set(c.participants) == {sender, recipient}:
                conv = c
                break

        if not conv:
            conv_id = f"conv_{sender}_{recipient}"
            conv = Conversation(
                id=conv_id,
                participants=[sender, recipient],
                last_message=text,
                last_updated="Just now",
                messages=[],
            )
            self.conversations[conv_id] = conv

        dm_id = f"dm_{uuid.uuid4().hex[:8]}"
        is_sensitive = any(kw in text.lower() for kw in ["password", "token", "secret", "conn_str", "postgresql://"])
        dm = DirectMessage(
            id=dm_id,
            conversation_id=conv.id,
            sender=sender,
            recipient=recipient,
            text=text,
            timestamp=datetime.now().strftime("%I:%M %p"),
            is_sensitive=is_sensitive,
        )
        conv.messages.append(dm)
        conv.last_message = text
        conv.last_updated = "Just now"
        return dm

    # --- Social Graph (Follow/Unfollow) ---
    def follow_user(self, follower: str, target: str) -> bool:
        if follower == target or target not in self.users:
            return False
        self.following[follower].add(target)
        self.followers[target].add(follower)
        self.users[target].followers_count = len(self.followers[target])
        self.users[follower].following_count = len(self.following[follower])
        return True

    def unfollow_user(self, follower: str, target: str) -> bool:
        if target not in self.users:
            return False
        self.following[follower].discard(target)
        self.followers[target].discard(follower)
        self.users[target].followers_count = len(self.followers[target])
        self.users[follower].following_count = len(self.following[follower])
        return True

    # --- Search ---
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

    # --- Admin / Metrics ---
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_users": len(self.users),
            "total_posts": len(self.posts),
            "total_stories": len(self.stories),
            "total_conversations": len(self.conversations),
            "total_dms": sum(len(c.messages) for c in self.conversations.values()),
            "system_status": "operational",
        }

    def admin_dump_users(self) -> List[Dict[str, Any]]:
        dump = []
        for u in self.users.values():
            dump.append({
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "password_hash": "$2b$12$e8F.vQk4a2Z.bM5m1xX9u.SuperHashDumpSimulated",
                "session_tokens": [f"sess_{uuid.uuid4().hex[:16]}"],
            })
        return dump


db = MockDatabase()
