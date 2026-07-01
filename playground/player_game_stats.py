"""Reconstruct the per-player box score (``player_game_stats``) from raw game events.

Each team's own event stream contains everything about its own players (offense AND
defense), so stats are accumulated per-stream and concatenated -- no interleaving needed.
Validated against the df_stats ground truth (see validate_stats.py).
"""

from pathlib import Path

from audl_parse import (
    BLOCK,
    DEFENSE_POINT,
    DROP,
    OFFENSE_POINT,
    PASS_COMPLETED,
    POSSESSION_RESET,
    PULL,
    PULL_OB,
    QUARTER_END,
    STALL,
    THEY_SCORE,
    THROWAWAY,
    THROWAWAY_CAUSED,
    TIMEOUT_LINEUP_D,
    TIMEOUT_LINEUP_O,
    WE_SCORE,
    build_ext_id_map,
    build_roster_map,
    parse_events,
    warn_unknown_event,
    write_json,
)

HUCK_THRESHOLD = 40  # downfield yards (verified against ground truth)
QUARTER_SECONDS = 720  # 12-minute quarters; fallback for first point of a quarter

# Events that interrupt but do NOT end a possession and keep the same player on the
# disc (calls, timeouts, injury): the throw-chain continues across them. Substitutions
# (t=40/41) are NOT here -- a line change makes the next touch an unattributable pickup.
CONTINUE_EVENTS = {10, 12, 14, 15}

_STAT_FIELDS = [
    "assists", "goals", "hockeyAssists", "completions", "throwaways", "stalls",
    "throwsAttempted", "catches", "drops", "blocks", "callahans", "pulls", "obPulls",
    "recordedPulls", "recordedPullsHangtime", "oPointsPlayed", "oPointsScored",
    "dPointsPlayed", "dPointsScored", "secondsPlayed", "yardsReceived", "yardsThrown",
    "hucksCompleted", "hucksAttempted",
]


def _new_stats():
    return {f: 0 for f in _STAT_FIELDS}


def _gain(ty, ry):
    """Downfield yards from thrower to receiver, capped at the goal line (y=100)."""
    return min(ry, 100) - min(ty, 100)


