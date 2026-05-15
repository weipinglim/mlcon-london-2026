import requests
from bs4 import BeautifulSoup
import json
import re

articles = []

for num in range(20, 26):
    url = f"https://gdpr-info.eu/art-{num}-gdpr/"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.find("div", class_="entry-content")
    if not content:
        print(f"Warning: no content for article {num}")
        continue

    text = content.get_text(separator="\n", strip=True)
    # Clean up: remove excessive newlines
    text = re.sub(r"\n+", "\n", text)

    # Extract title from first line or page title
    title_tag = soup.find("h1", class_="entry-title")
    title = title_tag.get_text(strip=True) if title_tag else f"Article {num}"

    articles.append({
        "article": f"Art. {num}",
        "title": title,
        "full_article": text
    })
    print(f"Fetched Art. {num}: {len(text)} chars")

with open("gdpr_articles_20_25.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print("Saved gdpr_articles_20_25.json")
