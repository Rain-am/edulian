from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

import main


class MainArgsTest(unittest.TestCase):
    def test_no_args_defaults_to_fixed_shipment_time(self) -> None:
        with patch.object(sys, "argv", ["main.py"]):
            args = main.parse_args()

        self.assertEqual(args.shipment_time, "2026-06-09")
        self.assertEqual(args.output, "output\\real-2026-06-09.xlsx")

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


if __name__ == "__main__":
    unittest.main()
