"""Connector protocol and sync result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncResult:
    records_fetched: int = 0
    records_written: int = 0
    cursor: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class ProviderInfo:
    id: str
    name: str
    auth_type: str  # oauth | api_key | upload
    description: str
    scopes: list[str] = field(default_factory=list)


class BaseConnector(ABC):
    provider: str

    @classmethod
    @abstractmethod
    def provider_info(cls) -> ProviderInfo:
        ...

    @classmethod
    def oauth_authorize_url(cls, state: str, redirect_uri: str) -> str | None:
        return None

    @classmethod
    def exchange_oauth_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        raise NotImplementedError(f"{cls.provider} does not support OAuth code exchange")

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Non-OAuth connect (API keys, etc.). Returns credentials + provider_metadata."""
        return credentials

    @classmethod
    @abstractmethod
    def sync(
        cls,
        org_id: str,
        connection: dict[str, Any],
        *,
        credentials: dict[str, Any],
        cursor: dict[str, Any],
        full_backfill: bool = False,
    ) -> SyncResult:
        ...
