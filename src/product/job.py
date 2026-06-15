from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.product.export_excel import export_product_preview_workbook
from src.product.fetcher import ProductApiDataSource


def run_product_preview_job(args: Any) -> None:
    rows = ProductApiDataSource().load_preview(limit=args.limit)
    output_path = Path(args.output)
    try:
        export_product_preview_workbook(rows, output_path)
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = output_path.with_name(f"{output_path.stem}-{timestamp}{output_path.suffix}")
        export_product_preview_workbook(rows, output_path)
        print(f"Output file is in use, wrote a new file instead: {output_path}")

    print(f"Generated product preview workbook: {output_path.resolve()}")
    print(f"Product preview rows: {len(rows)}")
