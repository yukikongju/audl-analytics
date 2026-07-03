"""Reconstruct per-player game stats from the staging tables (stg_throws / stg_pulls /
stg_point_lineups), matching the UFA/AUDL ``playerGameStats`` API
(``GET api/v1/playerGameStats?gameID=<id>``).

Because the staging tables are already keyed by external ``playerID`` with clean per-throw
flags and exact coordinates, this is a group-by aggregation -- not the possession state
machine the tsg reconstruction in ``playground/player_game_stats.py`` needed.

Field scope (see the plan): the ~24 count/yardage/point fields are computed to match the API
exactly; ``secondsPlayed`` is best-effort (inherits stg_point_lineups' partial clock); the
four ``*Opportunit*`` fields use a heuristic red-zone-possession model. Rows are keyed by
``playerID`` + team slug -- names/jersey (the API's nested ``player`` object) are out of scope.

Run ``uv run python -m player_game_stats <game_id> [--local]`` to print a per-field accuracy
table against the live API.
"""

from collections import defaultdict

from constants import REDZONE_Y
from pipeline_utils import BASE_URL, http_get_json

# Output field order (flat), matching the user's sample API row.
_COUNT_FIELDS = [
    "assists", "goals", "hockeyAssists", "completions", "throwAttempts", "throwaways",
    "stalls", "callahansThrown", "yardsReceived", "yardsThrown", "hucksAttempted",
    "hucksCompleted", "catches", "drops", "blocks", "callahans", "pulls", "obPulls",
    "recordedPulls", "recordedPullsHangtime", "oPointsPlayed", "oPointsScored",
    "dPointsPlayed", "dPointsScored", "secondsPlayed", "oOpportunities",
    "oOpportunityScores", "dOpportunities", "dOpportunityStops",
]

# The count fields we compute (the ~24 non-opportunity, non-seconds stats).
CORE_FIELDS = [
    "assists", "goals", "hockeyAssists", "completions", "throwAttempts", "throwaways",
    "stalls", "callahansThrown", "yardsReceived", "yardsThrown", "hucksAttempted",
    "hucksCompleted", "catches", "drops", "blocks", "callahans", "pulls", "obPulls",
    "recordedPulls", "recordedPullsHangtime", "oPointsPlayed", "oPointsScored",
    "dPointsPlayed", "dPointsScored",
]

# Verified 41/41 vs the live API (MTL-PIT): pure event-derived stats. Asserted exact.
# Notes on ones that took a fix:
#   goals/callahans -- attach the callahan scorer to the CALLAHAN_THEIRS throw (the type-23
#     event carries no defender; the scorer is on the type-12 CALLAHAN_OURS in the other stream).
#   hucksAttempted -- a dropped huck (type-20) still counts as an attempt (is_huck set on drops).
#   pulls -- an offsides re-pull (type-9 OFFSIDES_OURS) counts as a pull.
#   blocks -- a block (type-11) shows up in the other stream as the turnover it forced, a
#     throwaway OR a drop; attaching to both (see timeline) makes blocks exact.
EXACT_FIELDS = [
    "assists", "goals", "hockeyAssists", "completions", "throwAttempts", "throwaways",
    "stalls", "callahansThrown", "callahans", "blocks", "yardsReceived", "yardsThrown",
    "hucksCompleted", "hucksAttempted", "catches", "drops", "pulls", "obPulls",
    "recordedPulls", "recordedPullsHangtime",
]
# ±1 tolerated (float staging yards summed then rounded vs the API's integers).
YARD_FIELDS = {"yardsReceived", "yardsThrown"}

# Correct in aggregate but inherit a known staging limitation at the per-player level, so
# reported (not asserted exact):
#   o/dPointsPlayed/Scored -- mid-point-timeout sub stints + point-boundary segmentation in
#     stg_point_lineups don't match the API's point model (each player's O+D total is exact,
#     but the O/D split is off for players on the affected points).
STAGING_LIMITED_FIELDS = [
    "oPointsPlayed", "oPointsScored", "dPointsPlayed", "dPointsScored",
]
# Best-effort clock / heuristic opportunity model. Reported, never asserted.
INFORMATIONAL_FIELDS = [
    "secondsPlayed", "oOpportunities", "oOpportunityScores", "dOpportunities",
    "dOpportunityStops",
]


def _blank():
    d = {f: 0 for f in _COUNT_FIELDS}
    for f in ("oOpportunities", "oOpportunityScores", "dOpportunities", "dOpportunityStops"):
        d[f] = 0
    d["_hangtime_ms"] = 0.0  # accumulator; folded into recordedPullsHangtime at the end
    return d


