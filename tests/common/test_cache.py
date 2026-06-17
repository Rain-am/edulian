from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.common.cache import JsonCache


class JsonCacheTest(unittest.TestCase):
    def test_cache_round_trip_uses_versioned_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = JsonCache(cache_dir=tmp)

            cache.set("sku", "SKU/1", {"unit": "pcs"})

            self.assertEqual(cache.get("sku", "SKU/1", ttl_days=30), {"unit": "pcs"})
            self.assertTrue((Path(tmp) / "v2" / "sku").exists())

    def test_old_unversioned_cache_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_path = Path(tmp) / "sku" / "SKU1.json"
            old_path.parent.mkdir(parents=True)
            old_path.write_text(json.dumps({"saved_at": 9999999999, "value": {"unit": "fake"}}), encoding="utf-8")

            self.assertIsNone(JsonCache(cache_dir=tmp).get("sku", "SKU1", ttl_days=30))

    def test_refresh_ignores_existing_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = JsonCache(cache_dir=tmp)
            cache.set("sku", "SKU1", {"unit": "pcs"})

            self.assertIsNone(JsonCache(cache_dir=tmp, refresh=True).get("sku", "SKU1", ttl_days=30))

    def test_expired_cache_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = JsonCache(cache_dir=tmp)
            cache.set("sku", "SKU1", {"unit": "pcs"})
            path = Path(tmp) / "v2" / "sku" / "SKU1.json"
            path.write_text(json.dumps({"saved_at": 1, "value": {"unit": "pcs"}}), encoding="utf-8")

            self.assertIsNone(cache.get("sku", "SKU1", ttl_days=1))

    def test_clear_removes_versioned_cache_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_path = Path(tmp) / "sku" / "SKU1.json"
            old_path.parent.mkdir(parents=True)
            old_path.write_text("old", encoding="utf-8")
            cache = JsonCache(cache_dir=tmp)
            cache.set("sku", "SKU1", {"unit": "pcs"})

            cache.clear()

            self.assertTrue(old_path.exists())
            self.assertFalse((Path(tmp) / "v2").exists())


if __name__ == "__main__":
    unittest.main()
