// InstaTern - Frontend JavaScript & Social App Functionality

const state = {
  currentUser: null,
  posts: [],
  stories: [],
  conversations: [],
  notifications: [],
  activeConversationId: null,
  activeRecipient: null,
};

function getAuthHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
  await fetchCurrentUser();
  if (state.currentUser) {
    await Promise.all([
      fetchStories(),
      fetchFeed(),
      fetchSuggestions(),
      fetchNotifications(),
      fetchConversations(),
    ]);

    checkUrlParams();
  }
  setupEventListeners();
});

function checkUrlParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("open") === "dms") {
    openMessagesModal();
  }
  if (params.get("chat")) {
    startDirectMessageWith(params.get("chat"));
  }
  if (params.get("tag")) {
    const input = document.getElementById("searchInput");
    if (input) {
      input.value = "#" + params.get("tag");
      executeSearch(input.value);
    }
  }
}

function setupEventListeners() {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    let debounceTimeout = null;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        executeSearch(e.target.value);
      }, 250);
    });

    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target)) {
        const dropdown = document.getElementById("searchResultsDropdown");
        if (dropdown) dropdown.style.display = "none";
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

  // Create story form
  const createStoryForm = document.getElementById("createStoryForm");
  if (createStoryForm) {
    createStoryForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await submitNewStory();
    });
  }
}

// --- API Calls ---

