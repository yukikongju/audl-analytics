"""Reconstruct point / possession / throw ordering from the two gameEvents streams.

The two per-team streams cannot be merged by ``timestamp``: in some games each stream is on
its own clock (e.g. COL-ORE's streams are ~5 days apart), so a global time-sort interleaves
them completely wrong. Instead we use the clock-independent structure the tsg reconstruction
relies on: every point appears in BOTH streams (each ends with a score both sides log), so we

  1. split each stream into points (segmenting on score events),
  2. pair point ``k`` of home with point ``k`` of away, and
  3. within a point, weave the two teams' possessions by strict alternation -- the receiving
     team throws first, possession flips on every turnover.

Each stream lists only its OWN team's offensive touches, so a throw is always made by the
team whose stream it came from; that is how offense/defense are attributed. Blocks (``t11``)
are logged by the team that MADE them, so a point's blocks are consumed in order to attach a
``defender`` to the opposing throwaways that ended a possession.
"""

from constants import (
    BLOCK,
    CALLAHAN_OURS,
    CALLAHAN_THEIRS,
    DROP,
    GOAL,
    POINT_START,
    PULL_EVENTS,
    QUARTER_END,
    SCORE_THEIRS,
    STALL_OURS,
    START_O_POINT,
    SUB_EVENTS,
    THROW_EVENTS,
    THROWAWAY_OURS,
    warn_unknown_event,
)


def _other(side):
    return "A" if side == "H" else "H"


def _split_points(events, where=""):
    """Split one stream into points. Each point:

        {received, line_events, pull_events, blocks, possessions, scored}

    ``received`` is True if this stream's team received (its start was START_O_POINT).
    ``possessions`` is a list of ``{throws, end}`` for this team's offensive runs. ``scored``
    is 'us' / 'them' / None (buzzer) -- who ended the point.
    """
    points = []
    cur = None
    poss = None

    def new_point():
        return {
            "received": None, "line_events": [], "pull_events": [],
            "blocks": [], "possessions": [], "scored": None, "active": False,
        }

    def finalize(scored):
        nonlocal cur, poss
        if cur is not None and (scored is not None or cur["active"]):
            cur["scored"] = scored
            points.append(cur)
        cur, poss = None, None

    def new_poss():
        nonlocal poss
        poss = {"throws": [], "end": None}
        cur["possessions"].append(poss)

    def end_poss(kind):
        nonlocal poss
        if poss is not None:
            poss["end"] = kind
            poss = None

    for e in events:
        t = e.get("type")
        warn_unknown_event(t, where)

        if cur is None:
            if t in POINT_START:
                cur = new_point()
            else:
                continue  # stray event before the first point start

        if t in POINT_START:
            if cur["received"] is None:
                cur["received"] = t == START_O_POINT
            cur["line_events"].append(e)
        elif t in SUB_EVENTS:
            cur["line_events"].append(e)
        elif t in PULL_EVENTS:
            cur["pull_events"].append(e)
            cur["active"] = True
            end_poss("pull")
        elif t == BLOCK:
            cur["blocks"].append(e.get("defender"))
            cur["active"] = True
        elif t == CALLAHAN_OURS:
            cur["blocks"].append(e.get("defender"))
            cur["active"] = True
            finalize("us")               # this team's defender scored a callahan
        elif t in THROW_EVENTS:
            if poss is None:
                new_poss()
            poss["throws"].append(e)
            cur["active"] = True
            if t == GOAL:
                end_poss("goal")
                finalize("us")
            elif t == CALLAHAN_THEIRS:
                end_poss("callahan")
                finalize("them")         # we threw it, opponent caught a callahan
            elif t in (DROP, THROWAWAY_OURS, STALL_OURS):
                end_poss("turnover")
        elif t == SCORE_THEIRS:
            finalize("them")
        elif t in QUARTER_END:
            finalize(None)

    finalize(None)
    return points


