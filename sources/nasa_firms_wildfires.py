"""Source: NASA FIRMS — Fire Information for Resource Management System.

Active wildfire hotspots from VIIRS satellites, last 24h, for European bounding box.
Requires a free MAP_KEY: register at https://firms.modaps.eosdis.nasa.gov/api/map_key/
Set as GitHub Actions secret FIRMS_MAP_KEY. Module fails cleanly with a diagnostic
message if the key is missing so the runner marks it "failed" with an actionable note.
"""

import csv, io, os, time
from pull_common import http_get, wrap

ID = "nasa-firms-wildfires"
ENDPOINT = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
AUTH_MODE = "MAP_KEY (env FIRMS_MAP_KEY)"

# Europe + N Africa + W Asia — regions where a fire could plausibly disrupt an EU/UK flight
AREA = "-10,30,45,60"  # west,south,east,north  (lon-lon-lat-lat)


def pull() -> dict:
    key = os.environ.get("FIRMS_MAP_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "FIRMS_MAP_KEY env var missing — register free key at "
            "https://firms.modaps.eosdis.nasa.gov/api/map_key/ and add to GitHub Actions secrets."
        )
    t0 = time.time()
    url = f"{ENDPOINT}/{key}/VIIRS_SNPP_NRT/{AREA}/1"
    raw = http_get(url, timeout=45)
    reader = csv.DictReader(io.StringIO(raw))
    hotspots = [
        {
            "lat": float(r.get("latitude", 0)),
            "lon": float(r.get("longitude", 0)),
            "brightness_k": float(r.get("bright_ti4", 0) or 0),
            "acq_date": r.get("acq_date"),
            "acq_time": r.get("acq_time"),
            "confidence": r.get("confidence"),
            "frp_mw": float(r.get("frp", 0) or 0),
            "daynight": r.get("daynight"),
        }
        for r in reader
    ]
    data = {
        "product": "VIIRS_SNPP_NRT",
        "area_bbox_wsen": AREA,
        "window_hours": 24,
        "hotspots": hotspots,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(hotspots), time.time() - t0)