def build_player_game_stats(throws, pulls, lineups, team_slug_by_id=None, game_id=None):
    """Aggregate the three staging tables into one row per player.

    ``team_slug_by_id`` maps numeric team_season_id -> slug (built from stg_games); when
    omitted ``teamID`` falls back to the numeric id. ``game_id`` is unused in the row (the
    API entry carries none) but accepted for symmetry with the other transforms.
    """
    stats = defaultdict(_blank)
    team_of = {}          # player_id -> team_season_id (authoritative: lineups)

    def bump(pid, field, by=1):
        if pid is not None:
            stats[pid][field] += by

    # --- throws --------------------------------------------------------------------------
    for r in throws:
        thr, rec, dfn = r["thrower_id"], r["receiver_id"], r["defender_id"]
        if r["is_completion"]:
            bump(thr, "completions")
            bump(rec, "catches")
            bump(thr, "yardsThrown", r["yards_thrown"] or 0)
            bump(rec, "yardsReceived", r["yards_received"] or 0)
            if r["is_assist"]:
                bump(thr, "assists")
                bump(rec, "goals")
            if r["is_hockey_assist"]:
                bump(thr, "hockeyAssists")
            if r["is_huck"]:
                bump(thr, "hucksCompleted")
        if r["is_throwaway"]:
            bump(thr, "throwaways")
        if r["is_stall"]:
            bump(thr, "stalls")
        if r["is_drop"]:
            bump(rec, "drops")
        if r["is_callahan"]:
            bump(thr, "callahansThrown")
            bump(dfn, "callahans")
            bump(dfn, "goals")            # a callahan is a defensive goal for the catcher
        if r["is_block"]:
            bump(dfn, "blocks")
        if r["is_huck"]:
            bump(thr, "hucksAttempted")
        # throwAttempts = real throws (completions, throwaways, dropped throws, callahans);
        # a stall is not a released throw, so it is excluded.
        if r["is_completion"] or r["is_throwaway"] or r["is_drop"] or r["is_callahan"]:
            bump(thr, "throwAttempts")

    # --- pulls ---------------------------------------------------------------------------
    for r in pulls:
        p = r["puller_id"]
        bump(p, "pulls")
        if r["is_out_of_bounds"]:
            bump(p, "obPulls")
        if r["hangtime_seconds"]:
            bump(p, "recordedPulls")
            stats[p]["_hangtime_ms"] += r["hangtime_seconds"] * 1000.0

    # --- points (O/D played & scored, secondsPlayed) -------------------------------------
    # Group lineup stints by (point_id, team_id); union players across stints of a point.
    by_point_team = defaultdict(list)
    for r in lineups:
        by_point_team[(r["point_id"], r["team_id"])].append(r)
    for (pid_pt, team_id), stint_rows in by_point_team.items():
        is_o = any(s["line_type"] == "O-Line" for s in stint_rows)
        won = any(s["is_stint_scoring"] for s in stint_rows)
        players = set()
        for s in stint_rows:
            for p in s["lineup"]:
                players.add(p)
                team_of.setdefault(p, team_id)
                stats[p]["secondsPlayed"] += s["seconds_played"] or 0
        for p in players:
            if is_o:
                stats[p]["oPointsPlayed"] += 1
                stats[p]["oPointsScored"] += 1 if won else 0
            else:
                stats[p]["dPointsPlayed"] += 1
                stats[p]["dPointsScored"] += 1 if won else 0

    # --- opportunities (heuristic red-zone possession model) -----------------------------
    _accumulate_opportunities(throws, lineups, stats)

    # --- finalize ------------------------------------------------------------------------
    for p, s in stats.items():
        team_of.setdefault(p, _team_from_throws_pulls(p, throws, pulls))
        s["recordedPullsHangtime"] = round(s.pop("_hangtime_ms"))
        s["yardsThrown"] = round(s["yardsThrown"])
        s["yardsReceived"] = round(s["yardsReceived"])

    slug = team_slug_by_id or {}
    rows = []
    for p, s in stats.items():
        tid = team_of.get(p)
        row = {"playerID": p, "teamID": slug.get(tid, tid)}
        row.update({f: s[f] for f in _COUNT_FIELDS})
        rows.append(row)
    rows.sort(key=lambda r: (str(r["teamID"]), str(r["playerID"])))
    return rows


