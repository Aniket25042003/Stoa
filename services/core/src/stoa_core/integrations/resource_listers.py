"""
File: services/core/src/stoa_core/integrations/resource_listers.py
Layer: Core Integration Connectors
Purpose: Discover selectable resources for integration scope pickers.
"""

from __future__ import annotations

from typing import Any

import httpx

from stoa_core.integrations.base import ResourceListResult, ResourceOption

HUBSPOT_OBJECT_TYPES = [
    ("companies", "Companies"),
    ("contacts", "Contacts"),
    ("deals", "Deals"),
]


def list_slack_channels(
    credentials: dict[str, Any],
    *,
    cursor: str | None = None,
    query: str | None = None,
) -> ResourceListResult:
    headers = {"Authorization": f"Bearer {credentials['access_token']}"}
    params: dict[str, Any] = {
        "types": "public_channel,private_channel",
        "exclude_archived": "true",
        "limit": 200,
    }
    if cursor:
        params["cursor"] = cursor
    with httpx.Client(timeout=30) as client:
        res = client.get("https://slack.com/api/conversations.list", headers=headers, params=params)
        body = res.json()
    if not body.get("ok"):
        return ResourceListResult()
    q = (query or "").lower()
    resources = []
    for ch in body.get("channels") or []:
        name = ch.get("name") or ch.get("id")
        if q and q not in str(name).lower():
            continue
        resources.append(
            ResourceOption(
                id=ch["id"],
                label=f"#{name}",
                kind="channel",
                description=(ch.get("purpose") or {}).get("value"),
            )
        )
    return ResourceListResult(
        resources=resources,
        next_cursor=(body.get("response_metadata") or {}).get("next_cursor"),
    )


def list_ga4_properties(credentials: dict[str, Any]) -> ResourceListResult:
    headers = {"Authorization": f"Bearer {credentials['access_token']}"}
    resources: list[ResourceOption] = []
    page_token = None
    with httpx.Client(timeout=60) as client:
        while True:
            params = {"pageSize": 200}
            if page_token:
                params["pageToken"] = page_token
            res = client.get(
                "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
                headers=headers,
                params=params,
            )
            if res.status_code >= 400:
                break
            body = res.json()
            for account in body.get("accountSummaries") or []:
                account_name = account.get("displayName") or account.get("account", "")
                for prop in account.get("propertySummaries") or []:
                    prop_name = prop.get("displayName") or prop.get("property", "")
                    prop_id = str(prop.get("property", "")).split("/")[-1]
                    resources.append(
                        ResourceOption(
                            id=prop_id,
                            label=prop_name,
                            kind="property",
                            description=account_name,
                            meta={"property_resource": prop.get("property")},
                        )
                    )
            page_token = body.get("nextPageToken")
            if not page_token:
                break
    return ResourceListResult(resources=resources)


def list_google_drive_files(
    credentials: dict[str, Any],
    *,
    cursor: str | None = None,
    query: str | None = None,
) -> ResourceListResult:
    headers = {"Authorization": f"Bearer {credentials['access_token']}"}
    q_parts = ["mimeType='application/vnd.google-apps.document'", "trashed=false"]
    if query:
        q_parts.append(f"name contains '{query.replace(chr(39), '')}'")
    params: dict[str, Any] = {
        "q": " and ".join(q_parts),
        "pageSize": 50,
        "fields": "nextPageToken,files(id,name,modifiedTime)",
    }
    if cursor:
        params["pageToken"] = cursor
    with httpx.Client(timeout=60) as client:
        res = client.get("https://www.googleapis.com/drive/v3/files", headers=headers, params=params)
        if res.status_code >= 400:
            return ResourceListResult()
        body = res.json()
    resources = [
        ResourceOption(id=f["id"], label=f.get("name") or f["id"], kind="file")
        for f in body.get("files") or []
        if f.get("id")
    ]
    return ResourceListResult(resources=resources, next_cursor=body.get("nextPageToken"))


