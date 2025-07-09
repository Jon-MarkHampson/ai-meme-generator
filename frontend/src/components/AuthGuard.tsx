// AuthGuard.tsx
'use client';
import { PropsWithChildren, useEffect, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { PUBLIC_ROUTES } from '@/lib/authRoutes';

export function AuthGuard({ children }: PropsWithChildren) {
    const { user, loading, sessionTimeRemaining } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const [showSessionWarning, setShowSessionWarning] = useState(false);

    const isPublic = PUBLIC_ROUTES.includes(pathname as (typeof PUBLIC_ROUTES)[number]);

    // Handle session expiry message from URL params
    useEffect(() => {
        const sessionParam = searchParams.get('session');
        const authParam = searchParams.get('auth');

        if (sessionParam === 'expired') {
            // Show session expired notification
            console.log('Session has expired. Please log in again.');
            // You could show a toast notification here
        }

        if (authParam === 'required') {
            // Show authentication required message
            console.log('Authentication required. Please log in to continue.');
            // You could show a toast notification here
        }

        // Clean up the URL parameters
        if (sessionParam === 'expired' || authParam === 'required') {
            const url = new URL(window.location.href);
            url.searchParams.delete('session');
            url.searchParams.delete('auth');
            window.history.replaceState({}, '', url.toString());
        }
    }, [searchParams]);

    // Monitor session time remaining and show warnings
    useEffect(() => {
        if (sessionTimeRemaining !== null && sessionTimeRemaining > 0) {
            // Show warning when 5 minutes or less remaining
            if (sessionTimeRemaining <= 300 && !showSessionWarning) {
                setShowSessionWarning(true);
                console.warn(`Session expires in ${Math.floor(sessionTimeRemaining / 60)} minutes`);
                // You could show a toast notification here
            }

            // Hide warning if session time increases (user activity refreshed token)
            if (sessionTimeRemaining > 300 && showSessionWarning) {
                setShowSessionWarning(false);
            }
        } else {
            setShowSessionWarning(false);
        }
    }, [sessionTimeRemaining, showSessionWarning]);

    // Handle authentication redirects
    useEffect(() => {
        if (!loading) {
            if (!isPublic && !user) {
                // User needs to be authenticated but isn't
                // Note: This should rarely happen since middleware catches most cases
                router.replace('/?auth=required');
            } else if (isPublic && user && pathname === '/') {
                // User is authenticated and on public home page, redirect to app
                router.replace('/generate');
            }
        }
    }, [isPublic, loading, user, router, pathname]);

    // Show loading state while checking auth
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    // Show session warning if applicable
    if (showSessionWarning && user) {
        const minutesLeft = Math.floor((sessionTimeRemaining || 0) / 60);
        console.log(`Session warning: ${minutesLeft} minutes remaining`);
        // You could render a session warning banner here
    }

    return <>{children}</>;
}
