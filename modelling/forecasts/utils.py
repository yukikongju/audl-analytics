"""Shared helpers for the forecasting pipeline.

Exposes the `registry` decorator factory used to register functions or classes
into a name -> object mapping (e.g. `OBJECTIVE_REGISTRY`, `QUERY_REGISTRY`).
"""


def registry(registry, name):
    def decorator(cls_or_fn):
        registry[name] = cls_or_fn
        return cls_or_fn
    return decorator
