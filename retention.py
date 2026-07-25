"""Retention policy: keep 90 days full · roll older into monthly summaries.

Runs at the end of every nightly cron (see run_all.py). For each source:
    * Any data/YYYY-MM-DD/<sid>.json older than 90 days is archived into
      data/rollup/YYYY-MM/<sid>.json as a list of {date, rows, bytes, summary}
      one entry per original file; the original file is then deleted.
    * Files younger than 90 days stay untouched.

Reads all snapshot files stdlib-only. Idempotent — safe to run multiple times.
"""

import json, pathlib, shutil
from datetime import datetime, timedelta, timezone

RETAIN_DAYS = 90


def cutoff_date() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=RETAIN_DAYS)


def enumerate_dated_dirs(data_root: pathlib.Path):
    for d in sorted(data_root.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        # Match YYYY-MM-DD directories only
        try:
            dt = datetime.strptime(name, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        yield dt, d


def summarise(payload: dict) -> dict:
    """Reduce a full snapshot to the fields worth keeping in the rollup."""
    return {
        "source_id": payload.get("source_id"),
        "pulled_at": payload.get("pulled_at"),
        "rows": payload.get("rows"),
        "endpoint": (payload.get("provenance") or {}).get("endpoint"),
        # Keep first + last item summaries where available so we can still cite the day
        "first_item": (
            (payload.get("data") or {}).get("items", [{}])[0]
            or (payload.get("data") or {}).get("events", [{}])[0]
            or (payload.get("data") or {}).get("metar", [{}])[0]
            or None
        ),
    }


def rollup(data_root: pathlib.Path) -> dict:
    """Roll snapshots older than cutoff into monthly rollup files. Return stats."""
    cutoff = cutoff_date()
    rollup_root = data_root / "rollup"
    rollup_root.mkdir(parents=True, exist_ok=True)

    archived_files = 0
    archived_bytes = 0
    per_source = {}

    for dt, dated_dir in enumerate_dated_dirs(data_root):
        if dt >= cutoff:
            continue
        month_key = dt.strftime("%Y-%m")
        month_dir = rollup_root / month_key
        month_dir.mkdir(parents=True, exist_ok=True)
        for f in dated_dir.glob("*.json"):
            try:
                content = json.loads(f.read_text())
            except Exception:
                content = {"source_id": f.stem, "pulled_at": dt.isoformat(), "rows": 0}
            sid = content.get("source_id") or f.stem
            rollup_path = month_dir / f"{sid}.json"
            existing = []
            if rollup_path.exists():
                try:
                    existing = json.loads(rollup_path.read_text())
                    if not isinstance(existing, list):
                        existing = [existing]
                except Exception:
                    existing = []
            entry = summarise(content)
            entry["date"] = dt.strftime("%Y-%m-%d")
            entry["archived_bytes"] = f.stat().st_size
            existing.append(entry)
            rollup_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
            per_source[sid] = per_source.get(sid, 0) + 1
            archived_files += 1
            archived_bytes += entry["archived_bytes"]
            f.unlink()
        # Remove now-empty dated directory
        try:
            dated_dir.rmdir()
        except OSError:
            pass  # not empty (unexpected extra files) — leave in place

    return {
        "cutoff": cutoff.strftime("%Y-%m-%d"),
        "archived_files": archived_files,
        "archived_bytes": archived_bytes,
        "per_source": per_source,
    }


if __name__ == "__main__":
    import sys
    root = pathlib.Path(__file__).parent / "data"
    stats = rollup(root)
    print(json.dumps(stats, indent=2))
