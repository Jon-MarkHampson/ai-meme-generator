// frontend/src/components/ChatBubble.tsx
import { FC } from "react";
import { Card, CardContent } from "@/components/ui/card";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const ChatBubble: FC<{ text: string; isUser: boolean }> = ({ text, isUser }) => (
    <div className={`flex px-4 ${isUser ? "justify-end" : "justify-start"}`}>
        <Card
            className={`max-w-[70%] p-2 ${isUser
                ? "bg-primary text-primary-foreground"
                : "bg-card text-card-foreground"
                }`}
        >
            <CardContent className="whitespace-pre-wrap break-words">
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                        a: ({ node, ...props }) => (
                            <a
                                {...props}
                                className="text-blue-600 dark:text-blue-400 font-medium hover:underline underline-offset-2 transition-colors"
                                target="_blank"
                                rel="noopener noreferrer"
                            />
                        ),
                    }}
                >
                    {text}
                </ReactMarkdown>
            </CardContent>
        </Card>
    </div>
);