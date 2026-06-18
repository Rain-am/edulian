from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from src.product.job import _default_incremental_window


class ProductJobTest(unittest.TestCase):
    def test_default_incremental_window_is_yesterday_to_today(self) -> None:
        class FixedDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 6, 18)

        with patch("src.product.job.date", FixedDate):
            self.assertEqual(_default_incremental_window(), ("2026-06-17", "2026-06-18"))


if __name__ == "__main__":
    unittest.main()
