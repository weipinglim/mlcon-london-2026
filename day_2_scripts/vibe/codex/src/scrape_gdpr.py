#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


BASE_URL = "https://gdpr-info.eu"
HOME_URL = f"{BASE_URL}/"
DEFAULT_MODEL = "qwen3.5:4b"
DEFAULT_OUTPUTS = [
    Path("data/gdpr_articles.json"),
    Path("site/gdpr_articles.json"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape GDPR articles and summarize them with a local Ollama model."
    )
    parser.add_argument("--start", type=int, default=20, help="First article number to scrape.")
    parser.add_argument("--end", type=int, default=25, help="Last article number to scrape.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument(
        "--ollama-host",
        default="http://127.0.0.1:11434",
        help="Base URL for the local Ollama server.",
    )
    return parser.parse_args()


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.replace(" .", ".").replace(" ,", ",")
    return value.strip()


def build_article_url_map(home_html: str) -> dict[int, str]:
    soup = BeautifulSoup(home_html, "html.parser")
    article_map: dict[int, str] = {}

    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = re.search(r"/art-(\d+)-gdpr/?$", href)
        if not match:
            continue

        article_number = int(match.group(1))
        if href.startswith("http://") or href.startswith("https://"):
            article_map[article_number] = href
        else:
            article_map[article_number] = f"{BASE_URL}{href}"

    return article_map


def clone_without_superscripts(tag: Tag) -> Tag:
    clone = BeautifulSoup(str(tag), "html.parser")
    root = clone.find()
    if root is None:
        raise ValueError("Could not clone tag for cleanup.")

    for sup in root.find_all("sup"):
        sup.decompose()

    return root


def text_excluding_nested_lists(tag: Tag) -> str:
    parts: list[str] = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if child.name in {"ol", "ul"}:
                continue
            parts.append(child.get_text(" ", strip=True))
    return normalize_text(" ".join(parts))


def render_list(list_tag: Tag, level: int = 0) -> list[str]:
    lines: list[str] = []
    index = 1
    for item in list_tag.find_all("li", recursive=False):
        cleaned_item = clone_without_superscripts(item)
        body = text_excluding_nested_lists(cleaned_item)
        prefix = f"{'  ' * level}{index}. "
        if body:
            lines.append(prefix + body)

        for nested in cleaned_item.find_all(["ol", "ul"], recursive=False):
            lines.extend(render_list(nested, level + 1))

        index += 1
    return lines


def extract_full_article(soup: BeautifulSoup) -> tuple[str, str]:
    heading = soup.find("h1")
    if heading is None:
        raise ValueError("Could not find article heading.")

    title = normalize_text(heading.get_text(" ", strip=True))
    content = soup.select_one(".entry-content")
    if content is None:
        raise ValueError(f"Could not find article content for {title}.")

    chunks: list[str] = []
    for child in content.children:
        if not isinstance(child, Tag):
            continue

        classes = child.get("class", [])
        if "empfehlung-erwaegungsgruende" in classes:
            break

        cleaned_child = clone_without_superscripts(child)
        if cleaned_child.name in {"ol", "ul"}:
            chunks.extend(render_list(cleaned_child))
            continue

        text = normalize_text(cleaned_child.get_text(" ", strip=True))
        if text:
            chunks.append(text)

    full_article = "\n".join(chunks).strip()
    if not full_article:
        raise ValueError(f"Could not extract article body for {title}.")

    return title, full_article


def summarize_article(
    article_label: str,
    article_title: str,
    full_article: str,
    model: str,
    ollama_host: str,
) -> str:
    prompt = f"""
You are summarizing a GDPR article for a professional legal-reference website.

Return exactly one plain-text summary sentence of 20-40 words.
Do not quote the text.
Do not mention being an AI.
Do not use markdown.
Focus on the legal right, obligation, or restriction created by the article.
Only include conditions or exceptions that are explicitly stated in the article text.
Do not add legal grounds, examples, or interpretations that are not present in the article.

Article label: {article_label}
Article title: {article_title}
Article text:
{full_article}
""".strip()

    response = requests.post(
        f"{ollama_host.rstrip('/')}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 96,
            },
        },
        timeout=300,
    )
    response.raise_for_status()
    payload = response.json()
    summary = normalize_text(payload.get("response", ""))
    if not summary:
        raise ValueError(f"Empty summary received for {article_label}.")
    return summary


def scrape_articles(start: int, end: int, model: str, ollama_host: str) -> dict[str, list[dict[str, Any]]]:
    home_html = fetch_html(HOME_URL)
    article_url_map = build_article_url_map(home_html)

    records: list[dict[str, Any]] = []
    for article_number in range(start, end + 1):
        if article_number not in article_url_map:
            raise KeyError(f"Article {article_number} was not found on {HOME_URL}.")

        article_url = article_url_map[article_number]
        article_html = fetch_html(article_url)
        soup = BeautifulSoup(article_html, "html.parser")
        article_title, full_article = extract_full_article(soup)
        article_label = f"Art. {article_number}"
        summary = summarize_article(
            article_label=article_label,
            article_title=article_title,
            full_article=full_article,
            model=model,
            ollama_host=ollama_host,
        )

        records.append(
            {
                "article": article_label,
                "title": article_title,
                "summary": summary,
                "full_article": full_article,
                "source_url": article_url,
            }
        )

    return {"GDPR": records}


def write_outputs(payload: dict[str, list[dict[str, Any]]], outputs: list[Path]) -> None:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False)
    for output_path in outputs:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    payload = scrape_articles(
        start=args.start,
        end=args.end,
        model=args.model,
        ollama_host=args.ollama_host,
    )
    write_outputs(payload, DEFAULT_OUTPUTS)
    print(
        f"Wrote {len(payload['GDPR'])} articles "
        f"({args.start}-{args.end}) to: {', '.join(str(path) for path in DEFAULT_OUTPUTS)}"
    )


if __name__ == "__main__":
    main()
