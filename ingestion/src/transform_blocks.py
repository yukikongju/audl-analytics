"""stg_blocks transform (from the gameEvents API).

One row per defensive block: a ``BLOCK`` (type-11) or a ``CALLAHAN_OURS`` (type-12, the
defender catches in the endzone -- a block that is also a goal). Each event names its
``defender`` directly, so counting blocks from these is exact -- unlike inferring them by
attaching to the opposing team's throwaway, which misses blocks on buzzer/unpaired points.

``possession_id``/``sequence_id`` link the block to the exact ``ext_throws`` sequence it
broke up. A block is logged in the blocking (defending) team's stream, while the turnover it
forced is a throw in the opponent's stream -- the timeline bridges the two by stamping that
throw with a ``defender_id`` (see ``build_timeline``). We join on ``(point_id, defender)`` to
carry that throw's possession/sequence back onto the block. When the bridge can't be made --
e.g. a desynced or empty opponent stream, or a buzzer/unpaired point where the forced turnover
has no paired throw -- these ids are left null; the block is still counted so per-player block
totals stay exact.
"""

from collections import defaultdict

from constants import BLOCK, CALLAHAN_OURS, THROW_EVENTS

_BLOCK_TYPES = {BLOCK, CALLAHAN_OURS}


def extract_blocks_events(timeline, ctx):
    """Return the stg_blocks rows for a game. ``timeline`` is from ``build_timeline``."""
    # Forced-turnover throws carry possession/sequence and a defender_id; index them by
    # (point, defender) so each block can claim the throw it broke up, in order.
    seq_by = defaultdict(list)
    for it in timeline:
        if it["event"].get("type") in THROW_EVENTS and it["defender_id"] is not None:
            seq_by[(it["point_id"], it["defender_id"])].append(
                (it["possession_id"], it["sequence_id"]))

    rows = []
    for it in timeline:
        e = it["event"]
        t = e.get("type")
        if t not in _BLOCK_TYPES:
            continue
        defender = e.get("defender")
        matches = seq_by[(it["point_id"], defender)]
        possession_id, sequence_id = matches.pop(0) if matches else (None, None)
        rows.append({
            "game_id": ctx["game_id"],
            "point_id": it["point_id"],
            "possession_id": possession_id,
            "sequence_id": sequence_id,
            "defender_id": defender,
            "defense_ext_team_id": it["team_id"],   # the blocking team is the one on defense
            "is_callahan": t == CALLAHAN_OURS,
        })
    return rows
