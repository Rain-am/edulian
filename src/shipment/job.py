from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.shipment.build_rows import build_customs_workbook_data
from src.shipment.export_excel import export_customs_workbook
from src.shipment.export_mysql import export_customs_rows_to_mysql
from src.shipment.fetcher import LingxingApiDataSource
from src.shipment.sample_data import SampleDataSource


def run_shipment_job(args: Any) -> None:
    data_source = SampleDataSource() if args.use_sample_data else LingxingApiDataSource()
    raw_data = data_source.load(shipment_time=args.shipment_time)
    workbook_data = build_customs_workbook_data(raw_data)
    output_path = _export_with_available_path(workbook_data, Path(args.output))
    if args.write_db:
        db_rows = export_customs_rows_to_mysql(workbook_data)
        print(f"MySQL rows upserted: {db_rows}")

    print(f"Generated customs workbook: {output_path.resolve()}")
    print(f"Customs rows: {len(workbook_data.customs_rows)}")
    print(f"Issue rows: {len(workbook_data.issue_rows)}")
    print(f"Purchase split rows: {len(workbook_data.purchase_split_rows)}")
    pending_purchase_entities = sum(1 for row in workbook_data.customs_rows if row.purchase_entity == "待确认")
    purchase_entities = sorted({row.purchase_entity for row in workbook_data.customs_rows if row.purchase_entity != "待确认"})
    print(f"Pending purchase entity rows: {pending_purchase_entities}")
    if purchase_entities:
        print("Purchase entities: " + ", ".join(purchase_entities[:10]))
    if not workbook_data.purchase_split_rows:
        print("Warning: no purchase split rows were generated; shipment detail did not provide purchase_items/purchase_sn.")


def _export_with_available_path(workbook_data, output_path: Path) -> Path:
    try:
        export_customs_workbook(workbook_data, output_path)
        return output_path
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        fallback_path = output_path.with_name(f"{output_path.stem}-{timestamp}{output_path.suffix}")
        export_customs_workbook(workbook_data, fallback_path)
        print(f"Output file is in use, wrote a new file instead: {fallback_path}")
        return fallback_path
