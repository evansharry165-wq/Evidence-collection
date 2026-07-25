"""Source: OpenSky Network — current airborne state vectors.

Anonymous access: ~400 credits/day. Pulls /states/all snapshot as a daily heartbeat.
Full historical per-flight tracks require authenticated access (Layer 2 upgrade).
For now this proves the endpoint is reachable and captures a nightly snapshot of every
airborne aircraft over Europe that could be replayed later.
"""

import json, time
from pull_common import http_get, wrap

ID = "opensky-flight-tracks"
ENDPOINT = "https://opensky-network.org/api/states/all"
AUTH_MODE = "none (anon-limited)"

# European bounding box — cuts out ~85% of global traffic to stay within anon credits
BBOX = {"lamin": 35.0, "lamax": 60.0, "lomin": -10.0, "lomax": 30.0}


def pull() -> dict:
    t0 = time.time()
    url = f"{ENDPOINT}?lamin={BBOX['lamin']}&lomin={BBOX['lomin']}&lamax={BBOX['lamax']}&lomax={BBOX['lomax']}"
    raw = http_get(url, timeout=45)
    obj = json.loads(raw) if raw.strip() else {"time": None, "states": []}
    states = obj.get("states") or []
    # Trim: keep only the columns we actually need for evidence use
    # Original: [icao24, callsign, origin_country, time_position, last_contact, longitude, latitude,
    #           baro_altitude, on_ground, velocity, true_track, vertical_rate, sensors, geo_altitude,
    #           squawk, spi, position_source]
    trimmed = [
        {
            "icao24": s[0],
            "callsign": (s[1] or "").strip() or None,
            "country": s[2],
            "lon": s[5],
            "lat": s[6],
            "baro_alt_m": s[7],
            "on_ground": s[8],
            "vel_ms": s[9],
            "track_deg": s[10],
            "vr_ms": s[11],
        }
        for s in states
    ]
    data = {
        "snapshot_time_unix": obj.get("time"),
        "bbox": BBOX,
        "note": "Anonymous OpenSky snapshot — historical per-flight tracks require Layer-2 auth.",
        "states": trimmed,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(trimmed), time.time() - t0)


if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from pull_common import write_snapshot
    p = pull()
    d, sz = write_snapshot(p, pathlib.Path(__file__).parent.parent)
    print(f"OK — {p['rows']} states, {sz} bytes → {d}")
