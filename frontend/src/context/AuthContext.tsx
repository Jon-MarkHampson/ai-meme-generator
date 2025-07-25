// AuthContext.tsx
'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext, useCallback } from 'react'
import { apiLogin, apiLogout, apiSignup, fetchProfile, User, apiUpdateProfile, getSessionStatus, apiRefreshSession } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { isPublicRoute } from '@/lib/authRoutes'
import { toast } from 'sonner'

// Mutable reference that can be used outside React (e.g. axios interceptor)
let setUserRef: React.Dispatch<React.SetStateAction<User | null>> | null = null;

/** Clears user state without navigation—handy for 401 interceptors */
export function logoutSilently() {
  setUserRef?.(null);
}

interface AuthContextType {
  user: User | null
  loading: boolean
  sessionTimeRemaining: number | null
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
}

export const AuthContext = createContext<AuthContextType>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [sessionTimeRemaining, setSessionTimeRemaining] = useState<number | null>(null)
  const [hasRecentActivity, setHasRecentActivity] = useState(false)
  const router = useRouter()

  // expose the state setter to logoutSilently()
  setUserRef = setUser;

  // Session monitoring - check remaining time
  const checkSession = useCallback(async () => {
    if (!user) {
      console.log('🔍 [AUTH DEBUG] checkSession: No user, skipping session check');
      return;
    }

    console.log('🔍 [AUTH DEBUG] checkSession: Starting session check for user:', user.email);

    try {
      const sessionInfo = await getSessionStatus();
      const remaining = sessionInfo?.time_remaining ?? 0;
      console.log(`⏱️ [AUTH DEBUG] Session remaining: ${remaining} seconds, hasRecentActivity: ${hasRecentActivity}`);

      setSessionTimeRemaining(remaining);

      // If session expired, handle logout
      if (remaining <= 0) {
        console.warn('❌ [AUTH DEBUG] Session expired! Logging out user');
        setUser(null);
        setSessionTimeRemaining(null);
        router.replace('/?session=expired');
        return;
      }

      // Auto-refresh only if user is VERY recently active (within 30s) and session between 30-60s
      if (remaining < 60 && remaining > 30 && hasRecentActivity) {
        console.log('🔄 [AUTH DEBUG] Session < 60s and user recently active - attempting refresh');
        try {
          await apiRefreshSession();
          console.log('✅ [AUTH DEBUG] Session refreshed successfully');
          // Recheck after refresh
          setTimeout(checkSession, 1000);
        } catch (error) {
          console.error('❌ [AUTH DEBUG] Failed to refresh session:', error);
          toast.error('Unable to extend session. Please save your work and log in again.');
        }
      } else if (remaining < 60) {
        console.log(`⚠️ [AUTH DEBUG] Session < 60s but user not recently active (hasRecentActivity: ${hasRecentActivity}) - allowing countdown`);
      }
    } catch (error) {
      console.error('❌ [AUTH DEBUG] Session check failed:', error);
      setSessionTimeRemaining(null);
    }
  }, [user, hasRecentActivity, router]);

  // Monitor session every 30 seconds when user is logged in
  useEffect(() => {
    if (!user) {
      console.log('👤 [AUTH DEBUG] No user - clearing session timer');
      setSessionTimeRemaining(null);
      return;
    }

    console.log('⏰ [AUTH DEBUG] Setting up session monitoring for user:', user.email);
    checkSession(); // Initial check
    const interval = setInterval(() => {
      console.log('🔔 [AUTH DEBUG] 30-second session check interval triggered');
      checkSession();
    }, 30000); // Check every 30 seconds

    return () => {
      console.log('🛑 [AUTH DEBUG] Clearing session monitoring interval');
      clearInterval(interval);
    };
  }, [user, checkSession]);

  // Activity detection to enable session refresh
  useEffect(() => {
    if (!user) {
      console.log('👤 [AUTH DEBUG] No user - skipping activity detection setup');
      return;
    }

    console.log('🖱️ [AUTH DEBUG] Setting up activity detection for user:', user.email);
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    let activityTimer: NodeJS.Timeout;

    const handleActivity = () => {
      if (!hasRecentActivity) {
        console.log('✨ [AUTH DEBUG] User activity detected - marking as active');
        setHasRecentActivity(true);
      }

      // Reset inactivity timer (30 seconds - shorter window)
      clearTimeout(activityTimer);
      activityTimer = setTimeout(() => {
        console.log('😴 [AUTH DEBUG] 30 seconds of inactivity - marking user as inactive');
        setHasRecentActivity(false);
      }, 30 * 1000); // 30 seconds instead of 2 minutes
    };

    // Attach event listeners
    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    console.log('🎯 [AUTH DEBUG] Activity listeners attached for events:', activityEvents);

    return () => {
      console.log('🛑 [AUTH DEBUG] Removing activity listeners and clearing timer');
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
      clearTimeout(activityTimer);
    };
  }, [user, hasRecentActivity]);

  // Initial auth check - only on protected routes
  useEffect(() => {
    if (typeof window === 'undefined') {
      console.log('🖥️ [AUTH DEBUG] Server-side render detected - skipping auth check');
      return; // Server-side skip
    }

    const currentPath = window.location.pathname;
    console.log('🚀 [AUTH DEBUG] Initial auth check starting for path:', currentPath);

    // If we're on a public route, don't make any auth checks
    if (isPublicRoute(currentPath)) {
      console.log('🌍 [AUTH DEBUG] Public route detected - clearing user and loading');
      setUser(null);
      setLoading(false);
      return;
    }

    console.log('🔒 [AUTH DEBUG] Protected route detected - checking session status');
    // Only check auth status if we're on a protected route
    getSessionStatus()
      .then((sessionInfo) => {
        if (sessionInfo) {
          console.log('✅ [AUTH DEBUG] Valid session found, fetching user profile. Time remaining:', sessionInfo.time_remaining);
          // We have a valid session, fetch the full profile
          return fetchProfile().then((user) => {
            console.log('👤 [AUTH DEBUG] User profile fetched:', user.email);
            setUser(user);
          });
        } else {
          console.log('❌ [AUTH DEBUG] No valid session - redirecting to login');
          // No valid session on protected route - redirect to login
          setUser(null);
          router.replace('/login?auth=required');
        }
      })
      .catch((error) => {
        console.error('❌ [AUTH DEBUG] Auth check failed:', error);
        // Handle any errors by clearing user state and redirecting
        setUser(null);
        router.replace('/login?auth=required');
      })
      .finally(() => {
        console.log('🏁 [AUTH DEBUG] Initial auth check completed - setting loading to false');
        setLoading(false);
      })
  }, [router])

  const login = async (email: string, password: string) => {
    await apiLogin(email, password)
    // After login, fetch the user profile
    const user = await fetchProfile()
    setUser(user)
    router.push('/generate')
  }

  const signup = async (firstName: string, lastName: string, email: string, password: string) => {
    const signupResponse = await apiSignup(firstName, lastName, email, password)
    setUser(signupResponse.user)
    router.push('/generate')
  }

  const logout = async () => {
    setUser(null)
    await apiLogout()
    router.push('/?logout=success')
  }

  const updateProfile = async (payload: {
    currentPassword: string
    firstName?: string
    lastName?: string
    email?: string
    password?: string
  }) => {
    const updatedUser = await apiUpdateProfile(payload)
    setUser(updatedUser)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        sessionTimeRemaining,
        login,
        signup,
        logout,
        updateProfile
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
