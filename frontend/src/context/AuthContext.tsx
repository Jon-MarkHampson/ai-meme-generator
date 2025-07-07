'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react'
import API from '@/lib/api'
import { apiLogin, apiLogout, apiSignup, fetchProfile, User, apiUpdateProfile } from '@/lib/auth'
import { useRouter } from 'next/navigation'

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
  // expose the state setter to logoutSilently()
  setUserRef = setUser;
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    fetchProfile()
      .then((u) => setUser(u))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])


  const login = async (email: string, password: string) => {
    await apiLogin(email, password)
    const u = await fetchProfile()
    setUser(u)
  }

  const signup = async (firstName: string, lastName: string, email: string, password: string) => {
    const { user: newUser, access_token } = await apiSignup(
      firstName,
      lastName,
      email,
      password
    )
    // backend doesn’t set httpOnly cookie on signup, so we store it temporarily:
    document.cookie = `access_token=${access_token}; path=/;`
    setUser(newUser)
  }


  const logout = async () => {
    try {
      await apiLogout();        // clear cookie server-side
    } catch {
      // optional: show a toast if it fails
    }
    setUser(null);              // clear client-side user
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
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}