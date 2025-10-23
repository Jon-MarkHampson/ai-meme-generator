/**
 * AI Meme Generation Chat Interface
 * 
 * This component provides a conversational interface for creating AI-generated memes.
 * Features include real-time streaming responses, conversation history management,
 * model selection, and persistent conversation storage.
 * 
 * Key features:
 * - Real-time streaming AI responses with Server-Sent Events
 * - Conversation sidebar with history and search
 * - Dynamic model selection (OpenAI, Anthropic)
 * - Automatic conversation creation and management
 * - Stream cancellation and error handling
 * - Responsive chat interface with loading states
 * 
 * Technical implementation:
 * - Uses streaming fetch API for real-time updates
 * - Implements abort controllers for stream cancellation
 * - Manages conversation state with React hooks
 * - Handles race conditions in async operations
 * - Provides optimistic UI updates for better UX
 */
"use client";
import { useEffect, useState, useRef } from "react";
import { useSession } from "@/contexts/SessionContext";
import { AuthGuard } from "@/components/AuthGuard";
import { ConversationRead, ChatMessage } from "@/types/conversations";
import {
    createConversation,
    streamChat,
    listMessages,
    listConversations,
    deleteConversation,
    sortConversationsByUpdatedAt,
} from "@/services/generate";
import { SquarePen } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ChatBubble } from "@/components/ChatBubble";
import { ChatInput } from "@/components/ChatInput";
import { AgentSelector } from "@/components/AgentSelector";
import { ImageAgentSelector } from "@/components/ImageAgentSelector";
import { useModelSelection } from "@/hooks/useModelSelection";
import { useConversationSummary } from "@/hooks/useConversationSummary";
import { getDefaultImageModel } from "@/services/models";


// Welcome message displayed when starting a new conversation
const WELCOME: ChatMessage[] = [
    {
        role: "model",
        content:
            "👋 Hey there! Let's make some memes! \nDo you have an idea, shall we brainstorm, search the web or shall I surprise you?",
        timestamp: new Date().toISOString(),
    },
];

/**
 * Main chat interface component handling AI meme generation.
 * 
 * Manages conversation state, streaming responses, and user interactions.
 * Protected by AuthGuard to ensure only authenticated users can access.
 */
function GenerateContent() {
    const { } = useSession();

    // Component state management
    // Active conversation state
    const [convId, setConvId] = useState<string | null>(null);
    const [msgs, setMsgs] = useState<ChatMessage[]>(WELCOME);
    const [convos, setConvos] = useState<ConversationRead[] | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // AI manager/orchestrator model selection with persistent preference
    const { selectedModelId, changeModel } = useModelSelection({
        onModelChange: (model) => {
            console.log(`Manager model changed to: ${model.name} (${model.id})`);
        }
    });

    // Image generation model selection with persistent preference (separate from manager)
    const { selectedModelId: selectedImageModelId, changeModel: changeImageModel } = useModelSelection({
        storageKey: 'selectedImageModel',
        getDefaultModel: () => getDefaultImageModel(),
        onModelChange: (model) => {
            console.log(`Image model changed to: ${model.name} (${model.id})`);
        }
    });

    // Refs for stream management and auto-scrolling
    const abortRef = useRef<(() => void) | null>(null);
    const endRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [msgs]);

    // Load conversation history on component mount
    useEffect(() => {
        listConversations()
            .then((data) => {
                console.log("Conversations loaded:", data);
                setConvos(data);
            })
            .catch((error) => {
                console.error("Failed to load conversations:", error);
                setConvos([]);
            });
    }, []);

    // Load message history when conversation changes
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

    // Reset to welcome screen when no conversation selected
    useEffect(() => {
        if (convId === null) {
            setMsgs(WELCOME);
        }
    }, [convId]);

    /**
     * Handle user message submission and AI response streaming.
     * 
     * Creates conversation if needed, streams AI response in real-time,
     * and manages conversation state updates.
     */
    const handleSend = async (text: string) => {
        // Add user message to chat immediately for responsive UI
        setMsgs((prev) => [
            ...prev,
            { role: "user", content: text, timestamp: new Date().toISOString() },
        ]);

        // Show loading state while AI processes request
        setIsLoading(true);

        // Create new conversation if this is the first message
        let id = convId;
        if (!id) {
            try {
                const conv = await createConversation();
                id = conv.id;
                setConvId(id);
                // Add new conversation to sidebar and sort by recency
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

        // Cancel any existing stream to prevent conflicts
        if (abortRef.current) {
            abortRef.current();
        }

        // Start streaming AI response
        abortRef.current = streamChat(
            id,
            selectedModelId,        // Manager/orchestrator model
            selectedImageModelId,   // Image generation model
            text,
            (msg: ChatMessage, streamConvId: string) => {
                // Prevent race conditions by validating stream source
                if (streamConvId !== id) {
                    console.log(`Ignoring message from conversation ${streamConvId}, current is ${id}`);
                    return;
                }

                if (msg.role !== "model") return;

                // Hide loading indicator once AI starts responding
                setIsLoading(false);

                // Update or append AI message (streaming updates existing message)
                setMsgs((prev) => {
                    if (prev.length && prev[prev.length - 1].role === "model") {
                        // Update existing message with new content
                        const copy = [...prev];
                        copy[copy.length - 1] = msg;
                        return copy;
                    }
                    // Add new AI message
                    return [...prev, msg];
                });

                // Update conversation timestamp to reorder sidebar
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
            () => {
                // Handle stream errors gracefully
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

    /**
     * Delete a conversation and handle UI state cleanup.
     * Resets to welcome screen if deleting the active conversation.
     */
    const handleDeleteConversation = (id: string) => {
        const wasActive = id === convId;
        deleteConversation(id).then(() => {
            // Remove conversation from sidebar
            setConvos(prev => prev?.filter(c => c.id !== id) ?? []);
            // Reset to welcome if deleting active conversation
            if (wasActive) {
                setConvId(null);
                setMsgs(WELCOME);
            }
        });
    };

    /**
     * Update conversation metadata and reorder by recency.
     * Used for real-time summary updates and timestamp changes.
     */
    const updateConversationInList = (updatedConv: ConversationRead) => {
        setConvos(prevConvos => {
            if (!prevConvos) return [updatedConv];
            // Replace conversation and sort by most recent activity
            const updatedList = prevConvos.map(conv =>
                conv.id === updatedConv.id ? updatedConv : conv
            );
            return sortConversationsByUpdatedAt(updatedList);
        });
    };

    // Poll for conversation summary until available (only when convId exists)
    useConversationSummary(convId || "", (updatedConv) => {
        updateConversationInList(updatedConv);
    });

    // ─── New‐conversation reset handler ────────────────────────
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
                                    <AgentSelector
                                        selectedModel={selectedModelId}
                                        onModelChange={changeModel}
                                        showMetadata={true}
                                    />
                                </div>
                                <div className="flex gap-2 justify-center items-center">
                                    <ImageAgentSelector
                                        selectedModel={selectedImageModelId}
                                        onModelChange={changeImageModel}
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

/**
 * Protected page component that wraps the chat interface with authentication.
 * Redirects unauthenticated users to login page.
 */
export default function GeneratePage() {
    return (
        <AuthGuard>
            <GenerateContent />
        </AuthGuard>
    );
}