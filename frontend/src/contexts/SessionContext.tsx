/**
 * Session management context with sophisticated timer-based authentication.
 * 
 * Provides centralized session state management with:
 * - Multi-timer system (inactivity, warning, refresh)
 * - Activity tracking across user interactions
 * - Automatic token refresh for active users
 * - Cross-tab session synchronization
 * - Race condition prevention
 */
'use client';

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getSession, apiRefreshSession, apiLogout, getSessionStatus } from '@/services/auth';
import { type User } from '@/types/auth';
import { SESSION_TIMING, ACTIVITY_EVENTS } from '@/constants/sessionConfig';
import { showSessionWarning, updateSessionWarning, dismissSessionWarning } from '@/utils/sessionToasts';
import { HOME_ROUTE } from '@/config/routes';

interface SessionState {
    user: User | null;          // Current authenticated user data
    isAuthenticated: boolean;   // Whether user has valid session
    isValidating: boolean;      // Whether session validation is in progress
}

interface SessionContextValue {
    state: SessionState;
    logout: () => Promise<void>;           // Clear session and redirect to home
    refreshSession: () => Promise<void>;   // Refresh authentication token
    revalidateSession: () => Promise<void>; // Validate current session with backend
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<SessionState>({
        user: null,
        isAuthenticated: false,
        isValidating: true,
    });

    const router = useRouter();
    const [isInitialized, setIsInitialized] = useState(false);

