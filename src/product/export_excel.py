from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from src.common.xlsx_writer import write_xlsx_workbook
from src.product.models import ProductPreviewRow


PRODUCT_PREVIEW_HEADERS = [
    ("sku", "物料编码"),
    ("product_name", "品名"),
    ("material_cn", "中文材质"),
    ("unit", "单位"),
    ("customs_name_cn", "中文报关品名"),
    ("customs_code", "海关编码"),
    ("update_time", "更新时间"),
]


def export_product_preview_workbook(rows: list[ProductPreviewRow], output_path: Path) -> None:
    write_xlsx_workbook(
        [("物料表预览", PRODUCT_PREVIEW_HEADERS, [asdict(row) for row in rows])],
        output_path,
        text_keys={"sku"},
    )
