// frontend/src/components/ChatBubble.tsx
import { FC } from "react";
import { Card, CardContent } from "@/components/ui/card";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FavoriteToggle } from "./FavoriteToggle";

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
                        a: ({ node, ...props }) => {
                            const href = props.href || "";
                            // Render images inline with rounded corners and favorite toggle
                            if (/\.(jpeg|jpg|gif|png|svg)$/.test(href)) {
                                return (
                                    <span className="relative inline-block">
                                        <img src={href} alt="" className="max-w-full rounded-lg" />
                                        <span className="absolute top-2 right-2">
                                            <FavoriteToggle imageUrl={href} />
                                        </span>
                                    </span>
                                );
                            }
                            return (
                                <a
                                    {...props}
                                    className="text-blue-600 dark:text-blue-400 font-medium hover:underline underline-offset-2 transition-colors"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                />
                            );
                        },
                        img: ({ node, ...props }) => (
                            <span className="relative inline-block">
                                <img
                                    {...props}
                                    alt={props.alt}
                                    className="max-w-full max-h-96 rounded-lg"
                                />
                                <span className="absolute top-2 right-2">
                                    <FavoriteToggle imageUrl={typeof props.src === 'string' ? props.src : ""} />
                                </span>
                            </span>
                        ),
                    }}
                >
                    {text}
                </ReactMarkdown>
            </CardContent>
        </Card>
    </div>
);