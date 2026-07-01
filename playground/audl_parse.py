"""Shared helpers for reconstructing UFA/AUDL stats from raw game-event JSON.

Game files live at ``~/Data/AUDLStats/game_stats/<gameID>.json``. Each game dict has
``game``, ``rostersHome``, ``rostersAway``, ``tsgHome``, ``tsgAway``. Each ``tsg`` carries
``startOnOffense``, ``teamSeasonId`` and ``events`` (a *stringified* JSON array).

Event-type codes (the ``t`` field) mirror ``audl/stats/library/parameters.py`` and the
empirical investigation. Each team's event stream is from THAT team's own perspective and
uses that team's roster ``id`` values in ``l`` (lineup) / ``r`` (single player).
"""

import json
import os
from pathlib import Path

GAME_DIR = Path("~/Data/AUDLStats/game_stats").expanduser()
PLAYERS_CSV = Path("~/Data/AUDLStats/players_stats/players.csv").expanduser()

# --- Event-type constants -------------------------------------------------
OFFENSE_POINT = 1      # l = lineup of 7 (this team starts the point on offense)
DEFENSE_POINT = 2      # l = lineup of 7 (this team starts the point on defense)
PULL = 3               # r = puller, x,y = landing, ms = hangtime (ms)
PULL_OB = 4            # out-of-bounds pull (r = puller)
BLOCK = 5              # r = blocker (this team got a D block)
CALLAHAN = 6           # r = scorer: defender catches in endzone (goal+block+callahan)
STALL = 7             # stall turnover BY us (x,y = disc location)
THROWAWAY = 8          # throwaway BY us (x,y = disc landing)
THROWAWAY_CAUSED = 9   # we forced opponent turnover (marker)
CALL_ON_FIELD = 12
SWITCH_OFF_DEF = 13
TIMEOUT_OFFENSE = 14
TIMEOUT_DEFENSE = 15
INJURY = 17            # injury stoppage; a 17 while holding that ends the poss = STALL
DROP = 19              # r = dropper (this team dropped a catchable pass)
PASS_COMPLETED = 20    # r = receiver, x,y = receiver location
THEY_SCORE = 21        # opponent scored
WE_SCORE = 22          # r = scorer, x,y = endzone (goal == completed throw)
END_Q1 = 23
END_Q2 = 24
END_Q3 = 25
END_Q4 = 26
END_OT1 = 27
END_OT2 = 28
TIMEOUT_LINEUP_D = 40  # l = lineup after timeout
TIMEOUT_LINEUP_O = 41  # l = lineup after timeout
OFFSIDE = 44
START_GAME = 50

# Observed in the data but semantics not pinned to ground truth. They occur while the
# opponent has the disc or in timeout/transition gaps, never mid-possession for us, so
# they are treated as neutral no-ops (they must NOT end an open possession). See
# audl-event-encodings memory. Counts (3 games): 11x43, 18x3, 42x4, 43x4, 53x14, 54x2.
OPP_POSSESSION = 11    # marker during the opponent's possession (between our TO and theirs)
PRE_PICKUP = 18        # appears just before our pickup (next event is a t=20)
TIMEOUT_O_MARK = 42    # precedes an offensive timeout lineup (t=41)
TIMEOUT_D_MARK = 43    # precedes a defensive timeout lineup (t=40)
POST_TIMEOUT_53 = 53   # post-timeout transition marker
POST_TIMEOUT_54 = 54   # post-timeout transition marker

QUARTER_END = {END_Q1, END_Q2, END_Q3, END_Q4, END_OT1, END_OT2}
LINEUP_EVENTS = {OFFENSE_POINT, DEFENSE_POINT}
PULL_EVENTS = {PULL, PULL_OB}
TURNOVER_EVENTS = {STALL, THROWAWAY, DROP}

# Codes that legitimately END the current possession / reset the throw-chain when they
# are not handled explicitly by an accumulator. A code NOT in here and not explicitly
# handled is treated as a neutral no-op so an unknown code can never split a possession.
POSSESSION_RESET = {
    OFFENSE_POINT, DEFENSE_POINT, THROWAWAY_CAUSED, SWITCH_OFF_DEF, THEY_SCORE,
    OFFSIDE, START_GAME, TIMEOUT_LINEUP_D, TIMEOUT_LINEUP_O, *QUARTER_END,
}

# Codes that are known to be neutral within our offense: they must never end/split a
# possession (used by both accumulators' catch-all branch alongside unknown codes).
NEUTRAL_MARKERS = {
    OPP_POSSESSION, PRE_PICKUP, TIMEOUT_O_MARK, TIMEOUT_D_MARK,
    POST_TIMEOUT_53, POST_TIMEOUT_54,
}

