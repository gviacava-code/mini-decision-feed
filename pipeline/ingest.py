"""
SESSION 1 — Ingestion Script
────────────────────────────
Reads sales.csv and loads it into a local DuckDB database.
Run with:  python pipeline/ingest.py
"""

import duckdb
import os

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH   = os.path.join(ROOT_DIR, "data", "sales.csv")
DB_PATH    = os.path.join(ROOT_DIR, "data", "sales.duckdb")

def ingest():
    print("🚀 Starting ingestion...")
    print(f"   Reading CSV  : {CSV_PATH}")
    print(f"   Writing to DB: {DB_PATH}")

    # Connect to DuckDB (creates the file if it doesn't exist)
    con = duckdb.connect(DB_PATH)

    # Drop the table if it already exists so re-runs are safe
    con.execute("DROP TABLE IF EXISTS raw_sales")

    # Read the CSV directly into DuckDB — no pandas needed!
    con.execute(f"""
        CREATE TABLE raw_sales AS
        SELECT *
        FROM read_csv_auto('{CSV_PATH}')
    """)

    # Quick sanity check
    count = con.execute("SELECT COUNT(*) FROM raw_sales").fetchone()[0]
    print(f"\n✅ Ingestion complete — {count} rows loaded into raw_sales")

    # Preview the first 5 rows so you can see what landed
    print("\n📋 Preview (first 5 rows):")
    print("-" * 50)
    rows = con.execute("SELECT * FROM raw_sales LIMIT 5").fetchdf()
    print(rows.to_string(index=False))

    # Show all tables in the database
    tables = con.execute("SHOW TABLES").fetchdf()
    print(f"\n📦 Tables in database: {list(tables['name'])}")

    con.close()
    print("\n🎉 Done! Your DuckDB database is ready at: data/sales.duckdb")

if __name__ == "__main__":
    ingest()
