'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext, useCallback } from 'react'
import { apiLogin, apiLogout, apiSignup, fetchProfile, User, apiUpdateProfile, apiRefreshSession } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { getAccessTokenFromCookies, getTokenTimeRemaining } from '@/lib/authUtils'

// Mutable reference that can be used outside React (e.g. axios interceptor)
let setUserRef: React.Dispatch<React.SetStateAction<User | null>> | null = null;

/** Clears user state without navigation—handy for 401 interceptors */
export function logoutSilently() {
  setUserRef?.(null);
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
  const router = useRouter()

  // expose the state setter to logoutSilently()
  setUserRef = setUser;

  // Function to check token expiry and calculate remaining time
  const checkTokenExpiry = useCallback(() => {
    if (typeof window === 'undefined') return;

    const token = getAccessTokenFromCookies();
    if (!token) {
      setSessionTimeRemaining(null);
      return;
    }

    const remaining = getTokenTimeRemaining(token);
    if (remaining === null) {
      setSessionTimeRemaining(null);
      setUser(null);
      return;
    }

    if (remaining <= 0) {
      // Token is expired
      setSessionTimeRemaining(0);
      setUser(null);
      return;
    }

    setSessionTimeRemaining(remaining);

    // If less than 10 minutes remaining, try to refresh the session
    if (remaining < 600 && remaining > 0) {
      console.warn(`Session expires in ${Math.floor(remaining / 60)} minutes - attempting refresh`);
      refreshSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Function to refresh session by making an authenticated API call
  const refreshSession = useCallback(async () => {
    try {
      // Call the dedicated refresh endpoint
      await apiRefreshSession();
      console.log('Session refreshed successfully');

      // Recheck token expiry after refresh
      setTimeout(checkTokenExpiry, 1000);
    } catch (error) {
      console.warn('Failed to refresh session:', error);
    }
  }, [checkTokenExpiry]);

  // Monitor session expiry
  useEffect(() => {
    if (user) {
      checkTokenExpiry();

      // Check every 30 seconds
      const interval = setInterval(checkTokenExpiry, 30000);

      return () => clearInterval(interval);
    } else {
      setSessionTimeRemaining(null);
    }
  }, [user, checkTokenExpiry]);

  // Initial auth check
  useEffect(() => {
    fetchProfile()
      .then((u) => {
        setUser(u);
        checkTokenExpiry();
      })
      .catch(() => {
        setUser(null);
        setSessionTimeRemaining(null);
      })
      .finally(() => setLoading(false))
  }, [checkTokenExpiry])

  // Handle session expiry warnings and redirect
  useEffect(() => {
    if (sessionTimeRemaining !== null && sessionTimeRemaining <= 0 && user) {
      // Session has expired
      console.warn('Session has expired - logging out user');

      // Clear user state immediately
      setUser(null);
      setSessionTimeRemaining(null);

      // Let the API interceptor handle the redirect to avoid race conditions
      // The API interceptor will handle 401 errors and redirect appropriately
    }
  }, [sessionTimeRemaining, user]);

  // Add activity detection to extend sessions
  useEffect(() => {
    if (!user) return;

    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    let activityTimer: NodeJS.Timeout;

    const handleActivity = () => {
      // Clear existing timer
      if (activityTimer) {
        clearTimeout(activityTimer);
      }

      // Set timer to refresh session after 5 minutes of activity
      activityTimer = setTimeout(() => {
        // Only refresh if less than 10 minutes remaining to avoid spam
        if (sessionTimeRemaining && sessionTimeRemaining < 600) {
          refreshSession();
        }
      }, 5 * 60 * 1000); // 5 minutes
    };

    // Add event listeners
    activityEvents.forEach(event => {
      document.addEventListener(event, handleActivity, true);
    });

    // Initial activity setup
    handleActivity();

    return () => {
      // Cleanup
      if (activityTimer) {
        clearTimeout(activityTimer);
      }
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleActivity, true);
      });
    };
  }, [user, sessionTimeRemaining, refreshSession]);

  const login = async (email: string, password: string) => {
    await apiLogin(email, password)
    const u = await fetchProfile()
    setUser(u)
    checkTokenExpiry()
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
    checkTokenExpiry()
  }

  const logout = async () => {
    try {
      await apiLogout();        // clear cookie server-side
    } catch {
      // optional: show a toast if it fails
    }
    setUser(null);              // clear client-side user
    setSessionTimeRemaining(null);
    router.push("/");           // send them to homepage or login
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
