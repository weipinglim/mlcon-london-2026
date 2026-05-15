from flask import Flask, render_template_string, jsonify
import json
import re

app = Flask(__name__)

with open("gdpr_articles_20_25_summarized.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

# Clean up full_article text: remove navigation/footer cruft
def clean_article(text):
    # Remove everything from "Suitable Recitals" or "Table of contents" onwards
    text = re.split(r"Suitable Recitals", text, flags=re.IGNORECASE)[0]
    text = re.split(r"Table of contents", text, flags=re.IGNORECASE)[0]
    text = re.split(r"Report error", text, flags=re.IGNORECASE)[0]
    # Remove stray single-digit lines that are footnote markers
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "" or stripped.isdigit():
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

for art in articles:
    art["full_article"] = clean_article(art["full_article"])

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GDPR Article Explorer</title>
    <style>
        :root {
            --primary: #1a56db;
            --primary-dark: #1e429f;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.05);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }
        header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 2rem 1rem;
            text-align: center;
            box-shadow: var(--shadow-lg);
        }
        header h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }
        header p { margin-top: 0.5rem; opacity: 0.9; font-size: 1rem; }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }
        .layout {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
        @media (min-width: 768px) {
            .layout { grid-template-columns: 380px 1fr; }
        }
        .sidebar h2 {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }
        .article-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .article-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1rem 1.25rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: var(--shadow);
        }
        .article-card:hover {
            border-color: var(--primary);
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }
        .article-card.active {
            border-color: var(--primary);
            background: #eff6ff;
            box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.15);
        }
        .article-card .badge {
            display: inline-block;
            background: var(--primary);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            margin-bottom: 0.5rem;
        }
        .article-card .summary {
            font-size: 0.9rem;
            color: var(--text);
            line-height: 1.5;
        }
        .detail-panel {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            min-height: 300px;
        }
        .detail-panel.empty {
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            font-size: 1rem;
        }
        .detail-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }
        .detail-header h2 {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text);
        }
        .detail-header .badge {
            background: var(--primary);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
        }
        .detail-body {
            font-size: 0.95rem;
            line-height: 1.7;
            color: var(--text);
            white-space: pre-wrap;
        }
        .detail-body p {
            margin-bottom: 1rem;
        }
        .empty-state {
            text-align: center;
        }
        .empty-state svg {
            width: 48px;
            height: 48px;
            margin-bottom: 0.75rem;
            stroke: var(--text-muted);
        }
        footer {
            text-align: center;
            padding: 2rem 1rem;
            color: var(--text-muted);
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <header>
        <div style="font-size:0.8rem;opacity:0.8;margin-bottom:0.5rem;font-weight:500;letter-spacing:0.05em;">Kimi K2.6</div>
        <h1>GDPR Article Explorer</h1>
        <p>Select an article by its summary to view the full text</p>
    </header>
    <div class="container">
        <div class="layout">
            <aside class="sidebar">
                <h2>Articles</h2>
                <div class="article-list" id="articleList"></div>
            </aside>
            <main class="detail-panel empty" id="detailPanel">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                    </svg>
                    <p>Choose an article from the list to read the full text.</p>
                </div>
            </main>
        </div>
    </div>
    <footer>
        Powered by local LLM summaries (qwen3.5:4B) &middot; GDPR data from gdpr-info.eu
    </footer>
    <script>
        const articles = {{ articles | tojson }};
        const list = document.getElementById('articleList');
        const detail = document.getElementById('detailPanel');
        let activeIndex = null;

        function renderList() {
            list.innerHTML = '';
            articles.forEach((art, idx) => {
                const card = document.createElement('div');
                card.className = 'article-card' + (idx === activeIndex ? ' active' : '');
                card.innerHTML = `<span class="badge">${art.article}</span><div class="summary">${art.summary}</div>`;
                card.addEventListener('click', () => selectArticle(idx));
                list.appendChild(card);
            });
        }

        function selectArticle(idx) {
            activeIndex = idx;
            renderList();
            const art = articles[idx];
            detail.classList.remove('empty');
            detail.innerHTML = `
                <div class="detail-header">
                    <span class="badge">${art.article}</span>
                    <h2>${art.title.replace('Art. ' + art.article.split(' ')[1] + ' GDPR', '').trim()}</h2>
                </div>
                <div class="detail-body">${escapeHtml(art.full_article)}</div>
            `;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        renderList();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, articles=articles)

@app.route("/api/articles")
def api_articles():
    return jsonify(articles)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
