'use client'

import Link from 'next/link'
import { useSession } from '@/contexts/SessionContext'
import { ModeToggle } from '@/components/ui/mode-toggle'
import { useRouter } from 'next/navigation'

export function NavBar() {
    const { state, logout } = useSession()
    const router = useRouter()

    const handleLogout = async () => {
        await logout()
        router.push('/')
    }

    return (
        <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border p-4 flex justify-between items-center">
            <nav className="flex space-x-4">
                <Link href="/generate">Generate</Link>
                <Link href="/gallery">Gallery</Link>
                <Link href="/profile">Profile</Link>
                <Link href="/about">About</Link>
                <Link href="/support">Support</Link>
            </nav>

            <div className="flex items-center space-x-4">
                {state.isAuthenticated && state.user ? (
                    <>
                        <span className="text-sm text-muted-foreground">
                            {state.user.first_name} {state.user.last_name}
                        </span>
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