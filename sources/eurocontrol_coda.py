"""Source: Eurocontrol CODA — Central Office for Delay Analysis.

Public Eurocontrol delay statistics reports — monthly digests + weekly briefs
covering ATFM delay causes, network performance, delay-per-flight trends.
Companion to the eurocontrol-nm-public source: CODA is retrospective analysis
(what did happen), NM is live operational status (what is happening).

No REST API — pull the publications index page and extract PDF/report URLs.
Downstream UI links out; PDFs not stored inline.
"""

import re, time
from html import unescape
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap

ID = "eurocontrol-coda"
ENDPOINT = "https://www.eurocontrol.int/publications"
AUTH_MODE = "none"


def pull() -> dict:
    t0 = time.time()
    html = ""
    try:
        html = http_get(ENDPOINT + "?f%5B0%5D=publication_theme%3AEconomics%20and%20traffic%20statistics", timeout=45)
    except Exception:
        html = ""

    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL | re.I)
    # Extract every publication link that mentions CODA / delay / performance
    pubs = []
    seen = set()
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{6,140})</a>', text):
        url = m.group(1)
        title = unescape(m.group(2).strip())
        if not re.search(r"CODA|delay|network[- ]?performance|punctuality|ATFM", title, re.I):
            continue
        if not url.startswith("http"):
            url = "https://www.eurocontrol.int" + (url if url.startswith("/") else "/" + url)
        key = title[:80]
        if key in seen:
            continue
        seen.add(key)
        pubs.append({"title": title, "url": url})
        if len(pubs) >= 40:
            break
    data = {
        "endpoint": ENDPOINT,
        "note": "Retrospective delay analysis — companion to live NM feed. UI links out; PDFs not stored inline.",
        "publications": pubs,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(pubs), time.time() - t0)
