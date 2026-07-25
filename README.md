# evidence-collection

DefendAble's evidence-collection layer. Pulls free public data sources nightly and commits daily JSON snapshots to this repo. The DefendAble app (`261Claims` repo) reads those snapshots read-only via `raw.githubusercontent.com`.

## Why a separate repo

Keeps evidence pulls out of `261Claims`' commit history and lets us set different retention rules for the data layer. The app never calls external APIs directly — everything comes from committed snapshots so cases are reproducible.

## How it works

Nightly at 03:00 UTC, `.github/workflows/nightly-pull.yml` fires and runs `run_all.py`. That iterates every source declared in `manifest_source_of_truth.py`, calls its module in `sources/`, writes the payload to `data/YYYY-MM-DD/<source-id>.json` and `data/latest/<source-id>.json`, then updates `data/manifest.xlsx` in place. Sources are isolated — one failing does not stop the others.

Failures surface via GitHub Actions email notification to the account owner (`harryevans15@icloud.com`). Confirm the notification is on at https://github.com/settings/notifications under Actions.

## File layout

```
manifest_source_of_truth.py         source-of-truth Python list of every source
pull_common.py                      shared HTTP + wrap + write helpers
run_all.py                          nightly runner (invoked by GitHub Actions)
sources/                            one Python module per source; exposes ID + pull()
    aviationweather_metar_taf.py
    ...
data/
    manifest.xlsx                   live register — updated in place by the runner
    manifest_log.csv                append-only audit log of every run
    YYYY-MM-DD/                     dated snapshot folder — one JSON per source per day
    latest/                         mirror of newest snapshots — always the "current" copy
.github/workflows/nightly-pull.yml  cron + commit workflow
```

## Live URLs

Every source, once live, is readable at:
```
https://raw.githubusercontent.com/evansharry165-wq/evidence-collection/main/data/latest/<source-id>.json
```
That URL is what `defendable_evidence_reader.js` in the `261Claims` repo consumes.

## Adding a new source

1. Add an entry to `SOURCES` in `manifest_source_of_truth.py`.
2. Create `sources/<id_with_underscores>.py` exposing `ID = "..."` and `def pull() -> dict`.
3. Use `pull_common.wrap()` to shape the return value.
4. Rebuild `data/manifest.xlsx` locally to add the row: `python -c "from data.build_manifest import build; build()"` (script forthcoming).
5. Commit and push. The next cron run will exercise it.

## Manual run

Any collaborator can trigger the pipeline on demand from the Actions tab (workflow_dispatch button on the "Nightly pull" workflow).

## Layers

- **L1** — free, no auth or trivial auth. All rows in the current manifest.
- **L2** — paid single-fee (~<$500/yr): OPSGROUP, AVWX freemium, etc. Added after L1 is stable.
- **L3** — usage-billed: AeroDataBox, Twilio delivery metadata. Added last.

## License

MIT. Data-source snapshots retain their original licenses — see each source's provider page.
