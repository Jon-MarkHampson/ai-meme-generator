// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import Link from "next/link";
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/ui/mode-toggle"
import { AuthProvider } from '@/context/AuthContext'

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Meme Generator",
  description: "Interactively create memes powered by AI",
  viewport: "width=device-width, initial-scale=1",
  openGraph: {
    title: "AI Meme Generator",
    description: "Interactively create memes powered by AI",
    url: "https://yourdomain.com", // Replace with actual domain
    siteName: "AI Meme Generator",
    images: [
      {
        url: "/og-image.png", // Replace with actual image path
        width: 1200, // Replace with actual image width
        height: 630, // Replace with actual image height
        alt: "AI Meme Generator",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Meme Generator",
    description: "Interactively create memes powered by AI",
    images: ["/og-image.png"], // Replace with actual image path
  },
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <header className="
              sticky top-0 z-50
              bg-background/80 backdrop-blur-sm
              border-b border-border
              p-4 flex justify-between items-center
            "
            >
              <nav className="flex space-x-4">
                <Link href="/">Home</Link>
                <Link href="/chat">Meme Chat</Link>
                <Link href="/about">About</Link>
                <Link href="/contact">Contact</Link>
              </nav>
              <ModeToggle />
            </header>

            <main>{children}</main>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
