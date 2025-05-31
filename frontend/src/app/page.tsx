import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <h1 className="text-4xl font-bold text-gray-800 mb-4">
        Welcome to AI Meme Generator
      </h1>
      <p className="text-lg text-gray-600 mb-8">
        Create memes AI-powered, from the comfort of your browser.
      </p>
      <div className="space-x-4">
        <Link
          href="/signup"
          className="px-6 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg transition"
        >
          Sign Up
        </Link>
        <Link
          href="/login"
          className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
        >
          Log In
        </Link>
      </div>
    </main>
  )
}