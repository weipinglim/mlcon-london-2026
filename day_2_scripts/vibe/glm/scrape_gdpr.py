"""
Scrape GDPR articles from gdpr-info.eu and summarize with Ollama (qwen3.5:4b).

Usage:
    python scrape_gdpr.py              # articles 20-25 (smoke test)
    python scrape_gdpr.py --all        # articles 1-99
    python scrape_gdpr.py 30 35        # custom range
"""

import json
import re
import sys
import time

import ollama
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://gdpr-info.eu/art-{n}-gdpr/"
OUTPUT_FILE = "gdpr_articles.json"
MODEL = "qwen3.5:4b"


def scrape_article(article_num: int) -> dict | None:
    url = BASE_URL.format(n=article_num)
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        print(f"  [skip] Art. {article_num} - HTTP {resp.status_code}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the <h1> or heading containing "Art. N GDPR"
    heading = soup.find(lambda tag: tag.name in ("h1", "h2")
                        and re.search(rf"Art\.\s*{article_num}\s+GDPR", tag.get_text()))
    if not heading:
        print(f"  [skip] Art. {article_num} - heading not found")
        return None

    title_text = heading.get_text(strip=True)
    # e.g. "Art. 22 GDPR Automated individual decision-making, including profiling"
    match = re.match(r"Art\.\s*\d+\s+GDPR\s*[-–]?\s*(.*)", title_text)
    short_title = match.group(1).strip() if match else title_text

    # Article body is in div.entry-content as <ol> before the recitals section
    content_div = soup.find("div", class_="entry-content")
    if not content_div:
        print(f"  [skip] Art. {article_num} - entry-content not found")
        return None

    paragraphs = []
    for child in content_div.children:
        if not hasattr(child, "name") or child.name is None:
            continue
        text = child.get_text(strip=True)
        if "Suitable Recitals" in text or "page-navigation" in (child.get("class") or []):
            break
        if child.name in ("p", "ol", "ul"):
            paragraphs.append(text)

    full_text = "\n".join(paragraphs)
    if not full_text.strip():
        print(f"  [skip] Art. {article_num} - no article body")
        return None

    return {
        "article": f"Art. {article_num}",
        "title": short_title,
        "full_article": full_text,
    }


def summarize(text: str, article_id: str) -> str:
    prompt = (
        f"Summarize GDPR {article_id} in 2-3 clear sentences for a professional audience. "
        f"Focus on the key right, obligation, or principle it establishes. "
        f"Do not use bullet points or headings.\n\n{text}"
    )
    resp = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3},
        think=False,
    )
    return resp["message"]["content"].strip()


def main():
    if "--all" in sys.argv:
        start, end = 1, 99
    elif len(sys.argv) == 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    else:
        start, end = 20, 25

    print(f"Scraping GDPR articles {start}-{end} from gdpr-info.eu ...")
    articles = []

    for n in range(start, end + 1):
        print(f"  Fetching Art. {n} ...", end=" ", flush=True)
        data = scrape_article(n)
        if data is None:
            continue

        print("summarizing ...", end=" ", flush=True)
        data["summary"] = summarize(data["full_article"], data["article"])
        articles.append(data)
        print("done.")
        time.sleep(0.5)  # be polite to the server

    output = {"GDPR": articles}
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(articles)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
