from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.shipment.models import PurchaseBatch, RawCustomsData, ShipmentItem, SkuInfo

from .base import CustomsDataSource


class SampleDataSource(CustomsDataSource):
    def load(self, shipment_time: str | None = None) -> RawCustomsData:
        shipment_date = shipment_time or date.today().isoformat()
        return RawCustomsData(
            shipment_items=[
                ShipmentItem(
                    shipment_date=shipment_date,
                    shipment_no="FBA-SAMPLE-001",
                    sku="SKU-001",
                    quantity=Decimal("30"),
                    box_no="CTN-001",
                    box_count=Decimal("1"),
                    pieces=Decimal("1"),
                    logistics_provider="样例物流商",
                    logistics_channel="美森快船",
                    transport_method="海运",
                    logistics_method="海运",
                    logistics_center_code="ONT8",
                    volume=Decimal("0.12"),
                ),
                ShipmentItem(
                    shipment_date=shipment_date,
                    shipment_no="FBA-SAMPLE-001",
                    sku="SKU-001",
                    quantity=Decimal("20"),
                    box_no="CTN-002",
                    box_count=Decimal("1"),
                    pieces=Decimal("1"),
                    logistics_provider="样例物流商",
                    logistics_channel="美森快船",
                    transport_method="海运",
                    logistics_method="海运",
                    logistics_center_code="ONT8",
                    volume=Decimal("0.08"),
                ),
                ShipmentItem(
                    shipment_date=shipment_date,
                    shipment_no="FBA-SAMPLE-001",
                    sku="SKU-002",
                    quantity=Decimal("10"),
                    box_no="CTN-003",
                    box_count=Decimal("1"),
                    pieces=Decimal("1"),
                    logistics_provider="样例物流商",
                    logistics_channel="美森快船",
                    transport_method="海运",
                    logistics_method="海运",
                    logistics_center_code="ONT8",
                ),
            ],
            sku_infos={
                "SKU-001": SkuInfo(
                    sku="SKU-001",
                    product_name="样例产品A",
                    customs_name_cn="塑料收纳盒",
                    customs_name_en="Plastic storage box",
                    unit="个",
                    package_type="纸箱",
                    gross_weight=Decimal("0.35"),
                    net_weight=Decimal("0.30"),
                    outer_box_size="60*40*50cm",
                    box_length_cm=Decimal("60"),
                    box_width_cm=Decimal("40"),
                    box_height_cm=Decimal("50"),
                ),
                "SKU-002": SkuInfo(
                    sku="SKU-002",
                    product_name="样例产品B",
                    customs_name_cn="不锈钢杯",
                    customs_name_en="Stainless steel cup",
                    unit="个",
                    package_type="纸箱",
                    gross_weight=Decimal("0.50"),
                    net_weight=Decimal("0.42"),
                    outer_box_size="50*40*40cm",
                    box_length_cm=Decimal("50"),
                    box_width_cm=Decimal("40"),
                    box_height_cm=Decimal("40"),
                ),
            },
            purchase_batches=[
                PurchaseBatch(
                    shipment_no="FBA-SAMPLE-001",
                    box_no="CTN-001",
                    sku="SKU-001",
                    quantity=Decimal("10"),
                    purchase_entity="深圳样例贸易有限公司",
                    supplier="供应商甲",
                    domestic_source="广东深圳",
                    purchase_order_no="PO-001",
                    batch_no="BATCH-A",
                    purchase_unit_price=Decimal("12.30"),
                ),
                PurchaseBatch(
                    shipment_no="FBA-SAMPLE-001",
                    box_no="CTN-001",
                    sku="SKU-001",
                    quantity=Decimal("20"),
                    purchase_entity="深圳样例贸易有限公司",
                    supplier="供应商乙",
                    domestic_source="浙江宁波",
                    purchase_order_no="PO-002",
                    batch_no="BATCH-B",
                    purchase_unit_price=Decimal("12.80"),
                ),
                PurchaseBatch(
                    shipment_no="FBA-SAMPLE-001",
                    box_no="CTN-002",
                    sku="SKU-001",
                    quantity=Decimal("20"),
                    purchase_entity="深圳样例贸易有限公司",
                    supplier="供应商乙",
                    domestic_source="浙江宁波",
                    purchase_order_no="PO-002",
                    batch_no="BATCH-B",
                    purchase_unit_price=Decimal("12.80"),
                ),
            ],
        )
