from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from src.common.lingxing_client import _load_dotenv
from src.shipment.models import CustomsRow, CustomsWorkbookData


MYSQL_COLUMNS = [
    ("id", "id"),
    ("shipment_date", "shipment_date"),
    ("shipment_no", "shipment_no"),
    ("purchase_entity", "purchase_entity"),
    ("supplier", "supplier"),
    ("domestic_source", "domestic_source"),
    ("trade_term", "trade_term"),
    ("payment_method_name", "payment_method_name"),
    ("currency", "currency"),
    ("sku", "sku"),
    ("pieces", "pieces"),
    ("product_name", "product_name"),
    ("customs_name_cn", "customs_name_cn"),
    ("customs_name_en", "customs_name_en"),
    ("unit", "unit"),
    ("shipment_quantity", "shipment_quantity"),
    ("purchase_unit_price", "purchase_unit_price"),
    ("logistics_provider", "logistics_provider"),
    ("logistics_channel", "logistics_channel"),
    ("transport_method", "transport_method"),
    ("logistics_center_code", "logistics_center_code"),
    ("package_type", "package_type"),
    ("box_no", "box_no"),
    ("box_count", "box_count"),
    ("total_gross_weight", "total_gross_weight"),
    ("total_net_weight", "total_net_weight"),
    ("outer_box_size", "outer_box_size"),
    ("volume", "volume"),
    ("updated_at", "updated_at"),
]

SSHTunnelForwarderFactory: Any | None = None
PyMySQLModule: Any | None = None


class MySQLExportError(RuntimeError):
    pass


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    table: str = "customs_bill_parcels"
    charset: str = "utf8mb4"
    use_ssh_tunnel: bool = False
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_user: str = ""
    ssh_password: str = ""

    @classmethod
    def from_env(cls) -> "MySQLConfig":
        _load_dotenv()
        config = cls(
            host=os.getenv("MYSQL_HOST", ""),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", ""),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", ""),
            table=os.getenv("MYSQL_TABLE", "customs_bill_parcels"),
            use_ssh_tunnel=_env_bool(os.getenv("MYSQL_USE_SSH_TUNNEL", "0")),
            ssh_host=os.getenv("SSH_HOST", ""),
            ssh_port=int(os.getenv("SSH_PORT", "22")),
            ssh_user=os.getenv("SSH_USER", ""),
            ssh_password=os.getenv("SSH_PASSWORD", ""),
        )
        missing = [
            name
            for name, value in (
                ("MYSQL_HOST", config.host),
                ("MYSQL_USER", config.user),
                ("MYSQL_PASSWORD", config.password),
                ("MYSQL_DATABASE", config.database),
                ("MYSQL_TABLE", config.table),
            )
            if not value
        ]
        if missing:
            raise MySQLExportError("Missing MySQL config in .env: " + ", ".join(missing))
        if config.use_ssh_tunnel:
            ssh_missing = [
                name
                for name, value in (
                    ("SSH_HOST", config.ssh_host),
                    ("SSH_USER", config.ssh_user),
                    ("SSH_PASSWORD", config.ssh_password),
                )
                if not value
            ]
            if ssh_missing:
                raise MySQLExportError("Missing SSH tunnel config in .env: " + ", ".join(ssh_missing))
        return config


def export_customs_rows_to_mysql(data: CustomsWorkbookData, config: MySQLConfig | None = None) -> int:
    config = config or MySQLConfig.from_env()
    rows = [mysql_row_values(row) for row in data.customs_rows]
    if not rows:
        return 0

    connection = None
    tunnel = None
    try:
        connection, tunnel = _open_mysql_connection(config)
        with connection.cursor() as cursor:
            table_columns = _fetch_table_columns(cursor, config.table)
            validate_table_columns(table_columns)
            cursor.executemany(build_upsert_sql(config.table), rows)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()
        if tunnel is not None:
            tunnel.stop()
    return len(rows)


def _open_mysql_connection(config: MySQLConfig) -> tuple[Any, Any | None]:
    pymysql = _pymysql_module()

    host = config.host
    port = config.port
    tunnel = None
    if config.use_ssh_tunnel:
        tunnel = _open_ssh_tunnel(config)
        host = "127.0.0.1"
        port = int(tunnel.local_bind_port)

    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset=config.charset,
            autocommit=False,
        )
    except Exception as exc:
        if tunnel is not None:
            tunnel.stop()
        target = f"{host}:{port}" if config.use_ssh_tunnel else f"{config.host}:{config.port}"
        raise MySQLExportError(f"Could not connect to MySQL via {target}: {exc}") from exc
    return connection, tunnel


def _open_ssh_tunnel(config: MySQLConfig) -> Any:
    tunnel_factory = _ssh_tunnel_factory()

    try:
        tunnel = tunnel_factory(
            (config.ssh_host, config.ssh_port),
            ssh_username=config.ssh_user,
            ssh_password=config.ssh_password,
            remote_bind_address=(config.host, config.port),
            local_bind_address=("127.0.0.1", 0),
        )
        tunnel.start()
    except Exception as exc:
        raise MySQLExportError(f"Could not open SSH tunnel {config.ssh_host}:{config.ssh_port} -> {config.host}:{config.port}: {exc}") from exc
    return tunnel


def _pymysql_module() -> Any:
    if PyMySQLModule is not None:
        return PyMySQLModule
    try:
        import pymysql
    except ImportError as exc:
        raise MySQLExportError("PyMySQL is not installed. Run: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt") from exc
    return pymysql


def _ssh_tunnel_factory() -> Any:
    if SSHTunnelForwarderFactory is not None:
        return SSHTunnelForwarderFactory
    try:
        from sshtunnel import SSHTunnelForwarder
    except ImportError as exc:
        raise MySQLExportError("sshtunnel is not installed. Run: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt") from exc
    return SSHTunnelForwarder


def mysql_row_values(row: CustomsRow) -> tuple[Any, ...]:
    return tuple(_mysql_value(getattr(row, attr)) for attr, _ in MYSQL_COLUMNS)


def build_upsert_sql(table: str) -> str:
    columns = [column for _, column in MYSQL_COLUMNS]
    column_sql = ", ".join(_quote_identifier(column) for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    update_sql = ", ".join(
        f"{_quote_identifier(column)}=VALUES({_quote_identifier(column)})"
        for column in columns
        if column != "id"
    )
    return f"INSERT INTO {_quote_identifier(table)} ({column_sql}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_sql}"


def validate_table_columns(table_columns: Iterable[str]) -> None:
    actual = {column.lower() for column in table_columns}
    required = [column for _, column in MYSQL_COLUMNS]
    missing = [column for column in required if column.lower() not in actual]
    if missing:
        raise MySQLExportError("customs_bill_parcels is missing columns: " + ", ".join(missing))


def _fetch_table_columns(cursor: Any, table: str) -> set[str]:
    cursor.execute(f"SHOW COLUMNS FROM {_quote_identifier(table)}")
    columns: set[str] = set()
    for row in cursor.fetchall():
        if isinstance(row, dict):
            field = row.get("Field")
        else:
            field = row[0] if row else None
        if field:
            columns.add(str(field))
    return columns


def _mysql_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if value is None:
        return ""
    return value


def _quote_identifier(value: str) -> str:
    if not value or "`" in value:
        raise MySQLExportError(f"Invalid MySQL identifier: {value!r}")
    return f"`{value}`"


def _env_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}
