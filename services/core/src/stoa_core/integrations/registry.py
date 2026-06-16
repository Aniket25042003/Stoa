"""Provider registry."""

from __future__ import annotations

from stoa_core.integrations.base import BaseConnector, ProviderInfo

_REGISTRY: dict[str, type[BaseConnector]] = {}


def register_connector(cls: type[BaseConnector]) -> type[BaseConnector]:
    _REGISTRY[cls.provider] = cls
    return cls


def get_connector(provider: str) -> type[BaseConnector]:
    if provider not in _REGISTRY:
        raise ValueError(f"Unknown integration provider: {provider}")
    return _REGISTRY[provider]


def list_providers() -> list[ProviderInfo]:
    return [cls.provider_info() for cls in _REGISTRY.values()]


# Import connectors to register them (side-effect: @register_connector)
from stoa_core.integrations import (  # noqa: E402, F401
    csv_structured as _csv_structured,
)
