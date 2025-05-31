'use client'
import { useState, useContext } from 'react'
import { AuthContext } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const { login } = useContext(AuthContext)
  const router = useRouter()
  const [form, setForm] = useState({ username:'', password:'' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await login(form.username, form.password)
    router.push('/profile')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-sm mx-auto p-6">
      <input className="w-full p-2 border" placeholder="Username"
        onChange={e=>setForm(f=>({...f,username:e.target.value}))}/>
      <input type="password" className="w-full p-2 border" placeholder="Password"
        onChange={e=>setForm(f=>({...f,password:e.target.value}))}/>
      <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">
        Log In
      </button>
    </form>
  )
}