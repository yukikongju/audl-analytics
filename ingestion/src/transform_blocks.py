"""stg_blocks transform (from the gameEvents API).

One row per defensive block: a ``BLOCK`` (type-11) or a ``CALLAHAN_OURS`` (type-12, the
defender catches in the endzone -- a block that is also a goal). Each event names its
``defender`` directly, so counting blocks from these is exact -- unlike inferring them by
attaching to the opposing team's throwaway, which misses blocks on buzzer/unpaired points.
"""

from constants import BLOCK, CALLAHAN_OURS

_BLOCK_TYPES = {BLOCK, CALLAHAN_OURS}


def extract_blocks_events(timeline, ctx):
    """Return the stg_blocks rows for a game. ``timeline`` is from ``build_timeline``."""
    rows = []
    for it in timeline:
        e = it["event"]
        t = e.get("type")
        if t not in _BLOCK_TYPES:
            continue
        rows.append({
            "game_id": ctx["game_id"],
            "point_id": it["point_id"],
            "defender_id": e.get("defender"),
            "defense_team_id": it["team_id"],   # the blocking team is the one on defense
            "is_callahan": t == CALLAHAN_OURS,
        })
    return rows
