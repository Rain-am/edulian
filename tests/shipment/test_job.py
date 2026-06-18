from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from src.shipment.job import _shipment_times, run_shipment_job
from src.shipment.models import RawCustomsData


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

    def test_write_db_without_output_skips_excel_export(self) -> None:
        args = SimpleNamespace(
            clear_cache=False,
            use_sample_data=True,
            refresh_cache=False,
            shipment_time="2026-06-13",
            shipment_time_provided=True,
            output=None,
            db_preflight=False,
            write_db=True,
        )

        with (
            patch("src.shipment.job.SampleDataSource", return_value=FakeShipmentDataSource()),
            patch("src.shipment.job.build_customs_workbook_data", return_value=SimpleNamespace(customs_rows=[], issue_rows=[], purchase_split_rows=[])),
            patch("src.shipment.job.export_customs_workbook") as export_excel,
            patch("src.shipment.job.preflight_customs_rows_mysql", return_value=SimpleNamespace(table="customs_bill_parcels", row_count=0, duplicate_id_count=0)),
            patch("src.shipment.job.export_customs_rows_to_mysql", return_value=0),
        ):
            run_shipment_job(args)

        export_excel.assert_not_called()


class FakeShipmentDataSource:
    def load(self, shipment_time):
        return RawCustomsData()

if __name__ == "__main__":
    unittest.main()
