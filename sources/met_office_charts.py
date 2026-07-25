"""Source: Met Office aviation weather charts (surface pressure + significant weather).

The Met Office publishes free aviation weather charts as image files (F214 wind &
temp, F215 sig-wx, MSLP analysis, forecast). No REST API — pull the chart index
page, extract every chart image URL + timestamp, store references. Downstream UI
can then render the chart images inline without any weather-decoding overhead.

The images themselves aren't downloaded into the repo (they're big); we store the
URLs + metadata so the UI can lazy-load direct from Met Office.
"""

import re, time
from html import unescape
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap

ID = "met-office-charts"
ENDPOINT = "https://www.metoffice.gov.uk/services/transport/aviation/regulated/general-aviation"
AUTH_MODE = "none (public charts index)"


def pull() -> dict:
    t0 = time.time()
    html = ""
    try:
        html = http_get(ENDPOINT, timeout=45)
    except Exception:
        # Some Met Office pages need referrer headers; if fetch fails, still record
        # the endpoint so the UI can link out directly.
        pass

    # Extract every chart image URL from the page
    charts = []
    for m in re.finditer(r'<img[^>]+src="([^"]+(?:chart|f214|f215|mslp)[^"]*)"[^>]*(?:alt="([^"]*)")?', html or "", re.I):
        src = m.group(1)
        alt = m.group(2) or ""
        if not src.startswith("http"):
            src = "https://www.metoffice.gov.uk" + (src if src.startswith("/") else "/" + src)
        charts.append({"url": src, "alt": unescape(alt).strip() or None})

    # Also record known direct-link chart categories so the UI has fallbacks even if scrape returns nothing
    fallback = [
        {"category": "MSLP analysis",       "url": "https://www.metoffice.gov.uk/weather/maps-and-charts/surface-pressure",  "note": "Live MSLP chart page"},
        {"category": "Aviation sig-wx",     "url": "https://www.metoffice.gov.uk/services/transport/aviation/regulated/ga-briefing",  "note": "GA briefing hub"},
        {"category": "Volcanic ash advisory","url": "https://www.metoffice.gov.uk/services/transport/aviation/regulated/vaac",         "note": "London VAAC page"},
    ]
    data = {
        "endpoint": ENDPOINT,
        "note": "Chart image URLs — UI lazy-loads direct from Met Office. Not stored inline.",
        "charts": charts,
        "fallback_pages": fallback,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(charts), time.time() - t0)
