// frontend/src/app/chat/page.tsx
"use client";
import React, { useState, useRef, useEffect } from "react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";
import { sendChatMessage } from "@/lib/api";

// Message type
type Msg = { role: "user" | "assistant"; text: string };


export default function ChatPage() {
    const [msgs, setMsgs] = useState<Msg[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Scroll to bottom whenever messages change
        scrollRef.current?.scrollTo({
            top: scrollRef.current.scrollHeight,
            behavior: "smooth",
        });
    }, [msgs]);

    async function handleSend(text: string) {
        // Add user message
        setMsgs((prev) => [...prev, { role: "user", text }]);
        try {
            // Fetch assistant reply
            const reply = await sendChatMessage(text);
            setMsgs((prev) => [...prev, { role: "assistant", text: reply }]);
        } catch (error) {
            console.error("Chat error", error);
            setMsgs((prev) => [...prev, { role: "assistant", text: "Error fetching reply." }]);
        }
    }

    return (
        <div className="flex flex-col h-screen">
            {/* Centered container with max width */}
            <div className="flex-1 flex justify-center">
                <div className="flex flex-col w-full max-w-3xl">
                    {/* Scrollable message area */}
                    <ScrollArea className="flex-1">
                        <div ref={scrollRef} className="space-y-2 p-4">
                            {msgs.map((msg, idx) => (
                                <ChatBubble key={idx} text={msg.text} isUser={msg.role === "user"} />
                            ))}
                        </div>
                        <ScrollBar orientation="vertical" />
                    </ScrollArea>

                    {/* Sticky input at bottom */}
                    <div className="sticky bottom-0 w-full p-10">
                        <ChatInput onSend={handleSend} />
                    </div>
                </div>
            </div>
        </div>
    );
}
