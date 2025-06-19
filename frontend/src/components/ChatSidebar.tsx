// frontend/src/components/ChatSidebar.tsx
"use client";

import {
  Sidebar,
  SidebarContent,
} from "@/components/ui/sidebar";

export function ChatSidebar() {
  return (
    <Sidebar collapsible="icon" className="h-full bg-muted">
      <SidebarContent>
        <ul className="space-y-2">
          <li className="flex items-center p-2">Alice</li>
          <li className="flex items-center p-2">Bob</li>
          <li className="flex items-center p-2">Charlie</li>
          <li className="flex items-center p-2">David</li>
          <li className="flex items-center p-2">Eve</li>
          <li className="flex items-center p-2">Frank</li>
          <li className="flex items-center p-2">Grace</li>
          <li className="flex items-center p-2">Heidi</li>
          <li className="flex items-center p-2">Ivan</li>
          <li className="flex items-center p-2">Judy</li>
          <li className="flex items-center p-2">Karl</li>
          <li className="flex items-center p-2">Liam</li>
          <li className="flex items-center p-2">Mallory</li>
          <li className="flex items-center p-2">Nina</li>
          <li className="flex items-center p-2">Oscar</li>
        </ul>
      </SidebarContent>
    </Sidebar>
  );
}