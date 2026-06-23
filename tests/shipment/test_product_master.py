from __future__ import annotations

import unittest
from decimal import Decimal
from unittest.mock import patch

from src.shipment.build_rows import build_customs_workbook_data
from src.shipment.models import RawCustomsData, ShipmentItem, SkuInfo
from src.shipment.product_master import apply_product_master_data, merge_product_master


class ProductMasterTest(unittest.TestCase):
    def test_merge_product_master_overrides_non_empty_master_fields(self) -> None:
        sku_info = SkuInfo(sku="210610850001", product_name="接口品名", customs_name_cn="接口中文名", unit="8")

        merged = merge_product_master(
            sku_info,
            {"name": "物料表品名", "unit": "双", "chinese_customs_name": "物料表中文名"},
        )

        self.assertEqual(merged.product_name, "物料表品名")
        self.assertEqual(merged.unit, "双")
        self.assertEqual(merged.customs_name_cn, "物料表中文名")

    def test_merge_product_master_keeps_existing_values_when_master_fields_empty(self) -> None:
        sku_info = SkuInfo(sku="SKU1", product_name="接口品名", customs_name_cn="接口中文名", unit="8")

        merged = merge_product_master(sku_info, {"name": "", "unit": "", "chinese_customs_name": ""})

        self.assertEqual(merged.product_name, "接口品名")
        self.assertEqual(merged.unit, "8")
        self.assertEqual(merged.customs_name_cn, "接口中文名")

    def test_apply_product_master_data_updates_shipment_sku_info(self) -> None:
        raw = RawCustomsData(
            shipment_items=[
                ShipmentItem(
                    shipment_date="2026-06-22",
                    shipment_no="SP260622061",
                    sku="210610850001",
                    quantity=Decimal("1"),
                    product_name="发货单品名",
                )
            ],
            sku_infos={
                "210610850001": SkuInfo(
                    sku="210610850001",
                    product_name="接口品名",
                    customs_name_cn="接口中文名",
                    unit="8",
                    gross_weight=Decimal("1"),
                    outer_box_size="1*1*1",
                )
            },
        )

        with patch(
            "src.shipment.product_master.fetch_product_master_rows",
            return_value={
                "210610850001": {
                    "name": "物料表品名",
                    "unit": "双",
                    "chinese_customs_name": "物料表中文名",
                }
            },
        ):
            loaded, applied = apply_product_master_data(raw)

        self.assertEqual(loaded, 1)
        self.assertEqual(applied, 1)
        workbook_data = build_customs_workbook_data(raw)
        row = workbook_data.customs_rows[0]
        self.assertEqual(row.unit, "双")
        self.assertEqual(row.customs_name_cn, "物料表中文名")
        self.assertEqual(row.product_name, "发货单品名")


if __name__ == "__main__":
    unittest.main()
