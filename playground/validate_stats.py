"""Validate get_player_game_stats against the df_stats ground truth.

Ground truth: per-player JSON files in ~/Data/AUDLStats/players_stats/ (keyed by ext
playerID = filename stem), each with a ``stats`` list of per-game records, merged with
players.csv for name/team. We scope to the games available locally and diff each of the
26 box-score fields per player.
"""

import glob
import json
import os
from pathlib import Path

import pandas as pd

from audl_parse import (
    BLOCK,
    DEFENSE_POINT,
    DROP,
    OFFENSE_POINT,
    PASS_COMPLETED,
    PULL,
    PULL_OB,
    QUARTER_END,
    STALL,
    THEY_SCORE,
    THROWAWAY,
    WE_SCORE,
    build_roster_map,
    list_game_ids,
    load_game,
    parse_events,
)
from player_game_stats import _STAT_FIELDS, get_player_game_stats
from throws_stats import get_game_throws_stats

PLAYERS_DIR = Path("~/Data/AUDLStats/players_stats").expanduser()


def build_ground_truth(game_ids):
    """Build df_stats restricted to ``game_ids``, keyed by (gameID, firstName, lastName)."""
    game_ids = set(game_ids)
    paths = glob.glob(os.fspath(PLAYERS_DIR / "*.json"))
    records = []
    for path in paths:
        pid = Path(path).stem
        with open(path) as f:
            data = json.load(f)
        for rec in data.get("stats", []):
            if rec.get("gameID") in game_ids:
                rec = dict(rec)
                rec["playerID"] = pid
                records.append(rec)
    df = pd.DataFrame(records)

    players = pd.read_csv(PLAYERS_DIR / "players.csv")
    df = df.merge(players[["playerID", "firstName", "lastName", "teamID"]],
                  on="playerID", how="left")
    df["name"] = (df["firstName"].fillna("") + " " + df["lastName"].fillna("")).str.strip()
    return df


def build_predictions(game_ids):
    rows = []
    for gid in game_ids:
        rows.extend(get_player_game_stats(load_game(gid), game_id=gid))
    return pd.DataFrame(rows)


def main():
    game_ids = list_game_ids()
    truth = build_ground_truth(game_ids)
    pred = build_predictions(game_ids)

    # join on (gameID, player name) -- robust to the missing ext-id mapping
    merged = pred.merge(
        truth,
        left_on=["gameID", "playerName"],
        right_on=["gameID", "name"],
        how="inner",
        suffixes=("_pred", "_true"),
    )
    n_pred, n_true, n_join = len(pred), len(truth), len(merged)
    print(f"pred rows={n_pred}  truth rows={n_true}  joined={n_join}")
    unmatched = set(zip(pred["gameID"], pred["playerName"])) - set(
        zip(merged["gameID"], merged["playerName"]))
    if unmatched:
        print(f"  {len(unmatched)} predicted players unmatched (e.g. {list(unmatched)[:5]})")

    summary = []
    samples = {}
    for f in _STAT_FIELDS:
        pcol, tcol = f"{f}_pred", f"{f}_true"
        if pcol not in merged or tcol not in merged:
            continue
        p = pd.to_numeric(merged[pcol], errors="coerce").fillna(0)
        t = pd.to_numeric(merged[tcol], errors="coerce").fillna(0)
        diff = (p - t)
        mism = diff != 0
        summary.append({
            "field": f,
            "n_mismatch": int(mism.sum()),
            "n_total": len(merged),
            "pct_match": round(100 * (1 - mism.mean()), 1),
            "max_abs_diff": float(diff.abs().max()),
        })
        if mism.any():
            cols = ["gameID", "playerName", pcol, tcol]
            samples[f] = merged.loc[mism, cols].head(6)

    sdf = pd.DataFrame(summary).sort_values(["n_mismatch", "field"], ascending=[False, True])
    pd.set_option("display.width", 200)
    print("\n=== Per-field accuracy (worst first) ===")
    print(sdf.to_string(index=False))

    print("\n=== Sample mismatches ===")
    for f in sdf[sdf.n_mismatch > 0]["field"]:
        print(f"\n--- {f} ---")
        print(samples[f].to_string(index=False))

    # cheap secondary oracle from tsg aggregates
    print("\n=== tsg aggregate cross-check ===")
    for gid in game_ids:
        game = load_game(gid)
        prows = [r for r in get_player_game_stats(game, game_id=gid)]
        for side, key in (("H", "tsgHome"), ("A", "tsgAway")):
            tsg = game[key]
            tid = tsg.get("teamSeasonId")
            team_rows = [r for r in prows if r["teamID"] == tid]
            blk = sum(r["blocks"] for r in team_rows)
            comp = sum(r["completions"] for r in team_rows)
            to = sum(r["throwaways"] + r["stalls"] + r["drops"] for r in team_rows)
            hc = sum(r["hucksCompleted"] for r in team_rows)
            ha = sum(r["hucksAttempted"] for r in team_rows)
            print(f"{gid} {key}: blocks {blk}/{tsg.get('blocks')}  "
                  f"completions {comp}/{tsg.get('completionsNumer')}  "
                  f"turnovers {to}/{tsg.get('turnovers')}  "
                  f"hucks {hc}-{ha}/{tsg.get('hucksNumer')}-{tsg.get('hucksDenom')}")