def _accumulate_opportunities(throws, lineups, stats):
    """Per red-zone possession, credit oOpportunity to the offense's on-field players and
    dOpportunity to the defense's; a scored possession is an oOpportunityScore, an unscored
    one a dOpportunityStop. Field presence comes from the point's lineups (union of stints).
    """
    players_by_point_team = defaultdict(set)
    for r in lineups:
        players_by_point_team[(r["point_id"], r["team_id"])].update(r["lineup"])

    poss = defaultdict(list)
    for r in throws:
        poss[r["possession_id"]].append(r)

    for rows in poss.values():
        first = rows[0]
        reached_rz = any(
            (r["end_y"] is not None and r["end_y"] >= REDZONE_Y)
            or (r["start_y"] is not None and r["start_y"] >= REDZONE_Y)
            for r in rows
        )
        if not reached_rz:
            continue
        scored = any(r["is_assist"] for r in rows)
        pt = first["point_id"]
        off_players = players_by_point_team.get((pt, first["offense_team_id"]), set())
        def_players = players_by_point_team.get((pt, first["defense_team_id"]), set())
        for p in off_players:
            stats[p]["oOpportunities"] += 1
            if scored:
                stats[p]["oOpportunityScores"] += 1
        for p in def_players:
            stats[p]["dOpportunities"] += 1
            if not scored:
                stats[p]["dOpportunityStops"] += 1


def _team_from_throws_pulls(pid, throws, pulls):
    """Fallback team resolution for a player absent from lineups (e.g. only pulled)."""
    for r in throws:
        if r["thrower_id"] == pid or r["receiver_id"] == pid:
            return r["offense_team_id"]
        if r["defender_id"] == pid:
            return r["defense_team_id"]
    for r in pulls:
        if r["puller_id"] == pid:
            return r["pulling_team_id"]
    return None


# --- live-API comparison ---------------------------------------------------------------------
def fetch_player_game_stats(game_id):
    """GET the live playerGameStats API and return the flat list of player dicts."""
    payload = http_get_json(f"{BASE_URL}/api/v1/playerGameStats?gameID={game_id}")
    return payload["data"]


def _compare(built, api_rows):
    """Return {field: {"match": n, "total": n, "worst": (playerID, got, exp)}} for reporting."""
    api_by_id = {r["player"]["playerID"]: r for r in api_rows}
    fields = CORE_FIELDS + INFORMATIONAL_FIELDS
    report = {f: {"match": 0, "total": 0, "worst": None, "worst_diff": -1} for f in fields}
    for row in built:
        api = api_by_id.get(row["playerID"])
        if api is None:
            continue
        for f in fields:
            exp, got = api.get(f), row.get(f)
            if exp is None:
                continue
            report[f]["total"] += 1
            tol = 1 if f in YARD_FIELDS else 0
            diff = abs((got or 0) - exp)
            if diff <= tol:
                report[f]["match"] += 1
            elif diff > report[f]["worst_diff"]:
                report[f]["worst_diff"] = diff
                report[f]["worst"] = (row["playerID"], got, exp)
    return report


def _print_report(report, game_id):
    print(f"\nplayerGameStats reconciliation for {game_id}")
    print(f"{'field':24s} {'match/total':>12s}   worst (playerID got!=exp)")
    print("-" * 72)
    for f in CORE_FIELDS + INFORMATIONAL_FIELDS:
        r = report[f]
        if r["total"] == 0:
            continue
        mark = "OK " if r["match"] == r["total"] else "XX "
        if f in INFORMATIONAL_FIELDS:
            tag = " (info)"
        elif f in STAGING_LIMITED_FIELDS:
            tag = " (staging)"
        else:
            tag = ""
        worst = ""
        if r["worst"]:
            pid, got, exp = r["worst"]
            worst = f"{pid} {got}!={exp}"
        print(f"{mark}{f+tag:24s} {r['match']:5d}/{r['total']:<6d}   {worst}")


def main():
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from main import run  # reuse the pipeline to build staging tables

    p = argparse.ArgumentParser(description="Reconcile reconstructed player stats vs the API.")
    p.add_argument("game_id")
    p.add_argument("--local", action="store_true", help="build staging from local samples")
    args = p.parse_args()

    tables = run(args.game_id, out_dir="/tmp/audl-pgs", local=args.local)
    slug = _slug_map(tables["stg_games"])
    built = build_player_game_stats(
        tables["stg_throws"], tables["stg_pulls"], tables["stg_point_lineups"],
        team_slug_by_id=slug, game_id=args.game_id,
    )
    api_rows = fetch_player_game_stats(args.game_id)
    _print_report(_compare(built, api_rows), args.game_id)


def _slug_map(stg_games):
    """teamSeasonId -> ext_team_id slug, from stg_games rows."""
    return {r["teamSeasonId"]: r["ext_team_id"] for r in stg_games}


if __name__ == "__main__":
    main()
