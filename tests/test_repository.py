import pytest

from ktk_pipeline.db.repository import (
    CONFLICT_COLUMNS,
    TABLE_NAME,
    upsert_daily_metrics,
)


class StubClient:
    def __init__(self):
        self.calls = []
        self._table_name = None

    def table(self, name):
        self._table_name = name
        return self

    def upsert(self, records, *, on_conflict):
        self.calls.append((self._table_name, records, on_conflict))
        return self

    def execute(self):
        return None


def make_records(count):
    return [
        {
            "date": f"2026-01-{index % 28 + 1:02}",
            "platform_id": "fb",
            "metric_name": "views",
            "value": float(index),
        }
        for index in range(count)
    ]


def test_upserts_in_batches_and_reports_batch_sizes():
    client = StubClient()
    callbacks = []

    upsert_daily_metrics(
        client,
        make_records(1200),
        batch_size=500,
        on_batch=lambda number, size: callbacks.append((number, size)),
    )

    assert [len(call[1]) for call in client.calls] == [500, 500, 200]
    assert callbacks == [(1, 500), (2, 500), (3, 200)]
    assert all(
        table == TABLE_NAME and conflict == CONFLICT_COLUMNS
        for table, _, conflict in client.calls
    )


def test_rejects_nonpositive_batch_size():
    with pytest.raises(ValueError, match="batch_size"):
        upsert_daily_metrics(StubClient(), [], batch_size=0)


def test_empty_records_make_no_client_calls():
    client = StubClient()

    upsert_daily_metrics(client, [])

    assert client.calls == []
