'use client'
import { useState, useContext } from 'react'
import { AuthContext } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'

export default function SignupPage() {
  const { signup } = useContext(AuthContext)
  const router = useRouter()
  const [form, setForm] = useState({ username:'', email:'', password:'' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await signup(form.username, form.email, form.password)
    router.push('/profile')
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="card max-w-md w-full space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-center">Create your account</h2>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-400">
            Join us and start creating memes
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium">
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              className="input mt-1"
              placeholder="Enter your username"
              onChange={e => setForm(f => ({...f, username: e.target.value}))}
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              className="input mt-1"
              placeholder="Enter your email"
              onChange={e => setForm(f => ({...f, email: e.target.value}))}
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="input mt-1"
              placeholder="Choose a strong password"
              onChange={e => setForm(f => ({...f, password: e.target.value}))}
            />
          </div>
          <button type="submit" className="btn btn-primary w-full">
            Sign Up
          </button>
        </form>
      </div>
    </div>
  )
}