async function fetchCurrentUser() {
  try {
    const res = await fetch("/api/auth/me", {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      state.currentUser = await res.json();
      renderCurrentUser();
    } else {
      window.location.href = "/login";
    }
  } catch (err) {
    console.error("Error fetching current user:", err);
    window.location.href = "/login";
  }
}

async function fetchStories() {
  try {
    const res = await fetch("/api/stories", {
      headers: { ...getAuthHeader() }
    });
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
    const res = await fetch("/api/feed", {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      state.posts = await res.json();
      renderFeed();
    }
  } catch (err) {
    console.error("Error fetching feed:", err);
  }
}

async function fetchSuggestions() {
  try {
    const res = await fetch("/api/auth/suggestions", {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      const suggestions = await res.json();
      renderSuggestions(suggestions);
    }
  } catch (err) {
    console.error("Error fetching suggestions:", err);
  }
}

async function fetchNotifications() {
  try {
    const res = await fetch("/api/notifications", {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      state.notifications = await res.json();
      const unreadCount = state.notifications.filter(n => !n.is_read).length;
      const badge = document.getElementById("notifBadge");
      if (badge) {
        if (unreadCount > 0) {
          badge.textContent = unreadCount;
          badge.style.display = "inline-flex";
        } else {
          badge.style.display = "none";
        }
      }
    }
  } catch (err) {}
}

async function toggleLike(postId, buttonEl) {
  try {
    const res = await fetch(`/api/posts/${postId}/like`, {
      method: "POST",
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      const data = await res.json();
      const countEl = document.getElementById(`likes-count-${postId}`);
      if (countEl) countEl.innerHTML = `<b>${data.likes_count} likes</b>`;

      const svg = buttonEl.querySelector("svg");
      if (data.liked) {
        buttonEl.classList.add("liked");
        if (svg) svg.setAttribute("fill", "#ef4444");
      } else {
        buttonEl.classList.remove("liked");
        if (svg) svg.setAttribute("fill", "none");
      }
    }
  } catch (err) {
    console.error("Error liking post:", err);
  }
}

async function toggleSave(postId, buttonEl) {
  try {
    const res = await fetch(`/api/posts/${postId}/save`, {
      method: "POST",
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      const data = await res.json();
      const svg = buttonEl.querySelector("svg");
      if (data.saved) {
        buttonEl.classList.add("saved");
        if (svg) svg.setAttribute("fill", "var(--text-main)");
      } else {
        buttonEl.classList.remove("saved");
        if (svg) svg.setAttribute("fill", "none");
      }
    }
  } catch (err) {
    console.error("Error saving post:", err);
  }
}

async function addComment(postId) {
  const inputEl = document.getElementById(`comment-input-${postId}`);
  if (!inputEl) return;
  const text = inputEl.value.trim();
  if (!text) return;

  try {
    const res = await fetch(`/api/posts/${postId}/comments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ text })
    });
    if (res.ok) {
      const comment = await res.json();
      inputEl.value = "";
      const commentsListEl = document.getElementById(`comments-list-${postId}`);
      if (commentsListEl) {
        const cDiv = document.createElement("div");
        cDiv.className = "comment-item";
        cDiv.innerHTML = `<b>${escapeHtml(comment.author.username)}</b> ${escapeHtml(comment.text)}`;
        commentsListEl.appendChild(cDiv);
      }
    }
  } catch (err) {
    console.error("Error commenting:", err);
  }
}

async function submitNewPost() {
  const imageUrl = document.getElementById("newPostImage").value.trim();
  const caption = document.getElementById("newPostCaption").value.trim();
  const tagsRaw = document.getElementById("newPostTags").value;
  const tags = tagsRaw.split(",").map(t => t.trim().replace(/^#/, "")).filter(Boolean);

  if (!imageUrl) return;

  try {
    const res = await fetch("/api/posts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ image_url: imageUrl, caption, tags })
    });
    if (res.ok) {
      closeCreatePostModal();
      document.getElementById("newPostCaption").value = "";
      await fetchFeed();
    }
  } catch (err) {
    console.error("Error creating post:", err);
  }
}

async function submitNewStory() {
  const mediaUrl = document.getElementById("newStoryMedia").value.trim();
  if (!mediaUrl) return;

  try {
    const res = await fetch("/api/stories", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ media_url: mediaUrl })
    });
    if (res.ok) {
      closeCreateStoryModal();
      await fetchStories();
    }
  } catch (err) {
    console.error("Error creating story:", err);
  }
}

// --- Multi-Facet Search ---
async function executeSearch(query) {
  const dropdown = document.getElementById("searchResultsDropdown");
  if (!dropdown) return;

  if (!query.trim()) {
    dropdown.style.display = "none";
    dropdown.innerHTML = "";
    return;
  }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`, {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      const data = await res.json();
      const users = data.results.users || [];
      const posts = data.results.posts || [];
      const tags = data.results.tags || [];

      if (users.length === 0 && posts.length === 0 && tags.length === 0) {
        dropdown.innerHTML = `<div class="search-empty">No results found for "${escapeHtml(query)}"</div>`;
      } else {
        let html = "";
        if (users.length > 0) {
          html += `<div class="search-heading">Accounts</div>`;
          users.forEach(u => {
            html += `
              <div class="search-item" onclick="window.location.href='/profile/${escapeHtml(u.username)}'">
                <img src="${escapeHtml(u.avatar_url)}" class="search-avatar" />
                <div class="search-info">
                  <div class="search-user">@${escapeHtml(u.username)} ${u.is_verified ? '<span class="verified-badge">✓</span>' : ''}</div>
                  <div class="search-sub">${escapeHtml(u.full_name)}</div>
                </div>
              </div>
            `;
          });
        }
        if (tags.length > 0) {
          html += `<div class="search-heading">Hashtags</div>`;
          tags.forEach(t => {
            html += `
              <div class="search-item" onclick="filterByTag('${escapeHtml(t.tag)}')">
                <div class="search-tag-icon">#</div>
                <div class="search-info">
                  <div class="search-user">#${escapeHtml(t.tag)}</div>
                  <div class="search-sub">${t.posts_count} posts</div>
                </div>
              </div>
            `;
          });
        }
        if (posts.length > 0) {
          html += `<div class="search-heading">Posts (${posts.length})</div>`;
          posts.forEach(p => {
            html += `
              <div class="search-item" onclick="scrollToPost('${p.id}')">
                <img src="${escapeHtml(p.image_url)}" class="search-avatar" style="border-radius:4px;" />
                <div class="search-info">
                  <div class="search-user">@${escapeHtml(p.author.username)}</div>
                  <div class="search-sub">${escapeHtml(p.caption.slice(0, 35))}...</div>
                </div>
              </div>
            `;
          });
        }
        dropdown.innerHTML = html;
      }
      dropdown.style.display = "block";
    }
  } catch (err) {
    console.error("Search error:", err);
  }
}

function filterByTag(tag) {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) searchInput.value = "#" + tag;
  const dropdown = document.getElementById("searchResultsDropdown");
  if (dropdown) dropdown.style.display = "none";

  fetch(`/api/search?q=${encodeURIComponent(tag)}&type=tags`, { headers: getAuthHeader() })
    .then(r => r.json())
    .then(d => {
      state.posts = d.results.posts || [];
      renderFeed();
    });
}

function scrollToPost(postId) {
  const dropdown = document.getElementById("searchResultsDropdown");
  if (dropdown) dropdown.style.display = "none";
  const el = document.getElementById(`post-${postId}`);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.style.border = "2px solid #38bdf8";
    setTimeout(() => { el.style.border = "1px solid var(--border-color)"; }, 2000);
  }
}

// --- Direct Messages ---
async function openMessagesModal() {
  const modal = document.getElementById("messagesModal");
  if (modal) modal.style.display = "flex";
  await fetchConversations();
}

function closeMessagesModal() {
  const modal = document.getElementById("messagesModal");
  if (modal) modal.style.display = "none";
}

async function fetchConversations() {
  try {
    const res = await fetch("/api/messages", {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      state.conversations = await res.json();
      renderConversationsList();
      if (state.conversations.length > 0 && !state.activeConversationId) {
        selectConversation(state.conversations[0].id);
      }
    }
  } catch (err) {
    console.error("Error fetching conversations:", err);
  }
}

function renderConversationsList() {
  const listEl = document.getElementById("conversationsList");
  if (!listEl) return;

  if (state.conversations.length === 0) {
    listEl.innerHTML = `<div style="font-size:12px; color:var(--text-dim); text-align:center; padding-top:20px;">No messages yet.</div>`;
    return;
  }

  listEl.innerHTML = state.conversations.map(c => {
    const otherUser = c.participants.find(p => p !== state.currentUser?.username) || c.participants[0];
    const isSelected = c.id === state.activeConversationId;
    return `
      <div class="conv-item ${isSelected ? 'active' : ''}" onclick="selectConversation('${c.id}')">
        <div style="font-weight:600; font-size:13px; color:var(--text-main);">@${escapeHtml(otherUser)}</div>
        <div style="font-size:11px; color:var(--text-muted); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${escapeHtml(c.last_message || 'Active conversation')}</div>
      </div>
    `;
  }).join("");
}

function selectConversation(convId) {
  state.activeConversationId = convId;
  renderConversationsList();
  const conv = state.conversations.find(c => c.id === convId);
  if (!conv) return;

  const otherUser = conv.participants.find(p => p !== state.currentUser?.username) || conv.participants[0];
  state.activeRecipient = otherUser;

  const headerEl = document.getElementById("threadHeader");
  if (headerEl) {
    headerEl.innerHTML = `<span>Direct Chat with <a href="/profile/${escapeHtml(otherUser)}" style="color:var(--blue-link); text-decoration:none;">@${escapeHtml(otherUser)}</a></span>`;
  }

  renderThreadMessages(conv.messages || []);
}

function renderThreadMessages(messages) {
  const contentEl = document.getElementById("messagesContent");
  if (!contentEl) return;

  if (messages.length === 0) {
    contentEl.innerHTML = `<div style="color:var(--text-dim); font-size:12px; text-align:center; margin-top:20px;">No messages yet. Say hello!</div>`;
    return;
  }

  contentEl.innerHTML = messages.map(m => {
    const isMine = m.sender === state.currentUser?.username;
    return `
      <div class="dm-bubble ${isMine ? 'mine' : 'theirs'}">
        <div class="dm-text">${escapeHtml(m.text)}</div>
        <div class="dm-time">${escapeHtml(m.timestamp)}</div>
      </div>
    `;
  }).join("");

  contentEl.scrollTop = contentEl.scrollHeight;
}

async function sendCurrentDM() {
  const inputEl = document.getElementById("dmInput");
  if (!inputEl) return;
  const text = inputEl.value.trim();
  if (!text || !state.activeRecipient) return;

  try {
    const res = await fetch("/api/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ recipient: state.activeRecipient, text })
    });
    if (res.ok) {
      inputEl.value = "";
      await fetchConversations();
      if (state.activeConversationId) {
        selectConversation(state.activeConversationId);
      }
    }
  } catch (err) {
    console.error("Error sending DM:", err);
  }
}

function startDirectMessageWith(username) {
  openMessagesModal();
  state.activeRecipient = username;
  const headerEl = document.getElementById("threadHeader");
  if (headerEl) {
    headerEl.innerHTML = `<span>Direct Chat with <a href="/profile/${escapeHtml(username)}" style="color:var(--blue-link); text-decoration:none;">@${escapeHtml(username)}</a></span>`;
  }
  const contentEl = document.getElementById("messagesContent");
  if (contentEl) {
    contentEl.innerHTML = `<div style="color:var(--text-dim); font-size:12px; text-align:center; margin-top:20px;">Send a message to start chatting with @${escapeHtml(username)}</div>`;
  }
}

// Notifications Dropdown
function toggleNotifications() {
  const dropdown = document.getElementById("notifDropdown");
  if (!dropdown) return;

  const isVisible = dropdown.style.display === "block";
  if (isVisible) {
    dropdown.style.display = "none";
  } else {
    dropdown.innerHTML = `
      <div class="notif-header">
        <span>Notifications</span>
        <button class="notif-mark-btn" onclick="markAllNotifsRead()">Mark all as read</button>
      </div>
      <div class="notif-list">
        ${state.notifications.length === 0 ? '<div class="notif-empty">No notifications yet</div>' : ''}
        ${state.notifications.map(n => `
          <div class="notif-item ${n.is_read ? '' : 'unread'}">
            <img src="${escapeHtml(n.sender.avatar_url)}" class="notif-avatar" />
            <div class="notif-content">
              <b>@${escapeHtml(n.sender.username)}</b> ${escapeHtml(n.text)}
              <div class="notif-time">${escapeHtml(n.created_at)}</div>
            </div>
          </div>
        `).join("")}
      </div>
    `;
    dropdown.style.display = "block";
  }
}

async function markAllNotifsRead() {
  try {
    await fetch("/api/notifications/read", { method: "POST", headers: getAuthHeader() });
    state.notifications.forEach(n => n.is_read = true);
    const badge = document.getElementById("notifBadge");
    if (badge) badge.style.display = "none";
    toggleNotifications();
  } catch (err) {}
}

// Render User Pill & Sidebar
function renderCurrentUser() {
  const user = state.currentUser;
  if (!user) return;

  const userPill = document.getElementById("userPill");
  if (userPill) {
    userPill.innerHTML = `
      <img src="${escapeHtml(user.avatar_url)}" class="pill-avatar" />
      <span onclick="window.location.href='/profile/${escapeHtml(user.username)}'">${escapeHtml(user.username)}</span>
      <button class="logout-btn" onclick="handleLogout(event)" title="Log out">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
      </button>
    `;
  }

  const sidebarProfile = document.getElementById("sidebarUserProfile");
  if (sidebarProfile) {
    sidebarProfile.innerHTML = `
      <div class="sidebar-user-card" onclick="window.location.href='/profile/${escapeHtml(user.username)}'" style="cursor:pointer;">
        <img src="${escapeHtml(user.avatar_url)}" class="profile-big-avatar" />
        <div class="profile-meta">
          <div class="profile-username">
            ${escapeHtml(user.username)}
            ${user.is_verified ? '<span class="verified-badge">✓</span>' : ''}
          </div>
          <div class="profile-name">${escapeHtml(user.full_name)}</div>
          <div class="profile-bio">${escapeHtml(user.bio || '')}</div>
          <div class="profile-counts">
            <span><b>${user.followers_count}</b> followers</span>
            <span><b>${user.following_count}</b> following</span>
          </div>
        </div>
      </div>
    `;
  }
}

function renderSuggestions(creators) {
  const listEl = document.getElementById("suggestionsList");
  if (!listEl) return;

  if (creators.length === 0) {
    listEl.innerHTML = `<div style="font-size:12px; color:var(--text-dim);">No suggestions right now.</div>`;
    return;
  }

  listEl.innerHTML = creators.map(c => `
    <div class="suggestion-item">
      <div class="sugg-left" onclick="window.location.href='/profile/${escapeHtml(c.username)}'">
        <img src="${escapeHtml(c.avatar_url)}" class="sugg-avatar" />
        <div class="sugg-info">
          <div class="sugg-user">@${escapeHtml(c.username)} ${c.is_verified ? '✓' : ''}</div>
          <div class="sugg-name">${escapeHtml(c.full_name)}</div>
        </div>
      </div>
      <button class="sugg-follow-btn" onclick="followFromSidebar('${escapeHtml(c.username)}', this)">Follow</button>
    </div>
  `).join("");
}

async function followFromSidebar(username, btn) {
  try {
    const res = await fetch(`/api/auth/users/${username}/follow`, { method: "POST", headers: getAuthHeader() });
    if (res.ok) {
      btn.textContent = "Following";
      btn.disabled = true;
      btn.style.opacity = "0.6";
    }
  } catch (err) {}
}

function renderStories() {
  const container = document.getElementById("storiesContainer");
  if (!container) return;

  let html = `
    <div class="story-item create-story-circle" onclick="openCreateStoryModal()">
      <div class="story-ring add-ring">+</div>
      <span class="story-user">Your Story</span>
    </div>
  `;

  state.stories.forEach(s => {
    html += `
      <div class="story-item" onclick="viewStory('${escapeHtml(s.media_url)}')">
        <div class="story-ring">
          <img src="${escapeHtml(s.author.avatar_url)}" />
        </div>
        <span class="story-user">${escapeHtml(s.author.username)}</span>
      </div>
    `;
  });

  container.innerHTML = html;
}

function viewStory(url) {
  window.open(url, "_blank");
}

function renderFeed() {
  const container = document.getElementById("feedContainer");
  if (!container) return;

  if (state.posts.length === 0) {
    container.innerHTML = `<div class="empty-feed">No posts yet. Be the first to share a moment!</div>`;
    return;
  }

  container.innerHTML = state.posts.map(p => {
    const commentsHtml = (p.comments || []).map(c => `
      <div class="comment-item">
        <b onclick="window.location.href='/profile/${escapeHtml(c.author.username)}'" style="cursor:pointer;">${escapeHtml(c.author.username)}</b> ${escapeHtml(c.text)}
      </div>
    `).join("");

    const tagsHtml = (p.tags || []).map(t => `<span class="post-tag" onclick="filterByTag('${escapeHtml(t)}')">#${escapeHtml(t)}</span>`).join(" ");

    return `
      <article class="post-card" id="post-${p.id}">
        <div class="post-header">
          <div class="post-author-info" onclick="window.location.href='/profile/${escapeHtml(p.author.username)}'" style="cursor:pointer;">
            <img src="${escapeHtml(p.author.avatar_url)}" class="author-avatar" />
            <div>
              <div class="author-name">
                ${escapeHtml(p.author.username)}
                ${p.author.is_verified ? '<span class="verified-badge">✓</span>' : ''}
              </div>
              <div class="post-time">${escapeHtml(p.created_at)}</div>
            </div>
          </div>
        </div>

        <div class="post-image-container">
          <img src="${escapeHtml(p.image_url)}" alt="Post image" loading="lazy" />
        </div>

        <div class="post-body">
          <div class="post-actions">
            <div style="display:flex; gap:16px;">
              <button class="action-btn ${p.is_liked ? 'liked' : ''}" onclick="toggleLike('${p.id}', this)" title="Like">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="${p.is_liked ? '#ef4444' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
              </button>
              <button class="action-btn" onclick="document.getElementById('comment-input-${p.id}').focus()" title="Comment">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
              </button>
              <button class="action-btn" onclick="startDirectMessageWith('${escapeHtml(p.author.username)}')" title="Direct Message">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </div>
            <button class="action-btn ${p.is_saved ? 'saved' : ''}" onclick="toggleSave('${p.id}', this)" title="Save to collection">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="${p.is_saved ? 'var(--text-main)' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
            </button>
          </div>

          <div class="likes-count" id="likes-count-${p.id}"><b>${p.likes_count} likes</b></div>

          <div class="post-caption">
            <b onclick="window.location.href='/profile/${escapeHtml(p.author.username)}'" style="cursor:pointer;">${escapeHtml(p.author.username)}</b> ${escapeHtml(p.caption)}
          </div>

          ${tagsHtml ? `<div class="post-tags-container">${tagsHtml}</div>` : ''}

          <div class="comments-section" id="comments-list-${p.id}">
            ${commentsHtml}
          </div>

          <div class="add-comment-box">
            <input type="text" id="comment-input-${p.id}" placeholder="Add a comment..." onkeydown="if(event.key==='Enter') addComment('${p.id}')" />
            <button class="btn-comment" onclick="addComment('${p.id}')">Post</button>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

async function handleLogout(e) {
  if (e) e.stopPropagation();
  try {
    await fetch("/api/auth/logout", { method: "POST", headers: { ...getAuthHeader() } });
  } catch (err) {}
  localStorage.removeItem("access_token");
  window.location.href = "/login";
}

// Modal open/close helpers
function openCreatePostModal() {
  document.getElementById("createPostModal").style.display = "flex";
}
function closeCreatePostModal() {
  document.getElementById("createPostModal").style.display = "none";
}
function openCreateStoryModal() {
  document.getElementById("createStoryModal").style.display = "flex";
}
function closeCreateStoryModal() {
  document.getElementById("createStoryModal").style.display = "none";
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
