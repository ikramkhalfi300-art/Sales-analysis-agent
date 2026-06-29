"""
Simple file-based cache for forecast & AI results.
Keys are SHA256 hashes of input data + parameters.
"""
import hashlib
import json
import pickle
import time
from pathlib import Path

from config import CACHE_DIR, CACHE_TTL

CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _hash(*args) -> str:
    raw = json.dumps([str(a) for a in args], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def cache_set(key: str, value) -> None:
    path = CACHE_DIR / f"{key}.pkl"
    try:
        with open(path, "wb") as f:
            pickle.dump((time.time(), value), f)
    except Exception:
        pass

def cache_get(key: str):
    path = CACHE_DIR / f"{key}.pkl"
    try:
        if not path.exists():
            return None
        mtime = path.stat().st_mtime
        if time.time() - mtime > CACHE_TTL:
            path.unlink(missing_ok=True)
            return None
        with open(path, "rb") as f:
            _, value = pickle.load(f)
        return value
    except Exception:
        return None

def cache_clear() -> int:
    count = 0
    for p in CACHE_DIR.glob("*.pkl"):
        p.unlink(missing_ok=True)
        count += 1
    return count

def make_cache_key(namespace: str, *parts) -> str:
    return f"{namespace}_{_hash(*parts)}"
