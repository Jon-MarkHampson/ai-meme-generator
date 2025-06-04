'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react'
import Cookies from 'js-cookie'
import API from '@/lib/api'
import { apiLogin, apiSignup, fetchProfile, User , apiUpdateProfile} from '@/lib/auth'

interface AuthContextType {
  user: User | null
  loading: boolean   
  login: (username: string, password: string) => Promise<void>
  signup: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  updateProfile: (payload: {
    current_password: string
    username?: string
    email?: string
    password?: string
  }) => Promise<void>
}


export const AuthContext = createContext<AuthContextType>(null!)

/**
 * Wrap app in <AuthProvider> in layout.tsx
 * so every page can access `user`, `login`, `signup`, `logout`.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true) 

  // On mount, if a 'token' cookie exists, fetch /users/me
  useEffect(() => {
    const token = Cookies.get('token')
    if (token) {
      fetchProfile()
        .then((resp) => {
          setUser(resp.data)
        })
        .catch(() => {
          Cookies.remove('token')
          setUser(null)
        })
        .finally(() => {
          setLoading(false)
        })
    } else {
      setLoading(false)
    }
  }, [])

  /**
   * login: calls /auth/login, stores JWT cookie, then fetches profile
   */
  const login = async (username: string, password: string) => {
    const { access_token } = await apiLogin(username, password)
    Cookies.set('token', access_token)
    const profile = await fetchProfile()
    setUser(profile.data)
  }

  /**
   * signup: calls /auth/signup (gets user + token), stores cookie, and sets user
   */
  const signup = async (username: string, email: string, password: string) => {
    const { user: newUser, access_token } = await apiSignup(
      username,
      email,
      password
    )
    Cookies.set('token', access_token)
    setUser(newUser)
  }

  /**
   * logout: clear the cookie and React state
   */
  const logout = () => {
    Cookies.remove('token')
    setUser(null)
  }

  // ─── updateProfile: PATCH /users/me then re‐fetch /users/me ───
  const updateProfile = async (payload: {
    current_password: string
    username?: string
    email?: string
    password?: string
  }) => {
    // 1) PATCH /users/me (backend requires current_password in body)
    await API.patch("/users/me", payload)

    // 2) Re‐fetch the user’s profile so we update React state
    const resp = await fetchProfile()
    setUser(resp.data)
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