import sys
from datetime import date, timedelta
from types import SimpleNamespace

from ktk_pipeline.jobs import fb_insights


def test_dry_run_fetches_metrics_without_creating_supabase_client(
    monkeypatch, capsys
):
    monkeypatch.setenv("PAGE_ID", "fake-page-id")
    monkeypatch.setenv("FB_SYSTEM_TOKEN", "fake-system-token")
    monkeypatch.setitem(
        sys.modules,
        "dotenv",
        SimpleNamespace(load_dotenv=lambda: None),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fb_insights",
            "--start",
            "2026-07-07",
            "--end",
            "2026-07-14",
            "--dry-run",
        ],
    )

    def fake_graph_get(path, token, params=None):
        if path == "fake-page-id":
            return {"access_token": "fake-page-token"}
        start = date.fromisoformat(params["since"])
        values = [
            {
                "end_time": (
                    (start + timedelta(days=offset + 1)).strftime(
                        "%Y-%m-%dT07:00:00+0000"
                    )
                ),
                "value": offset + 1,
            }
            for offset in range(8)
        ]
        return {"data": [{"values": values}]}

    def unexpected_client(*args, **kwargs):
        raise AssertionError("get_client must not be called in dry-run mode")

    monkeypatch.setattr(fb_insights, "graph_get", fake_graph_get)
    monkeypatch.setattr(fb_insights, "get_client", unexpected_client)

    fb_insights.main()
    output = capsys.readouterr().out

    assert "Range: 2026-07-07 -> 2026-07-14" in output
    for metric in ("views", "viewers", "visits", "follows"):
        assert f"{metric}: 8 days" in output
    assert "Dry run:" in output
