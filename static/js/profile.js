// Profile Page JavaScript

const profileState = {
  currentUser: null,
  profile: null,
  activeTab: "posts",
  showAnalytics: false,
};

function getAuthHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

document.addEventListener("DOMContentLoaded", async () => {
  await fetchCurrentUser();
  await loadProfile();
  setupSearch();
});

async function fetchCurrentUser() {
  try {
    const res = await fetch("/api/auth/me", { headers: getAuthHeader() });
    if (res.ok) {
      profileState.currentUser = await res.json();
      renderUserPill();
    }
  } catch (err) {}
}

function renderUserPill() {
  const pill = document.getElementById("userPill");
  if (!pill) return;
  const user = profileState.currentUser;
  if (user) {
    pill.innerHTML = `
      <img src="${escapeHtml(user.avatar_url)}" class="pill-avatar" />
      <span onclick="window.location.href='/profile/${escapeHtml(user.username)}'">${escapeHtml(user.username)}</span>
      <button class="logout-btn" onclick="handleLogout(event)" title="Log out">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
      </button>
    `;
  } else {
    pill.innerHTML = `<a href="/login" style="color:var(--text-main); text-decoration:none;">Log In</a>`;
  }
}

async function loadProfile() {
  try {
    const res = await fetch(`/api/auth/users/${TARGET_USER}`, { headers: getAuthHeader() });
    if (!res.ok) {
      document.getElementById("profileHeaderCard").innerHTML = `<div class="profile-error">User @${escapeHtml(TARGET_USER)} not found.</div>`;
      return;
    }

    profileState.profile = await res.json();
    renderProfileHeader();
    renderPostsGrid();

    // Show saved tab if viewing own profile
    if (profileState.currentUser && profileState.currentUser.username === profileState.profile.username) {
      const savedTab = document.getElementById("tabSaved");
      if (savedTab) savedTab.style.display = "inline-flex";
    }
  } catch (err) {
    console.error("Error loading profile:", err);
  }
}

function renderProfileHeader() {
  const p = profileState.profile;
  const isMe = profileState.currentUser && profileState.currentUser.username === p.username;
  const headerCard = document.getElementById("profileHeaderCard");

  let actionButtonsHtml = "";
  if (isMe) {
    actionButtonsHtml = `
      <button class="btn-profile-edit" onclick="openEditProfileModal()">Edit Profile</button>
    `;
  } else {
    actionButtonsHtml = `
      <button class="btn-primary ${p.is_following ? 'btn-following' : ''}" id="btnFollow" onclick="toggleFollow('${p.username}')">
        ${p.is_following ? 'Following' : 'Follow'}
      </button>
      <button class="btn-secondary" onclick="window.location.href='/?chat=${p.username}'">Message</button>
    `;
  }

  headerCard.innerHTML = `
    <div class="profile-header-inner">
      <div class="profile-avatar-wrapper">
        <img src="${escapeHtml(p.avatar_url)}" class="profile-page-avatar" />
      </div>

      <div class="profile-details">
        <div class="profile-top-row">
          <h2 class="profile-handle">
            ${escapeHtml(p.username)}
            ${p.is_verified ? '<span class="verified-badge">✓</span>' : ''}
          </h2>
          <div class="profile-actions-bar">
            ${actionButtonsHtml}
          </div>
        </div>

        <div class="profile-stats-bar">
          <span><b>${p.posts_count}</b> posts</span>
          <span id="followersStat"><b>${p.followers_count}</b> followers</span>
          <span><b>${p.following_count}</b> following</span>
        </div>

        <div class="profile-bio-box">
          <div class="profile-real-name">${escapeHtml(p.full_name)}</div>
          <div class="profile-bio-text">${escapeHtml(p.bio || '')}</div>
          ${p.website ? `<a href="${escapeHtml(p.website)}" target="_blank" rel="noopener" class="profile-website">${escapeHtml(p.website)}</a>` : ''}
        </div>
      </div>
    </div>
  `;
}

