/** Conversation data structure from backend API */
export interface ConversationRead {
  id: string; // Unique conversation identifier
  user_id: string; // Owner of the conversation
  summary?: string; // AI-generated conversation summary
  created_at: string; // ISO timestamp of creation
  updated_at: string; // ISO timestamp of last activity
}

/** Individual chat message in a conversation */
export interface ChatMessage {
  role: "user" | "model"; // Message sender type
  content: string; // Message text content (supports markdown)
  timestamp: string; // ISO timestamp of message
}