"""stg_point_lineups transform (from the gameEvents API).

One row per point, per team, per stint. A stint is a stable set of 7 players: it opens at the
point start (``START_O_POINT``/``START_D_POINT``) and a new stint opens whenever a timeout or
injury sub (``MIDPOINT_TIMEOUT_*``/``INJURY``) puts a new line on the field. Each team's stream
carries its OWN line on those events, so the two streams give the two teams.

Times are best-effort: the game clock ``time`` (seconds into the period) is recorded on
line-setting events but NOT on goals, so a point's final ``stint_end_time`` is unknown, and
``seconds_played`` is derived from wall-clock ``timestamp`` deltas -- the same limitation the
tsg reconstruction hit.
"""

from constants import POINT_START, START_O_POINT, SUB_EVENTS

_LINE_EVENTS = POINT_START | SUB_EVENTS


def extract_point_lineups_events(timeline, ctx):
    """Return the stg_point_lineups rows for a game. ``timeline`` is from ``build_timeline``."""
    # Collect the ordered line-setting events per (point, side).
    stints = {}   # (point_id, side) -> list of stint dicts
    meta = {}     # (point_id, side) -> {team_score, opp_score, scorer_side, team_id}
    for it in timeline:
        e = it["event"]
        t = e.get("type")
        if t not in _LINE_EVENTS:
            continue
        key = (it["point_id"], it["side"])
        if key not in meta:
            team_score = it["home_score"] if it["side"] == "H" else it["away_score"]
            opp_score = it["away_score"] if it["side"] == "H" else it["home_score"]
            meta[key] = {
                "team_score": team_score,
                "opp_score": opp_score,
                "scorer_side": it["scorer_side"],
                "team_id": it["team_id"],
            }
        stints.setdefault(key, []).append({
            "line": e.get("line", []),
            "time": e.get("time"),
            "ts": e.get("timestamp"),
            "line_type": ("O-Line" if t == START_O_POINT else "D-Line") if t in POINT_START else None,
        })

    rows = []
    for (pid, side), stint_list in sorted(stints.items()):
        m = meta[(pid, side)]
        line_type = next((s["line_type"] for s in stint_list if s["line_type"]), None)
        scored = m["scorer_side"] == side
        for i, s in enumerate(stint_list):
            is_last = i == len(stint_list) - 1
            nxt = stint_list[i + 1] if not is_last else None
            end_time = nxt["time"] if nxt else None
            end_ts = nxt["ts"] if nxt else None
            seconds = (end_ts - s["ts"]) if (end_ts and s["ts"]) else None
            rows.append({
                "game_id": ctx["game_id"],
                "point_id": pid,
                "stint_id": i + 1,
                "team_id": m["team_id"],
                "team_score": m["team_score"],
                "opponent_score": m["opp_score"],
                "lineup": s["line"],
                "line_type": line_type,
                "is_stint_scoring": bool(scored and is_last),
                "stint_start_time": s["time"],
                "stint_end_time": end_time,
                "seconds_played": seconds,
            })
    return rows
