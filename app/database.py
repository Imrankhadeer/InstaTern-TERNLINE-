import sqlite3
import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from .config import settings
from .models import User, Post, Comment, Story, DirectMessage, Conversation


def hash_password(password: str) -> str:
    """Standard SHA-256 with salt password hashing."""
    salt = "insta_salt_prod_2026_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
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
            conn.commit()

        self._seed_default_data()

    def _seed_default_data(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            if cursor.fetchone()["count"] > 0:
                return

            # Seed real starter users
            seed_users = [
                (
                    "usr_sarah",
                    "sarah_dev",
                    hash_password("password123"),
                    "Sarah Jenkins",
                    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop&crop=face",
                    "Senior Software Engineer 💻 | Open Source contributor | Coffee lover ☕",
                    1,
                    0,
                    "user",
                    datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_marcus",
                    "marcus_photo",
                    hash_password("password123"),
                    "Marcus Chen",
                    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
                    "Architectural & Travel Photographer 📸 | Sony Alpha Creator",
                    1,
                    0,
                    "user",
                    datetime.now(timezone.utc).isoformat(),
                ),
                (
                    "usr_emily",
                    "emily_style",
                    hash_password("password123"),
                    "Emily Watson",
                    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=face",
                    "Minimalist Living & Studio Design ✨ | London 🇬🇧",
                    1,
                    0,
                    "admin",
                    datetime.now(timezone.utc).isoformat(),
                ),
            ]

            cursor.executemany("""
                INSERT INTO users (id, username, password_hash, full_name, avatar_url, bio, is_verified, is_private, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_users)

            # Seed followers
            cursor.execute("INSERT INTO followers VALUES (?, ?, ?)", ("sarah_dev", "marcus_photo", datetime.now(timezone.utc).isoformat()))
            cursor.execute("INSERT INTO followers VALUES (?, ?, ?)", ("emily_style", "sarah_dev", datetime.now(timezone.utc).isoformat()))

            # Seed posts
            post_1_id = "post_seed_1"
            cursor.execute("""
                INSERT INTO posts (id, author_username, image_url, caption, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                post_1_id,
                "marcus_photo",
                "https://images.unsplash.com/photo-1510519138197-06b8f2a09616?w=900&auto=format&fit=crop",
                "Night views from the workspace roof deck. Building things that scale 🚀",
                json.dumps(["architecture", "city", "design"]),
                "2 hours ago",
            ))

            post_2_id = "post_seed_2"
            cursor.execute("""
                INSERT INTO posts (id, author_username, image_url, caption, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                post_2_id,
                "sarah_dev",
                "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=900&auto=format&fit=crop",
                "Clean setup for the week ahead! Minimal distraction = maximum output 💻⚡",
                json.dumps(["workspace", "developer", "clean"]),
                "5 hours ago",
            ))

            # Seed likes
            cursor.execute("INSERT INTO likes VALUES (?, ?, ?)", (post_1_id, "sarah_dev", datetime.now(timezone.utc).isoformat()))
            cursor.execute("INSERT INTO likes VALUES (?, ?, ?)", (post_2_id, "marcus_photo", datetime.now(timezone.utc).isoformat()))

            # Seed comments
            cursor.execute("""
                INSERT INTO comments (id, post_id, author_username, text, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "cm_seed_1",
                post_1_id,
                "sarah_dev",
                "Stunning framing on this shot!",
                "1 hour ago",
            ))

            # Seed story
            cursor.execute("""
                INSERT INTO stories (id, author_username, media_url, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                "story_seed_1",
                "marcus_photo",
                "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop",
                "Just now",
            ))

            conn.commit()

    # User operations
    def get_user_by_username(self, username: str) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_user(conn, row)

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
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return None
            if row["password_hash"] == hash_password(password):
                return self._row_to_user(conn, row)
            return None

    def create_user(self, username: str, password: str, full_name: str, bio: str = "") -> User:
        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        pwd_hash = hash_password(password)
        avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, full_name, avatar_url, bio, is_verified, is_private, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'user', ?)
            """, (user_id, username, pwd_hash, full_name, avatar_url, bio, now))
            conn.commit()

        return self.get_user_by_username(username)

    def update_user_profile(self, username: str, full_name: Optional[str], bio: Optional[str], avatar_url: Optional[str]) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            if bio is not None:
                updates.append("bio = ?")
                params.append(bio)
            if avatar_url is not None:
                updates.append("avatar_url = ?")
                params.append(avatar_url)

            if not updates:
                return self.get_user_by_username(username)

            params.append(username)
            query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
            cursor.execute(query, params)
            conn.commit()

        return self.get_user_by_username(username)

    def _row_to_user(self, conn, row) -> User:
        cursor = conn.cursor()
        username = row["username"]
        cursor.execute("SELECT COUNT(*) as count FROM followers WHERE following_username = ?", (username,))
        followers_count = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) as count FROM followers WHERE follower_username = ?", (username,))
        following_count = cursor.fetchone()["count"]

        return User(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            avatar_url=row["avatar_url"],
            bio=row["bio"] or "",
            followers_count=followers_count,
            following_count=following_count,
            is_verified=bool(row["is_verified"]),
            is_private=bool(row["is_private"]),
            role=row["role"],
        )

    # Feed and Posts
    def get_feed(self, current_username: Optional[str] = None) -> List[Post]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts ORDER BY ROWID DESC")
            rows = cursor.fetchall()

            posts = []
            for r in rows:
                author = self.get_user_by_username(r["author_username"])
                if not author:
                    continue

                post_id = r["id"]
                # Get likes
                cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ?", (post_id,))
                likes_count = cursor.fetchone()["count"]

                is_liked = False
                if current_username:
                    cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ? AND username = ?", (post_id, current_username))
                    is_liked = cursor.fetchone()["count"] > 0

                # Get comments
                cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY ROWID ASC", (post_id,))
                comment_rows = cursor.fetchall()
                comments = []
                for c in comment_rows:
                    c_author = self.get_user_by_username(c["author_username"])
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

                posts.append(Post(
                    id=post_id,
                    author=author,
                    image_url=r["image_url"],
                    caption=r["caption"] or "",
                    likes_count=likes_count,
                    comments_count=len(comments),
                    comments=comments,
                    tags=tags,
                    created_at=r["created_at"],
                    is_liked=is_liked
                ))

            return posts

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

        author = self.get_user_by_username(username)
        return Post(
            id=post_id,
            author=author,
            image_url=image_url,
            caption=caption,
            likes_count=0,
            comments_count=0,
            comments=[],
            tags=tags or [],
            created_at=now,
            is_liked=False
        )

    def toggle_like(self, post_id: str, username: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
            exists = cursor.fetchone()["count"] > 0

            if exists:
                cursor.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
                liked = False
            else:
                cursor.execute("INSERT INTO likes (post_id, username, created_at) VALUES (?, ?, ?)",
                               (post_id, username, datetime.now(timezone.utc).isoformat()))
                liked = True

            cursor.execute("SELECT COUNT(*) as count FROM likes WHERE post_id = ?", (post_id,))
            likes_count = cursor.fetchone()["count"]
            conn.commit()

            return {"liked": liked, "likes_count": likes_count}

    def add_comment(self, post_id: str, username: str, text: str) -> Optional[Comment]:
        comment_id = f"cm_{uuid.uuid4().hex[:8]}"
        now = "Just now"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO comments (id, post_id, author_username, text, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (comment_id, post_id, username, text, now))
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

    # Search
    def search(self, query: str) -> Dict[str, Any]:
        term = f"%{query.strip()}%"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username LIKE ? OR full_name LIKE ? LIMIT 10", (term, term))
            user_rows = cursor.fetchall()
            users = [self._row_to_user(conn, r) for r in user_rows]

            cursor.execute("SELECT * FROM posts WHERE caption LIKE ? OR tags LIKE ? LIMIT 10", (term, term))
            post_rows = cursor.fetchall()
            posts = []
            for r in post_rows:
                author = self.get_user_by_username(r["author_username"])
                if author:
                    posts.append(Post(
                        id=r["id"],
                        author=author,
                        image_url=r["image_url"],
                        caption=r["caption"] or "",
                        likes_count=0,
                        comments_count=0,
                        comments=[],
                        tags=[],
                        created_at=r["created_at"],
                        is_liked=False
                    ))

            return {"users": users, "posts": posts}

    # Messaging
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
            conn.commit()

        return DirectMessage(
            id=msg_id,
            conversation_id=conv_id,
            sender=sender,
            recipient=recipient,
            text=text,
            timestamp=now
        )


db = Database()
