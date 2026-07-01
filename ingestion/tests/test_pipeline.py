"""Smoke + reconciliation tests for the staging pipeline.

The unit tests (``yards``) run anywhere. The pipeline tests use the local sample games in
``~/Data/AUDLStats/`` and are skipped when that data isn't present (e.g. in CI).
"""

import pytest

from pipeline_utils import list_local_game_ids, load_local_game, yards
from main import run

LOCAL_GAMES = list_local_game_ids()
needs_local = pytest.mark.skipif(not LOCAL_GAMES, reason="no local AUDLStats sample data")


def test_yards_forward_and_capped():
    assert yards(0, 40) == 40
    assert yards(90, 110) == 10  # capped at the goal line (y=100)
    assert yards(50, 50) == 0
    assert yards(None, 40) is None


@needs_local
@pytest.mark.parametrize("game_id", LOCAL_GAMES)
def test_run_produces_four_tables(tmp_path, game_id):
    tables = run(game_id, out_dir=str(tmp_path), local=True)
    assert set(tables) == {"stg_throws", "stg_pulls", "stg_point_lineups", "stg_games"}
    assert len(tables["stg_games"]) == 2  # one row per team
    assert tables["stg_throws"], "expected at least one throw"
    for name in tables:
        assert (tmp_path / game_id / f"{name}.json").exists()


@needs_local
@pytest.mark.parametrize("game_id", LOCAL_GAMES)
def test_completions_reconcile_with_tsg(game_id):
    """Σ is_completion per team == tsg.completionsNumer (ground truth)."""
    tables = run(game_id, out_dir="/tmp/audl-test-out", local=True)
    game = load_local_game(game_id)
    for side in ("Home", "Away"):
        team_id = game["game"][f"team_season_id_{side.lower()}"]
        expected = game[f"tsg{side}"]["completionsNumer"]
        got = sum(
            1
            for r in tables["stg_throws"]
            if r["offense_team_id"] == team_id and r.get("is_completion")
        )
        assert got == expected, f"{game_id} {side}: completions {got} != {expected}"
