// frontend/src/components/ChatBubble.tsx
import { FC } from "react";
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FavoriteToggle } from "./FavoriteToggle";

export const ChatBubble: FC<{ text: string; isUser: boolean; isLoading?: boolean }> = ({ text, isUser, isLoading = false }) => (
    <div className={`flex px-4 ${isUser ? "justify-end" : "justify-start"}`}>
        <Card
            className={`max-w-[70%] p-2 ${isUser
                ? "bg-primary text-primary-foreground"
                : "bg-card text-card-foreground"
                }`}
        >
            <CardContent className="whitespace-pre-wrap break-words">
                {!isUser && isLoading ? (
                    <div className="flex flex-col space-y-3">
                        <Skeleton className="h-4 w-[280px]" />
                        <div className="relative">
                            <Skeleton className="h-[80px] w-[300px] rounded-xl" />
                            {/* <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-sm text-muted-foreground font-medium">Generating...</span>
                            </div> */}
                        </div>
                        <div className="space-y-2">
                            <Skeleton className="h-4 w-[240px]" />
                            <Skeleton className="h-4 w-[200px]" />
                        </div>
                    </div>
                ) : (
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            a: ({ ...props }) => {
                                const href = props.href || "";
                                // Render images inline with rounded corners and favorite toggle
                                if (/\.(jpeg|jpg|gif|png|svg)$/.test(href)) {
                                    return (
                                        <span className="relative inline-block">
                                            {/* eslint-disable-next-line @next/next/no-img-element */}
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
                            img: ({ ...props }) => (
                                <span className="relative inline-block">
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
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
                )}
            </CardContent>
        </Card>
    </div>
);