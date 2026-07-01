"""stg_throws transform (from the gameEvents API).

One row per offensive throw attempt (``PASS``/``GOAL``/``DROP``/``THROWAWAY_OURS``/
``CALLAHAN_THEIRS``/``STALL_OURS``). Point/possession/sequence ordering, offense/defense
attribution and the block ``defender_id`` all come from ``timeline.build_timeline`` (which
weaves the two clock-independent streams). Because gameEvents records the actual thrower,
receiver and BOTH sets of coordinates on every throw, each row is self-contained -- no
chain-threading or pickup inference is needed (unlike the tsg reconstruction).
"""

from constants import (
    COMPLETION_EVENTS,
    DROP,
    GOAL,
    HUCK_YARDS,
    STALL_OURS,
    THROW_EVENTS,
    THROWAWAY_OURS,
)
from pipeline_utils import yards


def _is_huck(sy, ey):
    """A huck is a downfield throw of at least ``HUCK_YARDS``. Single source of truth so
    the ``is_huck`` flag and the ``huck`` throw_type never disagree at the threshold."""
    return sy is not None and ey is not None and (ey - sy) >= HUCK_YARDS


def _throw_type(sx, sy, ex, ey):
    """Tactical throw type from field geometry (offense attacks +y, lateral = x).

    Only the coordinate-derivable tactical class; mechanical type (hammer/scoober) and
    side (backhand/forehand) are not recoverable from endpoints, so they are omitted.
    """
    if None in (sx, sy, ex, ey):
        return None
    dx, dy = ex - sx, ey - sy
    if _is_huck(sy, ey):
        return "huck"
    if dy <= 0:
        return "dump"
    if abs(dx) >= 15 and dy < 10:
        return "swing"
    if 0 < dy <= 20 and abs(dx) < 15:
        return "under"
    return "upline"


def extract_throws_events(timeline, ctx):
    """Return the stg_throws rows for a game.

    ``timeline`` is the annotated event list from ``build_timeline``; ``ctx`` =
    ``{game_id, date, home_team_id, away_team_id}``.
    """
    rows = []
    for it in timeline:
        e = it["event"]
        t = e.get("type")
        if t not in THROW_EVENTS:
            continue

        sx, sy = e.get("throwerX"), e.get("throwerY")
        row = {
            "date": ctx["date"],
            "game_id": ctx["game_id"],
            "point_id": it["point_id"],
            "possession_id": it["possession_id"],
            "sequence_id": it["sequence_id"],
            "offense_team_id": it["offense_team_id"],
            "defense_team_id": it["defense_team_id"],
            "thrower_id": e.get("thrower"),
            "receiver_id": None,
            "defender_id": it["defender_id"],
            "is_completion": False,
            "is_throwaway": False,
            "is_drop": False,
            "is_block": it["defender_id"] is not None,
            "is_interception": False,
            "is_assist": False,
            "is_hockey_assist": False,
            "is_huck": False,
            "is_stall": False,
            "is_callahan": False,
            "start_x": sx,
            "start_y": sy,
            "end_x": None,
            "end_y": None,
            "yards_thrown": 0,
            "yards_received": 0,
            "throw_type": None,
        }

        if t in COMPLETION_EVENTS:  # PASS / GOAL
            row["receiver_id"] = e.get("receiver")
            ex, ey = e.get("receiverX"), e.get("receiverY")
            row["is_completion"] = True
            row["is_assist"] = t == GOAL
            row["yards_thrown"] = row["yards_received"] = round(yards(sy, ey) or 0, 2)
            row["is_huck"] = _is_huck(sy, ey)
        elif t == DROP:
            row["receiver_id"] = e.get("receiver")  # the dropper
            ex, ey = e.get("receiverX"), e.get("receiverY")
            row["is_drop"] = True
        elif t == THROWAWAY_OURS:
            ex, ey = e.get("turnoverX"), e.get("turnoverY")
            row["is_throwaway"] = True
            row["is_huck"] = _is_huck(sy, ey)  # an incomplete huck still counts as an attempt
        else:  # CALLAHAN_THEIRS (23) or STALL_OURS (24)
            ex, ey = e.get("turnoverX"), e.get("turnoverY")
            row["is_throwaway"] = True
            if t == STALL_OURS:
                row["is_throwaway"] = False
                row["is_stall"] = True
            else:  # CALLAHAN_THEIRS: we threw it, opponent scored a callahan
                row["is_callahan"] = True
                row["is_block"] = True
                row["is_interception"] = True

        row["end_x"], row["end_y"] = ex, ey
        row["throw_type"] = _throw_type(sx, sy, ex, ey)
        rows.append(row)

    _mark_hockey_assists(rows)
    return rows


def _mark_hockey_assists(rows):
    """Flag the completion immediately preceding each assist in the same possession."""
    by_poss = {}
    for i, r in enumerate(rows):
        by_poss.setdefault(r["possession_id"], []).append(i)
    for idxs in by_poss.values():
        assist_pos = next((k for k, i in enumerate(idxs) if rows[i]["is_assist"]), None)
        if assist_pos and assist_pos >= 1:
            prev = rows[idxs[assist_pos - 1]]
            if prev["is_completion"]:
                prev["is_hockey_assist"] = True
