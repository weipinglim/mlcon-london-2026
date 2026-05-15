"""
GDPR Article Browser – Flask web app.

Serves a professional single-page UI for browsing GDPR articles scraped from gdpr-info.eu.

Usage:
    python app.py              # default port 5000
    python app.py 8080         # custom port
"""

import json
import os
import sys

from flask import Flask, Response, jsonify, send_from_directory

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gdpr_articles.json")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")


def load_articles():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)["GDPR"]


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/articles")
def api_articles():
    data = load_articles()
    return Response(json.dumps(data), mimetype="application/json")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"GDPR Browser starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()
