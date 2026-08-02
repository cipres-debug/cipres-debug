#!/usr/bin/env python3
"""Extract a public HTML table into deterministic JSON and CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table" and self._table is None:
            self._table = []
        elif tag == "tr" and self._table is not None and self._row is None:
            self._row = []
        elif tag in {"th", "td"} and self._row is not None and self._cell is None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"th", "td"} and self._cell is not None and self._row is not None:
            self._row.append(_clean("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def parse_tables(html: str) -> list[list[list[str]]]:
    parser = TableParser()
    parser.feed(html)
    parser.close()
    return parser.tables


def rows_from_table(table: list[list[str]]) -> list[dict[str, str]]:
    if not table:
        return []
    width = max(len(row) for row in table)
    raw_headers = (table[0] + [""] * width)[:width]
    headers: list[str] = []
    for index, header in enumerate(raw_headers, 1):
        base = _clean(header) or f"column_{index}"
        candidate = base
        suffix = 2
        while candidate in headers:
            candidate = f"{base}_{suffix}"
            suffix += 1
        headers.append(candidate)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for values in table[1:]:
        cells = (values + [""] * width)[:width]
        row = dict(zip(headers, cells))
        fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if any(cells) and fingerprint not in seen:
            result.append(row)
            seen.add(fingerprint)
    return result


def fetch_html(url: str, timeout: float = 15.0) -> str:
    request = Request(url, headers={"User-Agent": "cipres-public-table-scraper/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def write_outputs(rows: Iterable[dict[str, str]], json_path: str | Path, csv_path: str | Path) -> int:
    materialized = list(rows)
    Path(json_path).write_text(json.dumps(materialized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    headers = list(materialized[0]) if materialized else []
    with Path(csv_path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        if headers:
            writer.writeheader()
            writer.writerows(materialized)
    return len(materialized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="public http(s) URL or local HTML path")
    parser.add_argument("--table-index", type=int, default=0)
    parser.add_argument("--json-out", default="rows.json")
    parser.add_argument("--csv-out", default="rows.csv")
    args = parser.parse_args()
    source = Path(args.url)
    html = source.read_text(encoding="utf-8") if source.exists() else fetch_html(args.url)
    tables = parse_tables(html)
    if not 0 <= args.table_index < len(tables):
        raise SystemExit(f"table index {args.table_index} unavailable; found {len(tables)} table(s)")
    rows = rows_from_table(tables[args.table_index])
    count = write_outputs(rows, args.json_out, args.csv_out)
    print(json.dumps({"rows": count, "json": args.json_out, "csv": args.csv_out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
