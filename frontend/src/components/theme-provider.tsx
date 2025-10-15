"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider
      attribute="class"           // sets <html class="dark"> or "light"
      defaultTheme="system"       // respects user's system theme
      enableSystem={true}         // allows switching based on OS
      disableTransitionOnChange   // smoother theme switch
      {...props}                  // allow overrides if needed
    >
      {children}
    </NextThemesProvider>
  )
}