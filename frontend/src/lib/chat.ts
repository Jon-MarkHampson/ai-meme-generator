// lib/chat.ts
import API from "./api";
import Cookies from "js-cookie";

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

// 1) Create a new conversation
export async function createConversation(): Promise<ConversationRead> {
  const { data } = await API.post<ConversationRead>("/chat/conversations/");
  return data;
}

// 2) List all of a user’s conversations
export async function listConversations(): Promise<ConversationRead[]> {
  const { data } = await API.get<ConversationRead[]>("/chat/conversations/");
  return data;
}

// 3) Fetch one conversation
export async function getConversation(id: string): Promise<ConversationRead> {
  const { data } = await API.get<ConversationRead>(`/chat/conversations/${id}`);
  return data;
}

// 4) Update summary
export async function updateConversation(
  id: string,
  summary: string
): Promise<ConversationRead> {
  const { data } = await API.patch<ConversationRead>(
    `/chat/conversations/${id}`,
    { summary }
  );
  return data;
}

// 5) Delete
export async function deleteConversation(id: string): Promise<void> {
  await API.delete<void>(`/chat/conversations/${id}`);
}

// 6) List messages
export async function listMessages(
  conversationId: string
): Promise<ChatMessage[]> {
  const { data } = await API.get<ChatMessage[]>(
    `/chat/conversations/${conversationId}/messages/`
  );
  return data;
}

// 7) Append a message
export async function postMessage(
  conversationId: string,
  content: string
): Promise<ChatMessage> {
  const { data } = await API.post<ChatMessage>(
    `/chat/conversations/${conversationId}/messages/`,
    { role: "user", content }
  );
  return data;
}

// 8) Streaming chat
export function streamChat(
  conversationId: string,
  prompt: string,
  onMessage: (msg: ChatMessage) => void,
  onError: (err: Error) => void
): () => void {
  const controller = new AbortController();
  const token = Cookies.get("token");

  fetch(
    `${API.defaults.baseURL}/chat/conversations/${conversationId}/stream/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ prompt }),
      signal: controller.signal,
    }
  )
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (!res.body) throw new Error("No response body");
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      return reader.read().then(function pump({ done, value }): any {
        if (done) return;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop()!; // leave incomplete chunk
        for (const line of lines) {
          if (line.trim()) onMessage(JSON.parse(line));
        }
        return reader.read().then(pump);
      });
    })
    .catch(onError);

  return () => controller.abort();
}
