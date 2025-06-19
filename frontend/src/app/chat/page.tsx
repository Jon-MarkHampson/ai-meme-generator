"use client";
import { useEffect, useState, useRef } from "react";
import {
    createConversation,
    streamChat,
    ChatMessage,
} from "@/lib/chat";
import { ScrollArea } from "@/components/ui/scroll-area"
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";


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
        // push below header
        <div className="flex justify-center mt-10">
            {/* debug border on the chat “frame” */}
            <div className="
         flex flex-col            /* stack scroll + input */
         h-[80vh]                 /* give it a fixed height */
         w-full max-w-3xl         /* center, limit width */
         px-3
       ">
                {/* 1) scrollable history */}
                <ScrollArea className="flex-1 overflow-auto border-1 border-border rounded-lg">
                    <div className="pt-4 space-y-2">
                        {msgs.map((m, i) => (
                            <ChatBubble key={i} text={m.content} isUser={m.role === "user"} />
                        ))}
                    </div>
                </ScrollArea>

                {/* 2) always-visible input at bottom */}
                <div className="pt-4 bg-background">
                    <ChatInput onSend={handleSend} />
                </div>
            </div>
        </div>
    );
}