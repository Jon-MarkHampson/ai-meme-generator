// AuthGuard.tsx
'use client';
import { PropsWithChildren, useEffect, useState, useRef } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { PUBLIC_ROUTES } from '@/lib/authRoutes';
import { toast } from 'sonner';

export function AuthGuard({ children }: PropsWithChildren) {
    const { user, loading, sessionTimeRemaining } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const [showSessionWarning, setShowSessionWarning] = useState(false);

    // Use refs to prevent infinite loops
    const hasShownSessionExpiredRef = useRef(false);
    const hasShownAuthRequiredRef = useRef(false);
    const hasShownLogoutSuccessRef = useRef(false);

    const isPublic = PUBLIC_ROUTES.includes(pathname as (typeof PUBLIC_ROUTES)[number]);

    // Extract URL parameters with stable values
    const sessionParam = searchParams.get('session');
    const authParam = searchParams.get('auth');
    const logoutParam = searchParams.get('logout');

    // Handle session expiry message from URL params
    useEffect(() => {
        // Only show session expired toast if it's from automatic expiry (not manual logout)
        if (sessionParam === 'expired' && !hasShownSessionExpiredRef.current) {
            // Show session expired notification
            toast.warning('Your session has expired. Please log in again.');
            hasShownSessionExpiredRef.current = true;
        }

        if (authParam === 'required' && !logoutParam && !hasShownAuthRequiredRef.current) {
            // Show authentication required message only if not a manual logout
            toast.info('Authentication required. Please log in to continue.');
            hasShownAuthRequiredRef.current = true;
        }

        // Clean up the URL parameters
        if (sessionParam === 'expired' || authParam === 'required' || logoutParam === 'success') {
            const url = new URL(window.location.href);
            url.searchParams.delete('session');
            url.searchParams.delete('auth');
            url.searchParams.delete('logout');
            window.history.replaceState({}, '', url.toString());
        }
    }, [sessionParam, authParam, logoutParam]);

    // Monitor session time remaining and show warnings
    useEffect(() => {
        if (sessionTimeRemaining !== null && sessionTimeRemaining > 0) {
            // 5-minute sessions: Show warning when 1 minute or less remaining
            if (sessionTimeRemaining <= 60 && !showSessionWarning) {
                setShowSessionWarning(true);
                const secondsLeft = sessionTimeRemaining;

                toast.warning(`Session expires in ${secondsLeft} second${secondsLeft !== 1 ? 's' : ''}`, {
                    description: 'Your session will expire soon due to inactivity. Move your mouse or click to extend.',
                    duration: 10000,
                });
            }

            // Hide warning if session time increases (user activity refreshed token)
            if (sessionTimeRemaining > 60 && showSessionWarning) {
                setShowSessionWarning(false);
            }
        } else {
            setShowSessionWarning(false);
        }
    }, [sessionTimeRemaining, showSessionWarning]);

    // Handle authentication redirects
    useEffect(() => {
        if (!loading) {
            if (!isPublic && !user && !logoutParam) {
                // User needs to be authenticated but isn't (and it's not from manual logout)
                // This catches cases where middleware or other checks missed the expiry
                router.replace('/?auth=required');
                return;
            }

            if (isPublic && user && pathname === '/') {
                // User is authenticated and on public home page, redirect to app
                router.replace('/generate');
                return;
            }

            // Additional check: if user was logged in but session expired
            if (!isPublic && user && sessionTimeRemaining !== null && sessionTimeRemaining <= 0) {
                // Session has expired but user state hasn't been cleared yet
                console.warn('AuthGuard detected expired session, redirecting...');
                router.replace('/?session=expired');
            }
        }
    }, [isPublic, loading, user, router, pathname, sessionTimeRemaining, logoutParam]);

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
        // Session warning toast is already shown in the useEffect above
        // This block can be used for additional UI elements if needed
    }

    return (
        <>
            {children}
        </>
    );
}
