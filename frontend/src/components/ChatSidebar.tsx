// frontend/src/components/ChatSidebar.tsx
"use client";

import {
  Sidebar,
  SidebarContent,
} from "@/components/ui/sidebar";

export function ChatSidebar() {
  return (
    <Sidebar
      className="h-full bg-muted mt-14"
    >
      <SidebarContent>
        <ul className="space-y-2 p-4">
          {/* TODO: map your real conversations here */}
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 1
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 2
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 3
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 4
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 5
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 6
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 7
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 8
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 9
          </li>
          <li className="cursor-pointer hover:bg-accent/10 rounded px-2 py-1">
            Conversation 10
          </li>
          {/* … */}
        </ul>
      </SidebarContent>
    </Sidebar>
  );
}