# Every event code we have observed and handle. A `t` outside this set is unseen in the
# games this was built against -- warn_unknown_event() flags it so a new code surfaces
# loudly instead of being silently ignored as a neutral no-op.
KNOWN_EVENT_CODES = {
    OFFENSE_POINT, DEFENSE_POINT, PULL, PULL_OB, BLOCK, CALLAHAN, STALL, THROWAWAY,
    THROWAWAY_CAUSED, 10, CALL_ON_FIELD, SWITCH_OFF_DEF, TIMEOUT_OFFENSE, TIMEOUT_DEFENSE,
    INJURY, DROP, PASS_COMPLETED, THEY_SCORE, WE_SCORE, TIMEOUT_LINEUP_D, TIMEOUT_LINEUP_O,
    OFFSIDE, START_GAME, *QUARTER_END, *NEUTRAL_MARKERS,
}

_WARNED_EVENT_CODES = set()


def warn_unknown_event(t, where=""):
    """Emit a one-time stderr warning the first time an unrecognised ``t`` code is seen.

    De-duplicated per (code, where) so a novel event code in a new game file is surfaced
    once rather than silently treated as a neutral no-op. Returns True if it was unseen.
    """
    if t in KNOWN_EVENT_CODES:
        return False
    key = (t, where)
    if key in _WARNED_EVENT_CODES:
        return False
    _WARNED_EVENT_CODES.add(key)
    import sys

    ctx = f" in {where}" if where else ""
    print(f"[audl_parse] WARNING: unrecognised event code t={t!r}{ctx}; "
          f"treated as a neutral no-op (not handled). Verify its meaning against ground "
          f"truth and add it to audl_parse.py.", file=sys.stderr)
    return True


def load_game(game_id):
    """Load a raw game dict by gameID (e.g. ``2026-05-10-MTL-PIT``)."""
    path = GAME_DIR / f"{game_id}.json"
    with open(path) as f:
        return json.load(f)


def list_game_ids():
    """Return the gameIDs available locally."""
    return sorted(p.stem for p in GAME_DIR.glob("*.json"))


def parse_events(tsg):
    """Return the event list for a tsg, decoding the stringified ``events`` field."""
    ev = tsg["events"]
    return json.loads(ev) if isinstance(ev, str) else ev


def build_roster_map(rosters):
    """int roster id -> {'name', 'first', 'last', 'jersey'}."""
    out = {}
    for r in rosters:
        p = r.get("player", {})
        first = (p.get("first_name") or "").strip()
        last = (p.get("last_name") or "").strip()
        out[r["id"]] = {
            "name": f"{first} {last}".strip(),
            "first": first,
            "last": last,
            "jersey": r.get("jersey_number"),
        }
    return out


_PLAYERS_CSV_CACHE = None


def _load_players_csv():
    global _PLAYERS_CSV_CACHE
    if _PLAYERS_CSV_CACHE is None:
        import csv

        rows = []
        with open(PLAYERS_CSV) as f:
            for row in csv.DictReader(f):
                rows.append(row)
        _PLAYERS_CSV_CACHE = rows
    return _PLAYERS_CSV_CACHE


def build_ext_id_map(rosters):
    """Best-effort int roster id -> external playerID string (e.g. ``adub``).

    The local game JSON has no external id, so we match on (first_name, last_name)
    against players.csv. Ambiguous (colliding) names resolve to ``None``.
    """
    by_name = {}
    for row in _load_players_csv():
        key = (row["firstName"].strip().lower(), row["lastName"].strip().lower())
        by_name.setdefault(key, []).append(row["playerID"])

    rmap = build_roster_map(rosters)
    out = {}
    for rid, info in rmap.items():
        key = (info["first"].lower(), info["last"].lower())
        matches = by_name.get(key, [])
        out[rid] = matches[0] if len(matches) == 1 else None
    return out


def merge_streams(home_events, away_events):
    """Tag each event with its side ('H'/'A') and return one timeline sorted by (n, side).

    ``n`` is a monotonic id shared across both streams; the side is a stable tiebreak.
    """
    tagged = [("H", e) for e in home_events] + [("A", e) for e in away_events]
    tagged.sort(key=lambda se: (se[1].get("n", 0), se[0]))
    return tagged


def write_json(obj, path):
    """Write ``obj`` as pretty JSON, creating parent dirs."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    return os.fspath(path)
