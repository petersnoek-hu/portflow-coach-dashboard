"""Make small .xlsx files for tests (stdlib only). All names in tests are invented."""

import io
import zipfile
from xml.sax.saxutils import escape


def _col(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _sheet_xml(rows) -> str:
    out = []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, value in enumerate(row):
            ref = f"{_col(c)}{r}"
            if value is None or value == "":
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            elif isinstance(value, str) and value.startswith("#") and value.upper() == value:
                cells.append(f'<c r="{ref}" t="e"><v>{escape(value)}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        out.append(f'<row r="{r}">{"".join(cells)}</row>')
    return ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/'
            f'spreadsheetml/2006/main"><sheetData>{"".join(out)}</sheetData></worksheet>')


def make_xlsx(sheets: dict) -> bytes:
    """sheets: {name: rows}; a name starting with '~' is a hidden sheet."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        entries, rels = [], []
        for i, (name, rows) in enumerate(sheets.items(), start=1):
            hidden = name.startswith("~")
            state = ' state="hidden"' if hidden else ""
            entries.append(f'<sheet name="{escape(name.lstrip("~"))}" sheetId="{i}"{state} r:id="rId{i}"/>')
            rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                        f'relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(rows))
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.'
                   'openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/'
                   f'officeDocument/2006/relationships"><sheets>{"".join(entries)}</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns='
                   f'"http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>')
    return buffer.getvalue()
