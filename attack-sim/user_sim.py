#!/usr/bin/env python3
"""
Interactive CLI & Automated Simulator for Normal User Activity on Instagram App.

Supports:
1. Interactive Menu Mode (prompts with numbered options to choose user, actions, etc.)
2. Command-Line Arguments Mode (for automated scripting and pipelines)
"""

import os
import sys
import time
import random
import argparse
import requests
from typing import Optional, List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure standard output can print Unicode characters on Windows consoles
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_TARGET = os.getenv("TARGET_APP_URL", "https://myapp-v1-p9qy.onrender.com")

SAMPLE_USERS = [
    {"username": "sarah_dev", "password": "password123", "name": "Sarah Developer"},
    {"username": "marcus_photo", "password": "password123", "name": "Marcus Photographer"},
    {"username": "emily_style", "password": "password123", "name": "Emily Style"},
    {"username": "alex_travels", "password": "password123", "name": "Alex Travels"},
]

POPULAR_TAGS = ["photography", "travel", "nature", "coding", "food", "design", "tech"]
SAMPLE_COMMENTS = [
    "Awesome shot! Fire!",
    "Love the lighting here!",
    "Great work, keep it up!",
    "So inspiring!",
    "Incredible view!",
    "Looks amazing!"
]
SAMPLE_DMS = [
    "Hey! How is your week going?",
    "Loved your latest post!",
    "Are you going to the meetup tomorrow?",
    "Check out this picture when you get a chance!"
]


