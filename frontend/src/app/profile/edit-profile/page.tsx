'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

import { useAuth } from '@/context/AuthContext'
import { apiDeleteAccount } from '@/lib/auth'

// Shadcn/UI imports:
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'

/**
 * 1) username/email: optional (if blank, won’t be sent to backend)
 * 2) password: if it’s a nonempty string, it must have length ≥ 6
 * 3) confirmPassword: only checked if password is nonempty
 * 4) ensure at least one of username/email/password is actually changed
 */
const formSchema = z
  .object({
    username: z
      .string()
      .min(2, { message: "Username must be at least 2 characters." })
      .optional(),

    // 1) We first transform "" → undefined
    // 2) If it is non‐undefined, then it must pass the email check
    email: z
      .string()
      .transform((val) => (val === "" ? undefined : val))
      .refine((val) => val === undefined || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val), {
        message: "Please enter a valid email address.",
      })
      .optional(),

    password: z
      .string()
      .transform((val) => (val === "" ? undefined : val))
      .refine((val) => val === undefined || val.length >= 6, {
        message: "Password must be at least 6 characters.",
      })
      .optional(),

    confirmPassword: z
      .string()
      .transform((val) => (val === "" ? undefined : val))
      .optional(),
  })
  .refine(
    (data) => {
      if (data.password !== undefined) {
        return data.confirmPassword !== undefined && data.password === data.confirmPassword
      }
      return true
    },
    {
      message: "Passwords do not match.",
      path: ["confirmPassword"],
    }
  )
  .refine(
    (data) => {
      // Make sure at least one of username/email/password is provided
      return data.username !== undefined || data.email !== undefined || data.password !== undefined
    },
    {
      message: "Please change at least one field.",
      path: [],
    }
  )

// Infer the TS type
type FormValues = z.infer<typeof formSchema>

export default function EditProfilePage() {
  const router = useRouter()
  const { user, loading, updateProfile, logout } = useAuth()

  // State for “Update Profile”
  const [updateError, setUpdateError] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)

  // State for “Delete Account”
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // If not logged in, redirect to /login
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [loading, user, router])

  // Initialize React Hook Form
  const methods = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: user?.username || '',
      email: user?.email || '',
      password: '',
      confirmPassword: '',
    },
  })

  async function onSubmit(values: FormValues) {
    setUpdateError(null)
    setIsUpdating(true)

    try {
      // Build “only changed fields” payload
      const payload: { username?: string; email?: string; password?: string } = {}
      if (values.username && values.username !== user?.username) {
        payload.username = values.username
      }
      if (values.email && values.email !== user?.email) {
        payload.email = values.email
      }
      if (values.password) {
        payload.password = values.password
      }

      if (Object.keys(payload).length === 0) {
        // Nothing changed; nothing to do
        setIsUpdating(false)
        return
      }

      await updateProfile(payload)
      router.push('/profile')
    } catch (err: any) {
      setUpdateError(err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setIsUpdating(false)
    }
  }

  async function handleDeleteAccount() {
    setDeleteError(null)
    setIsDeleting(true)

    try {
      await apiDeleteAccount(deletePassword)
      logout() // clear cookie + user state
      router.push('/')
    } catch (err: any) {
      setDeleteError(err.response?.data?.detail || 'Incorrect password.')
    } finally {
      setIsDeleting(false)
    }
  }

  if (!user) {
    // Optionally a spinner while loading === true
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        {/* — Update Profile Section — */}
        <CardHeader>
          <CardTitle className="text-center">Update Your Account</CardTitle>
          <p className="text-center text-sm text-gray-500">
            (Leave fields blank to keep unchanged)
          </p>
        </CardHeader>

        <CardContent>
          {updateError && (
            <p className="mb-4 text-center text-sm text-red-600">
              {updateError}
            </p>
          )}

          {/*
            ============
            IMPORTANT: wrap your <form> inside Shadcn/UI’s <Form>
            so that every <FormField> / <FormLabel> / <FormControl> 
            has a valid RHF context.
            ============
          */}
          <Form {...methods}>
            <form
              onSubmit={methods.handleSubmit(onSubmit)}
              className="space-y-8"
            >
              {/* Username */}
              <FormField
                control={methods.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input placeholder={user.username} {...field} />
                    </FormControl>
                    {methods.formState.errors.username && (
                      <p className="mt-1 text-sm text-red-600">
                        {methods.formState.errors.username.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* Email */}
              <FormField
                control={methods.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder={user.email}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.email && (
                      <p className="mt-1 text-sm text-red-600">
                        {methods.formState.errors.email.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* New Password */}
              <FormField
                control={methods.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>New Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Enter new password"
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.password && (
                      <p className="mt-1 text-sm text-red-600">
                        {methods.formState.errors.password.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* Confirm New Password */}
              <FormField
                control={methods.control}
                name="confirmPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm New Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Retype new password"
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.confirmPassword && (
                      <p className="mt-1 text-sm text-red-600">
                        {methods.formState.errors.confirmPassword.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* Save Changes Button */}
              <div className="mt-6 flex justify-center">
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isUpdating}
                >
                  {isUpdating ? 'Saving…' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </Form>
          { /* ^^^ Everything above is safely inside <Form> so useFormContext() is never null. */}
        </CardContent>

        {/* — Delete Account Section — */}
        <CardContent className="border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-center text-sm font-semibold text-red-600 mt-2 mb-2">
            Danger Zone
          </h3>

          {!confirmDelete ? (
            <div className="flex justify-center">
              <Button
                className='w-full'
                variant="destructive"
                onClick={() => {
                  setConfirmDelete(true)
                  setDeletePassword('')
                  setDeleteError(null)
                }}
              >
                Delete My Account
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-red-700 text-center">
                Enter your password to confirm deletion
              </p>

              <div className="space-y-1">
                <label htmlFor="delete-password" className="block text-sm font-medium text-red-700">
                  Password
                </label>
                <Input
                  id="delete-password"
                  type="password"
                  placeholder="Type your password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-neutral-100 dark:bg-neutral-700"
                />
                {deleteError && (
                  <p className="mt-1 text-sm text-red-600 text-center">
                    {deleteError}
                  </p>
                )}
              </div>

              <div className="flex justify-between">
                <Button
                  variant="destructive"
                  onClick={handleDeleteAccount}
                  disabled={isDeleting || deletePassword === ''}
                  className="flex-1 mr-2"
                >
                  {isDeleting ? 'Deleting…' : 'Confirm Delete'}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setConfirmDelete(false)
                    setDeleteError(null)
                    setDeletePassword('')
                  }}
                  className="flex-1 ml-2"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}