from datetime import date

from ktk_pipeline.jobs.fb_insights import to_csv_date


def test_to_csv_date_uses_previous_los_angeles_date():
    assert to_csv_date("2026-07-08T07:00:00+0000") == date(2026, 7, 7)
    assert to_csv_date("2026-01-15T08:00:00+0000") == date(2026, 1, 14)
