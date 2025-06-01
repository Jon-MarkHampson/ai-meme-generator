import Image from "next/image";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <>
    <main className="min-h-screen flex flex-col items-center justify-center px-4">
      <div>
        <h1 className="text-4xl font-bold">Welcome to the AI Meme Generator</h1>
        <p className="mt-4 text-center">Create your own memes using the power of AI!</p>
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
