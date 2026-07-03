"""stg_pulls transform (from the gameEvents API).

One row per pull (``PULL_INBOUNDS``/``PULL_OB``/``OFFSIDES_OURS`` re-pull). The pulling team is
the team on defense to start the point (the team whose stream logged the pull).
``pull_sequence`` starts at 1 and increments when a point has more than one pull (an offsides
penalty forcing a re-pull -- the API counts both the nullified and the re-pull).
"""

from constants import OFFSIDES_OURS, PULL_EVENTS, PULL_OB

# An offsides re-pull (9) is a pull the API counts; it carries no coords/hangtime.
_PULL_ROW_TYPES = PULL_EVENTS | {OFFSIDES_OURS}


def extract_pulls_events(timeline, ctx):
    """Return the stg_pulls rows for a game. ``timeline`` is from ``build_timeline``."""
    rows = []
    seq_by_point = {}
    for it in timeline:
        e = it["event"]
        if e.get("type") not in _PULL_ROW_TYPES:
            continue
        pid = it["point_id"]
        seq_by_point[pid] = seq_by_point.get(pid, 0) + 1
        rows.append({
            "game_id": ctx["game_id"],
            "point_id": pid,
            "pull_sequence": seq_by_point[pid],
            "pulling_team_id": it["team_id"],
            "puller_id": e.get("puller"),
            "hangtime_seconds": (e["pullMs"] / 1000.0) if e.get("pullMs") else None,
            "is_out_of_bounds": e.get("type") == PULL_OB,
            "end_x": e.get("pullX"),
            "end_y": e.get("pullY"),
        })
    return rows
