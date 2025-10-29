"use client";
import { useEffect, useRef } from "react";
import { getConversation } from "@/services/generate";
import type { ConversationRead } from "@/types/conversations";

/**
 * Poll /api/conversations/:id until a summary appears, then fires onUpdate and stops.
 */
export function useConversationSummary(
  conversationId: string,
  onUpdate: (conv: ConversationRead) => void,
  intervalMs = 3000
) {
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isActiveRef = useRef<boolean>(true);

  useEffect(() => {
    // Don't start polling if conversationId is null, undefined, or empty
    if (!conversationId) {
      // Clear any existing timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    isActiveRef.current = true;

    // Listen for session expiry to stop polling
    const handleSessionExpired = () => {
      console.log('[useConversationSummary] Session expired, stopping polling');
      isActiveRef.current = false;
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };

    window.addEventListener('session-expired', handleSessionExpired);

    timerRef.current = setInterval(async () => {
      // Stop polling if session expired
      if (!isActiveRef.current) {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        return;
      }

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
        // Stop polling on error (likely 401)
        isActiveRef.current = false;
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      }
    }, intervalMs);

    return () => {
      window.removeEventListener('session-expired', handleSessionExpired);
      isActiveRef.current = false;
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [conversationId, onUpdate, intervalMs]);
}
