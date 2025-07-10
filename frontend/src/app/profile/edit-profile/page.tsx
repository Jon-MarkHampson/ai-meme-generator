'use client';

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import { useAuth } from "@/context/AuthContext";
import { apiDeleteAccount } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";

/**
 * 1) currentPassword is REQUIRED (always sent as current_password to backend).
 * 2) firstName, lastName, email, password, confirmPassword are all optional.
 * 3) If password is non‐empty, confirmPassword must match.
 * 4) At least one of (firstName, lastName, email, password) must be present.
 */
const formSchema = z
  .object({
    currentPassword: z
      .string()
      .min(1, { message: "Current password is required." }),

    firstName: z
      .string()
      .min(1, { message: "First name must be at least 1 character." })
      .optional(),

    lastName: z
      .string()
      .min(1, { message: "Last name must be at least 1 character." })
      .optional(),

    email: z
      .string()
      .transform((v) => (v === "" ? undefined : v))
      .refine((v) => v === undefined || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), {
        message: "Please enter a valid email.",
      })
      .optional(),

    password: z
      .string()
      .transform((v) => (v === "" ? undefined : v))
      .refine((v) => v === undefined || v.length >= 6, {
        message: "New password must be at least 6 characters.",
      })
      .optional(),

    confirmPassword: z
      .string()
      .transform((v) => (v === "" ? undefined : v))
      .optional(),
  })
  .refine(
    (data) => {
      if (data.password !== undefined) {
        return data.confirmPassword !== undefined && data.password === data.confirmPassword;
      }
      return true;
    },
    {
      message: "Passwords do not match.",
      path: ["confirmPassword"],
    }
  )
  .refine(
    (data) => {
      // Make sure at least one of firstName/lastName/email/password was provided
      return (
        data.firstName !== undefined ||
        data.lastName !== undefined ||
        data.email !== undefined ||
        data.password !== undefined
      );
    },
    {
      message: "Please change at least one field.",
      path: [],
    }
  );

type FormValues = z.infer<typeof formSchema>;

export default function EditProfilePage() {
  const router = useRouter();
  const { user, updateProfile, logout } = useAuth();

  const [updateError, setUpdateError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Initialize React Hook Form with camelCase defaults,
  // but defaultValues pull from user.first_name / user.last_name
  const methods = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      currentPassword: "",
      firstName: user?.first_name || "",
      lastName: user?.last_name || "",
      email: user?.email || "",
      password: "",
      confirmPassword: "",
    },
  });

  async function onSubmit(values: FormValues) {
    setUpdateError(null);
    setIsUpdating(true);

    // Build a *camelCase* payload to match the TS signature of `updateProfile`.
    const payloadForAuthContext: {
      currentPassword: string;
      firstName?: string;
      lastName?: string;
      email?: string;
      password?: string;
    } = {
      currentPassword: values.currentPassword,
    };

    if (values.firstName && values.firstName !== user?.first_name) {
      payloadForAuthContext.firstName = values.firstName;
    }
    if (values.lastName && values.lastName !== user?.last_name) {
      payloadForAuthContext.lastName = values.lastName;
    }
    if (values.email && values.email !== user?.email) {
      payloadForAuthContext.email = values.email;
    }
    if (values.password) {
      payloadForAuthContext.password = values.password;
    }

    // If no other field changed, simply bail
    if (
      payloadForAuthContext.firstName === undefined &&
      payloadForAuthContext.lastName === undefined &&
      payloadForAuthContext.email === undefined &&
      payloadForAuthContext.password === undefined
    ) {
      setIsUpdating(false);
      return;
    }

    try {
      // Now pass the correct camelCase object.  AuthContext.updateProfile
      // is responsible for internally converting camelCase → snake_case
      await updateProfile(payloadForAuthContext);
      router.push("/profile");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setUpdateError(error.response?.data?.detail || "Failed to update profile.");
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleDeleteAccount() {
    setDeleteError(null);
    setIsDeleting(true);
    try {
      await apiDeleteAccount(deletePassword);
      logout();
      router.push("/");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setDeleteError(error.response?.data?.detail || "Incorrect password.");
    } finally {
      setIsDeleting(false);
    }
  }

  if (!user) {
    return null; // or a loading spinner
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        {/* — Update Profile Section — */}
        <CardHeader>
          <CardTitle className="text-center">Update Your Account</CardTitle>
          <p className="text-center text-sm text-gray-500">
            Optionally update your name email, or password.
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

          {/* ========= Wrap <form> inside Shadcn/UI’s <Form> for RHF context ========= */}
          <Form {...methods}>
            <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
              {/* — Current Password (always required) — */}
              <FormField
                control={methods.control}
                name="currentPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Enter your current password"
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.currentPassword && (
                      <p className="mt-1 text-sm text-destructive">
                        {methods.formState.errors.currentPassword.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — First Name (optional) — */}
              <FormField
                control={methods.control}
                name="firstName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>First Name</FormLabel>
                    <FormControl>
                      <Input placeholder={user.first_name} {...field} />
                    </FormControl>
                    {methods.formState.errors.firstName && (
                      <p className="mt-1 text-sm text-destructive">
                        {methods.formState.errors.firstName.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Last Name (optional) — */}
              <FormField
                control={methods.control}
                name="lastName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Last Name</FormLabel>
                    <FormControl>
                      <Input placeholder={user.last_name} {...field} />
                    </FormControl>
                    {methods.formState.errors.lastName && (
                      <p className="mt-1 text-sm text-destructive">
                        {methods.formState.errors.lastName.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Email (optional) — */}
              <FormField
                control={methods.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder={user.email} {...field} />
                    </FormControl>
                    {methods.formState.errors.email && (
                      <p className="mt-1 text-sm text-destructive">
                        {methods.formState.errors.email.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — New Password (optional) — */}
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
                      <p className="mt-1 text-sm text-destructive">
                        {methods.formState.errors.password.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Confirm New Password (optional) — */}
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
                      <p className="mt-1 text-sm text-destructive">
                        {methods.formState.errors.confirmPassword.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Buttons: Save / Cancel — */}
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

        {/* — Delete Account Section — */}
        <CardContent className="border-t">
          {!confirmDelete ? (
            <div className="flex justify-center mt-4">
              <Button
                variant="destructive"
                className="w-full"
                onClick={() => {
                  setConfirmDelete(true);
                  setDeletePassword("");
                  setDeleteError(null);
                }}
              >
                Delete My Account
              </Button>
            </div>
          ) : (
            <div className="space-y-4 mt-4">
              <p className="text-sm text-destructive text-center">
                Enter your password to confirm deletion
              </p>

              <div className="space-y-1">
                <label
                  htmlFor="delete-password"
                  className="block text-sm font-medium text-destructive"
                >
                  Password
                </label>
                <Input
                  id="delete-password"
                  type="password"
                  placeholder="Type your password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="block w-full rounded-md"
                />
                {deleteError && (
                  <p className="mt-1 text-sm text-destructive text-center">
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
                    setConfirmDelete(false);
                    setDeleteError(null);
                    setDeletePassword("");
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
  );
}