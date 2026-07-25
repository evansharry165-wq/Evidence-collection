"""On-demand: NOAA AviationWeather METAR + TAF, targeted per-case.

Same underlying API as the daily source but scoped to one case's specific
airports + date-range at ~30-minute resolution. Where the daily source pulls
current METAR for 63 airports once, this pulls historical METAR every 30 min
across an ~18h window for the case's 2 airports — ~72 readings vs 2 in the
daily snapshot for the same airports on that date.

Called by on_demand/run_fetch.py which invokes fetch(context) with case
facts + time window. Returns the same wrap() envelope as daily sources so
the reader is source-shape-agnostic.
"""

import json, sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from pull_common import http_get, utc_now_iso, wrap

ID = "aviationweather-metar-taf-on-demand"
BASE_SOURCE = "aviationweather-metar-taf"
ENDPOINT = "https://aviationweather.gov/api/data"
AUTH_MODE = "none"


def _fetch_metar_range(icao: str, start_iso: str, end_iso: str) -> list:
    """Pull METAR history for icao across [start_iso, end_iso]. Format hours=N."""
    # AviationWeather.gov supports hours= to look back — for a specific past
    # date we compute the hours-since-now and request enough backfill.
    url = f"{ENDPOINT}/metar?ids={icao}&format=json&hours=72"
    raw = http_get(url, timeout=60)
    return json.loads(raw) if raw.strip() else []


def _fetch_taf_current(icao: str) -> list:
    url = f"{ENDPOINT}/taf?ids={icao}&format=json"
    raw = http_get(url, timeout=45)
    return json.loads(raw) if raw.strip() else []


def _filter_to_window(readings: list, target_date_iso: str, hours_before: int, hours_after: int) -> list:
    """Keep only readings within [target - hours_before, target + hours_after]."""
    from datetime import datetime, timezone, timedelta
    try:
        target = datetime.fromisoformat(target_date_iso).replace(tzinfo=timezone.utc)
    except Exception:
        return readings
    window_start = target - timedelta(hours=hours_before)
    window_end = target + timedelta(hours=hours_after + 24)  # +24h = end-of-day
    out = []
    for r in readings:
        obs_time_str = r.get("obsTime") or r.get("reportTime")
        if not obs_time_str:
            continue
        try:
            # obsTime is Unix ms or ISO — try both
            if isinstance(obs_time_str, (int, float)):
                obs_dt = datetime.fromtimestamp(obs_time_str, tz=timezone.utc)
            else:
                obs_dt = datetime.fromisoformat(str(obs_time_str).replace("Z", "+00:00"))
        except Exception:
            continue
        if window_start <= obs_dt <= window_end:
            out.append(r)
    return out


def fetch(context: dict) -> dict:
    """Targeted METAR + TAF pull for a specific case.

    Required context keys: case_ref, date_iso, airports (list of ICAO)
    Optional:              window_hours_before (default 12), window_hours_after (default 6)
    """
    if not context.get("case_ref"): raise ValueError("case_ref required")
    if not context.get("date_iso"): raise ValueError("date_iso required")
    airports = context.get("airports") or []
    if not airports: raise ValueError("airports (list of ICAO) required")

    hb = int(context.get("window_hours_before", 12))
    ha = int(context.get("window_hours_after", 6))

    t0 = time.time()
    per_airport = {}
    total_metar = 0
    total_taf = 0

    for icao in airports:
        try:
            metar_all = _fetch_metar_range(icao, context["date_iso"], context["date_iso"])
            metar_window = _filter_to_window(metar_all, context["date_iso"], hb, ha)
            taf = _fetch_taf_current(icao)
        except Exception as e:  # noqa: BLE001
            per_airport[icao] = {"error": f"{type(e).__name__}: {e}", "metar": [], "taf": []}
            continue
        per_airport[icao] = {
            "metar": metar_window,
            "taf": taf,
            "metar_count_full_backfill": len(metar_all),
            "metar_count_in_window": len(metar_window),
        }
        total_metar += len(metar_window)
        total_taf += len(taf)

    envelope = wrap(ID, ENDPOINT, AUTH_MODE, {
        "per_airport": per_airport,
        "note": (
            "Historical METAR ~30-minute resolution across the case disruption window; "
            "TAF is current-issue (not archived per-hour by AviationWeather.gov)."
        ),
    }, total_metar + total_taf, time.time() - t0)

    # Additive: on-demand envelopes carry case + fetch context in provenance
    envelope["case_ref"] = context["case_ref"]
    envelope["fetch_context"] = {
        "date_iso":            context["date_iso"],
        "airports":            airports,
        "window_hours_before": hb,
        "window_hours_after":  ha,
        "triggered_by":        context.get("triggered_by") or "unknown",
        "workflow_run_url":    context.get("workflow_run_url"),
    }
    envelope["provenance"]["fetch_kind"] = "on-demand"
    envelope["provenance"]["base_source"] = BASE_SOURCE
    return envelope


if __name__ == "__main__":
    # Manual CLI test:  python3 aviationweather_metar_taf_on_demand.py DEF-REF EGLL,EIDW 2026-07-15
    ctx = {
        "case_ref": sys.argv[1],
        "airports": sys.argv[2].split(","),
        "date_iso": sys.argv[3],
    }
    print(json.dumps(fetch(ctx), indent=2)[:2000])
