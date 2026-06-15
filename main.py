from __future__ import annotations

import argparse
import os
import sys
import time
from urllib.request import urlopen

from src.product.job import run_product_preview_job
from src.shipment.job import run_shipment_job

DEFAULT_SHIPMENT_TIME = "2026-06-09"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Lingxing customs data jobs.")
    parser.add_argument(
        "--job",
        choices=("shipment", "product-preview"),
        default="shipment",
        help="Job to run. Use product-preview to export a 20-row product material preview.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Row limit for product-preview job.")
    parser.add_argument(
        "--shipment-time",
        "--ship-date",
        dest="shipment_time",
        default=DEFAULT_SHIPMENT_TIME,
        help=f"Shipment date, default {DEFAULT_SHIPMENT_TIME}.",
    )
    parser.add_argument("--output", help="Output .xlsx path.")
    parser.add_argument(
        "--use-sample-data",
        action="store_true",
        help="Use bundled sample data instead of calling Lingxing API.",
    )
    parser.add_argument(
        "--debug-api",
        action="store_true",
        help="Save Lingxing API response snapshots to logs/api_debug for troubleshooting.",
    )
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="Write shipment detail rows to MySQL after generating workbook data.",
    )
    parser.add_argument("--show-ip", action="store_true", help="Print current public outbound IP for whitelist setup.")
    parser.add_argument("--ip-repeat", type=int, default=1, help="Number of public IP probe rounds for --show-ip.")
    parser.add_argument("--ip-interval", type=float, default=1.0, help="Seconds to wait between --show-ip probe rounds.")
    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="Check whether Lingxing access token can be fetched with current .env credentials.",
    )
    args = parser.parse_args()
    if args.show_ip or args.check_auth:
        return args
    if len(sys.argv) == 1:
        args.job = "shipment"
        args.shipment_time = DEFAULT_SHIPMENT_TIME
        args.output = f"output\\real-{DEFAULT_SHIPMENT_TIME}.xlsx"
        args.use_sample_data = False
        return args
    if not args.output:
        parser.error("the following arguments are required unless using --show-ip or --check-auth: --output")
    return args


def main() -> None:
    args = parse_args()
    if args.show_ip:
        show_public_ips(repeat=args.ip_repeat, interval_seconds=args.ip_interval)
        return
    if args.check_auth:
        check_lingxing_auth()
        return

    if args.use_sample_data:
        print("Using sample data. Omit --use-sample-data to call Lingxing API.")
    if args.debug_api:
        os.environ["LINGXING_DEBUG_DIR"] = "logs/api_debug"

    try:
        if args.job == "product-preview":
            run_product_preview_job(args)
        else:
            run_shipment_job(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def show_public_ips(repeat: int = 1, interval_seconds: float = 1.0) -> None:
    urls = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
    ]
    seen_ips: set[str] = set()
    repeat = max(1, repeat)
    for round_index in range(1, repeat + 1):
        print(f"Probe round {round_index}/{repeat}")
        for url in urls:
            try:
                with urlopen(url, timeout=10) as response:
                    ip = response.read().decode("utf-8").strip()
                    seen_ips.add(ip)
                    print(f"  {url}: {ip}")
            except Exception as exc:
                print(f"  {url}: ERROR {exc}")
        if round_index < repeat:
            time.sleep(max(0.0, interval_seconds))
    if seen_ips:
        print("Unique public IPs observed:")
        for ip in sorted(seen_ips):
            print(ip)


def check_lingxing_auth() -> None:
    from src.common.lingxing_client import LingxingClient

    try:
        client = LingxingClient()
        token = client._fetch_access_token()
    except Exception as exc:
        print(f"Lingxing access token: FAILED - {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Lingxing access token: OK")
        print(f"Token prefix: {token[:6]}...")


if __name__ == "__main__":
    main()
