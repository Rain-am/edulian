from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


SheetData = tuple[str, list[tuple[str, str]], list[dict[str, Any]]]

STYLE_DEFAULT = 0
STYLE_HEADER = 1
STYLE_DATE = 2
STYLE_TEXT = 3


def write_xlsx_workbook(
    sheets: list[SheetData],
    output_path: Path,
    *,
    text_keys: set[str] | None = None,
    date_keys: set[str] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text_keys = text_keys or set()
    date_keys = date_keys or set()
    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        _write_static_parts(archive, sheets)
        for index, (_, headers, rows) in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _worksheet_xml(headers, rows, text_keys, date_keys))


def _excel_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value.normalize())
    return value


def _write_static_parts(archive: ZipFile, sheets: list[SheetData]) -> None:
    archive.writestr(
        "[Content_Types].xml",
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
""" + "".join(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for index in range(1, len(sheets) + 1)
        ) + "\n</Types>",
    )
    archive.writestr(
        "_rels/.rels",
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
    )
    archive.writestr(
        "xl/_rels/workbook.xml.rels",
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
""" + "".join(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, len(sheets) + 1)
        ) + f'\n<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        + "\n</Relationships>",
    )
    archive.writestr(
        "xl/workbook.xml",
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
""" + "".join(
            f'<sheet name="{escape(title)}" sheetId="{index}" r:id="rId{index}"/>'
            for index, (title, _, _) in enumerate(sheets, start=1)
        ) + "\n</sheets></workbook>",
    )
    archive.writestr(
        "xl/styles.xml",
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy-mm-dd"/></numFmts>
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFD9EAF7"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="4">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
</cellXfs>
</styleSheet>""",
    )


def _worksheet_xml(headers: list[tuple[str, str]], rows: list[dict[str, Any]], text_keys: set[str], date_keys: set[str]) -> str:
    row_xml = [_row_xml(1, [("", label) for _, label in headers], STYLE_HEADER, text_keys, date_keys)]
    for row_index, row in enumerate(rows, start=2):
        values = [(key, _excel_value(row.get(key))) for key, _ in headers]
        row_xml.append(_row_xml(row_index, values, STYLE_DEFAULT, text_keys, date_keys))
    dimension = f"A1:{_column_name(len(headers))}{len(rows) + 1}"
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<dimension ref="{dimension}"/>
<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
<sheetData>
{''.join(row_xml)}
</sheetData>
<autoFilter ref="{dimension}"/>
</worksheet>"""


def _row_xml(row_index: int, values: list[tuple[str, Any]], style: int, text_keys: set[str], date_keys: set[str]) -> str:
    cells = []
    for column_index, (key, value) in enumerate(values, start=1):
        ref = f"{_column_name(column_index)}{row_index}"
        cells.append(_cell_xml(ref, key, value, style, text_keys, date_keys))
    return f'<row r="{row_index}">{"".join(cells)}</row>'


def _cell_xml(ref: str, key: str, value: Any, style: int, text_keys: set[str], date_keys: set[str]) -> str:
    if key in text_keys:
        return _text_cell_xml(ref, value, STYLE_TEXT)
    if key in date_keys:
        excel_date = _excel_date_number(value)
        if excel_date is not None:
            return f'<c r="{ref}" s="{STYLE_DATE}"><v>{excel_date}</v></c>'

    style_attr = f' s="{style}"' if style else ""
    if value is None:
        return f'<c r="{ref}"{style_attr}/>'
    if isinstance(value, (int, float)) or (isinstance(value, str) and _is_number(value)):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    return _text_cell_xml(ref, value, style)


def _text_cell_xml(ref: str, value: Any, style: int) -> str:
    style_attr = f' s="{style}"' if style else ""
    if value is None:
        return f'<c r="{ref}" t="inlineStr"{style_attr}/>'
    text = escape(str(value))
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{text}</t></is></c>'


def _excel_date_number(value: Any) -> int | None:
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    else:
        return None
    return (parsed - date(1899, 12, 30)).days


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _is_number(value: str) -> bool:
    try:
        Decimal(value)
    except Exception:
        return False
    return True
