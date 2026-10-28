// InstaTern - Frontend JavaScript & Cyber Engine Live Telemetry

const state = {
  currentUser: null,
  posts: [],
  stories: [],
  telemetryEvents: [],
  connected: false,
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  initApp();
  setupEventListeners();
  startTelemetryPolling();
});

async function initApp() {
  await Promise.all([
    fetchCurrentUser(),
    fetchStories(),
    fetchFeed(),
    checkCyberEngineStatus(),
    fetchRecentTelemetry(),
  ]);
}

function setupEventListeners() {
  // Search box listener (triggers normal or SQLi search)
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        executeSearch(searchInput.value);
      }
    });
  }

  // Create post form
  const createPostForm = document.getElementById("createPostForm");
  if (createPostForm) {
    createPostForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await submitNewPost();
    });
  }
}

// --- API Calls ---

async function fetchCurrentUser() {
  try {
    const res = await fetch("/api/auth/me");
    if (res.ok) {
      state.currentUser = await res.json();
      renderCurrentUser();
    }
  } catch (err) {
    console.error("Error fetching current user:", err);
  }
}

async function fetchStories() {
  try {
    const res = await fetch("/api/stories");
    if (res.ok) {
      state.stories = await res.json();
      renderStories();
    }
  } catch (err) {
    console.error("Error fetching stories:", err);
  }
}

async function fetchFeed() {
  try {
    const res = await fetch("/api/feed");
    if (res.ok) {
      state.posts = await res.json();
      renderFeed();
    }
  } catch (err) {
    console.error("Error fetching feed:", err);
  }
}

async function checkCyberEngineStatus() {
  try {
    const res = await fetch("/api/attacks/status");
    if (res.ok) {
      const data = await res.json();
      const isOnline = data.connection && data.connection.connected;
      state.connected = isOnline;

      const badge = document.getElementById("ceStatusBadge");
      const dot = document.getElementById("ceStatusDot");
      const text = document.getElementById("ceStatusText");

      if (badge && text) {
        if (isOnline) {
          text.innerText = "STREAMING (200 OK)";
          badge.style.color = "var(--accent-lime)";
          badge.style.borderColor = "rgba(183, 243, 107, 0.4)";
          if (dot) dot.style.backgroundColor = "var(--accent-lime)";
        } else {
          text.innerText = "OFFLINE / BUFFERED";
          badge.style.color = "var(--warning-amber)";
          badge.style.borderColor = "rgba(245, 158, 11, 0.4)";
          if (dot) dot.style.backgroundColor = "var(--warning-amber)";
        }
      }
    }
  } catch (err) {
    console.warn("Cyber Engine status check failed:", err);
  }
}

async function fetchRecentTelemetry() {
  try {
    const res = await fetch("/api/attacks/recent-telemetry");
    if (res.ok) {
      const events = await res.json();
      renderTelemetryTicker(events);
    }
  } catch (err) {
    console.error("Error polling telemetry:", err);
  }
}

function startTelemetryPolling() {
  setInterval(() => {
    fetchRecentTelemetry();
    checkCyberEngineStatus();
  }, 2500);
}

// --- Render Functions ---

function renderCurrentUser() {
  const u = state.currentUser;
  if (!u) return;

  const userPill = document.getElementById("userPill");
  if (userPill) {
    userPill.innerHTML = `
      <img src="${u.avatar_url}" alt="${u.username}" />
      <span>@${u.username}</span>
    `;
  }

  const sidebarUser = document.getElementById("sidebarUserProfile");
  if (sidebarUser) {
    sidebarUser.innerHTML = `
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:12px;">
          <img src="${u.avatar_url}" style="width:48px; height:48px; border-radius:50%; object-fit:cover;" />
          <div>
            <strong>${u.username}</strong>
            <div style="font-size:12px; color:var(--text-muted);">${u.full_name}</div>
          </div>
        </div>
        <button class="nav-icon-btn" onclick="openSwitchUserModal()" style="font-size:12px; color:var(--accent-lime);">Switch</button>
      </div>
    `;
  }
}

function renderStories() {
  const container = document.getElementById("storiesContainer");
  if (!container) return;

  container.innerHTML = state.stories
    .map(
      (s) => `
    <div class="story-item" onclick="viewStory('${s.id}')">
      <div class="story-ring">
        <img src="${s.author.avatar_url}" alt="${s.author.username}" />
      </div>
      <span class="story-name">${s.author.username}</span>
    </div>
  `
    )
    .join("");
}

