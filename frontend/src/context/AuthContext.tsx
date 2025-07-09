'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext, useCallback } from 'react'
import API from '@/lib/api'
import { apiLogin, apiLogout, apiSignup, fetchProfile, User, apiUpdateProfile } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { jwtDecode } from 'jwt-decode'

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

interface JWTPayload {
  exp: number;
  iat?: number;
  sub?: string;
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

    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('access_token='))
      ?.split('=')[1];

    if (!token) {
      setSessionTimeRemaining(null);
      return;
    }

    try {
      const payload = jwtDecode<JWTPayload>(token);
      const currentTime = Math.floor(Date.now() / 1000);
      const remaining = payload.exp - currentTime;

      if (remaining <= 0) {
        // Token is expired
        setSessionTimeRemaining(0);
        setUser(null);
        return;
      }

      setSessionTimeRemaining(remaining);

      // If less than 5 minutes remaining, show warning
      if (remaining < 300 && remaining > 0) {
        console.warn(`Session expires in ${Math.floor(remaining / 60)} minutes`);
        // You could show a toast notification here
      }

    } catch (error) {
      console.error('Error decoding token:', error);
      setSessionTimeRemaining(null);
      setUser(null);
    }
  }, []);

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

  // Handle session expiry warnings
  useEffect(() => {
    if (sessionTimeRemaining !== null && sessionTimeRemaining <= 0 && user) {
      // Session has expired
      console.warn('Session has expired');
      setUser(null);
      setSessionTimeRemaining(null);

      // Only redirect if not already on a public route
      const isPublicRoute = ["/", "/login", "/signup"].includes(window.location.pathname);
      if (!isPublicRoute) {
        router.replace("/?session=expired");
      }
    }
  }, [sessionTimeRemaining, user, router]);

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
    const body: any = { current_password: currentPassword }
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
