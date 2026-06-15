from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from src.common.lingxing_client import LingxingClient, LingxingClientError
from src.product.models import ProductPreviewRow


class ProductApiDataSource:
    def __init__(self, client: LingxingClient | None = None) -> None:
        self.client = client or LingxingClient()
        self.product_list_endpoint = os.getenv(
            "LINGXING_PRODUCT_LIST_ENDPOINT",
            "/erp/sc/routing/data/local_inventory/productList",
        )
        self.product_detail_endpoint = os.getenv(
            "LINGXING_SKU_DETAIL_ENDPOINT",
            "/erp/sc/routing/data/local_inventory/productInfo",
        )

    def load_preview(self, limit: int = 20) -> list[ProductPreviewRow]:
        self._validate_config()
        rows = self._fetch_product_list_rows(limit)
        preview_rows: list[ProductPreviewRow] = []
        for row in rows:
            sku = str(_first(row, "sku", "seller_sku", "local_sku", "msku") or "")
            if not sku:
                continue
            update_time = _format_update_time(_first(row, "update_time", "updated_at", "gmt_modified", "modify_time"))
            try:
                data = self.client.post(self.product_detail_endpoint, {"sku": sku})
            except LingxingClientError:
                payload: dict[str, Any] = {"sku": sku}
            else:
                payload_data = data.get("data", data)
                payload = payload_data if isinstance(payload_data, dict) else {"sku": sku}
            preview_rows.append(_map_product_preview_row(sku, payload, update_time))
            if len(preview_rows) >= limit:
                break
        return preview_rows

    def _fetch_product_list_rows(self, limit: int) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_signatures: set[tuple[str, ...]] = set()
        page_size = min(max(limit, 1), _client_page_size(self.client))
        page = 1
        while len(rows) < limit:
            payload = {"page": page, "page_size": page_size}
            data = self.client.post(self.product_list_endpoint, payload)
            items = _extract_rows(data)
            if not items:
                break
            signature = tuple(str(_first(item, "sku", "seller_sku", "local_sku", "msku") or "") for item in items)
            if signature in seen_signatures:
                break
            seen_signatures.add(signature)
            rows.extend(items)
            if len(items) < page_size:
                break
            page += 1
            if page > 500:
                break
        return rows[:limit]

    def _validate_config(self) -> None:
        missing = []
        if not self.product_list_endpoint:
            missing.append("LINGXING_PRODUCT_LIST_ENDPOINT")
        if not self.product_detail_endpoint:
            missing.append("LINGXING_SKU_DETAIL_ENDPOINT")
        if missing:
            raise RuntimeError("Real Lingxing product API endpoints are not configured: " + ", ".join(missing))


def _map_product_preview_row(sku: str, payload: dict[str, Any], update_time: str) -> ProductPreviewRow:
    clearance = payload.get("clearance")
    if not isinstance(clearance, dict):
        clearance = {}
    return ProductPreviewRow(
        sku=str(payload.get("sku") or payload.get("seller_sku") or sku),
        product_name=str(payload.get("product_name") or payload.get("product_name_cn") or payload.get("name") or ""),
        material_cn=str(clearance.get("customs_clearance_material") or ""),
        unit=str(payload.get("unit") or ""),
        customs_name_cn=str(payload.get("bg_customs_export_name") or ""),
        customs_code=str(payload.get("bg_export_hs_code") or ""),
        update_time=update_time,
    )


def _extract_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("data", "list", "items", "rows", "records"):
        value = data.get(key)
        rows = _extract_rows(value)
        if rows:
            return rows
    return []


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _format_update_time(value: Any) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip()
    if len(text) >= 19 and text[4:5] == "-" and text[7:8] == "-":
        return text[:19]
    if not text.isdigit():
        return text

    timestamp = int(text)
    if len(text) >= 13:
        timestamp = timestamp // 1000
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        return text


def _client_page_size(client: Any) -> int:
    config = getattr(client, "config", None)
    page_size = getattr(config, "page_size", 100)
    try:
        value = int(page_size)
    except (TypeError, ValueError):
        return 100
    return value if value > 0 else 100