function renderFeed() {
  const container = document.getElementById("feedContainer");
  if (!container) return;

  if (state.posts.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-dim);">No posts yet in feed.</div>`;
    return;
  }

  container.innerHTML = state.posts
    .map(
      (post) => `
    <article class="post-card" id="post-${post.id}">
      <div class="post-header">
        <div class="post-author">
          <img src="${post.author.avatar_url}" alt="${post.author.username}" />
          <div class="author-info">
            <strong>${post.author.username} ${post.author.is_verified ? "✓" : ""}</strong>
            <span>${post.created_at}</span>
          </div>
        </div>
        <button class="nav-icon-btn" title="Options">•••</button>
      </div>

      <div class="post-image-container">
        <img src="${post.image_url}" alt="Post Image" loading="lazy" />
      </div>

      <div class="post-actions">
        <div class="actions-left">
          <button class="action-btn ${post.is_liked ? "liked" : ""}" onclick="toggleLike('${post.id}')" title="Like">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="${post.is_liked ? "currentColor" : "none"}" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
          </button>
          <button class="action-btn" onclick="focusCommentInput('${post.id}')" title="Comment">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          </button>
          <button class="action-btn" onclick="sharePost('${post.id}')" title="Share">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </div>
        <button class="action-btn" title="Bookmark">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
        </button>
      </div>

      <div class="post-content">
        <div class="likes-stat">${post.likes_count.toLocaleString()} likes</div>
        <div class="caption-text">
          <strong>${post.author.username}</strong> ${escapeHtml(post.caption)}
        </div>
        ${
          post.tags && post.tags.length > 0
            ? `<div class="caption-tags">${post.tags.map((t) => "#" + t).join(" ")}</div>`
            : ""
        }

        <div class="comments-list" id="comments-${post.id}">
          ${(post.comments || [])
            .map(
              (c) => `
            <div class="comment-row">
              <strong>${c.author.username}</strong> <span>${escapeHtml(c.text)}</span>
            </div>
          `
            )
            .join("")}
        </div>
        <div class="post-time">${post.created_at}</div>
      </div>

      <div class="add-comment-box">
        <input type="text" id="comment-input-${post.id}" placeholder="Add a comment..." onkeydown="if(event.key==='Enter') submitComment('${post.id}')" />
        <button onclick="submitComment('${post.id}')">Post</button>
      </div>
    </article>
  `
    )
    .join("");
}

function renderTelemetryTicker(events) {
  const ticker = document.getElementById("telemetryTicker");
  if (!ticker) return;

  if (!events || events.length === 0) {
    ticker.innerHTML = `<div style="color:var(--text-dim); text-align:center; padding-top:40px;">No telemetry events recorded yet.</div>`;
    return;
  }

  ticker.innerHTML = events
    .slice(0, 30)
    .map((ev) => {
      let cls = "accepted";
      if (ev.severity === "warning") cls = "warning";
      if (ev.severity === "critical") cls = "critical";

      const timeStr = (ev.timestamp || "").split("T")[1]?.slice(0, 8) || "now";
      const latencyStr = ev.delivery_latency_ms ? `${ev.delivery_latency_ms}ms` : "";

      return `
      <div class="ticker-item ${cls}">
        <div class="ticker-header">
          <span class="ticker-type">${ev.event_type}</span>
          <span>${timeStr} (${latencyStr})</span>
        </div>
        <div class="ticker-desc" title="${JSON.stringify(ev.attributes || {})}">
          ${ev.target_resource ? "target: " + ev.target_resource : ""} ${ev.trace_id ? "[" + ev.trace_id.slice(0, 14) + "...]" : ""}
        </div>
      </div>
    `;
    })
    .join("");
}

// --- Interactive Social Actions ---

async function toggleLike(postId) {
  try {
    const res = await fetch(`/api/posts/${postId}/like`, { method: "POST" });
    if (res.ok) {
      const updated = await res.json();
      const idx = state.posts.findIndex((p) => p.id === postId);
      if (idx !== -1) {
        state.posts[idx] = updated;
        renderFeed();
      }
      fetchRecentTelemetry();
    }
  } catch (err) {
    console.error("Like error:", err);
  }
}

