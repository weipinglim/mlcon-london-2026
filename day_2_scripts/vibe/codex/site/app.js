const state = {
  articles: [],
  filtered: [],
  selectedArticle: null,
};

const articleCount = document.getElementById("article-count");
const articleList = document.getElementById("article-list");
const searchInput = document.getElementById("search");
const template = document.getElementById("article-item-template");

const detailArticle = document.getElementById("detail-article");
const detailTitle = document.getElementById("detail-title");
const detailSummary = document.getElementById("detail-summary");
const detailBody = document.getElementById("detail-body");
const detailSource = document.getElementById("detail-source");

function renderDetail(article) {
  if (!article) {
    detailArticle.textContent = "Select an article";
    detailTitle.textContent = "Choose a summary on the left.";
    detailSummary.textContent = "The full article text will appear here.";
    detailBody.textContent = "";
    detailSource.href = "#";
    return;
  }

  detailArticle.textContent = article.article;
  detailTitle.textContent = article.title;
  detailSummary.textContent = article.summary;
  detailBody.textContent = article.full_article;
  detailSource.href = article.source_url;
}

function renderList() {
  articleList.innerHTML = "";

  for (const article of state.filtered) {
    const fragment = template.content.cloneNode(true);
    const button = fragment.querySelector(".article-item");

    fragment.querySelector(".article-label").textContent = article.article;
    fragment.querySelector(".article-item-title").textContent = article.title;
    fragment.querySelector(".article-item-summary").textContent = article.summary;

    if (state.selectedArticle?.article === article.article) {
      button.classList.add("is-selected");
    }

    button.addEventListener("click", () => {
      state.selectedArticle = article;
      renderDetail(article);
      renderList();
    });

    articleList.appendChild(fragment);
  }
}

function applyFilter(query) {
  const normalized = query.trim().toLowerCase();
  state.filtered = state.articles.filter((article) => {
    if (!normalized) {
      return true;
    }

    const haystack = `${article.article} ${article.title} ${article.summary}`.toLowerCase();
    return haystack.includes(normalized);
  });

  if (!state.filtered.some((article) => article.article === state.selectedArticle?.article)) {
    state.selectedArticle = state.filtered[0] ?? null;
    renderDetail(state.selectedArticle);
  }

  renderList();
}

async function loadArticles() {
  const response = await fetch("./gdpr_articles.json");
  if (!response.ok) {
    throw new Error(`Failed to load data: ${response.status}`);
  }

  const payload = await response.json();
  state.articles = payload.GDPR ?? [];
  state.filtered = [...state.articles];
  state.selectedArticle = state.filtered[0] ?? null;

  articleCount.textContent = `${state.articles.length} articles`;
  renderDetail(state.selectedArticle);
  renderList();
}

searchInput.addEventListener("input", (event) => {
  applyFilter(event.target.value);
});

loadArticles().catch((error) => {
  detailArticle.textContent = "Load error";
  detailTitle.textContent = "Could not load GDPR article data.";
  detailSummary.textContent = error.message;
});
