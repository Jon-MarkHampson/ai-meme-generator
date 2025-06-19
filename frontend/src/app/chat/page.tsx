"use client";
import { useEffect, useState, useRef } from "react";
import {
    createConversation,
    streamChat,
    listMessages,
    ChatMessage,
} from "@/lib/chat";
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";
import { ChatSidebar } from "@/components/ChatSidebar";

export default function ChatPage() {
    const [convId, setConvId] = useState<string | null>(null);
    const [msgs, setMsgs] = useState<ChatMessage[]>([
        {
            role: "model",
            content: "👋 Hey there! Ask me anything or request a meme.",
            timestamp: new Date().toISOString(),
        },
    ]);
    const abortRef = useRef<(() => void) | undefined>(undefined);
    const endRef = useRef<HTMLDivElement>(null);

    // 1) on mount, start a conversation
    // useEffect(() => {
    //     createConversation()
    //         .then((c) => setConvId(c.id))
    //         .catch(() =>
    //             setMsgs([
    //                 {
    //                     role: "model",
    //                     content: "⚠ Could not start conversation.",
    //                     timestamp: new Date().toISOString(),
    //                 },
    //             ])
    //         );
    // }, []);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [msgs]);
    // ————————————————————————————
    // 2) Whenever convId changes, load its history
    // ————————————————————————————
    useEffect(() => {
        if (!convId) return;
        listMessages(convId)
            .then((history) => {
                if (history.length) setMsgs(history);
                // after loading, scroll to bottom:
                setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 0);
            })
            .catch(() => {
                // (optional) handle error
            });
    }, [convId]);


    // 2) on user send
    const handleSend = async (text: string): Promise<void> => {
        // 1) show the user's bubble immediately
        setMsgs((prev) => [
            ...prev,
            { role: "user", content: text, timestamp: new Date().toISOString() },
        ]);

        // 2) If this is the very first message, create the conversation now:
        let id = convId;
        if (!id) {
            try {
                const conv = await createConversation();
                id = conv.id;
                setConvId(id);
            } catch (err) {
                // if we couldn't even make a conversation, show an error and bail
                setMsgs((prev) => [

                    ...prev,
                    {
                        role: "model",
                        content: "⚠️ Sorry, I couldn't start our chat. Please try again.",
                        timestamp: new Date().toISOString(),
                    },
                ]);
                return;
            }
        }

        // 3) stream the AI response
        abortRef.current = streamChat(
            id,
            text,
            (msg) => {
                if (msg.role !== "model") return; // only handle model messages not user
                setMsgs((prev) => {
                    // if the last bubble is already from the model, overwrite it
                    if (prev.length && prev[prev.length - 1].role === "model") {
                        const copy = [...prev];
                        copy[copy.length - 1] = msg;
                        return copy;
                    }
                    // otherwise append a new model bubble
                    return [...prev, msg];
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
        <div className="h-[calc(100vh-5rem)] overflow-hidden">
            <SidebarProvider>
                {/* 
        Wrap everything in a relative so our inner container can be absolute.
      */}
                <div className="relative w-full">
                    {/*
          Absolute‐position your entire chat UI underneath the header:
            - top-16 (4rem) matches your header's height (p-4 ➔ 1rem top + 1rem bottom + ~2rem content)
            - bottom-0
            - inset-x-0 stretches left & right
            - overflow-hidden so only our ScrollArea scrolls
        */}
                    <div className="flex absolute justify-center inset-x-0 bottom-0 h-[calc(100vh-6rem)]">
                        {/* ─── Sidebar ─── */}
                        <div className="shrink-0">
                            {/* pass a handler down into the sidebar */}
                            <ChatSidebar
                                onSelectConversation={(id) => {
                                    setConvId(id);
                                    // load that conversation’s past messages:
                                    listMessages(id)
                                        .then(setMsgs)
                                        .catch(() => {
                                            setMsgs([
                                                {
                                                    role: "model",
                                                    content: "⚠ Couldn't load that conversation.",
                                                    timestamp: new Date().toISOString(),
                                                },
                                            ]);
                                        });
                                }}
                            />
                        </div>

                        {/* ─── Chat Column ─── */}
                        <div className="flex flex-col flex-1 min-h-0 max-w-[1200px]">
                            <div className="p-2">
                                <SidebarTrigger />
                                History
                            </div>

                            {/* Only this scrolls */}
                            <ScrollArea className="flex-1 overflow-auto py-4 border-2 border-border rounded-lg">
                                <div className="space-y-2">
                                    {msgs.map((m, i) => (
                                        <ChatBubble
                                            key={i}
                                            text={m.content}
                                            isUser={m.role === "user"}
                                        />
                                    ))}
                                    {/* invisible anchor */}
                                    <div ref={endRef} />
                                </div>
                            </ScrollArea>

                            <div className="py-4 bg-background">
                                <ChatInput onSend={handleSend} />
                            </div>
                        </div>
                    </div>
                </div>
            </SidebarProvider>
        </div>
    );
}