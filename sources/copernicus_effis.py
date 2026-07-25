"""Source: Copernicus EFFIS / Emergency Management Service — EU forest-fire snapshots.

Copernicus EMS publishes an RSS feed of activation events (fires, floods, storms).
We pull the last-N Rapid Mapping activations for events with type 'Fire' or 'Wildfire'.
Free, no auth, official EU-agency source.
"""

import re, time
from html import unescape
from pull_common import http_get, wrap

ID = "copernicus-effis"
ENDPOINT = "https://emergency.copernicus.eu/mapping/list-of-activations-rapid.rss"
AUTH_MODE = "none"


def _parse_items(xml: str) -> list[dict]:
    """Ultra-light RSS parse — no xml lib dependency, stdlib-only."""
    items = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.DOTALL):
        block = m.group(1)
        def field(name: str) -> str | None:
            n = re.search(fr"<{name}>(.*?)</{name}>", block, re.DOTALL)
            if not n:
                return None
            v = n.group(1)
            v = re.sub(r"<!\[CDATA\[|\]\]>", "", v).strip()
            return unescape(v) or None
        items.append({
            "title": field("title"),
            "link": field("link"),
            "pub_date": field("pubDate"),
            "description": (field("description") or "")[:500],
        })
    return items


def pull() -> dict:
    t0 = time.time()
    raw = http_get(ENDPOINT, timeout=45)
    items = _parse_items(raw)
    # Filter to fire-related activations
    fire = [i for i in items if re.search(r"\b(fire|wildfire|forest)\b", (i.get("title") or "") + " " + (i.get("description") or ""), re.I)]
    data = {
        "feed_url": ENDPOINT,
        "all_activations": items,
        "fire_activations": fire,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(fire), time.time() - t0)
