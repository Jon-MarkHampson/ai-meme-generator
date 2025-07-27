'use client';

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getSession, apiRefreshSession, apiLogout, type User } from '@/lib/auth';
import { SESSION_TIMING, ACTIVITY_EVENTS } from '@/constants/sessionConfig';
import { showSessionWarning, updateSessionWarning, dismissSessionWarning } from '@/components/sessionToasts';
import { HOME_ROUTE } from '@/lib/authRoutes';

interface SessionState {
    user: User | null;
    isAuthenticated: boolean;
    isValidating: boolean;
}

interface SessionContextValue {
    state: SessionState;
    logout: () => Promise<void>;
    refreshSession: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<SessionState>({
        user: null,
        isAuthenticated: false,
        isValidating: true,
    });

    const router = useRouter();

    // Refs for timers
    const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);
    const warningTimerRef = useRef<NodeJS.Timeout | null>(null);
    const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
    const lastActivityRef = useRef<number>(Date.now());
    const warningToastIdRef = useRef<string | number | null>(null);

    // Logout function
    const logout = useCallback(async () => {
        try {
            await apiLogout();
        } catch (error) {
            console.error('Logout error:', error);
        }

        setState({ user: null, isAuthenticated: false, isValidating: false });
        router.push(HOME_ROUTE);
    }, [router]);

    // Refresh session
    const refreshSession = useCallback(async () => {
        if (!state.isAuthenticated) return;

        try {
            await apiRefreshSession();
            console.log('Session refreshed');
        } catch (error) {
            console.error('Failed to refresh session:', error);
            // If refresh fails, validate session status
            const user = await getSession();
            if (!user) {
                logout();
            }
        }
    }, [state.isAuthenticated, logout]);

    // Handle user activity
    const handleActivity = useCallback(() => {
        lastActivityRef.current = Date.now();

        // Clear existing timers
        if (inactivityTimerRef.current) {
            clearTimeout(inactivityTimerRef.current);
        }
        if (warningTimerRef.current) {
            clearInterval(warningTimerRef.current);
            warningTimerRef.current = null;
        }

        // Dismiss warning toast if active
        if (warningToastIdRef.current) {
            dismissSessionWarning(warningToastIdRef.current);
            warningToastIdRef.current = null;
        }

        // Reset inactivity timer
        if (state.isAuthenticated) {
            console.log('[Session] Activity detected, resetting timer');
            inactivityTimerRef.current = setTimeout(() => {
                console.log('[Session] Inactivity timeout reached, showing warning');
                // Start warning countdown
                let seconds = SESSION_TIMING.WARNING_DURATION / 1000;
                warningToastIdRef.current = showSessionWarning(seconds);

                warningTimerRef.current = setInterval(() => {
                    seconds--;
                    if (seconds > 0 && warningToastIdRef.current) {
                        updateSessionWarning(warningToastIdRef.current, seconds);
                    } else {
                        if (warningTimerRef.current) {
                            clearInterval(warningTimerRef.current);
                        }
                        console.log('[Session] Warning countdown finished, logging out');
                        logout();
                    }
                }, 1000);
            }, SESSION_TIMING.INACTIVITY_TIMEOUT);
        }
    }, [state.isAuthenticated, logout]);

    // Initial session validation
    useEffect(() => {
        const initializeSession = async () => {
            console.log('[Session] Initializing session check...');
            console.log('[Session] Current URL:', window.location.href);
            console.log('[Session] All cookies:', document.cookie);

            // Try multiple times to check for cookie (in case of timing issues)
            let attempts = 0;
            const maxAttempts = 5;

            const checkForCookie = async () => {
                attempts++;
                console.log(`[Session] Cookie check attempt ${attempts}/${maxAttempts}`);
                console.log('[Session] Cookies:', document.cookie);

                const cookies = document.cookie.split(';');
                const hasAuthCookie = cookies.some(cookie => {
                    const trimmed = cookie.trim();
                    console.log('[Session] Checking cookie:', trimmed);
                    return trimmed.startsWith('access_token=');
                });

                console.log('[Session] Has auth cookie:', hasAuthCookie);

                if (hasAuthCookie) {
                    // Cookie found! Stop checking and validate
                    console.log('[Session] Auth cookie found! Validating session...');

                    try {
                        const user = await getSession();
                        console.log('[Session] Session valid, user:', user);
                        setState({
                            user,
                            isAuthenticated: !!user,
                            isValidating: false,
                        });
                    } catch (error) {
                        console.error('[Session] Session validation error:', error);
                        setState({
                            user: null,
                            isAuthenticated: false,
                            isValidating: false,
                        });
                    }
                    return; // Important: exit the function after finding cookie
                }

                if (attempts < maxAttempts) {
                    // Try again in 200ms
                    setTimeout(checkForCookie, 200);
                    return;
                }

                // No cookie found after all attempts
                console.log('[Session] No auth cookie found after', attempts, 'attempts');
                setState({
                    user: null,
                    isAuthenticated: false,
                    isValidating: false,
                });
            };

            // Start checking
            checkForCookie();
        };

        // Add a small delay to ensure cookies are set after redirect
        setTimeout(initializeSession, 100);
    }, []);

    // Periodic session validation for external logouts
    useEffect(() => {
        if (!state.isAuthenticated) return;

        // Check session validity every 10 seconds
        const interval = setInterval(async () => {
            try {
                await getSession();
            } catch (error) {
                console.log('[Session] Session check failed, logging out');
                // Session invalid, reset state
                setState({
                    user: null,
                    isAuthenticated: false,
                    isValidating: false,
                });
                // Redirect to home
                router.push(HOME_ROUTE);
            }
        }, 10000); // Check every 10 seconds

        return () => clearInterval(interval);
    }, [state.isAuthenticated, router]);

    // Activity tracking
    useEffect(() => {
        if (!state.isAuthenticated) {
            console.log('[Session] Not authenticated, skipping activity tracking');
            return;
        }

        console.log('[Session] Setting up activity tracking');

        // Initial activity
        handleActivity();

        // Add event listeners
        const events = ACTIVITY_EVENTS;
        events.forEach(event => {
            document.addEventListener(event, handleActivity, { passive: true });
        });

        // Set up refresh interval
        refreshTimerRef.current = setInterval(refreshSession, SESSION_TIMING.REFRESH_INTERVAL);

        // Cleanup
        return () => {
            console.log('[Session] Cleaning up activity tracking');
            events.forEach(event => {
                document.removeEventListener(event, handleActivity);
            });

            if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
            if (warningTimerRef.current) clearInterval(warningTimerRef.current);
            if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
            if (warningToastIdRef.current) dismissSessionWarning(warningToastIdRef.current);
        };
    }, [state.isAuthenticated, handleActivity, refreshSession]);

    // Periodic session validation for external logouts
    useEffect(() => {
        if (!state.isAuthenticated) return;

        // Check session validity every 10 seconds
        const interval = setInterval(async () => {
            try {
                await getSession();
            } catch (error) {
                console.log('[Session] Session check failed, logging out');
                // Session invalid, reset state
                setState({
                    user: null,
                    isAuthenticated: false,
                    isValidating: false,
                });
                // Redirect to home
                router.push(HOME_ROUTE);
            }
        }, 10000); // Check every 10 seconds

        return () => clearInterval(interval);
    }, [state.isAuthenticated, router]);

    const value: SessionContextValue = {
        state,
        logout,
        refreshSession,
    };

    return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
    const context = useContext(SessionContext);
    if (!context) {
        throw new Error('useSession must be used within SessionProvider');
    }
    return context;
}