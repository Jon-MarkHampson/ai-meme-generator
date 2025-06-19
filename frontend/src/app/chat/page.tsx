"use client";
import { useEffect, useState, useRef } from "react";
import {
    createConversation,
    streamChat,
    ChatMessage,
} from "@/lib/chat";
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";
import { ChatSidebar } from "@/components/ChatSidebar";

export default function ChatPage() {
    const [convId, setConvId] = useState<string | null>(null);
    const [msgs, setMsgs] = useState<ChatMessage[]>([]);
    const abortRef = useRef<(() => void) | undefined>(undefined);

    // 1) on mount, start a conversation
    useEffect(() => {
        createConversation()
            .then((c) => setConvId(c.id))
            .catch(() =>
                setMsgs([
                    {
                        role: "model",
                        content: "⚠ Could not start conversation.",
                        timestamp: new Date().toISOString(),
                    },
                ])
            );
    }, []);

    // 2) on user send
    const handleSend = async (text: string): Promise<void> => {
        if (!convId) return;
        // 1) show the user's bubble immediately
        setMsgs((prev) => [
            ...prev,
            { role: "user", content: text, timestamp: new Date().toISOString() },
        ]);

        // 2) stream the AI response
        abortRef.current = streamChat(
            convId,
            text,
            (msg) => {
                if (msg.role !== "model") return; // only handle model messages
                setMsgs((prev) => {
                    // if the last bubble is already from the model, overwrite it
                    if (prev.length && prev[prev.length - 1].role === "model") {
                        const copy = [...prev];
                        copy[copy.length - 1] = {
                            role: "model",
                            content: msg.content,
                            timestamp: msg.timestamp,
                        };
                        return copy;
                    }
                    // otherwise append a new model bubble
                    return [
                        ...prev,
                        { role: "model", content: msg.content, timestamp: msg.timestamp },
                    ];
                });
            },
            () => {
                // on error, append a single error bubble
                setMsgs((prev) => [
                    ...prev,
                    {
                        role: "model",
                        content: "⚠ Error talking to AI.",
                        timestamp: new Date().toISOString(),
                    },
                ]);
            }
        );
    };

    return (
        <SidebarProvider>
            <div className="flex align-middle justify-center h-[80vh] w-full max-w-[1200px] mt-10 px-3">
                {/* 1) Sidebar drawer */}
                <ChatSidebar />

                {/* 2) Chat content area */}
                <div className="flex-1 flex flex-col align-middle justify-center w-full">
                    {/* toggle button always shown (you can hide on desktop with md:hidden if you like) */}
                    <div className="p-2">
                        <SidebarTrigger />
                    </div>

                    {/* messages */}
                    <ScrollArea className="flex-1 overflow-auto border-1 border-border rounded-lg">
                        <div className="pt-4 space-y-2">
                            {msgs.map((m, i) => (
                                <ChatBubble
                                    key={i}
                                    text={m.content}
                                    isUser={m.role === "user"}
                                />
                            ))}
                        </div>
                    </ScrollArea>

                    {/* input */}
                    <div className="py-4 bg-background">
                        <ChatInput onSend={handleSend} />
                    </div>
                </div>
            </div>
        </SidebarProvider>
    );
}