/**
 * Chat bubble component for displaying user and AI messages.
 * Supports markdown rendering with security measures.
 */
import { FC } from "react";
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FavoriteToggle } from "./FavoriteToggle";

/**
 * Sanitize URLs to prevent XSS (Cross-Site Scripting) attacks.
 * Only allows http and https protocols, blocking potentially dangerous
 * protocols like javascript:, data:, or file:
 * 
 * @param url - The URL string to sanitize
 * @returns Safe URL or null if unsafe/invalid
 */
function sanitizeUrl(url: string): string | null {
  if (!url || typeof url !== 'string') return null;
  
  try {
    const parsed = new URL(url);
    // Whitelist approach: only allow safe protocols
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return null;
    }
    return url;
  } catch {
    // Invalid URLs are rejected for safety
    return null;
  }
}

/**
 * Check if a URL points to an image file based on extension.
 * Supports common web image formats including query parameters.
 * 
 * @param url - The URL to check
 * @returns true if URL ends with image extension
 */
function isImageUrl(url: string): boolean {
  if (!url) return false;
  // Regex matches image extensions, ignoring query parameters
  return /\.(jpeg|jpg|gif|png|svg|webp)(\?[^]*)?$/i.test(url);
}

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
                                const sanitizedUrl = sanitizeUrl(href);
                                
                                // Don't render if URL is not safe
                                if (!sanitizedUrl) {
                                    return <span className="text-red-500">[Invalid URL]</span>;
                                }
                                
                                // Render images inline with rounded corners and favorite toggle
                                if (isImageUrl(sanitizedUrl)) {
                                    return (
                                        <span className="relative inline-block">
                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img 
                                                src={sanitizedUrl} 
                                                alt="Generated meme" 
                                                className="max-w-full rounded-lg" 
                                                loading="lazy"
                                            />
                                            <span className="absolute top-2 right-2">
                                                <FavoriteToggle imageUrl={sanitizedUrl} />
                                            </span>
                                        </span>
                                    );
                                }
                                return (
                                    <a
                                        {...props}
                                        href={sanitizedUrl}
                                        className="text-blue-600 dark:text-blue-400 font-medium hover:underline underline-offset-2 transition-colors"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    />
                                );
                            },
                            img: ({ ...props }) => {
                                const src = typeof props.src === 'string' ? props.src : "";
                                const sanitizedUrl = sanitizeUrl(src);
                                
                                // Don't render if URL is not safe
                                if (!sanitizedUrl) {
                                    return <span className="text-red-500">[Invalid image URL]</span>;
                                }
                                
                                return (
                                    <span className="relative inline-block">
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img
                                            {...props}
                                            src={sanitizedUrl}
                                            alt={props.alt || "Generated meme"}
                                            className="max-w-full max-h-96 rounded-lg"
                                            loading="lazy"
                                        />
                                        <span className="absolute top-2 right-2">
                                            <FavoriteToggle imageUrl={sanitizedUrl} />
                                        </span>
                                    </span>
                                );
                            },
                        }}
                    >
                        {text}
                    </ReactMarkdown>
                )}
            </CardContent>
        </Card>
    </div>
);