function renderPostsGrid() {
  const grid = document.getElementById("profilePostsGrid");
  const posts = profileState.activeTab === "saved"
    ? (profileState.profile.saved_posts || [])
    : (profileState.profile.posts || []);

  if (posts.length === 0) {
    grid.innerHTML = `
      <div class="empty-profile-posts">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
        <p>No ${profileState.activeTab} yet</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = posts.map(post => `
    <div class="grid-post-item" onclick="viewPostDetails('${post.id}')">
      <img src="${escapeHtml(post.image_url)}" loading="lazy" />
      <div class="grid-overlay">
        <span>❤️ ${post.likes_count}</span>
        <span>💬 ${post.comments_count}</span>
      </div>
    </div>
  `).join("");
}

async function toggleFollow(username) {
  const btn = document.getElementById("btnFollow");
  try {
    const res = await fetch(`/api/auth/users/${username}/follow`, {
      method: "POST",
      headers: getAuthHeader(),
    });
    if (res.ok) {
      const data = await res.json();
      profileState.profile.is_following = data.following;
      profileState.profile.followers_count = data.followers_count;

      if (btn) {
        btn.textContent = data.following ? "Following" : "Follow";
        btn.className = `btn-primary ${data.following ? 'btn-following' : ''}`;
      }
      const followersStat = document.getElementById("followersStat");
      if (followersStat) {
        followersStat.innerHTML = `<b>${data.followers_count}</b> followers`;
      }
    }
  } catch (err) {
    console.error("Error toggling follow:", err);
  }
}

async function toggleAnalyticsView() {
  const analyticsCard = document.getElementById("analyticsCard");
  const tabBtn = document.getElementById("tabAnalytics");

  if (profileState.showAnalytics) {
    analyticsCard.style.display = "none";
    tabBtn.classList.remove("active");
    profileState.showAnalytics = false;
    return;
  }

  try {
    const res = await fetch(`/api/auth/users/${profileState.profile.username}/analytics`);
    if (res.ok) {
      const data = await res.json();
      const tagsHtml = data.top_tags.map(t => `<span class="analytics-tag">#${escapeHtml(t.tag)} (${t.count})</span>`).join(" ");

      analyticsCard.innerHTML = `
        <div class="analytics-inner">
          <div class="analytics-title">Performance &amp; Engagement Insights</div>
          <div class="analytics-metrics-grid">
            <div class="metric-box">
              <span class="metric-num">${data.engagement_rate}%</span>
              <span class="metric-lbl">Engagement Rate</span>
            </div>
            <div class="metric-box">
              <span class="metric-num">${data.total_likes_received}</span>
              <span class="metric-lbl">Total Likes</span>
            </div>
            <div class="metric-box">
              <span class="metric-num">${data.total_comments_received}</span>
              <span class="metric-lbl">Comments</span>
            </div>
            <div class="metric-box">
              <span class="metric-num">${data.total_posts}</span>
              <span class="metric-lbl">Total Posts</span>
            </div>
          </div>
          ${tagsHtml ? `<div class="analytics-tags-row"><b>Top Niches:</b> ${tagsHtml}</div>` : ''}
        </div>
      `;
      analyticsCard.style.display = "block";
      tabBtn.classList.add("active");
      profileState.showAnalytics = true;
    }
  } catch (err) {
    console.error("Error fetching analytics:", err);
  }
}

function switchProfileTab(tab) {
  profileState.activeTab = tab;
  document.getElementById("tabPosts").classList.toggle("active", tab === "posts");
  const tabSaved = document.getElementById("tabSaved");
  if (tabSaved) tabSaved.classList.toggle("active", tab === "saved");
  renderPostsGrid();
}

// Edit Profile Modal
function openEditProfileModal() {
  const p = profileState.profile;
  document.getElementById("editFullName").value = p.full_name;
  document.getElementById("editBio").value = p.bio || "";
  document.getElementById("editWebsite").value = p.website || "";
  document.getElementById("editAvatarUrl").value = p.avatar_url;
  document.getElementById("editProfileModal").style.display = "flex";
}

function closeEditProfileModal() {
  document.getElementById("editProfileModal").style.display = "none";
}

async function saveProfileChanges(e) {
  e.preventDefault();
  const full_name = document.getElementById("editFullName").value.trim();
  const bio = document.getElementById("editBio").value.trim();
  const website = document.getElementById("editWebsite").value.trim();
  const avatar_url = document.getElementById("editAvatarUrl").value.trim();

  try {
    const res = await fetch("/api/auth/profile", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ full_name, bio, website, avatar_url })
    });
    if (res.ok) {
      closeEditProfileModal();
      await loadProfile();
    }
  } catch (err) {
    console.error("Error saving profile:", err);
  }
}

function setupSearch() {
  const searchInput = document.getElementById("searchInput");
  if (!searchInput) return;

  let debounceTimeout = null;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      runSearch(e.target.value);
    }, 250);
  });

  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target)) {
      const dropdown = document.getElementById("searchResultsDropdown");
      if (dropdown) dropdown.style.display = "none";
    }
  });
}

async function runSearch(query) {
  const dropdown = document.getElementById("searchResultsDropdown");
  if (!dropdown) return;
  if (!query.trim()) {
    dropdown.style.display = "none";
    return;
  }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    if (res.ok) {
      const data = await res.json();
      const users = data.results.users || [];
      const tags = data.results.tags || [];

      if (users.length === 0 && tags.length === 0) {
        dropdown.innerHTML = `<div class="search-empty">No results for "${escapeHtml(query)}"</div>`;
      } else {
        let html = "";
        if (users.length > 0) {
          html += `<div class="search-heading">Creators</div>`;
          users.forEach(u => {
            html += `
              <div class="search-item" onclick="window.location.href='/profile/${escapeHtml(u.username)}'">
                <img src="${escapeHtml(u.avatar_url)}" class="search-avatar" />
                <div class="search-info">
                  <div class="search-user">@${escapeHtml(u.username)} ${u.is_verified ? '✓' : ''}</div>
                  <div class="search-sub">${escapeHtml(u.full_name)}</div>
                </div>
              </div>
            `;
          });
        }
        if (tags.length > 0) {
          html += `<div class="search-heading">Tags</div>`;
          tags.forEach(t => {
            html += `
              <div class="search-item" onclick="window.location.href='/?tag=${encodeURIComponent(t.tag)}'">
                <div class="search-tag-icon">#</div>
                <div class="search-info">
                  <div class="search-user">#${escapeHtml(t.tag)}</div>
                  <div class="search-sub">${t.posts_count} posts</div>
                </div>
              </div>
            `;
          });
        }
        dropdown.innerHTML = html;
      }
      dropdown.style.display = "block";
    }
  } catch (err) {}
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
