# GDPR Article Browser

Scrapes GDPR articles from `https://gdpr-info.eu/`, summarizes each article with a local Ollama model, and serves a browser UI for navigating summaries and full text.

## Initial smoke test

Generate Articles 20-25 with local Ollama `qwen3.5:4b`:

```bash
python3 src/scrape_gdpr.py --start 20 --end 25 --model qwen3.5:4b
```

This writes:

- `data/gdpr_articles.json`
- `site/gdpr_articles.json`

Run the site:

```bash
python3 src/server.py --port 8000
```

Open `http://127.0.0.1:8000`.

## Scale to all articles

After the smoke test passes, generate the full corpus:

```bash
python3 src/scrape_gdpr.py --start 1 --end 99 --model qwen3.5:4b
```
