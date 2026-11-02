"""Database operations for daily metrics."""

from collections.abc import Callable
from typing import TypedDict

from supabase import Client

TABLE_NAME = "fact_daily_metrics"
CONFLICT_COLUMNS = "date,platform_id,metric_name"


class DailyMetric(TypedDict):
    """One daily metric row, with its date formatted as YYYY-MM-DD."""

    date: str
    platform_id: str
    metric_name: str
    value: float


def upsert_daily_metrics(
    client: Client,
    records: list[DailyMetric],
    batch_size: int = 500,
    *,
    on_batch: Callable[[int, int], None] | None = None,
) -> None:
    """Upsert daily metrics, notifying after each successful batch if requested."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")

    for batch_number, start in enumerate(
        range(0, len(records), batch_size),
        start=1,
    ):
        batch = records[start:start + batch_size]
        client.table(TABLE_NAME).upsert(
            batch,
            on_conflict=CONFLICT_COLUMNS,
        ).execute()
        if on_batch is not None:
            on_batch(batch_number, len(batch))
