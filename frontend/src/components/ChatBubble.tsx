import { FC } from "react";
import { Card, CardContent } from "@/components/ui/card";

export const ChatBubble: FC<{ text: string; isUser: boolean }> = ({ text, isUser }) => (
    <Card className={`${isUser ? "self-end bg-blue-50" : "self-start bg-gray-50"} max-w-xs`}>
        <CardContent className="whitespace-pre-wrap">{text}</CardContent>
    </Card>
);