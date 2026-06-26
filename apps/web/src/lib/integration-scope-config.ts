/**
 * @file apps/web/src/lib/integration-scope-config.ts
 * @description Maps integration providers to scope field keys for the resource picker UI.
 */

export type ScopeFieldConfig = {
  multi: boolean;
  fieldKey: string;
  kinds?: string[];
  guided?: boolean;
  guidedFields?: { key: string; label: string; type?: string }[];
};

export const SCOPE_CONFIG: Record<string, ScopeFieldConfig> = {
  slack: { multi: true, fieldKey: "channel_ids", kinds: ["channel"] },
  ga4: { multi: false, fieldKey: "property_id", kinds: ["property"] },
  google_drive: { multi: true, fieldKey: "file_ids", kinds: ["file"] },
  notion: { multi: true, fieldKey: "page_ids", kinds: ["page", "database"] },
  posthog: { multi: false, fieldKey: "project_id", kinds: ["project"] },
  jira: { multi: true, fieldKey: "project_keys", kinds: ["project"] },
  hubspot: { multi: true, fieldKey: "object_types", kinds: ["object_type"] },
  salesforce: { multi: true, fieldKey: "objects", kinds: ["object_type"] },
  zendesk: { multi: true, fieldKey: "view_ids", kinds: ["view"] },
  intercom: { multi: true, fieldKey: "tag_ids", kinds: ["tag", "team"] },
  gong: { multi: true, fieldKey: "workspace_ids", kinds: ["workspace"] },
  reviews: {
    multi: false,
    fieldKey: "product_query",
    guided: true,
    guidedFields: [
      { key: "product_query", label: "G2/Capterra product URL or name" },
      { key: "max_results", label: "Max reviews (default 50)" },
    ],
  },
  reddit: {
    multi: false,
    fieldKey: "search_query",
    guided: true,
    guidedFields: [
      { key: "search_query", label: "Brand or product search query" },
      { key: "max_results", label: "Max posts (default 50)" },
    ],
  },
};

/** Extra scope keys saved alongside primary selection. */
export const SCOPE_SECONDARY_KEYS: Record<string, string> = {
  hubspot: "pipeline_ids",
  notion: "database_ids",
  intercom: "team_ids",
  salesforce: "record_type_ids",
};

export function buildScopePayload(
  provider: string,
  selected: Array<{ id: string; label: string; kind: string }>,
  guidedValues?: Record<string, string>
): Record<string, unknown> {
  const config = SCOPE_CONFIG[provider];
  if (!config) return { scope_configured: true };

  if (config.guided && guidedValues) {
    const payload: Record<string, unknown> = { ...guidedValues, scope_configured: true };
    if (provider === "reviews") {
      payload.platforms = selected.filter((s) => s.kind === "platform").map((s) => s.id);
      if (!payload.platforms || (payload.platforms as string[]).length === 0) {
        payload.platforms = ["g2", "capterra", "trustradius"];
      }
    }
    if (provider === "reddit") {
      payload.subreddits = selected.filter((s) => s.kind === "subreddit").map((s) => s.id);
    }
    return payload;
  }

  const labels: Record<string, string> = {};
  for (const item of selected) {
    labels[item.id] = item.label;
  }

  if (!config.multi) {
    const item = selected[0];
    return {
      [config.fieldKey]: item?.id,
      scope_labels: labels,
      scope_configured: true,
    };
  }

  const primaryKinds = config.kinds ?? [];
  const primary = selected.filter((s) => primaryKinds.includes(s.kind)).map((s) => s.id);
  const secondaryKey = SCOPE_SECONDARY_KEYS[provider];
  const payload: Record<string, unknown> = {
    [config.fieldKey]: primary,
    scope_labels: labels,
    scope_configured: true,
  };

  if (provider === "notion") {
    payload.page_ids = selected.filter((s) => s.kind === "page").map((s) => s.id);
    payload.database_ids = selected.filter((s) => s.kind === "database").map((s) => s.id);
  } else if (provider === "hubspot") {
    payload.object_types = selected.filter((s) => s.kind === "object_type").map((s) => s.id);
    payload.pipeline_ids = selected.filter((s) => s.kind === "pipeline").map((s) => s.id);
  } else if (provider === "intercom") {
    payload.tag_ids = selected.filter((s) => s.kind === "tag").map((s) => s.id);
    payload.team_ids = selected.filter((s) => s.kind === "team").map((s) => s.id);
  } else if (provider === "salesforce") {
    payload.objects = selected.filter((s) => s.kind === "object_type").map((s) => s.id);
    payload.record_type_ids = selected.filter((s) => s.kind === "record_type").map((s) => s.id);
  } else if (secondaryKey) {
    payload[secondaryKey] = selected
      .filter((s) => !primaryKinds.includes(s.kind))
      .map((s) => s.id);
  }

  return payload;
}
