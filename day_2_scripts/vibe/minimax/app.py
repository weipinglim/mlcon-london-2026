#!/usr/bin/env python3
"""GDPR Article Browser - Flask web application."""

import json
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Load GDPR data
DATA_PATH = os.path.join(os.path.dirname(__file__), "gdpr_articles.json")

def load_gdpr_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

gdpr_data = load_gdpr_data()


@app.route("/")
def index():
    """Main page showing article list with summaries."""
    return render_template("index.html", articles=gdpr_data["GDPR"])


@app.route("/api/articles")
def get_articles():
    """Return all articles with summaries (for initial load)."""
    return jsonify(gdpr_data)


@app.route("/api/articles/<article_num>")
def get_article(article_num):
    """Return full article text for a specific article number."""
    for art in gdpr_data["GDPR"]:
        # Extract article number from "Art. XX"
        art_num = art["article"].replace("Art. ", "")
        if art_num == article_num:
            return jsonify(art)
    return jsonify({"error": "Article not found"}), 404


if __name__ == "__main__":
    print("Starting GDPR Article Browser...")
    print("Open http://localhost:5001 in your browser")
    app.run(host="0.0.0.0", port=5003, debug=True)