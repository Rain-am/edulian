from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.product.fetcher import ProductApiDataSource, _format_update_time


class ProductClient:
    def __init__(self) -> None:
        self.config = SimpleNamespace(page_size=100)
        self.post_payloads = []

    def post(self, endpoint, payload):
        self.post_payloads.append((endpoint, payload))
        if endpoint.endswith("productList"):
            return {
                "code": 0,
                "data": {
                    "list": [
                        {"sku": "SKU-1", "update_time": "2026-06-01 10:00:00"},
                        {"sku": "SKU-2", "update_time": "2026-06-02 11:00:00"},
                    ]
                },
            }
        if endpoint.endswith("productInfo"):
            return {
                "code": 0,
                "data": {
                    "sku": payload["sku"],
                    "product_name": f"Product {payload['sku']}",
                    "clearance": {"customs_clearance_material": "Cotton"},
                    "unit": "pcs",
                    "bg_customs_export_name": "Clothing",
                    "bg_export_hs_code": "6109100000",
                },
            }
        return {"code": 0, "data": {}}


class ProductApiDataSourceTest(unittest.TestCase):
    def test_product_preview_uses_product_list_update_time_and_detail_fields(self) -> None:
        rows = ProductApiDataSource(client=ProductClient()).load_preview(limit=2)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].sku, "SKU-1")
        self.assertEqual(rows[0].product_name, "Product SKU-1")
        self.assertEqual(rows[0].material_cn, "Cotton")
        self.assertEqual(rows[0].unit, "pcs")
        self.assertEqual(rows[0].customs_name_cn, "Clothing")
        self.assertEqual(rows[0].customs_code, "6109100000")
        self.assertEqual(rows[0].update_time, "2026-06-01 10:00:00")

    def test_format_update_time_converts_second_timestamp(self) -> None:
        self.assertEqual(_format_update_time("1780985590"), "2026-06-09 14:13:10")

    def test_format_update_time_converts_millisecond_timestamp(self) -> None:
        self.assertEqual(_format_update_time("1780985590000"), "2026-06-09 14:13:10")


if __name__ == "__main__":
    unittest.main()
