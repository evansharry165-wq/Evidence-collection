"""Source: DGAC France — préavis de grève dans le transport aérien.

The French Ministry of Ecology & Transport publishes ATC / airline strike notices at
https://www.ecologie.gouv.fr/preavis-de-greve-dans-le-transport-aerien.
No REST API — module fetches the HTML page and extracts every mention of a preavis by
date. Fragile against page-structure changes; escalate to Layer-2 (paid service) if the
scrape breaks and stays broken.
"""

import re, time
from html import unescape
from pull_common import http_get, wrap

ID = "dgac-france-notices"
ENDPOINT = "https://www.ecologie.gouv.fr/preavis-de-greve-dans-le-transport-aerien"
AUTH_MODE = "none (HTML scrape)"


def _extract_notices(html: str) -> list[dict]:
    # Strip tags, look for date patterns and greve/preavis mentions
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", unescape(text))
    notices = []
    # Match French date formats: "12 juillet 2026", "12/07/2026", "12-07-2026"
    for m in re.finditer(
        r"(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}"
        r"|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})[^.]{0,300}(gr[èe]ve|pr[ée]avis)[^.]{0,300}",
        text, re.I,
    ):
        notices.append({"date_match": m.group(1), "snippet": m.group(0)[:400].strip()})
    # Dedupe by snippet hash
    seen, out = set(), []
    for n in notices:
        k = n["snippet"][:100]
        if k not in seen:
            seen.add(k)
            out.append(n)
    return out[:50]


def pull() -> dict:
    t0 = time.time()
    html = http_get(ENDPOINT, timeout=45)
    notices = _extract_notices(html)
    data = {
        "source_page": ENDPOINT,
        "notices": notices,
        "note": "HTML-scrape — validate manually before citing as evidence in a case.",
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(notices), time.time() - t0)
