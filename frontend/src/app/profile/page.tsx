'use client'
import { useContext, useEffect } from 'react'
import { AuthContext } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'

export default function ProfilePage() {
  const { user, logout } = useContext(AuthContext)
  const router = useRouter()

  useEffect(() => {
    if (!user) router.push('/login')
  }, [user])

  if (!user) return <p>Loading…</p>

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl mb-4">Welcome, {user.username}</h1>
      <p className="mb-6">Email: {user.email}</p>
      <button
        className="bg-red-500 text-white p-2 rounded"
        onClick={() => { logout(); router.push('/login') }}
      >
        Log Out
      </button>
    </div>
  )
}