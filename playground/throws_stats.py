"""Reconstruct every throw of a game (``throws_events``) from raw game events.

Each team's stream lists only its own offensive touches, so a point's possessions are
split across the two streams. The two streams' ``n`` timestamps are not reliably
synchronised, so instead of interleaving by time we reconstruct the canonical order from
game logic: within a point, possession strictly alternates between the receiving team and
the pulling team, flipping on every turnover, until a goal is scored. We therefore split
each stream into per-point possessions and weave them (receiver run 1, puller run 1,
receiver run 2, ...) until a possession ends in a goal.
"""

from audl_parse import (
    BLOCK,
    DEFENSE_POINT,
    DROP,
    NEUTRAL_MARKERS,
    OFFENSE_POINT,
    PASS_COMPLETED,
    PULL,
    PULL_OB,
    QUARTER_END,
    THEY_SCORE,
    THROWAWAY,
    WE_SCORE,
    build_ext_id_map,
    build_roster_map,
    parse_events,
    warn_unknown_event,
    write_json,
)
from player_game_stats import OUTPUT_DIR

CALLAHAN = 6
STALL_OOB = 7
INJURY = 17
GOAL_EVENTS = (WE_SCORE, CALLAHAN)
THROWAWAY_EVENTS = (THROWAWAY, STALL_OOB)
CONTINUE = {10, 12, 14, 15}


def _split_points(events, where=""):
    """Split one team's stream into points (segmented by scores so both streams align).

    Each point -> {received: bool, possessions: [{throws, end, start_xy}, ...]}. A point
    is finalised when it ends in a score (t=21/t=22/t=6) OR when the quarter buzzer
    interrupts a point that actually got underway (a pull was thrown or a pass attempted) --
    those buzzer-interrupted points hold real throws the box score counts, so we keep them.
    A bare pre-set lineup (a line set just before the buzzer with no play) is discarded.
    Both streams see every quarter end, and a genuinely-played point has activity in both
    (the puller pulls, the receiver throws), so finalising on ``active`` keeps the two
    streams' point indices aligned. ``throws`` holds raw throw events; a stall ends a
    possession without a throw event.
    """
    points = []
    cur = None              # possessions list for the open point
    received = None
    poss = None
    pull_xy = None
    active = False          # has this point actually started (a pull or a throw)?

    def open_point():
        nonlocal cur, received, poss, pull_xy, active
        cur, received, poss, pull_xy, active = [], None, None, None, False

    def finalize(scored=False, buzzer=False):
        nonlocal cur, received, poss, active
        if cur is not None and (scored or buzzer):
            points.append({"received": bool(received), "possessions": cur})
        cur = received = poss = None
        active = False

    def new_poss(start_xy):
        nonlocal poss
        poss = {"throws": [], "end": None, "start_xy": start_xy}
        if cur is not None:
            cur.append(poss)

    def end_poss(kind):
        nonlocal poss
        if poss is not None:
            poss["end"] = kind
        poss = None

    open_point()
    for i, e in enumerate(events):
        t = e.get("t")
        holding = poss is not None and bool(poss["throws"])

        if t in (OFFENSE_POINT, DEFENSE_POINT):
            if cur is None:
                open_point()
            if received is None:
                received = (t == OFFENSE_POINT)
        elif t in (PULL, PULL_OB):
            pull_xy = (e.get("x"), e.get("y"))
            active = True
            end_poss("pull")
        elif t == PASS_COMPLETED:
            r = e.get("r")
            if poss is not None and poss["throws"] and poss["throws"][-1].get("r") == r:
                continue  # self re-list after a call
            if poss is None:
                new_poss(pull_xy)
                pull_xy = None
            poss["throws"].append(e)
            active = True
        elif t in GOAL_EVENTS:
            if poss is None:
                new_poss(pull_xy)
            poss["throws"].append(e)
            end_poss("goal")
            finalize(scored=True)
        elif t == THEY_SCORE:
            finalize(scored=True)
        elif t in THROWAWAY_EVENTS:
            if poss is None:
                new_poss(pull_xy)
            poss["throws"].append(e)
            active = True
            end_poss("turnover")
            pull_xy = (e.get("x"), e.get("y"))
        elif t == DROP:
            if poss is None:
                new_poss(pull_xy)
            poss["throws"].append(e)
            active = True
            end_poss("turnover")
        elif t == BLOCK:
            end_poss("stall" if holding else "block")
        elif t == INJURY:
            if holding and _lost_after(events, i):
                end_poss("stall")
        elif t in CONTINUE or t in NEUTRAL_MARKERS:
            pass  # mid-stream marker / unconfirmed code: keep the possession open
        elif t in QUARTER_END:
            # keep a genuinely-played point cut off by the buzzer (it has a pull/throw);
            # discard a bare pre-set lineup. Then open a fresh point for the next quarter.
            finalize(buzzer=active)
            open_point()
        else:
            warn_unknown_event(t, where)
            end_poss("other")

    return points


def _lost_after(events, i):
    for j in range(i + 1, len(events)):
        tj = events[j].get("t")
        if tj in (PASS_COMPLETED, *GOAL_EVENTS, *THROWAWAY_EVENTS):
            return False
        if tj in (THEY_SCORE, OFFENSE_POINT, DEFENSE_POINT, PULL, PULL_OB):
            return True
    return True


