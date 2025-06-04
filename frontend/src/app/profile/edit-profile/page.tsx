// src/app/(protected)/edit-profile/page.tsx

"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useAuth } from "@/context/AuthContext"
import { apiDeleteAccount } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"

/**
 * 1) current_password is REQUIRED whenever submitting changes.
 * 2) username/email: optional, only if changed.
 * 3) password: if nonempty, must be ≥6. confirmPassword must match it.
 * 4) Must change at least one of { username, email, password }.
 */
const formSchema = z
  .object({
    current_password: z
      .string()
      .min(1, { message: "You must enter your current password to save changes." }),

    username: z.string().min(2, { message: "Username must be at least 2 characters." }).optional(),

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
      // If they typed a new password, confirmPassword must match
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
      // Must change at least one of username/email/password (besides current_password)
      return data.username !== undefined || data.email !== undefined || data.password !== undefined
    },
    {
      message: "Please change at least one field.",
      path: [],
    }
  )

type FormValues = z.infer<typeof formSchema>

export default function EditProfilePage() {
  const router = useRouter()
  const { user, loading, updateProfile, logout } = useAuth()

  // ─── Update Profile state ───
  const [updateError, setUpdateError] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)

  // ─── Delete Account state (omitted here) ───
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deletePassword, setDeletePassword] = useState("")
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Redirect to /login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login")
    }
  }, [loading, user, router])

  const methods = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      current_password: "",
      username: user?.username || "",
      email: user?.email || "",
      password: "",
      confirmPassword: "",
    },
  })

  async function onSubmit(values: FormValues) {
    setUpdateError(null)
    setIsUpdating(true)

    try {
      // Build payload (always include current_password)
      const payload: {
        current_password: string
        username?: string
        email?: string
        password?: string
      } = {
        current_password: values.current_password,
      }
      if (values.username && values.username !== user?.username) {
        payload.username = values.username
      }
      if (values.email && values.email !== user?.email) {
        payload.email = values.email
      }
      if (values.password) {
        payload.password = values.password
      }

      // If nothing changed, do nothing:
      if (
        payload.username === undefined &&
        payload.email === undefined &&
        payload.password === undefined
      ) {
        setIsUpdating(false)
        return
      }

      // ─── CALL updateProfile FROM CONTEXT ───
      await updateProfile(payload)

      // Since updateProfile() calls `fetchProfile()` and `setUser(…)`,
      // the React context still has a non‐null `user`, so you stay logged in.
      router.push("/profile")
    } catch (err: any) {
      setUpdateError(err.response?.data?.detail || "Failed to update profile.")
    } finally {
      setIsUpdating(false)
    }
  }

  async function handleDeleteAccount() {
    setDeleteError(null)
    setIsDeleting(true)
    try {
      await apiDeleteAccount(deletePassword)
      logout()
      router.push("/")
    } catch (err: any) {
      setDeleteError(err.response?.data?.detail || "Incorrect password.")
    } finally {
      setIsDeleting(false)
    }
  }

  if (!user) {
    return null // or a spinner
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Update Your Account</CardTitle>
          <p className="text-center text-sm text-gray-500">
            You can update your username, email, or password here.
            <br />
            (Current password is required to save changes.)
          </p>
        </CardHeader>

        <CardContent>
          {updateError && (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{updateError}</AlertDescription>
            </Alert>
          )}

          <Form {...methods}>
            <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
              {/* Current Password */}
              <FormField
                control={methods.control}
                name="current_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Type your current password"
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.current_password && (
                      <p className="mt-1 text-sm text-red-600">
                        {methods.formState.errors.current_password.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* Username (optional) */}
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

              {/* Email (optional) */}
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

              {/* New Password (optional) */}
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

              {/* Confirm New Password (optional) */}
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

              {/* Save Changes & Cancel Buttons */}
              <div className="mt-6 flex flex-col space-y-2 justify-center">
                <Button type="submit" className="w-full" disabled={isUpdating}>
                  {isUpdating ? "Saving…" : "Save Changes"}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => router.push("/profile")}
                  className="w-full"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>

        {/* Delete Account Section (unchanged) */}
        <CardContent className="border-t border-gray-200 dark:border-gray-700">
          {!confirmDelete ? (
            <div className="flex justify-center mt-4">
              <Button
                variant="destructive"
                className="w-full"
                onClick={() => {
                  setConfirmDelete(true)
                  setDeletePassword("")
                  setDeleteError(null)
                }}
              >
                Delete My Account
              </Button>
            </div>
          ) : (
            <div className="space-y-4 mt-4">
              <p className="text-sm text-red-700 text-center">
                Enter your password to confirm deletion
              </p>

              <div className="space-y-1">
                <label
                  htmlFor="delete-password"
                  className="block text-sm font-medium text-red-700"
                >
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
                  disabled={isDeleting || deletePassword === ""}
                  className="flex-1 mr-2"
                >
                  {isDeleting ? "Deleting…" : "Confirm Delete"}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setConfirmDelete(false)
                    setDeleteError(null)
                    setDeletePassword("")
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