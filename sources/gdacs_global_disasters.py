"""Source: GDACS — Global Disaster Alert & Coordination System (UN + EU).

Free JSON feed of active global disasters — earthquakes, floods, tropical storms,
tsunamis, volcanoes, droughts. Every event carries a severity alert level
(Green / Orange / Red) computed by GDACS' own scoring model. Ideal for cases
where the disruption cause is a wider-region natural event.

No auth, no rate limit. Official inter-agency source.
"""

import json, time
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from pull_common import http_get, wrap

ID = "gdacs-global-disasters"
ENDPOINT = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS?fromdate=&todate=&alertlevel=Green;Orange;Red&eventlist=EQ;TC;FL;VO;DR;WF"
AUTH_MODE = "none"


def pull() -> dict:
    t0 = time.time()
    raw = http_get(ENDPOINT, timeout=45)
    obj = json.loads(raw) if raw.strip() else {"features": []}
    features = obj.get("features") or []
    events = []
    for f in features:
        props = f.get("properties", {}) or {}
        geom = f.get("geometry", {}) or {}
        coords = geom.get("coordinates") or [None, None]
        events.append({
            "id":            props.get("eventid"),
            "type":          props.get("eventtype"),
            "type_name":     props.get("eventname"),
            "name":          props.get("name"),
            "country":       props.get("country"),
            "iso3":          props.get("iso3"),
            "alert_level":   props.get("alertlevel"),
            "alert_score":   props.get("alertscore"),
            "severity":      props.get("severitydata", {}).get("severity") if isinstance(props.get("severitydata"), dict) else None,
            "population":    props.get("population", {}).get("population") if isinstance(props.get("population"), dict) else None,
            "from_date":     props.get("fromdate"),
            "to_date":       props.get("todate"),
            "url":           props.get("url", {}).get("report") if isinstance(props.get("url"), dict) else None,
            "lon":           coords[0] if coords else None,
            "lat":           coords[1] if coords else None,
        })
    by_type = {}
    by_alert = {}
    for e in events:
        by_type[e["type"] or "unknown"] = by_type.get(e["type"] or "unknown", 0) + 1
        by_alert[e["alert_level"] or "unknown"] = by_alert.get(e["alert_level"] or "unknown", 0) + 1
    data = {
        "endpoint": ENDPOINT,
        "events": events,
        "by_type": by_type,
        "by_alert_level": by_alert,
    }
    return wrap(ID, ENDPOINT, AUTH_MODE, data, len(events), time.time() - t0)
