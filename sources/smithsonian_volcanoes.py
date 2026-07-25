"""Source: Smithsonian Global Volcanism Program — currently-active volcanoes.

Free JSON feed of every volcano currently or recently erupting, with location,
last-eruption date, alert level. Complements the VAAC ash feed by giving
upstream volcanic-activity intelligence (an ash-cloud VAAC advisory is
downstream of an eruption; this source catches eruptions before they trigger
an advisory).
"""

import json, re, time
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap

ID = "smithsonian-volcanoes"
ENDPOINT = "https://volcano.si.edu/news/WeeklyVolcanoRSS.xml"
AUTH_MODE = "none"


def _parse_items(xml: str) -> list[dict]:
    from html import unescape
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
        # Titles look like "Volcano — Country (activity summary)"
        name_country = title.split("—") if "—" in title else title.split("-")
        volcano = (name_country[0] if name_country else title).strip()
        country = (name_country[1] if len(name_country) > 1 else "").strip()
        items.append({
            "volcano": volcano,
            "country_hint": country,
            "title": title,
            "link": field("link"),
            "pub_date": field("pubDate"),
            "description": re.sub(r"<[^>]+>", " ", desc)[:1200].strip(),
        })
    return items


def pull() -> dict:
    t0 = time.time()
    raw = http_get(ENDPOINT, timeout=45)
    items = _parse_items(raw)
    data = {
        "feed_url": ENDPOINT,
        "note": "Weekly report of ongoing / recent volcanic activity — pairs with VAAC ash advisories.",
        "volcanoes": items,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(items), time.time() - t0)