def _pair_points(H, A):
    """Pair each stream's points into physical points, robust to buzzer-point mismatches.

    Both streams log every SCORE in the same order, so scoring points pair 1:1. A buzzer
    (quarter-end, ``scored is None``) point may appear in only one stream; pairing on the
    score sequence keeps the scoring points aligned instead of letting a lone buzzer point
    shift every subsequent pairing (which would scramble cross-stream block attribution and
    point ids). Returns a list of ``(home_point|None, away_point|None)``.
    """
    pairs = []
    i = j = 0
    while i < len(H) or j < len(A):
        hp = H[i] if i < len(H) else None
        ap = A[j] if j < len(A) else None
        h_buzz = hp is not None and hp["scored"] is None
        a_buzz = ap is not None and ap["scored"] is None
        if hp is not None and ap is not None and not h_buzz and not a_buzz:
            pairs.append((hp, ap)); i += 1; j += 1          # both scored -> same point
        elif h_buzz and a_buzz:
            pairs.append((hp, ap)); i += 1; j += 1          # both quarter-ended together
        elif h_buzz:
            pairs.append((hp, None)); i += 1                # home-only buzzer fragment
        elif a_buzz:
            pairs.append((None, ap)); j += 1                # away-only buzzer fragment
        elif hp is not None:
            pairs.append((hp, None)); i += 1
        else:
            pairs.append((None, ap)); j += 1
    return pairs


def _weave(recv_possessions, pull_possessions):
    """Order a point's possessions: receiver first, alternating on each turnover.

    Every possession is emitted; when one side's runs are exhausted the other's follow.
    Returns a list of ``(is_receiver, possession)``.
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


def _annotated(side, team, opp, event, **extra):
    row = {
        "side": side, "team_id": team, "opp_team_id": opp, "event": event,
        "point_id": None, "possession_id": None, "sequence_id": None,
        "offense_team_id": None, "defense_team_id": None, "defender_id": None,
        "home_score": None, "away_score": None, "scorer_side": None,
    }
    row.update(extra)
    return row


def build_timeline(home_events, away_events, home_team, away_team, where=""):
    """Return a flat list of annotated events (line/pull/throw), point- and possession-tagged.

    Throw events carry ``possession_id``/``sequence_id``/``offense_team_id``/
    ``defense_team_id``/``defender_id``. All events carry ``point_id`` and the score ENTERING
    the point (``home_score``/``away_score``) plus ``scorer_side`` (who won the point).
    """
    H = _split_points(home_events, f"{where}/H")
    A = _split_points(away_events, f"{where}/A")
    side_team = {"H": home_team, "A": away_team}

    ann = []
    hs = as_ = 0
    poss_counter = 0

    for k, (hp, ap) in enumerate(_pair_points(H, A)):
        pid = k + 1
        enter_h, enter_a = hs, as_

        # which side received (holds the first possession)
        if hp and hp["received"] is True:
            recv = "H"
        elif ap and ap["received"] is True:
            recv = "A"
        elif hp and hp["received"] is False:
            recv = "A"
        elif ap and ap["received"] is False:
            recv = "H"
        else:
            recv = "H"
        puller = _other(recv)

        # who scored this point
        scorer = None
        for pt, side in ((hp, "H"), (ap, "A")):
            if not pt or pt["scored"] is None:
                continue
            scorer = side if pt["scored"] == "us" else _other(side)
        if scorer == "H":
            hs += 1
        elif scorer == "A":
            as_ += 1

        common = dict(point_id=pid, home_score=enter_h, away_score=enter_a,
                      scorer_side=scorer)

        # line + pull events (both streams)
        for pt, side in ((hp, "H"), (ap, "A")):
            if not pt:
                continue
            for e in pt["line_events"] + pt["pull_events"]:
                ann.append(_annotated(side, side_team[side], side_team[_other(side)],
                                       e, **common))

        # throw possessions, woven, with block attachment
        recv_poss = (hp if recv == "H" else ap)
        pull_poss = (hp if puller == "H" else ap)
        recv_list = recv_poss["possessions"] if recv_poss else []
        pull_list = pull_poss["possessions"] if pull_poss else []
        blocks = {
            "H": list(hp["blocks"]) if hp else [],
            "A": list(ap["blocks"]) if ap else [],
        }

        for is_recv, p in _weave(recv_list, pull_list):
            poss_counter += 1
            off_side = recv if is_recv else puller
            def_side = _other(off_side)
            throws = p["throws"]
            for j, e in enumerate(throws):
                defender = None
                if (j == len(throws) - 1 and p["end"] == "turnover"
                        and e.get("type") == THROWAWAY_OURS and blocks[def_side]):
                    defender = blocks[def_side].pop(0)
                ann.append(_annotated(
                    off_side, side_team[off_side], side_team[def_side], e,
                    possession_id=poss_counter, sequence_id=j + 1,
                    offense_team_id=side_team[off_side],
                    defense_team_id=side_team[def_side],
                    defender_id=defender, **common,
                ))

    return ann
