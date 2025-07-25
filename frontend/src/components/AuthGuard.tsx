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
    const hasShownLogoutSuccessRef = useRef(false);
    const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const toastIdRef = useRef<string | number | null>(null);
    const isRedirectingRef = useRef(false);

    const isPublic = isPublicRoute(pathname);

    // Extract URL parameters with stable values
    const sessionParam = searchParams.get('session');
    const authParam = searchParams.get('auth');
    const logoutParam = searchParams.get('logout');

    // Handle session expiry message from URL params
    useEffect(() => {
        console.log('🔍 [GUARD DEBUG] URL params - session:', sessionParam, 'auth:', authParam, 'logout:', logoutParam);

        // Only show session expired toast if it's from automatic expiry (not manual logout)
        if (sessionParam === 'expired' && !hasShownSessionExpiredRef.current) {
            console.log('⚠️ [GUARD DEBUG] Showing session expired toast');
            toast.warning('Your session has expired. Please log in again.');
            hasShownSessionExpiredRef.current = true;
        }

        if (authParam === 'required' && !logoutParam && !hasShownAuthRequiredRef.current) {
            console.log('🔐 [GUARD DEBUG] Showing auth required toast');
            toast.info('Authentication required. Please log in to continue.');
            hasShownAuthRequiredRef.current = true;
        }

        // Clean up the URL parameters
        if (sessionParam === 'expired' || authParam === 'required' || logoutParam === 'success') {
            console.log('🧹 [GUARD DEBUG] Cleaning up URL parameters');
            const url = new URL(window.location.href);
            url.searchParams.delete('session');
            url.searchParams.delete('auth');
            url.searchParams.delete('logout');
            window.history.replaceState({}, '', url.toString());
        }
    }, [sessionParam, authParam, logoutParam]);

    // Simple session monitoring using ACTUAL backend time
    useEffect(() => {
        console.log('⏱️ [GUARD DEBUG] Session monitoring - remaining:', sessionTimeRemaining, 'showWarning:', showSessionWarning);

        if (sessionTimeRemaining !== null && sessionTimeRemaining > 0) {
            // Start countdown when 90 seconds or less remaining (but don't show toast yet)
            if (sessionTimeRemaining <= 90 && !countdownIntervalRef.current) {
                console.log('🚨 [GUARD DEBUG] Starting countdown at', sessionTimeRemaining, 'seconds (≤90s threshold)');
                setLocalCountdown(sessionTimeRemaining);

                // Start local countdown timer
                console.log('⏰ [GUARD DEBUG] Starting local countdown interval');
                countdownIntervalRef.current = setInterval(() => {
                    setLocalCountdown(prev => {
                        if (prev === null || prev <= 1) {
                            if (prev === 1 && !isRedirectingRef.current) {
                                console.log('⚰️ [GUARD DEBUG] Local countdown reached 0 - preparing redirect');
                                isRedirectingRef.current = true;

                                // Clear timers before redirect
                                if (countdownIntervalRef.current) {
                                    clearInterval(countdownIntervalRef.current);
                                    countdownIntervalRef.current = null;
                                }
                                if (toastIdRef.current) {
                                    toast.dismiss(toastIdRef.current);
                                    toastIdRef.current = null;
                                }

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

            // Hide warning if session time increases significantly (user activity refreshed token)
            if (sessionTimeRemaining > 120 && (showSessionWarning || countdownIntervalRef.current)) {
                console.log('✨ [GUARD DEBUG] Session time increased >120s - hiding warning and clearing countdown');
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
            console.log('🛑 [GUARD DEBUG] No session time - clearing warning and countdown');
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
    }, [sessionTimeRemaining, showSessionWarning, router]);

    // Show toast when local countdown reaches 60 seconds
    useEffect(() => {
        if (localCountdown !== null && localCountdown <= 60 && localCountdown > 0 && !showSessionWarning) {
            console.log('🚨 [GUARD DEBUG] Local countdown reached 60s - showing toast');
            setShowSessionWarning(true);

            // Show initial toast
            toastIdRef.current = toast.warning(`Session expires in ${localCountdown} second${localCountdown !== 1 ? 's' : ''}`, {
                description: 'Your session will expire soon due to inactivity. Move your mouse or click to extend.',
                duration: Infinity,
            });
        }
    }, [localCountdown, showSessionWarning]);    // Update toast with local countdown
    useEffect(() => {
        if (showSessionWarning && localCountdown !== null && localCountdown > 0 && toastIdRef.current) {
            console.log('🔢 [GUARD DEBUG] Updating toast countdown:', localCountdown);
            const message = `Session expires in ${localCountdown} second${localCountdown !== 1 ? 's' : ''}`;

            toast.warning(message, {
                description: 'Your session will expire soon due to inactivity. Move your mouse or click to extend.',
                duration: Infinity,
                id: toastIdRef.current,
            });
        }
        else if (showSessionWarning && localCountdown === 0 && toastIdRef.current) {
            console.log('⚰️ [GUARD DEBUG] Local countdown reached 0 - dismissing toast');
            toast.dismiss(toastIdRef.current);
            toastIdRef.current = null;
            setShowSessionWarning(false);
        }
    }, [localCountdown, showSessionWarning]);

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
        if (!loading && !isRedirectingRef.current) {
            if (!isPublic && !user && !logoutParam) {
                router.replace('/?auth=required');
                return;
            }

            if (isPublic && user && pathname === '/') {
                router.replace('/generate');
                return;
            }
        }
    }, [isPublic, loading, user, router, pathname, logoutParam]);

    // Show loading state while checking auth
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    return (
        <>
            {children}
        </>
    );
}