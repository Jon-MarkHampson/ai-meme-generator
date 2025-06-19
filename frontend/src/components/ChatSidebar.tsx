// frontend/src/components/ChatSidebar.tsx
"use client";

import { useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import { listConversations } from "@/lib/chat";
import type { ConversationRead } from "@/lib/chat";

export interface ChatSidebarProps {
  /** called when the user clicks a conversation */
  onSelectConversation: (conversationId: string) => void;
}

export function ChatSidebar({ onSelectConversation }: ChatSidebarProps) {
  const [convos, setConvos] = useState<ConversationRead[]>([]);

  useEffect(() => {
    listConversations().then(setConvos).catch(console.error);
  }, []);

  return (
    <Sidebar collapsible="icon" className="h-full bg-muted">
      <ScrollArea className="h-full">
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Your Chats</SidebarGroupLabel>
            <SidebarGroupContent className="space-y-1">
              {convos.map((c) => (
                <div
                  key={c.id}
                  onClick={() => onSelectConversation(c.id)}
                  className="
                    cursor-pointer 
                    px-3 py-2 
                    rounded 
                    hover:bg-sidebar-accent 
                    hover:text-sidebar-accent-foreground
                  "
                >
                  {c.summary ?? "Conversation " + c.id.slice(0, 6)}
                </div>
              ))}
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </ScrollArea>
    </Sidebar>
  );
}