"""Scrape GDPR articles 20-25 from gdpr-info.eu and summarize with Ollama qwen3.5:4B."""
import json
import re
import requests
from bs4 import BeautifulSoup

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:4b"
ARTICLES = range(20, 26)  # 20-25 inclusive


def scrape_article(num):
    url = f"https://gdpr-info.eu/art-{num}-gdpr/"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    content = soup.find("div", id="content")
    if not content:
        raise ValueError(f"No #content div found for article {num}")

    h1 = content.find("h1")
    title = h1.get_text(strip=True) if h1 else f"Art. {num} GDPR"

    # Extract all list items and paragraphs that contain the article text.
    # The article body is before the "Suitable Recitals" h2.
    parts = []
    for el in content.find_all(["p", "li"]):
        # Stop at "Suitable Recitals" heading or "Related" sections
        prev_h2 = el.find_previous("h2")
        if prev_h2 and "suitable recital" in prev_h2.get_text(strip=True).lower():
            break
        text = el.get_text(" ", strip=True)
        # Skip nav/administrative text
        if text and len(text) > 20:
            parts.append(text)

    full_text = "\n\n".join(parts)
    if not full_text:
        raise ValueError(f"No article text extracted for article {num}")

    return {"article": f"Art. {num}", "title": title, "full_article": full_text}


def summarize(text, article_label):
    prompt = (
        f"You are a legal editor. Write a one-sentence plain-English summary "
        f"of this GDPR article ({article_label}). Keep it under 60 words. "
        f"Do not repeat the article number. Just the summary sentence.\n\n"
        f"{text}"
    )

    body = {"model": MODEL, "prompt": prompt, "stream": False, "think": False,
            "options": {"temperature": 0.3, "num_predict": 120}}
    resp = requests.post(OLLAMA_URL, json=body, timeout=300)
    resp.raise_for_status()
    summary = resp.json()["response"].strip()
    # Clean quotes
    summary = summary.strip('"').strip("'")
    return summary


def main():
    articles = []
    for num in ARTICLES:
        print(f"Scraping Art. {num}...")
        entry = scrape_article(num)
        print(f"  Summarizing ({len(entry['full_article'])} chars)...")
        entry["summary"] = summarize(entry["full_article"], entry["article"])
        del entry["title"]  # keep only article, summary, full_article
        articles.append(entry)
        print(f"  -> {entry['summary'][:80]}...")

    output = {"GDPR": articles}
    with open("gdpr_articles.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(articles)} articles to gdpr_articles.json")


if __name__ == "__main__":
    main()
