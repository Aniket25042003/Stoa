"""
File: services/core/src/stoa_core/integrations/scope.py
Layer: Core Integration Connectors
Purpose: Shared helpers for integration resource scope configuration.
"""

from __future__ import annotations

from typing import Any

# Providers that require scope before first sync.
REQUIRED_SCOPE_PROVIDERS = frozenset(
    {
        "slack",
        "ga4",
        "google_drive",
        "notion",
        "posthog",
        "jira",
        "hubspot",
        "salesforce",
        "zendesk",
        "intercom",
        "gong",
        "reviews",
        "reddit",
    }
)

# Keys written by the scope editor into provider_metadata.
SCOPE_KEYS_BY_PROVIDER: dict[str, list[str]] = {
    "slack": ["channel_ids"],
    "ga4": ["property_id"],
    "google_drive": ["file_ids"],
    "notion": ["page_ids", "database_ids"],
    "posthog": ["project_id", "host"],
    "jira": ["project_keys", "jql"],
    "hubspot": ["object_types", "pipeline_ids"],
    "salesforce": ["objects", "record_type_ids"],
    "zendesk": ["view_ids", "sync_all_tickets"],
    "intercom": ["tag_ids", "team_ids"],
    "gong": ["workspace_ids", "from_date"],
    "reviews": ["product_query", "platforms", "max_results"],
    "reddit": ["search_query", "subreddits", "max_results"],
}


def scope_configured(provider: str, metadata: dict[str, Any] | None) -> bool:
    meta = metadata or {}
    if meta.get("scope_configured") is True:
        return True
    if provider not in REQUIRED_SCOPE_PROVIDERS:
        return True
    return not validate_scope(provider, meta)


def validate_scope(provider: str, metadata: dict[str, Any] | None) -> list[str]:
    """Return user-facing error strings when required scope is missing."""
    meta = metadata or {}
    errors: list[str] = []

    if provider == "slack":
        if not meta.get("channel_ids"):
            errors.append("Select at least one Slack channel")
    elif provider == "ga4":
        if not meta.get("property_id"):
            errors.append("Select a GA4 property")
    elif provider == "google_drive":
        if not meta.get("file_ids"):
            errors.append("Select at least one Google Drive file")
    elif provider == "notion":
        if not meta.get("page_ids") and not meta.get("database_ids"):
            errors.append("Select at least one Notion page or database")
    elif provider == "posthog":
        if not meta.get("project_id"):
            errors.append("Select a PostHog project")
    elif provider == "jira":
        if not meta.get("project_keys") and not meta.get("jql"):
            errors.append("Select at least one Jira project")
        elif meta.get("jql"):
            try:
                assert_safe_jira_jql(str(meta["jql"]), project_keys=meta.get("project_keys"))
            except ValueError as exc:
                errors.append(str(exc))
    elif provider == "hubspot":
        if not meta.get("object_types"):
            errors.append("Select at least one HubSpot object type")
    elif provider == "salesforce":
        if not meta.get("objects"):
            errors.append("Select at least one Salesforce object type")
    elif provider == "zendesk":
        if not meta.get("sync_all_tickets") and not meta.get("view_ids"):
            errors.append("Select Zendesk views or choose all tickets")
    elif provider == "intercom":
        if not meta.get("tag_ids") and not meta.get("team_ids"):
            errors.append("Select at least one Intercom tag or team")
    elif provider == "gong":
        if not meta.get("workspace_ids") and not meta.get("from_date"):
            errors.append("Select Gong workspaces or a start date")
    elif provider == "reviews":
        if not meta.get("product_query"):
            errors.append("Enter a product URL or name for reviews")
    elif provider == "reddit":
        if not meta.get("search_query"):
            errors.append("Enter a Reddit search query")

    return errors


