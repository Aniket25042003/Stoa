"""
File: services/core/src/stoa_core/config.py
Layer: Application Source
Purpose: Implements config behavior for the application source.
Dependencies: Supabase, Celery, Redis, Pydantic
"""


from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Manage Settings behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # deployment — set explicitly to development or production
    stoa_env: str = ""
    internal_proxy_secret: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    storage_bucket: str = "intelligence-documents"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    redis_require_tls: bool | None = None
    redis_ssl_verify: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000"

    # LLM
    llm_provider: str = "vertex"
    llm_auto_failover: bool = True
    vertex_model: str = "gemini-2.5-pro"
    vertex_model_fast: str = "gemini-2.5-flash"
    vertex_model_pro: str = "gemini-2.5-pro"
    vertex_project: str | None = Field(default=None, validation_alias="VERTEX_PROJECT")
    gtm_vertex_project: str | None = Field(default=None, validation_alias="GTM_VERTEX_PROJECT")
    vertex_location: str = "us-central1"
    gtm_vertex_location: str | None = Field(default=None, validation_alias="GTM_VERTEX_LOCATION")
    gtm_vertex_model: str | None = Field(default=None, validation_alias="GTM_VERTEX_MODEL")
    gtm_vertex_model_fast: str | None = Field(
        default=None, validation_alias="GTM_VERTEX_MODEL_FAST"
    )
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_model_fast: str | None = None
    openai_model_pro: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None
    llm_temperature: float = 0.25
    llm_timeout_seconds: float = 60.0
    embed_model: str = "gemini-embedding-001"
    embed_dimensions: int = 3072
    embed_task_doc: str = "RETRIEVAL_DOCUMENT"
    embed_task_query: str = "RETRIEVAL_QUERY"
    embed_batch_size: int = 32

    # Retrieval / RAG
    retrieval_candidate_k: int = 40
    retrieval_final_k: int = 12
    retrieval_token_budget: int = 2000
    retrieval_rrf_k: int = 60
    retrieval_min_similarity: float = 0.0
    cohere_api_key: str | None = None
    cohere_rerank_model: str = "rerank-v3.5"
    kb_cache_ttl_seconds: int = 3600
    kb_query_cache_ttl_seconds: int = 1800
    kb_rewrite_cache_ttl_seconds: int = 3600
    kb_answer_cache_ttl_seconds: int = 1800

    # Agent tools / evidence
    agent_evidence_conversation_ttl_seconds: int = 259200
    agent_evidence_max_persist_per_turn: int = 8
    agent_evidence_max_snippet_chars: int = 2000
    agent_evidence_freshness_hours: int = 24
    agent_live_search_per_org_per_hour: int = 20
    agent_refresh_per_org_per_hour: int = 5
    agent_web_search_per_org_per_day: int = 20

    # Chunking
    chunk_target_tokens: int = 600
    chunk_max_tokens: int = 800
    chunk_overlap_tokens: int = 80

    # Limits
    max_upload_bytes: int = 10 * 1024 * 1024
    max_documents_per_org: int = 500
    rate_limit_per_minute: int = 60
    app_base_url: str = "http://localhost:3000"
    invite_token_pepper: str = ""

    # Content generation (Vertex AI Imagen + Veo)
    content_image_model: str = "imagen-4.0-fast"
    content_image_model_fast: str = "imagen-4.0-fast"
    content_video_model: str = "veo-3.1-lite"
    content_video_model_fast: str = "veo-3.1-lite"
    content_video_timeout_seconds: int = 300
    content_max_images_per_request: int = 4
    content_storage_bucket: str = "content-assets"

    # Integrations — credentials encryption (Fernet key, base64)
    integration_credentials_key: str = ""
    api_base_url: str = "http://localhost:8000"

    # HubSpot OAuth
    hubspot_client_id: str = ""
    hubspot_client_secret: str = ""

    # Gong OAuth
    gong_client_id: str = ""
    gong_client_secret: str = ""

    # Salesforce OAuth
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""

    # Zendesk OAuth
    zendesk_client_id: str = ""
    zendesk_client_secret: str = ""
    zendesk_subdomain: str = ""

    # Reviews + Reddit (Apify)
    apify_api_token: str = ""

    # Google OAuth (GA4 + Google Drive)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Slack OAuth
    slack_client_id: str = ""
    slack_client_secret: str = ""

    # Web research / enrichment
    tavily_api_key: str = ""
    jina_api_key: str = ""
    serpapi_api_key: str = ""
    enrichment_max_urls_per_job: int = 8
    enrichment_timeout_seconds: float = 25.0
    enrichment_max_jobs_per_org_per_day: int = 20
    disable_external_research: bool = False

    # Reddit
    reddit_access_token: str = ""
    reddit_user_agent: str = "stoa-intelligence/1.0"

    # Observability
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "stoa-intelligence"

    @property
    def broker_url(self) -> str:
        """Handles broker url logic for the surrounding Stoa workflow.

        Returns:
            str: Result produced for the caller.
        """
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        """Handles result backend logic for the surrounding Stoa workflow.

        Returns:
            str: Result produced for the caller.
        """
        return self.celery_result_backend or self.redis_url

    @property
    def cors_origin_list(self) -> list[str]:
        """Handles cors origin list logic for the surrounding Stoa workflow.

        Returns:
            list[str]: Result produced for the caller.
        """
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        """Handles is development logic for the surrounding Stoa workflow.

        Returns:
            bool: Result produced for the caller.
        """
        env = self.stoa_env.strip().lower()
        if env in {"development", "dev", "local"}:
            return True
        if env in {"production", "prod", "staging"}:
            return False
        # Unset STOA_ENV: treat localhost Redis as local dev; remote brokers stay strict.
        host = (urlparse(self.broker_url).hostname or "").lower()
        return host in {"localhost", "127.0.0.1", "::1"}

    @property
    def is_production(self) -> bool:
        """Handles is production logic for the surrounding Stoa workflow.

        Returns:
            bool: Result produced for the caller.
        """
        return self.stoa_env.strip().lower() in {"production", "prod"}

    @property
    def redis_require_tls_effective(self) -> bool:
        """Handles redis require tls effective logic for the surrounding Stoa workflow.

        Returns:
            bool: Result produced for the caller.
        """
        if self.redis_require_tls is not None:
            return self.redis_require_tls
        return self.is_production

    @property
    def resolved_vertex_project(self) -> str | None:
        """Handles resolved vertex project logic for the surrounding Stoa workflow.

        Returns:
            str | None: Result produced for the caller.
        """
        return self.vertex_project or self.gtm_vertex_project

    @property
    def resolved_vertex_location(self) -> str:
        """Handles resolved vertex location logic for the surrounding Stoa workflow.

        Returns:
            str: Result produced for the caller.
        """
        return self.gtm_vertex_location or self.vertex_location

    @property
    def resolved_vertex_model(self) -> str:
        """Handles resolved vertex model logic for the surrounding Stoa workflow.

        Returns:
            str: Result produced for the caller.
        """
        return self.gtm_vertex_model or self.vertex_model

    @property
    def resolved_vertex_model_fast(self) -> str:
        """Handles resolved vertex model fast logic for the surrounding Stoa workflow.

        Returns:
            str: Result produced for the caller.
        """
        return self.gtm_vertex_model_fast or self.vertex_model_fast


@lru_cache
def get_settings() -> Settings:
    """Handles get settings logic for the surrounding Stoa workflow.

    Returns:
        Settings: Result produced for the caller.
    """
    return Settings()
