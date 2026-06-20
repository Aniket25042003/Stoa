"""
File: services/core/src/stoa_core/integrations/base.py
Layer: Core Integration Connectors
Purpose: Implements base behavior for the core integration connectors.
Dependencies: standard library / local modules
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncResult:
    """Manage SyncResult behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    records_fetched: int = 0
    records_written: int = 0
    cursor: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class ProviderInfo:
    """Manage ProviderInfo behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    id: str
    name: str
    auth_type: str  # oauth | api_key | upload
    description: str
    scopes: list[str] = field(default_factory=list)


class BaseConnector(ABC):
    """Manage BaseConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider: str

    @classmethod
    @abstractmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        ...

    @classmethod
    def oauth_authorize_url(cls, state: str, redirect_uri: str) -> str | None:
        """Handles oauth authorize url logic for the surrounding Stoa workflow.

        Args:
            state (str): Input value used by this workflow step.
            redirect_uri (str): Input value used by this workflow step.

        Returns:
            str | None: Result produced for the caller.
        """
        return None

    @classmethod
    def exchange_oauth_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        """Handles exchange oauth code logic for the surrounding Stoa workflow.

        Args:
            code (str): Input value used by this workflow step.
            redirect_uri (str): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
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
        """Handles sync logic for the surrounding Stoa workflow.

        Args:
            org_id (str): Input value used by this workflow step.
            connection (dict[str, Any]): Input value used by this workflow step.
            credentials (dict[str, Any]): Input value used by this workflow step.
            cursor (dict[str, Any]): Input value used by this workflow step.
            full_backfill (bool): Input value used by this workflow step.

        Returns:
            SyncResult: Result produced for the caller.
        """
        ...
