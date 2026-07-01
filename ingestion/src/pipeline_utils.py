"""Shared helpers for the AUDL staging transforms.

Kept deliberately dependency-light: only ``requests`` (for fetching) and stdlib. The
transforms themselves are pure functions over already-fetched JSON, so they can be unit
tested against the local sample files in ``~/Data/AUDLStats/`` without any network.
"""

import json
import os
import requests
from pathlib import Path

BASE_URL = "https://www.backend.ufastats.com"

# Local sample data (for offline dev / validation). Not used by main.py's live fetch.
GAME_STATS_DIR = Path("~/Data/AUDLStats/game_stats").expanduser()
GAME_EVENTS_DIR = Path("~/Data/AUDLStats/game_events").expanduser()

from constants import ENDZONE_Y  # noqa: E402


def http_get_json(url):
    """GET ``url`` and return parsed JSON (raises on a non-2xx status)."""

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def game_date(game_id):
    """Extract the ISO date prefix from a gameID like ``2026-05-10-MTL-PIT``."""
    if game_id and len(game_id) >= 10:
        return game_id[:10]
    return None


def yards(y0, y1):
    """Downfield yards from y0 to y1, capped at the goal line (y=100).

    Both streams are normalized so the recording team's offense attacks +y, so forward
    progress is simply the change in y. Distances past the goal line don't count.
    """
    if y0 is None or y1 is None:
        return None
    return min(y1, ENDZONE_Y) - min(y0, ENDZONE_Y)


def write_json(obj, path):
    """Write ``obj`` as pretty JSON, creating parent dirs. Returns the path string."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    return os.fspath(path)


# --- Offline loaders (local samples) -----------------------------------------------------
def load_local_game(game_id):
    """Load a local game-stats dict (the ``stats-pages/game`` shape)."""
    with open(GAME_STATS_DIR / f"{game_id}.json") as f:
        return json.load(f)


def load_local_game_events(game_id):
    """Load a local gameEvents dict (the ``api/v1/gameEvents`` shape)."""
    with open(GAME_EVENTS_DIR / f"{game_id}.json") as f:
        return json.load(f)


def list_local_game_ids():
    """gameIDs available locally in the game-stats dir."""
    return sorted(p.stem for p in GAME_STATS_DIR.glob("*.json"))
