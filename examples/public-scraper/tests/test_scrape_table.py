import unittest

from scrape_table import parse_tables, rows_from_table


class ScrapeTableTests(unittest.TestCase):
    HTML = """
    <table><thead><tr><th> SKU </th><th>Price</th><th>Price</th></tr></thead>
    <tbody><tr><td>A-1</td><td>$10</td><td>10</td></tr>
    <tr><td>A-1</td><td>$10</td><td>10</td></tr><tr><td>B-2</td><td> $12 </td><td>12</td></tr></tbody></table>
    """

    def test_extracts_headers_normalizes_and_deduplicates(self):
        tables = parse_tables(self.HTML)
        self.assertEqual(len(tables), 1)
        self.assertEqual(rows_from_table(tables[0]), [
            {"SKU": "A-1", "Price": "$10", "Price_2": "10"},
            {"SKU": "B-2", "Price": "$12", "Price_2": "12"},
        ])

    def test_empty_table_has_no_rows(self):
        self.assertEqual(rows_from_table([]), [])

    def test_parser_handles_multiple_tables(self):
        self.assertEqual(len(parse_tables("<table><tr><th>a</th></tr><tr><td>b</td></tr></table>")), 1)

