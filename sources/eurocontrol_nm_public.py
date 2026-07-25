"""Source: Eurocontrol Network Manager — public network operations status.

The full NM B2B (authoritative regulations, flight-plan tactical updates) needs a B2B
certificate (first two free, €200 each thereafter). For Layer 1 we use the public
Network Operations Portal daily bulletin URL + the public NM Operations page.

Once the B2B cert lands we replace this module with the SOAP client — same source ID,
same output shape, richer payload.
"""

import re, time
from html import unescape
from pull_common import http_get, wrap

ID = "eurocontrol-nm-public"
ENDPOINT = "https://www.public.nm.eurocontrol.int/PUBPORTAL/gateway/spec/index.html"
AUTH_MODE = "none (public portal)"


def pull() -> dict:
    t0 = time.time()
    html = http_get(ENDPOINT, timeout=45)
    # Strip tags — this is a portal index; extract link text mentioning "regulation",
    # "network operations", "daily plan", "AIM"
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL | re.I)
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{4,120})</a>', text, re.I)
    keep = [
        {"url": u, "text": unescape(t.strip())}
        for u, t in links
        if re.search(r"regulation|network|daily|plan|bulletin|traffic|ATFM|delay|operational", t, re.I)
    ]
    data = {
        "portal_url": ENDPOINT,
        "note": (
            "Public portal index only — full ATFM regulation feed requires Eurocontrol NM B2B "
            "certificate (first two free per organisation). Replace this module with SOAP client "
            "once cert lands. See defendable_api_discussion.md §5A."
        ),
        "operational_links": keep,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(keep), time.time() - t0)
