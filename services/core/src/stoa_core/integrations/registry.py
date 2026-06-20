"""
File: services/core/src/stoa_core/integrations/registry.py
Layer: Core Integration Connectors
Purpose: Implements registry behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

from stoa_core.integrations.base import BaseConnector, ProviderInfo

_REGISTRY: dict[str, type[BaseConnector]] = {}


def register_connector(cls: type[BaseConnector]) -> type[BaseConnector]:
    """Handles register connector logic for the surrounding Stoa workflow.

    Returns:
        type[BaseConnector]: Result produced for the caller.
    """
    _REGISTRY[cls.provider] = cls
    return cls


def get_connector(provider: str) -> type[BaseConnector]:
    """Handles get connector logic for the surrounding Stoa workflow.

    Args:
        provider (str): Input value used by this workflow step.

    Returns:
        type[BaseConnector]: Result produced for the caller.
    """
    if provider not in _REGISTRY:
        raise ValueError(f"Unknown integration provider: {provider}")
    return _REGISTRY[provider]


def list_providers() -> list[ProviderInfo]:
    """Handles list providers logic for the surrounding Stoa workflow.

    Returns:
        list[ProviderInfo]: Result produced for the caller.
    """
    return [cls.provider_info() for cls in _REGISTRY.values()]


# Import connectors to register them (side-effect: @register_connector)
from stoa_core.integrations import (  # noqa: E402, F401, I001
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