class NormalUserSimulator:
    def __init__(self, target_url: str = DEFAULT_TARGET, delay: float = 0.4):
        self.target_url = target_url.rstrip("/")
        self.delay = delay
        self.session = requests.Session()
        self.current_user: Optional[str] = None
        self.token: Optional[str] = None

    def _sleep(self):
        if self.delay > 0:
            time.sleep(self.delay + random.uniform(0.1, 0.2))

    def _auth_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def print_action(self, action: str, details: str = ""):
        user_badge = f"[@{self.current_user}]" if self.current_user else "[Guest]"
        print(f"  {user_badge:<16} -> {action:<24} {details}")

    # -------------------------------------------------------------------------
    # Authentication & Session
    # -------------------------------------------------------------------------
    def login(self, username: str = "sarah_dev", password: str = "password123") -> bool:
        """Authenticate as a normal user."""
        try:
            res = self.session.post(
                f"{self.target_url}/api/auth/login",
                json={"username": username, "password": password},
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("access_token")
                self.current_user = username
                self.print_action("Logged in", f"Welcome @{username}!")
                return True
            else:
                self.print_action("Login failed", f"HTTP {res.status_code}: {res.text[:80]}")
                return False
        except Exception as e:
            self.print_action("Connection error", str(e))
            return False

    # -------------------------------------------------------------------------
    # 1. Browsing Experience (Feed & Stories)
    # -------------------------------------------------------------------------
    def browse_feed(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Browse the user home feed."""
        self._sleep()
        try:
            res = self.session.get(
                f"{self.target_url}/api/feed",
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code == 200:
                feed = res.json()
                self.print_action("Browsed Feed", f"Fetched {len(feed)} posts")
                for post in feed[:limit]:
                    author = post.get("username") or post.get("author", "unknown")
                    caption = (post.get("caption") or "").replace("\n", " ")[:40]
                    likes = post.get("likes_count", 0)
                    print(f"      - [{post.get('id')}] @{author}: \"{caption}\" ({likes} likes)")
                return feed
            else:
                self.print_action("Feed error", f"HTTP {res.status_code}")
                return []
        except Exception as e:
            self.print_action("Feed request failed", str(e))
            return []

    def view_stories(self) -> List[Dict[str, Any]]:
        """Watch user stories."""
        self._sleep()
        try:
            res = self.session.get(
                f"{self.target_url}/api/stories",
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code == 200:
                stories = res.json()
                self.print_action("Watched Stories", f"Loaded {len(stories)} active stories")
                for s in stories[:5]:
                    author = s.get("username", "unknown")
                    print(f"      - Story by @{author} [{s.get('id')}]")
                return stories
            else:
                self.print_action("Stories error", f"HTTP {res.status_code}")
                return []
        except Exception as e:
            self.print_action("Stories request failed", str(e))
            return []

    # -------------------------------------------------------------------------
    # 2. Social Interactions (Likes, Comments, Follows)
    # -------------------------------------------------------------------------
    def like_post(self, post_id: str):
        """Like a post."""
        self._sleep()
        try:
            res = self.session.post(
                f"{self.target_url}/api/social/like/{post_id}",
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code in (200, 201):
                self.print_action("Liked Post", f"Post ID: {post_id}")
            else:
                self.print_action("Like failed", f"HTTP {res.status_code}: {res.text[:60]}")
        except Exception as e:
            self.print_action("Like error", str(e))

    def comment_on_post(self, post_id: str, text: Optional[str] = None):
        """Add a comment on a post."""
        self._sleep()
        comment_text = text or random.choice(SAMPLE_COMMENTS)
        try:
            res = self.session.post(
                f"{self.target_url}/api/social/comment/{post_id}",
                json={"text": comment_text},
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code in (200, 201):
                self.print_action("Commented", f"\"{comment_text}\" on Post {post_id}")
            else:
                self.print_action("Comment failed", f"HTTP {res.status_code}: {res.text[:60]}")
        except Exception as e:
            self.print_action("Comment error", str(e))

    def follow_user(self, target_username: str):
        """Follow another creator."""
        if target_username == self.current_user:
            print("  [!] Cannot follow yourself.")
            return
        self._sleep()
        try:
            res = self.session.post(
                f"{self.target_url}/api/social/follow/{target_username}",
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code == 200:
                self.print_action("Followed", f"Started following @{target_username}")
            else:
                self.print_action("Follow failed", f"HTTP {res.status_code}: {res.text[:60]}")
        except Exception as e:
            self.print_action("Follow error", str(e))

    # -------------------------------------------------------------------------
    # 3. Discovery & Search
    # -------------------------------------------------------------------------
    def search_content(self, query: str, search_type: str = "all"):
        """Perform normal query search for users or hashtags."""
        self._sleep()
        try:
            res = self.session.get(
                f"{self.target_url}/api/search",
                params={"q": query, "type": search_type, "limit": 10},
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", {})
                users_found = len(results.get("users", []))
                posts_found = len(results.get("posts", []))
                tags_found = len(results.get("tags", []))
                self.print_action("Searched", f"Query '{query}' -> Users: {users_found}, Posts: {posts_found}, Tags: {tags_found}")
            else:
                self.print_action("Search error", f"HTTP {res.status_code}")
        except Exception as e:
            self.print_action("Search failed", str(e))

    # -------------------------------------------------------------------------
    # 4. Direct Messaging
    # -------------------------------------------------------------------------
    def send_message(self, recipient: str, text: Optional[str] = None):
        """Send a normal DM to a friend."""
        if recipient == self.current_user:
            print("  [!] Cannot message yourself.")
            return
        self._sleep()
        msg_text = text or random.choice(SAMPLE_DMS)
        try:
            res = self.session.post(
                f"{self.target_url}/api/messages",
                json={"recipient": recipient, "text": msg_text},
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code in (200, 201):
                self.print_action("Sent DM", f"To @{recipient}: \"{msg_text}\"")
            else:
                self.print_action("DM failed", f"HTTP {res.status_code}: {res.text[:60]}")
        except Exception as e:
            self.print_action("DM error", str(e))

    # -------------------------------------------------------------------------
    # 5. Content Creation (Post a Photo)
    # -------------------------------------------------------------------------
    def create_post(self, caption: str = "Enjoying a great coffee break today! ☕"):
        """Publish a new photo post."""
        self._sleep()
        img_id = random.randint(100, 999)
        payload = {
            "image_url": f"https://picsum.photos/id/{img_id}/800/800",
            "caption": caption
        }
        try:
            res = self.session.post(
                f"{self.target_url}/api/feed/posts",
                json=payload,
                headers=self._auth_headers(),
                timeout=5
            )
            if res.status_code in (200, 201):
                self.print_action("Published Post", f"Caption: \"{caption}\"")
            else:
                self.print_action("Create post failed", f"HTTP {res.status_code}: {res.text[:60]}")
        except Exception as e:
            self.print_action("Create post error", str(e))

    # -------------------------------------------------------------------------
    # Composite User Routine
    # -------------------------------------------------------------------------
    def run_daily_session(self, username: str = "sarah_dev"):
        """A realistic routine of an active user opening the app for a few minutes."""
        print(f"\n{'='*70}\n[*] Starting Organic Session for: @{username}\n{'='*70}")
        if not self.login(username=username):
            return

        self.view_stories()
        feed = self.browse_feed(limit=3)

        if feed:
            first_post = feed[0]
            pid = str(first_post.get("id") or "1")
            self.like_post(pid)
            self.comment_on_post(pid)

        tag = random.choice(POPULAR_TAGS)
        self.search_content(query=tag, search_type="tags")

        creators = [u["username"] for u in SAMPLE_USERS if u["username"] != username]
        if creators:
            chosen = random.choice(creators)
            self.follow_user(chosen)
            self.send_message(recipient=chosen)

        print(f"[OK] Completed session for @{username}\n")


# =============================================================================
# Interactive Menu UI
# =============================================================================
def prompt_choice(options: List[str], prompt_text: str = "Select an option") -> int:
    """Displays a numbered list and asks the user to pick one."""
    print()
    for idx, opt in enumerate(options, 1):
        print(f"  [{idx}] {opt}")
    print()
    while True:
        try:
            val = input(f"{prompt_text} (1-{len(options)}) [q to quit]: ").strip()
            if val.lower() in ("q", "quit", "exit"):
                print("Exiting...")
                sys.exit(0)
            choice = int(val)
            if 1 <= choice <= len(options):
                return choice
            print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def interactive_menu(sim: NormalUserSimulator):
    """Interactive CLI menu loop."""
    print("\n" + "="*65)
    print("   [+] INSTAGRAM APP - NORMAL USER ACTIVITY SIMULATOR")
    print(f"   Target URL: {sim.target_url}")
    print("="*65)

    # Step 1: Select User Account
    print("\n[Step 1] Select User Account to Login:")
    user_options = [f"@{u['username']} ({u['name']})" for u in SAMPLE_USERS] + ["Enter Custom Username"]
    user_choice = prompt_choice(user_options, "Select user")

    if user_choice <= len(SAMPLE_USERS):
        selected_user = SAMPLE_USERS[user_choice - 1]["username"]
        selected_pwd = SAMPLE_USERS[user_choice - 1]["password"]
    else:
        selected_user = input("Enter username: ").strip()
        selected_pwd = input("Enter password: ").strip()

    print(f"\n[*] Logging in as @{selected_user}...")
    if not sim.login(username=selected_user, password=selected_pwd):
        print("[!] Login failed. Please check if the target server is running.")
        sys.exit(1)

    # Step 2: Main Interactive Action Loop
    while True:
        print("\n" + "-"*65)
        print(f" Active User: @{sim.current_user}  |  Target: {sim.target_url}")
        print("-"*65)
        actions = [
            "Full Organic Session (Browse stories, feed, like, comment, search, DM)",
            "Browse Feed (View recent posts)",
            "Watch Active Stories",
            "Like a Post",
            "Comment on a Post",
            "Search (Hashtags or Creators)",
            "Follow a Creator",
            "Send a Direct Message",
            "Publish a New Photo Post",
            "Switch User",
            "Continuous Background Traffic Loop",
            "Exit"
        ]
        choice = prompt_choice(actions, "Choose action")

        if choice == 1:
            sim.run_daily_session(username=sim.current_user)

        elif choice == 2:
            sim.browse_feed()

        elif choice == 3:
            sim.view_stories()

        elif choice == 4:
            feed = sim.browse_feed(limit=5)
            pid = input("Enter Post ID to like (leave blank to like the first post): ").strip()
            if not pid and feed:
                pid = str(feed[0].get("id"))
            if pid:
                sim.like_post(pid)

        elif choice == 5:
            feed = sim.browse_feed(limit=5)
            pid = input("Enter Post ID to comment on (leave blank for first post): ").strip()
            if not pid and feed:
                pid = str(feed[0].get("id"))
            comment_text = input("Enter comment text (leave blank for random comment): ").strip() or None
            if pid:
                sim.comment_on_post(pid, text=comment_text)

        elif choice == 6:
            query = input("Enter search term (e.g. photography, travel, sarah): ").strip() or "photography"
            search_type = input("Type (all / users / posts / tags) [default: all]: ").strip() or "all"
            sim.search_content(query=query, search_type=search_type)

        elif choice == 7:
            creators = [u["username"] for u in SAMPLE_USERS if u["username"] != sim.current_user]
            print(f"Suggested creators: {', '.join(creators)}")
            target = input("Enter username to follow: ").strip() or (creators[0] if creators else "marcus_photo")
            sim.follow_user(target)

        elif choice == 8:
            creators = [u["username"] for u in SAMPLE_USERS if u["username"] != sim.current_user]
            recipient = input(f"Recipient username [suggested: {creators[0]}]: ").strip() or creators[0]
            msg = input("Message text (leave blank for random message): ").strip() or None
            sim.send_message(recipient=recipient, text=msg)

        elif choice == 9:
            caption = input("Enter post caption [default: 'Having a great day!']: ").strip() or "Having a great day!"
            sim.create_post(caption=caption)

        elif choice == 10:
            user_choice = prompt_choice(user_options, "Select user to switch to")
            if user_choice <= len(SAMPLE_USERS):
                u = SAMPLE_USERS[user_choice - 1]
                sim.login(u["username"], u["password"])
            else:
                u_name = input("Enter username: ").strip()
                p_word = input("Enter password: ").strip()
                sim.login(u_name, p_word)

        elif choice == 11:
            try:
                interval_str = input("Enter interval in seconds between user sessions [default: 5]: ").strip()
                interval = int(interval_str) if interval_str else 5
                print(f"[*] Starting background loop every {interval}s. Press Ctrl+C to stop.")
                while True:
                    user_obj = random.choice(SAMPLE_USERS)
                    sim.run_daily_session(username=user_obj["username"])
                    print(f"[*] Sleeping {interval}s... (Ctrl+C to return to menu)")
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n[!] Background loop stopped. Returning to menu.")

        elif choice == 12:
            print("Goodbye!")
            break


# =============================================================================
# CLI Main
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Normal User Traffic Simulator for Instagram App",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--target", default=DEFAULT_TARGET, help=f"Target Instagram App URL (default: {DEFAULT_TARGET})")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive selection menu")
    parser.add_argument("--user", default=None, help="Username to login as")
    parser.add_argument("--password", default="password123", help="User password")
    parser.add_argument(
        "--action",
        choices=["session", "feed", "stories", "search", "like", "comment", "follow", "dm", "post"],
        default=None,
        help="Run specific action directly without menu"
    )
    parser.add_argument("--query", default="photography", help="Search query (for --action search)")
    parser.add_argument("--recipient", default="marcus_photo", help="Recipient username (for --action dm)")
    parser.add_argument("--post-id", default=None, help="Post ID (for --action like or comment)")
    parser.add_argument("--target-user", default="marcus_photo", help="User to follow (for --action follow)")
    parser.add_argument("--text", default=None, help="Text message, comment, or caption")
    parser.add_argument("--delay", type=float, default=0.4, help="Pace delay between steps in seconds (default: 0.4)")
    parser.add_argument("--loop", action="store_true", help="Run indefinitely in a loop")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between sessions in loop mode (default: 10)")

    args = parser.parse_args()
    sim = NormalUserSimulator(target_url=args.target, delay=args.delay)

    # If no specific action/user or user passed -i, launch interactive menu!
    if args.interactive or (args.action is None and not args.loop and args.user is None):
        interactive_menu(sim)
        return

    # Non-interactive CLI flags mode
    target_user = args.user or "sarah_dev"

    if args.loop:
        print(f"[*] Starting loop against {args.target} (Interval: {args.interval}s)")
        try:
            while True:
                chosen = random.choice(SAMPLE_USERS)
                sim.run_daily_session(username=chosen["username"])
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
        return

    action = args.action or "session"
    if action == "session":
        sim.run_daily_session(username=target_user)
    else:
        if not sim.login(username=target_user, password=args.password):
            sys.exit(1)
        if action == "feed":
            sim.browse_feed()
        elif action == "stories":
            sim.view_stories()
        elif action == "search":
            sim.search_content(query=args.query)
        elif action == "like":
            pid = args.post_id or "1"
            sim.like_post(pid)
        elif action == "comment":
            pid = args.post_id or "1"
            sim.comment_on_post(pid, text=args.text)
        elif action == "follow":
            sim.follow_user(args.target_user)
        elif action == "dm":
            sim.send_message(recipient=args.recipient, text=args.text)
        elif action == "post":
            sim.create_post(caption=args.text or "Just posted from CLI!")


if __name__ == "__main__":
    main()
