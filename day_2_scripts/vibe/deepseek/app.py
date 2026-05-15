"""Flask app to browse GDPR articles by summary, showing full text on selection."""
import json
from pathlib import Path
from flask import Flask, render_template, jsonify

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "gdpr_articles.json"


def load_articles():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            data = json.load(f)
        return data.get("GDPR", [])
    return []


@app.route("/")
def index():
    articles = load_articles()
    return render_template("index.html", articles=articles)


@app.route("/api/articles")
def api_articles():
    return jsonify(load_articles())


if __name__ == "__main__":
    app.run(debug=True, port=5004)
