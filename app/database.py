import sqlite3
import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from .config import settings
from .models import (
    User, Post, Comment, Story, DirectMessage, Conversation,
    UserProfile, Notification, ActivityAnalytics
)


def hash_password(password: str) -> str:
    """Standard SHA-256 with salt password hashing."""
    salt = "insta_salt_prod_2026_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                avatar_url TEXT NOT NULL,
                bio TEXT DEFAULT '',
                website TEXT DEFAULT '',
                is_verified INTEGER DEFAULT 0,
                is_private INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user',
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS followers (
                follower_username TEXT NOT NULL,
                following_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (follower_username, following_username)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                author_username TEXT NOT NULL,
                image_url TEXT NOT NULL,
                caption TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (author_username) REFERENCES users(username)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                post_id TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (post_id, username)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_posts (
                post_id TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (post_id, username)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                author_username TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (author_username) REFERENCES users(username)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                author_username TEXT NOT NULL,
                media_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (author_username) REFERENCES users(username)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                participant1 TEXT NOT NULL,
                participant2 TEXT NOT NULL,
                last_message TEXT DEFAULT '',
                last_updated TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS direct_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                recipient TEXT NOT NULL,
                sender_username TEXT NOT NULL,
                type TEXT NOT NULL,
                post_id TEXT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            );
            """)
            conn.commit()

        self._seed_default_data()

    def _seed_default_data(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            if cursor.fetchone()["count"] > 0:
                return

            # Rich list of realistic creators and users
            seed_users = [
                (
                    "usr_sarah",
                    "sarah_dev",
                    hash_password("password123"),
                    "Sarah Jenkins",
                    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop&crop=face",
                    "Senior Software Engineer 💻 | Open Source contributor | Coffee lover ☕",
                    "https://sarahdev.io",
                    1, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_marcus",
                    "marcus_photo",
                    hash_password("password123"),
                    "Marcus Chen",
                    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
                    "Architectural & Travel Photographer 📸 | Sony Alpha Creator",
                    "https://marcuschen.visuals",
                    1, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_emily",
                    "emily_style",
                    hash_password("password123"),
                    "Emily Watson",
                    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=face",
                    "Minimalist Living & Studio Design ✨ | London 🇬🇧",
                    "https://emilystyle.co",
                    1, 0, "admin", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_alex",
                    "alex_travels",
                    hash_password("password123"),
                    "Alex Rivera",
                    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face",
                    "Wanderlust seeker 🌍✈️ | 42 countries and counting | Mountaineer 🏔️",
                    "https://alexadventures.blog",
                    0, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_chloe",
                    "chloe_cooks",
                    hash_password("password123"),
                    "Chloe Dubois",
                    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face",
                    "Pastry Chef & Sourdough Artisan 🥖🥐 | Author of 'Crust & Crumb'",
                    "https://chloecooks.com",
                    1, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_david",
                    "david_fitness",
                    hash_password("password123"),
                    "David Okafor",
                    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=face",
                    "Hybrid Athlete & Strength Coach 🏋️‍♂️ | Calisthenics & Marathons",
                    "https://ironandgrit.fit",
                    0, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_lisa",
                    "lisa_art",
                    hash_password("password123"),
                    "Lisa Zhang",
                    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&h=150&fit=crop&crop=face",
                    "Contemporary Oil & Digital Painter 🎨 | Gallery shows NYC & Tokyo",
                    "https://lisazhangart.com",
                    1, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_kevin",
                    "kevin_tech",
                    hash_password("password123"),
                    "Kevin Vance",
                    "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150&h=150&fit=crop&crop=face",
                    "AI Systems Architect & Mechanical Keyboard Builder ⌨️⚡",
                    "https://kevinvance.dev",
                    0, 0, "user", datetime.now(timezone.utc).isoformat(),
                ),
            ]

            cursor.executemany("""
                INSERT INTO users (id, username, password_hash, full_name, avatar_url, bio, website, is_verified, is_private, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_users)

            # Seed Follow Graph
            follows = [
                ("sarah_dev", "marcus_photo"),
                ("sarah_dev", "kevin_tech"),
                ("marcus_photo", "sarah_dev"),
                ("marcus_photo", "lisa_art"),
                ("emily_style", "sarah_dev"),
                ("emily_style", "chloe_cooks"),
                ("alex_travels", "marcus_photo"),
                ("alex_travels", "david_fitness"),
                ("chloe_cooks", "emily_style"),
                ("david_fitness", "alex_travels"),
                ("lisa_art", "marcus_photo"),
                ("kevin_tech", "sarah_dev"),
            ]
            now_str = datetime.now(timezone.utc).isoformat()
            cursor.executemany("INSERT OR IGNORE INTO followers VALUES (?, ?, ?)", [(f[0], f[1], now_str) for f in follows])

            # Seed Posts
            posts_data = [
                (
                    "post_seed_1",
                    "marcus_photo",
                    "https://images.unsplash.com/photo-1510519138197-06b8f2a09616?w=900&auto=format&fit=crop",
                    "Night views from the workspace roof deck. Building things that scale 🚀",
                    json.dumps(["architecture", "city", "design", "skyline"]),
                    "2 hours ago",
                ),
                (
                    "post_seed_2",
                    "sarah_dev",
                    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=900&auto=format&fit=crop",
                    "Clean setup for the week ahead! Minimal distraction = maximum output 💻⚡",
                    json.dumps(["workspace", "developer", "clean", "minimal"]),
                    "4 hours ago",
                ),
                (
                    "post_seed_3",
                    "alex_travels",
                    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=900&auto=format&fit=crop",
                    "Sunsets in the high desert canyon. Endless roads and new horizons 🏜️✨",
                    json.dumps(["travel", "nature", "wanderlust", "roadtrip"]),
                    "6 hours ago",
                ),
                (
                    "post_seed_4",
                    "chloe_cooks",
                    "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=900&auto=format&fit=crop",
                    "Fresh wild-yeast sourdough loaf fresh from the morning bake. That crackle! 🥖🍞",
                    json.dumps(["baking", "sourdough", "bread", "artisan"]),
                    "8 hours ago",
                ),
                (
                    "post_seed_5",
                    "lisa_art",
                    "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=900&auto=format&fit=crop",
                    "Work in progress on the 6ft canvas. Exploring light textures and ultramarine depth 🎨",
                    json.dumps(["art", "painting", "studio", "creative"]),
                    "12 hours ago",
                ),
                (
                    "post_seed_6",
                    "david_fitness",
                    "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=900&auto=format&fit=crop",
                    "5 AM track intervals done. Consistency over intensity every single week 🏃‍♂️💨",
                    json.dumps(["fitness", "running", "training", "discipline"]),
                    "1 day ago",
                ),
            ]
            cursor.executemany("""
                INSERT INTO posts (id, author_username, image_url, caption, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, posts_data)

            # Seed Likes
            likes_data = [
                ("post_seed_1", "sarah_dev"),
                ("post_seed_1", "emily_style"),
                ("post_seed_1", "alex_travels"),
                ("post_seed_2", "marcus_photo"),
                ("post_seed_2", "kevin_tech"),
                ("post_seed_3", "marcus_photo"),
                ("post_seed_3", "sarah_dev"),
                ("post_seed_4", "emily_style"),
                ("post_seed_5", "marcus_photo"),
                ("post_seed_6", "alex_travels"),
            ]
            cursor.executemany("INSERT INTO likes VALUES (?, ?, ?)", [(l[0], l[1], now_str) for l in likes_data])

            # Seed Comments
            comments_data = [
                ("cm_seed_1", "post_seed_1", "sarah_dev", "Stunning framing and lighting on this shot!", "1 hour ago"),
                ("cm_seed_2", "post_seed_1", "alex_travels", "Which city was this captured in?", "45 minutes ago"),
                ("cm_seed_3", "post_seed_2", "kevin_tech", "What keyboard switches are you using there?", "3 hours ago"),
                ("cm_seed_4", "post_seed_4", "emily_style", "That crust texture is absolute perfection 🤤", "5 hours ago"),
                ("cm_seed_5", "post_seed_5", "marcus_photo", "The contrast of cobalt and gold is breathtaking Lisa!", "10 hours ago"),
            ]
            cursor.executemany("""
                INSERT INTO comments (id, post_id, author_username, text, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, comments_data)

            # Seed Stories
            stories_data = [
                ("story_seed_1", "marcus_photo", "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop", "Just now"),
                ("story_seed_2", "alex_travels", "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600&auto=format&fit=crop", "15m ago"),
                ("story_seed_3", "chloe_cooks", "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop", "1h ago"),
                ("story_seed_4", "lisa_art", "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600&auto=format&fit=crop", "2h ago"),
            ]
            cursor.executemany("""
                INSERT INTO stories (id, author_username, media_url, created_at)
                VALUES (?, ?, ?, ?)
            """, stories_data)

            # Seed Notifications
            notifications_data = [
                ("notif_1", "sarah_dev", "marcus_photo", "like", "post_seed_2", "liked your post", "10m ago", 0),
                ("notif_2", "sarah_dev", "kevin_tech", "comment", "post_seed_2", "commented: 'What keyboard switches...'", "3h ago", 0),
                ("notif_3", "sarah_dev", "emily_style", "follow", None, "started following you", "1d ago", 1),
            ]
            cursor.executemany("""
                INSERT INTO notifications (id, recipient, sender_username, type, post_id, text, created_at, is_read)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, notifications_data)

            conn.commit()

    # User operations
    def get_user_by_username(self, username: str, current_username: Optional[str] = None) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_user(conn, row, current_username=current_username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_user(conn, row)

    def verify_user_password(self, username: str, password: str) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
            row = cursor.fetchone()
            if not row:
                return None
            if row["password_hash"] == hash_password(password):
                return self._row_to_user(conn, row)
            return None

    def create_user(self, username: str, password: str, full_name: str, bio: str = "", website: str = "") -> User:
        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        pwd_hash = hash_password(password)
        avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, full_name, avatar_url, bio, website, is_verified, is_private, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'user', ?)
            """, (user_id, username, pwd_hash, full_name, avatar_url, bio, website, now))
            conn.commit()

        return self.get_user_by_username(username)

    def update_user_profile(
        self,
        username: str,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
        website: Optional[str] = None,
        avatar_url: Optional[str] = None,
        is_private: Optional[bool] = None
    ) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name.strip())
            if bio is not None:
                updates.append("bio = ?")
                params.append(bio.strip())
            if website is not None:
                updates.append("website = ?")
                params.append(website.strip())
            if avatar_url is not None:
                updates.append("avatar_url = ?")
                params.append(avatar_url.strip())
            if is_private is not None:
                updates.append("is_private = ?")
                params.append(1 if is_private else 0)

            if not updates:
                return self.get_user_by_username(username)

            params.append(username)
            query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
            cursor.execute(query, params)
            conn.commit()

        return self.get_user_by_username(username)

    def _row_to_user(self, conn, row, current_username: Optional[str] = None) -> User:
        cursor = conn.cursor()
        username = row["username"]
        cursor.execute("SELECT COUNT(*) as count FROM followers WHERE following_username = ?", (username,))
        followers_count = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) as count FROM followers WHERE follower_username = ?", (username,))
        following_count = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) as count FROM posts WHERE author_username = ?", (username,))
        posts_count = cursor.fetchone()["count"]

        is_following = False
        if current_username and current_username != username:
            cursor.execute(
                "SELECT COUNT(*) as count FROM followers WHERE follower_username = ? AND following_username = ?",
                (current_username, username)
            )
            is_following = cursor.fetchone()["count"] > 0

        return User(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            avatar_url=row["avatar_url"],
            bio=row["bio"] or "",
            website=row["website"] if "website" in row.keys() else "",
            followers_count=followers_count,
            following_count=following_count,
            posts_count=posts_count,
            is_verified=bool(row["is_verified"]),
            is_private=bool(row["is_private"]),
            is_following=is_following,
            role=row["role"],
        )

    # Social graph: Follow / Unfollow
    def toggle_follow(self, follower_username: str, target_username: str) -> Dict[str, Any]:
        if follower_username == target_username:
            raise ValueError("You cannot follow yourself")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM followers WHERE follower_username = ? AND following_username = ?",
                (follower_username, target_username)
            )
            exists = cursor.fetchone()["count"] > 0

            if exists:
                cursor.execute(
                    "DELETE FROM followers WHERE follower_username = ? AND following_username = ?",
                    (follower_username, target_username)
                )
                is_following = False
            else:
                cursor.execute(
                    "INSERT INTO followers (follower_username, following_username, created_at) VALUES (?, ?, ?)",
                    (follower_username, target_username, datetime.now(timezone.utc).isoformat())
                )
                is_following = True

                # Create follow notification within the same transaction
                notif_id = f"notif_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO notifications (id, recipient, sender_username, type, post_id, text, created_at, is_read)
                    VALUES (?, ?, ?, 'follow', NULL, 'started following you', 'Just now', 0)
                """, (notif_id, target_username, follower_username))

            cursor.execute("SELECT COUNT(*) as count FROM followers WHERE following_username = ?", (target_username,))
            followers_count = cursor.fetchone()["count"]
            conn.commit()

            return {
                "following": is_following,
                "target_username": target_username,
                "followers_count": followers_count
            }

    def get_followers(self, username: str, current_username: Optional[str] = None) -> List[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.* FROM users u
                JOIN followers f ON f.follower_username = u.username
                WHERE f.following_username = ?
            """, (username,))
            return [self._row_to_user(conn, r, current_username) for r in cursor.fetchall()]

    def get_following(self, username: str, current_username: Optional[str] = None) -> List[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.* FROM users u
                JOIN followers f ON f.following_username = u.username
                WHERE f.follower_username = ?
            """, (username,))
            return [self._row_to_user(conn, r, current_username) for r in cursor.fetchall()]

    def get_suggested_users(self, current_username: str, limit: int = 5) -> List[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.* FROM users u
                WHERE u.username != ?
                AND u.username NOT IN (
                    SELECT following_username FROM followers WHERE follower_username = ?
                )
                ORDER BY RANDOM() LIMIT ?
            """, (current_username, current_username, limit))
            return [self._row_to_user(conn, r, current_username) for r in cursor.fetchall()]

    # Feed, Posts, and Bookmarks
    def get_feed(self, current_username: Optional[str] = None) -> List[Post]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts ORDER BY ROWID DESC")
            rows = cursor.fetchall()
            return [self._hydrate_post(conn, r, current_username) for r in rows if r]

    def get_user_posts(self, username: str, current_username: Optional[str] = None) -> List[Post]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE author_username = ? ORDER BY ROWID DESC", (username,))
            return [self._hydrate_post(conn, r, current_username) for r in cursor.fetchall()]

    def get_saved_posts(self, username: str) -> List[Post]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.* FROM posts p
                JOIN saved_posts sp ON sp.post_id = p.id
                WHERE sp.username = ?
                ORDER BY sp.ROWID DESC
            """, (username,))
            return [self._hydrate_post(conn, r, username) for r in cursor.fetchall()]

    def get_post_by_id(self, post_id: str, current_username: Optional[str] = None) -> Optional[Post]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._hydrate_post(conn, row, current_username)

    def _hydrate_post(self, conn, r, current_username: Optional[str] = None) -> Post:
        cursor = conn.cursor()
        author = self.get_user_by_username(r["author_username"], current_username=current_username)
        post_id = r["id"]

        # Likes
        cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ?", (post_id,))
        likes_count = cursor.fetchone()["count"]

        # Saves
        cursor.execute("SELECT COUNT(*) as count FROM saved_posts WHERE post_id = ?", (post_id,))
        saves_count = cursor.fetchone()["count"]

        is_liked = False
        is_saved = False
        if current_username:
            cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ? AND username = ?", (post_id, current_username))
            is_liked = cursor.fetchone()["count"] > 0
            cursor.execute("SELECT COUNT(*) as count FROM saved_posts WHERE post_id = ? AND username = ?", (post_id, current_username))
            is_saved = cursor.fetchone()["count"] > 0

        # Comments
        cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY ROWID ASC", (post_id,))
        comment_rows = cursor.fetchall()
        comments = []
        for c in comment_rows:
            c_author = self.get_user_by_username(c["author_username"], current_username=current_username)
            if c_author:
                comments.append(Comment(
                    id=c["id"],
                    post_id=post_id,
                    author=c_author,
                    text=c["text"],
                    created_at=c["created_at"]
                ))

        try:
            tags = json.loads(r["tags"])
        except Exception:
            tags = []

        return Post(
            id=post_id,
            author=author,
            image_url=r["image_url"],
            caption=r["caption"] or "",
            likes_count=likes_count,
            comments_count=len(comments),
            saves_count=saves_count,
            comments=comments,
            tags=tags,
            created_at=r["created_at"],
            is_liked=is_liked,
            is_saved=is_saved,
        )

    def create_post(self, username: str, caption: str, image_url: str, tags: List[str]) -> Optional[Post]:
        post_id = f"post_{uuid.uuid4().hex[:10]}"
        now = "Just now"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO posts (id, author_username, image_url, caption, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (post_id, username, image_url, caption, json.dumps(tags or []), now))
            conn.commit()

        return self.get_post_by_id(post_id, current_username=username)

    def delete_post(self, post_id: str, username: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT author_username FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            if not row or row["author_username"] != username:
                return False

            cursor.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
            cursor.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
            cursor.execute("DELETE FROM saved_posts WHERE post_id = ?", (post_id,))
            cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            conn.commit()
            return True

    def toggle_like(self, post_id: str, username: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT author_username FROM posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            if not post:
                raise ValueError("Post not found")

            cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
            exists = cursor.fetchone()["count"] > 0

            if exists:
                cursor.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
                liked = False
            else:
                cursor.execute(
                    "INSERT INTO likes (post_id, username, created_at) VALUES (?, ?, ?)",
                    (post_id, username, datetime.now(timezone.utc).isoformat())
                )
                liked = True

                # Notify author if not self-like
                if post["author_username"] != username:
                    notif_id = f"notif_{uuid.uuid4().hex[:8]}"
                    cursor.execute("""
                        INSERT INTO notifications (id, recipient, sender_username, type, post_id, text, created_at, is_read)
                        VALUES (?, ?, ?, 'like', ?, 'liked your post', 'Just now', 0)
                    """, (notif_id, post["author_username"], username, post_id))

            cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ?", (post_id,))
            likes_count = cursor.fetchone()["count"]
            conn.commit()

            return {"liked": liked, "likes_count": likes_count}

    def toggle_save_post(self, post_id: str, username: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM saved_posts WHERE post_id = ? AND username = ?", (post_id, username))
            exists = cursor.fetchone()["count"] > 0

            if exists:
                cursor.execute("DELETE FROM saved_posts WHERE post_id = ? AND username = ?", (post_id, username))
                saved = False
            else:
                cursor.execute(
                    "INSERT INTO saved_posts (post_id, username, created_at) VALUES (?, ?, ?)",
                    (post_id, username, datetime.now(timezone.utc).isoformat())
                )
                saved = True

            cursor.execute("SELECT COUNT(*) as count FROM saved_posts WHERE post_id = ?", (post_id,))
            saves_count = cursor.fetchone()["count"]
            conn.commit()
            return {"saved": saved, "saves_count": saves_count}

    def add_comment(self, post_id: str, username: str, text: str) -> Optional[Comment]:
        comment_id = f"cm_{uuid.uuid4().hex[:8]}"
        now = "Just now"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT author_username FROM posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            if not post:
                return None

            cursor.execute("""
                INSERT INTO comments (id, post_id, author_username, text, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (comment_id, post_id, username, text, now))

            if post["author_username"] != username:
                snippet = text[:30] + "..." if len(text) > 30 else text
                notif_id = f"notif_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO notifications (id, recipient, sender_username, type, post_id, text, created_at, is_read)
                    VALUES (?, ?, ?, 'comment', ?, ?, 'Just now', 0)
                """, (notif_id, post["author_username"], username, post_id, f"commented: '{snippet}'"))

            conn.commit()

        author = self.get_user_by_username(username)
        return Comment(
            id=comment_id,
            post_id=post_id,
            author=author,
            text=text,
            created_at=now
        )

    # Stories
    def get_stories(self) -> List[Story]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stories ORDER BY ROWID DESC")
            rows = cursor.fetchall()
            stories = []
            for r in rows:
                author = self.get_user_by_username(r["author_username"])
                if author:
                    stories.append(Story(
                        id=r["id"],
                        author=author,
                        media_url=r["media_url"],
                        created_at=r["created_at"]
                    ))
            return stories

    def create_story(self, username: str, media_url: str) -> Optional[Story]:
        story_id = f"story_{uuid.uuid4().hex[:8]}"
        now = "Just now"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stories (id, author_username, media_url, created_at)
                VALUES (?, ?, ?, ?)
            """, (story_id, username, media_url, now))
            conn.commit()

        author = self.get_user_by_username(username)
        return Story(
            id=story_id,
            author=author,
            media_url=media_url,
            created_at=now
        )

    # Advanced Multi-Facet Search
    def advanced_search(
        self,
        query: str,
        entity_type: str = "all",
        sort_by: str = "recent",
        limit: int = 20,
        current_username: Optional[str] = None
    ) -> Dict[str, Any]:
        term = f"%{query.strip()}%"
        is_hashtag = query.strip().startswith("#")
        clean_tag = query.strip().lstrip("#").lower()

        results = {
            "query": query,
            "entity_type": entity_type,
            "sort_by": sort_by,
            "users": [],
            "posts": [],
            "tags": [],
            "total_matches": 0,
        }

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Search Users
            if entity_type in ("all", "users") and not is_hashtag:
                cursor.execute("""
                    SELECT * FROM users
                    WHERE username LIKE ? OR full_name LIKE ? OR bio LIKE ?
                    LIMIT ?
                """, (term, term, term, limit))
                user_rows = cursor.fetchall()
                results["users"] = [self._row_to_user(conn, r, current_username) for r in user_rows]

            # Search Posts
            if entity_type in ("all", "posts", "tags"):
                order_clause = "ORDER BY ROWID DESC"
                if sort_by == "popular":
                    order_clause = "ORDER BY (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) DESC"

                if is_hashtag or entity_type == "tags":
                    cursor.execute(f"""
                        SELECT * FROM posts
                        WHERE LOWER(tags) LIKE ?
                        {order_clause} LIMIT ?
                    """, (f"%{clean_tag}%", limit))
                else:
                    cursor.execute(f"""
                        SELECT * FROM posts
                        WHERE caption LIKE ? OR LOWER(tags) LIKE ?
                        {order_clause} LIMIT ?
                    """, (term, term, limit))

                post_rows = cursor.fetchall()
                results["posts"] = [self._hydrate_post(conn, r, current_username) for r in post_rows]

            # Discover unique tags matching query
            if entity_type in ("all", "tags"):
                cursor.execute("SELECT tags FROM posts")
                all_tags_rows = cursor.fetchall()
                tag_counter = {}
                for r in all_tags_rows:
                    try:
                        t_list = json.loads(r["tags"])
                        for t in t_list:
                            t_lower = t.lower()
                            if clean_tag in t_lower or not clean_tag:
                                tag_counter[t_lower] = tag_counter.get(t_lower, 0) + 1
                    except Exception:
                        pass

                sorted_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:10]
                results["tags"] = [{"tag": t[0], "posts_count": t[1]} for t in sorted_tags]

            results["total_matches"] = len(results["users"]) + len(results["posts"]) + len(results["tags"])
            return results

    # Direct Messaging
    def get_user_conversations(self, username: str) -> List[Conversation]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations
                WHERE participant1 = ? OR participant2 = ?
                ORDER BY last_updated DESC
            """, (username, username))
            rows = cursor.fetchall()

            convs = []
            for r in rows:
                c_id = r["id"]
                cursor.execute("SELECT * FROM direct_messages WHERE conversation_id = ? ORDER BY ROWID ASC", (c_id,))
                msg_rows = cursor.fetchall()
                messages = [
                    DirectMessage(
                        id=m["id"],
                        conversation_id=c_id,
                        sender=m["sender"],
                        recipient=m["recipient"],
                        text=m["text"],
                        timestamp=m["timestamp"]
                    )
                    for m in msg_rows
                ]
                convs.append(Conversation(
                    id=c_id,
                    participants=[r["participant1"], r["participant2"]],
                    last_message=r["last_message"],
                    last_updated=r["last_updated"],
                    messages=messages
                ))
            return convs

    def send_message(self, sender: str, recipient: str, text: str) -> DirectMessage:
        now = datetime.now(timezone.utc).strftime("%H:%M")
        msg_id = f"dm_{uuid.uuid4().hex[:8]}"

        p1, p2 = sorted([sender, recipient])
        conv_id = f"conv_{p1}_{p2}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("""
                    INSERT INTO conversations (id, participant1, participant2, last_message, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (conv_id, p1, p2, text, now))
            else:
                cursor.execute("""
                    UPDATE conversations SET last_message = ?, last_updated = ? WHERE id = ?
                """, (text, now, conv_id))

            cursor.execute("""
                INSERT INTO direct_messages (id, conversation_id, sender, recipient, text, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (msg_id, conv_id, sender, recipient, text, now))

            # Trigger notification
            notif_id = f"notif_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO notifications (id, recipient, sender_username, type, post_id, text, created_at, is_read)
                VALUES (?, ?, ?, 'message', NULL, ?, 'Just now', 0)
            """, (notif_id, recipient, sender, f"sent you a message: '{text[:25]}...'"))

            conn.commit()

        return DirectMessage(
            id=msg_id,
            conversation_id=conv_id,
            sender=sender,
            recipient=recipient,
            text=text,
            timestamp=now
        )

    # Notifications
    def create_notification(
        self,
        recipient: str,
        sender_username: str,
        notif_type: str,
        text: str,
        post_id: Optional[str] = None
    ):
        notif_id = f"notif_{uuid.uuid4().hex[:8]}"
        now = "Just now"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notifications (id, recipient, sender_username, type, post_id, text, created_at, is_read)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (notif_id, recipient, sender_username, notif_type, post_id, text, now))
            conn.commit()

    def get_user_notifications(self, username: str) -> List[Notification]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM notifications
                WHERE recipient = ?
                ORDER BY ROWID DESC LIMIT 30
            """, (username,))
            rows = cursor.fetchall()
            notifs = []
            for r in rows:
                sender = self.get_user_by_username(r["sender_username"])
                if sender:
                    notifs.append(Notification(
                        id=r["id"],
                        recipient=r["recipient"],
                        sender=sender,
                        type=r["type"],
                        post_id=r["post_id"],
                        text=r["text"],
                        created_at=r["created_at"],
                        is_read=bool(r["is_read"])
                    ))
            return notifs

    def mark_notifications_read(self, username: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE recipient = ?", (username,))
            conn.commit()

    # User Profile & Activity Analytics
    def get_full_user_profile(self, target_username: str, current_username: Optional[str] = None) -> Optional[UserProfile]:
        user = self.get_user_by_username(target_username, current_username=current_username)
        if not user:
            return None

        posts = self.get_user_posts(target_username, current_username=current_username)
        saved = self.get_saved_posts(target_username) if current_username == target_username else []

        return UserProfile(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            website=user.website,
            followers_count=user.followers_count,
            following_count=user.following_count,
            posts_count=len(posts),
            is_verified=user.is_verified,
            is_private=user.is_private,
            is_following=user.is_following,
            role=user.role,
            posts=posts,
            saved_posts=saved,
        )

    def get_user_analytics(self, username: str) -> ActivityAnalytics:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            user = self.get_user_by_username(username)
            if not user:
                raise ValueError("User not found")

            # Likes received across all posts
            cursor.execute("""
                SELECT COUNT(*) as count FROM likes l
                JOIN posts p ON p.id = l.post_id
                WHERE p.author_username = ?
            """, (username,))
            total_likes = cursor.fetchone()["count"]

            # Comments received
            cursor.execute("""
                SELECT COUNT(*) as count FROM comments c
                JOIN posts p ON p.id = c.post_id
                WHERE p.author_username = ?
            """, (username,))
            total_comments = cursor.fetchone()["count"]

            # Total posts
            cursor.execute("SELECT tags FROM posts WHERE author_username = ?", (username,))
            post_rows = cursor.fetchall()
            total_posts = len(post_rows)

            tag_counts = {}
            for r in post_rows:
                try:
                    for t in json.loads(r["tags"]):
                        tag_counts[t] = tag_counts.get(t, 0) + 1
                except Exception:
                    pass

            top_tags = sorted([{"tag": k, "count": v} for k, v in tag_counts.items()], key=lambda x: x["count"], reverse=True)[:5]

            # Engagement calculation
            followers = max(user.followers_count, 1)
            engagement = round(((total_likes + total_comments) / (total_posts * followers if total_posts else 1)) * 100, 2)

            return ActivityAnalytics(
                total_posts=total_posts,
                total_likes_received=total_likes,
                total_comments_received=total_comments,
                followers_count=user.followers_count,
                following_count=user.following_count,
                engagement_rate=engagement,
                top_tags=top_tags,
            )


db = Database()
