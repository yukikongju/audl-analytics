def registry(registry, name):
    def decorator(cls_or_fn):
        registry[name] = cls_or_fn
        return cls_or_fn
    return decorator
