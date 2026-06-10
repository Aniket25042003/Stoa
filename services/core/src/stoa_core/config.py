"""Central configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    # Observability
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "stoa-intelligence"

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.stoa_env.strip().lower() in {"development", "dev", "local"}

    @property
    def is_production(self) -> bool:
        return self.stoa_env.strip().lower() in {"production", "prod"}

    @property
    def redis_require_tls_effective(self) -> bool:
        if self.redis_require_tls is not None:
            return self.redis_require_tls
        return self.is_production

    @property
    def resolved_vertex_project(self) -> str | None:
        return self.vertex_project or self.gtm_vertex_project

    @property
    def resolved_vertex_location(self) -> str:
        return self.gtm_vertex_location or self.vertex_location

    @property
    def resolved_vertex_model(self) -> str:
        return self.gtm_vertex_model or self.vertex_model

    @property
    def resolved_vertex_model_fast(self) -> str:
        return self.gtm_vertex_model_fast or self.vertex_model_fast


@lru_cache
def get_settings() -> Settings:
    return Settings()
