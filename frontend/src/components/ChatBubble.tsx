// frontend/src/components/ChatBubble.tsx
import { FC } from "react";
import { Card, CardContent } from "@/components/ui/card";

export const ChatBubble: FC<{ text: string; isUser: boolean }> = ({ text, isUser }) => (
    <div className={`flex px-4 ${isUser ? "justify-end" : "justify-start"}`}>
        <Card
            className={`max-w-xs p-2 ${isUser
                ? "bg-primary text-primary-foreground"
                : "bg-card text-card-foreground"
                }`}
        >
            <CardContent className="whitespace-pre-wrap break-words">
                {text}
            </CardContent>
        </Card>
    </div>
);