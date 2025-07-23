// lib/generate.ts
import API from "./api";

export interface ConversationRead {
  id: string;
  user_id: string;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  role: "user" | "model";
  content: string;
  timestamp: string;
}

export interface ConversationUpdateMessage {
  type: "conversation_update";
  conversation_id: string;
  summary: string;
  updated_at: string;
}

export type StreamMessage = ChatMessage | ConversationUpdateMessage;

// Add utility function to sort conversations by updated_at descending
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
  const { data } = await API.post<ConversationRead>("/generate/conversations/");
  return data;
}

// 2) List all of a user’s conversations
export async function listConversations(): Promise<ConversationRead[]> {
  const { data } = await API.get<ConversationRead[]>(
    "/generate/conversations/"
  );
  return data;
}

// 3) Fetch one conversation
export async function getConversation(id: string): Promise<ConversationRead> {
  const { data } = await API.get<ConversationRead>(
    `/generate/conversations/${id}`
  );
  return data;
}

// 4) Update summary
export async function updateConversation(
  id: string,
  summary: string
): Promise<ConversationRead> {
  const { data } = await API.patch<ConversationRead>(
    `/generate/conversations/${id}`,
    { summary }
  );
  return data;
}

// 5) Delete
export async function deleteConversation(id: string): Promise<void> {
  await API.delete<void>(`/generate/conversations/${id}`);
}

// 6) List messages
export async function listMessages(
  conversationId: string
): Promise<ChatMessage[]> {
  const { data } = await API.get<ChatMessage[]>(
    `/generate/conversations/${conversationId}/messages/`
  );
  return data;
}

// 7) Append a message
export async function postMessage(
  conversationId: string,
  content: string
): Promise<ChatMessage> {
  const { data } = await API.post<ChatMessage>(
    `/generate/conversations/${conversationId}/messages/`,
    { role: "user", content }
  );
  return data;
}

// 8) Streaming chat
export function streamChat(
  conversationId: string,
  manager_model: string,
  prompt: string,
  onMessage: (msg: ChatMessage, streamConvId: string) => void,
  onConversationUpdate: (update: ConversationUpdateMessage) => void,
  onError: (err: Error) => void
): () => void {
  const controller = new AbortController();

  const processStream = async () => {
    try {
      const res = await fetch(
        `${API.defaults.baseURL}/generate/conversations/${conversationId}/stream/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ manager_model, prompt }),
          signal: controller.signal,
          // this tells fetch to include HttpOnly cookie
          credentials: "include",
        }
      );

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
                const parsed = JSON.parse(line) as StreamMessage;
                if ("type" in parsed && parsed.type === "conversation_update") {
                  // Handle conversation update
                  onConversationUpdate(parsed);
                } else {
                  // Handle regular chat message
                  onMessage(parsed as ChatMessage, conversationId);
                }
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
        } catch (e) {
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
