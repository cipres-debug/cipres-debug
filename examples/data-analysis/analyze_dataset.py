#!/usr/bin/env python3
"""Deterministic CSV/JSON profiling with a small dependency-free SVG chart."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def _records_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        for key in ("records", "rows", "data", "items"):
            if key in value:
                value = value[key]
                break
        else:
            value = [value]
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("JSON input must be an object or an array of objects")
    return [dict(row) for row in value]


def load_records(path: str | Path) -> list[dict[str, Any]]:
    """Load a CSV or JSON file as a list of dictionaries."""
    source = Path(path)
    if source.suffix.lower() == ".csv":
        with source.open(newline="", encoding="utf-8-sig") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    with source.open(encoding="utf-8") as handle:
        return _records_from_json(json.load(handle))


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _number(value: Any) -> float | None:
    if _is_missing(value) or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def profile(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    columns = sorted({key for row in rows for key in row})
    result: dict[str, Any] = {"row_count": len(rows), "columns": columns, "fields": {}}
    for column in columns:
        values = [row.get(column) for row in rows]
        numbers = [number for value in values if (number := _number(value)) is not None]
        non_missing = [value for value in values if not _is_missing(value)]
        field: dict[str, Any] = {
            "missing": len(values) - len(non_missing),
            "distinct": len({json.dumps(value, sort_keys=True, ensure_ascii=False, default=str) for value in non_missing}),
        }
        if numbers and len(numbers) == len(non_missing):
            field.update(
                kind="numeric",
                min=min(numbers),
                max=max(numbers),
                mean=sum(numbers) / len(numbers),
            )
        else:
            field["kind"] = "categorical"
            counts = Counter(str(value) for value in non_missing)
            field["top_values"] = [
                {"value": value, "count": count}
                for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
            ]
        result["fields"][column] = field
    return result


def render_svg(summary: dict[str, Any], width: int = 720, height: int = 360) -> str:
    """Render a compact bar chart of missing values per field."""
    fields = summary["fields"]
    labels = list(fields)
    maximum = max((field["missing"] for field in fields.values()), default=0)
    maximum = max(maximum, 1)
    chart_left, chart_top, chart_width, chart_height = 60, 55, width - 90, height - 105
    bar_width = chart_width / max(len(labels), 1)
    bars = []
    for index, label in enumerate(labels):
        missing = fields[label]["missing"]
        bar_height = chart_height * missing / maximum
        x = chart_left + index * bar_width + bar_width * 0.15
        y = chart_top + chart_height - bar_height
        bars.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width * .7:.2f}" '
            f'height="{bar_height:.2f}" fill="#26c6a8"><title>{label}: {missing} missing</title></rect>'
        )
    labels_svg = "".join(
        f'<text x="{chart_left + i * bar_width + bar_width / 2:.2f}" y="{height - 30}" '
        f'text-anchor="middle" font-size="11" transform="rotate(-35 {chart_left + i * bar_width + bar_width / 2:.2f} {height - 30})">'
        f'{label[:18]}</text>'
        for i, label in enumerate(labels)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#101820"/>'
        f'<text x="{chart_left}" y="28" fill="#f1f5f4" font-size="18" font-family="sans-serif">Missing values by field</text>'
        f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" '
        f'y2="{chart_top + chart_height}" stroke="#a8b5b2"/>{"".join(bars)}{labels_svg}</svg>'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV or JSON file")
    parser.add_argument("--json-out", default="summary.json", help="summary output path")
    parser.add_argument("--svg-out", default="missing-values.svg", help="SVG chart output path")
    args = parser.parse_args()
    summary = profile(load_records(args.input))
    Path(args.json_out).write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.svg_out).write_text(render_svg(summary) + "\n", encoding="utf-8")
    print(json.dumps({"rows": summary["row_count"], "columns": len(summary["columns"]), "json": args.json_out, "svg": args.svg_out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
