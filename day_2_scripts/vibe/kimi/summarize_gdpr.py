import json
import requests
import os
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:4b"
OUT_FILE = "gdpr_articles_20_25_summarized.json"

with open("gdpr_articles_20_25.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

if os.path.exists(OUT_FILE):
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        done = json.load(f)
    done_map = {a["article"]: a for a in done}
else:
    done_map = {}

for art in articles:
    if art["article"] in done_map and done_map[art["article"]].get("summary"):
        print(f"Skipping {art['article']} (already done)")
        continue

    prompt = (
        f"Summarize the following GDPR article in 2-3 clear sentences. "
        f"Focus on the rights and obligations described.\n\n"
        f"{art['full_article']}\n\nSummary:"
    )

    print(f"Summarizing {art['article']}...", flush=True)
    start = time.time()
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
    elapsed = time.time() - start
    resp.raise_for_status()
    data = resp.json()
    summary = data.get("response", "").strip()
    art["summary"] = summary
    done_map[art["article"]] = art
    print(f"  Done in {elapsed:.1f}s: {summary[:120]}...")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(done_map.values()), f, indent=2, ensure_ascii=False)

print("All done.")
