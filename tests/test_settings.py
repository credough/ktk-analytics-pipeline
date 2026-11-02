import pytest

from ktk_pipeline.config.settings import MetaSettings, SupabaseSettings


def test_missing_setting_names_only_the_missing_variable(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_KEY", "fake-supabase-key")
    monkeypatch.setenv("UNRELATED_SECRET", "fake-unrelated-secret")

    with pytest.raises(ValueError) as error:
        SupabaseSettings.from_env()

    assert "SUPABASE_URL" in str(error.value)
    assert "fake-supabase-key" not in str(error.value)
    assert "fake-unrelated-secret" not in str(error.value)


def test_settings_repr_does_not_include_secrets():
    supabase = SupabaseSettings(url="https://fake.supabase.co", key="fake-key")
    meta = MetaSettings(page_id="fake-page-id", system_token="fake-token")

    assert "fake-key" not in repr(supabase)
    assert "fake-token" not in repr(meta)


def test_supabase_settings_do_not_require_meta_variables(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "fake-key")
    monkeypatch.delenv("PAGE_ID", raising=False)
    monkeypatch.delenv("FB_SYSTEM_TOKEN", raising=False)

    settings = SupabaseSettings.from_env()

    assert settings.url == "https://fake.supabase.co"
    assert settings.key == "fake-key"