def _throws_box(rows):
    """Derive a per-player box score (keyed by ext playerID) purely from throw rows.

    Only the fields a throw stream can express directly:
      completions = successful throws made (thrower of a real throw, not the pickup)
      catches     = successful receptions (receiver of a real throw; a goal IS a catch)
      goals/assists = the receiver/thrower of each point's scoring throw (the last throw
                      of the last possession of the point -- every point in the throws
                      output ends in a goal).
    A throw whose thrower_id is None is the possession's first touch (pickup) and is not a
    completion/catch, matching player_game_stats. ``unmapped`` counts real throw endpoints
    with no ext id (ambiguous name vs players.csv) so undercounting is visible.
    """
    from collections import defaultdict

    box = defaultdict(lambda: {"completions": 0, "catches": 0, "goals": 0, "assists": 0})
    unmapped = {"thrower": 0, "receiver": 0}

    for r in rows:
        if not (r["success"] and r["thrower_id"] is not None):
            continue  # incomplete, or the pickup (no thrower) -- not a completion/catch
        if r["thrower_ext_id"] is not None:
            box[r["thrower_ext_id"]]["completions"] += 1
        else:
            unmapped["thrower"] += 1
        if r["receiver_id"] is not None:
            if r["receiver_ext_id"] is not None:
                box[r["receiver_ext_id"]]["catches"] += 1
            else:
                unmapped["receiver"] += 1

    for r in rows:
        if not r.get("is_goal"):
            continue
        if r["receiver_ext_id"] is not None:
            box[r["receiver_ext_id"]]["goals"] += 1
        if r["thrower_id"] is not None and r["thrower_ext_id"] is not None:
            box[r["thrower_ext_id"]]["assists"] += 1

    return box, unmapped


def validate_throws_vs_truth():
    """Cross-check throw-derived completions/catches/goals/assists vs the df_stats truth.

    This is the real proof that throws_events agree with the ground truth: we rebuild the
    box score from the throw rows alone (joined to players.csv by ext id) and diff it
    against df_stats. Residual diffs are expected only on buzzer-nullified points (throws
    excludes them) and the rare opponent-callahan boundary drift.
    """
    fields = ["completions", "catches", "goals", "assists"]
    game_ids = list_game_ids()
    truth = build_ground_truth(game_ids)
    tkey = truth.set_index(["gameID", "playerID"])

    print("\n=== throws_events vs ground truth (ext-id join) ===")
    totals = {f: [0, 0] for f in fields}  # field -> [n_mismatch, n_total]
    over = {f: 0 for f in fields}         # field -> count of throws > truth (phantom stats)
    per_game = {gid: {f: 0 for f in fields} for gid in game_ids}  # field -> net Δ per game
    for gid in game_ids:
        rows = get_game_throws_stats(load_game(gid), game_id=gid)
        box, unmapped = _throws_box(rows)
        if unmapped["thrower"] or unmapped["receiver"]:
            print(f"  {gid}: unmapped throw endpoints "
                  f"(no ext id): {unmapped['thrower']} throwers, "
                  f"{unmapped['receiver']} receivers")
        for ext_id, derived in box.items():
            try:
                trow = tkey.loc[(gid, ext_id)]
            except KeyError:
                continue
            for f in fields:
                tv = int(pd.to_numeric(trow.get(f, 0)))
                dv = derived[f]
                totals[f][0] += int(dv != tv)
                totals[f][1] += 1
                over[f] += int(dv > tv)
                per_game[gid][f] += dv - tv
                if dv != tv:
                    name = trow.get("name")
                    print(f"    {gid} {name} {f}: throws={dv} truth={tv} (Δ{dv - tv})")

    print("\n  --- summary (throws-derived vs truth) ---")
    for f in fields:
        mm, n = totals[f]
        pct = round(100 * (1 - mm / n), 1) if n else 0.0
        flag = "  <-- PHANTOM (throws>truth!)" if over[f] else "  (all shortfalls)"
        print(f"  {f:12s}: {n - mm}/{n} match ({pct}%){flag if mm else ''}")
    print("\n  --- net Δ (throws - truth) per game; negative = throws omits, never invents ---")
    for gid in game_ids:
        deltas = "  ".join(f"{f}={per_game[gid][f]:+d}" for f in fields)
        print(f"  {gid}: {deltas}")


