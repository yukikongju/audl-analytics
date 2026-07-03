"""Validate reconstructed player game stats.

Layer 1 (always runs with local sample data): team-level reconciliation vs the tsg summary
fields in stg_games (ground truth) + internal consistency.

Layer 2 (skipped unless the network / a fixture is available): join to the live
playerGameStats API by playerID and assert the core count fields match.
"""

import pytest

from main import run
from pipeline_utils import list_local_game_ids
from player_game_stats import (
    CORE_FIELDS,
    EXACT_FIELDS,
    YARD_FIELDS,
    _slug_map,
    build_player_game_stats,
    fetch_player_game_stats,
)

LOCAL_GAMES = list_local_game_ids()
needs_local = pytest.mark.skipif(not LOCAL_GAMES, reason="no local AUDLStats sample data")


def _build(game_id):
    tables = run(game_id, out_dir="/tmp/audl-pgs-test", local=True)
    rows = build_player_game_stats(
        tables["stg_throws"], tables["stg_pulls"], tables["stg_point_lineups"],
        blocks=tables["stg_blocks"], team_slug_by_id=_slug_map(tables["stg_games"]),
        game_id=game_id,
    )
    return rows, tables


def _sum(rows, team_slug, field):
    return sum(r[field] for r in rows if r["teamID"] == team_slug)


@needs_local
@pytest.mark.parametrize("game_id", LOCAL_GAMES)
def test_team_totals_reconcile_with_stg_games(game_id):
    rows, tables = _build(game_id)
    slug = _slug_map(tables["stg_games"])
    for g in tables["stg_games"]:
        s = slug[g["teamSeasonId"]]
        assert _sum(rows, s, "completions") == g["completionsNumer"], f"{game_id} {s} completions"
        assert _sum(rows, s, "blocks") == g["blocks"], f"{game_id} {s} blocks"
        turnovers = sum(
            _sum(rows, s, f) for f in ("throwaways", "stalls", "drops")
        )
        assert turnovers == g["turnovers"], f"{game_id} {s} turnovers"
        # goals credited once each (incl. callahan catches) == final score
        assert _sum(rows, s, "goals") == g["score"], f"{game_id} {s} goals"
        assert _sum(rows, s, "hucksCompleted") == g["hucksNumer"], f"{game_id} {s} hucksNumer"
        assert _sum(rows, s, "hucksAttempted") == g["hucksDenom"], f"{game_id} {s} hucksDenom"


# Unrecorded-player sentinels the API doesn't emit; they carry stray touches but no lineup.
_SENTINEL_IDS = {None, "", "unknown"}


@needs_local
@pytest.mark.parametrize("game_id", LOCAL_GAMES)
def test_internal_consistency(game_id):
    rows, tables = _build(game_id)
    assert rows, "expected player rows"
    lineup_players = {p for r in tables["stg_point_lineups"] for p in r["lineup"]}
    for r in rows:
        pid = r["playerID"]
        # a real player who took the field appears in a lineup with >=1 point; anything with
        # no lineup presence must be an unrecorded-player sentinel, not a dropped real player.
        if pid in lineup_players:
            assert r["oPointsPlayed"] + r["dPointsPlayed"] >= 1, pid
        else:
            assert pid in _SENTINEL_IDS, f"non-sentinel player {pid} missing from lineups"
        # no negative counts (yards may legitimately be negative — a backwards throw)
        assert all(r[f] >= 0 for f in CORE_FIELDS if f not in YARD_FIELDS), pid
        # assists never exceed completions; hucks completed never exceed attempted
        assert r["assists"] <= r["completions"], pid
        assert r["hucksCompleted"] <= r["hucksAttempted"], pid


@needs_local
def test_live_api_exact_fields_match():
    """Assert the exact fields (incl. the four O/D-point fields) match the live API (±1 yards).

    The informational fields (secondsPlayed, opportunities) are best-effort and reported by
    ``python -m player_game_stats``, not asserted here. Skips when the network is unavailable.
    """
    game_id = "2026-05-10-MTL-PIT"
    if game_id not in LOCAL_GAMES:
        pytest.skip("sample game not present locally")
    try:
        api_rows = fetch_player_game_stats(game_id)
    except Exception as exc:  # network down / offline CI
        pytest.skip(f"live playerGameStats API unavailable: {exc}")

    rows, _ = _build(game_id)
    api_by_id = {r["player"]["playerID"]: r for r in api_rows}
    built_by_id = {r["playerID"]: r for r in rows}

    mismatches = []
    for pid, api in api_by_id.items():
        got = built_by_id.get(pid)
        if got is None:
            continue
        for f in EXACT_FIELDS:
            exp = api.get(f)
            if exp is None:
                continue
            tol = 1 if f in YARD_FIELDS else 0
            if abs((got[f] or 0) - exp) > tol:
                mismatches.append(f"{pid}.{f}: got {got[f]} exp {exp}")
    assert not mismatches, "exact-field mismatches:\n" + "\n".join(mismatches[:40])
