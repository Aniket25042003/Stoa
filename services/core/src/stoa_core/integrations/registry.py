"""Provider registry."""

from __future__ import annotations

from typing import Type

from stoa_core.integrations.base import BaseConnector, ProviderInfo

_REGISTRY: dict[str, Type[BaseConnector]] = {}


def register_connector(cls: Type[BaseConnector]) -> Type[BaseConnector]:
    _REGISTRY[cls.provider] = cls
    return cls


def get_connector(provider: str) -> Type[BaseConnector]:
    if provider not in _REGISTRY:
        raise ValueError(f"Unknown integration provider: {provider}")
    return _REGISTRY[provider]


def list_providers() -> list[ProviderInfo]:
    return [cls.provider_info() for cls in _REGISTRY.values()]


# Import connectors to register them (side-effect: @register_connector)
from stoa_core.integrations import (  # noqa: E402, F401
    csv_structured as _csv_structured,
    ga4 as _ga4,
    gong as _gong,
    google_drive as _google_drive,
    hubspot as _hubspot,
    intercom as _intercom,
    jira as _jira,
    notion as _notion,
    posthog as _posthog,
    reddit as _reddit,
    reviews as _reviews,
    salesforce as _salesforce,
    slack as _slack,
    zendesk as _zendesk,
)
