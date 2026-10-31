"""Supabase client construction."""

from supabase import Client, create_client

from ktk_pipeline.config.settings import SupabaseSettings


def get_client(settings: SupabaseSettings) -> Client:
    """Create a Supabase client from explicit settings."""
    return create_client(settings.url, settings.key)
