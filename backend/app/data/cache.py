import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

import orjson

from app.config import get_settings


def _key(namespace: str, payload: Any) -> Path:
    raw = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    h = hashlib.sha1(raw).hexdigest()[:16]
    cache_dir = get_settings().cache_path / namespace
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{h}.json"


def load(namespace: str, payload: Any, ttl_seconds: int) -> Any | None:
    p = _key(namespace, payload)
    if not p.exists():
        return None
    if (time.time() - p.stat().st_mtime) > ttl_seconds:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(namespace: str, payload: Any, value: Any) -> None:
    p = _key(namespace, payload)
    try:
        p.write_text(json.dumps(value, default=str), encoding="utf-8")
    except Exception:
        pass


async def cached(namespace: str, payload: Any, ttl_seconds: int, fetcher: Callable):
    cached_val = load(namespace, payload, ttl_seconds)
    if cached_val is not None:
        return cached_val
    value = await fetcher() if callable(fetcher) else fetcher
    save(namespace, payload, value)
    return value
