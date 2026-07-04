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

from constants import ENDZONE_Y  # noqa: E402


def _env_dir(name):
    """Resolve an env-var directory (e.g. ``AUDL_SOURCE_DIR``) to an expanded Path."""
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"{name} is not set — define it in .env (direnv) or pass an override")
    return Path(os.path.expandvars(val)).expanduser()


def source_dir():
    """Data-lake root for raw extracted JSON (``AUDL_SOURCE_DIR``)."""
    return _env_dir("AUDL_SOURCE_DIR")


def processed_dir():
    """Data-lake root for processed ``ext_*`` tables (``AUDL_PROCESSED_DIR``)."""
    return _env_dir("AUDL_PROCESSED_DIR")


def partition_dir(root, entity, year, month=None):
    """Hive-style dir: ``<root>/<entity>/season=<year>[/month=<MM>]``."""
    p = Path(root) / entity / f"season={year}"
    return p / f"month={month}" if month is not None else p


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


def game_year(game_id):
    """Season year (``2026``) parsed from a gameID's date prefix."""
    d = game_date(game_id)
    return d[:4] if d else None


def game_month(game_id):
    """Zero-padded month (``05``) parsed from a gameID's date prefix."""
    d = game_date(game_id)
    return d[5:7] if d else None


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


# --- SOURCE_DIR loaders (read raw extracted JSON from the data lake) ----------------------
def load_source_game_stats(game_id, root=None):
    """Load the extracted game-stats payload (the full ``stats-pages/game`` shape)."""
    root = Path(root) if root else source_dir()
    path = partition_dir(root, "game_stats", game_year(game_id), game_month(game_id)) / f"{game_id}.json"
    with open(path) as f:
        return json.load(f)


def load_source_game_events(game_id, root=None):
    """Load the extracted gameEvents payload.

    Extraction saves ``response["data"]``, so this is already the inner dict
    (``{homeEvents, awayEvents, ...}``) — callers use it directly, no ``["data"]``.
    """
    root = Path(root) if root else source_dir()
    path = partition_dir(root, "game_events", game_year(game_id), game_month(game_id)) / f"{game_id}.json"
    with open(path) as f:
        return json.load(f)


def list_source_game_ids(root=None):
    """gameIDs available in the SOURCE_DIR ``game_stats`` partitions (empty if unset)."""
    if root is None:
        try:
            root = source_dir()
        except RuntimeError:
            return []
    base = Path(root) / "game_stats"
    if not base.exists():
        return []
    return sorted(p.stem for p in base.glob("season=*/month=*/*.json"))