def merge_scope_patch(provider: str, metadata: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(metadata or {})
    allowed = set(SCOPE_KEYS_BY_PROVIDER.get(provider, [])) | {"scope_configured", "scope_labels"}
    for key, value in patch.items():
        if key in allowed:
            merged[key] = value
    if provider == "zendesk" and patch.get("view_ids"):
        view_ids = patch.get("view_ids") or []
        if "__all__" in view_ids:
            merged["sync_all_tickets"] = True
            merged["view_ids"] = []
    if patch.get("scope_configured") is True:
        remaining = validate_scope(provider, merged)
        if remaining:
            raise ValueError(remaining[0])
        merged["scope_configured"] = True
    elif provider == "jira" and patch.get("jql"):
        assert_safe_jira_jql(str(patch["jql"]), project_keys=merged.get("project_keys"))
    return merged


def assert_safe_jira_jql(jql: str, *, project_keys: list[str] | str | None = None) -> str:
    """Restrict custom JQL to project-scoped queries."""
    cleaned = (jql or "").strip()
    if not cleaned:
        raise ValueError("JQL query is required")
    if len(cleaned) > 1500:
        raise ValueError("JQL query is too long")
    lowered = cleaned.lower()
    keys: list[str] = []
    if isinstance(project_keys, list):
        keys = [str(k) for k in project_keys if k]
    elif isinstance(project_keys, str) and project_keys.strip():
        keys = [project_keys.strip()]
    if keys:
        if not any(k.lower() in lowered for k in keys):
            raise ValueError("JQL must filter to selected Jira projects")
    elif "project in" not in lowered and "project =" not in lowered:
        raise ValueError("JQL must include a project filter")
    return cleaned


def scope_summary(provider: str, metadata: dict[str, Any] | None) -> str | None:
    meta = metadata or {}
    labels = meta.get("scope_labels") or {}
    if provider == "slack":
        n = len(meta.get("channel_ids") or [])
        return f"{n} channel{'s' if n != 1 else ''}" if n else None
    if provider == "ga4":
        pid = meta.get("property_id")
        return labels.get(str(pid)) or (f"Property {pid}" if pid else None)
    if provider == "google_drive":
        n = len(meta.get("file_ids") or [])
        return f"{n} file{'s' if n != 1 else ''}" if n else None
    if provider == "notion":
        pages = len(meta.get("page_ids") or [])
        dbs = len(meta.get("database_ids") or [])
        if pages or dbs:
            return f"{pages} pages, {dbs} databases"
        return None
    if provider == "posthog":
        pid = meta.get("project_id")
        return labels.get(str(pid)) or (f"Project {pid}" if pid else None)
    if provider == "jira":
        n = len(meta.get("project_keys") or [])
        return f"{n} project{'s' if n != 1 else ''}" if n else None
    if provider == "hubspot":
        types = meta.get("object_types") or []
        return ", ".join(types) if types else None
    if provider == "salesforce":
        objs = meta.get("objects") or []
        return ", ".join(objs) if objs else None
    if provider == "zendesk":
        if meta.get("sync_all_tickets"):
            return "All tickets"
        n = len(meta.get("view_ids") or [])
        return f"{n} view{'s' if n != 1 else ''}" if n else None
    if provider == "intercom":
        tags = len(meta.get("tag_ids") or [])
        teams = len(meta.get("team_ids") or [])
        if tags or teams:
            return f"{tags} tags, {teams} teams"
        return None
    if provider == "gong":
        n = len(meta.get("workspace_ids") or [])
        return f"{n} workspace{'s' if n != 1 else ''}" if n else None
    if provider == "reviews":
        return meta.get("product_query") or None
    if provider == "reddit":
        q = meta.get("search_query")
        subs = meta.get("subreddits") or []
        if q and subs:
            return f'"{q}" in {len(subs)} subreddit(s)'
        return q or None
    return None


def _list_ids(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v) for v in value if v is not None and str(v).strip()}
    if isinstance(value, str) and value.strip():
        return {value.strip()}
    return set()


