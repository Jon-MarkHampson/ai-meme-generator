// AuthGuard.tsx
'use client';
import { PropsWithChildren, useEffect, useState, useRef } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { isPublicRoute } from '@/lib/authRoutes';
import { toast } from 'sonner';

export function AuthGuard({ children }: PropsWithChildren) {
    const { user, loading, sessionTimeRemaining } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const [showSessionWarning, setShowSessionWarning] = useState(false);
    const [localCountdown, setLocalCountdown] = useState<number | null>(null);

    // Use refs to prevent infinite loops
    const hasShownSessionExpiredRef = useRef(false);
    const hasShownAuthRequiredRef = useRef(false);
    const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const toastIdRef = useRef<string | number | null>(null);

    const isPublic = isPublicRoute(pathname);

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
        // Always sync local countdown with backend value when it changes
        if (sessionTimeRemaining !== null && sessionTimeRemaining > 0) {
            setLocalCountdown(sessionTimeRemaining);
        }

        // Clean up existing interval when sessionTimeRemaining changes significantly
        // (e.g., when session is refreshed due to activity)
        if (countdownIntervalRef.current && sessionTimeRemaining !== null && sessionTimeRemaining > 120) {
            // Session was refreshed, clear countdown and warning
            clearInterval(countdownIntervalRef.current);
            countdownIntervalRef.current = null;
            setShowSessionWarning(false);
            setLocalCountdown(null);
            if (toastIdRef.current) {
                toast.dismiss(toastIdRef.current);
                toastIdRef.current = null;
            }
            return;
        }

        if (sessionTimeRemaining !== null && sessionTimeRemaining > 0) {
            // 5-minute sessions: Show warning when 1 minute or less remaining
            if (sessionTimeRemaining <= 61 && !showSessionWarning) {
                setShowSessionWarning(true);

                // Show initial toast
                toastIdRef.current = toast.warning(`Session expires in ${sessionTimeRemaining} second${sessionTimeRemaining !== 1 ? 's' : ''}`, {
                    description: 'Your session will expire soon due to inactivity. Move your mouse or click to extend.',
                    duration: Infinity,
                });

                // Start local countdown timer only if we don't already have one
                if (!countdownIntervalRef.current) {
                    countdownIntervalRef.current = setInterval(() => {
                        setLocalCountdown(prev => {
                            if (prev === null || prev <= 1) {
                                // When local countdown reaches 0, redirect to expired page
                                if (prev === 1) {
                                    setTimeout(() => {
                                        router.replace('/?session=expired');
                                    }, 100);
                                }
                                return 0;
                            }
                            return prev - 1;
                        });
                    }, 1000);
                }
            }

            // Hide warning if session time increases significantly (user activity refreshed token)
            if (sessionTimeRemaining > 120 && showSessionWarning) {
                setShowSessionWarning(false);
                setLocalCountdown(null);
                if (countdownIntervalRef.current) {
                    clearInterval(countdownIntervalRef.current);
                    countdownIntervalRef.current = null;
                }
                if (toastIdRef.current) {
                    toast.dismiss(toastIdRef.current);
                    toastIdRef.current = null;
                }
            }
        } else {
            setShowSessionWarning(false);
            setLocalCountdown(null);
            if (countdownIntervalRef.current) {
                clearInterval(countdownIntervalRef.current);
                countdownIntervalRef.current = null;
            }
            if (toastIdRef.current) {
                toast.dismiss(toastIdRef.current);
                toastIdRef.current = null;
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionTimeRemaining]); // Remove showSessionWarning and router from dependencies to prevent loops

    // Update toast with local countdown
    useEffect(() => {
        if (showSessionWarning && localCountdown !== null && localCountdown > 0 && toastIdRef.current) {
            // Use a more stable approach - only update if the message would actually change
            const message = `Session expires in ${localCountdown} second${localCountdown !== 1 ? 's' : ''}`;

            // Update the toast without creating a new one
            toast.warning(message, {
                description: 'Your session will expire soon due to inactivity. Move your mouse or click to extend.',
                duration: Infinity,
                id: toastIdRef.current,
            });
        }
        // If countdown reaches 0, dismiss the warning toast
        else if (showSessionWarning && localCountdown === 0 && toastIdRef.current) {
            toast.dismiss(toastIdRef.current);
            toastIdRef.current = null;
            setShowSessionWarning(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [localCountdown]); // Remove showSessionWarning from dependencies to prevent loops

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (countdownIntervalRef.current) {
                clearInterval(countdownIntervalRef.current);
            }
            if (toastIdRef.current) {
                toast.dismiss(toastIdRef.current);
            }
        };
    }, []);

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