def list_notion_resources(
    credentials: dict[str, Any],
    *,
    cursor: str | None = None,
    query: str | None = None,
) -> ResourceListResult:
    headers = {
        "Authorization": f"Bearer {credentials['access_token']}",
        "Notion-Version": "2022-06-28",
    }
    payload: dict[str, Any] = {"page_size": 50}
    if cursor:
        payload["start_cursor"] = cursor
    if query:
        payload["query"] = query
    with httpx.Client(timeout=60) as client:
        res = client.post("https://api.notion.com/v1/search", headers=headers, json=payload)
        if res.status_code >= 400:
            return ResourceListResult()
        body = res.json()
    resources = []
    for item in body.get("results") or []:
        obj_type = item.get("object")
        title_parts = []
        for t in (item.get("title") or item.get("properties", {}).get("title", {}).get("title") or []):
            if isinstance(t, dict):
                title_parts.append(t.get("plain_text", ""))
        label = "".join(title_parts) or item.get("id", "Untitled")
        resources.append(
            ResourceOption(
                id=item["id"],
                label=label,
                kind="database" if obj_type == "database" else "page",
            )
        )
    return ResourceListResult(resources=resources, next_cursor=body.get("next_cursor"))


def list_posthog_projects(credentials: dict[str, Any], metadata: dict[str, Any]) -> ResourceListResult:
    host = metadata.get("host") or credentials.get("host") or "https://app.posthog.com"
    host = str(host).rstrip("/")
    headers = {"Authorization": f"Bearer {credentials['api_key']}"}
    with httpx.Client(timeout=30) as client:
        res = client.get(f"{host}/api/projects/", headers=headers)
        if res.status_code >= 400:
            return ResourceListResult()
        body = res.json()
    items = body.get("results") if isinstance(body, dict) else body
    if not isinstance(items, list):
        items = []
    return ResourceListResult(
        resources=[
            ResourceOption(
                id=str(p.get("id")),
                label=p.get("name") or str(p.get("id")),
                kind="project",
            )
            for p in items
            if p.get("id") is not None
        ]
    )


def list_jira_projects(credentials: dict[str, Any], metadata: dict[str, Any]) -> ResourceListResult:
    domain = metadata.get("domain") or credentials.get("domain")
    auth = httpx.BasicAuth(credentials["email"], credentials["api_token"])
    start_at = 0
    resources: list[ResourceOption] = []
    with httpx.Client(timeout=60) as client:
        while start_at < 500:
            res = client.get(
                f"https://{domain}/rest/api/3/project/search",
                auth=auth,
                params={"startAt": start_at, "maxResults": 50},
            )
            if res.status_code >= 400:
                break
            body = res.json()
            values = body.get("values") or []
            for p in values:
                resources.append(
                    ResourceOption(
                        id=p.get("key") or p.get("id"),
                        label=p.get("name") or p.get("key"),
                        kind="project",
                    )
                )
            if body.get("isLast", True) or not values:
                break
            start_at += len(values)
    return ResourceListResult(resources=resources)


def list_hubspot_resources(credentials: dict[str, Any]) -> ResourceListResult:
    resources = [
        ResourceOption(id=oid, label=label, kind="object_type")
        for oid, label in HUBSPOT_OBJECT_TYPES
    ]
    headers = {"Authorization": f"Bearer {credentials['access_token']}"}
    try:
        with httpx.Client(timeout=30) as client:
            res = client.get("https://api.hubapi.com/crm/v3/pipelines/deals", headers=headers)
            if res.status_code < 400:
                for pipe in res.json().get("results") or []:
                    resources.append(
                        ResourceOption(
                            id=str(pipe.get("id")),
                            label=pipe.get("label") or str(pipe.get("id")),
                            kind="pipeline",
                        )
                    )
    except Exception:
        pass
    return ResourceListResult(resources=resources)


def list_salesforce_resources(credentials: dict[str, Any], metadata: dict[str, Any]) -> ResourceListResult:
    instance = metadata.get("instance_url") or credentials.get("instance_url")
    headers = {"Authorization": f"Bearer {credentials['access_token']}"}
    resources: list[ResourceOption] = []
    for oid, label in [("Account", "Accounts"), ("Contact", "Contacts"), ("Opportunity", "Opportunities")]:
        resources.append(ResourceOption(id=oid, label=label, kind="object_type"))
    if not instance:
        return ResourceListResult(resources=resources)
    with httpx.Client(timeout=60) as client:
        res = client.get(
            f"{instance}/services/data/v59.0/query",
            headers=headers,
            params={"q": "SELECT Id, Name, SobjectType FROM RecordType LIMIT 200"},
        )
        if res.status_code < 400:
            for rec in res.json().get("records") or []:
                resources.append(
                    ResourceOption(
                        id=rec["Id"],
                        label=f"{rec.get('Name')} ({rec.get('SobjectType')})",
                        kind="record_type",
                        meta={"sobject": rec.get("SobjectType")},
                    )
                )
    return ResourceListResult(resources=resources)


