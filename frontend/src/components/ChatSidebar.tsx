// frontend/src/components/ChatSidebar.tsx
"use client";

import { useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DeleteIcon } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Sidebar,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import {
  ConversationRead,
  listConversations,
  deleteConversation,
} from "@/lib/generate";

export interface ChatSidebarProps {
  onSelectConversation: (id: string | null) => void;
  activeId?: string | null;
}

export function ChatSidebar({
  onSelectConversation,
  activeId,
}: ChatSidebarProps) {
  const [convos, setConvos] = useState<ConversationRead[] | null>(null);

  // load list once
  useEffect(() => {
    listConversations()
      .then(setConvos)
      .catch(() => setConvos([]));
  }, []);

  // whenever activeId changes to a value we don’t yet have, re-fetch
  useEffect(() => {
    if (activeId && convos && !convos.find((c) => c.id === activeId)) {
      listConversations().then(setConvos);
    }
  }, [activeId, convos]);

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
                      <div
                        className={`
                          flex items-center justify-between
                          px-3 py-2 rounded
                          ${c.id === activeId
                            ? "bg-sidebar-accent text-sidebar-accent-foreground"
                            : "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                          }
                          cursor-pointer
                        `}
                        onClick={() => onSelectConversation(c.id)}
                      >
                        {/* Chat title */}
                        <span className="truncate flex-1">
                          {c.summary ?? `Chat • ${c.id.slice(0, 6)}`}
                        </span>

                        {/* Delete with confirmation */}
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <button
                              onClick={(e) => e.stopPropagation()}
                              className="flex-shrink-0 p-1 rounded hover:text-destructive"
                              aria-label="Delete conversation"
                            >
                              <DeleteIcon className="w-4 h-4" />
                            </button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>
                                Delete “{c.summary ?? c.id.slice(0, 6)}”?
                              </AlertDialogTitle>
                              <AlertDialogDescription>
                                This cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => {
                                  deleteConversation(c.id).then(() => {
                                    setConvos((prev) => {
                                      const updated = prev?.filter((x) => x.id !== c.id) ?? [];
                                      // if we deleted the active convo, clear selection
                                      if (c.id === activeId) {
                                        if (updated.length > 0) {
                                          onSelectConversation(updated[0].id);
                                        } else {
                                          onSelectConversation(null);
                                        }
                                      }
                                      return updated;
                                    });
                                  });
                                }}
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
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