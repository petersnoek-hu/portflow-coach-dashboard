"""Read the cell values of an .xlsx file without extra packages (spec 013).

An .xlsx file is a zip archive with XML parts. Only what an import needs is read:
the worksheets (name, hidden or not) and the value of every cell as text. Shared
strings, inline strings, numbers, booleans, errors and the stored result of a
formula are supported; styles, dates as dates and merged cells are not.
"""

import io
import re
import zipfile
from dataclasses import dataclass
from xml.etree import ElementTree

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
MAX_ROWS = 5000


class NotAnXlsx(Exception):
    """The file is not an .xlsx file this reader can read."""


@dataclass
class Sheet:
    name: str
    hidden: bool
    rows: list[list[str]]


def _column(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "A").group(0)
    number = 0
    for letter in letters:
        number = number * 26 + ord(letter) - 64
    return number - 1


def _number_text(value: str) -> str:
    """'1234567.0' -> '1234567'; other numbers stay as they are."""
    try:
        number = float(value)
    except ValueError:
        return value
    return str(int(number)) if number.is_integer() and abs(number) < 1e15 else value


def _text(element) -> str:
    return "".join(node.text or "" for node in element.iter(f"{NS}t"))


def read_workbook(data: bytes) -> list[Sheet]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relations = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = [_text(item) for item in ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                      .findall(f"{NS}si")]
        targets = {rel.get("Id"): rel.get("Target") for rel in relations}
        sheets = []
        for sheet in workbook.find(f"{NS}sheets"):
            target = targets[sheet.get(f"{REL_NS}id")].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            sheets.append(Sheet(sheet.get("name"), sheet.get("state") in ("hidden", "veryHidden"),
                                _rows(archive.read(target), shared)))
        return sheets
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError, TypeError, AttributeError, IndexError,
            ValueError) as error:
        raise NotAnXlsx(str(error)) from None


def _rows(xml: bytes, shared: list[str]) -> list[list[str]]:
    rows = []
    for row in ElementTree.fromstring(xml).iter(f"{NS}row"):
        cells: dict[int, str] = {}
        for cell in row.findall(f"{NS}c"):
            kind, value = cell.get("t"), cell.find(f"{NS}v")
            if kind == "inlineStr":
                text = _text(cell)
            elif value is None or value.text is None:
                continue
            elif kind == "s":
                text = shared[int(value.text)]
            elif kind == "b":
                text = "ja" if value.text == "1" else "nee"
            elif kind in ("str", "e"):
                text = value.text
            else:
                text = _number_text(value.text)
            position = _column(cell.get("r")) if cell.get("r") else (max(cells) + 1 if cells else 0)
            cells[position] = text.strip()
        if any(cells.values()):
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        if len(rows) >= MAX_ROWS:
            break
    return rows
