"""Source: FAA NOTAM API — international NOTAM coverage.

The FAA API is the highest-quality free NOTAM source we can use — global coverage
(not just US airspace), stable JSON schema, no scraping. Requires free registration:
1. Register at https://api.faa.gov/s/
2. Create an "External NOTAM API" application
3. Get clientId + clientSecret
4. Add as GitHub Actions secrets: FAA_CLIENT_ID and FAA_CLIENT_SECRET

Pulls the current active NOTAMs for every airport in airports.TIER1_ICAO (the 23
multi-airline hubs). Tier-2 airports (single-airline bases) are queryable on-demand
by the app but not fetched nightly to stay well under the rate limit.
"""

import json, os, sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap
from airports import TIER1_ICAO, BY_ICAO

ID = "faa-notams"
ENDPOINT = "https://external-api.faa.gov/notamapi/v1/notams"
AUTH_MODE = "clientId + clientSecret (env FAA_CLIENT_ID / FAA_CLIENT_SECRET)"


def _fetch_airport(icao: str, client_id: str, client_secret: str) -> list[dict]:
    url = f"{ENDPOINT}?icaoLocation={icao}&pageSize=50"
    headers = {
        "client_id": client_id,
        "client_secret": client_secret,
        "User-Agent": "DefendAble-EvidenceCollection/1.0",
    }
    raw = http_get(url, headers=headers, timeout=30)
    obj = json.loads(raw) if raw.strip() else {"items": []}
    items = obj.get("items") or []
    trimmed = []
    for it in items:
        core = it.get("properties", {}).get("coreNOTAMData", {}).get("notam", {})
        trimmed.append({
            "id":           core.get("id"),
            "number":       core.get("number"),
            "type":         core.get("type"),
            "classification": core.get("classification"),
            "series":       core.get("series"),
            "location":     core.get("location"),
            "effective_start": core.get("effectiveStart"),
            "effective_end":   core.get("effectiveEnd"),
            "text":         core.get("text"),
        })
    return trimmed


def pull() -> dict:
    cid = os.environ.get("FAA_CLIENT_ID", "").strip()
    csec = os.environ.get("FAA_CLIENT_SECRET", "").strip()
    if not cid or not csec:
        raise RuntimeError(
            "FAA_CLIENT_ID / FAA_CLIENT_SECRET env vars missing — register free at "
            "https://api.faa.gov/s/ and add as GitHub Actions secrets."
        )

    t0 = time.time()
    per_airport = {}
    errors = {}
    total = 0
    for icao in TIER1_ICAO:
        try:
            items = _fetch_airport(icao, cid, csec)
            per_airport[icao] = {
                "airport_name": BY_ICAO.get(icao, {}).get("name"),
                "notams": items,
            }
            total += len(items)
        except Exception as e:  # noqa: BLE001
            errors[icao] = f"{type(e).__name__}: {e}"

    data = {
        "coverage_note": "Tier-1 hubs only; tier-2 airports queryable on-demand from app.",
        "airport_count": len(TIER1_ICAO),
        "per_airport": per_airport,
        "errors": errors,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, total, time.time() - t0)
