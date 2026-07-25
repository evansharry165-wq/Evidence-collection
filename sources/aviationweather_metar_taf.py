"""Source: NOAA AviationWeather.gov METAR + TAF.

Free, no auth. Pulls current METAR and TAF for the configured airport list.
This is the Ogimet replacement — same data, official US-government source, no rate limit.
"""

import json, time
from pull_common import http_get, wrap, utc_now_iso
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from airports import ICAO_LIST

ID = "aviationweather-metar-taf"
ENDPOINT = "https://aviationweather.gov/api/data"
AUTH_MODE = "none"


def pull() -> dict:
    airports = ",".join(ICAO_LIST)
    t0 = time.time()

    metar_url = f"{ENDPOINT}/metar?ids={airports}&format=json&hours=6"
    taf_url = f"{ENDPOINT}/taf?ids={airports}&format=json"

    metar_raw = http_get(metar_url)
    taf_raw = http_get(taf_url)

    metar = json.loads(metar_raw) if metar_raw.strip() else []
    taf = json.loads(taf_raw) if taf_raw.strip() else []

    data = {
        "airports_requested": ICAO_LIST,
        "metar": metar,
        "taf": taf,
    }
    rows = len(metar) + len(taf)
    fetch_seconds = time.time() - t0
    return wrap(ID, ENDPOINT, AUTH_MODE, data, rows, fetch_seconds)


if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from pull_common import write_snapshot
    payload = pull()
    dated, size = write_snapshot(payload, pathlib.Path(__file__).parent.parent)
    print(f"OK — {payload['rows']} rows, {size} bytes → {dated}")
