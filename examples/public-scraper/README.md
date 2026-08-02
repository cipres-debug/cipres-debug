# Public HTML table scraper example

This dependency-free Python CLI extracts a table from a public HTML page and
writes normalized JSON and CSV. It trims cell whitespace, gives blank or
duplicate headers stable names, removes exact duplicate rows, and uses a clear
user agent and timeout. It does not bypass authentication, CAPTCHAs, paywalls,
robots/access controls, or site prohibitions.

```powershell
python scrape_table.py sample.html --json-out rows.json --csv-out rows.csv
python -m unittest discover -s tests -v
```

For a live page, pass its public `https://` URL. The buyer must supply target
URLs and requested fields before a paid implementation begins.
