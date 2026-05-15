import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:4b"
OUT_FILE = "gdpr_articles_20_25_summarized.json"

with open(OUT_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

for art in articles:
    if art.get("summary"):
        continue

    prompt = (
        f"Provide a concise 2-3 sentence summary of the following GDPR article, "
        f"focusing on the rights and obligations it establishes.\n\n"
        f"{art['full_article']}\n\nSummary:"
    )

    print(f"Fixing {art['article']}...", flush=True)
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 4096}
        },
        timeout=600
    )
    resp.raise_for_status()
    data = resp.json()
    summary = data.get("response", "").strip()
    art["summary"] = summary
    print(f"  Done: {summary[:120]}...")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

print("All fixed.")
