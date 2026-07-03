"""Event-type codes for the UFA/AUDL ``gameEvents`` API.

The gameEvents endpoint (``api/v1/gameEvents?gameID=<id>``) returns a much cleaner event
stream than the terse ``tsg`` events embedded in the game-stats JSON: external playerIDs,
named coordinate fields, real pull hangtime, defender ids on blocks, and a synced absolute
``timestamp`` on every event. These codes come from the documented event table
(https://www.docs.ufastats.com/events) and are DISTINCT from the ``tsg`` ``t`` codes in
``playground/audl_parse.py`` -- do not mix the two.

Each team's stream is from THAT team's perspective ("recording team"), normalized so its
offense attacks +y (goal line at y=100, endzone 100-120). "ours"/"theirs" below are from
the recording team's point of view.
"""

# --- Point starts (carry `line` = 7 playerIDs, `time` = seconds into the period) --------
START_D_POINT = 1        # recording team starts this point on defense (it pulls)
START_O_POINT = 2        # recording team starts this point on offense (it receives)

# --- Substitutions / line changes (carry `line`, `time`) --------------------------------
MIDPOINT_TIMEOUT_OURS = 3     # timeout by recording team; `line` = players now on
MIDPOINT_TIMEOUT_THEIRS = 5   # timeout by opposing team; `line` = players now on
INJURY = 25                   # `line` = players on after injury subs

# --- Timeouts without a line (between points) -------------------------------------------
BETWEEN_POINT_TIMEOUT_OURS = 4
BETWEEN_POINT_TIMEOUT_THEIRS = 6

# --- Pulls -------------------------------------------------------------------------------
PULL_INBOUNDS = 7        # `puller`, `pullX`, `pullY`, `pullMs` (ms; 0 = not recorded)
PULL_OB = 8              # `puller` only (landed out of bounds)
OFFSIDES_OURS = 9        # `puller` -- re-pull forced on recording team
OFFSIDES_THEIRS = 10     # `puller` -- re-pull forced on opposing team

# --- Defensive events (recording team is on defense) ------------------------------------
BLOCK = 11               # `defender` = playerID getting the block
CALLAHAN_OURS = 12       # `defender` = playerID catching a callahan (D score)
THROWAWAY_THEIRS = 13    # opposing team threw it away (recording team gains possession)
STALL_THEIRS = 14        # opposing team stalled (recording team gains possession)
SCORE_THEIRS = 15        # opposing team scored

# --- Penalties ---------------------------------------------------------------------------
PENALTY_OURS = 16
PENALTY_THEIRS = 17

# --- Offensive throws (recording team has the disc) -------------------------------------
PASS = 18                # `thrower`,`throwerX/Y`,`receiver`,`receiverX/Y` (completion)
GOAL = 19                # completed pass into the endzone (assist + goal)
DROP = 20                # `receiver` = the dropper; thrower coords + receiver coords
DROPPED_PULL = 21        # `receiver` dropped the pull
THROWAWAY_OURS = 22      # `thrower`,`throwerX/Y`,`turnoverX/Y` (disc landing)
CALLAHAN_THEIRS = 23     # recording team threw it, opponent caught a callahan; `turnoverX/Y`
STALL_OURS = 24          # `thrower` held too long; `throwerX/Y`

# --- Period boundaries -------------------------------------------------------------------
END_Q1 = 28
HALFTIME = 29
END_Q3 = 30
END_REGULATION = 31
END_OT1 = 32
END_OT2 = 33

DELAYED = 34
POSTPONED = 35

# --- Sets used by the transforms ---------------------------------------------------------
POINT_START = {START_D_POINT, START_O_POINT}
SUB_EVENTS = {MIDPOINT_TIMEOUT_OURS, MIDPOINT_TIMEOUT_THEIRS, INJURY}
PULL_EVENTS = {PULL_INBOUNDS, PULL_OB}
OFFSIDES_EVENTS = {OFFSIDES_OURS, OFFSIDES_THEIRS}

# Offensive throw events (each produces one stg_throws row for the recording team).
THROW_EVENTS = {PASS, GOAL, DROP, THROWAWAY_OURS, CALLAHAN_THEIRS, STALL_OURS}
COMPLETION_EVENTS = {PASS, GOAL}

# Any score, from either perspective (ends the point).
SCORE_EVENTS = {GOAL, SCORE_THEIRS, CALLAHAN_OURS, CALLAHAN_THEIRS}

QUARTER_END = {END_Q1, HALFTIME, END_Q3, END_REGULATION, END_OT1, END_OT2}

# Every code we recognise; anything else is surfaced by warn_unknown_event().
KNOWN_EVENT_CODES = (
    POINT_START
    | SUB_EVENTS
    | PULL_EVENTS
    | OFFSIDES_EVENTS
    | THROW_EVENTS
    | SCORE_EVENTS
    | QUARTER_END
    | {
        BETWEEN_POINT_TIMEOUT_OURS, BETWEEN_POINT_TIMEOUT_THEIRS,
        BLOCK, THROWAWAY_THEIRS, STALL_THEIRS, DROPPED_PULL,
        PENALTY_OURS, PENALTY_THEIRS, DELAYED, POSTPONED,
    }
)

# --- Field / classification constants ----------------------------------------------------
HUCK_YARDS = 40          # downfield throw distance for a huck (matches tsg reconstruction)
REDZONE_Y = 80           # y >= 80 is the attacking red zone (scoring-opportunity range)
ENDZONE_Y = 100          # goal line; yards are capped here

_WARNED_EVENT_CODES = set()


def warn_unknown_event(t, where=""):
    """Emit a one-time stderr warning the first time an unrecognised type code is seen.

    De-duplicated per (code, where) so a novel event code in a new game file is surfaced
    once rather than silently ignored. Returns True if it was previously unseen.
    """
    if t in KNOWN_EVENT_CODES:
        return False
    key = (t, where)
    if key in _WARNED_EVENT_CODES:
        return False
    _WARNED_EVENT_CODES.add(key)
    import sys

    ctx = f" in {where}" if where else ""
    print(
        f"[gameEvents] WARNING: unrecognised event type={t!r}{ctx}; not handled. "
        f"Verify its meaning against the docs and add it to constants.py.",
        file=sys.stderr,
    )
    return True
