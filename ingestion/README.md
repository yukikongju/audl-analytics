# Ingestion

This module fetches game and season data from the [UFA website](https://www.watchufa.com/league/schedule)
and processes it into analytics-ready tables.

## Architecture

The pipeline runs in two stages over a Hive-partitioned data lake:

1. **Extract** (`scripts/*.sh` + `src/extract_*.py`) — fetch raw JSON from the UFA backend,
   strip the `{object, data}` envelope, and write one file per entity/game to
   `$AUDL_SOURCE_DIR`.
2. **Process** (`src/main.py`, the `audl-pipeline` entrypoint) — read a game's raw
   `game_events` + `game_stats`, build one shared event **timeline** (`src/timeline.py`),
   and emit five `ext_*` tables to `$AUDL_PROCESSED_DIR`.

```
$AUDL_SOURCE_DIR/                          $AUDL_PROCESSED_DIR/
  games/season=YYYY/                         ext_throws/season=YYYY/month=MM/<gameID>.parquet
  players/season=YYYY/                       ext_pulls/...
  teams/season=YYYY/                         ext_point_lineups/...
  game_stats/season=YYYY/month=MM/           ext_blocks/...
  game_events/season=YYYY/month=MM/          ext_games/...
  player_game_stats/season=YYYY/month=MM/
```

Both roots are read from the environment (`AUDL_SOURCE_DIR`, `AUDL_PROCESSED_DIR`; see
`pipeline_utils.py`), set via `.env` + [direnv](https://direnv.net/) (`.envrc`), or passed
explicitly with `--source-dir` / `--processed-dir`.

## How it works

All data comes from `https://www.backend.ufastats.com`. There are 6 endpoints:

| Endpoint | Returns | Scope | Envelope |
|---|---|---|---|
| `/api/v1/games?date={year}` | season schedule | per season | wrapped (`data`) |
| `/api/v1/players?years={year}` | player roster | per season | wrapped |
| `/api/v1/teams?years={year}` | team metadata | per season | wrapped |
| `/api/v1/playerGameStats?gameID={id}` | per-player box score | per game | wrapped |
| `/api/v1/gameEvents?gameID={id}` | home/away event streams | per game | wrapped |
| `/stats-pages/game/{id}` | full game-stats payload (`game`, `tsgHome/Away`, rosters) | per game | **not wrapped** |

> **Envelope gotcha.** The `api/v1` endpoints wrap their payload in
> `{"object": ..., "data": ...}`. Extraction strips this so downstream code sees only the
> inner data: the Python extractors take `response["data"]`, and the curl path strips it
> with `jq '.data'` — **except** `/stats-pages/game`, which is unwrapped and saved as-is.
> As a safety net, the source loaders call `unwrap()` (`pipeline_utils.py`), so a stray
> envelope on disk won't break processing.

The two stages map to these entrypoints (`pyproject.toml`):

1. **Extract** → `audl-extract-seasonal` (players/teams/games) and `audl-extract-weekly`
   (per-game data for a date window).
2. **Process** → `audl-pipeline` (raw game data → five `ext_*` tables).

### Output tables

| Table | Grain | Transform |
|---|---|---|
| `ext_throws` | one row per throw attempt (completion, yards, huck/dump/swing, block/assist links) | `transform_throws.py` |
| `ext_pulls` | one row per pull / re-pull (puller, hangtime, OOB) | `transform_pulls.py` |
| `ext_point_lineups` | one row per team-point stint (7-player lineup, O/D line, seconds) | `transform_point_lineups.py` |
| `ext_blocks` | one row per defensive block (defender, link to the throw it broke up) | `transform_blocks.py` |
| `ext_games` | two rows per game (home/away `tsg` summary + final score) | `transform_games.py` |

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) — runs everything.
- [`jq`](https://jqlang.github.io/jq/) — used by `setup.sh` to strip the response envelope
  on the curl path.
- `gcloud` — only for the daily GCS backup (`daily_extraction.sh`).
- A `.env` defining `AUDL_SOURCE_DIR` and `AUDL_PROCESSED_DIR` (loaded via `.envrc`), or
  pass `--source-dir` / `--processed-dir` on each command.

## Usage

Extract a season's reference data, then a per-game date window:

```bash
uv run audl-extract-seasonal --year 2026
uv run audl-extract-weekly --year 2026 --start-date 2026-07-03 --end-date 2026-07-03
```

Process one game into the five `ext_*` tables (`--format` is `parquet` or `json`, default
`parquet`; reads and writes use the same format):

```bash
uv run audl-pipeline 2026-07-03-CHI-MIN \
  --source-dir "$AUDL_SOURCE_DIR" --processed-dir "$AUDL_PROCESSED_DIR" --format json
```

## Running the tests

Some stats aren't given by the API and have to be reconstructed from the event streams
(player throws, lineups, blocks). The tests verify that reconstruction: gameEvents-derived
stats are exact by construction and are reconciled against the `tsg` summary
(`test_pipeline.py`) and, when the network is reachable, against the live `playerGameStats`
API (`test_player_game_stats.py`). A few fields are best-effort (`secondsPlayed`, the
`*Opportunit*` counts) and are never asserted exact.

```bash
cd ingestion
uv run pytest -v
```

## Ingestion Setup

**Backfilling** — loops seasons `2020..current`, extracts every completed game (curl +
`jq`), and processes each with `audl-pipeline` into `~/.Data/ufa/{extraction,processed}`:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Daily cron job** — `.github/workflows/daily_extraction.yml` runs at `0 0 * * *` (UTC),
gated on the `RUN_DAILY` repo variable. It runs `scripts/daily_extraction.sh`, which finds
the last backfilled date in the GCS bucket, fetches newly-`Final` games, and uploads the
**raw** JSON to `gs://ds-ufa-backups/season=YYYY/date=YYYY-MM-DD/game_id=<id>/`. This path
only backs up raw data — it does **not** run `audl-pipeline`.

## `scripts/` reference

| Script | Purpose |
|---|---|
| `setup.sh` | Full local backfill (extract + process) — the main entrypoint. |
| `daily_extraction.sh` | Daily raw-JSON backup to GCS (run by GitHub Actions). |
| `batch_process.sh` | Re-process a hardcoded list of games with `audl-pipeline`. |
| `downloads.sh`, `process.sh`, `testings.sh` | Ad-hoc dev helpers, not part of the main flow. |
