# KadaKareer Social Media Analytics Pipeline

Loads daily social media metrics exported from Meta Business Suite (Facebook & Instagram) into a Supabase (Postgres) data warehouse, which powers a Looker Studio dashboard.

## What it does

Meta Business Suite exports are UTF-16 encoded CSVs with a few quirks (a `sep=,` directive line, a metric title row, then a `Date, Primary` header). This script:

1. Reads each CSV export (Views, Viewers/Reach, Visits, Follows, Link clicks, Content interactions)
2. Cleans and decodes them
3. Upserts the data into a single long-format table (`fact_daily_metrics`) in Supabase, tagged by platform and metric name

## Why a long-format schema?

Instead of one table per platform, everything lands in one table shaped like:

```
date | platform_id | metric_name | value
```

This means adding a new platform (Instagram, Brevo email, etc.) later is just new rows — no schema changes needed.

## Usage

```bash
pip install supabase

export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-service-role-key"

python load_metrics.py --platform fb --folder "/path/to/FB/exports"
python load_metrics.py --platform ig --folder "/path/to/IG/exports"
```

## Expected file names per folder

| File | metric_name |
|---|---|
| Views.csv | views |
| Viewers.csv (FB only) | viewers |
| Reach.csv (IG only) | reach |
| Link_clicks.csv | link_clicks |
| Visits.csv | visits |
| Follows.csv | follows |
| Interactions.csv | content_interactions |

## Next steps

- [ ] Replace manual CSV export with Meta Graph API for automated ingestion
- [ ] Add Brevo API integration for email marketing metrics (same `fact_daily_metrics` table, `platform_id = 'brevo'`)
- [ ] Schedule as a recurring job (cron / cloud function) once API-based

## Author
  Aaron Celindro — Data & Impact, KadaKareer