'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react'
import { apiLogin, apiLogout, apiSignup, fetchProfile, User, apiUpdateProfile, getSessionStatus } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { isPublicRoute } from '@/lib/authRoutes'

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
}

export const AuthContext = createContext<AuthContextType>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // expose the state setter to logoutSilently()
  setUserRef = setUser;

  // Initial auth check - only on protected routes
  useEffect(() => {
    if (typeof window === 'undefined') return; // Server-side skip

    const currentPath = window.location.pathname;

    // If we're on a public route, don't make any auth checks
    if (isPublicRoute(currentPath)) {
      setUser(null);
      setLoading(false);
      return;
    }

    // Only check auth status if we're on a protected route
    getSessionStatus()
      .then((sessionInfo) => {
        if (sessionInfo) {
          // We have a valid session, fetch the full profile
          return fetchProfile().then(setUser);
        } else {
          // No valid session on protected route - redirect to login
          setUser(null);
          router.replace('/login?auth=required');
        }
      })
      .catch(() => {
        // Handle any errors by clearing user state and redirecting
        setUser(null);
        router.replace('/login?auth=required');
      })
      .finally(() => setLoading(false))
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
