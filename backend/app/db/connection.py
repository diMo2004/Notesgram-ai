from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.config import Settings


@dataclass(slots=True)
class DatabaseConnectionSettings:
    database_url: str


def build_database_connection_settings(settings: Settings) -> DatabaseConnectionSettings:
    return DatabaseConnectionSettings(database_url=str(settings.database_url))