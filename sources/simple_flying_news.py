"""Source: Simple Flying — general aviation news RSS.

simpleflying.com is broader-scope aviation news (routes, airline strategy,
regulatory changes, disruption coverage). Complements Aviation Herald's
incident-focused coverage with wider context — useful for regulatory-change
evidence and for spotting patterns Aviation Herald hasn't picked up yet.

Free RSS, no auth.
"""

import re, time
from html import unescape
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap

ID = "simple-flying-news"
ENDPOINT = "https://simpleflying.com/feed/"
AUTH_MODE = "none"

# Categories we especially care about — used to tag items for downstream filtering
CATEGORY_KEYWORDS = {
    "disruption":       [r"\bstrike\b", r"\bdelay\b", r"\bcancel", r"\bdisruption\b", r"\bATC\b", r"\bATFM\b", r"\bweather.*disrupt"],
    "regulatory":       [r"\bEC\s?261\b", r"\bUK\s?261\b", r"\bEASA\b", r"\bCAA\b", r"\bregulator", r"\bcompensation"],
    "operational":      [r"\bcrew\b", r"\bfleet\b", r"\brouting\b", r"\balliance\b", r"\bcode.?share\b"],
    "safety":           [r"\bincident\b", r"\bemergency\b", r"\bfire\b", r"\bevacuation\b", r"\bsmoke\b"],
    "airport":          [r"\bairport\b", r"\brunway\b", r"\bterminal\b", r"\btaxiway\b"],
}


def _tag(text: str) -> list[str]:
    tags = []
    for cat, patterns in CATEGORY_KEYWORDS.items():
        for p in patterns:
            if re.search(p, text, re.I):
                tags.append(cat)
                break
    return tags


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
        # Strip HTML from description
        desc_plain = re.sub(r"<[^>]+>", " ", desc)
        desc_plain = re.sub(r"\s+", " ", desc_plain).strip()
        items.append({
            "title": title,
            "link": field("link"),
            "pub_date": field("pubDate"),
            "guid": field("guid"),
            "description": desc_plain[:1200],
            "tags": _tag(title + " " + desc_plain),
        })
    return items


def pull() -> dict:
    t0 = time.time()
    raw = http_get(ENDPOINT, timeout=45)
    items = _parse_rss(raw)
    tagged = [i for i in items if i["tags"]]
    data = {
        "feed_url": ENDPOINT,
        "items": items,
        "tagged_items": tagged,
        "tag_counts": {c: sum(1 for i in items if c in i["tags"]) for c in CATEGORY_KEYWORDS.keys()},
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(items), time.time() - t0)
