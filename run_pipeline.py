import csv
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "data" / "sales_data.csv"
DB_FILE = BASE_DIR / "sales.db"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def run_pipeline():
    started_at = datetime.now(timezone.utc).isoformat()
    rows_read = inserted = skipped = 0

    try:
        if not CSV_FILE.exists():
            raise FileNotFoundError(f"Source CSV not found: {CSV_FILE}")

        with sqlite3.connect(DB_FILE) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    order_id INTEGER PRIMARY KEY,
                    product TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_amount REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    rows_read INTEGER NOT NULL,
                    rows_inserted INTEGER NOT NULL,
                    rows_skipped INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
            """)

            with CSV_FILE.open("r", newline="", encoding="utf-8") as source:
                reader = csv.DictReader(source)
                required = {"order_id", "product", "category", "quantity", "unit_price"}
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError(f"CSV must contain: {sorted(required)}")

                for row in reader:
                    rows_read += 1
                    quantity = int(row["quantity"])
                    unit_price = float(row["unit_price"])
                    cursor.execute("""
                        INSERT OR IGNORE INTO sales
                        (order_id, product, category, quantity, unit_price, total_amount)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        int(row["order_id"]), row["product"], row["category"],
                        quantity, unit_price, round(quantity * unit_price, 2)
                    ))
                    if cursor.rowcount == 1:
                        inserted += 1
                    else:
                        skipped += 1

            cursor.execute("""
                INSERT INTO pipeline_runs
                (started_at, rows_read, rows_inserted, rows_skipped, status)
                VALUES (?, ?, ?, ?, 'SUCCESS')
            """, (started_at, rows_read, inserted, skipped))
            total = cursor.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

        message = (
            f"SUCCESS | read={rows_read} | inserted={inserted} | "
            f"skipped={skipped} | total_in_database={total}"
        )
        logging.info(message)
        print(message)

    except Exception as error:
        logging.exception("FAILED | %s", error)
        # Record failed attempts separately without hiding the original error.
        with sqlite3.connect(DB_FILE) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    rows_read INTEGER NOT NULL,
                    rows_inserted INTEGER NOT NULL,
                    rows_skipped INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            connection.execute("""
                INSERT INTO pipeline_runs
                (started_at, rows_read, rows_inserted, rows_skipped, status)
                VALUES (?, ?, ?, ?, 'FAILED')
            """, (started_at, rows_read, inserted, skipped))
        raise

if __name__ == "__main__":
    run_pipeline()
