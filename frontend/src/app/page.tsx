// frontend/src/app/page.tsx
"use client";

import Link from "next/link";
import { useSession } from "@/contexts/SessionContext";
import { Button } from "@/components/ui/button";

export default function Home() {
  const { state } = useSession();

  return (
    <>
      <main className="min-h-screen flex flex-col items-center justify-center px-4">
        <div>
          <h1 className="text-4xl font-bold text-center">Welcome to the AI Meme Generator</h1>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-400">Create your own memes using the power of AI!</p>
        </div>
        
        {/* Show auth buttons only for unauthenticated users */}
        {!state.isValidating && !state.isAuthenticated && (
          <div className="mt-8 flex space-x-4">
            <Button variant="secondary" asChild>
              <Link href="/signup">Sign Up</Link>
            </Button>
            <Button asChild>
              <Link href="/login">Login</Link>
            </Button>
          </div>
        )}

        {/* Show get started button for authenticated users */}
        {state.isAuthenticated && (
          <div className="mt-8 flex space-x-4">
            <Button asChild>
              <Link href="/generate">Start Creating</Link>
            </Button>
            <Button variant="secondary" asChild>
              <Link href="/gallery">View Gallery</Link>
            </Button>
          </div>
        )}
      </main>
    </>
  );
}
