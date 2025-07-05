"use client";
import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import {
    createConversation,
    streamChat,
    listMessages,
    ChatMessage,
} from "@/lib/generate";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";
import { SquarePen } from "lucide-react";

const WELCOME: ChatMessage[] = [
    {
        role: "model",
        content:
            "👋 Hey there! Let's make some memes! Do you have an idea, shall we brainstorm or shall I surprise you?",
        timestamp: new Date().toISOString(),
    },
];


export default function ChatPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    // ─── Declare ALL your hooks first ─────────────────────────────
    const [convId, setConvId] = useState<string | null>(null);
    const [msgs, setMsgs] = useState<ChatMessage[]>(WELCOME);
    const abortRef = useRef<(() => void) | null>(null);
    const endRef = useRef<HTMLDivElement>(null);

    // ─── 1) redirect if not logged in ─────────────────────────────
    useEffect(() => {
        if (!loading && !user) {
            router.replace("/");
        }
    }, [loading, user, router]);

    // ─── 2) scroll to bottom on new msgs ──────────────────────────
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [msgs]);

    // ─── 3) whenever convId changes, load its history ─────────────
    useEffect(() => {
        if (!convId) return;
        listMessages(convId)
            .then((history) => {
                if (history.length) setMsgs(history);
                setTimeout(
                    () => endRef.current?.scrollIntoView({ behavior: "smooth" }),
                    0
                );
            })
            .catch(() => {
                setMsgs([
                    {
                        role: "model",
                        content: "⚠ Couldn't load that conversation.",
                        timestamp: new Date().toISOString(),
                    },
                ]);
            });
    }, [convId]);

    // 4) Reset to welcome when convId === null:
    useEffect(() => {
        if (convId === null) {
            setMsgs(WELCOME);
        }
    }, [convId]);

    // ─── Now do early return based on auth ────────────────────
    if (loading || !user) {
        return null; // or a loading spinner
    }

    // ─── 4) on user send ─────────────────────────────────────────
    const handleSend = async (text: string) => {
        setMsgs((prev) => [
            ...prev,
            { role: "user", content: text, timestamp: new Date().toISOString() },
        ]);

        let id = convId;
        if (!id) {
            try {
                const conv = await createConversation();
                id = conv.id;
                setConvId(id);
            } catch {
                setMsgs((prev) => [
                    ...prev,
                    {
                        role: "model",
                        content:
                            "⚠️ Sorry, I couldn't start our chat. Please try again.",
                        timestamp: new Date().toISOString(),
                    },
                ]);
                return;
            }
        }

        abortRef.current = streamChat(
            id,
            text,
            (msg) => {
                if (msg.role !== "model") return;
                setMsgs((prev) => {
                    if (prev.length && prev[prev.length - 1].role === "model") {
                        const copy = [...prev];
                        copy[copy.length - 1] = msg;
                        return copy;
                    }
                    return [...prev, msg];
                });
            },
            () =>
                setMsgs((prev) => [
                    ...prev,
                    {
                        role: "model",
                        content: "⚠ Error talking to AI.",
                        timestamp: new Date().toISOString(),
                    },
                ])
        );
    };

    // ─── 5) new‐conversation reset handler ────────────────────────
    const startNewConversation = () => {
        setConvId(null);
        setMsgs(WELCOME);
    };

    // ─── Finally, your JSX ────────────────────────────────────────
    return (
        <div className="h-[calc(100vh-5rem)] overflow-hidden">
            <SidebarProvider>
                <div className="relative w-full">
                    <div className="flex absolute justify-center inset-x-0 bottom-0 h-[calc(100vh-6rem)]">
                        <div className="shrink-0">
                            <ChatSidebar
                                activeId={convId}
                                onSelectConversation={(id) => {
                                    // always update the active conversation id (possibly null)
                                    setConvId(id)

                                    // but only fetch messages if it's a real conversation
                                    if (id) {
                                        listMessages(id).then(setMsgs)
                                    }
                                }}
                            />
                        </div>
                        <div className="flex flex-col flex-1 min-h-0 max-w-[1200px]">
                            <div className="flex flex-row p-2 justify-between">
                                <div className="flex items-center gap-2 text-sm font-medium text-primary bg-transparent rounded hover:bg-accent hover:text-accent-foreground">
                                    <SidebarTrigger className="w-4 h-4" />
                                    History
                                </div>
                                <button
                                    onClick={startNewConversation}
                                    className="flex items-center gap-2 text-sm font-medium text-primary bg-transparent rounded hover:bg-accent hover:text-accent-foreground">
                                    <SquarePen className="w-4 h-4" />
                                    New Conversation
                                </button>
                            </div>
                            <ScrollArea className="flex-1 overflow-auto py-4 border-2 border-border rounded-lg">
                                <div className="space-y-2">
                                    {msgs.map((m, i) => (
                                        <ChatBubble
                                            key={i}
                                            text={m.content}
                                            isUser={m.role === "user"}
                                        />
                                    ))}
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