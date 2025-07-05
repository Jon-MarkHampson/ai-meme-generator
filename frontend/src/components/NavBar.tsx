// frontend/src/components/NavBar.tsx
'use client'

import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { ModeToggle } from '@/components/ui/mode-toggle'

export function NavBar() {
    const { user, logout } = useAuth()

    return (
        <header
            className="
        sticky top-0 z-50
        bg-background/80 backdrop-blur-sm
        border-b border-border
        p-4 flex justify-between items-center
      "
        >
            <nav className="flex space-x-4">
                <Link href="/generate">Generate</Link>
                <Link href="/gallery">Gallery</Link>
                <Link href="/profile">Profile</Link>
                <Link href="/about">About</Link>
                <Link href="/support">Support</Link>
            </nav>

            <div className="flex items-center space-x-4">
                {user ? (
                    <button
                        onClick={logout}
                        className="text-sm text-destructive"
                    >
                        Logout
                    </button>
                ) : (
                    <>
                        <Link href="/login" className="text-sm">
                            Log In
                        </Link>
                        <Link href="/signup" className="text-sm">
                            Sign Up
                        </Link>
                    </>
                )}
                <ModeToggle />
            </div>
        </header>
    )
}