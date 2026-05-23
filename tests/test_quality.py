"""
SESSION 2 — Data Quality Tests
────────────────────────────────
Validates the data in DuckDB AFTER dbt has run.
Run with:  pytest tests/ -v

These tests mirror what a real data team would check before
trusting a dataset to power a business-facing API.
"""

import pytest
import duckdb
import os

# ── Setup ──────────────────────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(ROOT_DIR, "data", "sales.duckdb")

@pytest.fixture(scope="module")
def con():
    """Opens a DuckDB connection shared across all tests in this module."""
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Database not found at {DB_PATH}. Run ingest.py first.")
    conn = duckdb.connect(DB_PATH, read_only=True)
    yield conn
    conn.close()


# ── Raw layer tests ────────────────────────────────────────────────────────

class TestRawSales:
    """Checks the raw table loaded by ingest.py."""

    def test_table_exists(self, con):
        tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()
        assert "raw_sales" in tables, "raw_sales table not found — did you run ingest.py?"

    def test_row_count(self, con):
        count = con.execute("SELECT COUNT(*) FROM raw_sales").fetchone()[0]
        assert count == 36, f"Expected 36 rows, got {count}"

    def test_no_null_product(self, con):
        nulls = con.execute("SELECT COUNT(*) FROM raw_sales WHERE product IS NULL").fetchone()[0]
        assert nulls == 0, f"Found {nulls} rows with null product"

    def test_no_null_revenue(self, con):
        nulls = con.execute("SELECT COUNT(*) FROM raw_sales WHERE revenue IS NULL").fetchone()[0]
        assert nulls == 0, f"Found {nulls} rows with null revenue"

    def test_no_negative_revenue(self, con):
        bad = con.execute("SELECT COUNT(*) FROM raw_sales WHERE revenue <= 0").fetchone()[0]
        assert bad == 0, f"Found {bad} rows with zero or negative revenue"

    def test_no_negative_units(self, con):
        bad = con.execute("SELECT COUNT(*) FROM raw_sales WHERE units_sold <= 0").fetchone()[0]
        assert bad == 0, f"Found {bad} rows with zero or negative units_sold"

    def test_product_values(self, con):
        products = set(con.execute("SELECT DISTINCT product FROM raw_sales").fetchdf()["product"].tolist())
        expected = {"Product_A", "Product_B", "Product_C"}
        assert products == expected, f"Unexpected products found: {products - expected}"


# ── Mart layer tests ───────────────────────────────────────────────────────

class TestMartRevenueGrowth:
    """Checks the transformed mart table built by dbt."""

    def test_mart_exists(self, con):
        tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()
        assert "mart_revenue_growth" in tables, \
            "mart_revenue_growth not found — did you run 'dbt run'?"

    def test_mart_row_count(self, con):
        count = con.execute("SELECT COUNT(*) FROM mart_revenue_growth").fetchone()[0]
        assert count == 36, f"Expected 36 rows in mart, got {count}"

    def test_growth_pct_only_null_for_first_month(self, con):
        nulls = con.execute("""
            SELECT COUNT(*) FROM mart_revenue_growth
            WHERE mom_growth_pct IS NULL
        """).fetchone()[0]
        assert nulls == 3, f"Expected 3 null growth values (first months), got {nulls}"

    def test_no_null_revenue_in_mart(self, con):
        nulls = con.execute("""
            SELECT COUNT(*) FROM mart_revenue_growth WHERE revenue IS NULL
        """).fetchone()[0]
        assert nulls == 0, f"Found {nulls} null revenue values in mart"

    def test_revenue_is_always_positive(self, con):
        bad = con.execute("""
            SELECT COUNT(*) FROM mart_revenue_growth WHERE revenue <= 0
        """).fetchone()[0]
        assert bad == 0, f"Found {bad} non-positive revenue rows in mart"

    def test_product_a_december_is_highest(self, con):
        result = con.execute("""
            SELECT month FROM mart_revenue_growth
            WHERE product = 'Product_A'
            ORDER BY revenue DESC
            LIMIT 1
        """).fetchone()[0]
        assert str(result).startswith("2024-12"), \
            f"Expected Product_A peak in December, got {result}"

    def test_rolling_average_is_populated(self, con):
        nulls = con.execute("""
            SELECT COUNT(*) FROM mart_revenue_growth
            WHERE rolling_3m_avg_revenue IS NULL
        """).fetchone()[0]
        assert nulls == 0, f"Found {nulls} null rolling average values"

    def test_risk_flag_is_boolean(self, con):
        bad = con.execute("""
            SELECT COUNT(*) FROM mart_revenue_growth
            WHERE is_revenue_drop NOT IN (true, false)
        """).fetchone()[0]
        assert bad == 0, f"Found {bad} non-boolean values in is_revenue_drop"
