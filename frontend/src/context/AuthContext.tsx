'use client'

import { createContext, useState, useEffect, ReactNode } from 'react'
import Cookies from 'js-cookie'
import { login as apiLogin, signup as apiSignup, fetchProfile, User } from '@/lib/auth'

interface AuthContextType {
  user: User | null
  login: (u: string, p: string) => Promise<void>
  signup: (u: string, e: string, p: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextType>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = Cookies.get('token')
    if (token) {
      fetchProfile()
        .then(r => setUser(r.data))
        .catch(() => Cookies.remove('token'))
    }
  }, [])

  const login = async (username: string, password: string) => {
    const { access_token } = await apiLogin(username, password)
    Cookies.set('token', access_token)
    const profile = await fetchProfile()
    setUser(profile.data)
  }

  const signup = async (username: string, email: string, password: string) => {
    await apiSignup(username, email, password)
    await login(username, password)
  }

  const logout = () => {
    Cookies.remove('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}