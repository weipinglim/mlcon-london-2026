#!/usr/bin/env python3
"""FastAPI app serving the GDPR article browser."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="GDPR Article Browser")

BASE = Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/api/articles")
def get_articles():
    with open(BASE / "gdpr_articles.json", "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(BASE / "static" / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