def removed_uri_prefixes(provider: str, old_meta: dict[str, Any], new_meta: dict[str, Any]) -> list[str]:
    """URI prefixes for knowledge items that fall outside the new scope."""
    old = old_meta or {}
    new = new_meta or {}
    prefixes: list[str] = []

    if provider == "slack":
        for cid in _list_ids(old.get("channel_ids")) - _list_ids(new.get("channel_ids")):
            prefixes.append(f"slack:channel:{cid}")
    elif provider == "ga4":
        old_pid = old.get("property_id")
        new_pid = new.get("property_id")
        if old_pid and old_pid != new_pid:
            prefixes.append(f"ga4:summary:{old_pid}")
    elif provider == "google_drive":
        for fid in _list_ids(old.get("file_ids")) - _list_ids(new.get("file_ids")):
            prefixes.append(f"google_drive:file:{fid}")
    elif provider == "notion":
        for pid in _list_ids(old.get("page_ids")) - _list_ids(new.get("page_ids")):
            prefixes.append(f"notion:page:{pid}")
        for db in _list_ids(old.get("database_ids")) - _list_ids(new.get("database_ids")):
            prefixes.append(f"notion:database:{db}")
    elif provider == "posthog":
        old_pid = old.get("project_id")
        new_pid = new.get("project_id")
        if old_pid and old_pid != new_pid:
            prefixes.append(f"posthog:summary:{old_pid}")
    elif provider == "jira":
        if _list_ids(old.get("project_keys")) != _list_ids(new.get("project_keys")):
            prefixes.append("jira:")
    elif provider == "hubspot":
        entity_map = {"companies": "company", "contacts": "contact", "deals": "deal"}
        removed_types = _list_ids(old.get("object_types")) - _list_ids(new.get("object_types"))
        for obj in removed_types:
            entity = entity_map.get(obj, obj.rstrip("s"))
            prefixes.append(f"hubspot:{entity}:")
    elif provider == "salesforce":
        entity_map = {"Account": "account", "Contact": "contact", "Opportunity": "deal"}
        removed = _list_ids(old.get("objects")) - _list_ids(new.get("objects"))
        for obj in removed:
            entity = entity_map.get(obj, obj.lower())
            prefixes.append(f"salesforce:{entity}:")
    elif provider == "zendesk":
        if old.get("sync_all_tickets") and not new.get("sync_all_tickets"):
            prefixes.append("zendesk:")
        elif _list_ids(old.get("view_ids")) != _list_ids(new.get("view_ids")):
            prefixes.append("zendesk:")
    elif provider == "intercom":
        if _list_ids(old.get("tag_ids")) != _list_ids(new.get("tag_ids")):
            prefixes.append("intercom:")
        if _list_ids(old.get("team_ids")) != _list_ids(new.get("team_ids")):
            prefixes.append("intercom:")
    elif provider == "gong":
        if _list_ids(old.get("workspace_ids")) != _list_ids(new.get("workspace_ids")):
            prefixes.append("gong:")
    elif provider == "reviews":
        if old.get("product_query") != new.get("product_query"):
            prefixes.append("reviews:")
    elif provider == "reddit":
        if old.get("search_query") != new.get("search_query"):
            prefixes.append("reddit:")
        elif _list_ids(old.get("subreddits")) != _list_ids(new.get("subreddits")):
            prefixes.append("reddit:")

    return list(dict.fromkeys(prefixes))


def purge_knowledge_by_uri_prefixes(org_id: str, prefixes: list[str]) -> int:
    """Delete knowledge items (and chunks) whose uri starts with any prefix."""
    if not prefixes:
        return 0
    from stoa_core.db.supabase import get_supabase_admin
    from stoa_core.rag.cache import bump_kb_version

    sb = get_supabase_admin()
    deleted = 0
    for prefix in prefixes:
        res = (
            sb.table("knowledge_items")
            .select("id")
            .eq("org_id", org_id)
            .like("uri", f"{prefix}%")
            .execute()
        )
        for row in res.data or []:
            item_id = row["id"]
            sb.table("knowledge_chunks").delete().eq("item_id", item_id).execute()
            sb.table("knowledge_items").delete().eq("id", item_id).execute()
            deleted += 1
    if deleted:
        bump_kb_version(org_id)
    return deleted
