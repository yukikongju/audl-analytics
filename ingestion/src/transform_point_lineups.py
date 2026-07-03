"""stg_point_lineups transform (from the gameEvents API).

One row per point, per team, per stint. A stint is a stable set of 7 players: it opens at the
point start (``START_O_POINT``/``START_D_POINT``) and a new stint opens whenever a timeout or
injury sub (``MIDPOINT_TIMEOUT_*``/``INJURY``) puts a new line on the field. Each team's stream
carries its OWN line on those events, so the two streams give the two teams.

``line_type`` is the possession phase the stint's players ENTERED on ('O-Line'/'D-Line'),
carried on the line event by the timeline: the point-start line gets the point's O/D, but a
mid-point sub gets whichever phase the team was in at the timeout -- so an O-line subbed on
while the team is on offense during a point it pulled is an 'O-Line' stint. This matches the
API's per-player O/D-point attribution.

``seconds_played`` is derived from the game clock ``time`` (seconds into the period, which
resets each quarter): a stint runs until the next stint's start, or the next point's start in
the same quarter, or the end of the quarter (``QUARTER_SECONDS``) for the last point of a
period. It is best-effort -- the game clock stops on turnovers/timeouts, so it slightly
undercounts real on-field time.
"""

from constants import POINT_START, QUARTER_SECONDS, SUB_EVENTS

_LINE_EVENTS = POINT_START | SUB_EVENTS


def extract_point_lineups_events(timeline, ctx):
    """Return the stg_point_lineups rows for a game. ``timeline`` is from ``build_timeline``."""
    # Collect the ordered line-setting events per (point, side).
    stints = {}   # (point_id, side) -> list of stint dicts
    meta = {}     # (point_id, side) -> {team_score, opp_score, scorer_side, team_id, quarter}
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
                "quarter": it.get("quarter"),
            }
        stints.setdefault(key, []).append({
            "line": e.get("line", []),
            "time": e.get("time"),
            "phase": it.get("line_phase"),
        })

    # For each side, the next point's (quarter, start time) -- used to close a point's last
    # stint. Point ids are sequential across the game, so sorting by point_id gives play order.
    next_point = {}   # (point_id, side) -> (quarter, start_time) of the following point
    by_side = {}
    for (pid, side), stint_list in stints.items():
        by_side.setdefault(side, []).append(
            (pid, meta[(pid, side)]["quarter"], stint_list[0]["time"]))
    for side, entries in by_side.items():
        entries.sort()
        for i, (pid, _q, _tm) in enumerate(entries):
            nxt = entries[i + 1] if i + 1 < len(entries) else None
            next_point[(pid, side)] = (nxt[1], nxt[2]) if nxt else None

    rows = []
    for (pid, side), stint_list in sorted(stints.items()):
        m = meta[(pid, side)]
        scored = m["scorer_side"] == side
        # end time of the point's LAST stint: the next point's start if in the same quarter,
        # else the end of the quarter.
        nxt = next_point.get((pid, side))
        point_end = nxt[1] if (nxt and nxt[0] == m["quarter"]) else QUARTER_SECONDS
        for i, s in enumerate(stint_list):
            is_last = i == len(stint_list) - 1
            start_time = s["time"]
            end_time = point_end if is_last else stint_list[i + 1]["time"]
            seconds = None
            if start_time is not None and end_time is not None:
                seconds = end_time - start_time
                if seconds < 0:
                    seconds = None
            rows.append({
                "game_id": ctx["game_id"],
                "point_id": pid,
                "stint_id": i + 1,
                "team_id": m["team_id"],
                "team_score": m["team_score"],
                "opponent_score": m["opp_score"],
                "lineup": s["line"],
                "line_type": "O-Line" if s["phase"] == "O" else "D-Line",
                "is_stint_scoring": bool(scored and is_last),
                "stint_start_time": start_time,
                "stint_end_time": end_time,
                "seconds_played": seconds,
            })
    return rows
