"use client";
import { useEffect, useRef } from "react";
import { getConversation } from "@/lib/generate";
import type { ConversationRead } from "@/lib/generate";

/**
 * Poll /api/conversations/:id until a summary appears, then fires onUpdate and stops.
 */
export function useConversationSummary(
  conversationId: string,
  onUpdate: (conv: ConversationRead) => void,
  intervalMs = 3000
) {
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!conversationId) return;
    timerRef.current = setInterval(async () => {
      try {
        const conv = await getConversation(conversationId);
        if (conv.summary) {
          onUpdate(conv);
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
        }
      } catch (err) {
        console.error("Polling summary error", err);
      }
    }, intervalMs);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [conversationId, onUpdate, intervalMs]);
}
