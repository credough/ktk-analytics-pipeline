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
  python fb_insights_etl.py --start 2026-01-01          # backfill to yesterday
  python fb_insights_etl.py                             # daily run: last 3 days
  python fb_insights_etl.py --start 2026-07-07 --end 2026-07-15 --dry-run

Environment variables (never hardcode these or commit them):
  PAGE_ID, FB_SYSTEM_TOKEN, SUPABASE_URL, SUPABASE_KEY
Requires: pip install requests supabase tzdata
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

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
        sys.exit(f"Graph API error on '{path}': {message}")
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

    page_id = os.environ["PAGE_ID"]
    page_token = get_page_token(page_id, os.environ["FB_SYSTEM_TOKEN"])

    records = []
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

    from supabase import create_client
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    for i in range(0, len(records), 500):
        batch = records[i:i + 500]
        supabase.table("fact_daily_metrics").upsert(
            batch, on_conflict="date,platform_id,metric_name"
        ).execute()
        print(f"Upserted batch {i // 500 + 1}: {len(batch)} rows")
    print(f"Done: {len(records)} rows.")


if __name__ == "__main__":
    main()