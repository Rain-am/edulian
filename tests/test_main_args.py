from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

import main


class MainArgsTest(unittest.TestCase):
    def test_no_args_defaults_to_recent_shipment_window(self) -> None:
        with patch.object(sys, "argv", ["main.py"]):
            args = main.parse_args()

        self.assertFalse(args.shipment_time_provided)
        self.assertIsNone(args.shipment_time)
        self.assertEqual(args.output, "output\\real-recent.xlsx")

    def test_product_preview_args(self) -> None:
        with patch.object(
            sys,
            "argv",
            ["main.py", "--job", "product-preview", "--limit", "20", "--output", "output\\product-preview-20.xlsx"],
        ):
            args = main.parse_args()

        self.assertEqual(args.job, "product-preview")
        self.assertEqual(args.limit, 20)
        self.assertEqual(args.output, "output\\product-preview-20.xlsx")

    def test_show_ip_repeat_args_do_not_require_output(self) -> None:
        with patch.object(sys, "argv", ["main.py", "--show-ip", "--ip-repeat", "10", "--ip-interval", "0.2"]):
            args = main.parse_args()

        self.assertTrue(args.show_ip)
        self.assertEqual(args.ip_repeat, 10)
        self.assertEqual(args.ip_interval, 0.2)

    def test_probe_purchase_order_does_not_require_output(self) -> None:
        with patch.object(sys, "argv", ["main.py", "--probe-purchase-order", "PO260525005"]):
            args = main.parse_args()

        self.assertEqual(args.probe_purchase_order, "PO260525005")

    def test_write_db_allows_recent_window_without_explicit_shipment_time(self) -> None:
        with patch.object(sys, "argv", ["main.py", "--output", "output\\real.xlsx", "--write-db"]):
            args = main.parse_args()

        self.assertTrue(args.write_db)
        self.assertFalse(args.shipment_time_provided)

    def test_db_preflight_allows_recent_window_without_explicit_shipment_time(self) -> None:
        with patch.object(sys, "argv", ["main.py", "--output", "output\\real.xlsx", "--db-preflight"]):
            args = main.parse_args()

        self.assertTrue(args.db_preflight)
        self.assertFalse(args.shipment_time_provided)

    def test_db_preflight_args(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "main.py",
                "--shipment-time",
                "2026-06-13",
                "--output",
                "output\\real.xlsx",
                "--db-preflight",
                "--refresh-cache",
                "--clear-cache",
                "--debug-full-api",
            ],
        ):
            args = main.parse_args()

        self.assertTrue(args.db_preflight)
        self.assertTrue(args.refresh_cache)
        self.assertTrue(args.clear_cache)
        self.assertTrue(args.debug_full_api)
        self.assertTrue(args.shipment_time_provided)
        self.assertEqual(args.shipment_time, "2026-06-13")

    def test_write_db_and_db_preflight_are_mutually_exclusive(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "main.py",
                "--shipment-time",
                "2026-06-13",
                "--output",
                "output\\real.xlsx",
                "--write-db",
                "--db-preflight",
            ],
        ):
            with self.assertRaises(SystemExit):
                main.parse_args()


if __name__ == "__main__":
    unittest.main()
