/**
 * Navigation bar component with authentication-aware rendering.
 * Uses Next.js 13+ 'use client' directive for client-side features.
 */
'use client'

import Link from 'next/link'
import { useSession } from '@/contexts/SessionContext'
import { ModeToggle } from '@/components/ui/mode-toggle'

export function NavBar() {
    // Access session state and logout function from context
    const { state, logout } = useSession()

    const handleLogout = async () => {
        // The logout function in SessionContext handles clearing cookies
        // and redirecting to login page
        await logout()
    }

    return (
        <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border p-4 flex justify-between items-center">
            <nav className="flex space-x-4">
                <Link href="/generate">Generate</Link>
                <Link href="/gallery">Gallery</Link>
                <Link href="/about">About</Link>
                <Link href="/support">Support</Link>
            </nav>

            <div className="flex items-center space-x-4">
                {state.isAuthenticated && state.user ? (
                    <>
                        <Link 
                            href="/profile" 
                            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                        >
                            {state.user.first_name} {state.user.last_name}
                        </Link>
                        <button
                            onClick={handleLogout}
                            className="text-sm text-destructive hover:text-destructive/80"
                        >
                            Logout
                        </button>
                    </>
                ) : (
                    <>
                        <Link href="/login" className="text-sm hover:text-foreground/80">
                            Log In
                        </Link>
                        <Link href="/signup" className="text-sm hover:text-foreground/80">
                            Sign Up
                        </Link>
                    </>
                )}
                <ModeToggle />
            </div>
        </header>
    )
}