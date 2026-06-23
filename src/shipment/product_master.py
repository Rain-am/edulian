from __future__ import annotations

import os
from dataclasses import replace
from typing import Any, Iterable

from src.shipment.export_mysql import MySQLConfig, _open_mysql_connection, _quote_identifier
from src.shipment.models import RawCustomsData, SkuInfo


def apply_product_master_data(raw_data: RawCustomsData, config: MySQLConfig | None = None) -> tuple[int, int]:
    sku_codes = {item.sku for item in raw_data.shipment_items if item.sku}
    if not sku_codes:
        return 0, 0
    product_rows = fetch_product_master_rows(sku_codes, config=config)
    applied = 0
    for sku, product in product_rows.items():
        current = raw_data.sku_infos.get(sku, SkuInfo(sku=sku))
        updated = merge_product_master(current, product)
        if updated != current:
            raw_data.sku_infos[sku] = updated
            applied += 1
    return len(product_rows), applied


def fetch_product_master_rows(sku_codes: Iterable[str], config: MySQLConfig | None = None) -> dict[str, dict[str, str]]:
    skus = sorted({str(sku).strip() for sku in sku_codes if str(sku).strip()})
    if not skus:
        return {}
    config = config or MySQLConfig.from_env()
    table = os.getenv("MYSQL_PRODUCT_TABLE", "customs_product")
    rows: dict[str, dict[str, str]] = {}
    connection = None
    tunnel = None
    try:
        connection, tunnel = _open_mysql_connection(config)
        with connection.cursor() as cursor:
            for batch in _chunks(skus, 500):
                placeholders = ", ".join(["%s"] * len(batch))
                cursor.execute(
                    "SELECT `sku`, `name`, `unit`, `chinese_customs_name` "
                    f"FROM {_quote_identifier(table)} WHERE `sku` IN ({placeholders})",
                    batch,
                )
                for row in cursor.fetchall():
                    sku, value = _normalize_product_row(row)
                    if sku:
                        rows[sku] = value
    finally:
        if connection is not None:
            connection.close()
        if tunnel is not None:
            tunnel.stop()
    return rows


def merge_product_master(sku_info: SkuInfo, product: dict[str, str]) -> SkuInfo:
    return replace(
        sku_info,
        product_name=product.get("name") or sku_info.product_name,
        customs_name_cn=product.get("chinese_customs_name") or sku_info.customs_name_cn,
        unit=product.get("unit") or sku_info.unit,
    )


def _normalize_product_row(row: Any) -> tuple[str, dict[str, str]]:
    if isinstance(row, dict):
        sku = str(row.get("sku") or "").strip()
        return sku, {
            "name": str(row.get("name") or "").strip(),
            "unit": str(row.get("unit") or "").strip(),
            "chinese_customs_name": str(row.get("chinese_customs_name") or "").strip(),
        }
    sku = str(row[0] if len(row) > 0 else "").strip()
    return sku, {
        "name": str(row[1] if len(row) > 1 and row[1] is not None else "").strip(),
        "unit": str(row[2] if len(row) > 2 and row[2] is not None else "").strip(),
        "chinese_customs_name": str(row[3] if len(row) > 3 and row[3] is not None else "").strip(),
    }


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]
