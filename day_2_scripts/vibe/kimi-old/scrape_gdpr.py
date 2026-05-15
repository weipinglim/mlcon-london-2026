#!/usr/bin/env python3
"""Scrape GDPR articles 20-25 from gdpr-info.eu and summarize with local LLM."""

import json
import re
import textwrap
import time

import requests
from bs4 import BeautifulSoup

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:4b"
ARTICLES = range(20, 26)
OUTPUT = "gdpr_articles.json"


def fetch_article(art_num: int):
    url = f"https://gdpr-info.eu/art-{art_num}-gdpr/"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1", class_="entry-title")
    if not h1:
        raise ValueError(f"No title found for article {art_num}")

    number_span = h1.find("span", class_="dsgvo-number")
    title_span = h1.find("span", class_="dsgvo-title")

    art_label = number_span.get_text(strip=True) if number_span else f"Art. {art_num}"
    title = title_span.get_text(strip=True) if title_span else ""

    entry = soup.find("div", class_="entry-content")
    if not entry:
        raise ValueError(f"No content found for article {art_num}")

    ol = entry.find("ol")
    full_text_parts = []
    if ol:
        for li in ol.find_all("li", recursive=False):
            text = li.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            full_text_parts.append(text)
    else:
        text = entry.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        full_text_parts.append(text)

    full_text = "\n".join(full_text_parts)
    return {
        "article": art_label,
        "title": title,
        "full_article": full_text,
    }


def summarize(text: str, article_label: str) -> str:
    prompt = textwrap.dedent(
        f"""\
        Summarize the following GDPR article in 2-3 clear sentences.
        Focus on what rights or obligations it establishes.
        Be concise and accurate.

        {article_label}

        {text}

        Summary:"""
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    summary = data.get("response", "").strip()
    summary = re.sub(r'^["\']|["\']$', '', summary)
    return summary


def main():
    results = []
    for art_num in ARTICLES:
        print(f"Fetching article {art_num}...")
        article = fetch_article(art_num)
        print(f"  Summarizing with {MODEL}...")
        article["summary"] = summarize(article["full_article"], article["article"])
        results.append(article)
        print(f"  Done: {article['summary'][:100]}...")
        time.sleep(0.5)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"GDPR": results}, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} articles to {OUTPUT}")


if __name__ == "__main__":
    main()
