from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from src.shipment.job import _delete_before_date, _shipment_times


class ShipmentJobTest(unittest.TestCase):
    def test_omitted_shipment_time_runs_yesterday_and_today(self) -> None:
        args = SimpleNamespace(shipment_time=None, shipment_time_provided=False)

        with patch("src.shipment.job._today", return_value=date(2026, 6, 17)):
            shipment_times = _shipment_times(args)

        self.assertEqual(shipment_times, ["2026-06-16", "2026-06-17"])

    def test_explicit_shipment_time_runs_only_that_day(self) -> None:
        args = SimpleNamespace(shipment_time="2026-06-13", shipment_time_provided=True)

        with patch("src.shipment.job._today", return_value=date(2026, 6, 17)):
            shipment_times = _shipment_times(args)

        self.assertEqual(shipment_times, ["2026-06-13"])

    def test_delete_before_date_keeps_yesterday_and_today(self) -> None:
        with patch("src.shipment.job._today", return_value=date(2026, 6, 17)):
            delete_before = _delete_before_date()

        self.assertEqual(delete_before, "2026-06-16")


if __name__ == "__main__":
    unittest.main()
