"""Flask server for the GDPR article browser.

Run:
    python app.py            # http://localhost:5050
    python app.py --port 8080
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from flask import Flask, jsonify, render_template

BASE = Path(__file__).parent
DATA_FILE = BASE / "gdpr.json"

app = Flask(__name__, template_folder=str(BASE / "templates"),
            static_folder=str(BASE / "static"))


def load_articles() -> dict:
    if not DATA_FILE.exists():
        return {"GDPR": []}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/articles")
def api_articles():
    return jsonify(load_articles())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    app.run(host=args.host, port=args.port, debug=False)