def _accumulate_events(events, st, where=""):
    """Accumulate per-throw offensive/defensive stats into ``st`` (id -> stats dict).

    Model: a stream lists only this team's offensive touches; opponent possessions are
    invisible gaps. Within a possession the thrower of a pass is the receiver of the
    previous pass (chain rule). The FIRST t=20 of a possession is a *pickup* (the disc
    was on the ground after a pull/turnover) -- it is not a catch and earns no receiving
    yards, but it seeds the chain so the next throw is credited correctly.
    """
    chain = []          # receiver ids of completions/pickups in current possession
    chain_y = []        # parallel y of each chain entry
    pickup = True       # the next t=20 is the possession's first touch (a pickup)

    def reset():
        nonlocal chain, chain_y, pickup
        chain, chain_y, pickup = [], [], True

    def lost_after(i):
        """True if, after event i, we lose the disc before throwing again."""
        for j in range(i + 1, len(events)):
            tj = events[j].get("t")
            if tj in (PASS_COMPLETED, THROWAWAY, 7, WE_SCORE):
                return False  # we throw/keep -> the t=17 was just an injury stoppage
            if tj in (THEY_SCORE, OFFENSE_POINT, DEFENSE_POINT, PULL, PULL_OB):
                return True
        return True

    for i, e in enumerate(events):
        t = e.get("t")

        if t == PASS_COMPLETED:
            r, ry = e.get("r"), e.get("y")
            if chain and chain[-1] == r:
                continue  # same player re-listed (retain after a call) -- not a pass
            ty = chain_y[-1] if chain_y else None
            if not pickup:
                thrower = chain[-1] if chain else None
                if r is not None:
                    st(r)["catches"] += 1
                    if ty is not None and ry is not None:
                        st(r)["yardsReceived"] += _gain(ty, ry)
                if thrower is not None:
                    s = st(thrower)
                    s["completions"] += 1
                    if ty is not None and ry is not None:
                        s["yardsThrown"] += _gain(ty, ry)
                        if ry - ty >= HUCK_THRESHOLD:  # huck = raw downfield distance
                            s["hucksAttempted"] += 1
                            s["hucksCompleted"] += 1
            chain.append(r)
            chain_y.append(ry)
            pickup = False

        elif t == WE_SCORE:
            scorer, sy = e.get("r"), e.get("y")
            thrower = None if pickup else (chain[-1] if chain else None)
            ty = chain_y[-1] if chain_y else None
            hockey = chain[-2] if (not pickup and len(chain) >= 2) else None
            if scorer is not None:
                st(scorer)["goals"] += 1
                st(scorer)["catches"] += 1  # the goal reception is a catch
                if thrower is not None and ty is not None and sy is not None:
                    st(scorer)["yardsReceived"] += _gain(ty, sy)
            if thrower is not None:
                s = st(thrower)
                s["assists"] += 1
                s["completions"] += 1  # the assist throw is a completion
                if ty is not None and sy is not None:
                    s["yardsThrown"] += _gain(ty, sy)
                    if sy - ty >= HUCK_THRESHOLD:
                        s["hucksAttempted"] += 1
                        s["hucksCompleted"] += 1
            if hockey is not None:
                st(hockey)["hockeyAssists"] += 1
            reset()

        elif t in (THROWAWAY, 7):  # t=8 in-bounds / t=7 out-of-bounds throwaway
            thrower = None if pickup else (chain[-1] if chain else None)
            ty = chain_y[-1] if chain_y else None
            if thrower is not None:
                st(thrower)["throwaways"] += 1
                ey = e.get("y")
                if ty is not None and ey is not None and (ey - ty) >= HUCK_THRESHOLD:
                    st(thrower)["hucksAttempted"] += 1  # incomplete huck
            reset()

        elif t == 17:
            # injury stoppage normally; but a t=17 while we hold the disc that ends
            # the possession (no further throw before we lose it) is a STALL.
            if not pickup and chain and lost_after(i):
                st(chain[-1])["stalls"] += 1
                reset()

        elif t == 6:  # callahan: a defender catches in the endzone to score
            if e.get("r") is not None:
                s = st(e["r"])
                s["goals"] += 1
                s["blocks"] += 1
                s["callahans"] += 1
            reset()

        elif t == DROP:
            if e.get("r") is not None:
                st(e["r"])["drops"] += 1
            thrower = None if pickup else (chain[-1] if chain else None)
            if thrower is not None:  # a dropped pass still counts as a throw attempt
                d = st(thrower)
                d["_drops_caused"] = d.get("_drops_caused", 0) + 1
            reset()

        elif t == BLOCK:
            # t=5 while we currently hold the disc (not a fresh pickup) is a STALL
            # turnover charged to the holder; otherwise it is a genuine defensive block.
            if not pickup and chain:
                st(chain[-1])["stalls"] += 1
            elif e.get("r") is not None:
                st(e["r"])["blocks"] += 1
            reset()

        elif t in (PULL, PULL_OB):
            pid = e.get("r")
            if pid is not None:
                s = st(pid)
                s["pulls"] += 1
                if t == PULL_OB:
                    s["obPulls"] += 1
                if e.get("ms"):  # only pulls with a non-zero recorded hangtime
                    s["recordedPulls"] += 1
                    s["recordedPullsHangtime"] += e["ms"]
            reset()

        elif t in CONTINUE_EVENTS:
            pass  # call / timeout / injury / sub: possession (and chain) continues

        elif t in POSSESSION_RESET:
            # point starts, scores-against, quarter ends, subs, offside, etc.
            reset()

        else:
            # NEUTRAL_MARKERS and any genuinely unrecognised code: do NOT break an open
            # possession (an unseen code in a new game file must not corrupt the chain).
            warn_unknown_event(t, where)


