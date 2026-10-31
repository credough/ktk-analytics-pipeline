"""
FB Page Insights -> Supabase (fact_daily_metrics, platform_id = 'fb')

Metrics (each verified against the Business Suite CSV exports, Jul 7-14 2026):
  views    <- page_media_view
  viewers  <- page_total_media_view_unique
  visits   <- page_views_total
  follows  <- page_daily_follows   (NOT page_follows, which is a running total)

link_clicks and content_interactions have no confirmed API match yet, so this
script does not touch them. Keep loading those from CSV with load_metrics.py.

Date rule: the API's end_time is the END of the day. Convert it to
America/Los_Angeles and subtract one day to get the same date the CSV uses.

Usage:
    python -m ktk_pipeline.jobs.fb_insights --start 2026-01-01          # backfill to yesterday
    python -m ktk_pipeline.jobs.fb_insights                    # daily run: last 3 days
    python -m ktk_pipeline.jobs.fb_insights --start 2026-07-07 --end 2026-07-15 --dry-run

Environment variables (never hardcode these or commit them):
  PAGE_ID, FB_SYSTEM_TOKEN, SUPABASE_URL, SUPABASE_KEY
Requires: install the project dependencies with `python -m pip install -e .`
"""

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from ktk_pipeline.config.settings import MetaSettings, SupabaseSettings
from ktk_pipeline.db.client import get_client
from ktk_pipeline.db.repository import DailyMetric, upsert_daily_metrics

GRAPH = "https://graph.facebook.com/v26.0"
LA = ZoneInfo("America/Los_Angeles")
PLATFORM_ID = "fb"
CHUNK_DAYS = 60  # stay well under Meta's per-request date range limit

METRICS = {
    "views": "page_media_view",
    "viewers": "page_total_media_view_unique",
    "visits": "page_views_total",
    "follows": "page_daily_follows",
}


def _redact_graph_error(message: str, token: str) -> str:
    """Remove access tokens and EAA-prefixed strings from Graph API errors."""
    redacted = message.replace(token, "[REDACTED]") if token else message
    return re.sub(r"EAA\S*", "[REDACTED]", redacted)


def graph_get(path, token, params=None):
    """GET from the Graph API. Errors print only Meta's message, never the URL."""
    query = dict(params or {})
    query["access_token"] = token
    resp = requests.get(f"{GRAPH}/{path}", params=query, timeout=30)
    try:
        body = resp.json()
    except ValueError:
        sys.exit(f"Graph API returned a non-JSON response (HTTP {resp.status_code}).")
    if resp.status_code != 200 or "error" in body:
        message = body.get("error", {}).get("message", f"HTTP {resp.status_code}")
        safe_message = _redact_graph_error(str(message), token)
        sys.exit(f"Graph API error on '{path}': {safe_message}")
    return body


def get_page_token(page_id, system_token):
    return graph_get(page_id, system_token, {"fields": "access_token"})["access_token"]


def to_csv_date(end_time):
    """'2026-07-08T07:00:00+0000' -> date(2026, 7, 7)."""
    dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z")
    return (dt.astimezone(LA) - timedelta(days=1)).date()


def fetch_metric(page_id, page_token, api_metric, start, end):
    """Return {date: value} for start..end inclusive."""
    series = {}
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=CHUNK_DAYS - 1), end)
        body = graph_get(
            f"{page_id}/insights",
            page_token,
            {
                "metric": api_metric,
                "period": "day",
                "since": cur.isoformat(),
                "until": (chunk_end + timedelta(days=1)).isoformat(),
            },
        )
        for item in body.get("data", []):
            for v in item.get("values", []):
                series[to_csv_date(v["end_time"])] = v["value"]
        cur = chunk_end + timedelta(days=1)
    return {d: val for d, val in series.items() if start <= d <= end}


def main():
    from dotenv import load_dotenv

    load_dotenv()

    ap = argparse.ArgumentParser()
    ap.add_argument("--start", help="YYYY-MM-DD (default: --days back from end)")
    ap.add_argument("--end", help="YYYY-MM-DD (default: yesterday, Pacific time)")
    ap.add_argument("--days", type=int, default=3,
                    help="days to re-pull when --start is not given (default 3)")
    ap.add_argument("--dry-run", action="store_true", help="print rows, don't write")
    args = ap.parse_args()

    yesterday = datetime.now(LA).date() - timedelta(days=1)
    end = date.fromisoformat(args.end) if args.end else yesterday
    start = (date.fromisoformat(args.start) if args.start
             else end - timedelta(days=args.days - 1))
    print(f"Range: {start} -> {end}")

    meta_settings = MetaSettings.from_env()
    page_id = meta_settings.page_id
    page_token = get_page_token(page_id, meta_settings.system_token)

    records: list[DailyMetric] = []
    for metric_name, api_metric in METRICS.items():
        series = fetch_metric(page_id, page_token, api_metric, start, end)
        print(f"{metric_name}: {len(series)} days  ({api_metric})")
        for d, value in series.items():
            records.append({
                "date": d.isoformat(),
                "platform_id": PLATFORM_ID,
                "metric_name": metric_name,
                "value": float(value),
            })
    records.sort(key=lambda r: (r["metric_name"], r["date"]))

    if args.dry_run:
        for r in records[:40]:
            print(r["date"], r["metric_name"], r["value"])
        if len(records) > 40:
            print(f"... {len(records) - 40} more rows")
        print(f"Dry run: {len(records)} rows, nothing written.")
        return

    client = get_client(SupabaseSettings.from_env())

    def report_batch(batch_number: int, batch_size: int) -> None:
        print(f"Upserted batch {batch_number}: {batch_size} rows")

    upsert_daily_metrics(client, records, on_batch=report_batch)
    print(f"Done: {len(records)} rows.")


if __name__ == "__main__":
    main()