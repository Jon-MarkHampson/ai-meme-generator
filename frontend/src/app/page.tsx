// frontend/src/app/page.tsx
import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <>
      <main className="min-h-screen flex flex-col items-center justify-center px-4">
        <div>
          <h1 className="text-4xl font-bold text-center">Welcome to the AI Meme Generator</h1>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-400">Create your own memes using the power of AI!</p>
        </div>
        <div className="mt-8 flex space-x-4">
          <Button variant="secondary" asChild>
            <Link href="/signup">Sign Up</Link>
          </Button>
          <Button asChild>
            <Link href="/login">Login</Link>
          </Button>
        </div>
      </main>
    </>
  );
}
