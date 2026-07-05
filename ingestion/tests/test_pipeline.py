"""Smoke + reconciliation tests for the processing pipeline.

The unit tests (``yards``) run anywhere. The pipeline tests read the extracted sample games
from ``AUDL_SOURCE_DIR`` and are skipped when that data isn't present (e.g. in CI).
"""

import pytest

from pipeline_utils import game_month, game_year, list_source_game_ids, load_source_game_stats, yards
from main import run

LOCAL_GAMES = list_source_game_ids()
needs_local = pytest.mark.skipif(not LOCAL_GAMES, reason="no extracted AUDLStats sample data")


def test_yards_forward_and_capped():
    assert yards(0, 40) == 40
    assert yards(90, 110) == 10  # capped at the goal line (y=100)
    assert yards(50, 50) == 0
    assert yards(None, 40) is None


@needs_local
@pytest.mark.parametrize("game_id", LOCAL_GAMES)
def test_run_produces_five_tables(tmp_path, game_id):
    tables = run(game_id, processed_root=str(tmp_path))
    assert set(tables) == {"ext_throws", "ext_pulls", "ext_point_lineups", "ext_blocks",
                           "ext_games"}
    assert len(tables["ext_games"]) == 2  # one row per team
    assert tables["ext_throws"], "expected at least one throw"
    year, month = game_year(game_id), game_month(game_id)
    for name in tables:
        assert (tmp_path / name / f"season={year}" / f"month={month}" / f"{game_id}.parquet").exists()


@needs_local
@pytest.mark.parametrize("game_id", LOCAL_GAMES)
def test_completions_reconcile_with_tsg(tmp_path, game_id):
    """Σ is_completion per team == tsg.completionsNumer (ground truth)."""
    tables = run(game_id, processed_root=str(tmp_path))
    game = load_source_game_stats(game_id)
    for side in ("Home", "Away"):
        team_id = game["game"][f"team_season_id_{side.lower()}"]
        expected = game[f"tsg{side}"]["completionsNumer"]
        got = sum(
            1
            for r in tables["ext_throws"]
            if r["offense_team_id"] == team_id and r.get("is_completion")
        )
        assert got == expected, f"{game_id} {side}: completions {got} != {expected}"
