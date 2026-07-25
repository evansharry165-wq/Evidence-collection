"""Shared plumbing for every source pull.

Each source module implements:
    ID = "source-id"
    def pull() -> dict   # normalised payload; will be JSON-serialised

Common contract:
    - HTTP calls use urllib (stdlib only).
    - Timeouts default to 30s.
    - Any exception raised is caught by the runner and logged as failure for that source.
    - Return shape is always a dict — must include keys:
        source_id  · str
        pulled_at  · ISO-8601 UTC
        rows       · int (payload item count, or 0 if snapshot-style)
        data       · payload (whatever the source produces)
        provenance · dict with endpoint + auth-mode + fetch-duration-seconds
"""

import json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url: str, headers: dict | None = None, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "DefendAble-EvidenceCollection/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def wrap(source_id: str, endpoint: str, auth_mode: str, data, rows: int, fetch_seconds: float) -> dict:
    return {
        "source_id": source_id,
        "pulled_at": utc_now_iso(),
        "rows": rows,
        "data": data,
        "provenance": {
            "endpoint": endpoint,
            "auth_mode": auth_mode,
            "fetch_duration_seconds": round(fetch_seconds, 2),
            "runner": "github-actions",
        },
    }


def write_snapshot(payload: dict, root: Path) -> tuple[Path, int]:
    """Write payload to data/YYYY-MM-DD/<source>.json and to data/latest/<source>.json.

    Returns (path_of_dated_file, bytes_written)."""
    date_str = payload["pulled_at"][:10]
    dated_dir = root / "data" / date_str
    latest_dir = root / "data" / "latest"
    dated_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    dated_path = dated_dir / f"{payload['source_id']}.json"
    latest_path = latest_dir / f"{payload['source_id']}.json"
    dated_path.write_bytes(body)
    latest_path.write_bytes(body)
    return dated_path, len(body)
