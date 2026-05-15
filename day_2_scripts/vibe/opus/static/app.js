(() => {
  const listEl = document.getElementById("article-list");
  const detailEl = document.getElementById("detail");
  const searchEl = document.getElementById("search");
  const emptyEl = document.getElementById("empty-state");
  const countEl = document.getElementById("count-badge");

  let articles = [];
  let filtered = [];
  let activeId = null;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));
  }

  function renderList() {
    listEl.innerHTML = "";
    if (filtered.length === 0) {
      emptyEl.hidden = false;
      return;
    }
    emptyEl.hidden = true;
    for (const a of filtered) {
      const li = document.createElement("li");
      li.dataset.id = a.number;
      if (a.number === activeId) li.classList.add("active");
      li.innerHTML = `
        <span class="art-tag">${escapeHtml(a.article)}</span>
        <p class="art-summary">${escapeHtml(a.summary || "(no summary)")}</p>
      `;
      li.addEventListener("click", () => selectArticle(a.number));
      listEl.appendChild(li);
    }
  }

  function renderDetail(a) {
    if (!a) {
      detailEl.innerHTML = `
        <div class="placeholder">
          <h2>Select an article</h2>
          <p>Pick any article on the left to read the full text.</p>
        </div>`;
      return;
    }
    const titleClean = a.title.replace(/^Art\.\s*\d+\s*GDPR\s*/i, "").trim();
    detailEl.innerHTML = `
      <div class="detail-header">
        <span class="art-tag">${escapeHtml(a.article)}</span>
        <h2>${escapeHtml(titleClean || a.title)}</h2>
      </div>
      <div class="detail-summary">
        <strong>Summary</strong>
        ${escapeHtml(a.summary || "(no summary)")}
      </div>
      <div class="detail-body">${escapeHtml(a.full_article)}</div>
    `;
    detailEl.scrollTop = 0;
  }

  function selectArticle(n) {
    activeId = n;
    const a = articles.find((x) => x.number === n);
    renderList();
    renderDetail(a);
  }

  function applyFilter() {
    const q = searchEl.value.trim().toLowerCase();
    if (!q) {
      filtered = articles.slice();
    } else {
      filtered = articles.filter((a) => {
        return (
          (a.summary || "").toLowerCase().includes(q) ||
          (a.title || "").toLowerCase().includes(q) ||
          (a.article || "").toLowerCase().includes(q)
        );
      });
    }
    renderList();
  }

  searchEl.addEventListener("input", applyFilter);

  fetch("/api/articles")
    .then((r) => r.json())
    .then((data) => {
      articles = (data.GDPR || []).slice().sort((a, b) => a.number - b.number);
      filtered = articles.slice();
      countEl.textContent = `${articles.length} article${articles.length === 1 ? "" : "s"}`;
      renderList();
      if (articles.length > 0) selectArticle(articles[0].number);
    })
    .catch((err) => {
      listEl.innerHTML = `<li class="empty">Failed to load articles: ${escapeHtml(err.message)}</li>`;
    });
})();