    // Timer management for session lifecycle
    const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);  // Main inactivity countdown
    const warningTimerRef = useRef<NodeJS.Timeout | null>(null);     // Warning period timer
    const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);     // Auto-refresh timer
    const lastActivityRef = useRef<number>(Date.now());              // Last user activity timestamp
    const warningToastIdRef = useRef<string | number | null>(null);   // Active warning toast ID
    const sessionStatusIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const logout = useCallback(async () => {
        /**
         * Logout function that clears session and redirects to home.
         *
         * Process:
         * 1. Call backend logout API to clear server-side session
         * 2. Clear local session state
         * 3. Clear all timers
         * 4. Dismiss any warning toasts
         * 5. Redirect to home page
         *
         * Uses window.location.href for redirect to ensure it works even in background tabs.
         * router.push() doesn't work reliably when the tab is not visible.
         */
        try {
            await apiLogout();
        } catch (error) {
            console.error('Logout error:', error);
        }

        setState({ user: null, isAuthenticated: false, isValidating: false });

        // Use window.location.href instead of router.push() for reliable redirect
        // even when tab is in background
        window.location.href = HOME_ROUTE;
    }, []);

    // Track refresh attempts to prevent race conditions
    const refreshInProgressRef = useRef<boolean>(false);

    // Refresh session
    const refreshSession = useCallback(async () => {
        if (!state.isAuthenticated) return;

        // Prevent concurrent refresh attempts
        if (refreshInProgressRef.current) {
            console.log('[Session] Refresh already in progress, skipping');
            return;
        }

        // Don't try to refresh if we're already showing warning (session about to expire)
        if (warningToastIdRef.current) {
            console.log('[Session] Skipping refresh - warning already shown, session expiring soon');
            return;
        }

        refreshInProgressRef.current = true;

        try {
            await apiRefreshSession();
            console.log('[Session] Token refreshed successfully');
        } catch (error) {
            // Handle 401 gracefully - token already expired
            const axiosError = error as { response?: { status?: number } };
            if (axiosError.response?.status === 401) {
                console.log('[Session] Token expired during refresh, logging out gracefully');
            } else {
                console.error('[Session] Failed to refresh token:', error);
            }
            // If refresh fails, logout user
            logout();
        } finally {
            refreshInProgressRef.current = false;
        }
    }, [state.isAuthenticated, logout]);

    // Track whether user is authenticated (for activity handler)
    const isAuthenticatedRef = useRef(state.isAuthenticated);

    useEffect(() => {
        isAuthenticatedRef.current = state.isAuthenticated;
    }, [state.isAuthenticated]);

    // Handle user activity - just reset timers, don't recreate them
    // Use useCallback WITHOUT dependencies so event listeners stay stable
    const handleActivity = useCallback(() => {
        // Only process activity if authenticated
        if (!isAuthenticatedRef.current) return;

        lastActivityRef.current = Date.now();

        // Clear existing timers
        if (inactivityTimerRef.current) {
            clearTimeout(inactivityTimerRef.current);
            inactivityTimerRef.current = null;
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
        inactivityTimerRef.current = setTimeout(() => {
            console.log('[Session] Inactivity detected, showing session warning');

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
                        warningTimerRef.current = null;
                    }
                    console.log('[Session] Session expired due to inactivity');
                    logout();
                }
            }, 1000);
        }, SESSION_TIMING.INACTIVITY_TIMEOUT);
    }, [logout]); // Only depend on logout, which is stable

    // Revalidate session function for manual refresh
    const revalidateSession = useCallback(async () => {
        console.log('[Session] Manually revalidating session...');
        try {
            const user = await getSession();
            console.log('[Session] Revalidation result:', user);

            setState({
                user,
                isAuthenticated: !!user,
                isValidating: false,
            });
        } catch (error) {
            console.error('[Session] Revalidation error:', error);
            setState({
                user: null,
                isAuthenticated: false,
                isValidating: false,
            });
        }
    }, []);

    // Initial session validation
    useEffect(() => {
        if (isInitialized) return;

        const initializeSession = async () => {
            console.log('[Session] Initializing session validation...');

            try {
                const user = await getSession();
                setState({
                    user,
                    isAuthenticated: !!user,
                    isValidating: false,
                });
                console.log('[Session] Session initialized -', user ? `authenticated as ${user.email}` : 'not authenticated');
            } catch (error) {
                console.error('[Session] Session validation failed:', error);
                setState({
                    user: null,
                    isAuthenticated: false,
                    isValidating: false,
                });
            }
            setIsInitialized(true);
        };

        // Add a small delay to ensure cookies are set after redirect
        setTimeout(initializeSession, 100);
    }, [isInitialized]);

    // Listen for session expiry events from API interceptor
    useEffect(() => {
        const handleSessionExpired = () => {
            console.log('[Session] Received session-expired event, logging out');
            logout();
        };

        window.addEventListener('session-expired', handleSessionExpired);
        return () => window.removeEventListener('session-expired', handleSessionExpired);
    }, [logout]);

    // Handle page visibility changes - check session when tab becomes visible
    useEffect(() => {
        if (!state.isAuthenticated) return;

        const handleVisibilityChange = async () => {
            // Only check when page becomes visible
            if (document.visibilityState === 'visible') {
                console.log('[Session] Tab became visible, checking session status');

                try {
                    const status = await getSessionStatus();
                    if (status && status.time_remaining <= 0) {
                        console.log('[Session] Session expired while tab was hidden, logging out');
                        logout();
                    } else {
                        console.log('[Session] Session still valid after tab became visible');
                    }
                } catch (err) {
                    console.error('[Session] Failed to check session status on visibility change:', err);
                    // On error (likely 401), logout
                    logout();
                }
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [state.isAuthenticated, logout]);

    // Activity tracking
    useEffect(() => {
        if (!state.isAuthenticated) {
            return;
        }

        console.log('[Session] Setting up activity tracking and session timers');

        // Set up inactivity timer
        inactivityTimerRef.current = setTimeout(() => {
            console.log('[Session] Inactivity detected, showing session warning');

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
                        warningTimerRef.current = null;
                    }
                    console.log('[Session] Session expired due to inactivity');
                    logout();
                }
            }, 1000);
        }, SESSION_TIMING.INACTIVITY_TIMEOUT);

        // Add event listeners for user activity
        const events = ACTIVITY_EVENTS;
        events.forEach(event => {
            document.addEventListener(event, handleActivity, { passive: true });
        });

        // Set up refresh interval (only for active users)
        refreshTimerRef.current = setInterval(() => {
            // Only refresh if user is not in warning state (still active)
            if (!warningToastIdRef.current) {
                refreshSession();
            }
        }, SESSION_TIMING.REFRESH_INTERVAL);

        // Poll backend for session status
        sessionStatusIntervalRef.current = setInterval(async () => {
            try {
                const status = await getSessionStatus();
                if (status && status.time_remaining <= 0) {
                    console.log('[Session] Token expired on backend, logging out');
                    logout();
                }
            } catch (err) {
                console.error('[Session] Failed to fetch session status:', err);
            }
        }, 30000); // poll every 30 seconds

        // Cleanup
        return () => {
            events.forEach(event => {
                document.removeEventListener(event, handleActivity);
            });

            // Clear all timers and reset refs
            if (inactivityTimerRef.current) {
                clearTimeout(inactivityTimerRef.current);
                inactivityTimerRef.current = null;
            }
            if (warningTimerRef.current) {
                clearInterval(warningTimerRef.current);
                warningTimerRef.current = null;
            }
            if (refreshTimerRef.current) {
                clearInterval(refreshTimerRef.current);
                refreshTimerRef.current = null;
            }
            if (sessionStatusIntervalRef.current) {
                clearInterval(sessionStatusIntervalRef.current);
                sessionStatusIntervalRef.current = null;
            }
            if (warningToastIdRef.current) {
                dismissSessionWarning(warningToastIdRef.current);
                warningToastIdRef.current = null;
            }
            // Reset refresh flag on cleanup
            refreshInProgressRef.current = false;
        };
    }, [state.isAuthenticated, handleActivity, refreshSession, logout]);

    const value: SessionContextValue = {
        state,
        logout,
        refreshSession,
        revalidateSession,
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