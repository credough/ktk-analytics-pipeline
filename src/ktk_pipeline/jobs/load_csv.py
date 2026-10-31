"""
Loads Meta Business Suite CSV exports into Supabase's fact_daily_metrics table.
Works for both Facebook and Instagram exports.

All exports share the same structure:
  Row 1: sep=,
  Row 2: metric title (ignored)
  Row 3: header -> Date, Primary
  Row 4+: data rows

Usage:
    python -m ktk_pipeline.jobs.load_csv --platform fb --folder "C:\\path\to\\FB"
    python -m ktk_pipeline.jobs.load_csv --platform ig --folder "C:\\path\to\\IG"
"""

import argparse
import csv
import os

from ktk_pipeline.config.settings import SupabaseSettings
from ktk_pipeline.db.client import get_client
from ktk_pipeline.db.repository import DailyMetric, upsert_daily_metrics

# Filename -> metric_name mapping. Same filenames used across FB and IG,
# EXCEPT Instagram uses Reach.csv instead of Viewers.csv (different metric
# semantics: unique accounts reached, not raw viewer count).
FILE_METRIC_MAP = {
    "Views.csv": "views",
    "Viewers.csv": "viewers",       # FB only
    "Reach.csv": "reach",           # IG only
    "Link_clicks.csv": "link_clicks",
    "Visits.csv": "visits",
    "Follows.csv": "follows",
    "Interactions.csv": "content_interactions",
}


def parse_meta_csv(filepath):
    """Decode a UTF-16 Meta export and return list of (date, value) tuples."""
    with open(filepath, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-16")
    lines = text.splitlines()

    # Row 0 = sep=,   Row 1 = metric title   Row 2 = header   Row 3+ = data
    data_lines = lines[3:]
    reader = csv.reader(data_lines)

    rows = []
    for row in reader:
        if not row or len(row) < 2:
            continue
        date_str, value_str = row[0], row[1]
        date_only = date_str.split("T")[0]
        try:
            value = float(value_str)
        except ValueError:
            continue
        rows.append((date_only, value))
    return rows


def main():
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=["fb", "ig"],
                         help="Platform id to tag these rows with")
    parser.add_argument("--folder", default=".",
                         help="Folder containing the CSV exports")
    args = parser.parse_args()

    client = get_client(SupabaseSettings.from_env())
    platform_id = args.platform
    uploads_dir = args.folder

    all_records: list[DailyMetric] = []

    for filename, metric_name in FILE_METRIC_MAP.items():
        filepath = os.path.join(uploads_dir, filename)
        if not os.path.exists(filepath):
            continue  # expected -- e.g. FB has no Reach.csv, IG has no Viewers.csv

        rows = parse_meta_csv(filepath)
        print(f"Parsed {filename}: {len(rows)} rows -> metric '{metric_name}' ({platform_id})")

        for date_str, value in rows:
            all_records.append({
                "date": date_str,
                "platform_id": platform_id,
                "metric_name": metric_name,
                "value": value,
            })

    print(f"\nTotal records to upsert: {len(all_records)}")

    def report_batch(batch_number: int, batch_size: int) -> None:
        print(f"  Upserted batch {batch_number}: {batch_size} rows")

    upsert_daily_metrics(client, all_records, on_batch=report_batch)

    print("\nDone. Verify with:")
    print("  select metric_name, count(*), min(date), max(date)")
    print(f"  from fact_daily_metrics where platform_id = '{platform_id}' group by metric_name;")


if __name__ == "__main__":
    main()
