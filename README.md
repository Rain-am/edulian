# Lingxing FBA Customs Automation

This project generates a customs declaration workbook from real Lingxing FBA shipment data.

## Real API Run

1. Create local config:

```powershell
Copy-Item .env.example .env
```

2. Fill `.env`:

- `LINGXING_BASE_URL`
- `LINGXING_APP_ID`
- `LINGXING_APP_SECRET`
- `LINGXING_ACCESS_TOKEN` if required by your Lingxing API version
- `LINGXING_FBA_SHIPMENT_LIST_ENDPOINT`: defaults to `/erp/sc/routing/storage/shipment/getInboundShipmentList`
- `LINGXING_FBA_SHIPMENT_DETAIL_ENDPOINT`: defaults to `/erp/sc/routing/storage/shipment/getInboundShipmentListMwsDetail`
- `LINGXING_SKU_DETAIL_ENDPOINT`: defaults to `/erp/sc/routing/data/local_inventory/productInfo`

3. Run:

```powershell
.\.venv\Scripts\python.exe main.py --shipment-time 2026-06-10 --output output\报关明细.xlsx
```

## Sample Data

Sample data is only for testing Excel generation. It is never used unless you explicitly add:

```powershell
--use-sample-data
```

## Output Sheets

- `报关明细`: customs declaration rows.
- `问题清单`: missing fields and data issues.
- `采购拆分明细`: purchase order, supplier, and batch split details.

## Current Integration Point

The API client and data mapping are implemented in `src/fetchers/lingxing_api.py`.
The shipment list request filters `status=已发货` by default. Purchase unit price comes from `fba_stock_cost` in the FBA shipment list/detail payload.
The shipment list request sends one shipment date plus `time_type=0` by default.

If the Lingxing API rejects the status or date parameter names, adjust these `.env` values:

- `LINGXING_SHIPMENT_STATUS_FIELD`
- `LINGXING_SHIPMENT_TIME_FIELD`
- `LINGXING_SHIPMENT_TIME_TYPE_FIELD`
- `LINGXING_SHIPMENT_TIME_TYPE`

## Cloud Server Deploy

Generate a clean deploy folder on Windows:

```powershell
.\scripts\make_deploy.ps1
```

This creates `deploy_package` under the project folder. It does not copy `.env`, `.venv`, `logs`, `output`, caches, or local debug files.

To generate a sibling folder instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\make_deploy.ps1 -DeployPath "D:\work files\领星报关_deploy"
```

Upload `deploy_package` to the Linux cloud server, then run:

```bash
bash scripts/setup_linux.sh
nano .env
bash scripts/check.sh
.venv/bin/python main.py --check-auth
bash scripts/run_once.sh
```

Install the 20-minute cron job after the manual run succeeds:

```bash
bash scripts/install_cron.sh
crontab -l
tail -f logs/cron.log
```

For a specific shipment date:

```bash
SHIPMENT_TIME=2026-06-09 bash scripts/run_once.sh
```
