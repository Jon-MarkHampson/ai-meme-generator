import { FC, FormEvent, useState } from "react";
import { KeyboardEvent } from "react";
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export const ChatInput: FC<{ onSend: (msg: string) => Promise<void> }> = ({ onSend }) => {
    const [text, setText] = useState("");
    const submit = async (e?: FormEvent) => {
        e?.preventDefault();
        if (!text.trim()) return;
        await onSend(text);
        setText("");
    };
    // Catch Enter key to submit (Shift+Enter for new line)
    const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
        }
    };
    return (
        <form onSubmit={submit} className="relative">
            <Textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Type a message…"
                rows={3}
                className="w-full pr-24 resize-y"
            />
            <Button
                type="submit"
                className="absolute right-2 bottom-2 p-2 h-5 w-5 rounded-full text-primary bg-transparent hover:bg-primary/20 disabled:opacity-50 disabled:pointer-events-none"
            >
                <Send />
            </Button>
        </form>
    );
};