// frontend/src/app/generate/page.tsx
"use client";
import { useEffect, useState, useRef } from "react";
import { useSession } from "@/contexts/SessionContext";
import { AuthGuard } from "@/components/AuthGuard";
import {
    createConversation,
    streamChat,
    listMessages,
    ChatMessage,
    ConversationRead,
    ConversationUpdateMessage,
    listConversations,
    deleteConversation,
    sortConversationsByUpdatedAt,
} from "@/lib/generate";
import { SquarePen } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";
import { ModelSelector } from "@/components/ModelSelector";
import { useModelSelection } from "@/hooks/useModelSelection";


const WELCOME: ChatMessage[] = [
    {
        role: "model",
        content:
            "👋 Hey there! Let's make some memes! \nDo you have an idea, shall we brainstorm, search the web or shall I surprise you?",
        timestamp: new Date().toISOString(),
    },
];

function GenerateContent() {
    const { } = useSession();

    // ─── Declare ALL your hooks first ─────────────────────────────
    const [convId, setConvId] = useState<string | null>(null);
    const [msgs, setMsgs] = useState<ChatMessage[]>(WELCOME);
    const [convos, setConvos] = useState<ConversationRead[] | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    // ─── Model selection with smart hook ─────────────────────────────
    const { selectedModelId, changeModel } = useModelSelection({
        onModelChange: (model) => {
            console.log(`Model changed to: ${model.name} (${model.id})`);
        }
    });
    const abortRef = useRef<(() => void) | null>(null);
    const endRef = useRef<HTMLDivElement>(null);

    // ─── 1) scroll to bottom on new msgs ──────────────────────────
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [msgs]);

    // ─── List conversations on load ────────────────────────────────────
    useEffect(() => {
        listConversations()
            .then(setConvos)
            .catch(() => setConvos([]));
    }, []);

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

    // ─── 4) on user send ─────────────────────────────────────────
    const handleSend = async (text: string) => {
        setMsgs((prev) => [
            ...prev,
            { role: "user", content: text, timestamp: new Date().toISOString() },
        ]);

        // Set loading state and add a skeleton message
        setIsLoading(true);

        let id = convId;
        if (!id) {
            try {
                const conv = await createConversation();
                id = conv.id;
                setConvId(id);
                // Add new conversation and sort by updated_at
                setConvos(prev => {
                    const newList = prev ? [...prev, conv] : [conv];
                    return sortConversationsByUpdatedAt(newList);
                });
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
                setIsLoading(false);
                return;
            }
        }

        // Abort any existing stream before starting a new one
        if (abortRef.current) {
            abortRef.current();
        }

        abortRef.current = streamChat(
            id,
            selectedModelId,
            text,
            (msg: ChatMessage, streamConvId: string) => {
                // Only update messages if this stream matches the current conversation
                // Use 'id' instead of 'convId' because convId state update is async
                if (streamConvId !== id) {
                    console.log(`Ignoring message from conversation ${streamConvId}, current is ${id}`);
                    return;
                }

                if (msg.role !== "model") return;

                // Clear loading state on first model message
                setIsLoading(false);

                setMsgs((prev) => {
                    if (prev.length && prev[prev.length - 1].role === "model") {
                        const copy = [...prev];
                        copy[copy.length - 1] = msg;
                        return copy;
                    }
                    return [...prev, msg];
                });

                // When AI responds, the conversation is "updated", so reorder the list
                // We can simulate an updated conversation by updating its updated_at timestamp
                if (convos && streamConvId) {
                    const currentConv = convos.find(c => c.id === streamConvId);
                    if (currentConv) {
                        const updatedConv = {
                            ...currentConv,
                            updated_at: new Date().toISOString()
                        };
                        updateConversationInList(updatedConv);
                    }
                }
            },
            (update: ConversationUpdateMessage) => {
                // Handle conversation summary updates
                console.log(`Received conversation update for ${update.conversation_id}: ${update.summary}`);

                if (convos) {
                    const convToUpdate = convos.find(c => c.id === update.conversation_id);
                    if (convToUpdate) {
                        const updatedConv = {
                            ...convToUpdate,
                            summary: update.summary,
                            updated_at: update.updated_at
                        };
                        updateConversationInList(updatedConv);
                    }
                }
            },
            () => {
                setIsLoading(false);
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

    // ─── Delete conversation handler ────────────────────────────────────
    const handleDeleteConversation = (id: string) => {
        const wasActive = id === convId;
        deleteConversation(id).then(() => {
            // Remove the conversation from the list
            setConvos(prev => prev?.filter(c => c.id !== id) ?? []);
            // If the deleted one was active, always reset to welcome
            if (wasActive) {
                setConvId(null);
                setMsgs(WELCOME);
            }
        });
    };

    // ─── Update conversation and reorder list ────────────────────────────────
    const updateConversationInList = (updatedConv: ConversationRead) => {
        setConvos(prevConvos => {
            if (!prevConvos) return [updatedConv];
            const updatedList = prevConvos.map(conv =>
                conv.id === updatedConv.id ? updatedConv : conv
            );
            return sortConversationsByUpdatedAt(updatedList);
        });
    };

    // ─── 5) new‐conversation reset handler ────────────────────────
    const startNewConversation = () => {
        // Abort any existing stream when starting a new conversation
        if (abortRef.current) {
            abortRef.current();
            abortRef.current = null;
        }

        setIsLoading(false);
        setConvId(null);
        setMsgs(WELCOME);
    };

    // ─── Finally, JSX ────────────────────────────────────────
    return (
        <div className="fixed inset-x-0 top-[5rem] bottom-0 overflow-hidden">
            <SidebarProvider>
                <div className="relative w-full">
                    <div className="flex absolute justify-center inset-x-0 h-[calc(100vh-6rem)]">
                        <div className="shrink-0">
                            <ChatSidebar
                                convos={convos}
                                activeId={convId}
                                onSelectConversation={(id) => {
                                    // Abort any existing stream when switching conversations
                                    if (abortRef.current) {
                                        abortRef.current();
                                        abortRef.current = null;
                                    }

                                    // Clear loading state when switching conversations
                                    setIsLoading(false);

                                    // always update the active conversation id (possibly null)
                                    setConvId(id)

                                    // but only fetch messages if it's a real conversation
                                    if (id) {
                                        listMessages(id).then(setMsgs)
                                    }
                                }}
                                onDeleteConversation={handleDeleteConversation}
                            />
                        </div>
                        <div className="flex flex-col flex-1 min-h-0 max-w-[1200px]">
                            <div className="flex flex-row p-2 justify-between">
                                <div className="flex items-center gap-2 text-sm font-medium text-primary bg-transparent rounded hover:bg-accent hover:text-accent-foreground">
                                    <SidebarTrigger className="w-4 h-4" />
                                    History
                                </div>
                                <div className="flex gap-2 justify-center items-center">
                                    <ModelSelector
                                        selectedModel={selectedModelId}
                                        onModelChange={changeModel}
                                        showMetadata={true}
                                    />
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
                                    {isLoading && (
                                        <ChatBubble
                                            text=""
                                            isUser={false}
                                            isLoading={true}
                                        />
                                    )}
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

export default function GeneratePage() {
    return (
        <AuthGuard>
            <GenerateContent />
        </AuthGuard>
    );
}