def list_zendesk_views(credentials: dict[str, Any], metadata: dict[str, Any]) -> ResourceListResult:
    subdomain = metadata.get("subdomain") or credentials.get("subdomain")
    base = f"https://{subdomain}.zendesk.com/api/v2"
    auth = cls_auth(credentials, metadata)
    resources = [ResourceOption(id="__all__", label="All tickets", kind="view")]
    with httpx.Client(timeout=60) as client:
        res = client.get(
            f"{base}/views/active.json",
            auth=auth if isinstance(auth, httpx.BasicAuth) else None,
            headers=auth if isinstance(auth, dict) else None,
        )
        if res.status_code < 400:
            for view in res.json().get("views") or []:
                resources.append(
                    ResourceOption(
                        id=str(view.get("id")),
                        label=view.get("title") or str(view.get("id")),
                        kind="view",
                    )
                )
    return ResourceListResult(resources=resources)


def cls_auth(credentials: dict[str, Any], metadata: dict[str, Any]) -> httpx.BasicAuth | dict[str, str]:
    if credentials.get("api_token"):
        return httpx.BasicAuth(f"{credentials['email']}/token", credentials["api_token"])
    return {"Authorization": f"Bearer {credentials['access_token']}"}


def list_intercom_resources(credentials: dict[str, Any], metadata: dict[str, Any]) -> ResourceListResult:
    base_url = metadata.get("base_url", "https://api.intercom.io")
    headers = {
        "Authorization": f"Bearer {credentials['access_token']}",
        "Accept": "application/json",
        "Intercom-Version": "2.11",
    }
    resources: list[ResourceOption] = []
    with httpx.Client(timeout=60) as client:
        tags_res = client.get(f"{base_url}/tags", headers=headers)
        if tags_res.status_code < 400:
            for tag in tags_res.json().get("data") or []:
                resources.append(
                    ResourceOption(
                        id=str(tag.get("id")),
                        label=tag.get("name") or str(tag.get("id")),
                        kind="tag",
                    )
                )
        teams_res = client.get(f"{base_url}/teams", headers=headers)
        if teams_res.status_code < 400:
            for team in teams_res.json().get("teams") or teams_res.json().get("data") or []:
                resources.append(
                    ResourceOption(
                        id=str(team.get("id")),
                        label=team.get("name") or str(team.get("id")),
                        kind="team",
                    )
                )
    return ResourceListResult(resources=resources)


def list_gong_workspaces(credentials: dict[str, Any], metadata: dict[str, Any]) -> ResourceListResult:
    base = metadata.get("api_base_url", "https://api.gong.io").rstrip("/")
    if credentials.get("access_key"):
        auth: httpx.BasicAuth | dict[str, str] = httpx.BasicAuth(
            credentials["access_key"], credentials["access_key_secret"]
        )
    else:
        auth = {"Authorization": f"Bearer {credentials['access_token']}"}
    resources: list[ResourceOption] = []
    with httpx.Client(timeout=30) as client:
        res = client.get(
            f"{base}/v2/workspaces",
            auth=auth if isinstance(auth, httpx.BasicAuth) else None,
            headers=auth if isinstance(auth, dict) else None,
        )
        if res.status_code < 400:
            for ws in res.json().get("workspaces") or []:
                resources.append(
                    ResourceOption(
                        id=str(ws.get("id")),
                        label=ws.get("name") or str(ws.get("id")),
                        kind="workspace",
                    )
                )
    if not resources:
        resources.append(
            ResourceOption(
                id="default",
                label="All workspaces (default)",
                kind="workspace",
            )
        )
    return ResourceListResult(resources=resources)


def guided_reviews_resources() -> ResourceListResult:
    return ResourceListResult(
        resources=[
            ResourceOption(id="g2", label="G2", kind="platform"),
            ResourceOption(id="capterra", label="Capterra", kind="platform"),
            ResourceOption(id="trustradius", label="TrustRadius", kind="platform"),
        ]
    )


def guided_reddit_subreddits() -> ResourceListResult:
    suggestions = ["all", "technology", "saas", "startups", "marketing", "entrepreneur"]
    return ResourceListResult(
        resources=[ResourceOption(id=s, label=f"r/{s}", kind="subreddit") for s in suggestions]
    )
