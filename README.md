# InstaTern — Modern Social Media Web Application

InstaTern is a full-featured Instagram clone built with **FastAPI**, **SQLite**, **Jinja2**, and vanilla CSS/JavaScript.

---

## 🚀 Features

- **Home Feed & Stories**: Chronological feed with likes, bookmarking/saved posts, comments, and 24-hour stories.
- **Rich Profiles**: User bios, avatar management, follower and following counts, post galleries, and engagement analytics.
- **Social Graph**: Real-time follow/unfollow interactions and dynamic creator recommendations.
- **Direct Messaging**: 1-on-1 private messaging threads with real-time UI updates.
- **Multi-Facet Search**: Search creators, captions, and hashtags with recent/popular sorting.
- **Authentication**: Secure registration, password hashing (salted SHA-256), and JWT session management.

---

## 🛠️ Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   python run.py
   ```
   Open **http://localhost:8000** in your browser.

3. **Run tests**:
   ```bash
   python -m pytest -v
   ```

---

## 🐳 Docker

```bash
docker compose up --build
```
