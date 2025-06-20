// frontend/src/components/ChatSidebar.tsx
"use client";

import { useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area"
import { ClockIcon } from "lucide-react";
import { DeleteIcon } from "lucide-react";
import {
  Sidebar,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuSkeleton,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import { ConversationRead, listConversations } from "@/lib/generate";

export interface ChatSidebarProps {
  onSelectConversation: (id: string) => void;
  activeId?: string;
}
export function ChatSidebar({
  onSelectConversation,
  activeId,
}: ChatSidebarProps) {
  const [convos, setConvos] = useState<ConversationRead[] | null>(null);

  useEffect(() => {
    listConversations()
      .then(setConvos)
      .catch(() => setConvos([])); // on error, show empty
  }, []);

  return (
    <Sidebar className="h-full bg-muted">
      <ScrollArea className="h-full mt-0 lg:mt-16">
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Your Meme Chats</SidebarGroupLabel>
            <SidebarGroupContent>
              {convos === null ? (
                // loading skeleton
                <SidebarMenu>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <SidebarMenuItem key={i}>
                      <SidebarMenuSkeleton showIcon />
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              ) : convos.length === 0 ? (
                <div className="p-4 text-sm text-muted-foreground">
                  No conversations yet.
                </div>
              ) : (
                <SidebarMenu>
                  {convos.map((c) => (
                    <SidebarMenuItem key={c.id}>
                      <SidebarMenuButton
                        asChild
                        isActive={c.id === activeId}
                      >
                        <button
                          onClick={() => onSelectConversation(c.id)}
                          className="flex w-full justify-between px-3 py-2 rounded hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                        >
                          <span className="truncate">
                            {c.summary ?? `Chat • ${c.id.slice(0, 6)}`}
                          </span>
                          {/* <ClockIcon className="w-4 h-4 opacity-50" /> */}
                        </button>
                        {/* <button
                          onClick={() => {
                            // handle delete conversation
                          }}
                        >
                          <DeleteIcon className="w-4 h-4 opacity-50" />
                        </button> */}
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              )}
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </ScrollArea>
    </Sidebar>
  );
}