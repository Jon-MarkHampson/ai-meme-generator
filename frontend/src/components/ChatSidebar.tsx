"use client";

import { ConversationRead } from "@/lib/generate";
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

export interface ChatSidebarProps {
  convos: ConversationRead[] | null;
  onSelectConversation: (id: string | null) => void;
  onDeleteConversation: (id: string) => void;
  activeId?: string | null;
}

export function ChatSidebar({
  convos,
  onSelectConversation,
  onDeleteConversation,
  activeId,
}: ChatSidebarProps) {
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
                      <div className="flex items-center justify-between rounded">
                        <button
                          className={`
                            flex-1 text-left px-3 py-2 rounded
                            ${c.id === activeId
                              ? "bg-sidebar-accent text-sidebar-accent-foreground"
                              : "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                            }
                          `}
                          onClick={() => onSelectConversation(c.id)}
                        >
                          <span className="truncate">
                            {c.summary ?? `Chat • ${c.id.slice(0, 6)}`}
                          </span>
                        </button>

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
                                onClick={() => onDeleteConversation(c.id)}
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