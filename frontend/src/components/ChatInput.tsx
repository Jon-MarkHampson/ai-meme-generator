import { FC, FormEvent, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export const ChatInput: FC<{ onSend: (msg: string) => Promise<void> }> = ({ onSend }) => {
    const [text, setText] = useState("");
    const submit = async (e: FormEvent) => {
        e.preventDefault();
        if (!text.trim()) return;
        await onSend(text);
        setText("");
    };
    return (
        <form onSubmit={submit} className="flex space-x-2">
            <Input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Type a message…"
            />
            <Button type="submit">Send</Button>
        </form>
    );
};