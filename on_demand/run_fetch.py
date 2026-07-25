"""On-demand fetch runner.

Invoked by .github/workflows/on-demand-fetch.yml on workflow_dispatch.
Takes case context via CLI args + env, invokes each requested on-demand
source module, writes results to data/case-fetches/<case_ref>/, updates
per-case manifest, appends to global audit log.

Per-source failure isolation same as daily runner — one failing source
does not abort the run.
"""

import argparse, csv, importlib, json, os, pathlib, sys, traceback
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'sources' / 'on_demand'))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

ROOT = pathlib.Path(__file__).parent.parent
CASE_FETCHES = ROOT / "data" / "case-fetches"
AUDIT = CASE_FETCHES / "audit.csv"

# Registry — on-demand source modules ready to invoke
ON_DEMAND_SOURCES = {
    "aviationweather-metar-taf-on-demand": "aviationweather_metar_taf_on_demand",
    # Phase B additions plug in here:
    # "faa-notams-on-demand":          "faa_notams_on_demand",
    # "opensky-flight-tracks-on-demand": "opensky_flight_tracks_on_demand",
    # "gdacs-global-disasters-on-demand": "gdacs_global_disasters_on_demand",
}


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_one(sid: str, context: dict, case_dir: pathlib.Path) -> dict:
    module_name = ON_DEMAND_SOURCES.get(sid)
    result = {"id": sid, "status": "planned", "rows": 0, "bytes": 0, "path": None, "error": ""}
    if not module_name:
        result["status"] = "unknown"
        result["error"] = f"Source {sid} not in ON_DEMAND_SOURCES registry"
        return result
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        result["status"] = "failed"
        result["error"] = f"Module import failed: {e}"
        return result
    try:
        envelope = mod.fetch(context)
        # Serialise
        body = json.dumps(envelope, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        out_path = case_dir / f"{sid}.json"
        # If a targeted fetch already exists for this source, roll it with -N suffix
        n = 1
        while out_path.exists():
            out_path = case_dir / f"{sid}-{n}.json"
            n += 1
        out_path.write_bytes(body)
        result["status"] = "live"
        result["rows"] = envelope.get("rows", 0)
        result["bytes"] = len(body)
        result["path"] = str(out_path.relative_to(ROOT))
    except Exception as e:  # noqa: BLE001
        result["status"] = "failed"
        result["error"] = f"{type(e).__name__}: {e}"
        print(f"FAILED {sid}: {result['error']}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    return result


def write_case_manifest(case_dir: pathlib.Path, context: dict, results: list) -> None:
    manifest_path = case_dir / "manifest.json"
    existing = []
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    existing.append({
        "run_utc":       utc_iso(),
        "context":       context,
        "results":       results,
    })
    manifest_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))


def append_audit(context: dict, results: list) -> None:
    CASE_FETCHES.mkdir(parents=True, exist_ok=True)
    exists = AUDIT.exists()
    with AUDIT.open("a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["utc_timestamp", "case_ref", "triggered_by", "sources", "endpoints_hit", "total_rows", "total_bytes", "workflow_run_url"])
        now = utc_iso()
        sources = ",".join(r["id"] for r in results)
        endpoints = ",".join(sorted(set(
            r.get("path", "").split("/")[-1] for r in results if r.get("path")
        )))
        total_rows = sum(r.get("rows", 0) for r in results)
        total_bytes = sum(r.get("bytes", 0) for r in results)
        w.writerow([
            now, context.get("case_ref"), context.get("triggered_by") or "unknown",
            sources, endpoints, total_rows, total_bytes,
            context.get("workflow_run_url") or "",
        ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-ref",   required=True)
    ap.add_argument("--date-iso",   required=True)
    ap.add_argument("--airports",   required=True, help="Comma-separated ICAO codes")
    ap.add_argument("--flight-num", default="")
    ap.add_argument("--reg",        default="")
    ap.add_argument("--sources",    default="",
                    help="Comma-separated source IDs; default = all in ON_DEMAND_SOURCES")
    ap.add_argument("--window-hours-before", type=int, default=12)
    ap.add_argument("--window-hours-after",  type=int, default=6)
    ap.add_argument("--triggered-by", default=os.environ.get("GITHUB_ACTOR", "cli"))
    ap.add_argument("--workflow-run-url", default=os.environ.get("GITHUB_RUN_URL", ""))
    args = ap.parse_args()

    context = {
        "case_ref":            args.case_ref,
        "date_iso":            args.date_iso,
        "airports":            [a.strip().upper() for a in args.airports.split(",") if a.strip()],
        "flight_num":          args.flight_num,
        "reg":                 args.reg,
        "window_hours_before": args.window_hours_before,
        "window_hours_after":  args.window_hours_after,
        "triggered_by":        args.triggered_by,
        "workflow_run_url":    args.workflow_run_url,
    }
    requested = [s.strip() for s in args.sources.split(",") if s.strip()] or list(ON_DEMAND_SOURCES.keys())

    case_dir = CASE_FETCHES / args.case_ref
    case_dir.mkdir(parents=True, exist_ok=True)

    results = [run_one(sid, context, case_dir) for sid in requested]
    write_case_manifest(case_dir, context, results)
    append_audit(context, results)

    print(f"\n== On-demand fetch: {args.case_ref} · {len(results)} sources ==")
    for r in results:
        marker = "OK  " if r["status"] == "live" else "FAIL" if r["status"] == "failed" else "SKIP"
        print(f"  {marker}  {r['id']:44s}  {r['rows']:>6} rows  {r['bytes']:>8} bytes  → {r['path'] or '-'}")

    failed = [r for r in results if r["status"] == "failed"]
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
