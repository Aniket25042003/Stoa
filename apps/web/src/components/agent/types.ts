export type ConversationSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type AgentMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: string[];
  /** When true, assistant text reveals word-by-word (live turns only). */
  reveal?: boolean;
};
