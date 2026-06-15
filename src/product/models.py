from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductPreviewRow:
    sku: str
    product_name: str = ""
    material_cn: str = ""
    unit: str = ""
    customs_name_cn: str = ""
    customs_code: str = ""
    update_time: str = ""
