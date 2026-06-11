#!/usr/bin/env python3
"""Daily AI signal: top Hacker News AI stories from the last 24h, written into the README."""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
QUERIES = ["LLM", "AI agent", "Claude", "GPT", "open source model", "machine learning"]


def fetch(query, since):
    params = urllib.parse.urlencode({
        "query": query, "tags": "story",
        "numericFilters": f"created_at_i>{since},points>40",
        "hitsPerPage": 10,
    })
    req = urllib.request.Request(
        f"https://hn.algolia.com/api/v1/search?{params}",
        headers={"User-Agent": "profile-signal/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)["hits"]


def main():
    since = int(time.time()) - 86400
    seen, stories = set(), []
    for q in QUERIES:
        try:
            for h in fetch(q, since):
                if h["objectID"] not in seen and h.get("title"):
                    seen.add(h["objectID"])
                    stories.append(h)
        except Exception:
            continue
    stories.sort(key=lambda h: -h["points"])
    top = stories[:3]

    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    if top:
        rows = "\n>\n".join(
            f"> **[{h['title']}]({h.get('url') or 'https://news.ycombinator.com/item?id=' + h['objectID']})**"
            f" — {h['points']} pts"
            for h in top)
    else:
        rows = "> quiet day on the wire"
    section = (
        "<!--SIGNAL:START-->\n"
        f"`{today}` · top AI stories of the last 24h, picked daily by [this action](./.github/workflows/signal.yml)\n\n"
        f"{rows}\n"
        "<!--SIGNAL:END-->")
    text = README.read_text()
    README.write_text(re.sub(r"<!--SIGNAL:START-->.*?<!--SIGNAL:END-->", section, text, flags=re.S))


if __name__ == "__main__":
    main()
