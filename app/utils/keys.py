def cache_key(*parts) -> str:
    return ":".join(str(p) for p in parts)

