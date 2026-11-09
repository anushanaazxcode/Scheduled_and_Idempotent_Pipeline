# Task 03 — Scheduled and Idempotent Pipeline

A Python + SQLite sales pipeline that can be run repeatedly, loads only new orders, logs each run, and is scheduled with GitHub Actions.

## Project structure

- `data/sales_data.csv` — input dataset.
- `run_pipeline.py` — ETL/incremental loading script.
- `sales.db` — SQLite database created automatically.
- `logs/pipeline.log` — execution log.
- `.github/workflows/scheduled-pipeline.yml` — daily GitHub Actions schedule.

## How it works

1. `order_id` is the primary key and unique identifier.
2. `INSERT OR IGNORE` inserts new order IDs and skips IDs already in the database.
3. The existing database is reused; the pipeline does not drop or reload the sales table.
4. `pipeline_runs` records each run's timestamp, rows read, inserted, skipped, and status.
5. GitHub Actions restores the previous SQLite database from its cache, runs the pipeline, and saves the updated database under a new cache key.
6. The workflow runs daily at 09:00 IST and can also be started manually from the Actions tab.

## Run locally

Requires Python 3.11 or later. No third-party packages are required.

```bash
python run_pipeline.py
```

Run it a second time. The first run should insert the 8 sample orders; the second should insert 0 and skip 8.

## Test incremental loading

Add a new row with a new `order_id` to `data/sales_data.csv`, then run the script. Only the new row should be inserted. Run it again and the new row should be skipped.

## Check database and run history

```bash
python -c "import sqlite3; c=sqlite3.connect('sales.db'); print('Sales:', c.execute('SELECT COUNT(*) FROM sales').fetchone()[0]); print('Runs:', c.execute('SELECT * FROM pipeline_runs').fetchall()); c.close()"
```

Open `logs/pipeline.log` to see the run log.

## GitHub scheduling

Push the project to a public GitHub repository. Open **Actions → Scheduled Sales Pipeline** and choose **Run workflow** for a manual test. The scheduled workflow runs every day at 09:00 India time (03:30 UTC).

The workflow uses GitHub Actions cache to carry the SQLite database between scheduled runs. Cache entries are immutable, so every run saves using a unique key and restores using the `sales-db-` prefix. GitHub may evict caches after periods of inactivity; for a production-critical pipeline, use a persistent database or external storage rather than relying on a cache.

## Design decision / limitation

The source file has no update timestamp, so `order_id` is treated as the stable unique key. New orders are loaded incrementally, but changed details for an existing order ID are not updated.
