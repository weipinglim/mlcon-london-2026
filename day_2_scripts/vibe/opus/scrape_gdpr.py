"""Scrape GDPR articles from gdpr-info.eu and summarise each with qwen3.5:4b on Ollama.

Usage:
    python scrape_gdpr.py                  # default: articles 20-25 (smoke test)
    python scrape_gdpr.py --start 1 --end 99
    python scrape_gdpr.py --articles 5,17,22

Writes gdpr.json in the script directory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://gdpr-info.eu/art-{n}-gdpr/"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3.5:4b"
HEADERS = {"User-Agent": "Mozilla/5.0 (MLCon-Bootcamp GDPR scraper)"}
OUTPUT = Path(__file__).parent / "gdpr.json"

SUMMARY_SYSTEM = (
    "You are a legal-tech assistant who writes short, plain-English summaries of GDPR "
    "articles for a search interface. Respond with the summary text only — no preamble, "
    "no quotes, no markdown headings, no article numbers."
)
SUMMARY_PROMPT = (
    "Summarise the following GDPR article in 2-3 sentences (max ~60 words). "
    "Focus on what the article requires or grants, in language a non-lawyer can scan.\n\n"
    "Title: {title}\n\n"
    "Article text:\n{body}\n"
)


def fetch_article(n: int) -> tuple[str, str]:
    """Return (title, full_article_text) for article n."""
    url = BASE_URL.format(n=n)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    h1 = soup.find("h1")
    raw_title = h1.get_text(" ", strip=True) if h1 else f"Art. {n} GDPR"
    title = re.sub(r"\s+", " ", raw_title).strip()

    entry = soup.find("div", class_="entry-content")
    if entry is None:
        raise RuntimeError(f"No entry-content for article {n}")

    # Collect children until we hit the recitals / navigation blocks.
    stop_classes = {"empfehlung-erwaegungsgruende", "page-navigation",
                    "link-to-overview", "feedback"}
    parts: list[str] = []
    for child in entry.children:
        name = getattr(child, "name", None)
        if not name:
            continue
        classes = set(child.get("class", []))
        if classes & stop_classes:
            break
        text = child.get_text("\n", strip=True)
        if text:
            parts.append(text)

    body = "\n\n".join(parts).strip()
    body = re.sub(r"\n{3,}", "\n\n", body)
    return title, body


def summarise(title: str, body: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "system": SUMMARY_SYSTEM,
        "prompt": SUMMARY_PROMPT.format(title=title, body=body),
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=300)
    r.raise_for_status()
    text = r.json().get("response", "").strip()
    # Strip any leftover wrapping quotes.
    text = re.sub(r'^["“”\']+|["“”\']+$', "", text).strip()
    return text


def article_label(title: str, n: int) -> str:
    m = re.match(r"(Art\.\s*\d+)\s*GDPR", title)
    if m:
        return m.group(1)
    return f"Art. {n}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=20)
    ap.add_argument("--end", type=int, default=25)
    ap.add_argument("--articles", type=str, default=None,
                    help="Comma-separated list, overrides --start/--end")
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()

    if args.articles:
        numbers = [int(x) for x in args.articles.split(",") if x.strip()]
    else:
        numbers = list(range(args.start, args.end + 1))

    print(f"Scraping {len(numbers)} articles: {numbers}", file=sys.stderr)

    results = []
    for n in numbers:
        t0 = time.time()
        try:
            title, body = fetch_article(n)
        except Exception as e:
            print(f"  Art. {n}: fetch failed — {e}", file=sys.stderr)
            continue
        if not body:
            print(f"  Art. {n}: empty body, skipping", file=sys.stderr)
            continue
        print(f"  Art. {n}: fetched {len(body)} chars, summarising…", file=sys.stderr)
        try:
            summary = summarise(title, body)
        except Exception as e:
            print(f"  Art. {n}: summary failed — {e}", file=sys.stderr)
            summary = ""
        results.append({
            "article": article_label(title, n),
            "number": n,
            "title": title,
            "summary": summary,
            "full_article": body,
        })
        print(f"  Art. {n}: done in {time.time() - t0:.1f}s — "
              f"summary {len(summary)} chars", file=sys.stderr)

    payload = {"GDPR": results}
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {len(results)} articles to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
