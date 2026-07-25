"""Source: The Aviation Herald — incident-focused aviation news RSS.

avherald.com is the standard reference for aviation defence practitioners — every
serious incident is written up within 24-48 hours with independent sourcing.
Free RSS feed, no auth. Ideal for the news / incident-adjacent evidence category.
"""

import re, time
from html import unescape
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap

ID = "aviation-herald-news"
ENDPOINT = "https://avherald.com/h?rss.php"
AUTH_MODE = "none"


def _parse_rss(xml: str) -> list[dict]:
    items = []
    for m in re.finditer(r"<item[^>]*>(.*?)</item>", xml, re.DOTALL):
        block = m.group(1)
        def field(name: str) -> str | None:
            n = re.search(fr"<{name}[^>]*>(.*?)</{name}>", block, re.DOTALL)
            if not n:
                return None
            v = re.sub(r"<!\[CDATA\[|\]\]>", "", n.group(1)).strip()
            return unescape(v) or None
        title = field("title") or ""
        desc = field("description") or ""
        # Aviation Herald titles carry incident type inline — extract for easier filtering
        severity = None
        if re.search(r"\baccident\b|\bfatal\b|\bhull-loss\b", title + " " + desc, re.I):
            severity = "accident"
        elif re.search(r"\bincident\b|\bemergency\b|\bmayday\b", title + " " + desc, re.I):
            severity = "incident"
        elif re.search(r"\bevent\b|\breport\b", title + " " + desc, re.I):
            severity = "event"
        items.append({
            "title": title,
            "link": field("link"),
            "pub_date": field("pubDate"),
            "guid": field("guid"),
            "description": desc[:1200],
            "severity": severity,
        })
    return items


def pull() -> dict:
    t0 = time.time()
    raw = http_get(ENDPOINT, timeout=45)
    items = _parse_rss(raw)
    by_severity = {}
    for i in items:
        by_severity.setdefault(i["severity"] or "unknown", []).append(i["title"])
    data = {
        "feed_url": ENDPOINT,
        "items": items,
        "count_by_severity": {k: len(v) for k, v in by_severity.items()},
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(items), time.time() - t0)