def _throw_rows(possession, start_xy):
    """Yield (thrower_event, receiver_event, success) tuples threading the chain."""
    rows = []
    prev_xy = start_xy
    prev_recv = None
    n = len(possession["throws"])
    for idx, e in enumerate(possession["throws"]):
        t = e.get("t")
        success = t in (PASS_COMPLETED, *GOAL_EVENTS)
        if t == DROP:
            receiver = e.get("r")  # the dropper
            end_xy = (e.get("x"), e.get("y"))
        elif t in THROWAWAY_EVENTS:
            receiver = None
            end_xy = (e.get("x"), e.get("y"))
        else:
            receiver = e.get("r")
            end_xy = (e.get("x"), e.get("y"))
        # how this possession concluded: goal / turnover / stall / block / other, or None
        # if it never closed (cut off by the quarter buzzer -- an unconcluded possession).
        possession_end = possession.get("end")
        # the scoring throw: the last throw of a possession that ended in a goal
        is_goal = possession_end == "goal" and idx == n - 1
        rows.append({
            "thrower_id": prev_recv,
            "receiver_id": receiver,
            "success": success,
            "is_goal": is_goal,
            "possession_end": possession_end,
            "x": prev_xy[0] if prev_xy else None,
            "y": prev_xy[1] if prev_xy else None,
            "end_x": end_xy[0],
            "end_y": end_xy[1],
        })
        if success and receiver is not None:
            prev_recv = receiver
            prev_xy = end_xy
        else:
            prev_recv = None
    return rows


def get_game_throws_stats(game, game_id=None, write=False, out_dir=OUTPUT_DIR):
    """Return the list of throw rows for a game (both teams, full game order)."""
    if game_id is None:
        game_id = game.get("game", {}).get("ext_game_id")

    home_id = game["tsgHome"].get("teamSeasonId")
    away_id = game["tsgAway"].get("teamSeasonId")
    home_pts = _split_points(parse_events(game["tsgHome"]), where=f"{game_id}/tsgHome")
    away_pts = _split_points(parse_events(game["tsgAway"]), where=f"{game_id}/tsgAway")

    # int roster id -> external playerID / name (home & away int ids never collide), so a
    # single merged map resolves both teams' throwers/receivers.
    ext_map, name_map = {}, {}
    for roster_key in ("rostersHome", "rostersAway"):
        rosters = game.get(roster_key, [])
        ext_map.update(build_ext_id_map(rosters))
        name_map.update({rid: info["name"] for rid, info in build_roster_map(rosters).items()})

    rows = []
    point_id = 0
    possession_id = 0
    # Points align 1:1 across streams as long as each score is logged in both streams.
    # The rare exception is an opponent callahan (t=6): the scored-on team's stream has
    # no they-score for it, so its point count is one short. We iterate the max length
    # and tolerate a missing side so that no throw is dropped (boundaries for the games
    # affected may drift slightly after the callahan).
    blank = {"received": None, "possessions": []}

    for k in range(max(len(home_pts), len(away_pts))):
        hp = home_pts[k] if k < len(home_pts) else blank
        ap = away_pts[k] if k < len(away_pts) else blank
        if hp["received"] is None and ap["received"] is None:
            continue
        # the receiving team plays the first possession of the point
        if hp["received"]:
            recv_side, recv_pts, pull_pts = "H", hp, ap
        else:
            recv_side, recv_pts, pull_pts = "A", ap, hp
        recv_team = home_id if recv_side == "H" else away_id
        pull_team = away_id if recv_side == "H" else home_id

        point_id += 1
        sequences = _weave(recv_pts["possessions"], pull_pts["possessions"])

        start_xy = _first_pull_xy(pull_pts["possessions"], recv_pts["possessions"])
        for offense_is_recv, poss in sequences:
            possession_id += 1
            off_team = recv_team if offense_is_recv else pull_team
            def_team = pull_team if offense_is_recv else recv_team
            seq = 0
            for row in _throw_rows(poss, start_xy):
                seq += 1
                thrower, receiver = row["thrower_id"], row["receiver_id"]
                rows.append({
                    "game_id": game_id,
                    "point_id": point_id,
                    "possession_id": possession_id,
                    "sequence_id": seq,
                    "offense_team_id": off_team,
                    "defense_team_id": def_team,
                    "is_o_line": offense_is_recv,  # offense received this point (O-line)
                    **row,
                    "thrower_ext_id": ext_map.get(thrower),
                    "thrower_name": name_map.get(thrower),
                    "receiver_ext_id": ext_map.get(receiver),
                    "receiver_name": name_map.get(receiver),
                })
            # next possession starts where this one ended (the turnover disc)
            if poss["throws"]:
                last = poss["throws"][-1]
                start_xy = (last.get("x"), last.get("y"))

    if write:
        write_json(rows, f"{out_dir}/{game_id}.throws.json")
    return rows


def _first_pull_xy(pull_possessions, recv_possessions):
    for p in pull_possessions + recv_possessions:
        if p.get("start_xy") and p["start_xy"][0] is not None:
            return p["start_xy"]
    return None


def _weave(recv_possessions, pull_possessions):
    """Order a point's possessions: receiver and puller runs alternate (the receiver
    plays first), flipping on each turnover. Every possession is emitted (no throw is
    dropped); when one team's runs are exhausted the other's remaining runs follow.
    """
    out = []
    ri = pi = 0
    turn = "recv"
    while ri < len(recv_possessions) or pi < len(pull_possessions):
        if turn == "recv" and ri < len(recv_possessions):
            out.append((True, recv_possessions[ri])); ri += 1
            turn = "pull"
        elif turn == "pull" and pi < len(pull_possessions):
            out.append((False, pull_possessions[pi])); pi += 1
            turn = "recv"
        else:
            turn = "pull" if turn == "recv" else "recv"
    return out


if __name__ == "__main__":
    from audl_parse import list_game_ids, load_game

    for gid in list_game_ids():
        rows = get_game_throws_stats(load_game(gid), game_id=gid, write=True)
        n_pts = max((r["point_id"] for r in rows), default=0)
        print(f"{gid}: {len(rows)} throws, {n_pts} points")
