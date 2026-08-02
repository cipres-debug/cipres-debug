# CSV/JSON data analysis example

This small, dependency-free CLI profiles a supplied CSV or JSON dataset and
writes two deterministic artifacts: a machine-readable `summary.json` and an
SVG chart of missing values. It is intentionally scoped to public or supplied
non-secret data; it does not fetch websites or handle credentials.

```powershell
python analyze_dataset.py examples.csv --json-out summary.json --svg-out missing-values.svg
python -m pytest -q tests
```

The profiler reports row count, sorted columns, missing values, distinct values,
numeric min/max/mean, and the five most common categorical values. JSON may be a
list of objects or an object containing `records`, `rows`, `data`, or `items`.
