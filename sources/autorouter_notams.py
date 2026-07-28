"""Source: AutoRouter European NOTAM feed.

AutoRouter (https://www.autorouter.aero) provides a free-tier NOTAM feed with
better European coverage than the FAA NOTAM API. Free registration, JSON API.
The daily snapshot below queries the top European FIRs and stores per-FIR
NOTAM sets. Historical NOTAM query (what was live at 14:20 last Tuesday) is
a follow-up on-demand source that this Layer-1 module doesn't attempt.

Requires environment variable AUTOROUTER_USER + AUTOROUTER_PASS or API_KEY —
signup free at https://www.autorouter.aero. Falls back to marking failed
with actionable diagnostic if credentials missing.

Feed URL: https://api.autorouter.aero/v1.0/notam?location=<icao>&maxdays=1
Auth: HTTP Basic (user + pass) OR bearer token depending on account tier.
"""

import json, os, sys, pathlib, time, base64, urllib.request, urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap
from airports import TIER1_ICAO, BY_ICAO

ID = "autorouter-notams"
ENDPOINT = "https://api.autorouter.aero/v1.0/notam"
AUTH_MODE = "HTTP Basic (env AUTOROUTER_USER + AUTOROUTER_PASS)"


def _fetch_airport(icao: str, auth_header: str) -> list[dict]:
    """Pull current-active NOTAMs for a single airport / FIR."""
    url = f"{ENDPOINT}?location={icao}&maxdays=1"
    req = urllib.request.Request(url, headers={
        "Authorization": auth_header,
        "Accept": "application/json",
        "User-Agent": "DefendAble-EvidenceCollection/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return []
    try:
        obj = json.loads(raw)
    except Exception:
        return []
    # Response shape varies by tier; normalise to a list of NOTAM dicts.
    if isinstance(obj, list):
        items = obj
    elif isinstance(obj, dict) and "notams" in obj:
        items = obj["notams"]
    elif isinstance(obj, dict) and "data" in obj:
        items = obj["data"]
    else:
        items = []
    trimmed = []
    for it in items:
        trimmed.append({
            "id":              it.get("id") or it.get("notamId"),
            "series":          it.get("series"),
            "number":          it.get("number"),
            "type":            it.get("type"),
            "issued":          it.get("issued") or it.get("startdate"),
            "effective_start": it.get("startdate") or it.get("validFrom"),
            "effective_end":   it.get("enddate") or it.get("validTo"),
            "location":        it.get("location") or icao,
            "traffic":         it.get("traffic"),
            "purpose":         it.get("purpose"),
            "scope":           it.get("scope"),
            "text":            it.get("all") or it.get("text") or it.get("itemE"),
            "raw":             it,
        })
    return trimmed


def pull() -> dict:
    user = os.environ.get("AUTOROUTER_USER", "").strip()
    pw = os.environ.get("AUTOROUTER_PASS", "").strip()
    if not user or not pw:
        raise RuntimeError(
            "AUTOROUTER_USER / AUTOROUTER_PASS env vars missing — register free at "
            "https://www.autorouter.aero/ and add as GitHub Actions secrets."
        )
    creds = base64.b64encode(f"{user}:{pw}".encode()).decode()
    auth_header = f"Basic {creds}"

    t0 = time.time()
    per_airport = {}
    errors = {}
    total = 0
    for icao in TIER1_ICAO:
        try:
            items = _fetch_airport(icao, auth_header)
            per_airport[icao] = {
                "airport_name": BY_ICAO.get(icao, {}).get("name"),
                "notams": items,
            }
            total += len(items)
        except Exception as e:  # noqa: BLE001
            errors[icao] = f"{type(e).__name__}: {e}"

    data = {
        "coverage_note": "AutoRouter free tier: current-active NOTAMs for tier-1 hubs. Historical query = follow-up on-demand source.",
        "airport_count": len(TIER1_ICAO),
        "per_airport": per_airport,
        "errors": errors,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, total, time.time() - t0)
