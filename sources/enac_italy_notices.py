"""Source: ENAC Italy — sciopero nel trasporto aereo (aviation industrial-action notices).

ENAC publishes strike calendars at https://www.enac.gov.it/passeggeri/sciopero-nel-trasporto-aereo.
No REST API — HTML scrape. Same fragility caveat as DGAC France module.
"""

import re, time
from html import unescape
from pull_common import http_get, wrap

ID = "enac-italy-notices"
ENDPOINT = "https://www.enac.gov.it/passeggeri/sciopero-nel-trasporto-aereo"
AUTH_MODE = "none (HTML scrape)"


def _extract_notices(html: str) -> list[dict]:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", unescape(text))
    notices = []
    # Italian date formats: "12 luglio 2026", "12/07/2026"
    for m in re.finditer(
        r"(\d{1,2}\s+(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+\d{4}"
        r"|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})[^.]{0,300}(sciopero|proclamazione)[^.]{0,300}",
        text, re.I,
    ):
        notices.append({"date_match": m.group(1), "snippet": m.group(0)[:400].strip()})
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