def _team_points(events):
    """Walk one team's stream and count O/D points and scores (segmenting by score).

    A point's phase is the team's OWN start: t=1 -> offense (received), t=2 -> defense
    (pulled). Mirrors tsg ``oLinePoints``/``dLinePoints``/``oLineScores``/``dLineScores``.
    """
    o_pts = d_pts = o_sc = d_sc = 0
    phase = None
    started = False
    had_play = False  # did the point actually start (a pull/throw) before ending?
    play_events = {PULL, PULL_OB, PASS_COMPLETED, THROWAWAY, DROP, STALL, BLOCK}

    def count():
        nonlocal o_pts, d_pts
        if phase == "O":
            o_pts += 1
        elif phase == "D":
            d_pts += 1

    for e in events:
        t = e.get("t")
        if t == OFFENSE_POINT and not started:
            phase, started, had_play = "O", True, False
        elif t == DEFENSE_POINT and not started:
            phase, started, had_play = "D", True, False
        elif t in play_events:
            had_play = True
        elif t in (WE_SCORE, 6):  # we scored (t=6 callahan)
            if started:
                count()
                if phase == "O":
                    o_sc += 1
                else:
                    d_sc += 1
            phase, started = None, False
        elif t == THEY_SCORE:
            if started:
                count()  # a point we played but the opponent scored
            phase, started = None, False
        elif t in QUARTER_END:
            if started and had_play:  # a real point interrupted by the buzzer still counts
                count()
            phase, started = None, False
    return o_pts, d_pts, o_sc, d_sc


def _throws_team_aggregates(rows, redzone_y=80):
    """Possession & red-zone counts per team, derived from throw rows.

    An O-line possession belongs to a team that received the point (``is_o_line``); a
    D-line (break-chance) possession to the pulling team. A possession counts as real
    unless ``possession_end`` is a fragment marker -- "other"/"pull"/"block" -- which means
    a mid-possession event (timeout/sub) split the physical possession; the same possession
    continues and is counted once at its true end (goal/turnover/stall, or None when the
    quarter buzzer cuts it off -- a real possession tsg still counts). A red-zone possession
    is a real one whose disc is CAUGHT in the attacking 20 (80<=y<100); it scores on a goal.
    """
    from collections import defaultdict

    fragment_ends = {"other", "pull", "block"}  # marker-induced splits, not real possessions
    poss_team, poss_oline, poss_real = {}, {}, {}
    rz_poss, rz_score = defaultdict(set), defaultdict(set)
    for r in rows:
        p = r["possession_id"]
        poss_team[p] = r["offense_team_id"]
        poss_oline[p] = r["is_o_line"]
        poss_real[p] = r.get("possession_end") not in fragment_ends
        if not poss_real[p]:
            continue
        # red zone = disc CAUGHT in the attacking 20 (80<=y<100). A huck straight into the
        # endzone never gets possessed in the red zone, so it is NOT a red-zone possession
        # (this is why tsg redZoneScores < total goals).
        if r["success"] and r["end_y"] is not None and redzone_y <= r["end_y"] < 100:
            rz_poss[r["offense_team_id"]].add(p)
    for r in rows:  # a possession scores in the red zone iff it was a red-zone possession
        if r.get("is_goal") and r["possession_id"] in rz_poss[r["offense_team_id"]]:
            rz_score[r["offense_team_id"]].add(r["possession_id"])

    olp, dlp = defaultdict(int), defaultdict(int)
    for p, team in poss_team.items():
        if not poss_real[p]:
            continue
        if poss_oline[p]:
            olp[team] += 1
        else:
            dlp[team] += 1

    return {
        "oLinePossessions": olp, "dLinePossessions": dlp,
        "redZonePossessions": {k: len(v) for k, v in rz_poss.items()},
        "redZoneScores": {k: len(v) for k, v in rz_score.items()},
    }