def _accumulate_points(events, st):
    """Credit points played/scored and seconds, segmenting by score events.

    A player's O/D credit comes from the UNIT they entered the point with, not from what
    they did with the disc: the offence unit (t=1 O-point start, or t=41 offence-timeout
    sub) -> oPointsPlayed; the defence unit (t=2 D-point start, or t=40 defence-timeout
    sub) -> dPointsPlayed. So an O-line player subbed on via an offensive timeout during a
    point their team pulled still gets an O-point. First entry per point wins. On a goal
    (t=22/t=6) the offence-unit players also get oPointsScored, the defence dPointsScored.

    secondsPlayed is best-effort: the clock ``s`` (seconds left in the quarter) is recorded
    only on scores/timeouts, never on the pull, so we can only measure score-to-score time
    -- which includes the dead time before each pull and so runs high. Pull-to-score active
    time is not recoverable from this stream.
    """
    PLAY_EVENTS = {PULL, PULL_OB, PASS_COMPLETED, THROWAWAY, DROP, STALL, BLOCK}
    entry = {}  # pid -> 'O'/'D': the unit the player entered the point with
    started = False
    had_play = False
    clock_ref = QUARTER_SECONDS  # clock at the start of the current point

    def record(players, unit):
        for pid in players:
            entry.setdefault(pid, unit)

    def close(scored, dur):
        for pid, unit in entry.items():
            s = st(pid)
            if unit == "O":
                s["oPointsPlayed"] += 1
                if scored:
                    s["oPointsScored"] += 1
            else:
                s["dPointsPlayed"] += 1
                if scored:
                    s["dPointsScored"] += 1
        if dur and dur > 0:
            for pid in entry:
                st(pid)["secondsPlayed"] += dur

    def reset():
        nonlocal entry, started, had_play
        entry, started, had_play = {}, False, False

    for e in events:
        t = e.get("t")

        if t in (OFFENSE_POINT, DEFENSE_POINT):
            started = True
            record(e.get("l", []), "O" if t == OFFENSE_POINT else "D")
        elif t in (TIMEOUT_LINEUP_O, TIMEOUT_LINEUP_D):  # 41 offence unit / 40 defence unit
            record(e.get("l", []), "O" if t == TIMEOUT_LINEUP_O else "D")
        elif t in PLAY_EVENTS:
            had_play = True
        elif t in (WE_SCORE, THEY_SCORE, 6):  # t=6 is a callahan (we score)
            if started:
                s = e.get("s")
                dur = None
                if s is not None and clock_ref is not None:
                    dur = clock_ref - s
                    if dur < 0:  # quarter rolled over between the boundaries
                        dur = QUARTER_SECONDS - s
                close(scored=(t in (WE_SCORE, 6)), dur=dur)
                if s is not None:
                    clock_ref = s
            reset()
        elif t in QUARTER_END:
            # a real point cut off by the buzzer still counts (no reliable duration);
            # a bare pre-set lineup with no play is discarded.
            if started and had_play:
                close(scored=False, dur=None)
            clock_ref = QUARTER_SECONDS
            reset()


def _accumulate_stream(events, roster_ids, where=""):
    """Accumulate all stats for one team's stream."""
    stats = {rid: _new_stats() for rid in roster_ids}

    def st(pid):
        if pid not in stats:
            stats[pid] = _new_stats()
        return stats[pid]

    _accumulate_events(events, st, where)
    _accumulate_points(events, st)

    for s in stats.values():
        # throws attempted = completions + throwaways + passes dropped by the receiver
        # (a stall is not a throw); the assist throw is already in completions.
        s["throwsAttempted"] = (
            s["completions"] + s["throwaways"] + s.pop("_drops_caused", 0)
        )
        s["recordedPullsHangtime"] = round(s["recordedPullsHangtime"], 2)
        s["yardsReceived"] = round(s["yardsReceived"])
        s["yardsThrown"] = round(s["yardsThrown"])

    return stats


OUTPUT_DIR = Path(__file__).parent / "output"


def get_player_game_stats(game, game_id=None, write=False, out_dir=OUTPUT_DIR):
    """Return a list of per-player stat dicts for a game (both teams)."""
    if game_id is None:
        game_id = game.get("game", {}).get("ext_game_id")

    rows = []
    for side, tsg_key, roster_key in (
        ("H", "tsgHome", "rostersHome"),
        ("A", "tsgAway", "rostersAway"),
    ):
        tsg = game[tsg_key]
        rosters = game[roster_key]
        team_id = tsg.get("teamSeasonId")
        events = parse_events(tsg)
        rmap = build_roster_map(rosters)
        ext = build_ext_id_map(rosters)
        roster_ids = list(rmap.keys())
        stats = _accumulate_stream(events, roster_ids, where=f"{game_id}/{tsg_key}")

        for rid, s in stats.items():
            info = rmap.get(rid, {})
            row = {
                "gameID": game_id,
                "teamID": team_id,
                "playerID": ext.get(rid) or rid,
                "playerIntId": rid,
                "playerName": info.get("name"),
                "extPlayerId": ext.get(rid),
            }
            row.update(s)
            rows.append(row)

    if write:
        write_json(rows, f"{out_dir}/{game_id}.player_stats.json")
    return rows


if __name__ == "__main__":
    from audl_parse import list_game_ids, load_game

    for gid in list_game_ids():
        rows = get_player_game_stats(load_game(gid), game_id=gid, write=True)
        print(f"{gid}: {len(rows)} player rows")
