// InstaTern - Frontend JavaScript

const state = {
  currentUser: null,
  posts: [],
  stories: [],
  conversations: [],
  activeConversationId: null,
  activeRecipient: null,
};

function getAuthHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  initApp();
  setupEventListeners();
});

async function initApp() {
  await fetchCurrentUser();
  if (state.currentUser) {
    await Promise.all([
      fetchStories(),
      fetchFeed(),
      fetchSuggestions(),
    ]);
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
      }, 300);
    });
    // Close dropdown on outside click
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
      // Unauthorized -> redirect to login
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
    const res = await fetch("/api/search?q=", {
      headers: { ...getAuthHeader() }
    });
    // We can also fetch search results for random creators
  } catch (err) {
    console.error(err);
  }
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
      if (countEl) countEl.textContent = `${data.likes_count} likes`;

      if (data.liked) {
        buttonEl.classList.add("liked");
      } else {
        buttonEl.classList.remove("liked");
      }
    }
  } catch (err) {
    console.error("Error liking post:", err);
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
  const tags = tagsRaw.split(",").map(t => t.trim()).filter(Boolean);

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

async function executeSearch(query) {
  const dropdown = document.getElementById("searchResultsDropdown");
  if (!dropdown) return;

  if (!query.trim()) {
    dropdown.style.display = "none";
    dropdown.innerHTML = "";
    return;
  }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
      headers: { ...getAuthHeader() }
    });
    if (res.ok) {
      const data = await res.json();
      const users = data.results.users || [];
      const posts = data.results.posts || [];

      if (users.length === 0 && posts.length === 0) {
        dropdown.innerHTML = `<div class="search-empty">No results found for "${escapeHtml(query)}"</div>`;
      } else {
        let html = "";
        if (users.length > 0) {
          html += `<div class="search-heading">Accounts</div>`;
          users.forEach(u => {
            html += `
              <div class="search-item" onclick="startDirectMessageWith('${escapeHtml(u.username)}')">
                <img src="${escapeHtml(u.avatar_url)}" class="search-avatar" />
                <div class="search-info">
                  <div class="search-user">${escapeHtml(u.username)}</div>
                  <div class="search-sub">${escapeHtml(u.full_name)}</div>
                </div>
              </div>
            `;
          });
        }
        if (posts.length > 0) {
          html += `<div class="search-heading">Posts (${posts.length})</div>`;
          posts.forEach(p => {
            html += `
              <div class="search-item" onclick="document.getElementById('searchInput').value=''; document.getElementById('searchResultsDropdown').style.display='none';">
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
    headerEl.innerHTML = `<span>Direct Chat with @${escapeHtml(otherUser)}</span>`;
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
  // Close search dropdown
  const dropdown = document.getElementById("searchResultsDropdown");
  if (dropdown) dropdown.style.display = "none";

  openMessagesModal();
  state.activeRecipient = username;
  const headerEl = document.getElementById("threadHeader");
  if (headerEl) {
    headerEl.innerHTML = `<span>Direct Chat with @${escapeHtml(username)}</span>`;
  }
  const contentEl = document.getElementById("messagesContent");
  if (contentEl) {
    contentEl.innerHTML = `<div style="color:var(--text-dim); font-size:12px; text-align:center; margin-top:20px;">Send a message to start chatting with @${escapeHtml(username)}</div>`;
  }
}

// --- Render UI ---

function renderCurrentUser() {
  const user = state.currentUser;
  if (!user) return;

  const userPill = document.getElementById("userPill");
  if (userPill) {
    userPill.innerHTML = `
      <img src="${escapeHtml(user.avatar_url)}" class="pill-avatar" />
      <span>${escapeHtml(user.username)}</span>
      <button class="logout-btn" onclick="handleLogout(event)" title="Log out">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
      </button>
    `;
  }

  const sidebarProfile = document.getElementById("sidebarUserProfile");
  if (sidebarProfile) {
    sidebarProfile.innerHTML = `
      <div class="sidebar-user-card">
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
        <b>${escapeHtml(c.author.username)}</b> ${escapeHtml(c.text)}
      </div>
    `).join("");

    const tagsHtml = (p.tags || []).map(t => `<span class="post-tag">#${escapeHtml(t)}</span>`).join(" ");

    return `
      <article class="post-card" id="post-${p.id}">
        <div class="post-header">
          <div class="post-author-info">
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
            <button class="action-btn ${p.is_liked ? 'liked' : ''}" onclick="toggleLike('${p.id}', this)" title="Like">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="${p.is_liked ? 'var(--insta-gradient)' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
            </button>
            <button class="action-btn" onclick="document.getElementById('comment-input-${p.id}').focus()" title="Comment">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
            </button>
            <button class="action-btn" onclick="startDirectMessageWith('${escapeHtml(p.author.username)}')" title="Direct Message">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </div>

          <div class="likes-count" id="likes-count-${p.id}"><b>${p.likes_count} likes</b></div>

          <div class="post-caption">
            <b>${escapeHtml(p.author.username)}</b> ${escapeHtml(p.caption)}
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
