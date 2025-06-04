'use client'

import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react'
import Cookies from 'js-cookie'
import API from '@/lib/api'
import { apiLogin, apiSignup, fetchProfile, User, apiUpdateProfile } from '@/lib/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (firstName: string, lastName: string, email: string, password: string) => Promise<void>
  logout: () => void
  updateProfile: (payload: {
    currentPassword: string
    firstName?: string
    lastName?: string
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
  const login = async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password)
    Cookies.set('token', access_token)
    const profile = await fetchProfile()
    setUser(profile.data)
  }

  /**
   * signup: calls /auth/signup (gets user + token), stores cookie, and sets user
   */
  const signup = async (firstName: string, lastName: string, email: string, password: string) => {
    const { user: newUser, access_token } = await apiSignup(
      firstName,
      lastName,
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

    await API.patch("/users/me", body)
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