"""Shared helpers for the AUDL staging transforms.

The transforms themselves are pure functions over already-fetched JSON. The data lake is
stored as parquet (see ``write_parquet``/``read_parquet``): row-oriented datasets become
columnar parquet, while nested composite payloads (gameEvents/game-stats) round-trip
losslessly as a JSON payload column.
"""

import json
import os
import requests
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

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


def write_parquet(obj, path):
    """Write ``obj`` as parquet, creating parent dirs. Returns the path string.

    A list of dicts becomes a columnar parquet table. Anything Arrow can't tabularize
    (a nested composite dict like the gameEvents / game-stats payloads, or a ragged list)
    is stored losslessly as a single JSON string in a ``_payload`` column. The read side
    (``read_parquet``) uses the ``container`` schema-metadata flag to invert this.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = None
    if isinstance(obj, list):
        try:
            table = pa.Table.from_pylist(obj).replace_schema_metadata({b"container": b"list"})
        except Exception:
            table = None
    if table is None:
        table = pa.table({"_payload": [json.dumps(obj)]}).replace_schema_metadata({b"container": b"json"})
    pq.write_table(table, path)
    return os.fspath(path)


def read_parquet(path):
    """Inverse of ``write_parquet``: return the original list or nested payload.

    Reads the single file directly (``ParquetFile``) so Hive ``season=/month=`` ancestors
    aren't inferred as extra partition columns — the round-trip returns exactly what was
    written.
    """
    table = pq.ParquetFile(os.fspath(path)).read()
    container = (table.schema.metadata or {}).get(b"container", b"list")
    if container == b"json":
        return json.loads(table.column("_payload")[0].as_py())
    return table.to_pylist()


# --- Format dispatch (parquet | json) -----------------------------------------------------
FORMATS = ("parquet", "json")


def data_suffix(fmt):
    """File extension for a data-lake ``fmt`` (``"parquet"`` -> ``".parquet"``)."""
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r} (expected one of {FORMATS})")
    return f".{fmt}"


def write_table(obj, path):
    """Write ``obj`` as parquet or JSON, dispatched on ``path``'s extension."""
    suffix = Path(path).suffix
    if suffix == ".parquet":
        return write_parquet(obj, path)
    if suffix == ".json":
        return write_json(obj, path)
    raise ValueError(f"unsupported data extension {suffix!r} for {path}")


def read_table(path):
    """Read a parquet or JSON data-lake file, dispatched on ``path``'s extension."""
    suffix = Path(path).suffix
    if suffix == ".parquet":
        return read_parquet(path)
    if suffix == ".json":
        with open(path) as f:
            return json.load(f)
    raise ValueError(f"unsupported data extension {suffix!r} for {path}")


# --- SOURCE_DIR loaders (read raw extracted data from the data lake) ----------------------
def load_source_game_stats(game_id, root=None, fmt="parquet"):
    """Load the extracted game-stats payload (the full ``stats-pages/game`` shape)."""
    root = Path(root) if root else source_dir()
    path = partition_dir(root, "game_stats", game_year(game_id), game_month(game_id)) / f"{game_id}{data_suffix(fmt)}"
    return read_table(path)


def load_source_game_events(game_id, root=None, fmt="parquet"):
    """Load the extracted gameEvents payload.

    Extraction saves ``response["data"]``, so this is already the inner dict
    (``{homeEvents, awayEvents, ...}``) — callers use it directly, no ``["data"]``.
    """
    root = Path(root) if root else source_dir()
    path = partition_dir(root, "game_events", game_year(game_id), game_month(game_id)) / f"{game_id}{data_suffix(fmt)}"
    return read_table(path)


def list_source_game_ids(root=None, fmt="parquet"):
    """gameIDs available in the SOURCE_DIR ``game_stats`` partitions (empty if unset)."""
    if root is None:
        try:
            root = source_dir()
        except RuntimeError:
            return []
    base = Path(root) / "game_stats"
    if not base.exists():
        return []
    return sorted(p.stem for p in base.glob(f"season=*/month=*/*{data_suffix(fmt)}"))
