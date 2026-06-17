from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

CACHE_VERSION = "v2"


class JsonCache:
    def __init__(self, cache_dir: str | Path | None = None, refresh: bool = False) -> None:
        root = Path(cache_dir or os.getenv("LINGXING_CACHE_DIR", ".cache/lingxing"))
        self.cache_dir = root / CACHE_VERSION
        self.refresh = refresh

    def get(self, namespace: str, key: str, ttl_days: int) -> Any | None:
        if self.refresh:
            return None
        path = self._path(namespace, key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        saved_at = float(payload.get("saved_at") or 0)
        if saved_at <= 0:
            return None
        if time.time() - saved_at > ttl_days * 86400:
            return None
        return payload.get("value")

    def set(self, namespace: str, key: str, value: Any) -> None:
        if not _cacheable_value(value):
            return
        path = self._path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"saved_at": time.time(), "value": value}
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    def clear(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

    def _path(self, namespace: str, key: str) -> Path:
        safe_key = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(key))
        return self.cache_dir / namespace / f"{safe_key}.json"


def _cacheable_value(value: Any) -> bool:
    if value in (None, "", [], {}):
        return False
    return True
