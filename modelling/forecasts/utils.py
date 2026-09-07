"""Shared helpers for the forecasting pipeline.

Exposes the `registry` decorator factory used to register functions or classes
into a name -> object mapping (e.g. `OBJECTIVE_REGISTRY`, `QUERY_REGISTRY`).
"""

import pandas as pd

def registry(registry, name):
    def decorator(cls_or_fn):
        registry[name] = cls_or_fn
        return cls_or_fn
    return decorator

def duckdb_query(con, query) -> pd.DataFrame:
    try:
        df = con.execute(query).df()
        return df
    except Exception as e:
        raise RuntimeError(f"query '{query}' failed: {e}")
