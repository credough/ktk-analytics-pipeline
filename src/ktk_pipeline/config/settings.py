"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass, field


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing environment variable {name}. See .env.example.")
    return value


@dataclass(frozen=True)
class SupabaseSettings:
    """Supabase connection settings."""

    url: str
    key: str = field(repr=False)

    @classmethod
    def from_env(cls) -> "SupabaseSettings":
        return cls(
            url=_required_env("SUPABASE_URL"),
            key=_required_env("SUPABASE_KEY"),
        )


@dataclass(frozen=True)
class MetaSettings:
    """Meta Graph API settings."""

    page_id: str
    system_token: str = field(repr=False)

    @classmethod
    def from_env(cls) -> "MetaSettings":
        return cls(
            page_id=_required_env("PAGE_ID"),
            system_token=_required_env("FB_SYSTEM_TOKEN"),
        )
