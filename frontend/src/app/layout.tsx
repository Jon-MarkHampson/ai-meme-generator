// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from '@/context/AuthContext';
import { AuthGuard } from '@/components/AuthGuard';
import { NavBar } from "@/components/NavBar";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Meme Generator",
  description: "Interactively create memes powered by AI",
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

export function generateViewport() {
  return {
    viewport: "width=device-width, initial-scale=1",
  };
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
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
            <NavBar />
            <AuthGuard>
              <main>{children}</main>
            </AuthGuard>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