def validate_team_stats():
    """Cross-check reconstructed team aggregates vs ALL 14 tsg team-stat fields."""
    print("\n=== team stats vs tsg ground truth (all 14 fields) ===")
    fields = [
        "completionsNumer", "completionsDenom", "hucksNumer", "hucksDenom", "blocks",
        "turnovers", "oLinePoints", "oLineScores", "dLinePoints", "dLineScores",
        "oLinePossessions", "dLinePossessions", "redZonePossessions", "redZoneScores",
    ]
    approx = {"redZonePossessions", "redZoneScores"}  # depend on a red-zone y threshold
    tally = {f: [0, 0] for f in fields}
    for gid in list_game_ids():
        game = load_game(gid)
        ps = get_player_game_stats(game, game_id=gid)
        thr = _throws_team_aggregates(get_game_throws_stats(game, game_id=gid))
        for key in ("tsgHome", "tsgAway"):
            tsg = game[key]
            tid = tsg["teamSeasonId"]
            tr = [r for r in ps if r["teamID"] == tid]
            comp = sum(r["completions"] for r in tr)
            to = sum(r["throwaways"] + r["stalls"] + r["drops"] for r in tr)
            o_pts, d_pts, o_sc, d_sc = _team_points(parse_events(tsg))
            recon = {
                "completionsNumer": comp,
                "completionsDenom": comp + to,
                "hucksNumer": sum(r["hucksCompleted"] for r in tr),
                "hucksDenom": sum(r["hucksAttempted"] for r in tr),
                "blocks": sum(r["blocks"] for r in tr),
                "turnovers": to,
                "oLinePoints": o_pts, "oLineScores": o_sc,
                "dLinePoints": d_pts, "dLineScores": d_sc,
                "oLinePossessions": thr["oLinePossessions"].get(tid, 0),
                "dLinePossessions": thr["dLinePossessions"].get(tid, 0),
                "redZonePossessions": thr["redZonePossessions"].get(tid, 0),
                "redZoneScores": thr["redZoneScores"].get(tid, 0),
            }
            diffs = []
            for f in fields:
                rv, tv = recon[f], tsg.get(f)
                ok = rv == tv
                tally[f][1] += 1
                tally[f][0] += int(not ok)
                if not ok:
                    diffs.append(f"{f} {rv}/{tv}")
            tag = "OK" if not diffs else "  ".join(diffs)
            print(f"  {gid} {key}: {tag}")

    print("\n  --- per-field (exact over all team-games; * = threshold-approx) ---")
    for f in fields:
        mm, n = tally[f]
        star = "*" if f in approx else " "
        print(f"  {f:20s}{star}: {n - mm}/{n} exact")


def validate_throws():
    """Internal-consistency checks for throws_events (no ground truth exists)."""
    from itertools import groupby

    print("\n=== throws_events internal consistency ===")
    for gid in list_game_ids():
        game = load_game(gid)
        rows = get_game_throws_stats(game, game_id=gid)
        # sequence_id resets to 1 each possession and is contiguous
        bad_seq = 0
        for _, grp in groupby(rows, key=lambda r: r["possession_id"]):
            seqs = [r["sequence_id"] for r in grp]
            if seqs != list(range(1, len(seqs) + 1)):
                bad_seq += 1
        # possession_id increments by 1 and point_id is non-decreasing
        pids = [r["possession_id"] for r in rows]
        mono = all(b - a in (0, 1) for a, b in zip(pids, pids[1:]))
        n_points = max((r["point_id"] for r in rows), default=0)
        # completions cross-check vs the validated player box score
        ps = get_player_game_stats(game, game_id=gid)
        for key in ("tsgHome", "tsgAway"):
            tid = game[key]["teamSeasonId"]
            ct = sum(1 for r in rows if r["offense_team_id"] == tid
                     and r["success"] and r["thrower_id"] is not None)
            cp = sum(r["completions"] for r in ps if r["teamID"] == tid)
            tag = "ok" if ct == cp else f"diff {cp - ct} (buzzer-nullified points)"
            print(f"  {gid} {key}: throws-completions {ct} vs box {cp} -> {tag}")
        print(f"  {gid}: {len(rows)} throws, {n_points} points, "
              f"bad-sequence possessions={bad_seq}, possession_id monotonic={mono}")


if __name__ == "__main__":
    main()
    validate_team_stats()
    validate_throws()
    validate_throws_vs_truth()
