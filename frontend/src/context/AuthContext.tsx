'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext, useCallback } from 'react'
import { apiLogin, apiLogout, apiSignup, fetchProfile, User, apiUpdateProfile, apiRefreshSession, getSessionStatus } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { isPublicRoute } from '@/lib/authRoutes'
import { toast } from 'sonner';

// Mutable reference that can be used outside React (e.g. axios interceptor)
let setUserRef: React.Dispatch<React.SetStateAction<User | null>> | null = null;
let setIsLoggingOutRef: React.Dispatch<React.SetStateAction<boolean>> | null = null;

/** Clears user state without navigation—handy for 401 interceptors */
export function logoutSilently() {
  setIsLoggingOutRef?.(true); // Prevent session expiry toasts
  setUserRef?.(null);
  // Note: We don't reset setIsLoggingOutRef here because the session expiry 
  // redirect will handle the final cleanup
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (firstName: string, lastName: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (payload: {
    currentPassword: string
    firstName?: string
    lastName?: string
    email?: string
    password?: string
  }) => Promise<void>
  sessionTimeRemaining: number | null
}

export const AuthContext = createContext<AuthContextType>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [sessionTimeRemaining, setSessionTimeRemaining] = useState<number | null>(null)
  const [hasRecentActivity, setHasRecentActivity] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false) // Track manual logout
  const [sessionExpired, setSessionExpired] = useState(false) // Track session expiry
  const router = useRouter()

  // expose the state setters to logoutSilently()
  setUserRef = setUser;
  setIsLoggingOutRef = setIsLoggingOut;

  // Function to check token expiry using backend endpoint
  const checkTokenExpiry = useCallback(async () => {
    try {
      const sessionStatus = await getSessionStatus();
      const remaining = sessionStatus?.time_remaining ?? 0;
      setSessionTimeRemaining(remaining);

      // 5-minute sessions: Refresh when less than 1 minute remaining and user is active
      if (remaining < 60 && remaining > 30 && hasRecentActivity) {
        // Refresh when less than 1 minute remaining, more than 30 seconds left, and user is active
        console.warn(`Session expires in ${remaining} seconds - refreshing due to user activity`);
        refreshSession();
      } else if (remaining < 60 && remaining > 30 && !hasRecentActivity) {
        console.log(`Session expires in ${remaining} seconds but no recent activity - letting it expire naturally`);
      } else if (remaining <= 60 && remaining > 0) {
        console.log(`Session expires in ${remaining} seconds, activity: ${hasRecentActivity}`);
      }
    } catch (error) {
      console.log('DEBUG: Error checking session status:', error);
      setSessionTimeRemaining(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasRecentActivity]);

  // Function to refresh session by making an authenticated API call
  const refreshSession = useCallback(async () => {
    try {
      // Call the dedicated refresh endpoint
      console.trace('DEBUG: refreshSession() called from:');
      await apiRefreshSession();
      console.log('Session refreshed successfully');

      // Recheck token expiry after refresh
      setTimeout(() => {
        checkTokenExpiry();
      }, 1000);
    } catch (error) {
      console.warn('Failed to refresh session:', error);
      // Show user-friendly message for session refresh failure
      toast.error('Unable to extend session. Please save your work and log in again.');
    }
  }, [checkTokenExpiry]);

  // Monitor session expiry
  useEffect(() => {
    if (user) {
      checkTokenExpiry();

      // 5-minute sessions: Check every 30 seconds for reasonable monitoring
      // This is less aggressive but still provides good UX
      const interval = setInterval(() => {
        checkTokenExpiry();
      }, 30000);

      return () => clearInterval(interval);
    } else {
      setSessionTimeRemaining(null);
    }
  }, [user, checkTokenExpiry]);

  // Initial auth check - ONLY when needed to avoid unnecessary 401s
  useEffect(() => {
    // Don't try to fetch profile if session has already expired
    if (sessionExpired) {
      setLoading(false);
      return;
    }

    // Check if we're in browser and get current path
    if (typeof window === 'undefined') {
      setLoading(false);
      return;
    }

    const currentPath = window.location.pathname;

    // If we're on a public route, don't make any auth checks
    if (isPublicRoute(currentPath)) {
      setUser(null);
      setSessionTimeRemaining(null);
      setLoading(false);
      return;
    }

    // Only check auth status if we're on a protected route
    // This prevents 401 errors when landing on public pages
    getSessionStatus()
      .then((sessionInfo) => {
        if (sessionInfo) {
          // We have a valid session, fetch the full profile
          setSessionTimeRemaining(sessionInfo.time_remaining);
          return fetchProfile()
            .then((u) => {
              setUser(u);
            });
        } else {
          // No valid session on protected route - redirect to login
          setUser(null);
          setSessionTimeRemaining(null);
          if (typeof window !== 'undefined') {
            window.location.replace('/login?auth=required');
          }
        }
      })
      .catch(() => {
        // Handle any errors by clearing user state and redirecting
        setUser(null);
        setSessionTimeRemaining(null);
        if (typeof window !== 'undefined') {
          window.location.replace('/login?auth=required');
        }
      })
      .finally(() => setLoading(false))
  }, [sessionExpired])

  // Handle session expiry warnings and redirect
  useEffect(() => {
    console.log(`DEBUG: Session expiry check - remaining: ${sessionTimeRemaining}, user: ${user ? 'logged in' : 'null'}`);

    if (sessionTimeRemaining !== null && sessionTimeRemaining <= 0 && user && !isLoggingOut) {
      // Session has expired (but not due to manual logout)
      console.warn('Session has expired - logging out user');

      // Clear user state immediately and mark session as expired
      setUser(null);
      setSessionTimeRemaining(null);
      setSessionExpired(true);

      // Force redirect to login page if we're not already on a public route
      if (typeof window !== 'undefined' && !isPublicRoute(window.location.pathname)) {
        console.log('DEBUG: Redirecting to login page due to expired session');
        window.location.replace("/?session=expired");
      }
    }
  }, [sessionTimeRemaining, user, isLoggingOut]);  // Add activity detection to extend sessions
  useEffect(() => {
    if (!user) return;

    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    let activityTimer: NodeJS.Timeout;

    const handleActivity = () => {
      // Mark that user has recent activity
      setHasRecentActivity(true);

      // Clear existing timer
      if (activityTimer) {
        clearTimeout(activityTimer);
      }

      // 5-minute sessions: Clear recent activity flag after 30 seconds of inactivity
      activityTimer = setTimeout(() => {
        console.log('User marked as inactive after 30 seconds of no activity');
        setHasRecentActivity(false);
      }, 30 * 1000); // 30 seconds
    };

    // Handle page visibility changes (user switching tabs/coming back)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // User came back to the tab, check token immediately
        checkTokenExpiry();
      }
    };

    // Add event listeners
    activityEvents.forEach(event => {
      document.addEventListener(event, handleActivity, true);
    });

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Do NOT call handleActivity() immediately - let user actually do something first
    // This prevents automatic "active" state that would allow unwanted refreshes

    return () => {
      // Cleanup
      if (activityTimer) {
        clearTimeout(activityTimer);
      }
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleActivity, true);
      });
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [user, checkTokenExpiry]); // Removed refreshSession to prevent cycles

  const login = async (email: string, password: string) => {
    try {
      await apiLogin(email, password); // This sets the HTTP-only cookie
      const u = await fetchProfile(); // Fetch the user profile
      setUser(u);
      setSessionExpired(false); // Reset session expired flag on successful login
      checkTokenExpiry();
    } catch (error) {
      console.error('DEBUG: Login failed:', error);
      throw error;
    }
  }

  const signup = async (firstName: string, lastName: string, email: string, password: string) => {
    const { user: newUser, access_token } = await apiSignup(
      firstName,
      lastName,
      email,
      password
    )
    // backend doesn't set httpOnly cookie on signup, so we store it temporarily:
    document.cookie = `access_token=${access_token}; path=/;`
    setUser(newUser)
    setSessionExpired(false); // Reset session expired flag on successful signup
    checkTokenExpiry()
  }

  const logout = async () => {
    setIsLoggingOut(true); // Prevent session expiry toasts during manual logout

    try {
      await apiLogout();        // clear cookie server-side
      toast.success('Successfully logged out');
    } catch {
      // Even if server logout fails, clear client state
      toast.info('Logged out locally');
    }

    setUser(null);              // clear client-side user
    setSessionTimeRemaining(null);
    setSessionExpired(false);   // Reset session expired flag
    setIsLoggingOut(false);     // Reset the flag
    router.push("/?logout=success");  // Add logout parameter to prevent auth required toast
  }

  // ─── updateProfile: PATCH /users/me then re‐fetch /users/me ───
  const updateProfile = async (payload: {
    currentPassword: string
    firstName?: string
    lastName?: string
    email?: string
    password?: string
  }) => {
    const { currentPassword, firstName, lastName, email, password } = payload
    const body: {
      current_password: string
      first_name?: string
      last_name?: string
      email?: string
      password?: string
    } = { current_password: currentPassword }
    if (firstName !== undefined) body.first_name = firstName
    if (lastName !== undefined) body.last_name = lastName
    if (email !== undefined) body.email = email
    if (password !== undefined) body.password = password

    await apiUpdateProfile(body)
    const u = await fetchProfile()
    setUser(u)
    checkTokenExpiry()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        updateProfile,
        sessionTimeRemaining,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
