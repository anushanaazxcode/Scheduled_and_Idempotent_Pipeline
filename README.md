# Task 03 — Scheduled and Idempotent Pipeline

A small Python + SQLite pipeline that loads sales records incrementally, avoids duplicates, logs each run, and can run automatically on GitHub Actions.

## Project files

- `data/sales_data.csv` — source sales data.
- `run_pipeline.py` — reads the CSV and inserts only records not already present.
- `sales.db` — SQLite database created automatically when the script runs.
- `logs/pipeline.log` — run log created automatically.
- `.github/workflows/scheduled-pipeline.yml` — daily scheduled GitHub Actions workflow.

## How it works

1. `order_id` is the unique primary key.
2. The pipeline uses `INSERT OR IGNORE`. Existing order IDs are skipped; new order IDs are inserted.
3. The database is not dropped or reloaded on each run.
4. `pipeline_runs` stores the time, number of rows read, inserted, skipped, and run status.
5. GitHub Actions runs the pipeline daily at 09:00 IST. It can also be started manually from the Actions tab.

## Run locally

Requires Python 3. No external packages are needed.

```bash
python run_pipeline.py
```

Run the command a second time. The database record count should remain unchanged and the second run should report zero inserted rows.

## Test incremental loading

Add a new row to `data/sales_data.csv` with a new `order_id`, then run:

```bash
python run_pipeline.py
```

Only the new order should be inserted. Run it again and that order should be skipped.

## Check the database

Use a SQLite viewer or run this Python command:

```bash
python -c "import sqlite3; c=sqlite3.connect('sales.db'); print('Sales rows:', c.execute('SELECT COUNT(*) FROM sales').fetchone()[0]); print('Run history:', c.execute('SELECT * FROM pipeline_runs').fetchall()); c.close()"
```

## Check logs

Open `logs/pipeline.log`. Each successful or failed run is recorded there.

## Scheduling

After pushing this repository to GitHub, open **Actions** to see workflow runs. The workflow runs daily at 09:00 India time (GitHub cron uses UTC). You can also choose **Scheduled Sales Pipeline → Run workflow** to test it manually.

**Design decision:** `order_id` is treated as the stable unique key because the supplied sales dataset does not contain an update timestamp. This implementation is incremental for new orders; it does not update an existing order if its other fields change.
