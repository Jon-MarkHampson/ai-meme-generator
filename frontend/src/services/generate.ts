/**
 * AI meme generation and conversation management API client.
 *
 * This module provides the frontend interface for interacting with the AI meme
 * generation system, including conversation management, streaming responses,
 * and message history. Handles Server-Sent Events for real-time AI responses.
 *
 * Key features:
 * - Conversation CRUD operations with backend persistence
 * - Real-time streaming of AI responses via Server-Sent Events
 * - Dual message types: chat messages and conversation metadata updates
 * - Stream cancellation and error handling
 * - Conversation sorting by activity for better UX
 */
import API from "./api";
import { ConversationRead, ChatMessage } from "@/types/conversations";

/**
 * Sort conversations by most recent activity first.
 *
 * Used to maintain conversation list ordering in the sidebar,
 * ensuring active conversations appear at the top.
 *
 * @param conversations - Array of conversations to sort
 * @returns New sorted array (original unchanged)
 */
export function sortConversationsByUpdatedAt(
  conversations: ConversationRead[]
): ConversationRead[] {
  return [...conversations].sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );
}

// 1) Create a new conversation
export async function createConversation(): Promise<ConversationRead> {
  const { data } = await API.post<ConversationRead>("/conversations/");
  return data;
}

// 2) List all of a user’s conversations
export async function listConversations(): Promise<ConversationRead[]> {
  const { data } = await API.get<ConversationRead[]>("/conversations/");
  return data;
}

// 3) Fetch one conversation
export async function getConversation(id: string): Promise<ConversationRead> {
  const { data } = await API.get<ConversationRead>(`/conversations/${id}`);
  return data;
}

// 4) Update summary
export async function updateConversation(
  id: string,
  summary: string
): Promise<ConversationRead> {
  const { data } = await API.patch<ConversationRead>(`/conversations/${id}`, {
    summary,
  });
  return data;
}

// 5) Delete
export async function deleteConversation(id: string): Promise<void> {
  await API.delete<void>(`/conversations/${id}`);
}

// 6) List messages
export async function listMessages(
  conversationId: string
): Promise<ChatMessage[]> {
  const { data } = await API.get<ChatMessage[]>(
    `/messages/conversations/${conversationId}`
  );
  return data;
}

// Note: postMessage is not used - messages are created through the streaming endpoint

/**
 * Stream AI meme generation responses in real-time.
 *
 * Establishes a Server-Sent Events connection to the backend for streaming
 * AI responses as they're generated. Handles chat messages in real-time.
 *
 * @param conversationId - Target conversation ID
 * @param manager_model - AI model selection (e.g., "openai:gpt-4")
 * @param prompt - User's meme generation request
 * @param onMessage - Callback for chat message updates
 * @param onError - Callback for error handling
 * @returns Abort function to cancel the stream
 */
export function streamChat(
  conversationId: string,
  manager_model: string,
  prompt: string,
  onMessage: (msg: ChatMessage, streamConvId: string) => void,
  onError: (err: Error) => void
): () => void {
  const controller = new AbortController();

  const processStream = async () => {
    try {
      const res = await fetch(`${API.defaults.baseURL}/generate/meme`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          conversation_id: conversationId,
          manager_model,
        }),
        signal: controller.signal,
        // this tells fetch to include HttpOnly cookie
        credentials: "include",
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";

      try {
        while (true) {
          const { done, value } = await reader.read();

          // Check if the controller was aborted
          if (controller.signal.aborted) {
            break;
          }

          if (done) break;

          buf += dec.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop()!; // leave incomplete chunk

          for (const line of lines) {
            if (line.trim()) {
              try {
                const parsed = JSON.parse(line);
                onMessage(parsed as ChatMessage, conversationId);
              } catch (parseError) {
                console.warn(
                  "Failed to parse stream message:",
                  line,
                  parseError
                );
              }
            }
          }
        }
      } finally {
        // Always clean up the reader
        try {
          reader.releaseLock();
        } catch {
          // Reader might already be released
        }
      }
    } catch (error) {
      // Don't call onError if the operation was aborted
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }
      onError(error as Error);
    }
  };

  // Start the stream processing
  processStream();

  return () => controller.abort();
}