async function submitComment(postId) {
  const input = document.getElementById(`comment-input-${postId}`);
  if (!input || !input.value.trim()) return;

  const text = input.value.trim();
  input.value = "";

  try {
    const res = await fetch(`/api/posts/${postId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (res.ok) {
      await fetchFeed();
      fetchRecentTelemetry();
    }
  } catch (err) {
    console.error("Comment submission error:", err);
  }
}

function focusCommentInput(postId) {
  const input = document.getElementById(`comment-input-${postId}`);
  if (input) input.focus();
}

function sharePost(postId) {
  navigator.clipboard?.writeText(window.location.origin + `#${postId}`);
  alert(`Post link copied to clipboard: ${postId}`);
}

// --- Search & SQL Injection ---

async function executeSearch(query) {
  if (!query) return;

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (data.attack_detected_by_app) {
      alert(
        `🚨 SIMULATED ATTACK DETECTED!\n\n${data.warning}\n\nLeaked records: ${data.results.leaked_user_rows}\nCheck the Cyber Engine Console for the security finding!`
      );
    } else {
      console.log("Search results:", data.results);
    }
    fetchRecentTelemetry();
  } catch (err) {
    console.error("Search error:", err);
  }
}

// --- Attack Simulation Triggers ---

async function triggerBruteForceAttack() {
  const btn = document.getElementById("btnBruteForce");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch("/api/attacks/brute-force", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_username: "charlie_vip", attempts: 6 }),
    });
    const data = await res.json();
    alert(`💥 ${data.message}`);
    await fetchRecentTelemetry();
  } catch (err) {
    alert("Attack simulation failed: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function triggerAptExfilAttack() {
  const btn = document.getElementById("btnAptExfil");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch("/api/attacks/cross-service-exfil", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_table: "users", rows_affected: 1200 }),
    });
    const data = await res.json();
    alert(`🚨 ${data.message}`);
    await fetchRecentTelemetry();
  } catch (err) {
    alert("Attack simulation failed: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function triggerSearchSqli() {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) searchInput.value = "' OR 1=1; SELECT * FROM users --";
  await executeSearch("' OR 1=1; SELECT * FROM users --");
}

async function triggerBenignTraffic() {
  try {
    const res = await fetch("/api/attacks/benign-traffic", { method: "POST" });
    const data = await res.json();
    alert(`✅ Emitted ${data.events_fired} benign user telemetry events to Cyber Engine.`);
    await fetchRecentTelemetry();
  } catch (err) {
    alert("Benign simulation failed: " + err.message);
  }
}

// --- Modals & Switch User ---

function openCreatePostModal() {
  const modal = document.getElementById("createPostModal");
  if (modal) modal.classList.add("active");
}

function closeCreatePostModal() {
  const modal = document.getElementById("createPostModal");
  if (modal) modal.classList.remove("active");
}

async function submitNewPost() {
  const caption = document.getElementById("newPostCaption").value;
  const imageUrl = document.getElementById("newPostImage").value;
  const tagsStr = document.getElementById("newPostTags").value;

  const tags = tagsStr
    .split(",")
    .map((t) => t.trim().replace(/^#/, ""))
    .filter(Boolean);

  try {
    const res = await fetch("/api/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ caption, image_url: imageUrl, tags }),
    });

    if (res.ok) {
      closeCreatePostModal();
      document.getElementById("newPostCaption").value = "";
      document.getElementById("newPostImage").value = "";
      document.getElementById("newPostTags").value = "";
      await fetchFeed();
      fetchRecentTelemetry();
    }
  } catch (err) {
    alert("Failed to create post: " + err.message);
  }
}

function openSwitchUserModal() {
  const modal = document.getElementById("switchUserModal");
  if (modal) modal.classList.add("active");
  loadUsersList();
}

function closeSwitchUserModal() {
  const modal = document.getElementById("switchUserModal");
  if (modal) modal.classList.remove("active");
}

async function loadUsersList() {
  const listContainer = document.getElementById("switchUserList");
  if (!listContainer) return;

  try {
    const res = await fetch("/api/auth/users");
    if (res.ok) {
      const users = await res.json();
      listContainer.innerHTML = users
        .map(
          (u) => `
        <div style="display:flex; align-items:center; justify-content:space-between; padding:8px; border-radius:8px; background:var(--panel-bg); margin-bottom:8px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <img src="${u.avatar_url}" style="width:36px; height:36px; border-radius:50%;" />
            <div>
              <strong>${u.username}</strong>
              <div style="font-size:11px; color:var(--text-muted);">${u.full_name}</div>
            </div>
          </div>
          <button class="btn-primary" style="padding:4px 10px; font-size:11px;" onclick="selectUser('${u.username}')">Select</button>
        </div>
      `
        )
        .join("");
    }
  } catch (err) {
    console.error("Error loading users:", err);
  }
}

async function selectUser(username) {
  try {
    const res = await fetch(`/api/auth/switch-user/${username}`, { method: "POST" });
    if (res.ok) {
      closeSwitchUserModal();
      await fetchCurrentUser();
      fetchRecentTelemetry();
    }
  } catch (err) {
    console.error("Switch user error:", err);
  }
}

function viewStory(storyId) {
  const story = state.stories.find((s) => s.id === storyId);
  if (!story) return;
  alert(`Viewing Story from @${story.author.username} (${story.created_at})`);
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

